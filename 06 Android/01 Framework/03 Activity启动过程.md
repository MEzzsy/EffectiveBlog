# 🌟总结

1. 应用进程启动：见 [02 应用进程启动过程.md](02 应用进程启动过程.md) 
2. 应用通知AMS application初始化完成
3. AMS确认后处理待启动的Activity并下发启动事务
4. 启动事务在应用进程的binder线程池接收，通过H切换到主线程，然后最终调用`ActivityThread.performLaunchActivity()`
5. 应用主线程准备contextImpl，创建 Activity 实例，绑定 Context、Application 等，并创建 PhoneWindow
6. 最后调用 `Activity.performCreate()` 回调 `onCreate()`

# Application 初始化完成

```
Application.onCreate() 返回
  → handleBindApplication() 继续完成剩余初始化
  → IActivityManager.finishAttachApplication()
```

`finishAttachApplication()` 的作用是：**应用通知 AMS，Application 初始化阶段已完成，可以继续启动等待这个进程的组件了。**

1. **确认进程身份**：根据 PID 找到 `ProcessRecord`，检查 UID 和启动序号 `startSeq`，确保通知属于本次启动的进程。
2. **结束初始化等待**：移除应用绑定的超时消息，将 `pendingFinishAttach` 标记设为 `false`。
3. **继续启动 Activity**：调用 `mAtmInternal.attachApplication()`，由 ATMS 查找等待该进程的 Activity，推进到 `realStartActivityLocked()`，下发启动事务。
4. **处理其他待执行组件**

# 应用主线程执行启动事务

```text
[system_server 进程] 下发启动事务
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

启动事务在binder线程池接收，通过H切换到主线程，然后最终调用`ActivityThread.performLaunchActivity()`。

`performLaunchActivity()` 的以下工作也全部在应用主线程执行：

1. 获取 LoadedApk，**准备 Activity 的 `ContextImpl` 和 ClassLoader**。

   - 为什么需要ClassLoader，因为如果用`Class.forName(name)` ，该方法默认使用直接调用它的那个类的 ClassLoader。此时处于Framework代码，所以会从相应 Framework 类的加载器开始。但Activity属于应用类，会找不到该类。

     - 在应用代码里调用：通常从应用 ClassLoader 开始。

     - **在 **Framework** 代码里调用**：从相应 Framework 类的加载器开始，不会自动选择应用 ClassLoader。
2. 创建 Activity 实例
3. 获取已有 Application，调用 `Activity.attach()` 绑定 Context、Application 等，并创建 PhoneWindow。
4. 调用 `Activity.performCreate()` 回调 `onCreate()`。

```java
private Activity performLaunchActivity(
        ActivityClientRecord record, Intent customIntent) {

    // 1. 获取 LoadedApk，持有应用的代码、资源等信息
    if (record.packageInfo == null) {
        record.packageInfo = getPackageInfo(
                record.activityInfo.applicationInfo,
                mCompatibilityInfo,
                Context.CONTEXT_INCLUDE_CODE);
    }

    // 2. 创建 Activity 的 Context，获取 ClassLoader
    ContextImpl context = createBaseContextForActivity(record);
    ClassLoader loader = context.getClassLoader();

    // 省略组件解析、activity-alias 等处理
    String className = record.intent.getComponent().getClassName();

    // 3. 创建 Activity 实例，此时还没有调用 onCreate()
    Activity page = mInstrumentation.newActivity(
            loader, className, record.intent);

    // 4. 获取 Application，正常启动时复用已经创建好的对象
    Application application =
            record.packageInfo.makeApplicationInner(false, mInstrumentation);

    // 5. 将 Context 与 Activity 关联
    context.setOuterContext(page);

    // 6. 绑定运行环境，内部调用 attachBaseContext() 并创建 PhoneWindow
    // 以下省略了 attach 的其余参数，属于示意写法
    page.attach(context, this, mInstrumentation,
            record.token, record.ident, application, /* 其余参数略 */);

    // 省略主题、配置等准备工作

    // 7. 回调 Activity.onCreate()
    page.mCalled = false;
    record.activity = page;

    // 此处仅展示普通 Bundle 分支
    mInstrumentation.callActivityOnCreate(page, record.state);

    // 8. 检查子类是否调用了 super.onCreate()
    if (!page.mCalled) {
        // 原源码在这里抛出 SuperNotCalledException
    }

    record.setState(ON_CREATE);
    return page;
}
```

其中生命周期调用链是：

```
Instrumentation.callActivityOnCreate()
  → Activity.performCreate()
  → Activity.onCreate()
```

# onStart和onResume

> handleLaunchActivity执行完，TransactionExecutor会继续推进，调用handleStartActivity、handleResumeActivity回调onStart和onResume

新建 Activity 正常进入前台时，**TransactionExecutor 在应用主线程推进状态：`ON_CREATE → ON_START → ON_RESUME`**。

**`onStart()`：执行 Resume 事务前，先补齐 START 状态。**

```
TransactionExecutor.cycleToPath()
  → performLifecycleSequence()
  → ActivityThread.handleStartActivity()
  → Activity.performStart()
  → Instrumentation.callActivityOnStart()
  → Activity.onStart()
```

**`onResume()`：随后执行 `ResumeActivityItem`，进入 RESUME 状态。**

```
ResumeActivityItem.execute()
  → ActivityThread.handleResumeActivity()
  → ActivityThread.performResumeActivity()
  → Activity.performResume()
  → Instrumentation.callActivityOnResume()
  → Activity.onResume()
```
