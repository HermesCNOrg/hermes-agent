---
sidebar_position: 2.5
title: "平台支持"
description: "Hermes Agent 支持哪些操作系统、分发方式和功能。"
---

# 平台支持

Hermes Agent 维护对许多平台和分发方式的支持，但我们无法支持所有可能的安装方式。

---

## 第一层级

我们努力确保这些平台的安装和更新永不损坏。第一层级的问题和回归是我们的首要优先事项，优先级高于其他平台。

| 操作系统 / 架构                                                               | 安装方式                                                                                                                       | 说明                                                                                                                                                         |
| ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **macOS**（Apple Silicon）                                                    | [Hermes Desktop](https://hermes-agent.nousresearch.com/)、[`install.sh`](./installation.md#linux--macos--wsl2--android-termux) | |
| [**Windows 10 / 11**](../user-guide/windows-native.md)（x86_64、aarch64）     | [Hermes Desktop](https://hermes-agent.nousresearch.com/)、[`install.ps1`](./installation.md#windows-native)                    | 部分功能[不可用](../user-guide/windows-native.md#feature-matrix)。                                                                                           |
| **Linux / [WSL2](../user-guide/windows-wsl-quickstart.md)**（x86_64、aarch64） | [`install.sh`](./installation.md#linux--macos--wsl2--android-termux)                                                           | 我们在最新版 Ubuntu 和 WSL2 上测试。如果你的发行版具有 glibc、systemd，并遵循文件系统层级标准，那么它很可能运行得相当不错。 |
| [**Docker 容器**](../user-guide/docker.md#quick-start)（x86_64、aarch64）      | [`docker pull`](../user-guide/docker.md#quick-start)                                                                           | Docker 安装不支持 `hermes update`。更新通过运行新镜像完成。                                                                                                  |

---

## 第二层级

这些平台仅以尽力而为的方式在仓库内维护。
发布可能会破坏它们，而当它们损坏时，我们不能承诺会及时修复。

我们会接受修复它们问题的 PR，但其优先级低于修复第一层级平台的问题。

| 操作系统 / 架构                 | 安装方式                                                              | 说明                                                                            |
| ------------------------------ | --------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| **Android（Termux）**（aarch64） | [`install.sh`](./installation.md#linux--macos--wsl2--android-termux) | 部分功能[不可用](./termux.md#known-limitations-on-phones)。                      |
| **Nix**（macOS、Linux、NixOS）   | [`install.sh`](./nix-setup.md)                                       | 因 node.js 打包问题而经常损坏。祝你好运~！&lt;3                                 |

## 不受支持

这些平台和分发方式**不受支持**。
我们建议你迁移到受支持的分发方式或平台。
它们现在可能已损坏，将来可能会进一步损坏。
修复它们的 PR 将**不会**被接受，而任何维持与它们兼容性的代码都可能在任何时候被移除。

- 通过 AUR 安装（如果有帮助，我们可能会上游提交补丁 &lt;3）
- 使用 x86（Intel）处理器的 macOS
- 通过 `pypi` 安装（例如 `uv tool install hermes-agent`、`pip install hermes-agent` 等）
- 通过 `brew` 安装（`brew install hermes-agent`）

如果你正在使用不受支持的分发方式，请阅读[安装指南](./installation.md)，了解如何切换到受支持的方式。
