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

# Channels 和 Nodes

Channels 把外部聊天平台连接到 Gateway。不同渠道支持的文本、媒体、回复、表情和群聊能力并不完全相同，但它们共享同一套 Agent 运行时。

Nodes 是连接到 Gateway 的其他设备或执行节点。根据平台和授权，它们可以提供语音、摄像头、屏幕、位置、Canvas 或设备本地操作。Gateway 负责协调，具体能力则在节点所在设备上执行。

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

### 压缩时机

- **自动触发**：当前上下文的 token 数接近模型的上下文窗口上限，并进入预留的安全区。
- **溢出后触发**：模型返回 `context length exceeded`、`input is too long` 等上下文溢出错误，OpenClaw 压缩后重试本轮请求。
- **手动触发**：用户执行 `/compact`，也可以附带指令，要求摘要重点保留特定内容。
- **Context Engine 触发**：自定义 Context Engine 可以根据自己的策略主动执行压缩。

### 🌟整体介绍：上下文压缩如何实现

上下文压缩由 Context Engine 负责。Context Engine 是控制模型上下文生命周期的组件，决定从 Session 和记忆中选择哪些信息、如何组装本轮输入，以及历史过长时怎样压缩。OpenClaw 默认使用内置的 `legacy` Context Engine，也可以通过 Plugin 替换为自定义实现。

默认压缩过程如下：

1. Context Engine 估算当前上下文的 token 使用量。
2. 压缩前可以执行 memory flush，把重要事实写入长期记忆。
3. 将 Session 历史划分为“较早历史”和“最近消息”，并避免拆开 Tool Call 与对应的 Tool Result。
4. 使用大语言模型把较早历史总结成一条摘要；默认使用 Agent 的主要模型，也可以单独配置压缩模型。
5. 将摘要写入 Session，同时保留最近消息的原文。
6. 下一轮重新组装“系统规则、摘要、最近消息和当前输入”，继续执行 Agent Loop。

```text
较早历史 ──→ 大模型生成摘要 ──┐
最近消息 ─────────────────────┼→ 新的模型上下文
系统规则与当前输入 ───────────┘
```

这种压缩是有损的语义总结，摘要无法保证保留所有原始细节。默认情况下，原始 transcript 仍保存在 Session 存储中，只是不再全部发送给模型。Pruning 与压缩不同：它只从本轮内存上下文中裁剪较旧的工具结果，不生成摘要，也不修改 Session transcript。

### Memory Flush：压缩前保存重要信息

Memory Flush 是上下文压缩前的一次静默 Agent 回合。它用于识别当前对话中需要长期保留的信息，并在有损压缩发生前将其**写入 Agent Workspace 的记忆文件**，通常是 `memory/YYYY-MM-DD.md`。

```text
上下文接近压缩阈值
        ↓
静默触发 Memory Flush
        ↓
提取重要事实、决定和待办事项
        ↓
写入记忆文件并返回 NO_REPLY
        ↓
继续执行上下文压缩
```

OpenClaw 默认启用 Memory Flush。它会在正式压缩阈值之前的软阈值触发，默认提前量为 `4000` tokens，并且每个压缩周期最多执行一次。由于回合以 `NO_REPLY` 结束，用户通常不会看到额外消息。

Memory Flush 只负责保存重要信息，不会压缩 Session，也不能替代压缩摘要。它通常只适用于 OpenClaw 内置 Agent Session；CLI Backend、Heartbeat 或只读 Workspace 会跳过该步骤。还可以通过 `agents.defaults.compaction.memoryFlush.model` 为这个回合单独指定模型，该模型不会继承当前 Session 的备用模型链。

### 如何划分较早历史和最近消息

OpenClaw 默认不是按照主题或固定消息数量划分，而是使用 `keepRecentTokens` 作为最近消息的 token 预算，默认值为 `20000`。它从最新消息开始向前累计估算 token，达到预算后将当前位置作为候选切分点：

```text
从最新消息向前扫描
        ↓
累计估算 token
        ↓ 达到 keepRecentTokens
确定候选切分点
        ↓
切分点之前生成摘要
切分点之后保留原文
```

如果候选切分点落在 Assistant 的 Tool Call 和对应的 Tool Result 之间，OpenClaw 会把切分点向前移动到 Tool Call 的开始位置，使调用及其结果一起保留。即使因此略微超过 `keepRecentTokens`，也优先保证工具调用块完整；已经中止或报错的工具调用不会持续阻止切分。

