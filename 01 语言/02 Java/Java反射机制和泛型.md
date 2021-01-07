# 简介

能够分析类能力的程序称为反射。反射机制可以用来：

- 在运行中分析类的能力
- 在运行中查看对象
- 实现通用的数组操作代码
- 利用Method对象，这个对象很像C++的函数指针

# Type接口详解

来源https://blog.csdn.net/lkforce/article/details/82466893

## Type的简介

`java.lang.reflect.Type`接口及其相关接口用于描述java中用到的所有类型，是Java的反射中很重要的组成部分。

**在API文档中，Type接口的说明如下：**

Type 是 Java 编程语言中所有类型的公共高级接口。它们包括原始类型、参数化类型、数组类型、类型变量和基本类型。

从JDK1.5开始使用。

**API中提到的Type的组成部分说明如下：**

- 原始类型：一般意义上的java类，由class类实现
- 参数化类型：ParameterizedType接口的实现类
- 数组类型：GenericArrayType接口的实现类
- 类型变量：TypeVariable接口的实现类
- 基本类型：int，float等java基本类型，其实也是class

> 不知道为什么在文档中介绍Type接口的组成时，没有包含WildcardType接口。

## Type的获得

有很多场景下我们可以获得Type，比如：

1. 当我们拿到一个Class，用`Class.getGenericInterfaces()`方法得到Type[]，也就是这个类实现接口的Type类型列表。
2. 当我们拿到一个Class，用`Class.getDeclaredFields()`方法得到Field[]，也就是类的属性列表，然后用`Field.getGenericType()`方法得到这个属性的Type类型。
3. 当我们拿到一个Method，用`Method.getGenericParameterTypes()`方法获得Type[]，也就是方法的参数类型列表。

## Type的分类

Type接口包含了一个实现类(Class)和四个实现接口(TypeVariable, ParameterizedType, GenericArrayType, WildcardType)，这四个接口都有自己的实现类，但这些实现类开发都不能直接使用，只能用接口。

在不同的场景下，java会使用上面五种实现类的其中一种，来解释要描述的类型。

下面详细解释一下java是怎么在这五种实现类中选择的。

以方法的参数为例，写一段示例代码，重点关注其中的test方法：

