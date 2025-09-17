以下是一份系统的 Kotlin Multiplatform（KMP）学习大纲，从基础到进阶，兼顾理论与实战，涵盖核心技术、工程实践和场景落地：

# 第一阶段：KMP 基础与前置知识

**目标**：掌握 KMP 依赖的核心技术栈，理解跨平台思想与基础工具链。

## 1.1 Kotlin 核心语法强化

- **核心内容**：
  - 空安全与类型系统（`?`/`!!`/`Nothing`/`Any`）
  - 函数式编程（Lambda / 高阶函数 / 函数引用）
  - 协程与异步编程（`CoroutineScope`/`Dispatcher`/`Flow`/`StateFlow`）
    -  [协程与异步编程.md](协程与异步编程.md) 
  - 泛型与类型擦除（`reified` 关键字的跨平台限制）
  - 密封类（`sealed class`）与接口（跨平台状态管理基础）
- **实践**：用 Kotlin 实现一个带缓存的网络请求工具（单平台，侧重异步逻辑）。















#### 1.2 KMP 基础概念与工程结构

- **核心内容**：
  - 多平台项目的意义（代码共享 vs 平台特性保留）
  - 源码集（Source Set）：`commonMain`/`jvmMain`/`iosMain`/`androidMain` 等
  - 预期声明与实际实现（`expect`/`actual` 机制）
  - 平台目标（Target）：JVM/Android/iOS/Desktop/Web 的配置差异
- **实践**：
  - 手动创建最小 KMP 项目（不依赖模板），包含 `commonMain` 和 `jvmMain`
  - 实现 `expect fun getPlatformName(): String`，各平台返回对应名称（如 "Android"、"iOS"）

#### 1.3 工具链与环境配置

- **核心内容**：
  - IntelliJ IDEA 配置（KMP 插件、Kotlin 版本匹配）
  - Gradle 基础（Kotlin DSL 语法、`build.gradle.kts` 结构）
  - 多平台依赖管理（`api`/`implementation`、平台特定依赖声明）
  - iOS 环境联动（Xcode 配置、模拟器调试）
- **实践**：
  - 配置一个包含 Android + iOS 目标的 KMP 项目
  - 通过 Gradle 任务（`assembleAndroid`/`linkIosDebug`）验证构建流程

### **第二阶段：KMP 核心技术与跨平台能力（3-4 周）**

**目标**：掌握 KMP 代码共享的核心模式，解决平台差异问题，实现基础跨平台功能。

#### 2.1 共享代码设计模式

- **核心内容**：
  - 共享逻辑分层：数据层（Repository）、领域层（UseCase）、工具类
  - 平台接口抽象（`expect interface`）与平台实现（`actual class`）
  - 跨平台单例（`expect object`）与依赖注入（Koin/Hilt 多平台适配）
- **实践**：设计一个跨平台日志工具（`Logger`），Android 用 `Logcat`，iOS 用 `print`，桌面用 `System.out`。

#### 2.2 数据处理与序列化

- **核心内容**：
  - `kotlinx.serialization` 跨平台 JSON 解析
  - 数据模型设计（`@Serializable` 注解、多平台兼容性）
  - 二进制序列化（针对性能敏感场景）
- **实践**：定义一个 `User` 数据类，在各平台实现 JSON 序列化 / 反序列化。

#### 2.3 跨平台 I/O 操作

- **核心内容**：
  - 网络请求：`ktor-client` 多平台配置（Android/iOS/Desktop 适配）
  - 本地存储：`SQLDelight`（跨平台数据库）、`Multiplatform Settings`（键值对存储）
  - 协程在跨平台 I/O 中的线程管理（`Dispatchers.Main`/`Dispatchers.IO` 平台差异）
- **实践**：
  - 用 `ktor-client` 实现跨平台接口请求（获取用户列表）
  - 用 `SQLDelight` 存储用户数据并同步到各平台 UI

#### 2.4 平台交互进阶（JVM/Android <-> iOS）

- **核心内容**：
  - Kotlin 与 Swift/Objective-C 互操作（类型映射：`List`->`Array`、`suspend`->`async`）
  - Android 原生代码调用（`@AndroidJvm` 注解、资源访问）
  - iOS 原生代码集成（`@ObjCName` 注解、Swift 扩展）
- **实践**：在 KMP 中定义 `expect fun showToast(message: String)`，Android 用 `Toast`，iOS 用 `UIAlertController` 实现。

### **第三阶段：跨平台 UI 与状态管理（3-4 周）**

**目标**：掌握 Compose Multiplatform 跨平台 UI 开发，实现多端统一界面。

#### 3.1 Compose Multiplatform 基础

- **核心内容**：
  - 声明式 UI 思想与 Compose 语法（`@Composable`、`Modifier`、布局系统）
  - 跨平台组件差异（`AndroidView`/`IosView` 原生控件嵌入）
  - 资源管理（图片、字符串的多平台共享方案）
- **实践**：实现一个跨平台登录界面（包含输入框、按钮、表单验证）。

#### 3.2 状态管理与 UI 交互

- **核心内容**：
  - 共享状态设计（`StateFlow` 跨平台状态传递）
  - 单向数据流（UI -> 事件 -> 业务逻辑 -> 状态 -> UI）
  - 平台特定交互处理（如 Android 手势、iOS 滑动返回）
