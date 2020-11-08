# AMS家族

AMS的逻辑十分复杂，所以会有一些相关类帮助完成逻辑，Android7.0和8.0有些区别，如图：

-   Android7.0
    ![267](assets/267.jpg)

-   Android8.0
    ![268](assets/268.jpg)

# AMS的启动过程

AMS的启动是在SystemServer进程中启动的。

具体启动过程暂不记录。

# AMS与应用程序进程

Zygote的Java框架层中，会创建一个Server端的Socket，这个Socket用来等待AMS请求Zygote来创建新的应用程序进程。要启动一个应用程序，首先要保证这个应用程序所需要的应用程序进程已经存在。在启动应用程序时AMS会检查这个应用程序需要的应用程序进程是否存在，不存在就会请求Zygote进程创建需要的应用程序进程。

# AMS的数据结构

AMS涉及了很多数据结构，如ActivityRecord、TaskRecord、ActivityStack。

## ActivityRecord

ActivityRecord内部记录了Activity的所有信息，用来描述一个Activity。它是在启动Activity 时被创建的，见[Activity启动过程](Activity启动过程.md)。

**ActivityRecord的部分重要成员变量**

| 名称                | 类型                   | 说明                                                         |
| ------------------- | ---------------------- | ------------------------------------------------------------ |
| service             | ActivityManagerService | AMS的引用                                                    |
| info                | ActivityInfo           | Activity中代码和AndroidManifes设置的节点信息，比如launchMode |
| launchedFromPackage | String                 | 启动Activity的包名                                           |
| taskAffinity        | String                 | Activity希望归属的栈                                         |
| task                | TaskRecord             | ActivityRecord所在的TaskRecord                               |
| app                 | ProcessRecord          | ActivityRecord所在的应用程序进程                             |
| state               | ActivityState          | 当前Activity的状态                                           |
| icon                | int                    | Activity的图标资源标识符                                     |
| theme               | int                    | Activity的主题资源标识符                                     |

## TaskRecord

TaskRecord用来描述一个Activity 任务栈。

**TaskRecord的部分重要成员变量类型**

| 名称        | 类型                        | 说明                           |
| ----------- | --------------------------- | ------------------------------ |
| taskId      | init                        | 任务栈的唯一标识符             |
| affinity    | String                      | 任务栈的倾向性                 |
| intent      | Intent                      | 启动这个任务栈的Intent         |
| mActivities | ArrayList\<ActivityRecord\> | 按照历史顺序排列的Activity记录 |
| mStack      | ActivityStack               | 当前归属的ActivityStack        |
| mService    | ActivityManagerService      | AMS的引用                      |

## ActivityStack

ActivityStack是一个管理类，用来管理系统所有的Activity，内部维护了Activity的所有状态、特殊状态的Activity以及Activity相关的列表等数据。ActivityStack是由ActivityStackSupervisor来进行管理的，ActivityStackSupervisor在AMS的构造方法中被创建。

```java
public ActivityManagerService(Context systemContext) {
    //...
    mStackSupervisor = createStackSupervisor();
    //...
}
```

```java
protected ActivityStackSupervisor createStackSupervisor() {
    return new ActivityStackSupervisor(this, mHandler.getLooper());
}
```

### ActivityStack的实例类型

mHomeStack用来存储Launcher APP的所有Activity。

mFocusedStack表示当前正在接收输入或启动下一个Activity的所有Activity。

mLastFocusedStack表示此前接收输入的所有Activity。

### ActivityState

在ActivityStack中通过枚举存储来Activity的所有的状态：

```java
enum ActivityState {
    INITIALIZING,
    RESUMED,
    PAUSING,
    PAUSED,
    STOPPING,
    STOPPED,
    FINISHING,
    DESTROYING,
    DESTROYED
}
```

# 参考

1.  《Android进阶解密》，刘望舒。