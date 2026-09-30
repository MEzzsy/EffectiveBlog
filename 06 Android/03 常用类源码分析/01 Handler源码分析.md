# 🌟总结

1.   Android消息机制主要是指Handler + Looper + MessageQueue。
2.   线程是默认没有Looper，如果需要使用Handler需要创建Looper。Looper创建时会创建MessageQueue。
3.   MessageQueue内部用单链表存储Message。

## Looper

1.  线程是默认没有Looper，通过Looper.prepare创建一个Looper对象，并放入当前线程的ThreadLocal中。
2.  创建Looper时，会创建一个MessageQueue。

## 消息循环

1.   Handler post一个runnable或send一个message（post最终是通过send完成的）。
2.   这个message会带上当前的时间戳，如果是delay消息，则加上delay。
3.   调用MessageQueue的enqueueMessage方法将消息放入消息队列中，msg是按照时间戳（when）排序的。
4.   在Looper.loop方法中，不断调用MessageQueue的next获取一个消息，并通过msg对应的Handler来处理此msg。
5.   如果msg有callback，那么执行callback。如果没有callback，但是Handler设置了callback，那么交给callback的handleMessage来处理。如果callback的handleMessage返回false，那么Handler自己处理（handleMessage）。

### 消息获取

MessageQueue.next也是一个循环

1. 在MessageQueue.next方法中，先调用nativePollOnce并传入一个时间参数（nextPollTimeoutMillis，含义见下），让当前 Looper 线程处理 Native 事件。
   - 初始时间参数为0。不阻塞等待，处理已经就绪的 Native 事件后返回；没有native消息就立即返回。
2. 寻找下一个Java消息
   1. 如果队头是同步屏障，则寻找屏障后的第一条异步消息。
      - 同步屏障是`Message.target == null`的消息。通过 `postSyncBarrier()` 插入，会把消息同步屏障放在消息队列头部。设置了同步屏障，要对应的移除掉它，否则同步消息再也不会被处理。
   2. 有候选消息但没有到期，那么设置时间参数为`now - msg.when`。
   3. 有候选消息且到期，那么返回给Looper。
   4. 没有候选msg，那么设置时间参数为 `-1`。
      - 如果有IdleHandler且本次尚未执行过 IdleHandler 时，先执行回调，再把时间参数重置为0
      - 如果没有IdleHandler，那么进入下一轮。

## 细节

1.   创建一个Message。用obtain方法是为了复用Message，因为Handler的消息循环是很频繁的。
2.   Handler的sendMessage系列方法和post系列方法（post内部创建一个msg，然后将runnable设置给msg），最终调用enqueueMessage方法调给messageQueue。
3.   如果当前MessageQueue阻塞了，并且这个msg被放在MessageQueue的开头，那么就唤醒当前线程（nativeWake）。
4.   Looper内部是一个死循环，通过MessageQueue的next方法找到新msg，交给由Handler的dispatchMessage方法来处理。
     如果头msg还没到执行时间（now < when），那么就阻塞当前线程一段时间（nativePollOnce）。
5.   如果这个message内部有个runnable，就执行runnable。
     如果Handler有Callback，就执行Callback的handleMessage方法，这个方法有个boolean返回值，如果返回false，就执行Handler中的handleMessage方法，如果为true，那么消息处理完毕。

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

## IdleHandler**总结**

1.   如果MessageQueue注册了IdleHandler，那么在没有msg执行的空档期会回调IdleHandler的queueIdle方法。如果返回false，则该IdleHandler被移除出MessageQueue；如果返回true，则继续保留该IdleHandler。一个next方法只会回调一次IdleHandler。如果回调完IdleHandler还没到msg的执行时间，那么依然调用nativePollOnce进行阻塞。

## 异步消息总结

