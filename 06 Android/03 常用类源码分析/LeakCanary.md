# 只需要依赖就自动开启的原理

LeakCanary有个Provider。

在ContentProvider的onCreate在Application实例创建后，在Application的onCreate之前，所以注册一个ContentProvider可以在其onCreate里拿到程序生命周期的context。

```
object-watcher/object-watcher-android/src/main/AndroidManifest.xml
```

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest
    xmlns:android="http://schemas.android.com/apk/res/android">

  <application>
    <provider
        android:name="leakcanary.internal.MainProcessAppWatcherInstaller"
        android:authorities="${applicationId}.leakcanary-installer"
        android:enabled="@bool/leak_canary_watcher_auto_install"
        android:exported="false"/>
  </application>
</manifest>
```

```kotlin
internal class MainProcessAppWatcherInstaller : ContentProvider() {

  override fun onCreate(): Boolean {
    val application = context!!.applicationContext as Application
    AppWatcher.manualInstall(application)
    return true
  }
  // ...
}    
```

# 检测泄漏

```kotlin
fun manualInstall(
  application: Application,
  retainedDelayMillis: Long = TimeUnit.SECONDS.toMillis(5),
  watchersToInstall: List<InstallableWatcher> = appDefaultWatchers(application)
) {
  checkMainThread()
  // ...
  // Requires AppWatcher.objectWatcher to be set
  LeakCanaryDelegate.loadLeakCanary(application)

  watchersToInstall.forEach {
    it.install()
  }
  // Only install after we're fully done with init.
  installCause = RuntimeException("manualInstall() first called here")
}
```

不需要也不能手动初始化。

## install Watchers

```kotlin
fun appDefaultWatchers(
  application: Application,
  reachabilityWatcher: ReachabilityWatcher = objectWatcher
): List<InstallableWatcher> {
  return listOf(
    ActivityWatcher(application, reachabilityWatcher),
    FragmentAndViewModelWatcher(application, reachabilityWatcher),
    RootViewWatcher(reachabilityWatcher),
    ServiceWatcher(reachabilityWatcher)
  )
}
```

## ActivityWatcher

```kotlin
class ActivityWatcher(
  private val application: Application,
  private val reachabilityWatcher: ReachabilityWatcher
) : InstallableWatcher {

  private val lifecycleCallbacks =
    object : Application.ActivityLifecycleCallbacks by noOpDelegate() {
      override fun onActivityDestroyed(activity: Activity) {
        reachabilityWatcher.expectWeaklyReachable(
          activity, "${activity::class.java.name} received Activity#onDestroy() callback"
        )
      }
    }

  override fun install() {
    application.registerActivityLifecycleCallbacks(lifecycleCallbacks)
  }

  override fun uninstall() {
    application.unregisterActivityLifecycleCallbacks(lifecycleCallbacks)
  }
}
```

对于Activity的观察，用的是ActivityWatcher，通过application注册了一个lifecycleCallbacks，在onActivityDestroyed时，会调用ObjectWatcher的expectWeaklyReachable。

## ObjectWatcher

```kotlin
private val queue = ReferenceQueue<Any>()

