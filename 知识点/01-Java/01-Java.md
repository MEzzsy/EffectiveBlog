# Object 类相关

## java中==和equals和hashCode的区别

**1、==**

java中的数据类型，可分为两类：

1.  基本数据类型，也称原始数据类型
    byte,short,char,int,long,float,double,boolean   他们之间的比较，应用双等号（==）,比较的是他们的值。 

2.  引用类型(类、接口、数组) 
    当他们用（==）进行比较的时候，比较的是他们在内存中的存放地址，所以，除非是同一个new出来的对象，他们的比较后的结果为true，否则比较后结果为false。
    对象是放在堆中的，栈中存放的是对象的引用（地址）。由此可见'=='是对栈中的值进行比较的。如果要比较堆中对象的内容是否相同，那么就要重写equals方法了。

**2、equals**

1.  没有覆盖equals方法，equals是Object的方法，代码如下：

```java
public boolean equals(Object obj) {  
    return (this == obj);  
}  
```

2.  覆盖了equals方法，那么就要根据具体的代码来确定equals方法的作用了，一般是根据对象的内容是否相等来判断对象是否相等。

**3、hashCode**

hashCode的目的是用于在对象进行散列的时候作为key输入，保证散列的存取性能。Object的默认hashCode实现为在对象的内存地址上经过特定的算法计算出。

初学者可以这样理解，hashCode方法实际上返回的就是对象存储的物理地址（实际可能并不是）

1、如果两个对象equals，Java运行时环境会认为他们的hashcode一定相等。 
2、如果两个对象不equals，他们的hashcode有可能相等。 
3、如果两个对象hashcode相等，他们不一定equals。 
4、如果两个对象hashcode不相等，他们一定不equals。 

## 浅拷贝与深拷贝

```java
public class Human implements Cloneable{
    private int age;
    private String name;
    private Info mInfo;

    public Human(int age, String name, Info info) {
        this.age = age;
        this.name = name;
        mInfo = info;
    }

    @Override
    protected Object clone() throws CloneNotSupportedException {
        return super.clone();
    }

    @Override
    public String toString() {
        String s = super.toString();
        return s + "\n" + "Human{" +
                "age=" + age +
                ", name='" + name + '\'' +
                ", mInfo=" + mInfo +
                '}';
    }
}

public class Info implements Cloneable {
    private double d;
    private boolean b;

    public Info(double d, boolean b) {
        this.d = d;
        this.b = b;
    }

    @Override
    protected Object clone() throws CloneNotSupportedException {
        return super.clone();
    }

    @Override
    public String toString() {
        String s = super.toString();
        return s + "\n" + "Info{" +
                "d=" + d +
                ", b=" + b +
                '}';
    }
}
```

### 浅拷贝

对于数据类型是基本数据类型的成员变量，浅拷贝会直接进行值传递，也就是将该属性值复制一份给新的对象。

对于数据类型是引用数据类型的成员变量，比如说成员变量是某个数组、某个类的对象等，那么浅拷贝会进行引用传递，也就是只是将该成员变量的引用值（内存地址）复制一份给新的对象。在这种情况下，在一个对象中修改该成员变量会影响到另一个对象的该成员变量值。

```java
Info info = new Info(1.1, true);
Human human = new Human(2, "a", info);
Human human1= (Human) human.clone();
System.out.println(info);
System.out.println(human);
System.out.println(human1);

output：
com.mezzsy.learnsomething.Info@1b6d3586
Info{d=1.1, b=true}

com.mezzsy.learnsomething.Human@4554617c
Human{age=2, name='a', mInfo=com.mezzsy.learnsomething.Info@1b6d3586
Info{d=1.1, b=true}}

com.mezzsy.learnsomething.Human@74a14482
Human{age=2, name='a', mInfo=com.mezzsy.learnsomething.Info@1b6d3586
Info{d=1.1, b=true}}
```

> human1浅拷贝了human，从hash code看出，human1是一个新的对象，但是它内部的info是和human中的一样。

### 深拷贝

深拷贝对引用数据类型的成员变量的对象图中所有的对象都开辟了内存空间；而浅拷贝只是传递地址指向，新的对象并没有对引用数据类型创建内存空间。

```java
public class Human implements Cloneable {
    @Override
    protected Object clone() throws CloneNotSupportedException {
        Object o = super.clone();
        Human human = (Human) o;
        human.mInfo = (Info) human.mInfo.clone();
        return human;
    }
}

public class Info implements Cloneable {
    @Override
    protected Object clone() throws CloneNotSupportedException {
        return super.clone();
    }
}
```

```java
Info info = new Info(1.1, true);
Human human = new Human(2, "a", info);
Human human1= (Human) human.clone();
System.out.println(info);
System.out.println(human);
System.out.println(human1);

output：
com.mezzsy.learnsomething.Info@1b6d3586
Info{d=1.1, b=true}

com.mezzsy.learnsomething.Human@4554617c
Human{age=2, name='a', mInfo=com.mezzsy.learnsomething.Info@1b6d3586
Info{d=1.1, b=true}}

com.mezzsy.learnsomething.Human@74a14482
Human{age=2, name='a', mInfo=com.mezzsy.learnsomething.Info@1540e19d
Info{d=1.1, b=true}}
```

## 数据类型

8种基本数据类型

