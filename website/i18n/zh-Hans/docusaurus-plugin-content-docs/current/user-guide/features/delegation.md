---
sidebar_position: 7
title: "子智能体委派"
description: "使用 delegate_task 为并行工作流生成隔离的子智能体"
---

# 子智能体委派

`delegate_task` 工具会生成具有隔离上下文、继承的工具访问权限和各自终端会话的子 AIAgent 实例。每个子智能体获得全新的对话并独立工作——只有其最终摘要会进入父智能体的上下文。

顶层模型调用会自动在后台运行。Hermes 会立即返回一个句柄，以便对话继续，然后将结果作为新消息发回。编排者子智能体会等待自己的工作线程，以便在返回前综合其结果。

## 单个任务

```python
delegate_task(
    goal="Debug why tests fail",
    context="Error: assertion in test_foo.py line 42"
)
```

## 并行批处理

默认最多 3 个并发子智能体（可配置，无硬性上限）：

```python
delegate_task(tasks=[
    {"goal": "Research topic A", "context": "Focus on recent primary sources"},
    {"goal": "Research topic B", "context": "Compare the leading explanations"},
    {"goal": "Fix the build", "context": "Project root: /home/user/project"}
])
```

## 子智能体上下文如何工作

:::warning 关键：子智能体一无所知
子智能体以**完全全新的对话**开始。它们对父智能体的对话历史、先前的工具调用或委派前讨论的任何内容毫无了解。子智能体唯一的上下文来自父智能体调用 `delegate_task` 时填入的 `goal` 和 `context` 字段。
:::

这意味着父智能体必须在调用中传递子智能体需要的**一切**：

```python
# BAD - subagent has no idea what "the error" is
delegate_task(goal="Fix the error")

# GOOD - subagent has all context it needs
delegate_task(
    goal="Fix the TypeError in api/handlers.py",
    context="""The file api/handlers.py has a TypeError on line 47:
    'NoneType' object has no attribute 'get'.
    The function process_request() receives a dict from parse_body(),
    but parse_body() returns None when Content-Type is missing.
    The project is at /home/user/myproject and uses Python 3.11."""
)
```

子智能体会收到一个根据你的目标和上下文构建的聚焦系统提示词，指示其完成任务并提供关于所做工作、发现内容、修改的文件和遇到问题的结构化摘要。

## 实际示例

### 并行研究

同时研究多个主题并收集摘要：

```python
delegate_task(tasks=[
    {
        "goal": "Research the current state of WebAssembly in 2025",
        "context": "Focus on: browser support, non-browser runtimes, language support"
    },
    {
        "goal": "Research the current state of RISC-V adoption in 2025",
        "context": "Focus on: server chips, embedded systems, software ecosystem"
    },
    {
        "goal": "Research quantum computing progress in 2025",
        "context": "Focus on: error correction breakthroughs, practical applications, key players"
    }
])
```

### 代码审查 + 修复

将审查并修复工作流委派给一个全新的上下文：

```python
delegate_task(
    goal="Review the authentication module for security issues and fix any found",
    context="""Project at /home/user/webapp.
    Auth module files: src/auth/login.py, src/auth/jwt.py, src/auth/middleware.py.
    The project uses Flask, PyJWT, and bcrypt.
    Focus on: SQL injection, JWT validation, password handling, session management.
    Fix any issues found and run the test suite (pytest tests/auth/)."""
)
```

### 多文件重构

委派会淹没父智能体上下文的大型重构任务：

```python
delegate_task(
    goal="Refactor all Python files in src/ to replace print() with proper logging",
    context="""Project at /home/user/myproject.
    Use the 'logging' module with logger = logging.getLogger(__name__).
    Replace print() calls with appropriate log levels:
    - print(f"Error: ...") -> logger.error(...)
    - print(f"Warning: ...") -> logger.warning(...)
    - print(f"Debug: ...") -> logger.debug(...)
    - Other prints -> logger.info(...)
    Don't change print() in test files or CLI output.
    Run pytest after to verify nothing broke."""
)
```

## 批处理模式详情

当顶层智能体提供 `tasks` 数组时，Hermes 会返回一个后台句柄，并行运行子智能体，并在每个子智能体完成后发布一个汇总结果。编排者子智能体会在当前轮次中等待自己的批次，以便综合结果。

