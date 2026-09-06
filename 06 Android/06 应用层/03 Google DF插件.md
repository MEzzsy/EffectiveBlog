本文聚焦 Android Gradle Plugin 提供的 `com.android.dynamic-feature` 插件，以及与它配套的 Google Play Feature Delivery。示例使用 Kotlin DSL；Groovy DSL 的配置含义相同。

> 文档核对日期：2026-08-29。Play Feature Delivery、Android Gradle Plugin 和 Play Console 的规则会继续演进，落地前应再次检查文中官方资料。

# Android 编译产物基础

详见 [Android 编译产物基础](<02 Android编译产物基础.md>)。

# 🌟🌟🌟总结

DF 是 Android 的动态功能模块，可以随base一起安装也可以在运行时安装。

运行时安装依赖google play的能力，流程主要分为三部分。第一个是静态构建，与基础模块一起打包进同一个 AAB；第二个是运行时安装，通过service向google play提交安装请求以及通过broadcast接收状态；第三个就是运行时加载，下载并校验完成后，将 split APK 转为`DexPathList.Element`，再通过反射追加到 ClassLoader 的 `pathList.dexElements` 中，让后续类查找能够找到 DF 的代码；同时把资源路径加入对应 Context 的 `AssetManager`。模块可用后，再通知业务安装完成。

# DF 基础

## `com.android.dynamic-feature` 是什么

`com.android.dynamic-feature` 是 Android Gradle Plugin（AGP）提供的插件，用于将 Gradle 模块声明为动态功能模块（Dynamic Feature Module）。它将模块的代码、资源和 Manifest 与基础应用打入同一个 AAB，并生成安装时、按需或条件交付的元数据，供 Google Play 按规则和设备配置生成、下发 APK。

## DF特点

Dynamic Feature 不是传统意义上的插件化框架，也不是热修复方案：

- 动态模块必须随基础应用放在同一个 AAB 中发布，不能从任意服务器下载未发布的可执行代码；
- 模块与基础应用共享应用身份、签名和版本生命周期，不能独立更新；
- 它依赖 Google Play 的交付能力，其他应用商店不一定提供等价支持。

# 工作原理

## 基础模块与动态功能模块

依赖方向有一个看似反常但很重要的规则：动态功能模块依赖基础模块。

```text
:feature:checkout ─────implementation────▶ :app
        │                                      │
        │ 可以直接使用基础模块代码和资源        │ 不能静态引用尚未安装的功能实现
        └──────────────────────────────────────┘
```

基础模块通过 `android.dynamicFeatures` 告诉构建系统“哪些模块属于这个 AAB”，但业务代码不能直接 `import` 动态功能中的类。否则，基础 APK 在功能尚未下载时就可能引用不存在的类。

推荐把跨模块协议放在基础模块或独立的普通 Library 中：

```kotlin
// 位于基础模块或稳定的 API Library 中
interface CheckoutEntry {
    fun open(context: Context)
}
```

动态功能模块实现协议，基础模块在确认安装完成后，通过显式 Activity 类名、反射、路由表或依赖注入入口找到实现。无论采用哪种方式，都应将“是否已安装”作为调用功能前的必要条件。

## 模块名与 split 名称

构建时，AGP 会使用 Gradle 子项目路径的最后一段生成 Manifest 的 `split` 属性。例如：

```kotlin
include(":app")
include(":feature:checkout")
```

对应的模块名通常是 `checkout`。运行时请求安装时也必须使用这个名字：

```kotlin
SplitInstallRequest.newBuilder()
    .addModule("checkout")
    .build()
```

不要手工在源 Manifest 中设置 `manifest@split` 或 `android:isFeatureSplit`，这些属性应由构建系统注入。重命名 Gradle 模块可能改变 split 名称，因此模块名应该被视为发布协议的一部分，并集中定义为常量。

## 🌟从构建到运行的完整流程

