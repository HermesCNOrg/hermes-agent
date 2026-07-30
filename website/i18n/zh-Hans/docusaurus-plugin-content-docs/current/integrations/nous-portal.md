---
sidebar_position: 1
title: "Nous Portal"
description: "一个订阅、300 多个前沿模型和 Tool Gateway——运行 Hermes Agent 的推荐方式"
---

# Nous Portal

[Nous Portal](https://portal.nousresearch.com) 是 Nous Research 的统一订阅网关，也是**运行 Hermes Agent 的推荐方式**。一次 OAuth 登录取代了原本需要手动配置的各模型实验室、搜索 API、图像生成器和浏览器提供商的独立账户、API 密钥及计费关系。

如果你只来得及设置一项，就设置这个。最快路径：

```bash
hermes setup --portal
```

这条命令会执行 Portal OAuth，允许你选择 Nous 模型，在 `config.yaml` 中将 Nous 设为推理提供商，并启用 Tool Gateway。完成后即可立即运行 `hermes chat`。

还没有订阅？前往 [portal.nousresearch.com/manage-subscription](https://portal.nousresearch.com/manage-subscription) 注册，然后回来运行上面的命令。

## 订阅包含什么

### 300 多个前沿模型，一张账单

Portal 代理来自整个生态系统的精选智能体模型目录——费用记入你的 Nous 订阅，而不是让每个实验室各自占用一个积分余额。

| 系列 | 模型 |
|--------|--------|
| **Anthropic Claude** | Opus 4.7、Opus 4.6、Sonnet 4.6、Haiku 4.5 |
| **OpenAI** | GPT-5.5、GPT-5.5 Pro、GPT-5.4 Mini、GPT-5.4 Nano、GPT-5.3 Codex |
| **Google Gemini** | Gemini 3 Pro Preview、Gemini 3 Flash Preview、Gemini 3.1 Pro Preview、Gemini 3.1 Flash Lite Preview |
| **DeepSeek** | DeepSeek V4 Pro |
| **Qwen** | Qwen3.7-Max、Qwen3.6-35B-A3B |
| **Kimi / Moonshot** | Kimi K2.6 |
| **GLM / Zhipu** | GLM-5.1 |
| **MiniMax** | MiniMax M2.7 |
| **xAI** | Grok 4.3 |
| **NVIDIA** | Nemotron-3 Super 120B-A12B |
| **Tencent** | Hunyuan 3 Preview |
| **Xiaomi** | MiMo V2.5 Pro |
| **StepFun** | Step 3.5 Flash |
| **Hermes** | Hermes-4-70B、Hermes-4-405B（对话用途，见[下方说明](#a-note-on-hermes-4)） |
| **+ 其他所有模型** | 另外 280 多个模型——完整的智能体前沿 |

在底层，Portal 会将每个模型路由到最适合它的后端——部分模型通过 OpenRouter，其他模型通过专有或次级提供商；特定模型的路由也可能随时间变化。不论哪种情况，费用均计入你的 Nous 订阅。在会话中途使用 `/model`，即可在适合编程的 Claude Sonnet 4.6 与适合长上下文的 Gemini 3 Pro 之间切换——无需新凭证、无需充值，也不会出现意外的零余额错误。

:::note
由于路由按模型进行，且并不总是通过 OpenRouter，OpenRouter 专用请求扩展（例如 `provider` 路由偏好、`session_id` 粘性路由或顶层 `cache_control`）不属于 Portal API 合约；具体后端可能会忽略它们。
:::

### Nous Tool Gateway

同一订阅还会解锁 [Tool Gateway](/user-guide/features/tool-gateway)，该服务通过 Nous 托管的基础设施路由 Hermes Agent 的工具调用。五个后端，一次登录：

| 工具 | 合作伙伴 | 功能 |
|------|---------|--------------|
| **网页搜索和提取** | Firecrawl | 智能体级搜索和整页提取。无需 Firecrawl API 密钥，也无需管理速率限制。 |
| **图像生成** | FAL | 一个端点下的九种模型：FLUX 2 Klein 9B、FLUX 2 Pro、Z-Image Turbo、Nano Banana Pro（Gemini 3 Pro Image）、GPT Image 1.5、GPT Image 2、Ideogram V3、Recraft V4 Pro、Qwen Image。 |
| **文本转语音** | OpenAI TTS | 无需单独 OpenAI 密钥的高质量 TTS。可在各消息平台启用[语音模式](/user-guide/features/voice-mode)。 |
| **云端浏览器自动化** | Browser Use | 用于 `browser_navigate`、`browser_click`、`browser_type`、`browser_vision` 的无头 Chromium 会话。无需 Browserbase 账户。 |
| **云端终端沙箱** | Modal | 用于代码执行的无服务器终端沙箱（可选附加项）。 |

没有网关时，接入每一项意味着要有 Firecrawl 账户、FAL 账户、Browser Use 账户、OpenAI 密钥和 Modal 账户——五次独立注册、五个独立仪表板、五套独立充值流程。有了网关，全部通过一个订阅路由。

你也可以只启用特定网关工具（例如网页搜索而非图像生成）——参阅下文[将网关与自有后端混用](#mixing-the-gateway-with-your-own-backends)。

### 凭证不在 dotfiles 中

由于一切均通过一个经 OAuth 认证的 Portal 会话路由，你不会积累一个包含十几个长期 API 密钥的 `.env` 文件。磁盘上的唯一凭证是 `~/.hermes/auth.json` 中的刷新令牌；Hermes 会在每个请求中从它签发短期 JWT——见下文[令牌处理](#token-handling)。

### 跨平台一致性

[原生 Windows](/user-guide/windows-native) 的难点是按工具设置 API 密钥——从 Windows 配置 Firecrawl 账户、FAL 账户、Browser Use 账户和 OpenAI 密钥，是获得有用智能体时摩擦最大的环节。Portal 订阅消除了这一障碍：一次 OAuth 覆盖模型及全部网关工具，因此 Windows 用户无需手动配置四个后端，也能获得与 macOS/Linux 相同的体验。

## 关于 Hermes 4 的说明

Nous Research 自家的 **Hermes 4** 系列（Hermes-4-70B、Hermes-4-405B）可通过 Portal 以大幅折扣价格使用。这些是**前沿混合推理对话模型**——擅长数学、科学、遵循指令、遵从 schema、角色扮演和长篇写作。

不过，**不建议在 Hermes Agent 内部使用它们**。Hermes 4 针对对话和推理调优，而非智能体依赖的高频工具调用循环。请将其用于研究工作流，或通过[订阅代理](/user-guide/features/subscription-proxy)在其他工具中使用；但在智能体工作中，请从目录中选择前沿智能体模型：

```bash
/model anthropic/claude-sonnet-4.6     # 最佳通用智能体模型
/model openai/gpt-5.5-pro              # 强大的推理 + 工具调用
/model google/gemini-3-pro-preview     # 超大上下文窗口
/model deepseek/deepseek-v4-pro        # 高性价比编程模型
```

Portal 自己的[模型信息页](https://portal.nousresearch.com/info)也有相同警告，因此这并非 Hermes 方面的观点——而是 Nous Research 的官方指导。

## 设置

### 全新安装——一条命令

```bash
hermes setup --portal
```

这会一次性执行完整设置：

1. 打开浏览器，前往 portal.nousresearch.com 进行 OAuth 登录
2. 将刷新令牌存储到 `~/.hermes/auth.json`
3. 允许你从精选列表中选择 Nous 模型（也可以跳过以保留当前模型）
4. 在 `~/.hermes/config.yaml` 中将 Nous 设为推理提供商（当你选择模型时）
5. 启用 Tool Gateway（网页、图像、TTS、浏览器路由）
6. 返回终端，即可运行 `hermes chat`

如果还没有订阅，请先在 [portal.nousresearch.com/manage-subscription](https://portal.nousresearch.com/manage-subscription) 注册。

### 已有安装——将 Portal 与其他提供商一同添加

如果你已经使用 OpenRouter、Anthropic 或其他提供商配置了 Hermes，并希望在它们之外添加 Portal：

```bash
hermes model
# 从提供商列表中选择 "Nous Portal"
# 浏览器打开，登录，完成
```

你现有的提供商仍会保持配置。你可以在会话中途用 `/model` 或在会话之间用 `hermes model` 切换——Portal 会成为可用提供商之一，而不是唯一提供商。

### 无头 / SSH / 远程设置

OAuth 需要浏览器，但回环回调运行在 Hermes 所在的机器上。对于远程主机，见 [OAuth over SSH / Remote Hosts](/guides/oauth-over-ssh)——与任何其他基于 OAuth 的提供商相同的模式（`ssh -L` 端口转发）同样适用于 Portal。

### Profile 设置

如果你使用 [Hermes profiles](/user-guide/profiles)，Portal 刷新令牌将通过共享令牌存储自动在全部 profile 之间共享。在任一 profile 上登录一次，其余 profile 会自动取得它——无需为每个 profile 重复 OAuth 流程。

## 日常使用 Portal

### 检查已配置的内容

```bash
hermes portal            # 登录 Nous Portal 并设置它（一次性引导）
hermes portal info       # 登录状态、订阅信息、模型和网关路由
hermes portal status     # `portal info` 的别名
hermes portal tools      # 带有逐工具路由的详细 Tool Gateway 目录
hermes portal open       # 在浏览器中打开订阅管理页面
```

不带子命令的 `hermes portal` 是 `hermes auth add nous --type oauth` 的面向用户别名——它会让你登录、选择 Nous 模型、将 Nous 设置为推理提供商，并提供 Tool Gateway 加入选项（等同于 `hermes setup --portal`，也是首次快速设置使用的同一 Nous 流程）。

`hermes portal info` 给出高层概览：

```
  Nous Portal
  ───────────
  Auth:    ✓ logged in
  Portal:  https://portal.nousresearch.com
  Model:   ✓ using Nous as inference provider

  Tool Gateway
  ────────────
  Web search & extract  via Nous Portal
  Image generation      via Nous Portal
  Text-to-speech        via Nous Portal
  Browser automation    via Nous Portal
  Cloud terminal        not configured
```

### 切换模型

在会话内：

```bash
/model anthropic/claude-sonnet-4.6
/model openai/gpt-5.5-pro
/model google/gemini-3-pro-preview
```

或打开选择器：

```bash
/model
# 使用方向键，按 Enter 选择
```

在会话外（完整设置向导，适合添加新提供商）：

```bash
hermes model
```

### 将网关与自有后端混用

如果你已有 Browserbase 账户并希望继续使用，同时通过 Nous 路由网页搜索和图像生成，这也受支持。用 `hermes tools` 为每个工具选择后端：

```bash
hermes tools
# → Web search       → "Nous Subscription"
# → Image generation → "Nous Subscription"
# → Browser          → "Browserbase"  (your existing key)
# → TTS              → "Nous Subscription"
```

Tool Gateway 可按工具选择加入，并非全有或全无。Nous 管理的后端会显示在 `hermes tools` 中，无论你是否登录 Nous Portal——若你在认证前选择 "Nous Subscription"，Hermes 会以内联方式运行 Portal 登录（不会更改你的推理提供商，也不会触碰其他工具）。有关完整的逐工具配置矩阵，见 [Tool Gateway 文档](/user-guide/features/tool-gateway)。

### 订阅管理

随时管理套餐、查看使用量、升级或取消：

- **网页：** [portal.nousresearch.com/manage-subscription](https://portal.nousresearch.com/manage-subscription)
- **CLI 快捷方式：** `hermes portal open`（在默认浏览器中打开同一页面）

## 配置参考

执行 `hermes setup --portal` 后，`~/.hermes/config.yaml` 将如下所示：

```yaml
model:
  provider: nous
  default: anthropic/claude-sonnet-4.6     # 或你选择的任何模型
  base_url: https://inference-api.nousresearch.com/v1
```

Tool Gateway 设置位于各自的工具部分：

```yaml
web:
  backend: nous       # 网页搜索/提取通过 Tool Gateway 路由

image_gen:
  provider: nous

tts:
  provider: nous

browser:
  backend: nous
```

OAuth 刷新令牌单独存储在 `~/.hermes/auth.json` 中（不在 `config.yaml` 中——凭证和配置在设计上分开保存）。

## 令牌处理

Hermes 在每次推理调用时从存储的 Portal 刷新令牌签发短期 JWT，而非复用长期 API 密钥。令牌生命周期完全自动——刷新、签发、瞬时 401 时重试——你永远不会看到它。

如果 Portal 使刷新令牌失效（密码更改、手动撤销、会话过期），失效的刷新令牌会在**本地隔离**，因此 Hermes 会停止重放它，你也不会看到一连串相同的 401。下一次调用会显示清晰的“需要重新认证”消息。运行 `hermes auth add nous` 再次登录；下一次成功登录会清除隔离状态。

## 故障排查

### `hermes portal info` 显示“not logged in”

你尚未完成 OAuth 流程，或刷新令牌被清除了。运行：

```bash
hermes portal
```

或者使用 `hermes model` 并重新选择 Nous Portal。

### 会话中途收到“需要重新认证”消息

你的 Portal 刷新令牌已失效（密码更改、手动撤销或会话过期）。运行 `hermes auth add nous`，下一次请求将使用新凭证。旧令牌的隔离状态会在再次成功登录后自动清除。

### 想使用 Portal 未提供的特定提供商模型

Portal 将每个模型路由至适当后端——部分通过 OpenRouter，其他通过专有或次级提供商——因此 OpenRouter 支持的大多数模型通常都可用。如果某个模型没有出现在 `/model` 中，可以直接尝试 OpenRouter 风格的 slug：

```bash
/model anthropic/claude-opus-4.6
```

如果某个模型确实缺失，请[创建 issue](https://github.com/NousResearch/hermes-agent/issues)——我们将 Portal 目录呈现给 Hermes，缺口通常意味着有可更新的路由配置。

### 账单没有出现在我的 Portal 账户中

先检查 `hermes portal info`——如果它显示你正使用其他提供商（`Model: currently openrouter` 而不是 `using Nous as inference provider`），说明你的本地配置已经偏离。运行 `hermes model`，选择 Nous Portal，下一次请求将通过你的订阅路由。

## 另请参阅

- **[Tool Gateway](/user-guide/features/tool-gateway)** —— 每项网关工具、逐工具配置和定价的完整详情
- **[Subscription proxy](/user-guide/features/subscription-proxy)** —— 从非 Hermes 工具（其他智能体、脚本、第三方客户端）使用你的 Portal 订阅
- **[语音模式](/user-guide/features/voice-mode)** —— 使用 Portal 的 OpenAI TTS 进行语音对话
- **[AI Providers](/integrations/providers)** —— 用于比较替代方案的完整提供商目录
- **[OAuth over SSH](/guides/oauth-over-ssh)** —— 从远程主机或仅浏览器环境登录
- **[Profiles](/user-guide/profiles)** —— 共享一个 Portal 登录的多个 Hermes 配置
