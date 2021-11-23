# Looper

官方的使用例子：

```java
class LooperThread extends Thread {
    public Handler mHandler;

    public void run() {
        Looper.prepare();
        mHandler = new Handler() {
            public void handleMessage(Message msg) {
                // process incoming messages here
            }
        };
        Looper.loop();
    }
}
```

## prepare

```java
public static void prepare() {
    prepare(true);
}

private static void prepare(boolean quitAllowed) {
    if (sThreadLocal.get() != null) {
        throw new RuntimeException("Only one Looper may be created per thread");
    }
    sThreadLocal.set(new Looper(quitAllowed));
}
```

prepare方法在当前线程创建一个Looper，并设置到ThreadLocal中。

## 构造函数

```java
private Looper(boolean quitAllowed) {
    mQueue = new MessageQueue(quitAllowed);
    mThread = Thread.currentThread();
}
```

Looper创建时，会创建一个MessageQueue

## loop

```java
public static void loop() {
    final Looper me = myLooper();
    if (me == null) {
        throw new RuntimeException("No Looper; Looper.prepare() wasn't called on this thread.");
    }
    final MessageQueue queue = me.mQueue;

    // Make sure the identity of this thread is that of the local process,
    // and keep track of what that identity token actually is.
    Binder.clearCallingIdentity();
    final long ident = Binder.clearCallingIdentity();

    // Allow overriding a threshold with a system prop. e.g.
    // adb shell 'setprop log.looper.1000.main.slow 1 && stop && start'
    final int thresholdOverride =
            SystemProperties.getInt("log.looper."
                    + Process.myUid() + "."
                    + Thread.currentThread().getName()
                    + ".slow", 0);

    boolean slowDeliveryDetected = false;

    // 开启死循环
    for (;;) {
        // 调用MessageQueue的next来取出一个msg
        Message msg = queue.next(); // might block
        if (msg == null) {
            // No message indicates that the message queue is quitting.
            return;
        }

        // 省略日志代码
        // Make sure the observer won't change while processing a transaction.
        final Observer observer = sObserver;

        final long traceTag = me.mTraceTag;
        long slowDispatchThresholdMs = me.mSlowDispatchThresholdMs;
        long slowDeliveryThresholdMs = me.mSlowDeliveryThresholdMs;
        if (thresholdOverride > 0) {
            slowDispatchThresholdMs = thresholdOverride;
            slowDeliveryThresholdMs = thresholdOverride;
        }
        final boolean logSlowDelivery = (slowDeliveryThresholdMs > 0) && (msg.when > 0);
        final boolean logSlowDispatch = (slowDispatchThresholdMs > 0);

        final boolean needStartTime = logSlowDelivery || logSlowDispatch;
        final boolean needEndTime = logSlowDispatch;

        if (traceTag != 0 && Trace.isTagEnabled(traceTag)) {
            Trace.traceBegin(traceTag, msg.target.getTraceName(msg));
        }

        final long dispatchStart = needStartTime ? SystemClock.uptimeMillis() : 0;
        final long dispatchEnd;
        Object token = null;
        if (observer != null) {
            token = observer.messageDispatchStarting();
        }
        long origWorkSource = ThreadLocalWorkSource.setUid(msg.workSourceUid);
        try {
            // 通过msg对应的Handler来分发此msg
            msg.target.dispatchMessage(msg);
            if (observer != null) {
                observer.messageDispatched(token, msg);
            }
            dispatchEnd = needEndTime ? SystemClock.uptimeMillis() : 0;
        } catch (Exception exception) {
            if (observer != null) {
                observer.dispatchingThrewException(token, msg, exception);
            }
            throw exception;
        } finally {
            ThreadLocalWorkSource.restore(origWorkSource);
            if (traceTag != 0) {
                Trace.traceEnd(traceTag);
            }
        }
        if (logSlowDelivery) {
            if (slowDeliveryDetected) {
                if ((dispatchStart - msg.when) <= 10) {
                    Slog.w(TAG, "Drained");
                    slowDeliveryDetected = false;
                }
            } else {
                if (showSlowLog(slowDeliveryThresholdMs, msg.when, dispatchStart, "delivery",
                        msg)) {
                    // Once we write a slow delivery log, suppress until the queue drains.
                    slowDeliveryDetected = true;
                }
            }
        }
        if (logSlowDispatch) {
            showSlowLog(slowDispatchThresholdMs, dispatchStart, dispatchEnd, "dispatch", msg);
        }

        if (logging != null) {
            logging.println("<<<<< Finished to " + msg.target + " " + msg.callback);
        }

        // Make sure that during the course of dispatching the
        // identity of the thread wasn't corrupted.
        final long newIdent = Binder.clearCallingIdentity();
        if (ident != newIdent) {
            Log.wtf(TAG, "Thread identity changed from 0x"
                    + Long.toHexString(ident) + " to 0x"
                    + Long.toHexString(newIdent) + " while dispatching to "
                    + msg.target.getClass().getName() + " "
                    + msg.callback + " what=" + msg.what);
        }

        msg.recycleUnchecked();
    }
}
```

