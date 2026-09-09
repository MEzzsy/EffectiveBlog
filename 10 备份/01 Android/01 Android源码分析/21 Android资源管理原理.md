# 前言

我们一般通过 Resources 对象来访问 app 资源文件：

```
context.resources.getString(R.string.test)
```

而在 Application 的 onCreate 中就可以通过 Resources 访问 app 的资源了。因此本文从 Application 的创建方法来梳理资源创建和获取流程。

# 资源管理类的创建

## Application资源的创建

> 具体可以去看应用进程创建的知识点。

一个普通的app进程被 system_server 创建出来后，AMS会回调ActivityThread 的 bindApplication 进行后续工作，bindApplication 中通过 Handler机制把消息交给 handleBindApplication 处理，进Appliction对象的创建等。

```java
private void handleBindApplication(AppBindData data) {
  // ......
  // 创建LoadedApk对象
  data.info = getPackageInfoNoCheck(data.appInfo, data. compatInfo);
  // 创建Application对象
  Application app = data.info.makeApplication(data.restrictedBackupMode, null);
｝
```

### 创建LoadedApk对象

```java
private LoadedApk getPackageInfo(ApplicationInfo aInfo, CompatibilityInfo compatInfo, ClassLoader baseLoader, boolean securityViolation, boolean includeCode, boolean registerPackage) {
  // ...
  synchronized (mResourcesManager) {
    // ...
    LoadedApk packageInfo = ref != null ? ref.get() : null;
    // ...
    packageInfo =
      new LoadedApk(this, aInfo, compatInfo, baseLoader, securityViolation, includeCode && (aInfo.flags & ApplicationInfo.FLAG_HAS_CODE) != 0, registerPackage);
    // ...
    return packageInfo;
  }
}
```

getPackageInfo会创建LoadedApk对象。LoadedApk记录了Activity运行所在的app信息，比如资源信息。

### makeApplication

`LoadedApk#makeApplication`：

```
Application app = r.packageInfo.makeApplication(false, mInstrumentation);
```



```java
public Application makeApplication(boolean forceDefaultAppClass, Instrumentation instrumentation) {
  // ...
  Application app = null;
  // ...
  try {
    // ...
    ContextImpl appContext = ContextImpl.createAppContext(mActivityThread, this);

    // ...
    app = mActivityThread.mInstrumentation.newApplication(
      cl, appClass, appContext);
    appContext.setOuterContext(app);
  } catch (Exception e) {
    // ...
  }
  // ...

  return app;
}
```

makeApplication主要有以下流程：

- ﻿﻿创建application的contextlmpl
- ﻿﻿利用Instrumentation来创建appliction
- 将新创建的Application对象保存到Contextlmpl的成员变量mOuterContext

### createAppContext

```java
static ContextImpl createAppContext(ActivityThread mainThread, LoadedApk packageInfo,
        String opPackageName) {
    if (packageInfo == null) throw new IllegalArgumentException("packageInfo");
    ContextImpl context = new ContextImpl(null, mainThread, packageInfo, null, null, null, null,
            0, null, opPackageName);
    context.setResources(packageInfo.getResources());
    context.mIsSystemOrSystemUiContext = isSystemOrSystemUI(context);
    return context;
}
```

`packageInfo.getResources()`：

```java
public Resources getResources() {
    if (mResources == null) {
        final String[] splitPaths;
        try {
            splitPaths = getSplitPaths(null);
        } catch (NameNotFoundException e) {
            // This should never fail.
            throw new AssertionError("null split not found");
        }

        mResources = ResourcesManager.getInstance().getResources(null, mResDir,
                splitPaths, mOverlayDirs, mApplicationInfo.sharedLibraryFiles,
                Display.DEFAULT_DISPLAY, null, getCompatibilityInfo(),
                getClassLoader(), null);
    }
    return mResources;
}
```

每一个 Apk 都有一个 Resource 对象来描述它包内的资源，而这个 Resource 对象是通过 ResourcesManager 的getResource获取到的。