```java
class TypeLearn {
    public static void main(String[] args) {
        Method[] methods = TestReflect.class.getMethods();
        for (Method method : methods) {
            if (method.getName().equals("test")) {
                Type[] types = method.getGenericParameterTypes();

                //第一个参数，TestReflect p0
                Class type0 = (Class) types[0];
                System.out.println("type0:" + type0.getName());
                //type0:com.mezzsy.learnsomething.java.TypeLearn$TestReflect
                
                //第二个参数，List<TestReflect> p1
                Type type1 = types[1];
                Type[] parameterizedType1 = ((ParameterizedType) type1).getActualTypeArguments();
                Class parameterizedType1_0 = (Class) parameterizedType1[0];
                System.out.println("parameterizedType1_0:" + parameterizedType1_0.getName());
                //parameterizedType1_0:com.mezzsy.learnsomething.java.TypeLearn$TestReflect
                
                //第三个参数，Map<String,TestReflect> p2
                Type type2 = types[2];
                Type[] parameterizedType2 = ((ParameterizedType) type2).getActualTypeArguments();
                Class parameterizedType2_0 = (Class) parameterizedType2[0];
                System.out.println("parameterizedType2_0:" + parameterizedType2_0.getName());
                //parameterizedType2_0:java.lang.String
                Class parameterizedType2_1 = (Class) parameterizedType2[1];
                System.out.println("parameterizedType2_1:" + parameterizedType2_1.getName());
                //parameterizedType2_1:com.mezzsy.learnsomething.java.TypeLearn$TestReflect

                //第四个参数，List<String>[] p3
                Type type3 = types[3];
                Type genericArrayType3 = ((GenericArrayType) type3).getGenericComponentType();
                ParameterizedType parameterizedType3 = (ParameterizedType) genericArrayType3;
                Type[] parameterizedType3Arr = parameterizedType3.getActualTypeArguments();
                Class class3 = (Class) parameterizedType3Arr[0];
                System.out.println("class3:" + class3.getName());
                //class3:java.lang.String

                //第五个参数，Map<String,TestReflect>[] p4
                Type type4 = types[4];
                Type genericArrayType4 = ((GenericArrayType) type4).getGenericComponentType();
                ParameterizedType parameterizedType4 = (ParameterizedType) genericArrayType4;
                Type[] parameterizedType4Arr = parameterizedType4.getActualTypeArguments();
                Class class4_0 = (Class) parameterizedType4Arr[0];
                System.out.println("class4_0:" + class4_0.getName());
                //class4_0:java.lang.String
                Class class4_1 = (Class) parameterizedType4Arr[1];
                System.out.println("class4_1:" + class4_1.getName());
                //class4_1:com.mezzsy.learnsomething.java.TypeLearn$TestReflect

                //第六个参数，List<? extends TestReflect> p5
                Type type5 = types[5];
                Type[] parameterizedType5 = ((ParameterizedType) type5).getActualTypeArguments();
                Type[] parameterizedType5_0_upper = ((WildcardType) parameterizedType5[0]).getUpperBounds();
                Type[] parameterizedType5_0_lower = ((WildcardType) parameterizedType5[0]).getLowerBounds();

                //第七个参数，Map<? extends TestReflect,? super TestReflect> p6
                Type type6 = types[6];
                Type[] parameterizedType6 = ((ParameterizedType) type6).getActualTypeArguments();
                Type[] parameterizedType6_0_upper = ((WildcardType) parameterizedType6[0]).getUpperBounds();
                Type[] parameterizedType6_0_lower = ((WildcardType) parameterizedType6[0]).getLowerBounds();
                Type[] parameterizedType6_1_upper = ((WildcardType) parameterizedType6[1]).getUpperBounds();
                Type[] parameterizedType6_1_lower = ((WildcardType) parameterizedType6[1]).getLowerBounds();
            }
        }
    }

    private class TestReflect {

        public void test(
                TestReflect p0,
                List<TestReflect> p1,
                Map<String, TestReflect> p2,
                List<String>[] p3,
                Map<String, TestReflect>[] p4,
                List<? extends TestReflect> p5,
                Map<? extends TestReflect, ? super TestReflect> p6
        ) {
            System.out.println("hello world!!!");
        }

    }
}
```

我们需要关注的就是在类中定义的test方法，这个方法的7个参数基本上涵盖了Type能用到的所有类型。

所以在main方法中我们用反射得到了这个test方法，然后用`method.getGenericParameterTypes()`方法得到了test方法的所有参数类型，这是一个Type数组，数组中的每一个元素就是每个参数的类型，java为每一个Type选择了一个Type的实现类。

以此我们可以看到java是怎么在5种实现类中选择的。

### Class

当需要描述的类型是：

- 普通的java类（比如String，Integer，Method等等）
- 数组
- 自定义类（比如我们自己定义的TestReflect类），
- 8种java基本类型（比如int，float等）

那么java会选择Class来作为这个Type的实现类，我们甚至可以直接把这个Type强行转换类型为Class。

这些类基本都有一个特点：**基本和泛型无关，其他4种Type的类型，基本都是泛型的各种形态。**

第一个参数的测试代码：

```java
//第一个参数，TestReflect p0
Class type0=(Class)types[0];
System.out.println(type0.getName());
```

输出的结果是：

```
type0:com.webx.TestReflect
```

可见第一个参数Type的实现类就是Class。

### ParameterizedType

当需要描述的类是泛型类时，比如List，Map等，不论代码里写没写具体的泛型，java会选择ParameterizedType接口做为Type的实现。

真正的实现类是sun.reflect.generics.reflectiveObjects.ParameterizedTypeImpl。

ParameterizedType接口有`getActualTypeArguments()`方法，用于得到泛型的Type类型数组。

