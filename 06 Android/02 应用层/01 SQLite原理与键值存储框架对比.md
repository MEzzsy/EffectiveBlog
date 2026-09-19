> 资料核对日期：2026-09-06。本文面向 Android 应用开发，介绍 SQLite，重点对比 SharedPreferences（SP）、SQLite 和 MMKV 的键值存储用法与性能特点。

# SQLite 是什么

SQLite 是一个**嵌入式关系型数据库引擎**：应用把它作为库调用，直接访问本地数据库文件，不需要额外启动数据库服务，也不需要为了本地查询经过网络。

> “嵌入式”描述部署方式，“关系型”描述数据模型。



什么是关系型数据库？

**关系型数据库**是一种用“表”组织数据的数据库：

- **行**：一条记录，例如一个用户。
- **列**：记录的属性，例如姓名、年龄。
- **表之间可以关联**：例如订单表保存用户 ID，就能关联用户表，查询“某个用户的所有订单”。

# 两者定位

- SQLite 适合需要查询、关联和事务的结构化数据

- 键值对适合按 key 访问的轻量数据



# SP、SQLite、MMKV 的键值存储对比

以字符串键值为例，省略初始化和建表代码：

| 方案 | 写入方式 | 读取方式 | 适合的场景 |
| --- | --- | --- | --- |
| SP | `sp.edit().putString(key, value).apply()` | `sp.getString(key, defaultValue)` | 少量、低频修改的偏好设置；Android 自带 |
| SQLite | 建立以 key 为主键的表，通过 `INSERT / UPDATE` 写入 | `SELECT value FROM kv WHERE key = ?` | 需要事务、条件查询，或已有数据库的业务 |
| MMKV | `kv.encode(key, value)` | `kv.decodeString(key, defaultValue)` | 频繁读写的轻量 KV；需要引入库并初始化 |

## SP的apply和commit区别

- **`commit()`**：同步写盘，返回 `Boolean` 表示是否成功，避免在主线程调用。
- **`apply()`**：立即更新内存，异步写盘，无成功结果；生命周期切换时仍可能等待写盘。

Activity `onStop()` 返回后会等待apply写盘完成，可能会阻塞主线程。



举个例子，如果Activity A跳转到Activity B，Activity A触发的apply会阻塞B页面的打开吗？

**可能让 B 刚打开就卡顿，但通常不会阻止 B 的启动回调执行。**

假设 A、B 在同一进程，B 完全遮住 A，且 `targetSdk ≥ 11`，常见顺序是：

```
A 调用 apply() → 后台写盘
A.onPause()
B.onCreate() → B.onStart() → B.onResume()
A.onStop()
系统等待未完成的 apply() 写盘 ← 可能阻塞主线程
```

B 的启动回调已经执行，但 **A、B 共用主线程**，所以后续的 B 页面绘制、动画和点击响应仍可能被拖住。



## 为什么简单键值配置通常不优先用 SQLite