1. AGP 编译各模块代码，生成构建 AAB 所需的模块产物。
2. `:app:bundleRelease` 将所有模块打入同一个 AAB。
3. Google Play 读取每个动态模块的 `dist:module` 和 `dist:delivery` 配置。
4. Google Play 根据设备 ABI、屏幕密度、语言以及功能交付条件生成并选择 split APK。
5. 安装时模块随应用首次安装；按需模块暂不下发。
6. 用户触发按需功能时，基础应用通过 `SplitInstallManager` 请求模块。
7. Play Store 下载并验证 feature split，系统或 SplitCompat 使新代码和资源对应用可见。
8. 之后上传新版本 AAB 时，Google Play 会随应用版本更新已经安装的动态模块。

# 工程配置

## 🌟整体介绍

首先在 `settings.gradle` 中引入 Dynamic Feature 模块，并在基础 `app` 模块的 `dynamicFeatures` 中注册它。Dynamic Feature 模块应用 `com.android.dynamic-feature` 插件，并通过 `implementation project(":app")` 依赖基础模块。最后在该模块的 `AndroidManifest.xml` 中使用 `<dist:module>` 配置模块标题、`install-time` 或 `on-demand` 等交付方式，以及 `fusing` 策略。

## 注册模块

在 `settings.gradle.kts` 中包含基础模块和动态功能模块：

```kotlin
include(":app")
include(":feature:checkout")
```

## 配置基础应用模块

基础模块通过 `dynamicFeatures` 注册需要打入 AAB 的动态模块，并添加 Play Feature Delivery 运行库：

```kotlin
// app/build.gradle.kts
android {
    dynamicFeatures += setOf(":feature:checkout")
}

dependencies {
    implementation("com.google.android.play:feature-delivery:2.1.0")
}
```

## 配置动态功能模块

```kotlin
// feature/checkout/build.gradle.kts
plugins {
    id("com.android.dynamic-feature")
}

android {
    namespace = "com.example.shop.feature.checkout"
}

dependencies {
    implementation(project(":app"))
}
```

## 🌟配置动态模块 Manifest

动态模块的 `AndroidManifest.xml` 决定功能如何交付。下面是按需交付的最小示例：

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:dist="http://schemas.android.com/apk/distribution">

    <dist:module dist:title="@string/feature_checkout_title">
        <dist:delivery>
            <dist:on-demand />
<!--            <dist:install-time />-->          
        </dist:delivery>
        <dist:fusing dist:include="true" />
    </dist:module>

    <application>
        <activity
            android:name=".CheckoutActivity"
            android:exported="false" />
    </application>
