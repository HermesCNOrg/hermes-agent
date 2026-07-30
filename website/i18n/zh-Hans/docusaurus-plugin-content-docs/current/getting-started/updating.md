---
sidebar_position: 3
title: "更新与卸载"
description: "如何将 Hermes Agent 更新至最新版本或将其卸载"
---

# 更新与卸载

## 更新

使用单条命令更新至最新版本：

```bash
hermes update
```

此命令会从 `main` 拉取最新代码、更新依赖项，并提示你配置自上次更新以来新增的任何选项。

:::tip
`hermes update` 会自动检测新的配置选项并提示你添加。如果跳过了该提示，可手动运行 `hermes config check` 查看缺失的选项，再运行 `hermes config migrate` 以交互方式添加它们。
:::

### 更新过程中会发生什么

运行 `hermes update` 时，会执行以下步骤：

1. **更新前快照** — 默认保存一份轻量级状态快照（涵盖配对数据、cron 任务、`config.yaml`、`.env`、`auth.json` 及其他在运行时修改的状态文件；单个超过 1 GiB 的文件会被跳过，因此大型会话数据库不会拖慢更新）。由 `updates.pre_update_backup` 控制（默认 `quick`，`full` 会为整个 `HERMES_HOME` 创建 zip，`off` 则禁用）。可通过[快照与回滚](../user-guide/checkpoints-and-rollback.md)中所述的快照恢复流程进行恢复。
2. **Git pull** — 从 `main` 分支拉取最新代码并更新子模块
3. **拉取后的语法验证和自动回滚** — 拉取后，Hermes 会编译每次调用 `hermes` 时在启动阶段都会导入的九个关键文件。若任何文件无法解析（例如，存在孤立的合并冲突标记或文件被意外截断），Hermes 会运行 `git reset --hard <pre-pull-sha>` 回滚安装，以便 shell 仍可启动。在上游修复落地后重新运行 `hermes update`。
4. **依赖安装** — 运行 `uv pip install -e ".[all]"` 以获取新增或变更的依赖项
5. **配置迁移** — 检测自你当前版本以来新增的配置选项，并提示你设置
6. **Gateway 自动重启** — 更新完成后刷新正在运行的 gateway，使新代码立即生效。由服务管理的 gateway（Linux 上的 systemd、macOS 上的 launchd）通过服务管理器重启。Hermes 能将运行中的 PID 映射回某个 profile 时，会自动重新启动手动运行的 gateway。

### 针对非默认分支更新：`--branch`

默认情况下，`hermes update` 跟踪 `origin/main`。传入 `--branch <name>` 可针对其他分支更新，这对于 QA 通道、功能分支或候选发布版本测试很有用：

```bash
hermes update --branch release-candidate
hermes update --check --branch experimental   # 仅预览落后情况
```

如果本地检出位于不同分支，Hermes 会自动暂存所有未提交的工作，将 HEAD 切换至目标分支，然后拉取。不存在于本地的分支会自动跟踪 `origin/<name>`（`git checkout -B <name> origin/<name>`）。任何地方都不存在的分支会正常失败——退出前会恢复你暂存的更改，因此你绝不会处于异常状态。仅限 `main` 的 fork 上游同步逻辑会在非 `main` 分支上自动跳过。

### 非交互式更新中的本地更改

当你在终端中运行 `hermes update` 时，Hermes 会暂存所有未提交的源代码树更改、拉取，然后**询问**是否恢复它们——与一贯行为完全相同。交互式更新没有变化。

当更新在**没有终端**的情况下运行时——通过桌面/聊天应用的“更新”按钮或 gateway 触发的更新——没有可回答的提示。`updates.non_interactive_local_changes` 设置决定如何处理暂存的更改：

```yaml
# ~/.hermes/config.yaml
updates:
  non_interactive_local_changes: stash   # 默认值：保留并自动恢复
  # non_interactive_local_changes: discard  # 丢弃本地源代码编辑
```

