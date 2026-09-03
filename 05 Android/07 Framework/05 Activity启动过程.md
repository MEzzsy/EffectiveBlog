> 本文以 **AOSP `android-17.0.0_r1`（Android 17）** 为基线，说明普通前台 Activity 的启动流程。
>

# 总结

核心是：系统决定启动哪个 Activity、放入哪个任务，再通知应用主线程创建或恢复页面。**生命周期回调完成与首帧显示是不同阶段。**

1. 调用方发起 `startActivity()`，通过 Binder 请求 ATMS。
2. ATMS 解析目标、校验启动条件，决定复用还是新建任务及 Activity。
3. 目标进程可用则复用；否则由 AMS 配合 Zygote 准备进程，完成应用初始化。
4. 系统下发 `ClientTransaction`，应用通过 H（Handler）切到主线程执行。
5. 新建 Activity 通常依次执行 `onCreate()`、`onStart()`、`onResume()`，随后完成窗口显示与首帧绘制。

> **ATMS 从 Android 10（Android Q，API 29）开始引入。**所以，基于 Android 9 及以前的文章，通常会把 Activity 启动管理归到 AMS。

# 系统处理启动请求

以 `Activity.startActivity()` 为例，主要调用链为：

```text
Activity.startActivity()
  → startActivityForResult()
  → Instrumentation.execStartActivity()
  → IActivityTaskManager.startActivity()       // Binder
  → ActivityTaskManagerService（ATMS）
  → ActivityStartController → ActivityStarter.execute()
```

`IActivityTaskManager` 对应 **ATMS**。ATMS 负责 Activity、任务及生命周期调度；**AMS** 配合 ProcessList 管理应用进程。两者均位于 `system_server`。参见 [Instrumentation][instrumentation] 和 [ATMS][atms]。

ActivityStarter 解析 Intent，检查权限、组件可访问性及后台启动限制，并结合 `launchMode`、Intent flags、`taskAffinity` 等确定目标任务。现代源码使用 **Task** 表示任务，**ActivityRecord** 表示系统侧的 Activity 记录。参见 [ActivityStarter][starter]。

**`FLAG_ACTIVITY_NEW_TASK` 不保证新建任务**：系统可能复用已有任务，甚至直接将其移到前台。是否创建 Activity 实例、是否回调 `onNewIntent()`，还取决于启动模式和已有栈状态。参见 [任务与返回栈](https://developer.android.com/guide/components/activities/tasks-and-back-stack)。

# 目标进程准备

`ActivityTaskSupervisor.startSpecificActivity()` 检查目标进程及其 `IApplicationThread` 是否可用：

- **可用**：进入 `realStartActivityLocked()`，安排 Activity 启动。
- **不可用**：请求 AMS 启动进程；若进程正在启动，则等待其注册。普通路径由 AMS 经 Socket 请求 Zygote，应用进入 `ActivityThread.main()`，再通过 Binder 向 AMS 注册 `ApplicationThread`。

AMS 通过 `bindApplication()` 安排应用初始化，主线程执行 `handleBindApplication()`，创建 Application 并调用其 `onCreate()`。正常启动 Activity 时，Application 通常已初始化，**不会每启动一个 Activity 就重新创建**。参见 [ActivityTaskSupervisor][supervisor]、[ActivityThread][activity-thread]；进程创建细节见 [应用进程启动过程](<04 应用进程启动过程.md>)。

# 应用主线程执行启动事务

系统通过 ClientLifecycleManager 将启动操作封装进 **ClientTransaction**。对于新建后需要进入前台的 Activity，包含 `LaunchActivityItem` 和 `ResumeActivityItem`。参见 [系统侧事务构造][supervisor]。

```text
system_server：ClientTransaction.schedule()
  → IApplicationThread.scheduleTransaction()  // Binder
应用 Binder 线程：ApplicationThread 接收，发送 H.EXECUTE_TRANSACTION
应用主线程：TransactionExecutor.execute()
  → LaunchActivityItem.execute()
  → ActivityThread.handleLaunchActivity()
  → ActivityThread.performLaunchActivity()
```

这是现代版本的调用路径，旧文中的 `scheduleLaunchActivity()` 已不适用。**ApplicationThread 是应用侧的 Binder 接口实现，不是一条线程**；system_server 持有它的远程代理。ActivityThread 也不继承 Thread，它是主线程上的框架调度对象。参见 [ClientTransactionHandler][transaction-handler] 和 [ActivityThread][activity-thread]。

`LaunchActivityItem.execute()` 在主线程创建 **ActivityClientRecord**，保存应用侧的 Activity 状态，再执行启动。`performLaunchActivity()` 的核心工作如下：

1. 获取 **LoadedApk**（原文误写为 LoadApk），准备 Activity 的 `ContextImpl` 和 ClassLoader。
2. 经 `Instrumentation.newActivity()` → `AppComponentFactory.instantiateActivity()` 创建 Activity 实例。
3. 获取已有 Application，调用 `Activity.attach()` 绑定 Context、Application 等，并创建 PhoneWindow。
4. 经 `Instrumentation.callActivityOnCreate()` → `Activity.performCreate()` 回调 `onCreate()`。

参见 [LaunchActivityItem][launch-item]、[Instrumentation][instrumentation]、[Activity][activity] 和 [LoadedApk][loaded-apk]。

随后 TransactionExecutor 根据目标状态补齐生命周期：先经 `handleStartActivity()` 调用 `onStart()`，再执行 ResumeActivityItem，经 `handleResumeActivity()` 调用 `onResume()`。这属于**新实例正常进入前台**的路径；复用已有实例时，不一定再次执行 `onCreate()`。参见 [TransactionExecutor][executor]。

# 从生命周期到首帧

正常首次显示时，`handleResumeActivity()` 会将 DecorView 添加到 WindowManager，后续由 ViewRootImpl 等完成布局与绘制。因此，**`onCreate()` 或 `onResume()` 返回，都不能直接当作首帧已经显示**。参见 [ActivityThread][activity-thread]。

- **TTID**：应用首帧显示耗时。
- **TTFD**：应用主要内容加载并达到可用状态的耗时，由应用通过 `reportFullyDrawn()` 等机制报告。参见 [启动耗时说明](https://developer.android.com/topic/performance/vitals/launch-time)。

Android 12 起，系统提供 SplashScreen 启动画面；看到启动画面不代表 Activity 的内容已绘制完成。参见 [SplashScreen](https://developer.android.com/develop/ui/views/launch/splash-screen)。

# 两个容易混淆的边界

- **进程数量不固定**：同进程页面跳转主要涉及应用与 system_server；跨应用启动还涉及目标进程，冷启动再涉及 Zygote。不能简单按“根 Activity 四个、普通 Activity 两个”记忆。
- **发起请求不保证页面出现**：启动还受权限、任务复用及后台启动限制影响。Android 10 起限制后台启动 Activity，后续版本继续收紧相关规则。参见 [后台启动限制](https://developer.android.com/guide/components/activities/secure-bal)。

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
