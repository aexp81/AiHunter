# Security Skills - 项目说明与漏洞学习规范

## 项目目标

用 AI 辅助渗透测试工作，从真实漏洞报告中提炼可迁移的挖洞思维，沉淀为结构化模式库，在后续工作中直接调用。

## 知识库结构

```
security/                              # ★ 新架构（三层分离）
├── INDEX.yaml                         #   Layer 0：触发索引（每次测试必加载，< 60行）
├── patterns/
│   ├── blackbox/                      #   Layer 1：黑盒执行清单（按需加载，每文件<40行）
│   │   ├── auth/                      #     AUTH_PARAM_COMPLETENESS（★新增）
│   │   │                              #     LDAP_NULL_PASSWORD, DEFAULT_CREDENTIAL
│   │   ├── authz/                     #     IDOR, MASS_ASSIGN, PARAMETER_BINDING
│   │   │                              #     PERMISSION_LEVEL_CONFUSION, AUTHZ_BRANCH_GAP
│   │   │                              #     INDIRECT_OBJECT_REF
│   │   ├── input/                     #     PATH_TRAVERSAL, SSRF, STORED_XSS
│   │   │                              #     FILE_EXTENSION_XSS
│   │   ├── local/                     #  ★新增：本地/桌面/二进制提权（5个模式）
│   │   │                              #     WRITABLE_LOAD_PATH_HIJACK, PRIVILEGED_FILE_OP_TOCTOU
│   │   │                              #     LOCAL_IPC_PEER_TRUST, SANDBOX_POLICY_COVERAGE_GAP
│   │   │                              #     CLIENT_SIDE_POLICY_LOCAL_BYPASS
│   │   └── universal/                 #     UNAUTH_ENDPOINT
│   └── whitebox/                      #   Layer 1：白盒执行清单（含grep命令）
│       ├── auth/ authz/ input/
│       ├── logic/ universal/
│       └── local/                     #  ★新增：本地/二进制提权白盒审计（含MEMORY_CORRUPTION_PRIMITIVE_AUDIT）
├── cases/                             #   Layer 2：CVE案例库（不加载进上下文，按需查询）
│   └── blackbox-cases.yaml
├── anchor-traps/                      #   ★ 新增：AI实测失败记录（强制检查）
│   └── anchor-traps.yaml
├── insights/                          #   L3 挖洞导航思路库（writeup 提炼）
│   ├── README.md
│   ├── articles.yaml
│   └── <phase>/<ID>.yaml
├── .claude/skills/learn-writeup/      #   从 writeup 提炼 L3 思路的 skill
├── openwebui-patterns-blackbox.yaml   #   旧文件（已迁移，保留作参考）
├── openwebui-patterns-whitebox.yaml   #   旧文件（已迁移，保留作参考）
└── CLAUDE.md                          #   本文件
```

## 测试执行规则（新架构核心规则）

### 每次测试开始时必须加载的文件
1. `security/INDEX.yaml` —— 识别攻击面，找到对应模式文件路径
2. `security/anchor-traps/anchor-traps.yaml` —— 打断锚定，避免重蹈覆辙
3. 按 INDEX.yaml 的触发规则，加载 2-3 个对应模式文件

**绝对不要** 全量加载 patterns/ 目录，只加载当前目标需要的模式。

### 强制执行规则
每个模式文件的 `reasoning_chain` 必须逐条执行，**不允许因为"已经理解了这个接口"而跳过任何一条**。

这是防止 AI 被当前理解框架锚定的核心机制。

### anchor-traps 的使用
每次测试结束后，如果发现了"AI 之前跳过了某个检查"，必须在 `anchor-traps/anchor-traps.yaml` 里新增一条记录，包含：
- 被什么锚定（anchor）
- 跳过了什么检查（skipped_check）
- 为什么跳过（reason）
- 对应的强制检查（forced_checks）

