# demo1

## singleTop

Main为singleTop，AB为standard。

```
//启动Main
onCreate: Main
onStart: Main
onResume: Main

//Main中启动A
onPause: Main
onCreate: A
onStart: A
onResume: A
onStop: Main

//A中启动Main
onPause: A
onCreate: Main
onStart: Main
onResume: Main
onStop: A

//Main中启动Main
onPause: Main
onNewIntent: Main
onResume: Main
```

输入`adb shell dumpsys activity`查看任务栈。

```
ACTIVITY MANAGER ACTIVITIES (dumpsys activity activities)
Display #0 (activities from top to bottom):
  Stack #7:
    Task id #10
      TaskRecord{30db902 #10 A=com.mezzsy.myapplication2 U=0 sz=4}
      Intent { act=android.intent.action.MAIN cat=[android.intent.category.LAUNCHER] flg=0x10000000 cmp=com.mezzsy.myapplication2/.MainActivity }
        Hist #3: ActivityRecord{5434008 u0 com.mezzsy.myapplication2/.demo0004.D03Activity t10}
          Intent { cmp=com.mezzsy.myapplication2/.demo0004.D03Activity }
          ProcessRecord{98f6e49 11213:com.mezzsy.myapplication2/u0a64}
        Hist #2: ActivityRecord{adfc6a2 u0 com.mezzsy.myapplication2/.demo0004.AActivity t10}
          Intent { cmp=com.mezzsy.myapplication2/.demo0004.AActivity }
          ProcessRecord{98f6e49 11213:com.mezzsy.myapplication2/u0a64}
        Hist #1: ActivityRecord{234a9c0 u0 com.mezzsy.myapplication2/.demo0004.D03Activity t10}
          Intent { cmp=com.mezzsy.myapplication2/.demo0004.D03Activity }
          ProcessRecord{98f6e49 11213:com.mezzsy.myapplication2/u0a64}
        Hist #0: ActivityRecord{48e01c7 u0 com.mezzsy.myapplication2/.MainActivity t10}
          Intent { act=android.intent.action.MAIN cat=[android.intent.category.LAUNCHER] flg=0x10000000 cmp=com.mezzsy.myapplication2/.MainActivity }
          ProcessRecord{98f6e49 11213:com.mezzsy.myapplication2/u0a64}

    Running activities (most recent first):
      TaskRecord{30db902 #10 A=com.mezzsy.myapplication2 U=0 sz=4}
        Run #3: ActivityRecord{5434008 u0 com.mezzsy.myapplication2/.demo0004.D03Activity t10}
        Run #2: ActivityRecord{adfc6a2 u0 com.mezzsy.myapplication2/.demo0004.AActivity t10}
        Run #1: ActivityRecord{234a9c0 u0 com.mezzsy.myapplication2/.demo0004.D03Activity t10}
        Run #0: ActivityRecord{48e01c7 u0 com.mezzsy.myapplication2/.MainActivity t10}

    mResumedActivity: ActivityRecord{5434008 u0 com.mezzsy.myapplication2/.demo0004.D03Activity t10}
```

栈中情况为MAM（从左到右的顺序对应栈中的从上到下，下同）。

## singleTask

Main为singleTask，AB为standard。

```
//启动Main
onCreate: Main
onStart: Main
onResume: Main

//Main中启动A
onPause: Main
onCreate: A
onStart: A
onResume: A
onStop: Main

//A中启动B
onPause: A
onCreate: B
onStart: B
onResume: B
onStop: A

//B中启动Main
onDestroy: A
onPause: B
onNewIntent: Main
onRestart: Main
onStart: Main
onResume: Main
onStop: B
onDestroy: B
```

从B中启动Main之前的栈情况是BAM，BA出栈，但是log显示A先销毁。

查看任务栈

```
ACTIVITY MANAGER ACTIVITIES (dumpsys activity activities)
Display #0 (activities from top to bottom):
  Stack #8:
    Task id #12
      TaskRecord{62e4bae #12 A=com.mezzsy.another U=0 sz=1}
      Intent { flg=0x10000000 cmp=com.mezzsy.myapplication2/.demo0004.D03Activity }
        Hist #0: ActivityRecord{a7e0392 u0 com.mezzsy.myapplication2/.demo0004.D03Activity t12}
          Intent { flg=0x10000000 cmp=com.mezzsy.myapplication2/.demo0004.D03Activity }
          ProcessRecord{67bccdc 11427:com.mezzsy.myapplication2/u0a64}
    Task id #11
      TaskRecord{3596d4f #11 A=com.mezzsy.myapplication2 U=0 sz=1}
      Intent { act=android.intent.action.MAIN cat=[android.intent.category.LAUNCHER] flg=0x10000000 cmp=com.mezzsy.myapplication2/.MainActivity }
        Hist #0: ActivityRecord{9e7b43d u0 com.mezzsy.myapplication2/.MainActivity t11}
          Intent { act=android.intent.action.MAIN cat=[android.intent.category.LAUNCHER] flg=0x10000000 cmp=com.mezzsy.myapplication2/.MainActivity }
          ProcessRecord{67bccdc 11427:com.mezzsy.myapplication2/u0a64}

    Running activities (most recent first):
      TaskRecord{62e4bae #12 A=com.mezzsy.another U=0 sz=1}
        Run #1: ActivityRecord{a7e0392 u0 com.mezzsy.myapplication2/.demo0004.D03Activity t12}
      TaskRecord{3596d4f #11 A=com.mezzsy.myapplication2 U=0 sz=1}
        Run #0: ActivityRecord{9e7b43d u0 com.mezzsy.myapplication2/.MainActivity t11}

    mResumedActivity: ActivityRecord{a7e0392 u0 com.mezzsy.myapplication2/.demo0004.D03Activity t12}
```