</manifest>
```

其中：

- `<dist:on-demand />` 表示首次安装不下发，应用运行时再请求；
- `<dist:install-time />` 指“安装时交付”：用户首次安装应用时，功能模块就随基础应用一起安装，无需再调用 `SplitInstallManager.startInstall()` 下载。
- `dist:title` 引用的字符串必须定义在基础模块中，以便模块尚未安装时由 Google Play 展示；
- `<dist:fusing dist:include="true" />` 表示 API 20 及以下设备在安装时获得该功能；设为 `false` 时旧设备无法使用。API 21 及以上仍按 `<dist:delivery>` 交付；
- `split` 和 `android:isFeatureSplit` 由构建系统生成，不要手工填写。

核心规则如下：

- `com.android.dynamic-feature` 与其他 Android 插件使用同一个 AGP 版本；
- 动态模块依赖基础模块，基础模块业务代码不能静态引用尚未安装的动态模块实现；
- `compileSdk`、`minSdk`、build type 和 product flavor 应与基础模块匹配；
- `applicationId`、版本号、签名和是否启用代码压缩由基础模块统一配置。

### install-time和普通library的区别

两者都可以随应用首次安装就可用，但 Library 是代码依赖模块，install-time DF 是具有交付配置的功能模块。

| 对比                    | 普通 Android Library               | install-time DF                                   |
| ----------------------- | ---------------------------------- | ------------------------------------------------- |
| Gradle 插件             | `com.android.library`              | `com.android.dynamic-feature`                     |
| 编译依赖方向            | Base → Library                     | DF → Base                                         |
| Base 能否直接引用实现类 | 可以                               | 不能直接静态引用                                  |
| 构建产物                | 可生成 AAR，内容合并进使用它的模块 | 在 AAB 中作为功能模块保存                         |
| 最终 APK                | 不保留独立的 Library 安装单元      | 默认不可移除时融合进 Base；可移除时保留独立 split |
| 单独卸载功能            | 不支持                             | 设置 `removable=true` 后支持                      |
| 后续改成按需交付        | 需要改造成 DF                      | 可调整交付配置，但仍需实现下载和状态管理          |

**即使 install-time DF 最终融合进 Base APK，编译依赖方向也不会改变。** Base 仍不能因此直接 `import` DF 的实现类。

如果只是拆分代码、复用功能，通常选择 **Library**；如果需要功能卸载，或准备逐步迁移到按需交付，可以选择 **install-time DF**。[安装时交付说明](https://developer.android.com/guide/playcore/feature-delivery/install-time)

```xml
<dist:delivery>
	<dist:install-time>
		<dist:removable dist:value="true" />
	</dist:install-time>
</dist:delivery>
```

## 配置条件

条件交付表示只给满足条件的设备在安装时下发模块。支持的条件包括设备软硬件特征、国家或地区、API 级别，以及通过设备定位配置描述的型号、RAM、系统特性和 SoC 等属性。

例如，只在支持 AR 且 API 级别满足要求的设备上安装：

```xml
<dist:delivery>
    <dist:install-time>
        <dist:conditions>
            <dist:device-feature
                dist:name="android.hardware.camera.ar" />
            <dist:min-sdk dist:value="24" />
        </dist:conditions>
    </dist:install-time>
</dist:delivery>
```

多个条件同时存在时，设备必须满足全部条件，模块才会在安装时下发。

按 Play 账户对应的用户国家或地区筛选：

```xml
<dist:conditions>
    <dist:user-countries dist:exclude="false">
        <dist:country dist:code="US" />
        <dist:country dist:code="CA" />
    </dist:user-countries>
</dist:conditions>
```

这里的国家通常由 Google Play 账户的账单地址确定，不等同于当前 IP、SIM 卡国家或系统语言。

设备不满足安装时条件时，默认仍可在之后按需请求。需要明确保留按需入口时，可按官方条件交付格式同时声明：

```xml
<dist:delivery>
    <dist:on-demand />
    <dist:install-time>
        <dist:conditions>
            <dist:device-feature
                dist:name="android.hardware.camera.ar" />
        </dist:conditions>
    </dist:install-time>
