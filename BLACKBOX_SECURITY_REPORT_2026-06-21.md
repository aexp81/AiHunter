# 纯黑盒安全测试报告

- 目标：`http://localhost:8090/login.html`
- 日期：2026-06-21
- 方法：仅使用公开页面、前端 JavaScript 与 HTTP 请求/响应；不依赖后端源码
- 测试性质：低影响验证；未执行删除、文件写入、拒绝服务或持久化操作

## 结论

目标存在两条可独立完成的管理员接管路径：

1. `admin` 账号接受空密码，直接签发 `ADMIN` Bearer Token。
2. 前端 JavaScript 暴露 OAuth 客户端密钥和未认证注册接口；注册时可操纵 `ownerId` 获得 `ADMIN`，随后通过 OAuth password grant 获取管理员令牌。

管理员接口还会返回所有用户的明文密码，使一次管理员权限获取扩大为全量账户凭据泄露。

## 发现

### BB-01 管理员空密码认证绕过 — Critical

**接口**：`POST /api/login`

错误密码基线：

```http
POST /api/login
Content-Type: application/json

{"username":"admin","password":"definitely-wrong"}
```

响应 `401 Unauthorized`。

将密码改为空字符串：

```http
POST /api/login
Content-Type: application/json

{"username":"admin","password":""}
```

响应 `200 OK`，返回 Bearer Token，且响应声明 `roleType: ADMIN`。使用该令牌访问 `GET /api/users` 返回 `200`。

**影响**：未认证攻击者可直接取得管理员权限和全部受保护数据。

**修复**：删除任何空密码、默认密码或旁路分支；所有登录入口统一调用同一套密码校验；拒绝空白输入；增加针对空字符串、缺失字段和 Unicode 空白的回归测试。

### BB-02 未认证注册参数导致垂直越权 — Critical

**前端发现**：公开的 `/js/api.js` 可还原 `/api/register`、`/oauth/token` 等接口，以及 OAuth 客户端配置。

在管理员资料响应中可观察到管理员的 `ownerId` 为 `9001`。未携带任何认证信息提交：

```http
POST /api/register
Content-Type: application/json

{"username":"<unique>","password":"<redacted>","ownerId":9001}
```

响应 `200 OK`，新账户的 `roleType` 为 `ADMIN`。随后使用前端暴露的客户端配置请求 `/oauth/token`，获得该新账户的 `ADMIN` Token；该令牌访问 `/api/users` 返回 `200`。

测试创建的验证账户：`bb_admin_1782046293466`（密码未记录）。

**影响**：任何人都可自助创建管理员账户。这条攻击链不依赖 BB-01。

**修复**：注册接口禁止接收或信任 `ownerId`、角色、租户归属等授权属性；从服务端会话和邀请记录派生这些字段；管理员创建必须经过已认证且显式授权的管理接口；对所有可批量赋值字段采用 allowlist。

### BB-03 前端嵌入 OAuth 客户端密钥 — High

`/js/api.js` 中的轻度编码可在浏览器内直接还原：

- `clientId: portal-web`
- `clientSecret: super-secret-portal-2025`
- Token 端点：`/oauth/token`

使用这些值执行 `client_credentials` grant 返回 `200` 和有效 `CLIENT` Token；结合 BB-02，可执行 password grant 获取伪造管理员账户的 Token。

**影响**：客户端密钥对所有访问者公开，不能再作为客户端身份凭证；它同时放大注册越权问题。

**修复**：浏览器应用应视为 public client，不得持有 client secret；使用 Authorization Code + PKCE，或把 confidential-client 流程放到可信后端；立即轮换已暴露密钥。

### BB-04 管理员用户列表泄露明文密码 — Critical

使用管理员 Token 请求 `GET /api/users`，响应中的每个用户对象均包含 `password` 字段，且内容为可直接使用的明文密码。

**影响**：任一管理员 Token 泄露都会升级为全量账户接管；若用户复用密码，还可能扩展到其他系统。

**修复**：密码只保存强密码哈希（Argon2id、scrypt 或合适参数的 bcrypt）；响应 DTO 永远不包含密码字段；轮换所有已暴露密码并使现有 Token 失效。

### BB-05 登录缺少速率限制 — Medium

连续发送 30 次错误管理员密码请求，全部返回 `401`，未出现 `429` 或 `Retry-After`；紧接着的登录请求仍正常签发管理员 Token。

**影响**：允许高速密码猜测和凭据填充。

**修复**：按账号、源地址和设备信号组合限速；采用渐进延迟；异常时返回 `429` 与 `Retry-After`；避免永久锁死账号造成拒绝服务。

### BB-06 异常处理泄露内部实现信息 — Medium

畸形 JSON 和错误 `Content-Type` 均返回 `500`，响应包含 Java 包名、模型类名、Jackson 反序列化细节和内部异常链。

**影响**：帮助攻击者确认技术栈、内部类结构和输入处理路径；错误请求被错误标记为服务端故障。

**修复**：将解析错误和不支持的媒体类型分别映射为 `400`、`415`；客户端只返回固定错误码与关联 ID；完整异常仅记录在服务端日志。

### BB-07 缺少安全响应头与敏感响应缓存控制 — Low

登录页未观察到 `Content-Security-Policy`、`X-Content-Type-Options`、`Referrer-Policy`、点击劫持保护等安全头；Token 响应未观察到 `Cache-Control: no-store`。

**修复**：至少设置 `Content-Security-Policy`、`frame-ancestors`、`X-Content-Type-Options: nosniff`、`Referrer-Policy`；认证和 Token 响应设置 `Cache-Control: no-store` 与 `Pragma: no-cache`。生产环境强制 HTTPS 并配置 HSTS。

## 已验证的有效控制

- 无 Token 访问 `/api/ping`、`/api/me`、`/api/users` 均返回 `401`。
- `CLIENT` Token 不能访问用户资料或管理员用户列表，分别返回 `403`。
- 恶意 Origin 的 CORS 预检返回 `403 Invalid CORS request`，未观察到 Origin 反射。
- TRACE 返回 `405`。
- 常见 Actuator、Swagger、`.git`、source map 路径未暴露。
- 错误账号与管理员错误密码在门户登录接口上返回相同的 `401` 文案，未观察到直接账号枚举差异。

## 修复优先级

1. 立即修复空密码登录，并撤销全部现有 Token。
2. 关闭未认证注册，移除客户端可控授权属性，删除已创建的测试管理员账户。
3. 从前端移除并轮换 OAuth 客户端密钥。
4. 将密码迁移为强哈希并从所有响应中移除，强制用户重置密码。
5. 再处理限速、异常响应和安全头。

完成前四项后应重新执行完整认证/授权回归测试，重点覆盖所有 grant type、注册字段变体和管理员接口。
