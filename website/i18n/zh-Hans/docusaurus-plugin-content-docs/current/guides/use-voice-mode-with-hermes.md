---
sidebar_position: 8
title: "将语音模式与 Hermes 配合使用"
description: "一份实用指南，介绍如何在 CLI、Telegram、Discord 和 Discord 语音频道中设置和使用 Hermes 语音模式"
---

# 将语音模式与 Hermes 配合使用

本指南是 [语音模式功能参考](/user-guide/features/voice-mode) 的实用补充。

如果功能页面说明了语音模式能做什么，本指南则展示如何真正用好它。

:::tip
[Nous Portal](/integrations/nous-portal) 通过一次 OAuth 同时提供 LLM 和 TTS——语音模式无需额外凭据即可端到端运行。
:::

## 语音模式适合做什么

语音模式尤其适合以下情况：
- 你希望在 CLI 中进行免手操作的工作流
- 你希望在 Telegram 或 Discord 中获得语音回复
- 你希望 Hermes 待在 Discord 语音频道中进行实时对话
- 你希望在走动时快速记录想法、调试或来回交流，而不是打字

## 选择你的语音模式设置

Hermes 中实际上有三种不同的语音体验。

| 模式 | 最适合 | 平台 |
|---|---|---|
| 交互式麦克风循环 | 编程或研究时个人免手操作 | CLI |
| 聊天中的语音回复 | 常规消息之外的语音回复 | Telegram、Discord |
| 实时语音频道机器人 | 在 VC 中进行群组或个人实时对话 | Discord 语音频道 |

一个合适的路径是：
1. 先让文本功能正常工作
2. 然后启用语音回复
3. 如果希望获得完整体验，最后再使用 Discord 语音频道

## 第 1 步：先确保普通 Hermes 能正常工作

在使用语音模式前，请验证：
- Hermes 能启动
- 你的提供商已配置
- Agent 能正常回答文本提示

```bash
hermes
```

询问一个简单的问题：

```text
你有哪些可用工具？
```

如果这一步尚不稳定，请先修复文本模式。

## 第 2 步：安装正确的额外组件

### CLI 麦克风 + 播放

```bash
cd ~/.hermes/hermes-agent && uv pip install -e ".[voice]"
```

### 消息平台

```bash
cd ~/.hermes/hermes-agent && uv pip install -e ".[messaging]"
```

### 高级 ElevenLabs TTS

```bash
cd ~/.hermes/hermes-agent && uv pip install -e ".[tts-premium]"
```

### 本地 NeuTTS（可选）

```bash
python -m pip install -U neutts[all]
```

### 所有组件

```bash
cd ~/.hermes/hermes-agent && uv pip install -e ".[all]"
```

## 第 3 步：安装系统依赖项

### macOS

```bash
brew install portaudio ffmpeg opus
brew install espeak-ng
```

### Ubuntu / Debian

```bash
sudo apt install portaudio19-dev ffmpeg libopus0
sudo apt install espeak-ng
```

这些依赖的重要原因：
- `portaudio` → CLI 语音模式的麦克风输入/播放
- `ffmpeg` → TTS 和消息传递的音频转换
- `opus` → Discord 语音编解码器支持
- `espeak-ng` → NeuTTS 的音素化后端

## 第 4 步：选择 STT 和 TTS 提供商

Hermes 同时支持本地和云端语音技术栈。

### 最简单 / 最便宜的设置

使用本地 STT 和免费的 Edge TTS：
- STT 提供商：`local`
- TTS 提供商：`edge`

这通常是最适合开始使用的方案。

### 环境文件示例

添加到 `~/.hermes/.env`：

```bash
# 云端 STT 选项（local 不需要密钥）
GROQ_API_KEY=***
VOICE_TOOLS_OPENAI_KEY=***

# 高级 TTS（可选）
ELEVENLABS_API_KEY=***
```

### 提供商建议

#### 语音转文本

- `local` → 隐私和零成本使用的最佳默认选择
- `groq` → 非常快速的云端转写
- `openai` → 合适的付费备用方案

#### 文本转语音

- `edge` → 免费，对大多数用户来说已足够好
- `neutts` → 免费的本地/设备端 TTS
- `elevenlabs` → 最佳质量
- `openai` → 良好的折中方案
- `mistral` → 多语言，原生 Opus

### 如果你使用 `hermes setup`

如果你在设置向导中选择 NeuTTS，Hermes 会检查是否已经安装 `neutts`。如果缺失，向导会告知你 NeuTTS 需要 Python 包 `neutts` 和系统包 `espeak-ng`，会提供为你安装它们的选项，通过你的平台包管理器安装 `espeak-ng`，然后运行：

```bash
python -m pip install -U neutts[all]
```

如果你跳过该安装或安装失败，向导会回退到 Edge TTS。

## 第 5 步：推荐配置

```yaml
voice:
  record_key: "ctrl+b"
  max_recording_seconds: 120
  auto_tts: false
  beep_enabled: true
  silence_threshold: 200
  silence_duration: 3.0

stt:
  provider: "local"
  local:
    model: "base"

tts:
  provider: "edge"
  edge:
    voice: "en-US-AriaNeural"
```

这是适合大多数人的保守默认配置。

如果你想改用本地 TTS，请将 `tts` 块切换为：

```yaml
tts:
  provider: "neutts"
  neutts:
    ref_audio: ''
    ref_text: ''
    model: neuphonic/neutts-air-q4-gguf
    device: cpu
```

## 用例 1：CLI 语音模式

## 启用它

启动 Hermes：

```bash
hermes
```

在 CLI 内：