![20180916202419](http://111.230.96.19:8081/image/20190328192625.png)

还有一种基本数据类型refvar，是面向对象的引用变量，也叫引用句柄。默认值是null，存储的是refobj的首地址，可以直接使用==进行等值判断。

作为一个引用变量，不管它是指向包装类、集合类、字符串类还是自定义类，refvar均占用**4B**空间。注意它与真正对象refobj之间的区别。无论refobj是多么小的对象，最小占用的存储空间是12B（用于存储基本信息，称为对象头），但由于存储空间分配必须是8B的倍数，所以初始分配的空间至少是**16B**。

一个refvar至多存储一个refobj的首地址，一个refobj可以被多个refvar存储下它的首地址，即一个堆内对象可以被多个refvar引用指向。如果refobj没有被任何refvar指向，那么它迟早会被垃圾回收。而refvar的内存释放，与其他基本数据类型类似。

基本数据类型int占用4个字节，而对应的包装类Integer实例对象占用16个字节。这里可能会有人问：Integer里边的代码就只占用16B？这是因为字段属性除成员属性int value外，其他的如MAX_VALUE 、MIN_VALUE等**都是静态成员变量，在类加载时就分配了内存，与实例对象容量无关**（方法区内存与堆无关）。此外，**类定义中的方法代码不占用实例对象的任何空间**。IntegerCache是Integer的静态内部类，容量占用也与实例对象无关。由于refobj对象的基础大小是12B，再加上int是4B，所以Integer实例对象占用16B，按此推算Double对象占用的存储容量是24B，示例代码如下：

```java
public class Main {
    //对象头最少占用12个字节（B）

    //下方4个byte类型分配后，对象占用16（12+4）个字节
    byte b1;
    byte b2;
    byte b3;
    byte b4;

    //下方每个引用变量占4个字节，共20个
    Object o1;
    Object o2;
    Object o3;
    Object o4;
    Object o5;

    //Info实例占用空间并不计算在本对象内，依然只计算引用变量大小8（2*4）个字节
    Info info1 = new Info();
    Info info2 = new Info();

    /**
     * double类型占用8个字节，但此处是数组引用变量
     * 所以占用4个字节，而不是8000个字节
     * 这个引用指向的是double[] 类型，指向实际分配的数组空间首地址
     * 在new 对象时，已经实际分配空间
     */
    double[] mDoubles = new double[1000];
}
```

# int和Integer

int占32位4字节

## 存储原理

- `int`属于基本数据类型，存储在栈中。
- `Integer`属于复合数据类型，引用存储在栈中，引用所指向的对象存储在堆中。

## 缺省值

- `0`
- `null`

## 泛型支持

泛型支持`Integer`，不支持`int`

## int 与 Integer 之间的比较

```java
//基本数据类型。
int a1 = 128;
//非 new 出来的 Integer。
Integer a2 = 128;
//new 出来的 Integer。
Integer a3 = new Integer(128);
```

- 非`new`出来的`Integer`与`new`出来的`Integer`不相等，前者指向存放它的缓存（数值位于`-128`到`127`之间，一个数组，在常量池中），后者指向堆中的另外一块内存。
- 两个都是非`new`出来的`Integer`，如果在`-128`到`127`之间，返回的是`true`，否则返回的是`false`，因为`Java`在编译`Integer a2 = 128`的时候，会翻译成 `Integer.valueOf(128)`，而`valueOf`函数会对`-128`到`127`之间的数进行缓存。

```java
    public static Integer valueOf(int i) {
        //low = -128, high = 127.
        if (i >= IntegerCache.low && i <= IntegerCache.high)
            return IntegerCache.cache[i + (-IntegerCache.low)];
        return new Integer(i);
    }
```

- 两个都是`new`出来的，返回`false`。
- `int`与`Integer`相比，都为`true`，因为会把`Integer`自动拆箱为`int`再去比较。

## int和Integer的区别

1、Integer是int的包装类，int则是java的一种基本数据类型 。
2、Integer变量必须实例化后才能使用，而int变量不需要 。
3、Integer实际是对象的引用，当new一个Integer时，实际上是生成一个指针指向此对象；而int则是直接存储数据值。
4、Integer的默认值是null，int的默认值是0。

# **比较double数据是否相等的方法**

**方法一**

若精度要求不高，比如因为传感器有误差，小于0.001的数都可以认为等于0，那么就定义epsilon = 0.001

```java
final double epsilon = 0.001; 
double double_x = 0.0;
if(Math.abs(double_x - 0) < epsilon) {
    System.out.println("true");
}
```

**方法二**

转换成字符串之后用equals方法比较 

如果要比较的两个double数据的字符串精度相等，可以将数据转换成String然后借助String的equals方法来间接实现比较两个double数据是否相等。

```java
Double.toString(double_x).equals(Double.toString(double_y))
```

注意：这种方法只适用于比较精度相同的数据，并且是只用用于比较是否相等的情况下，不能用来判断大小。

**方法三**

转换成Long之后用==方法比较

使用Sun提供的Double.doubleToLongBits()方法，该方法可以将double转换成long型数据，从而可以使double按照long的方法（<, >, ==）判断是否大小和是否相等。

```java
Double.doubleToLongBits(0.01) == Double.doubleToLongBits(0.01)
Double.doubleToLongBits(0.02) > Double.doubleToLongBits(0.01)
Double.doubleToLongBits(0.02) < Double.doubleToLongBits(0.01) 
```

**方法四**

使用BigDecimal类型的equals方法或compareTo方法

类加载：

```java
import java.math.BigDecimal;
```

使用**字符串形式**的float型和double型构造BigDecimal：BigDecimal(String val)。BigDecimal的euquals方法是先判断要比较的数据类型，如果对象类型一致前提下同时判断精确度(scale)和值是否一致；compareTo方法则不会比较精确度，把精确度低的那个对象转换为高精确度，只比较数值的大小。

```java
System.out.println(new BigDecimal("1.2").equals(new BigDecimal("1.20")));  //输出false  
System.out.println(new BigDecimal("1.2").compareTo(new BigDecimal("1.20")) == 0); //输出true  
    		          
System.out.println(new BigDecimal(1.2).equals(new BigDecimal("1.20"))); //输出false
System.out.println(new BigDecimal(1.2).compareTo(new BigDecimal("1.20")) == 0); //输出false  
    		     
System.out.println(new BigDecimal(1.2).equals(new BigDecimal(1.20))); //输出true  
System.out.println(new BigDecimal(1.2).compareTo(new BigDecimal(1.20)) == 0);//输出true 
```

# String

## new String和直接赋值的区别

`new String`和直接赋值的区别：

- `String str1 = "ABC"`，可能创建一个或者不创建对象，如果`ABC`这个字符串在常量池中已经存在了，那么`str1`直接指向这个常量池中的对象。
- `String str2 = new String("ABC")`，至少创建一个对象。一定会在堆中创建一个`str2`中的`String`对象，它的`value`是`ABC`，如果`ABC`这个字符串在常量池中不存在，会在池中创建一个对象。

## 例子 1

```
String s ="a" + "b" + "c" + "d"
```

只创建了一个对象，在编译器在编译时优化后，相当于直接定义了一个`abcd`的字符串。

## 例子 2

```
String ab = "ab";                                          
String cd = "cd";                                       
String abcd = ab + cd;                                      
String s = "abcd";  
```

`ab`和`cd`存储的是两个常量池中的对象，当执行`ab + cd`时，首先会在堆中创建一个`StringBuilder`类，同时用`ab`指向的字符串对象完成初始化，然后调用`append`方法完成对`cd`指向字符串的合并操作，接着调用`StringBuilder`的`toString`方法在堆中创建一个`String`对象，最后将刚生成的`String`对象的地址存放在局部变量`abcd`中。

## String为什么要设计成不可变的

字符串池是方法区（Method Area）中的一块特殊的存储区域。当一个字符串已经被创建并且该字符串在池中，该字符串的引用会立即返回给变量，而不是重新创建一个字符串再将引用返回给变量。如果字符串不是不可变的，那么改变一个引用（如: string2）的字符串将会导致另一个引用（如: string1）出现脏数据。

# 内部类

## 分类

- 成员内部类：作为外部类的成员，可以直接使用外部类的所有成员和方法。
- 静态内部类：声明为`static`的内部类，成员内部类不能有`static`数据和`static`属性，但嵌套内部类可以。
- 局部内部类：内部类定义在方法和作用域内。只在该方法或条件的作用域内才能使用，退出作用域后无法使用。
- 匿名内部类：匿名内部类有几个特点：不能加访问修饰符；当所在方法的形参需要被内部类里面使用时，该形参必须为`final`。

## 作用

### 实现隐藏

外部顶级类即类名和文件名相同的只能使用`public`和`default`修饰，但内部类可以是`static`、`public/default/protected/private`。

### 无条件地访问外部类当中的元素

这仅限于非静态内部类，它和静态内部类的区别是：

- 静态内部类没有指向外部的引用
- 在任何非静态内部类中，都不能有静态变量、静态方法或者静态内部类。
- 创建非静态内部类，必须要通过外部类来创建，例如`Outer.InnerImpl outer = new Outer().new InnerImpl();`；静态内部类则可以直接创建，`Outer.InnerImpl outer = new Outer.InnerImpl();` 
- 静态内部类只可以访问外部类的静态方法和静态变量。
- 非静态内部类不能含有`static`的变量和方法。

### 实现多重继承

由于`Java`不允许多重继承，因此假如我们希望一个类同时具备其它两个类的功能时，就可以采用内部类来实现。

### 避免修改接口而实现同一个类中两种同名方法的调用

用于解决下面的困境：一个需要继承另一个类，还要实现一个接口，而继承的类和接口里面有两个同名的方法。那么我们调用该方法的时候，究竟是父类的，还是实现的接口呢，这时候就可以使用内部类来解决这一问题。

## 应用场景

从作用考虑

## 一些问题

### 什么时候使用局部内部类而不是匿名内部类？

- 需要一个已命名的构造器，或者需要重载构造器。
- 需要不止一个该内部类的对象。

### 静态内部类的设计意图

内部类设计意图：

- 内部类方法可以访问外部类的数据，包括私有数据。
- 对同一个包的其它类隐藏。

静态内部类的设计意图：

如果只是隐藏一个内部类，而不需要引用外部类的对象，那么可以使用静态内部类。

### 为什么内部类会隐式持有外部类的引用

```java
class InnerClassTest {
    private int id = 0;

    private void add() {
        id++;
    }

    private void use() {
        InnerClass innerClass = new InnerClass();
        innerClass.innerAdd();
    }

    private class InnerClass {

        public InnerClass() {
        }

        public InnerClass(int a) {
            id = a;
        }

        private void innerAdd() {
            add();//调用外部类的方法
            id++;//使用外部类的成员变量
        }
    }
}
```

InnerClassTest是外部类，里面有个内部类InnerClass，InnerClass有两个构造方法，注意这两个构造方法。

对InnerClassTest进行反编译，会生成2个class文件，一个是InnerClassTest.class，另一个是InnerClassTest$InnerClass.class。

主要看一下InnerClassTest$InnerClass.class

```java
//
// Source code recreated from a .class file by IntelliJ IDEA
// (powered by Fernflower decompiler)
//

package com.mezzsy.learnsomething.java;

class InnerClassTest$InnerClass {
    public InnerClassTest$InnerClass(InnerClassTest var1) {
        this.this$0 = var1;
    }

    public InnerClassTest$InnerClass(InnerClassTest var1, int var2) {
        this.this$0 = var1;
        var1.id = var2;
    }

    private void innerAdd() {
        this.this$0.add();
        ++this.this$0.id;
    }
}
```

注意看构造方法，虽然在代码上一个是无参，一个是只有一个参数，但是实际上编辑器会插入一个参数，这个参数就是隐式的外部类的引用，当使用外部类的变量或者方法时，会使用这个隐式引用。

# 泛型

[泛型笔记](/Users/mezzsy/Projects/Blog/Java/泛型.md)，以下内容是对笔记的提取，建议看看笔记。

## 泛型的优点

对于一般的类和方法，如果要编写应用于多种类型的代码，那么代码的耦合度就会非常大。泛型实现了类型参数化的概念，能够让代码应用于多种类型。（利用Object数组也可以，但是这样会造成类型安全问题）

泛型在编译期增加了一道检查，在使用泛型时安全放置和使用数据。

泛型的好处：

- 类型安全。放置的是什么，取出来的自然是什么，不用担心会抛出ClassCastException异常。
- 提升可读性。从编码阶段就显式地知道泛型集合、泛型方法等处理的对象类型是什么。
- 代码重用。泛型合并了同类型的处理代码，使代码重用度变高。

## 泛型方法

为什么静态方法不能访问类的类型参数呢？

静态方法是对于类而言的，如果静态方法可以访问，那么假设有两个对象设置了不同的类型参数，对于这个静态方法而言，它就会访问两种类型参数，这显然是不合理的。

## 类型擦除

**Java泛型是使用擦除来实现的**，这意味着在使用泛型时，任何具体的类型信息都被擦除了。因此List\<String\> 和List\<Integer\>在运行时事实上是相同的类型。这两种形式都被檫除成它们的“原生”类型，即List。 

- `List<String>`、`List<T>`擦除后的类型为`List`。
- `List<String>[]`、`List<T>[]`擦除后的类型为`List[]`。
- `List<? extends E>`、`List<? super E>`擦除后的类型为`List<E>` 
- `List<T extends Serialzable & Cloneable>`擦除后的类型为`List<Serialzable>`。

### 类型擦除的目的

- 避免对JVM的改动，如果JVM将泛型类型延续到运行期，那么到运行期时JVM就要进行大量的重构工作。
- 版本兼容（主要原因）。在编译期擦除可以更好地支持原生类型。

### 类型擦除的后果

#### 不能创建泛型数组

不能创建泛型数组。一般的解决方法是创建动态数组ArrayList。

```java
public static void main(String[] args) {
        Generic<Integer>[] generics = new Generic[3];
        generics = (Generic<Integer>[]) new Object[3];//可以编译，但是运行会报ClassCastException
        generics[0] = new Generic<>();
        generics[1] = (Generic<Integer>) new Object();
//        generics[2] = new Generic<Double>();//编译时错误
    }

    static class Generic<T>{}
}
```

##### 问题一

对于这个问题

```java
generics = (Generic<Integer>[]) new Object[3];//可以编译，但是运行会报ClassCastException
```

由于类型擦除，这里可以不用管泛型，可以换成String和Object：

```java
public static void main(String[] args) {
  	Object[] objectsToStrings = new String[2];//正常运行
  
    String[] strings;
    Object[] objects = new Object[2];
    
    //效果和strings = (String[]) new Object[2];一样
    strings= (String[]) objects;
}
```

以上运行依然会造成ClassCastException，因为在创建数组的时候会确定类型。

> 上面的解释有点难以理解，这里我以反证的方法进行分析：
>
> 如果可以正常运行，那么Object数组中的内容会被赋给String数组，如果Object数组有非String类型的，比如Integer，那么就表示String数组存放了Integer类型，这显然是不行的。
>
> 所以，上面的解释可以这么理解，数组在创建的时候会确定类型，如果通过父类数组转型可能会导致数组内有另一个子类类型，所以这个时候会报异常。
>
> 子类数组转父类数组就没有什么问题，因为类型是符合的（符合父类）如上面代码的第二行。

以上问题的解是本人参考《Java编程思想》和《有效的Java》得出的，可能存在某些未知问题。

由上面的问题引发出一个类似的泛型问题：

```java
public static void main(String[] args) {
    GenericArray<String> array = new GenericArray<>(2);
    String[] strings = array.rep();
}

private static class GenericArray<T> {
    private T[] array;

    @SuppressWarnings("unchecked")
    public GenericArray(int size) {
        array = (T[]) new Object[size];
    }

    public void put(T t, int index) {
        array[index] = t;
    }

    public T get(int index) {
        return array[index];
    }

    public T[] rep() {
        return array;
    }
}
```

以上情况也是出现ClassCastException，原因也是类似的。

```java
Object[] strings = array.rep();
```

以这样的方式引用没有问题，因为类型擦除后T[]就是Object[]。

如果要用泛型数组，那么需要声明Object[]，在putget的时候进行转型，参照ArrayList。

#### 不能使用instanceof比较类型

不能使用instanceof关键字，因为类型信息擦除了，

如果要比较类型，可以利用isInstanceOf()方法

```java
final class Main<T> {
    private Class<T> kind;

    public static void main(String[] args) {
        Main<String> main = new Main<>();
        main.setKind(String.class);
        main.f("a");//true
        main.f(1);//false
    }

    public void setKind(Class<T> kind) {
        this.kind = kind;
    }

    public void f(Object o) {
        System.out.println(kind.isInstance(o));
    }
}
```

#### 不能创建对象

不能用new T()来创建对象，部分原因是因为擦除，而另一部分原因是因为编译器不能验证T具有默认(无参)构造器。

解决办法是利用工厂方法模式或者模版方法模式

```java
//工厂方法模式
private static class Factory<T> {
    public T create(Class<T> clazz) {
        T t;
        try {
            t = clazz.newInstance();
            return t;
        } catch (IllegalAccessException e) {
            System.out.println("IllegalAccessException");
            return null;
        } catch (InstantiationException e) {
            System.out.println("InstantiationException");
            return null;
        }
    }
}
```

```java
//模版方法模式
private static abstract class GenericWithCreate<T> {
    protected final T t;

    public GenericWithCreate() {
        t = create();
    }

    abstract T create();
}

private static class Creator extends GenericWithCreate<Main>{

    @Override
    Main create() {
        return new Main();
    }
}
```

## 边界

见笔记的边界和通配符部分。

## 泛形数组问题

参考《有效的Java》

一些知识：

数组与泛型相比，有两个重要的不同点。首先，数组是**协变**的。 其实只是表示如果Sub为Super的子类型，那么数组类型Sub[]就是Super[]的子类型。相反，泛型则是**不可变**的：对于任意两个不同的类型Type 1和Type2，List\<Type 1\>既不是List\<Type2\>的子类型，也不是List\<Type2\>的超类型。

```java
Object[] objects = new Integer[2];
objects[0] = "a";//编译正常，运行时ArrayStoreException
```

```java
List<Object> objects = new ArrayList<Integer>();//编译不通过
objects.add("a");
```

数组与泛型之间的第二大区别在于，数组是具体化的。因此数组会在运行时才知道并检查它们的元素类型约束。如上所述，如果企图将String保存到Integer数组中，就会得到一个ArrayStoreException异常。

相比之下，泛型则是通过擦除来实现的。因此泛型只在编译时强化它们的类型信息，并在运行时丢弃(或者擦除)它们的元素类型信息。擦除就是使泛型可以与没有使用泛型的代码随意进行互用。

```java
List<Integer> integers = new ArrayList<>();
integers.add(1);
List strings = new ArrayList();
strings.add("a");
integers.addAll(strings);
System.out.println(integers);//输出[1, a]
```

回到这个问题：为什么泛形不能创建数组（如：new List\<Integer\>[]）？

**因为它不是类型安全的。**

```java
List<String>[] lists = new ArrayList<String>[2];
List<Integer> integers = Arrays.asList(1);
Object[] objects = lists;
objects[0] = integers;
String s = lists[0].get(0);
```

假设第1行是合法的，它创建了一个泛型数组。
第2行创建并初始化了一个包含单个元素的List\<Integer\>。
第3行将List\<String\> 数组保存到一个Object数组变量中，这是合法的，因为数组是协变的。
第4行将List\<Integer\>保存到Object数组里唯一的元素中，这是可以的，因为泛型是通过擦除实现的：List\<Integer\>实例的运行时类型只是List，List\<String\>[]实例的运行时类型则是List[]，因此这种安排不会产生ArrayStoreException异常。
但现在有麻烦了。将一个List\<Integer\>实例保存到了原本声明只包含List\<String\>实例的数组中。在第5行中，从这个数组里唯一的列表中获取了唯一的元素。编译器自动地将获取到的元素转换成String，但它是一个Integer，因此，在运行时得到了一个ClassCastException异常。
为了防止出现这种情况，(创建泛型数组的)第1行产生了一个编译时错误。

如果一定要创建泛型数组，可以用这种方式：

```java
List<?>[] lists = new ArrayList<?>[2];
```

# 集合

## HaspMap源码总结

1.**HashMap内部采用数组+链表/红黑树**，使用散列表解决碰撞冲突的问题，其中数组的每个元素是单链表的头结点，链表/红黑树是用来解决冲突的。

2.HashMap有两个重要的参数：初始容量和加载因子。这两个参数极大的影响了HashMap的性能。初始容量是hash数组的长度，当前加载因子=当前hash数组元素/hash数组长度，最大加载因子为最大能容纳的数组元素个数（默认最大加载因子为0.75），当hash数组中的元素个数超出了最大加载因子和容量的乘积时，要对hashMap进行扩容，扩容过程存在于hashmap的put方法中，扩容过程始终以2次方增长。

3.HashMap是泛型类，key和value可以为任何类型，包括null类型。key为null的键值对永远都放在以table[0]为头结点的链表中，当然不一定是存放在头结点table[0]中。

1. static final int DEFAULT_INITIAL_CAPACITY = 1 << 4; -> 数组默认初始容量：16
2. static final int MAXIMUM_CAPACITY = 1 << 30; -> 数组最大容量2 ^ 30 次方
3. static final float DEFAULT_LOAD_FACTOR = 0.75f; -> 默认负载因子的大小：0.75
4. **static final int MIN_TREEIFY_CAPACITY = 64; -> 树形最小容量：哈希表的最小树形化容量，超过此值允许表中桶(Node)转化成红黑树**
5. **static final int TREEIFY_THRESHOLD = 8; -> 树形阈值：当链表长度达到8时，将链表转化为红黑树**
6. **static final int UNTREEIFY_THRESHOLD = 6; -> 树形阈值：当链表长度小于6时，将红黑树转化为链表**
7. int threshold; -> 可存储key-value 键值对的临界值 需要扩充时;值 = 容量 * 加载因子
8. transient int size; 已存储key-value 键值对数量
9. final float loadFactor; -> 负载因子
10. transient Node< K,V>[] table; -> 链表数组（用于存储hashmap的数据）

### 部分方法解析

**放入（put方法）**

根据key的hash值和数组长度（hash&n-1）得出key在数组中的位置。

如果当前位置没有key，那么将键值对放入。

如果有冲突：

如果是同一个key，那么更新value。

如果是数组中的节点是红黑树节点，那么就放入树中。

如果是链表节点，那么放入单链表中的**最后一个**：
如果单链表的长度超过树化阈值（8），如果数组长度小于64，那么扩容，否则将此单链表转化为红黑树。

放入键值对后，如果当前键值对数量超过阈值，那么resize。

**resize方法**

首先创建新的数组，长度为原来的2倍，阈值也变为原来的2倍。

然后对原数组的每一个位置进行遍历，如果有链表，那么会把链表分为2份。

> 这里分为2份的原理是：
>
> 比如之前的长度10000（16），一个key为1111，一个key为11111，那么根据
> [hash&(n-1)]，它们放在同一个位置。
>
> 扩容后的长度100000。在扩容的方法中利用的是[hash&oldcap]（oldcap为原来的长度）来区分。那么，1111的是0，11111的不为0，这里就分出了2个链表，如果有多个节点情况也是如此，最终会分为2个链表，一个low，一个high，low的位置为[原来的坐标]，high的坐标为[原来的坐标+oldcap]。

如果红黑树在resize后的大小小于非树化阈值（6），那么变为单链表。

**树化（treeifyBin方法）**

先将单链表节点转为红黑树节点，然后将单链表转为双向链表，再转为红黑树。

*什么时候树化？*

桶为数组中的一个节点，size为HashMap中键值对数量，capacity为数组长度。MIN_TREEIFY_CAPACITY(64)树形最小容量，TREEIFY_THRESHOLD(8)树形阈值，UNTREEIFY_THRESHOLD(6)，threshold阈值。

一、当单链表中的长度>TREEIFY_THRESHOLD，但是capacity<MIN_TREEIFY_CAPACITY，不会变成红黑树，会进行扩容。

二、当单链表中的长度>TREEIFY_THRESHOLD，而且capacity>=MIN_TREEIFY_CAPACITY，将此单链表转为红黑树。

三、只要size>threshold，就会进行扩容。

四、在扩容的时候，桶中元素个数小于非树化阈值（6），就会把树形的桶元素还原为单链表结构。

> 为什么单链表要转为红黑树？
>
> 红黑树所有的操作最坏情况都是O（log（n））的。
>
> 红黑树的平均查找长度是log(n)，长度为8，查找长度为log(8)=3。
>
> 链表的平均查找长度为n/2，当长度为8时，平均查找长度为8/2=4，这才有转换成树的必要。链表长度如果是小于等于6，6/2=3，虽然速度也很快的，但是转化为树结构和生成树的时间并不会太短。

**删除（remove方法）**

根据key的hash值和数组长度得出key在数组中的位置。

如果当前位置有key，而且key就是要删除的那个key，那么移除。

否则，要么从红黑树中找到那个节点或者从单链表中找到那个节点，然后移除。

移除：

如果是红黑树，按照红黑树的移除操作。

如果是单链表的头部，那么头部变为节点的下一个。

如果是单链表的中间，那么前一个节点的next变为当前结点的下一个。

### 线程安全

为什么HashMap不是线程安全的？

举个例子：如果两个线程同时put，如果这两个key的hash相同，那么会放在同一个位置，可能会产生覆盖。

要想线程安全的使用

线程安全的HashMap

Hashtable、ConcurrentHashMap、使用Collections类的synchronizedMap方法包装一下。

### HashMap和Hashtable区别？

简单总结有几点：

1.  HashMap支持null Key和null Value；Hashtable不允许。这是因为HashMap对null进行了特殊处理，将null的hashCode值定为了0，从而将其存放在哈希表的第0个bucket。

2.  HashMap是非线程安全，HashMap实现线程安全方法为`Map map = Collections.synchronziedMap(new HashMap())；`
    Hashtable是线程安全。

3.  HashMap默认长度是16，扩容是原先的2倍
    Hashtable默认长度是11，扩容是原先的2n+1

4.  HashMap继承AbstractMap
    Hashtable继承了Dictionary

5.  如果在创建时给定了初始化大小，那么HashTable会直接使用给定的大小，而HashMap会将其扩充为2的幂次方大小。 

### ConcurrentHashMap和Hashtable的区别

都可以用于多线程的环境，但是当Hashtable的大小增加到一定的时候，性能会急剧下降，因为迭代时需要被锁定很长的时间。因为ConcurrentHashMap引入了分割(segmentation)，不论它变得多么大，仅仅需要锁定map的某个部分，而其它的线程不需要等到迭代完成才能访问map。**简而言之，在迭代的过程中，ConcurrentHashMap仅仅锁定map的某个部分，而Hashtable则会锁定整个map。**

### HashMap、SparseArray、ArrayMap的区别

1.  在数据量小的时候一般认为1000以下，当key为int的时候，使用SparseArray确实是一个很不错的选择，内存大概能节省30%，相比用HashMap，因为key值不需要装箱，所以时间性能平均来看也优于HashMap。
2.  ArrayMap相对于SparseArray，特点就是key值类型不受限，任何情况下都可以取代HashMap，但是通过研究和测试发现，ArrayMap的内存节省并不明显。并且AS会提示使用SparseArray，但是不会提示使用ArrayMap。

## SparseArray源码总结

当key为int类型的时候可以使用SparseArray。

成员变量

```java
private static final Object DELETED = new Object();
private boolean mGarbage = false;
private int[] mKeys;
private Object[] mValues;
private int mSize;
```

默认大小是10

mKeys是升序排序的。

### 部分方法解析

**放入（put方法)**

