---
sidebar_position: 5
title: "将 Hermes 用作 Python 库"
description: "在你自己的 Python 脚本、Web 应用或自动化流水线中嵌入 AIAgent——无需 CLI"
---

# 将 Hermes 用作 Python 库

Hermes 不只是一个 CLI 工具。你可以直接导入 `AIAgent`，并在自己的 Python 脚本、Web 应用或自动化流水线中以编程方式使用它。本指南将说明具体方法。

---

## 安装

克隆 Hermes 并创建其受支持的可编辑开发环境：

```bash
git clone https://github.com/NousResearch/hermes-agent.git
cd hermes-agent
uv sync
```

从该检出目录中使用 `uv run python your_app.py` 运行你的应用。Hermes 不发布支持通过 `requirements.txt` 安装的 wheel 或源代码发行包。

:::tip
将 Hermes 用作库时，需要使用与 CLI 相同的环境变量。至少设置 `OPENROUTER_API_KEY`（或者，如果使用直接的提供商访问，则设置 `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`）。
:::

---

## 基本用法

使用 Hermes 最简单的方式是 `chat()` 方法——传入一条消息，获得一个字符串：

```python
from run_agent import AIAgent

agent = AIAgent(
    model="anthropic/claude-sonnet-4.6",
    quiet_mode=True,
)
response = agent.chat("What is the capital of France?")
print(response)
```

`chat()` 会在内部处理完整的对话循环——工具调用、重试及其他一切——并且只返回最终文本响应。

:::warning
在自己的代码中嵌入 Hermes 时，始终设置 `quiet_mode=True`。否则，代理会打印 CLI 旋转指示器、进度指示器和其他终端输出，从而使应用程序的输出杂乱。
:::

---

## 完整的对话控制

如需更精细地控制对话，请直接使用 `run_conversation()`。它会返回一个包含完整响应、消息历史和元数据的字典：

```python
agent = AIAgent(
    model="anthropic/claude-sonnet-4.6",
    quiet_mode=True,
)

result = agent.run_conversation(
    user_message="Search for recent Python 3.13 features",
    task_id="my-task-1",
)

print(result["final_response"])
print(f"Messages exchanged: {len(result['messages'])}")
```

返回的字典包含：
- **`final_response`** —— 代理的最终文本回复
- **`messages`** —— 完整的消息历史（系统、用户、助手、工具调用）

（你传入的 `task_id` 会存储在代理实例上，用于 VM 隔离，但不会在返回字典中回显。）

你还可以传入自定义系统消息，它会覆盖该调用的临时系统提示词：

```python
result = agent.run_conversation(
    user_message="Explain quicksort",
    system_message="You are a computer science tutor. Use simple analogies.",
)
```

---

## 配置工具

使用 `enabled_toolsets` 或 `disabled_toolsets` 控制代理可访问的工具集：

```python
# 仅启用 Web 工具（浏览、搜索）
agent = AIAgent(
    model="anthropic/claude-sonnet-4.6",
    enabled_toolsets=["web"],
    quiet_mode=True,
)

# 启用除终端访问外的所有功能
agent = AIAgent(
    model="anthropic/claude-sonnet-4.6",
    disabled_toolsets=["terminal"],
    quiet_mode=True,
)
```

:::tip
当你需要一个最小化、受严格限制的代理时（例如，研究机器人只允许 Web 搜索），请使用 `enabled_toolsets`。当你希望拥有大多数能力但需要限制特定能力时（例如，在共享环境中禁止终端访问），请使用 `disabled_toolsets`。
:::

---

## 多轮对话

通过传回消息历史，在多个轮次之间维护对话状态：

```python
agent = AIAgent(
    model="anthropic/claude-sonnet-4.6",
    quiet_mode=True,
)

# 第一轮
result1 = agent.run_conversation("My name is Alice")
history = result1["messages"]

# 第二轮——代理会记住上下文
result2 = agent.run_conversation(
    "What's my name?",
    conversation_history=history,
)
print(result2["final_response"])  # "Your name is Alice."
```

`conversation_history` 参数接受前一个结果中的 `messages` 列表。代理会在内部复制该列表，因此你的原始列表绝不会被修改。

---

## 保存轨迹

启用轨迹保存，以 ShareGPT 格式捕获对话——这对生成训练数据或调试很有用：

```python
agent = AIAgent(
    model="anthropic/claude-sonnet-4.6",
    save_trajectories=True,
    quiet_mode=True,
)

agent.chat("Write a Python function to sort a list")
# Saves to trajectory_samples.jsonl in ShareGPT format
```

每个对话会作为单独的一行 JSONL 追加，因此可轻松从自动化运行中收集数据集。

---

## 自定义系统提示词

使用 `ephemeral_system_prompt` 设置自定义系统提示词，以引导代理的行为；它**不会**保存到轨迹文件中（从而保持训练数据干净）：

```python
agent = AIAgent(
    model="anthropic/claude-sonnet-4",
    ephemeral_system_prompt="You are a SQL expert. Only answer database questions.",
    quiet_mode=True,
)

response = agent.chat("How do I write a JOIN query?")
print(response)
```

