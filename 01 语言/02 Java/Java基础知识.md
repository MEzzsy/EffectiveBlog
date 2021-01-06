# 编译和运行过程

```java
//MainApp.java
public class MainApp {  
    public static void main(String[] args) {  
        Animal animal = new Animal("Puppy");  
        animal.printName();  
    }  
}  
//Animal.java 
public class Animal {  
    public String name;  
    public Animal(String name) {  
        this.name = name;  
    }  
    public void printName() {  
        System.out.println("Animal ["+name+"]");  
    }  
}  
```

**编译**

第一步(编译)：创建完源文件之后，程序会先被编译为class文件。Java编译一个类时，如果这个类所依赖的类还没有被编译，编译器就会先编译这个被依赖的类，然后引用，否则直接引用。如果java编译器在指定目录下找不到该类所依赖的类class文件的话，编译器会报“cant find symbol”的错误。

编译后的字节码文件格式主要分为两部分：**常量池**和**方法字节码**。常量池记录的是代码出现过的所有token(类名，成员变量名等等)以及符号引用（方法引用，成员变量引用等等）；方法字节码放的是类中各个方法的字节码。

**运行**

第二步（运行）：java类运行的过程大概可分为两个过程：1、类的加载  2、类的执行。

JVM主要在程序第一次主动使用类的时候，才会去加载该类。也就是说，JVM并不是在一开始就把一个程序就所有的类都加载到内存中，而是到不得不用的时候才把它加载进来，而且只加载一次。

下面是程序运行的详细步骤：

1. 在编译好java程序得到MainApp.class文件后，在命令行上敲java AppMain。系统就会启动一个jvm进程，jvm进程从classpath路径中找到一个名为AppMain.class的二进制文件，将MainApp的类信息加载到运行时数据区的方法区内，这个过程叫做MainApp类的加载。
2. 然后JVM找到AppMain的主函数入口，开始执行main函数。
3. main函数的第一条命令是Animal  animal = new Animal("Puppy");就是让JVM创建一个Animal对象，但是这时候方法区中没有Animal类的信息，所以JVM马上加载Animal类，把Animal类的类型信息放到方法区中。
4. 加载完Animal类之后，Java虚拟机做的第一件事情就是在堆区中为一个新的Animal实例分配内存，然后调用构造函数初始化Animal实例，这个Animal实例持有着指向方法区的Animal类的类型信息（其中包含有方法表，java动态绑定的底层实现）的引用。
5. 当使用animal.printName()的时候，JVM根据animal引用找到Animal对象，然后根据Animal对象持有的引用定位到方法区中Animal类的类型信息的方法表，获得printName()函数的字节码的地址。
6. 开始运行printName()函数。

# 编码

## 为什么要编码

- 计算机中存储信息的最小单元是`8bit`，所以能表示的字符范围是`0~255`个。
- 要表示的符号太多，无法用一个字节来完全表示。
- 要解决这个矛盾必须要一个新的数据结构`char`，从`char`到`byte`必须编码。

## 编码方式

- ASCII 码
    `ASCII`码总共有`128`个，用一个字节的低`7`位表示。
- ISO-8859-1
    在`ASCII`码基础上制定了一系列标准来扩展`ASCII`编码，其仍然是单字节编码，总共能表示`256`个字符。
- GB2312
    双字节编码，总的范围是`A1~F7`，从`A1~A9`是符号区，总共包含`682`个符号；从`B0~F7`是汉字区，包含`6763`个汉字。
- GBK
    扩展`GB2312`，加入更多的汉字，其编码范围是`8140~FEFE`，和`GB2312`兼容。
- GB18030
    我国的强制标准，可能是单字节、双字节或者四字节编码，与`GB2312`兼容。
- Unicode编码集
    `ISO`试图创建一个全新的语言字典，将所有的语言互相翻译。`String`在内存中 **不需要编码格式**，它只是一个`Unicode`字符串而已。只有当字符串需要在网络中传输或要被写入文件时，才需要编码格式。
    - UTF-16
        `UTF-16`具体定义了`Unicode`字符在计算机中的存取方法，它用两个字节表示`Unicode`转化格式。
    - UTF-8
        UTF-16的缺点在于很大部分字符仅用一个字节就可以表示，目前却需要使用两个，而UTF-8采用了变长技术，不同类型的字符可以由1~4个字节组成。 
        - 如果一个字节，最高位为`0`，表示这是一个`ASCII`字符。
        - 如果一个字节，以`11`开头，连续的`1`个数表示这个字符的字节数。
        - 如果一个字节，以`10`开始，表示它不是首字节，需要向前查找才能得到当前字符的首字节。

```
String s = "源"; 
//编码。
byte[] b = s.getBytes("UTF-8");
//解码。 
String n = new String(b,"UTF-8"); 
```

Unicode 为世界上所有字符都分配了一个唯一的数字编号，而UTF-8/16/32将编号表示成二进制。UTF-8/16/32 都是 Unicode 的一种实现。

## 对比

- `GB2312`与`GBK`编码规则类似，但是`GBK`范围更大，它能处理所有汉字字符。
- `UTF-16`和`UTF-8`都是处理`Unicode`编码，`UTF-16`效率更高，它适合在本地磁盘和内存之间使用。
- `UTF-16`不是在网络之间传输，因为网络传输容易损坏字节流，`UTF-8`更适合网络传输，对`ASCII`字符采用单字节存储，单字节损毁不会影响后面其它字符。

# 对象

## 引用

即使没有对象，引用也可以独立存在。比如创建一个String引用：

```java
String s;
```

这里创建的只是引用，不是对象。

# 操作符

## 取模运算

符号与被除数保持一致

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

**判断是否是偶数**

```java
/**
 * 测试是否为偶数
 */
private static void test2() {
    for (int i = -3; i <= 3; i++) {
        System.out.println(i + "是否是偶数：" + isEven(i));
    }
}

private static boolean isEven(int n) {
    return n % 2 == 0;
}

-3是否是偶数：false
-2是否是偶数：true
-1是否是偶数：false
0是否是偶数：true
1是否是偶数：false
2是否是偶数：true
3是否是偶数：false
```

没有问题。

**判断是否为奇数**

```java
/**
 * 测试是否为奇数
 */
private static void test3() {
    for (int i = -3; i <= 3; i++) {
        System.out.println(i + "是否是奇数：" + isOdd(i));
    }
}

private static boolean isOdd(int n) {
    return n % 2 == 1;
}

-3是否是奇数：false
-2是否是奇数：false
-1是否是奇数：false
0是否是奇数：false
1是否是奇数：true
2是否是奇数：false
3是否是奇数：true
```

如果判断奇数的方法是这样的：

```java
private static boolean isOdd(int n) {
    return n % 2 == 1;
}
```

那么结果就会出现问题，因为取模结果的符号与被除数有关。

正确的方法：

```java
private static boolean isOdd(int n) {
    return n % 2 != 0;
}

-3是否是奇数：true
-2是否是奇数：false
-1是否是奇数：true
0是否是奇数：false
1是否是奇数：true
2是否是奇数：false
3是否是奇数：true
```

## 短路现象

&&和||是短路的。

&&如果遇到false，那么后面的不再执行；||如果遇到true，那么后面的不再执行；|和&不管怎样都执行。

## 按位操作符

- **&**：与
- **|**：或
- **^**：异或
- **~**：非

有符号左移(<<)是在低位补0。

有符号右移(>>)是，如果是负数，高位补1，正数补0。

无符号右移(>>>)是高位补0。