二分搜索寻找key在数组中的位置，如果key存在，更新值。反之，返回二分搜索得到的下标。

下标小于size并且key的值被标记为删除，那么更新值。

如果垃圾标记位为true并且size超出容量，那么就运行gc方法，再重新二分搜索，返回新的下标。

如果size大于容量，那么扩容。

如果下标不是最后一个，那么把后面的键值对往后移，然后在当前位置放入键值对。

**移除（remove方法）**

根据key，二分搜索找到下标i。

如果有这个key的话（i>=0）

```java
if (i >= 0) {
    if (mValues[i] != DELETED) {
        mValues[i] = DELETED;
        mGarbage = true;
    }
}
```

**删除（gc方法）**

如果在放入的时候，mGarbage标记位为true并且size大于等于数组的长度，那么进行垃圾删除。

```java
private void gc() {
    int n = mSize;
    int o = 0;
    int[] keys = mKeys;
    Object[] values = mValues;

    for (int i = 0; i < n; i++) {
        Object val = values[i];

        if (val != DELETED) {
            if (i != o) {
                keys[o] = keys[i];
                values[o] = val;
                values[i] = null;
            }

            o++;
        }
    }
    mGarbage = false;
    mSize = o;
}
```

就是把非DELETED的往前移。很简单。

## ArrayList源码总结

