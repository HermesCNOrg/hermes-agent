---
sidebar_position: 1
title: "快速入门"
description: "与 Hermes Agent 的第一次对话——从安装到聊天，不到 5 分钟"
---

# 快速入门

本指南将带你从零开始完成一个能经受实际使用的 Hermes 配置。安装、选择提供商、验证可工作的聊天，并在出问题时明确知道该做什么。

## 更喜欢观看？

**Onchain AI Garage** 制作了一份涵盖安装、设置和基本命令的 Masterclass 演示；如果你更愿意通过视频跟着操作，它是本页的良好补充。更多内容请见完整的 [Hermes Agent 教程与使用案例](https://www.youtube.com/playlist?list=PLmpUb_PWAkDxewld5ZYyKifuHxgIbiq2d) 播放列表。

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

## 适用对象

- 全新用户，想走最短路径完成可用设置
- 正在切换提供商，不想把时间浪费在配置错误上
- 正在为团队、机器人或始终运行的工作流设置 Hermes
- 厌倦了“它安装好了，但仍然什么都做不了”

## 最快路径

选择与你目标相符的行：

| 目标 | 先做这个 | 然后做这个 |
|---|---|---|
| 我只想让 Hermes 在机器上运行 | `hermes setup` | 运行一次真实聊天并验证它会响应 |
| 我已经知道我的提供商 | `hermes model` | 保存配置，然后开始聊天 |
| 我想要一个机器人或始终运行的设置 | CLI 可用后运行 `hermes gateway setup` | 连接 Telegram、Discord、Slack 或其他平台 |
| 我想要本地或自托管模型 | `hermes model` → 自定义端点 | 验证端点、模型名称和上下文长度 |
| 我想要多提供商回退 | 先运行 `hermes model` | 仅在基础聊天可用后再添加路由和回退 |

**经验法则：**如果 Hermes 不能完成正常聊天，先不要添加更多功能。先让一次干净的对话正常工作，再逐层添加 gateway、cron、skills、语音或路由。

---

## 1. 安装 Hermes Agent
### 在 macOS 或 Windows 上使用 Hermes Desktop 安装器（推荐）
要轻松安装命令行和桌面应用，请从我们的网站[下载 Hermes Desktop 安装器](https://hermes-agent.nousresearch.com/)并运行它。

### 不使用 Hermes Desktop：
对于不使用 Hermes Desktop、仅命令行的安装，请运行：

#### Linux / macOS / WSL2 / Android (Termux)
```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

#### Windows（原生）

在 powershell 中运行：
```powershell
iex (irm https://hermes-agent.nousresearch.com/install.ps1)
```

:::tip Android / Termux
如果你在手机上安装，请参阅专门的 [Termux 指南](./termux.md)，了解经过测试的手动路径、受支持的附加功能和当前 Android 特有的限制。
:::

完成后，重新加载 shell：

```bash
source ~/.bashrc   # 或 source ~/.zshrc
```

有关详细安装选项、前提条件和故障排除，请参阅[安装指南](./installation.md)。

## 2. 选择提供商

这是最重要的设置步骤。使用 `hermes model` 以交互方式完成选择：

```bash
hermes model
```

:::tip 最简单的路径：Nous Portal
一个订阅涵盖 300 多个模型和 [Tool Gateway](../user-guide/features/tool-gateway.md)（网页搜索、图像生成、TTS、云浏览器）。在全新安装中：

```bash
hermes setup --portal
```

它会登录、将 Nous 设为你的提供商，并通过一条命令开启 Tool Gateway。
:::

:::info 设置模式
在全新安装中，`hermes setup` 提供三种模式：

- **快速设置（Nous Portal）** — 免费 OAuth 登录，无需 API 密钥；设置模型和 Tool Gateway 工具。推荐的快速路径。
- **完整设置** — 自己逐项完成每个提供商、工具和选项（自带密钥）。
- **空白状态** — 除了运行 agent 所需的最低限度外，所有功能都以**关闭**状态开始：**提供商和模型、文件操作工具集以及终端工具集**。没有网页、浏览器、代码执行、视觉、记忆、委派、cron、skills、插件或 MCP 服务器；压缩、检查点、智能路由和记忆捕获也全部禁用。在应用最小基线后，你可以选择两条路径之一：**在所有功能禁用的情况下开始**（立即以最小 agent 完成），或者**逐项完成所有配置**（选择加入工具、skills、插件、MCP 和消息）。当你需要一个最小、完全可控的 agent，且只打算启用所需功能时，请选择此项。

空白状态会写入明确的 `platform_toolsets.cli` 列表和 `agent.disabled_toolsets`，因此你未选择的任何内容都不会加载——即使在 `hermes update` 之后也是如此。稍后可用 `hermes tools` 重新启用任何内容，用 `hermes skills opt-in --sync` 初始化 skills，或用 `hermes setup agent` 调整设置。
:::

良好的默认选项：

| 提供商 | 是什么 | 如何设置 |
|----------|-----------|---------------|
| **Nous Portal** | 基于订阅，零配置 | 通过 `hermes model` OAuth 登录 |
| **OpenAI Codex** | ChatGPT OAuth，使用 Codex 模型 | 通过 `hermes model` 进行设备代码认证 |
| **Anthropic** | 直接使用 Claude 模型——Max 计划加额外使用额度（OAuth），或按 token 付费的 API 密钥 | `hermes model` → OAuth 登录（需要 Max 和额外额度），或 Anthropic API 密钥 |
| **OpenRouter** | 跨众多模型的多提供商路由 | 输入 API 密钥 |
| **Fireworks AI** | 直接的 OpenAI 兼容模型 API | 设置 `FIREWORKS_API_KEY` |
| **Z.AI** | GLM / Zhipu 托管模型 | 设置 `GLM_API_KEY` / `ZAI_API_KEY`（也接受 `Z_AI_API_KEY`） |
| **Kimi / Moonshot** | Moonshot 托管的编码和聊天模型 | 设置 `KIMI_API_KEY`（或 Kimi-Coding 专用的 `KIMI_CODING_API_KEY`） |
| **Kimi / Moonshot China** | 中国区 Moonshot 端点 | 设置 `KIMI_CN_API_KEY` |
| **Arcee AI** | Trinity 模型 | 设置 `ARCEEAI_API_KEY` |
| **GMI Cloud** | 多模型直接 API | 设置 `GMI_API_KEY` |
| **MiniMax (OAuth)** | 通过浏览器 OAuth 使用 MiniMax 前沿模型——无需 API 密钥（`hermes_cli/models.py` 中的模型名称可能随版本改变） | `hermes model` → MiniMax (OAuth) |
| **MiniMax** | 国际 MiniMax 端点 | 设置 `MINIMAX_API_KEY` |
| **MiniMax China** | 中国区 MiniMax 端点 | 设置 `MINIMAX_CN_API_KEY` |
| **Alibaba Cloud** | 通过 DashScope 使用 Qwen 模型 | 设置 `DASHSCOPE_API_KEY`（Qwen Coding Plan 也接受 `ALIBABA_CODING_PLAN_API_KEY`） |
| **Hugging Face** | 通过统一路由器使用 20 多个开放模型（Qwen、DeepSeek、Kimi 等） | 设置 `HF_TOKEN` |
| **AWS Bedrock** | 通过原生 Converse API 使用 Claude、Nova、Llama、DeepSeek | IAM 角色或 `aws configure`（[指南](../guides/aws-bedrock.md)） |
| **Azure Foundry** | Azure AI Foundry 托管模型 | 设置 `AZURE_FOUNDRY_API_KEY` + `AZURE_FOUNDRY_BASE_URL` |
| **Google AI Studio** | 通过直接 API 使用 Gemini 模型 | 设置 `GOOGLE_API_KEY` / `GEMINI_API_KEY` |
| **xAI** | 通过直接 API 使用 Grok 模型 | 设置 `XAI_API_KEY` |
| **xAI Grok OAuth** | SuperGrok / Premium+ 订阅，无需 API 密钥 | `hermes model` → xAI Grok OAuth |
| **NovitaAI** | 多模型 API 网关 | 设置 `NOVITA_API_KEY` |
| **StepFun** | Step Plan 模型 | 设置 `STEPFUN_API_KEY` |
| **Xiaomi MiMo** | 小米托管模型 | 设置 `XIAOMI_API_KEY` |
| **Tencent TokenHub** | 腾讯托管模型 | 设置 `TOKENHUB_API_KEY` |
| **Ollama Cloud** | 托管的 Ollama 模型 | 设置 `OLLAMA_API_KEY` |
| **LM Studio** | 提供 OpenAI 兼容 API 的本地桌面应用 | 设置 `LM_API_KEY`（非默认值时还需 `LM_BASE_URL`） |
| **Qwen OAuth** | Qwen Portal 浏览器 OAuth——无需 API 密钥 | `hermes model` → Qwen OAuth |
| **Kilo Code** | KiloCode 托管模型 | 设置 `KILOCODE_API_KEY` |
| **OpenCode Zen** | 按使用量付费地访问精选模型 | 设置 `OPENCODE_ZEN_API_KEY` |
| **OpenCode Go** | 每月 10 美元的开放模型订阅 | 设置 `OPENCODE_GO_API_KEY` |
| **DeepSeek** | 直接访问 DeepSeek API | 设置 `DEEPSEEK_API_KEY` |
| **NVIDIA NIM** | 通过 build.nvidia.com 或本地 NIM 使用 Nemotron 模型 | 设置 `NVIDIA_API_KEY`（可选：`NVIDIA_BASE_URL`） |
| **GitHub Copilot** | GitHub Copilot 订阅（GPT-5.x、Claude、Gemini 等） | 通过 `hermes model` 进行 OAuth，或使用 `COPILOT_GITHUB_TOKEN` / `GH_TOKEN` |
| **GitHub Copilot ACP** | Copilot ACP agent 后端（启动本地 `copilot` CLI） | `hermes model`（需要 `copilot` CLI + `copilot login`） |
| **Vercel AI Gateway** | Vercel AI Gateway 路由 | 设置 `AI_GATEWAY_API_KEY` |
| **Custom Endpoint** | VLLM、SGLang、Ollama，或任何 OpenAI 兼容 API | 设置基础 URL + API 密钥 |

对大多数初次用户：选择一个提供商，接受默认值，除非你知道为何要修改。完整的提供商目录、环境变量和设置步骤位于 [Providers](../integrations/providers.md) 页面。

:::caution 最小上下文：64K tokens
Hermes Agent 需要至少 **64,000 tokens** 上下文的模型。窗口较小的模型无法为多步骤工具调用工作流维持足够工作内存，启动时将被拒绝。大多数托管模型（Claude、GPT、Gemini、Qwen、DeepSeek）都轻松满足这一要求。若运行本地模型，将其上下文大小设为至少 64K（例如 llama.cpp 使用 `--ctx-size 65536`，Ollama 使用 `-c 65536`）。
:::

:::tip
你可以随时用 `hermes model` 切换提供商——没有锁定。全部受支持提供商及设置详情请见 [AI Providers](../integrations/providers.md)。
:::

### 设置如何存储

Hermes 将密钥与普通配置分开：

- **密钥和令牌** → `~/.hermes/.env`
- **非敏感设置** → `~/.hermes/config.yaml`

通过 CLI 正确设置值最简单：

```bash
hermes config set model anthropic/claude-opus-4.6
hermes config set terminal.backend docker
hermes config set OPENROUTER_API_KEY sk-or-...
```

正确的值会自动进入正确的文件。

## 3. 运行第一次聊天

```bash
hermes            # 经典 CLI
hermes --tui      # 现代 TUI（推荐）
```

你会看到欢迎横幅，其中显示模型、可用工具和 skills。使用一个具体且易于验证的提示：

:::tip 选择你的界面
Hermes 提供两个终端界面：经典的 `prompt_toolkit` CLI 和较新的 [TUI](../user-guide/tui.md)，后者带有模态覆盖层、鼠标选择和非阻塞输入。二者共享会话、斜杠命令和配置——分别以 `hermes` 与 `hermes --tui` 试用。
:::

```
总结此仓库，列出 5 个要点，并告诉我主入口点是什么。
```

```
检查我的当前目录，告诉我哪个看起来是主要项目文件。
```

```
帮助我为此代码库设置一个干净的 GitHub PR 工作流。
```

**成功的表现：**

- 横幅显示你选择的模型/提供商
- Hermes 回复时没有错误
- 它可以在需要时使用工具（终端、文件读取、网页搜索）
- 对话可正常持续超过一轮

如果这些都能做到，你已经越过最困难的部分。

## 4. 验证会话可用

继续之前，确保恢复功能可用：

```bash
hermes --continue    # 恢复最近的会话
hermes -c            # 简写形式
```

它应将你带回刚才的会话。若没有，请检查你是否处于同一 profile，以及会话是否确实保存。这在你同时处理多个设置或机器时很重要。

## 5. 试用关键功能

### 使用终端

```
❯ 我的磁盘用量是多少？显示最大的 5 个目录。
```

agent 会代表你运行终端命令并显示结果。

### 斜杠命令

输入 `/` 可看到所有命令的自动补全下拉菜单：

| 命令 | 功能 |
|---------|-------------|
| `/help` | 显示所有可用命令 |
| `/tools` | 列出可用工具 |
| `/model` | 以交互方式切换模型 |
| `/personality pirate` | 尝试有趣的人格 |
| `/save` | 保存对话 |

### 多行输入

按 `Alt+Enter`、`Ctrl+J` 或 `Shift+Enter` 添加新行。`Shift+Enter` 需要终端把它作为独特序列发送（Kitty / foot / WezTerm / Ghostty 默认支持；启用 Kitty 键盘协议后 iTerm2 / Alacritty / VS Code 终端支持）。`Alt+Enter` 和 `Ctrl+J` 在每种终端中都可用。

### 中断 agent

如果 agent 耗时过长，输入新消息并按 Enter——这会中断当前任务并切换到新指令。`Ctrl+C` 也可用。

## 6. 添加下一层

仅在基础聊天可用后再做。选择所需内容：

### 机器人或共享助手

```bash
hermes gateway setup    # 交互式平台配置
```

连接 [Telegram](/user-guide/messaging/telegram)、[Discord](/user-guide/messaging/discord)、[Slack](/user-guide/messaging/slack)、[WhatsApp](/user-guide/messaging/whatsapp)、[Signal](/user-guide/messaging/signal)、[Email](/user-guide/messaging/email)、[Home Assistant](/user-guide/messaging/homeassistant) 或 [Microsoft Teams](/user-guide/messaging/teams)。

### 自动化和工具

- `hermes tools` — 调整各平台的工具访问
- `hermes skills` — 浏览和安装可复用工作流
- Cron — 只在机器人或 CLI 设置稳定后使用

### 沙箱终端

为了安全，在 Docker 容器或远程服务器上运行 agent：

```bash
hermes config set terminal.backend docker    # Docker 隔离
hermes config set terminal.backend ssh       # 远程服务器
```

对于 Docker 沙箱，还可以开启**出口凭据注入代理**，使沙箱永远看不到真实 API 密钥——只能看到仅能从本地 TLS 拦截守护程序后使用的不透明代理令牌。请参阅 [Egress proxy](../user-guide/egress/iron-proxy.md)。设置方式是 `hermes egress setup && hermes egress start`；`hermes setup terminal` 也会向 Docker 用户指出它。Modal、SSH、Daytona 和 Singularity 尚未接入。

### 语音模式

```bash
# 在 Hermes 安装目录中运行（curl 安装器在 Linux/macOS 上将其放在
# ~/.hermes/hermes-agent，Windows 上放在 %LOCALAPPDATA%\hermes\hermes-agent）：
cd ~/.hermes/hermes-agent
uv pip install --python ./venv/bin/python -e ".[voice]"
# 包括用于免费本地语音转文字的 faster-whisper
```

然后在 CLI 中运行：`/voice on`。按 `Ctrl+B` 录音。请见[语音模式](../user-guide/features/voice-mode.md)。

### Skills

Skills 是按需提供的指令文档，教 Hermes 完成特定任务——部署到 Kubernetes、创建 GitHub PR、微调模型、搜索 GIF。每个 skill 都是一个 `SKILL.md` 文件，包含名称、描述和逐步流程。agent 可免费读取简短描述，只在任务确实需要时加载 skill 完整内容，所以添加 skills 不会使每个请求膨胀。

Hermes 随附的 skills 目录中已有安装在 `~/.hermes/skills/` 的 bundled skills。你可从 Skills Hub 添加更多，或编写自己的 skill。

**从 hub 浏览和安装：**

```bash
hermes skills browse                      # 列出所有可用项目
hermes skills search kubernetes           # 按关键字查找 skills
hermes skills install openai/skills/k8s   # 安装一个（先运行安全扫描）
```

安装参数是 hub 中的 `source/path` slug——`openai/skills/k8s` 指 OpenAI 目录中的 `k8s` skill。`hermes skills browse` 会显示要使用的确切 slug。

**使用 skill**——每个已安装 skill 都会自动成为斜杠命令：

```bash
/k8s deploy the staging manifest          # 用请求运行 skill
/k8s                                       # 加载它，让 Hermes 询问你的需要
```

这在 CLI 和任何已连接消息平台中都可用。无需预先安装所有内容——在普通对话中当任务匹配时，agent 会自行选择合适的 bundled skill。

请参阅 [Skills System](../user-guide/features/skills.md)，了解如何编写自己的 skill、外部 skill 目录和完整 hub 源列表。

### MCP 服务器

```yaml
# 添加到 ~/.hermes/config.yaml
mcp_servers:
  github:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxx"
```

### 编辑器集成（ACP）

ACP 支持随标准 `[all]` extras 提供，所以 curl 安装器已经包含它。只需运行：

```bash
hermes acp
```

（如果安装时不含 `[all]`，请先运行 `cd ~/.hermes/hermes-agent && uv pip install -e ".[acp]"`。）

请参阅 [ACP Editor Integration](../user-guide/features/acp.md)。

---

## 常见失败模式

以下问题最浪费时间：

| 症状 | 可能原因 | 修复方法 |
|---|---|---|
| Hermes 打开但给出空或损坏的回复 | 提供商认证或模型选择错误 | 再次运行 `hermes model`，确认提供商、模型和认证 |
| 自定义端点“可用”但返回垃圾内容 | 基础 URL、模型名称错误，或并非真正 OpenAI 兼容 | 先在独立客户端中验证端点 |
| Gateway 启动但没人能向它发消息 | 机器人令牌、允许列表或平台设置不完整 | 重新运行 `hermes gateway setup`，并检查 `hermes gateway status` |
| `hermes --continue` 找不到旧会话 | 切换了 profile 或会话从未保存 | 检查 `hermes sessions list`，并确认处于正确 profile |
| 模型不可用或发生异常回退 | 提供商路由或回退设置过于激进 | 在基础提供商稳定前保持路由关闭 |
| `hermes doctor` 标示配置问题 | 配置值缺失或过时 | 修复配置；添加功能前重新测试普通聊天 |

## 恢复工具包

当感觉有问题时，按此顺序：

1. `hermes doctor`
2. `hermes model`
3. `hermes setup`
4. `hermes sessions list`
5. `hermes --continue`
6. `hermes gateway status`

这一顺序可快速让你从“感觉不对劲”回到已知状态。

---

## 快速参考

| 命令 | 描述 |
|---------|-------------|
| `hermes` | 开始聊天 |
| `hermes model` | 选择 LLM 提供商和模型 |
| `hermes tools` | 配置每个平启用哪些工具 |
| `hermes setup` | 完整设置向导（一次配置所有内容） |
| `hermes doctor` | 诊断问题 |
| `hermes update` | 更新到最新版本 |
| `hermes gateway` | 启动消息 gateway |
| `hermes --continue` | 恢复上次会话 |

## 后续步骤

- **[CLI Guide](../user-guide/cli.md)** — 掌握终端界面
- **[Configuration](../user-guide/configuration.md)** — 自定义设置
- **[Messaging Gateway](../user-guide/messaging/index.md)** — 连接 Telegram、Discord、Slack、WhatsApp、Signal、Email、Home Assistant、Teams 等
- **[Tools & Toolsets](../user-guide/features/tools.md)** — 探索可用能力
- **[AI Providers](../integrations/providers.md)** — 完整提供商列表和设置详情
- **[Skills System](../user-guide/features/skills.md)** — 可复用的工作流和知识
- **[Tips & Best Practices](../guides/tips.md)** — 高级用户技巧