```java
public static void main(String[] args) {
    int i = -1;
    // 1111 1111 1111 1111 1111 1111 1111 1111
    System.out.println(Integer.toBinaryString(i));
    i >>>= 10;
    // 11 1111 1111 1111 1111 1111
    System.out.println(Integer.toBinaryString(i));
    // 4194303
    System.out.println(i);
//-----------------------------------------------------------------
    long l = -1;
    // 1111 1111 1111 1111 1111 1111 1111 1111 1111 1111 1111 1111 1111 1111 1111 1111
    System.out.println(Long.toBinaryString(l));
    l >>>= 10;
    // 11 1111 1111 1111 1111 1111 1111 1111 1111 1111 1111 1111 1111 1111
    System.out.println(Long.toBinaryString(l));
    // 18014398509481983
    System.out.println(l);
//---------------------------------------------------------------   
    short s = -1;
    // 1111 1111 1111 1111 1111 1111 1111 1111
    System.out.println(Integer.toBinaryString(s));//这里被强转为int
    
    s >>>= 10;//如果对byte或short值进行移位运算，会先被转换成int类型，再进行右移操作，然后被截断，赋值给原来的类型。
    // 1111 1111 1111 1111 1111 1111 1111 1111
    System.out.println(Integer.toBinaryString(s));
    // 例：这里short -1的二进制为 1111 1111 1111 1111，转为int：1111 1111 1111 1111 1111 1111 1111 1111，无符号右移10，得到结果0000 0000 0011 1111 1111 1111 1111 1111，截断变为1111 1111 1111 1111，值为-1.
    // -1
    System.out.println(s);
    
    s = -1;
    s >>>= 20;
    // 1111 1111 1111
    System.out.println(Integer.toBinaryString(s));
    // 例：-1的二进制为 1111 1111 1111 1111，转为int：1111 1111 1111 1111 1111 1111 1111 1111，无符号右移20，得到结果0000 0000 0000 0000 0000 1111 1111 1111，截断变为0000 1111 1111 1111，值为4095.
    // 4095
    System.out.println(s);
//---------------------------------------------------------------   
    byte b = -1;
    // 1111 1111 1111 1111 1111 1111 1111 1111
    System.out.println(Integer.toBinaryString(b));
    b >>>= 10;
    // 1111 1111 1111 1111 1111 1111 1111 1111
    System.out.println(Integer.toBinaryString(b));
    b = -1;
    // 1111111111111111111111
    System.out.println(Integer.toBinaryString(b >>> 10));//这里由于没有赋值给b，没有截断，所以结果正确。
}
```

> 通过将比较小的类型传递给Integer的toBinaryString方法，则该类型会自动转为int。

如果使用无符号右移，得到的结果可能不正确：

```java
public static void main(String[] args) {
    byte b = -1;
    System.out.println(b);
    out.println(Integer.toBinaryString(b));
    b >>>= 24;
    System.out.println(b);
    out.println(Integer.toBinaryString(b));
    b = -1;
    b >>>= 25;
    System.out.println(b);
    out.println(Integer.toBinaryString(b));
    b = -1;
    b >>>= 26;
    System.out.println(b);
    out.println(Integer.toBinaryString(b));
}

-1
11111111111111111111111111111111
-1
11111111111111111111111111111111
127
1111111
63
111111
```

总结：比int短的类型进行位移操作时，先转为int，然后高低位添0/1，然后从低位截断成原来的类型。

## 类型转换

-   如果要执行窄化转换的操作(也就是说，将能容纳更多信息的数据类型转换成无法容纳那么多信息的类型)，就有可能面临信息丢失的危险。此时，需要强制进行类型转换。
    对于扩展转换，则不必显式地进行类型转换，因为新类型肯定能容纳原来类型的信息，不会造成任何信息的丢失。

-   布尔类型不能进行类型转换。

-   在将float或double转型为整型值时，总是对该数字执行截尾（如0.7变为0，0.4也是0）。如果想要得到四舍五入的结果，就需要使用java.lang.Math中的round方法。
-   表达式中出现的最大的数据类型决定了表达式最终结果的数据类型。如果将一个float值与一个double值相乘，结果就是double；如果将一个int和一个long值相加，则结果为long。

### int和char

```java
int i = 100;
char c = 'a';
System.out.println((char) i);
System.out.println(c);
System.out.println((int) c);

d
a
97
```

### short、byte和char的运算

在char、byte和short中， 使用算术操作符会有数据类型提升的效果。对这些类型的任何一个进行算术运算，都会获得一个int结果， 必须将其显式地类型转换回原来的类型(窄化转换可能会造成信息的丢失)，以将值赋给原本的类型。但对于int值，却不必进行类型转化，因为所有数据都已经属于int类型。

```java
public static void main(String[] args) {
    short a = 1;
    short b = 2;
    short c = (short) (a + b);//必须显式地类型转换
}
```

# 控制执行流程

## 迭代

Java的迭代有for、foreach、Iterator的方式，for很好理解，这里看一下foreach和Iterator的区别：

**Java代码**

```java
/**
 * Iterator迭代
 */
private static void iterator1() {
    ArrayList<Integer> list = new ArrayList<>();
    list.add(1);

    Iterator<Integer> iterator = list.iterator();
    while (iterator.hasNext()) {
        System.out.println(iterator.next());
    }
}

/**
 * foreach迭代
 */
private static void iterator2() {
    ArrayList<Integer> list = new ArrayList<>();
    list.add(1);

    for (Integer i : list) {
        System.out.println(i);
    }
}
```

编译成class文件后，利用IDEA进行查看：

```java
private static void iterator1() {
    ArrayList var0 = new ArrayList();
    var0.add(1);
    Iterator var1 = var0.iterator();

    while(var1.hasNext()) {
        System.out.println(var1.next());
    }

}

private static void iterator2() {
    ArrayList var0 = new ArrayList();
    var0.add(1);
    Iterator var1 = var0.iterator();

    while(var1.hasNext()) {
        Integer var2 = (Integer)var1.next();
        System.out.println(var2);
    }

}
```

可以看到对于可以使用Iterator的集合来说，foreach和Iterator底层实现上是一样的。

数组没有Iterator的方式，这里看看数组的for和foreach的区别。

**java代码**

```java
/**
 * for方式
 */
private static void forr() {
    int[] ints = new int[10];

    for (int i = 0; i < ints.length; i++) {
        System.out.println(ints[i]);
    }
}

/**
 * foreach方式
 */
private static void foreach() {
    int[] ints = new int[10];

    for (int anInt : ints) {
        System.out.println(anInt);
    }
}
```

**class文件**

```java
private static void forr() {
    int[] var0 = new int[10];

    for(int var1 = 0; var1 < var0.length; ++var1) {
        System.out.println(var0[var1]);
    }

}

private static void foreach() {
    int[] var0 = new int[10];
    int[] var1 = var0;
    int var2 = var0.length;

    for(int var3 = 0; var3 < var2; ++var3) {
        int var4 = var1[var3];
        System.out.println(var4);
    }

}
```

可以看到，foreach这里先是获取数组长度，然后再利用for进行迭代，所以对于数组的迭代，for和foreach在底层上也是一样的。

### 小结

对于容器的迭代，foreach和Iterator在底层实现上是一样的。

对于数组的迭代，for和foreach在底层实现上是一样的。

## goto

goto虽然是Java的关键字，但是Java没有使用goto。Java的跳转是利用标签：

```java
TAG1:
for (int i = 0; i < 10; i++) {
    for (int j = 0; j < 20; j++) {
        if (i == 5 && j == 10) {
            break TAG1;
        }
    }
}
```

在for的头上加一个标签。break 标签很好理解，这里看一下continue 标签的结果：

```java
public static void main(String[] args) {

    TAG1:
    for (int i = 0; i < 3; i++) {
        for (int j = 0; j < 4; j++) {
            if (i == 1 && j == 2) {
                continue TAG1;
            }
            System.out.println(i + ":" + j);
        }
    }
}
```

out:

```
0:0
0:1
0:2
0:3
1:0
1:1
2:0
2:1
2:2
2:3
```

依然很好理解。

## switch

switch要求使用一个选择因子，并且必须是int或char那样的整数值。例如，假如将一个字符串（Java8以后可以）或者浮点数作为选择因子使用，那么它们在switch语句里是不会工作的。

<img src="assets/11.jpg" alt="11" style="zoom:50%;" />

看一下demo了解一下switch：

**demo1，顺序的case：**

```java
public static void main(String[] args) {
    for (int i = 0; i < 5; i++) {
        switch (i) {
            case 5:
                System.out.println(5);
            case 4:
                System.out.println(4);
            case 3:
                System.out.println(3);
            case 2:
                System.out.println(2);
            case 1:
                System.out.println(1);
            default:
                System.out.println("default");
                break;
        }
        System.out.println("------------");
    }
}
```

