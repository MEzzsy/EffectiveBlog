# 介绍

AsyncTask enables proper and easy use of the UI thread. This class allows you to perform background operations and publish results on the UI thread without having to manipulate threads and/or handlers.

这是源码中对AsyncTask的介绍，大概意思就是，AsyncTask可以方便的调用UI线程，能在后台进行操作然后不用开启线程或者使用Handler就可以将结果送到UI线程上。

AsyncTask可以进行一些不耗时的操作，如果想要进行耗时的操作，建议使用Executor或者ThreadPoolExecutor或者FutureTask。

AsyncTask需要传入三个泛型：

- Params：在执行AsyncTask时需要传入的参数，可以用于后台任务中使用。
- Progress: 如果需要在界面上显示进度条，则使用指定的泛型作为单位。
- Result：返回值的类型。

执行需要四个方法：

- onPreExecute：后台任务执行开始前调用，用于进行一些界面上的初始化操作，比如显示一个进度条对话框。
- doInBackground：这个方法的使用代码都会在子线程中操作，这里去处理耗时的操作。
- onProgressUpdate：对UI进行操作
- onPostExecute：后台任务执行完毕并通过return进行返回时，这个方法就会被调用。

# 分析

## AsyncTask()

先从构造方法开始分析，构造方法初始化了一些重要参数。

```java
public AsyncTask() {
    this((Looper) null);
}
```

```java
public AsyncTask(@Nullable Looper callbackLooper) {
    mHandler = callbackLooper == null || callbackLooper == Looper.getMainLooper()
        ? getMainHandler()
        : new Handler(callbackLooper);

    mWorker = new WorkerRunnable<Params, Result>() {
        public Result call() throws Exception {
            mTaskInvoked.set(true);
            Result result = null;
            try {
                Process.setThreadPriority(Process.THREAD_PRIORITY_BACKGROUND);
                //noinspection unchecked
                result = doInBackground(mParams);
                Binder.flushPendingCommands();
            } catch (Throwable tr) {
                mCancelled.set(true);
                throw tr;
            } finally {
                postResult(result);
            }
            return result;
        }
    };

    mFuture = new FutureTask<Result>(mWorker) {
        @Override
        protected void done() {
            try {
                postResultIfNotInvoked(get());
            } catch (InterruptedException e) {
                android.util.Log.w(LOG_TAG, e);
            } catch (ExecutionException e) {
                throw new RuntimeException("An error occurred while executing doInBackground()",
                        e.getCause());
            } catch (CancellationException e) {
                postResultIfNotInvoked(null);
            }
        }
    };
}
```

```java
private static abstract class WorkerRunnable<Params, Result> implements Callable<Result> {
    Params[] mParams;
}
```

mWorker是WorkerRunnable类型，其父类型是Callable，mFuture是FutureTask类型，如果熟悉Java线程池的话可以知道，mWorker是任务的核心，mFuture是封装了mWorker，使能够获取返回值。

## execute

调用execute开始执行任务，下面分析这个方法。这个方法调用了executeOnExecutor方法。

```java
public final AsyncTask<Params, Progress, Result> execute(Params... params) {
    return executeOnExecutor(sDefaultExecutor, params);
}
```

传入了2个参数sDefaultExecutor和params，params是用户指定的任务开启时需要的参数，sDefaultExecutor是一个串行线程池，一个应用所有的AsyncTask全部在这个线程池中排队执行。

在executeOnExecutor中，onPreExecute最先执行（如果用户重写了这个方法，在当前调用线程中执行），然后线程池执行AsyncTask。

```java
public final AsyncTask<Params, Progress, Result> executeOnExecutor(Executor exec, Params... params) {
    // 这里可以看出AsyncTask只能执行一次
    if (mStatus != Status.PENDING) {
        switch (mStatus) {
            case RUNNING:
                throw new IllegalStateException("Cannot execute task:"
                        + " the task is already running.");
            case FINISHED:
                throw new IllegalStateException("Cannot execute task:"
                        + " the task has already been executed "
                        + "(a task can be executed only once)");
        }
    }
    mStatus = Status.RUNNING;
    onPreExecute();
    mWorker.mParams = params;
    exec.execute(mFuture);
    return this;
}
```

