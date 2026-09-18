> 编译产物基础内容核对日期：2026-08-29；AAB、Split APK 结构及 resources.arsc 说明于 2026-09-04 补充核对。落地前应再次检查文中官方资料。

# 🌟🌟🌟整体理解

传统 Universal APK 包含多种设备配置资源，体积较大；自行维护多个 APK 又会增加维护成本。因此 Google 推出 AAB，由 Google Play 根据用户设备生成并下发 Base APK 和对应的 Split APK。对于非核心功能，还可以使用 Dynamic Feature，让用户在需要时再下载。

# APK

APK 是可以安装到 Android 设备上的应用包，通常包含：

- 编译后的 DEX 代码；
- `AndroidManifest.xml`；
- 图片、布局等资源文件，以及保存资源值和索引的 `resources.arsc`；
- assets 和 native `.so` 库；
- 签名及包内元数据。

传统的通用 APK 会同时包含多种 ABI、屏幕密度和语言资源，因此同一个 APK 能适配较多设备，但用户也可能下载当前设备不需要的内容。

## resources.arsc

`resources.arsc` 是 APK 根目录下的**已编译二进制资源表**。它把资源 ID、资源名称、配置条件与对应的资源值或文件路径联系起来，供 Android 运行时查找资源。

直接构建 APK 时，AAPT2 会编译、链接资源并生成资源表；构建 AAB 时则先使用 `resources.pb`，之后在生成 APK 的过程中转换为 `resources.arsc`，详见后文。[AAPT2 官方说明](https://developer.android.com/tools/aapt2)

### 资源表保存什么

**它既是资源索引，也保存一部分资源内容。** 以常见资源为例，下面的路径仅作示意：

| 源工程中的资源 | APK 中的存放方式 | `resources.arsc` 的作用 |
| --- | --- | --- |
| `res/values/strings.xml` 中的字符串 | 字符串值进入资源表，源 XML 不会原样保留 | 记录资源条目，并通过字符串池保存文本 |
| `res/values/colors.xml` 中的颜色常量 | 颜色值进入资源表 | 保存带类型的颜色值 |
| `res/layout/activity_main.xml` | 编译后的布局 XML 作为文件保存在 `res/` 下 | 记录布局资源对应的 APK 内文件路径 |
| `res/drawable/banner.png` | 图片作为文件保存在 `res/` 下 | 记录图片资源对应的 APK 内文件路径 |

同一个资源还可以有多个配置版本，例如 `string/pay` 的默认文本和中文文本，或 `drawable/banner` 的不同密度图片。资源表保留这些配置与值的对应关系，系统再按当前语言、密度、夜间模式等条件选择合适的版本。[Android 资源与配置说明](https://developer.android.com/guide/topics/resources/providing-resources)

从文件结构看，ARSC 由多个二进制数据块（chunk）组成，主要包括资源表头、全局值字符串池，以及资源包（package）中的类型名和条目名字符串池、类型描述及不同配置下的条目数据。类型可以是 `string`、`layout`、`drawable`，条目可以是 `pay`、`activity_main`、`banner`；这里的 package 是资源表内的组织单位，不等于一个 APK 文件。[AOSP 资源表结构定义](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/libs/androidfw/include/androidfw/ResourceTypes.h)

### 资源 ID 如何找到实际资源

代码中的 `R.string.pay` 表示一个整数资源 ID。其格式为 `0xPPTTEEEE`：`PP` 是资源包 ID，`TT` 是类型 ID，`EEEE` 是该类型下的条目索引，分别占 8、8、16 位。**资源 ID 不编码语言或屏幕密度，同一个资源的不同配置版本使用同一个 ID。**[AOSP 资源 ID 定义](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/libs/androidfw/include/androidfw/ResourceTypes.h)

假设应用同时提供默认和中文的 `pay` 字符串，忽略缓存等实现细节，查找过程可以简化为：

```text
context.getString(R.string.pay)
              ↓ 传入整数资源 ID
Resources / AssetManager 查找已加载的资源表
              ↓ 定位 string/pay，并匹配当前资源配置
              ├── 默认配置 → "Pay"
              └── 中文配置 → "支付"
              ↓ 当前语言匹配中文
返回 "支付"
```

对于 `R.layout.activity_main` 或 `R.drawable.banner`，资源系统先查表得到匹配配置下的文件路径，再读取 APK 中对应的 XML 或图片。因此，资源表不需要把布局节点或图片像素本身全部存进去；字符串等值资源则可以直接从表中取得。[Android 资源访问与匹配规则](https://developer.android.com/guide/topics/resources/providing-resources#BestMatch)

### 与 R、assets 和 resources.pb 的区别

- **`R` 提供代码中的资源标识**：例如 `R.string.pay` 提供 ID，具体文本由资源表及当前配置决定。
- **`assets/` 中的文件不分配资源 ID**：通常通过 `AssetManager.open("文件路径")` 读取，不经过这套资源 ID 查表与配置匹配机制。`res/raw/` 则会分配 `R.raw.xxx`，仍属于资源表管理的资源。[官方资源目录说明](https://developer.android.com/guide/topics/resources/providing-resources)
- **`resources.pb` 和 `resources.arsc` 都表示编译后的资源表**：前者用于 AAB 的构建与拆分，后者用于 APK 的运行时读取。后文会进一步说明二者的格式和转换关系。

实际排查时，可以在 Android Studio 的 APK Analyzer 中选择 `resources.arsc`，查看不同配置下的资源值；也可以使用 `aapt2 dump resources app.apk` 打印资源表。[APK Analyzer](https://developer.android.com/studio/debug/apk-analyzer)、[AAPT2 dump](https://developer.android.com/tools/aapt2#dump)

# AAB

Android App Bundle（AAB）是应用的**发布产物**，不能像 APK 一样直接安装。它保存基础模块、功能模块以及不同设备配置所需的代码和资源，Google Play 或 `bundletool` 会根据 AAB 生成实际安装到设备上的 APK。

AAB 的价值在于“先完整发布，再按设备拆分”。开发者只上传一个 AAB，Google Play 可以只给用户下发其设备需要的 ABI、密度、语言和功能模块内容。

## 为什么用AAB

AAB 和 Split APK 主要解决传统通用 APK 的三个问题：

- **无效下载较多**：通用 APK 会同时包含多种 ABI、屏幕密度和语言资源，而一台设备通常只需要其中一套。Google Play 可以根据 AAB 生成适配不同配置的 APK，再选择并下发当前设备需要的一组。
- **Multi-APK 维护复杂**：过去开发者需要自行构建和管理面向不同设备的多个 APK。使用 AAB 后，开发者只发布一个 Bundle，设备匹配和 APK 生成由 Google Play 完成。
- **功能无法独立交付**：单体 APK 中的所有功能都随应用一起安装。Feature APK 可以让低频功能按需下载，也可以按照国家、API 级别或硬件能力进行条件交付。

## AAB 的内部结构

AAB 是一个 ZIP 格式的归档，按模块组织编译产物。以基础模块 `:app` 和动态功能模块 `:feature:checkout` 为例，典型目录如下；部分文件和目录按实际内容存在：

```text
app.aab
├── BundleConfig.pb                  # APK 生成配置
├── BUNDLE-METADATA/                 # 构建工具元数据，例如混淆映射
│
├── base/                            # 基础模块
│   ├── manifest/
│   │   └── AndroidManifest.xml
│   ├── dex/
│   │   ├── classes.dex
│   │   └── classes2.dex
│   ├── resources.pb                 # protobuf 格式的资源表
│   ├── res/
│   │   ├── layout/activity_main.xml
│   │   ├── drawable-hdpi/...
│   │   └── drawable-xxhdpi/...
│   ├── lib/
│   │   ├── arm64-v8a/libexample.so
│   │   └── armeabi-v7a/libexample.so
│   ├── assets/...
│   └── root/...                     # 生成 APK 时移到 APK 根目录
│
└── checkout/                        # 动态功能模块
    ├── manifest/
    │   └── AndroidManifest.xml
    ├── dex/
    │   └── classes.dex
    ├── resources.pb
    ├── res/...
    ├── lib/...
    └── assets/...
```

`base/` 和 `checkout/` 分别保存各自的代码、资源与 Manifest。`BundleConfig.pb` 描述拆分、压缩等 APK 生成规则；`BUNDLE-METADATA/` 中的信息供工具和应用商店使用，不会直接打进生成的 APK。[官方 AAB 格式说明](https://developer.android.com/guide/app-bundle/app-bundle-format)

- AAB 中的业务代码已经编译成 DEX，Google Play 生成 APK 时不需要重新编译 Kotlin、Java 源码
- Manifest 和资源表则使用 Protocol Buffers 格式：即使 Manifest 文件名仍是 `AndroidManifest.xml`，它也不是普通文本 XML
- 资源表保存为 `resources.pb`，而不是 APK 中的 `resources.arsc`

### resources.pb

> 两者都是编译后的资源表，主要区别在于使用阶段和编码格式。
>
> - **`resources.pb` 给构建工具用**：采用 Protobuf，方便 Google Play / bundletool 解析、筛选和拆分资源。
> - **`resources.arsc` 给 Android 运行时用**：采用系统支持的二进制资源表格式，用于按资源 ID 和设备配置查找资源。

**AAB 中的资源还需要经过加工。** Google Play 拿到它以后，需要区分默认资源、中文资源、不同密度的图片，再将它们分配到对应 APK 中。

protobuf 用明确的结构描述这些信息，概念上类似：

```
资源表
└── package
    └── type：string
        └── entry：pay
            ├── 默认配置 → "Pay"
            ├── 中文配置 → "支付"
            └── 法语配置 → "Payer"
```

实际的 `Resources.proto` 就包含 `Package`、`Type`、`Entry`、`ConfigValue` 等结构。它还可以携带源码位置、工具版本等辅助信息，其中部分信息不会进入最终 ARSC。[AOSP 资源表定义](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/tools/aapt2/Resources.proto)

**从工具链设计上看，protobuf 的收益是便于解析、修改和扩展。** 工具可以使用生成的数据类型操作资源条目，再输出新的资源表。这是对其工程作用的解释，不代表 Google 官方公布了唯一的格式选型原因。

**APK 中的资源表则需要被 Android 直接使用。** 例如：

```
getString(R.string.pay)
```

资源系统需要根据资源 ID 定位条目，再根据当前语言选择值。ARSC 中的字符串池、资源类型块、条目索引和偏移等结构，就是这种查找使用的数据布局。[AOSP ARSC 结构定义](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/libs/androidfw/include/androidfw/ResourceTypes.h)

对应到上面的例子，启用语言拆分后，可以简化理解为：

```
AAB 的 resources.pb
包含 pay 的默认、中文、法语配置
              ↓ 筛选配置并转换格式
base.apk / resources.arsc
└── pay：默认值 "Pay"

中文配置 APK / resources.arsc
└── pay：中文值 "支付"

法语配置 APK / resources.arsc
└── pay：法语值 "Payer"
```

这里改变的是资源配置的分布和编码格式，同一个资源的不同语言版本仍然通过对应的资源 ID 关联。

另外，**`resources.pb` 也已经是编译、链接后的资源表表示，而且同样是二进制格式**。选择 protobuf 不意味着 ARSC 无法拆分：AAPT2 本身就支持资源拆分，以及 `proto`、`binary` 两种格式之间的转换。因此，不能把原因简单归结为“PB 更小、更快”或“只有 PB 才能拆包”。[AAPT2 官方说明](https://developer.android.com/tools/aapt2#convert)

# Split APK

Split APK 由 Google Play 根据 AAB 生成，核心工具是 `bundletool`。从 AAB 生成的应用通常由多个相互配合的 Split APK 组成：

| 类型 | 作用 |
| --- | --- |
| Base APK | 包含应用基础代码、基础资源和核心 Manifest |
| Configuration APK | 为 Base 或某个 Feature 补充特定 ABI 的原生库、屏幕密度或语言资源 |
| Feature APK | 承载某个 Dynamic Feature 的代码、资源及组件声明，具体内容取决于模块 |

这些 APK 共享相同的应用身份、版本和签名，需要作为同一个应用协同安装。Dynamic Feature 的“动态”主要体现在 Feature APK 可以不随首次安装下发，而是在用户需要功能时再安装。

## bundletool

`bundletool` 能基于 AAB 生成 Base、Feature、Configuration 等 APK，也能生成 Universal APK。

严格区分时：

| APK 类型          | 用途                         | 是否属于 Split APK        |
| ----------------- | ---------------------------- | ------------------------- |
| Base APK          | 应用基础代码、资源和核心配置 | 严格来说单独称为 Base APK |
| Feature APK       | 某个功能模块的内容           | 是                        |
| Configuration APK | 特定 ABI、语言、密度的内容   | 是                        |
| Universal APK     | 将内容集中打包为一个通用 APK | 否                        |

Android `PackageInstaller` 的准确表述是：**一个应用由一个 Base APK，加上零个或多个 Split APK 组成**。Base 的 split 名为 `null`，其他 Split APK 各自拥有唯一的 split 名。[官方定义](https://developer.android.com/reference/android/content/pm/PackageInstaller)

## Base APK 与 Feature APK 的内部结构

Split APK 仍然使用 APK 格式，每个包都有自己的 Manifest。下面是基础 APK 和包含代码、资源的功能 APK 的典型结构，省略签名及工具元数据；文件名仅为示意：

```text
base.apk
├── AndroidManifest.xml
├── classes.dex
├── classes2.dex
├── resources.arsc
├── res/
│   └── layout/activity_main.xml
└── assets/...

checkout.apk
├── AndroidManifest.xml
├── classes.dex
├── resources.arsc
├── res/
│   └── layout/activity_checkout.xml
└── assets/...
```

`classes.dex` 承载该包的代码，`resources.arsc` 承载资源表。Manifest 和布局 XML 使用编译后的二进制 XML 格式。源工程中 `values/strings.xml` 的字符串通常已经进入资源表，不会原样保留为 `res/values/strings.xml`。[APK Analyzer 官方说明](https://developer.android.com/studio/debug/apk-analyzer)

目录随实际内容变化：纯资源 Feature 可以没有 DEX，没有 assets 的模块也不需要 `assets/` 目录。启用配置拆分后，属于该模块的部分资源和 native 库会放入对应的 Configuration APK。

## Configuration APK 的内部结构

配置 APK 只补充某类设备配置需要的内容。例如，下面分别展示 ABI、屏幕密度和语言配置 APK 的典型结构，同样省略签名及工具元数据：

```text
ARM64 配置 APK
├── AndroidManifest.xml
└── lib/
    └── arm64-v8a/
        └── libexample.so

xxhdpi 配置 APK
├── AndroidManifest.xml
├── resources.arsc
└── res/
    └── drawable-xxhdpi-v4/
        └── banner.png

仅包含中文字符串的配置 APK
├── AndroidManifest.xml
└── resources.arsc
```

因此，不能认为每个 Split APK 都包含 `classes.dex`、`resources.arsc` 和 `res/`：

- 常见配置 APK 不包含 DEX；ABI 配置包仍然可以包含 `.so` 原生代码。
- 仅包含字符串的语言配置包可以把值直接保存在 `resources.arsc` 中，不需要单独的 `res/` 文件。
- 只携带 native 库的配置包可以没有 `resources.arsc`；Android 加载 APK 时允许资源表缺省。[AOSP APK 资源加载实现](https://android.googlesource.com/platform/frameworks/base/+/4624816/libs/androidfw/ApkAssets.cpp)

### 用途实例

**使用 AAB 经 Google Play 分发，并开启语言拆分时，多语言资源会以 Configuration APK（语言配置包）的形式下发。语言拆分默认开启。**[官方配置说明](https://developer.android.com/guide/app-bundle/configure-base)

Configuration APK 为 Base APK 或 Feature APK 补充特定配置的内容，常见配置包括**语言、屏幕密度和 CPU 架构**。例如：

- 应用支持中文、法语，会生成相应的语言配置包。
- 首次安装时，Google Play 下发与设备所选语言匹配的包。
- 用户之后切换语言时，Google Play 可以补充下载缺少的语言包。[官方交付说明](https://developer.android.com/guide/app-bundle/app-bundle-format#user_language_changes)

如果**关闭语言拆分**，多语言资源就直接打进对应的 Base APK 或 Feature APK，不再单独生成语言配置包。[官方配置说明](https://developer.android.com/guide/app-bundle/configure-base)

### so拆分

```
android {
    bundle {
        abi {
            enableSplit = true // 开启；改为 false 即关闭
        }
    }
}
```

- **`true`（默认）**：按 ABI 生成 Configuration APK，设备下载匹配架构的原生库。
- **`false`**：不生成独立的 ABI 配置包，原生库保留在对应的 Base APK 或 Feature APK 中。[官方配置说明](https://developer.android.com/guide/app-bundle/configure-base)

**开启 ABI 拆分，标准放在 `lib/<ABI>/` 下的 `.so`，会被分配到对应的 ABI Configuration APK 中。** Base APK 或 Feature APK 主体通常不再携带这些库。[官方说明](https://developer.android.com/guide/app-bundle/app-bundle-format#overview_of_split_apks)

例如，基础模块包含多个 ARM64 原生库，生成结果可以是：

```
base.apk
├── classes.dex
├── resources.arsc
└── res/...

Base 的 ARM64 Configuration APK
├── AndroidManifest.xml
└── lib/arm64-v8a/
    ├── libfoo.so
    └── libbar.so
```

**同一模块、同一 ABI 的多个 `.so` 可以放进同一个配置包**，不需要每个 `.so` 单独一个 APK。Feature 的原生库则进入该 Feature 对应的 ABI 配置包；如果功能按需交付，这些库也随功能后续下载。[模块与配置包关系](https://developer.android.com/guide/app-bundle/app-bundle-format#overview_of_split_apks)

“所有 `.so` 都在配置包里”需要限定条件：

- **关闭 ABI 拆分**时，原生库会保留在对应的主体 APK 中。[拆分配置](https://developer.android.com/guide/app-bundle/configure-base)
- **自行放在 `assets/` 等位置的 `.so`**，不能仅凭扩展名就按标准原生库拆分；标准识别路径是 `lib/<ABI>/lib名称.so`。[原生库目录规范](https://developer.android.com/ndk/guides/abis#native-code-in-app-packages)

## Manifest 如何关联各个 APK

系统通过 Manifest 中的包身份、split 标识和依赖信息识别各 APK 的关系。以 `checkout` 功能的中文配置包为例，APK 中 Manifest 解码后的关键字段可以简化为：

```xml
<manifest
    xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.example.shop"
    split="checkout.config.zh"
    android:versionCode="100"
    configForSplit="checkout">

    <application android:hasCode="false" />
</manifest>
```

这些字段的含义是：

- `package`：属于哪个应用，同一安装集合中的 APK 使用相同的应用包名。
- `split`：这个拆分包的标识。
- `configForSplit="checkout"`：补充 `checkout` 功能包；基础模块的配置包通常省略该属性。
- `android:hasCode="false"`：不包含 DEX，不代表不能包含 `.so`。

这是构建产物的示意，不应把 `split`、`configForSplit` 等字段手工复制到动态模块的源 Manifest 中。`bundletool` 会生成配置包的精简 Manifest，并设置对应关系。[bundletool Manifest 生成实现](https://raw.githubusercontent.com/google/bundletool/master/src/main/java/com/android/tools/build/bundletool/model/AndroidManifest.java)

安装后，这些 APK 仍然是多个文件，由 Android 作为同一个应用统一管理和使用。ClassLoader 与 AssetManager 如何访问这些 APK 中的代码和资源，见 [Google DF 插件：Dynamic Feature 安装后的运行时加载机制](<03 Google DF插件.md#dynamic-feature-安装后的运行时加载机制>)。

# Google Play 如何从 AAB 生成 APK

## 生成与交付流程

Google Play 的 APK 生成能力可以通过本地 `bundletool` 复现。整个过程可以概括为：

```text
AAB：按模块保存编译产物和 APK 生成配置
  ↓
解析模块关系、交付方式与拆分规则
  ↓
按模块、ABI、语言、屏幕密度划分内容
  ↓
转换 Manifest 和资源格式，打包并签名
  ↓
按设备配置和交付规则选择 APK 集合
  ↓
Android 将这组 APK 作为同一个应用安装和使用
```

具体包括：

1. **读取模块与配置**：解析各模块 Manifest 和 Bundle 配置，确定模块关系、交付方式及启用的拆分维度。
2. **划分内容**：保留基础和功能模块的主体内容，把适合拆分的 native 库、语言和密度资源分配到配置 APK。通常 DEX 随模块主体交付，ABI 拆分针对 `.so` 等架构相关内容。
3. **转换为 APK 格式**：调整文件路径，生成各 APK 的 Manifest，并将 protobuf 资源转换为 Android 运行时使用的二进制格式。AAPT2 提供相应格式转换能力。
4. **签名**：Play App Signing 使用应用签名密钥为 APK 签名。上传 AAB 使用的上传密钥与最终 APK 的应用签名密钥可以不同。
5. **匹配并交付**：根据设备配置和模块交付规则选择需要安装的 APK 集合，按需模块在后续请求时交付。

这里描述的是生成与选择 APK 的逻辑关系，不表示每次用户点击安装时，Play 都必须重新生成全部 APK。[bundletool 官方说明](https://developer.android.com/tools/bundletool)、[AAPT2 格式转换](https://developer.android.com/tools/aapt2#convert)、[Play App Signing](https://developer.android.com/studio/publish/app-signing#app-signing-google-play)

## AAB 文件如何映射到 APK

| AAB 中的内容 | 生成 APK 时的处理 |
| --- | --- |
| `base/dex/classes.dex` | 放到基础 APK 根目录的 `classes.dex` |
| `checkout/dex/classes.dex` | 放到功能 APK 根目录的 `classes.dex` |
| `模块/manifest/AndroidManifest.xml` | 处理为各 APK 根目录的二进制 Manifest |
| `模块/resources.pb` | 按拆分结果生成 `resources.arsc` |
| `模块/res/...` | 分配到主体或配置 APK，XML 资源转换格式 |
| `模块/lib/arm64-v8a/...` | 启用 ABI 拆分时，放入对应 ARM64 配置 APK |
| `模块/root/...` | 移到包含该模块内容的 APK 根目录 |

这些路径调整与资源表转换可以在 [bundletool 打包实现](https://raw.githubusercontent.com/google/bundletool/master/src/main/java/com/android/tools/build/bundletool/io/ApkSerializerHelper.java)中看到。

## 一个模块可以生成多个 APK

Configuration APK 可以属于 Base，也可以属于某个 Feature。假设启用了常见配置拆分、功能模块保留独立交付边界，而且模块确实包含相应资源，某台 ARM64、xxhdpi、中文设备所需的 APK 可能是：

```text
AAB 中的 base 模块
├── base.apk
├── base 的 ARM64 配置 APK
├── base 的 xxhdpi 配置 APK
└── base 的中文配置 APK

AAB 中的 checkout 模块
├── checkout 功能 APK
├── checkout 的 ARM64 配置 APK
├── checkout 的 xxhdpi 配置 APK
└── checkout 的中文配置 APK
```

这是当前设备匹配到的一组包，其他 ABI、密度和语言可以对应其他配置包；实际包数取决于模块内容和拆分规则。**一个 Feature 的交付可能同时涉及主体 APK 和多个配置 APK**，不能把“安装一个动态模块”理解成必然只下载一个 APK。[官方 Split APK 说明](https://developer.android.com/guide/app-bundle/app-bundle-format#overview_of_split_apks)

# 用户从 Google Play 下载什么

如果开发者上传的是 AAB，用户首次从 Google Play 安装应用时，下载的通常不只是 Base APK，而是 Google Play 为当前设备选择的一组优化 APK。以下以支持 Split APK 的 Android 5.0（API 21）及以上设备为例，只列出实际存在且匹配的配置包：

```text
首次安装
├── Base APK
├── Base 所需的 ABI、密度和语言 Configuration APK
└── 安装时交付的功能内容
    ├── 保留独立 split 的 install-time Feature APK
    └── 对应 Feature 所需的 Configuration APK

用户触发按需功能后
├── 配置为 on-demand 的 Feature APK
└── 对应 Feature 所需的 Configuration APK
```

Base APK 提供应用核心能力，Configuration APK 补充对应模块在当前设备上需要的资源和 native library。安装时功能内容会一起下发；某些不可移除的安装时模块可能被融合到 Base，因此不一定保留独立 Feature APK。对于支持按需交付的 API 21 及以上设备，配置为 on-demand 的 Dynamic Feature 通常不包含在首次安装中，而是在应用通过 `SplitInstallManager` 请求后，连同所需配置包一起下载。

Google Play 会把这些 APK 交给系统作为同一个应用统一安装，用户在商店界面中通常不会感知它们是多个文件。直接分发 Universal APK 时，通常交付一个包含所支持设备配置内容的 APK；AAB 也可以为不支持 split 的旧设备生成单 APK，是否包含某个功能取决于相应的融合规则。

# AAR

AAR 是 Android Library 的构建产物，可以包含代码、资源和 Manifest，但不能独立安装。构建应用时，AAR 内容会被合并进应用 APK 或 AAB。

普通 Android Library 主要解决源码和依赖模块化；Dynamic Feature 除了模块化，还会在 AAB 中保留独立的功能交付边界。

# 与 Dynamic Feature 的关系

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
