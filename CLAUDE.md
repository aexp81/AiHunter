# Security Skills - 项目说明与漏洞学习规范

## 项目目标

用 AI 辅助渗透测试工作，从真实漏洞报告中提炼可迁移的挖洞思维，沉淀为结构化模式库，在后续工作中直接调用。

## 知识库结构

```
AiHunter/（仓库根）
├── README.md                              #   项目入口（产品是什么 / 两库怎么查 / 流水线怎么跑）
├── CLAUDE.md                              #   本文件：项目说明 + 漏洞学习规范
├── BACKLOG.md                             #   长期任务/缺陷清单（持续迭代）
├── knowledge/                             # ★ 知识产物（产品本体，长期沉淀+被检索）
│   ├── security/                          #   SPA 执行架构（安全推理模式）
│   │   ├── INDEX.yaml                     #     触发索引（每次测试必加载）
│   │   ├── spa/                           #     SPA 模式库（按域分目录，按需加载）
│   │   │   ├── auth/                      #       认证域
│   │   │   ├── authz/                     #       授权域
│   │   │   ├── input/                     #       输入处理域
│   │   │   ├── logic/                     #       业务逻辑域
│   │   │   ├── local/                     #       本地提权域
│   │   │   └── ...                        #       域随学习动态新增
│   │   ├── summaries.yaml                 #     测试总结（每次测试收尾追加）
│   │   ├── cases/                         #     CVE案例库（不加载进上下文，按需查询）
│   │   │   └── blackbox-cases.yaml
│   │   └── anchor-traps/                  #   ★ AI实测失败记录（强制检查，与 INDEX 一起加载）
│   │       └── anchor-traps.yaml
│   └── insights/                          #   L3 挖洞导航思路库（writeup 提炼，按 phase 分目录）
│       ├── INDEX.yaml                      #   ★检索入口：自动生成的 approach 目录（tools 生成，勿手改）
│       ├── README.md
│       ├── articles.yaml
│       └── <phase>/<ID>.yaml              #     recon/auth/authz/input/logic/chain/supply-chain
├── pipeline/                              # ★ 知识生产/审计流水线（"机器"，不是知识本身）
│   ├── BATCH_ORCHESTRATOR.md              #     主线程批量学习编排
│   ├── batch_learn.md                     #     subagent 单批学习指令
│   ├── AUDIT_FRAMEWORK.yaml               #     模式质量审计框架 + audit_log
│   └── KNOWN_ISSUES.md                    #     已知平台问题与规避
├── state/                                 # ★ 流水线运行态（git 跟踪，与知识分离）
│   ├── task_state.yaml                    #     批量学习进度（断点恢复用）
│   └── current_ids.txt                    #     approach 去重缓存（可由 knowledge/insights/ 再生）
├── tools/                                 #   仓库工具（build_insights_index.py 生成索引 / validate.py 校验铁律）
├── reports/                               #   黑盒报告输出
└── .claude/skills/learn-writeup/          #   从 writeup 提炼 L3 思路的 skill
```

## 测试执行规则（SPA 架构）

### 每次测试开始时必须加载的文件
1. `knowledge/security/INDEX.yaml` —— 识别攻击面，匹配对应 SPA 文件路径
2. `knowledge/security/anchor-traps/anchor-traps.yaml` —— 打断锚定，避免重蹈覆辙
3. 按 INDEX.yaml 的触发规则，加载 2-3 个对应 SPA 文件

**绝对不要** 全量加载 spa/ 目录，只加载当前目标需要的 SPA。

### SPA 执行流程（思维链）
加载 SPA 文件后，按思维链 5 步顺序执行：
1. **observe** — 逐条验证 signals 是否与当前目标匹配
2. **infer** — 理解开发者的假设和薄弱点
3. **question** — 按 priority/effort 选择挑战目标
4. **verify** — 根据场景选白盒或黑盒路径，逐条执行验证步骤
5. **extend** — 确认漏洞后在当前域内寻找关联问题

