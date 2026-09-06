# 整体流程

Android 项目通常由 Gradle 和 Android Gradle Plugin（AGP）驱动构建。以生成 APK 为例，主要流程如下：

```text
读取构建配置
    ↓
合并 Manifest、资源和依赖
    ↓
AAPT2 编译并链接资源
    ↓
Kotlin/Java 源码编译为字节码
    ↓
脱糖并转换为 DEX
    ↓
打包 APK
    ↓
对齐、签名
```

# 主要阶段

## 读取构建配置

Gradle 读取 `settings.gradle`、项目与模块的 `build.gradle`，解析插件、依赖、构建类型和产品风味，最终确定要构建的 Variant，例如 `debug` 或 `release`。

## 处理资源与 Manifest

- 合并应用、构建类型、产品风味和依赖库中的 `AndroidManifest.xml`。
- AAPT2 编译 `res` 目录中的资源，再将其链接为资源表，同时生成供代码引用的 `R` 类。
- 收集 `assets`、so 库等无需编译或由其他工具生成的文件。

## 编译业务代码

- Kotlin 编译器和 Java 编译器将源码编译为 JVM 字节码，即 `.class` 文件。
- 注解处理器或 KSP 可能在此阶段生成额外源码。
- Compose 等插件也可能在编译期间改写或生成代码。

## 生成 DEX

D8 会先完成脱糖，将部分较新的 Java 语法或 API 转换为 Android 可执行的形式，再把 `.class` 字节码转换成 `.dex` 文件。

Release 构建通常还会启用 R8，根据规则完成代码压缩、优化和混淆，然后输出 DEX。方法数超过单个 DEX 的限制时，会生成多个 DEX 文件。

## 打包与签名

构建工具将 DEX、资源、Manifest、assets 和 so 库等内容组合为 APK。APK 通常还会经过以下处理：

1. 使用 `zipalign` 按规则对齐文件，减少运行时读取资源的额外开销。
2. 使用调试证书或发布证书签名，保证安装包的来源和完整性。

最终产物一般位于模块的 `build/outputs` 目录中。

# APK 与 AAB 的区别

- APK 是可以直接安装到设备上的应用包。
- AAB 是发布包，按模块保存代码和资源，不能直接安装。Google Play 会根据设备配置从 AAB 生成并签名优化后的 APK。

# Debug 与 Release

- Debug 构建默认使用调试证书签名，通常不启用代码压缩，构建速度更快，便于调试。
- Release 构建使用正式签名配置，通常启用 R8，并需要妥善维护混淆规则和签名文件。

Gradle 会利用任务缓存和增量编译，只重新执行受变更影响的任务，从而缩短后续构建时间。
