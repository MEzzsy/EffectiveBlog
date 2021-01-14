# JNI原理

如果Java要调用native函数，就必须通过一个位于JNI层的动态库来实现。动态库就是运行时加载的库，那么在什么时候以及什么地方加载这个库呢？

答案不固定，原则上是：在调用native函数前，任何时候、任何地方加载都可以。通行的做法是在类的static语句中加载，调用System.loadLibrary方法就可以了。

## Native方法注册

### 静态注册

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

### 动态注册

```
jint JNI_OnLoad(JavaVM *vm, void *) {
    LOGI("JNI_OnLoad");
    return JNI_VERSION_1_6;
}
```

当Java层通过System.loadLibrary加载完JNI动态库后，紧接着会查找该库中一个叫JNI_OnLoad的函数。如果有，就调用它，而动态注册的工作就是在这里完成的。

动态注册的主要原理就是利用JNIEnv的RegisterNatives函数。

## JNI引用

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

