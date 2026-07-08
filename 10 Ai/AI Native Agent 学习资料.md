# AI Native Agent 学习资料

## 学习目标

这份路径面向全栈工程师，目标不是研究 LLM 底层、训练、微调或调参，而是学习如何把 AI Native Agent 用到真实开发工作中，提升日常编码、调试、测试、review、文档和联调效率。

你需要重点掌握的是：

- 如何把需求拆成 agent 能执行的任务
- 如何给 agent 足够的项目上下文
- 如何让 agent 安全地读代码、改代码、跑命令、跑测试
- 如何把重复工作沉淀成 `AGENTS.md`、Skills、MCP 或自动化流程
- 如何让 agent 参与前端、后端、测试、review、CI、线上问题排查

一句话总结：你不是要成为 Agent 框架专家，而是要成为会管理 Agent 的全栈工程师。

## 不需要优先学习的内容

这些内容可以暂时跳过：

- LLM 训练、微调、LoRA、量化
- 模型 benchmark 细节
- temperature、top_p 等采样参数深挖
- 从零实现 planner、memory、tool router
- 复杂多 agent 系统的大型 demo

## 核心学习主线

建议按这个顺序学习：

1. Codex 型通用 agent 的工作方式
2. 上下文工程和 `AGENTS.md`
3. 工具调用、sandbox、approval 和安全边界
4. Skills：把重复流程封装成可复用工作流
5. MCP：让 agent 连接外部工具和真实工作环境
6. 浏览器验证、测试、CI、review 的闭环
7. Agents SDK / LangGraph：把高频工作流自动化

## 推荐资料

### 1. OpenAI Codex

链接：

- https://github.com/openai/codex
- https://developers.openai.com/codex

Codex 是最适合作为通用软件工程 agent 的学习样本。它能在本地或云端读代码、修改文件、运行命令、做 review、调用工具，并且有 sandbox、approval、workspace 权限等安全机制。

学习重点：

- Codex 如何读取项目上下文
- 如何写清楚任务目标、约束和完成标准
- 如何让 agent 先计划再执行
- 如何让 agent 跑测试、检查 diff、review 修改
- 如何通过 sandbox 和 approval 控制风险

建议练习：

- 让 Codex 解释一个模块的数据流
- 让 Codex 修一个小 bug
- 让 Codex 写一个 API endpoint
- 让 Codex 改一个前端页面
- 让 Codex 为改动补测试并跑测试
- 让 Codex review 当前 diff

### 2. AGENTS.md

链接：

- https://agents.md
- https://github.com/openai/codex

`AGENTS.md` 可以理解为给 agent 看的项目说明书。它适合记录项目结构、启动命令、测试命令、代码规范、PR 规范和禁止事项。

全栈项目里建议写入：

- 前端目录、后端目录、共享类型目录
- 本地启动命令
- lint、test、typecheck 命令
- API 规范
- 数据库迁移规则
- UI 组件规范
- PR review 标准
- 禁止事项，比如不要直接改生产配置、不要绕过权限校验

学习重点：

- 把重复解释的项目上下文沉淀下来
- 把反复出现的 review 意见写成规则
- 把不同目录的特殊规则放到更近的 `AGENTS.md`

### 3. OpenAI Skills Catalog

链接：

- https://github.com/openai/skills

Skills 是把重复工作流封装给 Codex 使用的方式。它通常由 `SKILL.md`、说明、参考资料和可选脚本组成。

适合全栈工程师沉淀成 Skill 的任务：

- 根据 issue 实现功能并补测试
- 检查接口变更是否同步前端类型
- 为页面补 loading、error、empty state
- review 当前 diff，重点看安全、性能、边界条件
- 根据后端 schema 生成前端表单
- 排查 CI 失败
- 写 release note
- 根据 PR diff 生成高质量 PR 描述

学习重点：

- Skill 的触发描述怎么写
- 一个 Skill 只聚焦一个任务
- 先用说明沉淀流程，必要时再加脚本
- 把团队共识变成 agent 可复用的执行流程

### 4. Model Context Protocol MCP

链接：

- https://github.com/modelcontextprotocol
- https://modelcontextprotocol.io

