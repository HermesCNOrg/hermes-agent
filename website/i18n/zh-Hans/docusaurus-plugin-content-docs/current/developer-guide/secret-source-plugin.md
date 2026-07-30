---
sidebar_position: 9
title: "密钥来源插件"
description: "如何为 Hermes Agent 构建密钥管理器后端插件"
---

# 构建密钥来源插件

密钥来源会在进程启动时将提供商凭据从外部密钥管理器（保险库、密码管理器、操作系统密钥库、自定义脚本）解析到环境变量中——在加载 `~/.hermes/.env` 之后、Hermes 读取凭据之前。Bitwarden 和 1Password 随项目内置；**其他所有后端都是插件**。本指南介绍如何构建一个。

:::tip
内置集合是有意封闭的，与[记忆提供商](/developer-guide/memory-provider-plugin)采用相同政策：向 `agent/secret_sources/` 添加新保险库后端的 PR 会被关闭，并附上本指南的链接。请将你的后端作为独立插件仓库发布，并在 Nous Research Discord 的 `#plugins-skills-and-skins` 中分享。
:::

## 框架负责什么，你负责什么

编排器（`agent.secret_sources.registry.apply_all`）负责所有安全和优先级敏感的事项，因此后端无法将其处理错误：

| 框架负责 | 你负责 |
|---|---|
| 来源排序、映射与批量的优先级 | 从你的后端获取值 |
| 先声明者胜出的冲突处理及警告 | 验证你的引用格式 |
| `override_existing` 语义（绝不跨来源） | 与你的 CLI/SDK/API 通信 |
| 受保护的引导令牌 | 声明哪个环境变量是你的引导令牌 |
| 每个来源的墙钟超时 | 保持 `fetch()` 速度合理 |
| 每个变量的来源追踪及 `(from X)` 标签 | 人类可读的 `label` |
| `os.environ` 写入 | 无——你绝不能直接操作环境 |

## 目录结构

```
~/.hermes/plugins/my-vault/
├── plugin.yaml      # 名称、描述
└── __init__.py      # SecretSource 子类 + register(ctx)
```

## SecretSource ABC

实现 `agent.secret_sources.base.SecretSource`。必须实现一个方法：

```python
from pathlib import Path

from agent.secret_sources.base import (
    ErrorKind,
    FetchResult,
    SecretSource,
    run_secret_cli,
)


class MyVaultSource(SecretSource):
    name = "myvault"          # 配置段键：secrets.myvault
    label = "My Vault"        # 用于启动行和来源追踪标签
    shape = "mapped"          # "mapped"（显式 VAR→ref 映射）或 "bulk"（项目转储）
    scheme = "mv"             # 可选：你拥有的唯一 URI 方案（mv://...）

    def fetch(self, cfg: dict, home_path: Path) -> FetchResult:
        """解析密钥。绝不能抛出异常。绝不能提示。"""
        result = FetchResult()
        token = os.environ.get("MYVAULT_TOKEN", "").strip()
        if not token:
            result.error = "secrets.myvault.enabled is true but MYVAULT_TOKEN is not set."
            result.error_kind = ErrorKind.NOT_CONFIGURED
            return result

        try:
            proc = run_secret_cli(
                ["myvault-cli", "export", "--json"],
                allow_env=["MYVAULT_TOKEN"],   # 仅限你的认证变量——绝不能传入完整 os.environ
                timeout=30,
            )
        except RuntimeError as exc:           # 启动失败 / 超时
            result.error = str(exc)
            result.error_kind = ErrorKind.BINARY_MISSING
            return result

        if proc.returncode != 0:
            result.error = f"myvault-cli exited {proc.returncode}: {proc.stderr[:200]}"
            result.error_kind = ErrorKind.AUTH_FAILED
            return result

        result.secrets = parse_your_output(proc.stdout)  # {ENV_VAR: value}
        return result

    def protected_env_vars(self, cfg: dict):
        # 你的引导令牌——任何来源（包括你自己的）都绝不能覆盖它。
        return frozenset({"MYVAULT_TOKEN"})
```

### 合约规则（强制执行，不是建议）

- **`fetch()` 绝不抛出异常。** 错误写入 `result.error` 和 `result.error_kind`。抛出异常的 fetch 会被编排器收容并报告为 `INTERNAL`——这属于合约违规，而非功能特性。
- **`fetch()` 绝不提示。** 启动会在非 TTY 上下文中运行（网关、cron、Docker）。`run_secret_cli()` 会关闭 stdin，使需要提示的辅助程序快速失败。交互式认证应属于你的 CLI 设置流程，绝不能位于启动路径中。
- **同步，且在预算内。** 编排器强制执行墙钟超时（默认 120 秒，用户可通过 `secrets.<name>.timeout_seconds` 调整）。超出时会报告 `TIMEOUT`，并丢弃你的结果。
- **你获取；编排器应用。** 返回你*将会*贡献的映射。绝不能自行写入 `os.environ`——否则会绕过优先级、冲突检测和来源追踪。
- **API 版本控制。** `SecretSource.api_version` 默认采用当前的 `SECRET_SOURCE_API_VERSION`。注册表会跳过（并发出警告）使用不同版本构建的来源，而不会让启动崩溃。