</dist:delivery>
```

条件交付不应该替代运行时能力检查。即使 Play 已按条件下发模块，使用相机、蓝牙、传感器或新 API 前仍应再次检查硬件、系统版本和权限。

### on-demand、install-time、fuse共存关系

所以dist:on-demand、dist:install-time、dist:fuse可以共存。

- **`fusing`** 可以与 `on-demand` 或 `install-time` 配合，控制模块是否纳入旧设备的单 APK，以及 Universal APK。
- **无条件的 `install-time`** 通常与 `on-demand` 二选一。
- **带条件的 `install-time`** 可以和 `on-demand` 同时声明：满足条件时首次安装交付，否则允许之后按需请求。

## 纯资源模块

如果动态功能模块不产生任何 DEX，只包含资源或资产，需要在该模块 Manifest 中声明：

```xml
<application android:hasCode="false" />
```

同时确保基础模块的 `<application>` 最终保持 `android:hasCode="true"`。若 Manifest 合并发生冲突，可以在基础模块使用 `tools:replace="android:hasCode"` 显式覆盖。

# 运行时安装与状态管理

> 本节直接对应 AndroidDemo 中的实现，核心代码位于基础模块的 `TestDynamicFeatureActivity`、`MyApplication`，以及动态模块的 `MainDynamicFeatureActivity`。

## 🌟整体流程

1. 启用 SplitCompat：继承SplitCompatApplication或者SplitCompat.install(this)
2. 创建安装管理器并请求安装
3. 监听安装状态

> 代码原理见下

## 启用 SplitCompat

AndroidDemo 的 `MyApplication` 直接继承 `SplitCompatApplication`，让运行时能够加载后续安装的 split：

```java
public class MyApplication extends SplitCompatApplication {
    // 原有初始化逻辑保持不变
}
```

或者

```kotlin
class MyApplication : Application() {
    override fun attachBaseContext(base: Context) {
        super.attachBaseContext(base)
        SplitCompat.install(this)
    }
}
```

动态模块入口还在 `attachBaseContext()` 中调用 `SplitCompat.installActivity()`，确保该 Activity 能访问动态模块中的代码和资源：

```kotlin
class MainDynamicFeatureActivity : BaseLinearLayoutActivity() {
    override fun attachBaseContext(newBase: Context) {
        super.attachBaseContext(newBase)
        SplitCompat.installActivity(this)
    }
}
```

## 创建安装管理器

`TestDynamicFeatureActivity` 使用模块名、动态页面完整类名和会话 ID 管理安装过程：

```kotlin
private const val MODULE_NAME = "dynamicfeature"
private const val FEATURE_ACTIVITY_NAME =
    "com.mezzsy.dynamicfeature.MainDynamicFeatureActivity"
private const val KEY_SESSION_ID = "session_id"

private lateinit var splitInstallManager: SplitInstallManager
private var currentSessionId = 0

override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    splitInstallManager = SplitInstallManagerFactory.create(applicationContext)
    currentSessionId = savedInstanceState?.getInt(KEY_SESSION_ID) ?: 0
}
```

`MODULE_NAME` 必须与动态模块的 split 名一致；`currentSessionId` 用于查询、恢复或取消当前安装任务。

## 请求立即安装

点击 Demo 的“立即下载模块”后，会先检查模块是否已经安装，再创建请求：

```kotlin
private fun requestInstall() {
    if (isModuleInstalled()) {
        appendLog("模块已安装，不重复发起下载")
        return
    }

    val request = SplitInstallRequest.newBuilder()
        .addModule(MODULE_NAME)
        .build()

    splitInstallManager.startInstall(request)
        .addOnSuccessListener { sessionId ->
            currentSessionId = sessionId
            appendLog("请求已受理，sessionId=$sessionId")
        }
        .addOnFailureListener(::showTaskFailure)
}
```

`startInstall()` 成功只表示 Play Core 接受了请求，模块是否真正可用要以监听器收到 `INSTALLED` 为准。

## 监听安装状态

Activity 实现 `SplitInstallStateUpdatedListener`，在可见期间注册监听器：

```kotlin
override fun onStart() {
    super.onStart()
    splitInstallManager.registerListener(this)
    restoreActiveSession()
    refreshModuleState()
}

override fun onStop() {
    splitInstallManager.unregisterListener(this)
    super.onStop()
}

