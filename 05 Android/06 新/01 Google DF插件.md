本文聚焦 Android Gradle Plugin 提供的 `com.android.dynamic-feature` 插件，以及与它配套的 Google Play Feature Delivery。示例使用 Kotlin DSL；Groovy DSL 的配置含义相同。

> 文档核对日期：2026-08-29。Play Feature Delivery、Android Gradle Plugin 和 Play Console 的规则会继续演进，落地前应再次检查文末官方资料。

# Android 编译产物基础

## 🌟🌟🌟整体理解

传统 Universal APK 包含多种设备配置资源，体积较大；自行维护多个 APK 又会增加开发成本。因此 Google 推出 AAB，由 Google Play 根据用户设备生成并下发 Base APK 和对应的 Split APK。对于非核心功能，还可以使用 Dynamic Feature，让用户在需要时再下载。

## APK

APK 是可以安装到 Android 设备上的应用包，通常包含：

- 编译后的 DEX 代码；
- `AndroidManifest.xml`；
- 图片、布局、字符串等资源；
- assets 和 native `.so` 库；
- 签名及包内元数据。

传统的通用 APK 会同时包含多种 ABI、屏幕密度和语言资源，因此同一个 APK 能适配较多设备，但用户也可能下载当前设备不需要的内容。

## AAB

Android App Bundle（AAB）是应用的**发布产物**，不能像 APK 一样直接安装。它保存基础模块、功能模块以及不同设备配置所需的代码和资源，Google Play 或 `bundletool` 会根据 AAB 生成实际安装到设备上的 APK。

AAB 的价值在于“先完整发布，再按设备拆分”。开发者只上传一个 AAB，Google Play 可以只给用户下发其设备需要的 ABI、密度、语言和功能模块内容。

## Split APK

从 AAB 生成的应用通常由多个相互配合的 Split APK 组成：

| 类型 | 作用 |
| --- | --- |
| Base APK | 包含应用基础代码、基础资源和核心 Manifest |
| Configuration APK | 包含特定 ABI、屏幕密度或语言资源 |
| Feature APK | 包含某个 Dynamic Feature 的代码、资源和组件 |

这些 APK 共享相同的应用身份、版本和签名，需要作为同一个应用协同安装。Dynamic Feature 的“动态”主要体现在 Feature APK 可以不随首次安装下发，而是在用户需要功能时再安装。

## 为什么需要 AAB 和 Split APK

AAB 和 Split APK 主要解决传统通用 APK 的三个问题：

- **无效下载较多**：通用 APK 会同时包含多种 ABI、屏幕密度和语言资源，而一台设备通常只需要其中一套。Google Play 可以根据 AAB 只生成并下发当前设备需要的 Split APK。
- **Multi-APK 维护复杂**：过去开发者需要自行构建和管理面向不同设备的多个 APK。使用 AAB 后，开发者只发布一个 Bundle，设备匹配和 APK 生成由 Google Play 完成。
- **功能无法独立交付**：单体 APK 中的所有功能都随应用一起安装。Feature APK 可以让低频功能按需下载，也可以按照国家、API 级别或硬件能力进行条件交付。

本质上，这套机制把一个大而全的 APK 转换成一组按设备和功能组合安装的小型 APK。Dynamic Feature 只有作为独立的 Feature APK，才能被单独下载和管理。代价是构建、测试和运行时状态管理更加复杂，并且高级交付能力依赖 Google Play。

## 用户从 Google Play 下载什么

如果开发者上传的是 AAB，用户首次从 Google Play 安装应用时，下载的通常不只是 Base APK，而是 Google Play 针对当前设备生成的一组优化 APK：

```text
首次安装
├── Base APK
├── 当前设备需要的 ABI Configuration APK
├── 当前设备需要的密度和语言 Configuration APK
└── 配置为 install-time 的 Feature APK

用户触发按需功能后
└── 配置为 on-demand 的 Feature APK
```

Base APK 提供应用核心能力，Configuration APK 补充当前设备需要的资源和 native library，安装时功能模块也会一起下发。配置为 on-demand 的 Dynamic Feature 不包含在首次安装中，而是在应用通过 `SplitInstallManager` 请求后下载。

