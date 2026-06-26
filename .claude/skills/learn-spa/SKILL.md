---
name: learn-spa
description: 从 CVE/Advisory 文章提炼可迁移的安全推理模式（SPA），沉淀进 knowledge/security/spa/ 目录。用户给出文章 URL 或粘贴正文时触发。
---

# learn-spa：CVE/Advisory 提炼安全推理模式

把一篇 CVE 报告或安全公告提炼为 **SPA（安全推理模式）**，
沉淀"看到什么该怀疑什么、怎么验证"的推理过程。严格遵循 CLAUDE.md 第 2-7 节。

## 适用来源

CVE 详情页、GitHub Security Advisory、NVD、漏洞研究博客中的技术分析。
**不适用于** writeup 叙事类文章（那些用 learn-writeup 提炼 L3 insight）。

区分标准：文章的核心是"漏洞是什么 + 怎么修"→ learn-spa；
文章的核心是"我怎么找到的 + 扑空了几次"→ learn-writeup。

## 核心铁律

1. **提取模式，不是细节**：不提取特定 payload 或复现步骤，提取可迁移的推理模式
2. **事实不可改**：evidence 中的 rootCause/fix 从原文提取，不主观改写
3. **不编造**：没有证据支撑的迁移场景不写入 transferableTo
4. **白盒黑盒分开**：verify 内白盒和黑盒各自独立
5. **技术细节准确**：协议行为引用 RFC，框架行为注明版本号

## 执行流程

### 步骤 1：抓取文章

- 优先使用 fetch_url 获取文章内容
- GitHub Advisory/NVD 等结构化页面可直接解析
- 抓不到原文就停止，不凭记忆提炼

### 步骤 2：提取事实

从原文中提取以下字段，文章没提到的写 unknown：

```yaml
evidence:
  - id: "CVE 编号"
    source: "原文 URL"
    product: "受影响产品"
    rootCause: "根因（原文描述，不改写）"
    fix: "修复方式"
    learned: "额外学到的（标注依据）"
```

### 步骤 3：判断归属

1. **选域**：这个漏洞主要涉及哪个安全域？
   - 能不该能登录 → auth
   - 能看/做不该看/做的 → authz
   - 输入被当成代码执行 → input
   - 业务规则被违反 → logic
   - 域名不在现有目录中 → 新建域目录

2. **归入已有还是新建**：
   - 先读目标域目录下已有的 SPA 文件列表
   - 把本漏洞根因去掉产品名概括成一句话
   - 与已有 SPA 的 vulnRoot 对比
   - 根因一致 → 追加 evidence 到已有 SPA
   - 根因不同 → 新建 SPA 文件
   - 犹豫不决 → 新建（合并比误归代价低）
   - **必须给出判断理由**

### 步骤 4：填充思维链

按 CLAUDE.md 第 2 节的 SPA 结构填充：

```yaml
observe:    # 可观测信号（不依赖源码）
infer:      # 开发者的假设及薄弱点
question:   # 挑战方法（标注 priority + effort）
verify:     # 白盒/黑盒验证步骤
extend:     # 确认后在当前域内延伸
```

**填充指引：**
- observe.signals：反问"如果我不知道这个漏洞，能从页面/响应看到什么让我起疑？"
- infer.assumptions：从 rootCause 反推"开发者假设了什么但实际不成立"
- verify.whitebox：从代码位置提取 grep 目标
- verify.blackbox：设计请求/响应对，每步含 action/expectedResult/onMatch/onMismatch
- extend：从修复方式推导"同域内还有哪里可能有类似问题"

### 步骤 5：域内发散（举一反三）

在步骤 4 的基础上，基于当前域的认知做合理延伸。
这一步的目的是让学到的知识不局限于文章本身，而是能迁移到同域的其他场景。

**发散规则：**
1. **只在当前域内发散**——不跨域
2. **每条发散必须有推导链**——从哪条事实出发、经过什么推理、得出什么结论，三者缺一不可
3. **标注来源**——区分"文章原文"和"域内推导"，用 `(原文)` 和 `(推导: 依据xxx)` 标注
4. **质量标准：举一反三**——从一个具体漏洞推导出同域内的同类问题，而不是天马行空
5. **宁缺毋滥**——推导链不成立的不写入，空着比编造好

**发散方向（按优先级）：**

1. **同域内的同类根因**：这个漏洞的根因模式，在当前域的其他功能里是否也可能存在？
   - 示例：文章说"首用户注册有 TOCTOU" → 推导"同域内密码重置流程是否也有先查后写的 TOCTOU？"
   - 推导链：首用户注册的 TOCTOU 根因是"先查条件再执行操作" → 密码重置也是"先查 token 有效再执行重置" → 同类根因
   
2. **已有 SPA 之间的关联**：新学的事实是否补强了当前域内已有的某个 SPA？
   - 示例：本文提到"signup 修了但 LDAP/OAuth 没修" → 已有 `emptyCredentialAuthBypass` 也涉及 LDAP 路径 → 两者都指向"多认证路径安全不一致"
   
3. **修复方式的反向推导**：文章描述的修复方式，暗示了什么其他风险？
   - 示例：修复用"先插后查" → 推导"如果数据库隔离级别配置不当，先插后查也可能失败"

**发散产出写入 extend 字段，每条标注推导依据：**
```yaml
extend:
  - check: "密码重置流程是否也有先查后写的 TOCTOU"
    reasoning: "(推导: 首用户注册 TOCTOU 的根因是先查条件再操作，密码重置的 token 校验流程结构相同)"
  - check: "同一应用其他认证路径是否同步了安全修复"
    reasoning: "(原文: signup_handler 修了但 LDAP/OAuth 没修，说明修复未全局排查)"
```

### 步骤 6：补充元数据

```yaml
id: "camelCase"                # == 文件名，驼峰命名
name: "中文描述名"
applicable: "whitebox / blackbox / both"
domain: "安全域"
severity: "critical / high / medium / low"
priority: "P1 / P2 / P3"
accessRequired: "unauthenticated / lowPrivilege / admin"
vulnRoot: "一句话漏洞本质"
prerequisite: "前置条件"
practicalNotes: "实战注意事项"
transferableTo: ["迁移场景"]
```

### 步骤 7：审计并写入

- 文件落位：`knowledge/security/spa/<domain>/<id>.yaml`
- 文件名 = id，驼峰命名
- 走 CLAUDE.md 第 7 节审计
- 运行 `python3 tools/validate.py` 确认 0 ERROR
- 如果新建了域目录，更新 INDEX.yaml 中的触发规则

## 输出给用户

提炼完汇报：新建了哪个 SPA / 追加了 evidence 到哪个已有 SPA、
归属域、severity、关键发现。不要假装提炼出了原文没有的东西。