压缩记录会保存 `firstKeptEntryId`。后续模型上下文由压缩摘要和从该位置开始的最近消息组成。在 `safeguard` 模式下，还可以通过 `recentTurnsPreserve` 额外保留最近若干个用户与 Assistant 回合。

## 长期记忆（Memory）

OpenClaw 的长期记忆主要保存在 Agent Workspace 的 Markdown 文件中：

- `USER.md`：稳定的用户偏好、沟通方式和用户信息。
- `MEMORY.md`：经过整理的长期事实、重要决定和持续有效的摘要。
- `memory/YYYY-MM-DD.md`：按日期记录的工作信息、观察和会话摘要。

`MEMORY.md` 适合保存精炼且长期有效的内容，详细过程更适合写入每日记忆文件。需要历史信息时，Agent 可以通过记忆搜索读取相关片段，并把结果重新加入当前上下文。

### OpenClaw 的记忆召回机制

OpenClaw 会把 `USER.md`、`MEMORY.md` 和 `memory/*.md` 切分成较小片段并建立索引。召回机制根据当前问题找到相关片段，再把少量结果加入本轮模型上下文，整体类似面向个人记忆的 RAG。

```text
用户消息
   ↓
从长期记忆中检索候选片段
   ↓
按相关性、时间和重要性排序并去重
   ↓
把少量相关内容加入当前上下文
   ↓
模型继续推理
```

OpenClaw 主要有三种召回方式：

1. **启动注入**：符合条件的主 Session 或私有 Session 启动时，可以直接加载 `USER.md` 和 `MEMORY.md` 中经过限制的内容，适合经常需要的稳定信息。
2. **系统自动召回**：主 Agent 运行前，系统匹配可信记忆的触发短语，将少量强相关内容作为隐藏上下文注入。启用 Active Memory 后，还可以由受限的记忆子 Agent 执行更深的召回。
3. **Agent 主动搜索**：主 Agent 已经开始推理，但发现缺少历史信息时，在 Agent Loop 中调用 `memory_search`；需要准确原文时，再调用 `memory_get` 读取指定文件和行范围。

   - 内置的 `memory_search` 通常综合以下信号：

     - 关键词匹配，可通过本地全文索引离线完成。

     - Embedding 语义相似度；Embedding 模型负责把文本转换成向量，不等同于负责对话的大语言模型。

     - 时间新鲜度和记忆重要性。

     - MMR 去重，减少返回内容重复的片段。

```text
Agent 判断需要历史信息
        ↓
memory_search 搜索相关片段
        ↓
必要时 memory_get 读取准确原文
        ↓
结果作为 Tool Result 加入 Agent Loop
        ↓
模型继续推理并生成回答
```

系统自动召回发生在主 Agent 第一次推理之前，范围较窄且只注入少量可信信息；Agent 主动搜索发生在 Agent Loop 内部，搜索范围更广，也可以多次查询和精读。两者可以先后执行，并不冲突。

这种“加入上下文”是本轮运行时注入，并不是把整个记忆文件复制到 Session。工具调用和结果通常会记录在当前 Session 中，但原始长期记忆仍保存在 Agent Workspace。

因此，Session 保证当前对话连续，上下文决定模型本轮能够看到什么，长期记忆负责让重要信息跨 Session 延续。

# Agent Workspace

Agent Workspace 是一个 Agent 的工作目录和持久化上下文目录。它保存 Agent 的身份、规则、用户信息、记忆和专用 Skills，默认路径通常是：

```text
~/.openclaw/workspace
```

典型结构如下：

```text
workspace/
├── AGENTS.md       # 工作规则和操作约定
├── SOUL.md         # 人格、语气和行为边界
├── IDENTITY.md     # Agent 的身份信息
├── USER.md         # 用户资料和稳定偏好
├── TOOLS.md        # 工具说明和使用约定
├── MEMORY.md       # 精炼后的长期记忆
├── memory/         # 每日记忆和工作记录
└── skills/         # 当前 Workspace 专用 Skills
```

Workspace 属于 Agent，而不是某个 Session。一个 Agent 的多个 Session 通常共享同一个 Workspace，因此 Memory Flush 写入的记忆能够在后续 Session 中继续使用。多 Agent 场景应为不同 Agent 配置独立 Workspace；如果多个 Agent 指向同一目录，它们就会共享规则和记忆文件。

Workspace 只是默认工作目录，不等于安全 Sandbox。没有启用 Sandbox 时，拥有文件工具的 Agent 仍可能通过绝对路径访问 Workspace 之外的文件。

# 草稿

# TODO

1. skill是如何选择的