不允许跳过任何一步。这是防止 AI 被当前理解框架锚定的核心机制。

### 侦查/选打法阶段检索 insights（L3 导航库）
- 加载 `knowledge/insights/INDEX.yaml`（自动生成的 approach 目录），按相关 phase **整段过一遍**，命中后再拉取 `<phase>/<ID>.yaml` 全文。
- 不可纯关键字匹配（见 insights/README 的 C2）。INDEX 由 `tools/build_insights_index.py` 生成，新增 insight 后需刷新（`python3 tools/build_insights_index.py`）。

### anchor-traps 的使用
每次测试结束后，如果发现了"AI 之前跳过了某个检查"，必须在 `knowledge/security/anchor-traps/anchor-traps.yaml` 里新增一条记录，包含：
- 被什么锚定（anchor）
- 跳过了什么检查（skipped_check）
- 为什么跳过（reason）
- 对应的强制检查（forced_checks）

### cases 的使用
`cases/` 目录只在写报告时查阅，**不加载进测试上下文**。

### 测试总结（强制收尾步骤）

每次测试结束后，必须在 `knowledge/security/summaries.yaml` 追加一条总结：

```yaml
- target: "目标标识"
  date: "YYYY-MM-DD"
  hits:
    - "SPA名 → 结果"
  misses:
    - "哪个信号没命中，为什么"
  newInsight: "一句话，这次测试学到的新东西"
```

**规则：**
- 每个字段一句话，不写段落
- 不写总结不算测完
- newInsight 是直觉的种子，提炼到最精炼的一句话

---

## 漏洞学习规范

### 1. 提取目标：模式，不是细节

**不提取：**
- 特定 CVE 的 payload 或复现步骤
- "这个 API 有 XXX 漏洞"的描述

**提取：**
- 可迁移到其他系统的攻击模式
- 挖洞者的推理过程（为什么去看这里）
- 在新目标上识别同类漏洞的判断方法

---

### 2. SPA 思维链结构（替代 reasoning_chain）

SPA 不使用 reasoning_chain 平铺清单，而是按思维过程分 5 个阶段组织：

```yaml
# observe — 可观测信号（不依赖源码）
observe:
  signals:
    - indicator: "登录页面含 LDAP/企业账户/域账户选项"
      observableAt: "登录表单 UI 或接口文档"

# infer — 开发者的假设
infer:
  assumptions:
    - assumption: "应用层在 LDAP bind 前已验证 password 非空"
      weakness: "RFC 4513 §5.1.2：空密码触发 Unauthenticated Bind，不是失败"

# question — 挑战假设
question:
  challenges:
    - target: "应用层是否真的做了非空校验"
      method: "提交 password='' 或省略 password 字段"
      priority: "high"        # high / medium / low
      effort: "low"           # low / medium / high

# verify — 验证步骤（白盒/黑盒分开）
verify:
  blackbox:
    - action: "POST login {account:'admin', password:''}"
      expectedResult: "401 或错误信息"
      onMatch: "有非空校验，此路不通"
      onMismatch: "返回 token → 认证绕过确认"
  whitebox:
    - grep: "ldap|simple_bind|bind_s|ldap3"
      reviewPoint: "LDAP 初始化和 bind 调用位置"
    - grep: "if not password|len(password)|password == ''"
      reviewPoint: "bind 调用前是否有非空校验"
    codeReviewFocus: "找到 bind() 调用，往上追踪 password 参数的验证逻辑"

# extend — 确认后在当前域内延伸
extend:
  - check: "同接口其他参数能否省略（account 字段）"
    reasoning: "同类校验缺失可能在多个字段同时存在"
```

**强制规则：**
- observe.signals 的每条指标必须不依赖源码就能观测到
- verify.whitebox 每个 grep 必须是可执行的搜索命令
- verify.blackbox 的 action 必须是具体的请求/操作，不能是"检查代码"
- 不允许在黑盒步骤中使用需要源码的信息

