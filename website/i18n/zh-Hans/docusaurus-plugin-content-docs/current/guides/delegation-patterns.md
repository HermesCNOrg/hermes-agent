---
sidebar_position: 13
title: "委派与并行工作"
description: "何时以及如何使用子代理委派：并行研究、代码审查和多文件工作的模式"
---

# 委派与并行工作

Hermes 可以生成隔离的子代理来并行处理任务。每个子代理都有自己的对话、终端会话和工具集。只有最终摘要会返回——中间工具调用绝不会进入你的上下文窗口。

如需完整的功能参考，请参阅[子代理委派](/user-guide/features/delegation)。

---

## 何时委派

**适合委派的任务：**
- 需要大量推理的子任务（调试、代码审查、研究综合）
- 会用中间数据淹没你的上下文的任务
- 并行且相互独立的工作流（同时进行研究 A 和 B）
- 希望代理不带偏见地处理的、需要全新上下文的任务

**请改用其他方式：**
- 单次工具调用 → 直接使用该工具
- 步骤之间需要逻辑处理的机械化多步骤工作 → `execute_code`
- 需要用户交互的任务 → 子代理不能使用 `clarify`
- 快速文件编辑 → 直接完成
- 必须在会话关闭或进程重启后继续存在的持久长时间任务 → `cronjob` 或 `terminal(background=True, notify_on_complete=True)`。顶层委派是异步的，但仍局限于本地进程。

---

## 模式：并行研究

同时研究三个主题，并获取结构化摘要：

```
并行研究以下三个主题：
1. 浏览器外 WebAssembly 的当前状态
2. 2025 年 RISC-V 服务器芯片的采用情况
3. 实用量子计算应用

重点关注近期进展和关键参与者。
```

在幕后，Hermes 使用：

```python
delegate_task(tasks=[
    {
        "goal": "Research WebAssembly outside the browser in 2025",
        "context": "Focus on: runtimes (Wasmtime, Wasmer), cloud/edge use cases, WASI progress"
    },
    {
        "goal": "Research RISC-V server chip adoption",
        "context": "Focus on: server chips shipping, cloud providers adopting, software ecosystem"
    },
    {
        "goal": "Research practical quantum computing applications",
        "context": "Focus on: error correction breakthroughs, real-world use cases, key companies"
    }
])
```

这三个任务会并发运行。每个子代理独立搜索网络并返回摘要。父代理随后会将这些内容综合为一份连贯的简报。

---

## 模式：代码审查

将安全审查委派给拥有全新上下文、能不带先入之见审视代码的子代理：

```
审查 src/auth/ 中的身份验证模块，查找安全问题。
检查 SQL 注入、JWT 验证问题、密码处理
以及会话管理。修复发现的任何问题并运行测试。
```

关键在于 `context` 字段——它必须包含子代理所需的一切：

```python
delegate_task(
    goal="Review src/auth/ for security issues and fix any found",
    context="""Project at /home/user/webapp. Python 3.11, Flask, PyJWT, bcrypt.
    Auth files: src/auth/login.py, src/auth/jwt.py, src/auth/middleware.py
    Test command: pytest tests/auth/ -v
    Focus on: SQL injection, JWT validation, password hashing, session management.
    Fix issues found and verify tests pass."""
)
```

:::warning 上下文问题
子代理对你的对话**完全一无所知**。它们从全新的状态开始。如果你委派“修复我们刚才讨论的 bug”，子代理不知道你指的是哪个 bug。务必明确传递文件路径、错误消息、项目结构和约束。
:::

---

## 模式：比较替代方案

并行评估同一问题的多种方法，然后选择最佳方案：

```
我需要为我们的 Django 应用添加全文搜索。请并行评估三种方法：
1. PostgreSQL tsvector（内置）
2. 通过 django-elasticsearch-dsl 使用 Elasticsearch
3. 通过 meilisearch-python 使用 Meilisearch

请分别说明：设置复杂度、查询能力、资源需求和维护开销。
比较它们并推荐一种方案。
```

每个子代理独立研究一个选项。由于它们彼此隔离，不会产生交叉影响——每项评估都根据自身优劣进行。父代理会获得全部三份摘要并进行比较。

---

## 模式：多文件重构

将大型重构任务拆分给并行子代理，每个代理负责代码库的不同部分：

```python
delegate_task(tasks=[
    {
        "goal": "Refactor all API endpoint handlers to use the new response format",
        "context": """Project at /home/user/api-server.
        Files: src/handlers/users.py, src/handlers/auth.py, src/handlers/billing.py
        Old format: return {"data": result, "status": "ok"}
        New format: return APIResponse(data=result, status=200).to_dict()
        Import: from src.responses import APIResponse
        Run tests after: pytest tests/handlers/ -v"""
    },
    {
        "goal": "Update all client SDK methods to handle the new response format",
        "context": """Project at /home/user/api-server.
        Files: sdk/python/client.py, sdk/python/models.py
        Old parsing: result = response.json()["data"]
        New parsing: result = response.json()["data"] (same key, but add status code checking)
        Also update sdk/python/tests/test_client.py"""
    },
    {
        "goal": "Update API documentation to reflect the new response format",
        "context": """Project at /home/user/api-server.
        Docs at: docs/api/. Format: Markdown with code examples.
        Update all response examples from old format to new format.
        Add a 'Response Format' section to docs/api/overview.md explaining the schema."""
    }
])
```

