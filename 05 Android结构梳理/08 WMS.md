# WMS的职责

1. **窗口管理**

	WMS是窗口的管理者，它负责窗口的启动、添加和删除，另外窗口的大小和层级也是由WMS进行管理的。窗口管理的核心成员有DisplayContent、WindowToken和WindowState。

2. **窗口动画**

	窗口间进行切换时，使用窗口动画可以显得更炫一些，窗口动画由WMS的动画子系统来负责，动画子系统的管理者为WindowAnimator。
3. **输入系统的中转站**

	通过对窗口的触摸从而产生触摸事件，InputManagerService(IMS)会对触摸事件进行处理，它会寻找一个最合适的窗口来处理触摸反馈信息，WMS是窗口的管理者，用它作为输入系统的中转站。

4. **Surface管理**
窗口并不具备绘制的功能，因此每个窗口都需要有块Surface来供自己绘制，为每个窗口分配Surface是由WMS来完成的。

# WMS的创建过程

WMS是在SystemServer进程中创建的：

```java
public static void main(String[] args) {
    new SystemServer().run();
}
```

```java
private void run() {
    try {
        //创建消息Looper
        Looper.prepareMainLooper();

        //加载了动态库libandroid_servers.so
        System.loadLibrary("android_servers");
        performPendingShutdown();
        //创建系统的Context
        createSystemContext();
        //创建SystemServiceManager，它会对系统的服务进行创建、启动和生命周期管理
        mSystemServiceManager = new SystemServiceManager(mSystemContext);
        mSystemServiceManager.setRuntimeRestarted(mRuntimeRestart);
        LocalServices.addService(SystemServiceManager.class, mSystemServiceManager);
        SystemServerInitThreadPool.get();
    } finally {
        traceEnd();
    }

    // Start services.
    try {
        traceBeginAndSlog("StartServices");
      	//启动引导服务
        startBootstrapServices();
      	//启动核心服务
        startCoreServices();
      	//启动其他服务
        startOtherServices();
        SystemServerInitThreadPool.shutdown();
    } catch (Throwable ex) {
        //。。。
    } finally {
        traceEnd();
    }
		//。。。
    Looper.loop();
    throw new RuntimeException("Main thread loop unexpectedly exited");
}
```

在startBootstrapServices方法中用SystermServiceManager启动了ActivityManagerService、PowerManagerService、PackageManagerService等服务。
在startCoreServices方法中启动了DropBoxManagerService、BatteryService、UsageStatsService和WebViewUpdateService。
在startOtherServices方法中启动了CameraService、AlarmManagerService、VrManagerService等服务。

这些服务的父类均为SystemService。可以看出官方把系统服务分为了三种类型，分别是引导服务、核心服务和其他服务，其中其他服务是一些非紧要和不需要立即启动的服务，WMS就是其他服务的一种。

```java
private void startOtherServices() {
  	//...
    try {
        traceBeginAndSlog("InitWatchdog");
        final Watchdog watchdog = Watchdog.getInstance();
        watchdog.init(context, mActivityManagerService);
        traceEnd();

        traceBeginAndSlog("StartInputManagerService");
        inputManager = new InputManagerService(context);
        traceEnd();

        traceBeginAndSlog("StartWindowManagerService");
        // WMS needs sensor service ready
        ConcurrentUtils.waitForFutureNoInterrupt(mSensorServiceStart, START_SENSOR_SERVICE);
        mSensorServiceStart = null;
        wm = WindowManagerService.main(context, inputManager,
                mFactoryTestMode != FactoryTest.FACTORY_TEST_LOW_LEVEL,
                !mFirstBoot, mOnlyCore, new PhoneWindowManager());
        ServiceManager.addService(Context.WINDOW_SERVICE, wm);
        ServiceManager.addService(Context.INPUT_SERVICE, inputManager);
        traceEnd();
				//...

    } catch (RuntimeException e) {
				//...
    }
		//...
    try {
        wm.displayReady();
    } catch (Throwable e) {
				//...
    }
		//...
    try {
        wm.systemReady();
    } catch (Throwable e) {
        //...
    }
    //...
}
```

startOtherServices方法用于启动其他服务，其他服务大概有100个左右。

Watchdog用来监控系统的一些关键服务的运行状况。

**注释1**
执行WMS的main方法，其内部会创建WMS，需要注意的是main方法其中一个传入的参数就是刚刚创建的IMS，WMS是输入事件的中转站，其内部包含了IMS引用并不意外。
这里得知WMS的main方法是运行在SystemServer的run方法中的，换句话说就是运行在“system_server”线程中。

这里看一下WMS的main方法：

```java
public static WindowManagerService main(final Context context, final InputManagerService im, final boolean haveInputMethods, final boolean showBootMsgs, final boolean onlyCore, WindowManagerPolicy policy) {
    DisplayThread.getHandler().runWithScissors(() -> sInstance = new WindowManagerService(context, im, haveInputMethods, showBootMsgs, onlyCore, policy), 0);
    return sInstance;
}
```

这里创建了WMS的实例，这个过程运行在Runnable的run方法中，而Runmable则传到了DisplayThread对应Handler的runWithScissors方法中，说明WMS的创建是运行在android.display线程中的。这里runWithScissors方法的第二个参数传入的是0，后面会提到。

下面来查看Handler的runWithScissors方法做了什么：

