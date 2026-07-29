# 密钥

Hermes 可以在进程启动时从外部密钥管理器拉取 API 密钥，而不是将其存储在 `~/.hermes/.env` 中。密钥管理器的引导令牌存放在 `.env` 中；其他所有提供商密钥（OpenAI、Anthropic、OpenRouter 等）都可以保留在管理器中并集中轮换。

支持：

- [Bitwarden Secrets Manager](./bitwarden) — 使用 `bws` CLI，按需安装，免费套餐可用。
- [1Password](./onepassword) — 通过官方 `op` CLI 使用 `op://` 引用；支持服务账户或桌面会话认证。
- [命令助手](./command) — 通过用户配置的助手（输出 `KEY=VALUE` 行）使用任何 CLI 密码库（`keepassxc-cli`、`secret-tool`、`pass`、自定义脚本）。

## 同时使用多个来源

你可以同时启用多个密钥来源——例如团队 Bitwarden 项目与个人密码库插件并用。各来源会按确定性的优先级规则为每个环境变量组合：

1. **默认情况下，你的 `.env` / shell 优先。** 只有在来源自身设置 `override_existing: true` 时，来源才会替换已有值（Bitwarden 默认设为 true，因此可进行集中轮换）。
2. **映射来源优先于批量来源。** 无论顺序如何，显式将环境变量绑定到引用的来源（`env:` 映射）优先于隐式注入整个密钥项目的来源。
3. **第一个来源优先。** 在相同形态内，可选的 `secrets.sources` 列表（或注册顺序）决定优先级。后续来源若声明了已经被声明的变量会被跳过——启动时会发出警告，绝不会静默处理。

`override_existing` 绝不会允许一个来源覆盖另一个来源已声明的变量，且没有任何来源可以覆盖另一个来源的引导令牌（例如 `BWS_ACCESS_TOKEN`）。

```yaml
secrets:
  sources: [bitwarden]     # 可选的显式排序
  bitwarden:
    enabled: true
    project_id: "..."
```

来源注入的每个凭据都会标注其来源——设置流程和 `hermes model` 会在检测到的密钥旁显示 `(from Bitwarden)`，因此你始终知道某个值来自何处。

## 配置文件与共享密码库

两个编排器级别的选项可让一个共享密码库安全地跨[配置文件](../features/profiles)使用：

- **`secrets.preserve_existing`** — 一个环境变量名称列表；即使来源设置了 `override_existing: true`，这些变量已有的 `.env` / shell 值也始终优先。用于刻意在各配置文件间不同的每配置文件平台密钥（例如 `FEISHU_APP_SECRET`），而其他所有内容都集中轮换：

  ```yaml
  secrets:
    preserve_existing: [FEISHU_APP_SECRET, TELEGRAM_BOT_TOKEN]
  ```

- **配置文件别名**（默认启用，设置 `secrets.profile_alias: false` 可禁用）— 当 Hermes 在具名配置文件下运行时，密码库中名为 `FOO_<PROFILE>` 的密钥（仅限凭据形态的后缀：`*_API_KEY`、`*_TOKEN`、`*_SECRET`、`*_KEY`、`*_PASSWORD`）也会填充规范名称 `FOO`。将 `TELEGRAM_BOT_TOKEN_MILLA` 存储在共享项目中，`milla` 配置文件的适配器——其读取固定名称 `TELEGRAM_BOT_TOKEN`——便会自动获得正确的值。密码库直接以规范名称提供的变量始终优先于别名。

两者均适用于每个来源——内置和插件来源——因为它们位于编排器中，而非后端中。

## 添加你自己的后端

第三方密钥管理器以独立插件形式发布，而不是作为核心 PR。后端继承 `agent.secret_sources.base.SecretSource`（一个必需方法：`fetch(cfg, home_path) -> FetchResult`），并在插件的 `register(ctx)` 中通过 `ctx.register_secret_source(MySource())` 注册。编排器负责优先级、冲突处理、超时和来源追踪——你的来源只负责获取。包含合约规则、子进程安全助手和一致性工具包的完整指南：[构建密钥来源插件](/developer-guide/secret-source-plugin)。

内置集合经过刻意限制（与内存提供商采用相同政策）：Bitwarden 和 1Password 在树内发布。其他所有方案——Infisical、Proton Pass、HashiCorp Vault、AWS Secrets Manager、操作系统密钥库——都应位于插件仓库中；请在 Nous Research Discord（`#plugins-skills-and-skins`）分享它们。