# Subagent 单批学习指令

你负责处理分配给你的 5 篇 HackerOne 报告。严格遵守以下流程。

## 准备

1. 读 `.claude/skills/learn-writeup/SKILL.md` 了解 schema 和核心铁律
2. 读 `knowledge/insights/README.md` 了解 phase 列表和去重规则（approach 去重）

## 对每篇报告（5 篇依次处理，每篇间隔 3 秒）

3. 用 `fetch_url` 抓取，优先 `.json` 端点（如 `https://hackerone.com/reports/123456.json`）
4. **不可访问处理**：403/404/空内容 → 跳过，加入 skipped 列表，不编造
5. **质量分流**：
   - 有 L3 内容（扑空/why_here_first/串链） → 全量提炼
   - 纯结果文（仅 PoC 无思维过程） → 看能否补 case 到已有 insight，否则跳过
6. **去重**：对照传入的 approach ID 列表，approach 命中已有 → 补 case（编辑已有文件的 cases 字段），不新建
7. **可提炼的**直接写入文件 `knowledge/insights/<phase>/<ID>.yaml`，schema 如下：

```yaml
name: "思路名称（描述判断，不是漏洞类）"
id: "大写蛇形"
applicable: "whitebox / blackbox / both"
phase: "recon/auth/authz/input/logic/chain/supply-chain"
also_phases: []
tags: [...]
source: "报告 URL"
observation: "(原文: \"...\") 或 未叙述（仅结果）"
hypothesis: "(原文: \"...\") 或 未叙述（仅结果）"
action_result: "(原文: \"...\")"
why_here_first: "(原文: \"...\") 或 未叙述（仅结果）"
chaining: "N/A 或描述"
approach: "一句话打法（去重键）"
reasoning_chain:
  - "问：..."
  - "如果...则..."
vuln_root: "一句话"
transferable_to: [...]
cases:
  - url: "..."
    note: "..."
```

## 反编造锚定（核心铁律）

- observation/hypothesis/why_here_first 必须引用原文：`(原文: "...")`
- 原文没叙述思考过程的，写 `未叙述（仅结果）`
- **绝对禁止脑补**——宁可标注"未叙述"也不要编造

## 重要：不要写 articles.yaml

**禁止直接编辑 `knowledge/insights/articles.yaml`**——该文件由主线程串行写入，避免并发冲突。
你需要在返回摘要中附带 articles.yaml 条目内容，由主线程统一追加。

## 写入失败处理

- 如果 write_file 报错（如 Pod 创建失败），等待 5 秒后重试一次
- 仍然失败 → 将完整 YAML 内容放在返回摘要中，由主线程代写

## 返回格式（严格遵守）

```
摘要：完成X篇，新增Y条insight[ID1,ID2,...]，Z篇不可访问[url1,url2,...]，补case到[ID3,ID4]
写入失败需主线程代写：无 / [文件路径和完整YAML内容]
---articles_yaml_entries---
  - url: "报告URL"
    title: "标题"
    learned_date: "当天日期"
    quality: "评级+理由"
    produced_insights: [ID列表]
    added_cases_to: [ID列表]

  - url: "第二篇URL"
    ...
```

摘要之外，只返回 articles.yaml 条目。不要返回完整 insight YAML 内容（除非写入失败需要代写）。不要返回分析过程。
