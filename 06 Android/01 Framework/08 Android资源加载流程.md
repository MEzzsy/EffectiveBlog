# 🌟整体流程

**整体流程**

1. 构建时生成资源 ID，通过 `R` 类供代码引用。`resources.arsc` 保存资源值、字符串池、配置及文件路径等；图片、编译后的布局 XML 等作为独立文件打包进 APK。
2. 运行时，通过context获取资源，底层则通过AssetManager。
3. `AssetManager` 根据资源 ID 和当前配置查询资源表，取得资源值或打开对应文件，再由上层完成解析、解码。
4. 对于assets下的资源，则通过AssetManager以文件流的方式读取。

```
Activity / Application（都是 Context）
        ↓ 通常经过包装层委托
ContextImpl
        ↓ getResources() 返回关联对象
Resources ←────── 创建 / 复用 ────── ResourcesManager
        ↓ 持有并调用                       │
ResourcesImpl ←── 创建 / 复用 ─────────────┘
        ↓ 持有并使用
AssetManager
        ↓ 通过 Native 实现
查询 resources.arsc、读取 APK 内的文件
```



**缓存机制**

1. **Drawable 缓存**：主要缓存 `ConstantState`。命中后通过 `newDrawable()` 创建实例，复用底层数据，减少重复解析和解码。缓存还会考虑主题，并在相关配置变化时失效。
   - **没有固定数量上限**，弱引用保存 `ConstantState`。状态被 GC 回收；影响该资源的配置发生变化时清理
2. **XML 缓存**：缓存已加载的二进制 XML 数据块，命中后创建新的解析器。缓存的不是 View 树，每次 inflate 仍需要创建 View。
   - **每个 `ResourcesImpl` 最多 4 个**。新条目循环覆盖旧条目；配置更新时清空

# 构建时：资源如何存进 APK

Android 构建工具通过 AAPT2 编译、链接资源，并生成资源表及供代码引用的资源符号。最终 APK 中，与资源相关的主要内容包括：

| 内容 | 作用 |
| --- | --- |
| `R` 中的资源 ID | 例如 `R.string.app_name`、`R.layout.activity_main`，让代码可以引用资源 |
| `resources.arsc` | 资源表，记录资源条目、不同配置下的值或文件路径，以及字符串池等数据 |
| `res/` 下的文件 | 保存编译后的布局 XML、图片等文件资源 |
| `assets/` 下的文件 | 保存按路径访问的原始文件，不生成 `R` 资源 ID |

- `R.string.app_name` 本质上是整数标识，不是字符串本身，也不是文件路径
- `res/values/strings.xml` 中的字符串会进入资源表相关数据，运行时不需要重新解析源码中的 `strings.xml`
- 布局 XML 则通常编译成二进制 XML，作为文件保存在 APK 中



`resources.arsc` 是**二进制资源表**，保存资源索引及部分资源内容，主要包括：

| 内容               | 示例                                                       |
| ------------------ | ---------------------------------------------------------- |
| **资源标识**       | 包、资源类型、名称，以及资源 ID 对应的条目                 |
| **资源值**         | 字符串、颜色、整数、布尔值、尺寸等；字符串保存在字符串池中 |
| **复杂资源及引用** | style 的属性集合、数组、对其他资源 ID 的引用               |
| **文件路径**       | 图片、布局等资源在 APK 内的路径                            |
| **配置信息**       | 语言、屏幕密度、横竖屏、夜间模式等配置下的不同版本         |

# 同一个 ID 如何适配不同设备

同一个资源可以提供多种配置版本，例如：

```text
res/values/strings.xml        → 默认字符串
res/values-zh/strings.xml     → 中文字符串
res/layout/main.xml          → 默认布局
res/layout-land/main.xml     → 横屏布局
res/drawable-hdpi/icon.png    → hdpi 图片
res/drawable-xhdpi/icon.png   → xhdpi 图片
```

不同配置下同名、同类型的资源使用同一个资源 ID。运行时，系统按照当前 Context 对应的语言、屏幕方向、尺寸、密度、夜间模式等配置，以及限定符匹配规则选择资源。

