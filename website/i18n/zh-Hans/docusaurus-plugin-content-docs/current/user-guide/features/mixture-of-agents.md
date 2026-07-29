---
sidebar_position: 7
title: "Mixture of Agents"
description: "创建具名的 MoA 预设，它们在 Mixture of Agents 提供商下显示为可选择的模型"
---

# Mixture of Agents

Mixture of Agents（混合智能体）是一种虚拟模型提供商。每个具名的 MoA 预设都会在 `moa` 提供商下显示为一个可选择的模型。

当你选择某个 MoA 预设时，该预设的聚合器就是实际运行的模型。它负责撰写助手回复并发出工具调用。参考模型会先运行，并提供供聚合器使用的分析。

当困难任务可受益于多个模型视角、但仍需要 Hermes 的正常智能体循环——工具调用、后续迭代、中断、记录持久化，以及与任何其他消息相同的会话上下文——时，使用 MoA。

## 选择 MoA 预设作为模型

你可以通过常规模型选择界面选择预设：

```bash
/model default --provider moa
/model review --provider moa
```

MoA 预设可在 **每个 Hermes 界面** 上选择，因为 MoA 是模型系统中的普通提供商：

- **CLI / 网关 / TUI `/model`** — 使用 `/model <preset> --provider moa`，或使用 `/model --provider moa` 选择默认预设。当名称与已配置预设完全匹配时，单独使用 `/model <preset>` 也有效。
- **`hermes model`** 和**仪表盘模型选择器** — 会出现 `Mixture of Agents` 提供商行，其中将预设名称列为模型。
- **桌面 GUI 应用** — 模型下拉菜单会显示 `MoA presets` 区域；选择其中一个（`MoA: <preset>`）会将活动模型切换为该预设。桌面设置面板也可创建和编辑预设。

因此，已配置预设会出现在你选择任何其他模型的所有位置。

## 斜杠命令快捷方式

`/moa` 是一次性的便捷语法糖。它通过**默认** MoA 预设运行单条提示，随后恢复你原先使用的模型：

```bash
/moa design and implement a migration plan for this flaky test cluster
```

Hermes 会在该轮临时切换为默认 MoA 预设，发送提示后恢复先前模型。全部参数都是提示内容——`/moa` 不再将其解释为预设名称。

```bash
/moa
```

单独使用 `/moa`（没有提示）只会输出用法。

如需为会话剩余时间**切换**到 MoA 预设，请在模型选择器中选择它——MoA 预设会在每个模型选择界面的 `Mixture of Agents` 提供商下出现（见上文）。`/moa` 有意不是模型切换，因此普通提示绝不会意外改变你的模型。

## 它如何在智能体循环中工作

选择提供商 `moa` 时，每次主模型调用，Hermes 都会：

1. 按名称解析所选预设；
2. 不携带工具 schema 地运行所配置的参考模型（它们仅收到对话中的用户/助手文本——不包括 Hermes 系统提示或工具调用记录——因此参考调用保持低成本，并避免严格提供商的拒绝）；
3. 将参考输出作为聚合器的私有上下文追加；
4. 使用常规 Hermes 工具 schema 调用已配置的聚合器；
5. 将聚合器回复视为真实模型回复；
6. 若聚合器调用工具，正常执行这些工具；
7. 在下次模型迭代时，基于更新后的对话（包括工具结果）再次运行同一 MoA 流程。

由于 MoA 是经由常规模型系统选择的，它会自动与 `/goal`、网关会话、TUI 会话和桌面聊天组合。

## 配置预设

你可以从以下位置配置具名 MoA 预设：

- Dashboard → Models → Model Settings → Mixture of Agents
- Desktop app → Settings → Model → Mixture of Agents
- `hermes moa configure [name]`
- `config.yaml`

配置存储明确的提供商/模型配对，因此你可混用提供商，并使用来自同一提供商的多个模型：

```yaml
moa:
  default_preset: default
  presets:
    default:
      reference_models:
        - provider: openai-codex
          model: gpt-5.5
        - provider: openrouter
          model: deepseek/deepseek-v4-pro
      aggregator:
        provider: openrouter
        model: anthropic/claude-opus-4.8
      # 可选：固定采样温度。省略时（默认），
      # 不会发送 temperature，每个模型使用其提供商默认值——
      # 行为与单模型 Hermes 智能体相同。
      # reference_temperature: 0.6
      # aggregator_temperature: 0.4
      max_tokens: 4096
      enabled: true
```