loop小结：

1.   在当前线程中开启一个死循环，从MessageQueue中取出下一个Message，交给Message对应的Handler去分发。

# MessageQueue

## 构造方法

```java
MessageQueue(boolean quitAllowed) {
    mQuitAllowed = quitAllowed;
    mPtr = nativeInit();
}
```

```cpp
static jlong android_os_MessageQueue_nativeInit(JNIEnv* env, jclass clazz) {
    NativeMessageQueue* nativeMessageQueue = new NativeMessageQueue();
    if (!nativeMessageQueue) {
        jniThrowRuntimeException(env, "Unable to allocate native queue");
        return 0;
    }

    nativeMessageQueue->incStrong(env);
    return reinterpret_cast<jlong>(nativeMessageQueue);
}
```

在Native层也创建了一个对应的NativeMessageQueue。

## next

```java
Message next() {
    final long ptr = mPtr;
    if (ptr == 0) {
        return null;
    }

    // 初始化为-1
    int pendingIdleHandlerCount = -1; 
    int nextPollTimeoutMillis = 0;
    for (;;) {
        if (nextPollTimeoutMillis != 0) {
            Binder.flushPendingCommands();
        }

        // 调用这个nativePollOnce会等待wake，如果超过nextPollTimeoutMillis时间，则不管有没有被唤醒都会返回。
        nativePollOnce(ptr, nextPollTimeoutMillis);

        synchronized (this) {
            final long now = SystemClock.uptimeMillis();
            Message prevMsg = null;
            Message msg = mMessages;
            if (msg != null && msg.target == null) {
                // msg.target为空的情况，只有MessageQueue.postSyncBarrier。异步消息只能结合Barrier使用，也就是说就算有异步的消息，但是没有设置Barrier，也是没效果的。
                do {
                    prevMsg = msg;
                    msg = msg.next;
                } while (msg != null && !msg.isAsynchronous());
            }
            if (msg != null) {
                if (now < msg.when) {
                    nextPollTimeoutMillis = (int) Math.min(msg.when - now, Integer.MAX_VALUE);
                } else {
                    mBlocked = false;
                    if (prevMsg != null) {
                        prevMsg.next = msg.next;
                    } else {
                        mMessages = msg.next;
                    }
                    msg.next = null;
                    msg.markInUse();
                    return msg;
                }
            } else {
                nextPollTimeoutMillis = -1;
            }

            if (mQuitting) {
                dispose();
                return null;
            }

            // 
            if (pendingIdleHandlerCount < 0
                    && (mMessages == null || now < mMessages.when)) {
                pendingIdleHandlerCount = mIdleHandlers.size();
            }
            // 如果没有IdleHandler，就执行阻塞
            if (pendingIdleHandlerCount <= 0) {
                mBlocked = true;
                continue;
            }

            if (mPendingIdleHandlers == null) {
                mPendingIdleHandlers = new IdleHandler[Math.max(pendingIdleHandlerCount, 4)];
            }
            mPendingIdleHandlers = mIdleHandlers.toArray(mPendingIdleHandlers);
        }

        for (int i = 0; i < pendingIdleHandlerCount; i++) {
            final IdleHandler idler = mPendingIdleHandlers[i];
            mPendingIdleHandlers[i] = null; 

            boolean keep = false;
            try {
                keep = idler.queueIdle();
            } catch (Throwable t) {
                Log.wtf(TAG, "IdleHandler threw exception", t);
            }

            if (!keep) {
                synchronized (this) {
                    mIdleHandlers.remove(idler);
                }
            }
        }

        // 一次next只会回调一次IdleHandler
        pendingIdleHandlerCount = 0;

        nextPollTimeoutMillis = 0;
    }
}
```

小结：

1.   找到下一个Msg并return。
2.   如果下一个消息还没到执行时间，就调用nativePollOnce等待nextPollTimeoutMillis时间。或者在下次enqueueMessage并且msg的when符合执行要求的时候，调用nativeWake进行唤醒。

## enqueueMessage

