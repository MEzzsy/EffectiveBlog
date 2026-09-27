# JavaVM和JNIEnv

-   JavaVM：它代表Java虚拟机。每一个Java进程有一个全局唯一的JavaVM对象。
-   JNIEnv：它是JNI运行环境的含义。每一个Java线程都有一个JNIEnv对象。Java线程在执行JNI相关操作时，都需要利用该线程对应的JNIEnv对象。

JavaVM和JNIEnv是jni.h里定义的数据结构，里边包含的都是函数指针成员变量。所以，这两个数据结构有些类似Java中的interface。不同虚拟机实现都会从它们派生出实际的实现类。

# so打包到apk

在打包与签名阶段，构建工具将 DEX、资源、Manifest、assets 和 so 库等内容组合为 APK。

具体见： [01 Android编译打包流程.md](02 Android编译打包/01 Android编译打包流程.md) 

# 安装apk时的so

安装 APK 时，系统选择匹配设备 ABI 的 so，分两种情况：

- **需要提取**：将 APK 中 `lib/<ABI>/` 下的 so 提取到应用的原生库目录，可通过 `ApplicationInfo.nativeLibraryDir` 获取。
- **不需要提取**（`extractNativeLibs=false`）：so 保留在 APK 内，运行时直接从 APK 加载；要求 so 未压缩并正确对齐。



`android:extractNativeLibs` 控制**安装 APK 时是否提取 so 库**：

- **`true`**：安装时将 so 提取到应用的原生库目录，运行时从该目录加载。
- **`false`**：不提取，运行时直接从 APK 加载；so 必须未压缩且正确对齐，可以减少安装占用空间。

它配置在 Manifest 的 `<application>` 标签上。

> 这里的 so 压缩指 APK 内的 ZIP 压缩。APK 本质上是 ZIP 文件：
>
> - 压缩存储：将 so 压缩后放进 APK，减小 APK 体积，加载前需要解压。
> - 未压缩存储：将 so 原样放进 APK，满足对齐要求时，可以直接映射到内存加载。
>
> 压缩是无损的，解压后的 so 与压缩前相同。

# 加载so库原理

## 🌟加载so库总结

1. **Java 层确定路径**：`System.load` 直接接收绝对路径；`System.loadLibrary` 接收库名，通过 ClassLoader 等机制找到 so 路径。
2. **ART 检查加载记录**：经 `Runtime.doLoad → nativeLoad → Runtime_nativeLoad → JVM_NativeLoad` 进入 `JavaVMExt::LoadNativeLibrary`，检查该路径是否已加载、ClassLoader 是否匹配，以及此前初始化是否成功。
3. **调用动态加载接口**：尚未加载时，ART 调用 `OpenNativeLibrary`。在本文的 Android 8.0 实现中，普通应用通常调用 `android_dlopen_ext`，携带 ClassLoader 对应的链接器命名空间；引导加载上下文则调用 `dlopen`。两者都将实际加载交给动态链接器。
4. **链接器加载 so**：映射 ELF 段、加载依赖库、解析符号并完成重定位，执行原生初始化函数，成功后返回库句柄。
5. **ART 执行 JNI 初始化**：保存句柄，通过符号查找（普通场景使用 `dlsym`）寻找 `JNI_OnLoad`；若存在则调用，并校验其返回的 JNI 版本。`JNI_OnLoad` 可用于动态注册 native 方法等初始化工作。
6. **返回 Java 层**：保存加载结果；正常成功时调用返回，加载或初始化失败时通常抛出 `UnsatisfiedLinkError`。

其中，`dlopen` 是 POSIX 动态加载接口，`dlsym` 用于按名称查找符号，Android 提供 `libdl` 入口；`android_dlopen_ext` 是 Android 扩展的动态加载接口。

## 加载方法

Java 层通过 `System.load` 或 `System.loadLibrary` 发起 so 加载，由 ClassLoader 提供加载上下文，ART 管理加载记录，再交给动态链接器完成实际加载。

```java
public final class System {
    //... 
    @CallerSensitive
    public static void load(String filename) {
        Runtime.getRuntime().load0(VMStack.getStackClass1(), filename);
    }

    @CallerSensitive
    public static void loadLibrary(String libname) {
        Runtime.getRuntime().loadLibrary0(VMStack.getCallingClassLoader(), libname);
    }
    //。。。
}
```

这里通过 `VMStack` 获取调用者的类或 ClassLoader，使库与正确的加载上下文关联。

| 方法 | 传入参数 | 示例 |
| --- | --- | --- |
| `System.load` | 目标 so 的绝对路径 | `System.load(new File(context.getFilesDir(), "libxxx.so").getAbsolutePath())`，前提是文件已存在且可加载 |
| `System.loadLibrary` | 不带 `lib` 前缀和 `.so` 后缀的库名 | `System.loadLibrary("xxx")`，通常查找 `libxxx.so` |

