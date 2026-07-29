---
sidebar_position: 11
title: "宠物（Petdex 吉祥物）"
description: "领养一个动画吉祥物，它会在 CLI、TUI 和桌面应用中对智能体活动作出反应"
---

# 宠物

Hermes 可以显示一个动画**宠物**——一个小型吉祥物精灵，它会在 **CLI**、**TUI** 和**桌面应用**中，根据智能体正在进行的活动（空闲、运行工具、思考、完成、失败）作出反应。宠物来自公开的 [petdex](https://github.com/crafter-station/petdex) 图库。

宠物纯粹用于装饰。它们**不会影响提示缓存、token 或智能体的行为**——精灵仅与显示有关。该功能**默认关闭**，在你安装并选择宠物之前不会启用。

## 工作原理

- 宠物会安装到你配置文件的 `pets/` 目录中（`<HERMES_HOME>/pets/<slug>/`），因此每个[配置文件](../profiles.md)都有自己的一套宠物。
- 选择宠物会将 `display.pet.slug` 和 `display.pet.enabled` 写入 `config.yaml`——不会将任何内容存储为密钥或环境变量。
- 每个界面都会监视它本来就在跟踪的活动，并将其映射到六种动画状态之一。映射集中定义在一个位置，因此每个界面的行为都相同：

  | 智能体活动 | 宠物状态 |
  | --- | --- |
  | 工具/轮次刚刚失败 | `failed` |
  | 计划已完成（所有待办事项均已完成） | `jump`（庆祝） |
  | 轮次顺利完成 | `wave` |
  | 工具正在执行 | `run` |
  | 模型正在思考/阅读 | `review` |
  | 轮次正在进行（未指定） | `run` |
  | 正在等待你（有澄清/批准提示处于打开状态） | `waiting`（在旧版 8 行精灵表上回退为 `idle`） |
  | 无事发生 | `idle` |

## 渲染

在终端（CLI/TUI）中，如果你的终端支持图形协议（**kitty**、**Ghostty**、**WezTerm**、**iTerm2** 或 **sixel**），Hermes 会以完整保真度渲染精灵。否则，它会自动回退到真彩色 Unicode **半块字符**渲染。在管道或重定向中（无 TTY），终端渲染会按设计禁用。

桌面应用会将宠物作为浮动精灵绘制在画布上，并可通过**设置 → 外观**开关它。

## 快速开始（CLI）

```bash
# Browse the gallery (filter by substring)
hermes pets list
hermes pets list cat

# Install a pet and make it active in one step
hermes pets install boba --select

# Preview / animate it in your terminal (Ctrl+C to stop)
hermes pets show

# Check your setup
hermes pets doctor
```

## `hermes pets` 命令

| 目标 | 命令 |
| --- | --- |
| 浏览图库 | `hermes pets list [query] [--limit N]` |
| 列出已安装的宠物 | `hermes pets list --installed` |
| 安装宠物 | `hermes pets install <slug> [--select] [--force]` |
| 设置当前宠物 | `hermes pets select [slug]`（省略 slug 以使用选择器） |
| 调整所有界面中的宠物大小 | `hermes pets scale <factor>`（例如 `0.5`，限制在 0.1–3.0） |
| 预览/播放动画 | `hermes pets show [slug] [--state <s>] [--cycle] [--once] [--mode <m>] [--scale <f>]` |
| 禁用宠物 | `hermes pets off` |
| 移除已安装的宠物 | `hermes pets remove <slug>` |
| 诊断设置 | `hermes pets doctor` |

`hermes pets show` 标志：

- `--state`——播放单个状态（`idle`、`wave`、`run`、`failed`、`review`、`jump`）。
- `--cycle`——依次播放每个状态。
- `--once`——只播放一次，而不是循环播放。
- `--mode`——覆盖渲染协议（`kitty`、`iterm`、`sixel`、`unicode`、`auto`）。
- `--scale`——覆盖屏幕显示缩放比例（`0` = 使用配置）。

## `/pet` 斜杠命令

在 CLI 和 TUI 中，你无需离开会话即可管理宠物：

- `/pet`——开关宠物（如果没有当前宠物，则领养第一个已安装的宠物）。
- `/pet list`——浏览图库。
- `/pet scale <factor>`——调整所有界面中的宠物大小（例如 `/pet scale 0.5`）。
- `/pet <slug>`——领养指定宠物。
- `/pet off`——禁用宠物。

在 TUI 中，`/pet list` 会打开交互式选择器浮层；在桌面应用中，它会打开 Cmd+K 宠物面板。

## 生成宠物（`/hatch`）

除了安装图库中的现成宠物外，Hermes 还可以根据文本描述**生成全新的宠物**——使用它自己的 AI 精灵生成流水线。

- CLI/TUI：`/hatch <description>`（别名 `/generate-pet`），或使用 `hermes pets` → 生成流程。
- 桌面应用：宝可梦图鉴风格的**生成**界面——包含动画蛋、孵化特效和草稿选择器。

生成方式（一个分为两步且成本有上限的流程）：

1. **基础草稿**——生成少量低成本、仅使用提示词的“这个宠物应该是什么样子”变体。你可以选择一个，也可以混搭/重试来获得全新的一轮。
2. **孵化**——使用选定的基础图像作为参考图像，为 Hermes 的每种状态（空闲、思考、使用工具等）分别生成一行基于参考图像的动画；随后以确定性方式将它们切分为帧，并打包成标准的 petdex/Codex 图集（由 192×208 单元格组成的 8×9 网格）。生成结果是一个归你保留的有效精灵表——你还可以执行 `petdex submit`。

### 图像后端

生成使用当前启用的[图像生成提供商](/user-guide/features/image-generation)，但它需要**参考图像约束**，以便让每一行动画都与基础图像保持为同一个角色。支持参考图像的后端包括：**Nous Portal**、**OpenRouter**、**OpenAI**（`gpt-image-2`）和 **Krea**。OpenRouter/Nous 默认运行质量优先的模型链。

- 解析顺序优先选择 Nous Portal → OpenAI → OpenRouter。
- 如果没有配置支持参考图像的后端，生成流程会显示一条可操作的错误消息，引导你前往 `hermes tools` → Image Generation。（安装/领养图库中的现有宠物不需要图像后端。）
- 使用 `HERMES_PET_IMAGE_PROVIDER` 环境变量覆盖后端（例如 `HERMES_PET_IMAGE_PROVIDER=openrouter`）。

## 桌面应用

在桌面应用中，你可以通过两种方式管理宠物：

- **Cmd+K → “宠物……”**——无需离开键盘即可浏览、搜索、领养和开关宠物（与主题选择器相对应）。
- **设置 → 外观**——同一个图库，外加一个**大小滑块**，拖动时可实时调整浮动吉祥物的大小。

这两种方式都会直接领养/开关/调整浮动吉祥物的大小——大小变更会立即生效；领养新宠物后，它会在片刻内亮相。

### 弹出式浮层

按住 **Shift 并点击**浮动宠物，可将其弹出到一个独立、透明且始终置顶的桌面窗口中。在那里，即使 Hermes 已最小化（Codex 风格），它仍会保持可见，因此你看一眼就能知道智能体正在做什么。

弹出后可使用的手势：

| 手势 | 操作 |
| --- | --- |
| **拖动** | 将宠物移动到屏幕上的任意位置，甚至可以移到应用外部。它的位置和弹入/弹出状态会在重启后保留。 |
| **单击** | 打开一个迷你输入框，向最近的会话发送提示，而不会将应用调到前台。 |
| **双击** | 切换应用窗口：如果窗口位于前台，则将其最小化；如果窗口已隐藏，则将其恢复。 |
| **按住 Shift 并点击** | 将宠物弹回窗口中。 |
| **邮件图标** | 仅在你离开时有轮次完成后出现；点击可将应用调到最近的对话线程（并将其标记为已读）。 |

只有弹出的宠物会显示**对话气泡**（`working…`、`thinking…`、`your turn`……）——在窗口内，应用本身就是交互界面，因此宠物会保持安静。

该浮层只是应用内宠物的纯粹映射——它没有独立的网关连接，也永远不会出现在程序坞或应用切换器中。

## 配置

所有设置都位于 `display.pet` 下，并写在 `config.yaml` 中：

```yaml
display:
  pet:
    enabled: false        # master on/off (true once you select a pet)
    slug: ""              # active pet; empty = first installed
    render_mode: auto      # auto | kitty | iterm | sixel | unicode | off
    scale: 0.33           # master size knob (relative to native 192x208 frames)
    unicode_cols: 0       # hard override for terminal width (0 = derive from scale)
```

- **`scale`** 是唯一的总体大小调节项。一个数值即可缩小每个界面：桌面画布按该数值缩放像素，而 CLI/TUI 根据它推导终端列宽。半块字符回退渲染会设置可辨识度下限——它无法像真正的像素级 kitty/GUI 渲染那样缩小，否则会变得模糊不清；因此，相同的 `scale` 在 kitty 下看起来清晰锐利，但在半块字符渲染中会受到下限限制。
- **`render_mode: auto`** 会检测 kitty/iTerm2/sixel，并回退到 Unicode 半块字符。明确设置该值可强制使用某种协议，也可以设置为 `off` 来禁用终端渲染，同时保留桌面上的宠物。
- **`unicode_cols`** 可独立于 `scale` 固定终端列宽；将其保留为 `0`，即可根据 `scale` 推导宽度。

## 故障排除

运行 `hermes pets doctor`——它会报告：

- 宠物目录以及已安装的宠物，
- `display.pet.enabled`、`display.pet.slug` 和解析出的当前宠物，
- 配置的 `render_mode`、检测到的终端图形协议，以及 TTY 的实际模式，
- Pillow（用于精灵解码）是否可导入。

安装、选择并启用宠物且 Pillow 可用后，它会输出 `✓ ready`。

常见注意事项：

- 只有宠物**已安装且已选择**（`enabled: true`）后，它才会显示。
- 在管道/重定向中（无 TTY），终端渲染会按设计禁用。
- petdex npm CLI 会安装到 `~/.codex/pets`；Hermes 则使用自己按配置文件隔离的 `<HERMES_HOME>/pets/`——请通过 `hermes pets` 安装。

## 另请参阅

- [`hermes-agent` 技能](../skills/bundled/autonomous-ai-agents/autonomous-ai-agents-hermes-agent.md)可根据你的请求为你安装和切换宠物（请参阅其中的 `references/petdex.md`）。