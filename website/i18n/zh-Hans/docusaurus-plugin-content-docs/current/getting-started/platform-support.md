---
sidebar_position: 2.5
title: "平台支持"
description: "Hermes Agent 支持哪些操作系统、分发方式与功能。"
---

# 平台支持

Hermes Agent 持续维护对许多平台和分发方式的支持，但我们无法支持所有可能的安装方式。

---

## 一级支持

我们力求绝不破坏这些平台的安装和更新。一级平台的问题和回归是我们的第一优先事项，优先于其他平台。

| 操作系统 / 架构 | 安装方式 | 说明 |
| --- | --- | --- |
| **macOS**（Apple Silicon） | [Hermes Desktop](https://hermes-agent.nousresearch.com/)、[`install.sh`](./installation.md#linux--macos--wsl2--android-termux) | |
| [**Windows 10 / 11**](../user-guide/windows-native.md)（x86_64、aarch64） | [Hermes Desktop](https://hermes-agent.nousresearch.com/)、[`install.ps1`](./installation.md#windows-native) | 少数功能[不可用](../user-guide/windows-native.md#feature-matrix)。 |
| **Linux / [WSL2](../user-guide/windows-wsl-quickstart.md)**（x86_64、aarch64） | [`install.sh`](./installation.md#linux--macos--wsl2--android-termux) | 我们测试最新的 Ubuntu 和 WSL2。若你的发行版具备 glibc、systemd 并遵循 Filesystem Hierarchy Standard，通常可以很好地运行。 |
| [**Docker 容器**](../user-guide/docker.md#quick-start)（x86_64、aarch64） | [`docker pull`](../user-guide/docker.md#quick-start) | Docker 安装不支持 `hermes update`；请通过运行新镜像更新。 |

---

## 二级支持

这些平台仅在仓库中尽力维护。
发布版本可能导致它们失效，我们无法承诺在发生问题时及时修复。

我们会接受用于修复这些平台问题的 PR，但优先级低于一级平台的问题。

| 操作系统 / 架构 | 安装方式 | 说明 |
| --- | --- | --- |
| **Android（Termux）**（aarch64） | [`install.sh`](./installation.md#linux--macos--wsl2--android-termux) | 少数功能[不可用](./termux.md#known-limitations-on-phones)。 |
| **Nix**（MacOS、Linux、NixOS） | [`install.sh`](./nix-setup.md) | 经常因 node.js 打包问题而出故障。祝你好运~！&lt;3 |

## 不支持

以下平台和分发方式**不受支持**。
建议迁移到受支持的分发方式或平台。
它们现在可能已经无法使用，未来也可能进一步失效。
用于修复它们的 PR 将不会被接受，任何保持其兼容性的代码都可能随时被移除。

- 通过 AUR 安装（如果有帮助，我们可能会向上游提交补丁 &lt;3）
- 使用 x86（Intel）处理器的 macOS
- 通过 `pypi` 安装（如 `uv tool install hermes-agent`、`pip install hermes-agent` 等）
- 通过 `brew` 安装（`brew install hermes-agent`）

如果你正在使用不受支持的分发方式，请阅读[安装指南](./installation.md)，了解如何切换到受支持的方式。