1.   异步消息常见用途：ViewRootImpl在进行view的刷新时，放置了一个Barrier，紧接着post了一个异步消息，该消息用于主线程渲染。
2.   Barrier消息入列时，如果Barrier是第一个消息，那么会唤醒线程。
3.   消息队列循环时，当首个消息为Barrier时，会去寻找第一个异步消息。
4.   异步消息必须结合Barrier使用，如果没有设置Barrier，也是没效果的。
5.   设置了Barrier，要对应的移除掉它，否则同步消息再也不会被处理。

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

        // 按超时参数进行 Native 轮询：0 不等待，-1 不设置超时，正数设置等待超时。
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
2.   如果下一个消息还没到执行时间，先计算等待超时，再在下一轮调用nativePollOnce。符合唤醒条件的新消息入队时，可以通过nativeWake使线程提前结束等待，重新检查队列。

### nativePollOnce

Java 层在 `MessageQueue.next()` 中调用 `nativePollOnce(ptr, nextPollTimeoutMillis)`，让当前 Looper 线程处理 Native 事件，并在暂时没有可执行的 Java 消息时等待。`ptr` 对应关联的 NativeMessageQueue，`nextPollTimeoutMillis` 控制本次轮询是否等待：

| 参数值 | 含义 |
| --- | --- |
| `0` | 不阻塞等待，处理已经就绪的 Native 事件后继续检查 Java 队列 |
| 正数 | 设置等待超时；事件就绪或唤醒可以使等待提前结束 |
| `-1` | 不指定等待超时，等待事件或唤醒；Native 层仍可能根据自己的消息调整超时 |

按上面的单链表版 `next()` 实现，一次调用的流程如下：

1. **先进行一次非阻塞轮询**：`nextPollTimeoutMillis` 初始为 `0`，所以即使 Java 队列中已有到期消息，也会先调用一次 `nativePollOnce()`。它返回后，Java 层才进入 `synchronized (this)` 检查队列。
2. **寻找下一条候选消息**：通常检查队头；如果队头是同步屏障，则寻找屏障后的第一条异步消息。候选消息已经到期时，将其从队列移除并 `return` 给 Looper，由 Looper 调用 Handler 分发。
3. **没有到期消息时，计算下一轮的等待参数**：候选消息尚未到期，设置为 `min(msg.when - now, Integer.MAX_VALUE)`；没有候选消息，设置为 `-1`。后者既可能是队列为空，也可能是同步屏障后没有异步消息。这里使用 `SystemClock.uptimeMillis()` 计算时间。
4. **按需执行 IdleHandler，再进入下一轮**：满足空闲条件且本次尚未执行过 IdleHandler 时，先执行回调，随后将超时重置为 `0`，立即重新检查，因为回调期间可能产生新消息。如果没有需要执行的 IdleHandler，则设置 `mBlocked = true` 并进入下一轮，使用刚计算的超时调用 `nativePollOnce()`。队列需要退出时则返回 `null`，结束消息循环。

因此，Java 层的过程是“**轮询 → 检查消息 → 确定等待参数 → 再次轮询**”。`nativePollOnce()` 返回只表示本轮 Native 轮询结束，Java 层还要重新读取时间和检查队列，才能判断有没有消息可执行。

**等待期间的新消息处理**：`nativePollOnce()` 位于 `synchronized (this)` 外，等待时不会占用 Java 队列锁，其他线程仍能入队。队列正在等待时，如果新消息成为队头，或者队头有屏障且新消息成为其后的第一条异步消息，`enqueueMessage()` 会调用 `nativeWake()`，让轮询提前返回并重新计算等待时间。

例如，原本正在等待一条 10 秒后执行的消息，此时插入一条 1 秒后执行的消息，就需要立即唤醒、重新计算等待时间；并不要求新消息已经到期。唤醒也不会打断正在执行的 Handler 回调。

另外，准备以非零超时进入 Native 轮询前，代码会先调用 `Binder.flushPendingCommands()`，将当前线程待提交的 Binder 命令发送到驱动。Native 层如何通过 epoll 等待和通过 eventfd 唤醒，见后面的「Native层的消息循环」。

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