例如，`getString(R.string.app_name)` 在中文环境下可以返回中文，在其他语言环境下使用默认字符串。图片密度匹配还可能涉及缩放，不能简单理解为“没有完全相同的目录就加载失败”。通常应提供默认资源，避免某些配置下没有可用内容。

# 运行时：谁负责加载资源

应用创建 Context 等运行环境时，Framework 会根据 APK 路径和配置准备资源对象。应用自身的资源可以来自 Base APK 和相关 Split APK，系统资源也会纳入资源访问体系。

| 类 | 主要职责 |
| --- | --- |
| `Context` | 提供 `getResources()`、`getString()` 等访问入口 |
| `ResourcesManager` | 进程内管理资源对象，根据资源路径、显示信息和配置创建或复用对象 |
| `Resources` | 对应用提供 `getString()`、`getLayout()` 等资源 API |
| `ResourcesImpl` | 承担资源加载实现、配置管理及部分缓存，持有 `AssetManager` |
| `AssetManager` | 通过底层实现访问 APK 中的资源表和文件，完成资源查询 |

## TypedValue：承接带类型的资源值

`TypedValue` 是一个**保存“值、类型及来源信息”的容器**，用于承接资源查询或主题属性解析的结果。`AssetManager` 查表后将结果填入它，上层再按类型处理。

| 常见字段 | 作用 |
| --- | --- |
| `type` | 值的类型，例如字符串、整数、颜色、尺寸、资源引用 |
| `data` | 原始数据，含义由 `type` 决定；可以是整数、颜色值、资源引用 ID 或字符串池索引等 |
| `string` | 字符串内容；对于布局、图片等文件资源，通常保存文件路径 |
| `resourceId` | 值来自资源时，对应的资源 ID |
| `assetCookie` | 字符串或文件路径所在资源来源的标识，用于定位对应 APK 等来源 |
| `density` | 资源对应的密度信息，用于后续尺寸换算或图片缩放 |

```kotlin
val value = TypedValue()
context.resources.getValue(R.string.app_name, value, true)
// type = TYPE_STRING，string 是应用名称文本

context.resources.getValue(R.drawable.icon, value, true) // 假设 icon 是 PNG
// type 同样是 TYPE_STRING，string 则是 APK 内的图片路径
```

这里 `true` 表示继续解析资源引用。**`TYPE_STRING` 既可能表示文字，也可能表示文件路径**；查到图片路径后，还需要打开文件并解码，`TypedValue` 本身不保存 Bitmap。上面复用同一个容器，第二次查询会覆盖第一次的结果。

# 字符串加载

```kotlin
val name = context.getString(R.string.app_name)
```

主要过程如下：

1. `Context` 取得对应的 `Resources`，调用 `getString()`。
2. `Resources.getString()` 通过 `getText()`，交给 `AssetManager.getResourceText()` 查询。
3. 底层根据资源 ID 定位资源条目，并结合当前语言等配置选择对应的值；如果是资源引用，还需要继续解析。
4. 从字符串池等数据中取得文本，最终返回 `String`。

因此，资源加载通常是**查资源表并读取对应内容**，并不是每次都遍历 APK 目录寻找同名文件。

```text
Context.getString(id)
 → Resources.getString(id) → getText(id)
 → ResourcesImpl.getAssets() → AssetManager.getResourceText(id)
 → getResourceValue() → nativeGetResourceValue()
 → 按当前配置查表、解析引用 → 从字符串池取得文本
 → 返回 CharSequence → 转成 String
```

源码

```java
// Context.java
public final String getString(int id) {
    return getResources().getString(id);
}

// Resources.java
public String getString(int id) {
    return getText(id).toString();
}

public CharSequence getText(int id) {
    CharSequence text = mResourcesImpl.getAssets().getResourceText(id);
    if (text != null) return text;
    throw new NotFoundException("String resource ID #" + id);
}
```

真正的查表由 `AssetManager` 进入 Native 完成，再由 Java 层取得字符串池中的文本。

