---
sidebar_position: 18
title: "桌面端原生登录（RFC 8252）"
description: "Hermes Desktop 应用如何通过系统浏览器和 PKCE 登录受保护网关——不使用嵌入式 WebView，也不使用会话 Cookie"
---

# 桌面端原生登录（RFC 8252）

当 Hermes Desktop 应用连接到**受保护网关**（位于 OAuth 提供商之后的托管或自行托管仪表板）时，它可以通过两种方式登录：

1. **原生登录（RFC 8252）**——应用会打开你的**真实系统浏览器**，你在已信任的浏览器中批准登录，应用随后接收并将令牌存储在操作系统的钥匙串中。**没有嵌入式 WebView，也没有浏览器会话 Cookie。**只要网关支持，这就是默认方式。
2. **嵌入式登录（旧版回退方式）**——应用会打开一个小型应用内浏览器窗口，并捕获网关的会话 Cookie。当网关是未声明支持原生登录的旧版本构建时，会自动使用此方式。

你无需在两者之间选择——应用会检测网关支持的功能并选择最佳方式。本页面解释其工作原理及原因。

## 为什么使用原生登录

在原生应用中嵌入浏览器来进行 OAuth 存在众所周知的缺点：登录页面无法看到你已有的浏览器会话（因此你需要重新输入凭据并重新完成 MFA），密码管理器和通行密钥通常无法工作，并且应用依赖于从私有 WebView 中读取会话 Cookie。RFC 8252（“OAuth 2.0 for Native Apps”）是避免所有这些问题的行业最佳实践：**在系统浏览器中进行授权，并将应用自己的令牌交给应用。**

具体对于 Hermes，原生登录意味着：

- **没有嵌入式 WebView。**授权在 Safari / Chrome / Firefox / Edge——无论你使用哪一个——中进行，保留你的登录状态、扩展和通行密钥。
- **没有会话 Cookie。**应用持有 OAuth **访问令牌**（有效期短）和**刷新令牌**，并通过操作系统钥匙串（Electron `safeStorage`）进行静态加密。REST 调用和 WebSocket 票据使用 `Authorization: *** 标头进行认证，而不是 Cookie jar。

## 工作原理

```
Desktop app                Gateway (/auth/native/*)          Nous Portal (IDP)
   │ 1. open loopback 127.0.0.1:<random port>
   │ 2. system browser ─►  /auth/native/authorize
   │    (PKCE challenge)    (starts the normal PKCE login) ─► /oauth/authorize
   │                        ◄──── code ──── /auth/callback ◄──┘
   │                        3. mint one-time gateway code
   │ ◄─ 302 127.0.0.1/cb?code=… ─┘
   │ 4. POST /auth/native/token (code + PKCE verifier)
   │ ◄─ 5. { access_token, refresh_token, expires_at } ───────┘
   │ 6. store in OS keychain; use Bearer for REST + WS tickets
```

网关对该流程进行**代理**：它是*桌面应用的*授权服务器，同时又是*上游身份提供商*（Nous Portal）的 OAuth 客户端。这是必需的，因为上游的 `client_id` 和允许的重定向 URI 绑定于网关自身的源——桌面应用无法成为 Portal 的直接客户端。桌面端仍可获得完整的 RFC 8252 体验：拥有自己的 PKCE 对、自己的回环重定向，以及自己持有的令牌。

**PKCE（RFC 7636）**保护回环跳转：一次性网关代码在没有代码验证器的情况下毫无用处，而代码验证器绝不会离开应用。该代码只能使用一次且有效期很短。

## 功能检测与回退

桌面端读取网关的公开 `/api/status` 端点，该端点会声明一个 `auth_flows` 数组：

| `auth_flows` 值 | 含义 |
|--------------------|---------|
| `["cookie", "native_pkce"]` | 网关支持原生登录 → 应用使用它 |
| `["cookie"]` | 网关仅支持旧版流程 → 应用使用嵌入式 WebView |
| *（字段不存在）* | 旧版网关 → 应用使用嵌入式 WebView |

如果已声明原生登录但因本地原因失败——例如安全工具阻止了回环监听器，或者你关闭了浏览器标签页——应用会**自动回退到嵌入式流程**，以便你仍然可以登录。

## 令牌生命周期

- **访问令牌**：有效期短（分钟）。在每次 REST 调用中以及创建 WebSocket 票据时，以 `Authorization: Bearer <token>` 形式发送。
- **刷新令牌**：有效期更长且会轮换。当访问令牌接近过期时，应用会调用 `/auth/native/refresh` 来轮换两个令牌，然后更新钥匙串。
- **最终过期**：如果刷新令牌失效（过期 / 已撤销 / 检测到重复使用），应用会清除其存储的令牌，并提示进行新的登录。
- **退出登录**：会清除该网关的原生令牌（钥匙串）和所有旧版会话 Cookie。

## 面向网关运营者

只要受保护网关注册了可代理的 OAuth 提供商（例如内置的 **Nous** 提供商），原生登录便会自动可用。无需配置——`/auth/native/*` 路由和 `auth_flows` 声明是仪表板认证子系统的一部分。仅支持密码和仅支持令牌的提供商不会声明 `native_pkce`（没有可代理的上游重定向），这些部署将继续使用其现有登录方式。

相关端点（均为公开的、认证前引导端点，与现有 `/auth/*` OAuth 路由相同）：

- `GET /auth/native/authorize`——启动代理的 PKCE 登录
- `POST /auth/native/token`——用回环代码和验证器交换令牌
- `POST /auth/native/refresh`——使用应用的刷新令牌轮换令牌

## 另请参阅

- [通过 SSH / 远程主机使用 OAuth](./oauth-over-ssh.md)——适用于远程机器上提供商/MCP OAuth 的回环回调模式。
- [通过 Nous Portal 运行 Hermes](./run-hermes-with-nous-portal.md)
