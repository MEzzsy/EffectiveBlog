来自：https://mp.weixin.qq.com/s/rrhA44Yo8Y_r47V08WP_mg

# foreach循环

## 原理

增强for循环是Java提供的一个语法糖，如果将以上代码编译后的class文件进行反编译（使用jad工具）的话，可以得到以下代码：

```java
Iterator iterator = userNames.iterator();
do
{
    if(!iterator.hasNext())
        break;
    String userName = (String)iterator.next();
    if(userName.equals("Hollis"))
        userNames.remove(userName);
} while(true);
System.out.println(userNames);
```

可以发现，原本的增强for循环，其实是依赖了while循环和Iterator实现的。

# 出现的问题

使用普通for循环对List进行遍历，删除List中元素内容等于Hollis的元素。

```java
public static void main(String[] args) {
    List<String> userNames = new ArrayList<>();
    userNames.add("Hollis");
    userNames.add("hollis");
    userNames.add("HollisChuang");
    userNames.add("H");

    for (int i = 0; i < userNames.size(); i++) {
        if (userNames.get(i).equals("Hollis")) {
            userNames.remove(i);
        }
    }

    System.out.println(userNames);
}

[hollis, HollisChuang, H]
```

没有什么问题。

在foreach循环中对集合元素做add/remove操作。

```java
List<String> userNames = new ArrayList<String>() {{
    add("Hollis");
    add("hollis");
    add("HollisChuang");
    add("H");
}};

for (String userName : userNames) {
    if (userName.equals("Hollis")) {
        userNames.remove(userName);
    }
}

System.out.println(userNames);
```

以上代码，使用增强for循环遍历元素，并尝试删除其中的Hollis字符串元素。运行以上代码，会抛出以下异常：

```
java.util.ConcurrentModificationException
```

同样的，在增强for循环中使用add方法添加元素，结果也会同样抛出该异常。

# 问题的原因

之所以会出现这个异常，是因为触发了一个Java集合的错误检测机制——fail-fast 。

## fail-fast

fail-fast，即快速失败，它是Java集合的一种错误检测机制。当多个线程对集合（非fail-safe的集合类）进行结构上的改变的操作时，有可能会产生fail-fast机制，这个时候就会抛出ConcurrentModificationException（当方法检测到对象的并发修改，但不允许这种修改时就抛出该异常）。

同时需要注意的是，即使不是多线程环境，如果单线程违反了规则，同样也有可能会抛出改异常。

那么，在增强for循环进行元素删除，是如何违反了规则的呢？

要分析这个问题，我们先将增强for循环这个语法糖进行解糖（使用jad对编译后的class文件进行反编译），得到以下代码：

```java
public static void main(String[] args) {
    // 使用ImmutableList初始化一个List
    List<String> userNames = new ArrayList<String>() {{
        add("Hollis");
        add("hollis");
        add("HollisChuang");
        add("H");
    }};

    Iterator iterator = userNames.iterator();
    do
    {
        if(!iterator.hasNext())
            break;
        String userName = (String)iterator.next();
        if(userName.equals("Hollis"))
            userNames.remove(userName);
    } while(true);
    System.out.println(userNames);
}
```

然后运行以上代码，同样会抛出异常。

经过debug，如果remove代码没有被执行过，iterator.next这一行是一直没报错的。抛异常的时机也正是remove执行之后的的那一次next方法的调用。

看下checkForComodification方法的代码，看下抛出异常的原因：

```java
final void checkForComodification() {
    if (modCount != expectedModCount)
        throw new ConcurrentModificationException();
}
```

代码比较简单，`modCount != expectedModCount`的时候，就会抛出`ConcurrentModificationException`。

那么，就来看一下，remove/add 操作室如何导致modCount和expectedModCount不相等的吧。

## 原因

- modCount是ArrayList中的一个成员变量。它表示该集合实际被修改的次数。