默认预设：

- 参考：`openai-codex:gpt-5.5`
- 参考：`openrouter:deepseek/deepseek-v4-pro`
- 聚合器 / 实际运行模型：`openrouter:anthropic/claude-opus-4.8`

### 使用 `reference_max_tokens` 调节顾问速度

每轮中，MoA 并行运行参考模型（顾问），然后聚合器执行操作。顾问生成是每轮的主要延迟来源——轮次的实际耗时与顾问输出的 token 数强相关，因为该轮必须等待最慢的顾问完成写作。默认情况下，顾问**不设上限**（未设置 `reference_max_tokens`），所以它们可能输出很长的、论文式建议。

在预设上设置 `reference_max_tokens` 可限制顾问输出，让建议保持简洁。聚合器只需要每位顾问判断的要点，因此上限（例如 `600`）可显著降低每轮实际耗时，且对质量影响很小。它仅限制**顾问**——实际聚合器的输出（用户可见回答）永不受限。

```yaml
moa:
  presets:
    fast:
      reference_models:
        - provider: openrouter
          model: anthropic/claude-opus-4.8
        - provider: openrouter
          model: openai/gpt-5.5
      aggregator:
        provider: openrouter
        model: anthropic/claude-opus-4.8
      reference_max_tokens: 600   # 简洁建议 → 更快的轮次
```

保持未设置（或设为 `0`/空白）即可维持此前不设上限的行为。

### 通过 `fanout` 控制顾问节奏

默认情况下，顾问在**每个用户轮次仅运行一次**（`fanout: user_turn`）——它们在该轮第一条消息上综合规划层面的建议，随后实际运行的聚合器独自完成工具循环的其余部分。这是成本最低的节奏：顾问成本不会随一轮中的工具调用次数倍增。另两种节奏以成本换取建议的新鲜度：

- `fanout: per_iteration` — 顾问在**每次工具迭代**中重新运行，因此其建议始终跟随最新工具结果——代价是顾问延迟和支出会随一轮中的工具调用次数倍增。
- `fanout: every_n:3` — 折中方案：顾问在每个用户轮次的**第一次**迭代运行，之后每第 **3** 次工具迭代运行一次（任何 `N >= 2` 都可）。中间的迭代复用上次顾问运行的缓存指导，因此聚合器每一步仍能获得建议——只是每 N 步刷新一次，而非每一步。计数器在每条新用户消息时重置，因此每轮都以新鲜建议开始。映射形式 `fanout: {mode: every_n, n: 3}` 也被接受，并会规范化为字符串形式。

```yaml
moa:
  presets:
    fresh:
      reference_models:
        - provider: openrouter
          model: anthropic/claude-opus-4.8
      aggregator:
        provider: openrouter
        model: openai/gpt-5.5
      fanout: per_iteration   # 顾问在每次工具迭代时刷新
```

未知或格式错误的值会回退到 `user_turn`。

:::note 默认值变更
在 2026 年 7 月之前，默认节奏为 `per_iteration`。现在默认值是 `user_turn`——成本最低、影响最小的节奏——除非按模式的基准测试证明更昂贵的默认值合理。希望恢复逐步顾问建议的预设需显式设置 `fanout: per_iteration`。
:::

### 顾问输出的隐私过滤器

顾问输出可能会将对话中的敏感数据——电子邮件、格式化电话号码、API 密钥、JWT——回显到 UI 中显示的参考区块、保存的 MoA 跟踪记录及聚合器提示中。`moa.privacy_filter`（默认关闭）可对这些位置进行脱敏：

```yaml
moa:
  privacy_filter: display   # 或：full
```

- `display` — 仅对**用户可见位置**脱敏：UI 中渲染的带标签参考区块，以及 `save_traces` 写入的记录。聚合器仍接收原始顾问文本，因此回答质量不受影响。
- `full` — 还会对注入聚合器提示的顾问文本（以及一次性 `/moa` 综合输入）进行脱敏。

