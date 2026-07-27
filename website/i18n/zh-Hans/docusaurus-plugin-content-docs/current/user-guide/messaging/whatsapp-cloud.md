---
sidebar_position: 6
title: "WhatsApp Business (Cloud API)"
description: "通过 Meta 官方 Business Cloud API 将 Hermes Agent 设置为 WhatsApp 机器人"
---

# WhatsApp Business Cloud API 设置

Hermes 可以通过 Meta 的**官方** WhatsApp Business Cloud API 连接到 WhatsApp。这是生产级方案：无需 Node.js 桥接子进程，无需二维码，不存在封号风险。

代价如下：

- 你需要一个 **Meta Business 账号**（而非个人 WhatsApp）。
- 机器人在一个专用的商务电话号码上运行，而非你的个人号码。
- Hermes 网关需要一个**公网 HTTPS URL**，以便 Meta 通过 Webhook 投递入站消息。
- 在用户最后一条消息超过 24 小时后发出的回复，需要预先审批通过的**模板**（这是 Meta 的"客服窗口"规则，而非 Hermes 的限制）。

如果这些约束不适合你的场景，[Baileys 桥接集成](./whatsapp.md) 是另一种选择——使用个人账号，无需公网 URL，但非官方且有封号风险。

:::tip 我应该用哪一个？
- **Cloud API（本指南）**——运行真实的业务机器人，追求稳定性，能接受 Meta 验证和模板审批流程
- **[Baileys 桥接](./whatsapp.md)**——个人项目、快速演示、单人使用场景，愿意承担机器人号码被封的风险
:::

---

## 快速开始

```bash
hermes whatsapp-cloud
```

向导会引导你完成每一个凭证的配置，在你粘贴时逐一验证（能抓住 #1 设置陷阱——把电话号码贴到 Phone Number ID 字段里），并打印需要在向导之外进行的步骤（启动 cloudflared、配置 Meta 的 Webhook 面板）的精确后续指引。

本页的其余部分为手动参考。

---

## 前置条件