---

### 3. 白盒 vs 黑盒在 verify 内分开

SPA 通过 `applicable` 字段标注适用场景：
- **blackbox**：只有 verify.blackbox 部分
- **whitebox**：只有 verify.whitebox 部分
- **both**：两者都有

白盒 verify 每个 grep 必须是实际可运行的命令。黑盒 verify 禁止引用源码信息。

---

### 4. SPA 必填字段

```yaml
# 路径：knowledge/security/spa/<domain>/<ID>.yaml
# 文件名 = id，大写蛇形命名

id: "LDAP_NULL_PASSWORD"          # 必填，== 文件名
name: "认证接口空密码绕过"          # 必填
applicable: "both"                 # 必填：whitebox / blackbox / both
domain: "auth"                     # 必填：安全域，随学习动态新增
severity: "critical"               # 必填：critical / high / medium / low
priority: "P1"                     # 必填：P1=高危低门槛 / P2=有条件 / P3=特定环境
accessRequired: "unauthenticated"  # 必填：unauthenticated / lowPrivilege / admin

observe: {}                        # 必填
infer: {}                          # 必填
question: {}                       # 必填
verify: {}                         # 必填（至少有 blackbox 或 whitebox 之一）

vulnRoot: ""                       # 必填：漏洞本质（一句话）
prerequisite: ""                   # 选填：前置条件
practicalNotes: ""                 # 选填：实战中的坑
transferableTo: []                 # 选填：可迁移场景
extend: []                         # 选填：确认后的延伸检查
evidence: []                       # 选填：真实案例证据
```

**安全域命名规范：**
- 域名使用小写英文短词，与 insights 的 phase 对齐
- 新建域必须在 INDEX.yaml 中注册触发规则
- 域不预设固定列表，随学习动态新增，但命名必须专业精准

---

### 5. 技术细节要准确，不能想当然

已发现的典型错误，后续避免：

| 错误 | 正确 |
|---|---|
| "LDAP 空密码 = 匿名绑定" | "LDAP 空密码触发 Unauthenticated Bind（RFC 4513 §5.1.2），不同于匿名绑定" |
| "现代浏览器会 Content Sniffing" | "跨域受 CORB 保护；同源仍会 sniff，除非有 nosniff header" |
| "LDAP 服务器大多数默认允许 Unauthenticated Bind" | "OpenLDAP 2.5+ 和 AD Windows Server 2019+ 默认拒绝，必须确认目标版本" |
| "multer 默认使用随机文件名（default_safe: true）" | "multer DiskStorage 默认使用原始文件名，default_safe: false" |
| IDOR 只测 GET | "必须测 GET / DELETE / PUT / PATCH，以及子资源路径" |
| Semgrep pattern-not 直接匹配函数调用 | "pattern-not 多行格式，区分赋值和直接使用" |

**规则：**
- 涉及协议行为（LDAP / OAuth / HTTP）必须引用 RFC 或官方文档
- 涉及框架默认行为必须注明版本号，且查官方文档确认
- 浏览器行为必须区分：同源 vs 跨域，现代版本 vs 旧版本
- 所有代码示例（grep / Semgrep）必须在真实环境验证后再写入

---

### 6. 白盒 SPA 额外规则

白盒 SPA（applicable: whitebox 或 both）的 verify.whitebox 中：
- 每个 grep 必须是可执行的搜索命令
- reviewPoint 说明搜到后看什么
- codeReviewFocus 说明审计的整体焦点

禁止只有文字描述没有命令（如"检查代码"）。

---

### 7. 审计规则（每次生成或更新 SPA 后必须执行）

每次添加新 SPA 或修改现有 SPA 后，按以下顺序自我检查：

