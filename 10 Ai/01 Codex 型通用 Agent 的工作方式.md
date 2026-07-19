学习目标：理解 Codex 这类通用软件工程 agent 如何接收任务、获取上下文、调用工具、修改代码、验证结果，并在权限边界内工作。

> 资料来源
>
> 本文根据以下网络资料翻译和整理，访问时间：2026-07-07。
>
> - OpenAI Codex 官方文档：https://developers.openai.com/codex
> - OpenAI Codex 开源仓库：https://github.com/openai/codex
> - Codex 官方手册：https://developers.openai.com/codex/codex-manual.md
> - AGENTS.md 说明：https://agents.md
>
> 说明：下面不是逐字全文翻译，而是面向全栈工程师学习的中文整理版。重点保留 Codex 的工作模型、上下文、线程、工具调用、验证、安全和可复用工作流。
>

# Codex 是什么

Codex 是 OpenAI 面向软件开发的 coding agent。它不只是聊天助手，而是能在一个真实工作区里读文件、理解代码、修改代码、运行命令、执行测试、调试错误、review diff，并根据你的反馈继续迭代。

# 🌟Codex 的基本工作循环：Agent Loop

> **资料来源**
>
> 本文根据以下 OpenAI 官方资料整理，访问时间：2026-07-12。
>
> - [OpenAI：Unrolling the Codex agent loop](https://openai.com/index/unrolling-the-codex-agent-loop/)
> - [OpenAI：Codex CLI](https://developers.openai.com/codex/cli)
> - [OpenAI：Codex Configuration Reference](https://developers.openai.com/codex/config-reference)
> - [OpenAI：Subagents](https://developers.openai.com/codex/concepts/multi-agents)
> - [OpenAI API：Responses API](https://developers.openai.com/api/docs/guides/responses-vs-chat-completions)
>
> 说明：OpenAI 官方把这一机制称为 Agent Loop，而不是 ReAct 模式。本文会用 ReAct 帮助理解“推理、行动、观察交替”的思想，但不会把两者视为完全相同的产品名称或实现。

Codex 收到 prompt 后，会进入一个 agent loop。

## Agent Loop 是什么

普通聊天模型的典型工作方式是：接收一段输入，然后生成一段文本。Codex 不仅能生成文本，还能搜索代码、读取文件、运行命令、修改工作区、调用外部工具，并根据真实执行结果继续工作。

把这些能力串起来的控制过程就是 Agent Loop。可以先把它简化成下面的循环：

```text
接收目标和约束
      ↓
理解当前状态并决定下一步
      ↓
直接回答，或者请求一次工具调用
      ↓
执行工具并获得结果
      ↓
把结果加入当前上下文
      ↓
根据新状态继续判断
      ↓
达到完成条件后返回最终结果
```

这里最重要的不是“模型一次想出了完整答案”，而是模型可以通过工具不断接触外部事实，并利用新事实修正后续行动。

例如，用户要求“修复登录接口偶发的 500 错误”。Codex 一开始通常不知道根因，只能先搜索入口、阅读日志和运行测试。第一次测试结果会影响下一步：如果发现数据库超时，就继续追踪连接池；如果发现空指针，就转向输入边界；如果无法复现，就需要构造更接近生产环境的条件。

## 一次循环包含什么

从概念上看，一次 Agent Loop 迭代包含四个部分。

### 当前状态

当前状态是模型此刻能够使用的信息，包括：

- 用户目标、约束和完成标准。
- 当前任务中的历史消息。
- 已经读取的代码和文档。
- 已执行命令的输出。
- 测试、构建、日志和浏览器结果。
- `AGENTS.md`、Skill 等持久或可复用指导。
- 当前可用的工具及其参数说明。
- Sandbox、Approval 等权限限制。

模型并不是直接“看见整台电脑”。只有进入上下文的信息和工具暴露出来的能力，才属于它的当前状态。

### 决策

模型根据当前状态判断下一步应该做什么。例如：

- 先搜索某个符号。
- 阅读一个配置文件。
- 运行最小相关测试。
- 修改一个函数。
- 请求联网或更高权限。
- 询问一个无法从项目中发现的关键需求。
- 在证据充分时结束任务。

这里的“决策”不等于向用户展示完整的私有思维链。对用户真正有用的是可检查的信息，例如当前假设、准备采取的动作、工具结果、关键依据和验证结论。

### 行动

如果模型需要接触环境，它会输出结构化的工具调用，而不是假装已经执行了操作。常见行动包括：

- 使用文件搜索工具定位代码。
- 读取文件或 Git diff。
- 调用 shell 运行测试、构建或静态检查。
- 使用补丁工具编辑文件。
- 使用浏览器验证页面行为。
- 通过 MCP 或插件访问 GitHub、文档库等外部系统。

工具调用通常包含工具名称和参数。Codex Harness 负责检查调用、执行工具，并把结果返回给模型。

### 观察

观察是工具执行后返回的真实结果，例如：

- 搜索到了哪些文件和符号。
- 文件的实际内容。
- 命令的退出码和标准输出。
- 测试通过或失败的详情。
- 编译器和类型检查器给出的错误。
- 浏览器中的 DOM、截图、控制台和网络状态。
- 工具调用被 Sandbox 拒绝或等待用户批准。

观察会改变下一轮的当前状态。模型应根据观察调整路线，而不是忽略结果继续执行原来的猜测。

## Codex Agent Loop 的运行原理

OpenAI 官方对 Codex Agent Loop 的描述可以抽象为以下伪代码：

```text
context = build_initial_context(user_prompt, instructions, tools, workspace_state)

while true:
    output = call_model(context)

    if output contains tool_call:
        result = execute_tool_under_policy(output.tool_call)
        context.append(output.tool_call)
        context.append(result)
        continue

    final_response = output
    break
```

真实实现还需要处理并行工具、流式输出、审批、超时、错误恢复、上下文压缩和任务中断等问题，但核心结构仍然是“模型输出工具请求，Harness 执行，再把结果反馈给模型”。

### Harness 与模型的分工

Codex 不只是一个模型名称，也包含承载模型运行的软件系统。理解 Agent Loop 时，可以把它分成两层：

- 模型负责理解任务、选择工具、生成参数、根据结果调整行动并判断何时结束。
- Harness 负责构造上下文、提供工具、真正执行调用、实施权限控制、记录结果并驱动下一次模型推理。

模型本身不会直接运行 shell，也不会直接写入磁盘。真正改变环境的是 Harness 所执行的工具调用。

### 初始上下文如何构造

任务开始时，Codex 会把多类信息组织成模型输入，主要包括：

- Instructions：系统和开发者级指导、项目约定以及当前权限说明。
- Tools：模型当前可以调用的工具定义。
- Input：用户消息、附件、图片、文件内容和任务历史。

在本地 Codex 中，项目的 `AGENTS.md`、配置、Sandbox 和 Approval 规则也会影响模型看到的指令或实际可执行边界。

这意味着 Agent Loop 的表现不仅取决于模型能力，还取决于上下文是否准确、工具是否合适、权限是否足够以及完成标准是否明确。

### 工具调用如何形成闭环

假设模型决定运行测试，它不会只输出自然语言“我要运行测试”，而是生成类似下面的结构化请求：

```json
{
  "tool": "shell",
  "arguments": {
    "command": "npm test -- login"
  }
}
```

Harness 执行后可能返回：

```text
exit_code: 1
LoginService.test.ts: expected 401, received 500
TypeError: Cannot read properties of undefined
```

这个结果被追加到上下文中。下一次推理时，模型不再只知道“登录有错误”，而是获得了具体失败位置、期望值和异常类型，于是可以读取对应测试及实现代码。

工具结果是 Agent Loop 中连接“语言推理”和“真实环境”的桥梁。



## Agent Loop 为什么有效

### 用外部事实降低猜测

模型的已有知识不能替代当前仓库、当前依赖和当前运行状态。Agent Loop 允许模型通过搜索、测试和日志获取实时事实，从而减少只凭记忆回答造成的错误。

### 把大问题转化成小反馈

复杂任务通常无法一步完成。Agent Loop 可以把任务拆成多个可验证动作：

```text
定位入口
→ 建立假设
→ 运行最小实验
→ 修改代码
→ 运行相关测试
→ 检查完整 diff
```

每一步都能产生反馈，使错误更早暴露。

### 允许根据结果改变计划

静态计划容易建立在错误假设上。Agent Loop 可以在执行中更新认识。例如，原计划修改前端状态管理，但测试证明后端没有持久化数据，后续行动就应该转向后端，而不是机械完成原计划。

### 让“完成”可以被验证

软件工程任务的主要产出通常不是最终文字，而是代码、配置、测试和运行状态。Agent Loop 能在结束前执行验证，将“我认为已经完成”转化为“相关测试、类型检查和复现步骤已经通过”。

## Agent Loop 与 ReAct 的关系

ReAct 通常表示 Reasoning and Acting，即推理与行动交替进行：

```text
Reason → Act → Observe → Reason → Act → Observe
```

Codex Agent Loop 与这个思想非常接近，因为它也会在模型推理、工具行动和环境观察之间循环。因此，可以说 Codex 默认运行的是一种 ReAct 风格的工具驱动 Agent。

但要注意三个区别：

1. Codex 官方产品中没有名为 `/react` 的命令，也没有 `react = true` 配置项。
2. OpenAI 官方使用的名称是 Agent Loop，不保证它严格复现某篇 ReAct 论文的提示格式或内部轨迹。
3. 用户不需要、也不应要求输出完整私有思维链；应关注可验证的行动、结果和关键依据。

因此，更准确的表达是：

> Codex 默认是工具驱动的迭代式 Agent，其行为可以用 ReAct 思想理解，但 ReAct 不是 Codex 中需要开启的正式模式。

## Agent Loop 与 Plan-and-Execute 的关系

Agent Loop 解决的是“如何持续行动和反馈”，Plan-and-Execute 解决的是“如何组织一个较长任务”。二者不是互斥关系。

### Default 模式

在 Default 模式下，Codex 可以直接探索、修改和验证。它可能在执行过程中维护任务清单，但主要目标是完成任务，而不只是输出计划。

### Plan 模式

在 Codex CLI 中可以使用 `/plan` 进入 Plan 模式。这个阶段适合：

- 阅读代码和收集事实。
- 澄清需求。
- 分析影响范围和依赖关系。
- 制定实施步骤、验证方式和回滚方案。

计划确认后，再回到执行阶段完成修改。

### 两者如何组合

一个完整的 Plan-and-Execute 工作流可以表示为：

```text
Plan 阶段
  Agent Loop：读取 → 搜索 → 提问 → 更新计划
        ↓
计划确认
        ↓
Execute 阶段
  Agent Loop：修改 → 测试 → 观察 → 修正 → 验证
```

即使先制定了计划，执行阶段仍然需要 Agent Loop。计划提供全局方向，循环负责处理执行中出现的新事实。



## Agent Loop 与多 Agent 的关系

多 Agent 是在单个 Agent Loop 之上增加并行编排。主 Agent 可以把相互独立的任务交给多个子 Agent，每个子 Agent 都运行自己的循环，最后由主 Agent 收集结果。

```text
主 Agent Loop
    ├── 子 Agent A：搜索安全问题
    ├── 子 Agent B：检查测试缺口
    └── 子 Agent C：分析性能风险
                 ↓
主 Agent 汇总、去重、核验并输出结论
```

它适合代码库探索、PR 多维审查、日志分片分析等可并行工作。多个 Agent 同时修改同一文件则容易产生冲突，因此并行 Agent 更适合读多写少、责任边界清晰的子任务。

多 Agent 没有替代 Agent Loop。它只是让多个 Loop 并行运行，并增加了任务分解、消息传递、等待和结果合并等编排工作。



# Prompt 决定任务边界

Codex 官方建议，一个好的任务说明最好包含四部分：

```text
Goal: 你要它完成什么
Context: 哪些文件、目录、错误、文档、设计稿、日志和背景相关
Constraints: 它必须遵守哪些架构、规范、安全要求和限制
Done when: 什么条件满足才算完成
```

中文模板：

```text
Goal: 修复设置页保存后刷新丢失的问题。

Context:
- 复现步骤：打开 /settings，切换 Enable alerts，点击 Save，刷新后状态恢复原样。
- 相关目录：src/pages/settings、src/api/settings、tests/settings。

Constraints:
- 不改变现有 API shape。
- 尽量保持改动最小。
- 如果需要改后端，必须保留现有权限校验。

Done when:
- bug 不再复现。
- 添加或更新回归测试。
- 运行相关测试、lint、typecheck。
- 最后 review diff，指出风险。
```

为什么这很重要：

- `Goal` 控制方向。
- `Context` 减少 agent 乱找文件。
- `Constraints` 防止过度重构或破坏架构。
- `Done when` 给 agent 一个可验证的停止条件。

# 🌟Codex 如何使用上下文

Codex 的上下文来自几个来源：

- 你的 prompt。
- 你显式提到的文件、目录、日志、截图或错误信息。
- IDE 中打开的文件或选中的代码。
- 它自己通过工具读取到的文件内容。
- 它运行命令得到的输出。
- 当前 thread 里已经发生过的对话、计划、工具调用和结果。
- `AGENTS.md` 等持久项目指导。
- MCP、Skills、浏览器、GitHub、Figma、Sentry 等外部工具。

一个重要限制是：所有上下文都要放进模型的上下文窗口。长任务中，Codex 可能会压缩上下文，把重要信息摘要保留下来，丢弃较不重要的细节。

你的实践原则：

- 不要只说“修一下这个 bug”，要给复现步骤。
- 不要只说“优化这个页面”，要给目标指标或截图。
- 不要只说“写测试”，要指出测试范围和边界场景。
- 如果项目大，要告诉它先读哪些目录或文件。

# Thread：一次任务的工作现场

Codex 的 thread 可以理解成一次连续工作会话。一个 thread 里可以有多个 prompt，也会包含模型输出、工具调用、文件修改、命令结果和你的后续反馈。

例子：

```text
第 1 条 prompt：实现用户设置保存功能。
第 2 条 prompt：补充失败路径测试。
第 3 条 prompt：review 当前 diff，重点看权限和 API 兼容性。
第 4 条 prompt：根据 review 修改。
```

Codex 支持多个 thread 并行工作，但要注意：不要让两个 thread 同时修改同一批文件，否则容易产生冲突。

本地 thread 和云端 thread 的区别：

- 本地 thread：运行在你的机器上，可以直接读写本地工作区、运行本地命令，适合即时开发和调试。
- 云端 thread：运行在隔离环境中，适合并行委派任务、从其他设备启动任务、处理 GitHub 上的分支或 PR。

# Plan mode：复杂任务先计划

对于复杂、模糊、高风险任务，Codex 官方建议先计划再实现。

适合先计划的场景：

- 需求还不清楚。
- 涉及多个模块。
- 涉及数据库迁移。
- 涉及前后端联动。
- 可能影响用户权限、安全或支付。
- 你不确定实现路径。

你可以这样说：

```text
先不要改代码。请先阅读相关文件，提出实现计划、风险点、需要确认的问题和验证方式。
```

或者：

```text
请先 interview 我，把这个模糊需求变成一个可执行任务，包括 Goal、Context、Constraints、Done when。
```

计划阶段的价值不是形式主义，而是让 agent 在动手前先对齐任务边界。

# Codex 不是只写代码，还要验证

Codex 的可靠性很大程度来自“能验证”。官方文档强调，不要只让 Codex 做修改，还要让它运行相关检查。

常见验证方式：

- 单元测试
- 集成测试
- E2E 测试
- lint
- format
- typecheck
- 构建
- 本地复现 bug
- 浏览器截图和 console 检查
- diff review

全栈工程师的完成标准应该写得具体：

```text
Done when:
- 后端新增接口有成功和失败路径测试。
- 前端页面包含 loading、error、empty state。
- API 类型同步完成。
- npm run lint、npm run typecheck、npm test 通过。
- 最后 review diff，列出风险和未覆盖点。
```

# Codex 的权限模型：Sandbox 和 Approval

Codex 型 agent 的一个核心特点是：它可以行动，所以必须有权限边界。

官方文档里，Codex 的安全控制主要来自两层：

- Sandbox mode：技术上允许 agent 做什么，比如能读哪里、写哪里、是否能联网。
- Approval policy：什么时候必须先问你，比如越过 sandbox、联网、运行高风险命令、调用有副作用的工具。

常见模式：

- `read-only`：只读，适合调研、解释代码、做计划。
- `workspace-write`：可以读写当前工作区，适合日常开发。
- `danger-full-access`：高权限模式，风险大，不建议作为默认。

默认情况下，本地 Codex 通常会关闭命令的网络访问，并把写权限限制在当前 workspace。需要编辑 workspace 外文件、联网、执行高风险操作时，Codex 会请求批准。

实践建议：

- 新项目或陌生项目先用只读或默认权限。
- 日常开发用 workspace-write。
- 不要随便开启全权限。
- 涉及生产数据、密钥、部署、数据库删除、权限变更时，必须让 agent 先解释计划再执行。
- 对来自网页、issue、外部文档的内容保持警惕，因为 prompt injection 可能让 agent 接收到恶意指令。

# AGENTS.md：让上下文长期生效

`AGENTS.md` 是给 agent 看的项目说明书。它会在 Codex 开始工作前加载，帮助 agent 理解项目约定。

一个好的 `AGENTS.md` 可以包含：

- repo 结构和重要目录。
- 如何安装、启动、构建项目。
- 测试、lint、typecheck 命令。
- 工程规范和 PR 期望。
- 禁止事项和安全约束。
- 什么叫完成，以及如何验证。

对全栈项目，建议包含：

```md
# AGENTS.md

## Project layout

- `apps/web`: frontend app
- `apps/api`: backend service
- `packages/shared`: shared types and utilities

## Commands

- `npm run lint`
- `npm run typecheck`
- `npm test`

## API rules

- Do not change public API response shapes without updating frontend types.
- Backend endpoints must validate input and enforce authorization.

## Frontend rules

- New pages must include loading, error, and empty states.
- Check mobile layout before finalizing UI changes.

## Done means

- Relevant tests pass.
- Typecheck passes.
- Diff has been reviewed for regressions and security issues.
```

`AGENTS.md` 的最佳使用方式：

- 开始时短一点，只写真正重要的规则。
- 当 agent 犯同样错误两次，把规则补进去。
- 项目根目录写通用规则，子目录写局部规则。
- 把它当成团队协作协议，而不是长篇说明书。

# Skills、MCP 和 Subagents 在工作方式中的位置

这一步不需要深入实现，但要先知道它们解决什么问题。

## Skills

Skills 是可复用工作流。适合把重复任务写成固定流程，比如：

- PR review
- CI 失败排查
- 生成 release note
- 根据 issue 生成实现计划
- 检查前后端 API 是否同步

Codex 会先看到 skill 的名称和描述，只有需要时才加载完整说明。这叫 progressive disclosure，可以避免一开始塞太多上下文。

## MCP

MCP 是连接外部工具和上下文的标准方式。它可以让 Codex 访问：

- GitHub issue / PR / actions
- Figma 设计稿
- 浏览器和页面截图
- Sentry 日志
- 内部文档
- 数据库或业务 API

你可以理解成：

```text
Codex 是 host
MCP client 是 Codex 内部连接
MCP server 是外部工具
```

MCP server 可以暴露：

- Tools：可以执行动作。
- Resources：可以读取数据。
- Prompts：可复用提示模板。

## Subagents

Subagents 是把不同任务委派给不同角色的 agent。比如一个 agent 专门跑测试，一个 agent 专门查日志，一个 agent 专门做安全 review。

初学阶段不急着用 subagents。先把单个 Codex thread 用好，再考虑多 agent。

# Codex 型 Agent 的典型全栈工作流

## 读懂一个模块

```text
Read @apps/api/src/orders and @apps/web/src/orders.
Explain the order creation flow from frontend submit to backend persistence.
Include validation, authorization, database writes, and frontend state updates.
End with a list of files I should inspect before changing this flow.
```

## 修复一个 bug

```text
Bug: 用户保存 profile 后页面提示成功，但刷新后数据没有变化。

Repro:
1. npm run dev
2. 打开 /profile
3. 修改 display name
4. 点击 Save
5. 刷新页面，display name 恢复旧值

Constraints:
- 不改变 API response shape。
- 保持现有权限校验。
- 改动尽量小。

Done when:
- 本地复现并修复。
- 添加回归测试。
- 运行相关测试和 typecheck。
- review diff。
```

## 实现一个前后端功能

```text
Goal: 添加用户通知偏好设置。

Context:
- 前端设置页在 apps/web/src/pages/settings。
- 后端用户设置 API 在 apps/api/src/settings。
- 共享类型在 packages/shared。

Constraints:
- 不引入新依赖。
- API 必须做输入校验和权限校验。
- 前端必须包含 loading、error、empty state。

Done when:
- 前端可保存和展示通知偏好。
- 后端接口有测试。
- 前端类型和后端 schema 同步。
- lint、typecheck、test 通过。
```

## Review 当前改动

```text
Review the current diff.
Focus on correctness, regressions, missing tests, frontend/backend API mismatch, authorization, input validation, error handling, and edge cases.
Report findings first, ordered by severity, with file and line references.
```

# 你应该形成的心智模型

Codex 型通用 agent 不是一个“更强的自动补全”，而是一个受上下文、工具、权限和验证约束的开发执行系统。

可以用这个模型理解：

```text
输入层：
  prompt、文件、日志、截图、AGENTS.md、MCP resources

推理层：
  理解目标、拆任务、制定计划、选择工具、判断完成条件

行动层：
  读文件、搜索代码、编辑文件、运行命令、打开浏览器、调用 MCP tools

反馈层：
  测试结果、命令输出、diff、截图、错误日志、用户反馈

安全层：
  sandbox、approval、network policy、只读/写入权限、人工确认

沉淀层：
  AGENTS.md、Skills、配置、自动化流程、团队规范
```

学习 Codex 型 agent，本质上是在学习如何设计这几个层之间的关系。

# 第一阶段练习清单

建议你用真实项目完成这些练习：

1. 让 Codex 解释一个前后端请求链路。
2. 让 Codex 修一个有复现步骤的小 bug。
3. 让 Codex 为一个函数或接口补测试。
4. 让 Codex review 当前 diff。
5. 让 Codex 先计划再实现一个小功能。
6. 给项目写第一版 `AGENTS.md`。
7. 故意给一个不完整需求，让 Codex 先 interview 你，补齐需求边界。

每次练习后记录三件事：

- 哪些上下文给得不够？
- 哪些完成标准不够清楚？
- 哪些规则应该沉淀到 `AGENTS.md`？

# 本阶段最低掌握标准

学完这一步，你应该能做到：

- 说清 Codex 的 agent loop。
- 知道 thread、context、tool call、sandbox、approval 分别是什么。
- 能写出包含 `Goal / Context / Constraints / Done when` 的任务说明。
- 能让 Codex 先计划，再执行，再验证。
- 能判断什么时候该用只读模式，什么时候可以让它写代码。
- 能把一个全栈任务拆成可执行、可验证的 agent 任务。

如果你能稳定做到这些，再进入下一步：上下文工程和 `AGENTS.md`。