`loadLibrary` 根据 ClassLoader 的原生库搜索路径定位目标，不固定从 `/data/data/包名/lib` 加载。目标可以是安装时提取出的 so，也可以是 APK 内未压缩且正确对齐的 so；

这两个方法触发加载，不会自动用新文件替换进程中已经加载的库；同一路径的成功加载记录通常会被复用。

## System的load方法

```java
public final class System {
    @CallerSensitive
    public static void load(String filename) {
        Runtime.getRuntime().load0(VMStack.getStackClass1(), filename);
    }
}
```

`Runtime.getRuntime()` 获取当前进程的 `Runtime` 实例，随后调用 `load0`。该方法检查绝对路径，并将路径和调用者的 ClassLoader 交给 `doLoad`。源码见 [Runtime.java](https://android.googlesource.com/platform/libcore/+/refs/tags/android-8.0.0_r1/ojluni/src/main/java/java/lang/Runtime.java)：

```java
synchronized void load0(Class<?> fromClass, String filename) {
     if (!(new File(filename).isAbsolute())) {
          throw new UnsatisfiedLinkError("Expecting an absolute path of the library: " + filename);
     }

    if (filename == null) {
          throw new NullPointerException("filename == null");
    }
    String error = doLoad(filename, fromClass.getClassLoader());
    if (error != null) {
        throw new UnsatisfiedLinkError(error);
    }
}
```

```java
private String doLoad(String name, ClassLoader loader) {
        String librarySearchPath = null;
        if (loader != null && loader instanceof BaseDexClassLoader) {
                BaseDexClassLoader dexClassLoader = (BaseDexClassLoader) loader;
                librarySearchPath = dexClassLoader.getLdLibraryPath();
        }
        synchronized (this) {
                return nativeLoad(name, loader, librarySearchPath);
        }
}
```

`doLoad` 最终调用 native 方法 `nativeLoad`。这里的 `name` 已经是目标路径；`librarySearchPath` 是从 `BaseDexClassLoader` 获取的搜索路径，传给原生加载层使用，影响库的加载环境及其依赖解析。

## System的loadLibrary方法

```java
public final class System {
      @CallerSensitive
    public static void loadLibrary(String libname) {
        Runtime.getRuntime().loadLibrary0(VMStack.getCallingClassLoader(), libname);
    }
}
```

```java
synchronized void loadLibrary0(ClassLoader loader, String libname) {
    if (libname.indexOf((int)File.separatorChar) != -1) {
        throw new UnsatisfiedLinkError("Directory separator should not appear in library name: " + libname);
    }
    String libraryName = libname;
    if (loader != null) {
        String filename = loader.findLibrary(libraryName);//注释1
        if (filename == null) {
            throw new UnsatisfiedLinkError(loader + " couldn't find \"" + System.mapLibraryName(libraryName) + "\"");
        }
        String error = doLoad(filename, loader);//注释2
        if (error != null) {
            throw new UnsatisfiedLinkError(error);
        }
        return;
    }

    String filename = System.mapLibraryName(libraryName);
    List<String> candidates = new ArrayList<String>();
    String lastError = null;
    for (String directory : getLibPaths()) {//注释3
        String candidate = directory + filename;//注释4
        candidates.add(candidate);

        if (IoUtils.canOpenReadOnly(candidate)) {
            String error = doLoad(candidate, loader);//注释5
            if (error == null) {
                return; 
            }
            lastError = error;
        }
    }

    if (lastError != null) {
        throw new UnsatisfiedLinkError(lastError);
    }
    throw new UnsatisfiedLinkError("Library " + libraryName + " not found; tried " + candidates);
}
```

该版本的 `loadLibrary0` 分为两条分支：

- **ClassLoader 不为 `null`**：普通应用通常走此分支。在注释1处调用 `loader.findLibrary` 获取目标路径，再在注释2处传给 `doLoad`；找不到时抛出 `UnsatisfiedLinkError`。
- **ClassLoader 为 `null`**：例如调用者由引导类加载器加载，或附加的原生线程没有相应 Java 调用者时，`VMStack.getCallingClassLoader()` 可以返回 `null`。该分支先用 `System.mapLibraryName` 将 `xxx` 映射为 `libxxx.so`，再遍历 `java.library.path` 指定的目录，拼接候选路径并尝试加载。参考：[VMStack 实现](https://android.googlesource.com/platform/art/+/refs/tags/android-8.0.0_r1/runtime/native/dalvik_system_VMStack.cc)。

应用常用的 `BaseDexClassLoader.findLibrary` 会委托给 `DexPathList.findLibrary`，后者将库名映射为文件名，然后遍历 `nativeLibraryPathElements`。搜索项既可以是文件系统目录，也可以是 APK 内的目录，因此返回值可能是独立 so 路径，也可能是 `安装目录/base.apk!/lib/arm64-v8a/libxxx.so` 这样的 APK 内路径。APK 内的库需要满足未压缩和对齐要求。参考：[BaseDexClassLoader.java](https://android.googlesource.com/platform/libcore/+/refs/tags/android-8.0.0_r1/dalvik/src/main/java/dalvik/system/BaseDexClassLoader.java)、[DexPathList.java](https://android.googlesource.com/platform/libcore/+/refs/tags/android-8.0.0_r1/dalvik/src/main/java/dalvik/system/DexPathList.java)。

`findLibrary` 负责定位库，实际加载发生在后续原生层。`System.load` 和 `System.loadLibrary` 最终都会经 `doLoad` 调用 `nativeLoad`：

```java
private static native String nativeLoad(String filename, ClassLoader loader,
                                        String librarySearchPath);
```

## nativeLoad方法分析

`nativeLoad` 通过 JNI 注册到 [Runtime.c 中的 Runtime_nativeLoad](https://android.googlesource.com/platform/libcore/+/refs/tags/android-8.0.0_r1/ojluni/src/main/native/Runtime.c)：

```c
JNIEXPORT jstring JNICALL
Runtime_nativeLoad(JNIEnv* env, jclass ignored, jstring javaFilename,
                   jobject javaLoader, jstring javaLibrarySearchPath)
{
    return JVM_NativeLoad(env, javaFilename, javaLoader, javaLibrarySearchPath);
}
```

`Runtime_nativeLoad` 调用 [OpenjdkJvm.cc 中的 JVM_NativeLoad](https://android.googlesource.com/platform/art/+/refs/tags/android-8.0.0_r1/runtime/openjdkjvm/OpenjdkJvm.cc)：

```cpp
JNIEXPORT jstring JVM_NativeLoad(JNIEnv* env,
                                 jstring javaFilename,
                                 jobject javaLoader,
                                 jstring javaLibrarySearchPath) {
  // 将 Java 路径字符串转换为原生层可访问的 UTF 字符串
  ScopedUtfChars filename(env, javaFilename);
  if (filename.c_str() == NULL) {
    return NULL;
  }

  std::string error_msg;
  {
    //获取当前运行时的虚拟机，JavaVMExt用于代表一个虚拟机实例
    art::JavaVMExt* vm = art::Runtime::Current()->GetJavaVM();
    //虚拟机加载so
    bool success = vm->LoadNativeLibrary(env,
                                         filename.c_str(),
                                         javaLoader,
                                         javaLibrarySearchPath,
                                         &error_msg);
    if (success) {
      return nullptr;
    }
  }

  // Don't let a pending exception from JNI_OnLoad cause a CheckJNI issue with NewStringUTF.
  env->ExceptionClear();
  return env->NewStringUTF(error_msg.c_str());
}
```

## LoadNativeLibrary分析

`JavaVMExt::LoadNativeLibrary` 成功时返回 `true`，失败时返回 `false`，并通过 `error_msg` 提供错误原因。上一层 `JVM_NativeLoad` 在正常成功时返回 `null`，加载失败时将错误信息转换为 Java 字符串；`Runtime` 再将该错误字符串转换为 `UnsatisfiedLinkError`。字符串转换等 JNI 操作本身也可能产生异常。

源码见 [java_vm_ext.cc 中的 LoadNativeLibrary](https://android.googlesource.com/platform/art/+/refs/tags/android-8.0.0_r1/runtime/java_vm_ext.cc)。下面分段展示关键逻辑，各片段中的省略部分仍属于同一个函数。

```cpp
bool JavaVMExt::LoadNativeLibrary(JNIEnv* env,
                                  const std::string& path,
                                  jobject class_loader,
                                  jstring library_path,
                                  std::string* error_msg);
```

`path`：目标库的路径，由 `System.load` 的参数或 `findLibrary` 等查找结果传入，通常包含路径和 `libxxx.so` 文件名，也可以是 APK 内路径。它与 Java 层 `System.loadLibrary("xxx")` 传入的简短库名不同。

`class_loader`：发起加载的 ClassLoader 上下文；引导类加载器在原生层可用 `null` 表示。同一 JNI 库不能同时归属于不同 ClassLoader。

`library_path`：来自 ClassLoader 的原生库搜索路径。`libnativeloader` 在需要创建 linker namespace（链接器命名空间）时使用它，影响依赖库的查找；目标库本身已经由 `path` 指定。

### 检查加载记录

该版本先按 `path` 查找已有记录，再检查 ClassLoader 是否一致以及初始化是否成功。`CheckOnLoadResult` 必要时会等待其他线程完成 `JNI_OnLoad`。这里的 ART 记录以路径字符串为键，不能简单理解为只按 so 文件名去重。

```cpp
bool JavaVMExt::LoadNativeLibrary(JNIEnv* env,
                                  const std::string& path,
                                  jobject class_loader,
                                  jstring library_path,
                                  std::string* error_msg) {
  error_msg->clear();
  SharedLibrary* library;
  Thread* self = Thread::Current();
  {
    MutexLock mu(self, *Locks::jni_libraries_lock_);
    library = libraries_->Get(path); // 按目标路径查询加载记录
  }
  // 省略 ClassLoader 规范化及 class_loader_allocator 的获取
  if (library != nullptr) {//如果满足此处的条件就说明此前加载过该so
    
    if (library->GetClassLoaderAllocator() != class_loader_allocator) {//如果此前加载用的ClassLoader和当前传入的ClassLoader不相同的话，就会返回false
      
      StringAppendF(error_msg, "Shared library \"%s\" already opened by ClassLoader %p; can't open in ClassLoader %p", path.c_str(), library->GetClassLoader(), class_loader);
      LOG(WARNING) << error_msg;
      return false;
    }
    //。。。
    
    if (!library->CheckOnLoadResult()) { // 必要时等待初始化完成，若此前初始化失败则返回 false
      StringAppendF(error_msg, "JNI_OnLoad failed on a previous attempt to load \"%s\"", path.c_str());
      return false;
    }
    
    //以上条件满足，则不再重复加载so。
    return true;
  }
	//...
}
```

### 打开动态库并记录句柄

`OpenNativeLibrary` 位于 [libnativeloader/native_loader.cpp](https://android.googlesource.com/platform/system/core/+/refs/tags/android-8.0.0_r1/libnativeloader/native_loader.cpp)。普通 Android 应用通常通过 ClassLoader 对应的 linker namespace 调用 `android_dlopen_ext`；引导加载上下文可直接调用 `dlopen`，Native Bridge 场景则走相应桥接接口。命名空间用于控制库的搜索范围和可见性。

动态链接器负责映射 ELF 段、加载依赖、解析符号和重定位，并执行原生初始化函数，然后返回句柄。这些原生初始化函数与后续 ART 调用的 `JNI_OnLoad` 是不同步骤。参考：[Bionic linker.cpp](https://android.googlesource.com/platform/bionic/+/refs/tags/android-8.0.0_r1/linker/linker.cpp)。

```cpp
bool JavaVMExt::LoadNativeLibrary(JNIEnv* env,
                                  const std::string& path,
                                  jobject class_loader,
                                  jstring library_path,
                                  std::string* error_msg) {
  //。。。
  Locks::mutator_lock_->AssertNotHeld(self);
  const char* path_str = path.empty() ? nullptr : path.c_str();
  bool needs_native_bridge = false;
  
  // 在对应的原生库加载上下文中打开目标路径，获取动态库句柄
  void* handle = android::OpenNativeLibrary(env,
                                            runtime_->GetTargetSdkVersion(),
                                            path_str,
                                            class_loader,
                                            library_path,
                                            &needs_native_bridge,
                                            error_msg);
	//。。。
  if (handle == nullptr) {//如果获取so句柄失败就会返回false，中断so加载。
    VLOG(jni) << "dlopen(\"" << path << "\", RTLD_NOW) failed: " << *error_msg;
    return false;
  }

  if (env->ExceptionCheck() == JNI_TRUE) {
    LOG(ERROR) << "Unexpected exception:";
    env->ExceptionDescribe();
    env->ExceptionClear();
  }
  bool created_library = false;
  {
    //新创建SharedLibrary, 并将so句柄作为参数传入进去。
    std::unique_ptr<SharedLibrary> new_library(
        new SharedLibrary(env,
                          self,
                          path,
                          handle,
                          needs_native_bridge,
                          class_loader,
                          class_loader_allocator));

    MutexLock mu(self, *Locks::jni_libraries_lock_);
    library = libraries_->Get(path);
    if (library == nullptr) {
      library = new_library.release();
      libraries_->Put(path, library);
      created_library = true;
    }
  }
  if (!created_library) {
    // 其他线程已建立记录，复用并检查其初始化结果
    return library->CheckOnLoadResult();
  }
  // 后续查找并调用 JNI_OnLoad，见下一段
}
```

### 查找并调用 JNI_OnLoad

`JNI_OnLoad` 是可选的 JNI 初始化回调，可用于动态注册 native 方法、缓存类引用等，不只用于动态注册。库未导出它时也可以加载成功；这不保证之后调用的每个 native 方法都能找到对应实现。

找到该函数后，ART 设置 ClassLoader 上下文并调用它，使其中的 `FindClass` 能使用加载该库的 ClassLoader。调用完成后恢复原上下文，并检查返回的 JNI 版本：`JNI_ERR` 或不支持的版本表示初始化失败。参考：[Android JNI 库加载说明](https://developer.android.com/ndk/guides/jni-tips#native-libraries)。

```cpp
bool JavaVMExt::LoadNativeLibrary(JNIEnv* env,
                                  const std::string& path,
                                  jobject class_loader,
                                  jstring library_path,
                                  std::string* error_msg) {
  //。。。
  
  bool was_successful = false;
  void* sym = library->FindSymbol("JNI_OnLoad", nullptr); // 查找可选的 JNI 初始化回调
  if (sym == nullptr) { // 未导出该回调也可加载成功
    
    VLOG(jni) << "[No JNI_OnLoad found in \"" << path << "\"]";
    was_successful = true;
  } else {
    ScopedLocalRef<jobject> old_class_loader(env, env->NewLocalRef(self->GetClassLoaderOverride()));
    self->SetClassLoaderOverride(class_loader);
    VLOG(jni) << "[Calling JNI_OnLoad in \"" << path << "\"]";
    typedef int (*JNI_OnLoadFn)(JavaVM*, void*);
    JNI_OnLoadFn jni_on_load = reinterpret_cast<JNI_OnLoadFn>(sym);
    int version = (*jni_on_load)(this, nullptr); // 调用回调并获取 JNI 版本

    // 省略旧 targetSdk 的信号处理兼容逻辑
    self->SetClassLoaderOverride(old_class_loader.get());

    if (version == JNI_ERR) {//如果version为JNI_ERR或者Bad JNI version，说明没有执行成功，was_successful的值仍旧为默认的false，否则就将was_successful赋值为true，最终会返回该was_successful。
      
      StringAppendF(error_msg, "JNI_ERR returned from JNI_OnLoad in \"%s\"", path.c_str());
    } else if (JavaVMExt::IsBadJniVersion(version)) {
      StringAppendF(error_msg, "Bad JNI version returned from JNI_OnLoad in \"%s\": %d", path.c_str(), version);
    } else {
      was_successful = true;
    }
    VLOG(jni) << "[Returned " << (was_successful ? "successfully" : "failure") << " from JNI_OnLoad in \"" << path << "\"]";
  }

  library->SetResult(was_successful);
  return was_successful;
}
```

### 小结

`LoadNativeLibrary` 主要完成以下工作：

1. 按路径检查加载记录，并校验 ClassLoader 和此前的初始化结果。
2. 委托原生加载层打开库，获取句柄并建立 `SharedLibrary` 记录，处理并发加载。
3. 调用可选的 `JNI_OnLoad`，检查其返回值，保存并返回初始化结果。

# Native方法调用

**Native 方法调用，就是 ART 通过 JNI，执行 so 中对应的 C/C++ 函数。**

普通 JNI 调用可以分为四步：

1. **找到函数**：静态注册按 JNI 命名规则查找；动态注册通过 `RegisterNatives` 提前建立方法与函数指针的映射。
2. **准备参数**：除 Java 方法参数外，还传入当前线程的 `JNIEnv*`，以及实例对象 `jobject`（静态方法则是 `jclass`）。
3. **执行函数**：通过函数指针，在当前线程进入 C/C++ 代码执行，不会自动创建新线程。
4. **返回 Java**：传回结果，清理本次调用的局部引用，并将待处理的 Java 异常交回 Java 层。

调用链可概括为：`Java native 方法 → JNI 调用桥接 → C/C++ 函数 → 返回 Java`。

# Native方法注册

## 静态注册

静态注册就是常见的写法，根据包名+类名+方法名寻找对应的函数，如创建项目初始生成的代码：

```cpp
public class MainActivity extends AppCompatActivity {
    static {
        System.loadLibrary("native-lib");
    }
    //...
    public native String stringFromJNI();
}
#include <jni.h>
#include <string>

extern "C" JNIEXPORT jstring JNICALL
Java_com_mezzsy_myapplication_MainActivity_stringFromJNI(
        JNIEnv* env,
        jobject /* this */) {
    std::string hello = "Hello from C++";
    return env->NewStringUTF(hello.c_str());
}
```

首先JNI函数名的格式是Java+包名+类名+方法名，如果Java的方法名存在"_"那么对应JNI方法名会多一个1，可以理解为转义。

在Java中调用native方法时，就会从JNI中寻找对应函数，如果没有就会报错，如果找到就会建立关联，其实是保存JNI的函数指针，这样再次调用native方法时直接使用这个函数指针就可以了。静态注册就是根据方法名，将Java方法和JNI函数建立关联，但是它有一些缺点：

-   JNI层的函数名称过长。
-   声明Native方法的类需要用javah生成头文件。
-   初次调用Native方法时需要建立关联，影响效率。

## 动态注册

```
jint JNI_OnLoad(JavaVM *vm, void *) {
    LOGI("JNI_OnLoad");
    return JNI_VERSION_1_6;
}
```

当Java层通过System.loadLibrary加载完JNI动态库后，紧接着会查找该库中一个叫JNI_OnLoad的函数。如果有，就调用它，而动态注册的工作就是在这里完成的。

动态注册的主要原理就是利用JNIEnv的RegisterNatives函数。

# JNI引用

甲骨文的文档：https://docs.oracle.com/javase/8/docs/technotes/guides/jni/spec/design.html#implementing_local_references

JNI规范中定义了三种引用：

1.  全局引用（Global reference）
    生存期为创建之后，直到显式的释放。
2.  局部引用（Local reference）
    生存期为创建后，直到显式的释放，或在当前上下文（可以理解成Java程序调用Native代码的过程）结束之后没有被JVM发现有JAVA层引用而被JVM回收并释放。
3.  弱全局引用（Weak global reference）
    生存期为创建之后，到显式的释放，或JVM认为应该回收它的时候（比如内存紧张的时候）进行回收而被释放。

### 局部引用

Java对象传入JNI函数时，会创建一个局部引用引用这个对象，所以这个对象暂时不会被回收。

在JNI函数返回时，局部引用会被回收。（来自官方文档）

>   如果JNI函数返回了一个局部引用，该引用是怎样被回收的？
>
>   zzsy：该问题目前个人理解是这样的：
>
>   ```cpp
>   extern "C"
>   JNIEXPORT jobject JNICALL
>   Java_com_mezzsy_myapplication_MainActivity_getNativeObj(JNIEnv *env, jobject thiz) {
>      return thiz;
>   }
>   ```
>
>   上面这段代码，多次调用，Java层拿到的都是同一个对象，而打印jobject的地址（强转为long long）是不同的。这说明同一个jobj虽然是指针，但是它并没有指向对应的对象，jobj引用指向的是句柄，而句柄才指向具体的对象。
>
>   所以当JNI函数返回时，局部引用也会被回收，Java层拿到的是具体对象，此时已经无关JNI层的引用了。

局部引用在Native代码显式释放非常重要。既然Java虚拟机会自动释放局部变量为什么还需要在Native代码中显示释放呢？原因有以下几点：

1.  Java虚拟机默认为Native引用分配的局部引用数量是有限的，大部分的Java虚拟机实现默认分配16个局部引用。当然Java虚拟机也提供API（[PushLocalFrame](http://download.oracle.com/javase/1.5.0/docs/guide/jni/spec/functions.html#push_local_frame)，[EnsureLocalCapacity](http://download.oracle.com/javase/1.5.0/docs/guide/jni/spec/functions.html#ensure_local_capacity)）让你申请更多的局部引用数量（Java虚拟机不保证你一定能申请到）。JNI编程中，实现Native代码时强烈建议调用 [PushLocalFrame](http://download.oracle.com/javase/1.5.0/docs/guide/jni/spec/functions.html#push_local_frame) ， [EnsureLocalCapacity](http://download.oracle.com/javase/1.5.0/docs/guide/jni/spec/functions.html#ensure_local_capacity) 来确保Java虚拟机为你准备好了局部变量空间。 
2.  如果你实现的Native函数是工具函数，会被频繁的调用。如果你在Native函数中没有显示删除局部引用，那么每次调用该函数Java虚拟机都会创建一个新的局部引用，造成局部引用过多。尤其是该函数在Native代码中被频繁调用，代码的控制权没有交还给Java虚拟机，所以Java虚拟机根本没有机会释放这些局部变量。退一步讲，就算该函数直接返回给Java虚拟机，也不能保证没有问题，我们不能假设Native函数返回Java虚拟机之后，Java虚拟机马上就会回收Native函数中创建的局部引用，依赖于Java虚拟机实现。所以我们在实现Native函数时一定要记着删除不必要的局部引用，否则你的程序就有潜在的风险，不知道什么时候就会爆发。 
3.  如果你Native函数根本就不返回。比如消息循环函数——死循环等待消息，处理消息。如果你不显示删除局部引用，很快将会造成Java虚拟机的局部引用内存溢出。

>   在JNI中显示释放局部引用的函数为 [DeleteLocalRef](http://download.oracle.com/javase/1.5.0/docs/guide/jni/spec/functions.html#DeleteLocalRef)，可以查看手册来了解调用方法。
>
>   在 JDK1.2 中为了方便管理局部引用，引入了三个函数—— [EnsureLocalCapacity](http://download.oracle.com/javase/1.5.0/docs/guide/jni/spec/functions.html#ensure_local_capacity) 、 [PushLocalFrame](http://download.oracle.com/javase/1.5.0/docs/guide/jni/spec/functions.html#push_local_frame) 、 [PopLocalFrame](http://download.oracle.com/javase/1.5.0/docs/guide/jni/spec/functions.html#pop_local_frame) 。这里介绍一下 PushLocalFrame 和 PopLocalFrame 函数。这两个函数是成对使用的，先调用 PushLocalFrame ，然后创建局部引用，并对其进行处理，最后调用 PushLocalFrame 释放局部引用，这时Java虚拟机也可以对其指向的对象进行垃圾回收。 可以用C语言的栈来理解这对JNI API，调用 PushLocalFrame 之后Native代码创建的所有局部引用全部入栈，当调用 PopLocalFrame 之后，入栈的局部引用除了需要返回的局部引用（PushLocalFrame 和 PopLocalFrame 这对函数可以返回一个局部引用给外部）之外，全部出栈，Java虚拟机这时可以释放他们指向的对象 。具体的用法可以参考手册。这两个函数使JNI的局部引用由于和C语言的局部变量用法类似，所以强烈推荐使用。

当创建局部变量之后，Java虚拟机直到Native代码显示调用了 DeleteLocalRef 删除局部引用或从Native返回且没有另外的引用才能对该对象进行回收。Native代码调用 DeleteLocalRef 显示删除局部引用之后，Java虚拟机就可以对局部引用指向的对象垃圾回收了。当Native代码创建了局部引用，但未显示调用DeleteLocalRef删除局部引用，并返回Java虚拟机的话，那么由虚拟机来决定什么时候删除该局部引用，然后对其指向的对象垃圾回收。程序员不能对java虚拟机删除局部引用的时机进行假设。

局部引用仅仅对于java虚拟机当前调用上下文有效，不能够在多次调用上下文中共享局部引用。这句话也可以这样理解： 局部引用只对当前线程有效，多个线程之间不能共享局部引用。局部引用不能用C语言的静态变量或者全局变量来保存，否则第二次调用的时候，将会产生崩溃 。

测试（伪代码）：

```cpp
static jobject save_thiz = NULL;
void XXXX(JNIEnv *env, jobject thiz)
{
		//...
  	save_thiz = thiz;//这种赋值不会增加jobject的引用计数
  	//...
  	return;
}

void use(JNIEnv *env, jobject thiz)
{
    jstring str = static_cast<jstring>(env->GetObjectField(save_thiz, strFieldId));
}
```

程序出现奔溃。

### 全局引用

局部引用大部分是通过JNI API返回而创建的，而全局引用必须要在Native代码中显示的调用JNI API [NewGlobalRef](http://download.oracle.com/javase/1.5.0/docs/guide/jni/spec/functions.html#NewGlobalRef)来创建，创建之后将一直有效，直到显示的调用 [DeleteGlobalRef](http://download.oracle.com/javase/1.5.0/docs/guide/jni/spec/functions.html#DeleteGlobalRef)来删除这个全局引用。请注意 [NewGlobalRef](http://download.oracle.com/javase/1.5.0/docs/guide/jni/spec/functions.html#NewGlobalRef)的第二个参数，既可以用一个局部引用，也可以用全局引用生成一个全局引用，当然也可以用弱全局引用生成一个全局引用，但是这中情况有特殊的用途，后文会介绍。

全局引用 和 局部引用 一样，可以防止其指向的对象被Java虚拟机垃圾回收。与 局部引用 只在当前线程有效不同的是 全局引用 可以在多线程之间共享（如果是多线程编程需要注意同步问题 ）。

### 弱全局引用

弱全局引用 和 全局引用 一样，可以在多个线程之间共享，但是并不强制进行显式的销毁。虽然在我们确定不再需要 弱全局引用 的时候，建议进行显式的销毁（ 调用 [DeleteWeakGlobalRef](http://download.oracle.com/javase/1.5.0/docs/guide/jni/spec/functions.html#DeleteWeakGlobalRef) ）。但是即使我们不显式的销毁 弱全局引用 ，JAVA虚拟机也能在它认为必要的时候自动回收并销毁 弱全局引用 。创建 弱全局引用 请使用[NewWeakGlobalRef](http://download.oracle.com/javase/1.5.0/docs/guide/jni/spec/functions.html#NewWeakGlobalRef) ，显式销毁 弱全局引用 请使用 [DeleteWeakGlobalRef](http://download.oracle.com/javase/1.5.0/docs/guide/jni/spec/functions.html#DeleteWeakGlobalRef) 。

与 全局引用 和 局部引用 能够阻止Java虚拟机垃圾回收其指向的对象不同，弱全局引用指向的对象随时都可以被Java虚拟机垃圾回收，所以使用弱全局变量的时候，要时刻记着：它所指向的对象可能已经被垃圾回收了。 JNI API 提供了引用比较函数 [IsSameObject](http://download.oracle.com/javase/1.5.0/docs/guide/jni/spec/functions.html#wp16514) ，用 弱全局引用 和 NULL 进行比较，如果返回 JNI_TRUE ，则说明弱全局引用指向的对象已经被释放。需要重新初始化弱全局引用。

根据上面的介绍你可能会写出如下的代码：

```cpp
static jobject weak_global_ref = NULL;
if ((*env)->IsSameObject(env, weak_global_ref, NULL) == JNI_TRUE)
{
  /* Init week global referrence again */
  weak_global_ref = NewWeakGlobalRef(...);
}
/* Process weak_global_ref */
```

上面这段代码表面上没有什么错误，但是我们忘了一点儿，Java虚拟机的垃圾回收随时都可能发生。假设如下情形：

1.  通过引用比较函数IsSameObject判断弱全局引用是否有效的时候，返回JNI_FALSE，证明其指向对象有效。
2.  这时Java虚拟机进行了垃圾回收，回收了弱全局引用指向的对象。
3.  这样如果我们后面访问弱全局引用指向的对象，将会引发程序崩溃，因为弱全局引用指向对象已经被Java虚拟机回收了。

根据JNI标准手册《 [Weak Global References](http://docs.oracle.com/javase/1.5.0/docs/guide/jni/spec/functions.html#weak) 》中的介绍，我们可以有这样一个使用弱全局引用的方案。在使用全局引用之前，我们先通过 [NewLocalRef](http://download.oracle.com/javase/1.5.0/docs/guide/jni/spec/functions.html#new_local_ref) 函数创建一个局部引用，然后使用这个局部引用来访问该对象进行处理，当完成处理之后，删除局部引用。局部引用可以阻止Java虚拟机回收其指向的对象，这样可以保证在处理期间弱全局引用和局部引用指向的对象不会被Java虚拟机回收。假如弱全局引用指向对象已经被Java虚拟机回收，则 [NewLocalRef](http://download.oracle.com/javase/1.5.0/docs/guide/jni/spec/functions.html#new_local_ref) 函数将会返回 NULL ，则创建局部引用失败，这个返回值有助于我们判断是否需要重新初始化弱全局引用。

弱全局引用是可以用来缓存jclass对象，但是用全局引用来缓存jclass对象将非常的危险。这里需要简单介绍一下Native的共享库的卸载。当ClassLoader释放完所有的class后，然后ClassLoader会卸载Native的共享库。如果我们用全局引用来缓存jclass对象的话，根据前面对全局引用对Java虚拟机垃圾回收机制的影响，将会阻止Java虚拟机回收该对象。如果我们不显式的释放全局引用（通过 [DeleteGlobalRef](http://download.oracle.com/javase/1.5.0/docs/guide/jni/spec/functions.html#DeleteGlobalRef) ），则Class Loader也将不能释放这个jclass对象，进而造成 ClassLoader 不能卸载Native的共享库（永远无法释放）。如果用弱全局引用来缓存将不会有这个问题，Java虚拟机随时都可以释放它指向的对象。

### 总结

1.  局部引用是Native代码中最常用的引用。大部分局部引用都是通过JNI API返回来创建，也可以通过调用[NewLocalRef](http://download.oracle.com/javase/1.5.0/docs/guide/jni/spec/functions.html#new_local_ref) 来创建。另外强烈建议Native函数返回值为局部引用。局部引用只在当前调用上下文中有效，所以局部引用不能用Native代码中的静态变量和全局变量来保存。另外时刻要记着Java虚拟机局部引用的个数是有限的，编程的时候强烈建议调用 [EnsureLocalCapacity](http://download.oracle.com/javase/1.5.0/docs/guide/jni/spec/functions.html#ensure_local_capacity) ， [PushLocalFrame](http://download.oracle.com/javase/1.5.0/docs/guide/jni/spec/functions.html#push_local_frame) 和 [PopLocalFrame](http://download.oracle.com/javase/1.5.0/docs/guide/jni/spec/functions.html#pop_local_frame) 来确保Native代码能够获得足够的局部引用数量。
2.  全局变量必须要通过 [NewGlobalRef](http://download.oracle.com/javase/1.5.0/docs/guide/jni/spec/functions.html#NewGlobalRef) 创建，通过 [DeleteGlobalRef](http://download.oracle.com/javase/1.5.0/docs/guide/jni/spec/functions.html#DeleteGlobalRef) 删除。主要用来缓存Field ID和Method ID。全局引用可以在多线程之间共享其指向的对象。在C语言中以静态变量和全局变量来保存。
3.  全局引用和局部引用可以阻止Java虚拟机回收其指向的对象。
4.  弱全局引用必须要通过[NewWeakGlobalRef](http://download.oracle.com/javase/1.5.0/docs/guide/jni/spec/functions.html#NewWeakGlobalRef)创建，通过[DeleteWeakGlobalRef](http://download.oracle.com/javase/1.5.0/docs/guide/jni/spec/functions.html#DeleteWeakGlobalRef)销毁。可以在多线程之间共享其指向的对象。在C语言中通过静态变量和全局变量来保持弱全局引用。弱全局引用指向的对象随时都可能会被Java虚拟机回收，所以使用的时候需要时刻注意检查其有效性。弱全局引用经常用来缓存 jclass 对象。
5.  全局引用和弱全局引用可以在多线程中共享其指向对象，但是在多线程编程中需要注意多线程同步。强烈建议在[JNI_OnLoad](http://download.oracle.com/javase/1.5.0/docs/guide/jni/spec/invocation.html#JNI_OnLoad)初始化 全局引用 和 弱全局引用 ，然后在多线程中进行读全局引用和弱全局引用，这样不需要对全局引用和弱全局引用同步（只有读操作不会出现不一致情况）。
