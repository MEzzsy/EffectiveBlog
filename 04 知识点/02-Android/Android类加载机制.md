# Android类加载机制

https://www.jianshu.com/p/7193600024e7

https://www.cnblogs.com/NeilZhang/p/8467721.html

https://www.jianshu.com/p/a620e368389a (good)

https://juejin.im/post/5a0ad2b551882531ba1077a2（good）

Java中的ClassLoader是加载class文件，而Android中的虚拟机无论是dvm还是art都只能识别dex文件。因此Java中的ClassLoader在Android中不适用。Android中的`java.lang.ClassLoader`这个类也不同于Java中的`java.lang.ClassLoader`。

Android平台上虚拟机运行的是Dex字节码，一种对class文件优化的产物，传统Class文件是一个Java源码文件会生成一个.class文件，而Android是把所有Class文件进行合并，优化，然后生成一个最终的class.dex，目的是把不同class文件重复的东西只需保留一份，如果我们的Android应用不进行分dex处理，最后一个应用的apk只会有一个dex文件。 

和java虚拟机中不同的是BootClassLoader是ClassLoader内部类，由java代码实现而不是c++实现，是Android平台上所有ClassLoader的最终parent，这个内部类是包内可见，所以我们没法使用。

- PathClassLoader是用来加载Android系统类和应用的类。PathClassLoader是用来加载Android系统类和应用的类，并且不建议开发者使用。 
- DexClassLoader支持加载APK、DEX和JAR，也可以从SD卡进行加载。

![classloader](http://111.230.96.19:8081/image/classloader.png)

PathClassLoader用来操作本地文件系统中的文件和目录的集合。并不会加载来源于网络中的类。Android采用这个类加载器一般是用于加载系统类和它自己的应用类。这个应用类放置在data/data/包名下。 

DexClassLoader可以加载一个未安装的APK，也可以加载其它包含dex文件的JAR/ZIP类型的文件。DexClassLoader需要一个对应用私有且可读写的文件夹来缓存优化后的class文件。而且一定要注意不要把优化后的文件存放到外部存储上，避免使自己的应用遭受代码注入攻击。

> Android中具体负责类加载的并不是哪个ClassLoader，而是通过DexFile的defineClassNative()方法来加载的。 

通过观察PathClassLoader与DexClassLoader的源码我们就可以确定，真正有意义的处理逻辑肯定在BaseDexClassLoader中 。

```java
public class BaseDexClassLoader extends ClassLoader {
    ...
    public BaseDexClassLoader(String dexPath， File optimizedDirectory， String libraryPath， ClassLoader parent){
        super(parent);
        this.pathList = new DexPathList(this， dexPath， libraryPath， optimizedDirectory);
    }
    ...
}
```

- dexPath：要加载的程序文件（一般是dex文件，也可以是jar/apk/zip文件）所在目录。
- optimizedDirectory：dex文件的输出目录（因为在加载jar/apk/zip等压缩格式的程序文件时会解压出其中的dex文件，该目录就是专门用于存放这些被解压出来的dex文件的）。
- libraryPath：加载程序文件时需要用到的库路径。
- parent：父加载器

> 上面说到的"程序文件"这个概念是我自己定义的，因为从一个完整App的角度来说，程序文件指定的就是apk包中的classes.dex文件；但从热修复的角度来看，程序文件指的是补丁。 

DexPathList的构造函数是将一个个的程序文件（可能是dex、apk、jar、zip）封装成一个个Element对象，最后添加到Element集合中。 

结合DexPathList的构造函数，其实DexPathList的findClass()方法很简单，就只是对Element数组进行遍历，一旦找到类名与name相同的类时，就直接返回这个class，找不到则返回null。 

> 为什么是调用DexFile的loadClassBinaryName()方法来加载class？这是因为一个Element对象对应一个dex文件，而一个dex文件则包含多个class。也就是说Element数组中存放的是一个个的dex文件，而不是class文件！！！这可以从Element这个类的源码和dex文件的内部结构看出。

数组的遍历是有序的，假设有两个dex文件存放了二进制名称相同的Class，类加载器肯定就会加载在放在数组前面的dex文件中的Class。现在很多热修复技术就是把修复的dex文件放在DexPathList中Element[]数组的前面，这样就实现了修复后的Class抢先加载了，达到了修改bug的目的。

> 热修复基本原理

## 个人总结

BaseDexClassLoader中有个pathList对象，pathList中包含一个DexFile的数组dexElements ，dexPath传入的原始dex(.apk，.zip，.jar等)文件在optimizedDirectory文件夹中生成相应的优化后的odex文件，dexElements数组就是这些odex文件的集合，对于类加载呢，就是遍历这个集合。

## 插件化

插件化技术也叫动态加载技术。需要解决三个基础性问题：资源访问、Activity生命周期的管理和ClassLoader。

宿主：指普通的APK。

插件：指经过处理的dex或者apk。

### hook机制

hook，又叫钩子，通常是指对一些方法进行拦截。这样当这些方法被调用时，也能够执行我们自己的代码，这也是面向切面编程的思想（AOP）

android中，本身并不提供这样的拦截机制，但是有时候，我们可以在一些特殊的场合实现一种的Hook方法。

大致思路：

1. 找到需要Hook方法的系统类

2. 利用代理模式来代理系统类的运行拦截我们需要拦截的方法

3. 使用反射的方法把这个系统类替换成你的代理类

### 热修复

| 平台       | HotFix阿里 | AndFix阿里 | Tinker腾讯 | Qzone腾讯 | Robust美团 |
| ---------- | ---------- | ---------- | ---------- | --------- | ---------- |
| 即时生效   | 是         | 是         | 否         | 否        | 是         |
| 性能消耗   | 较小       | 较小       | 较大       | 较大      | 较小       |
| 侵入式打包 | 否         | 否         | 是         | 是        | 是         |
| Rom体积    | 较小       | 较小       | 较大       | 较小      | 较小       |
| 接入复杂度 | 傻瓜式     | 简单       | 复杂       | 简单      | 复杂       |
| 补丁大小   | 较小       | 较小       | 较小       | 较大      | 一般       |
| 全平台支持 | 是         | 是         | 是         | 是        | 是         |
| 类替换     | 是         | 是         | 是         | 是        | 否         |
| so替换     | 是         | 否         | 是         | 否        | 否         |
| 资源替换   | 是         | 否         | 是         | 是        | 否         |

目前较火的热修复方案大致分为两派，分别是：

1. 阿里系：DeXposed、andfix：从底层二进制入手（c语言）。
2. 腾讯系：tinker：从java加载机制入手。