### 选择你的 `shape`

- `mapped` ——用户在配置中将环境变量名显式绑定到引用（如 1Password 的 `env:` 映射）。意图最明确：映射声明在争议变量上优先于批量声明。
- `bulk` ——你隐式注入整个项目/文件夹的密钥（如 Bitwarden BSM）。让位于映射来源。

### 可选钩子

| 方法 | 默认值 | 覆盖时机 |
|---|---|---|
| `is_enabled(cfg)` | `cfg.get("enabled")` | 自定义激活逻辑 |
| `override_existing(cfg)` | `cfg.get("override_existing", False)` | 你想要不同的默认值（两个内置来源均默认为 `True`，以支持轮换） |
| `protected_env_vars(cfg)` | 空 | 你有引导令牌（你几乎肯定有） |
| `fetch_timeout_seconds(cfg)` | 120 秒 | 你的后端需要不同的预算 |
| `config_schema()` | `{}` | 为设置界面声明配置键 |
| `remediation(kind, cfg)` | 每个 `ErrorKind` 的通用提示 | 你希望失败警告指向你自己的修复命令（例如，内置来源在 `AUTH_FAILED` 时返回 `Run hermes secrets <name> token…`）。必须是从 kind 到字符串的纯映射：无 I/O，绝不抛出异常。返回 `""` 以抑制提示。 |

## 子进程安全：使用 `run_secret_cli()`

如果你的后端调用 CLI，请使用共享辅助函数，而不要直接使用 `subprocess.run`。它免费提供经过审计的安全态势：仅 argv（无 `shell=True`）、**最小化的允许列表子进程环境**（来源运行时，`os.environ` 已包含 Hermes 已知的所有凭据——绝不能将其交给子进程）、`NO_COLOR` 和已清除 ANSI 的 stderr、关闭 stdin、超时后产生干净的 `RuntimeError`。将用户提供的引用字符串放在 argv 中 `--` 终止符之后，使它们绝不能被解析为标志。

## 注册

```python
# __init__.py
def register(ctx):
    ctx.register_secret_source(MyVaultSource())
```

以下情况的注册会被拒绝（记录日志警告，绝不会崩溃）：非 `SecretSource` 实例、无效或重复的名称、其他来源拥有的 `scheme`、错误的 `api_version`，或不属于 `mapped`/`bulk` 的 `shape`。

:::note 时机
插件发现运行在启动期间第一次 `load_hermes_dotenv()` 调用之后，因此插件来源不会在发现它的进程第一次加载环境变量时被查询。它会在此后启动的每个 Hermes 进程（网关子进程、cron 会话、子代理）中被查询。内置来源覆盖首次进程的引导。
:::

## 用户像配置其他来源一样配置它

```yaml
secrets:
  sources: [myvault, bitwarden]   # 可选排序
  myvault:
    enabled: true
    # ... 你的 config_schema 键
```

多来源优先级、冲突警告和 `(from My Vault)` 来源追踪标签都会自动生效——请参阅[面向用户的密钥文档](/user-guide/secrets/)以了解优先级阶梯。

## 使用一致性工具包验证

在你的插件测试中，从 Hermes 仓库的工具包（`tests/secret_sources/conformance.py`）继承：

```python
import pytest
from tests.secret_sources.conformance import SecretSourceConformance

class TestMyVaultConformance(SecretSourceConformance):
    @pytest.fixture
    def source(self):
        return MyVaultSource()
```

它会检查其他人在违反时容易出问题的规则：对格式错误的配置绝不抛出异常、机器可读的错误种类、默认禁用、正数超时、有效的受保护变量名，以及完整的 `apply_all()` 往返。通过一致性测试是称后端符合合约的审查门槛。

## ErrorKind 参考

| 种类 | 含义 |
|---|---|
| `NOT_CONFIGURED` | 已启用但缺少令牌 / 项目 / 映射 |
| `BINARY_MISSING` | 辅助 CLI 未找到或不可执行 |
| `AUTH_FAILED` / `AUTH_EXPIRED` | 凭据无效 / 已过期 |
| `REF_INVALID` | 密钥引用未通过验证 |
| `NETWORK` | 传输层失败 |
| `EMPTY_VALUE` | 后端未返回某个引用的任何内容——绝不能用 `""` 覆盖有效凭据 |
| `TIMEOUT` | 获取超出其预算 |
| `INTERNAL` | 其他任何情况（bug、意外的形状） |
