# Handler流程

Android消息机制主要是指Handler的运行机制，Handler的运行需要底层的MessageQueue和Looper。MessageQueue不是一个队列，而是采用单链表的数据结构。MessageQueue是存储消息的，而Looper会以无限循环的形式去查看是否有新消息，如果有的话就处理消息。Looper还有一个ThreadLocal，它的作用是在每个线程存储数据。

线程是默认没有Looper，如果需要使用Handler需要创建Looper。

> 为什么不允许在子线程访问UI？
>
> 因为UI控件不是线程安全的，在多线程访问UI控件会处于不可预期的状态。
>
> 为什么不加锁？
>
> 锁机制会让UI访问逻辑变得复杂，其次会降低效率。
>
> 最简单且高效的办法就是用单线程模型来处理UI操作。

流程：

Handler post一个runnable或send一个message（post最终是通过send完成的）---->调用MessageQueue的enqueueMessage方法将消息放入消息队列中---->然后Looper处理，调用runnable或者handlerMessage。

个人总结：

用户创建一个消息发给Handler，Handler将这个消息最终调用enqueueMessage方法调给messageQueue，将消息放入消息队列中，此时Looper找到新消息，就处理这个消息，而Looper交由Handler的dispatchMessage方法来处理，如果这个message内部有个runnable，就执行runnable。如果Handler有Callback（一般在工作方法里传入），就执行Callback的handleMessage方法，这个方法有个boolean返回值，如果返回false，就执行Handler中的handleMessage方法，如果为true，那么消息处理完毕。

```java
public void dispatchMessage(Message msg) {
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

# ThreadLocal

当某些数据是以线程为作用域且在不同线程具有不同的数据副本时，就可以考虑使用ThreadLocal（比如Looper）。

每个线程都有一个ThreadLocalMap，ThreadLocalMap里有个数组table（Map本质就是数组）存放Entry的对象。

Entry本身就是ThreadLocal的弱引用，key就是ThreadLocal（或者说是Entry），成员变量只有value。用弱引用是因为，有些线程是长时间存在的（如主线程），如果使用强引用，可能会导致内存泄露。

ThreadLocal的set方法放入需要的值，先获取Thread，再取出这个Thread的ThreadLocalMap。既然叫Map，那操作和Map差不多。先根据hash值和table数组长度获取数组位置，如果产生hash冲突，这里的解决办法是位置+1，如果存在key，就更新值，直到找到一个null的位置。如果超出了数组长度就放在0位置，然后扩容。扩容是容量*2，具体细节没必要深入。

ThreadLocal的get方法：先获取Thread，再取出这个Thread的ThreadLocalMap，然后根据此ThreadLocal取出值。

# 消息队列MessageQueue

主要包含两个操作：插入（enqueueMessage）和读取（next）。

next是一个无限循环的方法，如果消息队列没有消息，next就一直阻塞，当有消息时，next方法会返回这条消息并从单链表中删除。

# Looper

Looper会不停地从MessageQueue查看是否有新消息。

```java
new Thread(new Runnable() {
    @Override
    public void run() {
        Looper.prepare();//创建Looper
        Handler handler=new Handler();
        Looper.loop();//开启循环
    }
}).start();
```

# 几个问题

1.**为什么一个线程只有一个Looper、只有一个MessageQueue？**

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

MessageQueue用的是Looper的MessageQueue对象，而Looper只有一个，那么MessageQueue也只有一个。

> 可以有多个Handler。
>
> looper对象只有一个，在分发消息时怎么区分不同的handler？
>
> 关于这个问题主要看三点： 
> 一是Message类中有个字段target，这个字段是Handler类型的。 
> 二在Handler的enqueueMessage方法中有这么一句代码：msg.target = this;即把handler对象与Message绑定在了一起。 
> 三在Looper类的looper方法中分发消息的代码是：msg.target.dispatchMessage(msg);
>
> 此时就明白了：在发送消息时handler对象与Message对象绑定在了一起。在分发消息时首先取出Message对象，然后就可以得到与它绑定在一起的Handler对象了。

2.**如何获取当前线程的Looper？是怎么实现的？（理解ThreadLocal）**

```java
Looper.myLooper();

public static @Nullable Looper myLooper() {
        return sThreadLocal.get();
}

static final ThreadLocal<Looper> sThreadLocal = new ThreadLocal<Looper>();
private static void prepare(boolean quitAllowed) {
        ...//省略
        sThreadLocal.set(new Looper(quitAllowed));
}

