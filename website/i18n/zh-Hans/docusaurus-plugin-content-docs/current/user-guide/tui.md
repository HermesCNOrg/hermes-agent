---
sidebar_position: 2
title: "TUI"
description: "启动 Hermes 的现代终端 UI——支持鼠标操作、丰富的浮层和非阻塞输入。"
---

# TUI

TUI 是 Hermes 的现代前端——一个终端 UI，与 [Classic CLI](cli.md) 使用相同的 Python 运行时。相同的 agent、相同的会话、相同的斜杠命令；只是一个更简洁、响应更灵敏的交互界面。

这是以交互方式运行 Hermes 的推荐方式。

## 启动

```bash
# 启动 TUI
hermes --tui

# 恢复最近的 TUI 会话（回退到最近的 classic 会话）
hermes --tui -c
hermes --tui --continue

# 通过 ID 或标题恢复特定会话
hermes --tui -r 20260409_000000_aa11bb
hermes --tui --resume "my t0p session"

# 直接运行源码——跳过预构建步骤（供 TUI 贡献者使用）
hermes --tui --dev
```

也可通过环境变量启用：

```bash
export HERMES_TUI=1
hermes          # 现在使用 TUI
hermes chat     # 同样如此
```

或者在 `~/.hermes/config.yaml` 中将它设为持久默认值：

```yaml
display:
  interface: tui   # "cli"（默认）或 "tui"
```

使用 `display.interface: tui` 时，不带参数的 `hermes`（以及 `hermes chat`）会启动 TUI。显式标志始终优先——对于单次调用，运行 `hermes --cli` 可回到 classic REPL；当配置默认值为 `cli` 时，使用 `hermes --tui` / `HERMES_TUI=1` 可强制使用 TUI。

classic CLI 仍是随产品发布的默认界面。[CLI Interface](cli.md) 中记录的所有功能——斜杠命令、快捷命令、skill 预加载、personality、多行输入、中断——在 TUI 中完全相同。

## 为什么选择 TUI

- **即时首帧** — 应用完成加载前就绘制 banner，因此 Hermes 启动时终端不会显得卡住。
- **非阻塞输入** — 会话就绪前即可输入并排队消息。agent 上线的瞬间便会发送你的第一条 prompt。
- **丰富的浮层** — 模型选择器、会话选择器、审批及澄清提示都会渲染为模态面板，而不是内联流程。
- **实时会话面板** — 工具和 skill 会在初始化时逐步填入。
- **鼠标友好的选择** — 拖动时以统一背景突出显示，而不是 SGR 反色。可使用终端正常的复制手势复制。
- **备用屏幕渲染** — 差异更新意味着流式传输时不会闪烁，退出后也不会留下滚动历史杂乱内容。
- **编辑器功能** — 长片段内联折叠粘贴、`Cmd+V` / `Ctrl+V` 文本粘贴及剪贴板图片回退、括号粘贴安全，以及图片/文件路径附件规范化。

相同的 [skins](features/skins.md) 和 [personalities](features/personality.md) 都适用。可在会话中途用 `/skin ares`、`/personality pirate` 切换，UI 会实时重绘。有关完整可自定义键列表，以及它们适用于 classic 还是 TUI，请参阅 [Skins & Themes](features/skins.md)——TUI 支持 banner 调色板、UI 颜色、prompt 字形/颜色、会话显示、补全菜单、选择背景、`tool_prefix` 和 `help_header`。

### 可折叠的 banner 区段

TUI 启动 banner 将运行时信息分为四个可折叠区段，每个区段标题旁都有 `▸` / `▾` 箭头：

| 区段 | 默认状态 |
|---------|---------------|
| Tools | 打开 |
| Skills | 折叠 |
| System Prompt | 折叠 |
| MCP Servers | 折叠 |

点击区段标题（或箭头）的任何位置即可切换它。Tools 列表默认打开，因为它是会话启动时查看最多的区段；Skills、System Prompt 和 MCP Servers 默认折叠，因此即使已安装数十个 skill 或接入许多 MCP server，banner 仍保持紧凑。状态仅属于该 banner 实例，下一次启动会恢复默认值。

## 要求

- **Node.js** ≥ 20 — TUI 作为由 Python CLI 启动的子进程运行。`hermes doctor` 会验证此项。
- **TTY** — 与 classic CLI 一样，若管道传入 stdin 或在非交互环境运行，将回退到单查询模式。

首次启动时，Hermes 会将 TUI 的 Node 依赖安装到 `ui-tui/node_modules`（一次性操作，需数秒）。后续启动很快。拉取新 Hermes 版本后，源文件比 dist 更新时会自动重建 TUI bundle。