- **最大并发数：** 默认 3 个任务（可通过 `delegation.max_concurrent_children` 或 `DELEGATION_MAX_CONCURRENT_CHILDREN` 环境变量配置；下限为 1，没有硬性上限）。超过限制的批次会返回工具错误，而非被静默截断。
- **线程池：** 使用 `ThreadPoolExecutor`，以配置的并发限制作为最大工作线程数。
- **进度显示：** 在 CLI 模式下，树形视图会实时显示每个子智能体的工具调用以及每个任务的完成行。在网关模式下，进度会被批量处理并中继到父智能体的进度回调。
- **结果排序：** 无论完成顺序如何，结果均按任务索引排序，以匹配输入顺序。
- **取消：** 后续消息不会取消顶层后台批次。`/stop` 或关闭/重置所属会话会取消其活跃子智能体。同步编排者子智能体仍遵循其父智能体的中断状态。

来自编排者的同步单任务委派会直接运行，无需线程池开销。

### 持久化后台完成事件

后台委派完成后，Hermes 会在将完成事件发布到常规新轮次队列前，将它存储在活跃 profile 的 `state.db` 中。如果 Hermes 在完成后、交付前重启，待处理事件会被恢复，并通过相同的所有权检查进行路由。竞争的消费者使用持久化声明，因此只有成功接受合成轮次的消费者会确认交付；失败的尝试会释放声明以供重试。

这不会在崩溃后恢复子智能体的执行。当其所属进程在子智能体仍运行时消失，委派会被记录为 `unknown`，因为 Hermes 无法证明其外部副作用是否发生。待处理和已交付记录均有边界，并且按 profile 隔离。

## 模型覆盖

你可以通过 `config.yaml` 为子智能体配置不同的模型——这对于将简单任务委派给更便宜、更快的模型很有用：

```yaml
# In ~/.hermes/config.yaml
delegation:
  model: "google/gemini-flash-2.0"    # Cheaper model for subagents
  provider: "openrouter"              # Optional: route subagents to a different provider
```

如果省略，子智能体使用与父智能体相同的模型。

## 继承的工具访问权限

`delegate_task` 不接受面向模型的 `toolsets` 参数。每个子智能体继承父智能体已启用的工具集，因此模型无法向子智能体授予父智能体本身不具备的能力。如果委派工作需要额外能力，请在开始对话前配置父智能体的工具。