默认容量是10，可以自定义容量。

成员变量有个数组`Object[] elementData`，用来存储数据。

### 部分方法解析

**添加数据（add方法）**

在最后面的位置添加。

```
elementData[size++] = e;
```

**插入**

将当前位置的后面的数据往后移，然后在当前位置插入新的数据。

**删除（remove方法）**

如果是最后一个，那么直接令其为null，否则将后面的元素往前移。

**扩容**

在添加和插入之前，会进行扩容判定，如果添加后（size+1）会超出容量，那么会进行扩容。

容量变为原来的1.5倍。

### 总结

-   ArrayList是基于动态数组实现的，随机存取快，但是在增删时候，需要数组的拷贝复制，这个时候明显劣势。
-   它不是线程安全的。
-   它能存放null值。
-   ArrayList的默认初始化容量是10，每次扩容时候增加原先容量的一半，也就是变为原来的1.5倍

## LinkedList和ArrayList的区别

1. ArrayList是实现了基于动态数组的数据结构，而LinkedList是基于链表的数据结构
2. 对于随机访问get和set，ArrayList要优于LinkedList，因为LinkedList要移动指针
3. 对于添加和删除操作add和remove，ArrayList要移动数据；LinkedList的添加和删除是O(1)的，但是寻找元素需要时间，它是利用折半的方法查找的，如果index小于size的一半就从前往后，反之从后往前。总的来说LinkedList略占优势。

