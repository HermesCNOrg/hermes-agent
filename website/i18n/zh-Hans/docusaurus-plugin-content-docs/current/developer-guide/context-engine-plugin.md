---
sidebar_position: 9
title: "Context Engine 插件"
description: "如何构建替换内置 ContextCompressor 的 context engine 插件"
---

# 构建 Context Engine 插件

Context engine 插件使用替代策略管理对话上下文，以替换内置的 `ContextCompressor`。例如，无损上下文管理（LCM）引擎会构建知识 DAG，而非进行有损摘要。

## 工作原理

Agent 的上下文管理构建在 `ContextEngine` ABC（`agent/context_engine.py`）之上。内置的 `ContextCompressor` 是默认实现。插件引擎必须实现相同的接口。

同一时间只能有**一个** context engine 处于激活状态。选择由配置驱动：

```yaml
# config.yaml
context:
  engine: "compressor"    # 默认内置实现
  engine: "lcm"           # 激活名为 "lcm" 的插件引擎
```

插件引擎**绝不会自动激活**——用户必须显式将 `context.engine` 设置为插件的名称。

## 目录结构

每个 context engine 位于 `plugins/context_engine/<name>/`：

```
plugins/context_engine/lcm/
├── __init__.py      # 导出 ContextEngine 子类
├── plugin.yaml      # 元数据（name、description、version）
└── ...              # 引擎所需的任何其他模块
```

## ContextEngine ABC

你的引擎必须实现以下**必需**方法：

```python
from agent.context_engine import ContextEngine

class LCMEngine(ContextEngine):

    @property
    def name(self) -> str:
        """简短标识符，例如 'lcm'。必须与 config.yaml 的值匹配。"""
        return "lcm"

    def update_from_response(self, usage: dict) -> None:
        """每次 LLM 调用后，以 usage dict 为参数调用。

        从响应更新 self.last_prompt_tokens、self.last_completion_tokens、
        self.last_total_tokens。
        """

    def should_compress(self, prompt_tokens: int = None) -> bool:
        """若本轮应触发压缩则返回 True。"""

    def compress(self, messages: list, current_tokens: int = None,
                 focus_topic: str = None) -> list:
        """压缩消息列表并返回新的（可能更短的）列表。

        返回的列表必须是有效的 OpenAI 格式消息序列。

        ``focus_topic`` 是手动 ``/compress <focus>`` 提供的可选主题字符串；
        支持引导式压缩的引擎应优先保留与其相关的信息，其他引擎可以忽略它。
        """
```

### 引擎必须维护的类属性

Agent 直接读取这些属性以用于显示和日志记录：

```python
last_prompt_tokens: int = 0
last_completion_tokens: int = 0
last_total_tokens: int = 0
threshold_tokens: int = 0        # 触发压缩的时机
context_length: int = 0          # 模型的完整上下文窗口
compression_count: int = 0       # compress() 已运行的次数
```

### 可选方法

这些方法在 ABC 中具有合理的默认值。按需覆盖：

| 方法 | 默认值 | 何时覆盖 |
|--------|---------|--------------|
| `on_session_start(session_id, **kwargs)` | 空操作 | 需要加载持久化状态（DAG、DB）时 |
| `on_session_end(session_id, messages)` | 空操作 | 需要刷新状态、关闭连接时 |
| `on_session_reset()` | 重置 token 计数器 | 有要清除的每会话状态时 |
| `update_model(model, context_length, ...)` | 更新 context_length + threshold | 需要在模型切换时重新计算预算时 |
| `get_tool_schemas()` | 返回 `[]` | 引擎提供 agent 可调用的工具时（例如 `lcm_grep`） |
| `handle_tool_call(name, args, **kwargs)` | 返回错误 JSON | 实现工具处理器时 |
| `should_compress_preflight(messages)` | 返回 `False` | 可以进行低成本的 API 调用前估算时 |
| `get_status()` | 标准 token/threshold dict | 有要暴露的自定义指标时 |
| `select_context(request_messages, *, conversation_messages, incoming_message, budget_tokens)` | 返回 `None`（空操作） | 为**本次**请求选择/路由进入的上下文时（检索、主题路由）——见下文 |
| `on_turn_complete(messages, usage=None, **kwargs)` | 空操作 | 要摄取/索引/观察已完成的轮次时——见下文 |

