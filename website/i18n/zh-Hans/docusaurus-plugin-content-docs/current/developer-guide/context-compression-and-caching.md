# 上下文压缩与缓存

Hermes Agent 使用双重压缩系统和 Anthropic 提示词缓存，在长对话中高效管理上下文窗口用量。

源文件：`agent/context_engine.py`（ABC）、`agent/context_compressor.py`（默认引擎）、
`agent/prompt_caching.py`、`gateway/run.py`（会话卫生）、`run_agent.py`（搜索 `_compress_context`）

## 可插拔上下文引擎

上下文管理基于 `ContextEngine` ABC（`agent/context_engine.py`）构建。内置的 `ContextCompressor` 是默认实现，但插件可使用替代引擎（例如无损上下文管理）替换它。

```yaml
context:
  engine: "compressor"    # default — built-in lossy summarization
  engine: "lcm"           # example — plugin providing lossless context
```

引擎负责：
- 决定何时应触发压缩（`should_compress()`）
- 执行压缩（`compress()`）
- 可选地暴露 agent 可调用的工具（例如 `lcm_grep`）
- 跟踪 API 响应中的 token 用量

通过 `config.yaml` 中的 `context.engine` 由配置驱动进行选择。解析顺序为：
1. 检查 `plugins/context_engine/<name>/` 目录
2. 检查通用插件系统（`register_context_engine()`）
3. 回退到内置 `ContextCompressor`

插件引擎**绝不会自动激活**——用户必须显式将 `context.engine` 设为该插件的名称。默认的 `"compressor"` 始终使用内置实现。

通过 `hermes plugins` → Provider Plugins → Context Engine 配置，或直接编辑 `config.yaml`。

有关构建上下文引擎插件，请参阅 [上下文引擎插件](/developer-guide/context-engine-plugin)。

## 双重压缩系统

Hermes 具有两个独立运行的压缩层：

```
                     ┌──────────────────────────┐
  Incoming message   │   Gateway Session Hygiene │  Fires at 85% of context
  ─────────────────► │   (pre-agent, rough est.) │  Safety net for large sessions
                     └─────────────┬────────────┘
                                   │
                                   ▼
                     ┌──────────────────────────┐
                     │   Agent ContextCompressor │  Fires at 50% of context (default)
                     │   (in-loop, real tokens)  │  Normal context management
                     └──────────────────────────┘
```

### 1. Gateway 会话卫生（85% 阈值）

位于 `gateway/run.py`（搜索 `Session hygiene: auto-compress`）。这是一个**安全网**，会在 agent 处理消息前运行。当会话在两轮之间增长过大时（例如 Telegram/Discord 中的隔夜累积），它可防止 API 失败。

- **阈值**：固定为模型上下文长度的 85%
- **Token 来源**：优先采用上一轮 API 实际报告的 token；回退到基于字符的粗略估算（`estimate_messages_tokens_rough`）
- **触发条件**：仅当 `len(history) >= 4` 且压缩已启用时
- **目的**：捕获逃过 agent 自身压缩器的会话

Gateway 卫生阈值有意高于 agent 压缩器。将其设为 50%（与 agent 相同）会使较长的 gateway 会话每一轮都过早压缩。

### 2. Agent ContextCompressor（50% 阈值，可配置）

位于 `agent/context_compressor.py`。这是**主要压缩系统**，在 agent 的工具循环内运行，能够访问准确的、由 API 报告的 token 计数。

## 配置

所有压缩设置均从 `config.yaml` 的 `compression` 键读取：

