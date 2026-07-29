---
sidebar_position: 4
title: "Slack"
description: "使用 Socket Mode 将 Hermes Agent 设置为 Slack 机器人"
---

# Slack 设置

使用 Socket Mode 将 Hermes Agent 作为机器人连接到 Slack。Socket Mode 使用 WebSocket 而非公开 HTTP 端点，因此你的 Hermes 实例无需公开访问——它可以在防火墙后、笔记本电脑上或私有服务器上正常运行。

:::warning 经典 Slack 应用已弃用
使用 RTM API 的经典 Slack 应用已于 **2025 年 3 月完全弃用**。Hermes 使用带有 Socket Mode 的现代 Bolt SDK。如果你有旧的经典应用，必须按照以下步骤创建新应用。
:::

## 概述

| 组件 | 值 |
|-----------|-------|
| **库** | Python 的 `slack-bolt` / `slack_sdk`（Socket Mode） |
| **连接方式** | WebSocket——无需公开 URL |
| **所需认证令牌** | Bot Token（`xoxb-`）+ App-Level Token（`xapp-`） |
| **用户标识** | Slack Member ID（例如 `U01ABC2DEF3`） |

---

## 第一步：创建 Slack 应用

最快的方式是粘贴 Hermes 为你生成的 manifest（清单文件）。它会一次性声明所有内置斜杠命令（`/btw`、`/stop`、`/model`……）、所有必需的 OAuth 权限范围、所有事件订阅，并启用 Socket Mode。

### 方式 A：使用 Hermes 生成的 manifest（推荐）

1. 生成 manifest。新 Slack 应用必须使用 Agent 视图：
   ```bash
   hermes slack manifest --agent-view --write
   ```
   此命令会将 `~/.hermes/slack-manifest.json` 写入磁盘并打印粘贴说明。
   仍在使用 Slack 旧版 Assistant 视图的现有应用，在准备迁移之前可以省略 `--agent-view`。

   若要使用现有 UTF-8 文本或 Markdown 文件填充 Slack 的应用长描述，请添加 `--long-description-file`：

   ```bash
   hermes slack manifest --agent-view \
     --long-description-file AGENTS.md --write
   ```

   文件内容会在 Slack 的 175–4,000 个字符范围内原样保留。若要使用内联文本，请改用
   `--long-description "..."`；内联和文件选项互斥，且均不能与 `--slashes-only` 组合使用。
