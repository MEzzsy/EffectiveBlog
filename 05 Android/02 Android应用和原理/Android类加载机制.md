# Java中的ClassLoader

## ClassLoader的类型

Java中的类加载器主要有两种类型，即系统类加载器和自定义类加载器。其中系统类加载器包括3种：

1. **Bootstrap ClassLoader(引导类加载器)**
    C/C++代码实现的加载器，用于加载指定的JDK的核心类库，比如`java.lang.` `java.util.`等这些系统类。

2. **Extensions ClassLoader(拓展类加载器)**
    Java中的实现类为ExtClassLoader，它用于加载Java的拓展类，提供除了系统类之外的额外功能。

3. **Application ClassLoader(应用程序类加载器)**
    Java中的实现类为AppClassLoader，主要加载应用程序的class。

4. **Custom ClassLoader(自定义类加载器)**
    除了系统提供的类加载器，还可以自定义类加载器，自定义类加载器通过继承`java.lang.ClassLoader`类的方式来实现自己的类加载器。

## ClassLoader的继承关系

```java
public static void main(String[] args) {
    ClassLoader loader = Main.class.getClassLoader();

    while (loader != null) {
        System.out.println(loader);
        loader = loader.getParent();
    }
}
```

```
sun.misc.Launcher$AppClassLoader@18b4aac2
sun.misc.Launcher$ExtClassLoader@7f31245a
```

AppClassLoader的父类加载器为ExtClassLoader，并不代表AppClassLoader继承自ExtClassLoader，而是以责任链的方式进行组合。

## 双亲委托模式

类加载器查找Class所采用的是双亲委托模式，所谓双亲委托模式就是首先判断该Class是否已经加载，如果没有则不是自身去查找而是委托给父加载器进行查找，这样依次进行递归，直到委托到最顶层的Bootstrap ClassLoader，如果Bootstrap ClassLoader找到了该Class，就会直接返回，如果没找到，则继续依次向下查找，如果还没找到则最后会交由自身去查找。

结合ClassLoader的继承关系，可以得出ClassLoader的父子关系并不是使用继承来实现的，而是使用组合来实现代码复用的。

**采取双亲委托模式主要有如下两点好处：**

-   避免重复加载，如果已经加载过一次Class，就不需要再次加载，而是直接读取已经加载的Class。
-   更加安全，如果不使用双亲委托模式，就可以自定义一个String类来替代系统的String类，这显然会造成安全隐患，采用双亲委托模式会使得系统的String类在Java虚拟机启动时就被加载，也就无法自定义String类来替代系统的String类，除非修改类加载器搜索类的默认算法。
    还有一点，只有两个类名一致并且被同一个类加载器加载的类，Java虚拟机才会认为它们是同一个类。

# Android中的ClassLoader

因为Android中的虚拟机和Java虚拟机不太一样，所以Android的ClassLoader与Java的也有区别。

## ClassLoader的类型

Android也分为系统类加载器和自定义类加载器。其中系统类加载器主要包括BootClassLoader、PathClassLoader和DexClassLoader。

1.  **BootClassLoader**
    Android系统启动时会使用BootClassLoader来预加载常用类，与JDK中的Bootstrap ClassLoader不同，它并不是由C/C++代码实现的，而是由Java实现的，BootClassLoader是ClassLoader的内部类，并继承自ClassLoader。

2.  **DexClassLoader**
    DexClassLoader可以加载dex文件以及包含dex的压缩文件(apk和jar文件)，不管加载哪种文件，最终都要加载dex文件。
    DexClassLoader继承自BaseDexClassLoader，方法都在BaseDexClassLoader中实现。

3. **PathClassLoader**
    Android系统使用PathClassLoader来加载系统类和应用程序的类。PathClassLoader继承自BaseDexClassLoader，也都在BaseDexClassLoader中实现。
    在PathClassLoader的构造方法中没有参数optimizedDirectory，这是因为PathClassLoader已经默认了参数optimizedDirectory的值为`/data/dalvik-cache`，PathClassLoader无法定义解压的dex文件存储路径，因此PathClassLoader通常用来加载已经安装的apk的dex文件(安装的apk的dex文件会存储在`/data/dalvik-cache`中)。

