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

## 不同任务栈

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

一个任务栈对应任务管理器的一个卡片，打开任务管理器可以看到现在有两个卡片

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

singleInstance模式下，任务栈只能有一个Activity实例，所以在singleInstance启动的Activity跑到了默认任务栈下。

## 启动相同任务栈-SingleTask

```xml
<activity
            android:name=".basic.activity.launchmode.SingleInstanceTaskSingleTaskActivity"
            android:launchMode="singleTask"
            android:taskAffinity="com.mezzsy.singleInstance" />
```

SingleTask的任务栈名和SingleInstance相同

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

虽然SingleTask和SingleInstance的任务名相同，但是两个还是在不同的任务栈，它们的id不同。

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



# demo

主Activity在默认栈，ABC在另一个栈。

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

个人分析：此时栈情况为ABC，C在栈顶，BC出栈，但是log显示B先出栈。

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

然后我加了一个D，栈内为ABCD，D在栈顶，D启动A，log如上。可以这么理解DCB依次出栈，但是onDestroy方法是反着来执行的。

