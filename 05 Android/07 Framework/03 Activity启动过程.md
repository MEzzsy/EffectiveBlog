> 本文以 **AOSP `android-17.0.0_r1`（Android 17）** 为基线，说明普通前台 Activity 的启动流程。
>

# 总结

核心是：系统决定启动哪个 Activity、放入哪个任务，再通知应用主线程创建或恢复页面。**生命周期回调完成与首帧显示是不同阶段。**

1. **调用方进程（通常为主线程）**：发起 `startActivity()`，通过 Binder 请求 ATMS（系统服务）。
2. **system_server 进程**：ATMS（系统服务）解析目标、校验启动条件，决定复用还是新建任务及 Activity。
3. **system_server → Zygote → 应用进程**：目标进程可用则复用；否则通过 Zygote 创建新的应用进程。新的应用进程会做一些初始化操作（比如创建Binder线程池）以及在主线程创建并初始化 Application。
4. **system_server → 应用 Binder 线程 → 应用主线程**：应用进程向 AMS 注册后，系统服务会下发 （启动事务）`ClientTransaction`，通过 H（Handler）切换线程执行。
5. **应用主线程**：然后一步步到应用主线程。先准备 Activity 的 ContextImpl ，然后创建 Activity 实例，将 Activity 实例与 Context 和 Application 绑定并创建 PhoneWindow 。最后回调`onCreate()`。

> **ATMS 从 Android 10（Android Q，API 29）开始引入。**所以，基于 Android 9 及以前的文章，通常会把 Activity 启动管理归到 AMS。

# 进程与线程约定

下文的“应用进程”默认指**目标应用进程**。调用方可以是 Launcher、其他应用，也可以是目标应用自身。

| 执行位置 | 主要工作 |
| --- | --- |
| 调用方进程／调用线程 | 执行 `startActivity()`、Instrumentation；点击事件通常在主线程发起 |
| system_server 进程 | ATMS、AMS、ActivityStarter 等处理调度；Binder 线程接收跨进程请求，部分后续工作转交服务的 Handler 线程 |
| Zygote 进程 | 按需创建或提供应用进程 |
| 应用进程／Binder 线程 | 接收 `bindApplication()`、`scheduleTransaction()`，预处理并投递消息 |
| 应用进程／主线程 | H 分发消息，初始化 Application、创建 Activity、执行生命周期及 View 操作 |

**应用 Binder 线程和应用主线程属于同一个进程。** 图中的 Binder 调用跨进程，H 投递消息完成应用进程内的线程切换；不能把 system_server 中的工作统一理解为“主线程执行”。

# 系统处理启动请求

以 `Activity.startActivity()` 为例，主要调用链为：

```text
[调用方进程／调用线程，通常为主线程]
Activity.startActivity()
  → startActivityForResult()
  → Instrumentation.execStartActivity()
  → IActivityTaskManager.startActivity()       // Binder 跨进程

[system_server 进程／Binder 线程接收本次请求]
ActivityTaskManagerService（ATMS）
  → ActivityStartController → ActivityStarter.execute()
```

`IActivityTaskManager` 对应 **ATMS**。ATMS 负责 Activity、任务及生命周期调度；**AMS** 配合 ProcessList 管理应用进程。两者均位于 `system_server`，彼此协作属于进程内调用或 Handler 调度。参见 [Instrumentation][instrumentation] 和 [ATMS][atms]。

**【system_server 进程】** ActivityStarter 解析 Intent，检查权限、组件可访问性及后台启动限制，并结合 `launchMode`、Intent flags、`taskAffinity` 等确定目标任务。**Task** 和 **ActivityRecord** 均为该进程中的系统侧记录。参见 [ActivityStarter][starter]。