**DexClassLoader和PathClassLoader的区别**

从下面的log中可以看出，Acticity的加载只涉及到了PathClassLoader和BootClassLoader，DexClassLoader是做什么的？

1.  DexClassLoader可以加载jar/apk/dex，可以从SD卡中加载未安装的apk
2.  PathClassLoader只能加载系统中已经安装过的apk

## ClassLoader的继承关系

```java
protected void onCreate(Bundle savedInstanceState) {
    super.onCreate(savedInstanceState);
    setContentView(R.layout.activity_d38);
    ClassLoader classLoader = D38Activity.class.getClassLoader();
    while (classLoader != null) {
        Log.d(TAG, classLoader.toString());
        classLoader = classLoader.getParent();
    }
}
```

```
dalvik.system.PathClassLoader[DexPathList[[zip file "/data/app/com.mezzsy.myapplication-TIh5Su8UFr1OqfYo6W1tyw==/base.apk"],nativeLibraryDirectories=[/data/app/com.mezzsy.myapplication-TIh5Su8UFr1OqfYo6W1tyw==/lib/arm64, /data/app/com.mezzsy.myapplication-TIh5Su8UFr1OqfYo6W1tyw==/base.apk!/lib/arm64-v8a, /system/lib64, /vendor/lib64, /product/lib64]]]
java.lang.BootClassLoader@4abfb82
```

可以看到有两种类加载器：一种是PathClassLoader，另一种是BootClassLoader。

## ClassLoader的加载过程

Android的类加载也遵循双亲委托模型，加载方法为loadClass：

### **ClassLoader#loadClass**

```java
public Class<?> loadClass(String name) throws ClassNotFoundException {
    return loadClass(name, false);
}
```

```java
protected Class<?> loadClass(String name, boolean resolve) throws ClassNotFoundException {
        // 检查类是否加载
        Class<?> c = findLoadedClass(name);
        if (c == null) {
            try {
              	//判断父加载器是否存在，存在就调用父加载器的loadClass，否则就调用findBootstrapClassOrNull方法，这个方法直接返回null。
                if (parent != null) {
                    c = parent.loadClass(name, false);
                } else {
                    c = findBootstrapClassOrNull(name);
                }
            } catch (ClassNotFoundException e) {
            }

          	//如果为null，就表示向上委托的类加载没有完成，就会执行这里的findClass方法。
            if (c == null) {
                // findClass直接抛出异常，此方法需要在子类中进行重写。
                c = findClass(name);
            }
        }
        return c;
}
```

#### **BaseDexClassLoader#findClass**

```java
public class BaseDexClassLoader extends ClassLoader {
    private final DexPathList pathList;

    public BaseDexClassLoader(String dexPath, File optimizedDirectory, String librarySearchPath, ClassLoader parent) {
        super(parent);
        this.pathList = new DexPathList(this, dexPath, librarySearchPath, null);
		//...
    }

    protected Class<?> findClass(String name) throws ClassNotFoundException {
        List<Throwable> suppressedExceptions = new ArrayList<Throwable>();
        Class c = pathList.findClass(name, suppressedExceptions);
        if (c == null) {
            // ...抛出异常
        }
        return c;
    }
}
```

在BaseDexClassLoader构造方法中创建了DexPathList对象，并且任务交给DexPathList的findClass方法。

#### **DexPathList#findClass**

```java
public Class<?> findClass(String name, List<Throwable> suppressed) {
    for (Element element : dexElements) {
        Class<?> clazz = element.findClass(name, definingContext, suppressed);
        if (clazz != null) {
            return clazz;
        }
    }
	// ...
    return null;
}
```

Element是DexPathList的内部类，其封装了DexFile（用于加载Dex文件）

