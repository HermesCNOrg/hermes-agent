---
sidebar_position: 15
title: "Web Dashboard"
description: "基于浏览器的管理面板，用于管理配置、API 密钥、MCP 服务器、消息配对、Webhook、Gateway、Memory、凭据、会话、日志、分析、定时任务和技能"
---

# Web Dashboard

Web Dashboard 是一个基于浏览器的 UI，用于管理你的 Hermes Agent 安装。无需编辑 YAML 文件或运行 CLI 命令，即可通过简洁的 Web 界面配置设置、管理 API 密钥并监控会话。

:::tip
托管模式的认证使用 Nous Portal OAuth；如果你还希望 Dashboard 连接到真实后端，`hermes setup --portal` 也会配置模型和工具网关。参见 [Nous Portal](/integrations/nous-portal)。
:::

## 快速开始

```bash
hermes dashboard
```

这将启动一个本地 Web 服务器，并在浏览器中打开 `http://127.0.0.1:9119`。Dashboard 完全在你的机器上运行——数据不会离开 localhost。

### 选项

| 标志 | 默认值 | 描述 |
|------|---------|-------------|
| `--port` | `9119` | Web 服务器运行端口 |
| `--host` | `127.0.0.1` | 绑定地址 |
| `--no-open` | — | 不自动打开浏览器 |
| `--insecure` | 关闭 | 允许绑定到非 localhost 主机（**危险**——会在网络上暴露 API 密钥；请配合防火墙和强认证使用） |
| `--isolated` | 关闭 | 当从命名配置文件启动时（`worker dashboard`），运行一个专用的、按配置隔离的服务器，而非路由到机器级 Dashboard |

```bash
# 自定义端口
hermes dashboard --port 8080

# 绑定到所有接口（在共享网络上请谨慎使用）
hermes dashboard --host 0.0.0.0

# 启动时不打开浏览器
hermes dashboard --no-open
```

## 管理多个配置文件

Dashboard 是一个**机器级**管理界面：一台服务器管理本机上的每个[配置文件](../profiles.md)。侧边栏中的配置文件切换器（当存在多个配置文件时可见）决定管理页面读取和写入哪个配置文件——Config、API Keys、Skills、MCP、Models 和 Chat 标签页都遵循该选择。当选择了 Dashboard 自身以外的配置文件时，顶部会出现一个琥珀色横幅，标明当前管理的配置文件名称，使写入目标始终清晰。

选择状态保存在 URL 中（`?profile=<name>`），因此深层链接如 `http://127.0.0.1:9119/skills?profile=worker` 打开时切换器已预选，并能在刷新后保持。

从配置文件别名启动 Dashboard 会路由到机器级 Dashboard，而不是启动第二个服务器：

```bash
worker dashboard
# → 已运行中：打开浏览器，?profile=worker 已预选
# → 未运行：  启动机器级 Dashboard，默认选中 "worker"
```

传递 `--isolated` 可选退出此行为，运行一个限定于该配置文件的专用服务器（统一前的旧行为——适用于你刻意用不同认证暴露不同配置文件的 Dashboard）。

**Chat** 标签页也遵循切换器：限定范围的聊天会在 PTY 子进程中使用所选配置文件的 `HERMES_HOME` 启动，因此对话会使用该配置文件的模型、技能、记忆和会话历史。切换配置文件会启动一个新的终端会话。

哪些内容按配置文件独立且**不**被切换器吸收：Gateway 进程（通过 `hermes -p <name> gateway …` 管理）、每个配置文件的会话数据库以及定时任务调度器（Cron 页面已通过自己的过滤器跨配置文件聚合显示）。

## 前置条件

默认的 `hermes-agent` 安装不包含 HTTP 栈或 PTY 辅助工具——这些是可选扩展。**Web Dashboard** 需要 FastAPI 和 Uvicorn（`web` 扩展）。**Chat** 标签页还需要 `ptyprocess` 来在伪终端后面启动嵌入式 TUI（POSIX 上的 `pty` 扩展）。使用以下命令同时安装：

```bash
cd ~/.hermes/hermes-agent && uv pip install -e ".[web,pty]"
```

`web` 扩展会引入 FastAPI/Uvicorn；`pty` 扩展会引入 `ptyprocess`（POSIX）或 `pywinpty`（原生 Windows——注意嵌入式 TUI 本身仍需要 WSL）。`cd ~/.hermes/hermes-agent && uv pip install -e ".[all]"` 包含两个扩展，如果你还需要消息/语音等功能，这是最简便的方式。

在没有依赖项的情况下运行 `hermes dashboard` 时，它会告诉你需要安装什么。如果前端尚未构建且 `npm` 可用，则会在首次启动时自动构建。

Chat 标签页是每次 `hermes dashboard` 启动的一部分——内嵌的浏览器聊天面板（通过 PTY/WebSocket 运行 TUI）始终可用，无需任何额外参数。

## 页面

### Status（状态）

首页显示你的安装的实时概览：

- **Agent 版本**和发布日期
- **Gateway 状态**——运行中/已停止、PID、已连接平台及其状态
- **活跃会话**——过去 5 分钟内活跃的会话数量
- **最近会话**——最近 20 个会话的列表，包含模型、消息数、token 用量和对话预览

状态页每 5 秒自动刷新一次。

### Chat（聊天）