## 数组或者容器的最大长度

数组的length是int类型，最大值为2的31次方-1，当设置了这个值后会导致内存溢出。那么实际的最大长度是多少呢？这个和虚拟机的参数有关，可以通过设置参数来更改内存最大值。

## LinkedList

LinkedList源码很简单，见[LinkedList源码分析](/Applications/Projects/Blog/源码分析/LinkedList源码分析.md)

> transient 关键字
>
> 1）一旦变量被transient修饰，变量将不再是对象持久化的一部分，该变量内容在序列化后无法获得访问。
>
> 2）transient关键字只能修饰变量，而不能修饰方法和类。注意，本地变量是不能被transient关键字修饰的。变量如果是用户自定义类变量，则该类需要实现Serializable接口。
>
> 3）被transient关键字修饰的变量不再能被序列化，一个静态变量不管是否被transient修饰，均不能被序列化。

# 几个问题

## 重载和重写的区别

### 重写

重写是子类对父类的允许访问的方法的实现过程进行重新编写，返回值和形参都不能改变。

#### 方法的重写规则

- 参数列表必须完全与被重写方法的相同；

- 返回类型必须完全与被重写方法的返回类型相同；

- 访问权限不能比父类中被重写的方法的访问权限更低。例如：如果父类的一个方法被声明为public，那么在子类中重写该方法就不能声明为protected。

