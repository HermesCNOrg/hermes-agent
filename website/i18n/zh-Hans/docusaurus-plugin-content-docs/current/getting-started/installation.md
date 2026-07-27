---
sidebar_position: 2
title: "安装"
description: "在 Linux、macOS、WSL2、原生 Windows 或通过 Termux 在 Android 上安装 Hermes Agent"
---

# 安装

不到两分钟即可安装并运行 Hermes Agent！

:::tip 平台支持
如需查看完整的平台支持矩阵（包括支持的操作系统、分发方式和受平台限制的功能），请参阅**[平台支持](./platform-support.md)**。
:::

## 快速安装
### 在 macOS 或 Windows 上使用 Hermes Desktop 安装程序（推荐）
如需轻松安装命令行和桌面应用，请从我们的网站[下载 Hermes Desktop 安装程序](https://hermes-agent.nousresearch.com/)并运行。

### 不使用 Hermes Desktop：
如需在不安装 Hermes Desktop 的情况下仅安装命令行版本，请运行：

#### Linux / macOS / WSL2 / Android (Termux)
```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

#### Windows（原生）

在 PowerShell 中运行：
```powershell
iex (irm https://hermes-agent.nousresearch.com/install.ps1)
```

如果仅安装命令行版本后还想安装并运行 Hermes Desktop，只需运行：
```bash
hermes desktop
```

### 安装程序会做什么

安装程序会自动处理一切——安装所有依赖（Python、Node.js、ripgrep、ffmpeg）、克隆仓库、创建虚拟环境、配置全局 `hermes` 命令以及配置 LLM 提供商。完成后即可开始聊天。

#### 安装目录结构

安装程序将文件放在哪里，取决于你是以普通用户还是 root 身份安装：

| 安装方式                               | 代码位置                       | `hermes` 二进制                         | 数据目录                              |
| -------------------------------------- | ------------------------------ | --------------------------------------- | ------------------------------------- |
| 用户级（git 安装程序）                 | `~/.hermes/hermes-agent/`      | `~/.local/bin/hermes`（符号链接）       | `~/.hermes/`                          |
| Root 模式（`sudo curl … \| sudo bash`） | `/usr/local/lib/hermes-agent/` | `/usr/local/bin/hermes`                 | `/root/.hermes/`（或 `$HERMES_HOME`） |

Root 模式的 **FHS 布局**（`/usr/local/lib/…`、`/usr/local/bin/hermes`）与 Linux 上其他系统级开发工具的安装位置一致。它适用于共享机器部署：只需安装一份系统级程序，即可供所有用户使用。每位用户的个人配置（身份验证、skills、会话）仍存放在各自的 `~/.hermes/` 中，或由 `HERMES_HOME` 显式指定。

### 安装后

重新加载 shell，然后开始聊天：

```bash
source ~/.bashrc   # or: source ~/.zshrc
hermes             # Start chatting!
```

如需稍后重新配置某项设置，请使用对应的专用命令：

```bash
hermes model          # Choose your LLM provider and model
hermes tools          # Configure which tools are enabled
hermes gateway setup  # Set up messaging platforms
hermes config set     # Set individual config values
hermes config get     # Inspect individual config values
hermes setup          # Or run the full setup wizard to configure everything at once
```

:::tip 最快路径：Nous Portal
一项订阅即可使用 300 多个模型以及 [Tool Gateway](/user-guide/features/tool-gateway)（网络搜索、图像生成、TTS、云浏览器），无需再逐个配置工具密钥：

```bash
hermes setup --portal
```

这条命令会一次性完成登录、将 Nous 设为提供商并开启 Tool Gateway。
:::

---

## 前置条件

**安装程序：** 在非 Windows 平台上，唯一的前置条件是 **Git**。在 Linux 上，还要确保 `curl` 和 `xz-utils` 可用（安装程序会下载 `.tar.xz` 格式的 Node.js 压缩包）。桌面应用还需要 `g++`（Debian/Ubuntu 上为 `build-essential`），用于编译原生模块。其余一切均由安装程序自动处理：

- **uv**（快速 Python 包管理器）
- **Python 3.11**（通过 uv 安装，无需 sudo）
- **Node.js v22**（用于浏览器自动化和 WhatsApp 桥接）
- **ripgrep**（快速文件搜索）
- **ffmpeg**（用于 TTS 的音频格式转换）

:::info
你**无需**手动安装 Python、Node.js、ripgrep 或 ffmpeg。安装程序会检测缺失的组件并自动安装。只需确保 `git` 可用（`git --version`）。在 Linux 上，请确保已安装 `curl` 和 `xz-utils`（Debian/Ubuntu 可运行 `sudo apt install curl xz-utils`）。如需使用桌面应用，还要安装 `build-essential`（`sudo apt install build-essential`）。
:::

:::tip Nix 用户
Nix **不再是官方明确支持的安装方式**（仅提供尽力而为的支持）。如果你已经在使用 Nix（无论是在 NixOS、macOS 还是 Linux 上），可以通过专用流程进行配置，其中包含 Nix flake、声明式 NixOS 模块和可选的容器模式。请参阅 **[Nix 与 NixOS 配置](./nix-setup.md)**指南。
:::

---

## 手动安装 / 开发者安装

如果你希望克隆仓库并从源代码安装——例如参与贡献、从特定分支运行，或完全控制虚拟环境——请参阅贡献指南中的[开发环境配置](../developer-guide/contributing.md#development-setup)章节。

---

## 无 Sudo 权限 / 系统服务用户安装

Hermes 支持以专用非特权用户身份运行（例如作为 `hermes` systemd 服务账户，或任何没有 `sudo` 权限的用户）。安装流程中真正需要 root 权限的只有 Playwright 的 `--with-deps` 步骤，它会通过 `apt` 安装 Chromium 使用的共享库（`libnss3`、`libxkbcommon` 等）。安装程序会检测 sudo 是否可用；如果不可用，则会平稳降级——它会将 Chromium 二进制文件安装到服务用户自己的 Playwright 缓存中，并输出需要由管理员单独运行的准确命令。

**推荐的分步方式（Debian/Ubuntu）：**

1. **由具有 sudo 权限的管理员用户执行一次**，安装 Chromium 所需的系统库：
   ```bash
   sudo npx playwright install-deps chromium
   ```
   （可在任意目录运行——`npx` 会即时获取 Playwright。）

2. **以非特权服务用户身份**运行常规安装程序。安装程序会检测到 sudo 不可用，跳过 `--with-deps`，并将 Chromium 安装到该用户的本地 Playwright 缓存中：
   ```bash
   curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
   ```

   如果想完全跳过 Playwright 步骤——例如你在无图形界面的环境中运行，且不需要浏览器自动化——请传入 `--skip-browser`：
   ```bash
   curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash -s -- --skip-browser
   ```

3. **让服务用户的 shell 能够使用 `hermes`。** 安装程序会将启动器写入 `~/.local/bin/hermes`。系统服务账户的 PATH 通常较为精简，不包含 `~/.local/bin`。你可以将它添加到用户环境中，也可以将启动器符号链接到系统目录：
   ```bash
   # Option A — add to the service user's profile
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

   # Option B — symlink system-wide (run as an admin)
   sudo ln -s /home/hermes/.hermes/hermes-agent/venv/bin/hermes /usr/local/bin/hermes
   ```

4. **验证：** 此时 `hermes doctor` 应能正常运行。如果出现 `ModuleNotFoundError: No module named 'dotenv'`，说明你正在使用系统 Python 调用仓库源代码中的 `hermes` 文件（`~/.hermes/hermes-agent/hermes`），而不是 venv 启动器（`~/.hermes/hermes-agent/venv/bin/hermes`）——请修正第 3 步。

同样的方式也适用于 Arch（安装程序使用 pacman，并采用相同的 sudo 检测逻辑）、Fedora/RHEL 和 openSUSE——这些发行版完全不支持 `--with-deps`，因此始终需要由管理员单独安装系统库。安装程序会输出相应的 `dnf`/`zypper` 命令。

---

## 故障排查

| 问题 | 解决方案 |
|---------|----------|
| `hermes: command not found` | 重新加载 shell（`source ~/.bashrc`）或检查 PATH |
| `API key not set` | 运行 `hermes model` 配置提供商，或运行 `hermes config set OPENROUTER_API_KEY your_key` |
| 更新后配置缺失 | 先运行 `hermes config check`，再运行 `hermes config migrate` |

如需更多诊断信息，请运行 `hermes doctor`——它会准确说明缺少什么以及如何修复。

## 安装方式自动检测

Hermes 会自动检测它是通过 `pip`、git 安装程序、Homebrew 还是 NixOS 安装的，`hermes update` 会针对该安装方式输出对应的更新命令。无需设置环境变量——检测依据是安装目录结构（Python site-packages、`~/.hermes/hermes-agent/`、Homebrew 前缀或 Nix store 路径）。`hermes doctor` 也会在环境摘要中显示检测到的安装方式。
