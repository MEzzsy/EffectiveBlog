# 核心学习主线

1.  [01 Codex 型通用 Agent 的工作方式](01 Codex 型通用 Agent 的工作方式.md) 
2.  [02 上下文工程和 AGENTS](02 上下文工程和 AGENTS.md) 
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