Google Play 会把这些 Split APK 作为同一个应用统一安装，用户在商店界面中通常不会感知它们是多个文件。只有开发者直接发布传统 APK 时，用户获取的才是一个包含全部代码和资源的完整 APK。

## AAR

AAR 是 Android Library 的构建产物，可以包含代码、资源和 Manifest，但不能独立安装。构建应用时，AAR 内容会被合并进应用 APK 或 AAB。

普通 Android Library 主要解决源码和依赖模块化；Dynamic Feature 除了模块化，还会在 AAB 中保留独立的功能交付边界。

## 与 Dynamic Feature 的关系

整个过程可以简化为：

```text
:app + :dynamicfeature + AAR 依赖
                 │
                 │ Android Gradle Plugin
                 ▼
                AAB
                 │
                 │ Google Play 或 bundletool
                 ▼
Base APK + Configuration APK + Feature APK
                                      │
                                      │ 按需下载和安装
                                      ▼
                              Dynamic Feature 可用
```

因此，`com.android.dynamic-feature` 插件不是让应用随意加载外部 APK，而是让某个功能在同一个 AAB 中形成可独立交付的 Feature APK。

# 概念与定位

## `com.android.dynamic-feature` 是什么

`com.android.dynamic-feature` 是 Android Gradle Plugin（AGP）的一部分，用于把一个 Gradle 模块声明为 **Dynamic Feature Module**，即动态功能模块。

它解决的是“应用功能何时交付到用户设备”的问题。开发者把相对独立的功能从基础模块中拆出，构建时仍生成同一个 Android App Bundle（AAB），Google Play 再根据交付规则和设备配置生成、安装对应的 split APK。

它适合体积较大、使用频率较低或只对部分设备开放的功能，例如视频编辑、AR 和地区性支付功能。对于应用启动、登录和核心导航等所有用户都需要的功能，通常仍应保留在基础模块中。

插件主要在构建阶段完成以下工作：

- 建立动态功能模块与基础应用模块的构建关系；
- 将代码、资源和 Manifest 打入同一个 AAB；
- 根据 `dist:*` 配置生成安装时、按需或条件交付所需的元数据。

它本身不负责运行时下载。运行时安装、监听进度、取消和卸载功能由 Play Feature Delivery Library 提供。

## 🌟三个容易混淆的组成部分

| 组成部分 | 发生阶段 | 职责 |
| --- | --- | --- |
| `com.android.dynamic-feature` | 构建期 | 声明模块类型，将模块打入 AAB 并生成交付元数据 |
| Play Feature Delivery Library | 运行期 | 通过 `SplitInstallManager` 请求、监听和管理动态功能 |
| `bundletool` 或 Google Play | 打包与分发期 | 从 AAB 生成适配设备的 base、feature、ABI、语言和密度 split APK |

简而言之，Gradle 插件负责“构建进 AAB”，Google Play 或 `bundletool` 负责“生成并分发 split APK”，运行库负责“在应用内请求和管理模块”。

## 它不是什么

Dynamic Feature 不是传统意义上的插件化框架，也不是热修复方案：

- 动态模块必须随基础应用放在同一个 AAB 中发布，不能从任意服务器下载未发布的可执行代码；
- 模块与基础应用共享应用身份、签名和版本生命周期，不能独立更新；
- 它依赖 Google Play 的交付能力，其他应用商店不一定提供等价支持。

# 工作原理

## 基础模块与动态功能模块

一个使用 Dynamic Feature 的应用至少包含：

- 一个应用基础模块，通常为 `:app`，应用 `com.android.application`；
- 一个或多个动态功能模块，应用 `com.android.dynamic-feature`；
- 可选的普通 Android Library 模块，用于承载稳定接口、数据层和公共实现。

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

1. AGP 为基础模块和动态功能模块创建匹配的 build type、product flavor 和 variant。
2. `:app:bundleRelease` 将所有模块打入同一个 AAB。
3. Google Play 读取每个动态模块的 `dist:module` 和 `dist:delivery` 配置。
4. Google Play 根据设备 ABI、屏幕密度、语言以及功能交付条件生成并选择 split APK。
5. 安装时模块随应用首次安装；按需模块暂不下发。
6. 用户触发按需功能时，基础应用通过 `SplitInstallManager` 请求模块。
7. Play Store 下载并验证 feature split，系统或 SplitCompat 使新代码和资源对应用可见。
8. 之后上传新版本 AAB 时，Google Play 会随应用版本更新已经安装的动态模块。