MCP 是 agent 连接外部工具和上下文的开放协议。它可以让 Codex 或其他 agent 访问 GitHub、Figma、浏览器、文档库、Sentry、数据库、内部系统等。

全栈工程师优先关注的 MCP：

- GitHub：issue、PR、review、actions
- Playwright / Chrome DevTools：调试页面、截图、检查 DOM
- Figma：根据设计稿实现页面
- Sentry：根据线上报错定位问题
- Context7 / Docs：查询最新框架文档
- 数据库或内部 API：查询业务上下文

学习重点：

- MCP server 暴露 tools、resources、prompts
- agent 通过 MCP 获取外部上下文或执行动作
- 对 side effect 工具设置审批和权限边界
- MCP 常常和 Skills 配合使用：Skill 定义流程，MCP 提供工具

### 5. OpenAI Agents SDK

链接：

- https://github.com/openai/openai-agents-python
- https://openai.github.io/openai-agents-python/

OpenAI Agents SDK 适合学习现代 agent 工作流的工程抽象，包括 tools、handoffs、guardrails、sessions、tracing、human-in-the-loop 等。

学习重点：

- agent 如何配置 instructions 和 tools
- 如何把 agent 当作工具调用
- 如何做 handoff
- 如何加 guardrails
- 如何用 tracing 调试 agent 运行过程
- 如何把 Codex 作为 MCP server 接入更大的工作流

适合做的小项目：

- issue -> 分析 -> 生成实现计划 -> Codex 执行 -> 测试 -> review
- PR diff -> 风险扫描 -> 生成 review comment
- Sentry error -> 找相关代码 -> 复现建议 -> patch
- API schema -> 前端类型 -> 表单 -> 测试

### 6. LangGraph

链接：

- https://github.com/langchain-ai/langgraph
- https://docs.langchain.com/oss/python/langgraph/

LangGraph 适合学习长流程、有状态、可恢复、可观测的 agent 工作流。它更偏生产级 agent 编排。

学习重点：

- stateful agent
- durable execution
- human-in-the-loop
- long-term / short-term memory
- 分支、子图、失败恢复
- agent observability

适合在掌握 Codex、AGENTS.md、Skills、MCP 之后再学。

### 7. Hugging Face AI Agents Course

链接：

- https://huggingface.co/learn/agents-course/unit0/introduction

这是免费的 agent 课程，覆盖 agent 基础、工具、动作/观察循环、smolagents、LlamaIndex、LangGraph、Agentic RAG 和最终项目。

你的学习方式建议：

- Unit 1 看 agent 基础，但跳过 LLM 细节
- Unit 2 重点看 smolagents、LlamaIndex、LangGraph 怎么组织工具和工作流
- Unit 3 看 Agentic RAG 的应用场景
- Bonus 里的 fine-tuning 可以跳过
- Bonus 里的 observability 和 evaluation 值得看

### 8. smolagents

链接：

- https://github.com/huggingface/smolagents

`smolagents` 适合理解最小 agent 实现。它强调 agents that think in code，支持 code agent、MCP、沙箱执行、多模型提供商。

学习重点：

- 一个简单 agent 的最小结构
- tools 如何被 agent 调用
- code agent 和普通 tool-calling agent 的差异
- 为什么执行代码必须考虑 sandbox

### 9. LlamaIndex

链接：

- https://github.com/run-llama/llama_index
- https://docs.llamaindex.ai

LlamaIndex 适合学习文档、知识库、RAG 和 agent 的结合。如果你的工作涉及内部文档、接口文档、业务知识库、日志分析，它很有价值。

学习重点：

- document agent
- agentic RAG
- 索引、检索、工具调用如何组合
- 如何让 agent 基于私有知识库回答和执行任务

### 10. 进阶论文和评估资料

建议后期再看：

- AI Agents That Matter: https://arxiv.org/abs/2407.01502
- Security of AI Agents: https://arxiv.org/abs/2406.08689

学习重点：

- 不只看 benchmark 分数
- 关注成本、可复现性、过拟合和真实可用性
- 关注 prompt injection、工具权限、数据泄露、越权操作

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
