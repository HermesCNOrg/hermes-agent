---
sidebar_position: 2
title: "斜杠命令参考"
description: "交互式 CLI 和消息平台斜杠命令的完整参考"
---

# 斜杠命令参考

Hermes 提供两个斜杠命令入口，二者均由 `hermes_cli/commands.py` 中的中央 `COMMAND_REGISTRY` 驱动：

- **交互式 CLI 斜杠命令** — 由 `cli.py` 分发，并根据注册表提供自动补全
- **消息平台斜杠命令** — 由 `gateway/run.py` 分发，帮助文本和平台菜单均根据注册表生成

已安装的 skill 也会在两个入口中作为动态斜杠命令提供。其中包括 `/plan` 等内置 skill；该命令会打开计划模式，并将 Markdown 计划保存到活动工作区/后端工作目录下的 `.hermes/plans/` 中。

## 权限与管理员/普通用户分级

所有支持按用户设置允许名单的消息平台（Telegram、Discord、Slack、Matrix、Mattermost、Signal 等）也都支持两级斜杠命令权限：**管理员**可以使用所有已注册命令，**普通用户**只能使用 `user_allowed_commands` 中列出的命令（以及始终允许的基础命令 `/help` 和 `/whoami`）。请在 `~/.hermes/gateway-config.yaml` 对应平台的 `extra:` 块中配置 `allow_admin_from` 和 `user_allowed_commands`（以及相应的群组配置 `group_allow_admin_from` / `group_user_allowed_commands`）。

各平台文档均提供示例，其配置结构完全相同：