```yaml
compression:
  enabled: true              # Enable/disable compression (default: true)
  threshold: 0.50            # Fraction of context window (default: 0.50 = 50%)
  # model_thresholds:        # Per-model threshold overrides (substring match,
  #   "glm-5.2": 0.40        # longest key wins). See "Per-model threshold
  #   "claude-sonnet": 0.35  # overrides" below.
  target_ratio: 0.20         # How much of threshold to keep as tail (default: 0.20)
  protect_last_n: 20         # Minimum protected tail messages (default: 20)
  min_tail_user_messages: 1  # Real user messages guaranteed in the tail (default: 1)
  codex_gpt55_autoraise: true  # gpt-5.5 on Codex OAuth: raise trigger to 85% (default: true)
  codex_gpt55_autoraise_notice: true  # Show the one-time autoraise notice (default: true)
  codex_app_server_auto: native  # native|hermes|off for Codex app-server thread compaction

# Summarization model/provider configured under auxiliary:
auxiliary:
  compression:
    model: null              # Override model for summaries (default: auto-detect)
    provider: auto           # Provider: "auto", "openrouter", "nous", "main", etc.
    base_url: null           # Custom OpenAI-compatible endpoint
```

### 参数详情

| 参数 | 默认值 | 范围 | 描述 |
|-----------|---------|-------|-------------|
| `threshold` | `0.50` | 0.0-1.0 | 当提示词 token ≥ `threshold × context_length` 时触发压缩 |
| `model_thresholds` | `{}` | map | `threshold` 的按模型覆盖值。键会针对模型名进行子串匹配（最长匹配胜出）。小上下文下限仍会在其基础上应用（见下文） |
| `target_ratio` | `0.20` | 0.10-0.80 | 控制尾部保护 token 预算：`threshold_tokens × target_ratio` |
| `protect_last_n` | `20` | ≥1 | 始终保留的最近消息最小数量 |
| `min_tail_user_messages` | `1` | ≥1 | 保证在未压缩尾部中存活的真实（可操作）用户消息最小数量。`1` = 现有的单个最后用户锚点（保持行为不变的默认值）。提高到例如 `3`，即使庞大的工具输出填满尾部 token 预算，也会逐字保留最近 3 个真实用户轮次。空白平台回显、压缩交接和合成续接行永远不计入 N。此保证优先于尾部 token 预算——当锚点将切分点拉回时，尾部可能超出预算 |
| `protect_first_n` | `3` | （硬编码） | 系统提示词 + 首次交换始终保留 |
| `idle_compact_after_seconds` | `0` | ≥0 秒 | 选择启用：会话闲置这么多秒后恢复时立即压缩（0 = 禁用）。上下文 ≤ `threshold × target_ratio` 时跳过；遵守冷却、反抖动和锁定保护 |
| `codex_gpt55_autoraise` | `true` | bool | 对 ChatGPT Codex OAuth 路由上的 gpt-5.5 将触发阈值提高到 85%（见下文）。设为 `false` 可保留全局 `threshold` |
| `codex_gpt55_autoraise_notice` | `true` | bool | 显示一次性 Codex gpt-5.5 自动提高通知。设为 `false` 可保留 85% 自动提高但抑制横幅 |
| `codex_app_server_auto` | `native` | `native`、`hermes`、`off` | Codex app-server 会话的线程压缩模式（见下文） |

### 按模型阈值覆盖

`compression.model_thresholds` 允许根据活动模型在不同点触发压缩——当你在上下文窗口差异很大的模型间切换时很有用（例如，1M 上下文模型可更晚压缩，而 128K 模型应更早压缩）：

```yaml
compression:
  threshold: 0.50
  model_thresholds:
    "glm-5.2": 0.40
    "glm-5.2-1M": 0.25
    "claude-sonnet": 0.35
```

解析规则：

- 键会针对模型名进行**子串匹配**；**最长匹配键胜出**（对模型 `glm-5.2-1M`，`glm-5.2-1M` 胜过 `glm-5.2`）。
- 未匹配任何键（或映射为空）时，应用全局 `threshold`。
- 每次 `/model` 切换时都会重新解析覆盖值；切换到没有匹配键的模型会回退到全局 `threshold`。
- **小上下文下限仍在覆盖值基础上适用**（仅提高）：上下文窗口小于 512K 的模型下限为 `0.75`，因此低于下限的覆盖值会提高至 `0.75`，而高于下限的覆盖值（例如 `0.80`）会胜出。

插件上下文引擎可通过 `from agent.context_compressor import resolve_model_threshold` 复用相同解析逻辑；覆盖 `update_model()` 的引擎拥有自己的压缩策略，可能忽略该映射。