```java
boolean enqueueMessage(Message msg, long when) {
    if (msg.target == null) {
        throw new IllegalArgumentException("Message must have a target.");
    }
    if (msg.isInUse()) {
        throw new IllegalStateException(msg + " This message is already in use.");
    }

    synchronized (this) {
        if (mQuitting) {
            IllegalStateException e = new IllegalStateException(
                    msg.target + " sending message to a Handler on a dead thread");
            Log.w(TAG, e.getMessage(), e);
            msg.recycle();
            return false;
        }

        msg.markInUse();
        msg.when = when;
        Message p = mMessages;
        boolean needWake;
        if (p == null || when == 0 || when < p.when) {
            // New head, wake up the event queue if blocked.
            msg.next = p;
            mMessages = msg;
            needWake = mBlocked;
        } else {
            // Inserted within the middle of the queue.  Usually we don't have to wake
            // up the event queue unless there is a barrier at the head of the queue
            // and the message is the earliest asynchronous message in the queue.
            needWake = mBlocked && p.target == null && msg.isAsynchronous();
            Message prev;
            for (;;) {
                prev = p;
                p = p.next;
                if (p == null || when < p.when) {
                    break;
                }
                if (needWake && p.isAsynchronous()) {
                    needWake = false;
                }
            }
            msg.next = p; // invariant: p == prev.next
            prev.next = msg;
        }

        // We can assume mPtr != 0 because mQuitting is false.
        if (needWake) {
            nativeWake(mPtr);
        }
    }
    return true;
}
```

1.   Message的链表顺序按照when（运行时间，delay的原理就是delay加上当前时间得到最终的运行时间）来的。
     如果有个Message enqueue，那么遍历链表，比较when，将该msg放置在合适的位置。

# Handler

## dispatchMessage

```java
public void dispatchMessage(@NonNull Message msg) {
    if (msg.callback != null) {
        handleCallback(msg);
    } else {
        if (mCallback != null) {
            if (mCallback.handleMessage(msg)) {
                return;
            }
        }
        handleMessage(msg);
    }
}
```

1.   如果msg有callback，那么交给msg的callback来执行此msg。
2.   如果Handler设置了callback，那么交给callback的handleMessage来处理。
3.   如果callback的handleMessage返回false，那么Handler自己处理（handleMessage）。

## sendMessageAtTime

```java
public boolean sendMessageAtTime(@NonNull Message msg, long uptimeMillis) {
    MessageQueue queue = mQueue;
    if (queue == null) {
        RuntimeException e = new RuntimeException(
                this + " sendMessageAtTime() called with no mQueue");
        Log.w("Looper", e.getMessage(), e);
        return false;
    }
    return enqueueMessage(queue, msg, uptimeMillis);
}
```

```java
private boolean enqueueMessage(@NonNull MessageQueue queue, @NonNull Message msg,
        long uptimeMillis) {
    msg.target = this;
    msg.workSourceUid = ThreadLocalWorkSource.getUid();

    if (mAsynchronous) {
        msg.setAsynchronous(true);
    }
    return queue.enqueueMessage(msg, uptimeMillis);
}
```

1.   sendMessage的一系列方法最终调用的是sendMessageAtTime。
2.   将msg的target设置为Handler本身。

# IdleHandler

```java
public class TestHandlerActivity extends BaseDemoActivity {
    private static final String TAG = "TestHandlerActivity";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Executors.newSingleThreadExecutor().execute(new MyTestHandler());
    }

    private static class MyTestHandler implements Runnable {
        @Override
        public void run() {
            Looper.prepare();
            Looper.myQueue().addIdleHandler(new MyIdleHandler(false));
            Looper.myQueue().addIdleHandler(new MyIdleHandler(true));
            final Handler handler = new Handler(new Handler.Callback() {
                @Override
                public boolean handleMessage(@NonNull Message msg) {
                    Log.i(TAG, "handleMessage: " + msg.what);
                    return false;
                }
            });
            handler.sendEmptyMessageDelayed(1, 2000);
            Looper.loop();
        }
    }

    private static class MyIdleHandler implements MessageQueue.IdleHandler {
        private final boolean queueIdle;

        public MyIdleHandler(boolean queueIdle) {
            this.queueIdle = queueIdle;
            Log.i(TAG, "new MyIdleHandler: " + hashCode() +
                    ", queueIdle = " + queueIdle);
        }

        @Override
        public boolean queueIdle() {
            Log.i(TAG, "queueIdle: " + hashCode());
            return queueIdle;
        }
    }

}
```

```
TestHandlerActivity: new MyIdleHandler: 143851827, queueIdle = false
TestHandlerActivity: new MyIdleHandler: 29127918, queueIdle = true
TestHandlerActivity: queueIdle: 143851827
TestHandlerActivity: queueIdle: 29127918
TestHandlerActivity: handleMessage: 1
TestHandlerActivity: queueIdle: 29127918
```

# 异步消息

MessageQueue

```java
// 这里msg是头msg
if (msg != null && msg.target == null) {
	// msg.target为空的情况，只有MessageQueue.postSyncBarrier。异步消息只能结合Barrier使用，也就是说就算有异步的消息，但是没有设置Barrier，也是没效果的。
	do {
		prevMsg = msg;
		msg = msg.next;
	} while (msg != null && !msg.isAsynchronous());
}
```

