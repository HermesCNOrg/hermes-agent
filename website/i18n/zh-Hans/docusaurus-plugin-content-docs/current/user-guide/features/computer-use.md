---
title: 计算机使用
sidebar_position: 16
---

# 计算机使用

Hermes Agent 可以在 **macOS、Windows 和 Linux** 上于**后台**驱动你的桌面——点击、输入、滚动和拖动。你的光标不会移动，键盘焦点不会改变，虚拟桌面 / Spaces 也不会自行切换。你和代理在同一台机器上协同工作。

与大多数计算机使用集成不同，这项功能适用于**任何支持工具调用的模型**——Claude、GPT、Gemini，或本地 OpenAI 兼容端点上的开放模型。无需处理 Anthropic 原生模式。

## 工作原理

`computer_use` 工具集通过 stdio 使用 MCP 与开源后台计算机使用驱动程序 [`cua-driver`](https://github.com/trycua/cua) 通信。每个平台在底层都使用相应的无障碍功能和输入栈：

| 平台 | 无障碍树 | 输入分发 |
|---|---|---|
| macOS | AX (private SkyLight SPIs) | `SLPSPostEventRecordTo` — pid-scoped, no cursor warp |
| Windows | UIAutomation | `SendInput` + `PostMessage` — no focus steal |
| Linux | AT-SPI (X11 + Wayland) | XTest (X11) / virtual-keyboard (Wayland) |

每个平台上的结果都相同：代理可以读取任意可见窗口的无障碍树，并发布合成事件，而无需将窗口置于前台、切换虚拟桌面或移动真实的操作系统光标。

有关底层契约——*为什么*后台模式很重要、无前台不变量以及点击分发的内部机制——请参阅**[cua.ai/docs/explanation/the-no-foreground-contract](https://cua.ai/docs/explanation/the-no-foreground-contract)**。

## 启用

选择最方便的路径即可——两种路径运行的是同一个上游安装程序：

**选项 1：专用 CLI 命令（最直接）。**

```
hermes computer-use install
```

此命令会获取并运行上游 cua-driver 安装程序：macOS/Linux 上运行 `install.sh`，Windows 上运行 `install.ps1`。使用 `hermes computer-use status` 验证安装状态。

**选项 2：交互式启用工具集。**

1. 运行 `hermes tools`，选择 `🖱️  Computer Use (macOS/Windows/Linux)`。
2. 设置流程会运行上游安装程序（与选项 1 相同）。

安装完成后，无论选择哪条路径，都要授予相应平台所需的前置权限：

| 平台 | 前置条件 |
|---|---|
| **macOS** | 系统设置 → 隐私与安全性 → **辅助功能** + **屏幕录制** → 允许你的终端（或 Hermes 应用）。`hermes computer-use doctor` 会告知你缺少哪项权限。 |
| **Windows** | 安装时不需要任何前置条件。如果你通过 SSH 驱动（而不是 RDP / 控制台），需要使用自动启动模式——参见 [cua.ai/docs/how-to-guides/driver/windows-ssh](https://cua.ai/docs/how-to-guides/driver/windows-ssh)，了解 Session 0 ↔ Session 1+ 代理。 |
| **Linux** | 需要可访问的显示服务器：X11 需要设置 `DISPLAY`，Wayland 需要设置 `XDG_SESSION_TYPE=wayland`。Wayland 会话需要 XWayland 桥接才能进行捕获。必须启用 AT-SPI（GNOME/KDE/Xfce 默认启用）。 |

然后在启用工具集的情况下启动会话：

```
hermes -t computer_use chat
```

或者将 `computer_use` 添加到 `~/.hermes/config.yaml` 中已启用的工具集列表。

## `hermes computer-use doctor` — 首个排查步骤

`hermes computer-use doctor` 会运行 cua-driver 的结构化 `health_report` MCP 工具，并输出逐项检查矩阵。这是找出某个操作“为什么”不起作用的最快方法。

```
$ hermes computer-use doctor
⚠️  cua-driver 0.5.8 on darwin — degraded
  ✅ binary_version: cua-driver 0.5.8
  ✅ platform_supported: macOS 26.4.1 (arm64)
  ✅ session_active: MCP session is active.
  ❌ bundle_identity: Process has no CFBundleIdentifier.
      → Run the binary inside CuaDriver.app so TCC grants attribute correctly.
  ✅ tcc_accessibility: Accessibility is granted.
  ✅ tcc_screen_recording: Screen Recording is granted.
  ✅ ax_capability: AX is trusted and reachable.
  ✅ screen_capture_capability: ScreenCaptureKit reachable; 1 display(s) shareable.
```

- 当总体状态为 `ok` 时，**退出代码为 0**——所有组件均已正确连接。
- 当状态为 `degraded` 或 `failed` 时，**退出代码为 1**——至少有一项检查失败；每项失败旁的提示会告诉你需要修复什么。
- 当 cua-driver 二进制文件本身无法访问时，**退出代码为 2**。

可用选项：

- `--include CHECK` — 仅运行列出的检查（多个检查可重复使用）
- `--skip CHECK` — 跳过某项检查（优先于 `--include`）
- `--json` — 输出原始结构化载荷，形状与 `tools/call health_report` MCP 响应相同

检查矩阵会根据平台调整：在 Windows + Linux 上，`bundle_identity` / `tcc_*` 为 `skip`，因为这些概念不适用。`ax_capability` 会分别在 macOS 上检查 AX、在 Windows 上检查 UIA、在 Linux 上检查 AT-SPI；如果无法访问，每个平台都会给出相应的诊断提示。

## 代理光标与会话

代理执行操作时，你会看到一个**带色调的覆盖层光标**滑过屏幕，移动到每次点击、输入或滚动的落点。真实的操作系统光标永远不会移动——覆盖层只是一个视觉提示，表示“代理正在这里操作”。每次 Hermes 运行都会声明自己的 cua-driver **会话 ID**（例如 `hermes-3a7b9c14d2e8`）；光标身份以该会话为键，因此并发运行和子代理各自拥有独立光标，不会相互干扰。

你可以使用 `cua-driver` 的 CLI 选项或运行时 `set_agent_cursor_style` MCP 工具调整光标；完整选项请参阅 [cua.ai/docs/how-to-guides/driver/personalize-cursor](https://cua.ai/docs/how-to-guides/driver/personalize-cursor)，其中包括内置的 `arrow` 与 `teardrop` 轮廓、通过 `--cursor-icon` 指定自定义 SVG / PNG / ICO、运行时渐变色和绽放光晕。

## 深入了解 — cua-driver 技能包

Hermes 有意让其技能（`skills/autonomous-ai-agents/computer-use/SKILL.md`）专注于 Hermes 侧的 `computer_use` 操作词汇——这是代理加载的唯一事实来源。对于更深入的材料——平台特定的深度解析、录制语义以及浏览器页面交互——请让你的代理框架使用 cua-driver 团队直接发布和维护的 cua-driver 技能包：

```
cua-driver skills install
```

这会将技能包符号链接到你的代理框架技能目录中。运行后，代理可以访问：

| 文件 | 主题 |
|---|---|
| `SKILL.md` | 跨平台核心（快照不变量、无前台契约、点击分发、AX 树机制） |
| `MACOS.md` | macOS 细节：无前台契约、AXMenuBar 导航、SkyLight 点击分发、Apple Events JS 桥接 |
| `WINDOWS.md` | Windows 细节：UIA 树、UWP / `ApplicationFrameHost` 托管、Session 0 隔离、自动启动模式 |
| `LINUX.md` | Linux 细节：AT-SPI 树、X11 / Wayland、终端模拟器检测 |
| `RECORDING.md` | 轨迹与视频录制语义 |
| `WEB_APPS.md` | 浏览器页面交互提示 |
| `TESTS.md` | 按轨迹回放的工作流程 |

这些是**平台深度解析，而不是 Hermes 技能的重复内容**——当代理报告“在 Windows 上，我的点击落在了错误的元素上”时，它会读取 `WINDOWS.md`，了解 UIA / UWP 上下文，从而解释原因并采取不同的操作方式。

`cua-driver skills status` 会显示已安装的内容，以及它链接到哪些代理框架。目前自动检测列表涵盖 Claude Code、Codex、OpenCode、OpenClaw 和 Antigravity；**Hermes 自动检测计划作为 `trycua/cua` 的后续工作实现**——在此之前，请运行一次 `cua-driver skills install`，并将你的框架指向生成的 `~/.cua-driver/skills/cua-driver` 目录（或将其符号链接到你通常使用的技能目录）。

## 快速示例

用户提示：*“查找我来自 Stripe 的最新电子邮件，并总结他们希望我做什么。”*

代理的计划（macOS / Windows / Linux 上的步骤形状相同——模型会替换为符合平台习惯的快捷键和应用名称）：

1. `computer_use(action="capture", mode="som", app="Mail")` — 获取电子邮件应用的屏幕截图，其中每个侧边栏项目、工具栏按钮和消息行都带有编号。
2. `computer_use(action="click", element=14)` — 点击搜索字段。
3. `computer_use(action="type", text="from:stripe")`
4. `computer_use(action="key", keys="return", capture_after=True)` — 提交并获取新屏幕截图。
5. 点击顶部结果，读取正文并进行总结。

在整个过程中，你的光标会停留在原来的位置，电子邮件应用也不会切换到前台。

## 提供商兼容性

| 提供商 | 支持视觉？ | 可用？ | 备注 |
|---|---|---|---|
| Anthropic (Claude Sonnet/Opus 3+) | ✅ | ✅ | 综合表现最佳；支持 SOM + 原始坐标。 |
| OpenRouter (any vision model) | ✅ | ✅ | 支持多段工具消息。 |
| OpenAI (GPT-4+, GPT-5) | ✅ | ✅ | 同上。 |
| Google (Gemini 2+) | ✅ | ✅ | 同时支持工具调用和视觉。 |
| Local vLLM / LM Studio / Ollama (vision model) | ✅ | ✅ | 前提是模型支持多段工具内容。 |
| Text-only models | ❌ | ✅ (degraded) | 使用 `mode="ax"` 进行仅无障碍树操作。 |

屏幕截图会以内嵌的 OpenAI 风格 `image_url` 部分随工具结果发送。对于 Anthropic，适配器会将其转换为原生 `tool_result` 图像块。图像 MIME 类型来自 cua-driver 明确提供的 `mimeType` 字段（`image/png` 或 `image/jpeg`）——客户端不会进行魔数嗅探。

## 安全性

Hermes 采用多层防护措施：

- 破坏性操作（click、type、drag、scroll、key、focus_app）需要获得批准——可以通过 CLI 对话框交互式批准，也可以通过消息平台的批准按钮批准。
- 工具层面硬阻止的按键组合：清空废纸篓、强制删除、锁定屏幕、注销、强制注销。
- 工具层面硬阻止的输入模式：`curl | bash`、`sudo rm -rf /`、fork 炸弹等。
- 代理的系统提示会明确告知它：不得点击权限对话框，不得输入密码，不得遵循截图中嵌入的指令。

如果你希望每次操作都得到确认，可以在 `~/.hermes/config.yaml` 中配合使用 `approvals.mode: manual`。

## 令牌效率

屏幕截图很昂贵。Hermes 应用了四层优化：

- **屏幕截图清除**——Anthropic 适配器在上下文中只保留最近的 3 张屏幕截图；更早的截图会变成 `[screenshot removed to save context]` 占位符。
- **客户端压缩裁剪**——上下文压缩器会检测多模态工具结果，并从旧结果中移除图像部分。
- **感知图像的令牌估算**——每张图像按约 1500 个令牌（Anthropic 的统一费率）计算，而不是按其 base64 字符长度计算。
- **服务端上下文编辑（仅限 Anthropic）**——启用后，适配器会通过 `context_management` 启用 `clear_tool_uses_20250919`，让 Anthropic API 在服务端清除旧的工具结果。

在 1568×900 的显示屏上执行 20 次操作的会话，屏幕截图上下文通常约消耗 30K 个令牌，而不是约 600K。

## 限制

- **性能。** 后台模式比前台模式慢——通过无障碍功能路由的事件在 macOS 上约需 5–20 毫秒，在 Windows UIA 上约需 3–10 毫秒，在 Linux AT-SPI 上约需 5–15 毫秒，而直接 HID 发布则不需要这些开销。对于代理速度的点击来说并不明显；如果你尝试录制速通操作，则会注意到差异。
- **无法使用键盘输入密码。** `type` 对命令 shell 载荷设置了硬阻止模式；输入密码时，请使用系统自动填充功能（macOS 钥匙串 / Windows Credential Manager / GNOME Keyring / KWallet）。
- **某些应用不会公开无障碍树。** Windows 上的新式 UWP 应用、Linux 上低于 28 的 Electron，以及一些使用自定义绘制的 macOS 应用（Logic、Final Cut、部分游戏）会提供稀疏或空的 AX 树。如果树为空，可以回退到像素坐标；也可以直接跳过该任务。
- **Windows：普通代理无法驱动提升权限（管理员）窗口。** Windows UIPI（用户界面特权隔离）会强制执行完整性级别边界：中等完整性进程（默认的 Hermes 代理）无法枚举高完整性（管理员）进程所拥有窗口的 UIA 树，也无法向该窗口注入鼠标输入。其表现为：`capture(mode='som')` 返回 0 个元素，`click(...)` 报告成功却没有任何效果，即使截图显示正常（GDI 捕获处于完整性检查之下）。键盘事件可以部分绕过 UIPI，因此 Tab / Enter 仍可在提升权限的对话框中导航。这是操作系统限制，而不是 cua-driver 的缺陷——它影响所有 Windows 自动化栈。要驱动提升权限的窗口，请让 Hermes 代理本身以高完整性运行（从提升权限的终端启动）；否则请操作非提升权限窗口。
- **特定平台的部署注意事项：**
  - **macOS** 使用私有 SkyLight SPI。Apple 可能在任何操作系统更新中修改它们。Hermes 会在已安装的 cua-driver 版本低于其测试版本时发出警告。
  - **Windows** SSH 会话运行在没有交互式桌面的 **Session 0** 中。从 RDP / 控制台会话内部驱动 Hermes，或设置 cua-driver 的自动启动计划任务——[windows-ssh](https://cua.ai/docs/how-to-guides/driver/windows-ssh) 中提供了操作方法。
  - **Linux** 需要可访问的显示服务器。无头服务器需要先运行 Xvfb（`Xvfb :99 -screen 0 1920x1080x24`），之后 `computer_use` 才能捕获或注入事件。纯 Wayland 会话需要 XWayland 桥接来进行屏幕捕获（cua-driver 的 Wayland 注入路径会独立处理输入）。

如果要进行跨平台 GUI 自动化，但不想承担桌面开销（也不想配置 TCC / Session 0 / X11），`browser` 工具集会使用真正的无头 Chromium，是仅限网页任务的正确选择。

## 配置

覆盖驱动程序二进制文件路径（测试 / CI / 本地构建）：

```
HERMES_CUA_DRIVER_CMD=/path/to/your/cua-driver
```

完全替换后端（用于测试）：

```
HERMES_COMPUTER_USE_BACKEND=noop   # records calls, no side effects
```

### 遥测

cua-driver 上游默认启用匿名使用遥测（PostHog）。**Hermes 会为你禁用遥测**——在每次 cua-driver 调用时（MCP 后端、`status`、`doctor` 和安装流程），Hermes 都会在驱动程序环境中设置 `CUA_DRIVER_RS_TELEMETRY_ENABLED=0`。

如果要重新选择加入（让 cua-driver 使用其自身的默认设置并发送遥测），请在 `config.yaml` 中设置：

```yaml
computer_use:
  cua_telemetry: true   # default: false (telemetry off)
```

启用时，`hermes computer-use doctor` 会报告 `telemetry: enabled`；关闭时（默认），会报告 `telemetry: disabled via CUA_DRIVER_RS_TELEMETRY_ENABLED`。

## 针对本地 cua-driver 构建进行测试

如果你正在开发 cua-driver 本身，或想测试尚未发布的修复，可以让 Hermes 使用你从源代码构建的二进制文件，而不是已发布的版本。Hermes 使用 `shutil.which("cua-driver")` 解析驱动程序，并且**不会强制执行 `HERMES_CUA_DRIVER_VERSION`**，因此本地构建（报告为 `0.0.0-local-*`）会按原样接受。有两种方式：

### 选项 A — `install-local`（构建并放入 PATH）

在 `trycua/cua` 检出目录中，运行上游本地安装程序。它会以发布模式构建 Rust 后端，并将 `cua-driver` 放入生产安装程序使用的相同安装布局，同时将其 bin 目录添加到你的 PATH 中：

```powershell
# Windows (PowerShell), from the cua repo root
./libs/cua-driver/scripts/install-local.ps1 -NoAutoStart
```

```bash
# macOS / Linux, from the cua repo root  (defaults to a debug build without --release)
./libs/cua-driver/scripts/install-local.sh --release
```

- Windows 会在 `%USERPROFILE%\\.cua-driver\\packages\\…` 下暂存构建，并将 `%LOCALAPPDATA%\\Programs\\Cua\\cua-driver\\bin`（已添加到用户 PATH）junction 到该目录。macOS/Linux 会将 `cua-driver` 符号链接到 `~/.local/bin`（使用 `--bin-dir <path>` 覆盖）。
- `-NoAutoStart` 会跳过注册 `cua-driver-serve` 登录守护进程——Hermes 测试不需要它（见下文说明）。

然后打开一个新的 shell（使 PATH 变更生效）并确认：

```
cua-driver --version                 # local builds report 0.0.0-local-release
# Windows:      (Get-Command cua-driver).Source
# macOS/Linux:  which cua-driver
```

### 选项 B — 直接让 Hermes 指向构建出的二进制文件（最快循环）

完全跳过安装流程：运行 `cargo build`，并将 `HERMES_CUA_DRIVER_CMD` 设置为生成的二进制文件。最适合快速编辑 / 构建 / 测试。

```bash
cargo build -p cua-driver            # add --release for a release build; run from libs/cua-driver/rust
```

```
# Windows (.env)
HERMES_CUA_DRIVER_CMD=C:\path\to\cua\libs\cua-driver\rust\target\debug\cua-driver.exe
# macOS / Linux (.env)
HERMES_CUA_DRIVER_CMD=/path/to/cua/libs/cua-driver/rust/target/debug/cua-driver
```

### 确认 Hermes 正在使用你的构建

- `hermes computer-use status` 会打印解析出的二进制文件路径和版本。
- `hermes computer-use doctor` 会确认二进制文件可访问，并端到端地执行完整 MCP 路径。
- 在会话中，`computer_use(action="capture")` 会执行生成的 `cua-driver mcp` 子进程。

### 注意事项与易踩坑

- **Hermes 会通过 stdio 生成自己的 `cua-driver mcp` 子进程**——它不会连接长期运行的 `cua-driver serve` 自动启动守护进程或其命名管道。因此，测试不需要计划任务 / LaunchAgent（使用 `-NoAutoStart` 即可）。自动启动守护进程和 Windows UIAccess 工作进程（`cua-driver-uia.exe`）只对某些应用（例如 WPF）的前台安全输入有影响；标准工具界面通过 stdio 子进程工作。在 Windows SSH 会话中，确实需要自动启动模式——请参见“限制”部分。
- **Windows 上的二进制文件被锁定。** 正在运行的 `cua-driver-serve` 守护进程可能会占用 `cua-driver.exe`，阻止重建时覆盖文件。`install-local.ps1` 会自动将被锁定的二进制文件重命名移开；如果你手动运行 `cargo build`（选项 B），请先使用 `cua-driver autostart disable`（或 `schtasks /End /TN cua-driver-serve`）停止它。
- **重建循环。** 编辑 cua-driver 源代码后，选项 A 重新运行 `install-local`（它会重新构建、重新暂存并切换 `current` junction），选项 B 只需重新运行 `cargo build`——无论哪种方式都不需要修改 Hermes。
- **本地构建会跳过版本检查。** Hermes 会在已安装的 cua-driver 低于各操作系统的测试基线时发出警告，但会豁免 `0.0.0-local-*` 开发构建，因此本地构建永远不会触发该警告。

## 故障排除

**遇到任何问题时的第一步：运行 `hermes computer-use doctor`。**结构化的逐项检查矩阵会告诉你（以及任何帮助你调试的代理）究竟哪里出了问题。

doctor 无法捕获的具体故障模式：

**`computer_use backend unavailable: cua-driver is not installed`**——运行 `hermes computer-use install` 获取 cua-driver 二进制文件，或运行 `hermes tools` 并启用 Computer Use 工具集。

**点击似乎没有效果**——先捕获并验证。你没有看到的模态窗口可能阻塞了输入。使用 `escape` 或关闭按钮将其关闭。

**元素索引已过时**——SOM 索引只在下一次 `capture` 之前有效。在任何改变状态的操作后重新捕获。封装器会使用不透明的 `element_token`s 检测过期情况——你会看到明确的错误，而不是错误的点击。

**“type 文本中存在阻止模式”**——你试图 `type` 的文本匹配危险 shell 模式列表。请拆分命令或重新考虑这一操作。

**Linux 上的捕获为空**——可能是未设置 `DISPLAY`，或者你处于没有 XWayland 桥接的纯 Wayland 环境。`hermes computer-use doctor` 会将其标记为 `ax_capability: fail`，并给出 `Set DISPLAY (X11)…` 提示。

**通过 SSH 在 Windows 上捕获为空**——你处于 Session 0（服务会话）。直接从 RDP / 控制台驱动，或设置自动启动模式——参见 [cua.ai/docs/how-to-guides/driver/windows-ssh](https://cua.ai/docs/how-to-guides/driver/windows-ssh)。

## 另请参阅

- **Hermes 侧技能**——`skills/autonomous-ai-agents/computer-use/SKILL.md`——教授 Hermes 的 `computer_use` 操作词汇；这是代理加载的内容。
- **cua-driver 技能包**——如需平台特定的深度解析（macOS 无前台契约、Windows UIA + Session 0、Linux AT-SPI + X11/Wayland、录制和浏览器页面），请运行 `cua-driver skills install` 并阅读 `MACOS.md` / `WINDOWS.md` / `LINUX.md` / `RECORDING.md` / `WEB_APPS.md`。一旦 `cua-driver skills install` 自动检测到 Hermes（计划中的后续工作），安装时就会自动完成这一过程。
- **cua.ai/docs**——cua-driver 项目的文档：
  - [什么是计算机使用？](https://cua.ai/docs/explanation/what-is-computer-use) — 概念介绍
  - [无前台契约](https://cua.ai/docs/explanation/the-no-foreground-contract) — *为什么*后台模式很重要
  - [安装参考](https://cua.ai/docs/how-to-guides/driver/install) — 跨平台安装详情
  - [自定义代理光标](https://cua.ai/docs/how-to-guides/driver/personalize-cursor) — 内置形状、自定义资源和运行时覆盖
  - [通过 SSH 驱动 Windows](https://cua.ai/docs/how-to-guides/driver/windows-ssh) — Session 0 → Session 1+ 自动启动模式
  - [保持 cua-driver 运行](https://cua.ai/docs/how-to-guides/driver/keep-running) — 自动启动 / 守护进程生命周期
  - [连接你的代理](https://cua.ai/docs/how-to-guides/driver/connect-your-agent) — 将 cua-driver 注册到各种框架（包括 Hermes）
- [cua-driver 源代码（trycua/cua）](https://github.com/trycua/cua)
- [浏览器自动化](./browser.md)，用于不需要驱动原生应用的跨平台网页任务。
