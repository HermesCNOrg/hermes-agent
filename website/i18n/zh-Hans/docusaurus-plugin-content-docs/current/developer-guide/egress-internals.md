---
sidebar_position: 14
title: "出站代理内部机制"
description: "iron-proxy 出站防火墙如何与 Hermes 集成：模块布局、生命周期、安全不变量和扩展点"
---

# 出站代理内部机制

本页从贡献者／插件作者视角介绍出站凭据注入防火墙（`hermes egress` / iron-proxy）的架构。面向最终用户的设置和使用文档见 [出站代理](../user-guide/egress/iron-proxy.md)。

用户页面概述了威胁模型和高级设计；本页说明其*如何*接线、安全相关代码位于何处，以及如果你改动它必须保留哪些不变量。

## 模块布局

```text
agent/proxy_sources/iron_proxy.py     核心：二进制安装、CA 生成、配置构建、
                                       子进程生命周期、映射 I/O、PID/nonce
                                       防御。尽可能提供纯函数接口。

hermes_cli/proxy_cli.py               向导和斜杠命令处理程序。
                                       `hermes egress {install,setup,start,stop,
                                       status,disable,config}`。将核心模块
                                       接线到 argparse。

hermes_cli/main.py:_dispatch_egress   顶层子解析器分发器。
                                       dest='egress_command'（有意与入站 OAuth
                                       的 `hermes proxy` 子解析器分离，后者使用
                                       dest='proxy_command'）。

hermes_cli/config.py: proxy schema    DEFAULT_CONFIG 中的 `proxy:` 块。
                                       添加一个配置项意味着：在此处添加它，在
                                       proxy_cli.cmd_setup 中添加向导提示或
                                       `setdefault`，并在用户指南页面中记录它。

tools/environments/docker.py
  _egress_proxy_args_for_docker()     构建 Docker 后端在 `proxy.enabled: true`
                                       时注入的 volume_args / env_overrides /
                                       host_args 三元组。

  DockerEnvironment.__init__          Docker 侧合并逻辑：针对关键出站变量的
                                       冲突检测、经由
                                       _HERMES_EGRESS_NODE_OPTIONS_APPEND
                                       哨兵进行 NODE_OPTIONS 追加合并、
                                       enforce_on_docker 优先级。

tests/test_iron_proxy.py              密封测试（约 70 个）。二进制安装路径、
                                       配置构建、映射 I/O、子进程生命周期、
                                       docker 参数构建器、拒绝 CIDR 默认值、
                                       绑定策略、CA TOCTOU、
                                       ensure_audit_log 行为等。

tests/test_iron_proxy_cli.py          CLI 处理程序单元测试（约 20 个）。
                                       Argparse 接线、响亮失败路径、BWS 刷新
                                       接线、dest='egress_command' 回归保护。

tests/test_iron_proxy_e2e.py          实时 E2E（由 HERMES_RUN_E2E=1 门控）。
                                       真实 iron-proxy 二进制、真实 curl，
                                       验证端到端令牌交换。
```

## 生命周期