# Native层的消息循环

>   文档：https://developer.android.com/ndk/reference/group/looper

## 实现方式

Native层消息循环的大致实现方式（线程之间的消息通信）：

1.   通过ALooper_acquire增加已有 Looper 的引用。
2.   通过eventfd创建一个fd，并通过ALooper_addFd来注册这个fd。
3.   其它线程需要给目标线程发送消息时，用write(fd)的方式来通知。
4.   ALooper_addFd调用时，设置一个callback，当其它线程通知时，这个callback会执行，并且是在目标线程执行的。
5.   通过ALooper_release释放资源。

## ALooper原理

Native层的消息循环实现的核心是epoll。

### ALooper_addFd

注册fd也就是通过epoll_ctl来add一个新的epoll event，该fd对应一个新的序号SequenceNumber，并赋值给epoll event。

epoll 是 Linux 提供的 I/O 事件通知机制，让一个线程同时等待多个 fd（文件描述符）上的事件。 比如 socket 有数据可读、管道收到数据、eventfd 收到通知。

它主要有三个 API：

| API               | 作用                                 |
| ----------------- | ------------------------------------ |
| `epoll_create1()` | 创建一个 epoll 实例                  |
| `epoll_ctl()`     | 添加、修改或删除监听的 fd 和事件类型 |
| `epoll_wait()`    | 等待事件，并返回哪些 fd 已经就绪     |

可以理解成：先告诉内核“帮我关注这些 fd”，然后等待内核告诉你“哪些可以处理了”。 没有事件时，线程可以阻塞休眠；出现事件或等待超时后，再继续执行，无需持续占用 CPU 反复查询。

结合 Android Looper，唤醒过程是：

```
Looper 线程在 epoll_wait() 中等待
             ↑
其他线程调用 nativeWake()
             ↓
向 Looper 内部的 eventfd 写入通知
             ↓
eventfd 变为可读，epoll_wait() 返回
             ↓
Looper 消费通知，继续检查消息队列
```

### write fd

write fd需要其它线程调用。如果write了，那么epoll_wait是会返回对应的event的。

## nativePollOnce