# 工程配置

## 🌟🌟🌟整体介绍

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

示例版本来自当前官方接入文档，实际项目应在升级时核对 Play Core 发布说明。

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
- `dist:title` 引用的字符串必须定义在基础模块中，以便模块尚未安装时由 Google Play 展示；
- `<dist:fusing dist:include="true" />` 表示 API 20 及以下设备在安装时获得该功能；设为 `false` 时旧设备无法使用。API 21 及以上仍按 `<dist:delivery>` 交付；
- `split` 和 `android:isFeatureSplit` 由构建系统生成，不要手工填写。

核心规则如下：

- `com.android.dynamic-feature` 与其他 Android 插件使用同一个 AGP 版本；
- 动态模块依赖基础模块，基础模块业务代码不能静态引用尚未安装的动态模块实现；
- `compileSdk`、`minSdk`、build type 和 product flavor 应与基础模块匹配；
- `applicationId`、版本号、签名和是否启用代码压缩由基础模块统一配置。

# Manifest 与交付模式

## Manifest 基本结构

动态功能模块使用 distribution 命名空间描述交付方式：

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:dist="http://schemas.android.com/apk/distribution">

    <dist:module
        dist:instant="false"
        dist:title="@string/feature_checkout_title">

        <dist:delivery>
            <dist:on-demand />
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

`dist:title` 用于系统向用户说明待下载模块，官方要求标题不超过 50 个字符。这个字符串资源必须放在基础模块中，因为动态模块尚未安装时系统就可能需要展示它：

```xml
<!-- app/src/main/res/values/strings.xml -->
<string name="feature_checkout_title">结算功能</string>
```

如果 Release 构建启用了资源压缩，而基础模块代码没有直接引用该标题，资源压缩器可能将它删除。可以在基础模块添加资源保留文件：

```xml
<!-- app/src/main/res/raw/keep.xml -->
<resources xmlns:tools="http://schemas.android.com/tools"
    tools:keep="@string/feature_checkout_title" />
```

## 安装时交付

安装时交付表示模块随应用首次安装。未声明其他高级交付方式时，这是功能模块的默认行为；显式写法如下：

```xml
<dist:module
    dist:instant="false"
    dist:title="@string/feature_checkout_title">
    <dist:delivery>
        <dist:install-time />
    </dist:delivery>
    <dist:fusing dist:include="true" />
</dist:module>
```

它适合以下场景：

- 功能首次启动就必须可用；
- 当前只想做模块化，暂时不引入下载状态机；
- 功能代码和资源较大，但绝大多数用户都会使用；
- 希望逐步从普通 Library 迁移为按需模块。

安装时模块默认不可移除。若功能在完成任务后可以删除，例如新手引导，可以把它设为 removable：

```xml
<dist:delivery>
    <dist:install-time>
        <dist:removable dist:value="true" />
    </dist:install-time>
</dist:delivery>
```

`removable="true"` 会阻止 `bundletool` 把该安装时模块融合到基础模块，以便之后独立卸载，但 split 数量增加可能影响安装性能。官方建议可移除的安装时模块保持在 10 个以内。

## 按需交付

按需交付表示首次安装不包含模块，用户真正需要时再请求：

```xml
<dist:delivery>
    <dist:on-demand />
</dist:delivery>
```

按需功能应该满足：

- 不影响应用核心启动和基本闭环；
- 即使无网络、空间不足或 Play Store 不可用，基础应用仍能正常运行；
- 产品能提供明确的下载进度、失败重试和取消体验；
- 下载完成前，代码不会直接加载动态模块类或资源。

只有 Android 5.0（API 21）及以上设备支持运行时下载并安装功能。若仍支持更早版本，可通过 `dist:fusing` 决定模块是否被包含在面向旧设备的 multi-APK 中：

```xml
<dist:fusing dist:include="true" />
```

设置为 `true` 表示旧设备会在安装时获得该功能，不再具有按需效果；设置为 `false` 表示旧设备完全无法获得该功能。