`exec.execute(mFuture)`执行任务。这个exec就是下面的SerialExecutor对象sDefaultExecutor。

## SerialExecutor

```java
public static final Executor SERIAL_EXECUTOR = new SerialExecutor();
private static volatile Executor sDefaultExecutor = SERIAL_EXECUTOR;

private static class SerialExecutor implements Executor {
    final ArrayDeque<Runnable> mTasks = new ArrayDeque<Runnable>();
    Runnable mActive;

    public synchronized void execute(final Runnable r) {
        mTasks.offer(new Runnable() {
            public void run() {
                try {
                    r.run();
                } finally {
                    scheduleNext();
                }
            }
        });
        if (mActive == null) {
            scheduleNext();
        }
    }

    protected synchronized void scheduleNext() {
        if ((mActive = mTasks.poll()) != null) {
            THREAD_POOL_EXECUTOR.execute(mActive);
        }
    }
}
```

从SerialExecutor的实现可以分析AsyncTask的排队执行过程。

首先系统会把AsyncTask的params封装成FutureTask对象，起到Runnable的作用。

然后交给SerialExecutor的execute方法处理。execute方法会把FutureTask对象封装成一个Runnable对象（再次封装成一个Runnable是为了能够等任务执行完再执行scheduleNext方法）插入到任务队列中，如果没有正在活动的AsyncTask，那么scheduleNext方法就会执行下一个AsyncTask任务，**这一点可以看出，AsyncTask默认是串行执行的**。

AsyncTask有两个线程池（SerialExecutor和THREAD_POOL_EXECUTOR）和一个Handler （InternalHandler）

SerialExecutor**用于任务的排队**

THREAD_POOL_EXECUTOR**用于执行任务**

InternalHandler**用于将执行环境从线程池切换到主线程**

```java
protected synchronized void scheduleNext() {
	if ((mActive = mTasks.poll()) != null) {
   		THREAD_POOL_EXECUTOR.execute(mActive);
	}
}

mWorker = new WorkerRunnable<Params, Result>() {
    public Result call() throws Exception {
        mTaskInvoked.set(true);
        Result result = null;
        try {
            Process.setThreadPriority(Process.THREAD_PRIORITY_BACKGROUND);
            //noinspection unchecked
            result = doInBackground(mParams);
            Binder.flushPendingCommands();
        } catch (Throwable tr) {
            mCancelled.set(true);
            throw tr;
        } finally {
            postResult(result);
        }
        return result;
    }
};
```

`THREAD_POOL_EXECUTOR.execute(mActive)`执行队列中的任务，FutureTask的run方法会被调用，而在FutureTask的run方法中会调用mWorker的call方法，在call方法中先将mTaskInvoked设为true，表示当前的任务已经被调用了，然后执行AsyncTask的doInBackground方法，然后将返回值传递给postResult方法。

```java
private Result postResult(Result result) {
    @SuppressWarnings("unchecked")
    Message message = getHandler().obtainMessage(MESSAGE_POST_RESULT,
            new AsyncTaskResult<Result>(this, result));
    message.sendToTarget();
    return result;
}
```

getHandler()会return一个mHandler，而mHandler在构造函数中会转化成一个InternalHandler类的sHandler。

```java
mHandler = callbackLooper == null || callbackLooper == Looper.getMainLooper()
    ? getMainHandler()
    : new Handler(callbackLooper);
```

然后发送一个MESSAGE_POST_RESULT的消息。这个类的定义如下：

