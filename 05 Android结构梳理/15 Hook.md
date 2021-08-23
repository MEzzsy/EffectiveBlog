# Hook技术分类

根据Hook的API语言划分，分为HookJava和HookNative：

-   Hook Java主要通过反射和代理来实现，应用于在SDK开发环境中修改Java代码。
-   Hook Native则应用于在NDK开发环境和系统开发中修改Native代码。

根据Hook的进程划分，分为应用程序进程Hook和全局Hook：

-   应用程序进程Hook只能Hook当前所在的应用程序进程。
-   应用程序进程是Zygote进程fock出来的，如果对Zygote进行Hook，就可以实现Hook系统所有的应用程序进程，这就是全局Hook。

根据Hook的实现方式划分，分为如下两种：

-   通过反射和代理实现，只能HO0K当前的应用程序进程。
-   通过Hook框架来实现，比如Xposed，可以实现全局Hook，但是需要root。

# 代理模式

见[代理模式](../07 设计模式/代理模式.md)

# Hook startActivity方法

见Demo