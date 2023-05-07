[官方文档](https://developer.android.com/ndk/guides/asan?hl=zh-cn)https://zhuanlan.zhihu.com/p/109193953)

下面从使用方式解析Asan的原理

# wrap.sh

[封装 Shell 脚本](https://developer.android.com/ndk/guides/wrap-script?hl=zh-cn)

当需要对包含原生代码的应用进行调试和性能剖析时，希望以全新的进程来运行应用，而不是从 zygote 克隆。

只用于启动应用的简单 `wrap.sh` 文件：

```shell
#!/system/bin/sh
exec "$@"
```

## Asan的wrap.sh

```shell
#!/system/bin/sh
HERE="$(cd "$(dirname "$0")" && pwd)"
export ASAN_OPTIONS=log_to_syslog=false,allow_user_segv_handler=1
ASAN_LIB=$(ls $HERE/libclang_rt.asan-*-android.so)
if [ -f "$HERE/libc++_shared.so" ]; then
    # Workaround for https://github.com/android-ndk/ndk/issues/988.
    export LD_PRELOAD="$ASAN_LIB $HERE/libc++_shared.so"
else
    export LD_PRELOAD="$ASAN_LIB"
fi
"$@"
```

## 为什么要以全新的进程来运行应用

Android一般的进程是从zygote fork的，如果在zygote进程设置环境变量然后再启动app，虽然app进程会继承环境变量，但是执行时机已经太晚，因为linker已经执行过了，而且zygote的Java环境都已经准备好还预加载了一些代码和资源，因此后续不会在获取环境变量。

所以要以全新的进程启动，并且在启动前设置环境变量。

[参考](https://sanfengandroid.github.io/2021/01/10/modify-linker-to-implement-plt-hook/)

# so注入(LD_PRELOAD)

## 简单demo

### so1

```cpp
int get_val() {
  return 123;
}
```

很简单，就是返回123。将其编译so并依赖。

### main

```cpp
void testPreLoad() {
  NDK_LOG("testPreLoad val=%d", get_val());
}
```

```
I/NDK_DEMO: testPreLoad val=123
```

### so2

```cpp
int get_val() {
  return 456;
}
```

和so1的区别就是返回456，编译成so，用来注入so库。so2存放的位置没有要求，这里就放进apk中。

### 注入so库

```
#!/system/bin/sh

# so注入部分
HERE="$(cd "$(dirname "$0")" && pwd)"
PRELOAD_LIB=$(ls $HERE/libtest-after-preload.so)
export LD_PRELOAD="$PRELOAD_LIB"

"$@"
```

再次调用testPreLoad函数：

```
I/NDK_DEMO: testPreLoad val=456
```

返回的是456，这样就实现了so注入。

## 总结

上面的demo模仿了asan的配置方式，大致能了解asan实现注入的方式。

## LD_PRELOAD

LD_PRELOAD是linux的系统环境变量，因为android基于linux内核所以此环境变量依然存在。

当linker初始化时会获取首先获取LD_PRELOAD指向的so库然后再获取elf文件的其他依赖库，所以LD_PRELOAD指向的so库是最先加载的。linker在对elf可执行文件进行重定位时会根据so库的加载顺序去寻找导出函数，所以利用LD_PRELOAD加载自定义的so库并实现特定函数可以拦截elf加载的其他库的特定函数的目的。同时也达到了so库注入的目的。

## 参考

https://www.cnblogs.com/revercc/p/16773944.html

https://sanfengandroid.github.io/2021/01/10/modify-linker-to-implement-plt-hook/

# Asan原理

## 参考

[官方](https://github.com/google/sanitizers/wiki/AddressSanitizerAlgorithm)

[博客](https://wwm0609.github.io/2020/04/17/hwasan/)

## 基本原理

1.  程序申请的每8bytes内存映射到1byte的shadow内存上
2.  因为malloc返回的地址都是基于8字节对齐的，所以每8个字节实际可能有以下几个状态
    case 1：8个字节全部可以访问，例如`char* p = new char[8];` 将0写入到这8个字节对应的1个字节的shadow内存；
    case 2：前1<=n<8个字节可以访问, 例如`char* p = new char[n]`, 将数值n写入到相应的1字节的shadow内存，尽管这个对象实际只占用5bytes，malloc的实现里[p+5, p+7]这尾部的3个字节的内存也不会再用于分配其他对象，所以通过指针p来越界访问最后3个字节的内存也是被允许的。
3.  asan还会在程序申请的内存的前后，各增加一个redzone区域（n * 8bytes），用来解决overflow/underflow类问题
4.  free对象时，asan不会立即把这个对象的内存释放掉，而是写入1个负数到该对象的shadown内存中，即将该对象成不可读写的状态， 并将它记录放到一个隔离区(book keeping)中, 这样当有野指针或use-after-free的情况时，就能跟进shadow内存的状态，发现程序的异常；一段时间后如果程序没有异常，就会再释放隔离区中的对象
5.  编译器在对每个变量的load/store操作指令前都插入检查代码，确认是否有overflow、underflow、use-after-free等问题

## 检测堆上变量的非法操作

asan在运行时会替换系统默认的malloc实现，当执行以下代码时，

```c++
void foo() {
  char* ptr = new char[10];
  ptr[1] = 'a';
  ptr[10] = '\n'
}
```

`new`关键字实际最终调用还是malloc函数，而asan提供的malloc实现基本就如下代码片段所示：

```c++
// asan提供的malloc函数
void* asan_malloc(size_t requested_size) {
    size_t actual_size = RED_ZONE_SIZE /*前redzone*/ + align8(requested_size) + RED_ZONE_SIZE/*后redzone*/;
    // 调用libc的malloc去真正的分配内存
    char* p = (char*)libc_malloc(acutal_size);
    // 标记前后redzone区不可读写
    poison(p, requested_size);

    return p + RED_ZONE_SIZE; // 返回偏移后的地址
}

void foo() {
  // 运行时实际执行的代码
  char* ptr = asan_malloc(10);

  // 编译器插入的代码
  if (isPoisoned(ptr+1)) {
    abort();
  }
  ptr[1] = 'a';

  // 编译器插入的代码
  if (isPoisoned(ptr+10)) {
    abort(); // crash： 访问到了redzone区域
  }
  ptr[10] = '\n'
}
```

asan_malloc会额外多申请2个redzone大小的内存, 实际的内存布局如下所示：

```
----------------------------------------------------------------   
|    redzone（前）    |    用户申请的内存      |    redzone(后)    |   
----------------------------------------------------------------
```

用户申请的内存对应的shadow内存会被标记成可读写的，而redzone区域内存对应的shadow内存则会被标记成不可读写的,
这样就可以检测对堆上变量的越界访问类问题了。

## 检测栈上对象的非法操作

对于以下代码片段

```c++
void foo() {
  char a[8];
  
  a[1] = '\0';
  a[8] = '\0'; // 越界

  return;
}
```

编译器则直接在a数组的前后都插入1个redzone，最终的代码会变成下面的方式：

```c++
void foo() {
  char redzone1[32];  // 编译器插入的代码, 32字节对齐
  char a[8];
  char redzone2[24];  // 编译器插入的代码, 与用于申请的数组a一起做32字节对齐
  char redzone3[32];  // 编译器插入的代码, 32字节对齐

  // 编译器插入的代码
  int  *shadow_base = MemToShadow(redzone1);
  shadow_base[0] = 0xffffffff;  // 标记redzone1的32个字节都不可读写
  shadow_base[1] = 0xffffff00;  // 标记数组a的8个字节为可读写的，而redzone2的24个字节均不可读写
  shadow_base[2] = 0xffffffff;  // 标记redzone3的32个字节都不可读写

  // 编译器插入的代码
  if (isPoisoned(a+1)) {
      abort();
  }
  a[1] = '0';

  // 编译器插入的代码
  if (isPoisoned(a+8)) {
      abort(); // crash: 因为a[8]访问到了redzone区
  }
  a[8] = '\0';

  // 整个栈帧都要被回收了，所以要将redzone和数组a对应的内存都标记成可读可写的
  shadow_base[0] = shadow_base[1] = shadow_base[2] = 0;
  return;
}
```

## 程序申请的对象内存和它的shadow内存映射关系

因为asan对**每8bytes**程序内存会保留**1byte**的shadow内存，所以在进程初始化时，asan得预留(`mmap`)1/8的虚拟内存，