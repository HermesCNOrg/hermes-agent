# 命令辅助程序密钥来源

通过在启动时运行你自己的辅助命令来解析凭据——任何带有 CLI 的密钥存储都可以：`keepassxc-cli`、`secret-tool`（GNOME 密钥环）、`pass`、`gpg`、Vaultwarden 的 CLI，或读取 tmpfs 环境文件的脚本。该辅助程序会在 stdout 上输出 `KEY=VALUE` 行；Hermes 通过与 [Bitwarden](./bitwarden) 和 [1Password](./onepassword) 相同的编排器应用它们，因此你可以同时启用任意组合的来源。

## 工作原理

1. 你在 `config.yaml` 中配置辅助命令（绝不在 `.env` 中——命令属于配置，`.env` 保存值）。
2. 启动时，在加载 `.env` 后，Hermes 会通过 `/bin/sh -c` 运行一次该辅助程序，并将其 stdout 解析为 dotenv blob。
3. 解析出的键会经过标准优先级阶梯：除非设置 `override_existing: true`，否则 `.env`/shell 胜出；在有争议的变量上，映射来源优先于此批量来源；首次声明者胜出。

```yaml
secrets:
  command:
    enabled: true
    command: "cat /run/user/1000/hermes-secrets.env"
    # 或任何输出 KEY=VALUE 行的密钥库 CLI：
    # command: "pass show hermes/env"
    # command: "secret-tool lookup service hermes-env"
```

## 配置

| 键 | 默认值 | 作用 |
|---|---|---|
| `enabled` | `false` | 总开关。 |
| `command` | `""` | 通过 `/bin/sh -c` 运行的辅助程序；必须在 stdout 上输出 `KEY=VALUE` 行。 |
| `helper_timeout_seconds` | `3` | 单次辅助程序运行的硬超时。刻意设置得很短——辅助程序必须快速且非交互式（不得有解锁提示或触摸/PIN）。 |
| `override_existing` | `false` | 辅助程序值覆盖 `.env`/shell 值。默认关闭（不同于 Bitwarden/1Password），因为本地辅助程序不是中央轮换权威。 |

## 安全模型

- 辅助命令字符串是你的配置——其信任级别与你控制的 `.env` 文件相同。
- 输出被硬性限制为 1 MiB；失控的辅助程序无法卡住启动过程（超时时会终止进程组）。
- 辅助程序的 **stderr 会被丢弃**——密钥库 CLI 的诊断信息可能携带秘密材料，因此它们绝不会到达 Hermes 的输出。失败只记录结构化字段（退出代码 / 信号 / errno），绝不记录命令字符串。
- 仅含空白字符的值被视为“无值”——占位条目绝不会流入 Authorization 标头。
- 仅支持 POSIX（需要 `/bin/sh`）。在 Windows 上，此来源会报告自身未配置，启动会继续。

## 失败模式

启动永远不会被阻塞。错误会输出一行消息和一条 `→` 修复提示：

| 症状 | 原因 | 修复方法 |
|---|---|---|
| `secrets.command.command is empty` | 已启用但未设置命令 | 在 config.yaml 中设置 `secrets.command.command` |
| `helper command failed` | 非零退出、超时或生成失败 | 在 shell 中手动运行辅助程序以查看真实错误（Hermes 会特意丢弃其 stderr） |
| `helper output was not a KEY=VALUE map` | 辅助程序输出了裸值或垃圾内容 | 让辅助程序输出 dotenv 形式的行 |

## 何时使用此功能而不是插件

命令来源是没有捆绑集成的密钥库的逃生出口。如果你发现自己正在用长脚本包装复杂的 CLI 操作，不妨考虑使用正式的[密钥来源插件](/developer-guide/secret-source-plugin)——插件具备缓存、来源标签和类型化配置。