output：

```
default
------------
1
default
------------
2
1
default
------------
3
2
1
default
------------
4
3
2
1
default
------------
```

**demo2，乱序的case：**

```java
public static void main(String[] args) {
    for (int i = 1; i < 6; i++) {
        switch (i) {
            default:
                System.out.println("default");
                break;
            case 4:
                System.out.println(4);
            case 5:
                System.out.println(5);
            case 1:
                System.out.println(1);
            case 3:
                System.out.println(3);
            case 2:
                System.out.println(2);
        }
        System.out.println("------------");
    }
}
```

output：

```
1
3
2
------------
2
------------
3
2
------------
4
5
1
3
2
------------
5
1
3
2
------------
```

对应的字节码：

```
 public static void main(java.lang.String[]);
    Code:
       0: iconst_1
       1: istore_1
       2: iload_1
       3: bipush        6
       5: if_icmpge     104
       8: iload_1
       9: tableswitch   { // 1 to 5
                     1: 69
                     2: 83
                     3: 76
                     4: 55
                     5: 62
               default: 44
          }
      44: getstatic     #2                  // Field java/lang/System.out:Ljava/io/PrintStream;
      47: ldc           #3                  // String default
      49: invokevirtual #4                  // Method java/io/PrintStream.println:(Ljava/lang/String;)V
      52: goto          90
      55: getstatic     #2                  // Field java/lang/System.out:Ljava/io/PrintStream;
      58: iconst_4
      59: invokevirtual #5                  // Method java/io/PrintStream.println:(I)V
      62: getstatic     #2                  // Field java/lang/System.out:Ljava/io/PrintStream;
      65: iconst_5
      66: invokevirtual #5                  // Method java/io/PrintStream.println:(I)V
      69: getstatic     #2                  // Field java/lang/System.out:Ljava/io/PrintStream;
      72: iconst_1
      73: invokevirtual #5                  // Method java/io/PrintStream.println:(I)V
      76: getstatic     #2                  // Field java/lang/System.out:Ljava/io/PrintStream;
      79: iconst_3
      80: invokevirtual #5                  // Method java/io/PrintStream.println:(I)V
      83: getstatic     #2                  // Field java/lang/System.out:Ljava/io/PrintStream;
      86: iconst_2
      87: invokevirtual #5                  // Method java/io/PrintStream.println:(I)V
      90: getstatic     #2                  // Field java/lang/System.out:Ljava/io/PrintStream;
      93: ldc           #6                  // String ------------
      95: invokevirtual #4                  // Method java/io/PrintStream.println:(Ljava/lang/String;)V
      98: iinc          1, 1
     101: goto          2
     104: return
```

在字节码层面上，switch是利用了goto的方式，先定义每个case的序号，对于每个i，获取对应的case的序号，然后执行goto语句，跳转到相应的case部分，由于没有break，按照字节码的执行流程，会继续执行下面的case部分。这也是为什么Java层面上，会继续执行后面的case语句。

# String

## 格式化输出

### printf

```java
public class Main {
    public static void main(String[] args) {
        /*** 输出字符串 ***/
        // %s表示输出字符串，也就是将后面的字符串替换模式中的%s
        System.out.printf("%s", "abc");
        // %n表示换行
        System.out.printf("%s%n", "end line");
        // 还可以支持多个参数
        System.out.printf("%s = %s%n", "Name", "Zhangsan");
        // %S将字符串以大写形式输出
        System.out.printf("%S = %s%n", "Name", "Zhangsan");
        // 支持多个参数时，可以在%s之间插入变量编号，1$表示第一个字符串，3$表示第3个字符串
        System.out.printf("%1$s = %3$s %2$s%n", "Name", "san", "Zhang");


        /*** 输出boolean类型 ***/
        System.out.printf("true = %b; false = ", true);
        System.out.printf("%b%n", false);


        /*** 输出整数类型***/
        Integer iObj = 342;
        // %d表示将整数格式化为10进制整数
        System.out.printf("%d; %d; %d%n", -500, 2343L, iObj);
        // %o表示将整数格式化为8进制整数
        System.out.printf("%o; %o; %o%n", -500, 2343L, iObj);
        // %x表示将整数格式化为16进制整数
        System.out.printf("%x; %x; %x%n", -500, 2343L, iObj);
        // %X表示将整数格式化为16进制整数，并且字母变成大写形式
        System.out.printf("%X; %X; %X%n", -500, 2343L, iObj);


        /*** 输出浮点类型***/
        Double dObj = 45.6d;
        // %e表示以科学技术法输出浮点数
        System.out.printf("%e; %e; %e%n", -756.403f, 7464.232641d, dObj);
        // %E表示以科学技术法输出浮点数，并且为大写形式
        System.out.printf("%E; %E; %E%n", -756.403f, 7464.232641d, dObj);
        // %f表示以十进制格式化输出浮点数
        System.out.printf("%f; %f; %f%n", -756.403f, 7464.232641d, dObj);
        // 还可以限制小数点后的位数
        System.out.printf("%.1f; %.3f; %f%n", -756.403f, 7464.232641d, dObj);


        /*** 输出日期类型***/
        // %t表示格式化日期时间类型，%T是时间日期的大写形式，在%t之后用特定的字母表示不同的输出格式
        Date date = new Date();
        long dataL = date.getTime();
        // 格式化年月日
        // %t之后用y表示输出日期的年份（2位数的年，如99）
        // %t之后用m表示输出日期的月份，%t之后用d表示输出日期的日号
        System.out.printf("%1$ty-%1$tm-%1$td; %2$ty-%2$tm-%2$td%n", date, dataL);
        // %t之后用Y表示输出日期的年份（4位数的年），
        // %t之后用B表示输出日期的月份的完整名， %t之后用b表示输出日期的月份的简称
        System.out.printf("%1$tY-%1$tB-%1$td; %2$tY-%2$tb-%2$td%n", date, dataL);

        // 以下是常见的日期组合
        // %t之后用D表示以 "%tm/%td/%ty"格式化日期
        System.out.printf("%1$tD%n", date);
        //%t之后用F表示以"%tY-%tm-%td"格式化日期
        System.out.printf("%1$tF%n", date);
        

        /*** 输出时间类型***/
        // 输出时分秒
        // %t之后用H表示输出时间的时（24进制），%t之后用I表示输出时间的时（12进制），
        // %t之后用M表示输出时间的分，%t之后用S表示输出时间的秒
        System.out.printf("%1$tH:%1$tM:%1$tS; %2$tI:%2$tM:%2$tS%n", date, dataL);
        // %t之后用L表示输出时间的秒中的毫秒
        System.out.printf("%1$tH:%1$tM:%1$tS %1$tL%n", date);
        // %t之后p表示输出时间的上午或下午信息
        System.out.printf("%1$tH:%1$tM:%1$tS %1$tL %1$tp%n", date);

        // 以下是常见的时间组合
        // %t之后用R表示以"%tH:%tM"格式化时间
        System.out.printf("%1$tR%n", date);
        // %t之后用T表示以"%tH:%tM:%tS"格式化时间
        System.out.printf("%1$tT%n", date);
        // %t之后用r表示以"%tI:%tM:%tS %Tp"格式化时间
        System.out.printf("%1$tr%n", date);
        

        /*** 输出星期***/
        // %t之后用A表示得到星期几的全称
        System.out.printf("%1$tF %1$tA%n", date);
        // %t之后用a表示得到星期几的简称
        System.out.printf("%1$tF %1$ta%n", date);

        // 输出时间日期的完整信息
        System.out.printf("%1$tc%n", date);
    }
}
/**
 *printf方法中,格式为"%s"表示以字符串的形式输出第二个可变长参数的第一个参数值;
 *格式为"%n"表示换行;格式为"%S"表示将字符串以大写形式输出;在"%s"之间用"n$"表示
 *输出可变长参数的第n个参数值.格式为"%b"表示以布尔值的形式输出第二个可变长参数
 *的第一个参数值.
 */
/**
 * 格式为"%d"表示以十进制整数形式输出;"%o"表示以八进制形式输出;"%x"表示以十六进制
 * 输出;"%X"表示以十六进制输出,并且将字母(A、B、C、D、E、F)换成大写.格式为"%e"表
 * 以科学计数法输出浮点数;格式为"%E"表示以科学计数法输出浮点数,而且将e大写;格式为
 * "%f"表示以十进制浮点数输出,在"%f"之间加上".n"表示输出时保留小数点后面n位.
 */
/**
 * 格式为"%t"表示输出时间日期类型."%t"之后用y表示输出日期的二位数的年份(如99)、用m
 * 表示输出日期的月份,用d表示输出日期的日号;"%t"之后用Y表示输出日期的四位数的年份
 * (如1999)、用B表示输出日期的月份的完整名,用b表示输出日期的月份的简称."%t"之后用D
 * 表示以"%tm/%td/%ty"的格式输出日期、用F表示以"%tY-%tm-%td"的格式输出日期.
 */
/**
 * "%t"之后用H表示输出时间的时(24进制),用I表示输出时间的时(12进制),用M表示输出时间
 * 分,用S表示输出时间的秒,用L表示输出时间的秒中的毫秒数、用 p 表示输出时间的是上午还是
 * 下午."%t"之后用R表示以"%tH:%tM"的格式输出时间、用T表示以"%tH:%tM:%tS"的格式输出
 * 时间、用r表示以"%tI:%tM:%tS %Tp"的格式输出时间.
 */
/**
 * "%t"之后用A表示输出日期的全称,用a表示输出日期的星期简称.
 */
```