### Codex gpt-5.5 阈值自动提高

ChatGPT Codex OAuth 后端将 gpt-5.5 硬性限制为 **272K** 上下文窗口（同一 slug 在 OpenAI 直接 API 和 OpenRouter 上提供 1.05M，在 GitHub Copilot 上提供 400K）。使用默认的 50% 触发点时，压缩将在约 136K 触发——仅使用模型实际可用窗口的一半。活动路由为 Codex OAuth（`provider: openai-codex`）且模型为 gpt-5.5 时，Hermes 会将触发点提高到 **85%**（约 231K），并显示附带退出命令的通知。该通知每个 profile 仅显示一次——`$HERMES_HOME` 下的标记（`.codex_gpt55_autoraise_notice`）会记录其已运行，因此重复的 agent/会话初始化（例如每条传入 gateway 消息）不会再次发出它；若提高后的阈值后来改变，则会再次通知一次。仅此精确路由受影响；任何其他 provider 上的 gpt-5.5 均保留你的全局 `threshold`。要改回全局值：

```bash
hermes config set compression.codex_gpt55_autoraise false
```

要保留 85% 自动提高、但只隐藏一次性通知：

```bash
hermes config set compression.codex_gpt55_autoraise_notice false
```

### Codex app-server 线程压缩

Codex app-server 会话（`api_mode: codex_app_server`——codex CLI/agent 运行时）与其他所有路由不同：codex agent 拥有后备线程上下文，因此 Hermes 的辅助摘要器无法缩小它——重写本地转录镜像会使实际线程继续无界增长，直至硬性上下文重置。对于此运行时，压缩改为通过 app-server 自己的机制：

- 手动压缩（`/compress`）会请求 app-server 压缩线程（`thread/compact/start`），并等待压缩轮次完成。
- 自动压缩由 `compression.codex_app_server_auto` 控制：默认 `native` 让 app-server 决定何时压缩，而 Hermes 记录产生的压缩事件（压缩计数器、会话事件）。设置 `hermes` 可让 Hermes 的压缩阈值发起 app-server 压缩，设置 `off` 则完全禁用由 Hermes 发起的自动压缩（codex 仍可能原生压缩）。

Hermes 的本地转录在此运行时绝不会被重写——state.db 记录压缩边界，而可见转录保持完整。所有其他路由（包括 Codex OAuth 聊天会话）继续使用 Hermes 的摘要压缩器。

### 计算值（默认设置下的 200K 上下文模型）

```
context_length       = 200,000
threshold_tokens     = 200,000 × 0.50 = 100,000
tail_token_budget    = 100,000 × 0.20 = 20,000
max_summary_tokens   = min(200,000 × 0.05, 12,000) = 10,000
```

:::note 阈值由主模型的上下文窗口决定
`threshold_tokens` 始终为 `threshold × context_length`，其中 `context_length` 是**主 agent 模型**的上下文窗口——绝非辅助/摘要模型的。对于默认 `0.50` 下的 262,144-token 模型，阈值为 `262,144 × 0.50 = 131,072`。该数值接近常见的“128K 上下文”仅是该百分比的巧合，并不表示辅助模型的窗口是触发器。辅助模型的上下文窗口是另一项考量——请参阅下方“摘要模型上下文长度”警告，了解它如何影响能否生成摘要，而非何时触发压缩。
:::

## 压缩算法

`ContextCompressor.compress()` 方法遵循四阶段算法：

### 阶段 1：清除旧工具结果（廉价，无 LLM 调用）

保护尾部之外的旧工具结果（>200 个字符）会被替换为：
```
[Old tool output cleared to save context space]
```

这是一个廉价的预处理，可从冗长的工具输出（文件内容、终端输出、搜索结果）中节省大量 token。

### 阶段 2：确定边界

