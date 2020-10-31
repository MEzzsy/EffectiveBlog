# Lambda总结

Kotlin的lambda语句可以修改外部可变变量，其原理是外部包了一层包装类，包装类实例的引用不会被改变，但是可以改变其中的值。

不可变(final)变量和Java一样，进行值的拷贝。

## 内联函数

lambda表达式会被编译成匿名类。每调用一次lambda表达式，一个额外的类就会被创建。并且如果lambda捕捉了某个变量，那么每次调用的时候都会创建一个新的对象。这会带来运行时的额外开销，导致使用lambda比使用一个直接执行相同代码的函数效率更低。

一个高效的做法是内联函数。

使用inline修饰符标记一个函数，在函数被使用的时候编译器并不会生成函数调用的代码，而是使用函数实现的真实代码替换每一次的函数调用。

当一个函数被声明为inline时，它的函数体是内联的。换句话说， 函数体会被直接替换到函数被调用的地方，而不是被正常调用。

>   类似于C++的内联函数

## 在lambda中返回

### 非局部返回

```kotlin
fun lookForAlice(people: List<Person>) {
    for (person in people) {
        if (person.name == "Alice") {
            println("Found!")
            return
        }
    }
    println("Alice is not found")
}
```

在lambda中使用return关键字，它会从调用lambda的函数中返回，并不只是从lambda中返回。这样的return语句叫作非局部返回。

局部返回只适用于内联函数。

### 局部返回

局部返回需要用到标签。

```kotlin
fun lookForAlice(people: List<Person>) {
    people.forEach label@{
        if (it.name == "Alice") return@label
    }
    println("Alice might be somewhere")
}
```

在lambda的花括号之前放一个标签名(可以是任何标识符)，接着放一个@符号。要从一个lambda返回，在return关键字后放一个@符号，接着放标签名。

也使用lambda作为参数的函数的函数名可以作为标签。

```kotlin
fun lookForAlice(people: List<Person>) {
    people.forEach {
        if (it.name == "Alice") return@forEach
    }
    println("Alice might be somewhere")
}
```