---
sidebar_position: 15
title: "Google Vertex AI"
description: "通过 Google Cloud Vertex AI 将 Hermes Agent 与 Gemini 配合使用——OAuth2 服务账号或 ADC、GCP 账单和配额，无需静态 API 密钥"
---

# Google Vertex AI

Hermes Agent 通过 Vertex 的 OpenAI 兼容端点支持 **Google Cloud Vertex AI 上的 Gemini 模型**。与 [Google AI Studio 提供商](/guides/google-gemini)（其使用静态 API 密钥访问 `generativelanguage.googleapis.com`）不同，Vertex 提供 **企业级速率限制和 GCP 账单/额度**；当你希望 Gemini 用量从 Google Cloud 账户扣除、而非使用 AI Studio 密钥时，它是正确的选择。

:::info Vertex 使用 OAuth2 认证，而非 API 密钥
Vertex 的标准端点**没有静态 API 密钥**。每个请求都需要由服务账号 JSON 或应用默认凭据（ADC）之一签发的短期 **OAuth2 访问令牌**（TTL 约为 1 小时）。Hermes 会为你签发并**自动刷新**这些令牌——你无需手动粘贴令牌。这就是为什么将临时令牌粘贴到自定义提供商的 `api_key` 字段不起作用：它会在会话中途过期。
:::

## 前提条件

- 一个 **Google Cloud 项目**，且已启用 **Vertex AI API** 并开通结算。
- **凭据**，以下之一：
  - 具有 `roles/aiplatform.user` 角色的**服务账号 JSON**密钥文件，或
  - 通过 `gcloud auth application-default login` 获取的**应用默认凭据**（ADC）（或者在 GCP VM 上运行时使用元数据服务器）。
- **`google-auth`**——首次选择 Vertex 时会自动安装（延迟安装）。如果失败，请运行 `hermes setup` 修复托管安装。

## 快速开始

```bash
# 选项 A——服务账号 JSON（推荐用于服务器 / 网关）
echo "VERTEX_CREDENTIALS_PATH=/path/to/service-account.json" >> ~/.hermes/.env

# 选项 B——应用默认凭据（适合本地开发）
gcloud auth application-default login

# 选择 Vertex 作为提供商
hermes model
# → 选择“More providers...” → “Google Vertex AI”
# → 输入你的 GCP 项目 ID（或留空以使用凭据中的项目 ID）
# → 选择区域（默认：global）
# → 选择 Gemini 模型

# 开始聊天
hermes chat
```

## 配置

Vertex 按敏感性划分其设置：

- **凭据路径**是指向密钥的指针，存放在 `~/.hermes/.env` 中。
- **项目 ID 和区域**是非敏感路由设置，存放在 `~/.hermes/config.yaml` 中。

`~/.hermes/.env`：

```bash
# 使用其中之一（按此顺序检查）；省略两者以使用 ADC：
VERTEX_CREDENTIALS_PATH=/path/to/service-account.json
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

`~/.hermes/config.yaml`：

```yaml
model:
  default: google/gemini-3-flash-preview
  provider: vertex

vertex:
  project_id: my-gcp-project   # 留空 → 使用嵌入在凭据中的项目
  region: global               # Gemini 3.x 预览版要求使用 "global"
```

:::tip 环境变量优先于 config.yaml
`VERTEX_PROJECT_ID` 和 `VERTEX_REGION` 会覆盖 `config.yaml` 中的 `vertex.project_id` / `vertex.region` 值。将它们用于每个 shell 的覆盖；将持久设置保留在 `config.yaml` 中。
:::

### 认证工作原理

1. Hermes 按以下顺序解析凭据：`VERTEX_CREDENTIALS_PATH` → `GOOGLE_APPLICATION_CREDENTIALS` → ADC。
2. 它签发 OAuth2 访问令牌（`cloud-platform` 作用域）并缓存该令牌，在令牌距过期不足 5 分钟时刷新。
3. 该令牌会交给指向 Vertex 端点的标准 OpenAI 客户端：
   ```text
   https://aiplatform.googleapis.com/v1beta1/projects/{project}/locations/{region}/endpoints/openapi
   ```
   区域位置则使用 `{region}-aiplatform.googleapis.com` 主机。
4. 如果会话运行时间超过令牌有效期且某个请求返回 `401`，Hermes 会重新签发令牌并自动重试。在长期运行的网关中，如果 ADC 的刷新令牌本身已过期，Hermes 会在配置了服务账号 JSON 时回退使用它。

## 可用模型

Vertex 要求模型 ID 使用 `google/` 供应商前缀。`hermes model` 选择器提供：

| 模型 | ID |
|-------|----|
| Gemini 3.1 Pro Preview | `google/gemini-3.1-pro-preview` |
| Gemini 3 Pro Preview | `google/gemini-3-pro-preview` |
| Gemini 3 Flash Preview | `google/gemini-3-flash-preview` |
| Gemini 3.1 Flash Lite Preview | `google/gemini-3.1-flash-lite-preview` |
| Gemini 2.5 Pro | `google/gemini-2.5-pro` |
| Gemini 2.5 Flash | `google/gemini-2.5-flash` |

:::note Gemini 3.x 使用 `global` 区域
Gemini 3.x 预览模型通过 `global` 端点提供服务。区域端点（`us-central1` 等）可能对它们返回 404。除非你有特定理由固定某个区域，否则请保留 `region: global`。
:::

## 在会话中切换模型

```text
/model google/gemini-3-pro-preview
/model google/gemini-3-flash-preview
```

`/model` 会在已配置的提供商和模型之间切换；它不会收集新凭据。请先使用 `hermes model` 配置 Vertex。

## 推理 / 思考

Vertex 通过 OpenAI 兼容接口公开 Gemini 的思考预算。Hermes 会自动将其推理强度设置映射到 `extra_body.google.thinking_config`，因此 `reasoning_effort` 的工作方式与其他 Gemini 接口相同。

## 诊断

```bash
hermes doctor
```

诊断工具会报告 Vertex 凭据是否可解析（服务账号路径或 ADC），以及提供商是否已配置。

## 故障排除

### “Vertex AI credentials could not be resolved”

Hermes 未找到服务账号 JSON 或可用的 ADC。请在 `~/.hermes/.env` 中设置 `VERTEX_CREDENTIALS_PATH`，或运行 `gcloud auth application-default login`。如果凭据中未嵌入你的项目，请在 `config.yaml` 中设置 `vertex.project_id`。

### 未安装 `google-auth`

Hermes 会在你首次选择 Vertex 提供商时延迟安装它。如果失败，请运行 `hermes setup` 修复托管安装。

### Gemini 3.x 模型出现 404

你可能正在使用区域端点。请在 `config.yaml` 的 `vertex:` 部分中设置 `region: global`（或取消设置 `VERTEX_REGION`）。

### 403 / 权限被拒绝

服务账号（或你的 ADC 身份）需要在该项目中拥有 `roles/aiplatform.user` 角色，并且必须为该项目启用 Vertex AI API。

## 相关内容

- [Google Gemini (AI Studio)](/guides/google-gemini)——无需 GCP、使用静态 API 密钥的 Gemini
- [AWS Bedrock](/guides/aws-bedrock)——另一种原生云提供商集成
- [AI Providers](/integrations/providers)
- [Configuration](/user-guide/configuration)
