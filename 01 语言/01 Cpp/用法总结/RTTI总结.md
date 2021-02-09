RTTI旨在为程序在运行阶段确定对象的类型提供一种标准方式。

# dynamic_cast运算符

继承树：

```cpp
class Grand{ // has virtual methods};
class Superb : public Grand { ... };
class Magnificent : public Superb { ... };
```

接下来假设有下面的指针：

```cpp
Grand *pg = new Grand;
Grand *ps = new Superb;
Grand *pm = new Magnificent;
```

最后，对于下面的类型转换：

```cpp
Magnificent *p1 = (Magnificent *) pm;// #1
Magnificent *p2 = (Magnificent *) pg;// #2
Superb *p3 = (Magnificent *) pm;// #3
```

类型转换#1就是安全的，因为它将Magificent类型的指针指向类型为Magnificent的对象。

类型转换#2就是不安全的，因为它将基数对象(Grand)的地址赋给派生类(Magnificent)指针。

类型转换#3是安全的，因为它将派生对象的地址赋给基类指针。

```cpp
Superb *pm = dynamic_cast<Superb *>(pg);
```

如果指针pg可以安全地转换为Superb *，运算符将返回对象的地址，否则返回一个空指针。

也可以将dynamic_cast 用于引用，其用法稍微有点不同：没有与空指针对应的引用值，因此无法使用特殊的引用值来指示失败。当请求不正确时，dynamic_cast 将引发类型为bad_cast 的异常，这种异常是从exception类派生而来的，它是在头文件typeinfo中定义的。

# typeid运算符和type_info类

typeid运算符使得能够确定两个对象是否为同种类型，可以接受两种参数：

-   类名

-   结果为对象的表达式

typeid运算符返回一个对type_info对象的引用，其中type_info是在头文件typeinfo(以前为typeinfo.h)中定义的一个类。type_info 类重载了==和!=运算符，以便可以使用这些运算符来对类型进行比较。例如，如果pg指向的是一个Magnificent对象，则下述表达式的结果为bool值true，否则为false：

```cpp
typeid(Magnificent) = typeid(*pg)
```

如果pg是一个空指针，程序将引发bad_typeid 异常。该异常类型是从exception类派生而来的，是在头文件typeinfo中声明的。

type_info类的实现随厂商而异，但包含一个name()成员，该函数返回一个随实现而异的字符串：通常(但并非一定)是类的名称。