```text
/voice on
```

### 录音流程

默认按键：
- `Ctrl+B`

工作流：
1. 按下 `Ctrl+B`
2. 说话
3. 等待静音检测自动停止录音
4. Hermes 转写并回复
5. 如果 TTS 已开启，它会朗读答案
6. 循环可自动重新开始，以便持续使用

### 实用命令

```text
/voice
/voice on
/voice off
/voice tts
/voice status
```

### 适合 CLI 的工作流

#### 即时调试

说：

```text
我一直遇到 docker 权限错误。帮我调试。
```

然后继续免手操作：
- “再读一遍最后一个错误”
- “用更简单的方式解释根本原因”
- “现在给我确切的修复方法”

#### 研究 / 头脑风暴

非常适合：
- 一边走动一边思考
- 口述尚未成形的想法
- 要求 Hermes 实时整理你的思路

#### 无障碍 / 少打字的会话

如果打字不方便，语音模式是保持完整 Hermes 循环的最快方式之一。

## 调整 CLI 行为

### 静音阈值

如果 Hermes 开始/停止录音过于频繁，请调整：

```yaml
voice:
  silence_threshold: 250
```

阈值更高 = 灵敏度更低。

### 静音时长

如果你在句子之间经常停顿，请增加：

```yaml
voice:
  silence_duration: 4.0
```

### 录音按键

如果 `Ctrl+B` 与你的终端或 tmux 使用习惯冲突：

```yaml
voice:
  record_key: "ctrl+space"
```

## 用例 2：Telegram 或 Discord 中的语音回复

此模式比完整语音频道更简单。

Hermes 保持为普通聊天机器人，但可以朗读回复。

### 启动网关

```bash
hermes gateway
```

### 开启语音回复

在 Telegram 或 Discord 中：

```text
/voice on
```

或

```text
/voice tts
```

### 模式

| 模式 | 含义 |
|---|---|
| `off` | 仅文本 |
| `voice_only` | 仅当用户发送语音时朗读 |
| `all` | 朗读每一条回复 |

### 何时使用哪种模式

- 如果你只希望对源自语音的消息获得语音回复，请使用 `/voice on`
- 如果你始终希望使用完整的语音助手，请使用 `/voice tts`

### 适合消息平台的工作流

#### 手机上的 Telegram 助手

适用于：
- 你远离机器时
- 你想发送语音消息并快速获得语音回复时
- 你希望 Hermes 像便携式研究或运维助手一样工作时

#### 带语音输出的 Discord 私信

当你希望进行私人交互，而不受服务器频道提及行为影响时很有用。

## 用例 3：Discord 语音频道

这是最高级的模式。

Hermes 加入 Discord VC，监听用户语音，将其转写，运行普通 Agent 流水线，并在频道中朗读回复。

## 必需的 Discord 权限

除普通文本机器人设置外，请确保机器人具有：
- 连接
- 说话
- 最好具有使用语音活动

还应在 Developer Portal 中启用特权意图：
- Presence Intent
- Server Members Intent
- Message Content Intent

## 加入和离开

在机器人所在的 Discord 文本频道中：

```text
/voice join
/voice leave
/voice status
```

### 加入后会发生什么

- 用户在 VC 中说话
- Hermes 检测语音边界
- 转写内容会发布到关联的文本频道
- Hermes 以文本和音频回复
- 文本频道是发出 `/voice join` 的频道

### Discord VC 使用的最佳实践

- 保持 `DISCORD_ALLOWED_USERS` 范围严格
- 起初使用专用的机器人/测试频道
- 尝试 VC 模式前，先验证 STT 和 TTS 能在普通文本聊天语音模式中正常工作

## 语音质量建议

### 最佳质量设置

- STT：本地 `large-v3` 或 Groq `whisper-large-v3`
- TTS：ElevenLabs

### 最佳速度 / 便利性设置

- STT：本地 `base` 或 Groq
- TTS：Edge

### 最佳零成本设置

- STT：本地
- TTS：Edge

## 常见故障模式

### “未找到音频设备”

安装 `portaudio`。

### “机器人已加入但什么也听不到”

检查：
- 你的 Discord 用户 ID 位于 `DISCORD_ALLOWED_USERS` 中
- 你没有被静音
- 特权意图已启用
- 机器人具有连接/说话权限

### “它能转写但不朗读”

检查：
- TTS 提供商配置
- ElevenLabs 或 OpenAI 的 API 密钥 / 配额
- 用于 Edge 转换路径的 `ffmpeg` 安装

### “Whisper 输出乱码”

尝试：
- 更安静的环境
- 更高的 `silence_threshold`
- 不同的 STT 提供商/模型
- 更短、更清晰的表达

### “它在私信中能用，但在服务器频道中不能用”

这通常是提及策略导致的。

默认情况下，除非另有配置，机器人在 Discord 服务器文本频道中需要 `@mention`。

## 建议的第一周设置

如果你希望以最短路径获得成功：

1. 让文本 Hermes 正常工作
2. 运行 `hermes setup voice` 以启用语音支持
3. 使用本地 STT + Edge TTS 的 CLI 语音模式
4. 然后在 Telegram 或 Discord 中启用 `/voice on`
5. 仅在此之后，再尝试 Discord VC 模式

这一推进方式能使调试范围保持较小。

## 接下来阅读

- [语音模式功能参考](/user-guide/features/voice-mode)
- [消息网关](/user-guide/messaging)
- [Discord 设置](/user-guide/messaging/discord)
- [Telegram 设置](/user-guide/messaging/telegram)
- [配置](/user-guide/configuration)
