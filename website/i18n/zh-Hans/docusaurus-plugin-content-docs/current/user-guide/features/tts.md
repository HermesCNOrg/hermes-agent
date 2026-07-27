---
sidebar_position: 9
title: "语音与 TTS"
description: "跨所有平台的文字转语音与语音消息转录"
---

# 语音与 TTS

Hermes Agent 支持跨所有消息平台的文字转语音（TTS）输出和语音消息转录（STT）。

:::tip Nous 订阅用户
如果你拥有付费的 [Nous Portal](https://portal.nousresearch.com) 订阅，OpenAI TTS 可通过 **[Tool Gateway](tool-gateway.md)** 使用，无需单独的 OpenAI API 密钥。新安装可运行 `hermes setup --portal` 登录并一次性开启所有 gateway 工具；已有安装可通过 `hermes model` 或 `hermes tools` 选择 **Nous Subscription** 仅启用 TTS。
:::

## 文字转语音（TTS）

支持十个提供商将文字转换为语音：

| 提供商 | 质量 | 费用 | API 密钥 |
|----------|---------|------|---------|
| **Edge TTS**（默认） | 良好 | 免费 | 无需 |
| **ElevenLabs** | 优秀 | 付费 | `ELEVENLABS_API_KEY` |
| **OpenAI TTS** | 良好 | 付费 | `VOICE_TOOLS_OPENAI_KEY` |
| **MiniMax TTS** | 优秀 | 付费 | `MINIMAX_API_KEY` |
| **Mistral (Voxtral TTS)** | 优秀 | 付费 | `MISTRAL_API_KEY` |
| **Google Gemini TTS** | 优秀 | 免费额度 | `GEMINI_API_KEY` |
| **xAI TTS** | 优秀 | 付费 | `XAI_API_KEY` |
| **NeuTTS** | 良好 | 免费（本地） | 无需 |
| **KittenTTS** | 良好 | 免费（本地） | 无需 |
| **Piper** | 良好 | 免费（本地） | 无需 |

### 平台投递方式

| 平台 | 投递方式 | 格式 |
|----------|----------|--------|
| Telegram | 语音气泡（内联播放） | Opus `.ogg` |
| Discord | 语音气泡（Opus/OGG），回退为文件附件 | Opus/MP3 |
| WhatsApp | 音频文件附件 | MP3 |
| CLI | 保存至 `~/.hermes/audio_cache/` | MP3 |

### 配置

```yaml
# In ~/.hermes/config.yaml
tts:
  provider: "edge"              # "edge" | "elevenlabs" | "openai" | "minimax" | "mistral" | "gemini" | "xai" | "neutts" | "kittentts" | "piper"
  speed: 1.0                    # Global speed multiplier (provider-specific settings override this)
  edge:
    voice: "en-US-AriaNeural"   # 322 voices, 74 languages
    speed: 1.0                  # Converted to rate percentage (+/-%)
  elevenlabs:
    voice_id: "pNInz6obpgDQGcFmaJgB"  # Adam
    model_id: "eleven_multilingual_v2"
  openai:
    model: "gpt-4o-mini-tts"
    voice: "alloy"              # alloy, echo, fable, onyx, nova, shimmer
    base_url: "https://api.openai.com/v1"  # Override for OpenAI-compatible TTS endpoints
    speed: 1.0                  # 0.25 - 4.0
  minimax:
    model: "speech-2.8-hd"     # speech-2.8-hd (default), speech-2.8-turbo
    voice_id: "English_Graceful_Lady"  # See https://platform.minimax.io/faq/system-voice-id
    speed: 1                    # 0.5 - 2.0
    vol: 1                      # 0 - 10
    pitch: 0                    # -12 - 12
  mistral:
    model: "voxtral-mini-tts-2603"
    voice_id: "c69964a6-ab8b-4f8a-9465-ec0925096ec8"  # Paul - Neutral (default)
  gemini:
    model: "gemini-2.5-flash-preview-tts"  # or gemini-3.1-flash-tts-preview
    voice: "Kore"               # 30 prebuilt voices: Zephyr, Puck, Kore, Enceladus, Gacrux, etc.
    audio_tags: false           # Enable hidden Gemini 3.1 TTS audio-tag insertion
    persona_prompt_file: ""      # Optional Markdown/text file with Gemini voice direction
  xai:
    voice_id: "eve"             # or a custom voice ID — see docs below
    language: "en"              # ISO 639-1 code
    sample_rate: 24000          # 22050 / 24000 (default) / 44100 / 48000
    bit_rate: 128000            # MP3 bitrate; only applies when codec=mp3
    # base_url: "https://api.x.ai/v1"   # Override via XAI_BASE_URL env var
  neutts:
    ref_audio: ''
    ref_text: ''
    model: neuphonic/neutts-air-q4-gguf
    device: cpu
  kittentts:
    model: KittenML/kitten-tts-nano-0.8-int8   # 25MB int8; also: kitten-tts-micro-0.8 (41MB), kitten-tts-mini-0.8 (80MB)
    voice: Jasper                               # Jasper, Bella, Luna, Bruno, Rosie, Hugo, Kiki, Leo
    speed: 1.0                                  # 0.5 - 2.0
    clean_text: true                            # Expand numbers, currencies, units
  piper:
    voice: en_US-lessac-medium                  # voice name (auto-downloaded) OR absolute path to .onnx
    # voices_dir: ''                            # default: ~/.hermes/cache/piper-voices/
    # use_cuda: false                           # requires onnxruntime-gpu
    # length_scale: 1.0                         # 2.0 = twice as slow
    # noise_scale: 0.667
    # noise_w_scale: 0.8
    # volume: 1.0                               # 0.5 = half as loud
    # normalize_audio: true
```

**速度控制**：全局 `tts.speed` 值默认应用于所有提供商。每个提供商可用自身的 `speed` 设置覆盖它（例如 `tts.openai.speed: 1.5`）。提供商级别的速度优先于全局值。默认值为 `1.0`（正常速度）。

### Gemini 角色提示

Gemini TTS 可以遵循自然语言的表现力指令。将 `tts.gemini.persona_prompt_file` 设置为描述语音角色的本地 Markdown 或文本文件。该文件可以包含 Gemini 风格的章节，例如 `AUDIO PROFILE`、`SCENE`、`DIRECTOR'S NOTES`、`SAMPLE CONTEXT` 和 `TRANSCRIPT`。

如果文件包含 `{transcript}` 或 `{{ transcript }}`，Hermes 会将该占位符替换为实时的 TTS 文本。否则，Hermes 会自动附加一个带标签的 `TRANSCRIPT` 章节。角色提示保留在本地，不会显示在聊天回复中。

```yaml
tts:
  provider: gemini
  gemini:
    voice: Algieba
    persona_prompt_file: ~/.hermes/tts/butler-voice.md
```

### Gemini 音频标签

Gemini 3.1 Flash TTS 支持自由形式的方括号音频标签，例如 `[whispers]`、`[excitedly]`、`[very slow]`、`[laughs]` 以及其他表现力投递说明。启用 `tts.gemini.audio_tags` 后，Hermes 会在 Gemini TTS 之前运行一次隐藏的重写。重写过程会将内联标签插入到 TTS 脚本中；可见的聊天回复保持不变。

```yaml
tts:
  provider: gemini
  gemini:
    model: gemini-3.1-flash-tts-preview
    audio_tags: true
```

重写过程使用 `auxiliary.tts_audio_tags`，默认使用你的主聊天模型。如果你希望由更便宜或更快的模型处理标签插入，可以覆盖该辅助任务。

### 输入长度限制

每个提供商都有文档记录的单次请求输入字符上限。Hermes 在调用提供商前会截断文本，确保请求不会因长度错误而失败：

| 提供商 | 默认上限（字符数） |
|----------|---------------------|
| Edge TTS | 5000 |
| OpenAI | 4096 |
| xAI | 15000 |
| MiniMax | 10000 |
| Mistral | 4000 |
| Google Gemini | 32000 |
| ElevenLabs | 取决于模型（见下文） |
| NeuTTS | 2000 |
| KittenTTS | 2000 |
| Piper | 5000 |

**ElevenLabs** 根据配置的 `model_id` 选择上限：

| `model_id` | 上限（字符数） |
|------------|-------------|
| `eleven_flash_v2_5` | 40000 |
| `eleven_flash_v2` | 30000 |
| `eleven_multilingual_v2`（默认）、`eleven_multilingual_v1`、`eleven_english_sts_v2`、`eleven_english_sts_v1` | 10000 |
| `eleven_v3`、`eleven_ttv_v3` | 5000 |
| 未知模型 | 回退至提供商默认值（10000） |

**按提供商覆盖**，在 TTS 配置的提供商节下使用 `max_text_length:`：

```yaml
tts:
  openai:
    max_text_length: 8192   # raise or lower the provider cap
```

仅接受正整数。零、负数、非数字或布尔值将回退至提供商默认值，因此错误的配置不会意外禁用截断。

### Telegram 语音气泡与 ffmpeg

Telegram 语音气泡需要 Opus/OGG 音频格式：

- **OpenAI、ElevenLabs 和 Mistral** 原生输出 Opus，无需额外配置
- **Edge TTS**（默认）输出 MP3，需要 **ffmpeg** 进行转换
- **MiniMax TTS** 输出 MP3，需要 **ffmpeg** 转换以在 Telegram 显示语音气泡
- **Google Gemini TTS** 输出原始 PCM，使用 **ffmpeg** 直接编码为 Opus 以在 Telegram 显示语音气泡
- **xAI TTS** 输出 MP3，需要 **ffmpeg** 转换以在 Telegram 显示语音气泡
- **NeuTTS** 输出 WAV，同样需要 **ffmpeg** 转换以在 Telegram 显示语音气泡
- **KittenTTS** 输出 WAV，同样需要 **ffmpeg** 转换以在 Telegram 显示语音气泡
- **Piper** 输出 WAV，同样需要 **ffmpeg** 转换以在 Telegram 显示语音气泡

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Fedora
sudo dnf install ffmpeg
```

若未安装 ffmpeg，Edge TTS、MiniMax TTS、NeuTTS、KittenTTS 和 Piper 的音频将作为普通音频文件发送（可播放，但显示为矩形播放器而非语音气泡）。

:::tip
如果你希望在不安装 ffmpeg 的情况下使用语音气泡，请切换至 OpenAI、ElevenLabs 或 Mistral 提供商。
:::

### xAI 自定义声音（声音克隆）

xAI 支持克隆你的声音并将其用于 TTS。在 [xAI Console](https://console.x.ai/team/default/voice/voice-library) 中创建自定义声音，然后在配置中设置生成的 `voice_id`：

```yaml
tts:
  provider: xai
  xai:
    voice_id: "nlbqfwie"   # your custom voice ID
```

有关录制、支持格式和限制的详细信息，请参阅 [xAI Custom Voices 文档](https://docs.x.ai/developers/model-capabilities/audio/custom-voices)。

### Piper（本地，支持 44 种语言）

Piper 是来自 Open Home Foundation（Home Assistant 维护者）的快速本地神经网络 TTS 引擎。它完全在 CPU 上运行，支持 **44 种语言**的预训练声音，无需 API 密钥。

**通过 `hermes tools` 安装** → Voice & TTS → Piper — Hermes 会自动为你运行 `pip install piper-tts`。或手动安装：`pip install piper-tts`。

**切换至 Piper：**

```yaml
tts:
  provider: piper
  piper:
    voice: en_US-lessac-medium
```

首次对未在本地缓存的声音进行 TTS 调用时，Hermes 会运行 `python -m piper.download_voices <name>` 并将模型（约 20-90MB，取决于质量等级）下载至 `~/.hermes/cache/piper-voices/`。后续调用将复用已缓存的模型。

**选择声音。** [完整声音目录](https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/VOICES.md) 涵盖英语、西班牙语、法语、德语、意大利语、荷兰语、葡萄牙语、俄语、波兰语、土耳其语、中文、阿拉伯语、印地语等——每种语言均有 `x_low` / `low` / `medium` / `high` 质量等级。可在 [rhasspy.github.io/piper-samples](https://rhasspy.github.io/piper-samples/) 试听声音样本。

**使用预下载的声音。** 将 `tts.piper.voice` 设置为以 `.onnx` 结尾的绝对路径：

```yaml
tts:
  piper:
    voice: /path/to/my-custom-voice.onnx
```

**高级参数**（`tts.piper.length_scale` / `noise_scale` / `noise_w_scale` / `volume` / `normalize_audio`、`use_cuda`）与 Piper 的 `SynthesisConfig` 一一对应。在较旧的 `piper-tts` 版本上这些参数会被忽略。

### 自定义命令提供商

如果你想使用的 TTS 引擎未被原生支持（VoxCPM、MLX-Kokoro、XTTS CLI、声音克隆脚本，或任何其他暴露 CLI 的引擎），你可以将其作为**命令类型提供商**接入，无需编写任何 Python 代码。Hermes 将输入文本写入临时 UTF-8 文件，运行你的 shell 命令，并读取命令生成的音频文件。

在 `tts.providers.<name>` 下声明一个或多个提供商，并通过 `tts.provider: <name>` 在它们之间切换——与切换 `edge` 和 `openai` 等内置提供商的方式相同。

```yaml
tts:
  provider: voxcpm                 # pick any name under tts.providers
  providers:
    voxcpm:
      type: command
      command: "voxcpm --ref ~/voice.wav --text-file {input_path} --out {output_path}"
      output_format: mp3
      timeout: 180
      voice_compatible: true       # try to deliver as a Telegram voice bubble

    mlx-kokoro:
      type: command
      command: "python -m mlx_kokoro --in {input_path} --out {output_path} --voice {voice}"
      voice: af_sky
      output_format: wav

    piper-custom:                  # native Piper also supports custom .onnx via tts.piper.voice
      type: command
      command: "piper -m /path/to/custom.onnx -f {output_path} < {input_path}"
      output_format: wav
```

#### 示例：Doubao（中文 seed-tts-2.0）

如需通过字节跳动的 [seed-tts-2.0](https://www.volcengine.com/docs/6561/1257544) 双向流式 API 实现高质量中文 TTS，请安装 [`doubao-speech`](https://pypi.org/project/doubao-speech/) PyPI 包并将其作为命令提供商接入：

```bash
pip install doubao-speech
export VOLCENGINE_APP_ID="your-app-id"
export VOLCENGINE_ACCESS_TOKEN="your-access-token"
```

```yaml
tts:
  provider: doubao
  providers:
    doubao:
      type: command
      command: "doubao-speech say --text-file {input_path} --out {output_path}"
      output_format: mp3
      max_text_length: 1024
      timeout: 30
```

凭据来自你的 shell 环境（`VOLCENGINE_APP_ID` / `VOLCENGINE_ACCESS_TOKEN`）或 `~/.doubao-speech/config.yaml`。通过在命令中添加 `--voice zh-female-warm`（或 `doubao-speech list-voices` 中的任何其他别名）来选择声音。`doubao-speech` 还内置了流式 ASR——有关 Hermes 集成，请参阅[下方的 STT 章节](#example-doubao--volcengine-asr)。源码和完整文档：[github.com/Hypnus-Yuan/doubao-speech](https://github.com/Hypnus-Yuan/doubao-speech)。

#### 占位符

你的命令模板可以引用以下占位符。Hermes 在渲染时会替换它们，并根据上下文（裸值 / 单引号 / 双引号）对每个值进行 shell 转义，因此包含空格和其他 shell 敏感字符的路径是安全的。

| 占位符 | 含义 |
|------------------|------------------------------------------------------|
| `{input_path}` | Hermes 写入的临时 UTF-8 文本文件路径 |
| `{text_path}` | `{input_path}` 的别名 |
| `{output_path}` | 命令必须写入音频的路径 |
| `{format}` | `mp3` / `wav` / `ogg` / `flac` |
| `{voice}` | `tts.providers.<name>.voice`，未设置时为空 |
| `{model}` | `tts.providers.<name>.model` |
| `{speed}` | 解析后的速度倍率（提供商级别或全局） |

使用 `{{` 和 `}}` 表示字面大括号。

#### 可选键

| 键 | 默认值 | 含义 |
|--------------------|---------|------------------------------------------------------------------------------------------------------------|
| `timeout` | `120` | 秒数；超时后进程树将被终止（Unix `killpg`，Windows `taskkill /T`）。 |
| `output_format` | `mp3` | `mp3` / `wav` / `ogg` / `flac` 之一。若 Hermes 选择路径，则从输出扩展名自动推断。 |
| `voice_compatible` | `false` | 为 `true` 时，Hermes 通过 ffmpeg 将 MP3/WAV 输出转换为 Opus/OGG，使 Telegram 渲染语音气泡。 |
| `max_text_length` | `5000` | 渲染命令前，输入将被截断至此长度。 |
| `voice` / `model` | 空 | 仅作为占位符值传递给命令。 |

#### 行为说明

- **内置名称始终优先。** `tts.providers.openai` 条目永远不会覆盖原生 OpenAI 提供商，因此任何用户配置都无法静默替换内置提供商。
- **默认投递方式为文档。** 命令提供商在所有平台上均以普通音频附件投递。通过 `voice_compatible: true` 按提供商选择加入语音气泡投递。
- **命令失败会暴露给 Agent。** 非零退出码、空输出或超时均会返回包含命令 stderr/stdout 的错误，便于你从对话中调试提供商。
- **设置了 `command:` 时，`type: command` 为默认值。** 显式写出 `type: command` 是良好实践，但非必须；包含非空 `command` 字符串的条目会被视为命令提供商。
- **`{input_path}` / `{text_path}` 可互换。** 使用在你的命令中读起来更自然的那个。

#### 安全性

命令类型提供商会以你的用户权限运行你配置的任何 shell 命令。Hermes 会对占位符值进行转义并强制执行配置的超时，但命令模板本身是受信任的本地输入——请像对待 PATH 中的 shell 脚本一样对待它。

### Python 插件提供商

对于无法用单个 shell 命令表达的 TTS 引擎——没有 CLI 的 Python SDK、流式引擎、声音列表 API、OAuth 刷新认证——可通过 `ctx.register_tts_provider()` 注册 Python 插件。该插件与[自定义命令提供商](#custom-command-providers)注册表**共存**（不替换）；选择适合你引擎的接入方式。

#### 如何选择

| 你的后端具有… | 使用 |
|---|---|
| 单个 CLI，从文件/stdin 读取文本并将音频写入文件/stdout | **命令提供商**（无需 Python） |
| 两三个通过 shell 管道串联的 CLI | **命令提供商** |
| 仅有 Python SDK，没有 CLI | **插件** |
| 你希望分块投递的流式字节（生成中的语音气泡） | **插件**（覆盖 `stream()`） |
| `hermes setup` 使用的声音列表 API | **插件**（覆盖 `list_voices()`） |
| OAuth 刷新流程（非静态 bearer token） | **插件** |

内置提供商始终优先，命令提供商优先于同名插件——因此插件可以安全地注册任何非内置名称，无需担心覆盖现有配置。

#### 最小插件

将以下内容放入 `~/.hermes/plugins/my-tts/`：

`plugin.yaml`：
```yaml
name: my-tts
version: 0.1.0
description: "My custom Python TTS backend"
```

`__init__.py`：
```python
from agent.tts_provider import TTSProvider


class MyTTSProvider(TTSProvider):
    @property
    def name(self) -> str:
        return "my-tts"  # what tts.provider matches against

    @property
    def display_name(self) -> str:
        return "My Custom TTS"

    def is_available(self) -> bool:
        # Return False when credentials/deps are missing — picker skips
        # this row but the dispatcher still routes here on explicit config.
        import os
        return bool(os.environ.get("MY_TTS_API_KEY"))

    def synthesize(self, text, output_path, *, voice=None, model=None,
                   speed=None, format="mp3", **extra) -> str:
        # Write audio bytes to output_path, return the path.
        # Raise on failure — the dispatcher converts exceptions to a
        # standard error envelope.
        import my_tts_sdk
        client = my_tts_sdk.Client()
        audio_bytes = client.synthesize(text=text, voice=voice or "default")
        with open(output_path, "wb") as f:
            f.write(audio_bytes)
        return output_path


def register(ctx):
    ctx.register_tts_provider(MyTTSProvider())
```

启用它（`hermes plugins enable my-tts`），将 `tts.provider` 指向它（在 `config.yaml` 中设置 `tts.provider: my-tts`），`text_to_speech` 工具将通过你的插件路由。

#### 可选 hook

在你的提供商类上覆盖以下方法以获得更丰富的集成：

- `list_voices()` → 返回 `{id, display, language, gender, preview_url}` 字典列表，显示在 `hermes tools` 中。
- `list_models()` → 返回 `{id, display, languages, max_text_length}` 字典列表。
- `get_setup_schema()` → 返回 `{name, badge, tag, env_vars: [{key, prompt, url}]}` 以驱动 `hermes tools` / `hermes setup` 中的选择器行。若不提供，插件仍可正常工作，但其在选择器中的行信息会很简略。
- `stream(text, *, voice, model, format, **extra)` → 迭代器，产出音频字节用于流式投递（默认抛出 `NotImplementedError`）。
- `voice_compatible` 属性 → 若你的输出与 Opus 兼容且 gateway 应将其作为语音气泡投递，则设为 `True`（默认 `False` = 普通音频附件）。

完整的抽象基类（含文档字符串）请参阅 `agent/tts_provider.py`。

## 语音消息转录（STT）

在 Telegram、Discord、WhatsApp、Slack 或 Signal 上发送的语音消息会被自动转录并作为文本注入对话。Agent 将转录内容视为普通文本。

| 提供商 | 质量 | 费用 | API 密钥 |
|----------|---------|------|---------| 
| **本地 Whisper**（默认） | 良好 | 免费 | 无需 |
| **Groq Whisper API** | 良好至最佳 | 免费额度 | `GROQ_API_KEY` |
| **OpenAI Whisper API** | 良好至最佳 | 付费 | `VOICE_TOOLS_OPENAI_KEY` 或 `OPENAI_API_KEY` |

:::info 零配置
安装了 `faster-whisper` 后，本地转录即可开箱即用。若不可用，Hermes 也可使用常见安装位置（如 `/opt/homebrew/bin`）的本地 `whisper` CLI，或通过 `HERMES_LOCAL_STT_COMMAND` 指定的自定义命令。
:::

### 配置

```yaml
# In ~/.hermes/config.yaml
stt:
  provider: "local"           # "local" | "groq" | "openai" | "mistral" | "xai"
  local:
    model: "base"             # tiny, base, small, medium, large-v3
  openai:
    model: "whisper-1"        # whisper-1, gpt-4o-mini-transcribe, gpt-4o-transcribe
  mistral:
    model: "voxtral-mini-latest"  # voxtral-mini-latest, voxtral-mini-2602
  xai:
    model: "grok-stt"         # xAI Grok STT
```

### 提供商详情

**本地（faster-whisper）** — 通过 [faster-whisper](https://github.com/SYSTRAN/faster-whisper) 在本地运行 Whisper。默认使用 CPU，有 GPU 时使用 GPU。模型大小：

| 模型 | 大小 | 速度 | 质量 |
|-------|------|-------|---------|
| `tiny` | ~75 MB | 最快 | 基础 |
| `base` | ~150 MB | 快 | 良好（默认） |
| `small` | ~500 MB | 中等 | 较好 |
| `medium` | ~1.5 GB | 较慢 | 优秀 |
| `large-v3` | ~3 GB | 最慢 | 最佳 |

**Groq API** — 需要 `GROQ_API_KEY`。当你需要免费托管 STT 选项时，是良好的云端备选方案。

**OpenAI API** — 优先使用 `VOICE_TOOLS_OPENAI_KEY`，回退至 `OPENAI_API_KEY`。支持 `whisper-1`、`gpt-4o-mini-transcribe` 和 `gpt-4o-transcribe`。

**Mistral API（Voxtral Transcribe）** — 需要 `MISTRAL_API_KEY`。使用 Mistral 的 [Voxtral Transcribe](https://docs.mistral.ai/capabilities/audio/speech_to_text/) 模型。支持 13 种语言、说话人分离和词级时间戳。通过 `cd ~/.hermes/hermes-agent && uv pip install -e ".[mistral]"` 安装。

**xAI Grok STT** — 需要 `XAI_API_KEY`。以 multipart/form-data 格式发送至 `https://api.x.ai/v1/stt`。如果你已在使用 xAI 进行聊天或 TTS 并希望一个 API 密钥搞定一切，这是个好选择。自动检测顺序将其排在 Groq 之后——显式设置 `stt.provider: xai` 可强制使用。

**自定义本地 CLI 回退** — 若你希望 Hermes 直接调用本地转录命令，请设置 `HERMES_LOCAL_STT_COMMAND`。命令模板支持 `{input_path}`、`{output_dir}`、`{language}` 和 `{model}` 占位符。你的命令必须在 `{output_dir}` 下某处写入 `.txt` 转录文件。

#### 示例：Doubao / Volcengine ASR

如果你使用 [`doubao-speech`](https://pypi.org/project/doubao-speech/) 进行 Doubao TTS（见[上文](#example-doubao-chinese-seed-tts-20)），同一个包也可通过本地命令 STT 接口处理语音转文字：

```bash
pip install doubao-speech
export VOLCENGINE_APP_ID="your-app-id"
export VOLCENGINE_ACCESS_TOKEN="your-access-token"
export HERMES_LOCAL_STT_COMMAND='doubao-speech transcribe {input_path} --out {output_dir}/transcript.txt'
```

```yaml
stt:
  provider: local_command
```

Hermes 将传入的语音消息写入 `{input_path}`，运行命令，并读取 `{output_dir}` 下生成的 `.txt` 文件。语言由 Volcengine bigmodel 端点自动检测。

### 回退行为

若配置的提供商不可用，Hermes 会自动回退：
- **本地 faster-whisper 不可用** → 在云端提供商之前尝试本地 `whisper` CLI 或 `HERMES_LOCAL_STT_COMMAND`
- **未设置 Groq 密钥** → 回退至本地转录，然后是 OpenAI
- **未设置 OpenAI 密钥** → 回退至本地转录，然后是 Groq
- **未设置 Mistral 密钥/SDK** → 在自动检测中跳过；回退至下一个可用提供商
- **无可用提供商** → 语音消息直接传递，并向用户给出准确说明

### STT 自定义命令提供商

如果你想使用的 STT 引擎未被原生支持（Doubao ASR、NVIDIA Parakeet、whisper.cpp 编译版本、开源 SenseVoice CLI，或任何其他暴露 shell 命令的引擎），可以将其作为**命令类型提供商**接入，无需编写任何 Python 代码。Hermes 会针对音频文件运行你的 shell 命令并读取返回的转录文本。

在 `stt.providers.<name>` 下声明一个或多个提供商，并通过 `stt.provider: <name>` 在它们之间切换——形式与 TTS [命令提供商注册表](#custom-command-providers)相同，方向改为输入=音频 → 输出=转录。

```yaml
stt:
  provider: parakeet                # pick any name under stt.providers
  providers:
    parakeet:
      type: command
      command: "parakeet-asr --model nvidia/parakeet-tdt-0.6b-v2 --in {input_path} --out {output_path}"
      format: txt
      language: en
      timeout: 300

    whispercpp:
      type: command
      command: "whisper-cli -m ~/models/ggml-large-v3.bin -f {input_path} -otxt -of {output_dir}/transcript"
      format: txt

    sensevoice:
      type: command
      command: "sensevoice-cli {input_path} --json | tee {output_path}"
      format: json
```

这补充了原有的 `HERMES_LOCAL_STT_COMMAND` 逃生口——该环境变量通过内置的 `local_command` 路径仍然可以原样使用。当需要**多个**由 shell 驱动的 STT 引擎、希望通过 `stt.provider` 选择的名称，或需要按提供商设置 `language` / `model` / `timeout` 时，请使用 `stt.providers.<name>`。

#### STT 占位符

你的命令模板可以引用以下占位符。Hermes 在渲染时会替换它们，并根据上下文（裸值 / 单引号 / 双引号）对每个值进行 shell 转义，因此包含空格的路径是安全的。

| 占位符 | 含义 |
|-------------------|----------------------------------------------------------------------|
| `{input_path}` | 输入音频文件的绝对路径（原始位置，只读） |
| `{output_path}` | 命令应将转录写入的绝对路径 |
| `{output_dir}` | `{output_path}` 的父目录（便于 whisper 风格的工具使用） |
| `{format}` | 配置的输出格式：`txt` / `json` / `srt` / `vtt` |
| `{language}` | 配置的语言代码（默认为 `en`） |
| `{model}` | `stt.providers.<name>.model`，未设置时为空 |

使用 `{{` 和 `}}` 表示字面大括号（在命令中嵌入 JSON 片段时很方便）。

#### 转录结果的读取方式

命令成功退出后：

1. 如果 `{output_path}` 存在且非空 → Hermes 将其作为 UTF-8 文本读取。
2. 否则，如果命令写入了 stdout → Hermes 使用 stdout。
3. 否则 → 错误："Command STT provider wrote no output file and produced no stdout"。

这让你既可以使用写入文件的 CLI（`whisper-cli`、`parakeet-asr`），也可以使用输出转录到 stdout 的 curl 风格单行命令（`curl … | jq -r .text`）。

对于 `format: json` / `srt` / `vtt`，Hermes 将原始文件内容作为 `transcript` 字段返回。从 JSON 中提取 `.text` 不属于运行器的职责范围——要么配置 `format: txt`，要么在下游对 JSON 进行后处理。

#### STT 命令提供商可选键

| 键 | 默认值 | 含义 |
|-----------------|---------|------------------------------------------------------------------------------------------------------|
| `timeout` | `300` | 秒数；超时后进程树将被终止（Unix `start_new_session`，Windows `taskkill /T`）。 |
| `format` | `txt` | `txt` / `json` / `srt` / `vtt` 之一。设置 `{output_path}` 的扩展名。 |
| `language` | `en` | 传递给 `{language}`。默认使用 `stt.language`，然后回退至 `en`。 |
| `model` | 空 | 传递给 `{model}`。`transcribe_audio()` 的 `model=` 参数会覆盖此值。 |

#### STT 命令提供商行为说明

- **内置名称始终优先。** 声明 `stt.providers.openai: type: command` 不会覆盖真正的 OpenAI Whisper 处理器。内置名称在命令提供商解析器运行之前就会被短路处理。
- **进程树清理。** 超过 `timeout` 的命令，其整个进程树都会被终止，而不仅仅是 shell 包装器。长期运行的 ASR 管道中派生模型加载子进程的情况也能被可靠地清理。
- **Shell 转义是自动的。** `'…'` 内的占位符会进行单引号安全转义；`"…"` 内的会进行 `$`/`` ` ``/`"` 转义；引号外的会使用 `shlex.quote`。不要对占位符值进行预转义。

#### STT 命令提供商安全性

该 shell 命令以与 Hermes 相同的用户身份运行，拥有完整的文件系统访问权限——与 `tts.providers.<name>: type: command` 和 `HERMES_LOCAL_STT_COMMAND` 相同的信任模型。只声明来自你信任的来源的命令提供商。

### STT Python 插件提供商

对于既非内置又无法用 shell 命令表达的 STT 引擎（需要 Python SDK、OAuth 刷新认证、流式分块等），可以通过 `ctx.register_transcription_provider()` 注册 Python 插件。该插件与 6 个内置提供商（`local`、`local_command`、`groq`、`openai`、`mistral`、`xai`）以及 `stt.providers.<name>: type: command` 注册表**共存**——内置提供商保留其原生实现且在名称冲突时始终优先；命令提供商优先于同名插件（配置比插件安装更本地化）。

#### 如何选择（STT）

| 后端具有… | 使用 |
|--------------------------------------------------------------|------------------------------------------------------------------|
| 单个 shell 命令，输入音频文件，输出文本 | `stt.providers.<name>: type: command`（无需 Python） |
| 只需要旧式的单命令逃生口 | `HERMES_LOCAL_STT_COMMAND` 环境变量（为向后兼容保留） |
| 仅提供 Python SDK，没有 CLI | `register_transcription_provider()` 插件 |
| OAuth 刷新认证、流式分块、声音列表元数据 | `register_transcription_provider()` 插件 |
| 内置提供商已覆盖（`local`、`groq`、`openai` 等） | 设置 `stt.provider: <name>`——内置提供商已内联 |

#### 解析顺序

1. **`stt.provider` 是内置名称** → 内置分发。**始终优先。**
2. **`stt.provider` 匹配设置了 `command:` 的 `stt.providers.<name>`** → 命令提供商运行器（见 [STT 自定义命令提供商](#stt-custom-command-providers)）。优先于同名插件。
3. **`stt.provider` 匹配插件注册的 `TranscriptionProvider`** → 插件分发：
   - 如果插件的 `is_available()` 返回 `False`（缺少凭据或 SDK），调用会返回标识该插件的不可用错误信息——**不是**通用的"No STT provider available"消息。
   - 否则，调用插件的 `transcribe()`，参数包括 `model`（从公开的 `model=` 参数获取，回退至 `stt.<provider>.model`）和 `language`（从 `stt.<provider>.language` 获取）。
4. **无匹配** → "No STT provider available"错误。

#### 按提供商的配置命名空间

插件从 `config.yaml` 中的 `stt.<provider>` 读取其按提供商的配置，与内置提供商读取 `stt.openai.model` / `stt.mistral.model` 的方式相同：

```yaml
stt:
  provider: my-stt
  my-stt:
    model: whisper-large-v3
    language: ja          # forwarded as language= to transcribe()
    # any other plugin-specific keys go here; read them via your
    # own config.yaml access in __init__/is_available/transcribe
```

分发器会将 `model` 和 `language` 从该节中转发；其他内容，插件可以自行读取。

#### 最小插件

将以下内容放入 `~/.hermes/plugins/my-stt/`：

`plugin.yaml`：
```yaml
name: my-stt
version: 0.1.0
description: "My custom Python STT backend"
```

`__init__.py`：
```python
from agent.transcription_provider import TranscriptionProvider


class MySTTProvider(TranscriptionProvider):
    @property
    def name(self) -> str:
        return "my-stt"  # what stt.provider matches against

    @property
    def display_name(self) -> str:
        return "My Custom STT"

    def is_available(self) -> bool:
        # Return False when credentials/deps are missing — picker skips
        # this row but the dispatcher still routes here on explicit config.
        import os
        return bool(os.environ.get("MY_STT_API_KEY"))

    def transcribe(self, file_path, *, model=None, language=None, **extra):
        # Return the standard transcribe envelope:
        #   {"success": bool, "transcript": str, "provider": str, "error": str}
        # Do NOT raise — convert exceptions to the error envelope so the
        # gateway/CLI caller sees a consistent shape on failure.
        try:
            import my_stt_sdk
            client = my_stt_sdk.Client()
            text = client.transcribe(open(file_path, "rb"))
            return {
                "success": True,
                "transcript": text,
                "provider": "my-stt",
            }
        except Exception as exc:
            return {
                "success": False,
                "transcript": "",
                "error": f"my-stt failed: {exc}",
                "provider": "my-stt",
            }


def register(ctx):
    ctx.register_transcription_provider(MySTTProvider())
```

启用它（`hermes plugins enable my-stt`），在 `config.yaml` 中设置 `stt.provider: my-stt`，语音消息转录将通过你的插件路由。

#### 可选 hook

在你的提供商类上覆盖以下方法以获得更丰富的集成：

- `list_models()` → 返回 `{id, display, languages, max_audio_seconds}` 字典列表。
- `default_model()` → 当用户未覆盖模型时返回的字符串。
- `get_setup_schema()` → 返回 `{name, badge, tag, env_vars: [{key, prompt, url}]}` 以驱动 `hermes tools` / `hermes setup` 中的选择器行（STT 的选择器分类尚未发布——此元数据可供插件使用，以保持向前兼容）。

完整的抽象基类（含文档字符串）请参阅 `agent/transcription_provider.py`。
