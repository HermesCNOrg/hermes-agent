---
sidebar_position: 4
title: "MCP（模型上下文协议）"
description: "通过 MCP 将 Hermes Agent 连接到外部工具服务器，并精确控制 Hermes 加载哪些 MCP 工具"
---

# MCP（模型上下文协议）

MCP 让 Hermes Agent 连接到外部工具服务器，使 agent 能够使用 Hermes 本身之外的工具——GitHub、数据库、文件系统、浏览器栈、内部 API 等等。

如果你曾经希望 Hermes 使用某个已经存在于其他地方的工具，MCP 通常是最简洁的方式。

## MCP 能给你带来什么

- 无需先编写原生 Hermes 工具，即可访问外部工具生态系统
- 在同一配置中同时支持本地 stdio 服务器和远程 HTTP MCP 服务器
- 启动时自动发现并注册工具
- 在服务器支持的情况下，提供针对 MCP 资源和 prompt（提示词）的实用工具封装
- 按服务器过滤，只向 Hermes 暴露你真正需要的 MCP 工具

## 快速开始

1. MCP 支持已包含在标准安装中——无需额外步骤。

2. 在 `~/.hermes/config.yaml` 中添加一个 MCP 服务器：

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/projects"]
```

3. 启动 Hermes：

```bash
hermes chat
```

4. 让 Hermes 使用 MCP 支持的能力。

例如：

```text
List the files in /home/user/projects and summarize the repo structure.
```

Hermes 会发现 MCP 服务器的工具，并像使用其他工具一样使用它们。

## 目录：一键安装经 Nous 批准的 MCP

Hermes 附带了一个经过策划的 MCP 服务器目录，这些服务器已由 Nous 工作人员审查
并合并。它们默认是禁用的——只安装你真正需要的。

```bash
hermes mcp                # 交互式选择器（默认）
hermes mcp catalog        # 纯文本列表，可脚本化
hermes mcp install n8n    # 按名称安装目录条目
```

选择器会显示每个条目的当前状态：

```
n8n          available              Manage and inspect n8n workflows from Hermes
linear       enabled                Linear issue/project management (remote OAuth)
github       installed (disabled)   GitHub repo + PR tools
```

在行上按 `Enter` 进行安装（并完成所需凭据的配置）、启用、禁用或卸载。目录条目存储在
hermes-agent 仓库的 `optional-mcps/` 目录下——存在于该目录表示已获得 Nous 批准。
没有社区提交层级；通过合并 PR 来添加条目。

目录条目可能需要：

- **API 密钥**——Hermes 在安装时提示，并将值写入 `~/.hermes/.env`。非秘密值（base URL）也写入同一文件。
- **OAuth**（远程 MCP）——在配置中写入 `auth: oauth`；MCP 客户端在首次连接时打开浏览器。
- **OAuth**（第三方提供商，如 Google/GitHub）——如果你尚未完成身份验证，Hermes 会引导你使用 `hermes auth <provider>`。

### 安装时选择工具

配置完凭据后，Hermes 会探测 MCP 服务器，列出其暴露的每一个工具并呈现一个复选框列表：

```
Select tools for 'linear' (SPACE toggle, ENTER confirm)
  [x] find_issues       Find issues matching a query
  [x] get_issue         Get a single issue
  [x] create_issue      Create a new issue
  [ ] delete_workspace  Delete a Linear workspace
  ...
