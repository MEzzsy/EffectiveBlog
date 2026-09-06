# 介绍

Raphael是西瓜视频基础技术团队开发的一款 native 内存泄漏检测工具。

源码：https://github.com/bytedance/memory-leak-detector

介绍原文：https://mp.weixin.qq.com/s/RF3m9_v5bYTYbwY-d1RloQ

# 总结

1. hook目标函数
   如果是定向so，则通过plt的方式hook，[plt hook原理](./PltHook.md)。
   如果是全局hook，则通过inline hook。inline hook 是在目标函数的头部直接插入跳转指令，其 hook 的是最终的函数实现，不存在增量 so hook 问题，hook 效率高效直接。（原理暂时略过）
2. 获取分配内存处的堆栈
   [基于fp的栈回朔](./基于fp的栈回朔.md)
3. 如何过滤malloc_proxy内部分配的内存？
   如果在malloc_proxy内部创建对象，会重复调用malloc_proxy，导致栈溢出。Raphael的做法是不创建对象，而是在Raphael初始化时创建大量对象，并缓存。在调用malloc_proxy时，使用缓存对象。