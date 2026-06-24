# AiHunter

AI 辅助渗透测试的**可迁移知识库**。从真实漏洞报告与 writeup 中提炼「挖洞思维」，
沉淀为结构化、可在新目标上直接调用的模式库与导航思路库。

> 完整的行为规范、字段定义与学习规则见 [`CLAUDE.md`](CLAUDE.md)。本文件只讲「有什么、放哪、怎么用」。

## 目录结构

```
knowledge/   ★ 知识产物（产品本体）
├── security/    三层执行架构：测试时按需加载的模式库
└── insights/    L3 导航思路库：writeup 提炼的「为什么先看这里」
pipeline/    知识生产/审计流水线（“机器”，不是知识本身）
state/       流水线运行态（进度、去重缓存；git 跟踪）
reports/     黑盒报告输出
tools/       仓库工具（build_insights_index.py 生成索引 / validate.py 校验格式铁律）
BACKLOG.md   长期任务/缺陷清单（持续迭代）
.claude/     learn-writeup skill
```

## 两个知识库，分别什么时候查

### `knowledge/security/` —— 三层执行架构（测试时调用）

按「攻击面 → 模式」路由，**测试现场**用。

| Layer | 路径 | 作用 | 是否加载进上下文 |
|---|---|---|---|
| 0 路由 | `security/INDEX.yaml` | 按攻击面类型找到要加载的模式文件 | ★ 每次测试必加载 |
| 1 清单 | `security/patterns/{blackbox,whitebox}/<类>/` | 逐条执行的 `reasoning_chain` 检查清单（黑盒 19 + 白盒 25） | 按 INDEX 触发，只载 2-3 个 |
| 2 案例 | `security/cases/blackbox-cases.yaml` | CVE 真实案例 | 仅写报告时查 |
| — 锚定 | `security/anchor-traps/anchor-traps.yaml` | AI 实测被锚定/漏检的记录 + 强制检查 | ★ 与 INDEX 一起加载 |

模式分类：`auth / authz / input / local / universal / logic`。

### `knowledge/insights/` —— L3 导航思路库（学习/复盘时积累，规划时查）

241 条「挖洞导航经验」，按**挖洞阶段（phase）**分目录，一条思路一个文件（文件名 = id）：

| phase | 条数 | phase | 条数 |
|---|---|---|---|
| authz | 87 | input | 33 |
| auth | 44 | logic | 23 |
| chain | 43 | recon | 8 |
| | | supply-chain | 3 |

与 security 的区别：security 是「确认一个可疑点的验证清单」（L1/L2），
insights 是「为什么先看这里、扑空怎么转向、怎么串链」（L3 导航过程）——CVE 学不到、靠 writeup。
去重键是 `approach`（打法），不是漏洞类。详见 [`knowledge/insights/README.md`](knowledge/insights/README.md)。

**检索入口**：`knowledge/insights/INDEX.yaml`（由 `tools/build_insights_index.py` 自动生成的 approach 目录）。测试/规划时加载它、按相关 phase 整段过一遍，命中后再拉全文；新增 insight 后跑一次脚本刷新。

## 流水线 `pipeline/`

批量从 writeup 提炼 insights 的「机器」：

- `BATCH_ORCHESTRATOR.md` —— 主线程编排（分批、并行 subagent、去重、断点恢复）
- `batch_learn.md` —— 单个 subagent 的处理指令
- `AUDIT_FRAMEWORK.yaml` —— 模式质量审计框架 + `audit_log`
- `KNOWN_ISSUES.md` —— 已知平台问题与规避

新增/手动学单篇 writeup 走 `.claude/skills/learn-writeup` skill（用户给 URL 或正文即触发）。

## 运行态 `state/`

- `task_state.yaml` —— 批量学习进度，用于跨会话断点恢复
- `current_ids.txt` —— approach 去重缓存，**可由 `knowledge/insights/` 重新生成**

## 快速上手

- **要测一个目标** → 读 `knowledge/security/INDEX.yaml` + `anchor-traps`，按攻击面加载对应模式，逐条执行。
- **要学一篇 writeup** → 触发 `learn-writeup` skill，提炼进 `knowledge/insights/<phase>/`。
- **要批量学** → 按 `pipeline/BATCH_ORCHESTRATOR.md` 执行。
- **新增 insight 后** → `python3 tools/build_insights_index.py` 刷新检索索引。
- **规则/字段定义** → 一律以 `CLAUDE.md` 为准。
