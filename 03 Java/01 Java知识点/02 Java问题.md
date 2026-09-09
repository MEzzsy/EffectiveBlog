# 重载和重写的区别

## 重写

重写是子类对父类的允许访问的方法的实现过程进行重新编写，返回值和形参都不能改变。

### 方法的重写规则

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

## 重载

重载是在一个类里面，方法名字相同，而参数不同。返回类型可以相同也可以不同。

### 重载规则

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

# 为什么不能在foreach中对元素进行add/remove操作(fail-fast原理)

因为会出现ConcurrentModificationException异常。之所以会抛出这个异常，是因为foreach底层是用iterator来实现的。add/remove方法会改变一个成员变量modCount，而在获取iterator的时候会将modCount赋给expectedModCount，在遍历的时候如果发现这两者不等，那么就会异常，以防可能出现了并发问题。

如果没有modCount，在add/remove时，会导致迭代器的指针失效。