```java
private static class InternalHandler extends Handler {
    public InternalHandler(Looper looper) {
        super(looper);
    }

    @SuppressWarnings({"unchecked", "RawUseOfParameterizedType"})
    @Override
    public void handleMessage(Message msg) {
        AsyncTaskResult<?> result = (AsyncTaskResult<?>) msg.obj;
        switch (msg.what) {
            case MESSAGE_POST_RESULT:
                // There is only one result
                result.mTask.finish(result.mData[0]);
                break;
            case MESSAGE_POST_PROGRESS:
                result.mTask.onProgressUpdate(result.mData);
                break;
        }
    }
}
```

为了能够将环境切换到主线程，这要求sHandler必须在主线程创建。这是一个静态成员，而静态成员会在加载类的时候初始化，使用变相要求**AsyncTask必须在主线程创建**。

```java
public AsyncTask() {
	this((Looper) null);
}

public AsyncTask(@Nullable Handler handler) {
	this(handler != null ? handler.getLooper() : null);
}

/**
 * Creates a new asynchronous task. This constructor must be invoked on the UI thread.
 */
public AsyncTask(@Nullable Looper callbackLooper) {
    mHandler = callbackLooper == null || callbackLooper == Looper.getMainLooper()
            ? getMainHandler()
            : new Handler(callbackLooper);
}
```

AsyncTask的注释直接说明了这一点。不过AsyncTask的构造函数有3个，暴露的只有1个，即无参构造函数，所以即使在子线程中调用，AsyncTask最终也会创建MainLooper的Handler。

收到MESSAGE_POST_RESULT后会调用finish方法。

```java
private void finish(Result result) {
    if (isCancelled()) {
        onCancelled(result);
    } else {
        onPostExecute(result);
    }
    mStatus = Status.FINISHED;
}
```

这里doInBackground的返回结果会传递给onPostExecute方法。

在分析的时候，好像没有看到哪里调用了onProgressUpdate，后来发现调用onProgressUpdate需要publishProgress，而这个方法需要在doInBackground中使用。

官方文档的demo里这样使用：

```java
protected Long doInBackground(URL... urls) {
	int count = urls.length;
	long totalSize = 0;
	for (int i = 0; i < count; i++) {
		totalSize += Downloader.downloadFile(urls[i]);
		publishProgress((int) ((i / (float) count) * 100));
		if (isCancelled()) break;
	}
	return totalSize;
}
```

## cancel

```java
public final boolean cancel(boolean mayInterruptIfRunning) {
    mCancelled.set(true);
    return mFuture.cancel(mayInterruptIfRunning);
}
```

cancel方法需要传递一个参数，如果为true，会调用Thread的interrupt方法；如果会false，那么任务会执行完。最终都会执行完任务，并回调onCancel。

>   Thread的interrupt方法的效果见`/01 语言/02 Java/并发`，大致结论是这样的：如果当前调用了可中断的阻塞函数，那么调用interrupt方法会抛出异常；反之只是设置一下状态，不会中断线程。

在AsyncTask的doInBackground里最好判断一下isCancelled，以感知当前AsyncTask是否被cancel。

另外任务即使被cancel了，也还是存在SerialExecutor的队列中，等排队轮到执行时，FutureTask的run会判断状态，直接return。

# 注意

-   AsyncTask不适合大量数据的请求，因为AsyncTask中线程池一个时间只能执行一个，因为SerialExecutor是串行队列，任务是一个一个执行。