2. 前往 [https://api.slack.com/apps](https://api.slack.com/apps) →
   **Create New App** → **From an app manifest**
3. 选择你的工作区，粘贴 JSON 内容，检查后点击 **Next** → **Create**
4. 直接跳至**第六步：将应用安装到工作区**。manifest 已为你处理好权限范围、事件和斜杠命令。

### 方式 B：从头手动创建

1. 前往 [https://api.slack.com/apps](https://api.slack.com/apps)
2. 点击 **Create New App**
3. 选择 **From scratch**
4. 输入应用名称（例如 "Hermes Agent"）并选择你的工作区
5. 点击 **Create App**

你将进入应用的 **Basic Information** 页面。继续执行下方第 2–6 步。

---

## 第二步：配置 Bot Token 权限范围

在侧边栏导航至 **Features → OAuth & Permissions**。向下滚动至 **Scopes → Bot Token Scopes**，添加以下权限：

| 权限范围 | 用途 |
|-------|---------|
| `chat:write` | 以机器人身份发送消息 |
| `app_mentions:read` | 检测在频道中被 @ 提及的情况 |
| `channels:history` | 读取机器人所在公开频道的消息 |
| `channels:read` | 列出并获取公开频道信息 |
| `groups:history` | 读取机器人被邀请加入的私有频道消息 |
| `im:history` | 读取私信历史记录 |
| `im:read` | 查看基本私信信息 |
| `im:write` | 打开并管理私信 |
| `mpim:history` | 读取群组私信（多人私信）历史记录 |
| `mpim:read` | 查看基本群组私信信息 |
| `users:read` | 查询用户信息 |
| `files:read` | 读取并下载附件文件，包括语音备忘录/音频 |
| `files:write` | 上传文件（图片、音频、文档） |

:::caution 缺少权限范围 = 功能缺失
没有 `channels:history` 和 `groups:history`，机器人**将无法接收频道消息**——它只能在私信中工作。没有 `files:read`，Hermes 可以聊天，但**无法可靠读取用户上传的附件**。这是最常被遗漏的权限范围。
:::

**可选权限范围：**

| 权限范围 | 用途 |
|-------|---------|
| `groups:read` | 列出并获取私有频道信息 |
| `assistant:write` | 在机器人处理消息时，于机器人名称旁渲染工作状态行（“正在思考…”）。没有此权限范围，`assistant.threads.setStatus` 调用会静默失败，Slack 会显示自己的轮换通用占位文本（“正在寻找答案…”、“正在审阅结果…”等）——Hermes 无法控制这些文本。`typing_status_text` 要产生任何可见效果必须具备此权限范围。 |

---

## 第三步：启用 Socket Mode

Socket Mode 让机器人通过 WebSocket 连接，无需公开 URL。

1. 在侧边栏前往 **Settings → Socket Mode**
2. 将 **Enable Socket Mode** 切换为开启
3. 系统会提示你创建一个 **App-Level Token**：
   - 命名为类似 `hermes-socket` 的名称（名称不重要）
   - 添加 **`connections:write`** 权限范围
   - 点击 **Generate**
4. **复制该令牌**——它以 `xapp-` 开头。这就是你的 `SLACK_APP_TOKEN`

:::tip
你随时可以在 **Settings → Basic Information → App-Level Tokens** 下找到或重新生成 App-Level Token。
:::

---

## 第四步：订阅事件

此步骤至关重要——它控制机器人能看到哪些消息。

1. 在侧边栏前往 **Features → Event Subscriptions**
2. 将 **Enable Events** 切换为开启
3. 展开 **Subscribe to bot events** 并添加：

| 事件 | 是否必需 | 用途 |
|-------|-----------|---------|
| `message.im` | **必需** | 机器人接收私信 |
| `message.mpim` | **必需** | 机器人接收其加入的**群组私信**（多人私信）消息 |
| `message.channels` | **必需** | 机器人接收其加入的**公开**频道消息 |
| `message.groups` | **推荐** | 机器人接收被邀请加入的**私有**频道消息 |
| `app_mention` | **必需** | 防止机器人被 @ 提及时出现 Bolt SDK 错误 |

4. 点击页面底部的 **Save Changes**

:::danger 缺少事件订阅是第一大设置问题
如果机器人在私信中正常工作但**在频道中不响应**，你几乎肯定忘记添加 `message.channels`（公开频道）和/或 `message.groups`（私有频道）。没有这些事件，Slack 根本不会将频道消息传递给机器人。
:::

---

## 第五步：启用 Messages Tab

此步骤启用对机器人的私信功能。没有它，用户在尝试私信机器人时会看到**"向此应用发送消息已被关闭"**的提示。

1. 在侧边栏前往 **Features → App Home**
2. 向下滚动至 **Show Tabs**
3. 将 **Messages Tab** 切换为开启
4. 勾选 **"Allow users to send Slash commands and messages from the messages tab"**

:::danger 没有此步骤，私信将被完全屏蔽
即使拥有所有正确的权限范围和事件订阅，除非启用 Messages Tab，否则 Slack 不允许用户向机器人发送私信。这是 Slack 平台的要求，而非 Hermes 的配置问题。
:::

---

## 第六步：将应用安装到工作区

1. 在侧边栏前往 **Settings → Install App**
2. 点击 **Install to Workspace**
3. 检查权限并点击 **Allow**
4. 授权后，你将看到一个以 `xoxb-` 开头的 **Bot User OAuth Token**
5. **复制此令牌**——这就是你的 `SLACK_BOT_TOKEN`

:::tip
如果你之后更改了权限范围或事件订阅，**必须重新安装应用**才能使更改生效。Install App 页面会显示提示横幅。
:::

---

## 第七步：查找用于白名单的用户 ID

Hermes 使用 Slack **Member ID**（而非用户名或显示名称）作为白名单。

查找 Member ID 的方法：

1. 在 Slack 中点击用户的名称或头像
2. 点击 **View full profile**
3. 点击 **⋮**（更多）按钮
4. 选择 **Copy member ID**

Member ID 格式类似 `U01ABC2DEF3`。你至少需要自己的 Member ID。

---

## 第八步：配置 Hermes

将以下内容添加到你的 `~/.hermes/.env` 文件：

```bash
# 必需
SLACK_BOT_TOKEN=«redacted:xox…»
SLACK_APP_TOKEN=xapp-your-app-token-here
SLACK_ALLOWED_USERS=U01ABC2DEF3              # 逗号分隔的 Member ID

# 可选
SLACK_HOME_CHANNEL=C01234567890              # 定时/计划消息的默认频道
SLACK_HOME_CHANNEL_NAME=general              # 主频道的可读名称（可选）
```

或运行交互式设置：

```bash
hermes gateway setup    # 提示时选择 Slack
```

然后启动 gateway：

```bash
hermes gateway              # 前台运行
hermes gateway install      # 安装为用户服务
sudo hermes gateway install --system   # 仅 Linux：开机启动系统服务
```

:::tip Codex 推理精度安全
对于使用 Codex 的 Slack 对等 Agent 频道，建议使用 `agent.reasoning_effort: high` 或更低。`xhigh` 可能将整个轮次消耗在隐藏推理中，从不生成可见的助手文本；Hermes 现在会从话题中抑制这些不完整轮次的警告，并将诊断信息保留在 gateway 日志中。
:::

---

## 第九步：将机器人邀请到频道

启动 gateway 后，你需要**邀请机器人**加入希望它响应的频道：

```
/invite @Hermes Agent
```

机器人**不会**自动加入频道。你必须逐个频道邀请它。

---

## 斜杠命令

每个 Hermes 命令（`/btw`、`/stop`、`/new`、`/model`、`/help`……）都是原生 Slack 斜杠命令——与它们在 Telegram 和 Discord 上的工作方式完全相同。在 Slack 中输入 `/`，自动补全选择器会列出每个 Hermes 命令及其描述。

底层实现：Hermes 附带一个生成的 Slack 应用 manifest（见第一步，方式 A），它将 [`COMMAND_REGISTRY`](https://github.com/NousResearch/hermes-agent/blob/main/hermes_cli/commands.py) 中的每个命令声明为斜杠命令。在 Socket Mode 下，无论 manifest 的 `url` 字段如何，Slack 都会通过 WebSocket 路由命令事件。

### Agent 消息体验

新的 Slack 应用使用 Slack 的 **Agent** 消息体验。现有的 Hermes Assistant 应用可以通过使用 `--agent-view` 重新生成 manifest 进行迁移：

```bash
hermes slack manifest --agent-view --write
```

在 **Features → App Manifest** 中更新 manifest，如果 Slack 提示则重新安装应用。Agent 视图无法恢复为 Assistant 视图，用户在切换后可能需要强制刷新 Slack。生成的 Agent manifest 订阅了 `message.im`、`app_home_opened` 和 `app_context_changed`，因此 Hermes 可以识别 Messages 标签页中的私信，并在一个轮次中接收用户的活跃 Slack 上下文。Hermes 仅将该上下文作为标签提供；它不会读取被查看频道的历史记录。

### 更新后刷新斜杠命令

当 Hermes 添加新命令时（例如执行 `hermes update` 后），重新生成 manifest 并更新你的 Slack 应用：

```bash
hermes slack manifest --write
```

然后在 Slack 中：
1. 打开 [https://api.slack.com/apps](https://api.slack.com/apps) →
   你的 Hermes 应用
2. **Features → App Manifest → Edit**
3. 粘贴 `~/.hermes/slack-manifest.json` 的新内容
4. **保存**。如果权限范围或斜杠命令有变化，Slack 会提示重新安装应用。

### 旧版 `/hermes <子命令>` 仍然有效

为了向后兼容旧版 manifest，你仍然可以输入 `/hermes btw run the tests`——Hermes 会以与 `/btw run the tests` 相同的方式路由它。自由形式的问题也有效：`/hermes what's the weather?` 会被当作普通消息处理。

### 在话题（thread）中使用命令（`!cmd` 前缀）

Slack 本身会阻止在话题回复中使用原生斜杠命令——在话题中尝试 `/queue`，Slack 会回复 *"/queue is not supported in threads. Sorry!"*。没有任何应用端设置可以重新启用它们；Slack 从不将它们传递给 Hermes。

作为解决方案，Hermes 识别前导 `!` 作为在话题（以及任何其他地方）中有效的替代命令前缀。在话题回复中输入 `!queue`、`!stop`、`!model gpt-5.4` 等普通回复——Hermes 会以与斜杠形式完全相同的方式处理，并在同一话题中回复。

只有第一个 token（词元）会与已知命令列表进行匹配，因此像 `!nice work` 这样的随意消息会原样传递给 agent。
感叹号形式也可置于提及之后（`@Hermes !stop`），并支持前导空白——两种形式都会在话题中作为命令分派。

审批提示（危险命令 `/execute_code` 审批）通常以交互式按钮形式呈现。当按钮无法送达且 Hermes 回退到文本提示时，提示会指示你用 `!approve` / `!deny` 回复——该形式在话题内同样有效。

### 斜杠命令回复是仅自己可见的

对原生斜杠命令（例如 `/status`、`/help`）的回复会**仅自己可见**——“Only visible to you”——因此命令输出不会刷屏频道。“Running /cmd…” 占位符会被实际回复替换；较长回复会分块为后续的仅自己可见消息。Slack 将该回复流程限制为 5 条消息，因此超长输出会以明确的截断提示结束，而不会被静默丢弃。如果主要的仅自己可见路径失败，Hermes 会通过第二个仅自己可见的 API 路径重试——斜杠命令回复绝不会作为回退公开发布到频道。（作为普通消息输入的命令——话题中的 `!cmd`、`@Hermes /cmd`——仍会以正常的可见消息回复。）

### 澄清提示（单击按钮）

当 agent 需要向你提出多选问题（`clarify` 工具）时，Slack 会将其渲染为 **Block Kit 按钮**——每个选项一个按钮，另有“✏️ Other…”按钮可切换至自由文本模式（你的下一条输入消息即成为答案）。点击后，消息会原地更新，显示谁回答了以及选择了什么；对同一提示的后续点击会被忽略。按钮点击遵循与消息相同的用户授权规则；过期提示（gateway 重启、超时）会要求你重新提问，而不会静默吞掉点击。开放式澄清问题会渲染为普通问题，并接受你的下一条输入回复。无需配置——无论 `rich_blocks` 设置为何，此功能均可使用。

### 高级：仅输出斜杠命令数组

如果你手动维护 Slack manifest 并只需要斜杠命令列表：

```bash
hermes slack manifest --slashes-only > /tmp/slashes.json
```

将该数组粘贴到现有 manifest 的 `features.slash_commands` 键中。

---

## 机器人的响应方式

了解 Hermes 在不同场景下的行为：

| 场景 | 行为 |
|---------|----------|
| **私信** | 机器人响应每条消息——无需 @ 提及 |
| **频道** | 机器人**仅在被 @ 提及时响应**（例如 `@Hermes Agent what time is it?`）。在频道中，Hermes 在该消息附带的话题中回复。 |
| **话题** | 如果你在现有话题中 @ 提及 Hermes，它会在同一话题中回复。一旦机器人在话题中有活跃会话，**该话题中的后续回复无需 @ 提及**——机器人会自然跟进对话。 |

:::tip
在频道中，始终 @ 提及机器人来开始对话。一旦机器人在话题中活跃，你可以在该话题中回复而无需提及它。话题之外，没有 @ 提及的消息会被忽略，以防止在繁忙频道中产生噪音。
:::

---

## 配置选项

除了第八步中的必需环境变量外，你还可以通过 `~/.hermes/config.yaml` 自定义 Slack 机器人行为。

### 话题与回复行为

```yaml
platforms:
  slack:
    # 控制多部分响应的话题方式
    # "off"   — 永不将回复串入原始消息的话题
    # "first" — 第一个分块串入用户消息（默认）
    # "all"   — 所有分块串入用户消息
    reply_to_mode: "first"

    extra:
      # 是否在话题中回复（默认：true）。
      # 为 false 时，频道消息直接在频道中回复，而非话题。
      # 已在话题中的消息仍在话题中回复。
      reply_in_thread: true

      # 同时将话题回复发布到主频道
      # （Slack 的"同时发送到频道"功能）。
      # 仅广播第一条回复的第一个分块。
      reply_broadcast: false

      # 将 Agent 消息渲染为 Slack Block Kit 区块（默认：false）。
      # 为 true 时，最终的 Agent 消息会以结构化区块发送——包括
      # 章节标题、分隔线、真正的嵌套列表（通过 rich_text）以及
      # 原生 Block Kit 表格——而非扁平的 mrkdwn 文本。同时始终附带
      # 纯文本回退内容，用于通知和无障碍访问。超出 Slack 限制
      # （100 行 / 20 列 / 1 万字符）的表格会优雅地回退为对齐的等宽文本。
      rich_blocks: false

      # 在最终的 Block Kit 回复中附加 Slack 原生反馈控件。
      # 需要 rich_blocks: true。默认：false。
      feedback_buttons: false

      # 固定在 Agent 视图 Messages 标签页顶部的建议提示。
      # 可以是 {title, message} 行的列表，或包含标题的对象：
      # {title: "Start here", prompts: [{title: "Plan", message: "..."}]}
      suggested_prompts: []

      # 使用用户首条消息为 Agent/Assistant 私信话题命名。
      # 默认：true。设为 false 以保留 Slack 的默认话题标题。
      assistant_thread_titles: true

      # 接受其他 Slack 机器人的消息（默认："none"）。
      # "none" 忽略机器人，"mentions" 仅在该机器人消息本身
      # @ 提及 Hermes 时接受它，"all" 接受所有其他机器人。
      # Hermes 始终忽略自己的机器人用户，以防止自回显。
      allow_bots: "none"

      # 可继续 cron 任务的投递方式（默认："thread"）。
      # "in_channel" 将可继续的 cron 任务直接平铺投递到频道中
      # （不新建话题）；需与 reply_in_thread: false（及
      # require_mention: false）搭配，纯文本回复即可继续任务。
      # 详见 cron 指南 →"平铺频道内继续"。
      cron_continuable_surface: thread
```

| 键 | 默认值 | 描述 |
|-----|---------|-------------|
| `platforms.slack.reply_to_mode` | `"first"` | 多部分消息的话题模式：`"off"`、`"first"` 或 `"all"` |
| `platforms.slack.extra.reply_in_thread` | `true` | 为 `false` 时，频道消息直接回复而非话题。已在话题中的消息仍在话题中回复。 |
| `platforms.slack.extra.reply_broadcast` | `false` | 为 `true` 时，话题回复也会发布到主频道。仅广播第一个分块。 |
| `platforms.slack.extra.rich_blocks` | `false` | 为 `true` 时，Agent 消息会渲染为 [Block Kit](https://docs.slack.dev/block-kit/) 区块（标题、分隔线、真正的嵌套列表以及原生表格）。始终附带纯文本回退。超出 Slack 限制的表格会回退为对齐的等宽文本。无需重新安装应用——这仅是发送端的改动。 |
| `platforms.slack.extra.feedback_buttons` | `false` | 与 `rich_blocks` 同时启用时，在最终回复中附加 Slack 原生反馈控件。 |
| `platforms.slack.extra.suggested_prompts` | `[]` | 最多四个用于 Agent/Assistant 私信入口的 `{title, message}` 提示；接受列表或 `{title, prompts}` 格式。 |
| `platforms.slack.extra.assistant_thread_titles` | `true` | 为 `true` 时，使用用户首条消息为 Agent/Assistant 私信话题命名。 |
| `platforms.slack.extra.allow_bots` | `"none"` | 控制来自其他 Slack 机器人的消息：`"none"` 忽略它们，`"mentions"` 仅在**该消息本身** @ 提及 Hermes 时接受机器人消息，`"all"` 接受所有消息。对于机器人间协作，使用 `"mentions"` 最安全。请参阅[接受其他机器人的消息](#接受其他机器人的消息allow_bots)。 |
| `platforms.slack.extra.cron_continuable_surface` | `"thread"` | [可继续 cron 任务](../features/cron.md#flat-in-channel-continuation-slack)的投递方式。`"thread"` 为每次投递新建专用话题（默认）；`"in_channel"` 直接平铺投递到频道时间线。使用 `in_channel` 时需搭配 `reply_in_thread: false`（及 `require_mention: false`），纯文本回复即可继续任务。 |

对应的环境变量为 `SLACK_ALLOW_BOTS=none|mentions|all`。两者均设置时，`platforms.slack.extra.allow_bots` 优先。若对等机器人无需显式提及即可相互回复，应避免使用 `all`，因为它们自己的回复策略仍可能形成循环。

### 工作状态行

agent 处理消息时，Slack 会在话题中机器人名称旁显示状态行。默认情况下 Hermes 将其设为 `is thinking...`；可通过 `typing_status_text` 自定义，例如名为 Ada 的小猫助手：

```yaml
platforms:
  slack:
    # 自定义工作状态行（默认："is thinking..."）。
    typing_status_text: "is pouncing… 🐾"
```

| 键 | 默认值 | 描述 |
|-----|---------|-------------|
| `platforms.slack.typing_status_text` | `"is thinking..."` | agent 处理消息时显示的工作状态行文本。需要 `assistant:write` 权限范围——没有它，状态调用会静默失败，无论此项如何设置，Slack 都会渲染自己的通用占位文本。将 `typing_indicator: false` 设为该值可完全禁用状态行。 |

:::note 状态显示的位置
自定义状态显示在**回复编辑器下方的页脚**（“*BotName* is thinking…”），而非消息列表内联位置。AI 应用工作期间，Slack 在消息区域显示的内联 “Generating response…” / “Finding answers…” 行是 **Slack 自身轮换的指示器**——`assistant.threads.setStatus` 不控制它们，两者可同时出现。
:::

同一个键也会自定义 Google Chat 可见的工作状态标记消息（`platforms.google_chat.typing_status_text`，默认 `"Hermes is thinking…"`）——请注意，在 Google Chat 中它是一条真实发布的消息，随后会被修补为回复，而非临时状态。

### 实时状态（按工具）

默认情况下，状态行会在 agent 工作时**实时更新**：它不再固定为 `is thinking...`，而是显示 agent 当前正在做什么——`is running pytest tests/…`、`is reading docs/api.md…`、`is searching the web for slack api limits…`。在工具调用之间，它会恢复为静态文本。这沿用既有的状态刷新频率，因此不额外发起 Slack API 调用；即使 `tool_progress: off`（Slack 默认）也可工作——不同于进度气泡，状态行是临时的，不会在频道留下内容。

通过 `display.live_status`（全局或按平台）控制：

```yaml
display:
  platforms:
    slack:
      # full = 动词 + 参数（"is running pytest…"）[默认]
      # verb = 仅动词（"is running…"）——隐藏命令/路径，
      #        适用于共享或面向客户的频道
      # off  = 静态文本（typing_status_text 或 "is thinking..."）
      live_status: full
```

| 键 | 默认值 | 描述 |
|-----|---------|-------------|
| `display.live_status` | `"full"` | 按工具显示的实时状态行。`full` 显示动词和参数预览；`verb` 仅显示动词（避免在共享频道中泄露文件路径和命令）；`off` 恢复静态文本。与静态状态行相同，需要 `assistant:write` 权限范围。 |

### 会话隔离

```yaml
# 全局设置——适用于 Slack 和所有其他平台
group_sessions_per_user: true
```

为 `true`（默认值）时，共享频道中的每个用户都有自己独立的对话会话。在 `#general` 中与 Hermes 对话的两个人将有各自独立的历史记录和上下文。

设为 `false` 可启用协作模式，整个频道共享一个对话会话。请注意，这意味着用户共享上下文增长和 token 成本，且一个用户的 `/reset` 会清除所有人的会话。

### 提及与触发行为

```yaml
slack:
  # 在频道中要求 @mention（这是默认行为；
  # Slack 适配器无论如何都会在频道中强制执行 @mention 门控，
  # 但你可以明确设置此项以与其他平台保持一致）
  require_mention: true

  # 防止话题自动参与：仅回复包含明确 @mention 的频道消息。
  # 关闭此项（默认），Slack 可以"自动参与"——记住话题中的过去提及，
  # 跟进机器人消息的回复，并在无需新提及的情况下恢复活跃会话。
  # 开启 strict_mention 后，每条新频道消息都必须 @mention 机器人，
  # Hermes 才会响应。
  strict_mention: false

  # 忽略发给其他用户的消息：当频道或话题消息以 @ 提及
  # 机器人以外的某人开头时（例如 "@rasha can you take this?"），
  # 除非也提及机器人，否则保持静默。只有*前导*提及才算“发给”某人——
  # 句中提及（"loop in @rasha"）仍会传给机器人。此项覆盖
  # free_response_channels 和话题自动参与。选择启用；默认关闭。环境变量：SLACK_IGNORE_OTHER_USER_MENTIONS。
  ignore_other_user_mentions: false

  # 对话题回复要求显式 @mention，同时仍由 require_mention /
  # free_response_channels 控制顶级频道消息。它比 strict_mention 更窄：
  # 当自由回复机器人不应参与繁忙话题中的每条跟进时使用。
  # 选择启用；默认关闭。环境变量：SLACK_THREAD_REQUIRE_MENTION。
  thread_require_mention: false

  # 按频道强制提及覆盖——与 free_response_channels 相反。列出的频道
  # 始终要求显式 @mention，即使全局 require_mention 为 false 或频道可自由回复。
  # 正在进行的对话仍会自动跟进（被提及的话题、活跃会话、机器人发起的话题）。
  # 逗号分隔的 ID 或列表。环境变量：SLACK_REQUIRE_MENTION_CHANNELS。
  require_mention_channels: ""

  # 触发机器人的自定义提及模式
  # （除默认 @mention 检测外）
  mention_patterns:
    - "hey hermes"
    - "hermes,"

  # 每条发出消息前添加的文本
  reply_prefix: ""
```

:::tip 何时使用 `strict_mention`
在繁忙工作区中，如果 Slack 默认的"机器人记住此话题"行为让用户感到意外，请将此项设为 `true`——例如，在一个长技术支持话题中，机器人在开始时提供了帮助，而你希望它保持沉默，除非被明确 @ 提及。私信和活跃的交互会话不受影响。
:::

:::tip 何时使用 `ignore_other_user_mentions`
当机器人通过话题自动参与或 `free_response_channels` 跟进繁忙话题、却插入人类彼此发言的消息时，将此项设为 `true`。它比 `strict_mention` 更精细：已参与话题中的普通跟进仍会得到回答；只有以 @ 提及其他人开头的消息会被跳过。**1:1 私信不受影响**；群组私信（MPIM）和频道都会应用它，符合下方的共享界面策略。广播 token（`@here`、`@channel`）和频道引用是面向整个房间，而非个人，因此绝不会被跳过。
:::

:::info
Slack 支持两种模式：默认情况下需要 `@mention` 才能开始对话，但你可以通过 `SLACK_FREE_RESPONSE_CHANNELS`（逗号分隔的频道 ID）或 `config.yaml` 中的 `slack.free_response_channels` 为特定频道取消此限制。一旦机器人在话题中有活跃会话，后续话题回复无需提及。在**1:1 私信**中，机器人始终响应，无需提及。
:::

:::caution 群组私信（MPIM）是共享界面，而非 1:1 私信
**1:1 私信**是与一个人的私人对话，因此免于提及要求。**群组私信（MPIM / 多人私信）** 是一个 *共享界面*——多人可以看到并触发机器人——因此它遵循与频道相同的操作控制：`require_mention`、`strict_mention`、`free_response_channels` 和 `allowed_channels` 均适用，且机器人仅在确实被 `@mention` 时才添加 `:eyes:`/`:white_check_mark:` 反应。要让机器人在特定群组私信中自由响应，请将其频道 ID（以 `G` 开头）添加到 `free_response_channels`。
:::

#### 应该选择哪个提及选项？

这些门控选项可以组合——每项回答不同的问题：

| 选项 | 所回答的问题 | 默认值 | 范围 |
|--------|--------------------|---------|-------|
| `require_mention` | **顶级频道消息**是否需要 @mention？ | `true` | 所有频道 |
| `free_response_channels` | 哪些频道免于 `require_mention`？ | 无 | 列出的频道 |
| `require_mention_channels` | 即使 `require_mention` 为 `false` 或频道可自由回复，哪些频道也始终需要 @mention？优先于两者。 | 无 | 列出的频道 |
| `thread_require_mention` | 即使顶级消息不需要，**话题回复**是否仍需要 @mention？不会记住被提及的话题。 | `false` | 仅话题 |
| `strict_mention` | 是否**每条**频道消息（顶级和话题）都需要新的 @mention？禁用所有自动跟进：被提及话题记忆、机器人回复跟进、活跃会话恢复。 | `false` | 所有频道和话题 |
| `ignore_other_user_mentions` | 是否应跳过**以 @ 提及其他人开头**的消息（`@rasha can you take this?`）？覆盖自由回复和话题自动跟进；句中引用仍会传给机器人。 | `false` | 频道和群组私信 |

经验法则：`strict_mention` 是最广泛的工具；`thread_require_mention` 可让繁忙话题安静下来而不影响顶级门控；`require_mention_channels` 可在自由回复机器人上重新收紧单个频道；`ignore_other_user_mentions` 只跳过明确发给其他人的消息。1:1 私信始终响应，且不受所有这些选项影响。

### 接受其他机器人的消息（`allow_bots`）

默认情况下，Hermes 会忽略其他 Slack 机器人或应用发布的所有消息（包括 Workflow Builder 发布的消息）。对于多 agent 工作区——多个 Hermes 实例或在同一频道协作的对等机器人——请通过 `allow_bots` 选择启用：

```yaml
platforms:
  slack:
    extra:
      # "none"（默认）——忽略所有由机器人/应用创作的消息
      # "mentions"       ——仅当该消息本身 @ 提及本机器人时
      #                    接受机器人消息
      # "all"            ——接受所有其他机器人（本机器人除外）
      allow_bots: mentions
```

环境变量等价项：`SLACK_ALLOW_BOTS=none|mentions|all`（两者均设置时配置键优先）。未知值会被视为 `none`。

`mentions` 模式的门控方式：

- 仅当对等机器人消息**本身包含对本机器人的当前 `@mention`**时才会接受它——可以在其文本或 Block Kit 区块中。话题历史不计算在内：先前在话题中提及机器人、回复机器人的消息以及活跃的话题会话，均**不会**允许后续未提及的对等机器人消息。这是刻意设计——它能切断 agent 间的确认/状态循环。
- 人类消息不受影响；正常提及门控仍适用。
- Hermes 在所有模式中始终忽略自己的消息，以防止自回显循环。

`mentions` 是机器人间协作的推荐模式：每个 agent 每轮都必须显式召唤另一个。除非每个对等机器人的回复策略都能防止循环，否则避免使用 `all`——两个回答所有消息的机器人会无限互相回答。检测涵盖带标签的机器人消息（`bot_id`、`subtype: bot_message`）、由应用发起的事件和未标记的机器人*用户*（通过 `users.info` 探测），因此会在各工作区中一致过滤对等 Hermes agent。

对于严格的多机器人部署，请与 `require_mention: true` 和 `strict_mention: true` 搭配——请参阅下方的冒烟检查配置。

### 反应触发器（`reaction_triggers`）

默认情况下，表情反应会被确认并丢弃——机器人消息上的 👍 不会执行任何操作。设置 `slack.reaction_triggers` 可将反应路由进 agent 循环（需要 `reactions:read` 权限范围以及 Slack 应用 manifest 中的 `reaction_added`/`reaction_removed` 机器人事件订阅——请重新生成 `hermes slack manifest`）：

```yaml
slack:
  # 选择启用。false/未设置（默认）= 确认并丢弃反应。
  # true = 机器人*自己的消息*上的任何反应均会路由进 agent。
  reaction_triggers: true
  # 或显式表情白名单——仅这些名称会路由，且可针对任何消息
  # （表情交接工作流，例如用 :task: 捕获）：
  # reaction_triggers: [white_check_mark, thumbsup, task]
  # 可选交接目标：在此频道（顶级）或话题（C123:<thread_ts>）中回复，
  # 而非在被反应消息的话题中回复。
  # reaction_trigger_target: C0123456789
```

环境变量等价项：`SLACK_REACTION_TRIGGERS`（`true`/`all` 或逗号分隔列表）和 `SLACK_REACTION_TRIGGER_TARGET`。

行为：

- 反应作为普通 agent 轮次到达，文本为 `reaction:added:👍` / `reaction:removed:👍`（常见 Slack 名称会转换为 Unicode；未知名称保持原样，例如 `reaction:added:custom-emoji`），并置于被反应消息的话题下，因此 agent 可以看到被反应的内容，且该轮次与回复一样进入同一会话。
- 反应者成为该消息的用户，因此**用户授权和 `allowed_channels` 门控与输入消息完全相同**——随机用户的反应不能在其消息无法触发 agent 的位置触发 agent。
- 使用 `reaction_triggers: true` 时，仅机器人**自己的**消息上的反应会路由（批准/确认流程）。使用显式表情白名单时，列出的表情可从任何消息路由。
- 机器人自身的生命周期反应（`:eyes:` 等）绝不会反馈回来。
- 独立于此选择启用项，每个人类反应都会为不需要 agent 轮次的观察者触发 `reaction:added`/`reaction:removed` [gateway hooks](../features/hooks.md#available-events)。

### 对等 Agent 冒烟检查

对于依赖每轮严格提及的多机器人 Slack 部署，请保持以下配置：

```yaml
slack:
  require_mention: true
  strict_mention: true
  allow_bots: mentions
  allowed_channels: ""
```

变更 gateway 配置、部署或重启后，运行此合成冒烟测试目标：

```bash
uv run --frozen pytest -q tests/gateway/test_slack_peer_agent_smoke.py -o addopts=''
```

此目标仅使用进程内合成 Slack 事件。它不会发送真实 Slack 消息，默认也不需要真实机器人 token。

失败分类：

- `config:`：`test_peer_agent_smoke_preflight_contract` 捕获了配置不匹配（`require_mention`、`strict_mention`、`allow_bots` 或 `allowed_channels`）。
- `platform_connectivity:`：适配器/客户端未初始化，因此路由冒烟结果尚不可信。
- `bot_identity:`：适配器从未解析其机器人用户 ID，因此当前消息提及检查无法工作。
- `routing_logic:`：Slack 适配器在某项对等 agent 不变量上发生回归（人类提及路由、对等机器人忽略、显式对等提及准入或被动确认/状态/错误抑制）。

若此目标通过但真实工作区仍错误路由消息，请在路由逻辑之外排查 Slack token/工作区连接性和运行时部署状态。

### 频道白名单（`allowed_channels`）

将机器人限制在固定的 Slack 频道集合中——当机器人被邀请到许多频道但只应在少数频道中响应时很有用。设置后，不在此列表中的频道消息将被**静默忽略**，即使机器人被 `@mention`。

**1:1 私信不受此过滤器影响**，因此授权用户始终可以通过私信联系机器人。**群组私信（MPIM）不受豁免**——与频道一样，MPIM 必须在白名单中（其 ID 以 `G` 开头），否则其消息将被丢弃。

```yaml
slack:
  allowed_channels:
    - "C0123456789"   # #ops
    - "C0987654321"   # #incident-response
```

或通过环境变量（逗号分隔）：

```bash
SLACK_ALLOWED_CHANNELS="C0123456789,C0987654321"
```

行为说明：

- 空/未设置 → 无限制（完全向后兼容）。
- 非空 → 频道 ID 必须在列表中，否则消息在任何其他门控（提及要求、`free_response_channels` 等）运行之前被丢弃。
- Slack 频道 ID 以 `C`（公开）、`G`（私有）或 `D`（私信）开头。可通过 Slack UI 的"打开频道详情"→"关于"面板或 API 查找。

另见：[管理员/用户斜杠命令分离](../../reference/slash-commands.md#permissions-and-adminuser-split)。

### 未授权用户处理

```yaml
slack:
  # 当未授权用户（不在 SLACK_ALLOWED_USERS 中）私信机器人时的处理方式
  # "pair"   — 提示他们输入配对码（默认）
  # "ignore" — 静默丢弃消息
  unauthorized_dm_behavior: "pair"
```

你也可以为所有平台全局设置：

```yaml
unauthorized_dm_behavior: "pair"
```

`slack:` 下的平台特定设置优先于全局设置。

### 语音转录

```yaml
# 全局设置——启用/禁用传入语音消息的自动转录
stt_enabled: true
```

为 `true`（默认值）时，传入的音频消息会在被 agent 处理之前，使用配置的 STT 提供商自动转录。

### 完整示例

```yaml
# 全局 gateway 设置
group_sessions_per_user: true
unauthorized_dm_behavior: "pair"
stt_enabled: true

# Slack 特定设置
slack:
  require_mention: true
  unauthorized_dm_behavior: "pair"

# 平台配置
platforms:
  slack:
    reply_to_mode: "first"
    extra:
      reply_in_thread: true
      reply_broadcast: false
```

---

## 主频道

将 `SLACK_HOME_CHANNEL` 设置为频道 ID，Hermes 将在此频道发送计划消息、定时任务结果和其他主动通知。查找频道 ID 的方法：

1. 在 Slack 中右键点击频道名称
2. 点击 **View channel details**
3. 向下滚动——频道 ID 显示在底部

```bash
SLACK_HOME_CHANNEL=C01234567890
```

确保机器人已被**邀请到该频道**（`/invite @Hermes Agent`）。

### Cron 投递目标

Cron 任务（参见 [cron 指南](../features/cron.md#delivery-options)）可通过三种方式定位 Slack：

| `deliver:` 值 | 投递位置 |
|------------------|----------------|
| `slack` | 主频道（`SLACK_HOME_CHANNEL`） |
| `slack:C0123456789` | 由 ID 指定的频道 |
| `slack:U0123456789` | 该用户的**私信**——裸用户 ID 会自动解析为私信会话（需要 `im:write` 权限范围） |

即使 cron 进程不与 gateway 位于同一位置，投递仍可工作——Hermes 会回退为使用 `SLACK_BOT_TOKEN` 的独立 Web API 发送程序。cron 输出中的 `MEDIA:` 附件会作为原生 Slack 文件共享上传到相同目标。

### 发送消息和媒体（`send_message`）

agent 的 `send_message` 工具接受相同的目标形式：频道 ID（`C…`/`G…`）、私信会话（`D…`）或裸用户 ID（`U…`/`W…`）；后者会在每种发送路径中解析为用户私信，包括文本、媒体和交互式提示。`MEDIA:<path>` 附件（图片、PDF、文档）会作为原生文件共享上传；当一条短消息附带单个附件时，它会作为文件说明而非单独消息发送。缺失文件会按文件报告为警告，而不会导致整个发送失败。

---

## 多工作区支持

Hermes 可以使用单个 gateway 实例**同时连接多个 Slack 工作区**。每个工作区使用其自己的机器人用户 ID 独立认证。

### 配置

在 `SLACK_BOT_TOKEN` 中以**逗号分隔列表**的形式提供多个 bot token：

```bash
# 多个 bot token——每个工作区一个
SLACK_BOT_TOKEN=«redacted:xox…»,«redacted:xox…»,«redacted:xox…»

# Socket Mode 仍使用单个 app-level token
SLACK_APP_TOKEN=xapp-your-app-token
```

或在 `~/.hermes/config.yaml` 中：

```yaml
platforms:
  slack:
    token: "«redacted:xox…»,«redacted:xox…»"
```

### OAuth Token 文件

除了环境变量或配置中的 token 外，Hermes 还会从以下位置的 **OAuth token 文件**加载 token：

```
~/.hermes/slack_tokens.json
```

此文件是一个将团队 ID 映射到 token 条目的 JSON 对象：

```json
{
  "T01ABC2DEF3": {
    "token": "«redacted:xox…»",
    "team_name": "My Workspace"
  }
}
```

此文件中的 token 会与通过 `SLACK_BOT_TOKEN` 指定的 token 合并。重复的 token 会自动去重。

### 工作原理

- 列表中的**第一个 token** 是主 token，用于 Socket Mode 连接（AsyncApp）。
- 每个 token 在启动时通过 `auth.test` 进行认证。gateway 将每个 `team_id` 映射到其自己的 `WebClient` 和 `bot_user_id`。
- 消息到达时，Hermes 使用正确的工作区特定客户端进行响应。
- 主 `bot_user_id`（来自第一个 token）用于向后兼容期望单一机器人身份的功能。

---

## 语音消息

Hermes 支持 Slack 上的语音功能：

- **传入：** 语音/音频消息使用配置的 STT 提供商自动转录：本地 `faster-whisper`、Groq Whisper（`GROQ_API_KEY`）或 OpenAI Whisper（`VOICE_TOOLS_OPENAI_KEY`）
- **传出：** TTS 响应以音频文件附件形式发送

---

## 按频道设置 Prompt

为特定 Slack 频道分配临时系统 prompt（提示词）。该 prompt 在运行时每轮注入——从不持久化到对话历史——因此更改立即生效。

```yaml
slack:
  channel_prompts:
    "C01RESEARCH": |
      You are a research assistant. Focus on academic sources,
      citations, and concise synthesis.
    "C02ENGINEERING": |
      Code review mode. Be precise about edge cases and
      performance implications.
```

键为 Slack 频道 ID（通过频道详情 → "关于" → 滚动到底部查找）。匹配频道中的所有消息都会将该 prompt 作为临时系统指令注入。

## 按频道绑定技能

在特定频道或私信中新会话开始时自动加载技能。与按频道设置 prompt（每轮注入）不同，技能绑定在**会话开始时**将技能内容作为用户消息注入——它成为对话历史的一部分，后续轮次无需重新加载。

这非常适合有专用用途的私信或频道（闪卡、特定领域问答机器人、支持分类频道等），在这些场景中你不希望模型自己的技能选择器在每次简短回复时决定是否加载。

```yaml
slack:
  channel_skill_bindings:
    # 私信频道——始终以"german-flashcards"模式运行
    - id: "D0ATH9TQ0G6"
      skills:
        - german-flashcards
    # 研究频道——按顺序预加载多个技能
    - id: "C01RESEARCH"
      skills:
        - arxiv
        - writing-plans
    # 简写形式：单个技能作为字符串
    - id: "C02SUPPORT"
      skill: hubspot-on-demand
```

注意事项：
- 绑定按频道 ID 匹配。对于绑定频道中的话题消息，话题继承父频道的绑定。
- 技能仅在会话开始时加载（新会话或自动重置后）。如果更改绑定，请运行 `/new` 或等待会话自动重置以使其生效。
- 与 `channel_prompts` 结合使用，可在技能指令之上为每个频道设置语气/约束。

## 故障排除

| 问题 | 解决方案 |
|---------|----------|
| 机器人不响应私信 | 验证 `message.im` 在事件订阅中，且应用已重新安装 |
| 机器人在私信中正常但在频道中不响应 | **最常见问题。** 将 `message.channels` 和 `message.groups` 添加到事件订阅，重新安装应用，并用 `/invite @Hermes Agent` 邀请机器人加入频道 |
| 机器人不响应频道中的 @mention | 1) 检查 `message.channels` 事件是否已订阅。2) 机器人必须被邀请到频道。3) 确保已添加 `channels:history` 权限范围。4) 更改权限范围/事件后重新安装应用 |
| 机器人忽略私有频道中的消息 | 添加 `message.groups` 事件订阅和 `groups:history` 权限范围，然后重新安装应用并 `/invite` 机器人 |
| 机器人不响应群组私信（多人私信） | 添加 `message.mpim` 事件订阅和 `mpim:history` 权限范围（以及 `mpim:read`），然后**重新安装**应用。没有 `message.mpim`，即使 1:1 私信正常，Slack 也永远不会向机器人投递群组私信消息。 |
| 私信中出现"向此应用发送消息已被关闭" | 在 App Home 设置中启用 **Messages Tab**（见第五步） |
| "not_authed" 或 "invalid_auth" 错误 | 重新生成 Bot Token 和 App Token，更新 `.env` |
| 机器人响应但无法在频道中发帖 | 用 `/invite @Hermes Agent` 邀请机器人加入频道 |
| 机器人可以聊天但无法读取上传的图片/文件 | 添加 `files:read`，然后**重新安装**应用。当 Slack 返回权限范围/认证/权限失败时，Hermes 现在会在聊天中显示附件访问诊断信息。 |
| `missing_scope` 错误 | 在 OAuth & Permissions 中添加所需权限范围，然后**重新安装**应用 |
| Socket 频繁断开 | 检查你的网络；Bolt 会自动重连，但不稳定的连接会导致延迟 |
| 更改了权限范围/事件但没有任何变化 | 更改任何权限范围或事件订阅后，**必须重新安装**应用到工作区 |

### 快速检查清单

如果机器人在频道中不工作，请验证以下**所有**项目：

1. ✅ 已订阅 `message.channels` 事件（公开频道）
2. ✅ 已订阅 `message.groups` 事件（私有频道）
3. ✅ 已订阅 `app_mention` 事件
4. ✅ 已添加 `channels:history` 权限范围（公开频道）
5. ✅ 已添加 `groups:history` 权限范围（私有频道）
6. ✅ 添加权限范围/事件后已**重新安装**应用
7. ✅ 已**邀请**机器人加入频道（`/invite @Hermes Agent`）
8. ✅ 你在消息中 **@mention** 了机器人

---

## 安全

:::warning
**始终设置 `SLACK_ALLOWED_USERS`**，填入授权用户的 Member ID。没有此设置，gateway 默认会**拒绝所有消息**作为安全措施。切勿分享你的 bot token——像密码一样对待它们。
:::

- Token 应存储在 `~/.hermes/.env` 中（文件权限 `600`）
- 定期通过 Slack 应用设置轮换 token
- 审计谁有权访问你的 Hermes 配置目录
- Socket Mode 意味着不暴露公开端点——减少一个攻击面
