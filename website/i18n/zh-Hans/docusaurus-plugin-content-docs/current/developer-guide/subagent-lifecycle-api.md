---
title: 公共子代理生命周期 API
sidebar_label: 子代理生命周期 API
---

# 公共子代理生命周期 API

插件可以启动并监管全新的 Hermes 子会话，而无需导入
`tools.delegate_tool`、网关内部机制、TUI 状态或 `AIAgent` 字段。
该服务会从当前代理轮次解析其父级，因此可在
CLI、网关、非交互式和看板工作器会话中运行。在活跃代理轮次之外启动会以
`No active Hermes parent session` 失败闭合。

```python
from agent.subagent_lifecycle import SubagentLaunchRequest

def launch_review(ctx):
    # 在代理轮次处于活跃状态时，从插件工具或钩子中调用。
    service = ctx.subagent_lifecycle
    handle = service.launch(SubagentLaunchRequest(
        goal="审查此更改是否引入回归。",
        context="仅检查所提供的仓库。",
        role="leaf",
        correlation_id="review-42",
        allowed_toolsets=("file",),
    ))
    # 如有需要，持久化 handle.to_dict()。
    if service.wait(handle, timeout_seconds=2).timed_out:
        return handle.to_dict()
    return service.result(handle)
```

`SubagentHandle` 可序列化，并携带带版本的、不透明的能力凭据。
将其传回 `status`、`wait`、`cancel`、`result` 或 `reconnect`；格式错误
或伪造的句柄会返回 `UNKNOWN`/`UNKNOWN_HANDLE`，且无法访问子代理。

稳定状态为 `PENDING`、`STARTING`、`RUNNING`、`SUCCEEDED`、`FAILED`、
`INTERRUPTED`、`CANCEL_REQUESTED`、`CANCELLED` 和 `UNKNOWN`。

`cancel(handle, reason=...)` 为协作式操作：它会请求子代理在下一个安全边界
中断，并返回 `CANCEL_REQUESTED`；在 `wait` 或 `result` 观察到终止状态之前，
它绝不会声称已完成。终止结果不可变、幂等、长度上限为 32k 个字符，会省略
转录内容和隐藏推理，并包含稳定的结果哈希。

此 API 是由生命周期管理的异步执行。子代理构建和完成使用与 `delegate_task`
相同的主机所有路径，其中包括父级工具解析恢复、内存通知、串行化的 `subagent_stop`
钩子、资源清理和子代理成本汇总。它不会更改同步的 `delegate_task` 工具、批量委派
或其网关/TUI 显示。初始实现会在进程内保留元数据和终止结果一小时。
进程重启后，`reconnect` 会返回 `RECONNECT_UNAVAILABLE`，且绝不会启动替代子代理。
正在运行的 Python 线程同样无法在进程退出后存活；调用方必须将这些句柄视为因进程退出而中断。

请求以失败闭合的方式处理：goal/context/metadata 的大小受限，未知工具集或会扩大
父级权限范围的工具集会被拒绝，并且在 Hermes 能够在不削弱隔离性的前提下支持它们之前，
每工具阻止项、工作目录覆盖和每次启动超时都会被明确拒绝。使用 `allowed_toolsets`
来收窄子代理；Hermes 现有的不安全工具阻止项仍会被强制执行。