```java
public final boolean runWithScissors(final Runnable r, long timeout) {
    if (r == null) {
        throw new IllegalArgumentException("runnable must not be null");
    }
    if (timeout < 0) {
        throw new IllegalArgumentException("timeout must be non-negative");
    }
    if (Looper.myLooper() == mLooper) {//注释1
        r.run();
        return true;
    }

    BlockingRunnable br = new BlockingRunnable(r);
    return br.postAndWait(this, timeout);
}
```

在注释1处根据每个线程只有一个Looper的原理来判断当前的线程(system_server线程)是否是Handler所指向的线程(android.display线程)，如果是则直接执行Runnable的run方法，如果不是则调用BlockingRunnable的postAndWait方法，井将当前线程的Runnable作为参数传进去。

BlockingRunnable是Handler的内部类，代码如下所示：

```java
private static final class BlockingRunnable implements Runnable {
    private final Runnable mTask;
    private boolean mDone;

    public BlockingRunnable(Runnable task) {
        mTask = task;
    }

    @Override
    public void run() {
        try {
            mTask.run();//注释1
        } finally {
            synchronized (this) {
                mDone = true;
                notifyAll();
            }
        }
    }

    public boolean postAndWait(Handler handler, long timeout) {
        if (!handler.post(this)) {//将当前的 BlockingRunnable 添加到 Handler 的任务队列中
            return false;
        }
				//前面runWithcissors方法的第二个参数为0，因此timeout等于0
        synchronized (this) {
            if (timeout > 0) {
                final long expirationTime = SystemClock.uptimeMillis() + timeout;
                while (!mDone) {
                    long delay = expirationTime - SystemClock.uptimeMillis();
                    if (delay <= 0) {
                        return false; // timeout
                    }
                    try {
                        wait(delay);
                    } catch (InterruptedException ex) {
                    }
                }
            } else {
                while (!mDone) {
                    try {
                        wait();
                    } catch (InterruptedException ex) {
                    }
                }
            }
        }
        return true;
    }
}
```

如果mDone为false的话会一直调用注释3处的wait方法使得当前线程(system_server 线程)进入等待状态，那么等待的是哪个线程呢？

在注释1处执行了传入的Runnable的run方法(运行在android.display线程)，执行完毕后在finally代码块中将mDone设置为true，并调用notifyAll方法唤醒处于等待状态的线程，这样就不会继续调用注释3处的wait方法。

因此得出结论，system_server线程等待的就是android.display线程，一直到android.display线程执行完毕再执行system_server线程，这是因为android.display线程内部执行了WMS的创建，而WMS的创建优先级要更高。以上是WMS的创建，最后查看WMS的构造方法：

```java
private WindowManagerService(Context context, InputManagerService inputManager, boolean haveInputMethods, boolean showBootMsgs, boolean onlyCore, WindowManagerPolicy policy) {
    //...
    mInputManager = inputManager;//注释1
    //...
    mDisplayManager = (DisplayManager)context.getSystemService(Context.DISPLAY_SERVICE);
    mDisplays = mDisplayManager.getDisplays();//注释2
    for (Display display : mDisplays) {
        createDisplayContentLocked(display);//注释3
    }
		//...
    mActivityManager = ActivityManager.getService();//注释4
    //...
    mAnimator = new WindowAnimator(this);//注释5
    mAllowTheaterModeWakeFromLayout = context.getResources().getBoolean(
            com.android.internal.R.bool.config_allowTheaterModeWakeFromWindowLayout);
    LocalServices.addService(WindowManagerInternal.class, new LocalService());
    initPolicy();//注释6
    Watchdog.getInstance().addMonitor(this);//注释7
		//...
}
```

**注释1**

用来保存传进来的IMS，这样WMS持有了IMS的引用。

**注释2**

通过DisplayManager的getDisplays方法得到Display数组(每个显示设备都有一个Display实例)。

**注释3**

接着遍历Display数组，在注释3处的createDisplayContentLocked方法将Display封装成DisplayContent，DisplayContent 用来描述一块屏幕。

**注释4**

得到AMS实例，并赋值给mActivityManager，这样WMS就持有了AMS的引用。

**注释5**

创建了WindowAnimator，它用于管理所有的窗口动画。

**注释6**

初始化了窗口管理策略的接口类WindowManagerPolicy(WMP)，它用来定义一个窗口策略所要遵循的通用规范。

**注释7**

将自身也就是WMS通过addMonitor方法添加到Watchdog中，Watchdog用来监控系统的一些关键服务的运行状况(比如传入的WMS的运行状况)，这些被监控的服务都会实现Watchdog.Monitor接口。Watchdog每分钟都会对被监控的系统服务进行检查，如果被监控的系统服务出现了死锁，则会杀死Watchdog所在的进程，也就是SystemServer进程。

查看注释6处的initPolicy 方法，如下所示：

```java
private void initPolicy() {
    UiThread.getHandler().runWithScissors(new Runnable() {
        @Override
        public void run() {
            WindowManagerPolicyThread.set(Thread.currentThread(), Looper.myLooper());

            mPolicy.init(mContext, WindowManagerService.this, WindowManagerService.this);//注释1
        }
    }, 0);
}
```

initPolicy方法和此前讲的WMS的main方法的实现类似，在注释1处执行了WMP的init方法，WMP是一个接口，init 方法具体在PhoneWindowManager (PWM)中实现。PWM的init方法运行在android.ui线程中，它的优先级要高于initPolicy方法所在的android.display线程，因此android.display 线程要等PWM的init 方法执行完毕后，处于等待状态的android.display线程才会被唤醒从而继续执行下面的代码。本文共提到了3个线程，分别是system_server, android.display 和android.ui，下面给出这3个线程之间的关系：

**此文不再记录**