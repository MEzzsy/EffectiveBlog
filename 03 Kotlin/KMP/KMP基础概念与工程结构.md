# KMP 核心概念

## 1. 跨平台的本质：共享代码与平台代码分离

KMP 的核心思想是将业务逻辑、数据模型等**平台无关代码**放在共享模块，而将 UI、系统 API 调用等**平台相关代码**放在各平台模块，通过**抽象接口 + 平台实现**的方式关联。

- **共享代码（Common Code）**：用纯 Kotlin 编写，不依赖任何平台特定 API，可被所有平台模块引用。
- **平台代码（Platform Code）**：针对特定平台（如 Android、iOS）编写的代码，可调用平台原生 API（如 Android 的 `Activity`、iOS 的 `UIKit`）。
- **互操作性（Interop）**：KMP 提供与各平台原生代码的交互能力：
  - 与 Java 无缝互操作（Android 天然支持）。
  - 与 Objective-C/Swift 互操作（通过 `expect/actual` 和生成的框架）。
  - 与 JavaScript 互操作（通过 `kotlin.js` 绑定）。



## 2. 关键术语

- **`expect/actual` 机制**：共享代码中用 `expect` 声明抽象接口 / 类 / 函数，各平台模块用 `actual` 提供具体实现（KMP 跨平台的核心机制）。

  ```kotlin
  // 共享代码（commonMain）
  expect fun platformName(): String
  
  // Android 平台（androidMain）
  actual fun platformName() = "Android"
  
  // iOS 平台（iosMain）
  actual fun platformName() = "iOS"
  ```

- **目标平台（Target）**：KMP 支持的输出平台，如 `android`、`iosArm64`、`iosX64`、`jvm（桌面）`、`js（Web）` 等。

- **源集（Source Set）**：按平台或功能划分的代码集合，如 `commonMain`（所有平台共享）、`androidMain`（Android 平台）、`iosMain`（iOS 平台）等。

- **依赖（Dependency）**：共享模块可依赖 Kotlin 标准库或其他 KMP 库；平台模块可额外依赖平台特定库（如 Android 的 `appcompat`）。

#### 3. 适用场景与优势

- **适用场景**：跨平台业务逻辑（如网络请求、数据解析、状态管理）、SDK 开发、工具类库等。
- **不适用场景**：平台特定 UI（需用各平台原生框架，如 Compose for Android、SwiftUI for iOS）。
- **优势**：
  - 减少重复代码，提高开发效率。
  - 统一业务逻辑，避免多平台行为不一致。
  - 复用 Kotlin 语言特性（空安全、协程、数据流等）。



# KMP 工程结构

KMP 工程采用模块化设计，核心是一个**共享模块（Shared Module）** 和多个**平台模块（Platform Modules）**。以下是典型的 KMP 工程结构（以 Android Studio 为例）：

```plaintext
MyKmpProject/
├─ app/                  # 平台应用模块（如 Android 应用）
│  ├─ src/main/          # Android 平台代码
├─ iosApp/               # iOS 应用模块（通常是 Xcode 项目）
├─ shared/               # 共享模块（核心）
│  ├─ build.gradle.kts   # 共享模块配置
│  ├─ src/
│  │  ├─ commonMain/     # 所有平台共享代码
│  │  │  ├─ kotlin/      # Kotlin 源代码
│  │  │  └─ resources/   # 共享资源（如配置文件）
│  │  ├─ commonTest/     # 共享测试代码（跨平台测试）
│  │  ├─ androidMain/    # Android 平台特有代码
│  │  ├─ androidTest/    # Android 平台测试
│  │  ├─ iosMain/        # iOS 平台特有代码
│  │  ├─ iosTest/        # iOS 平台测试
│  │  ├─ jvmMain/        # 桌面（JVM）平台特有代码
│  │  └─ ...（其他平台）
```

## 1. 共享模块（Shared Module）

共享模块是 KMP 的核心，包含所有平台共享的代码和平台特定代码的抽象。其配置文件 `build.gradle.kts` 定义了支持的目标平台和依赖。

**典型配置示例**：

```kotlin
// shared/build.gradle.kts
plugins {
    kotlin("multiplatform") version "1.9.0"
    kotlin("plugin.serialization") version "1.9.0" // 可选：序列化插件
}

kotlin {
    // 1. 声明目标平台
    androidTarget() // Android 平台
    
    ios { // iOS 平台（支持真机和模拟器）
        binaries {
            framework {
                baseName = "Shared" // 生成的 iOS 框架名称
            }
        }
    }
    
    jvm("desktop") { // 桌面（JVM）平台
        compilations.all {
            kotlinOptions.jvmTarget = "11"
        }
    }

    // 2. 配置源集依赖
    sourceSets {
        val commonMain by getting {
            dependencies {
                // 共享依赖（Kotlin 标准库、KMP 库）
                implementation(kotlin("stdlib-common"))
                implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.7.3")
            }
        }
        
        val androidMain by getting {
            dependencies {
                // Android 特有依赖
                implementation("androidx.core:core-ktx:1.10.1")
            }
        }
        
        val iosMain by getting
        
        val desktopMain by getting {
            dependencies {
                // 桌面特有依赖
                implementation("org.jetbrains.kotlinx:kotlinx-coroutines-swing:1.7.3")
            }
        }
        
        // 测试源集
        val commonTest by getting {
            dependencies {
                implementation(kotlin("test-common"))
                implementation(kotlin("test-annotations-common"))
            }
        }
    }
}

// 仅 Android 平台需要的配置
android {
    compileSdk = 33
    sourceSets["main"].manifest.srcFile("src/androidMain/AndroidManifest.xml")
    defaultConfig {
        minSdk = 21
    }
}
```

## 2. 平台模块（Platform Modules）

平台模块是各平台的应用入口，负责调用共享模块的代码并处理平台特定逻辑。

- **Android 模块**：通常是一个标准的 Android 应用模块（`com.android.application`），通过依赖共享模块的 `androidMain` 源集使用共享代码。

  ```kotlin
  // app/build.gradle.kts
  dependencies {
      implementation(project(":shared"))
  }
  ```

- **iOS 模块**：通常是一个 Xcode 项目，通过引入共享模块生成的 `.framework` 文件使用共享代码。在 KMP 配置中，`ios` 目标会自动生成框架，供 Xcode 引用。

- **桌面模块**：可基于 JVM 构建 Swing、JavaFX 或 Compose for Desktop 应用，依赖共享模块的 `jvmMain` 源集。

## 3. 源集（Source Set）的作用

源集是 KMP 组织代码的核心方式，按平台分层管理：

- **`commonMain`**：所有平台共享的代码，是跨平台逻辑的主要存放地。
- **平台源集（如 `androidMain`、`iosMain`）**：平台特定实现，用于补充共享代码中用 `expect` 声明的抽象。
- **测试源集（如 `commonTest`、`androidTest`）**：对应层级的测试代码，`commonTest` 中的测试可在所有平台运行。

# KMP 代码组织原则

1. **优先写在共享模块**：业务逻辑、数据模型、网络 / 数据库接口等尽量放在 `commonMain`，通过 `expect/actual` 抽象平台差异。
2. **最小化平台代码**：平台模块仅包含 UI、系统 API 调用等必须平台特定的代码。
3. **利用 KMP 库**：优先使用支持 KMP 的库（如 `kotlinx-coroutines`、`ktor`、`sqldelight`），避免引入平台绑定的库。
4. **分层设计**：共享模块内部可按层次划分（如 `data`、`domain`、`presentation`），与平台 UI 层分离。