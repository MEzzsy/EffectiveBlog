# AI Native Agent 学习资料与学习路径

这份资料适合从 0 到 1 系统学习 AI Native Agent。建议不要一开始就追求复杂的多 Agent 系统，而是先理解 Agent 的基本循环，再逐步进入工具调用、工作流、RAG、MCP、评测和安全。

## 推荐学习路径

### 1. Agent 基础

先理解 Agent 的核心概念：

- LLM 如何根据目标进行推理
- 工具调用如何发生
- Action / Observation 循环是什么
- Agent 与普通 Chatbot 的区别
- 什么情况下不需要 Agent

推荐资料：

- [Hugging Face AI Agents Course](https://huggingface.co/learn/agents-course/unit0/introduction)
- [smolagents](https://github.com/huggingface/smolagents)

### 2. 工具调用与最小 Agent

目标是写出一个能调用工具的最小可用 Agent，例如：

- 查询网页
- 调用本地函数
- 读取文件
- 执行简单计算
- 根据工具结果继续推理

推荐资料：

- [smolagents GitHub](https://github.com/huggingface/smolagents)
- [OpenAI Agents SDK](https://github.com/openai/openai-agents-python)

### 3. 状态机与 Agent 工作流

当 Agent 任务变复杂时，需要显式建模状态、分支、循环、人工确认和错误恢复。

重点学习：

- 有状态工作流
- 多步骤任务编排
- Human-in-the-loop
- 长运行任务
- 可恢复执行
- Agent 状态持久化

推荐资料：

- [LangGraph](https://github.com/langchain-ai/langgraph)

### 4. Agentic RAG 与知识库

学习如何让 Agent 使用外部知识，而不是只依赖模型自身记忆。

重点学习：

- 文档解析
- 向量检索
- 查询改写
- 检索结果重排
- 多轮问答中的上下文管理
- RAG 与工具调用结合

推荐资料：

- [LlamaIndex](https://github.com/run-llama/llama_index)

### 5. 多 Agent 协作

在掌握单 Agent 后，再学习多个 Agent 如何分工协作。

重点学习：

- 角色分工
- Planner / Executor 模式
- Reviewer / Critic 模式
- 多 Agent 对话
- 任务拆解与合并
- 协作失败时的恢复策略

推荐资料：

- [Microsoft AutoGen](https://github.com/microsoft/autogen)
- [CrewAI](https://github.com/crewAIInc/crewAI)

### 6. MCP 与工具生态

MCP 是 Agent 连接外部工具和数据源的重要开放协议，适合学习如何让 Agent 使用本地文件、数据库、浏览器、API、开发工具等上下文。

重点学习：

- MCP Server
- MCP Client
- Tool schema
- Resource / Prompt / Tool 的区别
- 权限与安全边界
- 如何为自己的工具写 MCP 服务

推荐资料：

- [Model Context Protocol GitHub](https://github.com/modelcontextprotocol)

### 7. 评测、安全与生产化

Agent 越能行动，风险越高。生产级 Agent 必须关注评测、可观测性、成本和安全。

重点学习：

- Agent benchmark 的局限
- 成本与效果权衡
- 可复现评测
- Prompt injection
- 工具权限控制
- 数据泄露风险
- 日志、追踪和回放

推荐资料：

- [AI Agents That Matter](https://arxiv.org/abs/2407.01502)
- [Security of AI Agents](https://arxiv.org/abs/2406.08689)

## 资料清单

| 资料 | 类型 | 适合阶段 | 说明 |
| --- | --- | --- | --- |
| [Hugging Face AI Agents Course](https://huggingface.co/learn/agents-course/unit0/introduction) | 免费课程 | 入门到进阶 | 系统学习 Agent 理论、工具调用和实践项目 |
| [smolagents](https://github.com/huggingface/smolagents) | 开源框架 | 入门 | 轻量级 Agent 框架，适合理解最小 Agent 实现 |
| [LangGraph](https://github.com/langchain-ai/langgraph) | 开源框架 | 进阶 | 适合学习有状态、可恢复、生产级 Agent 工作流 |
| [LlamaIndex](https://github.com/run-llama/llama_index) | 开源框架 | 进阶 | 适合学习 Agentic RAG 和知识库 Agent |
| [Microsoft AutoGen](https://github.com/microsoft/autogen) | 开源框架 | 进阶 | 适合学习多 Agent 对话和协作 |
| [CrewAI](https://github.com/crewAIInc/crewAI) | 开源框架 | 进阶 | 适合快速构建角色型多 Agent 工作流 |
| [Model Context Protocol](https://github.com/modelcontextprotocol) | 开放协议 | 进阶到生产 | 学习 Agent 如何连接工具、数据源和外部上下文 |
| [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) | 开源 SDK | 入门到进阶 | 学习轻量级多 Agent 工作流设计 |
| [AI Agents That Matter](https://arxiv.org/abs/2407.01502) | 论文 | 进阶 | 理解 Agent 评测、成本、可复现性和真实价值 |
| [Security of AI Agents](https://arxiv.org/abs/2406.08689) | 论文 | 进阶到生产 | 学习 Agent 安全风险、攻击面和防护思路 |

## 最短学习路线

如果时间有限，可以按下面顺序学习：

1. [Hugging Face AI Agents Course](https://huggingface.co/learn/agents-course/unit0/introduction)
2. [smolagents](https://github.com/huggingface/smolagents)
3. [LangGraph](https://github.com/langchain-ai/langgraph)
4. [Model Context Protocol](https://github.com/modelcontextprotocol)
5. [AI Agents That Matter](https://arxiv.org/abs/2407.01502)

## 实践项目建议

### 项目 1：个人资料问答 Agent

目标：

- 读取本地 Markdown / PDF / 网页资料
- 建立索引
- 回答问题时引用来源
- 支持多轮追问

建议技术：

- LlamaIndex
- LangGraph

### 项目 2：网页研究 Agent

目标：

- 接收一个研究主题
- 自动搜索资料
- 摘要关键观点
- 输出结构化研究笔记
- 标注来源链接

建议技术：

- LangGraph
- OpenAI Agents SDK
- MCP browser / search tools

### 项目 3：代码仓库助手 Agent

目标：

- 读取一个代码仓库
- 回答架构问题
- 定位 bug 相关文件
- 给出修改建议
- 生成测试计划

建议技术：

- MCP filesystem
- LangGraph
- LlamaIndex

### 项目 4：多 Agent 内容生产流

目标：

- Planner 负责选题和大纲
- Researcher 负责资料收集
- Writer 负责初稿
- Reviewer 负责审稿
- Editor 负责最终润色

建议技术：

- AutoGen
- CrewAI
- LangGraph

## 学习提醒

- 不要只看框架 demo，要关注 Agent 为什么会失败。
- 工具调用比多 Agent 更基础，先把工具边界学清楚。
- RAG 是很多真实 Agent 的核心能力。
- MCP 值得尽早学习，它会影响你如何设计 Agent 的工具生态。
- 生产级 Agent 的关键不是“看起来聪明”，而是可控、可复现、可观测、可评测。