- `stash`（默认）— 自动暂存、拉取，然后在更新后的代码之上自动恢复你的更改。不会丢失任何内容；如果恢复时发生冲突，会将它们保留在 git stash 中，以供手动恢复。
- `discard` — 自动暂存，并在拉取后丢弃该 stash，使更新始终落在干净工作树上。仅在你从不打算保留 Hermes 源代码本地编辑的机器上使用。它执行 stash-drop（而不是 `git reset --hard` + `git clean -fd`），因此绝不会触及 `node_modules`、`venv` 和构建输出等被忽略的路径。

在桌面应用中，此设置位于**设置 → 高级 → 应用内更新本地更改**。

### 仅预览：`hermes update --check`

想在拉取前确认是否有更新？运行 `hermes update --check`——它会获取并与 `origin/main` 比较提交。不修改任何文件，也不会重启 gateway。适合在以“是否有更新”为条件的脚本和 cron 任务中使用。

### 完整更新前备份：`--backup`

对于高价值 profile（生产环境 gateway、团队共享安装），可选择在拉取前对 `HERMES_HOME`（配置、认证、会话、技能、配对数据）进行完整备份：

```bash
hermes update --backup
```

或将其设为每次运行的默认行为：

```yaml
# ~/.hermes/config.yaml
updates:
  pre_update_backup: full
```

`updates.pre_update_backup` 是单一开关，有三种模式：`quick`（默认——上述轻量级状态快照）、`full`（快速快照加上完整的 `HERMES_HOME` zip；在大型 home 目录上可能增加数分钟）和 `off`（完全不做更新前备份——`--no-backup` 对单次运行的作用相同）。旧版布尔值仍然有效：`true` 表示 `full`，`false` 表示 `off`。

### Windows：另一个 `hermes.exe` 正在运行

在 Windows 上，如果 `hermes update` 检测到另一个 `hermes.exe` 进程正持有 venv 的入口点可执行文件，它将拒绝运行——最常见的是 Hermes Desktop 应用启动的后端、另一个终端中打开的 `hermes` REPL，或正在运行的 gateway：

```
$ hermes update
✗ Another hermes.exe is running:
    PID 12345  hermes.exe

  Updating now would fail to overwrite ...\venv\Scripts\hermes.exe because
  Windows blocks REPLACE on a running executable.

  Close Hermes Desktop, exit any open `hermes` REPLs, and
  stop the gateway (`hermes gateway stop`) before retrying.
  Override with `hermes update --force` if you've already
  confirmed those processes will not write to the venv.
```

关闭列出的进程后重新运行。如果确定并发进程不会造成干扰（很少见——通常仅在将防病毒软件 shim 错误归因时有用），可传入 `--force` 跳过检查。在这种情况下，更新程序仍会以指数退避重试 `.exe` 重命名操作；对于顽固的锁定，它会通过 `MoveFileEx(MOVEFILE_DELAY_UNTIL_REBOOT)` 将替换安排在下次重启时执行，以便更新能够完成。

第二道独立保护会在任何进程正通过其 Python 解释器运行时拒绝触及 venv（桌面应用的后端、gateway 或 Python REPL）。这些进程会锁定原生扩展文件（`.pyd`），而在访问被拒错误后中途终止的依赖同步会使安装卡在两个版本之间。此保护**不能**由 `--force` 绕过；若确定检测到的占用者为误报，请使用明确的 `hermes update --force-venv`。

预期输出如下：

```
$ hermes update
Updating Hermes Agent...
📥 Pulling latest code...
Already up to date.  (or: Updating abc1234..def5678)
📦 Updating dependencies...
✅ Dependencies updated
🔍 Checking for new config options...
✅ Config is up to date  (or: Found 2 new options — running migration...)
🔄 Restarting gateways...
✅ Gateway restarted
✅ Hermes Agent updated successfully!
```

### 建议的更新后验证

`hermes update` 处理主要更新路径，但快速验证可确认一切都已正确落地：

1. `git status --short` — 如果工作树意外变脏，请在继续前检查
2. `hermes doctor` — 检查配置、依赖项和服务健康状态
3. `hermes --version` — 确认版本已按预期更新
4. 如果使用 gateway：`hermes gateway status`
5. 如果 `doctor` 报告 npm audit 问题：在标记的目录中运行 `npm audit fix`

