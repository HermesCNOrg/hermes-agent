---
title: 图像生成
description: 通过 FAL.ai 生成图像——支持 11 个模型，包括 FLUX 2、GPT Image（1.5 和 2）、Nano Banana Pro、Ideogram、Recraft V4 Pro、Krea 2 等；可通过 `hermes tools` 选择。
sidebar_label: 图像生成
sidebar_position: 6
---

# 图像生成

Hermes Agent 通过 FAL.ai 根据文本提示生成图像。开箱即支持 11 个模型，每个模型在速度、质量和成本方面都有不同的权衡。活动模型可由用户通过 `hermes tools` 配置，并会持久保存到 `config.yaml`。

## 支持的模型

| 模型 | 速度 | 优势 | 价格 |
|---|---|---|---|
| `fal-ai/flux-2/klein/9b` *（默认）* | `<1s` | 快速、文本清晰 | $0.006/MP |
| `fal-ai/flux-2-pro` | ~6s | 工作室级照片写实效果 | $0.03/MP |
| `fal-ai/z-image/turbo` | ~2s | 英文/中文双语，60 亿参数 | $0.005/MP |
| `fal-ai/nano-banana-pro` | ~8s | Gemini 3 Pro、推理深度、文本渲染 | $0.15/张（1K） |
| `fal-ai/gpt-image-1.5` | ~15s | 提示词遵循能力 | $0.034/张 |
| `fal-ai/gpt-image-2` | ~20s | 最先进的文本渲染 + CJK、具备世界认知的照片写实效果 | $0.04–0.06/张 |
| `fal-ai/ideogram/v3` | ~5s | 最佳排版能力 | $0.03–0.09/张 |
| `fal-ai/recraft/v4/pro/text-to-image` | ~8s | 设计、品牌系统、可直接用于生产 | $0.25/张 |
| `fal-ai/qwen-image` | ~12s | 基于 LLM、复杂文本 | $0.02/MP |
| `fal-ai/krea/v2/medium/text-to-image` | ~15-25s | 插画、动漫、绘画、富有表现力/艺术性的风格 | $0.030–0.035/张 |
| `fal-ai/krea/v2/large/text-to-image` | ~25-60s | 照片写实效果、原始纹理质感（运动模糊、颗粒、胶片） | $0.060–0.065/张 |