**SQLite 可以做键值存储，但仅保存主题、开关等简单配置时，通常没有必要专门引入数据库。** 相比直接调用 KV API，需要管理表结构、编写 SQL、处理查询结果；读写还经过数据库执行、页管理及事务日志等机制，增加实现成本和部分运行开销。[SQLite 架构](https://www.sqlite.org/arch.html)

这不代表 SQLite 一定更慢。如果项目已有数据库，或多个 key 必须作为同一个事务更新，使用 SQLite 完全合理。反过来，需要筛选、排序和分页的记录，也不宜仅为追求单次读写速度而全部塞进 MMKV。

# MMKV 原理与相对 SP 的性能优势

## SP 的基本原理

SP（SharedPreferences）采用 **内存 Map + XML 文件**保存键值数据：

- **加载与读取**：通过 Context 获取指定配置文件对应的 SP 实例，首次加载时在后台解析 XML，存入内存 Map。之后 `getXxx()` 直接查 Map；如果加载尚未完成，读取会等待。
- **暂存与更新**：`Editor` 先收集 `put`、`remove` 等修改，调用 `commit()` 或 `apply()` 后，再将这些修改合并到内存 Map。
- **文件持久化**：真正写盘时，将该配置文件对应的整份 Map 序列化为 XML 并同步文件，即使只修改一个 key；部分过时的异步提交可跳过写盘。

## MMKV 的基本原理

MMKV 把键值数据编码后存入文件，主要依靠三点：

- **mmap 内存映射**：把文件映射到进程地址空间，通过访问映射内存读写数据，由操作系统负责回写文件。
- **紧凑的二进制编码**：采用基于 Protobuf 的编码方式，减少 XML 文本及标签的存储、解析开销。
- **增量追加**：常规更新尽量只追加变化的键值；空间不足时，重整有效数据，必要时扩容，避免每次修改都重写整份数据。

这些机制共同服务于频繁的小型 KV 更新。[MMKV 设计说明](https://github.com/Tencent/MMKV/wiki/design)

## 相比 SP，优势主要在哪里

| 对比点 | SP | MMKV 的优势 |
| --- | --- | --- |
| 数据格式 | XML，首次加载时解析到内存 Map | 二进制编码更紧凑，减少文本解析开销 |
| 更新少量 key | 真正写盘时，把该配置文件的整个 Map 序列化为 XML；部分中间状态可能跳过写盘 | 常规路径只追加变化的 KV，减少写入数据量 |
| 写入路径 | 写入 XML 文件并执行同步；`apply()` 把写盘异步化 | 通过映射内存更新，减少常规写入路径中的文件操作开销 |

因此，**当同一配置文件中 key 较多、又频繁更新少量 key 时，MMKV 更容易体现优势**。这一判断来自两者的实现方式，具体收益仍取决于数据规模和设备。[SP 源码](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/core/java/android/app/SharedPreferencesImpl.java)、[MMKV 设计说明](https://github.com/Tencent/MMKV/wiki/design)

需要注意，**SP 加载完成后也从内存 Map 读取，并非每次 get 都解析 XML**。MMKV 同样有初始化、缺页和文件重整等成本；mmap 也不代表没有磁盘 I/O，或每次写入返回就已完成断电持久化。比较性能时应保持相同的落盘要求。[SP 源码](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/core/java/android/app/SharedPreferencesImpl.java)、[MMKV 同步 API](https://raw.githubusercontent.com/Tencent/MMKV/master/Android/MMKV/mmkv/src/main/java/com/tencent/mmkv/MMKV.java)

另外，SP 的 `apply()` 在组件生命周期切换时仍可能因等待未完成的写盘而阻塞主线程；MMKV 不依赖这条 SP 等待路径，但不能据此认为它适合在主线程无限量读写。[SP apply 说明](https://developer.android.com/reference/android/content/SharedPreferences.Editor#apply())

# 性能应该如何比较

“MMKV 比 SQLite 快多少”没有脱离工作负载的统一答案。单 key 读取、批量写入、条件查询和断电可恢复的提交，是不同测试任务。

建议先定义同一份数据和验收标准，再测量：

| 测试项 | 需要固定的条件 | 关注指标 |
| --- | --- | --- |
| 启动首次读取 | 冷启动、文件大小、key 数量、对象大小 | 首读耗时、初始化开销、内存峰值 |
| 稳态随机读取 | 相同数据规模、缓存状态、随机 key 分布 | 吞吐、P50 / P95 / P99 延迟 |
| 写入与批量写入 | 相同批量大小、事务边界和持久性要求 | 提交耗时、失败率、尾部延迟 |
| 条件查询与分页 | 同一筛选排序任务，数据库索引合理 | 完成整个业务查询的耗时与内存 |
| 并发访问 | 相同线程或进程数量、相同冲突比例 | 锁等待、丢失更新、结果正确性 |
| 异常后恢复 | 区分应用进程退出、写入中断与设备异常 | 已确认写入是否保留、数据是否完整 |

尤其要避免以下比较方式：

- SQLite 每条记录独立提交，却让另一个方案批量更新或延迟同步。
- 把 SharedPreferences 的 `apply()` 返回耗时当成写盘完成耗时。
- 只测已有缓存的热读，却用结论解释冷启动表现。
- SQLite 不建查询所需索引，另一方却把全部数据预先放进内存查找结构。
- 只报告平均值，忽略 checkpoint、文件重整、扩容和大对象带来的尾部延迟。

这是建议的评估方法，本文没有进行设备基准测试，也不提供未经测量的倍数结论。数据库的事务批量写入、查询列裁剪和索引优化，应先按官方实践落实。[Android SQLite 性能实践](https://developer.android.com/topic/performance/sqlite-performance-best-practices)