### cases 的使用
`cases/` 目录只在写报告时查阅，**不加载进测试上下文**。

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

### 2. reasoning_chain 必须是检查清单，不是结果描述

**错误写法（描述漏洞已经存在）：**
```yaml
reasoning_chain:
  - "filename 来自用户请求"
  - "路径拼接 f'{UPLOAD_DIR}/{filename}'"
  - "没有 os.path.basename()"
```

**黑盒错误写法（命令式陈述）：**
```yaml
blackbox_reasoning:
  - "步骤1：正常上传文件"
  - "步骤2：尝试穿越 payload"
  - "步骤3：观察响应"
```

**正确写法（面对未知目标时能执行的步骤）：**
```yaml
# 白盒版本
reasoning_chain:
  - "问：路径中是否包含用户可控输入？"
  - "白盒：grep -rn 'open(' <file> | grep 'filename'"
  - "问：拼接前有路径规范化吗？(basename / resolve / abspath)"
  - "如果：包含用户输入 + 无规范化 → 漏洞存在，构造 payload 验证"

# 黑盒版本
blackbox_reasoning:
  - "问：正常上传后文件 URL 是什么格式？"
  - "问：将 filename 改为 ../../tmp/test.txt 后，响应码是 200 还是 400？"
  - "如果返回 200，问：能否从其他接口读取 /tmp/test.txt？"
```

**强制规则：**
- 禁止使用"步骤X："开头（自动化检查会拒绝）
- 每个判断必须用"问："或"如果...则..."开头
- 白盒版本每个"问："后必须跟"白盒：grep/Semgrep 命令"

---

### 3. 白盒 vs 黑盒必须分开

每个模式必须明确标注适用场景：

- **白盒专用**：依赖读源码（如"看代码注释是否提到已修复"）
- **黑盒专用**：依赖行为观察（如"发送 payload 观察响应码"）
- **两者通用**：逻辑可独立适用于两种场景

模式2（Fix Inconsistency）是典型白盒专用，黑盒无法使用，不要放入黑盒库。

---

### 4. 每个模式必须包含的字段

```yaml
- name: "模式名称"
  id: "PATTERN_ID"
  applicable: "whitebox / blackbox / both"

  trigger:            # 什么时候触发这个模式
  reasoning_chain:    # 检查清单（问句形式）
  access_required:    # 需要什么访问权限
  prerequisite:       # 必要的前置条件
  practical_notes:    # 实战中的坑和补充
  verify:             # 如何验证漏洞存在
  vuln_root:          # 漏洞本质（一句话）
  transferable_to:    # 可迁移到哪些系统/场景
  cases:              # 真实案例引用
```

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

### 6. 白盒模式额外规则

白盒模式的每个 reasoning_chain 步骤必须附带可执行的搜索命令：

```yaml
# 正确示例
reasoning_chain:
  - "问：上传文件名是否参与路径构造？"
  - "白盒：grep -rn 'filename' --include='*.py' | grep 'open\\|write\\|join'"
  - "如果命中：查看上下文，判断是否有 basename 或路径规范化"
```

禁止只有文字描述没有命令：
```yaml
# 错误示例
reasoning_chain:
  - "问：上传文件名是否参与路径构造？(检查代码)"  # ❌ "检查代码"不是可执行步骤
```

---

### 7. 审计规则（每次生成或更新模式后必须执行）

每次添加新模式或修改现有模式后，按以下顺序自我检查：

1. **格式检查**：reasoning_chain 是否全部是问句？白盒是否有 grep 命令？
2. **完整性检查**：对照 AUDIT_FRAMEWORK.yaml 的 common_omissions 逐项确认
3. **技术准确性**：涉及协议/框架/浏览器行为的描述是否有依据？
4. **字段完整性**：transferable_to / access_required / prerequisite 是否都有？
5. **记录**：将审计结果追加到 AUDIT_FRAMEWORK.yaml 的 audit_log

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
