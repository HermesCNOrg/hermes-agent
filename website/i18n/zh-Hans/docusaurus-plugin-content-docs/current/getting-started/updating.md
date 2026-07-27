---
sidebar_position: 3
title: "更新与卸载"
description: "如何将 Hermes Agent 更新至最新版本或将其卸载"
---

# 更新与卸载

## 更新

使用一条命令即可更新至最新版本：

```bash
hermes update
```

此命令会从 `main` 拉取最新代码、更新依赖项，并提示你配置自上次更新以来新增的所有选项。

:::tip
`hermes update` 会自动检测新的配置选项并提示你添加。如果跳过了该提示，可以手动运行 `hermes config check` 查看缺少的选项，再运行 `hermes config migrate` 以交互方式添加。
:::

### 更新期间会发生什么

运行 `hermes update` 时，会依次执行以下步骤：

1. **更新前快照** — 默认保存一份轻量级状态快照（涵盖配对数据、cron 任务、`config.yaml`、`.env`、`auth.json` 以及其他运行时会修改的状态文件；单个超过 1 GiB 的文件会被跳过，因此大型会话数据库不会拖慢更新）。此行为由 `updates.pre_update_backup` 控制（默认为 `quick`；`full` 会为整个 `HERMES_HOME` 创建 zip 备份；`off` 则禁用备份）。你可以按照[快照与回滚](../user-guide/checkpoints-and-rollback.md)中的快照恢复流程进行恢复。
2. **Git pull** — 从 `main` 分支拉取最新代码并更新子模块
3. **拉取后语法验证与自动回滚** — 拉取完成后，Hermes 会编译每次调用 `hermes` 时启动阶段所导入的八个关键文件。如果其中任何文件无法解析（例如残留了孤立的合并冲突标记，或文件被意外截断），Hermes 会运行 `git reset --hard <pre-pull-sha>`，将安装回滚到更新前的状态，确保 shell 中的命令仍可启动。待上游修复发布后，重新运行 `hermes update` 即可。
4. **安装依赖项** — 运行 `uv pip install -e ".[all]"`，安装新增或有变更的依赖项
5. **配置迁移** — 检测当前版本之后新增的配置选项，并提示你进行设置
6. **Gateway 自动重启** — 更新完成后会刷新正在运行的 gateway，使新代码立即生效。由服务管理的 gateway（Linux 上的 systemd、macOS 上的 launchd）会通过服务管理器重启。对于手动启动的 gateway，如果 Hermes 能将运行中的 PID 映射到相应 profile，也会自动重新启动。

### 从非默认分支更新：`--branch`

默认情况下，`hermes update` 跟踪 `origin/main`。传入 `--branch <name>` 可改为从其他分支更新，适用于 QA 渠道、功能分支或候选版本测试：

```bash
hermes update --branch release-candidate
hermes update --check --branch experimental   # preview behindness only
```

如果本地检出的是另一个分支，Hermes 会自动暂存所有未提交的更改，将 HEAD 切换到目标分支，然后执行拉取。本地不存在的分支会自动设置为跟踪 `origin/<name>`（`git checkout -B <name> origin/<name>`）。如果分支在任何位置都不存在，操作会妥善失败；退出前会恢复已暂存的更改，避免让你陷入异常状态。在非 `main` 分支上，只有 `main` 才会执行的 fork 与上游同步逻辑会自动跳过。

### 非交互式更新时的本地更改

在终端中运行 `hermes update` 时，Hermes 会暂存源码树中所有未提交的更改，完成拉取后再**询问**是否恢复这些更改——这与以往的行为完全一致。交互式更新的行为没有变化。

当更新在**没有终端**的情况下运行时——例如通过桌面端或聊天应用中的“Update”按钮，或由 gateway 触发更新——无法通过提示获取你的选择。此时，`updates.non_interactive_local_changes` 设置决定如何处理已暂存的更改：

```yaml
# ~/.hermes/config.yaml
updates:
  non_interactive_local_changes: stash   # default: keep + auto-restore
  # non_interactive_local_changes: discard  # throw local source edits away
```

- `stash`（默认）— 自动暂存、拉取，然后在更新后的代码之上自动恢复你的更改。不会丢失任何内容；如果恢复时发生冲突，这些更改会保留在 git stash 中，供你手动恢复。
- `discard` — 自动暂存，并在拉取后丢弃该 stash，使更新后的工作树始终保持干净。仅应在你完全不打算保留 Hermes 源码本地修改的机器上使用。此模式会丢弃 stash（而不是运行 `git reset --hard` 和 `git clean -fd`），因此不会触碰 `node_modules`、`venv` 和构建产物等被忽略的路径。

在桌面应用中，该设置位于 **Settings → Advanced → In-App Update Local Changes**。

### 仅预览：`hermes update --check`

想在拉取之前了解是否有可用更新？运行 `hermes update --check`——它会获取提交并与 `origin/main` 进行比较。不会修改任何文件，也不会重启 gateway。适合用于以“是否有更新”为判断条件的脚本和 cron 任务。

### 完整更新前备份：`--backup`

对于高价值 profile（生产环境 gateway、团队共享安装），你可以选择在拉取前完整备份 `HERMES_HOME`（配置、认证信息、会话、技能和配对数据）：

```bash
hermes update --backup
```

也可以将其设为每次运行时的默认行为：

```yaml
# ~/.hermes/config.yaml
updates:
  pre_update_backup: full
```

