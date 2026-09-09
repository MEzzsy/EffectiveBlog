# int和Integer

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

```java
private static void test21() {
    System.out.println(test21Fun1());
    System.out.println(test21Fun2());
}

private static int test21Fun1() {
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

private static int test21Fun2() {
    try {
        return 100;
    } catch (Exception e) {
        return 200;
    } finally {
        return 300;
    }
}
```

```
try block
finally block
b>25, b = 100
100
300
```

如果finally有return，最终会用finally的return。

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

以上来自实验的log。java模运算结果的符号取决于被模数。