override fun onStateUpdate(state: SplitInstallSessionState) {
    if (MODULE_NAME !in state.moduleNames()) return

    currentSessionId = state.sessionId()
    runOnUiThread { renderState(state) }
}
```

`renderState()` 根据状态更新日志和会话数据：

| 状态 | Demo 中的处理 |
| --- | --- |
| `PENDING` | 提示等待下载 |
| `DOWNLOADING` | 用已下载字节数和总字节数计算进度 |
| `DOWNLOADED` / `INSTALLING` | 提示下载完成或正在安装 |
| `REQUIRES_USER_CONFIRMATION` | 调起 Play Core 的用户确认框 |
| `INSTALLED` | 清空会话 ID，并刷新 `installedModules` |
| `FAILED` / `CANCELED` | 输出错误或取消信息，并清空会话 ID |

需要用户确认时，Demo 会避免对同一会话重复弹窗：

```kotlin
private fun requestUserConfirmation(state: SplitInstallSessionState) {
    if (confirmationSessionId == state.sessionId()) return

    val started = splitInstallManager.startConfirmationDialogForResult(
        state,
        this,
        REQUEST_CONFIRMATION,
    )
    if (started) confirmationSessionId = state.sessionId()
}
```

确认结果通过 `onActivityResult()` 返回；用户同意后，安装流程继续，最终仍以状态监听结果为准。

## 恢复安装会话

下载可能跨越 Activity 重建或前后台切换。Demo 一方面保存 `currentSessionId`，另一方面在 `onStart()` 查询所有会话，恢复属于目标模块且尚未结束的任务：

```kotlin
override fun onSaveInstanceState(outState: Bundle) {
    outState.putInt(KEY_SESSION_ID, currentSessionId)
    super.onSaveInstanceState(outState)
}

private fun restoreActiveSession() {
    splitInstallManager.sessionStates
        .addOnSuccessListener { states ->
            states.firstOrNull { state ->
                MODULE_NAME in state.moduleNames() &&
                    !isTerminalStatus(state.status())
            }?.let { state ->
                currentSessionId = state.sessionId()
                renderState(state)
            }
        }
        .addOnFailureListener(::showTaskFailure)
}
```

只保存 session ID 不够，因为进程或页面离开期间状态可能已经变化；重新读取 `sessionStates` 才能获得当前真实状态。

## 打开动态页面

基础模块不能直接引用动态模块中的 Activity 类。Demo 先检查 `installedModules`，再通过完整类名启动页面：

```kotlin
private fun openFeature() {
    if (!isModuleInstalled()) {
        appendLog("模块尚未安装，请先下载")
        return
    }

    val intent = Intent().setClassName(this, FEATURE_ACTIVITY_NAME)
    startActivity(intent)
}

private fun isModuleInstalled(): Boolean =
    MODULE_NAME in splitInstallManager.installedModules
```

## 预加载、取消和卸载

Demo 将三个操作分别映射到 Play Core API：

```kotlin
// 后台预加载：best-effort，无法监听精确进度
splitInstallManager.deferredInstall(listOf(MODULE_NAME))

// 取消当前即时安装会话
splitInstallManager.cancelInstall(currentSessionId)

// 请求系统在后台卸载模块
splitInstallManager.deferredUninstall(listOf(MODULE_NAME))
```

`deferredInstall()` 和 `deferredUninstall()` 都是延迟请求：调用成功仅表示请求已提交，不表示操作已经完成。取消安装则必须持有有效的 `sessionId`。

# 代码、资源与组件访问

## 代码访问规则

略

## 资源访问规则

动态模块自己的代码可以正常使用自己的 `R`。跨模块访问时需要注意：

- 基础模块编译时没有动态模块的资源 ID，不能直接引用动态模块的 `R`；
- 安装后跨模块按名称查找资源时，使用资源定义所在模块的 package/namespace；
- 刚安装完模块后，旧 Activity 的 `Resources` 可能尚未刷新；
- 跨模块读取新资源应优先使用 application context，或重建 Activity、重新安装 SplitCompat；
- 通知、小组件等系统 UI 需要立即读取的资源应该留在基础模块。

按名称访问资源的示例：

```kotlin
val resources = applicationContext.resources
val id = resources.getIdentifier(
    "checkout_banner",
    "drawable",
    "com.example.shop.feature.checkout"
)

