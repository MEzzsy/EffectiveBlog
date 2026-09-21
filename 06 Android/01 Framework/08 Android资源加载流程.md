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

`R.string.app_name` 本质上是整数标识，不是字符串本身，也不是文件路径。`res/values/strings.xml` 中的字符串会进入资源表相关数据，运行时不需要重新解析源码中的 `strings.xml`；布局 XML 则通常编译成二进制 XML，作为文件保存在 APK 中。



`resources.arsc` 是**二进制资源表**，保存资源索引及部分资源内容，主要包括：

| 内容               | 示例                                                       |
| ------------------ | ---------------------------------------------------------- |
| **资源标识**       | 包、资源类型、名称，以及资源 ID 对应的条目                 |
| **资源值**         | 字符串、颜色、整数、布尔值、尺寸等；字符串保存在字符串池中 |
| **复杂资源及引用** | style 的属性集合、数组、对其他资源 ID 的引用               |
| **文件路径**       | 图片、布局等资源在 APK 内的路径                            |
| **配置信息**       | 语言、屏幕密度、横竖屏、夜间模式等配置下的不同版本         |

上述结构可见 [AOSP 资源表定义](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/libs/androidfw/include/androidfw/ResourceTypes.h)。

例如：**字符串文本可以直接保存在表中；PNG 图片和布局 XML 的文件内容保存在 APK 的 `res/` 中，表中记录它们的路径。**

# 运行时：谁负责加载资源

应用创建 Context 等运行环境时，Framework 会根据 APK 路径和配置准备资源对象。应用自身的资源可以来自 Base APK 和相关 Split APK，系统资源也会纳入资源访问体系。

| 类 | 主要职责 |
| --- | --- |
| `Context` | 提供 `getResources()`、`getString()` 等访问入口 |
| `ResourcesManager` | 进程内管理资源对象，根据资源路径、显示信息和配置创建或复用对象 |
| `Resources` | 对应用提供 `getString()`、`getLayout()` 等资源 API |
| `ResourcesImpl` | 承担资源加载实现、配置管理及部分缓存，持有 `AssetManager` |
| `AssetManager` | 通过底层实现访问 APK 中的资源表和文件，完成资源查询 |

这张表表示职责分工，并不意味着每个 API 都严格逐层调用。例如字符串读取可以通过 `ResourcesImpl.getAssets()` 取得 `AssetManager`，直接查询文本。`AssetManager` 也不只负责 `assets/`，它同样参与 `res/` 资源的加载。

# 以字符串加载为例

```kotlin
val name = context.getString(R.string.app_name)
```

主要过程如下：

1. `Context` 取得对应的 `Resources`，调用 `getString()`。
2. `Resources.getString()` 通过 `getText()`，交给 `AssetManager.getResourceText()` 查询。
3. 底层根据资源 ID 定位资源条目，并结合当前语言等配置选择对应的值；如果是资源引用，还需要继续解析。
4. 从字符串池等数据中取得文本，最终返回 `String`。

因此，资源加载通常是**查资源表并读取对应内容**，并不是每次都遍历 APK 目录寻找同名文件。

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

# 布局、图片和 assets 的区别

## 布局：读取 XML 后还要创建 View

```kotlin
val view = LayoutInflater.from(context)
    .inflate(R.layout.activity_main, parent, false)
```

资源系统先根据 ID 和配置找到布局文件，并提供 XML 解析器；`LayoutInflater` 再读取节点、创建 View、处理属性并组装 View 树。**找到布局资源与创建界面对象是两个步骤。**

布局中的 `@string/title` 会继续走资源查找；`?attr/...` 则需要结合当前 Context 的 Theme 解析，因此加载页面布局时通常使用对应 Activity 的 Context。

## Drawable：查找资源后解码或解析

Drawable 是“可以被绘制的内容”的抽象，既可以表示位图，也可以表示矢量图、形状或多种状态的组合，并不一定对应一张图片。

### 调用入口

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

### 先查资源表，确定读取什么

`AssetManager` 根据资源 ID 和当前配置选择资源，将结果写入 `TypedValue`。对于文件资源，关键字段包括：

- `string`：APK 内的文件路径，例如 `res/drawable-xhdpi-v4/icon.png`，实际路径以构建产物为准。
- `assetCookie`：标识资源来自哪个已加载的 APK 等资源来源。
- `density`：选中资源的密度信息，用于后续尺寸换算或缩放。

**资源表负责定位，图片内容仍保存在 APK 的文件条目中。** 系统可以直接打开 APK 内的资源，不需要先把图片完整解压到应用私有目录。

### 再检查缓存，按类型加载

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

### 缓存与最终绘制

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

## assets：直接按路径打开

```kotlin
val json = context.assets.open("config/settings.json")
    .bufferedReader()
    .use { it.readText() }
```

`assets/` 文件保留路径结构，通过 `AssetManager.open()` 读取，不生成资源 ID，也不参与 `res/` 的限定符自动匹配。`res/raw/` 虽然也可以保存原始文件，但会生成 `R.raw.xxx`，可通过 `Resources.openRawResource()` 按 ID 访问。