```java
static class Element {
    private final File path;
    private final DexFile dexFile;
    private ClassPathURLStreamHandler urlHandler;
    private boolean initialized;

		//。。。

    public Class<?> findClass(String name, ClassLoader definingContext, List<Throwable> suppressed) {
      	//如果dexFile不为null就调用dexFile的loadClassBinaryName方法
        return dexFile != null ? dexFile.loadClassBinaryName(name, definingContext, suppressed) : null;
    }
}
```

#### **DexFile#loadClassBinaryName**

```java
public Class loadClassBinaryName(String name, ClassLoader loader, List<Throwable> suppressed) {
    return defineClass(name, loader, mCookie, this, suppressed);
}
```

```java
private static Class defineClass(String name, ClassLoader loader, Object cookie, DexFile dexFile, List<Throwable> suppressed) {
    Class result = null;
    try {
      	//这里调用defineClassNative方法来加载dex文件，这是一个native方法
        result = defineClassNative(name, loader, cookie, dexFile);
    } catch {
        // ...
    }
    return result;
}
```

### 小结

Android的ClassLoader也遵循了双亲委托模式，如果类已经加载，那么直接返回，如果没有加载，交给父加载器加载。重复此过程一直到加载完成，如果还没有加载完成，那么抛出ClassNotFoundException异常。

## BootClassLoader的创建

BootClassLoader是在ZygoteInit入口方法中被创建的，用于加载preloaded-classes文件中存有的预加载类。

## PathClassLoader的创建

PathClassLoader是在系统服务进程（SystemServer）中创建的。

TODO PathClassLoader是在另一个进程中创建的，那么是怎么获取实例的。

# 总结

-   Java的引导类加载器是由C++编写的，Android中的引导类加载器则是用Java编写的。
-   由于Android中加载的不再是Class文件，因此Android中没有ExtClassLoader和
    AppClassLoader，替代它们的是PathClassoader和DexClassLoader。

# 个人总结

## Java和Android的区别

1.   Java中的ClassLoader是加载class文件，Android中是加载dex文件。Android中的`java.lang.ClassLoader`这个类也不同于Java中的`java.lang.ClassLoader`。
2.   Android平台上虚拟机运行的是Dex字节码，一种对class文件优化的产物。Android把所有Class文件进行合并，优化，然后生成一个最终的class.dex，目的是把不同class文件重复的东西只需保留一份，如果Android应用不进行分dex处理，最后一个应用的apk只会有一个dex文件。 
3.   和java虚拟机中不同的是BootClassLoader是ClassLoader内部类，由java代码实现而不是c++实现。

## PathClassLoader与DexClassLoader的区别

1.   PathClassLoader只能加载已经安装到Android系统中的apk文件（/data/app目录），是Android默认使用的类加载器。（其实这说的应该是在dalvik虚拟机上，在art虚拟机上PathClassLoader可以加载未安装的apk的dex）。
2.   DexClassLoader可以加载任意目录下的dex/jar/apk/zip文件，比PathClassLoader更灵活。

## 热修复基本原理

DexPathList的构造函数是将一个个的程序文件（可能是dex、apk、jar、zip）封装成一个个Element对象，最后添加到Element集合中。 

```java
// DexPathList#findClass
public Class<?> findClass(String name, List<Throwable> suppressed) {
    for (Element element : dexElements) {
        Class<?> clazz = element.findClass(name, definingContext, suppressed);
        if (clazz != null) {
            return clazz;
        }
    }

    if (dexElementsSuppressedExceptions != null) {
        suppressed.addAll(Arrays.asList(dexElementsSuppressedExceptions));
    }
    return null;
}
```

结合DexPathList的构造函数，其实DexPathList的findClass()方法很简单，就只是对Element数组进行遍历，一旦找到类名与name相同的类时，就直接返回这个class，找不到则返回null。 

数组的遍历是有序的，假设有两个dex文件存放了二进制名称相同的Class，类加载器肯定就会加载在放在数组前面的dex文件中的Class。

现在很多热修复技术就是把修复的dex文件放在DexPathList中dexElements数组的前面，这样就实现了修复后的Class抢先加载了，达到了修改bug的目的。