## 条件交付

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

## 关于 Instant Delivery

Instant Delivery 曾用于 Google Play Instant。用户无需先安装完整应用，可以通过链接或 Play 商店的“立即体验”入口直接运行一个轻量功能。Google Play 只临时下发该体验所需的代码和资源，用户之后仍可选择安装完整应用。

它与 on-demand 的区别是：on-demand 需要基础应用已经安装，而 Instant Delivery 面向尚未安装应用的用户。动态模块过去可通过 `dist:instant="true"` 声明为 Instant Experience 的一部分。

不过，Google 已宣布从 2025 年 12 月起停止 Google Play Instant：Instant Apps 不能再通过 Google Play 发布，相关服务 API 也不再工作。

因此，新项目不应再把 `dist:instant="true"` 作为交付方案。本文其余示例都显式使用 `dist:instant="false"`，实际应聚焦安装时、按需或条件交付。

## 纯资源模块

如果动态功能模块不产生任何 DEX，只包含资源或资产，需要在该模块 Manifest 中声明：

```xml
<application android:hasCode="false" />
```

同时确保基础模块的 `<application>` 最终保持 `android:hasCode="true"`。若 Manifest 合并发生冲突，可以在基础模块使用 `tools:replace="android:hasCode"` 显式覆盖。

# 运行时安装与状态管理

本节直接对应 AndroidDemo 中的实现，核心代码位于基础模块的 `TestDynamicFeatureActivity`、`MyApplication`，以及动态模块的 `MainDynamicFeatureActivity`。

## 启用 SplitCompat

AndroidDemo 的 `MyApplication` 直接继承 `SplitCompatApplication`，让运行时能够加载后续安装的 split：

```java
public class MyApplication extends SplitCompatApplication {
    // 原有初始化逻辑保持不变
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

## 失败处理

所有异步任务统一交给 `showTaskFailure()`，从 `SplitInstallException` 中读取错误码：

```kotlin
private fun showTaskFailure(error: Exception) {
    val errorCode = (error as? SplitInstallException)?.errorCode
    appendLog("请求失败：${formatErrorCode(errorCode)}；${error.message}")
}
```

Demo 的 `formatErrorCode()` 已覆盖网络异常、空间不足、模块不可用、应用来源不匹配、缺少 Play Store 等常见问题，运行时直接根据日志中的错误码定位即可。

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

## 构建 APK 与 AAB

使用 `--bundle` 构建包含 Dynamic Feature 的 Debug AAB：

```shell
./run.sh --bundle
```

需要清理旧产物时执行：

```shell
./run.sh --bundle --clean
```

AAB 输出位置为：

```text
app/build/outputs/bundle/debug/app-debug.aab
```

Bundle 模式会关闭仅用于 APK 构建的 ABI Split。AAB 会自行生成 ABI 配置 APK，同时可以避免 AGP 7.4.2 在处理 Dynamic Feature 时读取到多个基础模块资源产物。

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

# Dynamic Feature 安装后的运行时加载机制

## 问题本质

Feature Split APK 中包含模块的 `classes.dex`、`resources.arsc`、`res/` 和 `assets/`。文件下载到设备只代表“交付完成”，当前进程还必须把它加入已有的代码和资源查找范围。

本 Demo 使用常见的非 isolated split 配置，Dynamic Feature 不会创建独立 ClassLoader 或资源系统，而是与 Base APK 运行在同一应用进程中。其核心动作只有两个：

```text
Feature Split APK
├── classes.dex ───────▶ 加入应用 ClassLoader 的 DEX 查找路径
└── resources.arsc/res ▶ 加入 Context 的 AssetManager 查找路径
```

## 与普通 App 类加载相比多了什么问题

普通 App 启动前，Base APK 及安装时 split 已经由 PackageManager 登记。系统可以在创建进程时一次性完成下面的工作：

```text
读取完整 APK 路径
    ↓
创建应用 ClassLoader 和 Resources
    ↓
创建 Application、Activity 等组件
    ↓