- 父类的成员方法只能被它的子类重写。

- 声明为final的方法不能被重写。

- 声明为static的方法不能被重写，但是能够被再次声明。
  语法上子类允许出现和父类只有方法体不一样其他都一模一样的static方法，但是在父类引用指向子类对象时，通过父类引用调用的依然是父类的static方法，而不是子类的static方法。

  即：语法上static支持重写，但是运行效果上达不到多态目的

- 子类和父类在同一个包中，那么子类可以重写父类所有方法，除了声明为private和final的方法。

- 子类和父类不在同一个包中，那么子类只能够重写父类的声明为public和protected的非final方法。

- 重写的方法能够抛出任何非强制异常，无论被重写的方法是否抛出异常。但是，重写的方法不能抛出新的强制性异常，或者比被重写方法声明的更广泛的强制性异常，反之则可以。

- 构造方法不能被重写。

- 如果不能继承一个方法，则不能重写这个方法。

### 重载

重载是在一个类里面，方法名字相同，而参数不同。返回类型可以相同也可以不同。

#### 重载规则

- 被重载的方法必须改变参数列表(参数个数或类型或顺序不一样)
- 被重载的方法可以改变返回类型
- 被重载的方法可以改变访问修饰符
- 被重载的方法可以声明新的或更广的检查异常
- 无法以返回值类型作为重载函数的区分标准

```java
class OverloadMethods {
    public static void main(String[] args) {
        overloadMethod(1);
    }

    private static void overloadMethod(){
        System.out.println("无参方法");
    }

    private static void overloadMethod(int i){
        System.out.println("参数为int的方法");
    }

    private static void overloadMethod(Integer i){
        System.out.println("参数为Integer的方法");
    }

    private static void overloadMethod(int... ints){
        System.out.println("参数为int[]的方法");
    }

    private static void overloadMethod(Integer... integers){
        System.out.println("参数为Integer[]的方法");
    }

    private static void overloadMethod(Object o){
        System.out.println("参数为Object的方法");
    }
}

output:
参数为int的方法

将int注释：
参数为Integer的方法

如上，并将Integer注释：
参数为Object的方法

如上，并将Object注释：
错误: 对overloadMethod的引用不明确
OverloadMethods 中的方法 overloadMethod(int...) 和 OverloadMethods 中的方法 overloadMethod(Integer...) 都匹配

如上，并将Integer[]注释：
参数为int[]的方法
```

```
public static void main(String[] args) {
    overloadMethod(1);
}

private static void overloadMethod(int i){
    System.out.println("参数为int的方法");
}

private static void overloadMethod(long i){
    System.out.println("参数为long的方法");
}

output:
参数为int的方法
```

