---
name: learn-writeup
# [原始] description: 从任意来源的漏洞挖掘文章（HackerOne / 博客 / Medium / 公众号 / PDF 等）提炼可迁移的"挖洞思路"（L3 导航过程），按决策三元组锚定原文，去重后沉淀进 hunting-insights.yaml。用户给出文章 URL 或粘贴正文时触发。
description: 从任意来源的漏洞挖掘文章（HackerOne / 博客 / Medium / 公众号 / PDF 等）提炼可迁移的"挖洞思路"（L3 导航过程），按决策三元组锚定原文，去重后沉淀进 insights/<phase>/ 目录。用户给出文章 URL 或粘贴正文时触发。
---

# learn-writeup：漏洞文章思路提炼

把一篇漏洞 writeup 提炼成 **L3 挖洞思路**（为什么先看这里、扑空怎么转向、怎么串链），
而不是又一个漏洞类清单。严格遵循项目 CLAUDE.md 第 8 节的镜头。

## 适用来源

任意来源：HackerOne、个人博客、Medium、公众号、Twitter/X 长推、PDF、会议 slides、
GitHub writeup。不局限于某个平台。

## 核心铁律（违反即作废）

1. **读时套镜头，不是读完总结**：带着 `observation→hypothesis→action_result` 去读，
   边读边填。禁止读完先归一个"这是 IDOR/SSRF"再倒推。
2. **反编造锚定**：`observation / hypothesis / why_here_first` 每项必须能在原文找到对应
   句子。文章没叙述思考过程的，写 `未叙述（仅结果）`，**禁止脑补内心戏**。
3. **质量分流**：没有"扑空的路 / 为什么先看这里 / 串链"的纯结果文，**不强塞三元组**，
   降级为 case 挂到已有模式下。
4. **按思路命名，禁止用漏洞类做 name**（不要叫 "IDOR"，要叫"只读共享资源的状态按钮"）。
<!-- [原始] 5. **必做结构化分类**：每条 insight 必填 `phase`（取自 hunting-insights.yaml 的
   taxonomy.phase：recon/auth/authz/input/logic/chain）+ `tags`（自由标签）。
   学每篇前先读该文件的 taxonomy 与 articles 索引（防重复学习、保持分类一致）。 -->
5. **必做结构化分类**：每条 insight 必填 `phase`（合法值见 `insights/README.md`：
   recon/auth/authz/input/logic/chain/supply-chain）+ `tags`（自由标签）。
   学每篇前先读 `insights/README.md` 的分类与去重规则，以及 `insights/articles.yaml` 索引（防重复学习、保持分类一致）。

## 执行流程

### 步骤 1 抓取
- **必须优先使用 playwright MCP**（`browser_navigate` → `browser_snapshot` 取文本），
  不要用 WebFetch。WebFetch 对公众号、JS 渲染页、有安全策略拦截的域名会直接失败，
  浪费一次工具调用。
- WebFetch **仅用于**确定是纯静态 HTML 的场景（如 GitHub raw 文件、纯文本 API）。
- playwright 也失败时，请用户直接粘贴正文。
- 要求返回**原文文本**（后续锚定要用），不要只要摘要。
- 抓不到原文就**停止**，不要凭标题或记忆提炼。

### 步骤 2 质量分流
读完原文，回答：**这篇有没有写 扑空的路 / 为什么先看这里 / 怎么串链？**
- 有 → 进入步骤 3 全量提炼。
- 只有"发现 X 漏洞 + payload"无导航叙事 → 跳到步骤 5，作为 case 补到已有模式，
  并明确告诉用户"这篇是结果文，已降级为 case，未强提炼 L3"。

### 步骤 3 提炼（按 CLAUDE.md 第 8 节 schema）
对每条思路填写下列字段。L3 三项 + reasoning_chain 是重点：

```yaml
- name: "思路名称（描述判断，不是漏洞类）"
  id: "INSIGHT_<大写蛇形>"
  applicable: "whitebox / blackbox / both"
  source: "文章 URL 或来源描述"

  # L3 核心（每项后用 (原文: "...") 锚定；无叙述写 未叙述（仅结果））
  observation:    # 看到什么异常 / 什么让他起疑
  hypothesis:     # 据此猜哪里可能有问题
  action_result:  # 做了什么 → 成/败；失败后怎么转向（保留扑空的路）
  why_here_first: # 为什么先看这里（优先级/直觉来源）
  chaining:       # 低危怎么组合成高危（无则 N/A）

  reasoning_chain: # 落地为可执行检查清单（问句形式，遵守第2节规则）
  vuln_root:       # 被违反的开发者心智假设（一句话）
  transferable_to: # 可迁移到哪些系统/场景（具体，不能"所有Web应用"）
  cases:           # 文章链接 / 报告引用
```

锚定写法示例：
`observation: '导出功能的文件名直接回显在 Content-Disposition (原文: "the filename param was reflected...")'`

### 步骤 4 去重（写入前必做）
先读 `insights/articles.yaml`（这篇学过没）和相关 phase 目录下已有 insight，判断：
- **去重键是 `approach`（打法/导航路径），不是 vuln_root**（见 insights/README.md）。
- **approach 全新** → 在 `insights/<phase>/<ID>.yaml` 新建一个文件。
- **approach 已有** → 不新建，把本篇作为新 `case`（含 source）补进那条 insight，
  并在 articles.yaml 的 `added_cases_to` 登记。
- **approach 近似但导航路径不同** → 仍算新条目（宁可多一条，别合并掉 L3 差异）。
- 跨阶段思路：主阶段放目录，其余写 `also_phases` 字段。

### 步骤 5 审计并写入
- 文件落位：`insights/<phase>/<ID>.yaml`，一条一文件，文件名=id。
- 更新 `insights/articles.yaml`：登记 url/title/quality/produced_insights/added_cases_to。
- 走 CLAUDE.md 第 7 节审计：L3 三项是否锚定原文或标"未叙述"？reasoning_chain 全问句？
  必填字段（含 approach）齐全？yaml 能 safe_load？
- 审计结果追加到 AUDIT_FRAMEWORK.yaml 的 audit_log。

## 批量处理
用户一次给多篇：复用 CVE 批量学习的并行 subagent 模式——每个 subagent 啃一篇返回
结构化三元组，主控统一去重合并写入，避免重复劳动和条目冲突。

## 输出给用户
提炼完口头汇报：新增/增强了哪几条思路、哪些被降级为 case、哪些原文没叙述思考过程
（标注了"未叙述"）。不要假装提炼出了原文没有的导航经验。
