---
sidebar_position: 4
---

# 同时运行多个 Gateway

在一台机器上将多个 [profile](./profiles.md)（每个拥有各自的机器人 Token、会话和记忆）作为托管服务运行。本文涵盖运维要点：如何一起启动它们、跨 profile 查看日志、防止主机休眠，以及从常见的 launchd/systemd 异常中恢复。

如果你只运行一个 Hermes Agent，则无需阅读本文——请参阅 [Profiles](./profiles.md) 了解基础内容。

## 何时使用

当你希望两个或多个 Hermes Agent 同时在线时适用此方案。常见场景：

- 一个 Telegram 机器人上运行个人助手，另一个运行编码助手
- 每个家庭成员一个 Agent，或每个 Slack 工作区一个 Agent
- 同一配置的沙箱 + 生产实例
- 一个研究 Agent + 一个写作 Agent + 一个定时任务机器人——每个拥有独立的记忆和技能

每个 profile 已有其专属的跨平台 LaunchAgent（`ai.hermes.gateway-<name>.plist`）或 systemd 用户服务（`hermes-gateway-<name>.service`）。本指南在此基础上提供统一管理的模式。

## 快速开始

```bash
# 创建 profiles（一次性操作）
hermes profile create coder
hermes profile create personal-bot
hermes profile create research

# 分别配置
coder setup
personal-bot setup
research setup

# 将每个 gateway 安装为托管服务
coder gateway install
personal-bot gateway install
research gateway install

# 全部启动
coder gateway start
personal-bot gateway start
research gateway start
```

完成——三个独立的 Agent，各自运行在自己的进程中，在崩溃和用户登录时自动重启。

## 替代方案：一个 Gateway 服务所有 Profile（多路复用）

上述模式是**每个 profile 一个进程**。这是默认做法，也是大多数场景的正确选择。但在拥有大量 profile 的主机上——或在一个 profile 一个进程运维成本过高的容器部署中——你可以改为运行**一个多路复用 gateway**：默认 profile 的 gateway 成为唯一的入站进程，为机器上的**所有** profile 处理消息。

这是**选用的**且**默认关闭**。关闭时，本文所有内容不变——以下每个行为都不生效。

### 何时优选多路复用

- 容器/VPS 部署中，N 个 supervisor 单元、N 个端口和 N 个 PID 文件成为负担。
- 许多低流量 profile，每个单独起一个进程不值得。
- 你希望只有一个东西需要启动、监控和重启。

当你希望 profile 之间有严格的进程级隔离（独立的内存空间、独立的崩溃域、能够在不影响其他 profile 的情况下重启其中一个）时，仍然坚持每个 profile 一个进程。

### 如何开启

在**默认 profile**（它拥有多路复用器）上设置该标志，然后重启其 gateway：

```bash
hermes config set gateway.multiplex_profiles true
hermes gateway restart
```

等价地，在默认 profile 的 `~/.hermes/config.yaml` 中：

```yaml
gateway:
  multiplex_profiles: true
```

（为方便起见，顶层 `multiplex_profiles: true` 也是接受的。）下次启动时，默认 gateway 会枚举所有 profile，用每个 profile 自己的凭据启动其已启用的平台，并将每条入站消息路由到所属的 profile。每次对话解析被路由 profile 的配置、技能、记忆、SOUL **以及 provider 密钥**——凭据绝不会跨 profile 共享。

次要 profile 你**不需要**运行 `hermes gateway start`——默认 gateway 会为它们服务。请参阅下面的合约变更。

### 开启多路复用后的变化

启用该标志后，一些行为会发生变化。关闭标志后所有这些都会恢复。

#### 1. 次要 profile 不得自行启动 gateway

多路复用器运行时，对指定 profile 执行 `hermes gateway start` / `run` 会报**硬错误**，并将你指回多路复用器：

```
The default gateway is running as a profile multiplexer and already serves
profile 'coder'. ...
```

多路复用器是唯一的入站进程；第二个 profile gateway 会导致该 profile 的平台被双重绑定。仅当你确实希望为该 profile 使用独立进程时，才使用 `--force`（不推荐在多路复用器运行时使用）。因此，本文前面部分的跨 profile 生命周期脚本在多路复用模式下**不适用**——你只需要管理默认 gateway。

#### 2. HTTP 入站平台通过 `/p/<profile>/` URL 前缀访问