:::tip 在 git worktree 间工作？
从许多 worktree 运行 `hermes --tui --dev` 的贡献者可共享一个 `node_modules`，而无需在每个 checkout 中安装——请参阅 [TUI & Desktop from Worktrees](../developer-guide/worktree-ui-dev.md)。
:::

### 外部预构建

附带预构建 bundle 的发行版（Nix、系统包）可让 Hermes 指向它：

```bash
export HERMES_TUI_DIR=/path/to/prebuilt/ui-tui
hermes --tui
```

目录必须包含 `dist/entry.js`。

## 快捷键

快捷键与 [Classic CLI](cli.md#keybindings) 完全一致。仅有以下行为差异：

- **鼠标拖动** 会以统一的选择背景突出文本。
- **`Cmd+V` / `Ctrl+V`** 先尝试正常文本粘贴，随后回退到 OSC52/原生剪贴板读取，最后当剪贴板或粘贴负载解析为图像时附加图像。
- **`/terminal-setup`** 为本地 VS Code / Cursor / Windsurf 安装终端绑定，以在 macOS 上获得更好的 `Cmd+Enter` 及撤销/重做一致性。
- **斜杠自动补全** 会作为带描述的浮动面板打开，而不是内联下拉菜单。
- **`Ctrl+X`** 打开实时会话切换器。若已高亮排队消息（agent 仍在运行时发送），它仍会删除该排队消息。**`Esc`** 取消编辑并取消高亮，不会删除。
- **`Ctrl+G` / `Ctrl+X Ctrl+E`** 在 `$EDITOR` 中打开当前输入缓冲区，以编写多行/长 prompt；保存并退出会将内容作为 prompt 发送回来。

## 斜杠命令

所有斜杠命令都可原样使用。其中少数由 TUI 所有——它们会产生更丰富的输出，或渲染为浮层而不是内联面板：

| 命令 | TUI 行为 |
|---------|--------------|
| `/help` | 含分类命令的浮层，可用方向键导航 |
| `/sessions`（别名 `/switch`） | 实时会话切换器——列出打开的 TUI 会话、在它们之间切换、关闭它们，或另开一个 |
| `/model` | 按 provider 分组、带费用提示的模态模型选择器 |
| `/skin` | 实时预览——浏览时即应用主题更改 |
| `/details` | 切换详细工具调用详情（全局或每区段） |
| `/usage` | 丰富的 token / 费用 / 上下文面板 |
| `/agents`（别名 `/tasks`） | 可观测性浮层——带终止/暂停控制的实时 subagent 树、每分支费用 / token / 文件汇总、逐轮历史 |
| `/reload` | 将 `~/.hermes/.env` 重新读入运行中的 TUI 进程，使新添 API key 无需重启即可生效 |
| `/mouse [on\|off\|toggle\|wheel\|buttons\|all]` | 在运行时选择鼠标跟踪预设（也会持久化到 `config.yaml` 的 `display.mouse_tracking`）。`wheel`（1000+1006）保留滚轮滚动，不含使 tmux 在 prompt 行不断输出 "No image in clipboard" 的悬停事件；`buttons` 添加拖动选择；`all` 是带悬停驱动 UI 的默认值。 |

其他每个斜杠命令（包括安装的 skill、快捷命令和 personality 切换）均与 classic CLI 相同。参阅[斜杠命令参考](../reference/slash-commands.md)。

## 实时会话切换器

当你希望一个终端充当多个 TUI 会话的调度器时，请使用实时会话切换器。它仅列出此 TUI 进程当前仍在运行的会话；已关闭会话仍保存为转录，可用 `/resume` 或 `hermes --tui --resume <id-or-title>` 重新打开。

可通过以下任一方式打开：

- 在 TUI 中按 `Ctrl+X`。
- `/sessions` 或 `/switch`。
- `/sessions new`，立即创建一个新的实时会话。
- 点击状态行中的 `N live sessions` 计数。

<img alt="Hermes TUI Session Orchestrator with one live session and a +new row" src="/docs/img/docs/tui-session-orchestrator/session-orchestrator.png" />

<video controls muted loop playsInline src="/docs/img/docs/tui-session-orchestrator/session-orchestrator-demo.mp4" title="Hermes TUI Session Orchestrator demo" style={{maxWidth: '100%'}}></video>

在切换器内：

- `↑` / `↓` 移动选择；鼠标点击也可选择行。
- `Enter` 切换到选定的实时会话。
- `Ctrl+D` 关闭选定的实时会话。
- `Ctrl+N` 启动空白实时会话。
- `Ctrl+R` 刷新实时会话列表。
- `Esc` 关闭切换器。
- 选择 `+new`，输入 prompt 后按 `Enter`，即可调度一个新的实时会话。若仅想为该新会话选择模型，请先按 `Tab`。

## LaTeX 数学渲染

TUI 的 Markdown 管线内联渲染 LaTeX 数学：`$E = mc^2$` 和 `$$\frac{a}{b}$$` 会渲染为 Unicode 格式数学，而不是原始 TeX 源码。支持内联和块级数学；不支持的语法会回退为显示包在代码 span 中的原样 TeX，以保持可复制性。

它始终开启，无需配置。classic CLI 保留原始 TeX。

## 浅色终端检测

TUI 会自动检测浅色终端，并相应换用浅色主题。检测有三层：

1. `HERMES_TUI_THEME` 环境变量——最高优先级。取值为 `light`、`dark`，或原始 6 字符背景色十六进制值（例如 `ffffff`、`1a1a2e`）。
2. `COLORFGBG` 环境变量——xterm 衍生终端使用的经典“我的背景色是什么？”提示。
3. 通过 OSC 11 探测终端背景——适用于未设置 `COLORFGBG` 的现代终端（Ghostty、Warp、iTerm2、WezTerm、Kitty）。

若无论终端为何都希望永久使用浅色主题：

```bash
export HERMES_TUI_THEME=light
```

## 忙碌指示器样式

状态栏的忙碌指示器可插拔——默认会在 agent 工作时每 2.5 秒轮换 Hermes 的 kawaii 表情调色板。通过配置或 `/indicator` 斜杠命令选择其他样式：

```yaml
display:
  tui_status_indicator: kaomoji   # kaomoji | emoji | unicode | ascii
```

或者在会话中：`/indicator emoji`（等）。各样式配有匹配的字形宽度，轮换时状态栏其余部分不会抖动。

## 自动恢复

默认情况下，`hermes --tui` 每次启动均创建新会话。若要自动重新附加到最近的 TUI 会话（当终端或 SSH 连接意外中断时很有用），可选择启用：

```bash
export HERMES_TUI_RESUME=1          # 最近的 TUI 会话
# 或：
export HERMES_TUI_RESUME=<session-id>   # 特定会话
```

取消设置变量，或显式传递 `--resume <id>`，即可在每次启动时覆盖它。

## 状态行

TUI 的状态行实时跟踪 agent 状态：

| 状态 | 含义 |
|--------|---------|
| `starting agent…` | 会话 ID 已激活；工具和 skill 仍在上线。你可输入——消息会排队，并在就绪时发送。 |
| `ready` | Agent 空闲，接受输入。 |
| `thinking…` / `running…` | Agent 正在推理或运行工具。 |
| `interrupted` | 当前轮次已取消；按 Enter 再次发送。 |
| `forging session…` / `resuming…` | 初始连接或 `--resume` 握手。 |

每个 skin 的状态栏颜色及阈值与 classic CLI 共享——自定义请参阅 [Skins](features/skins.md)。

状态行还显示：

- **带 git 分支的工作目录** — `~/projects/hermes-agent (docs/two-week-gap-sweep)`。在侧边终端执行 `git checkout` 时，分支后缀会更新（有 mtime 缓存），因此 TUI 显示实际活动分支，而不是启动时的分支。
- **每条 prompt 的经过时间** — 轮次运行时为 `⏱ 12s/3m 45s`（实时），轮次结束后固定为 `⏲ 32s / 3m 45s`。第一个数字是自上条用户消息以来的时间；第二个是会话总时长。每次新 prompt 都会重置。
- **`🗜️ N`** — 运行中会话已自动压缩的次数。首次压缩发生后显示。
- **`▶ N`** — 此会话中正在运行的 `/background` 任务数。至少有一项任务在运行时显示。
- **`⚠ YOLO`** — YOLO 模式开启时的明显警告（`hermes --yolo`、`/yolo` 或 `HERMES_YOLO_MODE=1`）。同一徽章也显示在启动 banner 中，因此你不会在未察觉的情况下启动自动批准会话。

## 配置

TUI 遵循全部标准 Hermes 配置：`~/.hermes/config.yaml`、profile、personality、skin、快捷命令、凭证池、memory provider、工具/skill 启用。不存在 TUI 专用配置文件。

少数键专门调整 TUI 界面：

```yaml
display:
  skin: default              # 任意内置或自定义 skin
  personality: helpful
  details_mode: collapsed    # hidden | collapsed | expanded — 全局手风琴默认值
  sections:                  # 可选：按区段覆盖（任意子集）
    thinking: expanded       # 始终打开
    tools: expanded          # 始终打开
    activity: collapsed      # 重新启用 activity 面板（默认隐藏）
  mouse_tracking: all        # off | wheel | buttons | all（或 true/false，以保持向后兼容）。
                             #   wheel   — 1000+1006（滚动+点击；无拖动、无悬停——
                             #             推荐在 tmux 内使用，以消除 prompt 行上由悬停事件造成的
                             #             "No image in clipboard" 垃圾输出）
                             #   buttons — 添加 1002，支持终端侧拖动选择
                             #   all     — 添加 1003，支持悬停（滚动条悬停分页、
                             #             link mouseenter 等）
```

运行时切换：

- `/details [hidden|collapsed|expanded|cycle]` — 设置全局模式
- `/details <section> [hidden|collapsed|expanded|reset]` — 覆盖一个区段
  （区段：`thinking`、`tools`、`subagents`、`activity`）

**默认可见性**

TUI 带有明确的按区段默认值，将轮次作为实时转录流式呈现，而不是一整墙的箭头：

- `thinking` — **展开**。推理会随模型输出内联流式呈现。
- `tools` — **展开**。工具调用及结果以打开状态渲染。
- `subagents` — 使用全局 `details_mode`（默认折叠在箭头下——在真正发生委托前保持安静）。
- `activity` — **隐藏**。环境元数据（gateway 提示、终端一致性提示、后台通知）对日常多数使用而言是噪音。工具失败仍内联渲染在失败工具行中；当每个面板都隐藏时，环境错误/警告通过浮动警报兜底显示。

按区段覆盖优先于区段默认值和全局 `details_mode`。要重塑布局：

- `display.sections.thinking: collapsed` — 将 thinking 放回箭头下
- `display.sections.tools: collapsed` — 将工具调用放回箭头下
- `display.sections.activity: collapsed` — 重新启用 activity 面板
- 运行时使用 `/details <section> <mode>`

在 `display.sections` 中明确设置的任何内容优先于默认值，因此现有配置无需更改便可继续工作。

## 会话

会话在 TUI 和 classic CLI 间共享——二者都写入同一 `~/.hermes/state.db`。可在一方启动会话，在另一方恢复。会话选择器会显示两个来源的会话，并带有来源标签。

生命周期、搜索、压缩和导出请参阅[会话](sessions.md)。

## TUI 如何与其 gateway 通信

默认情况下，TUI 会生成自己的进程内 gateway，因此每个 TUI 实例都是自包含的——无需配置。

你可能会在代码库或日志中看到 `HERMES_TUI_GATEWAY_URL` 环境变量。这是 **web dashboard 的内部连接细节**，不是用户可用的远程附加开关。打开 dashboard 的“Chat”标签（`hermes dashboard` → `/chat`）时，dashboard 的 web server 会生成嵌入式 TUI 子进程，并注入 `HERMES_TUI_GATEWAY_URL`，让该子进程通过回环 WebSocket（`/api/ws`）附加到 dashboard 自己的进程内 `tui_gateway`。`/api/ws` 端点只存在于 dashboard server（`hermes_cli/web_server.py`）内，受该进程的生命周期和认证约束。

不存在通用的“将任意 TUI 指向任意独立 gateway 端口”模式。特别是，OpenAI 兼容 API server（`hermes gateway` / `api_server` platform）**不**提供 `/api/ws`——它是模型后端接口（`/v1/chat/completions`、`/v1/models`，……），并有意不暴露 TUI 的 JSON-RPC 控制通道。将 `HERMES_TUI_GATEWAY_URL` 设为该端口会得到 404。

若要让多个界面共享一组会话，请使用共享的 `~/.hermes/state.db`（参阅[会话](sessions.md)）或 web dashboard 的嵌入聊天（参阅 [Web Dashboard](features/web-dashboard.md#chat)），而非手动设置 gateway URL。

## 回到 classic CLI

默认情况下，不带 `--tui` 启动 `hermes` 仍使用 classic CLI。若要让一台机器偏好 TUI，请在 `~/.hermes/config.yaml` 中设置 `display.interface: tui`（持久），或在 shell profile 中设置 `HERMES_TUI=1`（每 shell）。要返回，设置 `interface: cli` / 取消设置环境变量，或单次传递 `hermes --cli`。

若 TUI 无法启动（没有 Node、缺少 bundle、TTY 问题），Hermes 会打印诊断并回退，不会让你卡住。

## 另请参阅

- [CLI Interface](cli.md) — 完整的斜杠命令和快捷键参考（共享）
- [Sessions](sessions.md) — 恢复、分支和历史
- [Skins & Themes](features/skins.md) — 主题化 banner、状态栏和浮层
- [Voice Mode](features/voice-mode.md) — 两个界面都可用
- [Configuration](configuration.md) — 所有配置键
