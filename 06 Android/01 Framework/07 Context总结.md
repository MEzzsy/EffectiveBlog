# 核心关系

`Context` 是访问 Android 应用环境的抽象入口，用于读取资源、操作文件、启动组件、获取系统服务等。不同 Context 关联的生命周期、主题、配置和窗口环境可能不同。

| 类 | 作用 |
| --- | --- |
| `ContextImpl` | Framework 内部的主要实现，负责资源、存储及系统服务访问等基础能力 |
| `ContextWrapper` | 持有基础 Context（`mBase`），默认将调用委托给它，子类可以修改行为 |
| `ContextThemeWrapper` | 在包装基础上增加主题等 UI 相关能力 |

`Application` 继承 `ContextWrapper`，`Activity` 继承 `ContextThemeWrapper`，因此它们本身都是 Context。这体现了装饰模式：通过包装复用基础能力，并在外层扩展行为；不能理解成组件自身完全没有实现能力。[ContextWrapper 文档](https://developer.android.com/reference/android/content/ContextWrapper)、[ContextThemeWrapper 文档](https://developer.android.com/reference/android/view/ContextThemeWrapper)

# 创建与获取

以下按 **AOSP Android 16（`android-16.0.0_r1`）** 的普通应用流程整理，省略特殊分支。

| 对象 | 创建与绑定的主线 |
| --- | --- |
| Application | 通常在 `ActivityThread.handleBindApplication()` 中调用 `LoadedApk.makeApplicationInner()`；先创建 `ContextImpl`，再经 `Instrumentation`、`AppComponentFactory` 实例化 Application，调用 `Application.attach()` |
| Activity | `ActivityThread.performLaunchActivity()` 通过 `createBaseContextForActivity()` 创建 Activity 的 `ContextImpl`，实例化 Activity 后调用 `Activity.attach()` |

二者的 `attach()` 最终通过 `attachBaseContext()` 保存 `mBase`；框架还会设置 `ContextImpl.mOuterContext`，引用外层组件。绑定发生在 `onCreate()` 之前，组件构造阶段不应依赖尚未绑定的 Context 能力。[ActivityThread 源码](https://android.googlesource.com/platform/frameworks/base/+/android-16.0.0_r1/core/java/android/app/ActivityThread.java)

Application 通常在应用绑定阶段就已创建，Activity 启动时会复用它。现代调用路径经过 `makeApplicationInner()` 和组件工厂，不能照搬旧文中“`newApplication()` 两个重载最终都调用同一个反射方法”的结论。[LoadedApk 源码](https://android.googlesource.com/platform/frameworks/base/+/android-16.0.0_r1/core/java/android/app/LoadedApk.java#1409)、[Instrumentation 源码](https://android.googlesource.com/platform/frameworks/base/+/android-16.0.0_r1/core/java/android/app/Instrumentation.java#1343)

- **`getApplicationContext()`**：普通应用中返回当前进程已创建的 Application 对象，通常经 `mBase` 委托给 `ContextImpl`，再从 `LoadedApk` 取出。
- **`getBaseContext()`**：返回包装对象直接持有的 `mBase`；它可能仍是另一层包装，不等同于 Application。

两者分别用于取得应用级上下文和查看直接包装的上下文。[ContextImpl 源码](https://android.googlesource.com/platform/frameworks/base/+/android-16.0.0_r1/core/java/android/app/ContextImpl.java#475)、[ContextWrapper 源码](https://android.googlesource.com/platform/frameworks/base/+/android-16.0.0_r1/core/java/android/content/ContextWrapper.java#106)

# 使用时如何选择

| 场景 | 选择原则 |
| --- | --- |
| 数据库、文件操作、不依赖页面的长期对象 | 通常使用 Application Context，避免长期对象持有 Activity 而造成内存泄漏 |
| 页面布局、View、普通页面 Dialog | 使用当前 Activity 或基于它的主题 Context，以匹配页面主题、配置和窗口环境 |
| 非 Activity 窗口，如悬浮窗 | Android 11（API 30）起可使用 `createWindowContext()`，关联相应显示区域和窗口类型 |

Application Context 的生命周期通常与进程一致，但不能替代所有 UI Context；在分屏、折叠屏等场景中，其资源配置可能不对应当前页面区域。[Context 文档](https://developer.android.com/reference/android/content/Context#createWindowContext(int,%20android.os.Bundle))

从 Application 等非 Activity Context 调用 `startActivity()`，通常需要 `FLAG_ACTIVITY_NEW_TASK`；添加该标志后，启动行为仍受系统后台启动 Activity 的限制。[startActivity 文档](https://developer.android.com/reference/android/content/Context#startActivity(android.content.Intent))、[后台启动限制](https://developer.android.com/guide/components/activities/secure-bal)

# 系统服务的获取

常见委托路径为：`ContextWrapper.getSystemService()` → `ContextImpl.getSystemService()` → `SystemServiceRegistry` → 对应的 `ServiceFetcher`。

`SystemServiceRegistry` 注册服务名称、类型与获取器的映射。调用时通常按需取得或创建应用进程中的 Manager，再按获取器策略缓存；真正的系统端服务通常由系统进程管理，Manager 可通过 Binder 访问它。[SystemServiceRegistry 源码](https://android.googlesource.com/platform/frameworks/base/+/android-16.0.0_r1/core/java/android/app/SystemServiceRegistry.java)

- **`CachedServiceFetcher`**：使用 `ContextImpl.mServiceCache`，按基础 Context 缓存。多个 Wrapper 共享同一个基础 Context 时，也会共享这层缓存。
- **`StaticServiceFetcher`**：在获取器中保存实例，供应用进程内共享。

因此，不能一概认为“不同 Context 一定获得不同的系统服务对象”；还要区分客户端 Manager 与系统端服务。上述两种缓存策略均可在源码中看到。[缓存实现](https://android.googlesource.com/platform/frameworks/base/+/android-16.0.0_r1/core/java/android/app/SystemServiceRegistry.java#2281)

组件也可能覆写获取逻辑。例如 Activity 获取 `WINDOW_SERVICE` 时直接返回自身的 `mWindowManager`，并非每次都走 Registry。[Activity 源码](https://android.googlesource.com/platform/frameworks/base/+/android-16.0.0_r1/core/java/android/app/Activity.java#7884)

# Context 数量

**不能仅按组件实例数量计算进程内所有 Context 对象的数量。** 普通应用通常每个进程有一个 Application，各 Activity 实例又有自己的基础 Context；此外还存在底层 `ContextImpl`、额外的 Wrapper，以及 `createConfigurationContext()`、`createWindowContext()` 等产生的 Context。多进程也不会共享同一个 Application 对象。[Context 文档](https://developer.android.com/reference/android/content/Context)