```text
hermes egress install
  -> agent.proxy_sources.iron_proxy.install_iron_proxy(force=...)
       从 GitHub Releases 下载固定版本的 tarball + checksums.txt。
       在解压前进行 SHA-256 验证。
       Python 3.12+ 上使用 tarfile.extract(..., filter="data")（PEP 706）；
         较旧 Python 上回退到普通 extract，并通过 _pick_tar_member
         对成员名称进行清理。
       暂存到 ~/.hermes/bin/.iron-proxy_XXXX，chmod 755，os.replace
         到 ~/.hermes/bin/iron-proxy（原子操作）。
       _VERSION_CACHE.pop(target)，使强制重装在下次调用时重新探测
         --version。

hermes egress setup [--from-bitwarden | --no-bitwarden] [--rotate-tokens]
  -> proxy_cli.cmd_setup
       步骤 1. find_iron_proxy(install_if_missing=False) -> 缺失时安装。
       步骤 2. ensure_ca_cert()
                 通过子进程运行 openssl genrsa + req。
                 通过 os.open(O_WRONLY|O_CREAT|O_TRUNC|O_NOFOLLOW, 0o600)
                   + os.replace 写入 CA 密钥。它绝不会以默认 umask
                   存在于磁盘上。
                 以 0o644 写入 CA 证书（公开）。
       步骤 3. discover_provider_mappings()，或在 --from-bitwarden 时
                 通过 fetch_bitwarden_secrets() 从 BWS 获取名称。
                 merge_mappings(existing=load_mappings(), discovered,
                                rotate=args.rotate_tokens) 会保留先前的
                 令牌，除非传入 --rotate-tokens。
                 discover_uncovered_providers() 并显示警告。
       步骤 4. ensure_audit_log(audit_log_path)   # 在 OSError 时抛出
               build_proxy_config(...)，调用点应用默认值
                 （拒绝 CIDR 默认值、来自 _default_http_listen 的绑定策略）。
               write_proxy_config(cfg)            # 经 .tmp + os.replace 原子写入，0o600
               write_mappings(mappings)           # 原子写入，0o600
       步骤 5. proxy_cfg["enabled"] = True；credential_source 保留逻辑
               （重新运行时不要静默地将 bitwarden -> env 降级）；
               save_config(cfg)。

hermes egress start
  -> proxy_cli.cmd_start
       预检查（拒绝启动路径）：
         - credential_source=bitwarden？-> 预验证 access_token_env + project_id
       -> iron_proxy.start_proxy(
            refresh_secrets_from_bitwarden=...,
            bitwarden_config=...,
          )
            existing=_read_pid(); 如果存活，则幂等返回。
            _build_proxy_subprocess_env(...):  允许列表 + 映射的 real_env_names，
              移除 HTTPS_PROXY 等以避免递归，可选 BWS 刷新
              （除非 allow_env_fallback=true，否则缺少值时抛出异常）。
            设置 nonce：_proxy_nonce = sha256(urandom(16)); env[NONCE_ENV] = ...
            通过 O_NOFOLLOW + 0o600 + st_uid 检查打开 log_path。
            使用 stdin=DEVNULL、stdout=log_fd、stderr=STDOUT 的 Popen，
              start_new_session=True（POSIX）。
            在 finally 中关闭父进程的 log_fd。
            _write_pidfile_safely(pidfile, proc.pid)
              O_EXCL + O_NOFOLLOW + uid 检查 + 持久化 nonce 旁路文件。
              FileExistsError -> 区分存活与陈旧状态，陈旧时重试一次。
            安装 SIGINT/SIGTERM 处理程序（仅主线程）。
            轮询循环（do-while 形式）：
              while True:
                if proc.poll() is not None: tail log + unlink pidfile + raise
                if _port_listening(probe_host, tunnel_port): break  # probe_host = 已配置的绑定主机
                if time.time() >= deadline: break  （do-while：在第一次探测后检查）
                time.sleep(0.1)
            退出时若未监听：_kill_and_wait(proc) + unlink pidfile + raise。

hermes egress stop
  -> iron_proxy.stop_proxy
       _read_pid + _pid_alive 守卫。
       starttime_before = _pid_proc_starttime(pid)   # 仅 Linux；其他平台为 None
       os.kill(pid, SIGTERM)
       最多等待 5 秒以优雅退出。
       宽限期后：重新检查 starttime + _pid_alive。
         如果已回收（starttime 漂移 OR _pid_alive False），不要 SIGKILL。
         否则 os.kill(pid, _KILL_SIGNAL)。
       _cleanup_state_files：unlink pidfile + nonce 兄弟文件。
```

## 安全不变量

这些是承重属性。如果你改动该模块，必须保留它们。有回归测试的地方会标明测试名称。

### 文件系统权限

| 路径 | 模式 | 测试 |
|---|---|---|
| `~/.hermes/proxy/`（目录） | `0o700` | `test_proxy_state_dir_is_0o700` |
| `ca.key` | `0o600` | `test_ca_key_created_with_0o600` |
| `ca.crt` | `0o644` | （隐式；`ensure_ca_cert` 中的 chmod 调用） |
| `proxy.yaml` | `0o600` | （`write_proxy_config` 中原子重命名后的 chmod） |
| `mappings.json` | `0o600` | （`write_mappings` 中原子重命名后的 chmod） |
| `iron-proxy.pid` | `0o600` | （`_write_pidfile_safely` 中 `os.open(..., 0o600)` 的模式） |
| `iron-proxy.nonce` | `0o600` | （`_write_pidfile_safely` 中 `os.open(..., 0o600)` 的模式） |
| `audit.log` | `0o600` | `test_ensure_audit_log_creates_with_0o600` |
| `iron-proxy.log` | `0o600` | （`os.open(..., 0o600)` + `fchmod`） |

所有写入路径均使用 `os.open(O_WRONLY | O_CREAT | O_NOFOLLOW, 0o600)` + `os.fstat().st_uid` 检查。禁止使用 `shutil.copy2` + `os.chmod`，因为它会泄露一个默认 umask 时间窗口。

