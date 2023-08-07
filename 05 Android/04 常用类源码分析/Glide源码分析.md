# 参考

[Android图片加载框架最全解析](https://blog.csdn.net/guolin_blog/article/details/53759439)，作者郭霖。

以下源码分析基于Glide tag：`v4.9.0`

# 基本使用

```java
Glide.with(context).load("https://goo.gl/gEgYUd").into(imageView);
```

with一个context，load一个资源，into一个target，一般是imageView，也可以自定义target。

# with

```java
public static RequestManager with(@NonNull Context context) {
  return getRetriever(context).get(context);
}
```

with方法得到一个RequestManager对象。

```java
@NonNull
public RequestManager get(@NonNull Context context) {
  if (context == null) {
    throw new IllegalArgumentException("You cannot start a load on a null Context");
  } else if (Util.isOnMainThread() && !(context instanceof Application)) {
    if (context instanceof FragmentActivity) {
      return get((FragmentActivity) context);
    } else if (context instanceof Activity) {
      return get((Activity) context);
    } else if (context instanceof ContextWrapper) {
      return get(((ContextWrapper) context).getBaseContext());
    }
  }

  return getApplicationManager(context);
}
```

Glide会根据传入with方法的参数来确定图片加载的生命周期。

```java
@NonNull
private RequestManager getApplicationManager(@NonNull Context context) {
  if (applicationManager == null) {
    synchronized (this) {
      if (applicationManager == null) {
        Glide glide = Glide.get(context.getApplicationContext());
        applicationManager =
            factory.build(
                glide,
                new ApplicationLifecycle(),
                new EmptyRequestManagerTreeNode(),
                context.getApplicationContext());
      }
    }
  }

  return applicationManager;
}
```

如果在with方法中传入的是一个Application对象，Glide并不需要做什么特殊的处理，它自动就是和应用程序的生命周期是同步的，如果应用程序关闭的话，Glide的加载也会同时终止。

```java
@NonNull
public RequestManager get(@NonNull Context context) {
  if (context == null) {
    throw new IllegalArgumentException("You cannot start a load on a null Context");
  } else if (Util.isOnMainThread() && !(context instanceof Application)) {
    if (context instanceof FragmentActivity) {
      return get((FragmentActivity) context);
    } else if (context instanceof Activity) {
      return get((Activity) context);
    } else if (context instanceof ContextWrapper) {
      return get(((ContextWrapper) context).getBaseContext());
    }
  }

  return getApplicationManager(context);
}
```

```java
@NonNull
public RequestManager get(@NonNull Activity activity) {
  if (Util.isOnBackgroundThread()) {
    return get(activity.getApplicationContext());
  } else {
    assertNotDestroyed(activity);
    android.app.FragmentManager fm = activity.getFragmentManager();
    return fragmentGet(
        activity, fm, /*parentHint=*/ null, isActivityVisible(activity));
  }
}
```

```java
@Deprecated
@NonNull
private RequestManager fragmentGet(@NonNull Context context,
    @NonNull android.app.FragmentManager fm,
    @Nullable android.app.Fragment parentHint,
    boolean isParentVisible) {
  RequestManagerFragment current = getRequestManagerFragment(fm, parentHint, isParentVisible);
  RequestManager requestManager = current.getRequestManager();
  if (requestManager == null) {
    // TODO(b/27524013): Factor out this Glide.get() call.
    Glide glide = Glide.get(context);
    requestManager =
        factory.build(
            glide, current.getGlideLifecycle(), current.getRequestManagerTreeNode(), context);
    current.setRequestManager(requestManager);
  }
  return requestManager;
}
```

```java
@NonNull
private RequestManagerFragment getRequestManagerFragment(
    @NonNull final android.app.FragmentManager fm,
    @Nullable android.app.Fragment parentHint,
    boolean isParentVisible) {
  RequestManagerFragment current = (RequestManagerFragment) fm.findFragmentByTag(FRAGMENT_TAG);
  if (current == null) {
    current = pendingRequestManagerFragments.get(fm);
    if (current == null) {
      current = new RequestManagerFragment();
      current.setParentFragmentHint(parentHint);
      if (isParentVisible) {
        current.getGlideLifecycle().onStart();
      }
      pendingRequestManagerFragments.put(fm, current);
      fm.beginTransaction().add(current, FRAGMENT_TAG).commitAllowingStateLoss();
      handler.obtainMessage(ID_REMOVE_FRAGMENT_MANAGER, fm).sendToTarget();
    }
  }
  return current;
}
```

如果传入非Application参数。不管传入的是什么，都会向当前的Activity当中添加一个隐藏的Fragment。因为Glide需要知道加载的生命周期。如果在某个Activity上正在加载着一张图片，结果图片还没加载出来，Activity就被用户关掉了，那么图片就应该停止加载。通过添加隐藏Fragment的这种小技巧，Glide可以监听Activity的生命周期。

## 小结

with就是为了得到一个RequestManager对象，并根据传入的参数来确定图片加载的生命周期。

# load

load方法就是封装了传入的参数，并没有做实际的加载。返回的是一个`RequestBuilder<Drawable>`对象。

# into

into方法先是创建了一个Request对象。Request是用来发出加载图片请求的。

如果在load传入的参数有误，比如：Url为null，就显示错误占位图。

然后根据缓存策略进行加载，在子线程中加载，然后回调到主线程。

简单理一下into的流程：

```
RequestBuilder#into
RequestManager#track
SingleRequest#begin
SingleRequest#onSizeReady
Engine#load
```

# 缓存机制

主要看Engine类的load方法。

```java
public synchronized <R> LoadStatus load(
    GlideContext glideContext,
    Object model,
    Key signature,
    int width,
    int height,
    Class<?> resourceClass,
    Class<R> transcodeClass,
    Priority priority,
    DiskCacheStrategy diskCacheStrategy,
    Map<Class<?>, Transformation<?>> transformations,
    boolean isTransformationRequired,
    boolean isScaleOnlyOrNoTransform,
    Options options,
    boolean isMemoryCacheable,
    boolean useUnlimitedSourceExecutorPool,
    boolean useAnimationPool,
    boolean onlyRetrieveFromCache,
    ResourceCallback cb,
    Executor callbackExecutor) {
  long startTime = VERBOSE_IS_LOGGABLE ? LogTime.getLogTime() : 0;

  EngineKey key = keyFactory.buildKey(model, signature, width, height, transformations,
      resourceClass, transcodeClass, options);

  EngineResource<?> active = loadFromActiveResources(key, isMemoryCacheable);
  if (active != null) {
    cb.onResourceReady(active, DataSource.MEMORY_CACHE);
    if (VERBOSE_IS_LOGGABLE) {
      logWithTimeAndKey("Loaded resource from active resources", startTime, key);
    }
    return null;
  }

  EngineResource<?> cached = loadFromCache(key, isMemoryCacheable);
  if (cached != null) {
    cb.onResourceReady(cached, DataSource.MEMORY_CACHE);
    if (VERBOSE_IS_LOGGABLE) {
      logWithTimeAndKey("Loaded resource from cache", startTime, key);
    }
    return null;
  }

  EngineJob<?> current = jobs.get(key, onlyRetrieveFromCache);
  if (current != null) {
    current.addCallback(cb, callbackExecutor);
    if (VERBOSE_IS_LOGGABLE) {
      logWithTimeAndKey("Added to existing load", startTime, key);
    }
    return new LoadStatus(cb, current);
  }

  EngineJob<R> engineJob =
      engineJobFactory.build(
          key,
          isMemoryCacheable,
          useUnlimitedSourceExecutorPool,
          useAnimationPool,
          onlyRetrieveFromCache);

  DecodeJob<R> decodeJob =
      decodeJobFactory.build(
          glideContext,
          model,
          key,
          signature,
          width,
          height,
          resourceClass,
          transcodeClass,
          priority,
          diskCacheStrategy,
          transformations,
          isTransformationRequired,
          isScaleOnlyOrNoTransform,
          onlyRetrieveFromCache,
          options,
          engineJob);

  jobs.put(key, engineJob);

  engineJob.addCallback(cb, callbackExecutor);
  engineJob.start(decodeJob);

  if (VERBOSE_IS_LOGGABLE) {
    logWithTimeAndKey("Started new load", startTime, key);
  }
  return new LoadStatus(cb, engineJob);
}
```

主要分为这么几步：

1. buildKey
2. loadFromActiveResources
3. loadFromCache
4. start decodeJob

## buildKey

```java
EngineKey key = keyFactory.buildKey(model, signature, width, height, transformations, resourceClass, transcodeClass, options);
```

决定缓存Key的条件非常多，即使用override方法改变了一下图片的width或者height，也会生成一个完全不同的缓存Key。

## 加载内存缓存

### loadFromActiveResources

```java
@Nullable
private EngineResource<?> loadFromActiveResources(Key key, boolean isMemoryCacheable) {
  if (!isMemoryCacheable) {
    return null;
  }
  EngineResource<?> active = activeResources.get(key);
  if (active != null) {
    active.acquire();
  }

  return active;
}
```

```java
@Nullable
synchronized EngineResource<?> get(Key key) {
  ResourceWeakReference activeRef = activeEngineResources.get(key);
  if (activeRef == null) {
    return null;
  }

  EngineResource<?> active = activeRef.get();
  if (active == null) {
    cleanupActiveReference(activeRef);
  }
  return active;
}
```

```java
final Map<Key, ResourceWeakReference> activeEngineResources = new HashMap<>();
```

默认情况下，Glide是开启内存缓存的。

在Engine的load方法中，获取到key之后，先调用loadFromActiveResources方法，而这个方法是从弱引用中获取缓存。

如果获取到缓存，那么调用acquire增加引用计数。

### loadFromCache

```java
private EngineResource<?> loadFromCache(Key key, boolean isMemoryCacheable) {
  if (!isMemoryCacheable) {
    return null;
  }

  EngineResource<?> cached = getEngineResourceFromCache(key);
  if (cached != null) {
    cached.acquire();
    activeResources.activate(key, cached);
  }
  return cached;
}
```

```java
private EngineResource<?> getEngineResourceFromCache(Key key) {
  Resource<?> cached = cache.remove(key);

  final EngineResource<?> result;
  if (cached == null) {
    result = null;
  } else if (cached instanceof EngineResource) {
    // Save an object allocation if we've cached an EngineResource (the typical case).
    result = (EngineResource<?>) cached;
  } else {
    result = new EngineResource<>(cached, true /*isMemoryCacheable*/, true /*isRecyclable*/);
  }
  return result;
}
```

如果在弱引用缓存中没有获取到，那么再从LruCache中获取。LruCache算法（Least Recently Used），也叫近期最少使用算法。它的主要算法原理就是把最近使用的对象用强引用存储在LinkedHashMap中，并且把最近最少使用的对象在缓存值达到预设定值之前从内存中移除。

如果从Lru缓存拿到了数据，那么再放入弱引用缓存。

### 小结

Glide先从弱引用中获取。如果没有拿到弱引用缓存就从LruCache中获取。如果拿到了Lru缓存，那么从Lru缓存中移除并重新放入到弱引用缓存中。

这个弱引用策略是利用一个Map，值是弱引用。

## 缓存引用计数

EngineResource用一个acquired变量用来记录图片被引用的次数，调用acquire()方法会让变量加1，调用release()方法会让变量减1，当acquired变量大于0的时候，说明图片正在使用中，也就应该放到activeResources弱引用缓存当中。而经过release()之后，如果acquired变量等于0了，说明图片已经不再被使用了。然后将它put到LruResourceCache当中。这样也就实现了正在使用中的图片使用弱引用来进行缓存，不在使用中的图片使用LruCache来进行缓存的功能。

>   acquired调用很容易找到，就是在获取图片的时候。而release的调用比较难找，这里参考了[Glide如何通过引用计数复用Bitmap](https://www.jianshu.com/p/00540c9a4de9)。
>
>   调用栈：
>
>   ```
>   1.AcitivityFragmentLifecycle#onDestory//在Activity onDestory
>   2.RequestManager#onDestroy -> clear -> untrackOrDelegate
>   3.Glide#removeFromManagers
>   4.RequestManager#untrack
>   5.RequestTracker#clearRemoveAndRecycle
>   6.SingleRequest#clear releaseResource
>   7.Engine#release
>   8.EngineResource#release：当引用计数为0时，触发listener.onResourceReleased(key, this)
>   9.ResourceListener#onResourceReleased
>   10.Engine#onResourceReleased：如果Recourse能被缓存，则加入MemeoryCache，否则释放资源。
>   11.ResourceRecycler#recycle
>   12.BitmapResource#recycle：（将Bitmap放入回收池）
>   ```
>

除了applicationManager管理的请求，所有的请求都会随着页面的Destroy调用一次`EngineResource#release`，从而能确保被回收的资源不被任何页面使用。这里看到放入MemoryCache的资源，都是页面不再使用的资源。页面从MemoryCache获取缓存的同时，会将Resouce从MemoryCache中删除。

## 加载硬盘缓存

```java
Glide.with(this)
     .load(url)
     .diskCacheStrategy(DiskCacheStrategy.NONE)//禁止Glide对图片进行硬盘缓存
     .into(imageView);
```

这个diskCacheStrategy()方法基本上就是Glide硬盘缓存功能的一切，它可以接收四种参数：

- `DiskCacheStrategy.NONE`： 表示不缓存任何内容。
- `DiskCacheStrategy.SOURCE`： 表示只缓存原始图片。
- `DiskCacheStrategy.RESULT`： 表示只缓存转换过后的图片（默认选项）。
- `DiskCacheStrategy.ALL` ： 表示既缓存原始图片，也缓存转换过后的图片。

当使用Glide去加载一张图片的时候，Glide默认并不会将原始图片展示出来，而是会对图片进行压缩和转换。而Glide默认情况下在硬盘缓存的就是转换过后的图片（`DiskCacheStrategy.RESULT`），通过调用diskCacheStrategy()方法则可以改变这一默认行为。

和内存缓存类似，硬盘缓存的实现也是使用的LruCache算法，而且Google还提供了一个现成的工具类DiskLruCache。当然Glide是使用的自己编写的DiskLruCache工具类，但是基本的实现原理都是差不多的。

大致流程：

```
Engine#load
EngineJob#start
DecodeJob#run
DecodeJob#runWrapped
DecodeJob#decodeFromRetrievedData
```



### 读取缓存

当内存缓存中获取不到图片的时候，会开启线程，尝试从硬盘中获取缓存。

### 放入缓存

在没有缓存的情况下，会读取图片数据，再进行转换，最后放入缓存。

# 总结

Glide的源码分析主要针对它的缓存策略。

1.   Glide根据传入的Context来决定图片的生命周期，Glide是添加一个隐形的Fragment来监听Activity的生命周期。
2.   Glide先从弱引用中获取缓存。
3.   如果没有拿到弱引用缓存就从LruCache中获取。如果拿到了Lru缓存，那么从Lru缓存中移除并重新放入到弱引用缓存中。

放入的时候先放入弱引用，当不使用时，再放入LruCache里。
这里Glide利用引用计数法来判断弱引用是否需要放入LruCache中，使用的时候加1，释放的时候减1，释放是根据Activity的生命周期来判断的，上面也说过了，Glide利用一个隐形的Fragment来监听Activity的生命周期，当监听到onDestory的时候就释放。



当内存缓存中获取不到图片的时候，会开启线程，尝试从硬盘中获取缓存。

在没有缓存的情况下，会读取图片数据，再进行转换，最后放入缓存。