:::warning 更新后工作树出现脏状态
如果 `hermes update` 后 `git status --short` 显示意外变更，请在继续前停下来检查。这通常意味着本地修改被重新应用到更新后的代码之上，或依赖步骤刷新了锁文件。
:::

### 如果终端在更新中途断开

`hermes update` 会保护自身免受意外终端丢失的影响：

- 更新会忽略 `SIGHUP`，因此关闭 SSH 会话或终端窗口不再会在安装中途终止它。`pip` 和 `git` 子进程会继承此保护，因此掉线不会让 Python 环境处于半安装状态。
- 更新运行期间，所有输出会镜像到 `~/.hermes/logs/update.log`。如果终端消失，重新连接后检查日志，查看更新是否完成以及 gateway 重启是否成功：

```bash
tail -f ~/.hermes/logs/update.log
```

- `Ctrl-C`（SIGINT）和系统关机（SIGTERM）仍会被响应——这些是主动取消，而非意外。

你不再需要将 `hermes update` 包裹在 `screen` 或 `tmux` 中以应对终端断开。

### 检查当前版本

```bash
hermes version
```

与 [GitHub releases 页面](https://github.com/NousResearch/hermes-agent/releases)上的最新发布版本进行比较。

### 从消息平台更新

你也可以直接从 Telegram、Discord、Slack、WhatsApp 或 Teams 发送以下命令进行更新：

```
/update
```

此命令会拉取最新代码、更新依赖项并重启正在运行的 gateway。Bot 在重启期间会短暂下线（通常为 5–15 秒），然后恢复。

### 手动更新

如果你是手动安装的（未使用快速安装程序）：

```bash
cd /path/to/hermes-agent
# Activate the venv you created during install (outside the source tree)
export VIRTUAL_ENV="$HOME/.hermes/venvs/hermes-dev"
export PATH="$VIRTUAL_ENV/bin:$PATH"

# Pull latest code
git pull origin main

# Reinstall (picks up new dependencies)
uv pip install -e ".[all]"

# Check for new config options
hermes config check
hermes config migrate   # Interactively add any missing options
```

### 回滚说明

如果更新引入问题，可回滚到之前的版本：

```bash
cd /path/to/hermes-agent

# List recent versions
git log --oneline -10

# Roll back to a specific commit
git checkout <commit-hash>
uv pip install -e ".[all]"

# Restart the gateway if running
hermes gateway restart
```

要回滚至特定发布标签（请替换为之前的标签——例如 `v2026.5.16` 这样的近期发布版本，或 `git tag --sort=-version:refname` 中的任何早期标签）：

```bash
git checkout vX.Y.Z
uv pip install -e ".[all]"
```

:::warning
如果新增了配置选项，回滚可能导致配置不兼容。回滚后运行 `hermes config check`；若遇到错误，请从 `config.yaml` 中移除所有无法识别的选项。
:::

### Nix 用户注意事项

Nix 不再是明确支持的安装路径（仅尽力支持）——请参阅 [Nix 设置](./nix-setup.md)。如果通过 Nix flake 安装，更新由 Nix 包管理器负责：

```bash
# Update the flake input
nix flake update hermes-agent

# Or rebuild with the latest
nix profile upgrade hermes-agent
```

Nix 安装是不可变的——回滚由 Nix 的 generation 系统处理：

```bash
nix profile rollback
```

详情参见 [Nix 设置](./nix-setup.md)。

---

## 卸载

```bash
hermes uninstall
```

卸载程序会提供选项，让你保留配置文件（`~/.hermes/`）以便将来重新安装。

### 手动卸载

```bash
rm -f ~/.local/bin/hermes
rm -rf /path/to/hermes-agent
rm -rf ~/.hermes            # 可选——如计划重新安装则保留
```

:::info
如果将 gateway 安装为系统服务，请先停止并禁用它：
```bash
hermes gateway stop
# Linux: systemctl --user disable hermes-gateway
# macOS: launchctl remove ai.hermes.gateway
```
:::