if (id != 0) {
    imageView.setImageResource(id)
}
```

按名称查找缺少编译期检查，因此仅用于明确的跨模块边界。功能自己的 UI 应尽量让动态模块内部直接使用类型安全的资源引用。

## 原生库

动态模块可以包含 `.so`，但按需安装后直接 `System.loadLibrary()` 可能遇到库路径或依赖库加载顺序问题。Android 官方文档建议在按需模块场景使用 ReLinker，并在原生库互相依赖时显式保证依赖加载顺序。

如果动态模块的主要内容是大型纹理、音频、视频或游戏资源，而不是 Android 组件和 DEX 代码，应该同时评估 Play Asset Delivery；它对大型资产的交付模型更合适。

# 构建、测试与发布

## 启用 Dynamic Feature 模块

```properties
module.dynamicfeature.enabled=true
```

## 构建 AAB

使用 `--bundle` 构建包含 Dynamic Feature 的 Debug AAB

## 本地测试按需安装

工程提供了 `install-dynamic-feature.sh`，用于构建并安装 `bundletool --local-testing` 测试版本：

```shell
./install-dynamic-feature.sh
```

脚本会依次完成：

1. 调用 `./run.sh --bundle` 构建 AAB；
2. 使用 `bundletool build-apks --local-testing` 生成 APK Set；
3. 使用 `bundletool install-apks` 安装基础 APK，并把 Dynamic Feature APK 放入设备的本地测试目录。

本地 APK Set 输出位置为：

```text
app/build/outputs/bundle/debug/app-debug-local-testing.apks
```

脚本会优先使用系统中的 `bundletool` 命令，也支持通过环境变量指定 JAR：

```shell
BUNDLETOOL_JAR=/path/to/bundletool-all.jar \
  ./install-dynamic-feature.sh
```

连接多个设备时可以指定序列号：

```shell
./install-dynamic-feature.sh --device-id=<设备序列号>
```

安装完成后，从桌面启动应用，进入 Dynamic Feature 示例页面并点击“立即下载模块”，即可观察 `startInstall()` 的状态变化。不要使用 `--mode=universal`，否则无法模拟功能模块的按需安装。

`bundletool --local-testing` 不支持验证 `deferredInstall()` 和 `deferredUninstall()`；这两个接口需要通过 Google Play 测试轨道或内部应用分享验证。Android Studio 直接运行也可能预装动态模块，只适合调试模块代码，不能证明按需交付流程正确。

## 检查 AAB 内容

可以直接检查 AAB 中 `dynamicfeature` 模块的最终 Manifest：

```shell
bundletool dump manifest \
  --bundle=app/build/outputs/bundle/debug/app-debug.aab \
  --module=dynamicfeature
```

重点确认最终 `split` 名、`dist:on-demand`、`dist:title`、`dist:fusing` 和组件合并结果是否符合预期。也可以使用 Android Studio 的 APK Analyzer 查看各模块的代码、资源和体积分布。

# 🌟Dynamic Feature 安装后的运行时加载机制

## 与普通 App 类加载相比多了什么问题

普通 App 启动前，Base APK 及安装时 split 已经由 PackageManager 登记。此时代码集合在当前进程的生命周期内基本不变。某个类是否位于 DEX、某个资源是否位于资源表，通常在构建和启动阶段就已经确定。完整的普通类加载链路见 [Android 类从源码到运行时加载](<../05 Framework/06 Android类从源码到运行时加载.md>)。

运行时安装 Dynamic Feature 则改变了顺序：

```text
应用进程已经运行
    ↓
ClassLoader、AssetManager、Resources 已经创建
    ↓
新的 Feature Split 才被下载和安装
    ↓
把新代码和资源加入已经存在的运行环境
    ↓
