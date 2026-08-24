> 学习目标：理解 OpenClaw 的产品定位、核心架构、运行流程、扩展机制和安全边界，能够判断它适合解决什么问题，并完成一次最小化、安全的本地部署。

> 资料来源
>
> 本文根据 OpenClaw 官方文档、官方 GitHub 仓库和 OpenAI 官方文档整理，访问时间：2026-08-23。
>
> - [OpenClaw 官方网站](https://openclaw.ai/)
> - [OpenClaw GitHub 仓库](https://github.com/openclaw/openclaw)
> - [Getting Started](https://docs.openclaw.ai/start/getting-started)
> - [Gateway](https://docs.openclaw.ai/gateway)
> - [Agent Runtime](https://docs.openclaw.ai/concepts/agent)
> - [Agent Workspace](https://docs.openclaw.ai/concepts/agent-workspace)
> - [Memory](https://docs.openclaw.ai/concepts/memory)
> - [Tools、Skills 和 Plugins](https://docs.openclaw.ai/tools)
> - [Security](https://docs.openclaw.ai/gateway/security)
> - [Sandboxing](https://docs.openclaw.ai/gateway/sandboxing)
> - [OpenAI：Codex 官方文档](https://learn.chatgpt.com/docs)
> - [OpenAI：Codex Use Cases](https://developers.openai.com/codex/use-cases)
>
> 说明：OpenClaw 更新较快，支持的平台、模型、渠道和配置项可能发生变化。安装和生产部署时应以当前官方文档为准。

# OpenClaw 整体介绍

OpenClaw 是一个运行在自己设备上的开源个人 AI 助手平台。它把大语言模型、聊天渠道、工具、记忆、定时任务和设备能力连接到一个长期运行的 Agent 中，让用户可以从聊天软件等入口与同一个助手交互。

面向场景：为单个可信用户搭建一个长期在线、跨渠道、能调用真实工具的个人 AI 助手。

OpenClaw 不是大语言模型，也不只是一个聊天机器人。更准确地说，它是位于用户、模型和真实系统之间的 **Agent 运行时与控制平面**。

```text
用户与聊天渠道
      ↓
OpenClaw Gateway
      ↓
Agent、Session、Workspace、Memory
      ↓
大语言模型 ↔ Tools / Skills / Plugins
      ↓
文件、Shell、浏览器、消息平台、设备和外部服务
```

模型负责理解、推理和决定下一步；OpenClaw 负责保存状态、组装上下文、调用模型、执行工具、路由消息并控制权限。

## OpenClaw 和 Codex 的区别

OpenClaw 和 Codex 都属于能够读取上下文、调用工具并根据执行结果继续工作的 Agent 系统，但两者的核心定位不同：

```text
OpenClaw：面向个人助手的长期运行平台与控制平面
Codex：面向软件工程任务的 Agent 产品与执行环境
```

OpenClaw 关心的是“怎样让一个助手长期在线，并连接用户的消息渠道、记忆、模型、工具和设备”；

Codex 关心的是“怎样在一个工作区中理解代码、修改项目、运行验证并交付可审查的软件工程结果”。

两者也不是互斥的，有 OpenClaw 的原生 Codex Plugin 用于在 OpenClaw 中集成 Codex。

# OpenClaw 的整体运行流程

OpenClaw 的运行可以分为两个阶段：Gateway 启动时准备运行环境，以及收到消息或定时事件后执行一次 Agent Loop。

整体流程如下：

> 如果 Gateway 已启动并且聊天渠道已经连接，新消息的实际处理从第 4 步开始：

1. 启动 Gateway
2. 加载配置、凭据、Agents、Channels、Tools、Skills 和 Plugins
3. 连接聊天渠道并等待消息、定时任务或系统事件
4. 验证输入来源并路由到对应 Agent 与 Session
5. 组装系统指令、工作区文件、记忆和会话历史
6. 调用大语言模型
7. 模型直接回答，或者发起工具调用
8. 检查 Tool Policy、Approvals 和 Sandbox
9. 执行工具并把真实结果返回模型
10. 模型继续判断，直到完成任务或需要用户确认
11. 保存会话与必要记忆，并把结果发送回原渠道

# Gateway

Gateway 是 OpenClaw 的核心常驻进程和控制平面，**可以理解为个人 AI 助手的“操作系统服务”**。它负责连接用户入口、Agent、大语言模型和真实工具。

主要职责包括：

- 连接聊天渠道、Control UI、CLI 和设备节点。
- 验证消息来源，并路由到对应的 Agent 与 Session。
- 管理 Session、后台任务和运行状态。
- 组装上下文并调用大语言模型。
- 调度工具，并落实权限、审批和 Sandbox 策略。
- 把最终结果发送回原来的入口。

## 启动时机

Gateway 不是收到消息后才启动，而是需要提前运行并保持常驻：

- 前台运行：执行 `openclaw gateway` 或 `openclaw gateway run` 时启动，关闭终端进程后停止。
- 后台服务：安装 Gateway 服务后，由 macOS 的 launchd、Linux 的 systemd 或 Windows 任务计划程序在登录或服务启动时运行，并可在异常退出后自动重启。
- 桌面应用：应用会先连接已经运行的 Gateway；本地模式下若没有可用实例，则启动系统管理的 Gateway 服务。

Gateway 启动完成后便持续监听各个入口。新消息到来时只会触发消息路由和 Agent Loop，不会重新启动 Gateway。

## Gateway 启动流程

Gateway 启动时会加载配置、凭据、Channels、Agents、Tools、Skills 和 Plugins，然后进入常驻等待状态。收到新消息时不需要重新初始化，而是直接执行：

```text
验证输入来源
      ↓
路由到 Agent 与 Session
      ↓
组装本轮上下文
      ↓
启动 Agent Loop
```

## 多个对话入口如何处理

当多个入口同时连接 Gateway 时，Gateway 会先把不同渠道的消息转换为统一格式，并保留发送者、渠道、群组和回复地址等来源信息。

随后根据渠道绑定和 Session 配置进行路由：

```text
多个对话入口
      ↓
Gateway 统一接收并验证身份
      ↓
根据绑定选择 Agent
      ↓
根据发送者和会话类型选择 Session
      ↓
执行 Agent Loop
      ↓
把结果返回原入口
```

- 多个私聊入口可以指向同一个主 Session，从而共享上下文和记忆。
- 群聊、频道或不同用户通常使用独立 Session，避免上下文互相污染。
- 进入同一 Session 的消息遵循该 Session 的排队或转向规则；不同 Session 保持各自的状态。
- 最终回复会根据消息携带的来源信息返回对应的聊天入口。

因此，Gateway 的作用不是为每个聊天软件创建一套独立助手，而是让多个入口复用同一套 Agent 能力，同时通过 Session 隔离各自的对话状态。

## 多入口的底层逻辑

> 简单理解：Gateway 基于路由配置，将 Channel Adapter 统一格式化后的消息分发到对应的 Agent 和 Session。

多个对话入口的底层逻辑是：

```text
Channel Adapter
+ Gateway 消息路由
+ Agent Binding
+ Session 映射
```

Channel Adapter 把 Telegram、Slack 等平台的消息转换成统一格式，Gateway 再选择 Agent 和 Session。

以多个私聊入口共享主 Session 为例：各入口先通过 `bindings` 指向同一个 `agentId`，再由 `session.dmScope: "main"` 将消息映射到同一个 Session Key（默认类似 `agent:main:main`）。Gateway 仍会保留本次消息的来源，因此共享上下文不影响回复返回原入口。

```text
Telegram 私聊 ─┐
               ├→ 同一个 Agent → 同一个主 Session
Slack 私聊 ────┘                         ↓
                                回复返回本次消息入口
```

如果配置为 `per-peer`、`per-channel-peer` 或 `per-account-channel-peer`，Gateway 则会按用户、渠道或账号生成不同的 Session Key，实现上下文隔离。

# Agent

## Agent 的核心组成

- **身份与规则**：定义 Agent 的角色、行为方式和工作约束。
- **Workspace 与记忆**：保存上下文文件、用户信息和长期记忆。
- **模型配置**：指定默认模型、备用模型及 Model Provider。
- **Tools、Skills 与权限**：决定 Agent 能做什么，以及执行操作时受到哪些审批和 Sandbox 限制。
- **Sessions**：保存连续对话的消息和执行状态；一个 Agent 可以拥有多个 Session。
- **Bindings**：告诉 Gateway 哪些渠道、账号或用户应当路由到该 Agent。

## Agent 如何运行

收到 Gateway 路由的消息后，Agent 会读取对应 Session 和 Workspace，组装本轮上下文并启动 Agent Loop。模型可以直接生成答案，也可以请求调用工具；工具结果返回模型后，循环继续，直到任务完成或需要用户确认。

```text
Gateway 选择 Agent 与 Session
            ↓
加载 Workspace、记忆和会话历史
            ↓
调用模型判断下一步
            ↓
直接回答或调用工具
            ↓
保存结果并返回原入口
```

其中，Agent 定义“由谁、用什么能力执行”，Session 定义“这次对话延续哪一份上下文”。

## 运行多 Agent

一个 Gateway 可以运行多个 Agent。不同 Agent 可以拥有独立的 Workspace、模型、工具权限、记忆和 Sessions，再通过 `bindings` 分别服务个人、工作或其他渠道。多个 Agent 适合做职责隔离；如果需要隔离互不信任的用户，应使用独立 Gateway 或更强的系统级隔离。



# Session

## Session 是什么

Session 是 OpenClaw 中一段连续对话和执行过程的状态容器。它让 Agent 能够延续之前的消息、工具结果和任务进度，而不是每次收到消息都从零开始。

一个 Agent 可以拥有多个 Session，每个 Session 由 Session Key 标识，通常保存：

- 用户消息、模型回复和工具调用结果。
- 当前任务状态及上下文压缩后的摘要。
- 消息来源、最近回复入口等路由信息。

## Session 如何选择和运行

Gateway 选定 Agent 后，会根据私聊、群聊、渠道、发送者以及 Session 配置生成 Session Key。相同 Session Key 的消息共享上下文，不同 Session Key 的状态相互隔离。

```text
消息进入 Gateway
      ↓
选择 Agent
      ↓
生成 Session Key
      ↓
读取历史并运行 Agent Loop
      ↓
将消息和执行结果写回 Session
```

私聊可以汇聚到 Agent 的主 Session，例如 `agent:main:main`；也可以按用户、渠道或账号拆分。群聊、后台任务和子 Agent 通常使用独立 Session，避免无关上下文混在一起。

# 上下文与记忆

Session、上下文和长期记忆都与“保存信息”有关，但处于不同层次：

| 概念 | 作用 | 特点 |
| --- | --- | --- |
| Session | 保存一段对话或任务的持续状态 | 包含消息、工具调用和执行记录 |
| 上下文 | 提供本轮模型推理所需的信息 | 每轮重新组装，受模型上下文窗口限制 |
| 长期记忆 | 跨 Session 保存稳定信息 | 写入 Workspace，可在后续会话中重新读取 |

## 上下文

上下文是 OpenClaw 在一次模型调用中实际发送给大语言模型的全部信息，主要包括：

- 系统规则、可用 Tools 和 Skills。
- Workspace 中注入的身份、用户和记忆文件。
- 当前 Session 的对话历史与压缩摘要。
- 本轮消息、附件以及工具调用结果。

Session 中保存的内容不一定会全部进入上下文。OpenClaw 会根据模型的上下文窗口选择和组织信息，因此“Session 有这段记录”不代表“模型本轮一定看到了这段记录”。

## 上下文压缩

当历史接近模型的上下文窗口上限时，OpenClaw 会把较早的对话压缩成摘要，并保留最近消息，使当前 Session 可以继续运行。较旧或体积较大的工具结果也可以从本轮上下文中裁剪，但这不会等同于删除 Session 中保存的原始记录。

压缩前，OpenClaw 可以执行一次静默的 memory flush，把可能需要长期保留的信息先写入记忆文件，再缩短模型当前看到的历史。

## 长期记忆

OpenClaw 的长期记忆主要保存在 Agent Workspace 的 Markdown 文件中：

- `USER.md`：稳定的用户偏好、沟通方式和用户信息。
- `MEMORY.md`：经过整理的长期事实、重要决定和持续有效的摘要。
- `memory/YYYY-MM-DD.md`：按日期记录的工作信息、观察和会话摘要。

`MEMORY.md` 适合保存精炼且长期有效的内容，详细过程更适合写入每日记忆文件。需要历史信息时，Agent 可以通过记忆搜索读取相关片段，并把结果重新加入当前上下文。

```text
Session 历史 ─────┐
Workspace 文件 ──┼→ 组装本轮上下文 → 模型推理
长期记忆检索 ────┘                    ↓
                              新结果写回 Session
                                      ↓
                           重要信息写入长期记忆
```

因此，Session 保证当前对话连续，上下文决定模型本轮能够看到什么，长期记忆负责让重要信息跨 Session 延续。

# 草稿

# 核心架构

## Session

Session 是连续对话和执行状态的载体。它保存消息、模型输出、工具调用和上下文压缩后的结果。

OpenClaw 默认把同一用户从不同直接消息渠道发来的内容汇聚到主 Session。因此，用户可以在手机上通过聊天软件提出问题，再从电脑上的 Control UI 继续同一个上下文。

群聊、后台任务和子 Agent 通常使用独立 Session，以避免所有内容混入主对话。Session 可以被重置或压缩，但需要长期保留的信息应写入记忆文件，而不是只依赖模型上下文窗口。

## Workspace

Workspace 是 Agent 的工作目录，也是它的持久上下文目录，默认位置为：

```text
~/.openclaw/workspace
```

一个典型工作区包含：

```text
workspace/
├── AGENTS.md       # 操作规则和工作方式
├── SOUL.md         # 人格、语气和边界
├── IDENTITY.md     # 名称、身份和形象
├── USER.md         # 用户资料与稳定偏好
├── TOOLS.md        # 本地工具说明和使用约定
├── MEMORY.md       # 精炼后的长期记忆
├── memory/         # 按日期保存的工作记忆
├── skills/         # 当前工作区专用 Skills
└── canvas/         # 可选的 Canvas UI 内容
```

这些文件让 Agent 的行为可以被用户查看、修改、备份和版本控制，而不是隐藏在一个不可见的服务端状态里。

Workspace 只是工具的默认工作目录，**本身不是安全沙箱**。如果未启用沙箱或文件访问限制，工具仍可能通过绝对路径访问工作区之外的宿主机文件。

## Memory

OpenClaw 的长期记忆主要由普通 Markdown 文件构成。它没有一个模型可以自动永久记住所有对话；只有被写入持久存储并在后续检索或注入上下文的信息，才能跨 Session 使用。

记忆可以分为三层：

| 层次 | 典型文件 | 适合保存的内容 |
| --- | --- | --- |
| 用户模型 | `USER.md` | 稳定偏好、称呼方式、关系和长期项目背景 |
| 精炼记忆 | `MEMORY.md` | 长期有效的事实、决定和简短总结 |
| 工作记忆 | `memory/YYYY-MM-DD.md` | 每日记录、过程观察、详细上下文和临时线索 |

当对话接近上下文压缩时，OpenClaw 可以先触发一次 memory flush，提醒 Agent 把重要事实写入记忆文件，再压缩当前会话。后续需要历史信息时，Agent 可以通过记忆搜索读取相关片段。

这种机制的优点是可观察、可编辑和可迁移；缺点是记忆质量依赖写入和整理策略。错误、过期或互相矛盾的记录也可能影响后续行为，因此长期记忆需要定期审查。

## Channels 和 Nodes

Channels 把外部聊天平台连接到 Gateway。不同渠道支持的文本、媒体、回复、表情和群聊能力并不完全相同，但它们共享同一套 Agent 运行时。

官方支持的渠道包括 Telegram、WhatsApp、Discord、Slack、Signal、Google Chat、Microsoft Teams、iMessage、Matrix、飞书、QQ 等；部分随核心安装提供，部分需要安装官方插件。

Nodes 是连接到 Gateway 的其他设备或执行节点。根据平台和授权，它们可以提供语音、摄像头、屏幕、位置、Canvas 或设备本地操作。Gateway 负责协调，具体能力则在节点所在设备上执行。

# 能力扩展

## Tools

Tool 是 Agent 可以调用的结构化动作。它有明确的名称、参数和返回结果，而不是让模型假装完成了操作。

常见工具类别包括：

- 文件读取、写入和补丁修改。
- Shell 命令与后台进程。
- 浏览器控制、网页抓取和搜索。
- 消息发送和渠道操作。
- Session 查询、跨 Session 通信和子 Agent。
- 定时任务、提醒和后台自动化。
- 图片、音频和其他媒体处理。

模型只能看到经过当前工具配置、allow/deny 策略、渠道权限、沙箱状态和插件可用性共同过滤后仍然可用的工具。

## Skills

Skill 是以 `SKILL.md` 为入口的操作说明包，用来告诉 Agent **什么时候以及怎样完成一类任务**。它适合保存：

- 重复工作流。
- 命令执行顺序。
- 项目规范和审查清单。
- 特定工具的使用方法。
- 输出模板和完成标准。

Tool 提供“能做什么”，Skill 提供“应该怎样做”。例如，浏览器工具让 Agent 可以操作网页，而一个“提交费用报销”Skill 可以规定登录入口、表单字段、附件要求、审批前暂停点和验证步骤。

Skill 本身不能突破工具权限。说明中要求执行 Shell 命令，并不代表 Agent 自动获得 Shell 权限。

## Plugins

Plugin 是包含代码和清单的运行时扩展，可以新增：

- 工具。
- Skills。
- 聊天渠道。
- 模型提供商。
- 语音、媒体和搜索能力。
- 生命周期 Hook 和其他 Gateway 能力。

当需求只是告诉 Agent 一套已有工具的使用流程时，优先使用 Skill；当需求涉及新代码、凭据、协议或运行时生命周期时，使用 Plugin 更合适。

第三方 Plugin 和 Skill 都属于供应链输入。安装前应检查来源、权限、依赖和脚本，安装后也应限制它们能够访问的工具与凭据。

## Model Providers

OpenClaw 把模型选择与 Agent 运行时分开。用户可以为 Agent 配置主模型、备用模型和用于辅助任务的模型，也可以接入不同的模型提供商。

选择模型时应关注：

- 是否可靠支持工具调用。
- 上下文窗口是否满足任务需要。
- 延迟、价格和速率限制。
- 多模态输入输出能力。
- 对复杂指令和长流程的遵循能力。
- 数据是否允许发送给对应提供商。

OpenClaw 在自己的设备运行，不等于所有数据都只在本地处理。使用云端模型、搜索服务或聊天渠道时，相关内容仍会发送给对应服务。只有模型、工具和数据链路都在本地时，才能称为完整的本地处理。

# 主动工作能力

## Heartbeat

Heartbeat 会周期性唤醒主 Session，让 Agent 检查当前是否有需要处理的事项。它适合轻量的状态检查和提醒发现。

Heartbeat 触发的是完整 Agent 回合，频率越高，模型调用和 token 消耗通常越高。没有明确检查目标时，不应只为了“让助手更主动”而设置很短的周期。

## Automations

需要在确定时间执行、重复执行或可靠跟踪的工作，应使用 Automations。典型场景包括：

- 每天固定时间汇总信息。
- 在指定时间提醒用户。
- 周期性检查服务状态。
- 延迟执行一次后续任务。

可以把两者简单区分为：Heartbeat 负责“醒来看看是否有事”，Automation 负责“在明确的时间执行明确的任务”。
