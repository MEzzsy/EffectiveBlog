# 实验准备

本文保留原有实测日志，文末的[典型对照实验](#典型对照实验)用于继续验证。新增实验中的回调是**预期行为或示意序列，不是本次设备实测日志**。

## 控制实验条件

- 使用普通、不透明、全屏 Activity，关闭开发者选项中的“不保留活动”，先不引入旋转屏幕、多窗口和进程回收。
- 每次点击后等待页面切换和日志稳定，再执行下一步。每轮实验清理测试应用的旧任务，重新建立指定的初始栈。
- 记录设备 Android/API 版本、`targetSdk`、Manifest 中的 `launchMode` / `taskAffinity`、实际启动 flags。原有日志未记录这些信息，不能据此断言所有版本的回调交错顺序都相同。
- 除特别注明外，均从当前 Activity 调用 `startActivity(Intent(this, TargetActivity::class.java))`，不加 flags，也不调用 `finish()`。
- `M` 表示入口 `MainActivity`；`A` 表示被测试的 `AActivity`；`B`、`C` 是两个不同的普通 `standard` Activity。`[M, A₁, B]` 从左到右表示栈底到栈顶，`A₁`、`A₂` 是同一个 Activity 类的不同对象。
- 默认所有 Activity 使用应用默认 affinity；需要独立任务的实验会单独注明。`T1`、`T2` 是任务的示意名称，实际以 `taskId` 为准。

## 统一日志字段

给测试 Activity 加上下面的辅助方法，并在 `onCreate`、`onStart`、`onResume`、`onPause`、`onStop`、`onRestart`、`onDestroy` 中调用 `trace("回调名")`。各回调仍需正常调用对应的 `super` 方法。

```kotlin
// 放在公共测试 Activity 基类中；不把这个标识保存到 savedInstanceState。
private val instanceId = java.util.UUID.randomUUID().toString()

protected fun trace(event: String, incoming: Intent? = null) {
    val observedIntent = incoming ?: intent
    Log.d(
        "LaunchMode",
        "${javaClass.simpleName} instance=$instanceId " +
            "pid=${android.os.Process.myPid()} task=$taskId " +
            "event=$event finishing=$isFinishing " +
            "changingConfig=$isChangingConfigurations " +
            "request=${observedIntent?.getStringExtra("request")} " +
            "flags=${observedIntent?.flags?.let { Integer.toHexString(it) }}"
    )
}

override fun onNewIntent(newIntent: Intent) {
    super.onNewIntent(newIntent)
    trace("onNewIntent", newIntent)
    setIntent(newIntent)
    // 如果页面依赖启动参数，在这里同步更新页面内容。
}
```

每次启动可以传入不同的 `request`（如 `first`、`second`），验证新参数究竟由哪个实例接收。`onNewIntent()` 的参数是新 Intent；`getIntent()` 默认仍返回旧值，需要时通过 `setIntent()` 更新。官方只保证新 Intent 不在 resumed 状态交付，并且之后会调用 `onResume()`，不应给它与 `onRestart()` / `onStart()` 写死唯一的相对顺序。参见 [Activity.onNewIntent](https://developer.android.com/reference/android/app/Activity#onNewIntent(android.content.Intent))。

配合以下命令观察日志和真实任务结构：

```shell
adb logcat -v threadtime -s LaunchMode
adb shell dumpsys activity activities
```

重点区分三个问题：**对象是否复用看 instanceId，任务是否相同看 taskId，已有实例是否接收新的启动 Intent 看 onNewIntent。**

# singleTop

## 中途启动Standard

```
// 启动默认任务栈-SingleTop
I/启动模式-默认任务栈-SingleTop: onCreate: 251716135
I/启动模式-默认任务栈-SingleTop: onStart: 251716135
I/启动模式-默认任务栈-SingleTop: onResume: 251716135

// 启动默认任务栈-Standard
I/启动模式-默认任务栈-SingleTop: onPause: 251716135
I/启动模式-默认任务栈-Standard: onCreate: 182131432
I/启动模式-默认任务栈-Standard: onStart: 182131432
I/启动模式-默认任务栈-Standard: onResume: 182131432
I/启动模式-默认任务栈-SingleTop: onStop: 251716135

// 启动默认任务栈-SingleTop
I/启动模式-默认任务栈-Standard: onPause: 182131432
I/启动模式-默认任务栈-SingleTop: onCreate: 32330684
I/启动模式-默认任务栈-SingleTop: onStart: 32330684
I/启动模式-默认任务栈-SingleTop: onResume: 32330684
I/启动模式-默认任务栈-Standard: onStop: 182131432
```

## 连续两次启动SingleTop

```
// 启动默认任务栈-SingleTop
I/启动模式-默认任务栈-SingleTop: onCreate: 33756001
I/启动模式-默认任务栈-SingleTop: onStart: 33756001
I/启动模式-默认任务栈-SingleTop: onResume: 33756001

// 启动默认任务栈-SingleTop
I/启动模式-默认任务栈-SingleTop: onPause: 33756001
I/启动模式-默认任务栈-SingleTop: onNewIntent: 33756001
I/启动模式-默认任务栈-SingleTop: onResume: 33756001
```

# singleTask

## 相同任务栈

### 中途启动Standard

```
// 启动默认任务栈-SingleTask
I/启动模式-默认任务栈-SingleTask: onCreate: 175995576
I/启动模式-默认任务栈-SingleTask: onStart: 175995576
I/启动模式-默认任务栈-SingleTask: onResume: 175995576

// 启动默认任务栈-Standard
I/启动模式-默认任务栈-SingleTask: onPause: 175995576
I/启动模式-默认任务栈-Standard: onCreate: 203808398
I/启动模式-默认任务栈-Standard: onStart: 203808398
I/启动模式-默认任务栈-Standard: onResume: 203808398
I/启动模式-默认任务栈-SingleTask: onStop: 175995576

// 启动默认任务栈-SingleTask
I/启动模式-默认任务栈-Standard: onPause: 203808398
I/启动模式-默认任务栈-SingleTask: onRestart: 175995576
I/启动模式-默认任务栈-SingleTask: onStart: 175995576
I/启动模式-默认任务栈-SingleTask: onNewIntent: 175995576
I/启动模式-默认任务栈-SingleTask: onResume: 175995576
I/启动模式-默认任务栈-Standard: onStop: 203808398
I/启动模式-默认任务栈-Standard: onDestroy: 203808398
```

### 连续两次启动SingleTask

```
// 启动默认任务栈-SingleTask
I/启动模式-默认任务栈-SingleTask: onCreate: 104648595
I/启动模式-默认任务栈-SingleTask: onStart: 104648595
I/启动模式-默认任务栈-SingleTask: onResume: 104648595

// 启动默认任务栈-SingleTask
I/启动模式-默认任务栈-SingleTask: onPause: 104648595
I/启动模式-默认任务栈-SingleTask: onNewIntent: 104648595
I/启动模式-默认任务栈-SingleTask: onResume: 104648595
```

## 自定义 taskAffinity（需核对 taskId）

```
// 启动自定义任务栈-SingleTask
I/启动模式-自定义任务栈-SingleTask: onCreate: 119732331
I/启动模式-自定义任务栈-SingleTask: onStart: 119732331
I/启动模式-自定义任务栈-SingleTask: onResume: 119732331

// 启动默认任务栈-Standard
I/启动模式-自定义任务栈-SingleTask: onPause: 119732331
I/启动模式-默认任务栈-Standard: onCreate: 147209858
I/启动模式-默认任务栈-Standard: onStart: 147209858
I/启动模式-默认任务栈-Standard: onResume: 147209858
I/启动模式-自定义任务栈-SingleTask: onStop: 119732331

// 启动自定义任务栈-SingleTask
I/启动模式-默认任务栈-Standard: onPause: 147209858
I/启动模式-自定义任务栈-SingleTask: onRestart: 119732331
I/启动模式-自定义任务栈-SingleTask: onStart: 119732331
I/启动模式-自定义任务栈-SingleTask: onNewIntent: 119732331
I/启动模式-自定义任务栈-SingleTask: onResume: 119732331
I/启动模式-默认任务栈-Standard: onStop: 147209858
I/启动模式-默认任务栈-Standard: onDestroy: 147209858
```

当时在最近任务界面观察到了两个卡片。但这组日志没有记录 `taskId`，不能仅凭“默认任务栈”和“自定义任务栈”的标签断定两个 Activity 分属不同任务。若 Standard 是由 SingleTask 无 flags 启动的，它通常仍进入 SingleTask 所在的任务。

最近任务卡片可作为辅助观察，但也存在被排除展示的任务；任务划分应以 `taskId` 和 `dumpsys` 为准。参见 [Recents screen](https://developer.android.com/guide/components/activities/recents)。

# singleInstance

该singleInstance自定义任务栈

```xml
<activity
    android:name=".basic.activity.launchmode.SingleInstanceActivity"
    android:launchMode="singleInstance"
    android:taskAffinity="com.mezzsy.singleInstance" />
```

## 启动默认任务栈standard

```
// 启动SingleInstance
I/启动模式-SingleInstance: onCreate: 99726090
I/启动模式-SingleInstance: onStart: 99726090
I/启动模式-SingleInstance: onResume: 99726090

// 启动默认任务栈-Standard
I/启动模式-SingleInstance: onPause: 99726090
I/启动模式-默认任务栈-Standard: onCreate: 17426934
I/启动模式-默认任务栈-Standard: onStart: 17426934
I/启动模式-默认任务栈-Standard: onResume: 17426934
I/启动模式-SingleInstance: onStop: 99726090
```

使用命令**adb shell dumpsys activity activities**可进行查看任务栈情况。

任务栈情况（省略了一些信息）

```
Hist #4: ActivityRecord{18ba9e1 u0 com.mezzsy.myapplication/.basic.activity.launchmode.DefaultTaskStandardActivity t10890}
taskAffinity=10336:com.mezzsy.myapplication

Hist #3: ActivityRecord{2a490e9 u0 com.mezzsy.myapplication/.basic.activity.launchmode.TestLaunchModeActivity t10890}
taskAffinity=10336:com.mezzsy.myapplication

Hist #2: ActivityRecord{a8c931a u0 com.mezzsy.myapplication/.basic.activity.MainActActivity t10890}
taskAffinity=10336:com.mezzsy.myapplication

Hist #1: ActivityRecord{f649c11 u0 com.mezzsy.myapplication/.basic.MainBasicActivity t10890}
taskAffinity=10336:com.mezzsy.myapplication

Hist #0: ActivityRecord{8662938 u0 com.mezzsy.myapplication/.MainActivity t10890}
taskAffinity=10336:com.mezzsy.myapplication
```

```
Hist #0: ActivityRecord{ec9ddb8 u0 com.mezzsy.myapplication/.basic.activity.launchmode.SingleInstanceActivity t10891}
taskAffinity=10336:com.mezzsy.singleInstance
```

singleInstance 所在的任务只容纳它自身。这次实测中，它启动的 Standard 进入了默认 affinity 对应的已有任务；可推广的结论是“进入其他任务”，不能推广为“必然进入默认任务”。

## 启动相同 taskAffinity 的 SingleTask

```xml
<activity
            android:name=".basic.activity.launchmode.SingleInstanceTaskSingleTaskActivity"
            android:launchMode="singleTask"
            android:taskAffinity="com.mezzsy.singleInstance" />
```

SingleTask 和 SingleInstance 配置了相同的 `taskAffinity`。它表示任务归属偏好，不是任务的唯一名称。

```
I/启动模式-SingleInstance: onCreate: 264642248
I/启动模式-SingleInstance: onStart: 264642248
I/启动模式-SingleInstance: onResume: 264642248

I/启动模式-SingleInstance: onPause: 264642248
I/启动模式-SingleInstance任务栈-SingleTask: onCreate: 147472241
I/启动模式-SingleInstance任务栈-SingleTask: onStart: 147472241
I/启动模式-SingleInstance任务栈-SingleTask: onResume: 147472241
I/启动模式-SingleInstance: onStop: 264642248
```

任务栈情况

```
Hist #0: ActivityRecord{140ab6 u0 com.mezzsy.myapplication/.basic.activity.launchmode.SingleInstanceTaskSingleTaskActivity t10908}
taskAffinity=10336:com.mezzsy.singleInstance
```

```
Hist #0: ActivityRecord{8a887e u0 com.mezzsy.myapplication/.basic.activity.launchmode.SingleInstanceActivity t10907}
taskAffinity=10336:com.mezzsy.singleInstance
```

```
Hist #3: ActivityRecord{39dcc91 u0 com.mezzsy.myapplication/.basic.activity.launchmode.TestLaunchModeActivity t10906}
taskAffinity=10336:com.mezzsy.myapplication

Hist #2: ActivityRecord{348e622 u0 com.mezzsy.myapplication/.basic.activity.MainActActivity t10906}
taskAffinity=10336:com.mezzsy.myapplication

Hist #1: ActivityRecord{1e41f09 u0 com.mezzsy.myapplication/.basic.MainBasicActivity t10906}
taskAffinity=10336:com.mezzsy.myapplication

Hist #0: ActivityRecord{74985c9 u0 com.mezzsy.myapplication/.MainActivity t10906}
taskAffinity=10336:com.mezzsy.myapplication
```

虽然 SingleTask 和 SingleInstance 的 `taskAffinity` 相同，但它们的 `taskId` 分别为 10908 和 10907，因此属于不同任务。SingleInstance 独占任务的规则不会因为 affinity 相同而失效。

## 启动自身

```
// 启动SingleInstance
I/启动模式-SingleInstance: onCreate: 144933531
I/启动模式-SingleInstance: onStart: 144933531
I/启动模式-SingleInstance: onResume: 144933531

// 启动SingleInstance
I/启动模式-SingleInstance: onPause: 144933531
I/启动模式-SingleInstance: onNewIntent: 144933531
I/启动模式-SingleInstance: onResume: 144933531
```



# 清栈时多个实例的回调顺序

主 Activity 在默认栈，ABC 在另一个栈。以下保留原始日志；原记录没有附上完整 Manifest 和 flags，复现时应补齐。文末的 singleTask 清栈实验给出了明确配置。

主Activity启动A，A启动B，B启动C：

```
log:
A: onCreate: 
A: onStart: 
A: onResume: 
A: onPause: 
B: onCreate: 
B: onStart: 
B: onResume: 
A: onStop: 
B: onPause: 
C: onCreate: 
C: onStart: 
C: onResume: 
B: onStop: 
```

C启动A：

```
log:
B: onDestroy: 
C: onPause: 
A: onNewIntent: 
A: onRestart: 
A: onStart: 
A: onResume: 
C: onStop: 
C: onDestroy: 
```

此时栈为 `[A, B, C]`，C 在栈顶。这次日志显示 B 的 `onDestroy()` 先执行，但不能把回调先后直接解释成内部出栈操作的先后。

```
log:
B: onDestroy: 
C: onDestroy: 
D: onPause: 
A: onNewIntent: 
A: onRestart: 
A: onStart: 
A: onResume: 
D: onStop: 
D: onDestroy: 
```

再加入 D，栈为 `[A, B, C, D]`，由 D 启动 A，得到上面的日志。此时 B、C 已经 stopped，而 D 仍是前台实例，因此它们到达销毁状态所需的回调不同。可以确认的是 B、C、D 最终被结束，A 被复用；这组日志不足以得出“DCB 依次出栈，但 onDestroy 固定反序执行”的规则。

# 典型对照实验

以下实验重点观察同一实例的状态变化。除特别给出的简单序列外，不把多个 Activity 的回调整合成一条必须严格匹配的日志。

## singleTask：复用被其他页面覆盖的实例

为使初始任务结构明确，给 A 配置独立 affinity，并确保开始时没有该 affinity 的旧任务：

```xml
<activity
    android:name=".AActivity"
    android:launchMode="singleTask"
    android:taskAffinity="${applicationId}.launchmode.a"
    android:exported="false" />
```

M 启动 A，A 启动 B，B 启动 C，最后 C 启动 A。B、C 保持 `standard`，不加 flags，也不主动结束。

```text
最后一步之前：T1 [M]（后台）   T2 [A₁, B, C]（前台）
最后一步之后：T1 [M]（后台）   T2 [A₁]（前台）
```

- A₁：`instanceId` 不变，没有新的 `onCreate`；收到 `onNewIntent`，并从 stopped 状态经历 `onRestart → onStart → onResume`。新 Intent 的交付发生在本次 `onResume` 之前，和前两个回调的相对位置不要写死。
- B：此前已经 stopped，清栈时观察其 `onDestroy`，不要求再走一轮 `onPause/onStop`。
- C：从前台结束，通常经历 `onPause → onStop → onDestroy`。
- B、C 的销毁回调和 A₁ 的恢复可能交错，检查最终栈和实例身份比比较整段日志更可靠。

再在 A₁ 前台启动自身，可与 singleTop 的栈顶复用对照。清除目标上方 Activity 的规则见 [Tasks and the back stack](https://developer.android.com/guide/components/activities/tasks-and-back-stack#TaskLaunchModes)。

## singleTask：从另一任务唤回后台任务

沿用上一例配置，重新建立 `T1 [M]` 和 `T2 [A₁, B, C]`。从最近任务切回 M，等待 T2 的 C 完全 stopped，再由 M 显式启动 A。

```text
启动前：T1 [M]（前台）   T2 [A₁, B, C]（后台）
启动后：T1 [M]（后台）   T2 [A₁]（前台）
```

A₁ 在原来的 `taskId` 中复用并接收新 Intent；B、C 被结束，M 所在的任务保留。此时 C 已经 stopped，不能照搬上一例“C 从前台经历 onPause”的预期。

做一轮对照：重新建立同样的两个任务并切回 M，然后**直接从最近任务选择 T2**，不要调用 `startActivity(A)`。在实例存活且无其他干扰时，恢复的是栈顶 C，T2 仍为 `[A₁, B, C]`，A₁ 不会因为这次切换就收到 `onNewIntent()`。

这组实验区分“把整个任务带回前台”和“向 singleTask Activity 发起一次新的启动请求”。

## singleInstance：自己独占任务，离开后再回来

将 A 改为 `singleInstance`，继续使用独立 affinity。M、B 均为默认 affinity 的 `standard`，清理旧任务后执行 `M → A → B → A`。

```text
M → A 后：T1 [M]（后台）      T2 [A₁]（前台）
A → B 后：T1 [M, B]（前台）   T2 [A₁]（后台）
B → A 后：T1 [M, B]（后台）   T2 [A₁]（前台）
```

在这个已有默认任务的设置下，B 进入 T1；必须检查 B 与 A₁ 的 `taskId` 不同。最后一步 A₁ 收到 `onNewIntent()` 并恢复，B 只是 `onPause → onStop`，不会像 singleTask 同一任务内清栈那样被销毁。

关键观察：**A₁ 的任务始终只有它自己；返回 A₁ 不代表另一个任务中的 B 被清除。** 隔离规则见 [Manifest launchMode](https://developer.android.com/guide/topics/manifest/activity-element#lmode)。

## taskAffinity：只改归属偏好，与增加 NEW_TASK 对照

将 A 配置为 `standard`，使用独立 affinity；M 使用默认 affinity。每轮开始时都清理旧任务，再由 M 启动 A。

| 启动方式 | 预期任务结构 | 生命周期观察 |
| --- | --- | --- |
| 不加 flags | `T1 [M, A₁]` | A₁ 新建，A₁ 与 M 的 taskId 相同 |
| 加 `FLAG_ACTIVITY_NEW_TASK` | `T1 [M]`、`T2 [A₁]` | A₁ 新建，A₁ 与 M 的 taskId 不同 |

第二轮的代码：

```kotlin
startActivity(Intent(this, AActivity::class.java).apply {
    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
})
```

两轮都可能呈现“M 暂停、A 创建并恢复、M 停止”，所以**生命周期形状相同不等于任务结构相同**。第二轮得到新任务的前提是没有可复用的匹配任务；`NEW_TASK` 这个名字不意味着每次都创建一个新任务。参见 [Handle affinities](https://developer.android.com/guide/components/activities/tasks-and-back-stack#Affinities)。

## 启动 flags：CLEAR_TOP 是否保留目标实例

恢复默认 affinity，把 A、B、C 都设为 `standard`。每轮重新建立 `[M, A₁, B, C]`，由 C 启动 A，只改变 flags：

| flags | 最终栈 | A 的关键回调 |
| --- | --- | --- |
| 无 | `[M, A₁, B, C, A₂]` | A₂ 新建 |
| `SINGLE_TOP` | `[M, A₁, B, C, A₂]` | A 不在栈顶，仍新建 A₂ |
| `CLEAR_TOP` | `[M, A₂]` | A₁ 也被结束；A₂ 走创建流程 |
| `CLEAR_TOP \| SINGLE_TOP` | `[M, A₁]` | A₁ 复用，收到 `onNewIntent` 后恢复 |

表中缩写均指 `Intent.FLAG_ACTIVITY_*`。最后一轮的启动代码：

```kotlin
startActivity(Intent(this, AActivity::class.java).apply {
    addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP)
    putExtra("request", "clear-top-and-reuse")
})
```

重点比较后两轮：最终看起来都只剩 M 和 A，但 A 是新对象还是旧对象完全不同。对 standard 目标，单独 `CLEAR_TOP` 会连目标一起结束并重建；组合 `SINGLE_TOP` 才在这个场景中保留它。参见 [Intent.FLAG_ACTIVITY_CLEAR_TOP](https://developer.android.com/reference/android/content/Intent#FLAG_ACTIVITY_CLEAR_TOP)。

# 如何记录实验结论

每轮保存“配置与 flags → 操作步骤 → 启动前后 taskId 和栈内容 → 各实例的回调”，不要只截取 `onCreate` 或 `onNewIntent` 一行。

遇到与预期不同的日志，先检查实例是否被重建、页面是否透明、是否携带额外 flags，以及上一步是否已经结束。配置变化可能销毁并重建实例；进程被系统杀死时，也不保证先收到 `onDestroy()`，这些现象不能直接归因于 launchMode。参见 [Activity lifecycle](https://developer.android.com/guide/components/activities/activity-lifecycle)。

