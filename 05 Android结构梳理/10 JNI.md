1.  加载so库原理
2.  native方法调用原理
3.  JNI中的引用

# JavaVM和JNIEnv

-   JavaVM：它代表Java虚拟机。每一个Java进程有一个全局唯一的JavaVM对象。
-   JNIEnv：它是JNI运行环境的含义。每一个Java线程都有一个JNIEnv对象。Java线程在执行JNI相关操作时，都需要利用该线程对应的JNIEnv对象。

JavaVM和JNIEnv是jni.h里定义的数据结构，里边包含的都是函数指针成员变量。所以，这两个数据结构有些类似Java中的interface。不同虚拟机实现都会从它们派生出实际的实现类。

# 加载so库原理

//TODO

1. so库是如何打到apk包的？
2. 安装apk包是如何放置so库的？
3. 打开App是如何读取so库的？

加载so主要用到了System类的load和loadLibarary方法，如下所示：

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

>   上面的代码块中获取调用Class或者ClassLoader，是用VMStack.getStackClass1()和VMStack.getCallingClassLoader()，在其它版本用的是Reflection.getCallerClass()。
>
>   在自己使用Reflection.getCallerClass()方法时遇到了一些问题，然后查了资料，仅作参考：
>
>   **权限**
>
>   Reflection.getCallerClass()的调用者必须有权限，需要什么样的权限呢？
>
>   -   由bootstrap class loader加载的类可以调用
>   -   由extension class loader加载的类可以调用
>   -   都知道用户路径的类加载都是由 application class loader进行加载的，换句话说就是用户自定义的一些类中无法调用此方法
>
>   **作用**
>
>   `Reflection.getCallerClass()`方法调用所在的方法必须用@CallerSensitive进行注解，通过此方法获取class时会跳过链路上所有的有@CallerSensitive注解的方法的类，直到遇到第一个未使用该注解的类，避免了用`Reflection.getCallerClass(int n)` 这个过时方法来自己做判断。
>
>   小结：总而言之，Reflection.getCallerClass()不建议在开发中使用。

System的load方法传入的参数是so在磁盘的完整路径，用于加载指定路径的so。

System的loadLibrary方法传入的参数是so的名称，用于加载App安装后自动从apk包中复制到`/data/data/packagename/lib`下的so。

目前so的修复都是基于这两个方法。

## System的load方法

```java
public final class System {
    @CallerSensitive
    public static void load(String filename) {
        Runtime.getRuntime().load0(VMStack.getStackClass1(), filename);
    }
}
```

Runtime.getRuntime()会得到当前Java应用程序的运行环境Runtime，Runtime的load()方法如下所示：

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

doLoad方法会调用native方法nativeLoad。

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

loadLibrary0方法分为两个部分，一个是传入的ClassLoader不为null的部分，另一个是ClassLoader为null的部分。

先来看ClassLoader 为null 的部分。 在**注释3**处遍历getLibPaths方法，这个方法会返回`java.library.path`选项配置的路径数组。 在**注释4**处拼接出so路径并传入**注释5**处调用的doLoad方法中。（TODO 为什么会有null情况）

当ClassLoader不为null时。 在**注释2**处同样调用了doLoad方法，其中第一个参数是通过**注释1**处的ClassLoader的findLibrary方法来得到的。（具体分析见热修复原理，findLibrary方法内部可实现so库的替换）

System的load方法和loadLibrary方法在Java FrameWork层最终调用的都是nativeLoad方法。

```java
private static native String nativeLoad(String filename, ClassLoader loader,
                                        String librarySearchPath);
```

## nativeLoad方法分析

**Runtime.c#Runtime_nativeLoad**

```c
JNIEXPORT jstring JNICALL
Runtime_nativeLoad(JNIEnv* env, jclass ignored, jstring javaFilename,
                   jobject javaLoader, jstring javaLibrarySearchPath)
{
    return JVM_NativeLoad(env, javaFilename, javaLoader, javaLibrarySearchPath);
}
```

在Runtime_nativeLoad函数中调用了JVM_NativeLoad函数：

```c
JNIEXPORT jstring JVM_NativeLoad(JNIEnv* env,
                                 jstring javaFilename,
                                 jobject javaLoader,
                                 jstring javaLibrarySearchPath) {
  //将so的文件名转换为ScopeUtfChars
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

加载成功会返回true，加载失败返回false，同时JNI返回错误String。

**java_vm_ext.cc#LoadNativeLibrary**

```c
bool JavaVMExt::LoadNativeLibrary(JNIEnv* env,
                                  const std::string& path,
                                  jobject class_loader,
                                  jstring library_path,
                                  std::string* error_msg)
