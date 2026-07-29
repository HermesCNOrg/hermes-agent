---
标题： 计算机使用侧边栏位置：16---

# Computer Use

Hermes Agent 可以驱动您的桌面 — 单击、打字、滚动、拖动 — 在 **macOS、Windows 和 Linux** 上的 **背景** 中。你的光标不移动，键盘焦点不改变，并且您的虚拟桌面/空间不会打开你的心。您和代理人共同致力于同一台机器。
与大多数计算机使用的集成不同，这适用于**任何支持工具的工具model** — Claude、GPT、Gemini 或本地的开放模型OpenAI 兼容端点。无需担心人类原生模式关于。
## How it works

`computer_use` 工具集通过 stdio 与 MCP 进行对话[`cua-driver`](https://github.com/trycua/cua),开源后台计算机使用的驱动程序。每个平台都使用适当的辅助功能+输入堆栈在引擎盖下：
| Platform | Accessibility tree | Input dispatch |
|---|---|---|
| macOS | AX (private SkyLight SPIs) | `SLPSPostEventRecordTo` — pid-scoped, no cursor warp |
| Windows | UIAutomation | `SendInput` + `PostMessage` — no focus steal |
| Linux | AT-SPI (X11 + Wayland) | XTest (X11) / virtual-keyboard (Wayland) |

每个平台上的结果都是相同的：代理可以读取任何可见窗口和后期合成事件的可访问性树无需将其置于前台、切换虚拟桌面或移动真实操作系统光标。
对于基础合约——*为什么*后台模式很重要，无前景不变性，点击调度内部结构 - 请参阅**[cua.ai/docs/explanation/the-no-foreground-contract](https://cua.ai/docs/explanation/the-no-foreground-contract)**.
## Enabling

选择最方便的路径——两条路径都在同一条上游安装人员：
**选项 1：专用 CLI 命令（最直接）。**
```
hermes computer-use install
```

这将获取并运行上游 cua 驱动程序安装程序 — `install.sh`在 macOS/Linux 上，`install.ps1` 在 Windows 上。使用“hermes电脑使用”status` 来验证安装。
**选项 2：以交互方式启用工具集。**
1. Run `hermes tools`, pick `🖱️  Computer Use (macOS/Windows/Linux)`.
2. The setup runs the upstream installer (same as Option 1).

安装后，无论选择哪个路径，都授予适合平台的先决条件：
| Platform | Prereqs |
|---|---|
| **macOS** | System Settings → Privacy & Security → **Accessibility** + **Screen Recording** → allow your terminal (or Hermes app). `hermes computer-use doctor` will tell you which permission is missing. |
| **Windows** | None at install time. If you're driving over SSH (not RDP / console), you need the autostart pattern — see [cua.ai/docs/how-to-guides/driver/windows-ssh](https://cua.ai/docs/how-to-guides/driver/windows-ssh) for the Session 0 ↔ Session 1+ proxy. |
| **Linux** | A reachable display server: `DISPLAY` set for X11, or `XDG_SESSION_TYPE=wayland`. Wayland sessions need an XWayland bridge for capture. AT-SPI must be on (default on GNOME/KDE/Xfce). |

然后在启用工具集的情况下启动会话：
```
hermes -t computer_use chat
```

或将 `computer_use` 添加到 `~/.hermes/config.yaml` 中启用的工具集中。
## `hermes computer-use doctor` — your first triage stop

`hermes computer-use doctor` 运行 cua-driver 的结构化`health_report` MCP 工具并打印每个检查矩阵。这是单曲找出“为什么”某个操作不起作用的最快方法。
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

- **Exit code 0** when overall is `ok` — everything's wired up.
- **Exit code 1** when `degraded` or `failed` — at least one check failed; the hint on each failure tells you what to fix.
- **Exit code 2** when the cua-driver binary itself isn't reachable.

有用的标志：
- `--include CHECK` — run only the listed checks (repeat for multiple)
- `--skip CHECK` — skip a check (wins over `--include`)
- `--json` — emit the raw structured payload, same shape as the
`tools/call health_report` MCP 响应
校验矩阵是平台感知的：`bundle_identity` / `tcc_*` 是Windows + Linux 上的 `skip` 因为这些概念不适用。`ax_capability` 检查 macOS 上的 AX、Windows 上的 UIA、Linux 上的 AT-SPI —当无法到达时，每个都具有正确的诊断提示。
## The agent cursor and sessions

当代理行动时，您将看到**有色覆盖光标**滑动穿过屏幕到每次点击/键入/滚动所着陆的位置。真实的操作系统光标永远不会移动——覆盖层是一个视觉提示，上面写着“代理正在这里行动。” 每个 Hermes 运行都会声明自己的 cua-driver**会话 ID**（类似于 `hermes-3a7b9c14d2e8`）；光标的身份是该会话的关键，因此每个并发运行/子代理获得自己的光标而不踩到对方。
使用 `cua-driver` 的 CLI 标志或运行时调整光标`set_agent_cursor_style` MCP 工具 — 请参阅[cua.ai/docs/how-to-guides/driver/personalize-cursor](https://cua.ai/docs/how-to-guides/driver/personalize-cursor)完整菜单（内置 `arrow` 与 `teardrop` 轮廓、自定义SVG / PNG / ICO 通过 `--cursor-icon`，运行时渐变颜色，绽放晕）。
## Going deeper — the cua-driver skill pack

赫尔墨斯有意保留其技能（`skills/autonomous-ai-agents/computer-use/SKILL.md`）重点关注爱马仕这边的`computer_use`动作词汇——代理加载的单一事实来源。对于更深层次的材料 -特定于平台的深入研究、记录语义、浏览器页面交互——将你的特工安全带指向 cua-driver 技能包cua-driver 团队直接运送和维护：
```
cua-driver skills install
```

这会将包符号链接到您的代理工具的技能目录中。后运行它，代理可以访问：
| File | Topic |
|---|---|
| `SKILL.md` | The cross-platform core (snapshot invariant, no-foreground contract, click dispatch, AX-tree mechanics) |
| `MACOS.md` | macOS specifics: no-foreground contract, AXMenuBar navigation, SkyLight click dispatch, Apple Events JS bridge |
| `WINDOWS.md` | Windows specifics: UIA tree, UWP / `ApplicationFrameHost` hosting, Session 0 isolation, autostart pattern |
| `LINUX.md` | Linux specifics: AT-SPI tree, X11 / Wayland, terminal-emulator detection |
| `RECORDING.md` | Trajectory + video recording semantics |
| `WEB_APPS.md` | Browser-page interaction tips |
| `TESTS.md` | Replay-by-trajectory workflow |

这些是**平台深入研究，而不是赫尔墨斯技能的重复** -当代理报告“在 Windows 上，我的点击落在了错误的位置”元素，”它读取 `WINDOWS.md` 表示 UIA / UWP 上下文解释原因以及采取不同的做法。
`cua-driver skills status` 显示已安装的内容和代理它所链接的线束。今天自动检测列表涵盖了克劳德Code、Codex、OpenCode、OpenClaw 和 Antigravity； **爱马仕自动检测计划作为 `trycua/cua`** 的后续措施 — 直到然后，运行 `cua-driver skills install` 一次并将安全带指向生成的 `~/.cua-driver/skills/cua-driver` 目录（或符号链接将其纳入您常用的技能空间）。
## Quick example

用户提示：*“查找我来自 Stripe 的最新电子邮件并总结他们希望我做什么。”*
特工的计划（这与 macOS / Windows / Linux 上的形状相同 -该模型替换了平台惯用的快捷方式和应用程序名称）：
1. `computer_use(action="capture", mode="som", app="Mail")` — gets a
电子邮件应用程序的屏幕截图，包含每个侧边栏项目、工具栏按钮、和消息行编号。2. `computer_use(action="click", element=14)` — clicks the search field.
3. `computer_use(action="type", text="from:stripe")`
4. `computer_use(action="key", keys="return", capture_after=True)` —
提交并获取新的屏幕截图。5. Click the top result, read the body, summarise.

在这一切过程中，您的光标和电子邮件都会停留在您离开的地方应用程序永远不会出现在前面。
## Provider compatibility

| Provider | Vision? | Works? | Notes |
|---|---|---|---|
| Anthropic (Claude Sonnet/Opus 3+) | ✅ | ✅ | Best overall; SOM + raw coordinates. |
| OpenRouter (any vision model) | ✅ | ✅ | Multi-part tool messages supported. |
| OpenAI (GPT-4+, GPT-5) | ✅ | ✅ | Same as above. |
| Google (Gemini 2+) | ✅ | ✅ | Tool-calling + vision both supported. |
| Local vLLM / LM Studio / Ollama (vision model) | ✅ | ✅ | If the model supports multi-part tool content. |
| Text-only models | ❌ | ✅ (degraded) | Use `mode="ax"` for accessibility-tree-only operation. |

屏幕截图以 OpenAI 风格的 `image_url` 形式与工具结果一起发送部分。对于 Anthropic，适配器将它们转换为原生 `tool_result`图像块。图像 MIME 类型来自 cua-driver 的显式`mimeType` 字段（`image/png` 或 `image/jpeg`） — 无客户端魔术字节嗅探。
## Safety

Hermes采用多层护栏：
- Destructive actions (click, type, drag, scroll, key, focus_app)
需要批准 - 通过 CLI 对话框交互或通过消息传递平台批准按钮。- Hard-blocked key combos at the tool level: empty trash, force delete,
锁屏、注销、强制注销。- Hard-blocked type patterns: `curl | bash`, `sudo rm -rf /`, fork
炸弹等- The agent's system prompt tells it explicitly: no clicking permission
对话框，无需输入密码，无需嵌入以下说明截图。
与 `~/.hermes/config.yaml` 中的 `approvals.mode: manual` 配对，如果您希望每一个行动都得到确认。
## Token efficiency

截图很贵。 Hermes 应用了四层优化：
- **Screenshot eviction** — the Anthropic adapter keeps only the 3 most
最近的上下文截图；年长的变成了`[屏幕截图已删除保存上下文]`占位符。- **Client-side compression pruning** — the context compressor detects
多模式工具结果并从旧图像中剥离图像部分。- **Image-aware token estimation** — each image is counted as ~1500
令牌（Anthropic 的统一费率）而不是其 base64 字符长度。- **Server-side context editing (Anthropic only)** — when active, the
适配器通过 `context_management` 启用 `clear_tool_uses_20250919`，因此Anthropic 的 API 会在服务器端清除旧工具结果。
在 1568×900 显示屏上执行 20 个操作的会话通常需要约 30K 代币屏幕截图上下文，而不是 ~600K。
## Limitations

- **Performance.** Background mode is slower than foreground —
可访问性路由事件在 macOS 上大约需要 5–20 毫秒，在 macOS 上大约需要 3–10 毫秒Windows UIA，Linux AT-SPI 与直接 HID 发布相比约为 5–15 毫秒。不是代理速度点击明显；如果您尝试记录，就会注意到快速奔跑。- **No keyboard password entry.** `type` has hard-block patterns on
命令外壳有效负载；对于密码，请使用系统的自动填充（macOS 钥匙串 / Windows 凭据管理器 / GNOME 钥匙圈 /K钱包）。- **Some apps don't expose an accessibility tree.** Modern UWP apps on
Windows、Linux 上的 Electron < 28 以及一些具有自定义功能的 macOS 应用程序绘图（Logic、Final Cut、某些游戏）具有稀疏或空的 AX 树。如果树为空，则回退到像素坐标 - 或跳过任务完全。- **Windows: elevated (admin) windows can't be driven from a normal
** Windows UIPI（用户界面权限隔离）强制执行完整性级别边界：中等完整性进程（默认Hermes 代理）无法枚举 UIA 树，或注入鼠标输入进入由高完整性（管理员）进程拥有的窗口。症状：`capture(mode='som')` 返回 0 个元素且 `click(...)`即使屏幕截图显示成功，但什么也不做渲染良好（GDI 捕获位于完整性检查下方）。键盘事件部分绕过 UIPI，因此 Tab / Enter 仍然可以导航提升的对话。这是一个操作系统限制，而不是 cua 驱动程序错误 — 它影响每个 Windows 自动化堆栈。要驱动高架窗户，以高度完整性运行 Hermes 代理本身（从高架航站楼）；否则，目标是非高架窗户。- **Platform-specific deployment gotchas:**
  - **macOS** uses private SkyLight SPIs. Apple can change them in any
操作系统更新。当安装的 cua 驱动程序旧于以下版本时，Hermes 会发出警告测试的版本。  - **Windows** SSH sessions run in **Session 0**, which has no
交互式桌面。从 RDP/控制台内部驱动 Hermes会话，或设置 cua-driver 的自动启动计划任务 —[windows-ssh](https://cua.ai/docs/how-to-guides/driver/windows-ssh)有食谱。  - **Linux** requires a reachable display server. Headless servers
之前需要 Xvfb (`Xvfb :99 -screen 0 1920x1080x24`)`computer_use` 可以捕获或注入事件。 Pure Wayland 会话需要一个 XWayland 桥来进行屏幕捕获（cua-driver 的 Wayland注入路径独立处理输入）。
用于跨平台 GUI 自动化，无需桌面开销（并且没有 TCC / 会话 0 / X11 设置），`browser` 工具集使用真正的无头 Chromium，是仅网络任务的正确答案。
## Configuration

覆盖驱动程序二进制路径（测试/CI/本地构建）：
```
HERMES_CUA_DRIVER_CMD=/path/to/your/cua-driver
```

完全交换后端（用于测试）：
```
HERMES_COMPUTER_USE_BACKEND=noop   # records calls, no side effects
```

### Telemetry

cua-driver 附带默认启用的匿名使用遥测 (PostHog)上游。 **Hermes 会为您禁用它** — 在每次 cua-driver 调用时（MCP后端，`status`，`doctor`，并安装）Hermes套装驱动程序环境中的 `CUA_DRIVER_RS_TELEMETRY_ENABLED=0`。
要选择重新加入（让 cua-driver 使用其自己的默认值并发送遥测数据），请设置`config.yaml` 中的这个：
```yaml
computer_use:
  cua_telemetry: true   # default: false (telemetry off)
```

开启时，`hermes computer-use doctor` 报告 `telemetry: enabled`；关闭时（默认），它报告“遥测：通过CUA_DRIVER_RS_TELEMETRY_ENABLED`。
## Testing against a local cua-driver build

当您正在开发 cua-driver 本身 - 或者想要测试一个未发布的修复 - 将 Hermes 指向您从源代码构建的二进制文件已发布的版本。 Hermes 解决了驱动程序`shutil.which("cua-driver")` 和 ** 不强制执行`HERMES_CUA_DRIVER_VERSION`**，因此本地构建（报告为`0.0.0-local-*`) 按原样接受。两种方法：
### Option A — `install-local` (build + put it on PATH)

从 `trycua/cua` 结账中，运行上游本地安装程序。它在发布模式下构建 Rust 后端并将 `cua-driver` 放入与生产安装程序使用相同的安装布局，添加其 bin 目录到你的路径：
```powershell
# Windows (PowerShell), from the cua repo root
./libs/cua-driver/scripts/install-local.ps1 -NoAutoStart
```

```bash
# macOS / Linux, from the cua repo root  (defaults to a debug build without --release)
./libs/cua-driver/scripts/install-local.sh --release
```

- Windows stages the build under `%USERPROFILE%\.cua-driver\packages\…`
和路口`%LOCALAPPDATA%\Programs\Cua\cua-driver\bin`（添加到您的用户路径）到它。 macOS/Linux 将 `cua-driver` 符号链接到 `~/.local/bin`（用 `--bin-dir <path>` 覆盖）。- `-NoAutoStart` skips registering the `cua-driver-serve` logon daemon
— Hermes 测试不需要它（见注释）。
然后打开一个新的 shell（因此 PATH 更改可见）并确认：
```
cua-driver --version                 # local builds report 0.0.0-local-release
# Windows:      (Get-Command cua-driver).Source
# macOS/Linux:  which cua-driver
```

### Option B — point Hermes straight at the built binary (fastest loop)

完全跳过安装仪式：`cargo build` 并设置`HERMES_CUA_DRIVER_CMD` 到生成的二进制文件。最适合快速编辑/构建/测试。
```bash
cargo build -p cua-driver            # add --release for a release build; run from libs/cua-driver/rust
```

```
# Windows (.env)
HERMES_CUA_DRIVER_CMD=C:\path\to\cua\libs\cua-driver\rust\target\debug\cua-driver.exe
# macOS / Linux (.env)
HERMES_CUA_DRIVER_CMD=/path/to/cua/libs/cua-driver/rust/target/debug/cua-driver
```

### Confirm Hermes is using your build

- `hermes computer-use status` prints the resolved binary path and
版本。- `hermes computer-use doctor` confirms the binary is reachable and
端到端地练习完整的 MCP 路径。- In a session, `computer_use(action="capture")` exercises the spawned
`cua-driver mcp` 子进程。
### Notes & gotchas

- **Hermes spawns its own `cua-driver mcp` child over stdio** — it does
*不*附加到长时间运行的 `cua-driver serve` 自动启动守护进程或其命名管道。所以计划任务/LaunchAgent是不必要的用于测试（`-NoAutoStart` 就可以）。自动启动守护进程和Windows UIAccess 工作线程 (`cua-driver-uia.exe`) 仅适用于某些应用程序上的前台安全输入（例如 WPF）；标准工具Surface 通过 stdio 子项工作。在 Windows SSH 会话上，需要自动启动模式 - 请参阅限制部分。- **Locked binary on Windows.** A running `cua-driver-serve` daemon can
保留 `cua-driver.exe` 并阻止重建时的覆盖。`install-local.ps1` 重命名锁定的二进制文件自动地;如果您手动 `cargo build`（选项 B），请停止它首先使用 `cua-driver autostart disable` （或 `schtasks /End /TNcua-司机-服务`）。- **Rebuild loop.** After editing cua-driver source, re-run
`install-local`（重建、重新安置、翻转 `current` 连接点）对于选项 A，或者只是重新 `cargo build` 对于选项 B — 没有 Hermes无论哪种方式都需要改变。- **Local builds skip the version check.** Hermes warns when the
安装的 cua-driver 比其每个操作系统测试的基准更旧，但是免除 `0.0.0-local-*` 开发构建 - 所以你的本地构建永远不会触发该警告。
## Troubleshooting

**出现任何问题时的第一个操作：运行 `hermes computer-use doctor`。**结构化的每次检查矩阵告诉您（以及任何帮助您的代理）调试）到底出了什么问题。
医生没有发现的具体故障模式：
**`computer_use backend unavailable: cua-driver is not installed`** —运行 `hermes computer-use install` 以获取 cua-driver 二进制文件，或者运行 `hermes tools` 并启用计算机使用工具集。
**点击似乎没有效果** — 捕获并验证。模态的你没看到可能是阻塞输入。使用 `escape` 或 close 关闭它按钮。
**元素索引已过时** — SOM 索引仅在下一个`capture`。在执行任何状态更改操作后重新捕获。这包装器带有不透明的 `element_token`s 用于陈旧检测 - 你会看到明确的错误而不是错误的点击。
**“类型文本中的阻止模式”** — 您尝试 `type` 的文本匹配危险 shell 模式列表。分解命令或重新考虑一下。
**Linux 上的空捕获** — `DISPLAY` 未设置，或者您使用纯没有 XWayland 桥的 Wayland。 `hermes computer-use doctor` 将使用 `Set DISPLAY (X11)…` 提示将其标记为 `ax_capability: fail`。
**通过 SSH 在 Windows 上进行空捕获** — 您处于会话 0（会话服务会议）。直接从 RDP/控制台驱动，或设置自动启动模式 — 请参阅[cua.ai/docs/how-to-guides/driver/windows-ssh](https://cua.ai/docs/how-to-guides/driver/windows-ssh).
## See also

- **Hermes-side skill** — `skills/autonomous-ai-agents/computer-use/SKILL.md` — teaches the
爱马仕`computer_use`动作词汇；这就是代理加载的内容。- **cua-driver skill pack** — for platform-specific deep dives
（macOS 无前台合约、Windows UIA + Session 0、Linux AT-SPI  + X11/Wayland, recording, browser pages), run
`cua-driver skills install` 并读取 `MACOS.md` / `WINDOWS.md` /`LINUX.md` / `RECORDING.md` / `WEB_APPS.md`。一旦`cua-司机技能install`自动检测Hermes（计划的后续），会发生这种情况安装时自动。- **cua.ai/docs** — the cua-driver project's documentation:
  - [What is computer use?](https://cua.ai/docs/explanation/what-is-computer-use) — concept intro
  - [The no-foreground contract](https://cua.ai/docs/explanation/the-no-foreground-contract) — *why* background mode matters
  - [Install reference](https://cua.ai/docs/how-to-guides/driver/install) — cross-platform install details
  - [Personalize the agent cursor](https://cua.ai/docs/how-to-guides/driver/personalize-cursor) — built-in shapes, custom assets, runtime overrides
  - [Drive Windows over SSH](https://cua.ai/docs/how-to-guides/driver/windows-ssh) — the Session 0 → Session 1+ autostart pattern
  - [Keep cua-driver running](https://cua.ai/docs/how-to-guides/driver/keep-running) — autostart / daemon lifecycle
  - [Connect your agent](https://cua.ai/docs/how-to-guides/driver/connect-your-agent) — register cua-driver with various harnesses (Hermes among them)
- [cua-driver source (trycua/cua)](https://github.com/trycua/cua)
- [Browser automation](./browser.md) for cross-platform web tasks where you don't need to drive native apps.
