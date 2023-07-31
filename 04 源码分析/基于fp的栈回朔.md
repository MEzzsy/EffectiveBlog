# 介绍

这里使用的代码是[Raphael](https://github.com/bytedance/memory-leak-detector)的unwind64。

用 fp 进行栈回溯事情会很轻松。假如在编译的时候启用了 `-fno-omit-frame-pointer` 选项（clang 默认启用这个选项），编译器会把某个特定的寄存器当 fp 寄存器，用来保存当前函数调用栈的起始地址。

按照 ARM 的调用约定，在 fp 寄存器指向的栈空间上紧凑的存着上一层函数的 fp 地址和函数返回地址。

# 获取栈顶和栈底

```c++
// #include <pthread.h>
// st: stack top
// sb: stack bottom
static inline void GetStackRange(uintptr_t *st, uintptr_t *sb) {
  void *address;
  size_t size;

  pthread_attr_t attr;
  pthread_getattr_np(pthread_self(), &attr);
  pthread_attr_getstack(&attr, &address, &size);

  pthread_attr_destroy(&attr);

  *st = (uintptr_t) address + size;
  *sb = (uintptr_t) address;
}
```

通过`pthread_xxx`相关函数计算栈顶和栈底地址。

Raphael的栈顶和栈底表示栈空间的范围，fp地址不能超出这个范围。

# 栈回朔

```c++
static const uintptr_t kFrameSize = 2 * sizeof(uintptr_t);
static inline bool isValid(uintptr_t fp, uintptr_t st, uintptr_t sb) {
  return fp > sb && fp < st - kFrameSize;
}

// 通过__builtin_frame_address的方式来获取栈顶地址
// 它是编译器的内置函数，在编译期间会转换为特定的汇编指令。
// 转换过程如下，对AArch64架构而言，转换的结果就是读取x29的值（x29也即FP寄存器）
auto fp = (uintptr_t) __builtin_frame_address(0);

size_t depth = 0;
uintptr_t pc = 0;
while (isValid(fp, st, sb) && depth < max_depth) {
  uintptr_t tt = *((uintptr_t *) fp + 1);
  uintptr_t pre = *((uintptr_t *) fp);
  if (pre & 0xfu || pre < fp + kFrameSize) {
    break;
  }
  if (tt != pc) {
    stack[depth++] = tt;
  }
  pc = tt;
  sb = fp;
  fp = pre;
}
return depth;
```

这里fp每次+1是因为：栈是向低地址增长的，栈顶地址最小。

# 总结

fp 回溯性能是最好的，只有地址的加减操作。不过它也有些问题，比如在 Arm 32 位上有兼容问题 ，而且不能回溯穿过 JNI 和 OAT （没遵守 fp 的约定）。

from zsy：以上内容待丰富。

以上内容只介绍了64位的fp栈回朔，因为android64位的fp栈回朔兼容性比较好，处理简单。

32位的fp栈回朔处理比较麻烦，要考虑主线程和子线程的区别，栈底地址的获取也不同（见这篇文章https://juejin.cn/post/7028518916355801101）。