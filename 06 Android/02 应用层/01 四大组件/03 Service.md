# 本地服务（LocalService）

> 调用者和service在同一个进程里，所以运行在主进程的main线程中。所以不能进行耗时操作，可以采用在service里面**创建一个Thread**来执行任务。service影响的是**进程**的生命周期，讨论与Thread的区别没有意义。
>
> **任何 Activity 都可以控制同一Service，而系统也只会创建一个对应 Service 的实例**。

1. **onCreate**，创建服务。
2. **onStartCommand**，如果调用了startService方法就会回调这个方法。
3. **onBind**，如果调用了bindService方法就会回调这个方法。
4. **onDestroy**，如果调用了stopService或者unbindService就会回调这个方法。

服务(Service)是Android中实现程序后台运行的解决方案，它非常适合去执行那些不需要和用户交互而且还要求长期运行的任务。服务的运行不依赖于任何用户界面，即使程序被切换到后台，或者用户打开了另外一个应用程序，服务仍然能够保持正常运行。

不过需要注意的是，服务并不是运行在一个独立的进程当中的，而是依赖于创建服务时所在的应用程序进程。当某个应用程序进程被杀掉时，所有依赖于该进程的服务也会停止运行。

另外，也不要被服务的后台概念所迷惑，实际上服务并不会自动开启线程，所有的代码都是默认运行在主线程当中的。也就是说，需要在服务的内部手动创建子线程，并在这里执行具体的任务，否则就有可能出现主线程被阻塞住的情况。

## 启动和停止Service

**Context的方法**

```java
startService(intent);
stopService(intent);
bindService(Intent service， ServiceConnection conn ， int flags);
unbindService(ServiceConnection conn);
```

> 在Service中声明一个binder，onBind返回此binder。
>
> 在Activity中声明一个ServiceConnection，就可以调用binder中的方法。

**Service的方法**

```
stopSelf();
```

# IntentService

IntentService是一个抽象类，继承了Service。IntentService内部含有HandlerThread和Handler，所以它可以执行耗时操作，另外Looper将消息按顺序插入队列中，使用IntentService是顺序执行。

首先要提供个无参的构造函数，并且必须在其内部调用父类的有参构造函数。
然后要在子类中去实现onHandleIntent()这个抽象方法，在这个方法中可以去处理一些具体的逻辑，而且不用担心ANR的问题，因为这个方法已经是在子线程中运行的了。

```java
public class TestIntentService extends IntentService {
    private static final String TAG = "TestIntentService";
    
    public TestIntentService() {
        super("TestIntentService");
    }

    @Override
    protected void onHandleIntent(Intent intent) {
        Log.i(TAG, "onHandleIntent: ");
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        Log.i(TAG, "onDestroy: ");
    }
}
```

startService后：

```
I/TestIntentService: onHandleIntent: 
I/TestIntentService: onDestroy: 
```

```java
private final class ServiceHandler extends Handler {
    public ServiceHandler(Looper looper) {
        super(looper);
    }

    @Override
    public void handleMessage(Message msg) {
        onHandleIntent((Intent)msg.obj);
        stopSelf(msg.arg1);
    }
}
```

IntentService在运行完onHandleIntent后会自己停止。

IntentService特征:

- 会创建独立的worker线程来处理所有的Intent请求；
- 会创建独立的worker线程来处理onHandleIntent()方法实现的代码，无需处理多线程问题；
- 所有请求处理完成后，IntentService会自动停止，无需调用stopSelf()方法停止Service；
- 为Service的onBind()提供默认实现，返回null；
- 为Service的onStartCommand提供默认实现，将请求Intent添加到队列中；

# 后台服务

创建的服务一般是后台的。

# 前台服务

前台服务会一直有一个正在运行的图标在系统的状态栏显示，非常类似于通知的效果。

由于后台服务优先级相对比较低，当系统出现内存不足的情况下，它就有可能会被回收掉，所以前台服务就是来弥补这个缺点的，它可以一直保持运行状态而不被系统回收。

**创建服务类**

前台服务创建很简单，其实就在Service的基础上创建一个Notification，然后使用Service的startForeground()方法即可启动为前台服务。

```java
public final void startForeground(int id, Notification notification)
```

# 远程服务

> 调用者和service不在同一个进程中，service在单独的进程中的main线程，是一种垮进程通信方式。

具体见IPC机制。