```
public static void main(String[] args) {
        overloadMethod(1.1);
    }

    private static void overloadMethod(float i){
        System.out.println("参数为float的方法");
    }

    private static void overloadMethod(double i){
        System.out.println("参数为double的方法");
    }
    
output:
1的时候
参数为float的方法

1.1的时候
参数为double的方法
```

JVM在重载方法中，选择合适的目标方法的顺序是：

1. 精确匹配。
2. 如果是基本数据类型，自动转换成更大表示范围的基本类型。
3. 通过自动拆箱与装箱。
4. 通过子类向上转型继承路线依次匹配。
5. 通过可变参数匹配。

## String、StringBuffer与StringBuilder的区别

String 字符串常量
StringBuffer 字符串变量（线程安全）
StringBuilder 字符串变量（非线程安全）

String 是不可变的对象，因此在每次对 String 类型进行改变的时候其实都等同于生成了一个新的 String 对象，然后将指针指向新的 String 对象。

在大部分情况下 StringBuilder > StringBuffer > String

## 抽象类和接口区别

> 个人总结
>
> 抽象类是是子类的一个模板，描述子类通用特性的，不能被实例化。只能继承一个抽象类。
>
> 接口是抽象方法的集合，一个类如果实现了接口，那么需要使用这些方法。可以实现多个接口。

### **抽象类**

抽象类是用来捕捉子类的通用特性的 。它不能被实例化，只能被用作子类的超类。抽象类是被用来创建继承层级里子类的模板。

#### 抽象类的意义

- 为其子类提供一个公共的类型
- 封装子类中得重复内容
- 定义抽象方法，子类虽然有不同的实现，但是定义是一致的

### **接口**

接口是抽象方法的集合。如果一个类实现了某个接口，那么它就继承了这个接口的抽象方法。这就像契约模式，如果实现了这个接口，那么就必须确保使用这些方法。接口只是一种形式，接口自身不能做任何事情。

#### 接口的意义

规范、扩展、回调

### **对比**

接口和抽象类都是不能被实例化的，但是可以定义引用变量指向实例对象。

| **参数**           | **抽象类**                                                   | **接口**                                           |
| ------------------ | ------------------------------------------------------------ | -------------------------------------------------- |
| 默认的方法实现     | 它可以有默认的方法实现                                       | 不能有，但在Java8之后允许default实现。             |
| 实现               | **extends**                                                  | **implements**                                     |
| 构造器             | 抽象类可以有构造器                                           | 接口不能有构造器                                   |
| 与正常Java类的区别 | 除了不能实例化抽象类之外，它和普通Java类没有任何区别         | 接口是完全不同的类型                               |
| 访问修饰符         | 抽象方法可以有**public**、**protected**和**default**这些修饰符 | **public static abstract**                         |
| main方法           | 抽象方法可以有main方法并且可以运行                           | 接口没有main方法，不能运行。                       |
| 多继承             | 抽象方法可以继承一个类和实现多个接口                         | 接口可以继承一个或多个其它接口                     |
| 添加新方法         | 如果往抽象类中添加新的方法，可以给它提供默认的实现。因此不需要改变你现在的代码。 | 如果往接口中添加方法，那么必须改变实现该接口的类。 |

抽象类在被继承时体现的是is-a关系，接口在被实现时体现的是can-do关系

### 应用场景

- 如果一些方法有默认实现，那么使用抽象类。
- 如果想实现多重继承，那么必须使用接口。
- 如果基本功能在不断改变，那么就需要使用抽象类。如果不断改变基本功能并且使用接口，那么就需要改变所有实现了该接口的类。

## 为什么不能在foreach中对元素进行add/remove操作(fail-fast原理)

因为会出现ConcurrentModificationException异常。之所以会抛出这个异常，是因为

foreach底层是用iterator来实现的。add/remove方法会改变一个成员变量modCount，而在获取iterator的时候会将modCount赋给expectedModCount，在遍历的时候如果发现这两者不等，那么就会异常，以防可能出现了并发问题。

### 正确的做法

[禁止在foreach循环里进行元素的remove-add操作](/Applications/Projects/Blog/源码分析/禁止在foreach循环里进行元素的remove-add操作.md)

## 代理

静态代理是代理类在运行时已经存在。

动态代理则与静态代理相反，通过反射机制动态地生成代理者的对象。

# 并发与多线程

**并发**是指在某个时间段内，多任务交替处理的能力。

每个CPU不可能只顾着执行某个进程，让其他进程一直处于等待状态。所以，CPU把可执行时间均匀地分成若干份，每个进程执行一段时间后， 记录当前的工作状态，释放相关的执行资源并进入等待状态，让其他进程抢占CPU资源。

**并行**是指同时处理多任务的能力。

目前，CPU已经发展为多核，可以同时执行多个互不依赖的指令及执行块。

并发与并行两个概念非常容易混淆，它们的核心区别在于进程是否同时执行。以KTV唱歌为例，并行指的是有多少人可以使用话筒同时唱歌；并发指的是同一个话筒被多个人轮流使用。

在并发环境下，由于程序的封闭性被打破，出现了以下特点:

1. 并发程序之间有相互制约的关系。直接制约体现为一个程序需要另一个程序的计算结果：间接制约体现为多个程序竞争共享资源，如处理器、缓冲区等。

2. 并发程序的执行过程是断断续的。程序需要记忆现场指令及执行点。

3. 当并发数设置合理并且CPU拥有足够的处理能力时，并发会提高程序的运行效率。

## Thread的一些方法

