---
sidebar_position: 9
title: "从其他 Agent 导入"
description: "一条命令即可将 Claude Code（~/.claude）或 OpenAI Codex CLI（~/.codex）设置导入 Hermes，包括指令、允许列表、MCP 服务器、技能和记忆。"
---

# 从其他 Agent 导入

`hermes import-agent` 只需一条命令，即可将你现有的 **Claude Code** 或 **OpenAI Codex CLI** 设置导入 Hermes。它遵循与 [`hermes claw migrate`](../guides/migrate-from-openclaw.md) 相同的先预览模式：在写入任何内容之前，你始终会看到逐项计划；而 `--dry-run` 绝不会触及磁盘。

```bash
hermes import-agent                    # 自动检测 ~/.claude 或 ~/.codex
hermes import-agent claude-code        # 从 ~/.claude 导入
hermes import-agent codex              # 从 ~/.codex 导入
hermes import-agent claude-code --dry-run          # 仅预览
hermes import-agent codex --source /path/to/.codex # 自定义位置
hermes import-agent claude-code --overwrite --yes  # 替换冲突项，跳过提示
```

## 将导入什么

### Claude Code (`~/.claude`)

| Claude Code | Hermes |
|---|---|
| `CLAUDE.md`（全局指令） | `~/.hermes/memories/MEMORY.md` 中的记忆条目 |
| `settings.json` → `permissions.allow`（`Bash(...)` 规则） | `config.yaml` 中的 `command_allowlist` |
| `settings.json` → `permissions.deny`（`Bash(...)` 规则） | `config.yaml` 中的 `approvals.deny` |
| `mcpServers`（来自 `~/.claude.json` 和 `settings.json`） | `config.yaml` 中的 `mcp_servers` |
| `skills/<name>/`（包含 `SKILL.md` 的目录） | `~/.hermes/skills/claude-code-imports/<name>/` |
| `commands/*.md`（斜杠命令） | 跳过并附注说明——请将其转换为技能 |

Claude 的 `Bash(npm run test:*)` 前缀规则会变为 `npm run test*` glob。非 `Bash` 的权限规则（`Read(...)`、`WebFetch` 等）会控制 Claude 专属工具，因此会报告为未映射而不会导入。

### Codex CLI (`~/.codex`)

| Codex CLI | Hermes |
|---|---|
| `AGENTS.md`（全局指令） | `~/.hermes/memories/MEMORY.md` 中的记忆条目 |
| `config.toml` → `[mcp_servers.*]` | `config.yaml` 中的 `mcp_servers` |
| `memories/*.md` | `~/.hermes/memories/MEMORY.md` 中的记忆条目 |
| `skills/<name>/`（包含 `SKILL.md` 的目录） | `~/.hermes/skills/codex-imports/<name>/` |

## 绝不会导入什么

**API 密钥和凭据。**绝不会读取凭据文件（`~/.claude/.credentials.json`、`~/.codex/auth.json`）；MCP 服务器环境变量或具有看似秘密名称的标头（`*_TOKEN`、`*_API_KEY`、`Authorization` 等）会被移除并列在报告中，以便你有意地重新添加它们。请运行 `hermes setup` 配置提供商，或将密钥添加到 `~/.hermes/.env`。

## 行为说明

- **始终先预览。**该命令会在应用前打印完整计划；在非交互式会话中，除非你传入 `--yes`，否则它会在预览后停止。
- **合并而非替换。**记忆条目会与你现有的 `MEMORY.md` 去重；允许列表/拒绝列表模式会与 `config.yaml` 中已有内容合并。
- **默认跳过冲突。**Hermes 中已经存在的 MCP 服务器或技能会报告为冲突；传入 `--overwrite` 可替换它。
- **格式错误的文件不会中止运行。**损坏的 `settings.json` 或 `config.toml` 会在报告中成为逐项错误，而其他所有内容仍会继续导入。
- 改从 OpenClaw 迁移？请使用 [`hermes claw migrate`](../guides/migrate-from-openclaw.md)。