- expectedModCount 是 ArrayList中的一个内部类——Itr中的成员变量。expectedModCount表示这个迭代器期望该集合被修改的次数。其值是在ArrayList.iterator方法被调用的时候初始化的。只有通过迭代器对集合进行操作，该值才会改变。
- Itr是一个Iterator的实现，使用ArrayList.iterator方法可以获取到的迭代器就是Itr类的实例。

remove方法只修改了modCount，并没有对expectedModCount做任何操作。

# 总结

之所以会抛出ConcurrentModificationException异常，是因为使用了增强for循环，而在增强for循环中，集合遍历是通过iterator进行的，但是元素的add/remove却是直接使用的集合类自己的方法。这就导致iterator在遍历的时候，会发现有一个元素在自己不知不觉的情况下就被删除/添加了，就会抛出一个异常，用来提示用户，可能发生了并发修改。

# 正确的做法

## 直接使用普通for循环进行操作

不能在foreach中进行，但是使用普通的for循环还是可以的，因为普通for循环并没有用到Iterator的遍历，所以压根就没有进行fail-fast的检验。

## 直接使用Iterator进行操作

可以直接使用Iterator提供的remove方法。

```java
    List<String> userNames = new ArrayList<String>() {{
        add("Hollis");
        add("hollis");
        add("HollisChuang");
        add("H");
    }};

    Iterator iterator = userNames.iterator();

    while (iterator.hasNext()) {
        if (iterator.next().equals("Hollis")) {
            iterator.remove();
        }
    }
    System.out.println(userNames);
```

如果直接使用Iterator提供的remove方法，那么就可以修改到expectedModCount的值。那么就不会再抛出异常了。

## 使用Java 8中提供的filter过滤

Java 8中可以把集合转换成流，对于流有一种filter操作， 可以对原始 Stream 进行某项测试，通过测试的元素被留下来生成一个新 Stream。

```java
    List<String> userNames = new ArrayList<String>() {{
        add("Hollis");
        add("hollis");
        add("HollisChuang");
        add("H");
    }};

    userNames = userNames.stream().filter(userName -> !userName.equals("Hollis")).collect(Collectors.toList());
    System.out.println(userNames);
```

## 直接使用fail-safe的集合类

在Java中，除了一些普通的集合类以外，还有一些采用了fail-safe机制的集合类。这样的集合容器在遍历时不是直接在集合内容上访问的，而是先复制原有集合内容，在拷贝的集合上进行遍历。

由于迭代时是对原集合的拷贝进行遍历，所以在遍历过程中对原集合所作的修改并不能被迭代器检测到，所以不会触发ConcurrentModificationException。

```java
ConcurrentLinkedDeque<String> userNames = new ConcurrentLinkedDeque<String>() {{
    add("Hollis");
    add("hollis");
    add("HollisChuang");
    add("H");
}};

for (String userName : userNames) {
    if (userName.equals("Hollis")) {
        userNames.remove();
    }
}
```

基于拷贝内容的优点是避免了ConcurrentModificationException，但同样地，迭代器并不能访问到修改后的内容，即：迭代器遍历的是开始遍历那一刻拿到的集合拷贝，在遍历期间原集合发生的修改迭代器是不知道的。

java.util.concurrent包下的容器都是安全失败，可以在多线程下并发使用，并发修改。

## 使用增强for循环其实也可以

如果，我们非常确定在一个集合中，某个即将删除的元素只包含一个的话， 比如对Set进行操作，那么其实也是可以使用增强for循环的，只要在删除之后，立刻结束循环体，不要再继续进行遍历就可以了，也就是说不让代码执行到下一次的next方法。

```java
    List<String> userNames = new ArrayList<String>() {{
        add("Hollis");
        add("hollis");
        add("HollisChuang");
        add("H");
    }};

    for (String userName : userNames) {
        if (userName.equals("Hollis")) {
            userNames.remove(userName);
            break;
        }
    }
    System.out.println(userNames);
```

以上这五种方式都可以避免触发fail-fast机制，避免抛出异常。如果是并发场景，建议使用concurrent包中的容器，如果是单线程场景，Java8之前的代码中，建议使用Iterator进行元素删除，Java8及更新的版本中，可以考虑使用Stream及filter。