```cpp
int Looper::pollOnce(int timeoutMillis, int* outFd, int* outEvents, void** outData) {
    int result = 0;
    for (;;) {
        while (mResponseIndex < mResponses.size()) {
            const Response& response = mResponses.itemAt(mResponseIndex++);
            int ident = response.request.ident;
            if (ident >= 0) {
                int fd = response.request.fd;
                int events = response.events;
                void* data = response.request.data;
#if DEBUG_POLL_AND_WAKE
                ALOGD("%p ~ pollOnce - returning signalled identifier %d: "
                        "fd=%d, events=0x%x, data=%p",
                        this, ident, fd, events, data);
#endif
                if (outFd != nullptr) *outFd = fd;
                if (outEvents != nullptr) *outEvents = events;
                if (outData != nullptr) *outData = data;
                return ident;
            }
        }

        if (result != 0) {
#if DEBUG_POLL_AND_WAKE
            ALOGD("%p ~ pollOnce - returning result %d", this, result);
#endif
            if (outFd != nullptr) *outFd = 0;
            if (outEvents != nullptr) *outEvents = 0;
            if (outData != nullptr) *outData = nullptr;
            return result;
        }

        result = pollInner(timeoutMillis);
    }
}

int Looper::pollInner(int timeoutMillis) {
#if DEBUG_POLL_AND_WAKE
    ALOGD("%p ~ pollOnce - waiting: timeoutMillis=%d", this, timeoutMillis);
#endif

    // Adjust the timeout based on when the next message is due.
    if (timeoutMillis != 0 && mNextMessageUptime != LLONG_MAX) {
        nsecs_t now = systemTime(SYSTEM_TIME_MONOTONIC);
        int messageTimeoutMillis = toMillisecondTimeoutDelay(now, mNextMessageUptime);
        if (messageTimeoutMillis >= 0
                && (timeoutMillis < 0 || messageTimeoutMillis < timeoutMillis)) {
            timeoutMillis = messageTimeoutMillis;
        }
#if DEBUG_POLL_AND_WAKE
        ALOGD("%p ~ pollOnce - next message in %" PRId64 "ns, adjusted timeout: timeoutMillis=%d",
                this, mNextMessageUptime - now, timeoutMillis);
#endif
    }

    // Poll.
    int result = POLL_WAKE;
    mResponses.clear();
    mResponseIndex = 0;

    // We are about to idle.
    mPolling = true;

    struct epoll_event eventItems[EPOLL_MAX_EVENTS];
    int eventCount = epoll_wait(mEpollFd.get(), eventItems, EPOLL_MAX_EVENTS, timeoutMillis);

    // No longer idling.
    mPolling = false;

    // Acquire lock.
    mLock.lock();

    // Rebuild epoll set if needed.
    if (mEpollRebuildRequired) {
        mEpollRebuildRequired = false;
        rebuildEpollLocked();
        goto Done;
    }

    // Check for poll error.
    if (eventCount < 0) {
        if (errno == EINTR) {
            goto Done;
        }
        ALOGW("Poll failed with an unexpected error: %s", strerror(errno));
        result = POLL_ERROR;
        goto Done;
    }

    // Check for poll timeout.
    if (eventCount == 0) {
#if DEBUG_POLL_AND_WAKE
        ALOGD("%p ~ pollOnce - timeout", this);
#endif
        result = POLL_TIMEOUT;
        goto Done;
    }

    // Handle all events.
#if DEBUG_POLL_AND_WAKE
    ALOGD("%p ~ pollOnce - handling events from %d fds", this, eventCount);
#endif

    for (int i = 0; i < eventCount; i++) {
        const SequenceNumber seq = eventItems[i].data.u64;
        uint32_t epollEvents = eventItems[i].events;
        if (seq == WAKE_EVENT_FD_SEQ) {
            if (epollEvents & EPOLLIN) {
                awoken();
            } else {
                ALOGW("Ignoring unexpected epoll events 0x%x on wake event fd.", epollEvents);
            }
        } else {
            const auto& request_it = mRequests.find(seq);
            if (request_it != mRequests.end()) {
                const auto& request = request_it->second;
                int events = 0;
                if (epollEvents & EPOLLIN) events |= EVENT_INPUT;
                if (epollEvents & EPOLLOUT) events |= EVENT_OUTPUT;
                if (epollEvents & EPOLLERR) events |= EVENT_ERROR;
                if (epollEvents & EPOLLHUP) events |= EVENT_HANGUP;
                mResponses.push({.seq = seq, .events = events, .request = request});
            } else {
                ALOGW("Ignoring unexpected epoll events 0x%x for sequence number %" PRIu64
                      " that is no longer registered.",
                      epollEvents, seq);
            }
        }
    }
Done: ;

    // Invoke pending message callbacks.
    mNextMessageUptime = LLONG_MAX;
    while (mMessageEnvelopes.size() != 0) {
        nsecs_t now = systemTime(SYSTEM_TIME_MONOTONIC);
        const MessageEnvelope& messageEnvelope = mMessageEnvelopes.itemAt(0);
        if (messageEnvelope.uptime <= now) {
            // Remove the envelope from the list.
            // We keep a strong reference to the handler until the call to handleMessage
            // finishes.  Then we drop it so that the handler can be deleted *before*
            // we reacquire our lock.
            { // obtain handler
                sp<MessageHandler> handler = messageEnvelope.handler;
                Message message = messageEnvelope.message;
                mMessageEnvelopes.removeAt(0);
                mSendingMessage = true;
                mLock.unlock();

#if DEBUG_POLL_AND_WAKE || DEBUG_CALLBACKS
                ALOGD("%p ~ pollOnce - sending message: handler=%p, what=%d",
                        this, handler.get(), message.what);
#endif
                handler->handleMessage(message);
            } // release handler

            mLock.lock();
            mSendingMessage = false;
            result = POLL_CALLBACK;
        } else {
            // The last message left at the head of the queue determines the next wakeup time.
            mNextMessageUptime = messageEnvelope.uptime;
            break;
        }
    }

    // Release lock.
    mLock.unlock();

    // Invoke all response callbacks.
    for (size_t i = 0; i < mResponses.size(); i++) {
        Response& response = mResponses.editItemAt(i);
        if (response.request.ident == POLL_CALLBACK) {
            int fd = response.request.fd;
            int events = response.events;
            void* data = response.request.data;
#if DEBUG_POLL_AND_WAKE || DEBUG_CALLBACKS
            ALOGD("%p ~ pollOnce - invoking fd event callback %p: fd=%d, events=0x%x, data=%p",
                    this, response.request.callback.get(), fd, events, data);
#endif
            // Invoke the callback.  Note that the file descriptor may be closed by
            // the callback (and potentially even reused) before the function returns so
            // we need to be a little careful when removing the file descriptor afterwards.
            int callbackResult = response.request.callback->handleEvent(fd, events, data);
            if (callbackResult == 0) {
                AutoMutex _l(mLock);
                removeSequenceNumberLocked(response.seq);
            }

            // Clear the callback reference in the response structure promptly because we
            // will not clear the response vector itself until the next poll.
            response.request.callback.clear();
            result = POLL_CALLBACK;
        }
    }
    return result;
}
```

