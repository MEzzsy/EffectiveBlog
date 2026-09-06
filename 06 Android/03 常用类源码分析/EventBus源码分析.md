# EventBus的基本使用

>   使用版本：3.2.0。

EventBus是观察者模式的具体实现，当某处产生事件时，其订阅者就会收到消息并作出反应。本章介绍EventBus的基本使用。更多的使用可以参照[官网](https://greenrobot.org/eventbus/)。

## 快速使用

使用者需要将某一事件抽象成Java类，以及编写对应订阅者的处理方法。这里举一个例子，并不具有实际意义，如：

**事件发送**

```java
@Override
protected void onResume() {
    super.onResume();
    EventBus.getDefault().post(new ResumeEvent("onResume"));
}
```

这里将Activity的onResume方法作为一个事件，当onResume回调时，会发送一个事件ResumeEvent。

**事件**

```java
public class ResumeEvent {
    String message;

    public ResumeEvent(String message) {
        this.message = message;
    }
}
```

**事件的订阅者**

```java
public class EventSubscriber {
    private static final String TAG = "EventSubscriber";
    private String mName;

    public EventSubscriber(String name) {
        mName = name;
    }

    public void register() {
        EventBus.getDefault().register(this);
    }

    @Subscribe
    public void onEvent(ResumeEvent event) {
        Log.i(TAG, "onEvent: name = " + mName
                + " ,message = " + event.message
                + " ,thread = " + Thread.currentThread().getName());
    }

    public void unregister() {
        EventBus.getDefault().unregister(this);
    }

}
```

EventBus.getDefault()返回默认的EventBus对象，也可以用EventBus.builder()创建一个自定义的EventBus对象，一般使用默认的EventBus对象。

register方法传入一个订阅者对象，unregister用来解注册，防止内存泄漏。

@Subscribe注解标识订阅者的处理方法，要求是方法修饰符是public并且参数只能是事件的类型，否者会无法找到对应的处理方法，这里处理方法的逻辑就是打印日志。

**注册和解注册**

```java
public class EventBusActivity extends BaseActivity {
    private EventSubscriber mEventSubscriber;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        //...
        mEventSubscriber = new EventSubscriber("小明");
    }

    @Override
    protected void onStart() {
        super.onStart();
        mEventSubscriber.register();
    }
    
    //...

    @Override
    protected void onStop() {
        super.onStop();
        mEventSubscriber.unregister();
    }
}
```

**输出日志**

```
EventSubscriber: onEvent: name = 小明 ,message = onResume ,thread = main
```

可以看到，事件发生时，订阅者做出了具体的回应。

## 线程模式

EventBus有五种线程模式，用来指定处理方法所在线程，在注解@Subscribe中进行指定。

### POSTING

默认的模式，事件在哪个线程发送就在哪个线程处理。以下的代码将在上述代码的基础上进行修改：

```java
@Override
protected void onResume() {
    super.onResume();
    EventBus.getDefault().post(new PostingEvent("主线程"));
    new Thread(new Runnable() {
        @Override
        public void run() {
            EventBus.getDefault().post(new PostingEvent("子线程"));
        }
    }, "thread-eventbus").start();
}
```

```java
@Subscribe
public void onEvent(PostingEvent event) {
    Log.i(TAG, "onEvent: name = " + mName
            + " ,message = " + event.message
            + " ,thread = " + Thread.currentThread().getName());
}
```

输出log：

```
EventSubscriber: PostingEvent: name = 小明 ,message = 主线程 ,thread = main
EventSubscriber: PostingEvent: name = 小明 ,message = 子线程 ,thread = thread-eventbus
```

日志显示，在主线程post的事件会在主线程被处理，在子线程post的线程会在子线程被处理。

### MAIN

指定在Android主线程中进行方法处理。

先查看在主线程post事件的情况：

```java
@Override
protected void onResume() {
    super.onResume();
    new Thread(new Runnable() {
        @Override
        public void run() {
            EventBus.getDefault().post(new MainEvent("子线程"));
        }
    }, "thread-eventbus").start();
    EventBus.getDefault().post(new MainEvent("主线程"));
}
```

在处理方法中又post了一个事件。

```java
@Subscribe(threadMode = ThreadMode.MAIN)
public void onEvent(MainEvent event) {
    Log.i(TAG, "MainEvent: name = " + mName
            + " ,message = " + event.message
            + " ,thread = " + Thread.currentThread().getName());
    Log.i(TAG, "MainEvent: end. message = " + event.message);
}
```

log如下：

```
EventSubscriber: MainEvent: name = 小明 ,message = 主线程 ,thread = main
EventSubscriber: MainEvent: end. message = 主线程
EventSubscriber: MainEvent: name = 小明 ,message = 子线程 ,thread = main
EventSubscriber: MainEvent: end. message = 子线程
```

### MAIN_ORDERED

MAIN_ORDERED也是在主线程中执行处理方法，和MAIN不同的是，MAIN会可能出现这种情况，先postA事件，然后postB事件，但是B先执行完，然后A执行完。MAIN_ORDERED保证了顺序，先post的先执行完。

如：

**MAIN模式**

```java
@Override
protected void onResume() {
    super.onResume();
    new Thread(new Runnable() {
        @Override
        public void run() {
            EventBus.getDefault().post(new MainEvent("子线程"));
        }
    }, "thread-eventbus").start();
}
```

在子线程post一个事件。

```java
@Subscribe(threadMode = ThreadMode.MAIN)
public void onEvent(MainEvent event) {
    Log.i(TAG, "MainEvent: name = " + mName
            + " ,message = " + event.message
            + " ,thread = " + Thread.currentThread().getName());
    EventBus.getDefault().post(new AnotherMainEvent("aaa"));
    Log.i(TAG, "MainEvent: end. message = " + event.message);
}

@Subscribe(threadMode = ThreadMode.MAIN)
public void onEvent(AnotherMainEvent event) {
    Log.i(TAG, "AnotherMainEvent: name = " + mName
            + " ,message = " + event.message
            + " ,thread = " + Thread.currentThread().getName());
    Log.i(TAG, "AnotherMainEvent: end. message = " + event.message);
}
```

在第一个处理方法中又post另一个MAIN模式的事件。

日志：

```
EventSubscriber: MainEvent: name = 小明 ,message = 子线程 ,thread = main
EventSubscriber: AnotherMainEvent: name = 小明 ,message = aaa ,thread = main
EventSubscriber: AnotherMainEvent: end. message = aaa
EventSubscriber: MainEvent: end. message = 子线程
```

而类似的代码在MAIN_ORDERED下的日志：

```
EventSubscriber: MainOrderedEvent: name = 小明 ,message = 子线程 ,thread = main
EventSubscriber: MainOrderedEvent: end. message = 子线程
EventSubscriber: AnotherMainOrderedEvent: name = 小明 ,message = aaa ,thread = main
EventSubscriber: AnotherMainOrderedEvent: end. message = aaa
```

### BACKGROUND

如果在主线程post，那么在子线程中处理；如果在子线程post，那么就在原线程中处理。

```java
@Override
    protected void onResume() {
        super.onResume();
        EventBus.getDefault().post(new BackgroundEvent("主线程"));
        new Thread(new Runnable() {
            @Override
            public void run() {
                EventBus.getDefault().post(new BackgroundEvent("子线程"));
            }
        }, "thread-eventbus").start();
    }
```

```java
@Subscribe(threadMode = ThreadMode.BACKGROUND)
public void onEvent(BackgroundEvent event) {
    Log.i(TAG, "BackgroundEvent: name = " + mName
            + " ,message = " + event.message
            + " ,thread = " + Thread.currentThread().getName());
}
```

log如下：

```
EventSubscriber: BackgroundEvent: name = 小明 ,message = 主线程 ,thread = pool-1-thread-1
EventSubscriber: BackgroundEvent: name = 小明 ,message = 子线程 ,thread = thread-eventbus
```

### ASYNC

不管在什么线程post，都会在另一个子线程中处理。

```java
@Override
    protected void onResume() {
        super.onResume();
        EventBus.getDefault().post(new AsyncEvent("主线程"));
        new Thread(new Runnable() {
            @Override
            public void run() {
                EventBus.getDefault().post(new AsyncEvent("子线程"));
            }
        }, "thread-eventbus").start();
    }
```

```java
@Subscribe(threadMode = ThreadMode.ASYNC)
public void onEvent(AsyncEvent event) {
    Log.i(TAG, "AsyncEvent: name = " + mName
            + " ,message = " + event.message
            + " ,thread = " + Thread.currentThread().getName());
}
```

日志如下：

```
EventSubscriber: AsyncEvent: name = 小明 ,message = 主线程 ,thread = pool-1-thread-1
EventSubscriber: AsyncEvent: name = 小明 ,message = 子线程 ,thread = pool-1-thread-1
```

## 延迟事件

EventBus还提供了延迟事件，使得那些订阅此事件同时初始化在事件发生之后的对象能够响应此事件。使用很简单，只要调用EventBus对象的postSticky方法即可：

```java
EventBus.getDefault().postSticky(new StickyEvent("onCreate"));
```

当不想延迟事件被后续订阅者接收时，可以调用EventBus对象的removeStickyEvent方法进行移除：

```java
StickyEvent stickyEvent = EventBus.getDefault().getStickyEvent(StickyEvent.class);
if (stickyEvent != null) {
    EventBus.getDefault().removeStickyEvent(StickyEvent.class);
}
```

另外，订阅者处理方法的注解要设置sticky为true：

```java
@Subscribe(sticky = true,threadMode = ThreadMode.MAIN)
public void onEvent(StickyEvent event) {
    Log.i(TAG, "AsyncEvent: name = " + mName
            + " ,message = " + event.message
            + " ,thread = " + Thread.currentThread().getName());
}
```

下面的示例为两个按钮，一个按钮用来创建订阅者，一个按钮用来停止延迟事件，而延迟事件的发生在它们前面。

```java
public class EventBusActivity extends BaseActivity {
    private List<EventSubscriber> mEventSubscribers;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_event_bus);
        mEventSubscribers = new ArrayList<>();
        findViewById(R.id.btn_create_subscriber).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Log.i(EventSubscriber.TAG, "创建订阅者");
                String name = String.valueOf(System.currentTimeMillis());
                EventSubscriber eventSubscriber = new EventSubscriber(name);
                eventSubscriber.register();
                mEventSubscribers.add(eventSubscriber);
            }
        });
        findViewById(R.id.btn_stop).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Log.i(EventSubscriber.TAG, "停止延迟事件");
                StickyEvent stickyEvent = EventBus.getDefault().getStickyEvent(StickyEvent.class);
                if (stickyEvent != null) {
                    EventBus.getDefault().removeStickyEvent(StickyEvent.class);
                }
            }
        });

        EventBus.getDefault().postSticky(new StickyEvent("onCreate"));
    }

    @Override
    protected void onStop() {
        super.onStop();
        for (EventSubscriber eventSubscriber : mEventSubscribers) {
            eventSubscriber.unregister();
        }
    }
}
```

日志如下：

```
EventSubscriber: 创建订阅者
EventSubscriber: AsyncEvent: name = 1589614794126 ,message = onCreate ,thread = main
EventSubscriber: 创建订阅者
EventSubscriber: AsyncEvent: name = 1589614795482 ,message = onCreate ,thread = main
EventSubscriber: 创建订阅者
EventSubscriber: AsyncEvent: name = 1589614796669 ,message = onCreate ,thread = main
EventSubscriber: 停止延迟事件
EventSubscriber: 创建订阅者
EventSubscriber: 创建订阅者
```

如日志所示，当停止延迟事件后，创建订阅者已经不会再进行处理。

## Subscriber Index

EventBus处理方法是在运行时通过反射调用的，3.0之后，可以在编译期生成注释处理器。用这个方法可以提升性能。

使用方法，在app的build.gradle里添加下面的代码：

```groovy
android {
    defaultConfig {
        javaCompileOptions {
            annotationProcessorOptions {
                arguments = [ eventBusIndex : 'com.example.myapp.MyEventBusIndex' ]
            }
        }
    }
}

dependencies {
    def eventbus_version = '3.2.0'
    implementation "org.greenrobot:eventbus:$eventbus_version"
    annotationProcessor "org.greenrobot:eventbus-annotation-processor:$eventbus_version"
}
```

然后编译项目，项目会生成MyEventBusIndex类。然后将这个Index类加入到EventBus对象：

```java
EventBus eventBus = EventBus.builder().addIndex(new MyEventBusIndex()).build();
```

如果想EventBus.getDefault的对象也有这种功能，可以这样使用：

```java
EventBus.builder().addIndex(new MyEventBusIndex()).installDefaultEventBus();
```

## 其他功能

EventBus还有一些其它功能，比如自定义EventBus对象、优先级等。有兴趣的读者可以自行分析，本文不再介绍。

# EventBus源码分析

下面根据上文的基本使用来对EventBus源码进行分析。

## getDefault

从EventBus的入口开始分析。

**EventBus#getDefault()**

```java
public static EventBus getDefault() {
    EventBus instance = defaultInstance;
    if (instance == null) {
        synchronized (EventBus.class) {
            instance = EventBus.defaultInstance;
            if (instance == null) {
                instance = EventBus.defaultInstance = new EventBus();
            }
        }
    }
    return instance;
}
```

这里就是采用双重校验并加锁(DCL)的单例模式生成EventBus实例。 

## 注册register

```java
public void register(Object subscriber) {
    Class<?> subscriberClass = subscriber.getClass();
    List<SubscriberMethod> subscriberMethods = subscriberMethodFinder.findSubscriberMethods(subscriberClass);
    synchronized (this) {
        for (SubscriberMethod subscriberMethod : subscriberMethods) {
            subscribe(subscriber, subscriberMethod);
        }
    }
}
```

第一行代码获取了订阅者的class对象，然后第二行代码找出所有订阅的方法。

### SubscriberMethodFinder#findSubscriberMethods

```java
List<SubscriberMethod> findSubscriberMethods(Class<?> subscriberClass) {
    //代码1
    List<SubscriberMethod> subscriberMethods = METHOD_CACHE.get(subscriberClass);
    if (subscriberMethods != null) {
        return subscriberMethods;
    }
	//代码2
    if (ignoreGeneratedIndex) {
        subscriberMethods = findUsingReflection(subscriberClass);
    } else {
        subscriberMethods = findUsingInfo(subscriberClass);
    }
    
    if (subscriberMethods.isEmpty()) {
        throw new EventBusException("Subscriber " + subscriberClass
                + " and its super classes have no public methods with the @Subscribe annotation");
    } else {
        METHOD_CACHE.put(subscriberClass, subscriberMethods);
        return subscriberMethods;
    }
}
```

分析：

-   代码1查看是否有缓存。
-   代码2的ignoreGeneratedIndex变量表示是否强制使用反射加载处理方法，true为强制使用，默认为false。可通过EventBusBuilder设置。这里以false进行分析。

后面生成subscriberMethods成功的话会加入到缓存中，失败的话会throw异常。

 ```java
throw new EventBusException("Subscriber " + subscriberClass + 
          " and its super classes have no public methods with the @Subscribe annotation");
 ```

> 抛出异常说明添加注解的方法的访问修饰符需要为public。

###  SubscriberMethodFinder#findUsingInfo

```java
private List<SubscriberMethod> findUsingInfo(Class<?> subscriberClass) {
    FindState findState = prepareFindState();//代码1
    findState.initForSubscriber(subscriberClass);//代码2
    while (findState.clazz != null) {
        findState.subscriberInfo = getSubscriberInfo(findState);//代码3
        if (findState.subscriberInfo != null) {
            SubscriberMethod[] array = findState.subscriberInfo.getSubscriberMethods();
            for (SubscriberMethod subscriberMethod : array) {
                if (findState.checkAdd(subscriberMethod.method, subscriberMethod.eventType)) {
                    findState.subscriberMethods.add(subscriberMethod);
                }
            }
        } else {
            findUsingReflectionInSingleClass(findState);//代码4
        }
        findState.moveToSuperclass();
    }
    return getMethodsAndRelease(findState);//代码5
}
```

分析：

-   代码1表示从FindState对象池中获取一个FindState对象。
-   代码2初始化FindState对象。
-   代码3到代码4之间的代码是这样的，在EventBus基本使用中，有个Subscriber Index的优化方法，使得注解处理放到了编译期间，编译后会自动生成继承SubscriberInfoIndex类型的类，在创建EventBus对象的时候，通过addIndex方法将SubscriberInfoIndex对象传入进去。
    如果使用了这个优化方法，那么就不用通过反射的方式获取处理方法信息，直接将处理方法信息封装成SubscriberMethod对象并放入findState.subscriberMethods中。
    如果没有使用这个优化方法，就见代码4，通过反射的方式获取处理方法信息。
-   代码4，分析见`SubscriberMethodFinder#findUsingReflectionInSingleClass`
-   while循环会继续检查父类(findState.moveToSuperclass，当然遇到系统相关的类（如包名java开头的类）时会自动跳过，以提升性能。
-   代码5，将findState.subscriberMethods数组转为`List<SubscriberMethod>`对象，并将findState重置并放入FindState对象池中。

#### SubscriberMethodFinder#findUsingReflectionInSingleClass

```java
private void findUsingReflectionInSingleClass(FindState findState) {
    Method[] methods;
    try {
        methods = findState.clazz.getDeclaredMethods();
    } //。。。catch略
    
    for (Method method : methods) {
        int modifiers = method.getModifiers();
        if ((modifiers & Modifier.PUBLIC) != 0 && (modifiers & MODIFIERS_IGNORE) == 0) {
            Class<?>[] parameterTypes = method.getParameterTypes();
            if (parameterTypes.length == 1) {
                Subscribe subscribeAnnotation = method.getAnnotation(Subscribe.class);
                if (subscribeAnnotation != null) {
                    Class<?> eventType = parameterTypes[0];
                    if (findState.checkAdd(method, eventType)) {
                        ThreadMode threadMode = subscribeAnnotation.threadMode();
                        findState.subscriberMethods.add(new SubscriberMethod(method, eventType, threadMode,
                                subscribeAnnotation.priority(), subscribeAnnotation.sticky()));
                    }
                }
            } else if (strictMethodVerification && method.isAnnotationPresent(Subscribe.class)) {
                String methodName = method.getDeclaringClass().getName() + "." + method.getName();
                throw new EventBusException("@Subscribe method " + methodName +
                        "must have exactly 1 parameter but has " + parameterTypes.length);
            }
        } else if (strictMethodVerification && method.isAnnotationPresent(Subscribe.class)) {
            String methodName = method.getDeclaringClass().getName() + "." + method.getName();
            throw new EventBusException(methodName +
                    " is a illegal @Subscribe method: must be public, non-static, and non-abstract");
        }
    }
}
```

这个方法先是获取订阅者类的所有声明方法，寻找修饰符为public并且参数长度为1的方法，如果这个方法带有Subscribe注解，那么就提取这个方法的信息，如：参数类型、注解内容、method对象等，将这些信息封装成SubscriberMethod对象放入findState.subscriberMethods中。

### EventBus#subscribe

返回subscriberMethods之后，register方法的最后会调用subscribe方法： 

```java
private void subscribe(Object subscriber, SubscriberMethod subscriberMethod) {
    //代码1
    Class<?> eventType = subscriberMethod.eventType;
    Subscription newSubscription = new Subscription(subscriber, subscriberMethod);
    CopyOnWriteArrayList<Subscription> subscriptions = subscriptionsByEventType.get(eventType);
    if (subscriptions == null) {
        subscriptions = new CopyOnWriteArrayList<>();
        subscriptionsByEventType.put(eventType, subscriptions);
    } else {
        if (subscriptions.contains(newSubscription)) {
            throw new EventBusException("Subscriber " + subscriber.getClass() + " already registered to event "
                    + eventType);
        }
    }

    //代码2
    int size = subscriptions.size();
    for (int i = 0; i <= size; i++) {
        if (i == size || subscriberMethod.priority > subscriptions.get(i).subscriberMethod.priority) {
            subscriptions.add(i, newSubscription);
            break;
        }
    }

    //代码3
    List<Class<?>> subscribedEvents = typesBySubscriber.get(subscriber);
    if (subscribedEvents == null) {
        subscribedEvents = new ArrayList<>();
        typesBySubscriber.put(subscriber, subscribedEvents);
    }
    subscribedEvents.add(eventType);

    //代码4
    if (subscriberMethod.sticky) {
        if (eventInheritance) {
            Set<Map.Entry<Class<?>, Object>> entries = stickyEvents.entrySet();
            for (Map.Entry<Class<?>, Object> entry : entries) {
                Class<?> candidateEventType = entry.getKey();
                if (eventType.isAssignableFrom(candidateEventType)) {
                    Object stickyEvent = entry.getValue();
                    checkPostStickyEventToSubscription(newSubscription, stickyEvent);
                }
            }
        } else {
            Object stickyEvent = stickyEvents.get(eventType);
            checkPostStickyEventToSubscription(newSubscription, stickyEvent);
        }
    }
}
```

首先介绍一下出现的部分变量：

-   subscriptionsByEventType，`Map<Class<?>, CopyOnWriteArrayList<Subscription>>`类型，用来存储以事件类型为键、以Subscription列表为值的键值对。
-   typesBySubscriber，`Map<Object, List<Class<?>>>`类型，用来存储以订阅者对象为键、以事件类型列表为值的键值对。
-   stickyEvents，`Map<Class<?>, Object>`类型，用来存储以事件类型为键、以事件对象为值的键值对。

分析：

- 代码1，根据事件类型在subscriptionsByEventType去查找一个Subscription列表，Subscription是一个封装了订阅者对象和其处理方法的类型 ，如果没有则创建一个新的Subscription列表。从throw中也可以看出，EventBus不支持对同一个对象进行注册。
- 代码2，根据优先级将newSubscription对象放入到Subscription列表中。
- 代码3，将subscriber和subscribedEvents放入typesBySubscriber中。typesBySubscriber在判断订阅者是否注册以及解注册中会用到。
- 代码4，判断是否是sticky事件，如果是sticky事件的话，到最后会调用checkPostStickyEventToSubscription方法。这里有个eventInheritance变量，默认为true，它的作用是这样的，如果为true，就将sticky事件对象以及父类对象依次传入checkPostStickyEventToSubscription方法；如果为false，只将sticky事件对象本身传入checkPostStickyEventToSubscription方法。

####  EventBus#checkPostStickyEventToSubscription

```java
private void checkPostStickyEventToSubscription(Subscription newSubscription, Object stickyEvent) {
    if (stickyEvent != null) {
        postToSubscription(newSubscription, stickyEvent, isMainThread());
    }
}
```

checkPostStickyEventToSubscription调用了postToSubscription方法，postToSubscription方法的分析见下。

### 小结

register方法主要是将订阅者的处理方法提取封装，EventBus使用反射和编译期分析的方式进行提取。另外，将此期间产生的部分对象存储到Map或者列表中。

##  发送事件post

**EventBus#post**

```java
public void post(Object event) {
    PostingThreadState postingState = currentPostingThreadState.get();
    List<Object> eventQueue = postingState.eventQueue;
    eventQueue.add(event);

    if (!postingState.isPosting) {
        postingState.isMainThread = isMainThread();
        postingState.isPosting = true;
        if (postingState.canceled) {
            throw new EventBusException("Internal error. Abort state was not reset");
        }
        try {
            while (!eventQueue.isEmpty()) {
                postSingleEvent(eventQueue.remove(0), postingState);
            }
        } finally {
            postingState.isPosting = false;
            postingState.isMainThread = false;
        }
    }
}
```

currentPostingThreadState是一个ThreadLocal类型的对象，里面存储了PostingThreadState，而PostingThreadState中包含了一个eventQueue和其他一些标志位。

然后把传入的事件对象，放入eventQueue中，接着将eventQueue的对象取出并传入postSingleEvent方法中。

###  EventBus#postSingleEvent

```java
private void postSingleEvent(Object event, PostingThreadState postingState) throws Error {
    Class<?> eventClass = event.getClass();
    boolean subscriptionFound = false;
    if (eventInheritance) {//代码1
        List<Class<?>> eventTypes = lookupAllEventTypes(eventClass);//代码2
        int countTypes = eventTypes.size();
        for (int h = 0; h < countTypes; h++) {
            Class<?> clazz = eventTypes.get(h);
            subscriptionFound |= postSingleEventForEventType(event, postingState, clazz);
        }
    } else {
        subscriptionFound = postSingleEventForEventType(event, postingState, eventClass);
    }
    if (!subscriptionFound) {
        if (logNoSubscriberMessages) {
            logger.log(Level.FINE, "No subscribers registered for event " + eventClass);
        }
        if (sendNoSubscriberEvent && eventClass != NoSubscriberEvent.class &&
                eventClass != SubscriberExceptionEvent.class) {
            post(new NoSubscriberEvent(this, event));
        }
    }
}
```

-   代码1，eventInheritance在register方法中也出现了，其默认值为true，就是是否把事件类的父类算上。

-   代码2，lookupAllEventTypes方法是获取事件及其父类，内部有个缓存以提升性能。

最终都会调用postSingleEventForEventType方法。

#### EventBus#postSingleEventForEventType

```java
private boolean postSingleEventForEventType(Object event, PostingThreadState postingState, Class<?> eventClass) {
    //代码1
    CopyOnWriteArrayList<Subscription> subscriptions;
    synchronized (this) {
        subscriptions = subscriptionsByEventType.get(eventClass);
    }
    if (subscriptions != null && !subscriptions.isEmpty()) {
        for (Subscription subscription : subscriptions) {
            postingState.event = event;
            postingState.subscription = subscription;
            boolean aborted;
            try {
                postToSubscription(subscription, event, postingState.isMainThread);//代码2
                aborted = postingState.canceled;
            } finally {
                postingState.event = null;
                postingState.subscription = null;
                postingState.canceled = false;
            }
            if (aborted) {
                break;
            }
        }
        return true;
    }
    return false;
}
```

-   代码1，上文说过，subscriptionsByEventType是`Map<Class<?>, CopyOnWriteArrayList<Subscription>>`类型，用来存储以事件类型为键、以Subscription列表为值的键值对。而Subscription是一个封装了订阅者对象和其处理方法的类型。取出的`CopyOnWriteArrayList<Subscription>`就是对某事件感兴趣的订阅者集合。
-   代码2，然后遍历集合，取出subscription对象和事件对象并调用postToSubscription方法。

###  EventBus#postToSubscription

```java
private void postToSubscription(Subscription subscription, Object event, boolean isMainThread) {
    switch (subscription.subscriberMethod.threadMode) {
        case POSTING:
            invokeSubscriber(subscription, event);
            break;
        case MAIN:
            if (isMainThread) {
                invokeSubscriber(subscription, event);
            } else {
                mainThreadPoster.enqueue(subscription, event);
            }
            break;
        case MAIN_ORDERED:
            if (mainThreadPoster != null) {
                mainThreadPoster.enqueue(subscription, event);
            } else {
                invokeSubscriber(subscription, event);
            }
            break;
        case BACKGROUND:
            if (isMainThread) {
                backgroundPoster.enqueue(subscription, event);
            } else {
                invokeSubscriber(subscription, event);
            }
            break;
        case ASYNC:
            asyncPoster.enqueue(subscription, event);
            break;
        default:
            throw new IllegalStateException("Unknown thread mode: " + subscription.subscriberMethod.threadMode);
    }
}
```

此方法根据订阅者处理方法的注解中的线程模式threadMode，根据其效果（每个线程模式的效果可见上文基本使用）进行线程调度，核心方法是invokeSubscriber。

线程模式虽然有5种，但是可以总结为2种（A、B为不同线程）：

1.  在A线程post事件，在A线程中处理。
2.  在A线程post事件，在B线程中处理。

对于第一种情况，主要逻辑在post方法中，利用队列和isPosting标记位，先将事件加入队列，然后判断isPosting，如果是，说明有其它事件在处理中，那么此事件在队列中等待处理；如果否，那么就直接处理此事件。

对于第二种情况，原理是队列+线程池，将任务加入到队列中，依次交给线程池处理，典型的异步处理方法。（如果是在主线程处理的，那么是利用Handler调度到主线程中再处理。）

### 小结

post方法将传入的事件对象放到一个队列排队，不断取出第一个事件，根据事件类型，从Map中取出对应的订阅者和处理方法列表，并反射调用订阅者的方法来处理此事件。

## 发送Sticky事件postSticky

```java
public void postSticky(Object event) {
    synchronized (stickyEvents) {
        stickyEvents.put(event.getClass(), event);
    }
    post(event);
}
```

postSticky只有两段代码，第一段是将事件存储至stickyEvents，等待后面关注此事件的订阅者产生。第二段是立即调用post方法，使存在的订阅者能过处理此事件。

再回过头看看注册register那一章的最后一段，checkPostStickyEventToSubscription方法调用了postToSubscription方法，这一段解释了postSticky如何使后面出现的订阅者能够处理此事件。在注册订阅者的时候，如果发现订阅者的处理方法中存在Sticky类型的处理方法，那么就在已经post过的Sticky事件列表（即stickyEvents）中寻找匹配的事件类型，并立即处理。

## 解注册unregister

```java
public synchronized void unregister(Object subscriber) {
    List<Class<?>> subscribedTypes = typesBySubscriber.get(subscriber);
    if (subscribedTypes != null) {
        for (Class<?> eventType : subscribedTypes) {
            unsubscribeByEventType(subscriber, eventType);
        }
        typesBySubscriber.remove(subscriber);
    } else {
        logger.log(Level.WARNING, "Subscriber to unregister was not registered before: " + subscriber.getClass());
    }
}
```

```java
private void unsubscribeByEventType(Object subscriber, Class<?> eventType) {
    List<Subscription> subscriptions = subscriptionsByEventType.get(eventType);
    if (subscriptions != null) {
        int size = subscriptions.size();
        for (int i = 0; i < size; i++) {
            Subscription subscription = subscriptions.get(i);
            if (subscription.subscriber == subscriber) {
                subscription.active = false;
                subscriptions.remove(i);
                i--;
                size--;
            }
        }
    }
}
```

上文讲过，与订阅者对象有关的集合有这么一些：

-   subscriptionsByEventType，`Map<Class<?>, CopyOnWriteArrayList<Subscription>>`类型，用来存储以事件类型为键、以Subscription列表为值的键值对。Subscription是一个封装了订阅者对象和其处理方法的类型。
-   typesBySubscriber，`Map<Object, List<Class<?>>>`类型，用来存储以订阅者对象为键、以事件类型列表为值的键值对。

解注册就是把与此订阅者对象相关的从集合中清除。

#  个人总结

EventBus主要关注两个方法：register方法和post方法。

register方法，传入观察者对象的Class对象，然后通过运行时反射或者编译期注解解释将处理方法及Subscribe注解内容放在一个列表里，将每个处理方法和订阅者封装成Subscription。另外还有subscriptionsByEventType的Map，键为事件类型，值为一个存放Subscription的列表。对每个Subscription根据其事件类型，放入相应的列表中。总之就是封装和存储订阅者的信息。

post方法将传入的事件放到一个队列排队，不断取出第一个事件，根据事件类型，从subscriptionsByEventType中取出列表，反射调用订阅者的处理方法。