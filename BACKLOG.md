# AiHunter Backlog（长期任务/缺陷清单）

> 本文件是项目的**活清单**，持续更新迭代。每完成/变更一项，更新其状态并在末尾「迭代日志」追加一行。
> 严重度：🔴P0 阻断价值 / 🟡P1 重要 / 🟢P2 优化 / ⚪P3 整洁。
> 状态：`todo` / `doing` / `done` / `blocked` / `wontfix`。

## 状态总览

| ID | 严重度 | 状态 | 标题 |
|---|---|---|---|
| T-001 | 🔴P0 | done | insights 是死库：241 条无检索入口、INDEX 零引用，测试时无法调用 |
| T-002 | 🔴P1 | done | "自动化检查"是空头支票：无 lint/CI/hook，所有铁律全靠模型自觉 |
| T-003 | 🔴P1 | todo | 反馈环空转：anchor-traps 仅 3 条，"每次测试必新增"未落实 |
| T-004 | 🟡P2 | todo | 大单文件 + 串行写瓶颈：articles.yaml 5638 行 / task_state 99K |
| T-005 | 🟡P2 | todo | 去重键脆弱：approach 自由文本 + 扁平 ID 列表人肉判重，规模化必漏 |
| T-006 | 🟢P3 | todo | bb/wb 双份模式维护耦合（validate 已做 id/文件名一致性，trigger/vuln_root 对齐待补） |
| T-007 | 🟢P3 | todo | 硬编码计数漂移：CLAUDE/README/audit_log 写死数字易过期 |
| T-008 | 🟢P3 | todo | case 双存储：cases/ 集中库 vs insights 内联 cases 字段 |
| T-009 | ⚪P3 | todo | reasoning_chain 格式漂移：126 条 WARN（行首非 问/如果，多为命令式"测试：/拦截："） |

---

## 任务详情

### T-001 🔴P0 — insights 死库，无检索入口  ✅ done (2026-06-25)
- **问题**：`knowledge/security/INDEX.yaml` 对 insights 引用数 = 0；241 条 L3 思路测试时无加载路径，只有 44 个 pattern 能被路由。`insights/README` 自己写"攒到 50 条建 INDEX + 检索 skill"，现已 241 条仍未建。
- **影响**：生产投入最大的资产 ROI≈0，生产侧与消费侧数据子图不连通。
- **验收**：① 有 `tools/build_insights_index.py` 能从 241 个文件自动生成 `knowledge/insights/INDEX.yaml`（按 phase 分组，每条 id→approach 一行）；② INDEX 条数==实际文件数；③ CLAUDE.md 消费流规则写明"测试/规划时加载 insights/INDEX 并按 phase 整段过一遍"；④ 结构树/README 同步。
- **不做**：暂不建独立检索 skill（拆到后续）；不改 approach 去重机制（见 T-005）。

### T-002 🔴P1 — 铁律零自动化执行  ✅ done (2026-06-25)
- **问题**：全盘扫描无任何 .py/.sh/CI/hook，`.claude` 无 settings.json。CLAUDE.md 多处"自动化检查会拒绝步骤X"均为空话；`(原文:)` 反编造引用无人校验。
- **验收**：`tools/validate.py` 落地以下硬检查并可一键跑全库：reasoning_chain 全为问句（无"步骤X"/结果陈述）、白盒每个"问"后有 grep/Semgrep、必填字段完整、YAML 可解析、id 全局唯一、insights 三元组必填。退出码非 0 即失败，可挂 pre-commit。
- **依赖**：与 T-001 共用 `tools/` 基建。

### T-003 🔴P1 — 反馈环空转
- **问题**：anchor-traps 定义为防锚定核心机制、"每次测试必新增"，实际仅 3 条且同源一次实测。
- **验收**：明确触发与最小模板，降低记录门槛；考虑把 anchor-trap 与对应 pattern/insight 双向链接，让其在加载时自然浮现。需先攒真实测试数据，偏流程治理而非纯代码。

