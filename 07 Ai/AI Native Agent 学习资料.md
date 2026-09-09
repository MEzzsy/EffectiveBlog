# AI Native Agent 学习资料

## 面向全栈工程师的学习路径

### 阶段 1：用 Codex 提升日常开发效率

目标：把 Codex 当作全栈 pair programmer 使用。

练习任务：

- 解释某个业务模块的数据流
- 修一个 bug
- 写一个 REST / GraphQL endpoint
- 修改一个 React、Vue 或 Astro 页面
- 补单元测试或集成测试
- 跑 lint、typecheck、test
- review 当前 diff

每次任务尽量写清楚：

```text
Goal: 要完成什么
Context: 哪些文件、模块、错误、设计稿、接口文档相关
Constraints: 遵守哪些架构、代码规范、安全要求
Done when: 什么条件满足才算完成，比如测试通过、页面截图正确、bug 不再复现
```

### 阶段 2：沉淀项目上下文

目标：减少重复解释，让 agent 更懂你的项目。

产物：

- 项目根目录的 `AGENTS.md`
- 必要时在前端、后端、脚本、数据库目录下添加更具体的 `AGENTS.md`

建议内容：

- 项目结构
- 安装和启动命令
- 测试命令
- lint 和 typecheck 命令
- API 约定
- 数据库迁移约定
- UI 组件使用规范
- 安全和权限要求
- PR review 标准

### 阶段 3：建立验证闭环

目标：让 agent 不只是生成代码，而是能验证结果。

前端闭环：

- 实现页面
- 启动 dev server
- 用浏览器检查页面
- 检查 console error
- 截图验证桌面端和移动端
- 根据截图继续修正
- 跑 Playwright 或相关 E2E 测试

后端闭环：

- 阅读 controller、service、schema、migration
- 写最小实现
- 补测试
- 跑测试
- 检查输入校验、权限、错误处理、日志、事务
- review diff

### 阶段 4：把重复任务做成 Skill

目标：把你的工作方法封装成可复用流程。

优先选择一个高频、边界清楚的任务：

- PR review
- CI 失败排查
- 页面状态补全
- API 联调检查
- issue 实现计划
- release note 生成

Skill 模板：

```md
---
name: fullstack-review
description: Review full-stack changes for correctness, tests, API compatibility, UI states, and security risks.
---

1. Inspect the changed files.
2. Identify frontend, backend, schema, and test changes.
3. Check API compatibility between frontend and backend.
4. Check loading, error, and empty states for UI changes.
5. Check validation, authorization, and error handling for backend changes.
6. Run or recommend the most relevant tests.
7. Report only actionable findings with file references.
```

### 阶段 5：接入 MCP

目标：让 agent 连接真实工作环境。

建议顺序：

1. 文档类 MCP：Context7 或官方文档 MCP
2. 浏览器类 MCP：Playwright 或 Chrome DevTools
3. GitHub MCP：issue、PR、actions
4. Sentry MCP：线上错误和日志
5. Figma MCP：设计稿到页面实现

全栈场景示例：

- 根据 GitHub issue 生成实现计划
- 根据 Figma 设计稿实现页面
- 用 Playwright 检查页面视觉和交互
- 根据 Sentry 错误定位后端异常
- 根据 PR diff 做风险 review

### 阶段 6：学习 Agent 工作流编排

目标：把单次任务升级成自动化流程。

可以用 OpenAI Agents SDK 或 LangGraph 实现：

- issue -> 需求分析 -> 实现计划 -> Codex 执行 -> 测试 -> review
- PR -> diff 分析 -> 风险检查 -> 生成 review comment
- Sentry error -> 日志分析 -> 复现路径 -> patch 建议
- API schema -> 类型生成 -> 前端表单 -> 测试

这一步不急，建议在你已经熟练使用 Codex、`AGENTS.md`、Skills、MCP 后再做。

## 4 周实践计划

### 第 1 周：Codex 基础生产力

目标：

- 用 Codex 完成 3 个真实小任务
- 练习写清楚 `Goal / Context / Constraints / Done when`
- 每次要求 Codex 跑测试和 review diff

交付物：

- 3 次真实任务记录
- 一份你觉得效果最好的任务 prompt

### 第 2 周：项目上下文沉淀

目标：

- 给常用项目写 `AGENTS.md`
- 加入前端、后端、测试、PR 规范
- 观察 Codex 是否少犯重复错误

交付物：

- 项目级 `AGENTS.md`
- 一份目录或模块说明
- 一组常用验证命令

### 第 3 周：工具链接入

目标：

- 接一个文档类 MCP
- 接一个浏览器类 MCP
- 完成一次“实现页面 -> 浏览器验证 -> 截图修正”的闭环

交付物：

- 可用的 MCP 配置
- 一次前端页面验证记录
- 一个可复用的浏览器验证 prompt

### 第 4 周：自动化一个高频流程

目标：

- 从日常工作里选一个最烦的重复任务
- 做成 Skill 或 Agents SDK / LangGraph 小工作流

候选任务：

- PR review
- CI 失败排查
- 页面状态补全
- API 联调检查
- issue 实现计划

交付物：

- 一个可复用 Skill
- 或一个最小可运行 agent workflow

## 常用 Prompt 模板

### 功能开发

```text
Goal: 实现 [功能名称]。
Context: 相关文件是 [文件/目录]，业务背景是 [说明]。
Constraints: 遵守现有架构，不引入新依赖，保持 API 兼容。
Done when: 功能可用，相关测试通过，lint/typecheck 通过，并 review 当前 diff。
```

### Bug 修复

```text
Goal: 修复 [bug 描述]。
Context: 错误日志是 [日志]，复现步骤是 [步骤]，相关模块是 [文件/目录]。
Constraints: 尽量保持改动最小，不改变无关行为。
Done when: bug 不再复现，新增或更新测试覆盖该场景，相关检查通过。
```

### 前端页面实现

```text
Goal: 实现或修改 [页面/组件]。
Context: 设计要求是 [说明]，相关组件在 [目录]。
Constraints: 遵守现有设计系统，包含 loading、error、empty state，移动端不能布局错乱。
Done when: 页面在桌面端和移动端显示正确，无 console error，相关测试通过。
```

### 后端接口实现

```text
Goal: 实现 [接口/服务]。
Context: 相关 controller/service/schema 是 [文件]。
Constraints: 保持权限校验、输入校验、错误处理和事务一致。
Done when: 接口行为符合要求，测试覆盖成功和失败路径，相关检查通过。
```

### Review

```text
Review the current diff.
Focus on correctness, regressions, missing tests, frontend/backend API mismatch, security, authorization, error handling, and edge cases.
Report findings first, ordered by severity, with file and line references.
```

## 最短路线

如果时间有限，先学这四个：

1. OpenAI Codex: https://github.com/openai/codex
2. AGENTS.md / Skills: https://github.com/openai/skills
3. MCP: https://github.com/modelcontextprotocol
4. OpenAI Agents SDK: https://github.com/openai/openai-agents-python

掌握这四个之后，再补 LangGraph、smolagents、LlamaIndex 和评估安全资料。