### Formatter

当创建一个Formatter对象的时候，需要向其构造器传递一些信息， 告诉它最终的结果将向哪里输出，下面的例子是将结果输出到System.out中。

```java
public class Main {
    private Formatter mFormatter;

    public Main() {
        mFormatter = new Formatter(System.out);
    }

    public void printf(String s) {
        mFormatter.format("i am %S", s);//大写输出
    }

    public static void main(String[] args) {
        Main main = new Main();
        main.printf("zzsy");
    }
}
```

### 格式化说明符

格式修饰符的抽象的语法：

```
%[argument_index$][flags][width][.precision]conversion
```

-   argument_index$
    参数位置

-   width
    控制一个域的最小尺寸。Formatter对象通过在必要时添加空格，来确保一个域至少达到某个长度。在默认的情况下，数据是右对齐，不过可以通过使用“-”标志来改变对齐方向。
-   precision
    用来指明最大尺寸。width可以应用于各种类型的数据转换，并且其行为方式都一样。precision则不然，不是所有类型的数据都能使用precision，而且，应用于不同类型的数据转换时，precision的意义也不同。在将precision应用于String时，它表示打印String时输出字符的最大数量。而在将precision应用于浮点数时，它表示小数部分要显示出来的位数(默认是6位小数)，如果小数位数过多则舍入，太少则在尾部补零。由于整数没有小数部分，所以precision无法应用于整数，如果对整数应用precision，则会触发异常。

格式化在平时开发中用的不多，这里稍作记录，如果遇到，可以翻阅书籍进行查看。

## 正则表达式