栈中只有Main，而且因为Main设置的任务栈名为com.mezzsy.another与默认的不同，因此新创建com.mezzsy.another任务栈。而存活的Activity只有Main和Demo集合MainActivity。

一个任务栈对应任务管理器的一个卡片，打开任务管理器可以看到现在有两个卡片（一个Main，一个Demo集合MainActivity）

## singleInstance

Main为singleInstance，AB为standard。

```
//启动Main
onCreate: Main
onStart: Main
onResume: Main

//Main中启动A
onPause: Main
onCreate: A
onStart: A
onResume: A
onStop: Main

//A中启动B
onPause: A
onCreate: B
onStart: B
onResume: B
onStop: A

//B中启动Main
onPause: B
onNewIntent: Main
onRestart: Main
onStart: Main
onResume: Main
onStop: B
```

log显示AB并未销毁

任务栈情况

```
ACTIVITY MANAGER ACTIVITIES (dumpsys activity activities)
Display #0 (activities from top to bottom):
  Stack #9:
    Task id #15
      TaskRecord{3b0d15d #15 A=com.mezzsy.another U=0 sz=1}
      Intent { flg=0x10000000 cmp=com.mezzsy.myapplication2/.demo0004.D03Activity }
        Hist #0: ActivityRecord{914f569 u0 com.mezzsy.myapplication2/.demo0004.D03Activity t15}
          Intent { flg=0x10000000 cmp=com.mezzsy.myapplication2/.demo0004.D03Activity }
          ProcessRecord{7317aa0 11618:com.mezzsy.myapplication2/u0a64}
    Task id #14
      TaskRecord{d01aad2 #14 A=com.mezzsy.myapplication2 U=0 sz=3}
      Intent { act=android.intent.action.MAIN cat=[android.intent.category.LAUNCHER] flg=0x10000000 cmp=com.mezzsy.myapplication2/.MainActivity }
        Hist #2: ActivityRecord{e20e9b9 u0 com.mezzsy.myapplication2/.demo0004.BActivity t14}
          Intent { cmp=com.mezzsy.myapplication2/.demo0004.BActivity }
          ProcessRecord{7317aa0 11618:com.mezzsy.myapplication2/u0a64}
        Hist #1: ActivityRecord{ca834aa u0 com.mezzsy.myapplication2/.demo0004.AActivity t14}
          Intent { flg=0x10400000 cmp=com.mezzsy.myapplication2/.demo0004.AActivity }
          ProcessRecord{7317aa0 11618:com.mezzsy.myapplication2/u0a64}
        Hist #0: ActivityRecord{97601d7 u0 com.mezzsy.myapplication2/.MainActivity t14}
          Intent { act=android.intent.action.MAIN cat=[android.intent.category.LAUNCHER] flg=0x10000000 cmp=com.mezzsy.myapplication2/.MainActivity }
          ProcessRecord{7317aa0 11618:com.mezzsy.myapplication2/u0a64}

    Running activities (most recent first):
      TaskRecord{3b0d15d #15 A=com.mezzsy.another U=0 sz=1}
        Run #3: ActivityRecord{914f569 u0 com.mezzsy.myapplication2/.demo0004.D03Activity t15}
      TaskRecord{d01aad2 #14 A=com.mezzsy.myapplication2 U=0 sz=3}
        Run #2: ActivityRecord{e20e9b9 u0 com.mezzsy.myapplication2/.demo0004.BActivity t14}
        Run #1: ActivityRecord{ca834aa u0 com.mezzsy.myapplication2/.demo0004.AActivity t14}
        Run #0: ActivityRecord{97601d7 u0 com.mezzsy.myapplication2/.MainActivity t14}

    mResumedActivity: ActivityRecord{914f569 u0 com.mezzsy.myapplication2/.demo0004.D03Activity t15}
```

共有两个任务栈，com.mezzsy.another只有Main（D03Activity），默认任务栈有三个，从上到下的顺序依次是B、A、MainActivity（Demo集合的MainActivity）

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