### 子进程环境最小化

`_build_proxy_subprocess_env` **不得**使用 `os.environ.copy()`。允许列表是 `_PROXY_SUBPROCESS_ENV_ALLOWLIST`（PATH、HOME、区域设置等）加上 `load_mappings()` 引用的环境变量名称。其余一切都留在主机上。

回归测试：`test_subprocess_env_strips_unrelated_secrets`、`test_subprocess_env_strips_proxy_recursion_vars`、`test_subprocess_env_keeps_infrastructure_vars`。

### 绑定策略

`_default_http_listen` 返回单元素列表：Linux 上为 docker bridge 网关 IP（容器通过 `host.docker.internal:host-gateway` 访问代理，它会解析为 bridge 网关——环回绑定无法从其中的容器访问）；macOS/Windows Docker Desktop 上为环回地址（VPNkit 将 `host.docker.internal` 路由至主机）。Linux 上如果无法检测到 docker0 bridge，则会带警告回退到环回地址。绝不能是 `0.0.0.0`，绝不能是 `:PORT`（INADDR_ANY）。

`_detect_docker_bridge_ip` 通过 `ipaddress.IPv4Address` 验证，并拒绝 `is_unspecified` / `is_loopback` / `is_multicast` / `is_reserved` / `is_link_local` / `is_global`。PATH 上恶意的 `ip` shim 无法注入 `0.0.0.0`。

**v0.39 架构约束和监听器角色（已针对二进制实时验证）：**二进制的 `config.Proxy` 结构体仅有单数监听器字段——没有复数 `http_listens` 列表。`tunnel_listen` 是 CONNECT + MITM 监听器（`HTTPS_PROXY` 流量命中的位置）；`http_listen` 仅处理绝对形式的纯 HTTP 转发（发送至它的 CONNECT 会作为常规请求中继到上游并返回 400）。因此，`build_proxy_config` 在 `tunnel_port` 上绑定 `tunnel_listen`，在 `tunnel_port + 1` 上绑定 `http_listen`，二者都绑定于平台绑定主机。Docker 后端将 `HTTPS_PROXY` 设为 `tunnel_port`，将 `HTTP_PROXY` 设为 `tunnel_port + 1`。

存活探测（`start_proxy` 轮询循环、`get_status`）通过 `_read_http_listen_from_config()` 读取已配置绑定主机，并探测**该**主机——硬编码的环回探测会将健康的 bridge 绑定守护进程报告为死亡。

回归测试：`test_default_bind_is_loopback_not_zero_zero`（断言没有 INADDR_ANY，且渲染的 yaml 中**没有** `http_listens`）、`test_default_bind_uses_docker_bridge_on_linux`、`test_default_bind_falls_back_to_loopback_without_bridge`、`test_default_bind_is_loopback_on_macos`、`test_detect_docker_bridge_ip_rejects_dangerous`（针对 8 个攻击输入参数化）。

### 指标端口冲突

iron-proxy v0.39 中 `metrics.listen` 默认值为 `:9090`——与 Hermes 默认的 `tunnel_port: 9090` 是**同一**端口。`build_proxy_config` **必须**显式固定 `metrics.listen: 127.0.0.1:0`，以便指标绑定获得一个临时环回端口，无论操作者选择何种 `tunnel_port`，都不会与代理监听器冲突。

回归测试：`test_metrics_listener_pinned_to_loopback_ephemeral`。

### 默认拒绝 CIDR

`_DEFAULT_UPSTREAM_DENY_CIDRS` 覆盖环回地址（v4 + v6）、链路本地地址（包括位于 169.254.169.254 的 IMDS 和 IPv4 映射 v6 形式）、RFC1918、IPv6 ULA、CGNAT 和 RFC2544 基准测试范围。`build_proxy_config(..., upstream_deny_cidrs=None)` **必须**输出默认值；只有显式空列表才能选择退出。

回归测试：`test_default_deny_cidrs_present_when_unspecified`、`test_default_deny_includes_ipv4_mapped_v6`。

### 审计日志响亮失败

`ensure_audit_log` 在任何 `OSError` 上抛出 `RuntimeError`。在固定的 v0.39 中，守护进程永不写入这个文件（没有 `log.audit_path` 字段），因此 `cmd_setup` 将失败视为**警告**（在版本升级前该文件不承重），并将成功行限定为“reserved”。当固定版本迁移至包含 `log.audit_path` 的版本时，应重新审视：预创建对于从第一个字节即为 0o600 的保证变得承重，而向导应再次响亮失败。

