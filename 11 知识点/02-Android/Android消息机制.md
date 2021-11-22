# ThreadLocal

>   具体见源码分析

1.   当某些数据是以线程为作用域且在不同线程具有不同的数据副本时，就可以考虑使用ThreadLocal（比如Looper）。
2.   一个ThreadLocal对象对应一个线程本地变量。
3.   一个线程对应一个ThreadLocalMap，ThreadLocalMap里有个数组table存放Entry类型的对象。
4.   Entry本身是ThreadLocal的弱引用，一个Entry对应一个ThreadLocal和一个value。用弱引用是因为，有些线程是长时间存在的（如主线程），如果使用强引用，可能会导致内存泄露。
5.   ThreadLocal的set方法放入需要的值，先获取Thread，再取出这个Thread的ThreadLocalMap。
     先根据ThreadLocal的hash值和table数组长度获取数组位置。
     如果产生hash冲突，解决办法是位置+1，如果超出了数组长度就放在0位置。
     找到合适的位置后，放入数组中。
     如果超出阈值就扩容。扩容是容量*2。
6.   ThreadLocal的get方法：
     先获取Thread，再取出这个Thread的ThreadLocalMap，然后根据此ThreadLocal取出值。
7.   ThreadLocalMap的初始化是懒加载，table的初始大小是16。

# Handler消息机制

见源码分析。

**介绍**

1.   Android消息机制主要是指Handler + Looper + MessageQueue。MessageQueue内部采用单链表的数据结构。
2.   线程是默认没有Looper，如果需要使用Handler需要创建Looper。

**流程**

1.   Handler post一个runnable或send一个message（post最终是通过send完成的）
2.   调用MessageQueue的enqueueMessage方法将消息放入消息队列中
3.   然后Looper处理，调用`runnable.run`或者handleMessage。

**总结**

1.   创建一个Message。用obtain方法是为了复用Message，因为Handler的消息循环是很频繁的。
2.   Handler的sendMessage系列方法和post系列方法（post内部创建一个msg，然后将runnable设置给msg），最终调用enqueueMessage方法调给messageQueue。
     如果当前MessageQueue阻塞了，并且这个msg被放在MessageQueue的开头，那么就唤醒当前线程（nativeWake）。
3.   将消息放入MessageQueue中。MessageQueue内部的msg是安装when（运行时间）来排序的。
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

**IdleHandler总结**

1.   如果MessageQueue注册了IdleHandler，那么在没有msg执行的空档期会回调IdleHandler的queueIdle方法。如果返回false，则该IdleHandler被移除出MessageQueue；如果返回true，则继续保留该IdleHandler。一个next方法只会回调一次IdleHandler。如果回调完IdleHandler还没到msg的执行时间，那么依然调用nativePollOnce进行阻塞。

**异步消息总结**



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