凭据形态（API 密钥前缀、JWT、私钥、数据库连接字符串）由 Hermes 的中央密钥脱敏器掩盖；MoA 过滤器在此基础上增加电子邮件和明确格式电话号码的脱敏。为保留代码审查式建议，模式刻意保持保守：不会触及纯数字串、行号、时间戳、git SHA 和 IP 地址——仅匹配如 `(555) 123-4567` 或 `555-123-4567` 的带分隔符电话号码格式。

### 每槽位的推理努力程度

参考槽位和聚合器槽位也可以设置 `reasoning_effort`。当你希望同一模型以不同深度贡献，或希望聚合器比顾问参考模型思考得更深入时使用它。有效值与 Hermes 的常规推理控制一致：`none`、`minimal`、`low`、`medium`、`high`、`xhigh`、`max` 和 `ultra`。

```yaml
moa:
  presets:
    deep_review:
      reference_models:
        - provider: openai-codex
          model: gpt-5.6-sol
          reasoning_effort: low
        - provider: openai-codex
          model: gpt-5.6-sol
          reasoning_effort: xhigh
        - provider: xai-oauth
          model: grok-4.5
      aggregator:
        provider: openai-codex
        model: gpt-5.6-sol
        reasoning_effort: high
```

省略 `reasoning_effort` 可让该槽位使用提供商/Hermes 默认值。

## 终端预设管理

```bash
hermes moa list
hermes moa configure              # 更新默认预设
hermes moa configure review       # 创建或更新具名预设
hermes moa delete review
```

## 基准测试

在 HermesBench 上，一个双模型 MoA 预设——`claude-opus-4.8` 聚合器汇总 `gpt-5.5` 参考模型——得分超过任一单独运行的模型：

| 模型 | HermesBench 分数 |
|---|---|
| **Opus 聚合器（opus-4.8 + gpt-5.5 参考）— MoA** | **0.8202** |
| `anthropic/claude-opus-4.8` | 0.7607 |
| `openai/gpt-5.5` | 0.7412 |

该 MoA 配置比其最强组件（opus-4.8）高约 6 分，证实汇集第二种视角可提升困难任务的质量，而不只是对两者取平均。

## 提示缓存

MoA 的设计使**主对话的提示缓存绝不会被破坏**。选择 MoA 预设是常规模型选择：它不会在对话中途改变既往上下文、交换工具集或重建系统提示。你的对话历史、系统提示和工具 schema 保持字节稳定，因此所有其他模型依赖的缓存前缀完全保留，正如使用普通模型一样。切换到或离开 MoA 预设的缓存失效成本与任何其他 `/model` 切换相同——不会更多。

两类内部调用均能正常缓存：

- **参考模型**接收经过裁剪的确定性对话视图（系统提示和工具记录被去除——见上文循环）。因为该视图是稳定历史的稳定函数，参考模型的提示前缀会跨迭代重复并正常缓存。参考调用是简短的、没有工具的顾问调用。
- **聚合器**是实际运行的模型。参考输出作为私有指导追加到最新用户轮次的**末尾**。由于这些文本位于尾部——即完整稳定前缀（系统提示 + 既往历史）之后——不会使任何缓存前缀失效：聚合器会命中注入点以上所有内容的缓存，只有新追加的尾部是新的。这正是每个常规轮次的工作方式，每条新用户消息同样是未缓存的尾部 token。

因此，MoA 不会牺牲任一调用类型的提示缓存。它唯一的实际成本是每次迭代额外的参考调用——你付费的是多个模型视角，而不是损坏的缓存。与 Hermes 其余部分共享的长期对话前缀保持完整。

## 说明

- MoA 不再列于 `hermes tools`；没有需启用的 `moa` 工具集。
- 在预设上设置 `enabled: false` 会为该预设禁用参考扇出：聚合器独自行动，完全等同于将其作为普通模型选择。这是仪表盘和桌面设置中显示的按预设关闭开关。
- 预设的聚合器不能是另一个 MoA 预设。有意阻止递归 MoA 树。
- 某一参考模型的凭据失败不会中止该轮。Hermes 会将失败包含在参考上下文中，并继续使用成功返回的模型。
- MoA 会增加模型调用次数。一次模型迭代可涉及多次参考调用及一次聚合器调用。