## 每轮上下文选择和观察

`compress()` 回答的是“上下文太长 → 缩短它”。两个可选且默认空操作的钩子涵盖正交的*选择/观察*维度，因此引擎不再需要将 `should_compress()` 强制设为 `True` 并将 `compress()` 滥用为每轮回调：

```python
def select_context(self, request_messages, *, conversation_messages=None,
                   incoming_message=None, budget_tokens=0):
    """在派发前，为此次请求选择/替换上下文。

    返回供这一次 provider 调用使用的新消息列表（检索、主题路由、
    角色/分支切换），或返回 None 以保持不变。
    仅限请求：持久化的对话历史绝不会被修改。
    """

def on_turn_complete(self, messages, usage=None, **kwargs):
    """在 assistant/tool 循环完成后观察已完成的轮次。

    接收最终定稿的 transcript 的浅拷贝，以及本轮规范的 usage dict
    （若未获得 provider 响应则为 None），以便引擎可为下一次
    select_context() 进行摄取/索引/摘要。返回值会被忽略。
    """
```

契约：

- **默认空操作，故障开放。** 两者默认均为 `return None`。缺少钩子、发生异常或返回值无效时，请求将保持不变——因此，发生故障的引擎绝不会比未安装引擎更糟。宿主还会对继承的 ABC 默认实现进行身份检查并完全跳过它，因此未实现该钩子的引擎（包括内置压缩器）完全无需承担每请求工作。
- **`select_context()` 仅限请求。** 返回的列表会替换单次 provider 调用的消息；持久化历史绝不会被写入。返回 `None`、`[]`、非列表，或包含非 dict 的列表，都会故障开放为未修改的请求。
- **顺序 / 缓存稳定性。** 该钩子在 prompt cache-control 和每个请求清理器**之前**运行，因此：(a) 替换后的内容仍会通过与任何请求相同的验证；(b) 默认空操作使请求保持字节级完全相同——未实现该钩子的引擎的 prompt-cache 行为不变。替换列表的引擎只会改变自身的缓存前缀。按每个 provider 请求评估（重试时会再次运行）。
- **`on_turn_complete()`** 仅用于轮次后的观察；将 `messages` 视为只读。**覆盖为尽力而为：**它从标准轮次终结接缝触发。循环中的某些异常早期返回路径（例如 content-policy 阻止或 provider 终端故障）会在未经过终结流程的情况下持久化并返回，因此目前不会触发此钩子——应将其视为对已完成轮次的尽力观察，而不是每次早期退出都保证调用的回调。将所有终端路径统一到一个终结接缝是单独的后续工作。

### 何时使用这些钩子——以及何时不应使用

- **仅当你的引擎必须*替换*每请求上下文时才实现 `select_context()`**——例如检索增强选择、主题/分支路由、角色切换。它是唯一可以交换进入请求的消息的动词：`pre_llm_call` 插件钩子按文档设计仅能注入（它会追加到用户消息，绝不重写列表，以保留 prompt-cache 前缀）。如果不需要替换，就不要实现它。
- **如果你的插件只需要轮次后观察/摄取**（索引、记忆同步、分析），应实现一个**记忆 provider**（`sync_turn()`——参见[Memory Provider 插件](./memory-provider-plugin.md)），而不是 context engine。context engine 会取得会话压缩策略的所有权；memory provider 观察轮次但不拥有任何策略。`on_turn_complete()` 是已需要 `select_context()` 的引擎的观察镜像——使同一组件可以从它刚刚路由的轮次中学习——而不是通用轮次回调。
- **实际 `select_context()` 对 prompt-cache 的影响。** 非空操作的选择自然会改变其改变选择的那些轮次的 prompt-cache 前缀——该请求的前缀不再匹配 provider 的缓存前缀，因此这些轮次会重写缓存而非读取缓存。引擎应在没有任何变化时返回**稳定的选择**（相同对象或相等列表），并且只在路由决定确实不同时重塑上下文；每轮打乱选择会在不知不觉中失去每轮缓存复用。