Webhook（及其他 HTTP 入站）流量在默认监听器下通过 profile 前缀到达次要 profile，**而不是**第二个端口：

```
# 默认 profile
POST http://host:8644/webhooks/<route>
# "coder" profile，同一监听器
POST http://host:8644/p/coder/webhooks/<route>
```

前缀中的未知或未配置 profile 返回 `404`。因为一个共享监听器已经通过这种方式服务所有 profile，所以**次要 profile 不得自行启用端口绑定平台**——否则是配置错误，gateway 拒绝启动并指明 profile 和平台名：

```
Profile 'coder' enables the port-binding platform 'webhook', but
gateway.multiplex_profiles is on. ... Remove platforms.webhook from profile
'coder's config.yaml (configure it only on the default profile).
```

此规则覆盖的端口绑定平台：`webhook`、`api_server`、`msgraph_webhook`、`feishu`、`wecom_callback`、`bluebubbles`、`sms`。这些平台**仅在默认 profile 上配置**；所有 profile 都可通过其 `/p/<profile>/` 前缀访问。

#### 3. 每个凭据平台仍然需要每个 profile 自己的 Token

轮询/连接平台（Telegram、Discord、Slack、Matrix、Signal……）在多路复用下正常工作，但每个启用该平台的 profile 都必须提供**自己的**机器人 Token——同一个 Token 不能被两个 profile 同时轮询。如果两个 profile 配置了相同的 `(platform, token)`，启动时会快速失败并指明两个 profile 的名称（参见 [Token 冲突安全](#token-conflict-safety)——规则不变，只是现在在同一个进程内部执行检查）。

#### 4. 会话键按 profile 命名空间隔离

每个 profile 的会话存在于 `agent:<profile>:…` 命名空间下，这样同一平台/聊天中的两个 profile 在共享会话存储中永远不会冲突。**默认** profile 保留原有的 `agent:main:…` 命名空间，字节级不变，因此现有默认 profile 的会话不受影响——无需迁移，不会产生孤立历史。

#### 5. 一个 PID/锁和一个状态界面

只有一个进程级别的 PID 和锁（多路复用器，位于默认 home 下）。`hermes status` 显示多路复用器及其服务的 profile；`hermes status -p <name>` 聚焦单个 profile。每个 profile 仍在自己的 home 下写入各自的 `runtime_status.json`，因此现有的 per-profile 读取工具继续可用。

#### 什么**没有**变化

Per-profile 的 `.env` 凭据隔离得到保留，甚至事实上更加严格：profile 的密钥从其自身作用域解析，绝不会合并到共享环境中（这也意味着子进程，如 MCP 服务器和 Kanban Worker，只能看到自己 profile 的密钥）。Kanban、profile 作用域的技能/记忆/SOUL 以及模型路由的行为与使用独立 gateway 时完全一致。

### 将共享机器人的聊天路由到指定 Profile（`profile_routes`）

多路复用按**凭据**（每个 profile 自己的机器人 Token）或 **URL 前缀**（HTTP 平台的 `/p/<profile>/`）选择 profile。当多个社区共享**一个**机器人 Token 时——例如一个 Discord 机器人服务多个 Guild——你可以通过 `gateway.profile_routes` 额外将特定的 Guild/频道/线程路由到不同的 profile：

```yaml
gateway:
  multiplex_profiles: true
  profile_routes:
    # 整个 Discord 服务器 → 一个 profile
    - name: acme-server
      platform: discord
      guild_id: "1234567890"
      profile: acme

    # 该服务器中的一个频道 → 另一个 profile
    - name: acme-support
      platform: discord
      guild_id: "1234567890"
      chat_id: "9876543210"
      profile: acme-support

    # 一个 Telegram 群组（没有 guild 概念——仅 chat_id）
    - name: tg-group
      platform: telegram
      chat_id: "-1001234567890"
      profile: tg-profile
```

路由按最具体优先匹配（`thread_id` > `chat_id` > `guild_id`），所有声明的字段必须同时满足（AND），以频道为键的路由也匹配其父频道为该频道的线程/论坛帖子。未匹配任何路由的消息留在默认/活跃 profile 上。路由到的 profile 获得上述完整的 per-profile 隔离（配置、技能、记忆、凭据、会话命名空间）。路由在每个平台适配器上都有效，不限于 Discord。

`profile_routes` 要求 `gateway.multiplex_profiles: true`；未启用多路复用时路由被忽略。如果某个路由指定的 profile 在磁盘上不存在，gateway 会记录一条包含 profile 名和来源的警告，并回退到默认 home。

## 一次性启动、停止或重启所有 Gateway

CLI 提供单个 profile 的生命周期命令。要跨所有 profile 执行操作，在 shell 循环中包装它们。将下面的脚本放到 `~/.local/bin/hermes-gateways` 并执行 `chmod +x`：

```sh
#!/bin/sh
set -eu

# 在此添加或删除 profile 名称，以便与你创建/删除的 profile 保持同步
profiles="default coder personal-bot research"

usage() {
  echo "Usage: hermes-gateways {start|stop|restart|status|list}"
}

run_for_profile() {
  profile="$1"
  action="$2"
  if [ "$profile" = "default" ]; then
    hermes gateway "$action"
  else
    hermes -p "$profile" gateway "$action"
  fi
}

action="${1:-}"
case "$action" in
  start|stop|restart|status)
    for profile in $profiles; do
      echo "==> $action $profile"
      run_for_profile "$profile" "$action"
    done
    ;;
  list)
    hermes gateway list
    ;;
  *)
    usage
    exit 2
    ;;
esac
```

然后：

```bash
hermes-gateways start      # 启动所有已配置的 profile
hermes-gateways stop       # 停止所有已配置的 profile
hermes-gateways restart    # 全部重启
hermes-gateways status     # 查看所有 profile 的状态
hermes-gateways list       # 委托给 `hermes gateway list`
```

:::tip
`default` profile 通过 `hermes gateway <action>`（不带 `-p`）而不是 `hermes -p default gateway <action>` 来操作。上面的包装脚本已处理了两种形式的差异。
:::

## 管理单个 Profile

每个 profile 安装的快捷命令：

```bash
coder gateway run        # 前台运行（Ctrl-C 停止）
coder gateway start      # 启动托管服务
coder gateway stop       # 停止托管服务
coder gateway restart    # 重启
coder gateway status     # 查看状态
coder gateway install    # 创建 LaunchAgent / systemd 单元
coder gateway uninstall  # 删除服务文件
```

它们等价于 `hermes -p coder gateway <action>`——在 profile 别名不在 `PATH` 中，或需要从脚本动态定位 profile 时很有用。

## 服务文件

每个 profile 使用唯一名称安装自己的服务，因此安装永远不会冲突：

| 平台    | 路径                                                     |
| ------- | -------------------------------------------------------- |
| macOS   | `~/Library/LaunchAgents/ai.hermes.gateway-<profile>.plist` |
| Linux   | `~/.config/systemd/user/hermes-gateway-<profile>.service`  |

默认 profile 保留原有的名称：`ai.hermes.gateway.plist` / `hermes-gateway.service`。

## 查看日志

每个 profile 写入自己的日志文件：

```bash
# 默认 profile
tail -f ~/.hermes/logs/gateway.log
tail -f ~/.hermes/logs/gateway.error.log

# 命名 profile
tail -f ~/.hermes/profiles/<name>/logs/gateway.log
tail -f ~/.hermes/profiles/<name>/logs/gateway.error.log
```

同时查看所有 profile 的日志：

```bash
tail -f ~/.hermes/logs/gateway.log ~/.hermes/profiles/*/logs/gateway.log
```

CLI 还提供结构化的日志查看器：

```bash
hermes logs -f                  # 跟随默认 profile
hermes -p coder logs -f         # 跟随一个 profile
hermes logs --help              # 过滤器、级别、JSON 输出
```

## 确认实际运行的内容

```bash
hermes profile list             # profiles + 模型 + gateway 状态
hermes-gateways status          # 所有 profile 的完整状态
launchctl list | grep hermes    # macOS——PID 和标签
systemctl --user list-units 'hermes-gateway-*'   # Linux——单元
```

## 编辑配置

每个 profile 的配置保存在其自身目录下：

```
~/.hermes/profiles/<name>/
├── .env              # API 密钥、机器人 Token（chmod 600）
├── config.yaml       # 模型、provider、toolsets、gateway 设置
└── SOUL.md           # 人格 / 系统提示词
```

默认 profile 使用 `~/.hermes/` 目录，包含相同的三个文件。

使用任意编辑器或通过 CLI 编辑：

```bash
hermes config set model.model anthropic/claude-sonnet-4    # 默认 profile
coder config set model.model openai/gpt-5                  # 命名 profile
```

编辑 `.env` 或 `config.yaml` 后，重启受影响的 gateway：

```bash
coder gateway restart
# 或全部重启：
hermes-gateways restart
```

## 保持主机唤醒

Gateway 进程可以全天运行，但操作系统仍会在空闲时尝试休眠。两种方案：

### macOS — `caffeinate`

`caffeinate` 是 macOS 内置命令，在其运行期间阻止休眠。无需安装。

```bash
caffeinate -dis                    # 阻止显示屏、空闲和系统休眠
caffeinate -dis -t 28800           # 同上，8 小时后自动退出
caffeinate -i -w $(cat ~/.hermes/gateway.pid) &   # 在默认 gateway 运行时保持唤醒

# 持久化：后台运行，不再关注
nohup caffeinate -dis >/dev/null 2>&1 &
disown

# 检查 / 停止
pmset -g assertions | grep -iE 'caffeinate|prevent|user is active'
pkill caffeinate
```

| 标志    | 效果             |
| ------- | ---------------- |
| `-d`    | 阻止显示屏休眠   |
| `-i`    | 阻止空闲系统休眠（默认） |
| `-m`    | 阻止磁盘休眠     |
| `-s`    | 阻止系统休眠（仅交流供电的 Mac） |
| `-u`    | 模拟用户活动（防止屏幕锁定） |
| `-t N`  | 在 `N` 秒后自动退出  |
| `-w P`  | 在 PID `P` 退出时退出 |

:::warning 合盖仍会使 Mac 休眠
`caffeinate` 无法覆盖 MacBook 上由硬件驱动的合盖休眠。如需合盖运行，请更改节能/电池偏好设置，或使用第三方工具。
:::

### Linux — `systemd-inhibit` 或 `loginctl`

```bash
# 在命令运行时阻止挂起
systemd-inhibit --what=idle:sleep --who=hermes --why="gateways running" \
  sleep infinity &

# 允许用户服务在登出后继续运行（推荐）
sudo loginctl enable-linger "$USER"
```

启用 lingering 后，你的 systemd 用户单元（包括 `hermes-gateway-<profile>.service`）会在 SSH 断开连接和重启后继续运行。

## Token 冲突安全

每个 profile 必须为每个平台使用唯一的机器人 Token。如果两个 profile 共享一个 Telegram、Discord、Slack、WhatsApp 或 Signal Token，第二个 gateway 将拒绝启动，并显示包含冲突 profile 名称的错误。

审计方法：

```bash
grep -H 'TELEGRAM_BOT_TOKEN\|DISCORD_BOT_TOKEN' \
     ~/.hermes/.env ~/.hermes/profiles/*/.env
```

## 更新代码

`hermes update` 一次性拉取最新代码，并将新的内置技能同步到所有 profile：

```bash
hermes update
hermes-gateways restart
```

用户修改过的技能永远不会被覆盖。

## 故障排查

### "Could not find service in domain for user gui: 501"

你在之前执行了 `hermes gateway stop` 后又运行了 `hermes gateway start`。CLI 的 `stop` 会执行完整的 `launchctl unload`，从而将服务从 launchd 的注册表中移除。CLI 会在 `start` 时捕获此特定错误并自动重新加载 plist（`↻ launchd job was unloaded; reloading service definition`）。服务正常启动。无需修复。

### 崩溃后遗留的过期 PID

如果某个 profile 的 gateway 显示 `not running` 但仍有进程存活：

```bash
ps -ef | grep "hermes_cli.*-p <profile>"
cat ~/.hermes/profiles/<profile>/gateway.pid
kill -TERM <pid>          # 优雅终止
kill -KILL <pid>          # 如果几秒后仍未成功
<profile> gateway start
```

### 强制硬重置某个服务

```bash
# macOS
launchctl unload ~/Library/LaunchAgents/ai.hermes.gateway-<profile>.plist
launchctl load   ~/Library/LaunchAgents/ai.hermes.gateway-<profile>.plist

# Linux
systemctl --user restart hermes-gateway-<profile>.service
```

### 健康检查

```bash
hermes doctor                  # 默认 profile
hermes -p <profile> doctor     # 单个 profile
```
