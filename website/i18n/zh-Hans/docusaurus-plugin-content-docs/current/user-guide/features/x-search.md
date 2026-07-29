---
title: X（Twitter）搜索
description: 使用 xAI 内置的 x_search Responses 工具在 agent 内搜索 X（Twitter）帖子和话题串，支持 SuperGrok OAuth 登录或 XAI_API_KEY。
sidebar_label: X（Twitter）搜索
sidebar_position: 7
---

# X（Twitter）搜索

`x_search` 工具让 agent 可以直接搜索 X（Twitter）的帖子、个人资料和话题串。其底层依托 xAI 在 Responses API（`https://api.x.ai/v1/responses`）上内置的 `x_search` 工具：Grok 本身在服务器端运行搜索，并返回带有原始帖子引用的综合结果。

**当你明确需要 X 上的当前讨论、反应或说法时，请使用此工具而非 `web_search`。** 对于一般网页内容，请继续使用 `web_search` / `web_extract`。

## `x_search` 与 `xurl`

Hermes 可以提供两种不同的 X 功能界面：

| 界面 | 适用场景 | 不适用场景 |
|---------|------------|-------------------|
| `x_search` | 只读的公开 X 发现：当前讨论、反应、说法、个人资料、话题串，以及带引用的综合回答。 | 发帖、回复、点赞、私信、媒体上传、删除，或证明已认证的 X 账户发生了状态变化。 |
| `xurl` skill | 精确或已认证的 X API 操作：`post`、`reply`、`read`、`like`、`dm`、时间线、提及、媒体上传、特定账户读取和原始 v2 endpoint。 | 当 `x_search` 可用且不需要已认证账户上下文时，进行广泛的、由 Grok 综合的公开 X 研究。 |

对于混合工作流，请使用 `x_search` 发现候选公开帖子；在明确目标帖子、用户或操作后，再切换到 `xurl read` 或其他精确的 `xurl` 命令。任何改变 X 状态的操作都必须由 `xurl` 输出或 X API 响应确认；`x_search` 的回答绝不能作为写入已发生的证据。

:::tip
如果你本来就在通过 Portal 为 xAI 模型付费，Live Search 调用会从同一个为聊天配置的 xAI 密钥计费。参见 [Nous Portal](/integrations/nous-portal)。
:::

## 认证

满足以下**任一** xAI 凭据路径时，`x_search` 即会注册：

| 凭据 | 来源 | 配置方式 |
|------------|--------|-------|
| **SuperGrok / X Premium+ OAuth**（首选） | 在 `accounts.x.ai` 通过浏览器登录，自动刷新 | `hermes auth add xai-oauth` — 参见 [xAI Grok OAuth（SuperGrok / X Premium+）](../../guides/xai-grok-oauth.md) |
| **`XAI_API_KEY`** | 付费 xAI API 密钥 | 在 `~/.hermes/.env` 中设置 |

两者都使用相同的 endpoint 和相同的请求载荷，唯一差别是 bearer token。**当两者同时配置时，SuperGrok OAuth 优先**，因此 x_search 会使用你的订阅配额，而不是产生付费 API 消耗。

工具的 `check_fn` 在每次重建模型工具列表时都会运行 xAI 凭据解析器。返回 `True` 意味着 bearer 可获取、非空，并且（如果已过期）已成功刷新。刷新失败的已撤销 token 会将该工具从 schema 中隐藏；模型根本无法看到它。

## 启用工具

当存在 xAI 凭据（OAuth token 或 `XAI_API_KEY`）时自动启用。如果不想使用它，可通过 `hermes tools` → Search → x_search 显式禁用。

```bash
hermes tools
# → 🐦 X（Twitter）Search   （按空格键切换开关）
```

选择器提供两种凭据选项：

1. **xAI Grok OAuth（SuperGrok / Premium+）** — 如果你尚未登录，会打开浏览器前往 `accounts.x.ai`
2. **xAI API key** — 提示输入 `XAI_API_KEY`

任一选项均可满足门控条件。你可以选择已有的任意凭据；该工具使用任一凭据时的工作方式都相同。如果最终两者都配置了，OAuth 会在调用时优先。

## 配置

```yaml
# ~/.hermes/config.yaml
x_search:
  # 用于 Responses 调用的 xAI 模型。
  # grok-4.5 是建议的默认值；任何具有
  # x_search 工具访问权限的 Grok 模型都可以使用。
  model: grok-4.5

  # 可选的推理强度：low、medium、high 或 xhigh。省略时，
  # 使用所选模型的默认值。仅明确支持 xhigh 的模型（例如
  # grok-4.20-multi-agent）支持 xhigh。
  # reasoning_effort: low

  # 请求超时秒数。对于复杂查询，x_search 可能需要 60–120 秒；
  # 默认值很宽裕。最小值：30。
  timeout_seconds: 180

  # 针对 5xx / ReadTimeout / ConnectionError 的自动重试次数。
  # 每次重试均会退避（每次尝试 1.5 倍秒数，最长 5 秒）。
  retries: 2
```

`reasoning_effort` 会作为 `reasoning: {effort: ...}` 发送至 xAI Responses API。对于不支持可配置推理的模型，请不要设置它。无效值会在发出 API 请求前失败。

## 工具参数

agent 使用以下参数调用 `x_search`：