@Synchronized override fun expectWeaklyReachable(
  watchedObject: Any,
  description: String
) {
  if (!isEnabled()) {
    return
  }
  removeWeaklyReachableObjects()
  val key = UUID.randomUUID()
    .toString()
  val watchUptimeMillis = clock.uptimeMillis()
  val reference =
    KeyedWeakReference(watchedObject, key, description, watchUptimeMillis, queue)
  SharkLog.d {
    "Watching " +
      (if (watchedObject is Class<*>) watchedObject.toString() else "instance of ${watchedObject.javaClass.name}") +
      (if (description.isNotEmpty()) " ($description)" else "") +
      " with key $key"
  }

  watchedObjects[key] = reference
  checkRetainedExecutor.execute {
    moveToRetained(key)
  }
}
```

KeyedWeakReference继承了WeakReference，是一个弱引用，创建KeyedWeakReference时传入了一个引用队列。checkRetainedExecutor在ObjectWatcher的构造函数中创建。

```kotlin
val objectWatcher = ObjectWatcher(
  clock = { SystemClock.uptimeMillis() },
  checkRetainedExecutor = {
    check(isInstalled) {
      "AppWatcher not installed"
    }
    mainHandler.postDelayed(it, retainedDelayMillis)
  },
  isEnabled = { true }
)
```

## 总结

1.   通过application注册了一个lifecycleCallbacks，在onActivityDestroyed时，利用弱引用+引用队列的方式观察。
2.   5s后，检查对象是否还存在。

# dump heap

dump heap的操作在子线程。

```kotlin
@Synchronized private fun moveToRetained(key: String) {
  removeWeaklyReachableObjects()
  val retainedRef = watchedObjects[key]
  if (retainedRef != null) {
    retainedRef.retainedUptimeMillis = clock.uptimeMillis()
    onObjectRetainedListeners.forEach { it.onObjectRetained() }
  }
}
```

```kotlin
private fun checkRetainedObjects() {
  // 。。。。
  var retainedReferenceCount = objectWatcher.retainedObjectCount

  // objectWatcher持有对象时，先触发一次gc
  if (retainedReferenceCount > 0) {
    gcTrigger.runGc()
    retainedReferenceCount = objectWatcher.retainedObjectCount
  }

  // gc后，如果objectWatcher持有的引用数小于5，则return
  if (checkRetainedCount(retainedReferenceCount, config.retainedVisibleThreshold)) return

  val now = SystemClock.uptimeMillis()
  val elapsedSinceLastDumpMillis = now - lastHeapDumpUptimeMillis
  if (elapsedSinceLastDumpMillis < WAIT_BETWEEN_HEAP_DUMPS_MILLIS) {
    onRetainInstanceListener.onEvent(DumpHappenedRecently)
    showRetainedCountNotification(
      objectCount = retainedReferenceCount,
      contentText = application.getString(R.string.leak_canary_notification_retained_dump_wait)
    )
    scheduleRetainedObjectCheck(
      delayMillis = WAIT_BETWEEN_HEAP_DUMPS_MILLIS - elapsedSinceLastDumpMillis
    )
    return
  }

  dismissRetainedCountNotification()
  val visibility = if (applicationVisible) "visible" else "not visible"
  dumpHeap(
    retainedReferenceCount = retainedReferenceCount,
    retry = true,
    reason = "$retainedReferenceCount retained objects, app is $visibility"
  )
}
```

objectWatcher持有对象时，先触发一次gc

## gc

```kotlin
override fun runGc() {
  // Code taken from AOSP FinalizationTest:
  // https://android.googlesource.com/platform/libcore/+/master/support/src/test/java/libcore/
  // java/lang/ref/FinalizationTester.java
  // System.gc() does not garbage collect every time. Runtime.gc() is
  // more likely to perform a gc.
  Runtime.getRuntime()
    .gc()
  enqueueReferences()
  System.runFinalization()
}
```

## dump

```kotlin
private fun dumpHeap(
  retainedReferenceCount: Int,
  retry: Boolean,
  reason: String
) {
  val directoryProvider =
    InternalLeakCanary.createLeakDirectoryProvider(InternalLeakCanary.application)
  val heapDumpFile = directoryProvider.newHeapDumpFile()

  val durationMillis: Long
  if (currentEventUniqueId == null) {
    currentEventUniqueId = UUID.randomUUID().toString()
  }
  try {
    InternalLeakCanary.sendEvent(DumpingHeap(currentEventUniqueId!!))
    if (heapDumpFile == null) {
      throw RuntimeException("Could not create heap dump file")
    }
    saveResourceIdNamesToMemory()
    val heapDumpUptimeMillis = SystemClock.uptimeMillis()
    KeyedWeakReference.heapDumpUptimeMillis = heapDumpUptimeMillis
    durationMillis = measureDurationMillis {
      configProvider().heapDumper.dumpHeap(heapDumpFile)
    }
    if (heapDumpFile.length() == 0L) {
      throw RuntimeException("Dumped heap file is 0 byte length")
    }
    lastDisplayedRetainedObjectCount = 0
    lastHeapDumpUptimeMillis = SystemClock.uptimeMillis()
    objectWatcher.clearObjectsWatchedBefore(heapDumpUptimeMillis)
    currentEventUniqueId = UUID.randomUUID().toString()
    InternalLeakCanary.sendEvent(HeapDump(currentEventUniqueId!!, heapDumpFile, durationMillis, reason))
  } catch (throwable: Throwable) {
    InternalLeakCanary.sendEvent(HeapDumpFailed(currentEventUniqueId!!, throwable, retry))
    if (retry) {
      scheduleRetainedObjectCheck(
        delayMillis = WAIT_AFTER_DUMP_FAILED_MILLIS
      )
    }
    showRetainedCountNotification(
      objectCount = retainedReferenceCount,
      contentText = application.getString(
        R.string.leak_canary_notification_retained_dump_failed
      )
    )
    return
  }
}
```

主要看这段代码：

```kotlin
configProvider().heapDumper.dumpHeap(heapDumpFile)
```

```kotlin
object AndroidDebugHeapDumper : HeapDumper {
  override fun dumpHeap(heapDumpFile: File) {
    Debug.dumpHprofData(heapDumpFile.absolutePath)
  }
}
```

# 总结

1.   LeakCanary不用手动初始化是通过注册provider。
2.   LeakCanary通过application注册了一个lifecycleCallback，监听Activity的onDestroy
3.   当有Activity onDestroy时，用一个弱引用+引用队列的方式观察。
4.   5s后，触发一次观察。
5.   先通过Runtime.gc的方式，这种方式比System.gc更有可能gc。gc后，检查存活的对象。
6.   通过`Debug.dumpHprofData` dump heap，并分析。