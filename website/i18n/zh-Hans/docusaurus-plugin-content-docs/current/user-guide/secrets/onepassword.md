# 1Password

在进程启动时从 [1Password](https://1password.com/) 解析提供商 API 密钥，而不是将其以明文形式存储在 `~/.hermes/.env` 中。您将密钥保存在 1Password 条目中，并通过 `op://vault/item/field` 引用它们；轮换凭据只需在 1Password 中进行一次更改。

## 工作原理

1. 安装官方 [1Password CLI](https://developer.1password.com/docs/cli/get-started/)（`op`）并完成身份验证——可使用**服务帐户令牌**（无头服务器），也可使用**交互式/桌面会话**（您的笔记本电脑）。
2. 在 `~/.hermes/config.yaml` 中将环境变量名称映射到 `op://` 引用。
3. 每次 `hermes`（或网关，或 cron 作业）启动时，在加载 `~/.hermes/.env` 后，Hermes 都会为每个引用运行 `op read`，并将解析后的值设置到 `os.environ` 中。
4. 默认情况下，Hermes 会**覆盖**环境中已有的值，因此 1Password 是唯一事实来源——轮换一次凭据后，每个 Hermes 进程都会在下次启动时获取它。若希望改由 `.env` 优先，请将 `override_existing: false`。

Hermes 不会代您进行身份验证，也不会下载 `op`：它仅调用您已安装且已信任的 CLI。如果缺少 `op`、您的会话被锁定，或引用有误，Hermes 会打印一条单行警告，并继续使用 `.env` 中已有的任何凭据——绝不会阻塞启动。

## 身份验证

`op` 支持两种适合非交互式使用的模式；Hermes 均可使用：

- **服务帐户**（推荐用于服务器/CI）：在 1Password 中创建服务帐户，授予其相关保险库的读取权限，并将其令牌作为 `OP_SERVICE_ACCOUNT_TOKEN` 导出到 `~/.hermes/.env`。该令牌本身就是凭据——请像对待其他任何持有者令牌一样对待它。
- **桌面 / 交互式会话**（笔记本电脑）：运行 `op signin`（或在 1Password 应用中启用 CLI 集成）。Hermes 会将您的 `OP_SESSION_*` 变量传递给 `op` 子进程。1Password 缓存键包含这些会话变量，因此登录不同帐户时，绝不会提供在先前身份下缓存的值。

## 引导令牌

当您使用**服务帐户令牌**进行身份验证时，该令牌本身就是 Hermes 在解析任何 `op://` 引用*之前*所需的引导凭据。它必须存在于解析密钥的每个进程的 `os.environ` 中——包括 cron 作业（`kanban.dispatch_in_gateway: false`）、子进程调用、CLI 运行、macOS launchd 代理和 Docker 容器——而不只是交互式网关。有三种方式可使其可用，按优先级排序：

1. **放入 `~/.hermes/.env`（推荐）。**`hermes secrets onepassword setup --token <token>` 会将令牌写入 `~/.hermes/.env`，与 Bitwarden 的 `BWS_ACCESS_TOKEN` 完全相同。由于 `load_hermes_dotenv()` 始终加载 `.env`，该令牌会在所有位置可用，无需额外设置。这是最简单且可靠的选项。

2. **放入 `~/.hermes/.op.env`（已被 gitignore）。**如果您希望将服务帐户令牌保留在 `.env` 之外——例如，您可以将 `.env` 提交到私有 dotfiles 仓库，而令牌仍不进入版本控制——请将其置于 `~/.hermes/.op.env`：

   ```bash
   echo 'OP_SERVICE_ACCOUNT_TOKEN=ops_...' > ~/.hermes/.op.env
   chmod 600 ~/.hermes/.op.env
   ```

   Hermes 会在启动时自动加载 `.op.env`，在 `.env` **之后**，且绝不会覆盖环境中已有的令牌。`.op.env` 已被 gitignore，因此令牌绝不会进入已提交的文件。

3. **通过 systemd `EnvironmentFile`（Linux 网关）。**如果您在 systemd 下运行网关，可将令牌直接注入服务环境：

   ```ini
   [Service]
   EnvironmentFile=-/home/youruser/.hermes/.op.env
   ```

   以此方式注入的令牌优先级更高——Hermes 检测到 `OP_SERVICE_ACCOUNT_TOKEN` 已设置后，会完全跳过加载 `.op.env`。

如果令牌只能通过交互式 shell 获得（`op signin`、`.bashrc` 中的 `OP_SESSION_*` 导出等），cron 作业或新启动的子进程不会继承它；这些上下文会记录警告，并回退为使用 `.env` 已有的任何凭据。对于任何非交互式工作负载，请使用上述三个选项之一。

## 设置

### 1. 安装并登录 `op`

请遵循 [1Password CLI 入门指南](https://developer.1password.com/docs/cli/get-started/)。验证其是否正常工作：

```bash
op whoami
```

### 2. 启用集成

```bash
hermes secrets onepassword setup
```

此操作会验证 `op` 是否在 `PATH` 中（或使用 `--binary-path`），记录您的帐户/令牌设置，检查活动会话，并将 `secrets.onepassword.enabled: true` 打开。非交互式标志：

```bash
hermes secrets onepassword setup \
  --account my.1password.com \
  --token-env OP_SERVICE_ACCOUNT_TOKEN \
  --token "$OP_SERVICE_ACCOUNT_TOKEN"
```

### 3. 映射您的凭据

引用格式为 `op://<vault>/<item>/<field>`：

```bash
hermes secrets onepassword set OPENAI_API_KEY    "op://Private/OpenAI/api key"
hermes secrets onepassword set ANTHROPIC_API_KEY "op://Private/Anthropic/credential"
```

### 4. 预览并确认

```bash
hermes secrets onepassword sync     # 试运行：立即解析，并显示将应用的内容
hermes secrets onepassword status   # 配置 + 二进制文件 + 引用 + 身份验证
```

从现在起，每次 `hermes` 调用都会在启动时解析引用。每个进程中首次应用密钥时，您会在 stderr 中看到一行摘要。

## CLI

| 命令 | 功能 |
|---|---|
| `hermes secrets onepassword setup` | 验证 `op`、设置帐户 / 令牌环境变量、启用 |
| `hermes secrets onepassword status` | 显示配置、二进制文件、身份验证和已配置的引用 |
| `hermes secrets onepassword token` | 轮换服务帐户令牌：使用 `op whoami` 验证，然后将其存储到 `.env` |
| `hermes secrets onepassword set ENV_VAR "op://…"` | 将环境变量映射到引用（会去除空白并验证后存储） |
| `hermes secrets onepassword remove ENV_VAR` | 删除映射 |
| `hermes secrets onepassword sync` | 试运行：立即解析引用，并显示将应用的内容 |
| `hermes secrets onepassword sync --apply` | 解析并导出到当前 shell 的环境中 |
| `hermes secrets onepassword disable` | 将 `enabled: false` 打开；保留映射 |

`op` 和 `1password` 都可作为 `onepassword` 的别名。

## 配置

`~/.hermes/config.yaml` 中的默认值：

```yaml
secrets:
  onepassword:
    enabled: false
    env:
      OPENAI_API_KEY: "op://Private/OpenAI/api key"
      ANTHROPIC_API_KEY: "op://Private/Anthropic/credential"
    account: ""
    service_account_token_env: OP_SERVICE_ACCOUNT_TOKEN
    binary_path: ""
    cache_ttl_seconds: 300
    override_existing: true
```

| 键 | 默认值 | 功能 |
|---|---|---|
| `enabled` | `false` | 总开关。为 false 时，绝不调用 `op`。 |
| `env` | `{}` | 环境变量名称 → `op://vault/item/field` 引用的映射。名称不是有效环境变量名称，或值不是 `op://` 引用的条目会被跳过并显示警告。 |
| `account` | `""` | 传递给 `op read --account` 的帐户简称 / 登录地址。为空时使用 `op` 的默认帐户。 |
| `service_account_token_env` | `OP_SERVICE_ACCOUNT_TOKEN` | Hermes 从中读取服务帐户令牌的环境变量。其值会以 `OP_SERVICE_ACCOUNT_TOKEN`（`op` 所期望的名称）导出给 `op` 子进程。若要使用桌面/交互式会话，请保持该变量未设置。 |
| `binary_path` | `""` | `op` 的绝对路径。设置后会按原样使用，且**不会**查询 `PATH`——请固定此路径，以避免信任 `PATH` 中最先出现的任意 `op`。 |
| `cache_ttl_seconds` | `300` | 解析后值的复用时长（进程内和磁盘上）。设为 `0` 可禁用**两层**缓存——不会将任何值写入磁盘。 |
| `override_existing` | `true` | 为 true 时，解析后的值会覆盖环境中已有的任何值（使轮换生效）。改为 `false` 可让 `.env` / shell 导出优先；届时会在调用 `op` *之前*跳过这些引用。 |

## 故障模式

1Password 绝不会阻塞 Hermes 启动。任何问题发生时，您都会在 stderr 中看到一条单行警告，Hermes 将继续运行：

| 症状 | 原因 | 修复方式 |
|---|---|---|
| `the op CLI was not found on PATH` | 未安装 `op` / 不在 PATH 中 | 安装 CLI，或设置 `secrets.onepassword.binary_path` |
| `op read failed for 'op://…': …` | 会话被锁定、令牌过期或无保险库访问权限 | 执行 `op signin`，运行 `hermes secrets onepassword token` 轮换服务帐户令牌，或授予服务帐户访问权限 |
| `op read returned an empty value for 'op://…'` | 被引用的字段存在但为空 | 在 1Password 中修复条目/字段（绝不应用空值——现有环境变量保持不变） |
| `… is not an op:// secret reference` | 映射值不是 `op://` 引用 | 使用正确的 `op://vault/item/field` 格式重新设置 |
| `op read timed out` | 网络被阻断或 1Password 响应缓慢 | 检查连接性 / 桌面应用集成 |

启动警告现在会包含一行 `→` 修复提示，准确告诉您哪条命令可以修复故障。

## 缓存

成功且完整的拉取结果会在进程内和 `<hermes_home>/cache/op_cache.json` 磁盘中缓存（以原子方式写入，权限为 `0600`），因此连续的短生命周期 `hermes` 调用无需为每个引用都重新调用 `op`。该缓存：

- 仅存储解析后的密钥**值**——绝不存储服务帐户令牌或任何原始身份验证材料（身份验证会被指纹化到缓存键中）；
- 当令牌、帐户、`OP_SESSION_*` 变量或引用集合变更时失效；
- 当一次拉取出现任何按引用的错误时**不会**写入，因此不会在 TTL 内固化瞬时身份验证失败；
- 当 `cache_ttl_seconds: 0` 时会被完全禁用——包括读取和写入。

## 安全说明

- 1Password 服务帐户令牌可以读取该帐户有权访问的每个密钥。请将其存储在 `~/.hermes/.env` 中（而不是 `config.yaml`），如发生泄露，请在 1Password 中撤销并重新生成。
- 即使 `override_existing: true`，Hermes 也拒绝让解析后的值覆盖令牌环境变量本身。
- `op` 子进程获得的是最小化的允许列表环境（身份验证/会话变量加 `PATH`/`HOME`），而不是完整 `os.environ` 的副本，因此不会将 dotenv 加载后的提供商凭据全部继承给子进程。
- 会验证引用以 `op://` 开头，并在 `--` 选项终止符后传递引用，因此构造的值无法被解析为 `op` 标志。

## 不应使用此功能的情形

- **单机个人设置**，其中 `~/.hermes/.env` 已足够。
- 无法访问 1Password 的**隔离网络环境**。
- 已部署现有密钥注入机制的 **CI/CD**——请选择一种路径，而不是两种。

此功能适用于多机器集群、共享开发机、网关 VPS，或任何希望在多个 Hermes 安装之间集中轮换和撤销凭据的场景。
