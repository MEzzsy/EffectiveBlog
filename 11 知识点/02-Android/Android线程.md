# 介绍

AsyncTask底层用线程池，IntentService和HandlerThread底层用了线程。

# AsyncTask

AsyncTask是一个抽象类，它是由Android封装的一个轻量级异步类（轻量体现在使用方便、代码简洁），它可以在线程池中执行后台任务，然后把执行的进度和最终结果传递给主线程并在主线程中更新UI。

## 基本使用

1. onPreExecute()
    这个方法会在后台任务开始执行之前调用，用于进行一些界面上的初始化操作，比如显示一个进度条对话框等。
    在调用execute(params)后会调用。
2. doInBackground(Params...)
    这个方法中的所有代码都会在子线程中运行，我们应该在这里去处理所有的耗时任务。任务一旦完成就可以通过return语句来将任务的执行结果返回，如果AsyncTask的第三个泛型参数指定的是Void，就可以不返回任务执行结果。注意，在这个方法中是不可以进行UI操作的，如果需要更新UI元素，比如说反馈当前任务的执行进度，可以调用publishProgress(Progress...)方法来完成。
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

从起点execute开始分析，这个方法return一个executeOnExecutor。一个进程的所有AsyncTask都在一个串行线程池排队执行。在executeOnExecutor中，onPreExecute方法最先执行，然后线程池执行。

首先系统会把AsyncTask的params封装成FutureTask对象，起到Runnable的作用。然后交给SerialExecutor的execute方法处理。execute方法会把FutureTask对象插入到任务队列中，如果没有正在活动的AsyncTask，那么scheduleNext方法就会执行下一个AsyncTask任务，**这一点可以看出，AsyncTask默认是串行执行的**

AsyncTask有两个线程池（SerialExecutor和THREAD_POOL_EXECUTOR）和一个Handler（InternalHandler），SerialExecutor用于任务的排队，THREAD_POOL_EXECUTOR用于执行任务。InternalHandler用于将执行环境从线程池切换到主线程。

**个人思考：为什么用两个线程池，为什么不直接用一个线程池？**

第一个线程池的源码：

```java
private static class SerialExecutor implements Executor {
    final ArrayDeque<Runnable> mTasks = new ArrayDeque<Runnable>();
    Runnable mActive;

    public synchronized void execute(final Runnable r) {
        //...
    }

    protected synchronized void scheduleNext() {
        if ((mActive = mTasks.poll()) != null) {
            THREAD_POOL_EXECUTOR.execute(mActive);
        }
    }
}
```

接口Executor的源码：

```java
public interface Executor {
    void execute(Runnable command);
}
```

SerialExecutor除了将任务交给第二个线程池外，其余没有涉及线程的地方，因此猜测任务的排队所在的线程在调用AsyncTask.execute(Params)的线程。所以SerialExecutor名字叫线程池，但与线程池关系不大。

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
    AsyncTask不与任何组件绑定生命周期，所以在Activity/或者Fragment中创建执行AsyncTask时，最好在Activity/Fragment的onDestory()调用 cancel(boolean)；

2. 内存泄漏
    如果AsyncTask被声明为Activity的非静态的内部类，那么AsyncTask会保留一个对创建了AsyncTask的Activity的引用。如果Activity已经被销毁，AsyncTask的后台线程还在执行，它将继续在内存里保留这个引用，导致Activity无法被回收，引起内存泄露。解决方式和Handler差不多。

3. 结果丢失
    屏幕旋转或Activity在后台被系统杀掉等情况会导致Activity的重新创建，之前运行的AsyncTask（非静态的内部类）会持有一个之前Activity的引用，这时调用onPostExecute()再去更新界面将不再生效。

# HandlerThread

HandlerThread继承了Thread，内部创建了一个Looper，所以可以使用Handler，HandlerThread具体使用的场景是IntentService。

# 线程池

## 简单介绍

线程池的优点：

1. 重用线程池中的线程，避免因为线程的创建和销毁所带来的性能开销。
2. 能有效控制线程池的最大并发数，避免大量的线程之间因互相抢占系统资源而导致阻塞。
3. 能对线程进行简单的管理，并提供定时执行以及指定间隔循环执行等功能。

Android中最常见的四类具有不同功能特性的线程池，都是用ThreadPoolExecutor直接或间接实现自己的特性的：FixedThreadPool、CachedThreadPool、ScheduledThreadPool、SingleThreadExecutor。

## 线程池的分类

核心线程指不会被回收的线程。非核心线程指最大线程数减核心线程数，会被回收。

**FixedThreadPool：**

- 线程数量固定（需用户指定），当线程处于空闲状态也不会被回收，除非线程池被关闭。
- 只有核心线程，并且没有超时机制，另外任务队列没有大小限制。

**CachedThreadPool：**

- 线程数量不定，只有非核心线程，最大的线程数为Integer.MAX_VALUE
- 空闲线程具有超时机制，超过60秒就会被回收。
- 适合大量耗时少的任务。

**ScheduledThreadPool：**

- 核心线程数量固定，非核心线程没有限制，非核心线程闲置时会被立即回收。
- 主要用于执行定时任务和具有固定周期的重复任务。

**SingleThreadExecutor：**

- 只有一个核心线程，确保所有的任务都在同一个线程按顺序执行
- 意义在于统一所有的外界任务到一个线程，使得不需要处理同步问题。

## 自定义线程池

ThreadPoolExecutor是线程池的真正实现。

## 笔记

见笔记[Android线程和线程池](https://mezzsy.github.io/2019/06/23/Android/Android线程和线程池/)

# TODO

1.   为什么AsyncTask最好不要执行耗时任务