第二个参数的测试代码：

```java
//第二个参数，List< TestReflect > p1
Type type1=types[1];
Type[] parameterizedType1=((ParameterizedType)type1).getActualTypeArguments();
Class parameterizedType1_0=(Class)parameterizedType1[0];
System.out.println(parameterizedType1_0.getName());
```

type1是`List< TestReflect >`，List就属于泛型类，所以java选择ParameterizedType作为type1的实现，type1可以直接转换类型为ParameterizedType。

List的泛型中只能写一个类型，所以parameterizedType1数组长度只能是1，本例中泛型是TestReflect，是一个普通类，他的Type被java用Class来实现，也就是变量parameterizedType1_0，所以代码最后输出：

```
parameterizedType1_0:com.webx.TestReflect
```

第三个参数的测试代码：

```java
//第三个参数，Map<String,TestReflect> p2
Type type2=types[2];
Type[] parameterizedType2=((ParameterizedType)type2).getActualTypeArguments();
Class parameterizedType2_0=(Class)parameterizedType2[0];
System.out.println("parameterizedType2_0:"+parameterizedType2_0.getName());
Class parameterizedType2_1=(Class)parameterizedType2[1];
System.out.println("parameterizedType2_1:"+parameterizedType2_1.getName());
```

type2是`Map<String,TestReflect>`，Map属于泛型类，同样java选择ParameterizedType作为type2的实现，type2可以直接转换类型为ParameterizedType。

使用**getActualTypeArguments()**得到的泛型类型数组parameterizedType2有两个元素，因为Map在泛型中可以写两个类型，本例中Map的泛型类型分别是String类和TestReflect，他们的Type都会被java用Class来实现，所以最后输出的是：

```
parameterizedType2_0:java.lang.String
parameterizedType2_1:com.webx.TestReflect
```

### GenericArrayType

当需要描述的类型是泛型类的数组时，比如比如List[],Map[]，type会用GenericArrayType接口作为Type的实现。

真正的实现类是`sun.reflect.generics.reflectiveObjects.GenericArrayTypeImpl`。

GenericArrayType接口有getGenericComponentType()方法，得到数组的组件类型的Type对象。

第四个参数的测试代码：

```java
//第四个参数，List<String>[] p3
Type type3=types[3];
Type genericArrayType3=((GenericArrayType)type3).getGenericComponentType();
ParameterizedType parameterizedType3=(ParameterizedType)genericArrayType3;
Type[] parameterizedType3Arr=parameterizedType3.getActualTypeArguments();
Class class3=(Class)parameterizedType3Arr[0];
System.out.println("class3:"+class3.getName());
```

type3是`List<String>[]`，所以java选择GenericArrayType作为type3的实现，type3可以直接转换类型为GenericArrayType。

调用**getGenericComponentType()**方法，得到数组的组件类型的Type对象，也就是本例中的变量genericArrayType3，他代表的是`List<String>`类。

`List<String>`是泛型类，所以变量genericArrayType3的Type用ParameterizedType来实现，转换类型之后也就是变量parameterizedType3。

parameterizedType3.getActualTypeArguments()得到的是`List<String>`类型的泛型类数组，也就是数组parameterizedType3Arr。

数组parameterizedType3Arr只有一个元素，类型是String，这个Type由Class实现，就是变量class3，最后输出的是：

```
class3:java.lang.String
```

第五个参数的测试代码：

```java
//第五个参数，Map<String,TestReflect>[] p4
Type type4=types[4];
Type genericArrayType4=((GenericArrayType)type4).getGenericComponentType();
ParameterizedType parameterizedType4=(ParameterizedType)genericArrayType4;
Type[] parameterizedType4Arr=parameterizedType4.getActualTypeArguments();
Class class4_0=(Class)parameterizedType4Arr[0];
System.out.println("class4_0:"+class4_0.getName());
Class class4_1=(Class)parameterizedType4Arr[1];
System.out.println("class4_1:"+class4_1.getName());
```