**Chat** 标签页将完整的 Hermes TUI（与 `hermes --tui` 相同的界面）直接嵌入浏览器。你在终端 TUI 中能做的一切——斜杠命令、模型选择器、工具调用卡片、Markdown 流式输出、clarify/sudo/approval 提示、皮肤主题——在这里都完全一致，因为 Dashboard 运行的是真实的 TUI 二进制文件，并通过 [xterm.js](https://xtermjs.org/) 的 WebGL 渲染器以像素级精度渲染其 ANSI 输出。

**工作原理：**

- `/api/pty` 打开一个经 Dashboard 会话 token 认证的 WebSocket
- 服务器在 POSIX 伪终端后面启动 `hermes --tui`
- 按键传输到 PTY；ANSI 输出流式返回浏览器
- xterm.js 的 WebGL 渲染器将每个单元格绘制到整数像素网格；鼠标追踪（SGR 1006）、宽字符（Unicode 11）和方框绘制字形均原生渲染
- 调整浏览器窗口大小会通过 `@xterm/addon-fit` 插件调整 TUI 大小

**恢复已有会话：** 在 **Sessions** 标签页中，点击任意会话旁的播放图标（▶）。这会跳转到 `/chat?resume=<id>` 并以 `--resume` 参数启动 TUI，加载完整历史记录。

**会话切换器（右侧栏）：** Chat 标签页在终端右侧有一个类似 ChatGPT 风格的会话列表，让你无需离开页面即可切换对话。该栏顶部是模型选择器，下方就是会话列表；终端占据大部分屏幕。列表显示当前配置文件的最近会话——标题（回退为消息预览）、相对最后活跃时间、消息数以及非 CLI 会话的来源渠道。点击任意行即可原地恢复（终端以该会话的历史重新启动）；当前活跃会话高亮显示。**新聊天**开始一个新会话，刷新控件可重新拉取列表。该栏为只读切换——删除、重命名、导出和批量清理仍在 **Sessions** 标签页中。在窄屏幕上，它会折叠为侧滑面板。

**前置条件：**

- Node.js（与 `hermes --tui` 相同的要求；TUI 包在首次启动时构建）
- `ptyprocess`——由 `pty` 扩展安装（`cd ~/.hermes/hermes-agent && uv pip install -e ".[web,pty]"`，或 `[all]` 同时包含两者）
- POSIX 内核（Linux、macOS 或 WSL2）。`/chat` 终端面板特别需要 POSIX PTY——原生 Windows Python 没有等效实现，因此在原生 Windows 安装上，Dashboard 的其余部分（sessions、jobs、metrics、config editor）可以正常工作，但 `/chat` 标签页会显示提示，告知你需要使用 WSL2 才能使用该功能。

关闭浏览器标签页后，PTY 会在服务器端被干净地回收。重新打开会启动一个新会话。

要使 [Hermes Desktop](#将-hermes-desktop-连接到远程后端) 指向另一台机器上运行的 Dashboard 而非其自带的本地后端，请参见下面的远程后端部分。

### 将 Hermes Desktop 连接到远程后端

Hermes Desktop 通常启动自己的本地后端，但它也可以连接到另一台机器（VM、homelab 盒子等）上运行的 Dashboard，通过 **Settings → Gateway → Remote gateway**。这是最常见的"Desktop 显示后端已就绪但聊天从不工作"问题的来源，因为 Desktop 的就绪检查验证的内容少于实时聊天连接实际需要的条件。

:::info 前置条件：远程主机上必须运行 `hermes dashboard`
Desktop 连接的"远程后端"**就是**远程机器上运行的 `hermes dashboard` 进程——与本文档描述的服务器完全相同。在以下任何步骤起作用之前，它必须已启动并可访问；Desktop 是连接到它，而不是为你启动它。让它在 `systemd`/`tmux` 等下面保持运行，以便在注销和重启后继续存活。**Gateway**（Telegram/Discord/Slack 等）是一个**独立的**长期运行进程——如果你依赖消息渠道，请单独启动它；Desktop 应用连接的不是它。
:::

Desktop 的"远程后端就绪"探测只访问 `GET /api/status`，这是一个公开端点——只要主机上有*任何* Dashboard 在运行它就会应答。实时聊天连接是一个**独立的** WebSocket 连接到 `/api/ws`（以及 `/api/pty`），而该 socket 还受状态探测从未触及的两个检查门控：

1. **你必须通过认证。** 当 Dashboard 绑定到非回环地址时，它会启用认证门。用用户名和密码保护它（内置的[用户名/密码提供商](#用户名密码提供商无-oauth-idp)）；Desktop 登录一次，然后通过一次性票据复用到 WebSocket。如果没有配置提供商，非回环 Dashboard **在启动时就会失败关闭**。
2. **绑定主机必须允许客户端并匹配 Host 头。** 回环绑定（`127.0.0.1`）只接受回环客户端，因此无论凭据如何，远程机器在 socket 层就会被拒绝。绑定到非回环地址（`--host 0.0.0.0`），使对端 IP 检查允许远程客户端通过。你在 Desktop 中输入远程 URL 时必须使用与 Dashboard 绑定相同的主机来访问它——DNS 重新绑定防护要求 Host 头匹配。

#### 远程 Dashboard 设置

设置用户名和密码，然后将 Dashboard 绑定到可达地址运行。对于 `systemd` 服务：

```ini
[Service]
EnvironmentFile=%h/.hermes/.env
ExecStart=/path/to/venv/bin/python -m hermes_cli.main dashboard \
    --host 0.0.0.0 --port 9119 --no-open
```

`~/.hermes/.env` 包含：

```bash
HERMES_DASHBOARD_BASIC_AUTH_USERNAME=admin
HERMES_DASHBOARD_BASIC_AUTH_PASSWORD=choose-a-strong-password
HERMES_DASHBOARD_BASIC_AUTH_SECRET=<32+ 随机字节; openssl rand -base64 32>
```

然后在 Desktop 中输入**远程 URL**（例如 `http://VM_IP:9119`）并用该用户名和密码**登录**。有关完整配置，请参见[用户名/密码提供商](#用户名密码提供商无-oauth-idp)部分。

:::tip 确认门已启用再重试 Desktop
在任何机器上检查 Dashboard 是否通告了用户名/密码提供商：

```bash
curl -s http://VM_IP:9119/api/status | jq '.auth_required, .auth_providers'
# true
# ["basic"]
```

- `auth_required: true` 且提供商标记中包含 `"basic"` → Desktop 的**登录**流程可以工作。
- `auth_required: false` → 绑定是回环地址，或门未启用。绑定到非回环地址。
- `auth_required: true` 但没有 `"basic"` 提供商 → 用户名/密码环境变量未加载。先修复它们。
:::

如果 `/api/status` 显示门已启用且有 `"basic"` 提供商，但 Desktop 在登录后*仍然*无法连接，问题超出了基本设置范围——获取最新的 `desktop.log`（Settings → Gateway → Open logs）以及同一重试窗口内的 Dashboard 日志，查看 `/api/ws` 关闭代码（4403 = 聊天 WS 被请求守卫拒绝，例如 Host/peer 不匹配；4401 = WS 票据未通过认证）。

### Config（配置）

`config.yaml` 的表单式编辑器。所有 150+ 个配置字段均从 `DEFAULT_CONFIG` 自动发现，并按标签页分类组织：

![Config 管理页——左侧分类筛选器，右侧自动发现的字段](/img/dashboard/admin-config.png)

- **model** — 默认模型、提供商、基础 URL、推理设置
- **terminal** — 后端（local/docker/ssh/modal）、超时、Shell 偏好
- **display** — 皮肤、工具进度、恢复显示、spinner 设置
- **agent** — 最大迭代次数、gateway 超时、服务层级
- **delegation** — 子 agent 限制、推理力度
- **memory** — 提供商选择、上下文注入设置
- **approvals** — 危险命令审批模式（smart/manual/off）
- 更多——config.yaml 的每个部分都有对应的表单字段

具有已知有效值的字段（terminal 后端、皮肤、审批模式等）渲染为下拉菜单。布尔值渲染为开关。其余均为文本输入框。

**操作：**

- **Save** — 立即将更改写入 `config.yaml`
- **Reset to defaults** — 将所有字段恢复为默认值（点击 Save 前不会保存）
- **Export** — 将当前配置下载为 JSON
- **Import** — 上传 JSON 配置文件以替换当前值

:::tip
配置更改在下一次 agent 会话或 gateway 重启时生效。Web Dashboard 编辑的是 `hermes config set` 和 gateway 读取的同一个 `config.yaml` 文件。
:::

### API Keys（API 密钥）

管理存储 API 密钥和凭据的 `.env` 文件。密钥按类别分组：

- **LLM Providers** — OpenRouter、Anthropic、OpenAI、DeepSeek 等
- **Tool API Keys** — Browserbase、Firecrawl、Tavily、ElevenLabs 等
- **Messaging Platforms** — Telegram、Discord、Slack bot token 等
- **Agent Settings** — 非敏感环境变量，如 `API_SERVER_ENABLED`

每个密钥显示：
- 是否已设置（带有值的脱敏预览）
- 用途说明
- 提供商注册/密钥页面的链接
- 用于设置或更新值的输入框
- 删除按钮

高级/不常用的密钥默认隐藏，可通过开关显示。

### Sessions（会话）

浏览和检查所有 agent 会话。每行显示会话标题、来源平台图标（CLI、Telegram、Discord、Slack、cron）、模型名称、消息数、工具调用数以及最后活跃时间。实时会话以脉冲徽章标记。

- **Search** — 使用 FTS5 对所有消息内容进行全文搜索。结果显示高亮片段，展开时自动滚动到第一条匹配消息。
- **Stats** — 汇总栏显示总会话数、存储中活跃数量、归档数量、总消息数以及按来源的细分。
- **Expand** — 点击会话以加载完整消息历史。消息按角色（user、assistant、system、tool）用颜色区分，并以带语法高亮的 Markdown 渲染。
- **Tool calls** — 包含工具调用的 assistant 消息显示可折叠块，包含函数名和 JSON 参数。
- **Rename** — 原地设置或清除会话标题（铅笔图标）。
- **Export** — 将会话（元数据 + 完整消息历史）下载为 JSON（下载图标）。
- **Prune** — 顶部栏的"Prune old sessions"按钮删除结束时间早于 N 天的会话。
- **Delete** — 使用垃圾桶图标删除会话及其消息历史。

![Sessions 管理页——统计栏、prune 按钮，以及每行的重命名/导出/删除](/img/dashboard/admin-sessions.png)

### Logs（日志）

查看 agent、gateway 和错误日志文件，支持过滤和实时追踪。

- **File** — 在 `agent`、`errors` 和 `gateway` 日志文件之间切换
- **Level** — 按日志级别过滤：ALL、DEBUG、INFO、WARNING 或 ERROR
- **Component** — 按来源组件过滤：all、gateway、agent、tools、cli 或 cron
- **Lines** — 选择显示行数（50、100、200 或 500）
- **Auto-refresh** — 切换实时追踪，每 5 秒轮询新日志行
- **Color-coded** — 日志行按严重程度着色（错误为红色，警告为黄色，debug 为暗色）

### Analytics（分析）

基于会话历史计算的用量和成本分析。选择时间段（7、30 或 90 天）查看：

- **Summary cards** — 总 token 数（输入/输出）、缓存命中率、总估算或实际成本，以及总会话数和日均值
- **Daily token chart** — 堆叠柱状图，显示每日输入和输出 token 用量，悬停提示显示明细和成本
- **Daily breakdown table** — 每日日期、会话数、输入 token、输出 token、缓存命中率和成本
- **Per-model breakdown** — 显示每个使用模型的会话数、token 用量和估算成本的表格

### Cron（定时任务）

创建和管理按定期计划运行 agent prompt 的定时任务。

- **Create** — 填写名称（可选）、prompt、cron 表达式（如 `0 9 * * *`）和投递目标（local、Telegram、Discord、Slack 或 email）
- **Job list** — 每个任务显示其名称、prompt 预览、计划表达式、状态徽章（enabled/paused/error）、投递目标、上次运行时间和下次运行时间
- **Pause / Resume** — 在活跃和暂停状态之间切换任务
- **Edit** — 打开预填模态框以更改任务的 prompt、计划、名称或投递目标
- **Trigger now** — 在正常计划之外立即执行任务
- **Delete** — 永久删除定时任务

### Profiles（配置文件）

创建和管理[配置文件](../profiles.md)——具有独立配置、技能和会话的隔离 Hermes 实例。

- **Profile cards** — 每个显示其模型/提供商、技能数量、gateway 状态、描述和徽章（active、default、alias）
- **Create** — 名称 + 可选克隆默认配置/克隆所有/不包含内置技能、描述和模型；专用的 Profile Builder 页面（`/profiles/new`）提供完整流程（模型、MCP、技能）
- **Manage skills & tools** — 跳转到限定于该配置文件的 Skills 页面（设置侧边栏配置文件切换器）
- **Set as active** — 切换粘性默认值，**未来 CLI/gateway 运行**将选择该配置文件（同 `hermes profile use`）。这*不*改变 Dashboard 管理的内容——那是配置文件切换器的工作
- **Edit model / description / SOUL** — 内联编辑器，写入该配置文件
- **Rename / Delete** — 仅限命名配置文件

### Skills（技能）

浏览、搜索和切换已安装的技能与工具集，以及从中心安装新技能。技能从 `~/.hermes/skills/` 加载，并按类别分组。

- **Search** — 按名称、描述或类别过滤已安装的技能和工具集
- **Category filter** — 点击类别标签缩小列表范围（如 MLOps、MCP、Red Teaming、AI）
- **Toggle** — 使用开关启用或禁用单个技能。更改在下一次会话时生效。
- **Toolsets** — 单独的部分显示内置工具集（文件操作、Web 浏览等），包含其活跃/非活跃状态、设置要求和包含的工具列表
- **Browse hub** — 第三个视图在所有源中搜索技能中心（与 `hermes skills search` 相同），通过标识符安装任何结果并显示实时安装日志，还提供"Update all"按钮以刷新已安装的技能。

![Skills 管理页——Browse hub 视图：搜索、安装和更新](/img/dashboard/admin-skills-hub.png)

### MCP

无需 CLI 即可管理 [MCP](/integrations/mcp) 服务器。与 `hermes mcp` 读取的 `config.yaml` 中相同的 `mcp_servers` 配置块。

**你的 MCP 服务器：**

- **Add** — 注册 HTTP/SSE 服务器（URL）或 stdio 服务器（命令 + 参数），stdio 服务器可附带可选的 `KEY=VALUE` 环境变量
- **Enable / disable** — 在不删除的情况下开关服务器。禁用的服务器保留在配置中，以便以后重新启用。更改在下次 gateway 重启时生效。
- **Test** — 连接到服务器、列出其工具并断开连接——在 agent 依赖它之前验证连接
- **Remove** — 从配置中删除服务器
- 密钥形式的环境值在列表视图中被脱敏

**Catalog（目录）：** 浏览 Nous 批准的 MCP 服务器（内置的 `optional-mcps/` 目录），一键安装任意一个。需要 API 密钥的条目会内联提示输入；值写入 `.env`。这与 `hermes mcp catalog` / `hermes mcp install` 使用的是同一目录。

![MCP 管理页——你的服务器及启用/禁用开关，以及安装目录](/img/dashboard/admin-mcp.png)

### Webhooks（Webhook）

管理动态 [Webhook 订阅](/user-guide/messaging/webhooks)。webhook 平台必须先在消息设置中启用；页面会在未启用时显示提示。

- **Create** — 名称、描述、事件过滤器、投递目标、可选直接投递模式以及一条 agent prompt。创建时页面显示路由 URL 和一次性 HMAC 密钥供复制。
- **Enable / disable** — 开关订阅。禁用的路由保留在订阅文件中，但 gateway 会拒绝其传入事件（403）。Gateway 会热重载该文件，因此更改在下一个事件时生效——无需重启。
- **List** — 每个订阅显示其 URL、事件和投递目标
- **Delete** — 删除订阅

![Webhooks 管理页——带启用/禁用开关的订阅](/img/dashboard/admin-webhooks.png)

### Pairing（配对）

无需 CLI 即可批准和撤销消息用户——远程管理员如何将 Telegram/Discord 等用户加入配对网关。与 `hermes pairing` 完全一致。

- **Pending requests** — 每个显示平台、代码、用户和耗时，带有 Approve 按钮
- **Approved users** — 每个显示平台和用户，带有 Revoke 按钮
- **Clear pending** — 清除所有未完成的配对码

![Pairing 管理页](/img/dashboard/admin-pairing.png)

### Channels（消息渠道）

从浏览器连接 Hermes 到任何消息平台——与 `hermes setup gateway` 完全一致。页面列出每个受支持的渠道（Telegram、Discord、Slack、Matrix、Mattermost、WhatsApp、Signal、BlueBubbles/iMessage、Email、SMS/Twilio、DingTalk、飞书/Lark、WeCom、微信、QQ 机器人、元宝，以及 API 服务器和 webhook 端点）及其实时连接状态。

- **Configure** — 打开针对平台的表单，包含该渠道所需的字段（bot token、app token、服务器 URL、白名单等）。密钥渲染为密码输入框并脱敏存储；留空字段保留现有值。必填字段标记并验证。"Setup guide"链接指向该平台的凭据文档。
- **Enable / disable** — 开关渠道。凭据保留在磁盘上；仅更改活跃状态。
- **Test** — 检查渠道是否已配置、启用并向 gateway 报告实时连接。
- **Restart gateway** — 凭据写入 `~/.hermes/.env`，启用标志写入 `config.yaml`；gateway 在下一次重启时连接每个已启用的渠道，你可以直接从页面触发重启。

![Channels 管理页——每个消息平台带状态、启用开关和按平台的设置表单](/img/dashboard/admin-channels.png)

### System（系统）

一个整合的管理面板，用于安装范围的操作：

- **Host** — 实时系统统计：操作系统/内核、架构、主机名、Python 和 Hermes 版本、CPU 核心数 + 利用率、内存、Hermes home 的磁盘使用量、运行时间和负载均值。（CPU/内存/磁盘在安装 `psutil` 后显示；身份字段始终显示。）Hermes 版本显示**更新状态徽章**（最新 / 落后 N 个提交）和一个 **Check for updates** 按钮。当 git 或 pip 安装有可用更新时，**Update now** 按钮打开一个确认对话框——显示将要拉取的提交数量——然后在后台运行 `hermes update`。在 Docker/Nix/Homebrew 安装上，Dashboard 无法原地应用更新，因此显示正确的带外命令。
- **Nous Portal** — 登录状态、活跃推理提供商以及 Tool Gateway 路由表（哪些工具通过 Portal 运行 vs. 本地运行），带有管理订阅的链接。`hermes portal` 的只读镜像。
- **Skill curator** — 后台技能维护状态（活跃/暂停、间隔、上次运行时间）带暂停/恢复和立即运行按钮。`hermes curator` 的镜像。
- **Gateway** — 启动、停止和重启消息 gateway，带实时状态（运行中/已停止、PID、状态）。
- **Memory** — 选择外部 memory 提供商（或仅内置），重置内置的 `MEMORY.md` / `USER.md` 存储。
- **Credential pool** — 添加和删除 agent 轮换使用的 API 密钥（按提供商）。密钥在列表中脱敏；原始值仅在到达 agent 时可见。
- **Operations** — 运行 `doctor`、安全审计、创建备份、从备份归档恢复、更新技能、显示系统 prompt 大小明细、生成支持诊断包或迁移已弃用设置的配置。每个操作都启动一个后台动作，其实时日志流入页面。
- **Checkpoints** — 查看 `/rollback` 影子存储大小并清理它。
- **Shell hooks** — 列出已配置的 hook，其同意和执行状态；**创建** hook（事件、命令、匹配器、超时，带可选的同意授权）；删除 hook。Hook 运行任意命令，因此创建表单带有安全警告，hook 只有在同意被授予后才会触发。

![System 管理页——Host 统计和 Nous Portal 状态](/img/dashboard/admin-system-top.png)

![System 管理页——Skill curator、Gateway、Memory 和 Credential pool](/img/dashboard/admin-system-curator.png)

![System 管理页——Operations、Checkpoints 和 Shell hooks](/img/dashboard/admin-system-ops.png)

创建 shell hook（注意同意复选框和运行任意命令的警告）：

![新建 shell hook 模态框](/img/dashboard/admin-hook-create.png)

:::warning 安全提示
Web Dashboard 会读写包含 API 密钥和机密的 `.env` 文件。它默认绑定到 `127.0.0.1`——只能从本机访问。如果绑定到 `0.0.0.0`，网络上的任何人都可以查看和修改你的凭据。Dashboard 本身没有任何认证机制。
:::

## `/reload` 斜杠命令

Dashboard 还为交互式 CLI 添加了 `/reload` 斜杠命令。通过 Web Dashboard（或直接编辑 `.env`）更改 API 密钥后，在活跃的 CLI 会话中使用 `/reload` 即可获取更改，无需重启：

```
You → /reload
  Reloaded .env (3 var(s) updated)
```

这会将 `~/.hermes/.env` 重新读取到运行中进程的环境中。当你通过 Dashboard 添加了新的提供商密钥并希望立即使用时非常有用。

## REST API

Web Dashboard 暴露了一个供前端使用的 REST API。你也可以直接调用这些端点进行自动化操作：

:::tip 配置文件限定的端点
管理端点系列——`/api/config`、`/api/env`、`/api/skills`、`/api/tools/toolsets`、`/api/mcp` 和 `/api/model/{info,options,auxiliary,set}`——接受可选的 `?profile=<name>` 查询参数（或写入操作的 JSON 请求体中的 `"profile"` 字段），将读写限定于该配置文件的 `HERMES_HOME`。省略时使用 Dashboard 自身的配置文件。未知的配置文件名称返回 `404`。`/api/pty` WebSocket 也接受相同参数，以在所选的配置文件下启动聊天。
:::

### GET /api/status

返回 agent 版本、gateway 状态、平台状态和活跃会话数。

### GET /api/sessions

返回最近 20 个会话的元数据（模型、token 数、时间戳、预览）。

### GET /api/config

以 JSON 格式返回当前 `config.yaml` 内容。

### GET /api/config/defaults

返回默认配置值。

### GET /api/config/schema

返回描述每个配置字段的 schema——类型、描述、类别，以及适用时的选项。前端使用此 schema 为每个字段渲染正确的输入控件。

### PUT /api/config

保存新配置。请求体：`{"config": {...}}`。

### GET /api/env

返回所有已知环境变量，包含其设置/未设置状态、脱敏值、描述和类别。

### PUT /api/env

设置环境变量。请求体：`{"key": "VAR_NAME", "value": "secret"}`。

### DELETE /api/env

删除环境变量。请求体：`{"key": "VAR_NAME"}`。

### GET /api/sessions/\{session_id\}

返回单个会话的元数据。

### GET /api/sessions/\{session_id\}/messages

返回会话的完整消息历史，包含工具调用和时间戳。

### GET /api/sessions/search

对消息内容进行全文搜索。查询参数：`q`。返回匹配的会话 ID 和高亮片段。

### DELETE /api/sessions/\{session_id\}

删除会话及其消息历史。

### GET /api/logs

返回日志行。查询参数：`file`（agent/errors/gateway）、`lines`（数量）、`level`、`component`。

### GET /api/analytics/usage

返回 token 用量、成本和会话分析。查询参数：`days`（默认 30）。响应包含每日明细和按模型聚合数据。

### GET /api/cron/jobs

返回所有已配置的定时任务，包含其状态、计划和运行历史。

### POST /api/cron/jobs

创建新定时任务。请求体：`{"prompt": "...", "schedule": "0 9 * * *", "name": "...", "deliver": "local"}`。

### POST /api/cron/jobs/\{job_id\}/pause

暂停定时任务。

### POST /api/cron/jobs/\{job_id\}/resume

恢复已暂停的定时任务。

### POST /api/cron/jobs/\{job_id\}/trigger

在计划之外立即触发定时任务。

### DELETE /api/cron/jobs/\{job_id\}

删除定时任务。

### GET /api/skills

返回所有技能，包含其名称、描述、类别和启用状态。

### PUT /api/skills/toggle

启用或禁用技能。请求体：`{"name": "skill-name", "enabled": true}`。

### GET /api/tools/toolsets

返回所有工具集，包含其标签、描述、工具列表以及活跃/已配置状态。

### Admin 端点

以下端点为 MCP、Channels、Webhooks、Pairing 和 System 页面提供支持。它们与 `/api/` 的其他端点一样受同一认证门的保护。

| 方法和路径 | 用途 |
|---------------|---------|
| `GET /api/mcp/servers` | 列出已配置的 MCP 服务器（环境值脱敏） |
| `POST /api/mcp/servers` | 添加服务器。请求体：`{name, url?, command?, args?, env?, auth?}` |
| `POST /api/mcp/servers/{name}/test` | 连接、列出工具、断开连接 |
| `PUT /api/mcp/servers/{name}/enabled` | 启用/禁用服务器 |
| `DELETE /api/mcp/servers/{name}` | 删除服务器 |
| `GET /api/mcp/catalog` | 浏览 Nous 批准的 MCP 目录 |
| `POST /api/mcp/catalog/install` | 安装目录条目（附带所需的 env） |
| `GET /api/messaging/platforms` | 列出每个消息渠道及其状态和按平台的设置字段 |
| `PUT /api/messaging/platforms/{id}` | 配置渠道。请求体：`{enabled?, env?, clear_env?}`（env 写入 `.env`，enabled 写入 `config.yaml`） |
| `POST /api/messaging/platforms/{id}/test` | 报告渠道是否已配置、启用和连接 |
| `GET /api/pairing` | 列出待处理 + 已批准的消息用户 |
| `POST /api/pairing/approve` | 批准码。请求体：`{platform, code}` |
| `POST /api/pairing/revoke` | 撤销用户。请求体：`{platform, user_id}` |
| `POST /api/pairing/clear-pending` | 清除所有未完成的配对码 |
| `GET /api/webhooks` | 列出订阅 + 平台启用状态 |
| `POST /api/webhooks` | 创建订阅（返回一次性密钥） |
| `DELETE /api/webhooks/{name}` | 删除订阅 |
| `GET /api/credentials/pool` | 列出池化的轮换密钥（脱敏） |
| `POST /api/credentials/pool` | 添加密钥。请求体：`{provider, api_key, label?}` |
| `DELETE /api/credentials/pool/{provider}/{index}` | 删除密钥（1-based 索引） |
| `GET /api/memory` | 活跃提供商 + 可用提供商 + 内置文件大小 |
| `PUT /api/memory/provider` | 选择提供商（空值 = 仅内置） |
| `POST /api/memory/reset` | 重置内置记忆。请求体：`{target: all\|memory\|user}` |
| `POST /api/gateway/start` · `/stop` · `/restart` | Gateway 生命周期（后台运行） |
| `POST /api/ops/doctor` · `/security-audit` · `/backup` · `/import` | 诊断和维护（后台运行；通过 `/api/actions/{name}/status` 追踪输出） |
| `GET /api/ops/hooks` | 已配置的 shell hook + 白名单状态 |
| `GET /api/ops/checkpoints` · `POST .../prune` | 检查/清理 `/rollback` 存储 |
| `POST /api/ops/hooks` · `DELETE /api/ops/hooks` | 创建/删除 shell hook（需同意） |
| `GET /api/system/stats` | 主机统计——操作系统、CPU、内存、磁盘、运行时间 |
| `GET /api/hermes/update/check` | 报告更新可用性（落后提交数、安装方式），不执行更新。对于 git/pip 安装且落后的情况，还返回 `commits` 列表（`sha`、`summary`、`author`、`at`）。`?force=1` 可绕过 6h 缓存 |
| `GET /api/curator` · `PUT .../paused` · `POST .../run` | 技能 curator 状态 + 暂停/恢复 + 运行 |
| `GET /api/portal` | Nous Portal 认证 + Tool Gateway 路由（只读） |
| `POST /api/ops/prompt-size` · `/dump` · `/config-migrate` | 诊断（后台运行） |
| `PUT /api/webhooks/{name}/enabled` | 启用/禁用 webhook 路由 |
| `POST /api/skills/hub/install` · `/uninstall` · `/update` | Skills hub 操作（后台运行） |
| `GET /api/skills/hub/search` | 在所有源中搜索技能 center |
| `GET /api/sessions/stats` | 会话存储统计 |
| `PATCH /api/sessions/{id}` | 重命名/归档会话 |
| `GET /api/sessions/{id}/export` | 导出会话（元数据 + 消息）为 JSON |
| `POST /api/sessions/prune` | 删除结束时间早于 N 天的会话 |
| `PUT /api/cron/jobs/{id}` | 编辑定时任务的 prompt/计划/名称/投递目标 |

## 认证（门控模式）

当 Dashboard 绑定到公共或非回环地址——任何非 `127.0.0.1` / `localhost` 的地址时——Hermes Agent 会启用认证门。每个请求必须携带已验证的会话 cookie，否则会被重定向到登录页面。内置三个提供商：

- **[用户名/密码](#用户名密码提供商无-oauth-idp)**——在自托管/内部部署/homelab Dashboard 上启用认证的最简单方式。无需外部身份提供商。**仅在受信任网络或 VPN 后方使用——不适用于公共互联网暴露。**
- **[OAuth (Nous Portal)](#默认提供商-nous-research)**——适用于托管部署和任何可通过公共互联网访问的 Dashboard，也是[远程 Hermes Desktop 连接](#将-hermes-desktop-连接到远程后端)的推荐方式。每次登录都通过你的 Nous 账户验证，因此该提供商适合面向互联网使用。
- **[自托管 OIDC](#自托管-oidc-提供商)**——用于通过标准 OpenID Connect（Keycloak、Auth0、Okta、Google 通过 OIDC 桥接等）使用你自己的身份提供商。不涉及 Nous Portal；在由合规 OIDC 服务器前端保护时适合公共互联网暴露。

绑定到回环地址的操作员自有 Dashboard 不受影响——无需认证，无登录页面。

### 何时启用门

| 标志 | 认证门 | 用途 |
|-------|-----------|----------|
| `hermes dashboard`（默认——绑定到 `127.0.0.1`） | 关闭 | 本地开发 |
| `hermes dashboard --host 0.0.0.0` | **开启** | 远程/生产——使用用户名/密码提供商或 OAuth 保护 |

门的开启条件是：

1. 绑定主机不是 `127.0.0.1`、`::1`、`localhost` 或 `0.0.0.0`，并且
2. `--insecure` 标志**未**设置。

:::danger `--insecure` 完全禁用认证
`--insecure` 跳过认证门，提供一个未经身份验证的 Dashboard，它可以读写你的 `.env`（API 密钥、机密）并运行 agent 命令。**不要将其用于远程连接。** 要将 Dashboard 暴露给另一台机器，请配置[用户名/密码提供商](#用户名密码提供商无-oauth-idp)（或 OAuth）并保持 `--insecure` 关闭。该标志仅作为完全受信任、已防火墙隔离的单主机网络上的最后逃生口而存在。
:::

### 失败关闭语义

如果门会启用但**没有**注册 `DashboardAuthProvider`（没有 Nous 插件、没有自定义插件），`hermes dashboard` 将拒绝绑定并显示明确的错误消息。没有"默认拒绝但接受一切"的后备——配置错误的门控 Dashboard 永远不会启动。

当你**交互式**（真实终端）运行 `hermes dashboard --host 0.0.0.0` 且尚未配置任何提供商时，Hermes 不会仅仅失败——它会在现场提供设置选项：选择**用户名和密码**（写入 `dashboard.basic_auth` 到 `config.yaml`，几秒钟内即可运行）或 **OAuth**（指向 `hermes dashboard register`）。非交互式调用者——Docker/s6、CI、管道运行——跳过提示并命中上述的失败关闭错误，因此无人值守部署在没有认证的情况下仍不会启动。

### 默认提供商：Nous Research

内置的 `plugins/dashboard_auth/nous` 插件**始终安装**并自动加载。当配置了客户端 ID 时，它会自动注册一个名为 `nous` 的 `DashboardAuthProvider`。

由于每次登录都通过 Nous Portal 验证并受你的 Nous 账户保护，**Nous 提供商是适合向公共互联网暴露 Dashboard 的提供商。**

#### 注册 Dashboard

要使用 Nous 提供商，你需要一个 OAuth 客户端 ID（格式为 `agent:{id}`）。有两种方式获取：

- **CLI——`hermes dashboard register`。** 在 Dashboard 所在的主机上运行。它会解析你现有的 Nous 登录（如果尚未登录，先运行 `hermes setup`），在 Portal 注册一个自托管的 OAuth 客户端，并将 `HERMES_DASHBOARD_OAUTH_CLIENT_ID` 写入 `~/.hermes/.env`。可选标志：`--name`（人类可读标签，否则自动生成）和 `--redirect-uri`（面向互联网主机的公共 HTTPS 回调 URL）。

  ```bash
  hermes dashboard register
  # ✓ Registered dashboard "swift_falcon"
  # …writes HERMES_DASHBOARD_OAUTH_CLIENT_ID to ~/.hermes/.env
  ```

- **GUI——Local Dashboards 页面。** 在 Nous Portal 中打开 [`/local-dashboards`](https://portal.nousresearch.com/local-dashboards)，通过浏览器注册、命名、管理和撤销自托管 Dashboard。将生成的 `agent:{id}` 客户端 ID 复制到 `HERMES_DASHBOARD_OAUTH_CLIENT_ID`（环境变量）或 `dashboard.oauth.client_id`（config.yaml）。这也是你撤销通过 CLI 注册的 Dashboard 的地方。

#### 配置

该插件从两个来源读取，环境变量非空时优先：

**`config.yaml`**——规范来源：

```yaml
dashboard:
  oauth:
    client_id: agent:01HXYZ…             # 启用门的必需项
```

**环境变量**——操作员覆盖：

| 环境变量 | 覆盖项 | 格式 | 由谁配置 |
|---------|-----------|--------|----------------|
| `HERMES_DASHBOARD_OAUTH_CLIENT_ID` | `dashboard.oauth.client_id` | `agent:{instance_id}` | `hermes dashboard register` |

按照 Hermes Agent 的惯例（`~/.hermes/.env` 仅用于 API 密钥/机密），**`config.yaml` 是本地开发、本地部署以及任何你直接控制的部署中设置这些值的推荐位置**。环境变量路径的存在是为了让托管平台的密钥注入可以在不编辑镜像内 `config.yaml` 的情况下推送每个部署的 `client_id`——这是其主要用途。

空环境值被视为未设置，因此已配置但未填充的平台密钥不会意外遮盖有效的 `config.yaml` 条目。

如果两个来源都没有提供 client_id，插件会报告具体原因，Dashboard 的失败关闭绑定错误会准确告诉你需要修复什么：

```
Refusing to bind dashboard to 0.0.0.0 — the OAuth auth gate engages on
non-loopback binds, but no auth providers are registered.

Bundled providers reported these issues:
  • nous: HERMES_DASHBOARD_OAUTH_CLIENT_ID is not set (and
    dashboard.oauth.client_id in config.yaml is empty). The Nous Portal
    provisions this env var (shape 'agent:{instance_id}') when it
    deploys a Hermes Agent instance — set it to your provisioned
    client id (either as an env var or under dashboard.oauth.client_id
    in config.yaml), or pass --insecure to skip the OAuth gate entirely.

Or pass --insecure to skip the auth gate (NOT recommended on untrusted
networks).
```

#### 操作示例：Nous Research

从已登录的 Hermes 安装到 Nous 门控的 Dashboard，只需三步。

**1. 登录并注册 Dashboard。** `hermes dashboard register` 使用你现有的 Nous 登录来配置 OAuth 客户端并将 `HERMES_DASHBOARD_OAUTH_CLIENT_ID` 写入 `~/.hermes/.env`：

```bash
hermes setup            # 如果你尚未登录 Nous Portal
hermes dashboard register
# ✓ Registered dashboard "swift_falcon"
# …writes HERMES_DASHBOARD_OAUTH_CLIENT_ID to ~/.hermes/.env
```

**2. 在可达地址上运行 Dashboard。** 非回环绑定（不使用 `--insecure`）会启用 OAuth 门，刚刚写入的 `client_id` 激活了 `nous` 提供商：

```bash
hermes dashboard --host 0.0.0.0 --port 9119 --no-open
```

**3. 登录。** 打开 `http://<host>:9119/`，你将被重定向到 `/login`。点击 **Sign in with Nous Research** → 在 Portal 认证 → 返回已认证的 Dashboard。在任何机器上验证门的状态：

```bash
curl -s http://<host>:9119/api/status | jq '.auth_required, .auth_providers'
# true
# ["nous"]
```

`GET /api/auth/me` 返回已验证的会话（`provider: nous`）。对于面向互联网的主机，使用 `--redirect-uri https://hermes.example.com/auth/callback` 注册，并设置 `HERMES_DASHBOARD_PUBLIC_URL`，使 OAuth 回调解析到你的公共 URL（参见[公共 URL 覆盖](#公共-url-覆盖)）。

### 用户名/密码提供商（无 OAuth IDP）

如果你不想设置 OAuth 身份提供商——自托管的"只是给 Dashboard 加个密码"部署——内置的 `plugins/dashboard_auth/basic` 插件会注册一个名为 `basic` 的 `DashboardAuthProvider`，使用**用户名和密码**进行认证，而不是 OAuth 重定向。

它接入与 OAuth 提供商相同的认证门：门在非回环绑定（不使用 `--insecure`）时启用，登录页面为此提供商渲染凭据表单（而不是"Log in with X"按钮），登录后的所有内容——会话 cookie、透明刷新、WS 票据、注销、审计日志——与 OAuth 路径完全相同。会话是提供商自己生成的无状态 HMAC 签名令牌，因此**没有数据库，没有外部 IDP**。密码哈希使用标准库 `scrypt`（无第三方依赖）。

:::warning 仅在受信任网络上使用——不适用于公共互联网
用户名/密码提供商适用于**受信任网络**上的自托管/本地部署/homelab Dashboard，或仅通过 **VPN** 可达的场景。它使用单一共享凭据进行保护，没有外部身份提供商、MFA 或每个用户的账户，因此**不适合直接向公共互联网暴露 Dashboard**。对于面向互联网的 Dashboard，请改用 [Nous Research 提供商](#默认提供商-nous-research)（或你自己的[自托管 OIDC](#自托管-oidc-提供商)/[自定义 OAuth](#自定义提供商) 提供商）。
:::

#### 配置

与 Nous 提供商一样，它从 `config.yaml`（规范来源）读取，环境变量非空时优先。仅当配置了 `username` 加上 `password_hash`（推荐）或 `password` 时才激活——否则无效，OAuth 用户和回环/`--insecure` 操作员不受影响。

**`config.yaml`：**

```yaml
dashboard:
  basic_auth:
    username: admin
    # 推荐——不在静态存储中保存明文。计算方式：
    #   python -c "from plugins.dashboard_auth.basic import hash_password; print(hash_password('PW'))"
    password_hash: "scrypt$16384$8$1$…$…"
    # ...或明文密码（加载时在内存中哈希；静态存储安全性较低）：
    # password: "s3cret"
    secret: "<32+ 随机字节，base64 或 hex>"  # 令牌签名密钥
    session_ttl_seconds: 43200                    # 可选；访问令牌有效期（默认 12h）
```

**环境变量覆盖：**

| 环境变量 | 覆盖项 | 说明 |
|---------|-----------|-------|
| `HERMES_DASHBOARD_BASIC_AUTH_USERNAME` | `dashboard.basic_auth.username` | 激活必需 |
| `HERMES_DASHBOARD_BASIC_AUTH_PASSWORD_HASH` | `dashboard.basic_auth.password_hash` | 推荐（静态存储无明文） |
| `HERMES_DASHBOARD_BASIC_AUTH_PASSWORD` | `dashboard.basic_auth.password` | 明文；**优先级高于配置中的 `password_hash`**，因此你可以通过环境变量轮换密码 |
| `HERMES_DASHBOARD_BASIC_AUTH_SECRET` | `dashboard.basic_auth.secret` | 令牌签名密钥 |
| `HERMES_DASHBOARD_BASIC_AUTH_TTL_SECONDS` | `dashboard.basic_auth.session_ttl_seconds` | 访问令牌有效期 |

:::caution 设置显式 `secret` 以确保会话稳定
当 `secret` 为空时，将生成每个进程随机的签名密钥。这对单个进程没问题，但意味着**每次重启都会使所有会话失效**，且会话**不能跨多个 worker**。为重启持久 / 多 worker 部署设置显式 `secret`。
:::

`/auth/password-login` 端点按客户端 IP 进行速率限制（默认 10 次/分钟 → HTTP 429），对于未知用户和错误密码均返回相同的通用 `401 Invalid credentials`，因此不能用作用户名枚举的预言机。

#### 操作示例：用户名/密码

从零开始到在受信任网络上运行密码门控的 Dashboard，只需三步。

**1. 在 `~/.hermes/.env` 中设置凭据。** 对密码进行哈希处理，使静态存储中不留明文，并设置稳定的签名密钥，使会话在重启后持续有效：

```bash
# 计算所选密码的 scrypt 哈希：
HASH=$(python -c "from plugins.dashboard_auth.basic import hash_password; print(hash_password('choose-a-strong-password'))")

cat >> ~/.hermes/.env <<EOF
HERMES_DASHBOARD_BASIC_AUTH_USERNAME=admin
HERMES_DASHBOARD_BASIC_AUTH_PASSWORD_HASH=$HASH
HERMES_DASHBOARD_BASIC_AUTH_SECRET=$(openssl rand -base64 32)
EOF
chmod 600 ~/.hermes/.env
```

**2. 在可达地址上运行 Dashboard。** 非回环绑定（不使用 `--insecure`）会启用认证门，用户名 + 哈希激活 `basic` 提供商：

```bash
hermes dashboard --host 0.0.0.0 --port 9119 --no-open
```

**3. 登录。** 打开 `http://<host>:9119/`，你将被重定向到 `/login`——一个**凭据表单**（而不是"Sign in with X"按钮）。输入 `admin` / 你的密码 → 进入已认证的 Dashboard。在任何机器上验证门的状态：

```bash
curl -s http://<host>:9119/api/status | jq '.auth_required, .auth_providers'
# true
# ["basic"]
```

`GET /api/auth/me` 返回已验证的会话（`provider: basic`）。请将其保持在 VPN 后方——参见上面的警告；对于公共主机，请改用 [Nous Research](#默认提供商-nous-research) 或[自托管 OIDC](#自托管-oidc-提供商) 提供商。

#### 编写自己的密码提供商

`basic` 只是一个扩展点的实现。任何插件都可以注册密码提供商：在你的 `DashboardAuthProvider` 子类上设置 `supports_password = True` 并实现 `complete_password_login(*, username, password) -> Session`（拒绝时抛出 `InvalidCredentialsError`，后备存储故障时抛出 `ProviderError`）。纯密码提供商的 OAuth `start_login` / `complete_login` 方法可以保留为 `NotImplementedError` 桩。这是 LDAP 绑定、凭据数据库或任何其他非重定向认证方案的路径——框架为你处理表单、路由、cookie 和刷新。

### 自托管 OIDC 提供商

如果你运行自己的身份提供商，内置的 `plugins/dashboard_auth/self_hosted` 插件使用**标准 OpenID Connect** 对 Dashboard 进行身份验证——无需每个 IDP 的代码，不涉及 Nous Portal。已验证可与任何兼容的 OIDC 服务器配合使用：

> **Authentik · Keycloak · Zitadel · Authelia · Auth0 · Okta · Google · …**

与 Nous 提供商一样，它自动加载并仅在配置完成后才注册自身，因此对于回环 / `--insecure` Dashboard 而言它是无效的。

#### 配置

配置一个 **issuer** 和一个 **client_id**（公共 PKCE 客户端——无需客户端密钥）。插件从 `{issuer}/.well-known/openid-configuration` 获取 IDP 的 `authorization_endpoint`、`token_endpoint` 和 `jwks_uri`，因此你永远不需要硬编码端点 URL。

**`config.yaml`**——规范来源：

```yaml
dashboard:
  oauth:
    provider: self-hosted
    self_hosted:
      issuer: https://auth.example.com/application/o/hermes/   # 必需
      client_id: hermes-dashboard                              # 必需
      scopes: "openid profile email"                           # 可选（此为默认值）
```

**环境变量**——操作员覆盖（非空时环境变量优先级高于 `config.yaml`；空值视为未设置）：

| 环境变量 | 覆盖项 | 说明 |
|---------|-----------|-------|
| `HERMES_DASHBOARD_OIDC_ISSUER` | `dashboard.oauth.self_hosted.issuer` | OIDC issuer URL——必需 |
| `HERMES_DASHBOARD_OIDC_CLIENT_ID` | `dashboard.oauth.self_hosted.client_id` | 公共客户端 ID——必需 |
| `HERMES_DASHBOARD_OIDC_SCOPES` | `dashboard.oauth.self_hosted.scopes` | 默认为 `openid profile email` |

在你的 IDP 中，注册一个使用授权码 + PKCE（S256）授权类型的**公共**应用/客户端，并将 Dashboard 的回调添加为允许的重定向 URI。回调地址为 `<dashboard public URL>/auth/callback`（参见[公共 URL 覆盖](#公共-url-覆盖)了解 Dashboard 如何在代理后派生其公共 URL）。

#### 验证内容

提供商针对发现的 `jwks_uri` 验证 OpenID Connect **ID token**（RS256/ES256），其中 `iss` 和 `aud` 声明锁定为你配置的 `issuer` 和 `client_id`。标准 OIDC 声明映射到 Dashboard 会话：

| 会话字段 | 声明 |
|---------------|----------|
| `user_id` | `sub`（必需） |
| `email` | `email` |
| `display_name` | `name` → `preferred_username` → `nickname` → `email` |
| `org_id` | `org_id` / `organization`，否则为已加入的 `groups` |

ID token 是建立身份的依据——access token 被视为不透明的（OIDC 规范不要求其为 JWT）。端点 URL 必须是 HTTPS（回环 `http://` 允许用于本地开发 IDP），并且发现文档声明的 `issuer` 必须与你配置的一致（容忍尾部斜杠差异）。当 IDP 发放 refresh token 时，通过标准的 `refresh_token` 授权类型用于静默重新认证；注销在发现文档声明时调用 IDP 的 RFC 7009 `revocation_endpoint`。

> **机密客户端**（带有 `client_secret` 的）尚不支持——请配置公共 + PKCE 客户端，这是浏览器面向 Dashboard 的典型选择。

#### 操作示例：Keycloak

[Keycloak](https://www.keycloak.org/) 是为本地测试搭建自托管 OIDC 服务器最容易的方式之一——它以开发模式（内存数据库）作为单容器运行，并展示教科书式的 OIDC 发现。本教程可让你在几分钟内从零开始拥有一个工作的 Dashboard 登录。

**1. 运行预配置领域的 Keycloak。** 将此领域导出保存为 `realm-hermes.json`——它定义了一个 `hermes` 领域、一个 **公共 PKCE 客户端**（`hermes-dashboard`）以及一个测试用户，全部在启动时导入，无需在管理 UI 中点击任何内容：

```json
{
  "realm": "hermes",
  "enabled": true,
  "clients": [
    {
      "clientId": "hermes-dashboard",
      "name": "Hermes Agent Dashboard",
      "enabled": true,
      "publicClient": true,
      "standardFlowEnabled": true,
      "protocol": "openid-connect",
      "redirectUris": ["http://localhost:9119/auth/callback"],
      "webOrigins": ["http://localhost:9119"],
      "attributes": { "pkce.code.challenge.method": "S256" }
    }
  ],
  "users": [
    {
      "username": "testuser",
      "enabled": true,
      "emailVerified": true,
      "email": "testuser@example.com",
      "firstName": "Test",
      "lastName": "User",
      "credentials": [
        { "type": "password", "value": "testpassword", "temporary": false }
      ]
    }
  ]
}
```

启动它（Keycloak 26+），将该文件挂载到导入目录：

```bash
docker run --rm -p 8080:8080 \
  -e KC_BOOTSTRAP_ADMIN_USERNAME=admin \
  -e KC_BOOTSTRAP_ADMIN_PASSWORD=admin \
  -v "$PWD/realm-hermes.json:/opt/keycloak/data/import/realm-hermes.json:ro" \
  quay.io/keycloak/keycloak:26.0 \
  start-dev --import-realm
```

启动后，领域将在 `http://localhost:8080/realms/hermes/.well-known/openid-configuration` 处公开标准 OIDC 发现（issuer `http://localhost:8080/realms/hermes`）。管理控制台位于 `http://localhost:8080/`（`admin` / `admin`）。

**2. 将 Dashboard 指向 Keycloak。** 自托管插件允许回环 `http://` issuer（任何非回环 issuer 都需要 HTTPS），因此本地 Keycloak 可直接使用：

```bash
export HERMES_DASHBOARD_OIDC_ISSUER="http://localhost:8080/realms/hermes"
export HERMES_DASHBOARD_OIDC_CLIENT_ID="hermes-dashboard"
export HERMES_DASHBOARD_PUBLIC_URL="http://localhost:9119"
hermes dashboard --host 0.0.0.0 --port 9119 --no-open
```

`HERMES_DASHBOARD_PUBLIC_URL` 告诉 Dashboard 其 OAuth 回调为 `http://localhost:9119/auth/callback`——即是上面领域中注册的重定向 URI。绑定到 `0.0.0.0`（非回环绑定）且不使用 `--insecure`，这是启用 OAuth 门的方式。

**3. 登录。** 打开 `http://localhost:9119/`，你将被重定向到 `/login`。点击 **Sign in with Self-Hosted OIDC** → 在 Keycloak 上以 `testuser` / `testpassword` 认证 → 返回已认证的 Dashboard。侧边栏显示 `Logged in as Test User via self-hosted`，`GET /api/auth/me` 返回已验证的会话（`provider: self-hosted`、`email: testuser@example.com`）。

> 如果你在不同主机/端口上绑定或浏览，请将该来源的 `…/auth/callback` 添加到客户端的 **Valid redirect URIs**（Keycloak 管理控制台 → Clients → hermes-dashboard → Settings）。相同的模式适用于 Authentik、Zitadel、Authelia 和其他 OIDC 服务器——只有 issuer URL 和客户端注册 UI 不同。

### 公共 URL 覆盖

默认情况下，Dashboard 从请求中重建 OAuth 回调 URL——`X-Forwarded-Host` + `X-Forwarded-Proto` + `X-Forwarded-Prefix`（当 uvicorn 配置了 `proxy_headers=True` 时，`start_server` 会在启用认证门时启用此项）。在正确设置所有三个头的反向代理后面，这开箱即用。

对于不能可靠转发这些头的反向代理（手动 nginx 设置、内部入口、具有部分代理链的自定义域名部署）后面的部署，将 `dashboard.public_url`（或 `HERMES_DASHBOARD_PUBLIC_URL`）设置为 Dashboard 被访问的**完整公共 URL**：

```yaml
dashboard:
  public_url: "https://dashboard.example.com/hermes"
```

设置后，OAuth 回调 URL 逐字变为 `<public_url>/auth/callback`——`X-Forwarded-Prefix` 在该代码路径上被忽略，因为操作员已显式声明了公共 URL。这是有意为之：将前缀叠加到上面会在公共 URL 已包含前缀的常见情况下导致双重前缀。

优先级与其他 Dashboard 设置相同——环境变量优先级高于 `config.yaml`：

| 来源 | 覆盖路径 | 何时使用 |
|---------|---------------|-------------|
| `config.yaml` 中的 `dashboard.public_url` | `HERMES_DASHBOARD_PUBLIC_URL` | 本地开发/本地部署（规范来源） |
| `HERMES_DASHBOARD_PUBLIC_URL` 环境变量 | — | 托管平台密钥 / CI |
| （未设置） | — | 默认——从 `X-Forwarded-*` 头重建 |

验证会拒绝缺少 `http://` / `https://` 方案、缺少主机或包含引号、尖括号、空白或控制字符的值。格式错误的值会静默回退到头重建，以便登录流程保持工作，而不是将用户定向到恶意 URL。

> **注意：** `public_url` 仅覆盖 OAuth 回调 URL。`Secure` cookie 标记仍由 `request.url.scheme`（在 proxy_headers 下为 X-Forwarded-Proto）控制，因此在 TLS 终止的公共部署中使用 `http://` `public_url` 将产生非 Secure 的 cookie。这是操作员的陷阱——请将 `public_url` 与上游正确的 TLS 终止配合使用。

### OAuth 流程

提供商实现的是 [Nous Portal OAuth 合约 v1](https://github.com/NousResearch/nous-account-service/blob/main/docs/agent-dashboard-oauth-contract.md)——授权码授权 + PKCE（S256）：

1. 用户访问 `/` 而没有会话 cookie → 门重定向到 `/login`。
2. 登录页面显示"Continue with Nous Research"按钮 → `/auth/login?provider=nous`。
3. 服务器将 PKCE 状态存放在短期 cookie 中，将用户重定向到 `https://portal.nousresearch.com/oauth/authorize?…`。
4. 用户在 Portal 认证，到达 `/auth/callback?code=…&state=…`。
5. 服务器在 `POST /api/oauth/token` 处将 code 兑换为 access token，根据 Portal 的 JWKS（`/.well-known/jwks.json`）验证 JWT 签名，并设置 `hermes_session_at` cookie。
6. 用户被重定向到 `/`（或通过 `next=` 查询参数重定向到原始深层链接路径）。

Access token 的 TTL 为 15 分钟。**合约 v1 中没有 refresh token**——当 token 过期时，SPA 的 fetch 包装器检测到 401 信封并通过全页导航回到 `/login` 重新运行流程。

### 设置的 Cookie

| 名称 | 有效期 | 说明 |
|------|----------|-------|
| `hermes_session_at` | Token TTL（15 分钟） | HttpOnly、SameSite=Lax、HTTPS 时 Secure |
| `hermes_session_pkce` | 10 分钟 | HttpOnly；在往返过程中保存 PKCE verifier + 提供商提示 |
| `hermes_session_rt` | v1 中未使用 | 预留用于正向兼容；当 `refresh_token` 为空时不写入 |

三者均为 `Path=/` 和 `SameSite=Lax`。当通过 HTTPS（通过请求 URL scheme 检测——在 `proxy_headers=True` 下接受来自上游 TLS 终结器的 `X-Forwarded-Proto`）访问 Dashboard 时，会设置 `Secure` 标志。

### 注销

侧边栏 widget 显示 `Logged in as <user_id…> via nous` 带有注销图标。单击它会 POST 到 `/auth/logout`，清除所有 Dashboard 认证 cookie 并重定向回 `/login`。

### 审计日志

每次登录开始、成功、失败和会话验证失败都会作为 JSON 行写入 `$HERMES_HOME/logs/dashboard-auth.log`。敏感字段（`access_token`、`refresh_token`、`code`、`code_verifier`、`state`、`Authorization` 头）在记录前被脱敏。

### 自定义提供商

要插入非 Nous 的 OAuth 提供商（例如 Google、GitHub、自定义 OIDC），创建一个注册 `DashboardAuthProvider` 的插件：

```python
# ~/.hermes/plugins/dashboard-auth-myidp/__init__.py
from hermes_cli.dashboard_auth import DashboardAuthProvider, Session, LoginStart

class MyIdPProvider(DashboardAuthProvider):
    name = "myidp"
    display_name = "My Identity Provider"

    def start_login(self, *, redirect_uri): ...
    def complete_login(self, *, code, state, code_verifier, redirect_uri): ...
    def verify_session(self, *, access_token): ...
    def refresh_session(self, *, refresh_token): ...
    def revoke_session(self, *, refresh_token): ...

def register(ctx):
    ctx.register_dashboard_auth_provider(MyIdPProvider())
```

登录页面列出所有已注册的提供商；可以叠加多个提供商，用户在 `/login` 处选择一个。

### 非交互式（bearer token）认证

除了交互式的人类登录（会话 cookie + 刷新）之外，`DashboardAuthProvider` ABC 还通过 `supports_token = True` + `verify_token(token=...)` 支持**非交互式的服务间认证**。当提供商选择加入时，入站 `Authorization: Bearer ***` 会经过验证，成功后，一个 `TokenPrincipal` 会被附加到请求上（`request.state.token_principal`），供该提供商标记为可令牌认证的端点使用——无需 cookie、无需重定向、无需刷新。

内置的第一个使用者是 **drain** 提供商（`plugins/dashboard_auth/drain`）：`nous-account-service` 通过 `HERMES_DASHBOARD_DRAIN_SECRET` 配置每个 agent 的密钥，提供商使用常量时间比较验证入站的 bearer token，并将 `/api/gateway/drain` 注册为可令牌认证的端点。它**失败关闭**——短/弱密钥（< 256 位）在注册时被拒绝，端点保持禁用；环境变量未设置时，它是无效操作。行为配置项（`scope`、`min_secret_chars`）位于 `config.yaml` 的 `dashboard.drain_auth` 下。

自定义提供商可以通过相同的方式实现 `supports_token`/`verify_token`，以暴露它们自己的机器可认证端点。

### 验证门已启用

```bash
# 快速环境变量路径。
HERMES_DASHBOARD_OAUTH_CLIENT_ID=agent:test \
  hermes dashboard --host 0.0.0.0

# 或通过 config.yaml 的等效方式（推荐用于本地开发/本地部署）：
#
#   dashboard:
#     oauth:
#       client_id: agent:test
#
# 然后只需：
hermes dashboard --host 0.0.0.0

# 访问 /api/status 查看门状态：
curl -s http://127.0.0.1:9119/api/status | jq '.auth_required, .auth_providers'
# true
# ["nous"]
```

Dashboard 的 React StatusPage 在"Web server"下显示相同的字段。侧边栏的 AuthWidget 在你登录后显示当前身份。

## 将 Hermes Desktop 连接到远程后端

Hermes Desktop 可以操控另一台机器（VPS、家庭服务器、Tailscale 后面的 Mini）上运行的 Hermes 后端。在应用中，这位于 **Settings → Gateway → Remote gateway**，它要求输入**远程 URL** 和**登录**方式。（关于桌面应用本身——安装、设置、聊天——请参见 [Hermes Desktop](/user-guide/desktop) 页面。）

你使用其中一个内置的认证提供商保护远程 Dashboard，桌面应用将根据后端通告的提供商进行登录。对于超出本机范围的后端——VPS、公共主机、任何面向互联网的——推荐提供商是 **OAuth (Nous Portal)**（通过 [`hermes dashboard register`](#注册-dashboard) 注册，使用 *Sign in with Nous Research* 登录）。内置的[用户名/密码提供商](#用户名密码提供商无-oauth-idp)是后端在受信任 LAN 上或仅通过 VPN 可达时的最快选择，但**不适合直接暴露于公共互联网**。将 Dashboard 绑定到非回环地址会启用其认证门；一旦登录，Desktop 会自动将会话复用于聊天 WebSocket——无需复制或粘贴 token。

下面的示例使用用户名/密码路径，因为它在受信任网络上搭建最快；对于 OAuth 路径，请参见[默认提供商：Nous Research](#默认提供商-nous-research)。

### 在后端（远程机器）

```bash
# 1. 在 ~/.hermes/.env（机密文件，0600）中设置 Dashboard 登录凭据。
cat >> ~/.hermes/.env <<'EOF'
HERMES_DASHBOARD_BASIC_AUTH_USERNAME=admin
HERMES_DASHBOARD_BASIC_AUTH_PASSWORD=choose-a-strong-password
# 推荐：稳定的签名密钥，使会话在重启后持续。
HERMES_DASHBOARD_BASIC_AUTH_SECRET=$(openssl rand -base64 32)
EOF
chmod 600 ~/.hermes/.env

# 2. 将 Dashboard 绑定到可达地址运行。非回环绑定
#    启用认证门；用户名/密码提供商处理登录。
hermes dashboard --no-open --host 0.0.0.0 --port 9119
```

不希望保存明文？使用 `HERMES_DASHBOARD_BASIC_AUTH_PASSWORD_HASH` 配合 scrypt 哈希替代——完整说明参见[用户名/密码提供商](#用户名密码提供商无-oauth-idp)。

如果你将 Dashboard 作为 systemd 服务运行，当单元具有 `EnvironmentFile=%h/.hermes/.env` 时，`~/.hermes/.env` 会自动加载，因此凭据在启动时就存在于环境中。

:::warning
Dashboard 会读写你的 `.env`（API 密钥、机密）并可以运行 agent 命令。此处展示的**用户名/密码**设置适用于受信任网络——切勿将受密码保护的 Dashboard 直接暴露到开放的互联网。请将其放在 VPN 后面。[Tailscale](https://tailscale.com/) 是更简洁的选择：绑定到机器的 tailscale IP（`--host <tailscale-ip>`）并使用 `http://<tailscale-ip>:9119` 作为远程 URL。只有你的 tailnet 上的设备才能访问它。要通过公共互联网访问后端，请改用 **OAuth (Nous Portal)** 提供商。
:::

### 在 Hermes Desktop 中

**Settings → Gateway → Remote gateway：**

- **Remote URL** — `http://<backend-host>:9119`（如果你在前面放置反向代理，也支持路径前缀如 `/hermes`）
- **Sign in** — 应用检测到用户名/密码网关并显示**登录**按钮；点击并输入步骤 1 中的凭据
- **Save and reconnect** — 将桌面 shell 切换到远程后端

当后端设置了 `HERMES_DASHBOARD_BASIC_AUTH_SECRET` 时，会话会自动刷新并在重启后保持。

### 环境变量覆盖

除了应用内设置，你还可以在启动桌面应用前通过环境变量将桌面指向一个后端。当 `HERMES_DESKTOP_REMOTE_URL` 被设置时，它会覆盖已保存的应用内 URL（Gateway 设置面板会显示"env override"徽章并禁用编辑）；你仍然需要从面板使用用户名和密码**登录**。

| 环境变量 | 值 |
|---------|-------|
| `HERMES_DESKTOP_REMOTE_URL` | `http://<backend-host>:9119` |

### 故障排查

- **"Remote gateway incomplete"** — 你尚未输入远程 URL。
- **登录失败，返回 401 / "Invalid credentials"** — 用户名或密码与后端的 `HERMES_DASHBOARD_BASIC_AUTH_USERNAME` / `HERMES_DASHBOARD_BASIC_AUTH_PASSWORD` 不匹配。后端对未知用户和错误密码返回相同的通用错误，因此请同时检查两者。用 `curl -s http://<host>:9119/api/status | jq '.auth_required, .auth_providers'` 确认门状态——应返回 `true` 并包含 `"basic"`。
- **没有"Sign in"按钮——要求输入会话 token 替代** — 用户名/密码提供商未激活（`/api/status` 不会列出 `"basic"`）。确保已设置用户名和密码（或密码哈希）并且 Dashboard 进程已加载它们。
- **每次重启都退出登录** — 设置 `HERMES_DASHBOARD_BASIC_AUTH_SECRET` 为稳定值；否则签名密钥在每次启动时重新生成。
- **连接被拒绝/超时** — 后端绑定到了 `127.0.0.1`（默认值）而非可达地址，或者防火墙/VPN 阻止了端口。绑定到 `0.0.0.0` 或 tailscale IP，并向你的受信任网络开放端口。

## CORS

Web 服务器将 CORS 限制为仅 localhost 来源：

- `http://localhost:9119` / `http://127.0.0.1:9119`（生产环境）
- `http://localhost:3000` / `http://127.0.0.1:3000`
- `http://localhost:5173` / `http://127.0.0.1:5173`（Vite 开发服务器）

如果你在自定义端口上运行服务器，该来源会自动添加。

## 开发

如果你要为 Web Dashboard 前端做贡献：

```bash
# 终端 1：启动后端 API
hermes dashboard --no-open

# 终端 2：启动带 HMR 的 Vite 开发服务器
cd web/
npm install
npm run dev
```

`http://localhost:5173` 上的 Vite 开发服务器会将 `/api` 请求代理到 `http://127.0.0.1:9119` 上的 FastAPI 后端。

前端使用 React 19、TypeScript、Tailwind CSS v4 和 shadcn/ui 风格组件构建。生产构建输出到 `hermes_cli/web_dist/`，由 FastAPI 服务器作为静态 SPA 提供服务。

## 更新时自动构建

运行 `hermes update` 时，如果 `npm` 可用，Web 前端会自动重新构建。这使 Dashboard 与代码更新保持同步。如果未安装 `npm`，更新会跳过前端构建，`hermes dashboard` 将在首次启动时构建。

## 主题与插件

Dashboard 内置六个主题，并可通过用户自定义主题、插件标签页和后端 API 路由进行扩展——全部即插即用，无需克隆仓库。

**实时切换主题**：点击顶部栏语言切换器旁的调色板图标。选择会持久化到 `config.yaml` 的 `dashboard.theme` 下，并在页面加载时恢复。

**独立更改字体**：同一选择器的 **Font** 部分位于主题列表下方，可覆盖当前主题的 UI 字体。选择在主题切换间保留（`config.yaml` → `dashboard.font`）；选择 **Theme default** 可清除覆盖并恢复当前主题的字体。

内置主题：

| 主题 | 特点 |
|-------|-----------|
| **Hermes Teal** (`default`) | 深青色 + 奶油色，系统字体，舒适间距 |
| **Hermes Teal (Large)** (`default-large`) | 与 default 相同，但使用 18px 文字和更宽松的间距 |
| **Midnight** (`midnight`) | 深蓝紫色，Inter + JetBrains Mono |
| **Ember** (`ember`) | 暖深红 + 古铜色，Spectral 衬线体 + IBM Plex Mono |
| **Mono** (`mono`) | 灰度，IBM Plex，紧凑 |
| **Cyberpunk** (`cyberpunk`) | 黑底霓虹绿，Share Tech Mono |
| **Rosé** (`rose`) | 粉色 + 象牙色，Fraunces 衬线体，宽松 |

如需构建自定义主题、添加插件标签页、注入 shell 插槽或暴露插件专属 REST 端点，请参阅 **[扩展 Dashboard](./extending-the-dashboard)**——完整指南涵盖：

- 主题 YAML schema——调色板、排版、布局、资源、componentStyles、colorOverrides、customCSS
- 布局变体——`standard`、`cockpit`、`tiled`
- 插件 manifest、SDK、shell 插槽、页面级插槽（在不覆盖内置页面的情况下注入控件）、后端 FastAPI 路由
- 完整的主题加插件综合演示（Strike Freedom cockpit 示例）
- 发现、重载和故障排查