## 引擎工具

Context engine 可以暴露 agent 直接调用的工具。从 `get_tool_schemas()` 返回 schema，并在 `handle_tool_call()` 中处理调用：

```python
def get_tool_schemas(self):
    return [{
        "name": "lcm_grep",
        "description": "Search the context knowledge graph",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"}
            },
            "required": ["query"],
        },
    }]

def handle_tool_call(self, name, args, **kwargs):
    if name == "lcm_grep":
        results = self._search_dag(args["query"])
        return json.dumps({"results": results})
    return json.dumps({"error": f"Unknown tool: {name}"})
```

引擎工具会在启动时注入 agent 的工具列表并自动派发——无需注册到 registry。

## 注册

### 通过目录（推荐）

将引擎放在 `plugins/context_engine/<name>/`。`__init__.py` 必须导出一个 `ContextEngine` 子类。发现系统会自动找到并实例化它。

### 通过通用插件系统

通用插件也可以注册 context engine：

```python
def register(ctx):
    engine = LCMEngine(context_length=200000)
    ctx.register_context_engine(engine)
```

只能注册一个引擎。第二个尝试注册的插件会被拒绝并发出警告。

## 生命周期

```
1. 引擎被实例化（插件加载或目录发现）
2. on_session_start() —— 对话开始
3. update_from_response() —— 每次 API 调用后
4. should_compress() —— 每轮检查
5. compress() —— 当 should_compress() 返回 True 时调用
6. on_session_end() —— 会话边界（CLI 退出、/reset、gateway 到期）
```

`on_session_reset()` 会在 `/new` 或 `/reset` 时调用，以在不完全关闭的情况下清除每会话状态。

## 配置

用户通过 `hermes plugins` → Provider Plugins → Context Engine 选择你的引擎，或通过编辑 `config.yaml` 选择：

```yaml
context:
  engine: "lcm"   # 必须与引擎的 name 属性匹配
```

`compression` 配置块（`compression.threshold`、`compression.protect_last_n` 等）特定于内置 `ContextCompressor`，但有一个明确例外：`compression.model_thresholds`（按模型覆盖阈值）是 context-engine 契约的一部分。宿主会在初始 `update_model()` 调用**之前**将解析后的映射赋给 `engine.model_thresholds`，而基类的 `update_model()` 会应用它（最长子字符串匹配，回退到引擎配置的阈值）。覆盖 `update_model()` 的引擎拥有自己的压缩策略，可遵从或忽略此映射——可使用 `from agent.context_compressor import resolve_model_threshold` 来复用相同的解析逻辑。对于其他所有内容，如有需要，你的引擎应定义自己的配置格式，并在初始化期间从 `config.yaml` 读取。

## 测试

```python
from agent.context_engine import ContextEngine

def test_engine_satisfies_abc():
    engine = YourEngine(context_length=200000)
    assert isinstance(engine, ContextEngine)
    assert engine.name == "your-name"

def test_compress_returns_valid_messages():
    engine = YourEngine(context_length=200000)
    msgs = [{"role": "user", "content": "hello"}]
    result = engine.compress(msgs)
    assert isinstance(result, list)
    assert all("role" in m for m in result)
```

完整 ABC 契约测试套件见 `tests/agent/test_context_engine.py`。

## 另请参阅

- [上下文压缩与缓存](/developer-guide/context-compression-and-caching) —— 内置压缩器的工作原理
- [Memory Provider 插件](/developer-guide/memory-provider-plugin) —— 用于 memory 的类似单选插件系统
- [插件](/user-guide/features/plugins) —— 通用插件系统概述