```

Looper在创建的时候就加进了ThreadLocal中

3.**是不是任何线程都可以实例化Handler？有没有什么约束条件？**

需要有Looper

4.**Looper.loop是一个死循环，拿不到需要处理的Message就会阻塞，那在UI线程中为什么不会导致ANR？**

对于线程既然是一段可执行的代码，当可执行代码执行完成后，线程生命周期便该终止了，线程退出。而对于主线程，我们是绝不希望会被运行一段时间，自己就退出，那么如何保证能一直存活呢？**简单做法就是可执行代码是能一直执行下去的，死循环便能保证不会被退出**

https://www.zhihu.com/question/34652589

另外，因为Android的是由事件驱动的，looper.loop() 不断地接收事件、处理事件，每一个点击触摸或者说Activity的生命周期都是运行在 Looper.loop() 的控制之下，如果它停止了，应用也就停止了。

> 再次思考：
>
> 既然是死循环又如何去处理其他事务呢？
>
> 通过创建新线程的方式。
>
> 没看见哪里有相关代码为这个死循环准备了一个新线程去运转？
>
> 事实上，会在进入死循环之前便创建了新binder线程，在代码ActivityThread.main()中：
>
> ```java
> public static void main(String[] args) {
>      ....
> 
>      //创建Looper和MessageQueue对象，用于处理主线程的消息
>      Looper.prepareMainLooper();
> 
>      //创建ActivityThread对象
>      ActivityThread thread = new ActivityThread(); 
> 
>      //建立Binder通道 (创建新线程)
>      thread.attach(false);
> 
>      Looper.loop(); //消息循环运行
>      throw new RuntimeException("Main thread loop unexpectedly exited");
>  }
> ```
>
> **thread.attach(false)；便会创建一个Binder线程（具体是指ApplicationThread，Binder的服务端，用于接收系统服务AMS发送来的事件），该Binder线程通过Handler将Message发送给主线程**

Loop的loop方法是一个死循环，但是如果没有Message（取到的Message为null）就退出死循环了。

5.**Handler.sendMessageDelayed()怎么实现延迟的？结合Looper.loop()循环中，Message = messageQueue.next()和MessageQueue.enqueueMessage()分析。**

```java
public final boolean sendMessageDelayed(Message msg， long delayMillis)
{
    ...//省略
    return sendMessageAtTime(msg， SystemClock.uptimeMillis() + delayMillis);
}
```

```java
public boolean sendMessageAtTime(Message msg， long uptimeMillis) {
    ...//省略
    return enqueueMessage(queue， msg， uptimeMillis);
}
```

```java
private boolean enqueueMessage(MessageQueue queue， Message msg， long uptimeMillis) {
    ...//省略
    return queue.enqueueMessage(msg， uptimeMillis);
}

```

Handler.sendMessageDelayed()最终会调用MessageQueue.enqueueMessage()方法将消息插入消息队列里。

这是MessageQueue.enqueueMessage()：

```java
boolean enqueueMessage(Message msg， long when) {
...//省略
        msg.when = when;
        Message p = mMessages;
        if (p == null || when == 0 || when < p.when) {
            // New head， wake up the event queue if blocked.
            msg.next = p;
            mMessages = msg;
            needWake = mBlocked;
        } else {
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
...//省略
}
```

代码比较难看，但是我看了一眼判断条件，我就有点清楚，于是猜想：Message的插入顺序按照when（设置时间）来的，设置了delay之后，如果有个Message插进来了，和当前的Message进行比较，如果比当前早，那么插在前面。如果比当前的晚，那么用一个死循环不停地找，next一直调用，直到找到一个比DelayMessage晚的Message，然后把DelayMessage放在Message的前面`msg.next = p;`。

> 总之就是MessageQueue的排序是按照Message的成员变量when来排的。

**6.Looper是怎样关联当前线程的？**

Looper的有一个成员变量，这个成员变量在初始化的时候会引用当前线程。

```java
final Thread mThread;

private Looper(boolean quitAllowed) {
    mQueue = new MessageQueue(quitAllowed);
    mThread = Thread.currentThread();
}
```

**7.Looper什么时候开启**

在线程开启的时候开启。

**8.如果一个延迟消息还没到时间，怎么处理？**

Looper通过loop方法从MeassageQueue的next方法中取出Message。

先记录当前时间now，然后取出一个Message，如果这个Message的when大于now，就会计算两者差值nextPollTimeoutMillis，然后阻塞这么多时间。

如果在还没唤醒时又插入了一个when小于之前Message的when的Message呢？

在MeassageQueue的enqueueMessage方法插入Meaasge的时候，会进行唤醒。