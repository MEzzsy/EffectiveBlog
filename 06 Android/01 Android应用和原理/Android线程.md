# 介绍

1.   见`/04 源码分析/JDK/线程池源码分析`

AsyncTask底层用线程池，IntentService和HandlerThread底层用了线程。

# AsyncTask

AsyncTask是一个抽象类，它是由Android封装的一个轻量级异步类（轻量体现在使用方便、代码简洁），它可以在线程池中执行后台任务，然后把执行的进度和最终结果传递给主线程并在主线程中更新UI。

## 基本使用

1. onPreExecute()
    这个方法会在后台任务开始执行之前调用，用于进行一些界面上的初始化操作，比如显示一个进度条对话框等。
    在调用execute(params)后会调用。
2. doInBackground(Params...)
    这个方法中的所有代码都会在子线程中运行，应该在这里去处理所有的耗时任务。任务一旦完成就可以通过return语句来将任务的执行结果返回，如果AsyncTask的第三个泛型参数指定的是Void，就可以不返回任务执行结果。注意，在这个方法中是不可以进行UI操作的，如果需要更新UI元素，比如说反馈当前任务的执行进度，可以调用publishProgress(Progress...)方法来完成。
    在执行任务的时候调用。
3. publishProgress(Progress... values)
    在doInBackground中调用，内部会用一个Handler切换到主线程。
4. onProgressUpdate(Progress...)
    当在后台任务中调用了publishProgress(Progress...)方法后 ，onProgressUpdate(Progress...)方法就会很快被调用，该方法中携带的参数就是在后台任务中传递过来的。在这个方法中可以对UI进行操作，利用参数中的数值就可以对界面元素进行相应的更新。
5. onPostExecute (Result)
    当后台任务执行完毕并通过return语句进行返回时，这个方法就很快会被调用。返回的数据会作为参数传递到此方法中，可以利用返回的数据来进行一些UI操作，比如说提醒任务执行的结果，以及关闭掉进度条对话框等。
    任务执行完会调用postResult方法，这个方法会用Handler发送一个消息来运行此方法。

## 分析

具体见源码分析里的AsyncTask分析。

## AsyncTask的机制原理

- AsyncTask的本质是一个静态的线程池，AsyncTask派生的子类可以实现不同的异步任务，这些任务都是提交到静态的线程池中执行。
- 线程池中的工作线程执行doInBackground()方法执行异步任务。
- 当任务状态改变之后，工作线程会向UI线程发送消息，AsyncTask内部的InternalHandler响应这些消息，并调用相关的回调函数。

## 注意

- AsyncTask不适合大量数据的请求，因为AsyncTask中线程池**一个时间只能执行一个，因为使用了同步锁**；

- 由于Handler需要和主线程交互，而Handler又是内置于AsyncTask中，所以AsyncTask的创建必须在主线程。
- AsyncTaskResult的doInBackground(Params)方法执行异步任务运行在子线程中，其他方法运行在主线程中，可以操作UI组件。
- 不要手动的去调用AsyncTask的onPreExecute，doInBackground，onProgressUpdate，onPostExecute方法。
- 一个AsyncTask任务只能被执行一次。
- 运行中可以随时调用cancel(boolean)方法取消任务，如果成功调用isCancel()会返回true，并不会执行onPostExecute()，取而代之的是调用onCancelled()。从源码看，如果这个任务已经执行了这个时候调用cancel是不会真正的把task结束，而是继续执行，只不过改变的是执行之后的回调方法的onPostExecute还是onCancelled。
- 可能存在内存泄露情况，即非静态内部类持有外部类引用，解决办法同，Handler内存泄露解决办法一样，（在activity的onDestory 方法中调用 AsyncTask的cancel()方法）
- 并行或串行：在android 1.6之前的版本asynctask都是串行，即把任务放线程池中一串一串的执行，1.6到2.3改成并行，2.3之后为了维护系统稳定改成串行，但是任然可以执行并行操作。

## AsyncTask线程数目