type4是Map<String,TestReflect>[]，所以java选择GenericArrayType作为type4的实现，type4可以直接转换类型为GenericArrayType。

调用getGenericComponentType()方法，得到数组的组件类型的Type对象，也就是本例中的变量genericArrayType4，他代表的是Map<String,TestReflect>类型。

Map<String,TestReflect>是泛型类，所以变量genericArrayType4的Type用ParameterizedType来实现，转换类型之后也就是变量parameterizedType4。

parameterizedType4.getActualTypeArguments()得到的是Map<String,TestReflect>类型的泛型类数组，也就是变量parameterizedType4Arr。

变量parameterizedType4Arr有两个元素，类型是String和TestReflect，这两个Type都由Class实现，就是变量class4_0和变量class4_1，最后输出的是：

```
class4_0:java.lang.String
class4_1:com.webx.TestReflect
```

### WildcardType

当需要描述的类型是泛型类，而且泛型类中的泛型被定义为(? extends xxx)或者(? super xxx)这种类型，比如List<? extends TestReflect>，这个类型**首先将由ParameterizedType实现**，当调用ParameterizedType的getActualTypeArguments()方法后得到的Type就由WildcardType实现。

真正的实现类是`sun.reflect.generics.reflectiveObjects.WildcardTypeImpl`。

WildcardType接口有**getUpperBounds()**方法，得到的是类型的上边界的Type数组，实际上就是类型的直接父类，也就是extends后面的类型。显然在当前java的设定中，这个数组只可能有一个元素，因为java现在只能extends一个类。如果实在没写extends，那他的直接父类就是Object。

WildcardType接口有**getLowerBounds()**方法，得到的是类型的下边界的Type数组，有super关键字时可能会用到，经测试不会得到类型的子类，而是只得到super关键字后面的类型，如果没写super关键字，则返回空数组。

第六个参数的测试代码：

```java
//第六个参数，List<? extends TestReflect> p5
Type type5=types[5];
Type[] parameterizedType5=((ParameterizedType)type5).getActualTypeArguments();
Type[] parameterizedType5_0_upper=((WildcardType)parameterizedType5[0]).getUpperBounds();
Type[] parameterizedType5_0_lower=((WildcardType)parameterizedType5[0]).getLowerBounds();
```

type5代表List<? extends TestReflect>，用ParameterizedType实现。

调用getActualTypeArguments()方法后，得到只有一个元素的Type数组，这个元素就代表(? extends TestReflect)

把这个Type元素转成WildcardType后，可以调用getUpperBounds()和getLowerBounds()方法得到上边界和下边界，在本例中的上边界就是变量parameterizedType5_0_upper，只有一个元素，该元素代表TestReflect类型，下边界是变量parameterizedType5_0_lower，是个空数组。

第七个参数的测试代码：

```java
//第七个参数，Map<? extends TestReflect,? super TestReflect> p6
Type type6=types[6];
Type[] parameterizedType6=((ParameterizedType)type6).getActualTypeArguments();
Type[] parameterizedType6_0_upper=((WildcardType)parameterizedType6[0]).getUpperBounds();
Type[] parameterizedType6_0_lower=((WildcardType)parameterizedType6[0]).getLowerBounds();
Type[] parameterizedType6_1_upper=((WildcardType)parameterizedType6[1]).getUpperBounds();
Type[] parameterizedType6_1_lower=((WildcardType)parameterizedType6[1]).getLowerBounds();
```

type6代表Map<? extends TestReflect,? super TestReflect>，用ParameterizedType实现。

调用getActualTypeArguments()方法后，得到有两个元素的Type数组，两个元素分别代表(? extends TestReflect)和(? super TestReflect)

把这两个Type元素转成WildcardType后，可以调用getUpperBounds()和getLowerBounds()方法得到上边界和下边界。

在本例中第一个WildcardType的上边界就是变量parameterizedType6_0_upper，只有一个元素，该元素代表TestReflect类型，下边界是变量parameterizedType6_0_lower，是个空数组。

