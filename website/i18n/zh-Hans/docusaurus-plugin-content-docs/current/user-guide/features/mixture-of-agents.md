---
sidebar_position: 7
title: "Mixture of Agents"
description: "创建具名的 MoA 预设，它们在 Mixture of Agents 提供商下显示为可选择的模型"
---

# Mixture of Agents

Mixture of Agents（混合智能体）是一种虚拟模型提供商。每个具名的 MoA 预设都会在 `moa` 提供商下显示为一个可选择的模型。

当你选择某个 MoA 预设时，该预设的聚合器（aggregator）就是实际的运行模型。它负责撰写助手的回复并发起工具调用。参考模型（reference models）先运行，为聚合器提供分析依据。

当一项困难的任务受益于多个模型的视角、但仍需要 Hermes 正常的智能体循环——工具调用、后续迭代、中断、对话持久化以及与任何其他消息相同的会话上下文——时，请使用 MoA。

## 选择 MoA 预设作为你的模型

你可以通过正常的模型选择界面来选择预设：

```bash
/model default --provider moa
/model review --provider moa
```

MoA 预设可以在 **每个 Hermes 界面** 上被选择，因为 MoA 是模型系统中的一个普通提供商：

- **CLI / 网关 / TUI `/model`** — `/model <预设名> --provider moa`，或者不加预设名使用 `/model --provider moa` 以使用默认预设。当名称与已配置的预设完全匹配时，仅使用 `/model <预设名>` 也同样有效。
- **`hermes model` 和仪表盘模型选择器** — 会出现一个 `Mixture of Agents` 提供商行，其下列出你的预设名称作为模型。
- **桌面 GUI 应用** — 模型下拉菜单中会显示 `MoA presets` 部分；选择其中一个（`MoA: <预设名>`）会将活跃模型切换为该预设。桌面的设置面板也可以创建和编辑预设。

因此，配置好的预设会在你选择任何其他模型的地方出现。

## 斜杠命令快捷方式

`/moa` 是一种一次性便利糖。它通过 **默认** MoA 预设运行单次提示，然后恢复你之前使用的模型：

```bash
/moa design and implement a migration plan for this flaky test cluster
```

Hermes 会暂时切换到默认 MoA 预设执行那一轮对话，发送提示，之后再恢复你之前的模型。整个参数就是提示内容——`/moa` 不再将其解释为预设名称。

```bash
/moa
```

单独使用 `/moa`（不带提示）仅显示用法说明。

要 **切换** 到某个 MoA 预设用于会话剩余部分，请从模型选择器中选中它——MoA 预设会在每个模型选择界面上出现在 `Mixture of Agents` 提供商下（见上文）。`/moa` 故意不切换模型，这样普通的提示就不会意外改变你的模型。

## 在智能体循环中的工作方式

当选中 `moa` 提供商进行每次主模型调用时，Hermes 会：

1. 按名称解析所选预设；
2. 运行配置的参考模型，但不附带工具 schema（它们只接收对话的用户/助手文本——不包含 Hermes 系统提示或工具调用记录——因此参考调用保持廉价，并避免了严格提供商的拒绝）；
3. 将参考输出追加为聚合器的私密上下文；
4. 使用正常的 Hermes 工具 schema 调用配置的聚合器；
5. 将聚合器的回复视为真实的模型回复；
6. 如果聚合器调用工具，Hermes 正常执行这些工具；
7. 在下一个模型迭代中，对更新后的对话（包括工具结果）再次执行相同的 MoA 流程。

由于 MoA 是通过正常的模型系统选择的，它可以自动与 `/goal`、网关会话、TUI 会话和桌面聊天组合使用。

## 配置预设

你可以通过以下方式配置具名的 MoA 预设：

- 仪表盘 → Models → Model Settings → Mixture of Agents
- 桌面应用 → Settings → Model → Mixture of Agents
- `hermes moa configure [名称]`
- `config.yaml`

配置存储显式的提供商/模型对，因此你可以混合使用不同的提供商，并让同一个提供商提供多个模型：

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
      # 可选：固定采样温度。省略时（默认情况），
      # temperature 不被发送，每个模型使用其提供商的默认值——
      # 与单模型 Hermes 智能体的行为相同。
      # reference_temperature: 0.6
      # aggregator_temperature: 0.4
      max_tokens: 4096
      enabled: true