- **实践**：开发一个带分页加载的列表页（共享 `StateFlow` 管理数据，各平台适配滑动体验）。

#### 3.3 主题与样式统一

- **核心内容**：
  - Material3 跨平台主题配置（颜色、字体、形状）
  - 平台特性适配（Android 深色模式、iOS 动态字体）
  - 资源压缩与优化（图片格式选择、按需加载）
- **实践**：设计一套跨平台主题系统，在 Android/iOS/Desktop 保持视觉一致性。

### **第四阶段：进阶与工程化（3-4 周）**

**目标**：解决 KMP 实战中的复杂问题，掌握性能优化、测试与部署流程。

#### 4.1 性能优化

- **核心内容**：
  - 共享代码体积优化（`proguard`/`R8` 配置、依赖裁剪）
  - 内存管理（平台特定内存模型差异、避免泄露）
  - UI 渲染性能（Compose 重组优化、列表复用）
- **实践**：
  - 对一个图片列表页进行内存优化（避免 OOM）
  - 用 `Android Profiler`/`Xcode Instruments` 分析并优化性能瓶颈

#### 4.2 测试策略

- **核心内容**：
  - 共享代码单元测试（`commonTest` 与平台测试结合）
  - 跨平台 UI 测试（Compose Test 框架）
  - 端到端测试（Android Espresso + iOS XCUITest 联动）
- **实践**：为网络请求工具编写跨平台单元测试，覆盖成功 / 失败场景。

#### 4.3 架构设计

- **核心内容**：
  - 跨平台 MVVM/MVI 架构落地（共享 ViewModel/UseCase）
  - 模块化拆分（按功能拆分共享模块，避免单一模块臃肿）
  - 大型项目协作规范（代码风格、分支管理、平台特性隔离）
- **实践**：设计一个新闻客户端架构（共享数据层 + 领域层，平台层只负责 UI）。

#### 4.4 部署与 CI/CD

- **核心内容**：
  - 多平台构建自动化（Gradle 任务编排）
  - GitHub Actions/Jenkins 配置（Android APK/iOS IPA 打包）
  - 版本管理与发布策略（语义化版本、平台版本同步）
- **实践**：配置 GitHub Actions 实现 KMP 项目的 Android 打包与 iOS 模拟器测试。

### **第五阶段：实战项目与场景落地（4-6 周）**

**目标**：通过完整项目整合所学知识，解决真实业务场景问题。

#### 5.1 实战项目 1：跨平台工具类库

- **场景**：开发一个带加密功能的本地存储库（支持 Android/iOS/Desktop）
- **技术点**：`expect/actual` 加密实现、`SQLDelight`、平台权限适配
- **产出**：可发布到 Maven 的 KMP 库

#### 5.2 实战项目 2：全功能跨平台应用

- **场景**：开发一个待办事项（Todo）应用，包含：
  - 网络同步（`ktor-client` + 后端 API）
  - 本地缓存（`SQLDelight`）
  - 跨平台 UI（Compose Multiplatform）
  - 平台特性（Android 通知、iOS 快捷操作）
- **产出**：可在 Android/iOS/Desktop 运行的完整应用

#### 5.3 场景扩展：复杂交互场景

- **内容**：
  - 音视频处理（结合 FFmpeg 跨平台调用）
  - 地图集成（Google 地图 / Apple 地图的跨平台抽象）
  - 支付功能（平台支付 SDK 封装）
- **实践**：为 Todo 应用添加地理位置标记功能（抽象地图接口，各平台实现）

### **推荐学习资源**

1. **官方文档**：
   - [Kotlin 多平台官方指南](https://kotlinlang.org/docs/multiplatform.html)
   - [Compose Multiplatform 文档](https://www.jetbrains.com/lp/compose-multiplatform/)
2. **书籍**：
   - 《Kotlin Multiplatform Mobile 实战》
   - 《Kotlin 协程实战》（理解异步核心）
3. **课程**：
   - JetBrains Academy：[Kotlin Multiplatform Mobile](https://hyperskill.org/tracks/254)
   - YouTube 频道：Philipp Lackner（KMP 实战教程）
4. **开源项目**：
   - [JetBrains/compose-multiplatform-template](https://github.com/JetBrains/compose-multiplatform-template)（基础模板）
   - [cashapp/sqldelight](https://github.com/cashapp/sqldelight)（跨平台数据库示例）

### **避坑指南**

1. **版本兼容性**：KMP 各依赖（Kotlin 版本、Compose 版本、第三方库）必须严格匹配，否则易出现编译错误。
2. **平台特性边界**：避免过度追求 “100% 代码共享”，保留平台特性（如 Android 权限、iOS 生命周期）的灵活性。
3. **测试先行**：共享代码的 bug 会影响所有平台，需在 `commonTest` 中覆盖核心逻辑。
4. **循序渐进**：从工具类 / 数据层开始共享，再逐步扩展到 UI，避免一开始陷入复杂场景。

按此大纲学习，可在 3-4 个月内掌握 KMP 核心能力，并具备独立开发跨平台项目的能力。重点在于 “边学边练”，每个阶段的实践任务需动手落地，而非仅停留在理论。