```
┌─────────────────────────────────────────────────────────────┐
│  Message list                                               │
│                                                             │
│  [0..2]  ← protect_first_n (system + first exchange)        │
│  [3..N]  ← middle turns → SUMMARIZED                        │
│  [N..end] ← tail (by token budget OR protect_last_n)        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

尾部保护基于**token 预算**：从末尾向后遍历，累积 token 直至耗尽预算。如果预算所保护的消息少于固定 `protect_last_n` 数量，则回退至固定数量。

边界会对齐以避免拆分 tool_call/tool_result 组。`_align_boundary_backward()` 方法会越过连续工具结果以找到父 assistant 消息，从而保持组完整。

### 阶段 3：生成结构化摘要

:::warning 摘要模型上下文长度
摘要模型必须具有**至少与主 agent 模型一样大的**上下文窗口。整个中间部分会在单次 `call_llm(task="compression")` 调用中发送给摘要模型。如果摘要模型上下文较小，API 将返回上下文长度错误——`_generate_summary()` 会捕获它、记录警告并返回 `None`。随后压缩器会在**没有摘要的情况下丢弃中间轮次**，静默丢失对话上下文。这是压缩质量下降最常见的原因。
:::

中间轮次使用辅助 LLM 通过结构化模板进行摘要：

```
## Goal
[What the user is trying to accomplish]

## Constraints & Preferences
[User preferences, coding style, constraints, important decisions]

## Progress
### Done
[Completed work — specific file paths, commands run, results]
### In Progress
[Work currently underway]
### Blocked
[Any blockers or issues encountered]

## Key Decisions
[Important technical decisions and why]

## Relevant Files
[Files read, modified, or created — with brief note on each]

## Next Steps
[What needs to happen next]

## Critical Context
[Specific values, error messages, configuration details]
```

摘要预算会随被压缩内容的量缩放：
- 公式：`content_tokens × 0.20`（`_SUMMARY_RATIO` 常量）
- 最小值：2,000 token
- 最大值：`min(context_length × 0.05, 12,000)` token

### 阶段 4：组装压缩后的消息

压缩后的消息列表为：
1. 头部消息（首次压缩时在系统提示词中追加一条注释）
2. 摘要消息（选择角色以避免连续相同角色违规）
3. 尾部消息（未修改）

孤立的 tool_call/tool_result 对由 `_sanitize_tool_pairs()` 清理：
- 引用已移除调用的工具结果 → 移除
- 其结果已被移除的工具调用 → 注入存根结果

### 迭代式重新压缩

在后续压缩中，先前的摘要会连同指令一起传给 LLM，要求其**更新**摘要而非从头开始摘要。这会在多次压缩中保留信息——项目从“进行中”移到“已完成”、添加新进展、删除过时信息。

压缩器实例上的 `_previous_summary` 字段为此目的存储上一次摘要文本。

## 压缩前后示例

### 压缩前（45 条消息，约 95K token）

```
[0] system:    "You are a helpful assistant..." (system prompt)
[1] user:      "Help me set up a FastAPI project"
[2] assistant: <tool_call> terminal: mkdir project </tool_call>
[3] tool:      "directory created"
[4] assistant: <tool_call> write_file: main.py </tool_call>
[5] tool:      "file written (2.3KB)"
    ... 30 more turns of file editing, testing, debugging ...
[38] assistant: <tool_call> terminal: pytest </tool_call>
[39] tool:      "8 passed, 2 failed\n..."  (5KB output)
[40] user:      "Fix the failing tests"
[41] assistant: <tool_call> read_file: tests/test_api.py </tool_call>
[42] tool:      "import pytest\n..."  (3KB)
[43] assistant: "I see the issue with the test fixtures..."
[44] user:      "Great, also add error handling"
```

### 压缩后（25 条消息，约 45K token）

```
[0] system:    "You are a helpful assistant...
               [Note: Some earlier conversation turns have been compacted...]"
[1] user:      "Help me set up a FastAPI project"
[2] assistant: "[CONTEXT COMPACTION] Earlier turns were compacted...

               ## Goal
               Set up a FastAPI project with tests and error handling

               ## Progress
               ### Done
               - Created project structure: main.py, tests/, requirements.txt
               - Implemented 5 API endpoints in main.py
               - Wrote 10 test cases in tests/test_api.py
               - 8/10 tests passing

               ### In Progress
               - Fixing 2 failing tests (test_create_user, test_delete_user)

               ## Relevant Files
               - main.py — FastAPI app with 5 endpoints
               - tests/test_api.py — 10 test cases
               - requirements.txt — fastapi, pytest, httpx

               ## Next Steps
               - Fix failing test fixtures
               - Add error handling"
