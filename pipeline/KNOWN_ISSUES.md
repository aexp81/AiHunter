# 已知问题与规避策略

## 1. 沙箱 Pod 创建失败（2026-06-25 发现）

**错误信息**：
```
Failed to create sandbox Pod: pods "sa-sandbox-xxx" is forbidden:
pod rejected: RuntimeClass "gvisor" not found
```

**原因**：平台 Kubernetes 集群的 gVisor RuntimeClass 短暂不可用（节点调度/配置更新/资源不足），
导致所有文件读写操作失败。

**影响**：写入操作静默失败，不会产生半写入或损坏文件，但整批操作需要重做。

**规避策略**：
1. **分批写入**：不要一次并行写入 5+ 个文件，改为每次写 2-3 个，降低单次失败的重做代价
2. **写后立即验证**：每批写入后用 `yaml.safe_load()` 验证文件存在且可解析
3. **失败立即重试**：如果某批写入失败，等待 30 秒后重试一次；连续失败 2 次则暂停并通知用户
4. **最后统一校验**：全部写入完成后，用脚本一次性验证所有新文件的存在性和 YAML 语法

## 2. HackerOne 抓取速率限制

**问题**：短时间内并行抓取大量 HackerOne 报告可能触发人机验证（CAPTCHA）或 403。

**规避策略**：
1. **分批抓取**：每批最多 5 篇，批间等待 3-5 秒
2. **优先 JSON API**：使用 `reports/<id>.json` 端点而非 HTML 页面，API 限制通常更宽松
3. **失败降级**：HTML 页面 403 时尝试 JSON 端点；均失败则标记 deferred 而非反复重试
