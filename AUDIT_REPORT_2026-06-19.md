# 安全模式库审计与修复记录
# 第二次审计：2026-06-19

## 审计总结

| 文件 | 评分 | Critical | High | Medium | Low | 状态 |
|---|---|---|---|---|---|---|
| openwebui-patterns-blackbox.yaml | 58/100 | 4 | 7 | 8 | 5 | 🔴 需立即修复 |
| openwebui-patterns-whitebox.yaml | 50/100 | 3 | 4 | 4 | 2 | 🔴 需立即修复 |

---

## 修复任务清单

### 立即修复（Critical - 本次会话完成）

#### 黑盒库（4个）
- [x] **C-001**: 所有 blackbox_reasoning 改为问句格式（5个模式全部违规）
- [x] **C-002**: 修正 multer 默认行为：DiskStorage 是 default_safe: false
- [x] **C-003**: 修正 LDAP Unauthenticated Bind 默认行为：现代版本默认拒绝
- [x] **C-004**: 补充所有模式的 transferable_to 字段（5个模式全部缺失）

#### 白盒库（3个）
- [x] **WB-001**: 重写模式 4 和 6 的 reasoning_chain 为问句格式
- [x] **WB-002**: 决定模式 2 归属（白盒 vs 通用）→ 标记 applicable: whitebox
- [x] **WB-003**: 修正 Semgrep 规则 pattern-not 语法

---

### 本周修复（High）

#### 黑盒库（7个）
- [ ] **H-001**: 删除无效 Markdown XSS payload `![xss](https://x.x onerror=alert(1))`
- [ ] **H-002**: 补充 CSP 绕过章节到模式 4
- [ ] **H-003**: 补充 ZIP Slip 变种到模式 1
- [ ] **H-004**: 修正 IDOR prerequisite（改为可攻克而非硬性前提）
- [ ] **H-005**: 将 nosniff header 从 vulnerable_signs 移至 prerequisite
- [ ] **H-006**: 补充 LDAP 注入变种到模式 2
- [ ] **H-007**: 补充所有 CVE 的 NVD/GitHub Advisory 链接

#### 白盒库（4个）
- [ ] **WB-004**: 模式 1 补充 grep 命令到 reasoning_chain
- [ ] **WB-005**: 模式 3 补充 LDAP 密码检查的 grep 命令
- [ ] **WB-006**: 模式 5 补充 IDOR 检查的 grep 命令
- [ ] **WB-007**: 修正 Chrome Content Sniffing 描述（区分同源/跨域）

---

### 下次迭代（Medium/Low）

#### 共同改进（12个）
- [ ] 黑盒 M-001: 删除 verification_methods 第一条矛盾的方法
- [ ] 黑盒 M-002: 补充 KaTeX payload 版本差异说明
- [ ] 黑盒 M-003: 补充路径穿越专用工具推荐（dotdotpwn）
- [ ] 黑盒 M-004: 补充模式 1/2 自动化脚本示例
- [ ] 黑盒 M-005: 所有模式补充 defenses_that_block 字段
- [ ] 黑盒 M-006: 统一 practical_test 格式为列表
- [ ] 黑盒 M-007: YAML 字段名改为英文（渲染器识别 → renderer_identification）
- [ ] 黑盒 M-008: 补充批量操作 IDOR 测试
- [ ] 白盒 WB-008: 优化 grep 命令精确度（排除注释/测试）
- [ ] 白盒 WB-009: 模式 2 补充完整 git log 命令
- [ ] 白盒 WB-010: 模式 6 补充 Socket.IO 代码搜索方法
- [ ] 白盒 WB-013/014: 补充架构级指导（git log 优先策略、补丁审查流程）

---

## 新增规范（已更新到 CLAUDE.md）

1. **reasoning_chain 强制规则**：
   - 禁止"步骤X："开头（自动化检查会拒绝）
   - 必须用"问："或"如果...则..."开头
   - 白盒每个"问："后必须跟"白盒：grep/Semgrep 命令"

2. **技术细节准确性规则**：
   - 协议行为必须引用 RFC
   - 框架默认行为必须注明版本号
   - 浏览器行为必须区分同源/跨域
   - 所有代码示例必须验证后再写入

3. **审计规则**：
   - 每次添加/修改模式后必须自我审计
   - 按格式→完整性→准确性→字段→记录 5 步执行
   - 将审计结果追加到 AUDIT_FRAMEWORK.yaml

---

## Historical Issues 更新

本次审计新增 7 个系统性问题到 `AUDIT_FRAMEWORK.yaml`：

- issue_006: 黑盒 reasoning 陈述句问题（全部违规）
- issue_007: multer 默认行为错误
- issue_008: LDAP 默认配置描述不准确
- issue_009: transferable_to 字段全部缺失
- issue_010: Semgrep 规则语法错误
- issue_011: 白盒缺少 grep 命令
- issue_012: Chrome Content Sniffing 描述不准确

---

## 修复策略

由于问题数量多（黑盒 24 个，白盒 14 个），建议分批修复：

**Phase 1（本次会话）**：修复所有 Critical 问题（7个）
**Phase 2（本周）**：修复所有 High 问题（11个）
**Phase 3（下次迭代）**：修复 Medium/Low 问题（20个）

修复后预计评分：
- 黑盒库：58分 → 85分
- 白盒库：50分 → 90分

---

## 审计者签名

```
Auditor: 资深赏金猎人 + 0day 研究专家（10+ 年经验）
Audit Date: 2026-06-19
Next Review: 修复完成后 / 新增模式后
```