业务代码开始运行
```

此时代码集合在当前进程的生命周期内基本不变。某个类是否位于 DEX、某个资源是否位于资源表，通常在构建和启动阶段就已经确定。完整的普通类加载链路见 [Android 类从源码到运行时加载](<../07 Framework/06 Android类从源码到运行时加载.md>)。

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

“类位于构建产物中”“Feature Split 已经下载”“PackageManager 已经安装 split”“当前进程的 ClassLoader 已经能找到类”是四种不同状态，不能只判断其中一个就直接进入功能。

### 需要修改已经创建的 ClassLoader

普通启动由系统使用完整代码路径创建 ClassLoader；运行中安装时，应用 `PathClassLoader` 已经存在，其 `dexElements` 中没有新 Feature。当前进程若要立即使用 Feature，就必须安全地扩展现有 DEX 查找路径。

这项操作依赖 Android 不同版本的内部实现，而且已经加载过的类不会因为路径变化而重新定义。Dynamic Feature 只能增加新类来源，不能作为覆盖 Base 类的热修复机制。

### 代码和资源不是同一套加载系统

Feature DEX 可见后，只能说明 ClassLoader 可以查找类。Feature 资源还需要进入 `AssetManager`；已经创建的 Activity 又可能继续持有旧的 `Resources`。

因此可能出现“Feature 类已经能创建，但读取 Feature 布局或字符串失败”的中间状态。普通冷启动一般不会遇到这个时间差，因为 ClassLoader 和资源环境会基于同一组已安装 APK 一起建立。

### 编译期依赖方向无法自动改变

Dynamic Feature 编译时依赖 Base，Base 不反向依赖 Feature。运行时把 Feature DEX 加入 ClassLoader，并不会让 Base 在编译阶段突然获得 Feature 类型和资源 ID。

Base 仍然需要通过组件名、路由、反射或定义在 Base 中的公共接口进入 Feature。若使用字符串反射，还要考虑 R8 删除或重命名目标类的问题。

### 安装与页面生命周期相互独立

Feature 安装是异步过程，完成回调到达时，发起请求的 Activity 可能已经重建、停止甚至销毁，应用进程也可能中途退出。普通类加载通常发生在一次同步的类引用链中，不需要业务额外维护下载会话和页面状态。

### 已加载内容不能立即卸载

新的 DEX 可以加入 ClassLoader，但当前进程没有对等、可靠的“移除 DEX 并卸载所有类”操作。已经创建的 `Class`、对象和资源引用也可能继续存活。因此延迟卸载主要影响后续进程，不能被理解为当前进程中的代码立刻消失。

## Google 与应用开发者的责任边界

| 问题 | Google 提供或解决 | 应用开发者仍需解决 |
| --- | --- | --- |
| 构建与拆包 | AGP 的 Dynamic Feature 插件保留模块边界，AAB 和 Google Play 生成 Base、Feature 与配置 Split APK | 选择合理的模块边界，避免把启动必需代码放入按需模块 |
| 下载与安装 | Play Feature Delivery 负责交付、校验、安装兼容当前设备的 split，并提供安装状态和错误码 | 决定何时请求、如何展示进度、确认、取消、重试和失败降级 |
| 当前进程的代码可见性 | SplitCompat 处理不同 Android 版本的 DEX 路径扩展，使 Feature 类能够被应用 ClassLoader 查找 | 在 Application 中正确接入 SplitCompat，并确保安装完成前不访问 Feature 类 |
| 当前进程的资源可见性 | SplitCompat 把 Feature 及配置 Split 加入目标 Context 的资源路径 | 为 Feature Activity 接入 SplitCompat；旧页面需要新资源时，决定是否重建或重新进入页面 |
| 组件与入口 | 构建工具处理各模块 Manifest，split 安装后由系统登记并识别 Feature 组件 | 设计 Base 到 Feature 的入口协议，只在模块可用后导航，并处理入口参数兼容性 |
| 编译期依赖 | 构建工具允许 Feature 依赖 Base | 维护单向依赖；把共享接口放在 Base，处理反射入口及 R8 keep 规则 |
| 生命周期与状态 | 安装库提供 session 状态，进程重建后可以重新查询模块和会话 | 将安装状态与 Activity 生命周期解耦，恢复页面状态，避免重复请求和重复跳转 |
| 卸载 | Google Play 可以在合适时机移除已请求卸载的 split | 不假设当前进程立即卸载类；释放业务对象，并以新进程中的模块状态为准 |

Google 主要解决的是“如何可靠交付 split，以及如何让 Android 运行时认识新增的代码和资源”。它无法替应用决定何时进入功能、页面如何响应异步状态、模块未安装时显示什么，也无法修正不合理的模块依赖。

结合 Demo，`MyApplication` 继承 `SplitCompatApplication`、Feature Activity 调用 `SplitCompat.installActivity()`，属于应用必须完成的接入；DEX Element 的构造、Android 版本适配和资源路径注入则由 SplitCompat 实现，业务不需要也不应该自行反射修改 ClassLoader。

下面的反射字段和方法基于 Demo 使用的 `com.google.android.play:feature-delivery:2.1.0` 实现。它们属于库的内部实现，不是业务代码可以依赖的公开 API。

## DEX 如何进入 ClassLoader

Kotlin/Java 源码如何变成 DEX、系统如何在进程启动时创建应用 ClassLoader，以及 ART 如何完成类的加载、链接和初始化，见 [Android 类从源码到运行时加载](<../07 Framework/06 Android类从源码到运行时加载.md>)。这里仅说明 Dynamic Feature 相比普通启动流程多出的步骤。

应用启动后，默认 `PathClassLoader` 的 `DexPathList.dexElements` 已经确定。如果 Feature 在进程运行期间才安装，其 DEX 还不在这个数组中；SplitCompat 的工作就是把新 split 转换成可搜索的 Element 并追加进去。

### SplitCompat 的注入过程

Play Feature Delivery 2.1.0 中的 SplitCompat 大致执行以下过程：

1. 找到已经交付且校验通过的 Feature Split APK；
2. 检查 APK 中是否存在 `classes.dex`；
3. 从 `Context.getClassLoader()` 取得应用 ClassLoader；
4. 通过反射读取 `BaseDexClassLoader.pathList` 和 `DexPathList.dexElements`；
5. 根据 Android 版本调用隐藏的 `makeDexElements()` 或 `makePathElements()`，把 split APK 转换为 `DexPathList.Element`；
6. 将新元素追加到原有 `dexElements`，并记录可能出现的 `dexElementsSuppressedExceptions`。

可以把关键变化简化为：

```text
注入前：dexElements = [Base, Existing Split]