| 参数 | 类型 | 说明 |
|-----------|------|-------------|
| `query` | string（必需） | 要在 X 上查找的内容。 |
| `allowed_x_handles` | string 数组 | 可选的、**仅**包含这些账号的列表（最多 10 个）。会移除开头的 `@`。 |
| `excluded_x_handles` | string 数组 | 可选的、要排除的账号列表（最多 10 个）。与 `allowed_x_handles` 互斥。 |
| `from_date` | string | 可选的 `YYYY-MM-DD` 起始日期。 |
| `to_date` | string | 可选的 `YYYY-MM-DD` 结束日期。 |
| `enable_image_understanding` | boolean | 要求 xAI 分析匹配帖子附带的图像。 |
| `enable_video_understanding` | boolean | 要求 xAI 分析匹配帖子附带的视频。 |

该工具返回的 JSON 包含：

- `answer` — Grok 生成的综合文本回答
- `citations` — 由 Responses API 顶层字段返回的引用
- `inline_citations` — 从消息正文提取的 `url_citation` 注释（每条均含有 `url`、`title`、`start_index`、`end_index`）
- `degraded` — 当设置了任意缩小范围的过滤器（`allowed_x_handles`、`excluded_x_handles`、`from_date`、`to_date`），**且**两个引用渠道都返回空时为 `true`。此时 `answer` 基于模型自身知识综合得出，而非基于 X 索引，因此应视为无来源。否则为 `false`（也包括“未设置过滤器”的情形：宽泛的无来源回答只是一个回答，并非过滤器未命中）
- `degraded_reason` — 简要说明哪些过滤器处于激活状态的字符串；当 `degraded` 为 `false` 时为 `null`
- `credential_source` — OAuth 解析成功时为 `"xai-oauth"`；API 密钥解析成功时为 `"xai"`
- `model`、`query`、`provider`、`tool`、`success`

### 日期验证

`from_date` / `to_date` 会在 HTTP 调用前于客户端进行验证：

- 如果提供，两者都必须能解析为 `YYYY-MM-DD`。
- 当两者均被设置时，`from_date` 必须早于或等于 `to_date`。
- `from_date` 不得晚于当前 UTC 日期：尚未开始的时间窗口不可能有帖子，因此调用必然返回零条引用。
- 可以将 `to_date` 设为未来日期（调用方可能合理地请求“从昨天到明天”，以捕获帖子在发布时的内容）。

验证失败会显示为结构化的 `{"error": "..."}` 工具结果，绝不会对 xAI 发起 HTTP 调用。

## 示例

与 agent 对话：

> X 上的人们如何评价新的 Grok 图像功能？请重点关注来自 @xai 的回应。

agent 将：

1. 使用 `query="reactions to new Grok image features"`、`allowed_x_handles=["xai"]` 调用 `x_search`
2. 获得综合回答以及链接至具体帖子的引用列表
3. 回复答案和参考资料

如果用户接着请求“回复最佳的一条”或“给那条帖子点赞”，agent 应切换至 `xurl` skill，确认确切的目标帖子，并使用 X API 操作。`x_search` 始终是一个发现工具。

## 故障排查

### “No xAI credentials available”

当两条认证路径都失败时，该工具会显示此信息。请在 `~/.hermes/.env` 中设置 `XAI_API_KEY`，或者运行 `hermes auth add xai-oauth` 并完成浏览器登录。随后重启会话，让 agent 重新读取工具注册表。

### “`x_search` is not enabled for this model”

已配置的 `x_search.model` 无权使用服务器端 `x_search` 工具。请切换至 `grok-4.5`（默认值）或其他支持它的 Grok 模型。请查看 [xAI documentation](https://docs.x.ai/) 以获取当前列表。

### 工具未出现在 schema 中

可能有两个原因：

1. **工具集未启用。** 运行 `hermes tools`，确认 `🐦 X（Twitter）Search` 已勾选。
2. **没有 xAI 凭据。** check_fn 返回 False，因此 schema 保持隐藏。运行 `hermes auth status` 确认 xai-oauth 登录状态，并检查 `XAI_API_KEY` 是否已设置（如果你使用 API 密钥路径）。

### `degraded: true` — 没有引用的回答

当你使用 `allowed_x_handles`、`excluded_x_handles` 或日期范围，而响应返回 `degraded: true` 时，xAI 的 X 索引没有返回匹配的帖子，但 Grok 仍然根据其训练数据生成了综合回答。该回答没有来源：请不要将其当作真正的 X 结果。

值得检查的原因：

- **账号拼写错误。** 去掉 `@`，再次检查拼写，并确认账户存在。
- **日期范围过窄**，或已经错过今天的帖子；请扩大范围后重试。
- **xAI 索引缺口。** 即使有些活跃账户经常发帖，它们有时仍无法出现在 `x_search` 中。几分钟后重试；或者，当你需要精确读取某个账号的时间线时，使用 `xurl` skill 直接读取 X API。

## 另请参阅

- [xAI Grok OAuth（SuperGrok / X Premium+）](../../guides/xai-grok-oauth.md) — OAuth 设置指南
- [xurl skill](../skills/bundled/social-media/social-media-xurl.md) — 用于已认证账户操作的官方 X API CLI
- [Web 搜索与提取](web-search.md) — 用于一般（非 X）网页搜索
- [工具参考](../../reference/tools-reference.md) — 完整工具目录