1. **一个 Meta Business 账号**。前往 [business.facebook.com](https://business.facebook.com/) 创建。
2. **一个开启了 WhatsApp 功能的 Meta 应用**。详见下方"创建 Meta 应用"。
3. **一种将本地端口以 HTTPS 暴露到公网的方式**。推荐 Cloudflare Tunnel（`cloudflared`）——免费，无需端口转发，无需域名。ngrok、自有域名配合反向代理和 TLS、或者将网关直接绑定到公网 IP 的 VPS 也同样可行。
4. **可选但推荐**：在 `PATH` 中安装 ffmpeg，这样外向语音消息会以原生的 WhatsApp 语音笔记气泡（绿色波形）发送而非 MP3 音频附件。未安装时 Hermes 会自动降级。

---

## 创建 Meta 应用

1. 前往 [developers.facebook.com/apps](https://developers.facebook.com/apps) → **Create App**。
2. 选择使用场景：**"Connect with customers through WhatsApp"** → **Next**。
3. 选择或创建一个 Business Portfolio。查看发布要求。确认 → **Create app**。
4. 创建完成后你会进入 **Customize use case → Connect on WhatsApp → Quickstart**。点击 **Start using the API** → 现在你已进入 **API Setup** 页面。
5. 确保已关联一个 WhatsApp Business Account（WABA）。如果第 3 步创建了新 Portfolio，系统会自动创建一个。在 API Setup 页面确认。

你需要从面板获取以下值——向导按此顺序依次提示输入：

| 值 | 面板位置 | 字段格式 | 备注 |
|---|---|---|---|
| **Phone Number ID** | App Dashboard → WhatsApp → API Setup → "From" 下拉框下方 | 数字，15-17 位 | **不是**电话号码本身。#1 设置错误就是把真正的电话号码贴到这里。 |
| **Access Token** | App Dashboard → WhatsApp → API Setup → "Generate access token" | 以 `EAA` 开头，100+ 字符 | 临时令牌有效期 24 小时——生产环境参见下方"永久令牌"。 |
| **App Secret** | App Dashboard → Settings → Basic → 点击 App secret 旁的"Show" | 32 位小写十六进制 | 用于验证传入 Webhook 的签名。缺少此项时，入站消息将被拒绝（503）。 |
| **App ID**（可选） | App Dashboard → Settings → Basic | 数字，15-16 位 | 消息收发不需要，分析时有用。 |
| **WABA ID**（可选） | App Dashboard → WhatsApp → API Setup → 靠近顶部 | 数字，15+ 位 | 消息收发不需要，分析时有用。 |

---

## 永久令牌（生产环境）

临时访问令牌 **24 小时后**过期，这意味着今天生成的令牌明天就会失效。生产环境部署请使用**系统用户永久令牌**：

1. 前往 [business.facebook.com/latest/settings](https://business.facebook.com/latest/settings) → **System users**（左侧边栏）。
2. **Add** → 名称（如 `hermes-bot`）→ 角色：**Admin**。
3. 选择新用户 → **Assign Assets**：
   - 选择你的应用 → 在 Full control 下勾选 **Manage app**。
   - 选择你的 WhatsApp 账号 → 在 Full control 下勾选 **Manage WhatsApp Business Accounts**。
   - 点击 **Assign assets**。
4. **Generate token**，勾选以下权限：
   - `business_management`
   - `whatsapp_business_messaging`
   - `whatsapp_business_management`
5. 将**令牌过期时间设为：Never**。
6. 复制令牌 → 更新 `~/.hermes/.env` 中的 `WHATSAPP_CLOUD_ACCESS_TOKEN` → 重启网关。

系统用户令牌不会过期，除非你明确撤销。

---

## 将 Hermes 暴露到公网

Cloud API 通过 HTTPS POST 将入站消息发送到你的 Webhook URL——这意味着 Hermes 网关必须能被 Meta 的服务器访问到。三种常见方式：

### Cloudflare Tunnel（推荐）

免费，无需端口转发，支持 Windows / macOS / Linux。与网关并行运行。

**安装：**

```bash
# Windows
winget install Cloudflare.cloudflared

# macOS
brew install cloudflared

# Linux
# 从 https://github.com/cloudflare/cloudflared/releases 下载二进制文件
```

**运行快速隧道**（无需 Cloudflare 账号——会给你一个 `https://<随机>.trycloudflare.com` URL）：

```bash
cloudflared tunnel --url http://localhost:8090
```

记下打印的 URL——这就是你要提供给 Meta 的地址。

:::warning 快速隧道会轮换
免费的快速隧道 URL 每次重启 `cloudflared` 都会变化。如需固定 URL，请使用 `cloudflared tunnel login` 登录并创建命名隧道。免费 Cloudflare 账号拥有无限命名隧道——参见 [Cloudflare 文档](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) 了解命名隧道的工作流程。
:::

### ngrok

```bash
ngrok http 8090
```

免费版每次重启会显示不同的 URL。付费版可提供固定子域名。

### 自有域名 + 反向代理

如果你已有带 TLS 证书的服务器（Caddy、nginx 等），将某个路由指向 `localhost:8090` 即可。这是生产环境最稳定的方案，但需要已有基础设施。

---

## 在 Meta 侧配置 Webhook

隧道运行后：

1. 记下隧道打印的公网 URL——例如 `https://abc123.trycloudflare.com`。
2. 生成一个 **Verify Token**——向导会自动用 `secrets.token_urlsafe(32)` 生成；如果手动配置，运行：
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
   将其保存到 `~/.hermes/.env` 的 `WHATSAPP_CLOUD_VERIFY_TOKEN` 中。
3. 启动 Hermes 网关：`hermes gateway`。
4. 在 Meta App Dashboard → **WhatsApp → Configuration**（或 **Use cases → Customize → Configuration**，取决于 UI 版本）→ 点击 Webhook 部分的 **Edit**。
5. 填写：
   - **Callback URL**：`https://abc123.trycloudflare.com/whatsapp/webhook`
   - **Verify Token**：第 2 步的字符串（必须完全匹配）
6. 点击 **Verify and save**。Meta 会向你的 URL 发送 GET 请求，网关返回 Challenge，Meta 将 Webhook 标记为已验证。
7. 在 **Webhook fields** 下，点击 **Manage** → 订阅 **messages** 字段。这告诉 Meta 将入站消息实际投递到你的 Webhook。

**手动验证回路**（从第三方终端）：

```bash
TUNNEL="https://abc123.trycloudflare.com"
VERIFY="<你的 verify token>"

# 应返回 HTTP 200，正文为 "hello"
curl -i "$TUNNEL/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=$VERIFY&hub.challenge=hello"

# 健康检查端点——应显示 verify_token_configured: true 和 app_secret_configured: true
curl "$TUNNEL/health"
```

---

## 接收方白名单（Meta 侧）

在开发模式（应用通过 App Review 审核前）下，Meta 限制你的机器人可以给哪些号码发消息：

1. App Dashboard → WhatsApp → API Setup → **To** 下拉框。
2. 点击 **Manage phone number list**。
3. 添加你想要发消息的电话号码（你自己的、你团队的、友好测试者的）。Meta 会通过短信或 WhatsApp 向每个号码发送 6 位验证码。

开发模式下最多 5 个号码。经过 App Review 后此限制解除。

---

## 允许列表（Hermes 侧）

除了 Meta 的接收方白名单外，Hermes 还有自己的按平台允许列表，控制**哪些入站消息会被代理处理**。添加到 `~/.hermes/.env`：

```bash
# 逗号分隔的电话号码，包含国家代码，不要 '+' / 空格 / 短横线
WHATSAPP_CLOUD_ALLOWED_USERS=15551234567,15557654321

# 或允许所有人（仅在与 Meta 的接收方白名单配合时安全）
# WHATSAPP_CLOUD_ALLOW_ALL_USERS=true
```

向导在第 6 步设置此项。没有允许列表时，**所有入站消息都会被拒绝**——这是有意设计的，以防止接收方白名单被放宽后，随机号码也能调用机器人。

---

## 优化机器人的 WhatsApp 个人资料

WhatsApp 会在聊天标题和联系人列表中显示机器人的**名称和头像**。这些无法通过 Cloud API 设置——它们位于 Meta 的 Business Manager 中。

机器人正常运行后，前往 **[business.facebook.com/wa/manage/phone-numbers](https://business.facebook.com/wa/manage/phone-numbers/)**，点击你的电话号码，你会看到：

| 项目 | 位置 | 备注 |
|---|---|---|
| **显示名称** | 电话号页面顶部 | 更改需通过 Meta 的名称审核流程（约 24-48 小时）。 |
| **头像** | 电话号页面顶部 | 正方形图片，推荐 ≥640×640px。立即生效。 |
| **关于 / 描述 / 网站 / 邮箱 / 营业时间 / 分类** | "Edit profile" 按钮 | 用户点击机器人名称后在信息面板中显示。纯外观装饰。 |
| **认证徽章**（绿色对勾） | Business Manager → Security Center → Start Verification | 需要 Meta 单独的企业验证流程。 |

`hermes whatsapp-cloud` 向导会在设置结束时打印这些链接。机器人无需任何设置即可正常工作——以上只是优化机器人对用户展示效果的纯装饰项。

---

## 配置参考

所有设置位于 `~/.hermes/.env`。**必填**值以粗体标出。

| 变量 | 默认值 | 描述 |
|---|---|---|
| **`WHATSAPP_CLOUD_PHONE_NUMBER_ID`** | — | API Setup 中的 15-17 位 ID。**不是**电话号码。 |
| **`WHATSAPP_CLOUD_ACCESS_TOKEN`** | — | Meta 访问令牌（以 `EAA` 开头）。临时 24h 或系统用户永久令牌。 |
| **`WHATSAPP_CLOUD_APP_SECRET`** | — | Settings → Basic 中的 32 位十六进制字符串。缺少时入站消息被拒绝（503）。 |
| **`WHATSAPP_CLOUD_VERIFY_TOKEN`** | — | GET 握手用的共享密钥。向导自动生成。 |
| **`WHATSAPP_CLOUD_ALLOWED_USERS`** | — | 允许与机器人通信的 wa_id，逗号分隔。 |
| `WHATSAPP_CLOUD_ALLOW_ALL_USERS` | `false` | 设为 `true` 以绕过允许列表。 |
| `WHATSAPP_CLOUD_APP_ID` | — | 可选，用于未来分析集成。 |
| `WHATSAPP_CLOUD_WABA_ID` | — | 可选，用于未来分析集成。 |
| `WHATSAPP_CLOUD_WEBHOOK_HOST` | `0.0.0.0` | Webhook 服务器绑定的接口。 |
| `WHATSAPP_CLOUD_WEBHOOK_PORT` | `8090` | Webhook 服务器绑定的端口。必须与隧道转发的端口一致。 |
| `WHATSAPP_CLOUD_WEBHOOK_PATH` | `/whatsapp/webhook` | Meta 发 POST 的 URL 路径。 |
| `WHATSAPP_CLOUD_API_VERSION` | `v20.0` | Meta Graph API 版本。仅当 Meta 文档推荐更新版本时才需覆盖。 |
| `WHATSAPP_CLOUD_HOME_CHANNEL` | — | 用作机器人 Home Channel 的 wa_id（用于 cron 任务等）。 |

你可以同时启用 Baileys（`whatsapp`）和 Cloud（`whatsapp_cloud`）适配器，分别服务不同的电话号码。

---

## 功能

### 入站

- **文本消息**——直接传给代理。
- **图片**——自动下载并附加到代理的输入中。支持原生视觉能力的模型（Claude、GPT-4o、Gemini 等）直接读取图片；非视觉模型会收到自动生成的文字描述。
- **语音消息**——自动下载为 `.ogg`，通过你配置的 STT 提供商（本地 faster-whisper、OpenAI/Nous、Groq 等）转录，然后以文本形式交给代理。
- **文档**——自动下载。100KB 以内的纯文本文件（`.txt`、`.md`、`.json`、`.py`、`.csv` 等）会直接内联到代理的输入中，使其无需工具调用即可读取。较大的文件会缓存在本地，供代理的其他工具访问。
- **按钮点击**——当用户点击机器人之前发送的按钮时（澄清选择、指令审批、斜杠命令确认），点击事件会直接路由到对应的处理器。过期按钮点击会降级为普通文本输入处理。
- **回复上下文**——当用户回复机器人之前的一条消息时，代理能看到原始消息作为上下文。

### 出站

- **文本**——Markdown 会自动转换为 WhatsApp 的样式语法（`**bold**` → `*bold*`、`~~strike~~` → `~strike~`、标题 → 加粗、`[link](url)` → `link (url)`）。长消息按每段 4096 字符拆分。
- **图片**——代理生成的图片和本地图片文件均支持，以原生照片附件形式投递。
- **语音消息**——文字转语音输出通过 ffmpeg 转换为原生 WhatsApp 语音笔记气泡（绿色波形）。未安装 ffmpeg 时，降级为 MP3 音频附件。参见下方"语音消息"。
- **视频 / 文档**——均支持，以原生附件形式发送。

### 交互式 UX

当代理调用以下流程时，Hermes 使用 WhatsApp 的原生交互式消息——可点击的按钮，而非"回复数字"的文本提示：

- **`clarify` 工具**——多选问题渲染为快速回复按钮（1-3 个选项）或可点击展开的列表（4 个及以上选项）。选择"✏️ 其他"可让用户输入自由文本，代理将其作为决议结果接收。
- **危险命令审批**——当代理的终端/代码执行触发到受限命令时，用户会看到 `✅ 批准` / `❌ 拒绝` 按钮，无需输入 `/approve` 或 `/deny`。
- **斜杠命令确认**——`/reload-mcp` 等特权命令会显示 `✅ 允许一次` / `🔒 始终允许` / `❌ 取消` 按钮。

如果按钮渲染失败（例如在旧版 WhatsApp 客户端上），所有交互提示都会优雅降级为纯文本。

### 已读回执和打字指示

Hermes 会立即确认入站消息：

- 网关收到你的消息后，消息会显示**蓝色双勾**。
- 代理准备回复时，WhatsApp 聊天中机器人的名称会显示**"输入中……"**。
- 当机器人的首条回复消息到达时，打字指示会自动消失。

这使得用户能清楚区分机器人已看到消息与仍在处理回复两种状态。

### 语音消息

WhatsApp 区分"语音笔记"（绿色波形气泡）和通用音频文件附件。区别仅在编码：语音笔记需要是 `audio/ogg` 格式、`opus` 编码。

Hermes TTS 输出 MP3。有两种路径：

- **在 PATH 中有 ffmpeg**（推荐）——出站 TTS 会转换后作为真正的语音笔记到达。安装：
  - Windows：`winget install Gyan.FFmpeg`
  - macOS：`brew install ffmpeg`
  - Linux：包管理器
- **没有 ffmpeg**——出站 TTS 会作为 MP3 音频附件到达。可以播放，只是不会显示为语音笔记。网关日志会打印一次性警告通知。

你可以通过健康端点检查网关是否找到了 ffmpeg：

```bash
curl http://localhost:8090/health
# 查找 "ffmpeg_present": true
```

---

## 已知限制

### 24 小时对话窗口

Meta 只允许在用户最后一条入站消息后 **24 小时内**发送**自由格式消息**。在此窗口之外，Meta API 只接受预先审批通过的**消息模板**。

**实际影响：**

- 被动聊天（用户私信 → 机器人在 24 小时内回复 → 用户回复 → ……）可以无限持续。这覆盖了 >95% 的正常机器人使用场景。
- **向 WhatsApp 投递的 cron 任务**，如果间隔超过 24 小时，会遇到 Graph 错误代码 `131047`（"重新接触消息"）。
- **耗时超过 24 小时的 `delegate_task` 异步结果**同样会失败。
- **将外部事件路由到 WhatsApp 的 Webhook 订阅者**，在用户近期未私信机器人时也会失败。

Hermes 会在系统提示中告知代理此窗口限制，因此模型在安排延迟消息时会注意这一点。

消息模板支持（窗口外发送的变通方案）尚未在 Hermes 中实现。如有需要，请[提交 Issue](https://github.com/NousResearch/hermes-agent/issues)——已列入计划，但需等待明确的需求信号。

### 群聊

Cloud API 的群组支持有限（由 Meta 限制的能力层级）。Hermes 的 `whatsapp_cloud` 适配器在 v1 中**仅处理私聊**。如需群聊，请使用 Baileys 桥接。

### 出站速率限制

Meta 的默认吞吐量为**每个商务电话号码每秒 80 条消息**，可升级。Hermes 当前未在客户端侧强制执行此限制——极高吞吐量的发送可能会触及 Meta 限制。

---

## 故障排查

### Meta 面板中的设置验证失败（"URL couldn't be validated"）

几乎总是以下原因之一：

- **隧道 URL 错误或过期**——cloudflared 快速隧道会轮换。获取新 URL 并同时更新 `.env` 和 Meta 面板。
- **Verify Token 不匹配**——`~/.hermes/.env` 中 `WHATSAPP_CLOUD_VERIFY_TOKEN` 的值必须与你输入 Meta 面板的完全一致。先运行上面的 curl 探测，确认网关的 Verify 握手在本地工作正常。
- **网关未运行**——检查 `hermes gateway` 是否已启动。
- **未设置 App Secret**——缺少时 Hermes 会以 503 拒绝入站 POST。Meta 将其解读为"无法验证"。

### `graph error 100`：没有该 ID 的对象

你在 `WHATSAPP_CLOUD_PHONE_NUMBER_ID` 中粘贴了你的电话号码（10-11 位），而非 Phone Number ID（Meta 的 15-17 位内部 ID）。重新查看 API Setup 页面——Phone Number ID 显示在"From"下拉框的**下方**。

向导对此有校验器，但手动配置时值得注意。

### `graph error 190`：认证错误

你的访问令牌无效。子错误码：

- `subcode 463`——令牌过期。临时令牌有效期为 24 小时。重新生成，或改用系统用户永久令牌（见上文）。
- `subcode 467`——令牌已失效（被撤销或密码已更改）。
- 其他 190——生成令牌时未选择所需权限。确保三个权限（`business_management`、`whatsapp_business_messaging`、`whatsapp_business_management`）都已勾选。

### `graph error 131047`：重新接触消息

24 小时对话窗口已过期（参见"已知限制"）。解决方式：

- 让用户先给机器人发私信以重新打开窗口。
- 等待 Hermes 实现模板支持。

### 入站消息报错：`media metadata fetch failed (status=401)`

与出站报错（`graph error 190`）的 401 根因相同——访问令牌无效或已过期。修复令牌即可。

### 机器人回复显示为原始 JSON / 工具调用泄漏

常见原因：`whatsapp_cloud` 配置的 Toolset 缺少代理想要调用的工具。运行 `hermes tools list` 确认平台正在使用 `hermes-whatsapp`（即 Cloud 适配器的默认 Toolset，与 Baileys 相同）。

如果模型输出了形似工具调用的文本而非结构化调用，通常意味着 Toolset 实际上为空。参见 `hermes_cli/platforms.py` 了解平台到默认 Toolset 的映射。

### STT（语音笔记转录）返回空结果或"could not transcribe"

默认 `stt.provider: local` 需要安装 `pip install faster-whisper`。如果你是 Nous 订阅用户，可以将 STT 路由到 Meta 管理的音频网关：

```bash
hermes config set stt.provider openai
hermes config set stt.use_gateway true
hermes gateway restart
```

这会使用你的 Nous Portal 访问令牌，无需单独的 OpenAI 密钥。

---

## 安全说明

- **将 App Secret 视为密码**——任何人只要拥有它，就能伪造出 Hermes 作为真实消息接受的 Webhook 载荷。
- **Verify Token 是一个共享密钥**——泄露的风险较低（最坏情况是有人将 Meta 的 Webhook 重新订阅到他们的另一个 URL），但仍应避免提交到代码仓库。
- **Access Token 代表你的机器人的身份**——系统用户令牌等同于长期有效的 API 密钥。一旦部署环境被侵入，应立即轮换。
- **设置了 `WHATSAPP_CLOUD_APP_SECRET` 时，Webhook 端点只接受带签名的请求**——即使在开发环境也请保持设置。缺少时，网关会以 HTTP 503 拒绝入站投递。
- **`/health` 端点无需认证**——可以安全暴露，因为它只报告配置存在性布尔值，而非值本身。但如果你不想暴露它，可以在反向代理/隧道层限制访问。

---

## 与 Baileys 桥接的对比

| | Baileys（`hermes whatsapp`） | Cloud API（`hermes whatsapp-cloud`） |
|---|---|---|
| 账号类型 | 个人 | 企业 |
| 设置方式 | 扫描二维码 | Meta 应用 + WABA + 令牌 |
| 依赖 | Node.js + npm | 纯 Python（httpx + aiohttp） |
| 进程 | 托管 Node 子进程 | aiohttp Webhook 服务器 |
| 需要公网 URL？ | 否 | 是 |
| 封号风险 | 有（非官方 API） | 无（官方支持） |
| 入站方式 | 轮询 Node 桥接 | Meta 推送 Webhook POST |
| 出站方式 | 本地桥接 → Baileys | HTTPS 到 graph.facebook.com |
| 群组 | 完整支持 | 仅私聊（v1） |
| 24 小时窗口 | 无限制 | 严格规则——窗口外需模板 |
| 语音笔记（出站） | 原生 | 有 ffmpeg 时原生，否则降级为 MP3 |
| 已读回执 | 否 | 有（蓝色双勾） |
| 打字指示 | 否 | 有（回复时自动消失） |
| 交互式按钮 | 仅文本降级 | 原生（澄清、审批、斜杠确认） |
| 生产使用 | 有风险（Meta 可能封禁） | 专为生产设计 |

大多数为个人项目运行 Hermes 的用户更喜欢 Baileys。大多数运行面向客户的机器人的用户更喜欢 Cloud API。

---

## 参见

- [Meta 官方 WhatsApp Business Cloud API 文档](https://developers.facebook.com/documentation/business-messaging/whatsapp/)——底层平台、定价、App Review 和 Meta 侧速率限制的权威参考。
- [WhatsApp（Baileys 桥接）设置](whatsapp.md)——面向个人项目的另一种集成方案。
- [消息平台概览](index.md)——所有消息集成的速览。
