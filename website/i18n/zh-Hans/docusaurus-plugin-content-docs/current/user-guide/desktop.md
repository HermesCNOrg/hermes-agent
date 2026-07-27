---
sidebar_position: 3
title: "桌面应用"
description: "原生 Hermes 桌面应用——提供精心打磨的 Hermes 对话体验，支持流式工具输出、并排预览、文件浏览器、语音、定时任务、配置文件、技能和设置。支持 macOS、Windows 和 Linux。"
---

# 桌面应用

Hermes 桌面应用基于与 CLI 和网关**完全相同**的智能体构建——使用相同的配置、API 密钥、会话、技能和记忆。它不是一个独立产品，也不是轻量复刻版；它使用相同的 Hermes Agent 核心和设置，并通过现代、经过精心设计的 UI 来驱动。如果你曾在终端中使用过 `hermes`，在那里完成的所有设置都已可在这里使用，而你在这里进行的任何操作也会同步显示在那里。

它支持 **macOS、Windows 和 Linux**。

:::tip 各个界面有什么区别？
Hermes 有多个前端，它们都连接到同一个智能体：

- **桌面应用**（本页）——原生应用，为对话、配置和管理提供专门设计的 UI。
- **CLI**（`hermes`）和 **[TUI](./tui.md)**（`hermes --tui`）——终端界面。
- **[Web 控制台](./features/web-dashboard.md)**（`hermes dashboard`）——浏览器管理面板；其可选的**对话**标签页通过伪终端嵌入 TUI。

根据当前需要选择最合适的界面即可。它们共享状态，因此你可以在一个界面中开始会话，再到另一个界面中继续。
:::

## 安装

请按照 [Hermes Desktop 安装说明](../getting-started/installation.md)操作。

如果已经安装 Hermes，只需运行：

```bash
hermes desktop
```

它会使用你当前的配置、密钥、会话和技能。

## 应用功能

桌面应用以对话为核心，左侧边栏用于导航。它支持同时管理多个智能体对话、配置消息服务提供商、创建产物、浏览项目文件夹结构，以及同时处理多个项目。

### 对话

这是应用的核心区域，提供：

- **流式响应**：智能体工作时会实时显示工具活动和结构化的工具调用摘要。
- **与其他所有 Hermes 界面相同的对话历史**：在这里开始的会话可以在 CLI/TUI 中继续，反之亦然。
- **拖放文件**：将文件拖到对话区域的任意位置，即可附加到下一条消息。
- **右侧预览栏**：在继续对话的同时，并排呈现网页、文件和工具输出。
- **输入历史与队列编辑**：输入框为空时按上/下方向键，可调出并复用之前的提示词；还可在已排队消息发送前进行编辑。

#### 状态栏

对话底部的状态栏会实时显示会话状态，并提供快捷控制，无需打开“设置”：