```java
private static final int CORE_POOL_SIZE = Math.max(2, Math.min(CPU_COUNT - 1, 4));
private static final int MAXIMUM_POOL_SIZE = CPU_COUNT * 2 + 1;
private static final int KEEP_ALIVE_SECONDS = 30;

private static final BlockingQueue<Runnable> sPoolWorkQueue =
            new LinkedBlockingQueue<Runnable>(128);

ThreadPoolExecutor threadPoolExecutor = new ThreadPoolExecutor(
        CORE_POOL_SIZE, MAXIMUM_POOL_SIZE, KEEP_ALIVE_SECONDS, TimeUnit.SECONDS,
        sPoolWorkQueue, sThreadFactory);
```

至少2个，至多4个核心线程。

任务数量最大128。

> 个人总结:
>
> AsyncTask是一个轻量级的异步任务类，内部有2个线程池和一个Handler，SerialExecutor用于任务的排队，内部的execute和scheduleNext方法加了同步锁，保证了任务的顺序执行，THREAD_POOL_EXECUTOR用来真正的执行任务，官方注释说可以并行执行任务，但由于锁机制，导致也只能异步执行。Handler是一个InternalHandler，用来将线程切换到主线程。

## AsyncTask使用不当的后果

1. 生命周期
    AsyncTask不与任何组件绑定生命周期，所以在Activity/或者Fragment中创建执行AsyncTask时，最好在Activity/Fragment的onDestory调用cancel(boolean)

2. 内存泄漏
    如果AsyncTask被声明为Activity的非静态的内部类，那么AsyncTask会保留一个对创建了AsyncTask的Activity的引用。如果Activity已经被销毁，AsyncTask的后台线程还在执行，它将继续在内存里保留这个引用，导致Activity无法被回收，引起内存泄露。解决方式和Handler差不多。

3. 结果丢失
    屏幕旋转或Activity在后台被系统杀掉等情况会导致Activity的重新创建，之前运行的AsyncTask（非静态的内部类）会持有一个之前Activity的引用，这时调用onPostExecute()再去更新界面将不再生效。

# HandlerThread

HandlerThread继承了Thread，并允许Handler的特殊线程。

```java
@Override
public void run() {
    mTid = Process.myTid();
    Looper.prepare();
    synchronized (this) {
        mLooper = Looper.myLooper();
        notifyAll();
    }
    Process.setThreadPriority(mPriority);
    onLooperPrepared();
    Looper.loop();
    mTid = -1;
}
```

普通线程在run()方法中执行耗时操作，而HandlerThread在run()方法创建了一个消息队列不停地轮询消息，可以通过Handler发送消息来告诉线程该执行什么操作。

它在Android中是个很有用的类，它常见的使用场景实在IntentService中。当不再需要HandlerThread时，通过调用quit/Safely方法来结束线程的轮询并结束该线程。

# **IntentService**

**1. 概述**

IntentService是一个继承Service的抽象类，必须实现它的子类再去使用。

在说到HandlerThread时提到，HandlerThread的使用场景是在IntentService上，可以这样来理解IntentService，它是一个实现了HandlerThread的Service。

那么为什么要这样设计呢？这样设计的好处是Service的优先级比较高，可以利用这个特性来保证后台服务的优先正常执行，甚至还可以为Service开辟一个新的进程。

**2. 源码分析**

onCreate()函数：

```java
@Override
public void onCreate() {
    super.onCreate();
    HandlerThread thread = new HandlerThread("IntentService[" + mName + "]");
    thread.start();
    mServiceLooper = thread.getLooper();
    mServiceHandler = new ServiceHandler(mServiceLooper);
}
```

创建Service时，实现了一个HandlerThread的实例开启了一个线程，并在线程内部进行消息轮询，又创建了一个Handler来收发Looper的消息。

每启动一次服务时，不会开启新的服务，只是会调用onStartCommand()函数，又看到该函数调用了onStart()方法。

```java
@Override
public void onStart(@Nullable Intent intent, int startId) {
    Message msg = mServiceHandler.obtainMessage();
    msg.arg1 = startId;
    msg.obj = intent;
    mServiceHandler.sendMessage(msg);
}
```

在该方法中看到，这里用来接收Context传递的参数，通过Handler发送出去，然后再HandlerThread的线程上接收消息并且处理。

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

可以看到onHandleIntent()方法是需要接收消息处理的。