```java
// AssetManager.java
CharSequence getResourceText(int id) {
    TypedValue value = mValue; // 实际源码在同步块中复用临时对象
    return getResourceValue(id, 0, value, true)
            ? value.coerceToString() : null;
}

boolean getResourceValue(int id, int density, TypedValue out, boolean resolveRefs) {
    int cookie = nativeGetResourceValue(
            mObject, id, (short) density, out, resolveRefs);
    if (cookie <= 0) return false;

    // TYPE_STRING 的 data 是字符串池索引
    if (out.type == TypedValue.TYPE_STRING) {
        out.string = getPooledStringForCookie(cookie, out.data);
        if (out.string == null) return false;
    }
    return true;
}
```

`getText()` 可以保留样式信息，而 `getString()` 的 `toString()` 返回普通字符串。

# 布局加载

## 加载流程

```kotlin
val view = LayoutInflater.from(context)
    .inflate(R.layout.activity_main, parent, false)
```

资源系统先根据 ID 和配置找到布局文件，并提供 XML 解析器；`LayoutInflater` 再读取节点、创建 View、处理属性并组装 View 树。**找到布局资源与创建界面对象是两个步骤。**

布局中的 `@string/title` 会继续走资源查找；`?attr/...` 则需要结合当前 Context 的 Theme 解析，因此加载页面布局时通常使用对应 Activity 的 Context。

```text
LayoutInflater.inflate(layoutId, parent, attachToRoot)
 → Resources.getLayout(layoutId)
 → ResourcesImpl.getValue() → AssetManager.getResourceValue()
 → 查表得到布局文件路径和 assetCookie
 → ResourcesImpl.loadXmlResourceParser()
     ├── 命中 XmlBlock 缓存 → newParser()
     └── 未命中 → AssetManager.openXmlBlockAsset() → 缓存 → newParser()
 → 回到 LayoutInflater.inflate(parser, ...)
 → 创建根 View → 递归创建子 View → 按 attachToRoot 决定是否挂到 parent
```

## 源码

`getLayout()` 返回的是解析器。下面将 `Resources` 的中间转发方法内联，并只保留有效布局 ID 的分支。

```java
// Resources.java：getLayout() → loadXmlResourceParser(id, "layout")
public XmlResourceParser getLayout(int id) {
    TypedValue value = obtainTempTypedValue();
    try {
        // 内部调用 AssetManager.getResourceValue() 查表、解析引用
        mResourcesImpl.getValue(id, value, true);
        return mResourcesImpl.loadXmlResourceParser(
                value.string.toString(), id, value.assetCookie, "layout");
    } finally {
        releaseTempTypedValue(value);
    }
}
```

`ResourcesImpl` 按“来源 cookie + 文件路径”查 XML 数据块缓存，命中后仍创建新的解析器。下面保留成功分支，将缓存写入过程以注释缩略。

```java
// ResourcesImpl.java
XmlResourceParser loadXmlResourceParser(String file, int id, int cookie, String type) {
    for (int i = 0; i < mCachedXmlBlockFiles.length; i++) {
        if (mCachedXmlBlockCookies[i] == cookie
                && file.equals(mCachedXmlBlockFiles[i])) {
            return mCachedXmlBlocks[i].newParser(id);
        }
    }

    XmlBlock block = mAssets.openXmlBlockAsset(cookie, file);
    // 实际源码：检查 block，将其写入容量为 4 的循环缓存，并关闭被替换的旧块
    return block.newParser(id);
}
```

# Drawable加载

Drawable 是“可以被绘制的内容”的抽象，既可以表示位图，也可以表示矢量图、形状或多种状态的组合，并不一定对应一张图片。

## 🌟小结

**资源 ID → `AssetManager` 查表得到 `TypedValue` → `ResourcesImpl` 检查缓存：**

- **命中**：通过 `ConstantState` 创建 Drawable。
- **未命中**：读取文件，解码图片或解析 XML，按需应用主题、缓存状态，再返回 Drawable。

## 调用入口

```kotlin
val drawable = context.getDrawable(R.drawable.icon)
imageView.setImageDrawable(drawable)
```