```

预选的项目来源于：

1. **你之前的选择**（如果你之前安装过该条目——重新安装会保留你已有的选择，清单的默认值不会覆盖它）
2. **清单中的 `tools.default_enabled`**（如果条目声明了该字段——有些目录条目会预先修剪可变或不常用的工具）
3. **全部勾选**（如果以上都不适用）

按 ENTER 提交复选框列表。只有选中的工具会写入 `mcp_servers.<name>.tools.include`。如果全选，则不写入过滤规则（配置最简洁，行为一致）。

**如果探测失败**（服务器不可达、OAuth 尚未完成、后端服务未运行），安装仍然成功：清单中的 `tools.default_enabled` 会直接应用（如果声明了），否则不写入过滤规则。待服务器可达后，运行 `hermes mcp configure <name>` 进行细化。

### 信任模型

安装目录条目会运行清单指定的内容——`git clone`、条目的 `bootstrap` 命令（`pip install`、`npm install`等），以及最终的 MCP 服务器自身代码。清单通过 PR 审查后合入 hermes-agent 仓库，因此 Nous 在每条记录发布前已进行审查——**但你在安装前仍应阅读清单**，特别是 `source:` 字段的仓库、`install.bootstrap:` 命令以及任何 `transport.command:` 调用。

清单位于 GitHub 上的
[`optional-mcps/<name>/manifest.yaml`](https://github.com/NousResearch/hermes-agent/tree/main/optional-mcps)。
选择器在安装时也会打印清单的 `source:` URL，方便你快速验证上游仓库。Web 面板的 MCP
页面会为每个目录条目展示同样的详细信息——传输方式、认证类型、
端点 URL（HTTP）或命令+参数（stdio）、git 安装源/引用和
bootstrap 命令、以及设置说明——`source:` 会渲染为
可点击链接，因此你可以在点击安装之前检查条目连接或运行的内容。

### 清单版本兼容性

清单固定了 `manifest_version`。目录是向前兼容的：如果
某个 PR 添加的条目使用了比你当前 Hermes 理解的更新的 `manifest_version`，
选择器会为该条目显示警告（`⚠ '<name>' 需要更新版本的 Hermes`），
而不是静默隐藏它。看到此提示时，运行 `hermes update`
安装最新的 Hermes。

### 运行时 `${ENV_VAR}` 替换

在条目的 `transport.command`、`transport.args`、`transport.url`
和 `headers` 中，`${VAR}` 占位符会在服务器连接时从环境变量
（包括 `~/.hermes/.env` 中的所有内容）解析。
当目录条目需要引用用户在别处配置的值时，这很有用——
例如 `${HOME}/foo` 或 `${MY_PROVIDER_TOKEN}`。

请注意，这与目录清单中的 `${INSTALL_DIR}` 不同，后者
在安装时会被替换为目录克隆条目仓库的路径。

### 稍后更新工具选择

```bash
hermes mcp configure linear
```

重新打开相同的复选框列表，并预选中你当前的选择。当你想要启用更多工具，
或者服务器新增了你想要加入的工具时使用此命令。

### 更新目录清单

MCP 永远不会自动更新。Hermes 更新后如果清单版本发生变化，请重新运行 `hermes mcp install <name>` 来刷新。

要向目录添加 MCP，请针对
[`optional-mcps/`](https://github.com/NousResearch/hermes-agent/tree/main/optional-mcps) 提交 PR。

## 两种 MCP 服务器

### Stdio 服务器

Stdio 服务器作为本地子进程运行，通过 stdin/stdout 通信。

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "***"
```

适合使用 stdio 服务器的场景：
- 服务器已在本地安装
- 需要低延迟访问本地资源
- 你参考的 MCP 服务器文档中使用了 `command`、`args` 和 `env`

### HTTP 服务器

HTTP MCP 服务器是 Hermes 直接连接的远程端点。

```yaml
mcp_servers:
  remote_api:
    url: "https://mcp.example.com/mcp"
    headers:
      Authorization: "Bearer ***"
```

适合使用 HTTP 服务器的场景：
- MCP 服务器托管在其他地方
- 你的组织暴露了内部 MCP 端点
- 你不希望 Hermes 为该集成在本地启动子进程

### OAuth 认证的 HTTP 服务器

大多数托管的 MCP 服务器（Linear、Sentry、Atlassian、Asana、Figma、Stripe……）需要 OAuth 2.1，而不是静态的 bearer token。设置 `auth: oauth`，Hermes 会通过 MCP Python SDK 处理发现、动态客户端注册、PKCE、令牌交换、刷新和升级认证。

```yaml
mcp_servers:
  linear:
    url: "https://mcp.linear.app/mcp"
    auth: oauth
```

首次连接时，Hermes 会打印一个授权 URL，尽可能打开你的浏览器，并在本地环回端口上等待 OAuth 回调。令牌缓存在 `~/.hermes/mcp-tokens/<server>.json`，权限为 0o600；后续运行静默重用令牌，直到刷新失败。

