# 批量学习编排指令

主线程读取本文件后按以下步骤自动执行，不需要额外人工指令。

## 启动

1. 读 `state/task_state.yaml` 获取 `pending_urls`、`in_progress_urls`、`current_insight_count`
2. **幂等恢复检查**：如果 `in_progress_urls` 非空（上次会话中途崩溃），先处理：
   - 对每个 in_progress URL，检查 `knowledge/insights/articles.yaml` 中是否已有该 URL
   - 已有 → 移到 `completed_urls`
   - 未有 → 检查 knowledge/insights/ 下是否有残留文件（用 grep source 字段匹配 URL），有则删除（可能是损坏的半写入），然后移回 `pending_urls`
   - 清空 `in_progress_urls`，写回 `state/task_state.yaml`
3. 如果 `pending_urls` 为空，输出"全部完成"并打包上传，结束
4. 用以下命令提取当前所有 approach ID（仅 ID，不读全文）：
   ```bash
   cd knowledge/insights && for f in */*.yaml; do python3 -c "
   import yaml
   with open('$f') as fh:
       d = yaml.safe_load(fh)
       if 'id' in d: print(d['id'])
   "; done
   ```

## 循环（每轮处理 15 篇，每会话最多 3 轮 = 45 篇）

5. 从 `pending_urls` 取前 **15 个** URL
6. **标记 in_progress**：将这 15 个 URL 从 `pending_urls` 移到 `in_progress_urls`，立即写回 `state/task_state.yaml`
7. 将 15 个 URL 分成 **3 组**（每组 5 篇）
8. **并行启动 3 个 subagent**（task 工具），每个 subagent 传入：
   - `pipeline/batch_learn.md` 文件的完整内容作为指令
   - 分配的 5 个 URL
   - 步骤 4 提取的 approach ID 列表
   - 工作区路径前缀：仓库根目录（脚本在此目录下运行，全部用相对路径）
9. 等待 3 个 subagent 返回（每个返回：一行摘要 + articles.yaml 条目 YAML 文本）

### 主线程后处理（串行，消除并发冲突）

10. **串行追加 articles.yaml**：将 3 个 subagent 返回的 articles.yaml 条目依次追加到文件末尾（只由主线程写，避免并发覆盖）
11. **二次去重检查**：
    ```bash
    cd knowledge/insights && python3 -c "
    import yaml, os, collections
    ids = []
    for root, dirs, files in os.walk('.'):
        for f in files:
            if f.endswith('.yaml') and f != 'articles.yaml':
                with open(os.path.join(root, f)) as fh:
                    d = yaml.safe_load(fh)
                    if 'id' in d: ids.append((d['id'], os.path.join(root, f)))
    seen = {}
    for id, path in ids:
        if id in seen:
            print(f'重复 ID {id}: 保留 {seen[id]}，删除 {path}')
            os.remove(path)
        else:
            seen[id] = path
    "
    ```
12. **YAML 验证 + 自动清理损坏文件**：
    ```bash
    cd . && python3 -c "
    import yaml, os
    for root, dirs, files in os.walk('knowledge/insights'):
        for f in files:
            if f.endswith('.yaml'):
                path = os.path.join(root, f)
                try:
                    with open(path) as fh: yaml.safe_load(fh)
                except Exception as e:
                    print(f'损坏，已删除: {path} — {e}')
                    os.remove(path)
    print('YAML 验证完成')
    "
    ```
13. **更新 state/task_state.yaml**：
    - 将本轮 15 个 URL 从 `in_progress_urls` 移除
    - 追加到 `completed_urls`（结构化：每条含 url + produced_insights）
    - 更新 `current_insight_count`
    - 立即写回文件
14. **刷新 approach ID 列表**：重新执行步骤 4（下一轮 subagent 需要最新列表，消除跨轮去重盲区）
15. 如果已处理 ≥ 45 篇 → 跳到「收尾」
16. 否则回到步骤 5

## 收尾

17. **校验铁律 + 刷新检索索引**（拦截格式违规，并让本会话新学的 insight 进入 INDEX）：
    ```bash
    python3 tools/validate.py             # 有 ERROR 必须先修复，再继续打包
    python3 tools/build_insights_index.py
    ```
    确认 validate 输出 `0 errors`；索引条数 == 本会话结束后 `knowledge/insights/` 下 insight 文件总数。
18. 打包项目（排除 .git）：
    ```bash
    cd .. && rm -f AiHunter.zip && zip -r AiHunter.zip AiHunter/ -x "AiHunter/.git/*"
    ```
19. 上传 zip 并用 collect_artifact 收集
20. 输出最终摘要：
    - 本会话处理了 X 篇，新增 Y 条 insight
    - 剩余 Z 篇待处理
    - 新 zip URL（供下个会话使用）

## 写入错误规避（参见 pipeline/KNOWN_ISSUES.md）

- subagent 写 insight 文件失败时，返回完整 YAML 内容，由主线程代写
- 主线程写入也失败 → 等待 10 秒重试一次
- 连续失败 2 次 → 将 URL 移到 `failed_urls`，继续下一批
- HackerOne 403/404 由 subagent 自行处理，标记为 skipped

## 新会话恢复

新会话只需执行：
1. 下载上一次的 zip 解压到工作区
2. 阅读本文件并执行（步骤 2 的幂等恢复会自动处理中途崩溃的残留状态）

state/task_state.yaml 中保存了全部进度，无需手动传递状态。