[3] user:      "Fix the failing tests"
[4] assistant: <tool_call> read_file: tests/test_api.py </tool_call>
[5] tool:      "import pytest\n..."
[6] assistant: "I see the issue with the test fixtures..."
[7] user:      "Great, also add error handling"
```

## 提示词缓存（Anthropic）

来源：`agent/prompt_caching.py`

通过缓存对话前缀，多轮对话中的输入 token 成本可降低约 75%。使用 Anthropic 的 `cache_control` 断点。

### 策略：system_and_3

Anthropic 每个请求最多允许 4 个 `cache_control` 断点。Hermes 使用 “system_and_3” 策略：

```
Breakpoint 1: System prompt           (stable across all turns)
Breakpoint 2: 3rd-to-last non-system message  ─┐
Breakpoint 3: 2nd-to-last non-system message   ├─ Rolling window
Breakpoint 4: Last non-system message          ─┘
```

### 工作方式

`apply_anthropic_cache_control()` 会深度复制消息并注入 `cache_control` 标记：

```python
# Cache marker format
marker = {"type": "ephemeral"}
# Or for 1-hour TTL:
marker = {"type": "ephemeral", "ttl": "1h"}
```

标记会根据内容类型以不同方式应用：

| 内容类型 | 标记位置 |
|-------------|-------------------|
| 字符串内容 | 转换为 `[{"type": "text", "text": ..., "cache_control": ...}]` |
| 列表内容 | 添加到最后一个元素的字典 |
| None/空 | 添加为 `msg["cache_control"]` |
| 工具消息 | 添加为 `msg["cache_control"]`（仅原生 Anthropic） |

### 缓存感知设计模式

1. **稳定的系统提示词**：系统提示词是断点 1，并在所有轮次中缓存。避免在对话中途修改它（压缩仅在首次压缩时追加一条注释）。

2. **消息顺序很重要**：缓存命中要求前缀匹配。在中间添加或移除消息会使其后所有内容的缓存失效。

3. **压缩与缓存的交互**：压缩后，压缩区域的缓存失效，但系统提示词缓存仍然保留。滚动 3 消息窗口会在 1–2 轮内重新建立缓存。

4. **TTL 选择**：默认值为 `5m`（5 分钟）。在用户轮次之间会休息的长时间会话中使用 `1h`。

5. **模型身份是缓存键的一部分**：提供商侧缓存以处理请求的模型（以及帐户/API 密钥）为范围。任何对话中途的模型变更——显式 `/model` 切换、主模型回退，或凭据池轮换到不同帐户——都意味着下一次请求将获得零缓存命中，并以未折扣的输入价格重新读取完整对话。这是提供商缓存工作方式固有的限制，并非 Hermes 可以避免；因此 `/model`、回退 provider 和凭据池的面向用户文档均包含成本警告。不要添加在会话中静默交换模型或凭据的功能。

### 启用提示词缓存

满足以下条件时，提示词缓存会自动启用：
- 模型是 Anthropic Claude 模型（通过模型名称检测）
- provider 支持 `cache_control`（原生 Anthropic API 或 OpenRouter）

```yaml
# config.yaml — TTL is configurable (must be "5m" or "1h")
prompt_caching:
  cache_ttl: "5m"
```

CLI 在启动时显示缓存状态：
```
💾 Prompt caching: ENABLED (Claude via OpenRouter, 5m TTL)
```

## 上下文压力警告

中间上下文压力警告已被移除（请参阅 `run_agent.py` 中的迭代预算块，其中注明：“No intermediate pressure warnings — they caused models to 'give up' prematurely on complex tasks”）。当提示词 token 达到配置的 `compression.threshold`（默认 50%）时压缩会触发，之前没有警告步骤；gateway 会话卫生作为次级安全网，在模型上下文窗口的 85% 时触发。
