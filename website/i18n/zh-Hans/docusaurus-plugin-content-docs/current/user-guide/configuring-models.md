---
sidebar_position: 3
---

# 配置模型

Hermes 使用两类模型槽位：

- **主模型** — 智能体用于思考的模型。每条用户消息、每轮工具调用循环以及每次流式响应都会经过该模型。
- **辅助模型** — 智能体交由其他较小模型处理的辅助任务，包括上下文压缩、视觉（图像分析）、网页摘要、审批评分、MCP 工具路由、会话标题生成和技能搜索。每项任务都有自己的槽位，可以单独覆盖设置。

本页介绍如何通过仪表板配置这两类模型。如果你更习惯使用配置文件或 CLI，请跳至页面底部的[其他方法](#alternative-methods)。

:::tip 最快方式：Nous Portal
[Nous Portal](/user-guide/features/tool-gateway) 通过一项订阅提供 300 多个模型。全新安装后，运行 `hermes setup --portal`，即可登录并用一条命令将 Nous 设为提供商。使用 `hermes portal info` 查看已接入的配置。

- Portal 订阅用户使用**按 token 计费的提供商时还可享受九折优惠**。
:::

:::note `model:` schema — 空字符串与映射
全新安装时，内置默认配置中的 `model: ""` 是一个空字符串哨兵值，表示“尚未配置”。首次运行 `hermes setup` 或 `hermes model` 时，该键会原地升级为映射，其中包含 `provider`、`default`、`base_url` 和 `api_mode` 子键，也就是本页以及 [`profiles.md`](./profiles.md) / [`configuration.md`](./configuration.md) 中展示的结构。如果你在 `config.yaml` 中看到空字符串，请运行 `hermes model`（或在仪表板中点击 **Change**），Hermes 会为你写入字典形式的配置。
:::

## Models 页面

打开仪表板，点击侧边栏中的 **Models**。页面分为两个区域：

1. **Model Settings** — 顶部面板，用于为各槽位分配模型。
2. **Usage analytics** — 按排名显示所选时间段内运行过会话的所有模型卡片，其中包含 token 数量、费用和能力标签。

![Models 页面概览](/img/docs/dashboard-models/overview.png)

顶部卡片就是 **Model Settings** 面板。主模型一行始终显示智能体为新会话启动时将使用的模型。点击 **Change** 打开选择器。

## 设置主模型

点击 Main model 一行中的 **Change**：

![模型选择器对话框](/img/docs/dashboard-models/picker-dialog.png)

选择器分为两列：

- **左侧** — 已认证的提供商。此处只显示你已配置的提供商（已设置 API key、已通过 OAuth 登录或已定义为自定义端点）。如果缺少某个提供商，请前往 **Keys** 添加其凭据。
- **右侧** — 所选提供商的精选模型列表。这些是 Hermes 为该提供商推荐的智能体模型，而不是原始的 `/models` 列表（例如 OpenRouter 的原始列表包含 400 多个模型，其中还有 TTS、图像生成和重排序模型）。

在筛选框中输入提供商名称、slug 或模型 ID，即可缩小范围。

选好模型后点击 **Switch**，Hermes 会将其写入 `~/.hermes/config.yaml` 的 `model` 部分。**此更改仅对新会话生效** — 已打开的聊天标签页仍会继续使用启动时的模型。如需热切换当前聊天，请在该聊天中使用 `/model` 斜杠命令。

### 会话中途切换与上下文警告

当你在**活跃会话中**切换模型时（通过 Herm TUI 模型选择器、`hermes` CLI，或 Telegram/Discord 上的 `/model`），Hermes 会估算你的**下一条消息**是否会因新模型的上下文窗口而触发**预先上下文压缩**。如果会话长度已经接近或超过该模型的压缩阈值（参见[上下文压缩](./configuration.md#context-compression)），切换结果中会附带警告；该警告与高价模型提示使用相同的 `warning_message` 路径。切换仍会立即生效；压缩会在**切换后的第一条用户消息**到来时、模型作答前执行。

:::warning 会话中途切换会重置 prompt 缓存
Prompt 缓存与处理请求的模型绑定。因此，在对话中途更换模型，无论是显式使用 `/model` 切换、触发[自动回退](./features/fallback-providers.md)，还是[凭据池](./features/credential-pools.md)轮换至其他账户，下一条消息都会按完整输入 token 价格重新读取整段对话，而不能享受缓存价格（通常可优惠约 75–90%）。在较长的会话中，这次性重新读取的成本可能远高于两个模型之间的 token 单价差异。需要时仍可切换，但最好在对话早期或刚开始新会话后进行。
:::

## 设置辅助模型

点击 **Show auxiliary** 展开 11 个任务槽位：

![展开后的辅助模型面板](/img/docs/dashboard-models/auxiliary-expanded.png)

每项辅助任务默认为 `auto`，也就是 Hermes 会先尝试用主模型完成该任务。如果此路由不可用或遇到容量类故障，`auto` 会依次尝试该任务专属的 `auxiliary.<task>.fallback_chain`、主 `fallback_providers` / `fallback_model` 链，最后再尝试 Hermes 内置的辅助模型发现链。如果你希望某项辅助任务使用成本更低或速度更快的模型，可以单独覆盖其设置。

### 常见覆盖方式

| 任务 | 何时覆盖 |
|---|---|
| **Title Gen** | 几乎总是值得覆盖。$0.10/M 的 flash 模型生成会话标题的效果不输 Opus。默认配置将其设为 OpenRouter 上的 `google/gemini-3-flash-preview`。 |
| **Vision** | 主模型不支持视觉时。可将其设为 `google/gemini-2.5-flash` 或 `gpt-4o-mini`。 |
| **Compression** | 当你只为总结上下文就消耗 Opus/M2.7 的推理 token 时。快速聊天模型能以 1/50 的成本完成这项工作。 |
| **Approval** | 用于 `approval_mode: smart` — 由快速、低成本的模型（haiku、flash、gpt-5-mini）判断是否自动批准低风险命令。没必要在这里使用昂贵模型。 |
| **Web Extract** | 当你频繁使用 `web_extract` 时。逻辑与压缩相同：摘要不需要推理模型。 |
| **Skills Hub** | `hermes skills search` 使用此槽位。通常保持 `auto` 即可。 |
| **MCP** | 用于 MCP 工具路由。通常保持 `auto` 即可。 |
| **Triage Specifier** | 为看板分类规格细化器（`hermes kanban specify`）选择模型；该功能会把粗略的一句话扩展为具体规格。成本低且能力足够的模型就很合适。 |
| **Kanban Decomposer** | 为看板任务拆解选择模型，将一个分类任务拆成由多个子任务组成的图，交给专门的 profile 处理。 |
| **Profile Describer** | 为 profile 描述生成（`hermes profile describe --auto` / 仪表板中的自动生成按钮）选择模型。这是一次简短、低成本的调用。 |
| **Curator** | 为 curator 的技能使用情况审查选择模型。该任务在推理模型上可能运行数分钟，因此改用成本更低的辅助模型通常很划算。 |

### 按任务覆盖

点击任意辅助任务行中的 **Change**。此时会打开同一个选择器，操作也相同：选择提供商和模型，然后点击 Switch。该行将不再显示 `auto (use main model)`，而会显示 `provider · model`。

### 全部重置为 auto

如果你做了过多调整，想重新开始，请点击辅助模型区域顶部的 **Reset all to auto**。所有槽位都会恢复为使用主模型。

## “Use as”快捷方式

页面上的每张模型卡片都有一个 **Use as** 下拉菜单。这是最快的设置方式：在使用分析中找到一个模型，点击 **Use as**，即可一键将其分配给主模型槽位或任意一项辅助任务：

![Use as 下拉菜单](/img/docs/dashboard-models/use-as-dropdown.png)

下拉菜单包含：

- **Main model** — 与点击主模型一行中的 Change 相同。
- **All auxiliary tasks** — 一次将该模型分配给全部 11 个辅助槽位。如果你只是希望所有辅助任务都使用低成本的 flash 模型，这会很方便。
- **各个任务选项** — Vision、Web Extract、Compression 等。每项任务当前分配的模型会标记为 `current`。

如果某张卡片上的模型当前已分配给某个槽位，它会带有 `main` 或 `aux · <task>` 标签，让你一眼看出各个历史模型目前用在哪里。

## 写入 `config.yaml` 的内容

通过仪表板保存时，Hermes 会写入 `~/.hermes/config.yaml`：

**主模型：**
```yaml
model:
  provider: openrouter
  default: anthropic/claude-opus-4.7
  base_url: ''        # cleared on provider switch
  api_mode: chat_completions
```

**辅助模型覆盖（示例 — 视觉任务使用 gemini-flash）：**
```yaml
auxiliary:
  vision:
    provider: openrouter
    model: google/gemini-2.5-flash
    base_url: ''
    api_key: ''
    timeout: 120
    extra_body: {}
    download_timeout: 30
```

**辅助模型使用 auto（默认）：**
```yaml
auxiliary:
  compression:
    provider: auto
    model: ''
    base_url: ''
    # ... other fields unchanged
```

`provider: auto` 与 `model: ''` 会让 Hermes 对该任务使用主模型；如果主路由无法处理此次辅助调用，仍会遵循回退策略。

可选的任务专属回退链位于同一项辅助任务下：

```yaml
auxiliary:
  title_generation:
    provider: auto
    model: ''
    fallback_chain:
      - provider: openrouter
        model: inclusionai/ring-2.6-1t:free
```

如果没有 `fallback_chain`，`auto` 会先使用顶层 `fallback_providers` 链，再尝试内置的辅助模型发现链。

## 何时生效？

- **CLI**（`hermes chat`）：下次运行 `hermes chat` 时。
- **Gateway**（Telegram、Discord、Slack 等）：下一个*新*会话。现有会话会继续使用原模型。如果希望强制所有会话应用更改，请重启 gateway（`hermes gateway restart`）。
- **仪表板聊天标签页**（`/chat`）：下一个新 PTY。当前打开的聊天会继续使用原模型；如需热切换，请在其中使用 `/model`。

这些更改绝不会导致运行中会话的 prompt 缓存失效。这是有意为之：在会话内更换主模型需要重置缓存（system prompt 中包含模型专属内容），因此只有在聊天中显式使用 `/model` 斜杠命令才会执行这一操作。

## 故障排查

### 选择器中显示“No authenticated providers”

Hermes 只会列出拥有有效凭据的提供商。请检查侧边栏中的 **Keys**，其中应当至少有一种凭据：API key、成功的 OAuth 登录或自定义端点 URL。如果没有你想使用的提供商，请运行 `hermes setup` 完成接入，或前往 **Keys** 添加相应环境变量。

### 运行中的聊天没有更换主模型

这是预期行为。仪表板写入的是 `config.yaml`，新会话才会读取该文件。当前打开的聊天是一个正在运行的智能体进程，会继续使用启动时的模型。请在聊天中使用 `/model <name>`，只对该会话进行热切换。

### 辅助模型覆盖“没有生效”

请检查以下三点：

1. **是否启动了新会话？** 现有聊天不会重新读取配置。
2. **`provider` 是否设为 `auto` 以外的值？** 如果该字段显示 `auto`，任务仍在使用主模型。请点击 **Change** 并选择一个实际的提供商。
3. **提供商是否已认证？** 如果你为某项任务分配了 `minimax`，却没有 MiniMax API key，该任务会回退到 openrouter 默认模型，并在 `agent.log` 中记录警告。

### 我选择了一个模型，但 Hermes 替我切换了提供商

在 OpenRouter（或其他聚合器）上，未限定提供商的模型名称会先在聚合器内部解析。因此，OpenRouter 上的 `claude-sonnet-4` 会解析为 `anthropic/claude-sonnet-4.6`，继续使用你的 OpenRouter 认证；但如果在 Anthropic 原生认证下输入 `claude-sonnet-4`，则会保留为 `claude-sonnet-4-6`。如果发现提供商意外切换，请确认当前提供商是否符合预期；选择器始终会在对话框顶部显示当前主模型。

## 其他方法 {#alternative-methods}

### CLI 斜杠命令

在任意 `hermes chat` 会话中：

```
/model gpt-5.4 --provider openrouter             # session-only
/model gpt-5.4 --provider openrouter --global    # also persists to config.yaml
```

`--global` 的作用与仪表板中的 **Change** 按钮相同，并且还会原地切换正在运行的会话。

### 自定义别名

你可以为常用模型定义自己的短名称，然后在 CLI 或任意消息平台中使用 `/model <alias>`。有两种等效格式，可按你的工作流任选一种。

**标准格式（顶层 `model_aliases:`）** — 可以完整控制 provider 和 base_url：

```yaml
# ~/.hermes/config.yaml
model_aliases:
  fav:
    model: claude-sonnet-4.6
    provider: anthropic
  grok:
    model: grok-4
    provider: x-ai
```

**短字符串格式（`model.aliases.<name>: provider/model`）** — 更适合在 shell 中使用，因为 `hermes config set` 只能写入标量值，但这种格式无法携带自定义 `base_url`：

```bash
hermes config set model.aliases.fav anthropic/claude-opus-4.6
hermes config set model.aliases.grok x-ai/grok-4
```

两种方式使用同一个加载器（`hermes_cli/model_switch.py`）。如果 `model_aliases:` 和 `model.aliases:` 中存在同名条目，以 `model_aliases:` 中的条目为准。

之后即可在聊天中使用 `/model fav` 或 `/model grok`。用户别名会覆盖内置短名称（`sonnet`、`kimi`、`opus` 等）。完整说明请参阅[自定义模型别名](/reference/slash-commands#custom-model-aliases)。

### `hermes model` 子命令

```bash
hermes model            # Interactive provider + model picker (the canonical way to switch defaults)
```

`hermes model` 会引导你选择提供商并完成认证（OAuth 流程会打开浏览器；使用 API key 的提供商会提示你输入密钥），然后从该提供商的精选目录中选择具体模型。所选配置会写入 `~/.hermes/config.yaml` 中的 `model.provider` 和 `model.model`。

如需在不启动选择器的情况下列出提供商和模型，请使用仪表板或下方的 REST 端点。如需查看 CLI 此刻实际会使用的配置，请运行 `hermes config show | grep '^model\.'` 和 `hermes status`。

### 直接编辑配置

编辑 `~/.hermes/config.yaml`，然后重启读取该文件的进程。完整 schema 请参阅[配置参考](./configuration.md)。

### REST API

仪表板使用三个端点，也可用于脚本：

```bash
# List authenticated providers + curated model lists
curl -H "X-Hermes-Session-Token: $TOKEN" http://localhost:PORT/api/model/options

# Read current main + auxiliary assignments
curl -H "X-Hermes-Session-Token: $TOKEN" http://localhost:PORT/api/model/auxiliary

# Set the main model
curl -X POST -H "Content-Type: application/json" -H "X-Hermes-Session-Token: $TOKEN" \
  -d '{"scope":"main","provider":"openrouter","model":"anthropic/claude-opus-4.7"}' \
  http://localhost:PORT/api/model/set

# Override a single auxiliary task
curl -X POST -H "Content-Type: application/json" -H "X-Hermes-Session-Token: $TOKEN" \
  -d '{"scope":"auxiliary","task":"vision","provider":"openrouter","model":"google/gemini-2.5-flash"}' \
  http://localhost:PORT/api/model/set

# Assign one model to every auxiliary task
curl -X POST -H "Content-Type: application/json" -H "X-Hermes-Session-Token: $TOKEN" \
  -d '{"scope":"auxiliary","task":"","provider":"openrouter","model":"google/gemini-2.5-flash"}' \
  http://localhost:PORT/api/model/set

# Reset all auxiliary tasks to auto
curl -X POST -H "Content-Type: application/json" -H "X-Hermes-Session-Token: $TOKEN" \
  -d '{"scope":"auxiliary","task":"__reset__","provider":"","model":""}' \
  http://localhost:PORT/api/model/set
```

Session token 会在启动时注入仪表板 HTML，并在每次服务器重启后轮换。如果你要针对正在运行的仪表板编写脚本，可以从浏览器开发者工具中获取它（`window.__HERMES_SESSION_TOKEN__`）。