业务才能访问 Feature
```

因此它比普通 App 类加载多出以下问题。

### 代码在时间上不一定存在

普通 App 的 Base 代码从进程启动起就存在；按需 Feature 的 DEX 可能尚未下载、正在安装、安装失败，或者在上一次运行后被卸载。Base 不能把 Feature 类视为随时可用的普通依赖。

### 需要修改已经创建的 ClassLoader

普通启动由系统使用完整代码路径创建 ClassLoader；运行中安装时，应用 `PathClassLoader` 已经存在，其 `dexElements` 中没有新 Feature。当前进程若要立即使用 Feature，就必须安全地扩展现有 DEX 查找路径。

这项操作依赖 Android 不同版本的内部实现，而且已经加载过的类不会因为路径变化而重新定义。Dynamic Feature 只能增加新类来源，不能作为覆盖 Base 类的热修复机制。

### 代码和资源不是同一套加载系统

Feature DEX 可见后，只能说明 ClassLoader 可以查找类。Feature 资源还需要进入 `AssetManager`；已经创建的 Activity 又可能继续持有旧的 `Resources`。

因此可能出现“Feature 类已经能创建，但读取 Feature 布局或字符串失败”的中间状态。普通冷启动一般不会遇到这个时间差，因为 ClassLoader 和资源环境会基于同一组已安装 APK 一起建立。

### 已加载内容不能立即卸载

新的 DEX 可以加入 ClassLoader，但当前进程没有对等、可靠的“移除 DEX 并卸载所有类”操作。已经创建的 `Class`、对象和资源引用也可能继续存活。因此延迟卸载主要影响后续进程，不能被理解为当前进程中的代码立刻消失。

## 🌟代码层面上的原理

以下依据本机 [Play Feature Delivery 2.1.0 发布包](https://dl.google.com/dl/android/maven2/com/google/android/play/feature-delivery/2.1.0/feature-delivery-2.1.0.aar) 的字节码还原调用关系。代码采用 **Java 风格伪代码**：保留关键分支和数据流，用可读名称替代部分混淆名，省略日志、统计、语言请求和部分异常处理；文中同时标出对应的真实方法，便于对照实现。

### SplitCompat.install：保存实例，并注册后续加载入口

- SplitCompat.install主要是初始化SplitCompat，比如注册下载完成时的处理逻辑。以及加载已有的split。
  - **将 split APK 转换为 `DexPathList.Element`，再通过反射追加到现有 ClassLoader 的 `pathList.dexElements` 中。** 后续查找 DF 的类时，就能遍历到新增的 DEX。

- SplitCompat.installActivity(activity)主要是Activity能够访问已加载df的资源。

### startInstall：把请求变成 Binder 调用，并把回调变成 Task

- `startInstall()` 内部通过 `bindService()` **绑定 Play Store 提供的服务**，再通过 Binder 提交安装请求。
- `addOnSuccessListener` 表示**安装请求已被受理，获得了会话 ID**。不是指下载成功。
- 系统正式安装的 split 通常位于 `/data/app/.../`，准确路径应读取 `ApplicationInfo.splitSourceDirs。

### 下载完成后，代码如何回到 SplitCompat

- SplitCompat内部接收安装状态广播，安装完成后会触发SplitCompat.install核心逻辑进行加载。

业务不需要在下载回调中自己反射修改 ClassLoader：启动时保存处理器，下载完成时调用处理器，处理器再进入 SplitCompat 的加载函数。

### SplitCompat.install 是如何将 split 加载到 ClassLoader 中的，以 DEX 为例

核心操作是：**把 split APK 转换为 `DexPathList.Element`，追加到现有应用 ClassLoader 的 `dexElements` 数组中。** 以下以默认的非 isolated split 模式为例。

`SplitCompat.install()` 最终进入内部的 `zzh()` 加载逻辑。它找到已校验且需要加载的 split，检查其中是否包含 `classes.dex`，再取得 `context.getClassLoader()`，交给对应 Android 版本的适配实现。核心过程可简化为：