笔记：[线程池源码分析](https://mezzsy.github.io/2019/08/29/源码分析/线程池源码分析/)。

|         方法          | 含义                                                         |
| :-------------------: | :----------------------------------------------------------- |
|        sleep()        | 让出CPU的使用，暂停阻塞等待一段时间，时间过了就继续。不释放锁。sleep必须捕获异常。 |
|        wait()         | 让出CPU的使用。Object中的方法。阻塞和等待，但是需要notify来唤醒。释放锁。wait，notify和notifyAll不需要捕获异常 |
|        join()         | 会释放锁，底层用了wait。在一个线程中调用other.join()，将等待other执行完后才继续本线程 |
| notify()、notifyAll() | Object中的方法。唤醒线程                                     |
|        yield()        | 当前线程可转让cpu控制权，让别的就绪状态线程运行（切换），也会等待阻塞一段时间，但是时间不是由客户控制了 |
|     interrupte()      | 打断线程，代替过时方法stop()                                 |
|     setPriority()     | MIN_PRIORITY 最小优先级=1 ， NORM_PRIORITY 默认优先级=5 ，MAX_PRIORITY 最大优先级=10 |

> 带参数的wait方法当超过了指定时间后会移除等待集合，开始竞争锁，而不带wait的方法会一直等待。demo见Java笔记。
>
> notifyAll()是将所有等待此锁的线程移出等待集合，开始竞争锁。而notify方法是选择一个移出等待集合，开始竞争锁。

**sleep和wait的区别**

1.  sleep()方法是属于Thread类的。wait()方法是属于Object类的。
2.  sleep()方法是让出cpu给其他线程，到了指定的时间又会恢复运行状态。在此期间，线程不会释放对象锁。
    调用wait()方法的时候，线程会放弃对象锁，进入等待此对象的等待锁定池，只有针对此对象调用notify()方法后本线程才进入对象锁定池准备获取对象锁进入运行状态。
3.  使用范围：wait，notify和notifyAll只能在同步控制方法或者同步控制块里面使用，而sleep可以在任何地方使用 

**notify和notifyAll的区别**

notify是随机唤醒一个线程，notifyAll是唤醒所有线程。

## 创建线程的方式

1. 继承Thread类重写run方法
2. 实现Runnable接口
3. 使用Callable（重写call方法）和Future配合线程池使用。
   线程池的submit方法传入Callable对象，返回Future对象。利用Future对象的get方法得到Callable中call方法返回的值。

如果Runnable和run方法都有呢？

如：

```java
MyThread myThread = new MyThread(myRunnable);
myThread.start();
```

Thread的run方法

```java
public void run() {
    if (target != null) {
        target.run();//target就是传入的Runnable
    }
}
```

Runnable的run方法是在Thread的run方法调用的。

Thread子类如果没有调用super.run()方法，那么传入的Runnable对象的run方法不会被调用。

## 线程池介绍

线程池的优点：

1. 重用线程池中的线程，避免因为线程的创建和销毁所带来的性能开销。
2. 能有效控制线程池的最大并发数，避免大量的线程之间因互相抢占系统资源而导致阻塞。
3. 能对线程进行简单的管理，并提供定时执行以及指定间隔循环执行等功能。

Android中最常见的四类具有不同功能特性的线程池，都是用ThreadPoolExecutor直接或间接实现自己的特性的：FixedThreadPool、CachedThreadPool、ScheduledThreadPool、SingleThreadExecutor。

## 线程池的分类

核心线程指不会被回收的线程。非核心线程指最大线程数减核心线程数，会被回收。

**FixedThreadPool：**

- 线程数量固定（需用户指定），当线程处于空闲状态也不会被回收，除非线程池被关闭。
- 只有核心线程，并且没有超时机制，另外任务队列没有大小限制。

**CachedThreadPool：**

- 线程数量不定，只有非核心线程，最大的线程数为Integer.MAX_VALUE
- 空闲线程具有超时机制，超过60秒就会被回收。
- 适合大量耗时少的任务。

**ScheduledThreadPool：**

- 核心线程数量固定，非核心线程没有限制，非核心线程闲置时会被立即回收。
- 主要用于执行定时任务和具有固定周期的重复任务。

**SingleThreadExecutor：**

- 只有一个核心线程，确保所有的任务都在同一个线程按顺序执行
- 意义在于统一所有的外界任务到一个线程，使得不需要处理同步问题。

## 线程间的通信

一般指wait/nofityAll和await/signalAll，这两者的用法可以见Java笔记。

## 有三个线程T1，T2，T3，怎么确保它们按顺序执行

可以用线程类的join()方法在一个线程中启动另一个线程，另外一个线程完成该线程继续执行。为了确保三个线程的顺序你应该先启动最后一个(T3调用T2，T2调用T1)，这样T1就会先完成而T3最后完成。

```java
public class Main {

    public static void main(String[] args) {
        MyThread thread1 = new MyThread(1, null);
        MyThread thread2 = new MyThread(2, thread1);
        MyThread thread3 = new MyThread(3, thread2);
        thread3.start();
        thread2.start();
        thread1.start();
        //输出123
    }

    private static class MyThread extends Thread {
        int id;
        Thread mThread;

        public MyThread(int id, Thread thread) {
            this.id = id;
            mThread = thread;
        }

        @Override
        public void run() {
            super.run();
            try {
                if (mThread != null)
                    mThread.join();
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
            System.out.println(id);
        }
    }

}
```

## 线程对象回收

```java
new Thread(new Runnable() {
    @Override
    public void run() {
        
    }
}).start();
```

以这种方式创建线程，并没有一个引用去引用这个对象，为什么线程对象不会被回收？

创建Thread对象时，它并没有捕获任何对这些对象的引用。在使用普通对象时，会被回收，但是在使用Thread时，情况就不同了。每个Thread都“注册”了它自己，因此确实有一个对它的引用，而且在它的任务退出其run并死亡之前，垃圾回收器无法清除它。

# 异常机制

见笔记[Java异常机制](/Users/mezzsy/Projects/Blog/Java/Java异常机制.md)

## 注意点

**finally语句在return语句执行之后return返回之前执行的**

```java
public static void main(String[] args) {
    System.out.println(test1());
}

private static int test1() {
    int b = 20;
    try {
        System.out.println("try block");
        return b += 80;
    } catch (Exception e) {
        System.out.println("catch block");
    } finally {
        System.out.println("finally block");
        if (b > 25) {
            System.out.println("b>25, b = " + b);
        }
    }
    return b + 10;
}

try block
finally block
b>25, b = 100
100
```

# 运算符

运算符可能有一些与常识冲突的地方

**模运算**

```
2%5=2
-2%5=-2
2%(-5)=2
-2%(-5)=-2
5%2=1
-5%2=-1
5%(-2)=1
-5%(-2)=-1
```

以上来自实验的log。

# 注解

## 元注解

- @Target
  表示该注解可以用于什么地方。可能的ElementType参数包括：

  - CONSTRUCTOR
    构造器的声明
  - FIELD
    域声明(包括enum实例)
  - LOCAL VARIABLE
    局部变量声明
  - METHOD
    方法声明
  - PACKAGE
    包声明
  - PARAMETER
    参数声明
  - TYPE
    类、接口(包括注解类型)或enum声明

- @Retention

  表示需要在什么级别保存该注解信息。可选的RetentionPolicy参数包括:

  - SOURCE
    注解将被编译器丢弃。
  - CLASS
    注解在class文件中可用，但会被VM丢弃。
  - RUNTIME
    VM将在运行期也保留注解，因此可以通过反射机制读取注解的信息。

- @Documented
  将此注解包含在Javadoc中。

- @Inherited
  使用此注解声明出来的自定义注解，在使用此自定义注解时，如果注解在类上面时，子类会自动继承此注解，否则的话，子类不会继承此注解。