价格为 FAL 在撰写时的定价；请在 [fal.ai](https://fal.ai/) 查看当前价格。

## 设置

:::tip Nous 订阅者
如果你拥有付费的 [Nous Portal](https://portal.nousresearch.com) 订阅，无需 FAL API 密钥，即可通过 **[Tool Gateway](tool-gateway.md)** 使用图像生成。你的模型选择会在两条路径之间保留。新安装可运行 `hermes setup --portal`，以登录并一次性启用全部网关工具；现有安装可通过 `hermes tools` 选择 **Nous Subscription** 作为图像生成后端。

如果托管网关针对特定模型返回 `HTTP 4xx`，则该模型尚未在 Portal 端被代理——智能体会告知你这一点，并提供补救步骤（设置 `FAL_KEY` 以直接访问，或者选择其他模型）。
:::

### 获取 FAL API 密钥

1. 在 [fal.ai](https://fal.ai/) 注册
2. 从控制台生成 API 密钥

### 配置并选择模型

运行 tools 命令：

```bash
hermes tools
```

导航至 **🎨 Image Generation**，选择你的后端（Nous Subscription 或 FAL.ai），随后选择器会以列对齐的表格显示所有支持的模型——使用方向键导航，按 Enter 选择：

```
  Model                          Speed    Strengths                    Price
  fal-ai/flux-2/klein/9b         <1s      Fast, crisp text             $0.006/MP   ← currently in use
  fal-ai/flux-2-pro              ~6s      Studio photorealism          $0.03/MP
  fal-ai/z-image/turbo           ~2s      Bilingual EN/CN, 6B          $0.005/MP
  ...
```

你的选择会保存到 `config.yaml`：

```yaml
image_gen:
  model: fal-ai/flux-2/klein/9b
  use_gateway: false            # 使用 Nous Subscription 时为 true
```

### GPT-Image 质量

`fal-ai/gpt-image-1.5` 和 `fal-ai/gpt-image-2` 的请求质量固定为 `medium`（在 1024×1024 时约为 $0.034–$0.06/张）。我们不会将 `low` / `high` 档位作为面向用户的选项开放，以便 Nous Portal 的计费在所有用户之间保持可预测——各档位之间的成本差距为 3–22 倍。如果你想要更便宜的选项，请选择 Klein 9B 或 Z-Image Turbo；如果你想要更高质量，请使用 Nano Banana Pro 或 Recraft V4 Pro。

## 用法

面向智能体的 schema 有意保持最小化——模型会采用你已配置的内容：

```
Generate an image of a serene mountain landscape with cherry blossoms
```

```
Create a square portrait of a wise old owl — use the typography model
```

```
Make me a futuristic cityscape, landscape orientation
```

## 图像到图像 / 编辑

当活动模型支持时，同一个 `image_generate` 工具也会**编辑现有图像**——传入源图像，后端便会自动路由至其编辑端点（与 `video_generate` 处理图像到视频的方式相同）。
省略源图像时，它就是普通的文本到图像。

```
Take this photo and make it a rainy Tokyo street at night → <image>
```

```
Blend these two product shots into one hero image → <image1> <image2>
```

两个输入驱动编辑：

- **`image_url`** —— 要编辑/转换的主源图像（公开 URL 或本地路径）。
- **`reference_image_urls`** —— 额外的风格/构图参考图像（每个模型均有数量上限）。

### 哪些后端支持编辑

| 后端 | 图像到图像 | 参考图上限 | 方式 |
|---|---|---|---|
| **FAL.ai**（下列具备编辑能力的模型） | ✓ | 最多 9 张 | 路由至模型的 `/edit` 端点 |
| **OpenAI**（`gpt-image-2`） | ✓ | 最多 16 张 | `images.edit()` |
| **xAI**（Grok Imagine） | ✓ | 1 张 | `/v1/images/edits`（`grok-imagine-image-quality`） |
| **Krea**（`Krea 2`） | ✓ | 最多 10 张 | 参考图引导生成（`image_style_references`） |
| **OpenAI（Codex 认证）** | ✓ | 最多 16 张 | 带有 `input_image` 内容部分的 Codex Responses `image_generation` 工具 |

具有编辑端点的 FAL 模型包括：`flux-2/klein/9b`、`flux-2-pro`、
`nano-banana-pro`、`gpt-image-1.5`、`gpt-image-2`、`ideogram/v3` 和
`qwen-image`。纯文本到图像的 FAL 模型（`z-image/turbo`、`recraft`、
`krea/*`）会拒绝图像输入，并显示明确的错误信息，引导你选择具备编辑能力的模型。

:::note OpenAI（Codex 认证）为尽力而为功能

Codex 表面（`chatgpt.com/backend-api/codex`）将 `image_generation`
作为聊天模型可能调用的工具托管，而 Hermes 无法强制调用该工具——后端会拒绝托管工具的每一种 `tool_choice` 形式，因此请求依赖指令来引导模型。当宿主模型拒绝调用该工具时，调用会以 `empty_response` 失败。也有报告称，托管图像工具是否完全可访问会因账户而异。如果你需要图像生成以确定性的方式工作，请改为配置 **OpenAI**（API 密钥）、**FAL** 或 **xAI** 后端。

:::

活动模型的编辑能力会在运行时显示于工具说明中，因此智能体在调用工具前就知道 `image_url` 是否会得到支持。

## 宽高比

从智能体的视角，每个模型都接受相同的三种宽高比。内部会自动填入每个模型的原生尺寸规格：

| 智能体输入 | image_size（flux/z-image/qwen/recraft/ideogram） | aspect_ratio（nano-banana-pro） | image_size（gpt-image-1.5） | image_size（gpt-image-2） |
|---|---|---|---|---|
| `landscape` | `landscape_16_9` | `16:9` | `1536x1024` | `landscape_4_3`（1024×768） |
| `square` | `square_hd` | `1:1` | `1024x1024` | `square_hd`（1024×1024） |
| `portrait` | `portrait_16_9` | `9:16` | `1024x1536` | `portrait_4_3`（768×1024） |

GPT Image 2 映射至 4:3 预设而非 16:9，因为其最小像素数为 655,360——`landscape_16_9` 预设（1024×576 = 589,824）会被拒绝。

此转换在 `_build_fal_payload()` 中完成——智能体代码无需了解各模型的 schema 差异。

## 自动放大

通过 FAL **Clarity Upscaler** 进行的放大会按模型进行控制：

| 模型 | 放大？ | 原因 |
|---|---|---|
| `fal-ai/flux-2-pro` | ✓ | 向后兼容性（它曾是选择器出现前的默认模型） |
| 其他所有模型 | ✗ | 快速模型会失去其亚秒级的价值主张；高分辨率模型无需放大 |

当放大运行时，会使用以下设置：

| 设置 | 值 |
|---|---|
| 放大倍数 | 2× |
| Creativity | 0.35 |
| Resemblance | 0.6 |
| Guidance scale | 4 |
| Inference steps | 18 |

如果放大失败（网络问题、速率限制），将自动返回原始图像。

## 内部工作方式

1. **模型解析** —— `_resolve_fal_model()` 从 `config.yaml` 读取 `image_gen.model`，回退至 `FAL_IMAGE_MODEL` 环境变量，最后回退至 `fal-ai/flux-2/klein/9b`。
2. **构建载荷** —— `_build_fal_payload()` 将你的 `aspect_ratio` 转换为模型的原生格式（预设枚举、宽高比枚举或 GPT 字面量），合并模型的默认参数，应用任何调用方覆盖，然后按模型的 `supports` 白名单进行过滤，以确保绝不会发送不支持的键。
3. **提交** —— `_submit_fal_request()` 通过直接 FAL 凭据或托管 Nous 网关进行路由。
4. **放大** —— 仅当模型的元数据具有 `upscale: True` 时运行。
5. **交付** —— 最终图像 URL 返回给智能体，智能体会发出 `MEDIA:<url>` 标签，由平台适配器将其转换为原生媒体。

## 调试

启用调试日志：

```bash
export IMAGE_TOOLS_DEBUG=true
```

调试日志会写入 `./logs/image_tools_debug_<session_id>.json`，其中包含每次调用的详细信息（模型、参数、时序、错误）。

## 平台交付

| 平台 | 交付方式 |
|---|---|
| **CLI** | 图像 URL 以 Markdown `![](url)` 形式打印——单击即可打开 |
| **Telegram** | 图片消息，提示词作为说明文字 |
| **Discord** | 嵌入消息中 |
| **Slack** | URL 由 Slack 展开 |
| **WhatsApp** | 媒体消息 |
| **其他** | 纯文本中的 URL |

## 限制

- **需要凭据**才能使用活动后端（FAL `FAL_KEY` / Nous Subscription、`OPENAI_API_KEY`、xAI OAuth、`KREA_API_KEY`）
- **编辑取决于模型** —— 图像到图像仅适用于具备编辑能力的模型（见上表）；仅文本到图像的模型会拒绝图像输入，并显示明确错误
- **临时 URL** —— 后端返回的托管 URL 会在数小时/数天后过期；Hermes 会将其具体化到本地缓存，因此过期后交付仍能工作
- **每个模型的约束** —— 某些模型不支持 `seed`、`num_inference_steps` 等。`supports` / `edit_supports` 过滤器会静默丢弃不支持的参数；这是预期行为
