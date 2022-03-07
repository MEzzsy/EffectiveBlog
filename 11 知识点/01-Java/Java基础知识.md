# Object类相关

## java中==和equals和hashCode的区别

### ==

java中的数据类型，可分为两类：

1.  基本数据类型，也称原始数据类型
    byte,short,char,int,long,float,double,boolean之间的比较，应用双等号（==）,比较的是值。 

2.  引用类型(类、接口、数组) 
    当用（==）进行比较的时候，比较的是在内存中的存放地址，所以，除非是同一个new出来的对象，他们的比较后的结果为true，否则比较后结果为false。
    对象是放在堆中的，栈中存放的是对象的引用（地址）。由此可见'=='是对栈中的值进行比较的。如果要比较堆中对象的内容是否相同，那么就要重写equals方法了。

### equals

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
public class Human implements Cloneable {
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

```java
protected native Object clone() throws CloneNotSupportedException;
```

>   clone()是Object的一个方法。

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

# double数据比较

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

### 避免修改接口而实现同一个类中两种同名方法的调用

用于解决下面的困境：一个需要继承另一个类，还要实现一个接口，而继承的类和接口里面有两个同名的方法。那么我们调用该方法的时候，究竟是父类的，还是实现的接口呢，这时候就可以使用内部类来解决这一问题。

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