```

默认预设：

- 参考模型：`openai-codex:gpt-5.5`
- 参考模型：`openrouter:deepseek/deepseek-v4-pro`
- 聚合器/实际运行模型：`openrouter:anthropic/claude-opus-4.8`

### 使用 `reference_max_tokens` 调节顾问速度

每一轮对话中，MoA 并行运行参考模型（顾问），然后聚合器开始行动。顾问生成是每轮对话的主要延迟因素——实际耗时与顾问生成的 token 数量密切相关，因为本轮对话要等待最慢的顾问完成写作。默认情况下，顾问 **没有上限**（`reference_max_tokens` 未设置），因此它们可能会写出长篇的论文式建议。

在预设中设置 `reference_max_tokens` 可以限制顾问的输出，让其提供简洁的建议。聚合器只需要每个顾问判断的要点，因此设置上限（例如 `600`）可以显著缩短每轮对话的实际时间，而对质量影响很小。它只限制 **顾问本身**——实际聚合器的输出（用户可见的回答）永远不会被限制。

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
      reference_max_tokens: 600   # 简洁建议 → 更快的对话轮次
```

将其留空（或设为 `0`/空白）可保持之前无上限的行为。

### 每槽位推理深度

参考模型和聚合器槽位也可以设置 `reasoning_effort`。当你希望同一个模型以不同的深度贡献、或者希望聚合器比参考顾问思考得更深入时，可以使用此设置。有效值与 Hermes 正常的推理控制一致：`none`、`minimal`、`low`、`medium`、`high`、`xhigh` 和 `max`。

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

省略 `reasoning_effort` 可以让该槽位使用提供商/Hermes 的默认值。

## 终端预设管理

```bash
hermes moa list
hermes moa configure              # 更新默认预设
hermes moa configure review       # 创建或更新具名预设
hermes moa delete review
```

## 基准测试

在 HermesBench 上，一个双模型 MoA 预设——以 `claude-opus-4.8` 聚合 `gpt-5.5` 参考——得分超过任一单独运行的模型：

| 模型 | HermesBench 分数 |
|---|---|
| **Opus 聚合器（opus-4.8 + gpt-5.5 参考）— MoA** | **0.8202** |
| `anthropic/claude-opus-4.8` | 0.7607 |
| `openai/gpt-5.5` | 0.7412 |

MoA 配置比其最强的组件（opus-4.8）高出约 6 个点，证实聚合第二个视角能提升困难任务的质量，而不仅仅是取两者的平均值。

## 提示缓存

MoA 的设计确保 **主对话的提示缓存永远不会被破坏**。选择 MoA 预设是一种正常的模型选择：它不会改变过去的上下文、不会交换工具集、也不会在对话中间重建系统提示。你的对话历史、系统提示和工具 schema 保持字节稳定，因此其他模型依赖的缓存前缀被完整保留——就像普通模型一样。切换到 MoA 预设或从中切出的缓存失效代价与任何其他 `/model` 切换相同——不会更多。

两种内部调用类型都能正常缓存：

- **参考模型** 接收一个修剪过的、确定性的对话视图（系统提示和工具记录被剥离——参见上面的循环）。由于该视图是稳定历史的稳定函数，参考模型的提示前缀在各轮迭代中重复出现并正常缓存。参考调用是短小的、不带工具的顾问调用。
- **聚合器** 是实际的运行模型。参考输出作为私密指导被追加到最新用户轮次的 **末尾**。由于这些文本位于尾部——在完整的稳定前缀（系统提示 + 之前的历史）之下——它不会使任何缓存的前缀失效：聚合器在注入点之上的所有内容都能命中缓存，只有新追加的尾部是新的。这正是每个正常轮次的行为方式——每个新用户消息也是未缓存的尾部 token。

因此，MoA 不会牺牲任何一种调用类型的提示缓存。它唯一的实际成本是每轮迭代中额外的参考调用——你为多个模型视角付费，而不是为破碎的缓存付费。与 Hermes 其他部分共享的长对话前缀完全保持完整。

## 备注

- MoA 不再列在 `hermes tools` 下；没有需要启用的 `moa` 工具集。
- 对预设设置 `enabled: false` 会禁用该预设的参考扇出：聚合器单独行动，就像你直接将其选为普通模型一样。这是在仪表盘和桌面设置中公开的按预设关闭开关。
- 预设的聚合器不能是另一个 MoA 预设。递归 MoA 树被有意阻止。
- 某个参考模型的凭据失败不会中止该轮对话。Hermes 将失败信息包含在参考上下文中，并继续使用成功返回的模型。
- MoA 会增加模型调用数量。单次模型迭代可能涉及多次参考调用加上一次聚合器调用。