`updates.pre_update_backup` 是一个包含三种模式的设置项：`quick`（默认，即上文所述的轻量级状态快照）、`full`（在快速快照之外，再为整个 `HERMES_HOME` 创建 zip 备份；如果 home 目录很大，可能额外耗时数分钟）和 `off`（完全不做更新前备份；单次运行时使用 `--no-backup` 效果相同）。旧版布尔值仍然有效：`true` 表示 `full`，`false` 表示 `off`。

### Windows：另一个 `hermes.exe` 正在运行

在 Windows 上，如果 `hermes update` 检测到另一个 `hermes.exe` 进程占用了 venv 的入口点可执行文件，它会拒绝运行。最常见的情况包括 Hermes Desktop 应用启动的后端、另一个终端中打开的 `hermes` REPL，或正在运行的 gateway：

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

关闭列出的进程，然后重新运行。如果你确定并发进程不会造成干扰（这种情况很少见，通常只适用于防病毒软件 shim 被错误归因的情况），可以传入 `--force` 跳过检查。即便如此，更新程序仍会以指数退避方式重试重命名 `.exe`；遇到顽固的文件锁时，则通过 `MoveFileEx(MOVEFILE_DELAY_UNTIL_REBOOT)` 将替换安排在下次重启时执行，以便完成更新。

另有一项独立的保护机制：只要任何进程正通过该 venv 的 Python 解释器运行（例如桌面应用的后端、gateway 或 Python REPL），更新程序就会拒绝修改 venv。这些进程会锁定原生扩展文件（`.pyd`）；如果依赖项同步因访问被拒绝而中途失败，安装就会卡在两个版本之间。**不能**使用 `--force` 绕过这项保护；如果你确定检测到的占用进程属于误报，请使用明确的 `hermes update --force-venv`。

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

### 建议的更新后验证步骤

`hermes update` 会处理主要更新流程，但简单验证一下，可以确认所有内容均已正确更新：

1. `git status --short` — 如果工作树出现意外的未提交更改，请先检查再继续
2. `hermes doctor` — 检查配置、依赖项和服务健康状态
3. `hermes --version` — 确认版本已按预期更新
4. 如果你使用 gateway：`hermes gateway status`
5. 如果 `doctor` 报告 npm audit 问题：在标记的目录中运行 `npm audit fix`

:::warning 更新后工作树存在未提交更改
如果运行 `hermes update` 后，`git status --short` 显示意外更改，请先停下来检查，再继续操作。这通常意味着本地修改被重新应用到了更新后的代码之上，或依赖项处理步骤更新了锁文件。
:::

### 如果终端在更新过程中断开连接

`hermes update` 能够防止意外的终端连接中断影响更新：

- 更新过程会忽略 `SIGHUP`，因此关闭 SSH 会话或终端窗口不会再导致安装中途终止。`pip` 和 `git` 子进程也会继承这项保护，所以 Python 环境不会因连接中断而处于安装不完整的状态。
- 更新运行期间，所有输出都会同步写入 `~/.hermes/logs/update.log`。如果终端断开，请重新连接并查看日志，确认更新是否完成以及 gateway 是否重启成功：

```bash
tail -f ~/.hermes/logs/update.log
```

- `Ctrl-C`（SIGINT）和系统关机（SIGTERM）仍会正常生效——这些属于主动取消，而不是意外中断。

现在，即使终端连接中断，也不再需要使用 `screen` 或 `tmux` 包裹 `hermes update`。

### 查看当前版本

```bash
hermes version
```

你可以在 [GitHub releases 页面](https://github.com/NousResearch/hermes-agent/releases)上与最新版本进行比较。

### 从消息平台更新

你也可以在 Telegram、Discord、Slack、WhatsApp 或 Teams 中发送以下命令，直接执行更新：

```
/update
```

此命令会拉取最新代码、更新依赖项并重启正在运行的 gateway。Bot 会在重启期间短暂离线（通常为 5–15 秒），随后恢复运行。

### 手动更新

如果你采用手动安装（而非快速安装程序）：

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

如果更新引发问题，可以回滚到之前的版本：

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

要回滚到特定发布标签（请替换为之前使用的标签，例如 `v2026.5.16` 这样的近期版本，或 `git tag --sort=-version:refname` 列出的任何更早标签）：

```bash
git checkout vX.Y.Z
uv pip install -e ".[all]"
```

:::warning
如果新版本增加了配置选项，回滚可能会导致配置不兼容。回滚后请运行 `hermes config check`；如果遇到错误，请从 `config.yaml` 中删除无法识别的选项。
:::

### Nix 用户注意事项

Nix 不再是明确支持的安装方式（仅提供尽力而为的支持）——参见 [Nix 安装](./nix-setup.md)。如果你通过 Nix flake 安装，更新由 Nix 包管理器管理：

```bash
# Update the flake input
nix flake update hermes-agent

# Or rebuild with the latest
nix profile upgrade hermes-agent
```

Nix 安装不可变——回滚由 Nix 的 generation 系统处理：

```bash
nix profile rollback
```

详情参见 [Nix 安装](./nix-setup.md)。

---

## 卸载

```bash
hermes uninstall
```

卸载程序会提供一个选项，让你保留配置文件（`~/.hermes/`），以便日后重新安装。

### 手动卸载

```bash
rm -f ~/.local/bin/hermes
rm -rf /path/to/hermes-agent
rm -rf ~/.hermes            # Optional — keep if you plan to reinstall
```

:::info
如果你已将 gateway 安装为系统服务，请先停止并禁用该服务：
```bash
hermes gateway stop
# Linux: systemctl --user disable hermes-gateway
# macOS: launchctl remove ai.hermes.gateway
```
:::