Feature Split APK
        │
        └── makeDexElements/makePathElements ──▶ Feature Element

注入后：dexElements = [Base, Existing Split, Feature]
```

Android 不同版本的 `DexPathList` 隐藏方法签名并不一致，因此 SplitCompat 内部为不同 API 版本准备了不同适配实现。这也是应用不应自行复制这套反射逻辑的原因。

注入后，后续类查找会自然遍历到 Feature Element。新 Element 位于现有元素之后，因此 Dynamic Feature 不能依靠同名类覆盖 Base 代码；它只是为原应用增加新的代码来源，而不是建立一套插件隔离环境。

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

## 冷启动与运行中安装

| 场景 | DEX 与资源路径如何建立 |
| --- | --- |
| Feature 已由系统安装后再启动进程 | 系统根据包信息中的 split 路径，在创建进程时一次性建立 ClassLoader 和资源环境 |
| Feature 在进程运行期间安装 | ClassLoader、AssetManager 和 Resources 已经存在，需要 SplitCompat 把新 split 注入当前进程 |

因此，冷启动时主要是“按完整 APK 集合创建运行环境”，运行中安装则是“修改已经存在的运行环境”。后者才需要处理 DEX 注入和旧 Context 资源未刷新的问题。

## 完整链路

```text
Feature Split 安装完成
        │
        ├── classes.dex
        │      ↓
        │   生成 DexPathList.Element
        │      ↓
        │   追加到 ClassLoader.pathList.dexElements
        │      ↓
        │   后续 loadClass() 可以找到 Feature 类
        │
        └── resources.arsc / res / assets
               ↓
            AssetManager.addAssetPath()
               ↓
            Resources 可以解析 Feature 资源
```

最终结果不是“把模块整体加载进内存”，而是把 Feature Split APK 同时登记为新的代码来源和资源来源；类与资源仍在实际访问时才被查找和加载。