- [Telegram](../user-guide/messaging/telegram.md#slash-command-access-control)
- [Discord](../user-guide/messaging/discord.md)
- [Slack](../user-guide/messaging/slack.md)
- [Matrix](../user-guide/messaging/matrix.md)
- [Mattermost](../user-guide/messaging/mattermost.md)
- [Signal](../user-guide/messaging/signal.md)

如果某个作用域未设置 `allow_admin_from`，该作用域会保持不受限的向后兼容模式——所有获准用户均可运行所有命令。

## 交互式 CLI 斜杠命令

在 CLI 中输入 `/` 即可打开自动补全菜单。内置命令不区分大小写。

### 会话

| 命令 | 说明 |
|---------|-------------|
| `/new [name]`（别名：`/reset`） | 开始新会话（使用全新的会话 ID 和历史记录）。可选参数 `[name]` 用于设置初始会话标题——例如，`/new my-experiment` 会打开一个标题已设为 `my-experiment` 的新会话，方便以后通过 `/resume` 或 `/sessions` 找到它。追加 `now`、`--yes` 或 `-y` 可跳过确认弹窗，例如 `/reset now`、`/new --yes my-experiment`。 |
| `/clear` | 清屏并开始新会话 |
| `/history` | 显示对话历史记录 |
| `/save` | 保存当前对话 |
| `/prompt`（别名：`/compose`） | 使用 `$EDITOR`（Markdown）而非行内输入框撰写下一条提示词——适合较长、多行或需要精细排版的提示词。 |
| `/retry` | 重试最后一条消息（重新发送给 agent） |
| `/undo` | 移除最后一轮用户/助手对话 |
| `/title` | 设置当前会话的标题（用法：/title My Session Name） |
| `/compress [here [N] \| focus topic]` | 手动压缩对话上下文（写入 memory + 生成摘要）。`/compress here [N]` 会概括除最近 N 轮对话以外的所有内容（默认为 2 轮），并逐字保留这 N 轮内容——你可以自行选择压缩边界。焦点主题可以缩小完整摘要所保留内容的范围。 |
| `/rollback` | 列出或恢复文件系统检查点（用法：/rollback [number]） |
| `/snapshot [create\|restore <id>\|prune]`（别名：`/snap`） | 创建或恢复 Hermes 配置/状态快照。`create [label]` 保存快照，`restore <id>` 恢复至该快照，`prune [N]` 删除旧快照；不带参数时列出所有快照。 |
| `/stop` | 终止所有正在运行的后台进程 |
| `/queue <prompt>`（别名：`/q`） | 将提示词排入下一轮队列（不会中断 agent 当前的回复）。 |
| `/steer <prompt>` | 注入一条运行中说明，它会在**下一次工具调用之后**送达 agent——不会中断，也不会产生新的用户轮次。当前工具完成后，这段文本会追加到最后一个工具结果的内容中，从而在不打断当前工具调用循环的情况下为 agent 提供新上下文。可用它在任务中途调整方向（例如 agent 正在运行测试时输入“重点检查 auth 模块”）。 |
| `/goal <text>` | 设置一个让 Hermes 跨轮次持续推进的常驻目标——这是我们对 Ralph loop 的实现。每轮结束后，一个辅助裁判模型会判断目标是否完成；如果尚未完成，Hermes 会自动继续。子命令：`/goal status`、`/goal pause`、`/goal resume`、`/goal clear`。预算默认为 20 轮（`goals.max_turns`）；任何真实的用户消息都会抢占自动继续循环，且状态可在 `/resume` 后保留。完整指南见[持续目标](/user-guide/features/goals)。 |
| `/subgoal <text>` | 在循环进行期间为活动目标追加一项用户指定的判定条件。继续执行的提示词会将所有子目标原样呈现给 agent，裁判也会将其纳入 DONE/CONTINUE 判断——因此，只有原目标**和**每个子目标都达成后，目标才会被标记为完成。子命令：`/subgoal`（列出）、`/subgoal remove <N>`、`/subgoal clear`。需要已有活动的 `/goal`。 |
| `/moa <prompt>` | 使用默认的 [Mixture of Agents](/user-guide/features/mixture-of-agents) 预设运行一次提示词，然后恢复当前模型。仅执行一次，不会更改当前会话的模型。 |
| `/resume [name]` | 恢复之前命名的会话 |
| `/sessions`（TUI 别名：`/switch`） | 经典 CLI：在交互式选择器中浏览并恢复历史会话。TUI：打开实时会话切换器，显示当前已打开的 TUI 会话。在 TUI 中使用 `/sessions new` 可立即开始另一个实时会话。 |
| `/redraw` | 强制完整重绘 UI（用于修复 tmux 调整大小、鼠标选择残影等造成的终端显示错位） |
| `/status` | 显示会话信息——模型、提供商、profile、会话 ID、工作目录、标题、创建/更新时间戳、token 总量、agent 运行状态——随后显示本地的**会话回顾**区块（近期用户/助手轮次数、工具结果数、最常用工具、最近访问的几个文件、最新用户提示词和最新助手回复）。回顾内容根据内存中的对话在本地计算；不会调用 LLM，也不影响提示词缓存。 |
| `/agents`（别名：`/tasks`） | 显示当前会话中的活动 agent 和正在运行的任务。 |
| `/background <prompt>`（别名：`/bg`、`/btw`） | 在单独的后台会话中运行提示词。agent 会独立处理你的提示词——当前会话仍可继续用于其他工作。任务完成后，结果会显示在面板中。参阅 [CLI 后台会话](/user-guide/cli#background-sessions)。 |
| `/branch [name]`（别名：`/fork`） | 从当前会话创建分支（探索另一条路径） |
| `/handoff <platform>` | **仅限 CLI。** 将当前会话移交给消息平台（Telegram、Discord、Slack、WhatsApp、Signal、Matrix）。gateway 会立即接管，在支持线程的平台上创建新线程（Telegram 话题、Discord 文字频道线程、Slack 基于消息的线程），将目标位置重新绑定到你的 CLI session_id，以重放带有完整角色信息的对话记录，并构造一轮合成的用户消息，让 agent 确认已在新位置工作。成功后，CLI 会正常退出并提示 `/resume`；你可以随时通过 `/resume <title>` 在本地恢复会话。会话轮次进行中会拒绝执行。需要 gateway 正在运行，且已为目标平台配置 home 频道（在目标聊天中执行 `/sethome`）。参阅[跨平台移交](/user-guide/sessions#cross-platform-handoff)。 |

### 配置

| 命令 | 说明 |
|---------|-------------|
| `/config` | 显示当前配置 |
| `/model [model-name]` | 显示或更改当前模型。支持：`/model claude-sonnet-4`、`/model provider:model`（切换提供商）、`/model custom:model`（自定义端点）、`/model custom:name:model`（已命名的自定义提供商）、`/model custom`（根据端点自动检测），以及用户自定义别名（`/model fav`、`/model grok`——参阅[自定义模型别名](#custom-model-aliases)）。使用 `--global` 可将更改持久化到 config.yaml。**注意：** `/model` 只能在已经配置的提供商之间切换。如需添加新的提供商，请退出会话并在终端中运行 `hermes model`。**费用说明：**在对话中途切换模型会重置提示词缓存——缓存键包含模型，因此下一轮会以完整输入价格重新读取整个对话，而非享受约 75% 折扣的缓存价格。这是正常且不可避免的行为，但在长会话中值得留意。 |
| `/codex-runtime [auto\|codex_app_server\|on\|off]` | 切换 OpenAI/Codex 模型可选的 [Codex app-server runtime](../user-guide/features/codex-app-server-runtime)。`auto`（默认）使用 Hermes 的标准 chat completions；`codex_app_server` 会将每轮交给 `codex app-server` 子进程，以使用原生 shell、apply_patch、ChatGPT 订阅认证和迁移后的 Codex 插件。下次会话生效。 |
| `/personality` | 设置预定义的 personality |
| `/verbose` | 循环切换工具进度显示：off → new → all → verbose。可通过配置[为消息平台启用](#notes)。 |
| `/fast [normal\|fast\|status]` | 切换快速模式——OpenAI Priority Processing / Anthropic Fast Mode。选项：`normal`、`fast`、`status`。 |
| `/reasoning` | 管理推理强度和推理内容显示（用法：/reasoning [level\|show\|hide]） |
| `/skin` | 显示或更改显示皮肤/主题 |
| `/statusbar`（别名：`/sb`） | 开启或关闭上下文/模型状态栏 |
| `/voice [on\|off\|tts\|status]` | 切换 CLI 语音模式和语音播放。录音使用 `voice.record_key`（默认：`Ctrl+B`）。 |
| `/yolo` | 切换 YOLO 模式——跳过所有危险命令的审批提示。 |
| `/footer [on\|off\|status]` | 切换最终回复中的 gateway 运行时元数据页脚（显示模型、上下文占用百分比和 cwd）。 |
| `/busy [queue\|steer\|interrupt\|status]` | 仅限 CLI：控制 Hermes 工作时按下 Enter 的行为——将新消息排入队列、在当前轮次中进行引导，或立即中断。 |
| `/indicator [kaomoji\|emoji\|unicode\|ascii]` | 仅限 CLI：选择 TUI 忙碌指示器的样式。 |
| `/timestamps [on\|off\|status]` | 仅限 CLI：切换消息和 `/history` 中的 `[HH:MM]` 时间戳。 |

### 工具与 Skill

| 命令 | 说明 |
|---------|-------------|
| `/tools [list\|disable\|enable] [name...]` | 管理工具：列出可用工具，或在当前会话中禁用/启用指定工具。禁用工具会将其从 agent 的工具集中移除，并触发会话重置。 |
| `/toolsets` | 列出可用工具集 |
| `/browser [connect\|disconnect\|status]` | 管理本地 Chromium 系浏览器的 CDP 连接。`connect` 将浏览器工具连接到正在运行的 Chrome、Brave、Chromium 或 Edge 实例（默认：`http://127.0.0.1:9222`）。`disconnect` 断开连接。`status` 显示当前连接。如果未检测到调试器，则自动启动支持的 Chromium 系浏览器。 |
| `/skills` | 从在线 registry 搜索、安装、检查或管理 skill。它也是 skill 写入审批门控的审核入口：`/skills pending`、`/skills diff <id>`、`/skills approve <id>`、`/skills reject <id>`、`/skills approval on\|off`。参阅[为 agent 的 skill 写入设置门控](/user-guide/features/skills#gating-agent-skill-writes-skillswrite_approval)。 |
| `/memory [pending\|approve\|reject\|approval]` | 审核由写入审批门控（`memory.write_approval`）暂存的 memory 写入，并切换该门控。参阅[控制 memory 写入](/user-guide/features/memory#controlling-memory-writes-write_approval)。 |
| `/bundles` | 列出已配置的 skill bundle——即一次预加载多个 skill 的 `/<name>` 斜杠别名。在 `~/.hermes/config.yaml` 的 `bundles:` 下配置。参阅 [Skill Bundle](/user-guide/features/skills#skill-bundles)。 |
| `/learn <what to learn from>` | 从你描述的任何内容中提炼出可复用的 skill——可以是目录、URL、刚刚带领 agent 完成的工作流，或粘贴的笔记。此命令采用开放式流程：agent 会使用自己的工具收集来源，并按照项目的编写规范创作 `SKILL.md`。适用于 CLI、消息 gateway、TUI 和 dashboard 的 Skills 页面。 |
| `/cron` | 管理定时任务（列出、添加/创建、编辑、暂停、恢复、运行、删除） |
| `/suggestions [accept\|dismiss N\|catalog\|clear]`（别名：`/suggest`） | 审核自动化建议。使用 `/suggestions` 列出待处理建议，`/suggestions accept <id>` 根据建议创建自动化，`/suggestions dismiss <id>` 拒绝一项建议，`/suggestions catalog` 添加精选的入门自动化，`/suggestions clear` 清除已处理的建议记录。接受后创建的任务会保留当前入口作为投递来源。 |
| `/blueprint [name] [slot=value ...]`（别名：`/bp`） | 根据 blueprint 模板设置自动化。直接输入 `/blueprint` 会列出目录；`/blueprint <name>` 会在下一轮 agent 对话中启动引导式参数填写流程；`/blueprint <name> slot=value ...` 则直接创建任务。 |
| `/curator` | 后台 skill 维护——`status`、`run`、`pin`、`archive`。参阅 [Curator](/user-guide/features/curator)。 |
| `/kanban <action>` | 无需离开聊天即可操作多 profile、多项目协作看板。支持完整的 `hermes kanban` 命令：`/kanban list`、`/kanban show t_abc`、`/kanban create "title" --assignee X`、`/kanban comment t_abc "text"`、`/kanban unblock t_abc`、`/kanban dispatch` 等。还支持多看板：`/kanban boards list`、`/kanban boards create <slug>`、`/kanban boards switch <slug>`、`/kanban --board <slug> <action>`。参阅 [Kanban 斜杠命令](/user-guide/features/kanban#kanban-slash-command)。 |
| `/reload-mcp`（别名：`/reload_mcp`） | 从 config.yaml 重新加载 MCP 服务器 |
| `/reload-skills`（别名：`/reload_skills`） | 重新扫描 `~/.hermes/skills/`，查找新安装或已移除的 skill |
| `/reload` | 将 `.env` 变量重新加载到正在运行的会话中（无需重启即可读取新的 API 密钥） |
| `/plugins` | 列出已安装的插件及其状态 |
| `/pet [list\|<slug>]` | 切换显示或领养一个 [petdex](/user-guide/features/pets) 吉祥物。`/pet` 切换面板，`/pet list` 显示已安装的 pet，`/pet <slug>` 领养指定 pet。 |
| `/hatch <description>`（别名：`/generate-pet`） | 使用已配置的图像后端（OpenRouter / Nous Portal），根据文字描述生成一个全新的 petdex pet。参阅 [Pet](/user-guide/features/pets)。 |

### 信息

| 命令 | 说明 |
|---------|-------------|
| `/help` | 显示此帮助信息 |
| `/version` | 显示 Hermes Agent 的版本、构建和环境信息。 |
| `/usage` | 显示 token 用量、费用明细、会话时长，以及——当活动提供商支持时——从提供商 API 实时获取的**账户限额**区块，其中包括剩余配额/积分/套餐用量。 |
| `/credits` | 显示你的 Nous 积分余额和充值跳转链接。 |
| `/billing` | Nous 的 CLI 终端计费流程——查看余额、购买积分，以及管理自动充值/月度限额。 |
| `/insights` | 显示用量洞察和分析（最近 30 天） |
| `/platforms`（别名：`/gateway`） | 显示 gateway/消息平台状态（仅限 CLI 的摘要视图）。 |
| `/paste` | 附加剪贴板中的图片 |
| `/copy [number]` | 将最后一条助手回复复制到剪贴板（也可用数字复制倒数第 N 条）。仅限 CLI。 |
| `/image <path>` | 为下一条提示词附加本地图片文件。 |
| `/debug` | 上传调试报告（系统信息 + 日志）并获取可分享的链接。消息平台中也可使用。 |
| `/profile` | 显示活动 profile 名称和主目录 |

### 退出

| 命令 | 说明 |
|---------|-------------|
| `/quit` | 退出 CLI（也可使用 `/exit`）。 |

### 动态 CLI 斜杠命令

| 命令 | 说明 |
|---------|-------------|
| `/<skill-name>` | 将任意已安装的 skill 作为按需命令加载。示例：`/gif-search`、`/github-pr-workflow`、`/excalidraw`。 |
| `/skills ...` | 从 registry 和官方 optional-skills 目录搜索、浏览、检查、安装、审计、发布及配置 skill。 |

### 快捷命令

用户自定义快捷命令可以将简短的斜杠命令映射到 shell 命令或另一个斜杠命令。请在 `~/.hermes/config.yaml` 中配置：

```yaml
quick_commands:
  status:
    type: exec
    command: systemctl status hermes-agent
  deploy:
    type: exec
    command: scripts/deploy.sh
  inbox:
    type: alias
    target: /gmail unread
```

之后即可在 CLI 或消息平台中输入 `/status`、`/deploy` 或 `/inbox`。快捷命令会在分发时解析，因此不一定出现在每个内置自动补全/帮助表中。

快捷命令不支持仅包含字符串的提示词快捷方式。请将较长的可复用提示词放入 skill，或使用 `type: alias` 指向现有斜杠命令。

### 自定义模型别名

你可以为常用模型定义自己的短名称，然后在 CLI 或任何消息平台中通过 `/model <alias>` 使用。别名在两处的行为完全相同，既支持仅当前会话生效的切换（默认），也支持 `--global` 切换。

支持两种配置格式：

**完整格式** — 指定确切的模型、提供商，以及可选的 base URL。将以下内容写入 `~/.hermes/config.yaml`：

```yaml
model_aliases:
  fav:
    model: claude-sonnet-4.6
    provider: anthropic
  grok:
    model: grok-4
    provider: x-ai
  ollama-qwen:
    model: qwen3-coder:30b
    provider: custom
    base_url: http://localhost:11434/v1
```

**简写格式** — 使用一个字符串表示 `provider/model`。无需编辑 YAML，直接在 shell 中设置：

```bash
hermes config set model.aliases.fav anthropic/claude-opus-4.6
hermes config set model.aliases.grok x-ai/grok-4
```

然后在聊天中输入：

```
/model fav            # session-only
/model grok --global  # also persists current-model change to config.yaml
```

用户别名的优先级高于内置短名称，因此将别名命名为 `sonnet`、`kimi`、`opus` 等会覆盖内置名称。别名名称不区分大小写。

### 别名解析

命令支持前缀匹配：输入 `/h` 会解析为 `/help`，输入 `/mod` 会解析为 `/model`。如果前缀存在歧义（匹配多个命令），则采用注册表顺序中的第一个匹配项。完整命令名和已注册别名始终优先于前缀匹配。

## 消息平台斜杠命令

消息 gateway 在 Telegram、Discord、Slack、WhatsApp、Signal、Email、Home Assistant 和 Teams 聊天中支持以下内置命令：

| 命令 | 说明 |
|---------|-------------|
| `/start` | 平台协议命令。许多聊天平台（Telegram、Discord 等）会在用户首次打开 bot 对话时自动发送 `/start`。Hermes 会静默确认该 ping——不回复 agent 消息，也不消耗会话轮次——因此首次联系的握手不会浪费一轮对话。你也可以显式发送此命令，以确认 gateway 可以访问。 |
| `/new [name]`（别名：`/reset`） | 开始新会话（使用全新的会话 ID 和历史记录）。可选参数 `[name]` 用于设置初始会话标题。追加 `now`、`--yes` 或 `-y` 可跳过确认弹窗，例如 `/reset now`、`/new --yes my-experiment`。 |
| `/status` | 显示会话信息，随后显示本地的**会话回顾**区块（近期轮次数、最常用工具、访问的文件、最新提示词和回复）。 |
| `/stop` | 终止所有正在运行的后台进程，并中断正在运行的 agent。 |
| `/model [provider:model]` | 显示或更改模型。支持切换提供商（`/model zai:glm-5`）、自定义端点（`/model custom:model`）、已命名的自定义提供商（`/model custom:local:qwen`）、自动检测（`/model custom`），以及用户自定义别名（`/model fav`、`/model grok`——参阅[自定义模型别名](#custom-model-aliases)）。使用 `--global` 可将更改持久化到 config.yaml。**注意：** `/model` 只能在已经配置的提供商之间切换。如需添加新的提供商或设置 API 密钥，请在终端中（聊天会话之外）运行 `hermes model`。**费用说明：**在会话中途切换模型会重置提示词缓存（缓存键包含模型），因此下一条消息会以完整输入价格重新读取整个对话。 |
| `/codex-runtime [auto\|codex_app_server\|on\|off]` | 切换可选的 [Codex app-server runtime](../user-guide/features/codex-app-server-runtime)。该设置会持久化到 config.yaml 中的 `model.openai_runtime`，并逐出缓存的 agent，以便下一条消息使用新的 runtime。下次会话生效。 |
| `/personality [name]` | 为会话设置 personality 覆盖层。 |
| `/fast [normal\|fast\|status]` | 切换快速模式——OpenAI Priority Processing / Anthropic Fast Mode。 |
| `/retry` | 重试最后一条消息。 |
| `/undo` | 移除最后一轮对话。 |
| `/sethome`（别名：`/set-home`） | 将当前聊天标记为该平台用于投递消息的 home 频道。 |
| `/compress [here [N] \| focus topic]` | 手动压缩对话上下文。`/compress here [N]` 会逐字保留最近 N 轮对话（默认为 2 轮），并概括其余内容。焦点主题可以缩小完整摘要所保留内容的范围。 |
| `/topic [off\|help\|session-id]` | **仅限 Telegram 私聊。** 管理由用户控制的多会话话题模式。`/topic` 用于启用该模式或显示状态；`/topic off` 用于禁用并清除绑定；`/topic help` 显示用法；在话题中使用 `/topic <session-id>` 可恢复之前的会话。参阅[多会话私聊模式](/user-guide/messaging/telegram#multi-session-dm-mode-topic)。 |
| `/title [name]` | 设置或显示会话标题。 |
| `/resume [name]` | 恢复之前命名的会话。 |
| `/usage` | 显示 token 用量、估算费用明细（输入/输出）、上下文窗口状态、会话时长，以及——当活动提供商支持时——从提供商 API 实时获取的**账户限额**区块，其中包括剩余配额/积分。 |
| `/credits` | 显示你的 Nous 积分余额，以及可在浏览器中打开 portal 计费页面的充值链接。 |
| `/insights [days]` | 显示用量分析。 |
| `/reasoning [level\|show\|hide]` | 更改推理强度或切换推理内容显示。 |
| `/voice [on\|off\|tts\|join\|channel\|leave\|status]` | 控制聊天中的语音回复。`join`/`channel`/`leave` 用于管理 Discord 语音频道模式。 |
| `/rollback [number]` | 列出或恢复文件系统检查点。 |
| `/background <prompt>` | 在单独的后台会话中运行提示词。任务完成后，结果会投递回同一个聊天。参阅[消息平台后台会话](/user-guide/messaging/#background-sessions)。 |
| `/queue <prompt>`（别名：`/q`） | 将提示词排入下一轮队列，而不中断当前轮次。 |
| `/steer <prompt>` | 在下一次工具调用后注入一条消息且不中断当前执行——模型会在下一次迭代时获取它，而不会将其作为新轮次。 |
| `/goal <text>` | 设置一个让 Hermes 跨轮次持续推进的常驻目标——这是我们对 Ralph loop 的实现。裁判模型会在每轮结束后检查；如果尚未完成，Hermes 会自动继续，直到目标完成、你暂停/清除目标，或达到轮次预算（默认为 20 轮）。子命令：`/goal status`、`/goal pause`、`/goal resume`、`/goal clear`。agent 运行期间可以安全地查询状态、暂停或清除目标；设置新目标前必须先执行 `/stop`。参阅[持续目标](/user-guide/features/goals)。 |
| `/footer [on\|off\|status]` | 切换最终回复中的运行时元数据页脚（显示模型、上下文占用百分比和 cwd）。 |
| `/curator [status\|run\|pin\|archive]` | 后台 skill 维护控制。 |
| `/suggestions [accept\|dismiss N\|catalog\|clear]` | 直接在聊天中审核自动化建议。`/suggestions` 列出待处理建议，`catalog` 添加精选的入门自动化，`clear` 清理已处理的建议记录。接受建议后创建的任务会保留当前聊天/线程作为投递来源。 |
| `/blueprint [name] [slot=value ...]` | 浏览 cron blueprint、启动引导式参数填写对话，或直接创建 blueprint 任务。直接创建的任务会投递回当前聊天/线程。 |
| `/memory [pending\|approve\|reject\|approval]` | 审核由写入审批门控（`memory.write_approval`）暂存的 memory 写入——可直接在聊天中批准或拒绝——并通过 `/memory approval on\|off` 切换门控。参阅[控制 memory 写入](/user-guide/features/memory#controlling-memory-writes-write_approval)。 |
| `/skills [pending\|approve\|reject\|diff\|approval]` | 审核由写入审批门控（`skills.write_approval`）暂存的 **skill** 写入。每条暂存的写入会显示一行摘要；`/skills diff <id>` 在聊天中会被截断——请在 CLI 或 `~/.hermes/pending/skills/<id>.json` 中查看完整 diff。仅当门控开启（或仍有暂存写入）时显示；搜索/安装仍仅限 CLI。 |
| `/kanban <action>` | 在聊天中操作多 profile、多项目协作看板——参数与 CLI 完全相同。该命令会绕过 agent 运行状态保护，因此 `/kanban unblock t_abc`、`/kanban comment t_abc "…"`、`/kanban list --mine`、`/kanban boards switch <slug>` 等命令均可在轮次进行中使用。`/kanban create …` 会自动让发起聊天订阅新任务的最终事件。参阅 [Kanban 斜杠命令](/user-guide/features/kanban#kanban-slash-command)。 |
| `/platform <list\|pause\|resume> [name]` | 直接在聊天中操作正在运行的 gateway 平台。`/platform list` 会显示每个 adapter 及其状态（运行中、因熔断器暂停、手动暂停）；`/platform pause <name>` 会停止向该 adapter 分发新消息，但不会卸载它；`/platform resume <name>` 会重新启用它，并在上游恢复正常后清除已触发的熔断器。 |
| `/reload-mcp`（别名：`/reload_mcp`） | 从配置重新加载 MCP 服务器。 |
| `/yolo` | 切换 YOLO 模式——跳过所有危险命令的审批提示。 |
| `/commands [page]` | 分页浏览所有命令和 skill。 |
| `/approve [session\|always]` | 批准并执行待处理的危险命令。`session` 仅在当前会话中批准；`always` 会将其加入永久允许名单。 |
| `/deny` | 拒绝待处理的危险命令。 |
| `/update` | 将 Hermes Agent 更新到最新版本。 |
| `/restart` | 等活动任务全部结束后，平滑重启 gateway。gateway 恢复在线后，会向请求者所在的聊天/线程发送确认消息。 |
| `/debug` | 上传调试报告（系统信息 + 日志）并获取可分享的链接。 |
| `/help` | 显示消息平台帮助。 |
| `/<skill-name>` | 按名称调用任意已安装的 skill。 |

## 注意事项

- `/skin`、`/snapshot`、`/reload`、`/tools`、`/toolsets`、`/browser`、`/config`、`/cron`、`/platforms`、`/paste`、`/image`、`/statusbar`、`/plugins`、`/busy`、`/indicator`、`/redraw`、`/clear`、`/history`、`/save`、`/copy`、`/handoff`、`/billing` 和 `/quit` 是**仅限 CLI** 的命令。
- `/skills` 的**搜索/浏览/安装功能仅限 CLI**；当 `skills.write_approval` 开启时，其写入审批审核子命令（`pending`、`approve`、`reject`、`diff`、`approval`）也可在消息平台中使用。`/memory` 可在**两个入口**中使用。
- `/verbose` **默认仅限 CLI**，但可以在 `config.yaml` 中设置 `display.tool_progress_command: true`，为消息平台启用此命令。启用后，它会循环切换 `display.tool_progress` 模式并保存到配置。
- `/sethome`、`/update`、`/restart`、`/approve`、`/deny`、`/topic`、`/platform` 和 `/commands` 是**仅限消息平台**的命令。
- `/status`、`/version`、`/background`、`/queue`、`/steer`、`/voice`、`/reload-mcp`、`/reload-skills`、`/rollback`、`/debug`、`/fast`、`/footer`、`/curator`、`/kanban`、`/credits`、`/suggestions`、`/blueprint`、`/learn`、`/sessions` 和 `/yolo` 可在 **CLI 和消息 gateway** 中使用。
- `/voice join`、`/voice channel` 和 `/voice leave` 仅在 Discord 上有意义。
- 在 TUI 中，`/sessions` 显示当前 TUI 进程中的实时会话。对于已保存或已关闭的对话记录，请使用 `/resume [name]` 或 `hermes --tui --resume <id-or-title>`。

## 破坏性命令的确认提示

CLI 会在运行将丢弃未保存会话状态的斜杠命令前提示确认。目前的破坏性命令包括：

| 命令 | 会销毁的内容 |
|---------|------------------|
| `/clear` | 清屏并开始新会话——当前会话 ID 和内存中的历史记录都会丢失。 |
| `/new` / `/reset` | 开始新会话（使用新会话 ID 和空历史记录）。 |
| `/undo` | 从历史记录中移除最后一轮用户/助手对话。 |
| `/exit --delete` / `/quit --delete` | 退出，**并且**永久删除当前会话的 SQLite 历史记录和磁盘中的对话记录。 |

对于这些命令，CLI 会打开一个包含三个选项的弹窗：**Approve Once**（仅本次继续）、**Always Approve**（继续执行并持久化 `approvals.destructive_slash_confirm: false`，使后续破坏性命令不再提示确认）或 **Cancel**。

**单次跳过：**追加 `now`、`--yes` 或 `-y` 可在单次调用中绕过弹窗，例如 `/reset now`、`/new --yes my-session`、`/clear -y`、`/undo -y`。这适用于弹窗无法在你的终端中正确显示的情况（例如原生 Windows PowerShell，参阅 [issue #30768](https://github.com/NousResearch/hermes-agent/issues/30768)），也适用于通过脚本操作 CLI 的情况。

在 `~/.hermes/config.yaml` 中设置 `approvals.destructive_slash_confirm: false` 可全局禁用提示；将其改回 `true` 可重新启用。相关背景见[安全——破坏性斜杠命令确认](../user-guide/security.md#dangerous-command-approval)。