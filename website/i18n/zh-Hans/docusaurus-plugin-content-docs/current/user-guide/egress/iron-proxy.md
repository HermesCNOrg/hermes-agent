# 出站凭证注入代理（iron-proxy）

当 Hermes 在 Docker 终端沙箱中运行你的智能体时，该沙箱通常会保存你真实的上游 API 密钥（`OPENROUTER_API_KEY`、`OPENAI_API_KEY` 等）。沙箱中受到提示注入的智能体可以执行 `cat ~/.config/openrouter/auth.json` 或 `printenv | grep -i key`，然后窃取并外传这些密钥。

出站代理解决了这个问题：沙箱只保存不透明的**代理令牌**，绝不保存真实密钥。沙箱的所有出站流量都会经过主机上的本地 [iron-proxy](https://github.com/ironsh/iron-proxy) 守护进程（Apache-2.0，Go）；该进程会终止 TLS，并在将请求转发到上游之前，把代理令牌替换为真实凭证。即使沙箱遭到入侵，攻击者拿走的令牌也只能在**已配置的可信代理边界**之后使用——CA 私钥和代理端点的完整性都是该边界的一部分。如果流量可以被重定向到攻击者控制的代理基础设施（例如 CA 私钥被盗或代理端点被劫持），令牌提供的保证便不再成立。

此版本仅将出口代理接入 Docker 后端。Modal、Daytona、SSH 和 Singularity **尚未**获得代理环境变量或 CA 挂载。

## 它是什么

- 主机上的托管 `iron-proxy` 子进程，按需安装到 `~/.hermes/bin/iron-proxy`
- 位于 `~/.hermes/proxy/ca.crt` 的本地 CA，沙箱信任该 CA，因此 iron-proxy 可以对 TLS 进行中间人处理并重写标头
- 位于 `~/.hermes/proxy/proxy.yaml` 的 `proxy.yaml` 配置，其中列出允许的上游主机及机密转换映射
- 一个 `mappings.json` 文件，记录每个代理令牌对应的真实环境变量

沙箱会获得 `HTTPS_PROXY=http://host.docker.internal:9090`、`HTTP_PROXY=http://host.docker.internal:9091`，标准提供商环境变量（例如 `OPENROUTER_API_KEY`）则会被设为不透明的代理令牌。还会导出对应的 `HERMES_PROXY_TOKEN_<ENV_NAME>` 别名，用于诊断。现有的提供商 SDK 会读取常用的环境变量名，在 `Authorization` 中发送代理令牌，而 iron-proxy 的 `secrets` 转换会用主机端守护进程环境中的真实值替换它。

## 它不是什么

- 它**不是**入站 `hermes proxy` 命令；后者是 OAuth 聚合器反向代理。命令不同（`hermes egress`），方向也不同。
- 它**不**位于本地终端和提供商之间——仅位于沙箱和提供商之间。
- 它**不会**重写主机进程发起的进程内 LLM 调用所用的凭证。这些调用仍会直接使用你的 `.env` 密钥。这里的威胁模型是*沙箱*，而不是主机。

## 快速启动

```bash
# 1. Install the iron-proxy binary (pinned version, SHA-256 verified)
hermes egress install

# 2. Run the wizard: generates CA, mints proxy tokens for every provider key
#    in your env, writes proxy.yaml.
hermes egress setup

# 3. Start the proxy daemon
hermes egress start

# 4. Check status
hermes egress status
```

`hermes egress setup` 会从你的环境中发现提供商密钥。如果密钥只存在于 `~/.hermes/.env` 中（并未导出到 shell），setup 会自动读取该文件——无需先执行 `export`。

以后重新运行 `setup` 时（新增允许列表主机、轮换令牌、切换凭证来源），它会先停止正在运行的守护进程，因为配置保存在内存中，然后**询问是否替你重新启动它**，使更改立即生效。在 tty 中它会询问；传入 `--restart` 可始终重启，传入 `--no-restart` 则保持停止。若要在其他任何时候应用更改，可用 `hermes egress restart` 一条命令完成停止再启动。

一旦运行，Docker 终端后端会自动：

- 将 `~/.hermes/proxy/ca.crt` 挂载到沙箱中的 `/etc/ssl/certs/hermes-egress-ca.crt`
- 设置 `HTTPS_PROXY`、`HTTP_PROXY`、`REQUESTS_CA_BUNDLE`、`SSL_CERT_FILE`、`CURL_CA_BUNDLE`、`NODE_EXTRA_CA_CERTS`，使所有常见 HTTP 运行时都通过代理路由并信任该 CA
- 设置 `NODE_OPTIONS=--use-openssl-ca`（附加到 `docker_env.NODE_OPTIONS` 中已有的内容），使 Node.js 通过由其他 CA bundle 变量控制的 OpenSSL 存储进行路由——关于仍然存在的缺口，请参阅下文的 [Node.js 非对称 CA 注意事项](#nodejs-asymmetric-ca-caveat)
- 添加 `--add-host=host.docker.internal:host-gateway`，以便沙箱可以到达 Linux 上的主机端代理（Docker Desktop 在 macOS/Windows 上自动处理此问题）
- 在标准提供商环境变量名下导出代理令牌（例如 `OPENROUTER_API_KEY`），并为每个已生成的映射额外导出一个 `HERMES_PROXY_TOKEN_<ENV_NAME>` 诊断别名

## 配置

完整配置位于 `~/.hermes/config.yaml` 的 `proxy:` 部分。默认值以内联注释说明；所有配置项均为可选。

```yaml
proxy:
  # Master switch. When false the feature is a complete no-op — no
  # binaries downloaded, no docker mounts added, no subprocess started.
  enabled: false

  # Tunnel listener port. Sandboxes hit http://host.docker.internal:<port>.
  tunnel_port: 9090

  # Auto-download the pinned iron-proxy binary on first use.
  auto_install: true

  # Where iron-proxy looks up the real upstream secrets at egress time.
  #   env       — process env (default). Whatever is in your ~/.hermes/.env
  #               at proxy-start time is the source of truth.
  #   bitwarden — refetch from Bitwarden Secrets Manager on each proxy
  #               restart. Rotation in the BW web app propagates without
  #               touching .env. Requires `secrets.bitwarden.enabled: true`.
  credential_source: env

  # When true (default), the Docker backend refuses to start a sandbox if
  # the proxy is enabled but not running. Set to false to fall back to the
  # legacy "real credentials inside the sandbox" posture when the proxy
  # is unavailable.
  enforce_on_docker: true

  # When `credential_source: bitwarden` but the BWS access token /
  # project_id is missing OR the bws fetch returns no values for mapped
  # providers, the daemon raises by default (matches the spirit of "I
  # asked for rotation — don't silently use stale env values").  Set
  # to true to opt back into the legacy host-env fallback — useful for
  # migrations where you want to start switching to BW mode but haven't
  # wired every secret yet.
  allow_env_fallback: false

  # SSRF deny list applied to outbound traffic.  Omit / leave null to
  # use the safe default: loopback (v4 + v6), link-local (incl. cloud
  # metadata IPs at 169.254.169.254), RFC1918, IPv6 ULA, IPv4-mapped-v6,
  # CGNAT, and the RFC2544 benchmark range.  Set to an explicit `[]`
  # to opt out entirely (only sensible in hermetic tests).
  upstream_deny_cidrs: null

  # Extra allowed upstream hosts beyond the bundled defaults.
  # Wildcards (`*.foo.com`) are supported. The defaults cover OpenRouter,
  # OpenAI, Anthropic, Google, xAI, Mistral, Groq, Together, DeepSeek,
  # and Nous Research.
  extra_allowed_hosts: []
```

### 默认允许的上游主机

```
openrouter.ai           *.openrouter.ai
api.openai.com          api.anthropic.com
generativelanguage.googleapis.com
api.x.ai                api.mistral.ai
api.groq.com            api.together.xyz
api.deepseek.com        inference.nousresearch.com
```

如果你的智能体需要访问列表之外的上游——例如自托管推理端点、其他云 LLM 或 MCP 服务器——请将其添加到 `proxy.extra_allowed_hosts`。通配符会针对完整主机名进行匹配（`*.example.com` 匹配 `api.example.com` 和 `staging.example.com`，但不匹配 `example.com` 本身）。

### 默认 SSRF 拒绝 CIDR

无论是否在允许列表中，这些规则都会应用。iron-proxy 会在网络边界拒绝这些地址范围，因此通过允许列表主机名实施的 DNS 重绑定攻击无法访问 IMDS 或你的内部网络：

|CIDR|目的|
|---|---|
|`127.0.0.0/8`、`::1/128`|环回（v4 + v6）|
|`169.254.0.0/16`、`fe80::/10`|链路本地——**包括位于 `169.254.169.254` 的 AWS / GCP / Azure IMDS**|
|`10.0.0.0/8`、`172.16.0.0/12`、`192.168.0.0/16`|RFC1918|
|`fc00::/7`|IPv6 ULA|
|`::ffff:0:0/96`|IPv4 映射的 IPv6——封堵双栈 IMDS 绕过路径|
|`100.64.0.0/10`|RFC6598 CGNAT（由 AWS VPC、K8s Pod 网络使用）|
|`198.18.0.0/15`|RFC2544 基准范围|

如需覆盖默认值，请将 `proxy.upstream_deny_cidrs` 设为你自己的列表。如需完全停用（例如，封闭测试需要访问环回地址上的上游）：将其设为空列表 `[]`。

### 绑定策略

代理绝不会绑定 `0.0.0.0`。默认绑定因平台而异，因为 iron-proxy v0.39 仅支持**每个守护进程一个绑定地址**：

- **Linux：** Docker 网桥网关（默认为 `172.17.0.1:<tunnel_port>`）。容器通过 `host.docker.internal` 访问代理，而 `--add-host=host.docker.internal:host-gateway` 会将其准确解析为该网桥网关 IP——如果只绑定环回地址，沙箱内部将无法访问。网桥 IP 是主机 `docker0` 接口上的地址，因此不会暴露给局域网；默认网桥网络中的其他容器可以访问它，但请求仍然需要已生成的代理令牌，且上游必须在允许列表中。如果未检测到 Docker 网桥（Docker 未安装或未运行），绑定会回退到环回地址并发出警告。
- **macOS / Windows Docker Desktop：** 环回地址（`127.0.0.1:<tunnel_port>`）。Desktop 的 VPNkit 会将 `host.docker.internal` 路由到主机，因此容器可以访问环回地址；这是暴露范围最小的选择。

即使局域网中的其他设备获得了泄露的代理令牌，也无法使用该代理——这两种绑定都无法从外部网络访问。

我们还将 `metrics.listen: 127.0.0.1:0` 固定为该值，使守护进程内置的指标服务器使用临时环回端口，而不是默认的 `:9090`——否则它会与 `tunnel_port: 9090` 争用同一个套接字，导致守护进程以“address already in use”为由拒绝启动。请注意，`:0` 表示每次启动随机分配临时端口，而且该端口不会在任何地方公开，因此采用此固定值实际上等同于禁用指标。

如果 PATH 中优先级更高的恶意 `ip` 垫片试图注入非私有 IPv4 地址作为网桥地址（`0.0.0.0`、公网地址、多播地址、链路本地地址等），仍会回退到环回地址——我们绝不会绑定任何无法通过 `ipaddress.IPv4Address` + `is_*` 检查验证的地址。

## 涵盖的身份验证方案

`secrets` 转换会替换代理令牌在匹配位置中的每一次出现——而且它匹配的不只是 `Authorization: ***`：

| 提供商 | 环境变量 | 替换位置 |
|---|---|---|
| OpenRouter、OpenAI、Groq、Together、DeepSeek、Mistral、xAI、Nous | `*_API_KEY` | `Authorization` 标头 |
| Anthropic 原生 | `ANTHROPIC_API_KEY` | `x-api-key` + `Authorization` |
| Azure OpenAI | `AZURE_OPENAI_API_KEY` | `api-key` + `Authorization`（`*.openai.azure.com`、`*.cognitiveservices.azure.com`、`*.services.ai.azure.com`） |
| Google AI Studio（Gemini） | `GEMINI_API_KEY` / `GOOGLE_API_KEY` | `x-goog-api-key` 标头或 `?key=` 查询参数 |

`GEMINI_API_KEY` 和 `GOOGLE_API_KEY` 被视为一个凭证：在 **两个** 名称下创建单个代理令牌并注入到沙箱中，并且主机环境中的任一名称都满足发现。

## 未覆盖的提供商

涉及请求签名或由 SDK 生成 OAuth 的身份验证方案无法通过静态标头替换完成交换——如果存在相应环境变量，沙箱会保存这些提供商的**真实凭证**，因此对它们的出站隔离保证并不完整：

| 环境变量 | 提供商 | 原因 |
|---|---|---|
| `AWS_ACCESS_KEY_ID`、`AWS_SECRET_ACCESS_KEY` | AWS Bedrock / SageMaker | SigV4 签名请求 |
| `GOOGLE_APPLICATION_CREDENTIALS` | GCP Vertex AI | 从服务账号文件生成 OAuth |

大多数开发者笔记本电脑上都有这些环境变量，供无关工具使用（terraform、gcloud、aws CLI、ECR 推送）。它们会在向导和 `hermes egress status` 中显示为警告，但绝不会阻止代理启动。如果你不在沙箱中使用这些提供商，请 `unset` 这些变量以清除警告。

## Bitwarden 集成

如果你已通过 [`hermes secrets bitwarden setup`](../secrets/bitwarden) 使用 Bitwarden Secrets Manager，出站代理就可以从中获取真实凭证，而不是从 `os.environ` 获取：

```bash
hermes egress setup --from-bitwarden
```

这会设置 `proxy.credential_source: bitwarden`，并从你的 BW 项目中发现提供商环境变量名。

### 轮换语义

当 `credential_source: bitwarden` 时，iron-proxy 守护进程**每次启动**都会通过 `bws secret list <project_id>` 从 BWS 重新获取机密。因此轮换流程如下：

1. 在 Bitwarden Web 应用程序中轮换密钥。
2. 在主机上运行 `hermes egress stop && hermes egress start`。
3. 此后启动的沙箱会将代理令牌交换为新值。

无需编辑 `.env`，也无需重启主机上的 Hermes。只有代理守护进程会接触新值——你的主机进程和 `os.environ` 均不受影响。

### 启动时快速失败并明确报错

当 `credential_source: bitwarden` 时，`hermes egress start` 会在向导层预先检查，`_build_proxy_subprocess_env` 还会在守护进程层再次检查：

- BWS 访问令牌环境变量未设置 → 拒绝启动，并提示执行 `unset` 后重新运行，或执行 `hermes egress setup --no-bitwarden` 切换回 env 模式
- `secrets.bitwarden.project_id`为空→拒绝启动并提示运行`hermes secrets bitwarden setup`
- `bws secret list` 不返回一个或多个映射提供者的值 → 拒绝启动，列出缺失的名称

这是故意的。在 BW 模式下回退到主机环境会重新引入 BW 路径本应消除的过时错误（操作员选择 BW 作为轮换保证；静默回退会破坏该保证）。

对于迁移场景，配置标志 `proxy.allow_env_fallback: true` 可重新启用旧版的“如果 BWS 无法访问，则静默回退到主机环境”行为。当你逐个将机密迁移到 BW，并希望守护进程使用任何可用值启动时，可以使用它。

### 切换凭证源

|从|到|命令|
|---|---|---|
| env | bitwarden | `hermes egress setup --from-bitwarden` |
| bitwarden | env | `hermes egress setup --no-bitwarden` |

**在不带这两个标志中任何一个的情况下重新运行 `hermes egress setup`，会保留现有的 `credential_source`**——向导拒绝静默降级回 env。这一点很重要：一旦配置了 bitwarden 模式，你选择的就是其轮换保证；必须明确表示“我想再次使用 env”才能更改它。

## 命令

CLI 子命令树：

```
hermes egress install                  # download the pinned iron-proxy binary
hermes egress install --force          # re-download even if a managed copy exists

hermes egress setup                    # interactive wizard
hermes egress setup --tunnel-port N    # override the tunnel listener port
hermes egress setup --from-bitwarden   # use BWS as credential source (fail-loud)
hermes egress setup --no-bitwarden     # explicitly switch back to env mode
hermes egress setup --rotate-tokens    # mint fresh tokens for every provider
                                       #   (default preserves existing)

hermes egress start                    # spawn the managed proxy daemon
hermes egress stop                     # SIGTERM (then SIGKILL after 5s grace)
hermes egress restart                  # stop (if running) then start — needed when
                                       #   upstream SECRETS change (rotation, new provider)
hermes egress reload                   # hot-reload the ruleset from proxy.yaml via the
                                       #   management API — no restart, no dropped
                                       #   connections (allowlist / mapping edits)

hermes egress status                   # binary + config + pid + listening state + mappings
hermes egress status --show-tokens     # print proxy tokens in full
                                       #   (default: redacted prefix + suffix only)

hermes egress disable                  # flip proxy.enabled = false
                                       #   (does not stop a running proxy)

hermes egress config                   # print the path to proxy.yaml for debugging
```

### 令牌轮换

默认情况下，`hermes egress setup` 会**保留**已有提供商的代理令牌。添加新提供商时，只为新提供商创建新令牌；现有令牌保持不变。这样可避免在重新运行向导时，正在运行的沙箱开始收到 401。

`--rotate-tokens` 会轮换所有令牌：

```bash
hermes egress setup --rotate-tokens
```

当已有令牌且 stdin 是 tty 时，向导会提示确认：

```
⚠  --rotate-tokens will invalidate proxy tokens in every running
   Hermes sandbox.  They will start 401-ing against upstreams until restarted.
Type 'rotate' to confirm:
```

非 tty 调用（CI、脚本）会跳过提示——该标志会被视为有意传入。覆盖任何内容之前，当前的 `mappings.json` 都会被复制为带时间戳的同级文件，以便手动恢复：

```
backup: ~/.hermes/proxy/mappings.json.rotated-20260524T143012
```

`hermes egress setup` 在重写配置或令牌映射时会停止正在运行的守护进程，因为守护进程将旧 YAML 保存在内存中。执行 `--rotate-tokens` 后：

```bash
hermes egress start
```

已在运行的容器仍保存旧令牌，需要重新启动才能获取新令牌。新的持久化 Docker 容器包含 egress-posture 标签，因此 Hermes 不会在新会话中复用出站代理启用前或令牌轮换前创建的容器。

## 状态目录布局

Iron-Proxy 维护的所有内容都存在于 `~/.hermes/proxy/` 中：

| 路径 | 模式 | 用途 |
|---|---|---|
| `~/.hermes/proxy/`（目录） | `0o700` | 仅你拥有且可遍历 |
| `ca.crt` | `0o644` | 分发到沙箱中的公共 CA 证书 |
| `ca.key` | `0o600` | CA 签名密钥——绝不离开主机 |
| `proxy.yaml` | `0o600` | iron-proxy 配置；每次 `setup` 都会重写 |
| `mappings.json` | `0o600` | 沙箱代理令牌 → 上游环境变量 |
| `mappings.json.rotated-*` | `0o600` | 由 `--rotate-tokens` 创建的备份 |
| `iron-proxy.pid` | `0o600` | 正在运行的守护进程的 PID |
| `iron-proxy.nonce` | `0o600` | 用于防御 PID 回收的每次启动随机数 |
| `iron-proxy.log` | `0o600` | 守护进程 stdout/stderr——**在 v0.39 上包括每请求记录** |
| `audit.log` | `0o600` | 为未来二进制版本的专用每请求审计流预留；预先创建，确保上游接入该功能时仍满足隐私约定 |

CA 私钥是最敏感的文件。创建时从写入第一个字节起权限就是 `0o600`（不存在 umask 窗口期 TOCTOU），并使用 `O_NOFOLLOW`，因此同 UID 攻击者无法通过预先植入的符号链接重定向它。pidfile、nonce 文件、守护进程日志和审计日志也采用相同处理。

### iron-proxy v0.39 的日志记录

在当前固定的二进制版本（**v0.39.0**）上，iron-proxy 会将所有输出——守护进程级诊断和每请求记录——都写入 **`~/.hermes/proxy/iron-proxy.log`**。v0.39 的 `config.Log` 结构体没有单独的 `audit_path` 字段，因此无法把每请求记录路由到独立的专用流。

我们仍然在 `0o600` 和 `O_NOFOLLOW` 处预先创建 `~/.hermes/proxy/audit.log`，因为：

1. 它为未来版本升级预留了路径：当固定版本升级到支持 `log.audit_path` 的版本时，每请求记录会开始流入该文件，无需操作员重新配置。**在此之前，该文件会一直保持 0 字节——暂时不要让监控、告警或取证工具读取它。**目前所有用途都应使用 `iron-proxy.log`。
2. 从第一个字节起即为 0o600 的保证，可防范上游修复到来时的权限问题：如果文件尚不存在，v0.40+ 会按其默认 umask 创建它。

在该版本发布之前，请将 `iron-proxy.log` 视为双方受众的真相来源：

- 守护进程级事件（启动横幅、绑定错误、关闭原因、转换错误）。用于运维和故障排除。
- 每请求记录（CONNECT 到允许列表中的上游、触发机密交换、允许列表拒绝）。用于取证和合规。

这两个文件都会跨重启追加写入。如果你关心长期运行主机的磁盘占用，请使用 logrotate 轮换它们。

## 它是如何运作的

```
┌──────────────┐                ┌──────────────┐                ┌─────────────┐
│ Docker       │ CONNECT /     │ iron-proxy    │ HTTPS w/       │ OpenRouter  │
│ sandbox      ├──────────────▶│ (host:9090)   ├───────────────▶│ / OpenAI /  │
│              │ HTTP forward  │               │ real API key   │ Anthropic …  │
│ has:         │ w/ proxy tok  │ mints leaf    │                │             │
│ - proxy tok  │ in Auth hdr   │ cert from CA  │                │             │
│ - CA cert    │               │ matches token │                │             │
│ - HTTPS_PROXY│               │ swaps secret  │                │             │
└──────────────┘               └──────────────┘                └─────────────┘
                                       │
                                       │ daemon + per-request log (combined on v0.39)
                                       ▼
                              ~/.hermes/proxy/iron-proxy.log
                              (~/.hermes/proxy/audit.log reserved for v0.40+ split stream)
```

1. 沙箱发出 HTTPS 请求，例如 `POST https://openrouter.ai/v1/chat/completions`，并携带 `Authorization: Bearer hermes...er-…`（代理令牌，而不是真实密钥）。
2. 由于已设置 `HTTPS_PROXY`，请求会以 CONNECT 隧道的形式发送到 iron-proxy。
3. iron-proxy 检查允许列表。`openrouter.ai` 在允许列表中。
4. iron-proxy 为 `openrouter.ai` 生成由我们的 CA 签名的叶证书，终止 TLS 连接，检查请求。
5. `secrets` 转换会匹配 `Authorization` 标头中的代理令牌字符串，并替换为真实的 `OPENROUTER_API_KEY` 值；该值来自 iron-proxy 自身的环境。
6. 请求被重新加密并转发到 OpenRouter。
7. 在 v0.39 上，请求会记录到 `~/.hermes/proxy/iron-proxy.log`。当固定的二进制版本支持拆分日志流（v0.40+）时，每请求记录将流向 `~/.hermes/proxy/audit.log`，守护进程级诊断仍保留在 `iron-proxy.log` 中。请参阅 [iron-proxy v0.39 的日志记录](#logging-on-iron-proxy-v039)。

对于不在允许列表中的主机（例如 `https://attacker.example.com/leak?key=...`），请求会在任何字节离开主机前被拒绝，并返回 HTTP 403。拒绝事件会连同上游主机和来源沙箱一起记录到 `iron-proxy.log`。

### 将 CA 分发到沙箱

当 Docker 后端使用 `proxy.enabled: true` 启动容器并且守护进程正在侦听时，它将这些参数添加到 `docker run`：

| 参数 | 用途 |
|---|---|
|`-v ~/.hermes/proxy/ca.crt:/etc/ssl/certs/hermes-egress-ca.crt:ro`|CA 的只读挂载|
|`-e HTTPS_PROXY=http://host.docker.internal:9090`|Python httpx / curl / Go 默认传输 / Node fetch|
|`-e HTTP_PROXY=http://host.docker.internal:9091`|对于普通 HTTP，curl + wget — 普通的 HTTP 转发侦听器位于 `tunnel_port + 1`|
|`-e NO_PROXY=127.0.0.1,localhost,::1`|沙箱内的环回开发服务器绕过代理|
|`-e REQUESTS_CA_BUNDLE=…ca.crt`|Python`requests`|
|`-e SSL_CERT_FILE=…ca.crt`|Python `ssl` 模块 / OpenSSL — **替换**系统存储|
|`-e CURL_CA_BUNDLE=…ca.crt`|curl — **替换**系统存储|
|`-e NODE_EXTRA_CA_CERTS=…ca.crt`|Node.js — **添加**到系统存储|
|`-e NODE_OPTIONS="<your value> --use-openssl-ca"`|Node.js——通过 OpenSSL 存储路由（以追加方式设置；你原有的 `--max-old-space-size` 等选项会保留）|
|`-e HERMES_EGRESS_PROXY=1`|智能体可读取的哨兵值，用于判断自身是否已感知代理|
|`-e OPENROUTER_API_KEY=<proxy-token>`|标准提供商环境名称接收代理令牌，以便现有 SDK 继续工作|
|`-e HERMES_PROXY_TOKEN_<NAME>=…`|每个映射的诊断别名；与标准提供商环境变量相同的值|
|`--add-host=host.docker.internal:host-gateway`|仅限 Linux； Docker Desktop 自动映射它|

#### Node.js 非对称 CA 警告

`REQUESTS_CA_BUNDLE` / `SSL_CERT_FILE` / `CURL_CA_BUNDLE` 会**替换**沙箱内的系统 CA 存储，`NODE_EXTRA_CA_CERTS` 则是向其中**添加**证书。原则上，沙箱内的 Node.js 进程可以打开原始 `net.Socket` 并自行发起 TLS 握手，从而绕过代理——系统 CA 存储仍信任真实的上游证书，因此在 Python / curl 验证失败的场景中，该请求仍会成功。

`NODE_OPTIONS=--use-openssl-ca` 会附加到 `docker_env.NODE_OPTIONS` 中已有的内容。这会强制 Node 使用由 `SSL_CERT_FILE` 控制的 OpenSSL 存储，从而缩小这种不对称。它**无法**覆盖显式向 `tls.connect()` 或 `https.request()` 传入自有 `ca` 选项的代码，但能封堵最容易利用的情况。

这是 v1 的已知限制。请关注 [github.com/ironsh/iron-proxy/issues](https://github.com/ironsh/iron-proxy/issues) 了解上游解决进展；在此期间，不要在依赖出站隔离的沙箱中运行会打开原始套接字的不受信任 Node 代码。

### docker\_env 冲突

如果你在 `docker_env:` 配置块中设置了控制代理的环境变量（虽少见但有可能），当 `enforce_on_docker: true` 时，Hermes 会拒绝启动沙箱。其中包括两类：

- 出站控制变量：`HTTPS_PROXY`、`HTTP_PROXY`、`NO_PROXY`、`REQUESTS_CA_BUNDLE`、`SSL_CERT_FILE`、`CURL_CA_BUNDLE`、`NODE_EXTRA_CA_CERTS`
- 真实提供商环境变量：`mappings.json` 中的每个名称（例如 `OPENROUTER_API_KEY`、`OPENAI_API_KEY`）

错误示例：

```
docker_env in config.yaml overrides egress-proxy variables
['HTTPS_PROXY', 'OPENROUTER_API_KEY']; enforce_on_docker is enabled.
Remove these keys from docker_env or disable enforce_on_docker to
opt out of egress isolation.
```

使用 `enforce_on_docker: false` 时，同样的情况只会显示为警告，并以你的 `docker_env` 值为准——这对迁移或测试很有用，但也意味着你明确选择退出隔离保证。

## PID 和随机数防御

守护进程的 pidfile 是用 `O_EXCL` + `O_NOFOLLOW` + 所有权检查编写的。并发 `hermes egress start` 调用会产生以下两种结果之一：

- 现有 pidfile 指向仍在运行的 iron-proxy → 第二次启动被拒绝，并显示“another start in progress”，同时提示运行 `hermes egress stop`
- 现有的 pidfile 已过时（守护进程崩溃）→ 第二次启动取消链接并重试一次

除此之外，每个`start_proxy`在两个地方植入一个新的随机数：

- 守护进程环境中的`HERMES_IRON_PROXY_NONCE=<nonce>`
- `~/.hermes/proxy/iron-proxy.nonce`（0o600 pidfile 的同级）

当 `hermes egress stop`（或任何其他 `_pid_alive` 检查）需要确认某个 PID 仍指向*我们的*守护进程，而不是 iron-proxy 崩溃后恰好被分配相同 PID 的无关进程时，它会读取 `/proc/<pid>/environ` 并查找该随机数。磁盘上的副本使这一机制可以跨 CLI 调用工作（内存中的 `_proxy_nonce` 属于单个进程，每次调用 `hermes` 都会重置）。

如果随机数检查失败，代码会回退到检查 `argv[0]` 的基本名称是否为 `iron-proxy`。`stop_proxy` 还会在发送 SIGTERM 前记录 `/proc/<pid>/stat` 中的启动时间，并在 5 秒宽限期后再次验证——如果启动时间发生变化，说明等待期间 PID 已被回收，此时会抑制 SIGKILL 并发出警告。

## 安全模型

**这可以防止什么：**

- Docker 沙箱中的提示注入代理读取 `printenv` / 凭证文件并窃取真实密钥。
- 沙箱中的依赖项遭到入侵并向任意主机回连——默认拒绝的允许列表会阻止未知目的地。
- 智能体访问云元数据端点（`169.254.169.254`）——iron-proxy 默认通过 `upstream_deny_cidrs` 拒绝这些端点，包括 IPv4 映射 IPv6 形式 `::ffff:169.254.169.254`。
- 通过允许列表中的主机名实施 DNS 重绑定以访问私有 IP——拒绝 CIDR 会在连接时检查，而不是仅在加入允许列表时检查。
- 同 UID 本地进程读取 iron-proxy 守护进程的环境来抓取机密——只会转发映射引用的环境变量名，而不是完整的主机环境。
- 局域网中的其他设备利用泄露的沙箱代理令牌消耗你的 API 配额——代理绑定 Docker 网桥网关（Linux）或环回地址（Docker Desktop），绝不绑定 `0.0.0.0`，因此无法从外部网络访问。

**它无法防范什么：**

- 受损的主机进程。如果代理进程本身受到损害，则主机的`~/.hermes/.env`中的真实密钥无论如何都会暴露。这是针对“沙箱”危害而非主机危害的深度防御功能。
- **可信代理边界本身失守。** 令牌交换保证假设沙箱信任已挂载的 CA 证书（`/etc/ssl/certs/hermes-egress-ca.crt`），且流量确实到达*我们的* iron-proxy。如果 CA 私钥被盗，或沙箱出站流量被重定向到攻击者控制的代理基础设施，中间攻击者就可以出示有效的叶证书，代理令牌也不再构成有意义的边界（参见 [MITRE ATT&CK T1588.004](https://attack.mitre.org/techniques/T1588/004/)——获取可实施 AiTM 的 TLS 证书材料）。因此应妥善保护 CA 密钥（权限为 `0600`，仅存在于主机）和代理端点。
- 使用原始套接字绕过 `HTTPS_PROXY` 的沙箱进程。代理无法拦截未路由到它的内容。 Node.js 通过 `NODE_OPTIONS=--use-openssl-ca` 得到部分缓解（请参阅上面的警告）。
- 显式挂载到 Docker 的凭证文件（`terminal.credential_files` 或由技能注册的挂载）。出站保护仅覆盖提供商环境变量；不会检查任意挂载文件。不要把真实的提供商凭证挂载到强制执行出站隔离的沙箱中。
- 通过允许列表中的主机外传数据。如果允许 `api.openai.com`，智能体可以把外传数据嵌入发往该主机的请求正文。守护进程日志会记录该请求发生过，但不会阻止它。
- 未覆盖的提供商（AWS Bedrock SigV4、GCP Vertex 服务账号 OAuth）。它们的环境变量仍在沙箱中；如果启用这些提供商，其凭据将完全绕过代理。请参阅[未覆盖的提供商](#uncovered-providers)。
- iron-proxy 对内存中机密的归零。Go 二进制文件会在进程内存中保存换入的真实凭证；同 UID 攻击者读取核心转储或 `/proc/<pid>/mem` 时会暴露这些凭证。这超出本层的范围。

## 失效模式

- **未安装二进制文件，`auto_install: true`** — 首先`hermes egress setup` 或`hermes egress start` 下载它。 SHA-256 已针对上游`checksums.txt` 进行验证。
- **未安装二进制文件，`auto_install: false`** — `start` 失败，并显示一条明确的消息指向手动安装。
- **`enabled: true` 但代理未运行**——使用 `enforce_on_docker: true`（默认）时，Docker 沙箱创建会拒绝启动，并给出说明性错误。使用 `enforce_on_docker: false` 时，则会回退到携带真实凭证的直接出站方式并记录警告。
- **端口冲突**——iron-proxy 立即退出； `hermes egress start` 报告最后 20 行日志并以非零退出失败。
- **上游主机被拒绝**——沙箱从代理收到 HTTP 403，响应正文会说明哪个主机不被允许。智能体会看到并报告该错误。
- **云元数据 IP (169.254.169.254) 请求** — 被 `upstream_deny_cidrs` 拒绝，无论白名单如何。
- **`docker_env` 与代理控制变量发生冲突（强制执行）** — 沙箱创建拒绝使用冲突键的名称。
- **`docker_forward_env` 尝试转发受保护的提供商密钥（强制执行）** — 沙箱创建拒绝；从 `docker_forward_env` 中删除密钥或使用 `proxy.enforce_on_docker: false` 选择退出。
- **`docker_extra_args` 覆盖代理环境/网络控制（强制执行）** — 沙箱创建拒绝；用户提供的`-e HTTPS_PROXY=...`、`--env-file`或`--network`参数在Hermes生成的参数之后运行，并且可以绕过出口。
- **`credential_source: bitwarden`** 中缺少BWS 访问令牌 — `hermes egress start` 拒绝使用 `--no-bitwarden` 作为恢复提示。
- **iron-proxy 未在 5 秒内完成绑定**——进程会被终止，pidfile 会被删除，错误中会注明端口并附上 `iron-proxy.log` 尾部内容。
- **并发 `hermes egress start` 调用** — 如果第一个守护进程已启动，则第二个调用会拒绝并显示“另一个启动正在进行中”；否则，第二个将取消旧 pid 文件的链接并继续。

## 故障排除

### “拒绝启动：未设置 BWS_ACCESS_TOKEN”

你启用了 `credential_source: bitwarden`，但 shell 中没有访问令牌环境变量。可选择以下任一方式：

```bash
export BWS_ACCESS_TOKEN=…   # one-shot
hermes egress start
```

或者将其移至`~/.hermes/.env`。或者切换回 env 模式：

```bash
hermes egress setup --no-bitwarden
```

### “iron-proxy 立即退出”

查看 `~/.hermes/proxy/iron-proxy.log` 的最后 20 行。常见原因：

- 端口已被占用 → 更改 `proxy.tunnel_port`，或终止占用 9090 的其他进程
- `proxy.yaml`无效→运行`hermes egress setup`重新生成
- CA 证书/密钥权限错误 → `chmod 0o600 ~/.hermes/proxy/ca.key`

### “iron-proxy 未在 5s 内绑定 \<bind-host\>:9090”

守护进程已经启动，但始终没有绑定监听器。通常表示二进制文件卡死，或启动时正在执行耗时操作。请检查 `~/.hermes/proxy/iron-proxy.log`。孤儿进程会自动终止，pidfile 也会被清理，因此可以直接重试 `hermes egress start`。

### 沙箱连接代理超时（Linux）

容器会将 `host.docker.internal` 解析为 Docker 网桥网关，代理也绑定在那里，但主机防火墙（通常是默认拒绝 INPUT 的 `ufw`）会丢弃 `docker0` 上从容器到主机的流量。请从容器中验证：

```bash
docker run --rm --add-host host.docker.internal:host-gateway busybox \
  nc -zv -w 3 host.docker.internal 9090
```

如果在 `hermes egress status` 显示 `listening` 时超时，请在防火墙中允许桥接子网，例如对于 UFW：

```bash
sudo ufw allow in on docker0 to any port 9090 proto tcp
sudo ufw allow in on docker0 to any port 9091 proto tcp
```

（9091 = `tunnel_port + 1` 上的普通-HTTP 转发侦听器。）

### 沙箱从代理看到`HTTP 403`

沙箱内的智能体尝试访问不在 `proxy.extra_allowed_hosts` 中的主机。403 响应正文会说明是哪个主机。如果你希望允许它，请将其加入配置：

```yaml
proxy:
  extra_allowed_hosts:
    - api.example.com
    - "*.staging.example.com"
```

然后`hermes egress setup`（重新生成`proxy.yaml`）和`hermes egress stop && hermes egress start`。

### 沙箱看到 SSL 验证错误

可能是 CA 未挂载到沙箱中（这种情况很少见；当 `proxy.enabled: true` 时，Docker 后端会自动完成挂载），也可能是镜像中的 HTTP 客户端读取了非标准环境变量。

```bash
# Inside the sandbox:
cat /etc/ssl/certs/hermes-egress-ca.crt | head -1
# Should print: -----BEGIN CERTIFICATE-----
env | grep -E "^(REQUESTS|CURL|SSL|NODE).*CA"
# Should list all four CA-bundle env vars pointing at /etc/ssl/certs/hermes-egress-ca.crt
```

如果证书不存在，请检查是否已设置 `proxy.enabled: true`，并确认 `hermes egress status` 显示 `Listening yes`。如果缺少环境变量，沙箱镜像可能运行了会移除这些变量的入口点——请检查你的 `docker_env` 配置。

### 沙箱从上游看到`HTTP 401`

两个常见原因：

1. **重新设置时覆盖了令牌。** 你运行了 `hermes egress setup --rotate-tokens`（或以其他方式轮换了令牌），但正在运行的沙箱仍保留旧令牌。请重新启动沙箱。
2. **Bitwarden 刷新静默失败。** 新的明确失败行为下不应出现这种情况，但如果设置了 `proxy.allow_env_fallback: true`，守护进程可能会使用过期的环境变量值启动。请检查守护进程环境（`/proc/<iron-proxy-pid>/environ`）中是否存在预期的 `OPENROUTER_API_KEY` 等变量。

### 父进程死亡后“地址正在使用”

Hermes 父进程在执行 `hermes egress start` 期间终止（在监听探测期间按 Ctrl-C、发生 OOM 或 panic）。新的修复逻辑会在 `Popen` 后立即写入 pidfile，因此可以恢复孤儿进程：

```bash
hermes egress stop   # finds the orphan via the pidfile, kills it
hermes egress start
```

如果 `hermes egress stop` 显示“iron-proxy was not running”，但仍能在 `ps` 中看到守护进程，说明 pidfile 已失去同步。可手动恢复：

```bash
pkill -TERM iron-proxy
rm -f ~/.hermes/proxy/iron-proxy.pid ~/.hermes/proxy/iron-proxy.nonce
hermes egress start
```

### 检查每个请求的行为

在固定的二进制版本（**v0.39**）上，守护进程级事件和每请求记录都写入 `~/.hermes/proxy/iron-proxy.log`。其格式为逐行分隔的 JSON。可针对特定上游执行 grep：

```bash
grep '"upstream":"openrouter.ai"' ~/.hermes/proxy/iron-proxy.log | tail -20
```

或者实时观看：

```bash
tail -f ~/.hermes/proxy/iron-proxy.log | jq
```

当固定版本升级到 v0.40+（新增 `log.audit_path`）时，每请求记录将转移到 `~/.hermes/proxy/audit.log`，`iron-proxy.log` 则只保存守护进程级事件。在此之前，`audit.log` 是空占位文件（以 `0o600` 权限预先创建，使未来的守护进程继承严格权限）——目前应将 logrotate / 监控工具接入 `iron-proxy.log`，并计划在版本升级后加入 `audit.log`。

## 限制 (v1)

- 仅支持 Docker 后端。Modal、Daytona 和 SSH 的接入会在后续独立 PR 中完成。
- 使用基于签名的身份验证（AWS SigV4、GCP 服务账号 OAuth）的提供商会完全绕过代理——请参阅[未覆盖的提供商](#uncovered-providers)。基于标头令牌的提供商（Bearer、`x-api-key`、`api-key`、`x-goog-api-key`）均已覆盖。
- 没有本机 Windows 二进制上游。在 Linux / macOS / WSL 上运行。
- 第一代 CA 是有效期 10 年的自签名证书。轮换需要手动运行 `openssl genrsa ...`（或等待后续加入 `hermes egress rotate-ca`）。
- 重新运行 setup 时，如果配置或映射被重写，正在运行的守护进程会停止；之后需要重启守护进程（如果只更改规则集，也可执行 `hermes egress reload`），令牌轮换后还要重启已经运行的沙箱。
- iron-proxy 的内存密钥清零由上游控制。具有 `/proc/<pid>/mem` 读取权限的同 UID 攻击者可以从守护进程内存中读取替换后的密钥。
- iron-proxy v0.39 仅支持**每个守护进程一个绑定地址**（Linux 上绑定 Docker 网桥网关，Docker Desktop 上绑定环回地址），并将守护进程日志与每请求记录合并到单一日志流中。当上游加入 `proxy.http_listens`（复数）和 `log.audit_path` 后，可通过版本升级接入多地址绑定和专用审计流。

## 参见

- 上游项目：[github.com/ironsh/iron-proxy](https://github.com/ironsh/iron-proxy)
- 上游文档：[docs.iron.sh](https://docs.iron.sh/)
- Bitwarden 集成：[`hermes secrets bitwarden`](../secrets/bitwarden)
- Hermes Docker 终端后端：[Docker](../docker)
- 开发者/贡献者参考：[Egress proxy internals](../../developer-guide/egress-internals)