**远程/无头主机。** 当 Hermes 运行在与浏览器不同的机器上时，环回回调无法到达你的笔记本。两种方式完成流程：

- **粘贴回传（无需设置）：** 在交互式终端上，Hermes 会在授权 URL 旁边打印"Or paste the redirect URL here…"。在浏览器中打开 URL，批准，复制浏览器最终跳转到的完整 URL（重定向会显示连接错误——这是预期行为），在提示符处粘贴。纯 `?code=…&state=…` 查询字符串也可以。
- **SSH 端口转发：** 在另一个终端中运行 `ssh -N -L <port>:127.0.0.1:<port> user@host`，然后让重定向流程正常进行。

完整的操作指南，包括不支持 DCR 的服务器（如 Slack）、预注册的 `client_id`/`client_secret`、作用域定制以及通过 `hermes mcp login <server>` 重新认证，请参见 [通过 SSH / 远程主机的 OAuth](../../guides/oauth-over-ssh.md#mcp-servers)。

**陷阱——不支持自动注册的提供商（Google Drive、Atlassian）。** 某些服务器会拒绝纯 `auth: oauth` 所依赖的动态客户端注册步骤（RFC 7591）——Google 官方的 Drive 服务器（`https://drivemcp.googleapis.com/mcp/v1`）返回 `400 Bad Request`，因此无法创建 OAuth 客户端，也无法获取令牌。症状很微妙：这些服务器在无需认证的情况下也能返回 `tools/list`，因此 `hermes mcp login` 可以列出工具，看起来像是成功了，但每次真正的工具调用都会超时。`hermes mcp login` 现在可以检测到这种情况（它会检查令牌是否确实写入了磁盘），并提示你提供自己的 OAuth 客户端。在提供商的控制台中创建一个客户端，并将其添加到配置中：

```yaml
mcp_servers:
  googledrive:
    url: "https://drivemcp.googleapis.com/mcp/v1"
    auth: oauth
    oauth:
      client_id: "<your-oauth-client-id>"
      client_secret: "<your-oauth-client-secret>"
```

然后运行 `hermes mcp login googledrive`——使用预注册的客户端，Hermes 会跳过注册，直接运行标准的浏览器授权流程。

**陷阱——配置自动重载竞态。** 在正在运行的 Hermes 会话中编辑 `~/.hermes/config.yaml` 时，CLI 会以 30 秒超时自动重载 MCP 连接。这不足以完成交互式 OAuth 流程。请先添加条目，然后在一个新的终端中运行 `hermes mcp login <server>`——它会等待完整的 5 分钟让你完成认证。

## mTLS / 客户端证书

需要双向 TLS（客户端证书认证）的远程 HTTP MCP 服务器通过 `client_cert` / `client_key` 支持。Hermes 将解析后的证书传递给底层 HTTP 客户端，用于 TLS 握手。

`client_cert` 接受三种形式：

- **单个组合 PEM 路径**——一个文件同时包含证书和私钥：

```yaml
mcp_servers:
  internal_api:
    url: "https://mcp.internal.example.com/mcp"
    client_cert: "~/.certs/mcp-client.pem"
```

- **`[cert, key]` 二元组**——证书和密钥分别在单独的文件中（等同于设置 `client_cert` + `client_key`）：

```yaml
mcp_servers:
  internal_api:
    url: "https://mcp.internal.example.com/mcp"
    client_cert: ["~/.certs/mcp-client.crt", "~/.certs/mcp-client.key"]
```

- **`[cert, key, password]` 三元组**——当私钥已加密时，第三个元素是密钥口令：

```yaml
mcp_servers:
  internal_api:
    url: "https://mcp.internal.example.com/mcp"
    client_cert: ["~/.certs/mcp-client.crt", "~/.certs/mcp-client.key", "${MCP_KEY_PASSWORD}"]
```

你也可以通过 `client_cert`（组合 PEM）加上显式的 `client_key` 来完全分离证书和密钥。路径支持 `~` 展开；文件缺失会抛出清晰的、服务器级别的错误，而不是模糊的 TLS 握手失败。

## 基本配置参考

Hermes 从 `~/.hermes/config.yaml` 的 `mcp_servers` 下读取 MCP 配置。

### 常用字段

| 字段 | 类型 | 含义 |
|---|---|---|
| `command` | string | stdio MCP 服务器的可执行文件 |
| `args` | list | stdio 服务器的参数 |
| `env` | mapping | 传递给 stdio 服务器的环境变量 |
| `url` | string | HTTP MCP 端点 |
| `headers` | mapping | 远程服务器的 HTTP 头 |
| `client_cert` | string \| list | 用于 mTLS 的客户端证书——组合 PEM 路径，或 `[cert, key]` / `[cert, key, password]` |
| `client_key` | string | 客户端私钥 PEM 路径（当与 `client_cert` 分开时） |
| `timeout` | number | 工具调用超时时间 |
| `connect_timeout` | number | 初始连接超时时间（也限制 MCP `initialize` 握手） |
| `idle_timeout_seconds` | number | 在此秒数无工具调用后回收 stdio 服务器（`0` = 从不，默认）。服务器在下次工具调用时透明重启。 |
| `max_lifetime_seconds` | number | 在此总存活时间后回收 stdio 服务器（`0` = 从不，默认）。下次使用时透明重启。 |
| `enabled` | bool | 若为 `false`，Hermes 完全跳过该服务器 |
| `supports_parallel_tool_calls` | bool | 若为 `true`，该服务器的工具可并发运行 |
| `tools` | mapping | 按服务器过滤工具及实用工具策略 |

### 最简 stdio 示例

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
```

### 回收内存密集型 stdio 服务器

基于浏览器的 MCP 服务器（例如 `@playwright/mcp`）在首次工具调用后会保持一个完整的 Chromium 常驻——数百 MB 永远不会释放。选择自动回收，服务器会在空闲/存活时间限制后被关闭，然后在下次调用其某个工具时透明重启（其工具在整个过程中保持注册状态）：

```yaml
mcp_servers:
  playwright:
    command: "npx"
    args: ["-y", "@playwright/mcp@latest", "--headless"]
    idle_timeout_seconds: 900     # 15 分钟无工具调用后回收
    max_lifetime_seconds: 86400   # 每天至少回收一次
```

### 最简 HTTP 示例

```yaml
mcp_servers:
  company_api:
    url: "https://mcp.internal.example.com"
    headers:
      Authorization: "Bearer ***"
```

## 内置预设

对于知名 MCP 服务器，`hermes mcp add` 接受 `--preset` 标志，自动填写传输层细节，无需手动查找命令和参数。预设只提供默认值——你在同一命令行传入的其他内容（环境变量、头信息、过滤规则）仍然优先生效。

| 预设 | 配置内容 |
|---|---|
| `codex` | Codex CLI 的 MCP 服务器（通过 stdio 运行 `codex mcp-server`）。需要 PATH 中存在 `codex` CLI。 |

```bash
# 一行命令将 Codex CLI 添加为 MCP 服务器
hermes mcp add codex --preset codex
```

等价于写入：

```yaml
mcp_servers:
  codex:
    command: "codex"
    args: ["mcp-server"]
```

你可以使用任意本地名称（`hermes mcp add my-codex --preset codex` 完全可以）；预设只提供 `command`/`args` 默认值。

## Hermes 注册 MCP 工具的方式

Hermes 为 MCP 工具添加前缀，避免与内置名称冲突：

```text
mcp_<server_name>_<tool_name>
```

示例：

| 服务器 | MCP 工具 | 注册名称 |
|---|---|---|
| `filesystem` | `read_file` | `mcp_filesystem_read_file` |
| `github` | `create-issue` | `mcp_github_create_issue` |
| `my-api` | `query.data` | `mcp_my_api_query_data` |

实际使用中，你通常不需要手动调用带前缀的名称——Hermes 在正常推理过程中会自动识别并选择该工具。

## MCP 实用工具

在服务器支持的情况下，Hermes 还会围绕 MCP 资源和 prompt 注册实用工具：

- `list_resources`
- `read_resource`
- `list_prompts`
- `get_prompt`

这些工具按服务器注册，遵循相同的前缀规则，例如：

- `mcp_github_list_resources`
- `mcp_github_get_prompt`

### 重要说明

这些实用工具现在具备能力感知：
- 只有当 MCP 会话实际支持资源操作时，Hermes 才注册资源实用工具
- 只有当 MCP 会话实际支持 prompt 操作时，Hermes 才注册 prompt 实用工具

因此，一个只暴露可调用工具而没有资源/prompt 的服务器，不会获得这些额外的封装。

## 按服务器过滤

你可以控制每个 MCP 服务器向 Hermes 贡献哪些工具，从而精细管理工具命名空间。

### 完全禁用某个服务器

```yaml
mcp_servers:
  legacy:
    url: "https://mcp.legacy.internal"
    enabled: false
```

若 `enabled: false`，Hermes 完全跳过该服务器，甚至不尝试连接。

### 白名单过滤服务器工具

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "***"
    tools:
      include: [create_issue, list_issues]
```

只有列出的 MCP 服务器工具会被注册。

### 黑名单过滤服务器工具

```yaml
mcp_servers:
  stripe:
    url: "https://mcp.stripe.com"
    tools:
      exclude: [delete_customer]
```

除排除项外，所有服务器工具均被注册。

### 优先级规则

若两者同时存在：

```yaml
tools:
  include: [create_issue]
  exclude: [create_issue, delete_issue]
```

`include` 优先生效。

### 同样可过滤实用工具

你也可以单独禁用 Hermes 添加的实用工具封装：

```yaml
mcp_servers:
  docs:
    url: "https://mcp.docs.example.com"
    tools:
      prompts: false
      resources: false
```

含义：
- `tools.resources: false` 禁用 `list_resources` 和 `read_resource`
- `tools.prompts: false` 禁用 `list_prompts` 和 `get_prompt`

### 完整示例

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "***"
    tools:
      include: [create_issue, list_issues, search_code]
      prompts: false

  stripe:
    url: "https://mcp.stripe.com"
    headers:
      Authorization: "Bearer ***"
    tools:
      exclude: [delete_customer]
      resources: false

  legacy:
    url: "https://mcp.legacy.internal"
    enabled: false
```

## 如果所有工具都被过滤掉会怎样？

如果你的配置过滤掉了所有可调用工具，并禁用或省略了所有支持的实用工具，Hermes 不会为该服务器创建空的运行时 MCP 工具集。

这样可以保持工具列表整洁。

## 运行时行为

### 发现时机

Hermes 在启动时发现 MCP 服务器，并将其工具注册到普通工具注册表中。

### 动态工具发现

MCP 服务器可以在运行时通过发送 `notifications/tools/list_changed` 通知，告知 Hermes 其可用工具发生了变化。Hermes 收到该通知后，会自动重新获取服务器的工具列表并更新注册表——无需手动执行 `/reload-mcp`。

这对于能力动态变化的 MCP 服务器非常有用（例如，加载新数据库 schema 时添加工具，或服务下线时移除工具）。

刷新操作受锁保护，因此同一服务器快速连续发送的通知不会导致重叠刷新。prompt 和资源变更通知（`prompts/list_changed`、`resources/list_changed`）会被接收，但暂未处理。

### 重新加载

如果你修改了 MCP 配置，请使用：

```text
/reload-mcp
```

这会从配置重新加载 MCP 服务器并刷新可用工具列表。对于服务器主动推送的运行时工具变更，请参阅上方的[动态工具发现](#dynamic-tool-discovery)。

### 工具集

每个已配置的 MCP 服务器，在贡献至少一个已注册工具时，也会创建一个运行时工具集：

```text
mcp-<server>
```

这使得在工具集层面更容易理解 MCP 服务器的情况。

## 安全模型

### Stdio 环境变量过滤

对于 stdio 服务器，Hermes 不会盲目传递你的完整 shell 环境。

只有显式配置的 `env` 加上安全基线才会被传递。这减少了意外泄露密钥的风险。

### 配置层面的暴露控制

新的过滤支持同时也是一种安全控制：
- 禁用你不希望模型看到的危险工具
- 对敏感服务器只暴露最小白名单
- 在不需要暴露该接口时，禁用资源/prompt 封装

## 示例用例

### GitHub 服务器，仅暴露最小 issue 管理接口

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "***"
    tools:
      include: [list_issues, create_issue, update_issue]
      prompts: false
      resources: false
```

使用方式：

```text
Show me open issues labeled bug, then draft a new issue for the flaky MCP reconnection behavior.
```

### Stripe 服务器，移除危险操作

```yaml
mcp_servers:
  stripe:
    url: "https://mcp.stripe.com"
    headers:
      Authorization: "Bearer ***"
    tools:
      exclude: [delete_customer, refund_payment]
```

使用方式：

```text
Look up the last 10 failed payments and summarize common failure reasons.
```

### 文件系统服务器，限定单个项目根目录

```yaml
mcp_servers:
  project_fs:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/my-project"]
```

使用方式：

```text
Inspect the project root and explain the directory layout.
```

## 故障排查

### MCP 服务器无法连接

检查：

```bash
# 验证 MCP 依赖已安装（标准安装已包含）
cd ~/.hermes/hermes-agent && uv pip install -e ".[mcp]"

node --version
npx --version
```

然后验证你的配置并重启 Hermes。

### 工具未出现

可能原因：
- 服务器连接失败
- 发现过程失败
- 你的过滤配置排除了这些工具
- 该服务器不存在对应的实用工具能力
- 服务器通过 `enabled: false` 被禁用

如果你是有意过滤，这是预期行为。

### 为什么资源或 prompt 实用工具没有出现？

因为 Hermes 现在只在以下两个条件同时满足时才注册这些封装：
1. 你的配置允许它们
2. 服务器会话实际支持该能力

这是有意为之，保持工具列表的真实性。

## 并行工具调用

默认情况下，MCP 工具按顺序执行——一次一个。如果你的 MCP 服务器暴露的工具可以安全并发运行（例如只读查询、独立 API 调用），可以选择启用并行执行：

```yaml
mcp_servers:
  docs:
    command: "docs-server"
    supports_parallel_tool_calls: true
```

当 `supports_parallel_tool_calls` 为 `true` 时，Hermes 可能在单次工具调用批次中同时执行该服务器的多个工具，就像对内置只读工具（`web_search`、`read_file` 等）的处理方式一样。

:::caution
只对工具可以安全同时运行的 MCP 服务器启用并行调用。如果工具会读写共享状态、文件、数据库或外部资源，请在启用此设置前仔细评估读写竞争条件。
:::

## MCP Sampling 支持

MCP 服务器可以通过 `sampling/createMessage` 协议向 Hermes 请求 LLM 推理。这允许 MCP 服务器代表自己请求 Hermes 生成文本——适用于需要 LLM 能力但没有自己模型访问权限的服务器。

Sampling 对所有 MCP 服务器**默认启用**（当 MCP SDK 支持时）。可在 `sampling` 键下按服务器配置：

```yaml
mcp_servers:
  my_server:
    command: "my-mcp-server"
    sampling:
      enabled: true            # 启用 sampling（默认：true）
      model: "openai/gpt-4o"  # 覆盖 sampling 请求使用的模型（可选）
      max_tokens_cap: 4096     # 每次 sampling 响应的最大 token 数（默认：4096）
      timeout: 30              # 每次请求的超时时间，单位秒（默认：30）
      max_rpm: 10              # 速率限制：每分钟最大请求数（默认：10）
      max_tool_rounds: 5       # sampling 循环中的最大工具调用轮数（默认：5）
      allowed_models: []       # 服务器可请求的模型名称白名单（空 = 不限）
      log_level: "info"        # 审计日志级别：debug、info 或 warning（默认：info）
```

sampling 处理器包含滑动窗口速率限制器、按请求超时和工具循环深度限制，防止失控使用。每个服务器实例会跟踪指标（请求数、错误数、已用 token 数）。

如需对特定服务器禁用 sampling：

```yaml
mcp_servers:
  untrusted_server:
    url: "https://mcp.example.com"
    sampling:
      enabled: false
```

## 将 Hermes 作为 MCP 服务器运行

除了连接**到** MCP 服务器，Hermes 也可以**作为** MCP 服务器运行。这让其他支持 MCP 的 agent（Claude Code、Cursor、Codex 或任何 MCP 客户端）能够使用 Hermes 的消息能力——列出会话、读取消息历史，以及跨所有已连接平台发送消息。

### 适用场景

- 你希望 Claude Code、Cursor 或其他编程 agent 通过 Hermes 发送和读取 Telegram/Discord/Slack 消息
- 你需要一个单一的 MCP 服务器，同时桥接 Hermes 所有已连接的消息平台
- 你已经有一个运行中的 Hermes gateway，并已连接各平台

### 快速开始

```bash
hermes mcp serve
```

这会启动一个 stdio MCP 服务器。进程生命周期由 MCP 客户端（而非你）管理。

### MCP 客户端配置

将 Hermes 添加到你的 MCP 客户端配置中。例如，在 Claude Code 的 `~/.claude/claude_desktop_config.json` 中：

```json
{
  "mcpServers": {
    "hermes": {
      "command": "hermes",
      "args": ["mcp", "serve"]
    }
  }
}
```

或者，如果你将 Hermes 安装在特定位置：

```json
{
  "mcpServers": {
    "hermes": {
      "command": "/home/user/.hermes/hermes-agent/venv/bin/hermes",
      "args": ["mcp", "serve"]
    }
  }
}
```

### 可用工具

MCP 服务器暴露 10 个工具，与 OpenClaw 的 channel bridge 接口一致，并额外提供一个 Hermes 专属的 channel 浏览器：

| 工具 | 描述 |
|------|------|
| `conversations_list` | 列出活跃的消息会话。可按平台过滤或按名称搜索。 |
| `conversation_get` | 通过 session key 获取某个会话的详细信息。 |
| `messages_read` | 读取某个会话的近期消息历史。 |
| `attachments_fetch` | 从特定消息中提取非文本附件（图片、媒体）。 |
| `events_poll` | 从指定游标位置轮询新的会话事件。 |
| `events_wait` | 长轮询/阻塞，直到下一个事件到达（接近实时）。 |
| `messages_send` | 通过平台发送消息（例如 `telegram:123456`、`discord:#general`）。 |
| `channels_list` | 列出所有平台上可用的消息目标。 |
| `permissions_list_open` | 列出本次 bridge 会话中观察到的待审批请求。 |
| `permissions_respond` | 允许或拒绝待审批请求。 |

### 事件系统

MCP 服务器包含一个实时事件桥，轮询 Hermes 的会话数据库以获取新消息。这让 MCP 客户端能够近实时感知新来的会话：

```
# 轮询新事件（非阻塞）
events_poll(after_cursor=0)

# 等待下一个事件（阻塞，直到超时）
events_wait(after_cursor=42, timeout_ms=30000)
```

事件类型：`message`、`approval_requested`、`approval_resolved`

事件队列存储在内存中，在 bridge 连接时开始工作。较旧的消息可通过 `messages_read` 获取。

### 选项

```bash
hermes mcp serve              # 普通模式
hermes mcp serve --verbose    # 在 stderr 输出调试日志
```

### 工作原理

MCP 服务器直接从 Hermes 的会话存储（`~/.hermes/sessions/sessions.json` 和 SQLite 数据库）读取会话数据。后台线程轮询数据库以获取新消息，并维护一个内存事件队列。发送消息时，使用与 cron 投递和 `hermes send` CLI 相同的内部发送引擎（`tools/send_message_tool.py`）。

读取操作（列出会话、读取历史、轮询事件）**不需要** gateway 运行。发送操作**需要** gateway 运行，因为平台适配器需要活跃连接。

### 当前限制

- 内嵌的 `hermes mcp serve` 目前只暴露 **stdio-only** MCP 服务器。如果你需要 HTTP MCP 服务器，请运行单独的适配器——或者，更常见的做法是使用 Hermes 的 MCP **客户端**侧，它已经同时支持 stdio 和 HTTP（`mcp_servers.yaml` / `config.yaml` 中的 `url` + `headers`；参见上方的 [HTTP 服务器](#http-servers)）。
- 事件轮询间隔约 200ms，通过基于 mtime 优化的数据库轮询实现（文件未变化时跳过处理）
- 暂不支持 `claude/channel` 推送通知协议
- 仅支持纯文本发送（`messages_send` 不支持媒体/附件发送）

## 相关文档

- [在 Hermes 中使用 MCP](/guides/use-mcp-with-hermes)
- [CLI 命令](/reference/cli-commands)
- [斜杠命令](/reference/slash-commands)
- [常见问题](/reference/faq)
