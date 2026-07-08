> 学习目标：理解 Codex 这类通用软件工程 agent 如何接收任务、获取上下文、调用工具、修改代码、验证结果，并在权限边界内工作。

# 资料来源

本文根据以下网络资料翻译和整理，访问时间：2026-07-07。

- OpenAI Codex 官方文档：https://developers.openai.com/codex
- OpenAI Codex 开源仓库：https://github.com/openai/codex
- Codex 官方手册：https://developers.openai.com/codex/codex-manual.md
- AGENTS.md 说明：https://agents.md

说明：下面不是逐字全文翻译，而是面向全栈工程师学习的中文整理版。重点保留 Codex 的工作模型、上下文、线程、工具调用、验证、安全和可复用工作流。

# 1. Codex 是什么

Codex 是 OpenAI 面向软件开发的 coding agent。它不只是聊天助手，而是能在一个真实工作区里读文件、理解代码、修改代码、运行命令、执行测试、调试错误、review diff，并根据你的反馈继续迭代。

从使用者角度看，Codex 可以承担这些工作：

- 写代码：根据需求生成或修改代码，并尽量遵守现有项目结构和风格。
- 理解代码库：阅读陌生或复杂代码，解释模块职责、调用关系、数据流和风险点。
- Review 代码：检查潜在 bug、逻辑错误、边界条件、测试缺口和回归风险。
- Debug 和修复问题：根据错误日志、复现步骤、失败测试定位原因并提出补丁。
- 自动化开发任务：执行重构、测试、迁移、环境设置、文档更新等重复工作。

对全栈工程师来说，最重要的理解是：Codex 的价值不只是“生成代码”，而是帮助你把一次开发任务跑成一个闭环。

```text
需求 -> 理解上下文 -> 制定计划 -> 修改代码 -> 运行验证 -> Review -> 继续迭代
```

# 2. Codex 的基本工作循环

Codex 收到 prompt 后，会进入一个 agent loop：

1. 理解你的目标和约束。
2. 收集上下文，比如读取文件、搜索代码、查看测试、分析错误日志。
3. 决定下一步行动。
4. 调用工具，比如 shell、文件读取、文件编辑、apply patch、浏览器、MCP 工具。
5. 观察工具结果，比如命令输出、测试失败、文件内容、网页状态。
6. 根据结果继续推理和行动。
7. 在任务完成或你取消任务时停止。

你可以把它理解成一个“能行动的开发搭档”。普通聊天模型主要输出文字，Codex 型 agent 会把文字推理转化成实际操作。

# 3. Prompt 决定任务边界

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

# 4. Codex 如何使用上下文

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

# 5. Thread：一次任务的工作现场

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

# 6. Plan mode：复杂任务先计划

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

# 7. Codex 不是只写代码，还要验证

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

# 8. Codex 的权限模型：Sandbox 和 Approval

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

# 9. AGENTS.md：让上下文长期生效

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

# 10. Skills、MCP 和 Subagents 在工作方式中的位置

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

# 11. Codex 型 Agent 的典型全栈工作流

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

# 12. 你应该形成的心智模型

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

# 13. 第一阶段练习清单

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

# 14. 本阶段最低掌握标准

学完这一步，你应该能做到：

- 说清 Codex 的 agent loop。
- 知道 thread、context、tool call、sandbox、approval 分别是什么。
- 能写出包含 `Goal / Context / Constraints / Done when` 的任务说明。
- 能让 Codex 先计划，再执行，再验证。
- 能判断什么时候该用只读模式，什么时候可以让它写代码。
- 能把一个全栈任务拆成可执行、可验证的 agent 任务。

如果你能稳定做到这些，再进入下一步：上下文工程和 `AGENTS.md`。