以现代 AOSP 的 Framework 实现为例，主要流程如下，省略兼容库和特殊资源分支：

```text
Context.getDrawable(id)
        ↓ 携带当前 Theme
Resources.getDrawable(id, theme)
        ↓
Resources.getDrawableForDensity(id, 0, theme)
        ↓
ResourcesImpl.getValueForDensity() → AssetManager 查询资源表
        ↓ 得到 TypedValue
ResourcesImpl.loadDrawable()
        ├── 命中缓存 → 根据 ConstantState 创建 Drawable
        └── 未命中 → 读取图片或 XML，创建 Drawable
                         ↓
                  按需应用主题、缓存状态并返回
```

这里 density 参数为 `0` 表示使用当前资源配置的密度，不表示忽略密度。

## 先查资源表，确定读取什么

`AssetManager` 根据资源 ID 和当前配置选择资源，将结果写入 `TypedValue`。对于文件资源，关键字段包括：

- `string`：APK 内的文件路径，例如 `res/drawable-xhdpi-v4/icon.png`，实际路径以构建产物为准。
- `assetCookie`：标识资源来自哪个已加载的 APK 等资源来源。
- `density`：选中资源的密度信息，用于后续尺寸换算或缩放。

**资源表负责定位，图片内容仍保存在 APK 的文件条目中。** 

## 再检查缓存，按类型加载

`loadDrawable()` 先检查可用的 Drawable 缓存及系统预加载状态；未命中时，按资源类型处理：

| 资源类型 | 读取方式与结果 |
| --- | --- |
| 普通 PNG、JPEG、静态 WebP | 打开文件并解码，通常得到包装 Bitmap 的 `BitmapDrawable` |
| `.9.png` | 读取位图及拉伸信息，得到 `NinePatchDrawable` |
| `<vector>` XML | 解析路径等属性，创建 `VectorDrawable` |
| `<shape>` XML | 解析圆角、描边、填充等属性，创建 `GradientDrawable` |
| `drawable/` 下的 `<selector>` XML | 解析各状态及对应的子 Drawable，创建 `StateListDrawable` |
| 直接颜色值 | 直接创建 `ColorDrawable`，不需要打开图片文件 |

对于 APK 中的普通图片，现代 AOSP 通过 `AssetManager.openNonAsset()` 打开文件流，再由 `ImageDecoder` 解码。这里使用 `openNonAsset()`，因为目标是 `res/` 中的文件，而不是 `assets/` 下的路径。

对于 XML，框架取得二进制 XML 解析器，通过 `Drawable.createFromXmlForDensity()` 根据标签创建对象；遇到其他资源引用时继续加载。完成后，对支持主题的 Drawable 按需应用当前 Theme。因此，加载 Drawable 并不总会解码 Bitmap，也不是由 `LayoutInflater` 创建这些对象。

## 源码：查表与缓存

`Context.getDrawable(id)` 将当前 Theme 传给 `Resources.getDrawable(id, theme)`，后者进入 `getDrawableForDensity(id, 0, theme)`。这里先查资源表，再按查询结果加载 Drawable；下面内联了 `Resources.loadDrawable()` 的转发。

```java
// Resources.java
public Drawable getDrawableForDensity(int id, int density, Theme theme) {
    TypedValue value = obtainTempTypedValue();
    try {
        // 内部调用 AssetManager.getResourceValue()
        mResourcesImpl.getValueForDensity(id, density, value, true);
        return mResourcesImpl.loadDrawable(this, value, id, density, theme);
    } finally {
        releaseTempTypedValue(value);
    }
}
```

下面的 `loadDrawable()` **只保留默认密度参数（`density == 0`）、非预加载阶段、普通文件 Drawable 的路径**；省略直接颜色值、系统预加载缓存、特殊密度和 DrawableContainer 等分支。