### T-004 🟡P2 — 大单文件 + 串行写瓶颈
- **问题**：articles.yaml 5638 行 195K、task_state 99K，单文件 + 主线程串行写，git diff/merge 噩梦，断点恢复需整文件重写。
- **验收**：评估拆分（按年月/phase 分片或改 append-only JSONL）；保持生产流水线幂等恢复不被破坏。

### T-005 🟡P2 — 去重键脆弱
- **问题**：去重键 approach 是自由文本，判重靠模型读 200+ 扁平 ID 列表，无语义比对，规模化漏判。
- **验收**：调研轻量语义/规范化去重（approach 规范化指纹或 embedding 近邻提示），先给"疑似重复"候选而非全靠模型扫列表。

### T-006 🟢P3 — bb/wb 双份模式耦合
- **问题**：PATH_TRAVERSAL/SSRF/IDOR/MASS_ASSIGN/所有 local 等在 blackbox、whitebox 各一份，内容不同但改一处易漏另一处。
- **验收**：一致性检查（同名模式 trigger/vuln_root 对齐），纳入 T-002 validate。

### T-007 🟢P3 — 硬编码计数漂移
- **问题**：CLAUDE/README/audit_log 写死 241/289/290 等数字，随增长过期。
- **验收**：计数由脚本生成/校验（T-001 的 INDEX 已带 counts，可作为单一真相源）。

### T-008 🟢P3 — case 双存储
- **问题**：pattern 案例集中在 `cases/blackbox-cases.yaml`，insights 案例内联在 241 个 `cases:` 字段，两套约定两处查。
- **验收**：明确两者定位边界，或统一引用规范，避免写报告两头找。

### T-009 ⚪P3 — reasoning_chain 格式漂移
- **问题**：validate.py 报 126 条 WARN，行首非 问/如果 的检查式（多为命令式 "测试："/"拦截："/"延伸测试："/"修改1：" 等），与 CLAUDE §2"每个判断用问句"有偏差。非阻断。
- **验收**：分批把命令式行改写为问句/条件式，逐步压低 WARN；或确认部分前缀（如"扩展："）合法后并入 validate 白名单。`--strict` 可在清零后启用为 CI 门禁。

---

## 迭代日志
- 2026-06-24：基于项目深度分析创建本清单（T-001~T-008）。启动 T-001。
- 2026-06-25：T-001 done —— 新增 `tools/build_insights_index.py`，生成 `knowledge/insights/INDEX.yaml`（241 条，按 phase 分组，含 counts 作计数单一真相源）；CLAUDE.md 消费流 + 两 README + insights/README 已接入并同步。`--check` 模式可供后续 CI（T-002）调用。
- 2026-06-25：T-001 收尾 —— 把 `python3 tools/build_insights_index.py` 接入 `pipeline/BATCH_ORCHESTRATOR.md` 收尾（步骤17，打包前），批量学完自动刷新索引。注：单篇 `learn-writeup` skill 路径仍手动刷新，待接。
- 2026-06-25：T-002 done —— 新增 `tools/validate.py`（ERROR 硬规则 + WARN 漂移提示），全库 0 ERROR/126 WARN；修复 `whitebox/input/PATH_TRAVERSAL.yaml` 的 id≠文件名（PATH_TRAVERSAL_FILE_OP→PATH_TRAVERSAL，顺带补 T-006 一处）；已接入 BATCH_ORCHESTRATOR 收尾(步骤17 先校验后建索引) + CLAUDE §7 格式检查指向脚本。新增 T-009 跟踪 126 条 WARN。
- 2026-06-25：清理 CLAUDE §7 —— 删除第4条「字段完整性」（与第1条 validate 自动校验重复，且点名的 transferable_to/access_required/prerequisite 在 44 个 pattern 中 0 使用），原第5条「记录」上提为第4条。