```java
// 伪代码：省略去重、优化检查和异常处理；反射方法签名随 Android 版本变化。
ClassLoader loader = context.getClassLoader();
Object pathList = readField(loader, "pathList");
Object[] oldElements = (Object[]) readField(pathList, "dexElements");

// 反射调用系统方法，从 split APK 中打开 DEX 并构造 Element。
Object[] newElements = invokeHidden(
    pathList, "makePathElements",
    List.of(splitApk), optimizedDir, suppressedExceptions
);

// 数组不能原地扩容，因此创建相同元素类型的新数组，再写回原 pathList。
Object[] combined = (Object[]) Array.newInstance(
    oldElements.getClass().getComponentType(),
    oldElements.length + newElements.length
);
System.arraycopy(oldElements, 0, combined, 0, oldElements.length);
System.arraycopy(newElements, 0, combined, oldElements.length, newElements.length);
writeField(pathList, "dexElements", combined);
```

`readField()`、`writeField()` 和 `invokeHidden()` 表示反射读写字段、调用方法。2.1.0 中，读取 `pathList`、处理 `dexElements` 的逻辑位于 `internal.zzat`，数组追加位于 `internal.zzbi.zza()`；部分版本通过适配器反射调用 `makePathElements()`，其他版本使用 `makeDexElements()`。

系统方法会打开 APK 内的 DEX，创建持有 `DexFile` 的 `Element`。追加后，查找范围从 `[Base, 已有 split]` 变成 `[Base, 已有 split, 新 split]`。后续需要加载 DF 中的类时，ClassLoader 沿着 `DexPathList.findClass()` 遍历元素，命中新 split 的 `DexFile` 后，再交给 ART 定义类。因此，这一步主要建立新的类查找来源，并不会立即初始化 DF 中所有类。[DexPathList 源码](https://android.googlesource.com/platform/libcore/+/refs/heads/master/dalvik/src/main/java/dalvik/system/DexPathList.java)



## 资源如何被发现

### Resources 与 AssetManager 的关系

`Resources` 负责根据资源 ID 和当前设备配置选择资源，真正持有 APK 资源路径的是其底层 `AssetManager`。Feature 资源没有复制到 Base APK，而是继续保存在 Feature Split 及其语言、密度等配置 Split 中。

因此，资源生效的关键不是修改资源 ID，而是让 `AssetManager` 能访问这些新的 APK 文件。

### SplitCompat 的资源注入过程

Play Feature Delivery 2.1.0 的 SplitCompat 会取得目标 Context 的 `AssetManager`，然后对需要加载的 Feature Split 和配置 Split 逐个执行相当于下面的操作：

```text
Context.getAssets()
        │
        └── AssetManager.addAssetPath(featureSplitApkPath)
                         │
                         └── 返回资源路径对应的 cookie
```

`addAssetPath()` 同样是通过反射调用的隐藏方法。调用成功后，当前 `AssetManager` 的查找范围中就多了 Feature APK；由它支撑的 `Resources` 随后可以读取该 APK 内的资源表、`res/` 文件和 `assets/`。

### 资源查找过程

代码访问 Feature 资源时，流程可以简化为：

```text
资源 ID
  ↓
Resources
  ↓
AssetManager 中已挂载的资源表
  ├── Base APK
  ├── Feature Split APK
  └── Feature 配置 Split APK
  ↓
根据语言、密度等配置选出最终资源
```

Feature 主 split 提供资源定义，配置 split 提供匹配当前设备的具体变体。只有相关路径都进入 `AssetManager`，资源 ID 才能解析到正确内容。

`Resources` 和 `AssetManager` 依附于具体 Context。进程运行期间安装 Feature 时，已经创建的 Activity 可能仍持有旧的资源对象，因此代码路径已经可见，并不代表所有旧 Context 都自动获得了新的资源路径。SplitCompat 对 Activity Context 的处理，本质上就是让该 Context 使用包含新 split 的资源查找范围。
