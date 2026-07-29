---
sidebar_position: 1
title: "快速入门"
description: "与 Hermes Agent 的第一次对话——从安装到开始聊天，不到 5 分钟"
---

# 快速入门

本指南将帮助你从零开始搭建一个经得起实际使用的 Hermes 环境。你将完成安装、选择提供商、验证聊天是否正常，并准确了解出现问题时该怎么做。

## 更喜欢看视频？

**Onchain AI Garage** 制作了一套涵盖安装、设置和基本命令的 Masterclass 演示——如果你更愿意跟着视频操作，它会是本页面的良好补充。更多内容请参阅完整的 [Hermes Agent 教程与使用案例](https://www.youtube.com/playlist?list=PLmpUb_PWAkDxewld5ZYyKifuHxgIbiq2d)播放列表。

<div style={{position: 'relative', paddingBottom: '56.25%', height: 0, overflow: 'hidden', maxWidth: '100%', marginBottom: '1.5rem'}}>
  <iframe
    style={{position: 'absolute', top: 0, left: 0, width: '100%', height: '100%'}}
    src="https://www.youtube-nocookie.com/embed/R3YOGfTBcQg"
    title="Hermes Agent Masterclass: Installation, Setup, Basic Commands"
    frameBorder="0"
    allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
    allowFullScreen
  ></iframe>
</div>

## 适用人群

- 刚接触 Hermes，并希望以最短路径获得可用环境
- 正在切换提供商，不想因配置错误浪费时间
- 正在为团队、机器人或持续运行的工作流设置 Hermes
- 已经厌倦“安装成功，但仍然什么都做不了”的情况

## 最快路径

选择与你的目标相符的一行：

| 目标 | 首先这样做 | 然后这样做 |
|---|---|---|
| 我只想让 Hermes 在自己的机器上运行 | `hermes setup` | 进行一次真实聊天并确认它能够回复 |
| 我已经知道要使用哪个提供商 | `hermes model` | 保存配置，然后开始聊天 |
| 我想要机器人或持续运行的环境 | CLI 正常运行后执行 `hermes gateway setup` | 连接 Telegram、Discord、Slack 或其他平台 |
| 我想使用本地或自托管模型 | `hermes model` → 自定义端点 | 验证端点、模型名称和上下文长度 |
| 我想要多提供商故障转移 | 先执行 `hermes model` | 仅在基础聊天正常运行后添加路由和故障转移 |

**经验法则：**如果 Hermes 无法完成一次正常聊天，请先不要添加更多功能。先让一次干净完整的对话正常运行，再逐层添加网关、cron、技能、语音或路由。

---

## 1. 安装 Hermes Agent
### 在 macOS 或 Windows 上使用 Hermes Desktop 安装器（推荐）
要轻松安装命令行和桌面应用程序，请从我们的网站[下载 Hermes Desktop 安装器](https://hermes-agent.nousresearch.com/)并运行。

### 不使用 Hermes Desktop：
如果只安装命令行版本而不安装 Hermes Desktop，请运行：

#### Linux / macOS / WSL2 / Android（Termux）
```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

#### Windows（原生）

在 PowerShell 中运行：
```powershell
iex (irm https://hermes-agent.nousresearch.com/install.ps1)
```

:::tip Android / Termux
如果你在手机上安装，请参阅专门的 [Termux 指南](./termux.md)，了解经过测试的手动安装路径、支持的附加功能以及当前 Android 特有的限制。
:::

安装完成后，重新加载 shell：

```bash
source ~/.bashrc   # or source ~/.zshrc
```

有关详细安装选项、前置要求和故障排除，请参阅[安装指南](./installation.md)。

## 2. 选择提供商

这是最重要的单项设置步骤。使用 `hermes model` 以交互方式完成选择：

```bash
hermes model
```

:::tip 最简单的路径：Nous Portal
一次订阅即可使用 300 多个模型和 [Tool Gateway](../user-guide/features/tool-gateway.md)（网页搜索、图像生成、TTS、云浏览器）。在全新安装中运行：

```bash
hermes setup --portal
```

这条命令会一次完成登录、将 Nous 设为提供商，并开启 Tool Gateway。
:::

:::info 设置模式
在全新安装中，`hermes setup` 提供三种模式：

- **快速设置（Nous Portal）**——免费 OAuth 登录，无需 API 密钥；设置一个模型和 Tool Gateway 工具。这是推荐的快速路径。
- **完整设置**——自行逐一配置每个提供商、工具和选项（使用你自己的密钥）。
- **空白起点**——除运行智能体所需的最低配置外，一切均以**关闭**状态启动：**提供商与模型、文件操作工具集和终端工具集**。不启用网页、浏览器、代码执行、视觉、记忆、委派、cron、技能、插件或 MCP 服务器——压缩、检查点、智能路由和记忆捕获也全部禁用。应用最低基线后，你可以从两条路径中选择一条：**以全部禁用的状态开始**（立即完成，使用最简智能体），或**逐项完成所有配置**（自行启用工具、技能、插件、MCP 和消息平台）。如果你希望使用一个最简、完全受控的智能体，并打算仅启用自己确切需要的功能，请选择此模式。

空白起点会写入明确的 `platform_toolsets.cli` 列表和 `agent.disabled_toolsets`，因此任何未选择的内容都绝不会加载——即使执行 `hermes update` 后也不会。以后可通过 `hermes tools` 重新启用任何内容，使用 `hermes skills opt-in --sync` 预置技能，或使用 `hermes setup agent` 调整设置。
:::

不错的默认选择：

| 提供商 | 简介 | 设置方式 |
|----------|-----------|---------------|
| **Nous Portal** | 订阅制，零配置 | 通过 `hermes model` 进行 OAuth 登录 |
| **OpenAI Codex** | ChatGPT OAuth，使用 Codex 模型 | 通过 `hermes model` 进行设备代码认证 |
| **Anthropic** | 直接使用 Claude 模型——Max 套餐 + 额外用量额度（OAuth），或使用 API 密钥按 token 付费 | `hermes model` → OAuth 登录（需要 Max + 额外额度），或 Anthropic API 密钥 |
| **OpenRouter** | 在众多模型间进行多提供商路由 | 输入你的 API 密钥 |
| **Fireworks AI** | 直接使用兼容 OpenAI 的模型 API | 设置 `FIREWORKS_API_KEY` |
| **Z.AI** | GLM / 智谱托管模型 | 设置 `GLM_API_KEY` / `ZAI_API_KEY`（也接受 `Z_AI_API_KEY`） |
| **Kimi / Moonshot** | Moonshot 托管的编程和聊天模型 | 设置 `KIMI_API_KEY`（或 Kimi-Coding 专用的 `KIMI_CODING_API_KEY`） |
| **Kimi / Moonshot China** | 中国区域的 Moonshot 端点 | 设置 `KIMI_CN_API_KEY` |
| **Arcee AI** | Trinity 模型 | 设置 `ARCEEAI_API_KEY` |
| **GMI Cloud** | 多模型直连 API | 设置 `GMI_API_KEY` |
| **MiniMax (OAuth)** | 通过浏览器 OAuth 使用 MiniMax 前沿模型——无需 API 密钥（`hermes_cli/models.py` 中的模型名称可能会随版本变化） | `hermes model` → MiniMax (OAuth) |
| **MiniMax** | MiniMax 国际版端点 | 设置 `MINIMAX_API_KEY` |
| **MiniMax China** | MiniMax 中国区域端点 | 设置 `MINIMAX_CN_API_KEY` |
| **Alibaba Cloud** | 通过 DashScope 使用 Qwen 模型 | 设置 `DASHSCOPE_API_KEY`（Qwen Coding Plan 也接受 `ALIBABA_CODING_PLAN_API_KEY`） |
| **Hugging Face** | 通过统一路由器使用 20 多个开放模型（Qwen、DeepSeek、Kimi 等） | 设置 `HF_TOKEN` |
| **AWS Bedrock** | 通过原生 Converse API 使用 Claude、Nova、Llama、DeepSeek | IAM 角色或 `aws configure`（[指南](../guides/aws-bedrock.md)） |
| **Azure Foundry** | Azure AI Foundry 托管的模型 | 设置 `AZURE_FOUNDRY_API_KEY` + `AZURE_FOUNDRY_BASE_URL` |
| **Google AI Studio** | 通过直连 API 使用 Gemini 模型 | 设置 `GOOGLE_API_KEY` / `GEMINI_API_KEY` |
| **xAI** | 通过直连 API 使用 Grok 模型 | 设置 `XAI_API_KEY` |
| **xAI Grok OAuth** | SuperGrok / Premium+ 订阅，无需 API 密钥 | `hermes model` → xAI Grok OAuth |
| **NovitaAI** | 多模型 API 网关 | 设置 `NOVITA_API_KEY` |
| **StepFun** | Step Plan 模型 | 设置 `STEPFUN_API_KEY` |
| **Xiaomi MiMo** | 小米托管的模型 | 设置 `XIAOMI_API_KEY` |
| **Tencent TokenHub** | 腾讯托管的模型 | 设置 `TOKENHUB_API_KEY` |
| **Ollama Cloud** | 托管的 Ollama 模型 | 设置 `OLLAMA_API_KEY` |
| **LM Studio** | 提供兼容 OpenAI API 的本地桌面应用 | 设置 `LM_API_KEY`（如果不是默认值，还需设置 `LM_BASE_URL`） |
| **Qwen OAuth** | Qwen Portal 浏览器 OAuth——无需 API 密钥 | `hermes model` → Qwen OAuth |
| **Kilo Code** | KiloCode 托管的模型 | 设置 `KILOCODE_API_KEY` |
| **OpenCode Zen** | 按量付费使用精选模型 | 设置 `OPENCODE_ZEN_API_KEY` |
| **OpenCode Go** | 每月 10 美元订阅使用开放模型 | 设置 `OPENCODE_GO_API_KEY` |
| **DeepSeek** | 直接访问 DeepSeek API | 设置 `DEEPSEEK_API_KEY` |
| **NVIDIA NIM** | 通过 build.nvidia.com 或本地 NIM 使用 Nemotron 模型 | 设置 `NVIDIA_API_KEY`（可选：`NVIDIA_BASE_URL`） |
| **GitHub Copilot** | GitHub Copilot 订阅（GPT-5.x、Claude、Gemini 等） | 通过 `hermes model` 进行 OAuth，或设置 `COPILOT_GITHUB_TOKEN` / `GH_TOKEN` |
| **GitHub Copilot ACP** | Copilot ACP 智能体后端（启动本地 `copilot` CLI） | `hermes model`（需要 `copilot` CLI + `copilot login`） |
| **Custom Endpoint** | VLLM、SGLang、Ollama 或任何兼容 OpenAI 的 API | 设置基础 URL + API 密钥 |

对于大多数初次使用的用户：选择一个提供商，并接受默认值，除非你清楚自己为何要更改它们。包含环境变量和设置步骤的完整提供商目录位于[提供商](../integrations/providers.md)页面。

:::caution 最低上下文：64K token
Hermes Agent 要求模型至少具备 **64,000 个 token** 的上下文。窗口较小的模型无法为多步骤工具调用工作流维持足够的工作记忆，并会在启动时被拒绝。大多数托管模型（Claude、GPT、Gemini、Qwen、DeepSeek）都能轻松满足要求。如果你运行本地模型，请将其上下文大小设为至少 64K（例如 llama.cpp 使用 `--ctx-size 65536`，Ollama 使用 `-c 65536`）。
:::

:::tip
你可以随时使用 `hermes model` 切换提供商——没有锁定。有关所有受支持提供商的完整列表和设置详情，请参阅 [AI 提供商](../integrations/providers.md)。
:::

### 设置的存储方式

Hermes 将秘密信息与普通配置分开存储：

- **秘密信息和 token** → `~/.hermes/.env`
- **非秘密设置** → `~/.hermes/config.yaml`

通过 CLI 是正确设置值的最简便方式：

```bash
hermes config set model anthropic/claude-opus-4.6
hermes config set terminal.backend docker
hermes config set OPENROUTER_API_KEY sk-or-...
```

正确的值会自动写入正确的文件。

## 3. 进行第一次聊天

```bash
hermes            # classic CLI
hermes --tui      # modern TUI (recommended)
```

你会看到欢迎横幅，其中显示你的模型、可用工具和技能。使用一个具体且容易验证的提示词：

:::tip 选择你的界面
Hermes 提供两种终端界面：经典的 `prompt_toolkit` CLI，以及较新的 [TUI](../user-guide/tui.md)，后者支持模态叠加层、鼠标选择和非阻塞输入。二者共享相同的会话、斜杠命令和配置——可分别使用 `hermes` 与 `hermes --tui` 进行尝试。
:::

```
Summarize this repo in 5 bullets and tell me what the main entrypoint is.
```

```
Check my current directory and tell me what looks like the main project file.
```

```
Help me set up a clean GitHub PR workflow for this codebase.
```

**成功的表现：**

- 横幅显示你选择的模型/提供商
- Hermes 回复时没有错误
- 它能够在需要时使用工具（终端、文件读取、网页搜索）
- 对话可以正常持续一轮以上

如果这些都正常，你已经通过了最困难的部分。

## 4. 验证会话是否正常

继续之前，请确认恢复功能正常：

```bash
hermes --continue    # Resume the most recent session
hermes -c            # Short form
```

这应该会让你回到刚才的会话。如果没有，请检查你是否位于同一配置档案，以及会话是否确实已保存。以后在同时处理多个环境或机器时，这一点很重要。

## 5. 尝试关键功能

### 使用终端

```
❯ What's my disk usage? Show the top 5 largest directories.
```

智能体会代表你运行终端命令并显示结果。

### 斜杠命令

输入 `/` 可查看包含所有命令的自动补全下拉列表：

| 命令 | 功能 |
|---------|-------------|
| `/help` | 显示所有可用命令 |
| `/tools` | 列出可用工具 |
| `/model` | 以交互方式切换模型 |
| `/personality pirate` | 尝试有趣的人格 |
| `/save` | 保存对话 |

### 多行输入

按 `Alt+Enter`、`Ctrl+J` 或 `Shift+Enter` 可添加新行。使用 `Shift+Enter` 需要终端将其作为独立序列发送（Kitty / foot / WezTerm / Ghostty 默认如此；iTerm2 / Alacritty / VS Code 终端则需启用 Kitty 键盘协议）。`Alt+Enter` 和 `Ctrl+J` 在所有终端中均可使用。

### 中断智能体

如果智能体耗时过长，请输入新消息并按 Enter——这会中断当前任务并切换到你的新指令。`Ctrl+C` 也可以。

## 6. 添加下一层功能

仅在基础聊天正常运行后进行。选择你需要的功能：

### 机器人或共享助手

```bash
hermes gateway setup    # Interactive platform configuration
```

连接 [Telegram](/user-guide/messaging/telegram)、[Discord](/user-guide/messaging/discord)、[Slack](/user-guide/messaging/slack)、[WhatsApp](/user-guide/messaging/whatsapp)、[Signal](/user-guide/messaging/signal)、[Email](/user-guide/messaging/email) 或 [Home Assistant](/user-guide/messaging/homeassistant)，或 [Microsoft Teams](/user-guide/messaging/teams)。

### 自动化和工具

- `hermes tools`——按平台调整工具访问权限
- `hermes skills`——浏览并安装可复用工作流
- Cron——仅在机器人或 CLI 环境稳定后使用

### 沙箱终端

为确保安全，请在 Docker 容器或远程服务器上运行智能体：

```bash
hermes config set terminal.backend docker    # Docker isolation
hermes config set terminal.backend ssh       # Remote server
```

对于 Docker 沙箱，你还可以启用**出口凭据注入代理**，使沙箱永远看不到你的真实 API 密钥——只会看到仅能从本地 TLS 拦截守护进程后方使用的不透明代理 token。请参阅[出口代理](../user-guide/egress/iron-proxy.md)。设置命令为 `hermes egress setup && hermes egress start`；`hermes setup terminal` 也会向 Docker 用户提示此功能。Modal、SSH、Daytona 和 Singularity 尚未接入。

### 语音模式

```bash
# From the Hermes install directory (the curl installer placed it at
# ~/.hermes/hermes-agent on Linux/macOS or %LOCALAPPDATA%\hermes\hermes-agent on Windows):
cd ~/.hermes/hermes-agent
uv pip install -e ".[voice]"
# Includes faster-whisper for free local speech-to-text
```

然后在 CLI 中执行：`/voice on`。按 `Ctrl+B` 录音。请参阅[语音模式](../user-guide/features/voice-mode.md)。

### 技能

技能是按需使用的说明文档，用于教 Hermes 完成特定任务——部署到 Kubernetes、创建 GitHub PR、微调模型、搜索 GIF。每个技能都是一个 `SKILL.md` 文件，其中包含名称、描述和分步流程。智能体会免费读取简短描述，并且仅在任务确实需要某项技能时加载其完整内容，因此添加技能不会让每次请求都变得臃肿。

Hermes 附带一套已经安装在 `~/.hermes/skills/` 中的捆绑技能目录。你可以从 Skills Hub 添加更多技能，也可以编写自己的技能。

**从 Hub 浏览和安装：**

```bash
hermes skills browse                      # list everything available
hermes skills search kubernetes           # find skills by keyword
hermes skills install openai/skills/k8s   # install one (runs a security scan first)
```

安装参数是 Hub 中的 `source/path` slug——`openai/skills/k8s` 表示 OpenAI 目录中的 `k8s` 技能。`hermes skills browse` 会显示要使用的确切 slug。

**使用技能**——每个已安装的技能都会自动成为斜杠命令：

```bash
/k8s deploy the staging manifest          # run the skill with a request
/k8s                                       # load it and let Hermes ask what you need
```

这在 CLI 和任何已连接的消息平台中都有效。你不必预先安装所有技能——在正常对话中，当任务与某项捆绑技能匹配时，智能体会自行选择正确的技能。

有关编写自己的技能、外部技能目录和完整 Hub 来源列表，请参阅[技能系统](../user-guide/features/skills.md)。

### MCP 服务器

```yaml
# Add to ~/.hermes/config.yaml
mcp_servers:
  github:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxx"
```

### 编辑器集成（ACP）

ACP 支持包含在标准 `[all]` 附加组件中，因此 curl 安装器已经包含它。只需运行：

```bash
hermes acp
```

（如果你安装时未包含 `[all]`，请先运行 `cd ~/.hermes/hermes-agent && uv pip install -e ".[acp]"`。）

请参阅 [ACP 编辑器集成](../user-guide/features/acp.md)。

---

## 常见故障模式

以下问题最容易浪费时间：

| 症状 | 可能的原因 | 修复方法 |
|---|---|---|
| Hermes 能打开，但回复为空或异常 | 提供商认证或模型选择有误 | 再次运行 `hermes model`，并确认提供商、模型和认证信息 |
| 自定义端点“能用”，但返回乱码 | 基础 URL 或模型名称错误，或实际上并不兼容 OpenAI | 先在独立客户端中验证该端点 |
| 网关已启动，但无人能向它发送消息 | 机器人 token、允许列表或平台设置不完整 | 重新运行 `hermes gateway setup` 并检查 `hermes gateway status` |
| `hermes --continue` 找不到旧会话 | 切换了配置档案，或会话从未保存 | 检查 `hermes sessions list` 并确认你位于正确的配置档案 |
| 模型不可用或出现奇怪的故障转移行为 | 提供商路由或故障转移设置过于激进 | 在基础提供商稳定之前关闭路由 |
| `hermes doctor` 标记出配置问题 | 配置值缺失或过时 | 修复配置，并在添加功能前重新测试普通聊天 |

## 恢复工具包

感觉有问题时，请按以下顺序操作：

1. `hermes doctor`
2. `hermes model`
3. `hermes setup`
4. `hermes sessions list`
5. `hermes --continue`
6. `hermes gateway status`

这一顺序能让你快速从“感觉坏了”恢复到已知状态。

---

## 快速参考

| 命令 | 说明 |
|---------|-------------|
| `hermes` | 开始聊天 |
| `hermes model` | 选择你的 LLM 提供商和模型 |
| `hermes tools` | 配置每个平台启用哪些工具 |
| `hermes setup` | 完整设置向导（一次配置所有内容） |
| `hermes doctor` | 诊断问题 |
| `hermes update` | 更新至最新版本 |
| `hermes gateway` | 启动消息网关 |
| `hermes --continue` | 恢复上一次会话 |

## 后续步骤

- **[CLI 指南](../user-guide/cli.md)**——掌握终端界面
- **[配置](../user-guide/configuration.md)**——自定义你的环境
- **[消息网关](../user-guide/messaging/index.md)**——连接 Telegram、Discord、Slack、WhatsApp、Signal、Email、Home Assistant、Teams 等平台
- **[工具与工具集](../user-guide/features/tools.md)**——探索可用功能
- **[AI 提供商](../integrations/providers.md)**——完整的提供商列表和设置详情
- **[技能系统](../user-guide/features/skills.md)**——可复用工作流与知识
- **[技巧与最佳实践](../guides/tips.md)**——高级用户技巧