在本例中第二个WildcardType的上边界就是变量parameterizedType6_1_upper，只有一个元素，该元素代表Object类型，下边界是变量parameterizedType6_1_lower，只有一个元素，该元素代表TestReflect类型。

### TypeVariable

Type的最后一种实现形式是TypeVariable接口，这种实现形式是在泛型类中使用的。

比如我们定义一个泛型类TestReflect\<T>，并在类中定义方法oneMethod(T para)，那么当调用method.getGenericParameterTypes()方法得到的Type数组，数组的元素就是由TypeVariable接口实现的。

真正的实现类是`sun.reflect.generics.reflectiveObjects.TypeVariableImpl`。

# Class对象

每个类都有一个Class对象，每当编写并且编译了一个新类，就会产生一个Class对象，精确的说是保存在同名的.class文件里，为了生产这个类的对象，JVM将使用类加载器。

## 基本使用

**MainInterface**

```java
public interface MainInterface {
}
```

**MainParent**

```java
public class MainParent {
}
```

**MainChild**

```java
public class MainChild extends MainParent implements MainInterface  {
    public void say(){
        System.out.println("i am MainChild");
    }
}
```

**Main**

```java
public class Main {
    public static void main(String[] args) throws ClassNotFoundException, InstantiationException, IllegalAccessException {
        Class clazz = Class.forName("com.mezzsy.learnsomething.MainChild");
        System.out.println("getName():" + clazz.getName());
        System.out.println("getSimpleName():" + clazz.getSimpleName());
        System.out.println("getCanonicalName():" + clazz.getCanonicalName());
        System.out.println("getSuperclass():" + clazz.getSuperclass());
        System.out.println("isInterface():" + clazz.isInterface());
        System.out.println("getInterfaces():" + Arrays.toString(clazz.getInterfaces()));

        MainChild child = (MainChild) clazz.newInstance();
        child.say();
    }

}
```

output：

```
getName():com.mezzsy.learnsomething.MainChild
getSimpleName():MainChild
getCanonicalName():com.mezzsy.learnsomething.MainChild
getSuperclass():class com.mezzsy.learnsomething.MainParent
isInterface():false
getInterfaces():[interface com.mezzsy.learnsomething.MainInterface]
i am MainChild
```

-   使用getName()来产生全限定的类名，并分别使用getSimpleName()和getCanonicalName()来产生不含包名的类名和全限定的类名。
-   isInterface方法表示是否是个接口。
-   getInterfaces方法返回的是Class对象，表示Class对象中所包含的接口。
-   使用getSuperclass方法查询其直接基类。
-   使用newInstance来创建对象（必须带有默认的构造器）。

## 获取Class对象

**一、forName()方法**

```java
public class Main {
    public static void main(String[] args) {
        try {
            Class clazz = Class.forName("com.mezzsy.learnsomething.Main$A");
            System.out.println(clazz.getSimpleName());
        } catch (ClassNotFoundException e) {
            e.printStackTrace();
        }
    }

    private static class A {
        static {
            System.out.println("A static init");
        }
    }
}
```

```
A static init
A
```

forName()是取得Class对象的一个方法，用String作为参数，返回Class对象的引用。注意：字符串中必须使用全限定名（包含包名）

**二、getClass()方法**

```java
public class Main {
    public static void main(String[] args) {
        A a = new A();
        Class clazz = a.getClass();
        System.out.println(clazz.getSimpleName());
    }

    private static class A {
        static {
            System.out.println("A static init");
        }
    }
}
```

```
A static init
A
```

**三、简单方法**

`A.class`

这种方法更常用，另外使用这方法的时候不会自动初始化，即不会调用static块。

```java
public class Main {
    public static void main(String[] args) {
        Class clazz = A.class;
        System.out.println(clazz.getSimpleName());
    }

    private static class A {
        static {
            System.out.println("A static init");
        }
    }
}
```

```
A
```

### 获取类名

## 类型检查