- **单会话 YOLO 开关**：仅为当前会话开启或关闭 YOLO（行为与 TUI 一致）。YOLO 会绕过危险命令的审批提示，因此请务必了解自己关闭了什么保护——参见[安全 → YOLO 模式](./security.md#yolo-mode)。

想连接另一台机器上的 Hermes 实例，而不是使用应用内置的本地后端？请参阅下方的[连接远程后端](#connecting-to-a-remote-backend)。如需全面了解远程托管控制台的连接机制（身份验证关卡、`/api/ws` 对话套接字以及 WebSocket 关闭代码的排查方法），请参阅 [Web 控制台 → 将 Hermes Desktop 连接到远程后端](./features/web-dashboard.md#connecting-hermes-desktop-to-a-remote-backend)。

#### 选择模型

模型选择器位于**输入框**中，在麦克风左侧。点击后可在一个下拉菜单中切换模型、推理强度和快速模式。

- **输入框中的模型选择器是持久化的 UI 状态，不会修改默认值。**该选择会保存在本地（按设备），并在新建对话和重启后继续沿用，而不会重置为默认值——选择一次模型后，下次按 `Cmd/Ctrl+N` 就会使用它打开新对话。如果当前已有活动对话，切换模型只会作用于**当前对话**；无论哪种情况，在创建或切换会话时都会沿用该选择，而且**绝不会**写入配置文件的默认值。（切换[配置文件](#sessions--profiles)后，会重新使用该配置文件自己的默认值。）
- **在“设置 → 模型”中设置默认值。**这里的“主”模型是**每个配置文件的全局默认值**——新对话、定时任务、子智能体和辅助任务都会从它开始，并且只有这里会写入该默认值。每个[配置文件](#sessions--profiles)都保留自己的默认值。
- **按模型保存推理强度/快速模式预设。**桌面应用会为每个模型记住各自的推理强度和快速模式选择；每当选择该模型时，都会将这些预设重新应用到会话。预设只是桌面应用提供的便利功能，不会改变定时任务或子智能体的设置。
- **在对话中途切换会重置提示词缓存。**在活动对话中切换模型，意味着下一条消息需要按完整输入价格重新读取整个对话（服务提供商的提示词缓存按模型区分）。偶尔切换无妨；对于较长的对话，使用新模型开始一个新对话，通常比来回切换更省钱。

### 文件浏览器

无需离开应用即可浏览和预览工作目录，方便你跟随智能体读取、写入和编辑文件的过程。可使用 `hermes desktop --cwd <path>`（或 `HERMES_DESKTOP_CWD` 环境变量）设置初始项目目录。

### 语音

你可以与 Hermes 对话并听取语音回复，使用与其他界面相同的[语音模式](./features/voice-mode.md)。在 macOS 上，系统会在首次使用时请求麦克风权限。

### 设置与首次引导

通过完整的 UI 管理服务提供商、模型、工具和凭据，无需编辑 YAML。首次运行引导可让你在几秒内发出第一条消息。设置面板涵盖服务提供商/密钥、模型选择、工具集配置、MCP 服务器、网关和会话管理。

- **服务提供商设置面板**：集中管理推理服务提供商，并通过“账户/API 密钥”界面登录和保存各服务提供商的凭据。
- **菜单包含所有服务提供商和模型**：GUI 会显示完整的服务提供商列表，以及 `hermes model` 已知的每个模型。因此，你看到的模型目录与 CLI 相同，而不是经过筛选的子集。
- **xAI Grok OAuth**：Grok 是启动器中的一等 OAuth 服务提供商；与其他 OAuth 服务提供商一样，可通过浏览器流程登录。
- **通过 GUI 安装工具后端**：直接在应用中运行工具后端的安装后设置步骤，无需切换到终端。
- **辅助模型警告**：如果将主模型切换到新的服务提供商，但辅助任务（标题生成、摘要及类似辅助功能）仍固定使用另一个服务提供商，应用会发出警告，避免你在不知情的情况下将工作分散到两个服务提供商。

首次运行引导已采用统一的浮层设计系统重新设计，你也可以选择**稍后选择服务提供商**，跳过服务提供商设置，先进入应用。

### 管理面板

应用也提供更全面的 Hermes 管理功能，因此无需切换到终端：

- **技能**：浏览、安装和管理[技能](./features/skills.md)。
- **Cron**：查看和管理[定时任务](../reference/cli-commands.md#hermes-cron)。
- **配置文件**：切换不同的 [Hermes 配置文件](./profiles.md)（配置/技能/会话相互隔离）。
- **消息**：设置网关渠道。
- **智能体**和**指挥中心**：用于多智能体工作的编排界面。

### 键盘与导航

- **命令面板**：按 **Cmd+K**（Windows/Linux 上为 Ctrl+K），即可通过键盘跳转到操作和应用中的不同位置。
- **可重新绑定的快捷键**：可在“设置”的快捷键面板中，将应用快捷键重新映射为你习惯的按键。
- **自定义缩放快捷键**：以半级增量缩放界面，更精细地控制文字大小。
- **UI 语言切换器**：在应用内更改界面语言，包括简体中文（zh-Hans）。

### 会话与配置文件 {#sessions--profiles}

- **会话列表全面改进**：重新设计的会话列表支持归档及常规会话整理，便于在会话数量增长后保持列表易于管理。
- **按 id 搜索会话**：可通过会话 id 直接找到特定会话。
- **多配置文件并发会话**：同时运行属于多个[配置文件](./profiles.md)的会话，并使用跨配置文件的 `@session` 链接引用另一个配置文件中的会话。

## 更新

应用会在后台检查更新，并在更新就绪后提供一键更新。

也可以通过 GUI 使用[手动更新流程](https://hermes-agent.nousresearch.com/docs/getting-started/updating)。

## 卸载

打开**设置 → 关于 → 危险区域**，然后选择要移除的范围：

- **仅卸载对话 GUI**：移除桌面应用及其数据；Hermes 智能体、你的配置和对话会保留。（等同于 `hermes uninstall --gui`。）
- **卸载 GUI 和智能体，但保留我的数据**：移除应用和智能体，但保留配置、对话和密钥，以便日后重新安装。（等同于 `hermes uninstall`。）
- **全部卸载**：移除应用、智能体和全部用户数据。（等同于 `hermes uninstall --full`。）

应用会关闭以完成操作（清理程序会在应用退出后运行，以便移除正在运行的应用包及其自身的 venv）。如果未安装本地智能体（例如，仅连接远程后端的 GUI-only “lite” 客户端），需要移除智能体的选项会自动隐藏。

你也可以在终端中执行相同操作：只卸载 GUI 使用 `hermes uninstall --gui`；同时卸载智能体则使用 `hermes uninstall` / `hermes uninstall --full`。

:::note
在**源代码检出目录**中运行 `hermes uninstall --gui`（即 `hermes desktop` 开发构建）还会移除工作区的 `node_modules` 和 `apps/desktop/{dist,release}` 构建输出，因为它们属于 GUI 构建产物。可以通过 `hermes desktop`（或 `npm install` 后重新构建）恢复；但如果你正在开发桌面应用，之后需要重新安装依赖。
:::

## CLI 参考：`hermes desktop`

要通过 CLI 启动，只需运行 `hermes desktop`。默认情况下，它会安装工作区 Node 依赖、构建当前操作系统对应的未打包 Electron 应用，然后启动该构建产物。

| 标志                 | 说明                                                                               |
| -------------------- | ----------------------------------------------------------------------------------------- |
| `--skip-build`       | 跳过 npm 安装/打包，并从 `apps/desktop/release` 启动现有未打包应用 |
| `--force-build`      | 即使内容戳匹配，也强制执行完整重建                                    |
| `--build-only`       | 构建桌面应用但不启动（供 `hermes update` 使用）                      |
| `--source`           | 通过 `electron .` 启动 `apps/desktop/dist`，而不是已打包应用           |
| `--cwd PATH`         | 桌面对话会话的初始项目目录（设置 `HERMES_DESKTOP_CWD`）           |
| `--hermes-root PATH` | 覆盖应用使用的 Hermes 源代码根目录（设置 `HERMES_DESKTOP_HERMES_ROOT`）          |
| `--ignore-existing`  | 后端解析时强制应用忽略 `PATH` 中已有的任何 `hermes` CLI      |
| `--fake-boot`        | 启用确定性的启动延迟，用于验证启动 UI                            |

## 工作原理

打包后的应用包含 Electron 外壳和原生 React 对话界面。首次启动时，它可以将 Hermes Agent 运行时安装到 `HERMES_HOME`（`~/.hermes`，Windows 上则为 `%LOCALAPPDATA%\hermes`）——其布局**与 CLI 安装完全相同**，因此两者可以互换使用。后端解析会依次优先采用 `HERMES_DESKTOP_HERMES_ROOT`、已完成的托管安装、在 `PATH` 中探测到的 `hermes`（除非设置了 `--ignore-existing` / `HERMES_DESKTOP_IGNORE_EXISTING=1`），最后才采用面向 Nix 等打包工具的显式 `HERMES_DESKTOP_HERMES` 命令覆盖。React 渲染器会连接应用为你启动的无头后端——即一个提供 `tui_gateway` JSON-RPC/WebSocket API 的 `hermes serve` 进程——并复用智能体运行时，而不是嵌入 `hermes --tui`。桌面应用**自成一体**：它运行自己的 `hermes serve` 后端，绝不会打开或依赖 [Web 控制台](./features/web-dashboard.md)。（早于 `serve` 命令的运行时会自动回退到无头的 `dashboard --no-open`，因此应用更新不会超出后端的能力范围。）安装、后端解析和自更新逻辑都位于 Electron 主进程中。

## 连接远程后端 {#connecting-to-a-remote-backend}

默认情况下，应用会启动并管理自己的**本地**后端。你也可以将它连接到另一台机器上运行的 Hermes 后端，例如 VPS、家用服务器，或位于 Tailscale 网络中的 Mini。

:::info 远程后端是正在运行的 `hermes serve` 进程
“远程后端”指远程机器上运行的 **`hermes serve`** 服务器——桌面应用连接的就是这个进程。除非该后端确实已启动且网络可达，否则本节中的任何操作都无法生效。桌面应用不会替你启动它；你需要自行（或通过 `systemd` 服务）让 `hermes serve` 在远程主机上持续运行，然后由应用连接。如果你还使用消息渠道（Telegram、Discord 等），**网关**是另一个需要独立启动的长期运行进程——参见设置步骤后的说明。
:::

连接分为两部分：在后端通过**身份验证服务提供商**实施保护，再在应用中输入后端 URL 并登录。将后端绑定到非环回地址会自动启用身份验证关卡，而你配置的服务提供商负责让桌面应用通过验证。

**根据后端所在位置选择服务提供商：**

- **OAuth（Nous Portal）——对于任何可从本机之外访问的后端，首选此方式。**登录信息会通过你的 Nous 账户验证，因此该选项适用于 VPS、公网主机或任何远程后端。使用 `hermes dashboard register`（或 Portal 的 [`/local-dashboards`](https://portal.nousresearch.com/local-dashboards) 页面）注册控制台并配置其 OAuth 客户端，然后在应用中选择**使用 Nous Research 登录**。如果你运行自己的身份服务提供商，自托管 OIDC 服务提供商的工作方式也相同。
- **用户名/密码——仅用于本地或可信网络。**如果后端位于同一个可信局域网，或只能通过 VPN（例如 Tailscale）访问，这是最简单的选择。它使用一组共享凭据进行保护，无需外部身份服务提供商，因此**不要将它用于暴露在公共互联网中的控制台**——这种情况应改用 OAuth。

本节其余部分演示用户名/密码方案，因为它是在可信网络上最快的部署方式；OAuth 方案请参阅 [Web 控制台 → 默认服务提供商：Nous Research](./features/web-dashboard.md#default-provider-nous-research)。

### 在后端（远程机器）

设置用户名和密码，然后启动后端并绑定到可访问的地址。凭据保存在 `~/.hermes/.env`（权限模式为 0600 的密钥文件）中：

```bash
# 1. Set the dashboard login credentials.
cat >> ~/.hermes/.env <<'EOF'
HERMES_DASHBOARD_BASIC_AUTH_USERNAME=admin
HERMES_DASHBOARD_BASIC_AUTH_PASSWORD=choose-a-strong-password
# Recommended: a stable signing secret so sessions survive restarts.
# Without it a random key is generated per boot and you'll be logged out
# on every restart.
HERMES_DASHBOARD_BASIC_AUTH_SECRET=$(openssl rand -base64 32)
EOF
chmod 600 ~/.hermes/.env

# 2. Run the backend bound to a reachable address. The non-loopback bind
#    engages the auth gate; the username/password provider handles login.
hermes serve --host 0.0.0.0 --port 9119
```

只要希望桌面应用能够连接，就需要让该 `hermes serve` 进程持续运行——一旦它停止，应用便无法访问后端。可通过 `systemd`、`tmux` 或你选择的进程管理器运行，使其在注销和重启后仍能继续工作。

另外，如果你依赖消息渠道，请确保**网关正在运行**于远程主机：桌面应用连接的是 `hermes serve` 后端，而 Telegram/Discord/Slack 网关会话属于另一个进程，需要单独启动并保持运行。网关设置请参阅[消息](./messaging/index.md)。

不希望以明文形式保存密码？可以改为将 `HERMES_DASHBOARD_BASIC_AUTH_PASSWORD_HASH` 设置为 scrypt 哈希——使用 `python -c "from plugins.dashboard_auth.basic import hash_password; print(hash_password('PW'))"` 进行计算。完整配置范围（config.yaml 键、所有环境变量、速率限制器）请参阅 [Web 控制台 → 用户名/密码服务提供商](./features/web-dashboard.md#usernamepassword-provider-no-oauth-idp)。

要将后端作为 systemd 服务运行？请为 unit 添加 `EnvironmentFile=%h/.hermes/.env`，以便启动时将凭据载入环境。

:::warning
后端会读取和写入你的 `.env`（API 密钥、机密），也可以运行智能体命令。上述**用户名/密码**设置仅适用于可信网络——绝不要将受密码保护的后端直接暴露在开放互联网中；请将其置于 VPN 之后。[Tailscale](https://tailscale.com/) 是简洁的选择：绑定到机器的 tailscale IP（`--host <tailscale-ip>`），并将 `http://<tailscale-ip>:9119` 用作远程 URL，使其只能从你的 tailnet 访问。若要通过公共互联网访问后端，请改用 **OAuth（Nous Portal）**服务提供商。
:::

### 在应用中

打开**设置 → 网关 → 远程网关：**

1. **远程 URL**——`http://<backend-host>:9119`（如果前面配置了反向代理，也支持 `/hermes` 之类的路径前缀）
2. **登录**——应用会检测后端公布的服务提供商，并相应调整按钮。对于用户名/密码后端，它会显示**登录**按钮，点击后打开凭据表单（输入步骤 1 中的凭据）。对于 OAuth 后端，它会显示**使用 `<provider>` 登录**（例如*使用 Nous Research 登录*），并启动服务提供商的浏览器登录流程。无论使用哪种方式，应用最终都会获得经过后端身份验证的会话。
3. **保存并重新连接**——将桌面应用切换到远程后端。会话会自动刷新；设置 `HERMES_DASHBOARD_BASIC_AUTH_SECRET` 后，重启也会保持登录状态。

也可以在启动应用前通过 `HERMES_DESKTOP_REMOTE_URL` 环境变量设置后端 URL，而无需使用 UI（它会覆盖应用内设置）；但仍需从“网关”设置面板登录。

:::note 各配置文件使用不同的远程主机
远程网关主机按[配置文件](./profiles.md)分别配置，因此每个配置文件都可以连接自己的远程后端（或继续使用本地后端）。切换配置文件时，应用连接的远程主机也会随之切换。
:::

### 故障排查

- **登录失败，显示 401 / “Invalid credentials”**——用户名或密码与后端的 `HERMES_DASHBOARD_BASIC_AUTH_USERNAME` / `HERMES_DASHBOARD_BASIC_AUTH_PASSWORD` 不匹配。对于未知用户和错误密码，后端会返回相同的通用错误（不会形成枚举预言机），因此请仔细检查两者。可运行 `curl -s http://<host>:9119/api/status | jq '.auth_required, .auth_providers'`，确认身份验证关卡已开启；结果应报告 `true` 并包含 `"basic"`。
- **没有“登录”按钮，而是要求提供会话令牌**——后端的用户名/密码服务提供商未启用。`/api/status` 的 `auth_providers` 中不会列出 `"basic"`。请确认 `~/.hermes/.env` 中同时设置了用户名和密码（或密码哈希），并确认控制台进程确实已加载它们。
- **每次重启都会退出登录**——请将 `HERMES_DASHBOARD_BASIC_AUTH_SECRET` 设置为稳定值。如果未设置，令牌签名密钥会在每次启动时重新生成，导致所有会话失效。
- **连接被拒绝/超时**——后端绑定到了 `127.0.0.1`（默认值），或者防火墙/VPN 阻止了该端口。请绑定到 `0.0.0.0` 或 tailscale IP，并向可信网络开放该端口。

如需从 Web 控制台角度了解相同设置，请参阅 [Web 控制台 → 将 Hermes Desktop 连接到远程后端](./features/web-dashboard.md#connecting-hermes-desktop-to-a-remote-backend)；环境变量目录位于[环境变量 → Web 控制台与 Hermes Desktop](../reference/environment-variables.md#web-dashboard--hermes-desktop)。

## 故障排查

启动日志位于 `HERMES_HOME/logs/desktop.log`（其中包含后端输出和近期 Python traceback）——如果应用报告启动失败，请首先检查该文件。也可以通过 CLI 实时查看：

```bash
hermes logs gui -f
```

常用重置操作：

```bash
# Force a clean first-launch setup (macOS/Linux)
rm "$HOME/.hermes/hermes-agent/.hermes-bootstrap-complete"

# Rebuild a broken Python venv (macOS/Linux)
rm -rf "$HOME/.hermes/hermes-agent/venv"

# Reset a stuck macOS microphone prompt
tccutil reset Microphone com.nousresearch.hermes
```

### “Build desktop app” 卡在 Electron 下载阶段

构建过程会从 `github.com/electron/electron/releases` 下载 Electron 运行时（约 114&nbsp;MB）。如果安装程序卡在 **Build desktop app** 步骤，实时输出不断重复 `retrying attempt=…`，说明你的网络（防火墙、代理或地区限制）正在阻止或限制 GitHub 访问。

安装程序会自动尝试修复：构建失败时，首先 (1) 清除损坏的 Electron 缓存 zip 并重试；如果仍然失败，且你尚未设置 `ELECTRON_MIRROR`，则 (2) 再通过 `npmmirror.com`（事实上的 Electron 社区镜像）重试一次。`@electron/get` 会通过 SHASUM 校验下载内容，但校验和也来自同一镜像——它可以发现损坏或不完整的下载，却无法发现遭入侵的镜像。如果你不愿信任第三方主机，可以指定自己的 `ELECTRON_MIRROR`（见下文）；构建过程绝不会覆盖你设置的值。

要**选择自己的镜像**（例如企业内部或可信镜像），请在安装前设置 `ELECTRON_MIRROR`，或手动重新构建——构建过程会遵循该设置，不会将其覆盖：

```bash
ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/ \
  bash -c 'cd "$HOME/.hermes/hermes-agent/apps/desktop" && CSC_IDENTITY_AUTO_DISCOVERY=false npm run pack'
```

手动清除损坏的缓存 zip：

```bash
rm -f "$HOME/Library/Caches/electron"/electron-*.zip   # macOS
rm -f "$HOME/.cache/electron"/electron-*.zip            # Linux
```

## 从源代码构建

如果你想开发应用本身，请先在仓库根目录安装一次工作区依赖，然后从 `apps/desktop` 运行开发服务器：

```bash
npm install          # from repo root — links apps/desktop, web, apps/shared
cd apps/desktop
npm run dev          # Vite renderer + Electron, which boots the Python backend
```

将应用指向特定的检出目录，或与真实配置隔离：

```bash
HERMES_DESKTOP_HERMES_ROOT=/path/to/clone npm run dev
HERMES_HOME=/tmp/throwaway npm run dev
npm run dev:fake-boot   # exercise the startup overlay with deterministic delays
```

构建安装程序：

```bash
npm run dist:mac     # DMG + zip
npm run dist:win     # NSIS + MSI
npm run dist:linux   # AppImage + deb + rpm
npm run pack         # unpacked app under release/ (no installer)
```

如果环境中存在相关凭据（macOS 使用 `CSC_LINK` / `CSC_KEY_PASSWORD` / `APPLE_*`，Windows 使用 `WIN_CSC_*`），macOS/Windows 签名和公证会自动运行。

## 另请参阅

- [CLI 指南](./cli.md)——终端界面
- [TUI](./tui.md)——`hermes --tui` 和控制台对话标签页所使用的现代终端 UI
- [Web 控制台](./features/web-dashboard.md)——带有嵌入式对话标签页的浏览器管理面板
- [配置](./configuration.md)——桌面应用读写的配置
- [Windows（原生）](./windows-native.md)——Windows 原生安装路径