>   以上代码没有删改，但也不需要看，下面总结

1.   其它线程write fd，epoll_wait才能取得事件。
2.   epoll_wait会阻塞线程，等的时间就是nativePollOnce传入的时间。
3.   epoll_wait获取到一定的events时，根据其中的序号（注册fd时传入的），获取对应的Request对象，并callback（注册fd时传入的），这样就实现了在目标线程回调事件。

## 总结

Android的消息循环主要是Java层，不过在Java层的消息空闲期，也会通过nativePollOnce进行native层的消息循环。

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

`IdleHandler` 是 `MessageQueue` 提供的空闲回调接口，适合执行不紧急、耗时很短的任务。

- **注册与移除**：通过 `MessageQueue.addIdleHandler()` 注册，通过 `removeIdleHandler()` 主动移除。
- **触发条件**：按本文的 `next()` 实现，队列为空，或者队头消息尚未到执行时间时，会回调 `queueIdle()`。所以队列里有延迟消息时，也可能触发空闲回调。
- **返回值**：`queueIdle()` 返回 `false`，表示本次执行后移除；返回 `true`，表示保留，之后再次满足空闲条件时还可以执行。一次 `next()` 调用最多执行一轮已注册的 IdleHandler，不会因为返回 `true` 就在同一次空闲等待中反复回调。
- **执行线程**：回调在该队列所属的 Looper 线程执行。主线程的 IdleHandler 仍然运行在主线程，耗时操作会延迟后续消息处理；队列持续繁忙时，回调也可能迟迟不执行，因此不适合有严格时限的任务。

下面的示例注册两个 IdleHandler，并发送一条延迟消息，观察不同返回值的效果。

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

开始循环时，延迟消息尚未到期，两个 IdleHandler 都会执行；返回 `false` 的随后被移除。延迟消息处理完、队列再次空闲后，只会再次执行返回 `true` 的那个。

## 使用场景

IdleHandler 适合“可以晚点做、单次执行很短、允许等待空闲”的任务，常见场景有：

1. **延后非关键初始化**：例如暂时用不到的功能模块的轻量初始化、非关键监听器注册。这些工作不能是首屏展示或首次交互的必要依赖。
2. **小批量对象预创建**：提前创建少量后续可能使用的对象，减少真正使用时的开销。每次只处理少量工作，避免一次性加载大量布局或执行复杂计算。
3. **轻量内存维护**：例如清理少量失效的内存缓存项、整理临时状态、汇总少量统计数据。
4. **延后提交后台任务**：在空闲回调里向线程池提交可以推迟的预热任务，真正耗时的工作由后台线程完成，回调本身只负责提交。