Java判断类型的方式有这么几种：

1.  instanceOf
2.  Class的isInstance(Object obj)方法

```java
public class Main {
    public static void main(String[] args) {
        Object a = new A();
        Object a2 = new A();
        Object b = new B();

        System.out.println("a instanceof A：" + (a instanceof A));
        System.out.println("a instanceof B：" + (a instanceof B));

        System.out.println("a.getClass().isInstance(a)：" + (a.getClass().isInstance(a)));
        System.out.println("b.getClass().isInstance(a)：" + (b.getClass().isInstance(a)));

        System.out.println("a.getClass() == a2.getClass()：" + (a.getClass() == a2.getClass()));
        System.out.println("a.getClass() == b.getClass()：" + (a.getClass() == b.getClass()));
    }

    private static class A {}
    private static class B {}
}
```

```
a instanceof A：true
a instanceof B：false
a.getClass().isInstance(a)：true
b.getClass().isInstance(a)：false
a.getClass() == a2.getClass()：true
a.getClass() == b.getClass()：false
```

>   另外要注意的一个地方：
>
>   在写demo的时候是这样写的：
>
>   ```java
>   A a = new A();
>   A a2 = new A();
>   B b = new B();
>   ```
>
>   编译出错
>
>   ```java
>   System.out.println("a instanceof B：" + (a instanceof B));
>   System.out.println("a.getClass() == b.getClass()：" + (a.getClass() == b.getClass()));
>   ```
>
>   因此，使用instanceof和==（equals不会报错）的方法的时候，两个引用的类型必须是一棵继承树上的。

**注意**，上面的输出是一样的，但是instanceof和equals并不相同。instanceof保持了类型的
概念，如`x instanceof A`表示x是否是A继承树上的类型，而如果用==比较实际的Class对象，如`x==A`表示x是否是A这个类型而不考虑继承的更新。

## 创建对象

```k
e.getClass().newInstance()
```

可以用这个方法快速的创建一个和e具有相同类型的实例。newInstance()方法默认调用没有参数的构造方法，如果没有，那么会报错。

如果需要传入参数，就用Constructor的newInstance()方法：

```java
public class Human {
    private String name;
    private boolean sex;

    public Human() {
    }

    public Human(String name, boolean sex) {
        this.name = name;
        this.sex = sex;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public boolean getSex() {
        return sex;
    }

    public void setSex(boolean sex) {
        this.sex = sex;
    }
}
```

```java
public class Main {
    public static void main(String[] args) {
        Human human = new Human();
        try {
            Constructor<Human> constructor = (Constructor<Human>)
                    human.getClass().getConstructor(String.class, boolean.class);
            Human zzsy = constructor.newInstance("zzsy", true);
            System.out.println(zzsy.getName() + "，是否男性:" + zzsy.getSex());
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}

output：
zzsy，是否男性:true
```

用Class中的getConstructor方法，传入构造方法需要的参数的class类型，然后用Constructor的newInstance方法传入具体的参数，就可以构造一个对象了。

## 利用反射分析类

Field、Method、Constructor分别用于描述类的域、方法和构造器。这三个类都有一个叫getName()的方法，用来返回名称。

Field类有一个getType方法，用来返回描述域所属类型的Class对象。

Method和Constructor类能够报告参数类型的方法，Method还可以报告返回类型的方法。

这三个类还有一个getModifiers的方法，返回一个整型，用来描述修饰符使用状况。

Class类中的getFields、getConstructors、getMethods返回public域、方法和构造器数组，其中包括父类的公有成员。

Class类中的getDeclaredFields、getDeclaredConstructors、getDeclaredMethods返回所有的，包括私有的，但不包括父类的。

简单实用：

类代码：

```java
class C {
    public final static String STRING = "STRING";
    private int i;
    private String s;

    public C() {
    }

    public C(int i, String s) {
        this.i = i;
        this.s = s;
    }

    private void f1() {
        System.out.println("f1");
    }

    private double f2(double d) {
        return d;
    }
}
```