**`FLAG_ACTIVITY_NEW_TASK` 不保证新建任务**：系统可能复用已有任务，甚至直接将其移到前台。是否创建 Activity 实例、是否回调 `onNewIntent()`，还取决于启动模式和已有栈状态。参见 [任务与返回栈](https://developer.android.com/guide/components/activities/tasks-and-back-stack)。

# 目标进程准备

**【system_server 进程】** `ActivityTaskSupervisor.startSpecificActivity()` 检查目标进程及其 `IApplicationThread` 是否可用：

- **可用**：进入 `realStartActivityLocked()`，安排 Activity 启动。
- **不可用**：通过系统服务的 Handler 安排 AMS 启动进程；若进程正在启动，则等待其注册。

需要新进程时，主要边界如下：

```text
[system_server] AMS / ProcessList
  ── Socket ──→ [Zygote] 创建或提供应用进程
[应用进程／主线程] ActivityThread.main() → attach()
  ── Binder ──→ [system_server／Binder 线程] AMS.attachApplication()
  ── Binder ──→ [应用进程／Binder 线程] ApplicationThread.bindApplication()
  ── H.BIND_APPLICATION 消息 ──→ [应用进程／主线程] handleBindApplication()
      → 创建 Application → Application.onCreate()
```

**【应用进程／主线程】** 正常创建 Activity 时，Application 通常已初始化，**不会每启动一个 Activity 就重新创建**。参见 [ActivityTaskSupervisor][supervisor]、[ActivityThread][activity-thread]；进程创建细节见 [应用进程启动过程](<02 应用进程启动过程.md>)。

# 应用主线程执行启动事务

**【system_server 进程】** 系统通过 ClientLifecycleManager 将启动操作封装进 **ClientTransaction**。对于新建后需要进入前台的 Activity，包含 `LaunchActivityItem` 和 `ResumeActivityItem`。参见 [系统侧事务构造][supervisor]。

```text
[system_server 进程]
ClientTransaction.schedule()
  → IApplicationThread.scheduleTransaction()  // Binder 跨进程

[应用进程／Binder 线程]
ApplicationThread.scheduleTransaction()
  → ClientTransactionHandler.scheduleTransaction()
  → transaction.preExecute()
  → 发送 H.EXECUTE_TRANSACTION 消息             // 进程内切换线程

[应用进程／主线程]
H.handleMessage() → TransactionExecutor.execute()
  → LaunchActivityItem.execute()
  → ActivityThread.handleLaunchActivity()
  → ActivityThread.performLaunchActivity()
```

这是现代版本的调用路径，旧文中的 `scheduleLaunchActivity()` 已不适用。**ApplicationThread 是应用侧的 Binder 接口实现，不是一条线程**；system_server 持有它的远程代理。ActivityThread 也不继承 Thread：它负责主线程调度，但其继承的 `scheduleTransaction()` 在上述路径中由 Binder 线程调用，**不能仅凭类名判断执行线程**。参见 [ClientTransactionHandler][transaction-handler] 和 [ActivityThread][activity-thread]。

**【应用进程／主线程】** `LaunchActivityItem.execute()` 创建 **ActivityClientRecord**，保存应用侧的 Activity 状态，再执行启动。`performLaunchActivity()` 的以下工作也全部在应用主线程执行：

1. 获取 **LoadedApk**，准备 Activity 的 `ContextImpl` 和 ClassLoader。
2. 经 `Instrumentation.newActivity()` → `AppComponentFactory.instantiateActivity()` 创建 Activity 实例。
3. 获取已有 Application，调用 `Activity.attach()` 绑定 Context、Application 等，并创建 PhoneWindow。
4. 经 `Instrumentation.callActivityOnCreate()` → `Activity.performCreate()` 回调 `onCreate()`。

参见 [LaunchActivityItem][launch-item]、[Instrumentation][instrumentation]、[Activity][activity] 和 [LoadedApk][loaded-apk]。

**【应用进程／主线程】** 随后 TransactionExecutor 根据目标状态补齐生命周期：先经 `handleStartActivity()` 调用 `onStart()`，再执行 ResumeActivityItem，经 `handleResumeActivity()` 调用 `onResume()`。这属于**新实例正常进入前台**的路径；复用已有实例时，不一定再次执行 `onCreate()`，收到新 Intent 时的 `onNewIntent()` 也在主线程回调。参见 [TransactionExecutor][executor] 和 [ActivityThread][activity-thread]。

# 从生命周期到首帧

正常首次显示时，各阶段的执行位置不同：

- **应用进程／主线程**：`handleResumeActivity()` 调用应用侧 WindowManager 添加 DecorView，由 ViewRootImpl 安排 View 的测量、布局与绘制。
- **system_server 进程**：WindowManagerService（WMS）通过 Binder 接收窗口请求，管理窗口；应用侧 WindowManager 与 WMS 位于不同进程。
- **应用进程／RenderThread**：常规硬件加速路径中，配合 GPU 完成渲染；它与主线程、Binder 线程不同。
- **SurfaceFlinger 独立进程**：接收图形缓冲区，配合硬件合成器完成合成与显示。

因此，**`onCreate()` 或 `onResume()` 返回，都不能直接当作首帧已经显示**。参见 [ActivityThread][activity-thread]、[渲染线程说明](https://source.android.com/docs/core/tests/debug/systrace) 和 [SurfaceFlinger 与 WindowManager](https://source.android.com/docs/core/graphics/surfaceflinger-windowmanager)。

- **TTID**：应用首帧显示耗时。
- **TTFD**：应用主要内容加载并达到可用状态的耗时，由应用主线程通过 `reportFullyDrawn()` 等机制向系统报告。参见 [启动耗时说明](https://developer.android.com/topic/performance/vitals/launch-time)。

Android 12 起，系统提供 SplashScreen。**初始启动窗口由 system_server 发起创建，WM Shell（通常位于 SystemUI 进程）的启动画面线程负责显示**；看到启动画面不代表应用内容已绘制完成。参见 [StartingWindowController][starting-window] 和 [SplashScreen](https://developer.android.com/develop/ui/views/launch/splash-screen)。

# 两个容易混淆的边界

- **进程数量不固定**：同进程页面跳转主要涉及应用与 system_server；跨应用启动还涉及目标进程，冷启动再涉及 Zygote。不能简单按“根 Activity 四个、普通 Activity 两个”记忆。
- **发起请求不保证页面出现**：system_server 中的启动决策还受权限、任务复用及后台启动限制影响。Android 10 起限制后台启动 Activity，后续版本继续收紧相关规则。参见 [后台启动限制](https://developer.android.com/guide/components/activities/secure-bal)。

[instrumentation]: https://android.googlesource.com/platform/frameworks/base/+/refs/tags/android-17.0.0_r1/core/java/android/app/Instrumentation.java
[atms]: https://android.googlesource.com/platform/frameworks/base/+/refs/tags/android-17.0.0_r1/services/core/java/com/android/server/wm/ActivityTaskManagerService.java
[starter]: https://android.googlesource.com/platform/frameworks/base/+/refs/tags/android-17.0.0_r1/services/core/java/com/android/server/wm/ActivityStarter.java
[supervisor]: https://android.googlesource.com/platform/frameworks/base/+/refs/tags/android-17.0.0_r1/services/core/java/com/android/server/wm/ActivityTaskSupervisor.java
[activity-thread]: https://android.googlesource.com/platform/frameworks/base/+/refs/tags/android-17.0.0_r1/core/java/android/app/ActivityThread.java
[transaction-handler]: https://android.googlesource.com/platform/frameworks/base/+/refs/tags/android-17.0.0_r1/core/java/android/app/ClientTransactionHandler.java
[launch-item]: https://android.googlesource.com/platform/frameworks/base/+/refs/tags/android-17.0.0_r1/core/java/android/app/servertransaction/LaunchActivityItem.java
[activity]: https://android.googlesource.com/platform/frameworks/base/+/refs/tags/android-17.0.0_r1/core/java/android/app/Activity.java
[loaded-apk]: https://android.googlesource.com/platform/frameworks/base/+/refs/tags/android-17.0.0_r1/core/java/android/app/LoadedApk.java
[executor]: https://android.googlesource.com/platform/frameworks/base/+/refs/tags/android-17.0.0_r1/core/java/android/app/servertransaction/TransactionExecutor.java
[starting-window]: https://android.googlesource.com/platform/frameworks/base/+/refs/tags/android-17.0.0_r1/libs/WindowManager/Shell/src/com/android/wm/shell/startingsurface/StartingWindowController.java