**v0.39 架构约束：**`log.audit_path` **不是** iron-proxy v0.39 中 `config.Log` 结构体的字段，因此 `build_proxy_config` 接受 `audit_log` 关键字参数，但**不会**将其输出到渲染的 yaml。v0.39 的每请求记录与守护进程级事件一起落入 `iron-proxy.log`。`audit.log` 文件仍会使用 `O_NOFOLLOW` 以 `0o600` 预创建，因此当固定版本升级到支持独立流的版本时，隐私契约仍然成立。

回归测试：`test_ensure_audit_log_raises_on_immutable_parent`、`test_audit_log_kwarg_does_not_inject_audit_path_v039`。

### Bitwarden 模式响亮失败

当 `credential_source: bitwarden` **且** `proxy.allow_env_fallback: false`（默认值）时：
- 缺少访问令牌环境变量 -> `cmd_start` 拒绝执行。
- 缺少 `project_id` -> `cmd_start` 拒绝执行。
- `bws secret list` 对一个或多个映射提供商不返回值 -> `_build_proxy_subprocess_env` 抛出异常。

在 BW 模式中回退到主机环境变量，恰好会重新引入 BW 路径意图消除的陈旧性 bug。

回归测试：`test_cmd_start_refuses_when_bitwarden_token_missing`（CLI 层）；`_build_proxy_subprocess_env` 中的严格模式断言（守护进程层）。

### docker_env 冲突检测

当 `enforce_on_docker: true` 时，针对任何出站控制变量（HTTPS_PROXY、SSL_CERT_FILE、NODE_EXTRA_CA_CERTS 等）或任何映射的 `real_env_name`（OPENROUTER_API_KEY 等）的 `docker_env` 覆盖，都会在容器启动**之前**抛出 `RuntimeError`。

回归测试：`test_docker_env_collision_with_proxy_raises_when_enforce`。

### PID 回收防御

在信任 `argv[0]` 基名匹配之前，`_pid_alive` **必须**查阅进程内 `_proxy_nonce`（同一进程情况）或磁盘上的 `iron-proxy.nonce`（跨 CLI 情况）。`stop_proxy` **必须**在 SIGKILL 前重新检查 `/proc/<pid>/stat` 的 starttime，并在 starttime 漂移时抑制该信号。

回归测试：`test_stop_proxy_suppresses_sigkill_on_pid_recycle`、`test_pid_proc_starttime_parses_comm_with_parens`、`test_persisted_nonce_roundtrip`。

### 重新设置时的令牌保留

`merge_mappings(existing, discovered, rotate=False)` **必须**为重叠的提供商返回先前令牌。重新运行 `hermes egress setup` 不得静默地使正在运行的沙箱收到 401。`--rotate-tokens` 是显式选择加入。

回归测试：`test_merge_mappings_preserves_existing_tokens`、`test_merge_mappings_rotate_mints_fresh_tokens`。

### `credential_source` 保留

重新运行时，若未显式传入 `--no-bitwarden` 标志，`cmd_setup` **不得**将 `credential_source: bitwarden` 降级为 `env`。运行 `hermes egress setup`（无标志）会保留此前配置的任何值。

这通过 CLI 测试中的 `cmd_setup` 流程进行测试（在 `--from-bitwarden` 后跟一次普通 `setup` 重新运行时，会执行 bitwarden 保留路径）。

## 扩展点

### 添加新的 bearer-token 提供商

`iron_proxy.py` 中的 `_BEARER_PROVIDERS` 将环境变量名映射为上游主机元组。添加条目会使它可由 `discover_provider_mappings()` 发现；环境变量存在时，向导会自动为其生成令牌。

```python
_BEARER_PROVIDERS: Dict[str, Tuple[str, ...]] = {
    ...,
    "MY_PROVIDER_API_KEY": ("api.myprovider.com",),
}
```

还要更新 `_DEFAULT_ALLOWED_HOSTS`，使代理默认允许该上游。运行 `test_discover_provider_mappings_*` 进行确认。

### 添加新的 header-token 提供商（x-api-key 系列）

如果提供商使用静态的非 Authorization 标头（如 Anthropic 的 `x-api-key`、Azure 的 `api-key` 或 Gemini 的 `x-goog-api-key`）进行认证，请将其添加到 `_HEADER_AUTH_PROVIDERS`——iron-proxy 的 `secrets.replace.match_headers` 以任意标头名称为目标，因此这些是一级的交换提供商：

