> 学习目标：不研究模型训练和调参，而是学会为 Codex 型通用 Agent 提供准确、精简、可执行的上下文，并用 `AGENTS.md` 固化项目知识，从而减少重复说明、错误假设和无效探索。

# 资料来源

本文根据以下网络资料翻译、归纳并结合全栈工程实践重新组织，访问时间：2026-07-11。

- [OpenAI：Prompting](https://developers.openai.com/codex/prompting)
- [OpenAI：Customization](https://developers.openai.com/codex/concepts/customization)
- [OpenAI：Custom instructions with AGENTS.md](https://developers.openai.com/codex/guides/agents-md)
- [AGENTS.md 开放格式官网](https://agents.md/)

说明：本文不是逐字全文翻译，而是面向全栈工程师的中文学习版。涉及 Codex 文件发现顺序、覆盖规则、默认大小限制等产品行为时，以 OpenAI 官方文档为准。

# 1. 什么是上下文工程

上下文工程（Context Engineering）是指：在 Agent 执行任务前和执行过程中，持续为它选择、组织、更新真正有用的信息，使它能在正确约束下完成工作。

它和“写一句漂亮的 prompt”不是一回事。

- Prompt engineering 更关注“这句话怎样表达得更清楚”。
- Context engineering 更关注“Agent 在此刻需要看到哪些事实、规则、工具结果和历史状态”。

对软件工程 Agent 来说，一个结果通常取决于：

```text
任务结果
= 模型能力
+ 当前任务说明
+ 项目持久规则
+ Agent 找到的代码和文档
+ 命令、测试、日志等运行结果
+ 外部系统中的最新事实
+ 明确的完成标准
```

模型能力很重要，但在日常开发中，你更容易改进的是后面六项。这正是上下文工程的价值。

# 2. Codex 的上下文由哪些部分组成

可以把 Codex 的上下文分为六层。

## 2.1 当前任务

也就是你这次输入的 prompt，包括：

- 想得到什么结果。
- 已知背景和复现步骤。
- 哪些文件、页面、接口或日志相关。
- 哪些内容不能改。
- 如何验证完成。

当前任务适合承载一次性要求。例如：“这次只修 bug，不重构模块”。

## 2.2 持久项目指导

主要是仓库中的 `AGENTS.md`，也可以有个人级的 `~/.codex/AGENTS.md`。

它适合承载每次进入项目都有效的信息，例如：

- 项目结构和关键入口。
- 安装、启动、测试、lint、typecheck 命令。
- API、数据库和前端约定。
- 安全限制和 review 标准。
- 项目对“完成”的定义。

## 2.3 工作区内容

包括源代码、测试、配置、README、接口定义、数据库 schema 和 Git diff。Codex 可以通过搜索和读取文件逐步获取这些信息。

## 2.4 动态运行结果

包括：

- 测试失败信息。
- 编译和类型检查错误。
- 服务日志和堆栈。
- 浏览器截图、控制台和网络请求。
- `git diff`、`git status` 等当前状态。

这一层经常比静态文档更可信，因为它反映了代码此刻的真实行为。

## 2.5 外部来源

例如 GitHub issue、设计稿、官方 API 文档、监控平台、团队知识库。它们可以通过附件、网页搜索、插件或 MCP 提供。

外部信息可能过期，也可能包含不可信指令，因此要说明：

- 去哪里查。
- 查什么事实。
- 哪个来源优先。
- 是否允许执行外部操作。

## 2.6 当前任务历史

同一个任务中的对话、计划、工具调用、修改结果和你的纠正，也会成为后续上下文。

因此，发现方向偏了时应尽早纠正：

```text
先停止修改。你对权限模型的理解不正确：管理员只能查看，不能代替用户提交。
请重新检查相关代码和测试，然后更新计划。
```

# 3. 好上下文的六个标准

## 3.1 相关

只提供可能改变结果的信息。一个前端表单 bug 通常不需要整份基础设施文档。

## 3.2 充分

不能只说“保存有问题”，应提供复现步骤、预期行为、实际行为和相关入口。

## 3.3 可信

优先级通常可以这样理解：

```text
当前明确要求
> 可运行的测试和代码事实
> 项目内有效规则
> 官方文档
> issue、聊天记录和历史说明
> Agent 的一般经验或猜测
```

这不是 Codex 的完整内部优先级定义，而是日常工程中判断信息可信度的实用方法。

## 3.4 有边界

说明不能改变什么，以及什么操作必须先征得同意。例如：

- 不改变公共 API shape。
- 不新增生产依赖。
- 不修改数据库迁移历史。
- 不发布、不部署、不发送消息。

## 3.5 可验证

“代码更好”无法直接验收；“相关测试、lint、typecheck 通过，且重新执行复现步骤成功”可以验收。

## 3.6 新鲜

依赖版本、API 文档、线上事故和任务状态会变化。需要最新信息时，应明确要求联网核对并记录来源和日期。

# 4. 上下文不是越多越好

把整个仓库、全部日志和十几份文档一次性塞给 Agent，通常会带来三个问题：

- 重要规则被淹没。
- 冲突或过期信息增加。
- Agent 花更多时间阅读，却未必更准确。

更好的方式是渐进式披露：

1. 先给任务目标、边界和最小入口。
2. 让 Agent 搜索相关调用链和相邻测试。
3. 看到失败结果后，再补充日志或文档。
4. 只有遇到外部依赖时，才连接对应来源。

可以把 `AGENTS.md` 写成“地图和交通规则”，而不是“整座城市的百科全书”。

# 5. Codex Prompt 的实用结构

OpenAI 官方文档建议在重要任务中按需要提供 `Goal`、`Context`、`Output` 和 `Boundaries`。对软件开发，再加上 `Verification` 会更实用。

```text
Goal:
修复设置页显示保存成功、刷新后数据却丢失的问题。

Context:
- 页面：apps/web/src/pages/settings
- 接口：apps/api/src/routes/settings
- 复现：切换 Enable alerts，保存，刷新页面
- 预期：刷新后保持新值
- 实际：刷新后恢复旧值

Boundaries:
- 不改变现有 API shape
- 不新增生产依赖
- 保留权限校验

Output:
- 最小修复
- 回归测试
- 简短说明根因和风险

Verification:
- 先复现，再修复，再重新执行复现步骤
- 运行最小相关测试、lint 和 typecheck
- 最后 review diff
```

这个结构不是必须填写的表格。小任务一句话就够；只有当某项信息会改变结果时才加入。

# 6. 自动获得的上下文也有边界

不同 Codex 使用界面获得上下文的方式不同。

- IDE 扩展会自动包含打开的文件；选中关键代码会进一步缩小关注范围。
- CLI 中最好明确提到路径，或用 `@` 和 `/mention` 附加文件。
- Codex 可以自己搜索仓库，但复现步骤、业务含义和隐藏约束通常必须由你提供。
- 图片只能表达可见状态，交互、校验规则和响应式行为仍要用文字说明。

不要假设 Agent “应该知道”你脑中的业务规则。代码里没有表达、文档里没有记录、prompt 里没有说明的信息，对 Agent 来说通常就是未知信息。

# 7. `AGENTS.md` 是什么

`AGENTS.md` 是专门给 coding agent 阅读的项目说明文件，可以把它理解为“Agent 的 README”。它使用普通 Markdown，没有强制字段或固定章节。

它和 `README.md` 的分工通常是：

- `README.md` 面向人类，介绍项目、快速开始和贡献方式。
- `AGENTS.md` 面向 Agent，记录执行命令、代码约定、验证要求、目录路由和容易踩错的项目事实。

`AGENTS.md` 是开放格式，不只 Codex 可以使用。它的价值在于给不同 coding agent 一个稳定、可预测的指令入口。

# 8. Codex 如何发现 `AGENTS.md`

根据 OpenAI 当前官方文档，Codex 在每次运行开始时构建一次指导链。在 TUI 中，通常是每次启动会话时构建。

## 8.1 全局范围

Codex 首先检查 Codex home，默认是 `~/.codex`：

1. 如果存在非空的 `AGENTS.override.md`，读取它。
2. 否则读取非空的 `AGENTS.md`。
3. 这一层只读取第一个符合条件的文件。

全局文件适合个人偏好，例如沟通风格、默认验证习惯和安装依赖前先确认。

## 8.2 项目范围

Codex 从项目根目录开始，沿目录树走到当前工作目录。在每一级目录中按以下顺序检查：

1. `AGENTS.override.md`
2. `AGENTS.md`
3. 配置在 `project_doc_fallback_filenames` 中的备用文件名

每个目录最多采用一个文件。如果找不到项目根目录，则只检查当前目录。

## 8.3 合并和覆盖

Codex 按“根目录到当前目录”的顺序拼接这些文件。越靠近当前工作目录的指导出现得越晚，因此可以覆盖上层的宽泛规则。

```text
~/.codex/AGENTS.md              个人默认
repo/AGENTS.md                  整个仓库规则
repo/apps/web/AGENTS.md         前端规则
repo/apps/web/admin/AGENTS.md   管理端局部规则
```

如果当前工作目录是 `repo/apps/web/admin`，这四层指导会依次进入上下文，最靠近当前目录的规则优先。

## 8.4 大小限制

Codex 会跳过空文件。当合并后的项目指导达到 `project_doc_max_bytes` 限制时停止继续添加；当前默认值是 32 KiB。

遇到限制时，优先：

- 删除重复和低价值说明。
- 把局部规则下沉到对应子目录。
- 在 `AGENTS.md` 中提供文档路径，让 Agent 按需读取。
- 确有需要时再提高 `project_doc_max_bytes`。

# 9. `AGENTS.md` 应该写什么

一份实用的项目级文件通常包含以下内容。

## 9.1 项目地图

告诉 Agent 关键目录的职责和常见任务从哪里开始找。

```md
## Project map

- `apps/web`: React 前端
- `apps/api`: Node.js API
- `packages/contracts`: 前后端共享类型和接口契约
- `packages/db`: schema、迁移和数据访问层
- `tests/e2e`: Playwright 端到端测试
```

## 9.2 权威命令

提供能直接运行的命令，不要只写“运行测试”。

```md
## Commands

- 安装依赖：`pnpm install`
- 启动开发环境：`pnpm dev`
- lint：`pnpm lint`
- 类型检查：`pnpm typecheck`
- 单元测试：`pnpm test`
- E2E：`pnpm test:e2e`
```

如果完整测试很慢，同时给出最小测试命令和何时需要完整测试。

## 9.3 项目特有约定

只记录无法从 formatter、linter 或现有代码轻易推断的规则。

```md
## API conventions

- HTTP handler 只做解析和鉴权，业务逻辑放在 `services/`。
- 公共响应类型定义在 `packages/contracts`，不要在前后端重复声明。
- 新接口必须覆盖未授权、非法输入和成功路径。
```

## 9.4 验证和完成标准

```md
## Done means

- 运行受影响模块的最小测试。
- TypeScript 改动必须通过 typecheck。
- UI 改动需要检查 loading、empty、error 和移动端状态。
- 最后检查 diff，说明未执行的验证和剩余风险。
```

## 9.5 安全和禁止事项

```md
## Safety

- 不读取或提交 `.env` 中的密钥。
- 不修改已发布的数据库迁移；创建新的迁移。
- 未经明确要求，不部署、发布或修改生产数据。
- 添加生产依赖前先说明理由并征得确认。
```

# 10. 不适合写进 `AGENTS.md` 的内容

- 只对当前任务有效的临时要求：放进当前 prompt。
- 大段复制现有 README 或架构文档：改成路径和阅读条件。
- 能由 lint、formatter、类型系统强制执行的每一条细节：让工具负责执行。
- 已经过期的命令和目录结构：错误上下文比没有上下文更危险。
- 模糊口号，例如“写高质量代码”“遵循最佳实践”。
- 过多实现步骤：告诉 Agent 目标和约束，给它保留合理探索空间。

一个判断方法是：这条规则是否会在未来多个任务中反复改变 Agent 的行为？如果不会，它大概率不该进入 `AGENTS.md`。

# 11. 全栈项目模板

下面是一份可以按项目实际情况删改的模板。

```md
# AGENTS.md

## Repository map

- `apps/web`: React + TypeScript 前端
- `apps/api`: Node.js 后端
- `packages/contracts`: 共享 API 类型
- `packages/db`: 数据模型和迁移
- `tests/e2e`: Playwright 测试

## Start here

- 修改页面前先查看相邻组件和测试。
- 修改接口前先查看 route、service、contract 和调用方。
- 修改数据库前先查看 schema、最近迁移和回滚约定。

## Commands

- 安装：`pnpm install`
- 开发：`pnpm dev`
- lint：`pnpm lint`
- 类型检查：`pnpm typecheck`
- 单元测试：`pnpm test`
- E2E：`pnpm test:e2e`

## Engineering rules

- 保持公共 API 向后兼容，除非任务明确允许破坏性修改。
- 前后端共享类型放在 `packages/contracts`。
- 优先遵循相邻代码的既有模式，不引入平行抽象。
- 修复 bug 时添加最小回归测试。

## Frontend checks

- 检查 loading、empty、error 和 disabled 状态。
- 检查键盘操作和基本可访问性。
- UI 改动同时检查桌面和移动端。

## Backend checks

- 保留鉴权、输入校验和错误映射。
- 新增或修改接口时覆盖成功和失败路径。
- 数据库变更创建新迁移，不重写已发布迁移。

## Boundaries

- 不提交密钥或 `.env` 文件。
- 未经确认不添加生产依赖。
- 未经明确要求不部署、不发布、不修改生产数据。

## Before finishing

- 运行受影响范围内最小且充分的检查。
- Review 最终 diff，删除调试代码和无关改动。
- 报告执行过的命令、结果、未验证项和剩余风险。
```

不要直接把模板原样塞进每个仓库。删掉不适用内容，并替换为真实命令和真实目录，否则它只是看起来完整。

# 12. Monorepo 中的分层示例

项目结构：

```text
repo/
├── AGENTS.md
├── apps/
│   ├── web/
│   │   └── AGENTS.md
│   └── api/
│       └── AGENTS.md
└── packages/
    └── db/
        └── AGENTS.override.md
```

根目录 `AGENTS.md` 只放全仓库规则：

```md
## Repository rules

- 使用 pnpm workspace。
- 公共类型只能定义在 `packages/contracts`。
- 提交前运行受影响 package 的 lint、typecheck 和测试。
```

`apps/web/AGENTS.md` 放前端局部规则：

```md
## Web rules

- 使用现有设计系统组件。
- UI 修改要验证移动端、键盘操作和错误状态。
- 组件测试使用 `pnpm --filter web test`。
```

`apps/api/AGENTS.md` 放后端局部规则：

```md
## API rules

- Route 层不包含业务逻辑。
- 新接口必须添加 contract 和权限测试。
- API 测试使用 `pnpm --filter api test`。
```

`packages/db/AGENTS.override.md` 可以在数据库目录临时或明确替代同目录的普通文件：

```md
## Database rules

- 不修改已发布迁移。
- schema 变化必须生成新迁移并验证升级路径。
- 禁止连接或修改生产数据库。
```

# 13. 用路由信息减少无效阅读

如果 Codex 经常找对了方向，却读取太多文件，可以在 `AGENTS.md` 中增加“任务到入口”的映射。

```md
## Task routing

- 登录和 session：先读 `apps/api/src/auth/README.md` 和 `packages/contracts/auth.ts`。
- 账单页面：先读 `apps/web/src/features/billing`，不要从通用组件目录开始。
- 数据库迁移：先读 `packages/db/MIGRATIONS.md` 和最近两个迁移。
- UI 规范：优先读 `apps/web/src/design-system` 中的现有组件。
```

这种信息比罗列全部目录更有价值，因为它告诉 Agent 在什么条件下读取什么。

# 14. 把 `AGENTS.md` 当作反馈循环

OpenAI 官方建议从少量重要规则开始，在实际使用中逐步更新：

1. Agent 犯错。
2. 判断是一次性误解，还是项目知识缺失。
3. 如果会重复发生，把最小修正规则写进最近的 `AGENTS.md`。
4. 能自动执行的规则，同时加入 lint、类型检查、测试或 hook。
5. 后续任务观察错误是否消失。

适合沉淀的信号包括：

- 同一种错误出现两次以上。
- 每次都需要提醒相同的测试命令。
- Codex 总是从错误目录开始找。
- PR review 反复出现同一条反馈。
- 项目约定和通用行业习惯不同。

`AGENTS.md` 负责告诉 Agent 应该怎么做，自动化工具负责证明它确实做到了。两者配合比单独写一长串自然语言规则更可靠。

# 15. 如何验证 `AGENTS.md` 是否生效

官方文档给出的思路是直接让 Codex总结当前指导。

在仓库根目录运行：

```bash
codex --ask-for-approval never "Summarize the current instructions."
```

检查子目录规则：

```bash
codex --cd apps/web --ask-for-approval never "Show which instruction files are active."
```

你应确认：

- 全局和项目文件都被发现。
- 合并顺序符合预期。
- 子目录规则覆盖了宽泛规则。
- 文件不是空的，也没有因大小限制被截断。
- 修改配置或指导文件后，已重新启动 Codex 或新建会话。

# 16. 常见失败模式

## 16.1 把所有知识都写进去

结果：文件太长、规则冲突、关键要求难以发现。

改进：只保留常用规则和路由信息，详细知识放在专题文档中按需读取。

## 16.2 规则无法执行

错误示例：

```md
- 确保所有代码都很健壮。
```

更好的写法：

```md
- 修改 API 时覆盖成功、未授权和非法输入路径。
- 完成前运行 `pnpm --filter api test`。
```

## 16.3 命令不准确

结果：Agent 浪费时间猜包管理器、工作目录和参数。

改进：在干净环境中实际运行文档里的命令，并写明从哪个目录执行。

## 16.4 局部规则放在根目录

结果：前端规则干扰后端任务，或数据库限制影响无关目录。

改进：把规则放到适用范围内最近的目录。

## 16.5 只靠文字约束

结果：Agent 或人类仍可能漏掉要求。

改进：把可以机械判断的规则交给 formatter、linter、typechecker、测试和 CI。

## 16.6 临时纠正没有沉淀

结果：每个新任务都重新解释同一件事。

改进：任务结束时问自己：“这次纠正是否应该进入 `AGENTS.md` 或自动化检查？”

# 17. 全栈工程师的上下文工作流

面对一个真实任务，可以按下面的顺序使用 Codex。

## 第一步：给最小任务包

提供目标、复现、边界、入口和验证方式，不要一次性贴整个项目。

## 第二步：让 Codex 建立局部地图

```text
先不要修改。读取相关 AGENTS.md、入口文件、调用方和相邻测试，说明请求流和最可能的故障点。
```

## 第三步：核对它的假设

重点检查业务规则、权限、兼容性和数据生命周期。错误假设要在修改前纠正。

## 第四步：实施并用动态结果补充上下文

让 Codex 运行最小测试或复现步骤。失败输出会成为下一轮最有价值的上下文。

## 第五步：验证和 review

```text
运行相关测试、lint 和 typecheck，重新执行复现步骤，然后 review 最终 diff。报告未验证项和剩余风险。
```

## 第六步：沉淀可复用知识

如果本次任务暴露了长期缺失的项目规则，更新最近的 `AGENTS.md`；如果规则可自动判断，同时补充测试或静态检查。

# 18. 动手练习

## 练习一：上下文体检

从最近做过的一个 bug 中整理：

- 最初 prompt 缺少了什么。
- Codex 需要读哪些文件。
- 哪个测试或日志最能证明根因。
- 哪条信息应该沉淀为长期规则。

## 练习二：创建最小 `AGENTS.md`

只写五个部分：

1. 项目地图。
2. 三到六条权威命令。
3. 三条项目特有约定。
4. 两条安全边界。
5. 完成前检查。

控制在 80 行以内，然后让 Codex总结它加载到的指导。

## 练习三：分层

如果是前后端 monorepo，在前端和后端目录各写一个局部 `AGENTS.md`。从两个目录分别启动 Codex，比较生效规则。

## 练习四：建立反馈循环

未来一周记录 Codex 的重复错误。只有第二次出现时才考虑加入 `AGENTS.md`，并优先思考能否用测试或 lint 自动检查。

# 19. 掌握标准

完成这一阶段后，你应该能够：

- 解释 prompt engineering 和 context engineering 的区别。
- 为 bug、功能和 review 任务提供最小而充分的上下文。
- 区分一次性 prompt、`AGENTS.md`、专题文档、Skill 和自动化检查的职责。
- 说明 Codex 发现、合并和覆盖 `AGENTS.md` 的顺序。
- 为全栈项目编写简短、可执行、可验证的 `AGENTS.md`。
- 用嵌套文件管理 monorepo 的局部规则。
- 把重复纠正沉淀为项目指导或自动化约束。
- 发现并清理过期、冲突和低价值上下文。

# 20. 一句话总结

上下文工程不是把更多信息交给 Agent，而是在正确时刻交给它正确的信息；`AGENTS.md` 则把其中稳定、重复、项目特有的部分变成可以随仓库长期演进的工程资产。