main：

```java
C c = new C(1, "s");
        Class aClass = c.getClass();

        System.out.println("Field: \n----------------------");
        Field[] fields = aClass.getDeclaredFields();
        for (Field field : fields) {
            Class type = field.getType();
            String name = field.getName();
            String modifiers = Modifier.toString(field.getModifiers());
            if (modifiers.length() > 0)
                System.out.println(modifiers);
            System.out.println("type = " + type.getName() + " \nname = " + name);
            System.out.println("-----------");
        }

        System.out.println("Method: \n----------------------");
        Method[] methods = aClass.getDeclaredMethods();
        for (Method method : methods) {
            Class retType = method.getReturnType();
            String name = method.getName();
            String modifiers = Modifier.toString(method.getModifiers());
            if (modifiers.length() > 0)
                System.out.println(modifiers);
            System.out.println("return type = " + retType.getName());
            System.out.println("name = " + name);

            Class[] paramTypes = method.getParameterTypes();
            for (int i = 0; i < paramTypes.length; i++) {
                System.out.println(paramTypes[i].getName() + ", ");
            }
            System.out.println("-----------");
        }

        System.out.println("Method: \n----------------------");
        Constructor[] constructors = aClass.getDeclaredConstructors();
        for (Constructor constructor : constructors) {
            String name = constructor.getName();
            String modifiers = Modifier.toString(constructor.getModifiers());
            if (modifiers.length() > 0)
                System.out.println(modifiers);
            System.out.print(name + "(");

            Class[] paramTypes = constructor.getParameterTypes();
            for (int i = 0; i < paramTypes.length; i++) {
                System.out.print(paramTypes[i].getName() + ", ");
            }
            System.out.println(")");
            System.out.println("-----------");
        }



output:
Field: 
----------------------
public static final
type = java.lang.String 
name = STRING
-----------
private
type = int 
name = i
-----------
private
type = java.lang.String 
name = s
-----------
Method: 
----------------------
private
return type = void
name = f1
-----------
private
return type = double
name = f2
double, 
-----------
Constructor: 
----------------------
public
com.mezzsy.learnsomething.C()
-----------
public
com.mezzsy.learnsomething.C(int, java.lang.String, )
-----------
```

### 在运行时使用反射分析对象

```java
C c = new C(1, "s");
Class aClass = c.getClass();
try {
    Field field=aClass.getDeclaredField("i");
    field.setAccessible(true);
    Object o=field.get(c);
    System.out.println(o);
} catch (NoSuchFieldException | IllegalAccessException e) {
    e.printStackTrace();
}

output:
1
```

只用利用get才能得到可访问域的值。另外，对于私有域，用get会报错。java安全机制只允许查看任意对象有哪些域，而不允许读取它们的值。如果要访问值，那么需要用setAccessible方法。

get返回的是Object对象，而对于数值类型，返回的是对应的包装类，或者可以用getDouble（对应的数值类型）方法。

**set方法**

```java
public static void main(String[] args) {
    C c = new C(1, "s");
    Class aClass = c.getClass();
    try {
        Field field = aClass.getDeclaredField("i");
        field.setAccessible(true);
        Object i = field.getInt(c);
        System.out.println(i);

        field.set(c, 2);
        i = field.getInt(c);//需再次获取
        System.out.println(i);
    } catch (NoSuchFieldException | IllegalAccessException | IllegalArgumentException e) {
        e.printStackTrace();
    }
}
```

```
1
2
```

### 调用任意方法

使用Method的invoke方法，允许调用当前Method对象中的方法

```java
public double f2(double d) {
    return d;
}
```

```java
C c = new C(1, "s");
Class aClass = c.getClass();
try {
    Method method=aClass.getMethod("f2", double.class);
    double d = (double) method.invoke(c,1.1);
    System.out.println(d);
} catch (NoSuchMethodException | IllegalAccessException | InvocationTargetException e) {
    e.printStackTrace();
}

output:
1.1
```

# 动态代理

见Java的代理。