:::tip
每个子代理都有自己的终端会话。只要编辑的是不同文件，它们可以在同一个项目目录中工作而不会相互干扰。如果两个子代理可能会修改同一个文件，请在并行工作完成后自行处理该文件。
:::

---

## 模式：先收集，再分析

使用 `execute_code` 进行机械化数据收集，然后委派需要大量推理的分析：

```python
# Step 1: Mechanical gathering (execute_code is better here — no reasoning needed)
execute_code("""
from hermes_tools import web_search, web_extract

results = []
for query in ["AI funding Q1 2026", "AI startup acquisitions 2026", "AI IPOs 2026"]:
    r = web_search(query, limit=5)
    for item in r["data"]["web"]:
        results.append({"title": item["title"], "url": item["url"], "desc": item["description"]})

# Extract full content from top 5 most relevant
urls = [r["url"] for r in results[:5]]
content = web_extract(urls)

# Save for the analysis step
import json
with open("/tmp/ai-funding-data.json", "w") as f:
    json.dump({"search_results": results, "extracted": content["results"]}, f)
print(f"Collected {len(results)} results, extracted {len(content['results'])} pages")
""")

# Step 2: Reasoning-heavy analysis (delegation is better here)
delegate_task(
    goal="Analyze AI funding data and write a market report",
    context="""Raw data at /tmp/ai-funding-data.json contains search results and
    extracted web pages about AI funding, acquisitions, and IPOs in Q1 2026.
    Write a structured market report: key deals, trends, notable players,
    and outlook. Focus on deals over $100M."""
)
```

这通常是最有效的模式：`execute_code` 可以低成本地处理 10 次以上的顺序工具调用，随后子代理在干净的上下文中完成单项昂贵的推理任务。

---

## 继承的工具访问权限

子代理继承父代理已启用的工具集。`delegate_task` 不接受面向模型的 `toolsets` 参数，因此被委派的工作无法自行获得父代理没有的能力。若委派任务需要网络、终端、文件或其他访问权限，请在开始对话前配置父代理的工具。Hermes 仍会移除子代理被禁止使用的工具，如 `clarify`、`memory` 和 `send_message`；子代理保留 `execute_code` 用于以编程方式调用工具。

---

## 约束

- **默认 3 个并行任务**：批次默认并发运行 3 个子代理（可通过 config.yaml 中的 `delegation.max_concurrent_children` 配置；没有硬性上限，只有最小值 1）
- **嵌套委派为选择启用**：叶子子代理（默认）不能调用 `delegate_task`、`clarify`、`memory` 或 `execute_code`。编排器子代理（`role="orchestrator"`）保留 `delegate_task` 以继续委派，但仅当 `delegation.max_spawn_depth` 提高到默认值 1 以上时才可行（最小值为 1，没有上限）；另外三个工具仍被禁止。可通过 `delegation.orchestrator_enabled: false` 全局禁用。

### 调整并发度和深度

| 配置 | 默认值 | 范围 | 效果 |
|--------|---------|-------|--------|
| `max_concurrent_children` | 3 | >=1 | 每次 `delegate_task` 调用的并行批次大小 |
| `max_spawn_depth` | 1 | >=1 | 可以继续生成下级代理的委派层数 |

示例：运行 30 个具有嵌套子代理的并行工作器：

```yaml
delegation:
  max_concurrent_children: 30
  max_spawn_depth: 2
```

- **独立终端**——每个子代理都有自己的终端会话，以及独立的工作目录和状态
- **没有对话历史**——子代理只能看到父代理在调用 `delegate_task` 时传递的 `goal` 和 `context`
- **默认 50 次迭代**——对于简单任务，将 `max_iterations` 设置得更低以节省成本
- **不具备持久性**——顶层委派在后台运行并在稍后回传结果，但它仍绑定于所属会话和 Hermes 进程。关闭会话、执行 `/stop`、`/new` 或重启进程都可能取消或搁置进行中的工作。对于必须跨越这些边界继续存在的工作，请使用 `cronjob` 或 `terminal(background=True, notify_on_complete=True)`。

---

## 提示

**在目标中说明具体细节。**“修复 bug”太模糊。“修复 api/handlers.py 第 47 行中 `process_request()` 从 `parse_body()` 收到 None 时发生的 TypeError”能让子代理获得足够信息来完成工作。

**包含文件路径。**子代理不知道你的项目结构。务必包含相关文件的绝对路径、项目根目录和测试命令。

**将委派用于上下文隔离。**有时你需要一个新的视角。委派会迫使你清楚地阐述问题，子代理则不带你在对话中逐渐形成的假设来处理它。

**检查结果。**子代理摘要只是摘要。如果子代理说“已修复 bug 且测试通过”，请亲自运行测试或阅读差异来验证。

---

*如需完整的委派参考——所有参数、ACP 集成和高级配置——请参阅[子代理委派](/user-guide/features/delegation)。*