```java
// ResourcesImpl.java：上述限定场景下的缩略逻辑
Drawable loadDrawable(Resources res, TypedValue value, int id, int density,
        Resources.Theme theme) {
    long key = ((long) value.assetCookie << 32) | value.data;
    DrawableCache cache = mDrawableCache;
    int generation = cache.getGeneration();

    // 缓存内部由 ConstantState.newDrawable(res, theme) 创建实例
    Drawable drawable = cache.getInstance(key, res, theme);
    if (drawable != null) return drawable;

    drawable = loadDrawableForCookie(res, value, id, density);
    if (drawable == null) return null;

    boolean usesTheme = drawable.canApplyTheme();
    if (usesTheme && theme != null) {
        drawable = drawable.mutate();
        drawable.applyTheme(theme);
        drawable.clearMutated();
    }
    drawable.setChangingConfigurations(value.changingConfigurations);
    cacheDrawable(value, false, cache, theme, usesTheme, key, drawable, generation);
    return drawable;
}
```

其中 `value.data` 对文件资源通常是路径在字符串池中的索引，因此缓存 key 结合了资源来源与路径索引，主题由缓存内部另行区分。`cacheDrawable()` 保存可用的 `ConstantState`，不是直接缓存这个返回给 View 的 Drawable 实例。

## 源码：打开文件并解码或解析

未命中缓存后，普通 APK 文件资源进入以下两条分支。这里把 `loadXmlDrawable()`、`decodeImageDrawable()` 的关键逻辑内联，省略颜色 XML、特殊资源来源及异常处理。

```java
// ResourcesImpl.java
private Drawable loadDrawableForCookie(Resources res, TypedValue value,
        int id, int density) {
    String file = value.string.toString();

    if (file.endsWith(".xml")) {
        try (XmlResourceParser parser = loadXmlResourceParser(
                file, id, value.assetCookie, "drawable")) {
            // 根据 vector、shape、selector 等标签创建对应 Drawable
            return Drawable.createFromXmlForDensity(res, parser, density, null);
        }
    }

    AssetInputStream stream = (AssetInputStream) mAssets.openNonAsset(
            value.assetCookie, file, AssetManager.ACCESS_STREAMING);
    ImageDecoder.Source source = new ImageDecoder.AssetInputStreamSource(
            stream, res, value);
    return ImageDecoder.decodeDrawable(source, (decoder, info, src) -> {
        decoder.setAllocator(ImageDecoder.ALLOCATOR_SOFTWARE);
    });
}
```

这里先以空 Theme 创建 XML Drawable，未解析的主题属性由上一段 `loadDrawable()` 按需处理；图片流则交由这条解码路径管理关闭。普通静态图片通常得到 `BitmapDrawable`，随后才由 View 在绘制阶段使用它。

## 缓存与最终绘制

Drawable 缓存主要保存 `Drawable.ConstantState`，命中时通过 `newDrawable()` 创建实例，使多个 Drawable 能共享底层位图等数据，减少重复读取和解码。缓存还要考虑主题和配置变化，并不是仅按资源 ID 永久保存。

从同一资源获得的多个 Drawable 可能共享内部状态。如果要单独修改某个实例的 tint 等属性，可以先调用 `mutate()` 隔离可变状态；这不意味着一定复制一整份 Bitmap 像素。

注意：

- 返回的仍是当前 Drawable，**不会创建新的 Drawable 对象**。
- 隔离的是可变状态，底层 Bitmap 像素仍可共享。
- 如果两个 View 使用的是**同一个 Drawable 实例**，`mutate()` 无法将它们分开，需要分别获取实例。

```kotlin
val drawable = context.getDrawable(R.drawable.icon)?.mutate()
drawable?.setTint(Color.RED)
imageView.setImageDrawable(drawable)
```

读取完成得到的是 Drawable 对象。设置到 ImageView 后，界面绘制阶段才会调用其 `draw(Canvas)`，根据边界和状态绘制内容。

# assets：直接按路径打开

```kotlin
val json = context.assets.open("config/settings.json")
    .bufferedReader()
    .use { it.readText() }
```

`assets/` 文件保留路径结构，通过 `AssetManager.open()` 读取，不生成资源 ID，也不参与 `res/` 的限定符自动匹配。`res/raw/` 虽然也可以保存原始文件，但会生成 `R.raw.xxx`，可通过 `Resources.openRawResource()` 按 ID 访问。