```python
_HEADER_AUTH_PROVIDERS: Dict[str, Dict[str, Tuple[str, ...]]] = {
    ...,
    "MY_PROVIDER_API_KEY": {
        "hosts": ("api.myprovider.com",),
        "match_headers": ("x-my-auth-header", "Authorization"),
        "aliases": (),
    },
}
```

`aliases` **仅可**用于*相同*凭据的可互换环境变量名（例如为 `GEMINI_API_KEY` 设置 `GOOGLE_API_KEY`）——别名名称会折叠为单个映射，因为同一主机上的两条 `require: true` 规则会拒绝彼此的请求。还要更新 `_DEFAULT_ALLOWED_HOSTS`。

### 添加新的签名认证提供商（未覆盖）

如果提供商使用 SigV4 / SDK 生成的 OAuth / 请求签名，静态标头交换无法覆盖它。将环境变量添加到 `_NON_BEARER_PROVIDERS`，使向导和 `hermes egress status` 针对它发出警告：

```python
_NON_BEARER_PROVIDERS: Tuple[str, ...] = (
    ...,
    "MY_SIGNED_PROVIDER_ACCESS_KEY",
)
```

### 将 iron-proxy 接线到非 Docker 后端

`_egress_proxy_args_for_docker` 是 Docker 专用的。希望采用类似接线的后端需要其自身的类似实现，该实现：

1. 读取 `load_config().get("proxy", {})`；如果 `enabled` 为 false 则返回空参数。
2. 调用 `iron_proxy.get_status()`；在 `configured` / `pid` / `listening` / `ca_cert_path` 失败路径上呈现 `enforce` 语义。
3. 调用 `iron_proxy.load_mappings()`；如果为空**且** `enforce_on_docker: true`，则拒绝挂载。
4. 设置七个环境变量（HTTPS_PROXY、NO_PROXY、REQUESTS_CA_BUNDLE、SSL_CERT_FILE、CURL_CA_BUNDLE、NODE_EXTRA_CA_CERTS、HERMES_EGRESS_PROXY）以及每个映射对应的 `HERMES_PROXY_TOKEN_<NAME>` 变量。
5. 将 CA 证书分发到运行时会信任的沙箱路径（通常为 `/etc/ssl/certs/hermes-egress-ca.crt`）。
6. 针对用户的后端专用环境配置实施冲突检测。

Docker 实现约 150 行；预计 Modal / Daytona / SSH 也需要相近篇幅。

### 订阅每请求审计事件

当前固定的 v0.39 上，iron-proxy 将行分隔 JSON 写入 `~/.hermes/proxy/iron-proxy.log`（守护进程和每请求记录合并；参见用户指南中的“Logging on iron-proxy v0.39”）。插件／外部监视器可以跟踪该文件，并对允许列表拒绝、密钥交换或上游错误作出反应。当固定版本升级到支持 `log.audit_path` 的版本时，每请求流会移至 `audit.log`，而接线到该路径的监视器无需操作者操作即可生效。架构记录在 [docs.iron.sh/audit](https://docs.iron.sh/audit)（链接）。

## 测试

```bash
# 密封套件（无网络、无真实二进制）
scripts/run_tests.sh tests/test_iron_proxy.py tests/test_iron_proxy_cli.py

# 实时 E2E（真实二进制、真实 curl、真实 CONNECT 隧道）
HERMES_RUN_E2E=1 scripts/run_tests.sh tests/test_iron_proxy_e2e.py

# 针对 `hermes egress` 的实时 PTY 冒烟测试
HERMES_HOME=/tmp/hermes-egress-test python3 -m hermes_cli.main egress --help
HERMES_HOME=/tmp/hermes-egress-test python3 -m hermes_cli.main egress setup --help
```

CLI 使用 argparse，因此 `--help` 是“我的新标志是否正确注册”的良好首次探测。

## 另请参阅

- 面向用户的设置和故障排除：[出站代理](https://hermes-agent.nousresearch.com/docs/user-guide/egress/iron-proxy)
- Docker 后端内部机制：[Docker](https://hermes-agent.nousresearch.com/docs/user-guide/docker)
- Bitwarden Secrets Manager 集成：[`hermes secrets bitwarden`](https://hermes-agent.nousresearch.com/docs/user-guide/secrets/bitwarden)
- CLI 命令参考：[`hermes egress`](https://hermes-agent.nousresearch.com/docs/reference/cli-commands#hermes-egress)
- 沙箱注入的环境变量：[出站代理（沙箱注入）](https://hermes-agent.nousresearch.com/docs/reference/environment-variables#egress-proxy-sandbox-injected)