> 一个应用可能会存在多个 apk，比如说一个主base.apk，然后又动态下载了语言包apk等。

**getResource的逻辑：**

1. 构建ResourcesKey

2.  获取 ResourcesImpl

   - ﻿根据ResourcesKey从缓存中查找Resourceslmpl

   - ﻿反之创建一个Resourceslmpl，创建Resourceslmpl之前会创建AssetManager对象。

3. 通过 Resourceslmpl 构建 Resources 对象

**AssetManager的构建步骤：**

- ﻿﻿通过 loadApkAssets 获取 ApkAssets 对象（内部是通过ApkAssets#loadFromPath方法），用于描述一个 apk 中的资源数据。ApkAssets可能有多个。
- ﻿通过 AssetManager.Builder. build 构建 AssetManager 对象。主要是合并系统 Apk 的资源数据和上面解析的ApkAssets到 apkAssets 数组。

**ApkAssets#loadFromPath：**

通过apk文件寻找`resources.arsc`文件，mmap到内存，然后反序列化。

## 启动Activity

在创建Activity对象时，会创建Activity的ContextImpl，其中会重新创建Resource和AssetManager，并把原来的Asset资源添加到AssetManager中。

## 总结

- Application： Application持有contextlmpl，contextlmpl持有Resource，Resource持有LoadApk Resource。
- Activity：Activity持有自己的Contextlmpl，其中的Resource资源是从LoadApk中复制过来的，并增加了activity一些特有的资源。
- 资源构建：每个contextlmpl都有对应的Resource，Resource由去具体实现类Resourcelmpl进行管理，其持有AssetManager，在native层有对应的AssetManager2。AssetManager2会保存当前系统配置的configuration和进行对各个资源进行管理。

# 资源的查找

## 资源 ID 的构成

资源 ID 是一个 32 位整数，通常由以下几个部分构成：

1. 包 ID（8 位）：
   - 标识资源所属的应用程序包。
   - 系统资源的包 ID 通常是 0x01。
2. 类型 ID（8 位）：
   - 标识资源的类型（如布局、字符串、图片等）。
   - 每种资源类型在一个应用中都有一个唯一的类型 ID。
3. 资源 ID（16 位）：
   - 标识特定类型中的具体资源。
   - 在同一类型中，每个资源都有一个唯一的资源 ID。

## 获取String资源

```
context.resources.getString(R.string.test)
```

代码：

```java
public String getString(@StringRes int id) throws NotFoundException {
        return getText(id).toString();
    }
  
@NonNull public CharSequence getText(@StringRes int id) throws NotFoundException {
        CharSequence res = mResourcesImpl.getAssets().getResourceText(id);
        if (res != null) {
            return res;
        }
        throw new NotFoundException("String resource ID #0x"
                + Integer.toHexString(id));
    }  
```

从AsssetManager中获取string资源：

```java
boolean getResourceValue(@AnyRes int resId, int densityDpi, @NonNull TypedValue outValue,
            boolean resolveRefs) {
        Objects.requireNonNull(outValue, "outValue");
        synchronized (this) {
            ensureValidLocked();
            final int cookie = nativeGetResourceValue(
                    mObject, resId, (short) densityDpi, outValue, resolveRefs);
            // ...
            if (outValue.type == TypedValue.TYPE_STRING) {
                outValue.string = getPooledStringForCookie(cookie, outValue.data);
            }
            return true;
        }
    }
```

1. 调用 nativeGetResourceValue 方法，在 Native 层查找。
2. 若查找到的资源类型为 String 类型，则到对应的 ApkAssets 的 StringPool 中获取具体数据。

## 总结

- ﻿﻿获取 Context 对应的 ResourceImpl。
- 从 ResourceImpl 中获取 AssetManager，调用 AssetManager 中的 getResourceValue。
- getResourceValue根据id在native层遍历所有的资源包，并寻找最佳匹配的config的资源。
- ﻿﻿查找完最佳匹配的资源后，如果是string类型的，先从缓存值中查找，否则在native读取string并缓存到java层。
