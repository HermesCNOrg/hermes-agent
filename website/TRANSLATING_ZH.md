# Hermes 简体中文文档维护

本仓库是完整的 `NousResearch/hermes-agent` Fork。核心原则是：**通过正常 Git merge 跟随整个上游，但本 Fork 自己维护的内容只位于文档站点，主要是 `website/i18n/zh-Hans/`。**

## 分支与同步

- `upstream`：`https://github.com/NousResearch/hermes-agent.git`
- `origin`：中文 Fork `HermesCNOrg/hermes-agent`（远程仓库创建后配置）
- `main`：中文 Fork 主分支
- 自动化分支：`automation/daily-upstream-zh-hans`
- 自动化工作流：`.github/workflows/zh-docs-sync.yml`

工作流每天北京时间 10:17（UTC 02:17）运行，也支持手动触发。它不是复制 `website/docs`，而是在一个持续更新的自动化分支中完整合并 `upstream/main`，随后用 `website/scripts/zh_docs.py refresh` 对比每篇英文文档的 SHA-256。

只有 `website/docs/**/*.md` 或 `*.mdx` 在本次上游范围中新增、修改或重命名时，才调用 Hermes 翻译，而且只翻译本次变化的文件。删除英文页面时不调用翻译，对应旧中文会归档。完成状态验证和中文 Docusaurus 构建后，工作流创建或更新一个 **Draft PR**；不会启用自动合并，必须由 Ray 人工确认后再转为 Ready 并合并。

## 翻译状态

状态文件：`website/translation/zh-Hans-state.json`

| 状态 | 含义 |
|---|---|
| `missing` | 没有中文译文 |
| `needs_update` | 英文发生变化，中文仍对应旧版本 |
| `needs_review` | 从上游导入的既有中文，尚未按本流程审核 |
| `draft` | 中文被编辑，尚未人工审核 |
| `approved` | 当前英文版本对应的中文已人工审核 |

常规人工队列默认不包含自动生成的 Skills 文档，便于先处理核心指南；每日同步工作流则使用 `--include-generated`，确保本次确实发生变化的英文文档都被处理。

## 翻译规范

- 英文 `website/docs/` 是功能事实来源，不添加原文没有的能力或结论。
- 不翻译命令、代码、配置键、环境变量、文件路径、URL、锚点、产品名。
- 保留 front matter 键、MDX/JSX、admonition 类型、代码围栏和标题层级。
- 使用自然简体中文，不逐词硬译；`you` 通常译为“你”。
- `Hermes Agent`、`Hermes`、`Nous Research`、`MCP`、`Docusaurus` 保留英文。
- AI 生成内容只能标为 `draft`，必须人工逐篇核对后才能 `approved`。

## 常用命令

```bash
# 更新翻译状态并生成队列
python3 website/scripts/zh_docs.py refresh
python3 website/scripts/zh_docs.py queue --limit 20

# 预览或执行 Hermes 翻译
python3 website/scripts/zh_docs.py translate --limit 3 --dry-run
python3 website/scripts/zh_docs.py translate --limit 3
python3 website/scripts/zh_docs.py refresh

# 人工审核后批准
python3 website/scripts/zh_docs.py mark --reviewer <github-user> \
  getting-started/quickstart.md

# 验证
python3 -m unittest website/scripts/tests/test_zh_docs.py -v
python3 website/scripts/zh_docs.py validate
cd website && npm ci
NODE_OPTIONS='--max-old-space-size=1536' \
  npx docusaurus build --locale zh-Hans --no-minify
```

## 合并边界

中文维护 PR 允许修改：

- `website/i18n/zh-Hans/**`
- `website/translation/**`
- `website/TRANSLATING_ZH.md`
- `website/scripts/zh_docs.py` 及其测试
- 中文同步相关 GitHub Actions

除正常合并 `upstream/main` 带来的变化外，不在中文维护提交中修改 Hermes 核心代码。