- 由于Handler需要和主线程交互，而Handler又是内置于AsyncTask中，所以AsyncTask的创建必须在主线程。（**注意这条并不正确**，AsyncTask内部Handler的创建会选取主线程的Looper，而不是当前线程的Looper，所以AsyncTask可以在子线程中创建，本人已从代码和实践2个角度证实。新版本是可以，老版本是不可以的，为了兼容性，建议在主线程中创建）。
- AsyncTaskResult的doInBackground(Params)方法执行异步任务运行在子线程中，其他方法运行在主线程中，可以操作UI组件。
- 不要手动的去调用AsyncTask的onPreExecute，doInBackground，onProgressUpdate，onPostExecute方法，这些都是由android系统自动调用的。
- 一个AsyncTask任务只能被执行一次。
- 运行中可以随时调用cancel(boolean)方法取消任务，如果成功调用isCancel()会返回true，并不会执行onPostExecute()，取而代之的是调用onCancelled()。从源码看，如果这个任务已经执行了这个时候调用cancel是不会真正的把task结束，而是继续执行，只不过改变的是执行之后的回调方法的onPostExecute还是onCancelled。
- 可能存在内存泄露情况，即非静态内部类持有外部类引用，解决办法是利用静态内部类+弱引用Activity的方式。（在Activity的onDestroy调用cancel也没用，因为任务即使被cancel了，也还是存在SerialExecutor的队列中，等排队轮到执行时，FutureTask的run会判断状态，直接return）
- 并行或串行：在android 1.6之前的版本asynctask都是串行，即把任务放线程池中一串一串的执行，1.6到2.3改成并行，2.3之后为了维护系统稳定改成串行，但是任然可以执行并行操作。
-   可能会导致结果丢失。
    屏幕旋转等造成Activity重新创建时AsyncTask数据丢失的问题。当Activity销毁并创新创建后，还在运行的AsyncTask会持有一个Activity的非法引用即之前的Activity实例，导致onPostExecute()没有任何作用。

# 个人总结

AsyncTask是一个轻量级的异步任务类，内部有2个Executor和一个Handler，SerialExecutor是一个串行线程池，用于任务的排队，内部的execute和scheduleNext方法加了同步锁，保证了任务的顺序执行，THREAD_POOL_EXECUTOR用来真正的执行任务，官方注释说可以并行执行任务，但由于锁机制，导致也只能异步执行。Handler是一个InternalHandler，用来将线程切换到主线程。

**优缺点（结合源码的个人总结）**

优点：异步执行任务。

缺点：

1.  不适合执行耗时操作，会阻塞后续任务。
2.  有内存泄漏的危险，如果是普通匿名内部类，会持有外部Activity的引用。可以利用静态内部类+弱引用的方式解决。

# 他人总结

上文提到AsyncTask可以在子线程中创建，网上看了一篇[资料](https://blog.csdn.net/smileiam/article/details/89225102)，总结如下：

1.  android-21及之前只能在UI线程创建AsyncTask实例和调用execute方法。android22+可以在非UI线程中创建AsyncTask实例和调用execute方法。因为从android22+起Handler实例化时调用了Looper.getMainLooper()(主线程的Looper)。因为用的是主线程的Looper，所以建议是在主线程中进行实例化AsyncTask，但其实Handler只要有Looper就能实例化，并不会抛异常。AsyncTask的onPreExecute是执行在调用AsyncTask.execute()方法的线程中，onPostExecute方法是执行在主线程中的（用了主线程looper实例化handler），doInBackground方法是执行在AsyncTask新开的线程中的。

2.  对于AsyncTask的构造方法，android25及之前版本AsyncTask只提供了一个无参构造函数来创建AsyncTask实例，android26+AsyncTask提供了三个构造方法，但是对外公开调用的只有一个无参构造方法，或许以后可能会公开带Looper参数的构造方法。

3.  Handler是静态变量，属于类属性，同一进程所有AsyncTask实例共享一个Handler对象。android-21及之前Handler的实例化在类一加载的时候就创建了，android22~25 handler实例是在需要用到Handler发送消息的时候，才会进行Handler的实例化。android26+则是在创建AsyncTask实例时进行了Handler的实例化。这样做的好处是不会像android21之前那样类一加载就实例化耗费资源，而在需要用到Handler发消息的时候才实例化，如果在多线程并发发消息时，会有延迟。

4.  android26+AsyncTask中包含了两个Handler对象：mHandler（常量）和sHandler（静态变量），如果用AsyncTask有参构造方法中传入了Looper创建AsyncTask实例，mHandler会用传入的Looper来创建实例；而现在系统只支持AsyncTask无参构造方法创建AsyncTask实例，所以mHandler=sHandler.