即使父智能体拥有，某些工具也会对子智能体屏蔽：
- `delegation` — 对叶子子智能体（默认）屏蔽。由 `role="orchestrator"` 子智能体保留，受 `max_spawn_depth` 限制——参见下方的[深度限制和嵌套编排](#depth-limit-and-nested-orchestration)。
- `clarify` — 子智能体无法与用户交互。
- `memory` — 不写入共享的持久内存。
- `code_execution` — 子智能体应逐步推理。

## 最大迭代次数

每个子智能体有一个迭代限制（默认：50），它控制能够进行多少轮工具调用：

```python
delegate_task(
    goal="Quick file check",
    context="Check if /etc/nginx/nginx.conf exists and print its first 10 lines",
    max_iterations=10  # Simple task, don't need many turns
)
```

## 子智能体超时

默认情况下，子智能体**没有挂钟时间超时**。子智能体只会因其实际执行内容而失败——API 错误、工具错误或耗尽迭代预算——绝不会因委派层级的秒表而失败。早期版本提供了硬性上限（300 秒，之后为 600 秒），这会在合法的繁忙子智能体执行任务中途将它们杀死：深度代码审查、大型研究扇出和慢速推理模型在持续稳定推进时经常需要超过 10 分钟。

真正卡住的子智能体仍会被检测：当子智能体没有进展（没有 API 调用、没有工具启动）时，心跳陈旧监视器会停止刷新父智能体的活动，使网关不活动超时在真正卡住的工作者上触发。

如果你仍然想要硬性上限（例如，对无人值守的 cron 驱动委派进行成本控制），可以按安装实例选择启用：

```yaml
delegation:
  child_timeout_seconds: 0     # default: 0 = no timeout
  # child_timeout_seconds: 1800  # opt-in hard cap (floor 30s)
```

正值会对每个子智能体实施硬性挂钟时间限制；`0` 或负值会禁用它。

:::tip 零调用超时的诊断转储
配置硬性上限时，如果子智能体在**零次** API 调用后超时（通常是 provider 不可达、认证失败或工具模式被拒绝），`delegate_task` 会将结构化诊断写入 `~/.hermes/logs/subagent-timeout-<session>-<timestamp>.log`，其中包含子智能体的配置快照、凭据解析跟踪和任何早期错误消息。这比之前的静默超时更容易找出根因。
:::

## 监控运行中的子智能体（`/agents`）

TUI 附带一个 `/agents` 叠加层（别名 `/tasks`），将递归 `delegate_task` 扇出变成一等审计界面：

- 按父级分组的运行中和最近完成的子智能体实时树形视图。
- 每个分支的成本、token 和触及文件汇总。
- 终止和暂停控制——无需中断其兄弟智能体，即可在中途取消特定子智能体。
- 事后审查：即使子智能体已返回父智能体，也可逐轮查看其历史记录。

经典 CLI 只将 `/agents` 打印为文本摘要；TUI 才是这个叠加层的亮点。参见 [TUI — Slash commands](/user-guide/tui#slash-commands)。

## 实时记录

每次 `delegate_task` 调度也会为每个任务创建一个**只追加、可供人类阅读的日志**，这样你（或父智能体）可以实时观察子智能体的工作，而非等待汇总摘要：

```
<hermes_home>/cache/delegation/live/<delegation_id>/task-<n>.log
```

调度响应将路径作为 `live_transcripts` 返回，并且这些文件会在调度时预先创建，因此可立即使用：

```bash
tail -f ~/.hermes/cache/delegation/live/deleg_ab12cd34/task-0.log
```

每一行都有时间戳，并显示子智能体的 assistant 文本、思考片段、工具调用（`-> tool_name({args})`）、工具结果和最终状态标记。同一目录中的 `manifest.json` 描述批次（目标、任务数、每个任务的状态）。日志会在完成后保留——除摘要外，它们还兼作完整保真度的操作记录——并且超过 7 天的目录会在新调度时自动清理。由于它们位于 `cache/delegation` 下，也可从远程终端后端（Docker/Modal/SSH）读取。

## 深度限制和嵌套编排

默认情况下，委派是**扁平的**：父级（深度 0）生成子级（深度 1），而这些子级无法进一步委派。这能防止失控的递归委派。

对于多阶段工作流（研究 → 综合，或对多个子问题进行并行编排），父级可生成**编排者**子级，它们*可以*委派自己的工作者：

```python
delegate_task(
    goal="Survey three code review approaches and recommend one",
    role="orchestrator",  # Allows this child to spawn its own workers
    context="...",
)
```

- `role="leaf"`（默认）：子级不能进一步委派——与扁平委派行为相同。
- `role="orchestrator"`：子级保留 `delegation` 工具集。它受 `delegation.max_spawn_depth` 控制（默认 **1** = 扁平，因此在默认值下 `role="orchestrator"` 无效）。将 `max_spawn_depth` 提升至 2，允许编排者子级生成叶子孙级；3+ 则允许更深的树。没有上限——成本才是实际限制。
- `delegation.orchestrator_enabled: false`：全局终止开关，不论 `role` 参数如何，都会强制每个子级成为 `leaf`。

**成本警告：** 若 `max_spawn_depth: 3` 且 `max_concurrent_children: 3`，该树可达到 3×3×3 = 27 个并发叶子智能体。每增加一层都会使开销倍增——请有意地提高 `max_spawn_depth`。

## 生命周期和持久性

:::warning 后台完成持久性不是持久执行
在会话支持稍后交付时，顶层面向模型的 `delegate_task` 调用会自动在后台运行。Hermes 会立即返回一个句柄，结果会在子级或批次完成后重新进入对话。编排者子智能体在当前轮次中等待其工作者，因为它们必须在返回前综合结果。无状态请求/响应端点无法稍后交付分离结果时，会回退到同步执行。

- 正常的后续消息不会取消后台子级。`/stop` 会取消运行中的后台委派，关闭或重置所属会话会丢弃其活跃子级。
- 显式关闭/重置会话会中断该会话的后台子级。关闭网关拥有的会话的 TUI 查看器不会杀死网关的工作。
- Hermes 进程重启**不会**恢复运行中的子级。其尝试会成为 `unknown`，因为 Hermes 无法证明其发生了哪些外部副作用。
- 如果子级在重启前完成、但其结果尚未交付，则会恢复该事件，并通过所属会话的正常检查重新路由。
- 被取消的子级返回结构化结果（`status="interrupted"`、`exit_reason="interrupted"`），但由于父级同样被中断，该结果通常不会进入用户可见的回复。

对于必须在会话关闭或进程重启后存活的**持久执行**，请使用：

- `cronjob`（action=`create`）——调度一个独立的智能体运行；不受父轮次中断影响。
- `terminal(background=True, notify_on_complete=True)`——当智能体执行其他工作时仍持续运行的长时间 shell 命令。
:::

## 关键属性

- 每个子智能体都拥有其**自己的终端会话**（与父级分开）。
- 子智能体继承父级已启用的工具集；模型不能针对某个调用选择或扩展它们。
- **嵌套委派是选择加入的**——只有 `role="orchestrator"` 子级能进一步委派，且只有在 `max_spawn_depth` 从默认 1（扁平）提高后才能这样做。使用 `orchestrator_enabled: false` 可全局禁用。
- 叶子子智能体**不能**调用：`delegate_task`、`clarify`、`memory`、`send_message`、`cronjob`。编排者子智能体保留 `delegate_task`，但其他屏蔽项不变。两种角色均保留 `execute_code`（用于程序化工具调用），从而让子级能够批量执行机械性工作而非耗费推理迭代。
- **取消遵循所有权**——`/stop` 或关闭/重置所属会话会取消其后台子级；编排者下的同步后代遵循其父级的中断状态。
- 只有最终摘要进入父级上下文，从而保持高效的 token 使用。
- 子智能体继承父级的**API 密钥、provider 配置和凭据池**（支持在速率限制时轮换密钥）。

## delegate_task 与 execute_code

| 因素 | delegate_task | execute_code |
|--------|--------------|-------------|
| **推理** | 完整 LLM 推理循环 | 仅 Python 代码执行 |
| **上下文** | 全新的隔离对话 | 没有对话，仅脚本 |
| **工具访问** | 带推理能力的所有未屏蔽工具 | 通过 RPC 使用 7 个工具，不含推理 |
| **并行性** | 默认 3 个并发子智能体（可配置） | 单个脚本 |
| **最适合** | 需要判断的复杂任务 | 机械的多步骤流水线 |
| **Token 成本** | 更高（完整 LLM 循环） | 更低（仅返回 stdout） |
| **用户交互** | 无（子智能体不能澄清） | 无 |

**经验法则：** 当子任务需要推理、判断或多步骤问题解决时，使用 `delegate_task`。当你需要机械化数据处理或脚本化流水线时，使用 `execute_code`。

## 配置

```yaml
# In ~/.hermes/config.yaml
delegation:
  max_iterations: 50                        # Max turns per child (default: 50)
  # max_concurrent_children: 3              # Parallel children per batch (default: 3)
  # max_spawn_depth: 1                      # Tree depth (floor 1, no ceiling, default 1 = flat). Raise to 2 to allow orchestrator children to spawn leaves; 3+ for deeper trees.
  # orchestrator_enabled: true              # Disable to force all children to leaf role.
  model: "google/gemini-3-flash-preview"             # Optional provider/model override
  provider: "openrouter"                             # Optional built-in provider
  api_mode: anthropic_messages                       # optional; auto-detected from base_url for anthropic_messages endpoints

# Or use a direct custom endpoint instead of provider:
delegation:
  model: "qwen2.5-coder"
  base_url: "http://localhost:1234/v1"
  api_key: "local-key"
  # api_mode: "anthropic_messages"  # Optional. Wire protocol override for base_url ("chat_completions", "codex_responses", or "anthropic_messages"). Empty = auto-detect from URL (e.g. /anthropic suffix). Set explicitly for endpoints the heuristic can't classify (Azure AI Foundry, MiniMax, Zhipu GLM, LiteLLM proxies, …).
```

当 `base_url` 指向 Anthropic 兼容端点时——例如以 `/anthropic` 结尾的路径、Azure Foundry Claude 路由或 MiniMax `/anthropic` 代理——会自动将 `api_mode` 检测为 `anthropic_messages`，因此子智能体无需你设置即可使用正确的线路格式。自动检测的猜测错误时（很少见），请显式设置 `api_mode`。

:::tip
智能体会根据任务复杂度自动处理委派。你不必明确要求它委派——它会在合适时这样做。
:::