在MessageQueue的next方法中，如果发现头msg是没有target，那么就一直找下一个异步消息。

## 设置异步消息

```java
/**
 * Sets whether the message is asynchronous, meaning that it is not
 * subject to {@link Looper} synchronization barriers.
 * <p>
 * Certain operations, such as view invalidation, may introduce synchronization
 * barriers into the {@link Looper}'s message queue to prevent subsequent messages
 * from being delivered until some condition is met.  In the case of view invalidation,
 * messages which are posted after a call to {@link android.view.View#invalidate}
 * are suspended by means of a synchronization barrier until the next frame is
 * ready to be drawn.  The synchronization barrier ensures that the invalidation
 * request is completely handled before resuming.
 * </p><p>
 * Asynchronous messages are exempt from synchronization barriers.  They typically
 * represent interrupts, input events, and other signals that must be handled independently
 * even while other work has been suspended.
 * </p><p>
 * Note that asynchronous messages may be delivered out of order with respect to
 * synchronous messages although they are always delivered in order among themselves.
 * If the relative order of these messages matters then they probably should not be
 * asynchronous in the first place.  Use with caution.
 * </p>
 *
 * @param async True if the message is asynchronous.
 *
 * @see #isAsynchronous()
 */
public void setAsynchronous(boolean async) {
    if (async) {
        flags |= FLAG_ASYNCHRONOUS;
    } else {
        flags &= ~FLAG_ASYNCHRONOUS;
    }
}
```

这里主要贴出注释。意思是，某些操作，比如view的invalidation。通过放置一个barrier，来阻止有消息放在它前面。

>   个人理解：
>
>   view的刷新也是通过Handler来完成的。如果view需要刷新，但是有个消息放在刷新消息前了，那么就无法执行刷新。
>
>   相当于高优处理消息。

## ViewRootImpl#scheduleTraversals

```java
void scheduleTraversals() {
    if (!mTraversalScheduled) {
        mTraversalScheduled = true;
        mTraversalBarrier = mHandler.getLooper().getQueue().postSyncBarrier();
        mChoreographer.postCallback(
                Choreographer.CALLBACK_TRAVERSAL, mTraversalRunnable, null);
        notifyRendererOfFramePending();
        pokeDrawLockIfNeeded();
    }
}
```

Choreographer.java

```java
public void postCallback(int callbackType, Runnable action, Object token) {
    postCallbackDelayed(callbackType, action, token, 0);
}

public void postCallbackDelayed(int callbackType, Runnable action, Object token, long delayMillis) {
    // ...
    postCallbackDelayedInternal(callbackType, action, token, delayMillis);
}

private void postCallbackDelayedInternal(int callbackType, Object action, Object token, long delayMillis) {
    // ...
    synchronized (mLock) {
        final long now = SystemClock.uptimeMillis();
        final long dueTime = now + delayMillis;
        mCallbackQueues[callbackType].addCallbackLocked(dueTime, action, token);

        if (dueTime <= now) {
            scheduleFrameLocked(now);
        } else {
            Message msg = mHandler.obtainMessage(MSG_DO_SCHEDULE_CALLBACK, action);
            msg.arg1 = callbackType;
            // 设置异步标记
            msg.setAsynchronous(true);
            mHandler.sendMessageAtTime(msg, dueTime);
        }
    }
}
```

ViewRootImpl在进行view的刷新时，放置了一个屏障。然后post了一个异步消息。



```java
public int postSyncBarrier() {
    return postSyncBarrier(SystemClock.uptimeMillis());
}

private int postSyncBarrier(long when) {
    // Enqueue a new sync barrier token.
    // We don't need to wake the queue because the purpose of a barrier is to stall it.
    synchronized (this) {
        final int token = mNextBarrierToken++;
        final Message msg = Message.obtain();
        msg.markInUse();
        msg.when = when;
        msg.arg1 = token;

        Message prev = null;
        Message p = mMessages;
        if (when != 0) {
            while (p != null && p.when <= when) {
                prev = p;
                p = p.next;
            }
        }
        if (prev != null) { // invariant: p == prev.next
            msg.next = p;
            prev.next = msg;
        } else {
            msg.next = p;
            mMessages = msg;
        }
        return token;
    }
}
```

小结：

1.   消息队列循环执行，不一定是完全按照时间串行执行的，是可以有异步消息的。
2.   异步消息相当于高优msg，当存在Barrier且存在异步消息时，异步消息会被处理。
3.   异步消息必须结合Barrier使用，如果没有设置Barrier，也是没效果的。
4.   设置了Barrier，要对应的移除掉它，否则同步消息再也不会被处理。