这非常适合构建专门的代理——代码审查员、文档作者或 SQL 助手——它们都使用相同的底层工具。

---

## 批处理

如需并行运行许多提示词，Hermes 包含 `batch_runner.py`。它以适当的资源隔离来管理并发的 `AIAgent` 实例：

```bash
python batch_runner.py --input prompts.jsonl --output results.jsonl
```

每个提示词都会获得自己的 `task_id` 和隔离环境。如果需要自定义批处理逻辑，可以直接使用 `AIAgent` 自行构建：

```python
import concurrent.futures
from run_agent import AIAgent

prompts = [
    "Explain recursion",
    "What is a hash table?",
    "How does garbage collection work?",
]

def process_prompt(prompt):
    # 为线程安全起见，每个任务创建一个新的代理
    agent = AIAgent(
        model="anthropic/claude-sonnet-4",
        quiet_mode=True,
        skip_memory=True,
    )
    return agent.chat(prompt)

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(process_prompt, prompts))

for prompt, result in zip(prompts, results):
    print(f"Q: {prompt}\nA: {result}\n")
```

:::warning
始终为**每个线程或任务创建新的 `AIAgent` 实例**。代理维护内部状态（对话历史、工具会话、迭代计数器），在并发共享时并不具备线程安全性。
:::

---

## 集成示例

### FastAPI 端点

```python
from fastapi import FastAPI
from pydantic import BaseModel
from run_agent import AIAgent

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    model: str = "anthropic/claude-sonnet-4"

@app.post("/chat")
async def chat(request: ChatRequest):
    agent = AIAgent(
        model=request.model,
        quiet_mode=True,
        skip_context_files=True,
        skip_memory=True,
    )
    response = agent.chat(request.message)
    return {"response": response}
```

### Discord 机器人

```python
import discord
from run_agent import AIAgent

client = discord.Client(intents=discord.Intents.default())

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith("!hermes "):
        query = message.content[8:]
        agent = AIAgent(
            model="anthropic/claude-sonnet-4",
            quiet_mode=True,
            skip_context_files=True,
            skip_memory=True,
            platform="discord",
        )
        response = agent.chat(query)
        await message.channel.send(response[:2000])

client.run("YOUR_DISCORD_TOKEN")
```

### CI/CD 流水线步骤

```python
#!/usr/bin/env python3
"""CI step: auto-review a PR diff."""
import subprocess
from run_agent import AIAgent

diff = subprocess.check_output(["git", "diff", "main...HEAD"]).decode()

agent = AIAgent(
    model="anthropic/claude-sonnet-4",
    quiet_mode=True,
    skip_context_files=True,
    skip_memory=True,
    disabled_toolsets=["terminal", "browser"],
)

review = agent.chat(
    f"Review this PR diff for bugs, security issues, and style problems:\n\n{diff}"
)
print(review)
```

---

## 关键构造函数参数

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `model` | `str` | `""` | OpenRouter 格式的模型（默认为空；在运行时从你的 hermes 配置中解析） |
| `quiet_mode` | `bool` | `False` | 抑制 CLI 输出 |
| `enabled_toolsets` | `List[str]` | `None` | 将特定工具集加入白名单 |
| `disabled_toolsets` | `List[str]` | `None` | 将特定工具集加入黑名单 |
| `save_trajectories` | `bool` | `False` | 将对话保存到 JSONL |
| `ephemeral_system_prompt` | `str` | `None` | 自定义系统提示词（不会保存到轨迹） |
| `max_iterations` | `int` | `500` | 每次对话允许的最大工具调用迭代次数 |
| `skip_context_files` | `bool` | `False` | 跳过加载 AGENTS.md 文件 |
| `skip_memory` | `bool` | `False` | 禁用持久记忆读取/写入 |
| `api_key` | `str` | `None` | API 密钥（回退到环境变量） |
| `base_url` | `str` | `None` | 自定义 API 端点 URL |
| `platform` | `str` | `None` | 平台提示（`"discord"`、`"telegram"` 等） |

---

## 重要说明

:::tip
- 如果不希望将工作目录中的 `AGENTS.md` 文件加载到系统提示词中，请设置 **`skip_context_files=True`**。
- 设置 **`skip_memory=True`** 可防止代理读取或写入持久记忆——建议用于无状态 API 端点。
- `platform` 参数（例如 `"discord"`、`"telegram"`）会注入特定平台的格式提示，使代理调整其输出样式。
:::

:::warning
- **线程安全**：每个线程或任务创建一个 `AIAgent`。绝不要在并发调用之间共享实例。
- **资源清理**：当对话结束时，代理会自动清理资源（终端会话、浏览器实例）。如果在长期运行的进程中运行，请确保每个对话都能正常完成。
- **迭代限制**：默认的 `max_iterations=500` 较为宽松。对于简单的问答用例，请考虑降低它（例如 `max_iterations=10`），以防止失控的工具调用循环并控制成本。
:::
