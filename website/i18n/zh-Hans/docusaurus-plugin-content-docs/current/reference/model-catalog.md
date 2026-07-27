---
sidebar_position: 11
title: 模型目录
description: 用于管理 OpenRouter 和 Nous Portal 精选模型选择器列表的远程托管清单。
---

# 模型目录

Hermes 会从与文档站点一同托管的 JSON 清单中获取 **OpenRouter** 和 **Nous Portal** 的精选模型列表。这样，维护者无需发布新版 `hermes-agent`，也能更新模型选择器中的列表。

当清单无法访问时（例如处于离线状态、网络受限或托管服务故障），Hermes 会静默回退到 CLI 自带的仓库内快照。清单绝不会导致模型选择器不可用——最坏的情况只是显示你当前安装版本所附带的列表。

## 线上清单 URL

```
https://hermes-agent.nousresearch.com/docs/api/model-catalog.json
```

每次有变更合并到 `main` 时，现有的 `deploy-site.yml` GitHub Pages 流水线都会发布该清单。其事实来源是仓库中的 `website/static/api/model-catalog.json`。

## Schema

```json
{
  "version": 1,
  "updated_at": "2026-04-25T22:00:00Z",
  "metadata": {},
  "providers": {
    "openrouter": {
      "metadata": {},
      "models": [
        {"id": "z-ai/glm-5.2",         "description": "default", "default": true},
        {"id": "moonshotai/kimi-k2.6", "description": "recommended", "metadata": {}},
        {"id": "openai/gpt-5.4",       "description": ""}
      ]
    },
    "nous": {
      "metadata": {},
      "models": [
        {"id": "z-ai/glm-5.2", "default": true},
        {"id": "anthropic/claude-opus-4.7"},
        {"id": "moonshotai/kimi-k2.6"}
      ]
    }
  }
}
```

字段说明：

- **`version`** — 整数形式的 schema 版本。未来的 schema 会递增此版本号；Hermes 会拒绝无法识别版本的清单，并回退到硬编码快照。
- **`metadata`** — 清单、提供商和模型层级均可使用的自由格式字典，键名不限。Hermes 会忽略未知字段，因此你可以为条目添加注解（例如 `"tier": "paid"`、`"tags": [...]` 等），无需为此协调 schema 变更。
- **`description`** — 仅用于 OpenRouter。它决定模型选择器中的徽章文本（`"recommended"`、`"free"`、`"default"` 或留空）。Nous Portal 不使用此字段——免费层级限制由 Portal 的定价端点实时确定。
- **`default`** — 每个提供商只能有一个条目包含 `"default": true`。该模型是**静默默认模型**：当用户从未选择过模型时，Hermes 会使用它（例如 GUI 新手引导确认卡片、已配置 `provider` 但未配置 `model`，或 `model.default` 为空）。运行时只读取缓存（`get_default_model_from_cache`），因此高频解析路径绝不会访问网络；如果没有已缓存的清单，Hermes 会回退到仓库内的 `PREFERRED_SILENT_DEFAULT_MODEL` 常量，该常量必须与标记为默认的条目一致。这样，维护者无需发布新版本即可更换静默默认模型。该模型会特意选择能力可靠且成本较低的型号，而不会选择价格最高的旗舰型号。
- **定价和上下文长度**不包含在清单中。获取模型列表时，这些数据来自提供商的实时 API（`/v1/models` 端点和 models.dev）。

## 获取行为

| 何时 | 会发生什么 |
|---|---|
| `/model` 或 `hermes model` | 如果磁盘缓存已过期，则获取清单；否则使用缓存 |
| 磁盘缓存仍有效（< TTL） | 不发起网络请求 |
| 网络故障，但存在缓存 | 静默回退到缓存，并记录一行日志 |
| 网络故障，且没有缓存 | 静默回退到仓库内快照 |
| 清单未通过 schema 验证 | 按无法访问处理 |

缓存位置：`~/.hermes/cache/model_catalog.json`。

## 配置

```yaml
model_catalog:
  enabled: true
  url: https://hermes-agent.nousresearch.com/docs/api/model-catalog.json
  ttl_hours: 1
  providers: {}
```

将 `enabled` 设为 `false` 可完全禁用远程获取，并始终使用仓库内快照。

### 为各提供商设置覆盖 URL

第三方可以使用相同的 schema，自行托管精选模型列表。可按如下方式将某个提供商指向自定义 URL：

```yaml
model_catalog:
  providers:
    openrouter:
      url: https://example.com/my-openrouter-curation.json
```

覆盖清单只需包含需要自定义的提供商区块。其他提供商仍会通过主 URL 解析。

## 更新清单

维护者：

```bash
# Re-generate from the in-repo hardcoded lists (keeps manifest in sync after
# editing OPENROUTER_MODELS or _PROVIDER_MODELS["nous"] in hermes_cli/models.py).
python scripts/build_model_catalog.py
```

然后为 `website/static/api/model-catalog.json` 产生的变更向 `main` 提交 PR。合并后，文档站点会自动部署，新清单将在几分钟内上线。

你也可以直接手动编辑 JSON，以调整不适合写入仓库内快照的细粒度元数据——生成脚本只是一项便捷工具，并非唯一的事实来源。