1. **格式检查**：运行 `python3 tools/validate.py`（自动校验必填字段 / id == 文件名 / id 唯一 / 白盒 verify 含 grep），ERROR 必须清零
2. **完整性检查**：对照 pipeline/AUDIT_FRAMEWORK.yaml 的 common_omissions 逐项确认
3. **技术准确性**：涉及协议/框架/浏览器行为的描述是否有依据？
4. **记录**：将审计结果追加到 pipeline/AUDIT_FRAMEWORK.yaml 的 audit_log

---

### 8. 提炼"挖洞思路"：CVE 与 writeup 用不同镜头

**核心认知：漏洞知识分三层，价值递增。**

| 层 | 内容 | 来源 |
|---|---|---|
| L1 验证链 | 确认一个可疑点的步骤（reasoning_chain） | CVE 能学到 |
| L2 心智盲区 | 开发者的什么假设被违反（vuln_root） | CVE 能学到 |
| L3 导航过程 | 为什么先看这里、扑空怎么转向、怎么串链 | **CVE 学不到，靠 writeup** |

**CVE 的天花板**：CVE 是"已被找到的洞"，只记录结果，不记录猎人怎么找到它。
从 CVE 提炼会天然偏向"漏洞类目录 + 验证清单"，学不到陌生目标上的导航与直觉。
→ 已学完的 CVE 库到此为止，不再深挖单一产品。

**学 HackerOne writeup 的强制镜头（不要套 CVE 的漏洞类 schema）：**

writeup 是叙事，价值在 L3。若按漏洞类压扁，刚好丢掉最想要的思路。
必须按"决策三元组"提炼，而不是按漏洞类归档：

```yaml
- name: "思路名称（描述判断，不是漏洞类）"
  id: "INSIGHT_ID"
  applicable: "whitebox / blackbox / both"

  # —— L3 核心：导航过程（CVE 学不到的部分）——
  observation:    # 猎人看到什么异常 / 什么让他起疑
  hypothesis:     # 据此猜测哪里可能有问题
  action_result:  # 做了什么 → 成/败；失败后怎么转向（保留扑空的路）
  why_here_first: # 为什么先看这里（优先级/直觉的来源）
  chaining:       # 单个低危怎么和别的组合成高危（无则写 N/A）

  # —— 沿用现有字段 ——
  reasoning_chain: # 落地为可执行检查清单（问句形式，规则同第2节）
  vuln_root:       # 被违反的开发者心智假设（一句话）
  transferable_to: # 可迁移到哪些系统/场景
  cases:           # writeup 链接 / 报告引用
```

**强制规则：**
- `observation / hypothesis / why_here_first` 三项必填——这是 writeup 区别于 CVE 的价值，缺了就等于又抽成了漏洞类清单
- `action_result` 必须保留"失败的尝试和转向"，不要只写最终成功路径（负空间才是导航经验）
- 按"判断/思路"命名，禁止用漏洞类（如"IDOR"）做 name
- 提炼后仍走第 7 节审计流程

---

### 9. 网页抓取规则（工具选择）

**强制规则：**
- 抓取任何网页（公众号 / 博客 / Medium / HackerOne）**必须优先使用 playwright MCP**，不要用 WebFetch。
- WebFetch 对微信公众号、需要 JS 渲染的页面、有安全策略拦截的域名会直接失败，浪费一次工具调用。
- 正确顺序：playwright `browser_navigate` → `browser_snapshot` 取文本 → 失败时告知用户粘贴正文。
- WebFetch 仅用于确定是纯静态 HTML 的场景（如 GitHub raw 文件、纯文本 API）。

**典型高频错误（已发生）：**

| 错误行为 | 正确行为 |
|---|---|
| 对 `mp.weixin.qq.com` 用 WebFetch，收到网络限制错误后才切换 | 直接用 playwright，跳过 WebFetch 尝试 |
| 先尝试 WebFetch，失败后再切换，浪费一轮交互 | 见到公众号/博客 URL 即默认 playwright |