```

path：代表目标动态库的文件名，不包含路径信息。Java层通过`System.loadLibrary`加载动态库时，只需指定动态库的名称(比如libxxx)，不包含路径和后缀名。

class_loader：根据JNI规范，目标动态库必须和一个ClassLoader对象相关联，同一个目标动态库不能由不同的ClassLoader对象加载。

library_path：动态库文件搜索路径。将在这个路径下搜索path对应的动态库文件。

**第一部分**

```c
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
    library = libraries_->Get(path);//根据so的名称从libraries中获取对应的SharedLibrary类型指针library
  }
  //...
  if (library != nullptr) {//如果满足此处的条件就说明此前加载过该so
    
    if (library->GetClassLoaderAllocator() != class_loader_allocator) {//如果此前加载用的ClassLoader和当前传入的ClassLoader不相同的话，就会返回false
      
      StringAppendF(error_msg, "Shared library \"%s\" already opened by ClassLoader %p; can't open in ClassLoader %p", path.c_str(), library->GetClassLoader(), class_loader);
      LOG(WARNING) << error_msg;
      return false;
    }
    //。。。
    
    if (!library->CheckOnLoadResult()) {//判断上次加载so的结果，如果有异常也会返回false，中断so加载。
      StringAppendF(error_msg, "JNI_OnLoad failed on a previous attempt to load \"%s\"", path.c_str());
      return false;
    }
    
    //以上条件满足，则不再重复加载so。
    return true;
  }
	//...
}
```

**第二部分**

```c
bool JavaVMExt::LoadNativeLibrary(JNIEnv* env,
                                  const std::string& path,
                                  jobject class_loader,
                                  jstring library_path,
                                  std::string* error_msg) {
  //。。。
  Locks::mutator_lock_->AssertNotHeld(self);
  const char* path_str = path.empty() ? nullptr : path.c_str();
  bool needs_native_bridge = false;
  
  //加载动态库，打开路径path_str的so库，得到so句柄handle。Linux平台是利用dlopen，但Android系统进行了相关定制，主要是出于安全考虑。如：一个应用不能加载另外一个应用的动态库。
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
    library = libraries_->Get(path);//获取传入path对应的library，如果library为空指针，就将新创建的SharedLibrary赋值给library，并将library存储到libraries中。
    
    //。。。
}
```

**第三部分**

```c
bool JavaVMExt::LoadNativeLibrary(JNIEnv* env,
                                  const std::string& path,
                                  jobject class_loader,
                                  jstring library_path,
                                  std::string* error_msg) {
  //。。。
  
  bool was_successful = false;
  void* sym = library->FindSymbol("JNI_OnLoad", nullptr);//查找JNI_OnLoad函数的指针并赋值给空指针sym，JNI_OnLoad函数用于native方法的动态注册。
  if (sym == nullptr) {//如果没有找到JNI_OnLoad函数就将was_successful赋值为true, 说明已经加载成功。没有找到JNI_OnLoad函数也算加载成功，这是因为并不是所有so都定义了JNI_OnLoad函数，因为native方法除了动态注册，还有静态注册。
    
    VLOG(jni) << "[No JNI_OnLoad found in \"" << path << "\"]";
    was_successful = true;
  } else {
    ScopedLocalRef<jobject> old_class_loader(env, env->NewLocalRef(self->GetClassLoaderOverride()));
    self->SetClassLoaderOverride(class_loader);
    VLOG(jni) << "[Calling JNI_OnLoad in \"" << path << "\"]";
    typedef int (*JNI_OnLoadFn)(JavaVM*, void*);
    JNI_OnLoadFn jni_on_load = reinterpret_cast<JNI_OnLoadFn>(sym);
    int version = (*jni_on_load)(this, nullptr);//如果找到了JNI_OnLoad函数，就在注释3处执行JNI_OnLoad函数并将结果赋值给version。

    //。。。

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

LoadNativeLibrary函数主要做了如下3方面工作。

1. 判断so是否被加载过，两次ClassLoader是否是同一个，避免so重复加载。
2. 打开so并得到so句柄，如果so句柄获取失败，就返回false。创建新的SharedLibrary，如果传入path对应的library为空指针，就将新创建的SharedLibrary赋值给library，并将library存储到libraries中。
3. 查找JNI_OnLoad的函数指针，根据不同情况设置was_successful的值，最终返回该was_successful。

## 加载so库总结

1.  Java层调用System的load或者loadLibrary方法，内部会寻找so文件的路径。
2.  将搜索路径传给JNI函数，函数内部判断so是否被加载过，避免so重复加载。
3.  根据搜索路径，创建SharedLibrary，并存储。
4.  查找JNI_OnLoad的函数指针，如果存在就调用。根据不同情况设置was_successful的值，最终返回该was_successful。

# Native方法调用

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

局部引用在Native代码显式释放非常重要。既然Java虚拟机会自动释放局部变量为什么还需要我在Native代码中显示释放呢？原因有以下几点：

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

# NDK相关错误

编译C++文件时会遇到一个错误：

```
undefined symbol: XXX
```

可能的原因如下：

1.  没有实现cpp

2.  没有导入头文件对应的so文件。

3.  导入的so文件在cmake编译时加入了flag：-fvisibility=hidden，导致函数不可见，在需要的函数头上加上`__attribute__((visibility("default")))`，如：

    ```cpp
    __attribute__((visibility("default"))) int app_main(void)
    ```

# NDK开发工具

## addr2line

在运行时遇到问题，native的奔溃栈和Java的不同，只提供了地址，需要根据地址进行反解。

`addr2line`能够将地址转换为文件名和行号。给定一个可执行文件的地址或者一个可重定位目标的目标偏移，addr2line 就会利用 debug 信息来计算出与该地址关联的文件名和行号。

```
addr2line -f -e xxx.so 123 456 789
```

-   -f表示显示函数名称
-   -e表示输入文件名称
-   xxx.so表示相应的so文件
-   123 456 789表示地址，可以有多个

具体可见-h。

位置在`sdk/ndk/20.0.5594570/toolchains/arm-linux-androideabi-4.9/prebuilt/darwin-x86_64/bin/arm-linux-androideabi-addr2line`

## objdump

objdump 是 gcc 工具，用来查看编译后目标文件的组成。

位置：

-   32位：toolchains/arm-linux-androideabi-4.9/prebuilt/linux-x86_64/bin/arm-linux-androideabi-objdump
-   64位：toolchains/aarch64-linux-android-4.9/prebuilt/linux-x86_64/bin/aarch64-linux-android-objdump

一般使用：

```
arm-linux-androideabi-objdump -d 库文件 > 输出文件
```