**注意**：队列空闲不代表首帧已经绘制完成，也不保证接下来有足够长的空闲时间。IdleHandler 不能作为首帧完成通知或定时器；主线程回调中不应直接执行网络请求、磁盘 I/O、数据库查询等耗时工作。有明确完成时限的任务，也不应依赖空闲回调触发。

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

ViewRootImpl在进行view的刷新时，放置了一个Barrier。然后post了一个异步消息，改消息用于主线程渲染。

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

# 几个问题

## 为什么一个线程只有一个Looper、只有一个MessageQueue？

```java
static final ThreadLocal<Looper> sThreadLocal = new ThreadLocal<Looper>();
private static void prepare(boolean quitAllowed) {
    if (sThreadLocal.get() != null) {
        throw new RuntimeException("Only one Looper may be created per thread");
    }
    sThreadLocal.set(new Looper(quitAllowed));
}
```

第一次用prepare创建Looper的时候会创建一个Looper对象并放入sThreadLocal，如果再次调用，get方法返回的不为null，会报错。

至于MessageQueue，Looper中有这么一个变量：

```java
final MessageQueue mQueue;

private Looper(boolean quitAllowed) {
        mQueue = new MessageQueue(quitAllowed);
        mThread = Thread.currentThread();
}
```

MessageQueue是final对象，另外创建Handler的时候

```java
public Handler(Callback callback， boolean async) {
    //...省略
    mQueue = mLooper.mQueue;
    //...省略
}
```

1.   MessageQueue用的是Looper的MessageQueue对象，而Looper只有一个，那么MessageQueue也只有一个。
2.   可以有多个Handler，在分发消息时怎么区分不同的handler？
     在发送消息时handler对象与Message对象绑定在了一起。在分发消息时首先取出Message对象，然后就可以得到与它绑定在一起的Handler对象了。

## 是不是任何线程都可以实例化Handler？有没有什么约束条件？

需要有Looper。

## Looper.loop是一个死循环，拿不到需要处理的Message就会阻塞，那在UI线程中为什么不会导致ANR？

对于线程既然是一段可执行的代码，当可执行代码执行完成后，线程生命周期便该终止了，线程退出。而对于主线程，是绝不希望会被运行一段时间，自己就退出，那么如何保证能一直存活呢？简单做法就是可执行代码是能一直执行下去的，死循环便能保证不会被退出。

另外，因为Android的是由事件驱动的，looper.loop() 不断地接收事件、处理事件，每一个点击触摸或者说Activity的生命周期都是运行在 Looper.loop() 的控制之下，如果它停止了，应用也就停止了。

## Looper是怎样关联当前线程的？

Looper的有一个成员变量，这个成员变量在初始化的时候会引用当前线程。

```java
final Thread mThread;

private Looper(boolean quitAllowed) {
    mQueue = new MessageQueue(quitAllowed);
    mThread = Thread.currentThread();
}
```

## Looper什么时候应该开启

在线程开启的时候开启。

## 如果一个延迟消息还没到时间，怎么处理？

Looper通过loop方法从MeassageQueue的next方法中取出Message。

先记录当前时间now，然后取出一个Message，如果这个Message的when大于now，就会计算两者差值nextPollTimeoutMillis，然后阻塞这么多时间。

如果在还没唤醒时又插入了一个when小于之前Message的when的Message呢？

在MeassageQueue的enqueueMessage方法插入Meaasge的时候，会进行唤醒。

## 为什么不允许在子线程访问UI？

因为UI控件不是线程安全的，在多线程访问UI控件会处于不可预期的状态。

**为什么不加锁？**

锁机制会让UI访问逻辑变得复杂，其次会降低效率。最简单且高效的办法就是用单线程模型来处理UI操作。