[Java 正则表达式](https://www.runoob.com/java/java-regular-expressions.html)

>   正则表达式在LeetCode上用过几次，得出的结果很差，而且平时开发很少遇到，所以这里暂时略过。上面的链接是菜鸟教程的Java 正则表达式。

# 反射相关

[Java反射机制和泛型](Java反射机制和泛型.md)

# 泛型

[泛型](泛型.md)

# 数组

## 初始化方式

```java
public class Main {
    public static void main(String[] args) {
        A[] a = new A[]{new A(), new A(), new A()};
        
        A[] b = new A[4];
        for (int i = 0; i < b.length; i++) {
            b[i] = new A();
        }
    }

    private static class A {}
}
```

# Java I/O系统

可参考

https://www.jianshu.com/p/509c78602ed2

## File类

### 基本使用

```java
public static void main(String[] args) throws IOException {
        File file = new File("a");
//        File file = new File("G:\\AndroidProject\\AAAADemo\\Learn\\a");//可以使用反斜杠，但是要转义
//        File file = new File("G:/AndroidProject/AAAADemo/Learn/a");//可以用斜杠
        //常用方法
        file.createNewFile();//创建文件，不调用就不会创建
//        file.renameTo(new File("b"));//重命名
        System.out.println("文件的绝对路径：" + file.getAbsolutePath());
        System.out.println("文件是否存在：" + file.exists());
        System.out.println("文件是否是文件：" + file.isFile());
        System.out.println("文件是否是文件夹：" + file.isDirectory());
        System.out.println("文件的最后修改时间：" + new Date(file.lastModified()));
        System.out.println("文件的大小：" + file.length());
        System.out.println("文件的文件名：" + file.getName());
        
        File dir = new File("G:\\AndroidProject\\AAAADemo\\Learn\\a");
        //路径中只要有一个没有，则不会创建整个目录树
        dir.mkdir();

        //不管路径是否存在，都会创建整个目录树
        dir.mkdirs();
}

output:
文件的绝对路径：G:\AndroidProject\AAAADemo\Learn\a
文件是否存在：true
文件是否是文件：true
文件是否是文件夹：false
文件的最后修改时间：Tue Jan 22 18:08:14 CST 2019
文件的大小：0
文件的文件名：a
```

File类既能代表一个特定文件的名称，又能代表一个目录下的一组文件的名称。

```java
//此目录下的文件：BufferedInputFile.java、out、something.txt、DirList.java

public class DirList {

    public static void main(String[] args) {
        File file = new File("G:\\AndroidProject\\AAAADemo\\" +
                "Learn\\app\\src\\main\\java\\com\\mezzsy\\learnsomething\\java\\chapter18");
        String[] list;
        list = file.list(new FilenameFilter() {
            @Override
            public boolean accept(File dir, String name) {
                return !name.contains("java");
            }
        });
        Arrays.sort(list, String.CASE_INSENSITIVE_ORDER);
        for (String s : list) {
            System.out.println(s);
        }
    }

}

output:
out
something.txt
```

FilenameFilter是一个接口，其中的accept方法决定哪些文件可以包含在列表中。

## 编码

```java
public static void main(String[] args) throws IOException {
    String data="我是zzsy啊";
    //编码
    byte[] datas=data.getBytes("GBK");

    //解码
    String msg=new String(datas,0,datas.length,"GBK");
    System.out.println(msg);

    //乱码
    //字节数不够
    String s1=new String(datas,0,datas.length-1,"GBK");
    //字符集不统一
    String s2=new String(datas,0,datas.length-1,"UTF-8");

    System.out.println(s1);
    System.out.println(s2);
}

output：
我是zzsy啊
我是zzsy�
����zzsy�
```

## 输入和输出

### **InputStream类型**

| 类                   | 功能                                                         | 构造器参数（如何使用）                                       |
| -------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| ByteArrayInputStream | 允许将内存的缓冲区当作InputStream使用                        | 缓冲区，字节将从中取出<br />作为一种数据源：将其与FilterInputStream对象相连以提供有用接口 |
| FileInputStream      | 用于从文件中读取信息                                         | 字符串，表示文件名、文件或FileDescriptor对象<br />作为一种数据源：将其与FilterInputStream对象相连以提供有用接口 |
| PipedInputStream     | 产生用于写入相关PipedOutputStream的数据。实现“管道化”概念    | PipedOutputStream<br />作为多线程中数据源：将其与FiterlnputStream对象相连以提供有用接口 |
| SequenceInputStream  | 将两个或多个InputStream对象转换成单一InputStream             | 两个InpuSream对象或一个容纳InputStmam对象的容器Enumeration<br />作为一种数据源：将其与FilterlputStream对象相连以提供有用接口 |
| FilterInputStream    | 抽象类，作为“装饰器”的接口。其中，“装饰器”为其他的InputStream类提供有用功能。 |                                                              |

### **OutputStream类型**

| 类                    | 功能                                                         | 构造器参数（如何使用）                                       |
| --------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| ByteArrayOutputStream | 在内存中创建缓冲区。所有送往“流”的数据都要放置在此缓冲区     | 缓冲区初始化尺寸(可选的)<br/>用于指定数据的目的地：将其与FilterOutputStream对象相连以提供有用接口 |
| FileOutputStream      | 用于将信息写至文件                                           | 字符串，表示文件名、文件或FileDescriptor对象<br/>指定数据的目的地：将其与FilterOutputStream对象相连以提供有用接口 |
| PipedOutputStream     | 任何写入其中的信息都会自动作为相关PipedInputStream的输出。实现“管道化”概念。 | PipedInputStream<br/>指定用于多线程的数据的目的地：将其与FilterOutputStream对象相连以提供有用接口 |
| FilterOutputStream    | 抽象类，作为“装饰器”的接口。其中，“装饰器”为其他OutputStream提供有用功能。 |                                                              |

## 添加属性和有用的接口

### FilterInputStream类型

| 类                    | 功能                                                         | 构造器参数（如何使用）                                       |
| --------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| DataInputStream       | 与DataOutputStream搭配使用，可以按照可移植方式从流读取基本数据类型(int，char，long等) | InputStream<br/><br/>包含用于读取基本类型数据的全部接口      |
| BufferedInputStream   | 使用它可以防止每次读取时都得进行实际写操作。代表“使用缓冲区” | InputStream，可以指定缓冲区大小(可选的)<br/>本质上不提供接口，只不过是向进程中添加缓冲区所必需的。与接口对象搭配 |
| LineNumberInputStream | 跟踪输入流中的行号；可调用getLineNumber和setLineNumber(int)  | InputStream<br/>仅增加了行号，因此可能要与接口对象搭配使用   |

### FilterOutputStream类型

| 类               | 功能                                                         | 构造器参数（如何使用）                                       |
| ---------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| DataOutputStream | 与DataInputStream 搭配使用，因此可以按照可移植方式向流中写入基本类型数据(int, char, long等) | OutputStream包含用于写入基本类型数据的全部接口               |
| PrintStream      | 用于产生格式化输出。其中DataOut-putStream处理数据的存储，PrintStream处理显示 | OutputStream，可以用boolean值指示是否在每次换行时清空缓冲区(可选的)应该是对OutputStream对象的“final”封装。可能会经常使用到它。 |

## I/O流的典型使用方式

### 缓冲输入文件

```java
private static String bufferedRead(String fileName) {
    BufferedReader in = null;
    StringBuilder sb = new StringBuilder();
    try {
        in = new BufferedReader(new FileReader(fileName));
        String s;
        while ((s = in.readLine()) != null) {
            sb.append(s).append('\n');
        }
    } catch (IOException e) {
        if (in != null) {
            try {
                in.close();
            } catch (IOException e1) {
                e1.printStackTrace();
            }
        }
        e.printStackTrace();
    }
    return sb.toString();
}
```

### 从内存输入

```java
StringReader reader=new StringReader(bufferedRead(fileName));
int c;
while ((c=reader.read())!=-1){
    System.out.print((char) c);
}
```

### 格式化的内存输入

```java
DataInputStream in = new DataInputStream(new BufferedInputStream(new FileInputStream(fileName)));
while (in.available() != 0) {
    System.out.print((char) in.readByte());
}
```

### 基本的文件输出

```java
BufferedReader in = new BufferedReader(new StringReader(bufferedRead(fileName)));
PrintWriter writer = new PrintWriter(new BufferedWriter(new FileWriter(file)));
int lineNum = 1;
String s;
while ((s = in.readLine()) != null) {
    writer.println((lineNum++) + " : " + s);
}
writer.close();
```

一种快捷方式

```java
BufferedReader in = new BufferedReader(new StringReader(bufferedRead(fileName)));
PrintWriter writer = new PrintWriter(file);
int lineNum = 1;
String s;
while ((s = in.readLine()) != null) {
    writer.println((lineNum++) + " : " + s);
}
writer.close();
```

不必执行所有的装饰操作。

## Java NIO

[JavaNIO](JavaNIO.md)

## 压缩

Java I/O类库中的类支持读写压缩格式的数据流。可以用它们对其他的I/O类进行封装，以
提供压缩功能。

| 压缩类               | 功能                                                    |
| -------------------- | ------------------------------------------------------- |
| CheckedInputStream   | GetCheckSum( )为任何InputStream产生校验和(不仅是解压缩) |
| CheckedOutputStream  | GetCheckSum( )为任何OutputStream产生校验和(不仅是压缩)  |
| DeflaterOutputStream | 压缩类的基类                                            |
| ZipOutputStream      | 一个DeflaterOutputStream，用于将数据压缩成Zip文件格式   |
| GZIPOutputStream     | 一个DeflaterOutputStream，用于将数据压缩成GZIP文件格式  |
| InflaterInputStream  | 解压缩类的基类                                          |
| ZipInputStream       | 一个InflaterInputStream，用于解压缩Zip文件格式的数据    |
| GZIPInputStream      | 一个InflaterInputStream，用于解压缩GZIP文件格式的数据   |

### zip

自己写的一个压缩解压的工具类：

```java
package com.mezzsy.learnsomething.java.chapter18;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.Enumeration;
import java.util.zip.Adler32;
import java.util.zip.CheckedOutputStream;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;
import java.util.zip.ZipOutputStream;

/**
 * 压缩和解压缩的工具类
 *
 * @author mezzsy
 * @date 2019-10-12
 */
public class ZipUtil {
    @SuppressWarnings("UnnecessaryLocalVariable")
    public static void main(String[] args) {
        ZipUtil demo = new ZipUtil();
        String zipSrc = "/Users/mezzsy/Downloads/ziptest";
        String zipDst = "/Users/mezzsy/Downloads/res/ziptest.zip";
        demo.zip(zipSrc, zipDst);

        String unzipSrc = zipDst;
        String unZipDst = "/Users/mezzsy/Downloads/unziptest";
        demo.unzip(unzipSrc, unZipDst);
    }


    /**
     * 解压缩
     */
    public void unzip(String srcPath, String dsrPath) {
        System.out.println("开始解压");
        long startTime = System.currentTimeMillis();

        File file = new File(srcPath);
        if (!file.exists()) {
            System.out.println("文件不存在");
            return;
        }
        if (srcPath.length() < 4 || !(srcPath.substring(srcPath.length() - 4).equals(".zip"))) {
            System.out.println("文件格式错误，需要zip格式");
            return;
        }
        File dstFile = new File(dsrPath);
        if (dstFile.exists()) {
            if (dstFile.isFile()) {
                System.out.println("目的路径不能为文件");
                return;
            }
        }

        ZipFile zipFile = null;
        try {
            zipFile = new ZipFile(srcPath);
            Enumeration<? extends ZipEntry> enumeration = zipFile.entries();
            while (enumeration.hasMoreElements()) {
                ZipEntry zipEntry = enumeration.nextElement();
                unzip(zipEntry, dsrPath, zipFile);
            }
            System.out.println("解压成功");
        } catch (IOException e) {
            System.out.println("解压失败");
        } finally {
            closeStream(zipFile);
            System.out.println("解压结束，耗时：" + (System.currentTimeMillis() - startTime) + "ms");
        }
    }

    private void unzip(ZipEntry zipEntry, String path, ZipFile zipFile) throws IOException {
        File file = new File(path + "/" + zipEntry.getName());
        if (zipEntry.isDirectory()) {
            boolean res = file.mkdirs();
            if (!res)
                System.out.println("目的文件夹创建失败");
        } else {
            if (!file.getParentFile().exists()) {
                file.getParentFile().mkdirs();
            }

            InputStream inputStream = null;
            FileOutputStream fileOutputStream = null;
            try {
                inputStream = zipFile.getInputStream(zipEntry);
                fileOutputStream = new FileOutputStream(file);
                byte[] bytes = new byte[2 * 1024];
                int len;
                while ((len = inputStream.read(bytes)) != -1) {
                    fileOutputStream.write(bytes, 0, len);
                }
            } finally {
                closeStream(fileOutputStream);
                closeStream(inputStream);
            }
        }
    }

    /**
     * 压缩
     */
    public void zip(String srcPath, String dstPath) {
        System.out.println("开始压缩");
        long startTime = System.currentTimeMillis();

        File file = new File(srcPath);
        if (!file.exists()) {
            System.out.println("文件不存在");
            return;
        }

        FileOutputStream fileOutputStream = null;
        CheckedOutputStream checkedOutputStream = null;
        ZipOutputStream zipOutputStream = null;

        try {
            fileOutputStream = new FileOutputStream(dstPath);
            // 用Checksum类来计算和校验文件的校验和。
            // 一共有两种Checksum类型: Adler32 (它快一些) 和CRC32 (慢一些，但更准确)。
            checkedOutputStream = new CheckedOutputStream(fileOutputStream, new Adler32());
            zipOutputStream = new ZipOutputStream(checkedOutputStream);

            zip(file, file.getName(), zipOutputStream);

            System.out.println("压缩成功");
        } catch (IOException e) {
            System.out.println("压缩失败");
        } finally {
            closeStream(zipOutputStream);
            closeStream(checkedOutputStream);
            closeStream(fileOutputStream);

            System.out.println("压缩结束，耗时：" + (System.currentTimeMillis() - startTime) + "ms");
        }
    }

    /**
     * @param file            需要压缩的文件或文件夹
     * @param name            文件在压缩包内的名字，如"demo/a.txt"会创建demo文件夹，并把a.txt放入
     * @param zipOutputStream
     * @throws IOException
     */
    private void zip(File file, String name, ZipOutputStream zipOutputStream) throws IOException {
        if (file.isFile()) {
            FileInputStream fileInputStream = null;
            try {
                byte[] bytes = new byte[2 * 1024];
                fileInputStream = new FileInputStream(file.getAbsolutePath());
                zipOutputStream.putNextEntry(new ZipEntry(name));

                int len;
                while ((len = fileInputStream.read(bytes)) != -1) {
                    zipOutputStream.write(bytes, 0, len);
                }
            } finally {
                closeStream(fileInputStream);
            }
        } else {
            File[] files = file.listFiles();
            //空文件夹的情形
            if (files == null || files.length <= 0) {
                zipOutputStream.putNextEntry(new ZipEntry(name + "/"));
            } else {
                for (File listFile : file.listFiles()) {
                    //在文件前加所在文件夹的名称，否则会全部放入根目录下。
                    zip(listFile, name + "/" + listFile.getName(), zipOutputStream);
                }
            }
        }
    }

    private void closeStream(InputStream inputStream) {
        if (inputStream != null) {
            try {
                inputStream.close();
            } catch (IOException e) {
                System.out.println("出现故障");
            }
        }
    }

    private void closeStream(OutputStream outputStream) {
        if (outputStream != null) {
            try {
                outputStream.close();
            } catch (IOException e) {
                System.out.println("出现故障");
            }
        }
    }

    private void closeStream(ZipFile zipFile) {
        if (zipFile != null) {
            try {
                zipFile.close();
            } catch (IOException e) {
                System.out.println("出现故障");
            }
        }
    }
}
```

## 序列化

[Java序列化](Java序列化.md)

**简单demo**

```java
/**
 * 对象字节流
 */
private void objectTest() {
    byte[] bytes = new byte[0];
    try {
        ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
        ObjectOutputStream objectOutputStream = new ObjectOutputStream(byteArrayOutputStream);
        objectOutputStream.writeObject(new MyObject());
        bytes = byteArrayOutputStream.toByteArray();

        objectOutputStream.close();
    } catch (IOException e) {
        e.printStackTrace();
    }

    try {
        ByteArrayInputStream byteArrayInputStream = new ByteArrayInputStream(bytes);
        ObjectInputStream objectInputStream = new ObjectInputStream(byteArrayInputStream);
        MyObject object = (MyObject) objectInputStream.readObject();
        System.out.println(object);

        objectInputStream.close();
    } catch (IOException | ClassNotFoundException e) {
        e.printStackTrace();
    }
}

public class MyObject implements Serializable {
    private static final long serialVersionUID = -9168771153015225028L;

    public int id;
}
```

# 枚举

## 基本使用

```java
enum MyEnum{
    ONE,TWO,THREE
}
```

为了使用enum，需要创建一个该类型的引用，并将其赋值给某个实例：

```java
public static void main(String[] args) {
    MyEnum one = MyEnum.ONE;
    MyEnum two = MyEnum.TWO;
    MyEnum three = MyEnum.THREE;
}
```

在创建enum时，编译器会自动添加一些有用的特性。例如，它会创建toString方法，以便显示某个enum实例的名字。编译器还会创建ordinal方法，用来表示某个特定enum常量的声明顺序，以及static values方法（values方法是在编译期间添加的一个静态方法），用来按照enum常量的声明顺序，产生由这些常量值构成的数组：

```java
public static void main(String[] args) {
    for (MyEnum value : MyEnum.values()) {
        System.out.println(value.ordinal() + ":" + value);
    }
}
```

output

```
0:ONE
1:TWO
2:THREE
```

enum可以和switch配合使用。

```java
enum Str {
    A("a"), B("b"), C("c"), D("d");

    String s;

    Str(String s) {
        this.s = s;
    }

    public String getS() {
        return s;
    }
}
```

可以在枚举类中添加一些构造器。方法和域。构造器只是在调用枚举常量的时候调用（即只能为**private**）。

## 添加方法

除了不能继承自一个enum之外，基本上可以将enum看作一个常规的类。

可以向enum中添加方法。甚至可以有main方法。

如果希望每个枚举实例能够返回对自身的描述，而不仅仅只是默认的toString实现（只能返回枚举实例的名字）。为此，可以提供一个构造器 ，专门负责处理这个额外的信息，然后添加一个方法，返回这个描述信息。

```java
public class Main {
    public static void main(String[] args) {
        for (MyEnum value : MyEnum.values()) {
            System.out.println(value.getContent());
        }
    }

    enum MyEnum {
        ONE("This is One"),
        TWO("This is Two"),
        THREE("This is Three");

        private String content;

        MyEnum(String content) {
            this.content = content;
        }

        public String getContent() {
            return content;
        }
    }
}
```

```
This is One
This is Two
This is Three
```

注意，如果打算定义方法，那么必须在enum实例序列的最后添加一个分号。同时，必须先定义enum实例。如果在定义enum实例之前定义了任何方法或属性，那么在编译时就会得到错误信息。

在这个例子中，虽然有意识地将enum的构造器声明为private，但对于它的可访问性而言，其实并没有什么变化，因为只能在enum定义的内部使用其构造器创建enum实例。一旦enum的定义结束，编译器就不允许使用其构造器来创建任何实例了。

还可以为每个实例添加方法：

```java
enum MyEnum {
    ONE {
        public void sayOne() {
            System.out.println("one");
        }
    },
    TWO {
        public void sayTwo() {
            System.out.println("two");
        }
    },
    THREE {
        public void sayThree() {
            System.out.println("three");
        }
    };
}
```

不过这样方法无法被外界调用，如果要用，需要这样：

```java
enum MyEnum {
    ONE {
        public void say() {
            System.out.println("one");
        }
    },
    TWO {
        public void say() {
            System.out.println("two");
        }
    },
    THREE {
        public void say() {
            System.out.println("three");
        }
    };

    abstract void say();
}
```

## 继承

所有的enum都继承自java.lang.Enum类。由于Java不支持多重继承，所以enum不能再继承其他类，然而，在创建一个新的enum时，可以同时实现一个或多个接口。

如果希望扩展原enum中的元素，需要用到接口。在一个接口的内部，创建实现该接口的枚举，以此将元素进行分组，可以达到将枚举元素分类组织的目的。

```java
interface Number {
    enum SmallNumber implements Number {
        ONE, TWO;
    }

    enum BigNumber implements Number {
        NiNE, TEN;
    }
}
```

## 使用EnumSet替代标志

Set是一种集合，只能向其中添加不重复的对象。enum也要求其成员都是唯一的， 所以enum看起来也具有集合的行为。不过，由于不能从enum中删除或添加元素。Java SE5引入EnumSet，是为了通过enum创建一种替代品，以替代传统的基于int的“位标志”。这种标志可以用来表示某种“开/关” 信息，不过，使用这种标志，最终操作的只是一些bit，而不是这些bit想要表达的概念，因此很容易写出令人难以理解的代码。

EnumSet的设计充分考虑到了速度因素，因为它必须与非常高效的bit标志相竞争(其操作
与HashSet相比，非常地快)。就其内部而言，它(可能)就是将一个long值作为比特向量，所
以EnumSet非常快速高效。使用EnumSet的优点是，它在说明一个二进制位是否存在时，具有更好的表达能力，并且无需担心性能。

EnumSet中的元素必须来自一个enum。

```java
public class Main {
    public static void main(String[] args) {
        //创建空的set
        EnumSet<MyEnum> enumSet = EnumSet.noneOf(MyEnum.class);

        enumSet.add(MyEnum.ONE);
        System.out.println(enumSet);

        enumSet.addAll(EnumSet.allOf(MyEnum.class));
        System.out.println(enumSet);

        enumSet.remove(MyEnum.TWO);
        System.out.println(enumSet);
    }

    enum MyEnum {
        ONE, TWO, THREE
    }
}
```

```
[ONE]
[ONE, TWO, THREE]
[ONE, THREE]
```

## EnumMap

EnumMap是一种特殊的Map，它要求其中的键(key)必须来自一个enum。由于enum本身的限制，所以EnumMap在内部可由数组实现。因此EnumMap的速度很快，可以放心地使用enum实例在EnumMap中进行查找操作。不过，只能将enum的实例作为键来调用put方法，其他操作与使用一般的Map差不多。

# 注解

## 基本语法

### 元注解

Java目前只内置了三种标准注解以及四种元注解。

**标准注解**

1.  @Override
    表示当前的方法定义将覆盖超类中的方法。如果你不小心拼写错误，或者方法签名对不上被覆盖的方法，编译器就会发出错误提示。
2.  @Deprecated
    如果程序员使用了注解为它的元素，那么编译器会发出警告信息。
3.  @SuppressWarnings
    关闭不当的编译器警告信息。在Java SE5之前的版本中，也可以使用该注解，不过会被忽略不起作用。

**元注解**

-   @Target
    表示该注解可以用于什么地方。可能的ElementType参数包括：
    -   CONSTRUCTOR
        构造器的声明
    -   FIELD
        域声明(包括enum实例)
    -   LOCAL VARIABLE
        局部变量声明
    -   METHOD
        方法声明
    -   PACKAGE
        包声明
    -   PARAMETER
        参数声明
    -   TYPE
        类、接口(包括注解类型)或enum声明
-   @Retention
    表示需要在什么级别保存该注解信息。可选的RetentionPolicy参数包括：
    -   SOURCE
        注解将被编译器丢弃。
    -   CLASS
        注解在class文件中可用，但会被VM丢弃。
    -   RUNTIME
        VM将在运行期也保留注解，因此可以通过反射机制读取注解的信息。
-   @Documented
    将此注解包含在Javadoc中。
-   @Inherited
    使用此注解声明出来的自定义注解，在使用此自定义注解时，如果注解在类上面时，子类会自动继承此注解，否则的话，子类不会继承此注解。

### 定义注解

```java
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
@interface Test {   
}
```

除了@符号以外，@Test的定义很像一个空的接口。定义注解时，会需要一些元注解(meta-annotation)，如@Target和@Retention。@Target用来定义你的注解将应用于什么地方(例如是一个方法或者一个域)。@Rectetion用来定义该注解在哪一个级别可用，在源代码中(SOURCE)、类文件中(CLASS) 或者运行时(RUNTIME)。

没有元素的注解称为**标记注解**

```java
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
@interface Test {
    int id();

    String description() default "no description";
}
```

```java
public class Testable {
    @Test(id = 1)
    void testExecute() {
        execute();
    }

    @Test(id = 1, description = "haha")
    void testExecute2() {
        execute();
    }

    public void execute() {
        System.out.println("test");
    }
}
```

## 编写注解处理器

```java
class TestTracker {
    public static void track(Class<?> clazz) {
        for (Method method : clazz.getDeclaredMethods()) {
            Test test = method.getAnnotation(Test.class);
            if (test != null) {
                System.out.println("id = " + test.id() + ",description = " + test.description());
            }
        }
    }

    public static void main(String[] args) {
        track(Testable.class);
    }
}

output:
id = 1,description = no description
id = 1,description = haha
```

### 注解元素

注解元素可用的类型如下：

-   所有的基本类型。
-   String
-   Class
-   enum
-   Annotation
-   以上类型的数组

如果使用了其他类型，那么编译器会报错。

编译器对元素的默认值有些过分挑剔。首先，元素不能有不确定的值。也就是说，元素必须要么具有默认值，要么在使用注解时提供元素的值。

其次，对于非基本类型的元素，无论是在源代码中声明时，或是在注解接口中定义默认值时，都不能以null作为其值。这个约束使得处理器很难表现一个元素的存在或缺失的状态，因为在每个注解的声明中，所有的元素都存在，并且都具有相应的值。为了绕开这个约束，我们只能自己定义一些特殊的值，例如空字符串或负数，以此表示某个元素不存在。

**注解不支持继承。**

## apt处理注解

apt是Sun的一个库，Java库中没有，所以这里略过。

## 观察者模式

[自己写的仿EventBus](https://www.jianshu.com/p/84a8c438d0d3)

# 并发

[并发](并发.md)

[线程池归类总结](线程池归类总结.md)

# 字符串

## 格式化输出

```
public static void main(String[] args) {
    MyStringLearn demo = new MyStringLearn();
    demo.fPrintf();
}

private void fPrintf() {
    System.out.printf("%s is %d years old, he is %s's father\n", "zzsy", 20, "lmh");
    System.out.format("%s is %d years old, he is %s's father", "zzsy", 20, "lmh");
}

output:
zzsy is 20 years old, he is lmh's father
zzsy is 20 years old, he is lmh's father
```

| 字符 | 类型                 |
| ---- | -------------------- |
| d    | 整型                 |
| c    | Unicode字符          |
| b    | Boolean值            |
| s    | String               |
| f    | 浮点数（十进制）     |
| e    | 浮点数（科学计数法） |
| x    | 整数（十六进制）     |
| h    | 散列码（十六进制）   |

format方法模仿自C的printf方法。

### 格式化说明服符

```
%[argument_index$][flags][width][.precision]conversion
```

最常见的应用是控制一个域的最小尺寸，这可以通过指定width来实现。Formatter对象通过在必要时添加空格，来确保一个域至少达到某个长度。在默认的情况下，数据是右对齐，不过可以通过使用“-”标志来改变对齐方向。
与width相对的是precision，它用来指明最大尺寸。width可以应用于各种类型的数据转换，并且其行为方式都一样。precision则不然，不是所有类型的数据都能使用precision，而且，应用于不同类型的数据转换时，precision的意义也不同。在将precision应用于String时，它表示打印String时输出字符的最大数量。而在将precision应用于浮点数时，它表示小数部分要显示出来的位数（默认是6位小数），如果小数位数过多则舍人，太少则在尾部补零。由于整数没有小数部分，所以precision无法应用于整数，如果你对整数应用precision，则会触发异常。

```
private void fFormat() {
    System.out.format("%-5s %5s\n", "name", "price");
    System.out.format("%-5s %5s\n", "----", "----");
    System.out.format("%-5.5s %5.2f\n", "aaaaa", 1.12);
    System.out.format("%-5.5s %5.2f\n", "bbbb", 2.1);
    System.out.format("%-5.5s %5.2f\n", "cccccc", 3.123);
}

output:
name  price
----   ----
aaaaa  1.12
bbbb   2.10
ccccc  3.12
```

## 正则表达式

[Java正则表达式](Java正则表达式.md)

| 字符          | 说明                                                         |
| ------------- | ------------------------------------------------------------ |
| \             | 将下一字符标记为特殊字符、文本、反向引用或八进制转义符。例如，"n"匹配字符"n"。"\n"匹配换行符。序列"\\\\"匹配"\\"，"\\("匹配"("。 |
| ^             | 匹配输入字符串开始的位置。如果设置了 **RegExp** 对象的 **Multiline** 属性，^ 还会与"\n"或"\r"之后的位置匹配。 |
| $             | 匹配输入字符串结尾的位置。如果设置了 **RegExp** 对象的 **Multiline** 属性，$ 还会与"\n"或"\r"之前的位置匹配。 |
| *             | 零次或多次匹配前面的字符或子表达式。例如，zo* 匹配"z"和"zoo"。* 等效于 {0,}。 |
| +             | 一次或多次匹配前面的字符或子表达式。例如，"zo+"与"zo"和"zoo"匹配，但与"z"不匹配。+ 等效于 {1,}。 |
| ?             | 零次或一次匹配前面的字符或子表达式。例如，"do(es)?"匹配"do"或"does"中的"do"。? 等效于 {0,1}。 |
| {*n*}         | *n* 是非负整数。正好匹配 *n* 次。例如，"o{2}"与"Bob"中的"o"不匹配，但与"food"中的两个"o"匹配。 |
| {*n*,}        | *n* 是非负整数。至少匹配 *n* 次。例如，"o{2,}"不匹配"Bob"中的"o"，而匹配"foooood"中的所有 o。"o{1,}"等效于"o+"。"o{0,}"等效于"o*"。 |
| {*n*,*m*}     | *m* 和 *n* 是非负整数，其中 *n* <= *m*。匹配至少 *n* 次，至多 *m* 次。例如，"o{1,3}"匹配"fooooood"中的头三个 o。'o{0,1}' 等效于 'o?'。注意：您不能将空格插入逗号和数字之间。 |
| ?             | 当此字符紧随任何其他限定符（*、+、?、{*n*}、{*n*,}、{*n*,*m*}）之后时，匹配模式是"非贪心的"。"非贪心的"模式匹配搜索到的、尽可能短的字符串，而默认的"贪心的"模式匹配搜索到的、尽可能长的字符串。例如，在字符串"oooo"中，"o+?"只匹配单个"o"，而"o+"匹配所有"o"。 |
| .             | 匹配除"\r\n"之外的任何单个字符。若要匹配包括"\r\n"在内的任意字符，请使用诸如"[\s\S]"之类的模式。 |
| (*pattern*)   | 匹配 *pattern* 并捕获该匹配的子表达式。可以使用 **$0…$9** 属性从结果"匹配"集合中检索捕获的匹配。若要匹配括号字符 ( )，请使用"\("或者"\)"。 |
| (?:*pattern*) | 匹配 *pattern* 但不捕获该匹配的子表达式，即它是一个非捕获匹配，不存储供以后使用的匹配。这对于用"or"字符 (\|) 组合模式部件的情况很有用。例如，'industr(?:y\|ies) 是比 'industry\|industries' 更经济的表达式。 |
| (?=*pattern*) | 执行正向预测先行搜索的子表达式，该表达式匹配处于匹配 *pattern* 的字符串的起始点的字符串。它是一个非捕获匹配，即不能捕获供以后使用的匹配。例如，'Windows (?=95\|98\|NT\|2000)' 匹配"Windows 2000"中的"Windows"，但不匹配"Windows 3.1"中的"Windows"。预测先行不占用字符，即发生匹配后，下一匹配的搜索紧随上一匹配之后，而不是在组成预测先行的字符后。 |
| (?!*pattern*) | 执行反向预测先行搜索的子表达式，该表达式匹配不处于匹配 *pattern* 的字符串的起始点的搜索字符串。它是一个非捕获匹配，即不能捕获供以后使用的匹配。例如，'Windows (?!95\|98\|NT\|2000)' 匹配"Windows 3.1"中的 "Windows"，但不匹配"Windows 2000"中的"Windows"。预测先行不占用字符，即发生匹配后，下一匹配的搜索紧随上一匹配之后，而不是在组成预测先行的字符后。 |
| *x*\|*y*      | 匹配 *x* 或 *y*。例如，'z\|food' 匹配"z"或"food"。'(z\|f)ood' 匹配"zood"或"food"。 |
| [*xyz*]       | 字符集。匹配包含的任一字符。例如，"[abc]"匹配"plain"中的"a"。 |
| [^*xyz*]      | 反向字符集。匹配未包含的任何字符。例如，"[^abc]"匹配"plain"中"p"，"l"，"i"，"n"。 |
| [*a-z*]       | 字符范围。匹配指定范围内的任何字符。例如，"[a-z]"匹配"a"到"z"范围内的任何小写字母。 |
| [^*a-z*]      | 反向范围字符。匹配不在指定的范围内的任何字符。例如，"[^a-z]"匹配任何不在"a"到"z"范围内的任何字符。 |
| \b            | 匹配一个字边界，即字与空格间的位置。例如，"er\b"匹配"never"中的"er"，但不匹配"verb"中的"er"。 |
| \B            | 非字边界匹配。"er\B"匹配"verb"中的"er"，但不匹配"never"中的"er"。 |
| \c*x*         | 匹配 *x* 指示的控制字符。例如，\cM 匹配 Control-M 或回车符。*x* 的值必须在 A-Z 或 a-z 之间。如果不是这样，则假定 c 就是"c"字符本身。 |
| \d            | 数字字符匹配。等效于 [0-9]。                                 |
| \D            | 非数字字符匹配。等效于 [^0-9]。                              |
| \f            | 换页符匹配。等效于 \x0c 和 \cL。                             |
| \n            | 换行符匹配。等效于 \x0a 和 \cJ。                             |
| \r            | 匹配一个回车符。等效于 \x0d 和 \cM。                         |
| \s            | 匹配任何空白字符，包括空格、制表符、换页符等。与 [ \f\n\r\t\v] 等效。 |
| \S            | 匹配任何非空白字符。与 [^ \f\n\r\t\v] 等效。                 |
| \t            | 制表符匹配。与 \x09 和 \cI 等效。                            |
| \v            | 垂直制表符匹配。与 \x0b 和 \cK 等效。                        |
| \w            | 匹配任何字类字符，包括下划线。与"[A-Za-z0-9_]"等效。         |
| \W            | 与任何非单词字符匹配。与"[^A-Za-z0-9_]"等效。                |
| \x*n*         | 匹配 *n*，此处的 *n* 是一个十六进制转义码。十六进制转义码必须正好是两位数长。例如，"\x41"匹配"A"。"\x041"与"\x04"&"1"等效。允许在正则表达式中使用 ASCII 代码。 |
| \*num*        | 匹配 *num*，此处的 *num* 是一个正整数。到捕获匹配的反向引用。例如，"(.)\1"匹配两个连续的相同字符。 |
| \*n*          | 标识一个八进制转义码或反向引用。如果 \*n* 前面至少有 *n* 个捕获子表达式，那么 *n* 是反向引用。否则，如果 *n* 是八进制数 (0-7)，那么 *n* 是八进制转义码。 |
| \*nm*         | 标识一个八进制转义码或反向引用。如果 \*nm* 前面至少有 *nm* 个捕获子表达式，那么 *nm* 是反向引用。如果 \*nm* 前面至少有 *n* 个捕获，则 *n* 是反向引用，后面跟有字符 *m*。如果两种前面的情况都不存在，则 \*nm* 匹配八进制值 *nm*，其中 *n* 和 *m* 是八进制数字 (0-7)。 |
| \nml          | 当 *n* 是八进制数 (0-3)，*m* 和 *l* 是八进制数 (0-7) 时，匹配八进制转义码 *nml*。 |
| \u*n*         | 匹配 *n*，其中 *n* 是以四位十六进制数表示的 Unicode 字符。例如，\u00A9 匹配版权符号 (©)。 |

# Socket

[Socket](Socket.md)

# Java8

[Java8](Java8.md)

# 有效的Java

[有效的Java](有效的Java.md)

# 笔记来源

1.  《Java编程思想》
2.  菜鸟教程
3.  《Effective Java》
4.  《Java并发编程实战》

