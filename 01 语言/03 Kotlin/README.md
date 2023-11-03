Kotlin总结





# 1


第8章元编程
在之前学习Java的时候，Java的反射是一个比较难而且重要的知
识点。但是在很多框架和工具类中，你都能见到Java反射的影子，而
且很多问题使用反射解决会更加方便。但是本章会告诉你，Java的反
射只是元编程的一种方式。本章我们将会以元编程作为开篇，然后讲
述反射在Kotlin中是如何使用的，最后介绍Kotlin的注解，以及如何解
析我们自己定义的注解。
在正式讨论元编程之前，我们先来看一个将dataclass转换成
Map的例子。这个需求非常常见，相信大部分程序员都编写过类似的
数据转换代码。
data class User(val name: String, val age: Int)
object User {
fun toMap(a: User): Map<String, Any> = {
hashMapOf("name" to name, "age" to age)
}

Page 491
}
以上实现非常简单，对任何一个稍有经验的程序员都不构成任何
难度。但是要完美地实现这个需求却需要考虑更多。上述方案就有一
个缺点：对每一个新的类型我们都需要重复实现toMap函数，因为每
个类型拥有不同属性。
这显然是一种不好的实践，它有两个问题：
·违背了DRY(Don't Repeat Yourself)原则。这些实现虽然代码不完
全一样，但是结构雷同，在dataclass数量非常多的情况下，会出现
大量类似的样板代码。
·很容易将属性名写错。所有属性名都需要人工编写，很难保证100%
正确，在dataclass多的情况下，这个问题将变得更加严重。
当然，相信你已经开始思考如何用反射来实现这个函数了。

Page 492
8。1程序和数据
我们先用反射来实现一下这个函数。由于所有类型只需要一个函
数，所以我们可以定义全局的Mapper对象来完成这个需求。
object Mapper {
fun <A : Any> toMap(a: A) = {
//获取A中所有的属性
a::class.memberProperties.map { m ->
}
}
val p = m as KProperty
p.name to p.call(a)
}.toMap()
Mapp.toMap(new User("humora", 17))
利用反射我们完美地实现了需求：
·能适用于所有data class。只需要调用一个Mapper.toMap函数我们就
能将所有类型转化成Map。

Page 493
·不再需要手工创建Map。所有的属性名都是自动根据KClass对象获
取的，不存在写错的可能。
现在我们来审视一下上述代码中的a：：class。a：：class的类型
是KClass,是Kotlin中描述类型的类型(通常被称为metaclass)。如
果我们将User看成是描述现实概念的数据结构，那么在传入参数类型
为User时，a：：class则可以看成描述User类型的数据。这样描述数
据的数据就可以称之为元数据。那么元数据究竟与我们说的元编程有
何关联呢?

Page 494
8。1。1什么是元编程
前面已经提到，描述数据的数据可以称之为元素据。我们将程序
看成描述需求的数据，那么描述程序的数据就是程序的元数据。如前
文例子中的a：：class就是描述传入类型A的元数据。而像这样操作元
数据的编程就可以称之为元编程。
很多人可能会抱怨：说了这么多，元编程不就是反射吗?这个说
法是不全面的，元编程可以用一句话概括：程序即是数据，数据即是
程序。
注意这句话包含两个方面意思：
·前半句指的是访问描述程序的数据，如我们通过反射获取类型信息；
·后半句则是指将这些数据转化成对应的程序，也就是所谓代码生
成。
反射就是获取描述程序信息的典型例子，相信你已经十分熟悉
了，我们不赘述其概念。而代码生成则相对陌生一些，先来看一个来
自维基百科的简单例子：
#!/bin/sh

# metaprogram

echo '#!/bin/sh' > program
for i in $(seq 992)

Page 495
do
echo "echo $i" >> program
done
chmod +x program
这个脚本创建了一个名为program的文件，并通过echo命令将代
码写入该文件。这就是一个典型的生成代码的例子。这个例子将程序
作为程序的输出。
看到这里大家应该对元编程的概念有了基本了解。这是一个非常
简单的概念，不需要理解什么深奥的数学公式也能掌握。
仔细思考之后不难发现，元编程就像高阶函数一样，是一种更高
阶的抽象，高阶函数将函数作为输入或输出，而元编程则是将程序本
身作为输入或输出。
同时我们也会思考，元数据经过操作之后能不能直接作为程序使
用?也就“程序即数据，数据即程序”这句话中前后的数据是否指的
是同一种数据。
对于这个问题不同语言有不同答案，在Kotlin中我们显然没法将
一个KClass修改之后将其反过来生成一个新的class来使用；但是在
Lisp中,一切都可以视为LinkedList,而Lisp的宏则允许直接将这些
LinkedList作为程序的一部分。
像Lisp这样的一致性,我们称之为同像性(homoiconicity)。

Page 496
同像性
在计算机编程中,同像性(homoiconicity,来自希腊语单词homo,
意为与符号含义表示相同）是某些编程语言的特殊属性，它意味着一
个程序的结构与其句法是相似的，因此易于通过阅读程序来推测程序
的內在涵义。如果一门编程语言具备了同像性，说明该语言的文本表
示（通常指源代码）与其抽象语法树（AST）具有相同的结构（即，
AST和语法是同形的）。该特性允许使用相同的表示语法，将语言中
的所有代码当成资料来存取以及转换，提供了“代码即数据”的理论
前提。
总结一下目前我们得到的信息：
1）元编程是指操作元数据的编程。它通常需要获取程序本身的
信息或者直接生成程序的一部分或者两者兼而有之。
2）元编程可以消除某些样板代码。如前文例子那样，原本需要
对每个类型编写特定转化代码，而现在只需要统一的一个函数即可实
现。
然而元编程不是只有优点，同样也存在缺点：
1）它有一定的学习成本，在没听说过相关的技术之前，程序员
们通常会感觉到摸不着头脑。
2）它编写的代码不够直接，需要进一步思考才能被理解。
前面例子中，在不使用反射的情况下，代码非常直接；而用了反

Page 497
射之后,你必须对Kotlin的reflection api有所了解才能阅读。这还是比
较简单的情况，在一些支持宏的编程语言中，这些代码将会变得更加
难以理解。所以在工程实践中，我们推崇LeastPower原则，即使用
最初级的、最简单的、能满足你需求的技术，而不能单纯为了炫耀而
采用某些高级的特性或技术。

Page 498
8。1。2常见的元编程技术
理解了元编程的概念之后，我们继续讨论元编程技术常见的实现
手段。目前主流的实现方式包括：
·运行时通过API暴露程序信息。我们多次提及的反射就是这种实现思
路。
·动态执行代码。多见于脚本语言，如JavaScript就有eval函数，可以
动态地将文本作为代码执行。
·通过外部程序实现目的。如编译器，在将源文件解析为AST之后，
可以针对这些AST做各种转化。这种实现思路最典型的例子是我们常
常谈论的语法糖，编译器会将这部分代码AST转化为相应的等价的
AST，这个过程通常被称为desuger（解语法糖）。
以上便是常见的实现思路，我们看看这些思路在编程语言中的体
现。
什么是AST
抽象语法树是源代码语法结构的一种抽象表示。它以树状的形式表现
编程语言的语法结构，树上的每个节点都表示源代码中的一种结构。
之所以说语法是“抽象”的，是因为这里的语法并不会表示出真实语
法中出现的每个细节。比如，嵌套括号被隐含在树的结构中，并没有
以节点的形式呈现；而类似于if-condition-then这样的条件跳转语句，
可以使用带有两个分支的节点来表示。（维基百科）

Page 499
1。反射
这是读者们最熟悉的技术，但是可能大部分读者没想过反射这个
词的确切含义。
反射，有时候也称为自反，是指元语言（即前文提到的描述程序
的数据结构）和要描述的语言是同一种语言的特性。
Kotlin中的KClass就是如此,它是一个Kotlin的类,同时它的实例
又能作为描述其他类的元数据。像这样用Kotlin描述Kotlin自身信息的
行为就是所谓的反射或者自反。
不难看出，自反实际上更贴合这个定义，也容易理解。除了
Kotlin和Java以外,还有许多编程语言,如Ruby、Python等都支持反
射技术。
除了我们熟悉的运行时反射之外，也有许多语言支持编译期反
射，编译期反射通常需要和宏等技术结合使用，编译器将当前程序的
信息作为输入传入给宏，并将其结果作为程序的一部分。
2。宏
尽管很多编程语言都支持所谓的“宏”，但它们各自的实现却不
那么相同。
学过C语言程序员都知道，C语言编译器通常具有一个预处理功
能，支持在编译时将相应的宏调用展开成具体内容，实质上就是简单
的文本替换。举个简单的例子：

Page 500
#define SWAP(a,b) {int_temp = a; a = b; b = _temp}
int main() {
inti=0；
}
intj=1；
SWAP(i, J);
return 0;
上述代码定义了交换两个整型的宏SWAP，编译器在编译SWAP
时直接将其替换为int temp=a; a=b; b=temp。
这种简单粗暴的方式虽然有时候有效，但存在一个非常严重的问
题。上述例子中，假如调用宏代码已经定义了名为temp变量则会造
成重复定义。
其他诸如Lisp和Scala这样的语言中的宏更加強大，如前文所
说，它们会直接在宏展开时暴露抽象语法树（AST），你可以在宏定
义中直接操作这些AST，并生成需要的AST作为程序返回。
由于Kotlin目前不支持宏，而且短期內看起来也没有要支持宏的
迹象，这里不展开论述这些复杂的宏实现。
3。模板元编程
这可以说是C++的招牌特性，甚至有本名为《MordenC+

Page 501
+Design》的书通篇都是围绕这一特性来展示各种奇技淫巧。C++的
模板元编程还具备图灵完备性，理论上可以完成所有的编程任务。由
于模板元编程和Kotlin关系并不大，本文不再展开叙述。
4。路径依赖类型
维基百科上将此特性归为一种元编程，支持路径依赖类系的语言
通常可以在编译的时候从类型层面避免大部分bug。由于这个特性通
常只在一些学术型编程语言如Haskell、Scala中出现，实践中应用并
不广泛，我们不在此具体讨论。

Page 502
8.2 Kotlin的反射
反射是大部分程序员都非常熟悉的技术，很多著名的开源框架，
如Spring等，都不可避免地使用了反射技术。
反射技术的引入可以说是极大增加了Java编程语言的灵活性，使
得一些以前难以实现的需求得以实现，大幅度减轻了开发人员重复编
码的工作量。
Kotlin既然声称能100%兼容Java，那自然也是支持所有Java支持
的反射特性。

Page 503
8.2.1 Kotlin Java
Kotlin Java, Java KotlinTÂ, ƑÙ‡
节我们着重讨论Java平台下的Kotlin的反射。
首先通过两张图来对比Kotlin和Java反射基本数据结构，如图8-1、
图8-2所示。
Parameter
AnnotatedElement
Class
Field
AccessibleObject
Constructor
8-1JavaN***#4
Excutable
Package
Method

Page 504
KFunction0
KFunction1
KClass
KProperty.Getter
KProperty.Setter
KFunction
KAnnotatedElement
KCallable
8-2Kotlin★*#4
KParameter
KProperty
KMutable Property
观察以上二图不难发现：

1) Kotlin KClass Java Class¯¯-^^XH**,

Page 505
并且可以通过.java和.kotlin方法在KClass和Class之间互相转化。
2)Kotlin的KCallable和Java的AccessiableObject都可以理解为可
调用元素。Java中构造方法为一个独立的类型，而Kotlin则统一作为
KFunction处理。
3)Kotlin的KProperty和Java的Field不太相同。Kotlin的KProperty
通常指相应的Getter和Setter(只有可变属性Setter)整体作为一个
KProperty(通常情况Kotlin并不存在字段的概念),而Java的Field通
常仅仅指字段本身。
Kotlin的反射整体来说与Java非常接近，但是需要注意的是，在
某些情况下（通常是碰到一些Kotlin独有的特性时）Kotlin编译器会在
生产的字节码中存储额外信息，这些信息目前是通过kotlin。Metadata
注解实现的。Kotlin编译器会将Metadata标注这些类。前文我们提到
Kotlin的Lambda没有采用invokeDynamic指令实现,这可能也是一个
很大原因。要实现将现有Metadata机制适应新的invokeDynamic指令,
显然有巨大的工作量和兼容性问题，稍有不慎就可能会导致bug频出。
整体看来,Kotlin和Java反射非常相似,但得益于Kotlin本身语法
简洁的特点，在可读性上还是有很大的提升。本章开头的例子就能充
分说明问题。
我们可以将其翻译成等价的Java代码：
public static <A> Map<String, Object> toMap(A a) {

Page 506
}
Field) fs =
a.getClass().getDeclaredFields();
Map<String, Object> kvs = new HashMap<>();
Arrays.stream(fs).forEach((f) -> {
f.setAccessible(true);
try {
kvs.put(f.getName(), f.get(a));
} catch (IllegalAccessException e) {
}
e.printStackTrace();
}）；
return kvs;
即使是Java8，我们仍然可以看到可读性的提升。我们此处说的
可读并不是指代码长度，虽然在更复杂的例子中，Kotlin通常能做到
更简短，但此处我们考虑的可读性是指代码容易理解的程度。
1）Kotlin的例子更加直接地反映了函数意图：读取所有属性，并
将键值对生成Map；
2）Java的例子多了许多额外元素：先读取该类所有字段，创建
一个Map,使用stream的forEach来遍历,将每个字段的键值放到Map
中，返回这个Map，同时还需要处理可能的异常；
3）Java版本直接强制访问字段键值，需强制设置可访问性；而
Kotlin版本中KProperty的call函数实际上是直接调用Getter,这是更合

Page 507
理的方案。
从功能来看上述两者是一致的，但是Kotlin代码显然更加容易理
解，函数实现直接体现了函数意图；而Java版本则多了额外信息。
Kotlin用更少的元素表达同样或者更多的内涵，这也就是我们说的优
雅。

Page 508
8.2.2 Kotlin的KClass
尽管Kotlin的反射和Java非常相似，但是它仍旧有一些独特的地
方,主要是集中在Kotlin中独有,Java没有与之对应的特性。KClass
的特别属性或者函数如表8-1所示。
表8-1KClass特别属性或者函数
属性或函数名称
is Companion
isData
isSealed.
objectInstance
companionObjectInstance
declaredMemberExtension Functions
declared MemberExtension Properties
memberExtension Functions.
memberExtensionProperties
starProjected Type
import kotlin.reflect.full.*
sealed class Nat {
companion object { object Zero : Nat() }
含义
这些有助于我们实现Kotlin特性相关的反射逻辑，例如获取object
实例等。以下这个自然数编码的例子展示了这些用法。
val Companion._0
get() = Zero
是否伴生对象
是否数据类
是否密封类
object 实例(如果是 object)
伴生对象实例
扩展函数
扩展属性
本类及超类扩展函数
本类及超类扩展属性
泛型通配类型

Page 509
fun <A: Nat> Succ<A>.preceed(): A { return this.prev}
}
data class Succ<N: Nat>(val prev: N): Nat()
fun <A: Nat> Nat.plus(other: A): Nat = when {
other is Succ<*> -> Succ(this.plus(other.prev))// a + S(b) = S(a + b)
else -> this
}
上述表格中方法的调用结果如表8-2所示。
表8-2上述方法的调用结果
方法
Nat.Companion::class.isCompanion
Nat::class.isSealed
Nat.Companion::class.objectInstance
Nat::class.companionObjectInstance
Nat::class.declared MemberExtension Properties.map {it.name)
Suce::class.declared MemberExtensionFunctions.map (it.name}
Suce::class.memberExtension Functions.map (it.name}
Nat::class.declared MemberExtension Properties
Suce::class.declared MemberExtension Properties.map { it.name}
Suce::class.member Extension Properties.map {it.name}
Suce::class.starProjected Type
true
结果
true
nat. NatSCompanion@2473b9cc
nat. NatsCompanion@2473b9ce
[preceed]
0
[preceed]
[0]
[]
[0]
nat. Succ<*>
值得一提的是,declaredMemberExtensionFunctions这类函数返
回的结果指的是这个类中声明的扩展函数，而不是在其他位置声明的
本类的扩展函数。

Page 510
例如，上面例子中，Nat：：
class.
declaredMemberExtensionFunctions 返回了该类中定义的
Succ.preceed扩展函数,而没有返回定义在类外的Nat.plus函数。
所以这一系列方法作用就像“鸡肋”，更多时候我们希望获得的
是此类扩展方法。遗憾的是，目前没有直接方案可以获取某个类的所
有扩展函数。
除了上述根据类名获取KClass对象的方法以外，Kotlin还支持根
据具体的实例获得KClass。语法与上面类似，也是用：：class表示获
取class对象:Nat.Compantion._1: : class。

Page 511
8.2.3 Kotlin的KCallable
在上文和Java对比的时候我们提到Kotlin 把 Class中的属性
(Property)、函数(Funciton)甚至构造函数都看作KCallable,因为
它们是可调用的，它们都是Class的成员。那我们如何获取一个Class
的成员呢?
幸运的是，上文提到的KClass给我们提供了一个members方法，
它的返回值就是一个Collection<KCallable<*>>。接下来看看KCallabe
为我们提供了哪些有用的API，如表8-3所示。
表8-3 KCallabe提供的API
API
isAbstract:Boolean<KParameter>
isFinal: Boolean
isOpen: Boolean.
name:String
API
parameters: List<KParameter>
return Type: KType
typeParameters: List<KTypeParameter>
visibility:KVisibility?
call(vararg args: Any?): R
描述
此KCallable 是否为抽象的
KCallable
final
此 KCallable 是否为 open
此KCallable 的名称
描述
调用此 KCallable 需要的参数
此 KCallable 的返回类型
此 KCallable 的类型参数
此 KCallable 的可见性
给定参数调用此 KCallable
（续）
通过对KCallable的API的浏览,你会发现,这些API和Java中的
反射的API很相似,都是对KCallable(Class成员)的信息的获取。你

Page 512
可能对call这个函数理解得不够透彻，其实它就是通过反射执行这个
KCallable对应的逻辑。套用上面Nat的例子:
val _1 = Succ(Nat.Companion.Zero)
val preceed = _1::class.members.find { it.name == : "preceed" }
println(preceed?.call(_1, _1) == Nat.Companion.Zero)
可以看到，调用call就执行了对应逻辑。值得注意的是，如果
KCallable代表的是扩展函数，则除了传入对象实例外还需要额外传
入接收者实例。
有时候，我们不仅想使用反射来获取一个类的属性，还想更改它
的值，在Java中可以通过Field。set（。。。）来完成对字段的更改操作，
但是在Kotlin中，并不是所有的属性都是可变的，因此我们只能对那
些可变的属性进行修改操作。通过图8-2我们知道，KMutableProperty
是KProperty的一个子类，那我们如何识别一个属性是
KMutableProperty还是KProperty呢?我们使用when表达式可以轻松
解决这个问题。还是以上面的Person类作为例子，我们想把address
属性的值改为Hefei，如何去做呢?
fun KMutablePropertyShow() {
val p = Person("极跑科技",8,"HangZhou")
val props = p::class.memberProperties
for(prop in props){

Page 513
}
}
when(prop) {
is KMutableProperty<*> -> prop.setter.call(p,"Hefei")
else -> prop.call(p)
}
println(p.address)
运行的结果为Hefei，我们已经通过反射成功地修改了address的
值。再去仔细看一下Kotlin官方关于KMutableProperty的API,发现只
EŁKProperty T-setter.

Page 514
8。2。4获取参数信息
到此我们已经介绍了如何使用反射来获取Kotlin中的类、属性和
函数。让我们更进一步，看看如何使用Kotlin的反射来获取参数信
息。Kotlin把参数分为3个类别，分别是函数的参数（KParameter）、
函数的返回值(KType)及类型参数(KTypeParameter)。下面我们
就来看看如何获取它们及它们的用法。
1.KParameter
使用KCallabel.parameters即可获取一个List<KParameter>,它代
表的是函数（包括扩展函数）的参数。让我们先来浏览一下它的API，
如表8-4所示。
API
index:Int
isOptional: Boolean
is Vararg:Boolean
kind:Kind
name:Sting?
type:KType
表8-4API及其描述
fun KParameterShow() {
描述
返回该参数在参数列表里面的index
该参数是否为 Optional
该参数是否为 vararg
该参数的kind
该参数的名称
该参数的类型
我们还是使用上面的Person类来打印一下所有KCallable的参数
的类型，代码如下：

Page 515
val p = Person("极跑科技",8,"HangZhou")
for(c in Person::class.members) {
print("${c.name} -> ")
for(p in c.parameters){
}
print（"${p。type}"+"--"）
}
println()
}
运行结果：
address -> Person
name -> Person
detailAddress -> Person,kotlin.String
isChild -> Person
equals -> kotlin.Any,kotlin.Any?
hashCode -> kotlin.Any
toString -> kotlin.Any
通过上面的运行结果我们发现，对于属性和无参数的函数，它们
都有一个隐藏的参数为类的实例，而对于声明参数的函数，类的实例
作为第1个参数，而声明的参数作为后续的参数。对于那些从Any继
承过来的参数，Kotlin默认它们的第1个参数为Any。
值得一提的是，Java中尝试获取参数名有可能返回arg0、arg1，
而不是代码中指定的参数名称。若要获得参数名则可能需要指定-

Page 516
parameters编译参数。
2.KType
上面例子中,我们用KParameter的type属性获得KCallable的参数
类型，现在我们来看看如何获得KCallable的返回值类型。每一个
KCallabe都可以使用returnType来获取返回值类型,它的结果类型是
一个KType，代表着Kotlin中的类型。它的API如表8-5所示。
表8-5 KType的API及其描述
API
arguments:List<KTypeProjection>
classifier:KClassifier?
}
isMarkedNullable: Boolean
该类型的类型参数
该类型在类声明层面的类型,如该类型为 List<String>,那么通过 classifier
得到结果为List（忽略类型参数）
该类型是否标记为可空类型
还是使用Person类来做演示，这里我们在Person类中添加了一个
返回值为List<String>的friendsName方法,用来演示classifilerAPI:
fun friendsName(): List<String> {
return listOf("Yison", "Jilen")
描述
我们的演示代码如下：
Person::class.members.forEach {

Page 517
}
println("${it.name} -> ${it.returnType.classifier}")
运行结果如下：
address -> class kotlin.String
age-> class kotlin.Int
name -> class kotlin.String
detailAddress -> class kotlin.String
friendsName -> class kotlin.collections. List
isChild -> class kotlin.Boolean
equals -> class kotlin.Boolean
hashCode -> class kotlin.Int
toString -> class kotlin.String
通过对运行结果的分析我们发现，classifierAPI其实就是获取该
✰***EÓNÈH*2, Int->class kotlin.Int, List<String>-

>class kotlin.collections. List.
>3.KTypeParameter
>对于函数和类来说，还一个重要的参数————类型参数，在
>typeParameters *** class
>KClass KCallable
>callable的类型参数,它返回的结果集是List<KTypeParameter>,不存

Page 518
在类型参数时就返回一个空的List。在之前的Person中我们添加一个
带类型参数的方法，代码如下：
fun <A> get (a: A): A {
return a
}
然后我们可以使用下面的代码来获取get方法和List<String>的类
型参数：
fun KTypeParameterShow() {
for (c in Person::class.members) {
if(c.name .equals("get")) {
println(c.typeParameters)
}
}
}
val list = listOf<String>("How")
println(list::class.typeParameters)
[A]
运行的结果如下：

Page 519
[E]

Page 520
8.3 Kotlin的注解
前面我们提及过注解kotlin.Metadata,这是实现Kotlin大部分独特
特性反射的关键，Kotlin将这些信息直接以注解形式存储在字节码文
件中，以便运行时反射可以获取这些数据。
由于Kotlin兼容Java,所以所有Java可以添加注解的地方,Kotlin
也都可以。并且Kotlin也简化了注解创建语法，创建注解就像创建
class一样简单,只需额外在class前增加annotation关键字即可。
annotation class FooAnnotation(val bar: String)
上面的代码就直接创建了FooAnnotation注解,和创建其他Kotlin
的类一样，正如前文所说，只要在前面加上annotation，这个类就变
成了注解，和等价的Java代码相比较，确实简化了很多。同时和Java
一样，注解的参数只能是常量，并且仅支持下列类型：
·与Java对应的基本类型；
·字符串；
·Class对象(KClass或者Java的Class);

Page 521
·其他注解；
·上述类型数组。注意基本类型数组需要指定为对应的XXXArray，例
如IntArray,而不是Array<Int>。
有了注解之后我们就可以将注解应用在代码中。那么哪些代码可
以添加注解呢?熟悉Java的读者应该已经想到了@Target元注解，它
可以指定注解作用的位置。类似@Target这样标注在注解上的注解我
们称之为元注解。Java有下列5个元注解。
·Documented文档（通常是API文档）中必须出现该注解。
·Inherited如果超类标注了该类型，那么其子类型也将自动标注该注解
而无须指定。
Repeatable这个注解在同一位置可以出现多次。
·Retention表示注解用途，有3种取值。
·Sourc。仅在源代码中存在，编译后class文件中不包含该注解信息。
·CLASS。class文件中存在该注解，但不能被反射读取。
·RUNTIM。注解信息同样保存在class文件中并且可以在运行时通过
反射获取。
·Target表明注解可应用于何处。
Kotlin也有相应类似的元注解在kotlin.annotation包下,如表8-6所

Page 522
示。
Kotlin
表8-6 Kotliu与Java的元注解
kotlin.annotation. Retention
kotlin.annotation. Target
kotlin.annotation. Documented
kotlin.annotation.Repeatable
Java
java.lang.annotation.Retention
java.lang.annotation.Target
java.lang.annotation.Documented
java.lang.annotation.Repeatable
注意到,Kotlin目前不支持Inherited,理论上实现继承没有很大
难度，但当前版本还不支持。
通过上面对比我们发现，Kotlin和Java注解整体上是保持一致的，
熟悉Java注解的读者应该很容易将这部分知识迁移到Kotlin。同样，
Kotlin也有@Target元注解,和Java相似,它控制注解可以作用的位
置。

Page 523
8。3。1无处不在的注解
和Java一样，Kotlin的注解可以出现代码的各个位置，例如方
法、属性、局部变量、类等。此外注解还能作用于Lambda表达式、
整个源文件。
前文已经指出，Java注解标注的位置可以通过元注解@Target指
定，Kotlin也一样，并且Kotlin在Java的基础上增加一些可以标注的位
置,这些位置是在AnnotationTarget枚举中定义的,我们只需看看
AnnotationTarget有多少种取值就能知道它能作用于多少个位置,如
表8-7所示。
Kotlin(AnnotationTarget)
CLASS
ANNOTATION CLASS
TYPE_PARAMETER
PROPERTY
FIELD
LOCAL VARIABLE
VALUE_PARAMETER
表8-7Target的取值
Java(Target)
TYPE
ANNOTATION TYPE
TYPE PARAMETER
NA
FIELD
LOCAL VARIABLE
NA
说明
作用于类
作用于注解本身（即元注解）
作用于类型参数
作用于属性
作用于字段（属性通常包含字段Getter以及Setter）
作用于局部变量
作用于val参数

Page 524
Kotlin(Annotation Target)
CONSTRUCTOR
FUNCTION
PROPERTY GETTER
PROPERTY SETTER
TYPE
EXPRESSION
FILE
TYPEALIAS
Java(Target)
CONSTRUCTOR
METHOD
ΝΑ
NA
TYPE_USE
ΝΑ
PACKAGE
ΝΑ
作用于构造函数
TP (Java Method)
ist 明
Getter
MF Setter
作用丁类型：
作用于表达式
作用于文件开头/包声明（两者有细微区别）
作用于类型别名
下面就是一个简单Kotlin注解使用例子：
（续）
观察表8-7不难发现，Kotlin支持几乎所有Java可以标注的位置，
并且增加了一些Kotlin独有的位置。
@Cache(namespace = "hero", expires = 3600)
data class Hero(
annotation class Cache(val namespace: String, val expires: Int)
annotation class CacheKey(val keyName: String, val buckets: IntArray)
@CacheKey(keyName = "heroName", buckets= intArrayOf(1,2,3))
val name: String,
val attack: Int,
val defense: Int,
val initHp: Int

Page 525
细心的你可能已经发现，Kotlin的代码常常会表达多重含义。例
如，上述例子中的name除了生成了一个不可变的字段之外，实际上
还包含了Getter，同时又是其构造函数的一个参数。
这就带来一个问题，@CacheKey注解究竟是作用于何处?

Page 526
8。3。2精确控制注解的位置
为了解决这个问题，Kotlin引入精确的注解控制语法，如表8-8所
示。假如我们有注解annotation class CacheKey。
表8-8精确的注释控制语法
用法
@file:CacheKey
@property:CacheKey
@field:CacheKey
@get:CacheKey
用法
@set:CacheKey
@receiver:CacheKey
@param:CacheKey
@setparam:CacheKey
@delegate:CacheKey
举个例子：
含义
CacheKey 注解作用于文件
CacheKey 注解作用于属性
CacheKey 注解作用于字段
CacheKey 注解作用丁 Getter
含义
CacheKey EHF Setter
CacheKey注解作用于扩展函数或属性
CacheKey注解作用于构造函数参数
CacheKey 注解作用 Setter 的参数
CacheKey注解作用于存储代理实例的字段
@Cache(namespace = "hero", expires = 3600)
data class Hero(
（续）
@property:CacheKey(keyName = "heroName", buckets = = intArrayOf(1,
val name: String,
@field:CacheKey(keyName = "atk", buckets = intArrayOf(1, 2, 3))
val attack: Int,

Page 527
@get:CacheKey(keyName = "def", buckets = intArrayOf(1, 2, 3))
val defense: Int,
val initHp: Int
上述CacheKey注解分别作用在熟悉、字段和Getter上。

Page 528
8。3。3获取注解信息
代码标记上注解之后，注解本身也成了代码的一部分，我们自然
而然就会想到如何利用这些注解信息。Kotlin当然也提供方法获取注
解信息。
1。通过反射获取注解信息
一个自然而然的方案是通过反射去获取注解信息，这有一个前提
就是这个注解的Retentaion标注为Runtime或者没有显示指定(注默
认为Runtime）。前文中我们已经了解到如何通过反射获取类及其成
员，获取了这些数据之后，很容易就可以通过API获取其注解信息。
如：
annotation class Cache(val namespace: String, val expires: Int)
annotation class CacheKey(val keyName: String, val buckets: IntArray)
@Cache(namespace = "hero", expires = 3600)
data class Hero(
@CacheKey(keyName = "heroName", buckets = intArrayOf(1,2,3))
val name: String,
val attack: Int,
val defense: Int,
val initHp: Int
）

Page 529
fun main(args: Array<String>){
val cacheAnnotion = Hero::class.annotations.find{ it is Cache} as Cache?
println("namespace ${cacheAnnotion?.namespace}")
println("expires ${cacheAnnotion?.expires}")
}
显而易见，通过反射获取注解信息是在运行时发生的，和Java一
样存在一定的性能开销，当然这种开销大部分时候可以忽略不计。此
外前面提到的注解标准位置也会影响注解信息的获取。例如@file：
CacheKey这样标准的注解,则无法通调用KProperty.annotions获取到
该注解信息。
2。注解处理器
众所周知,JSR269引入了注解处理器(annotation processors),
允许我们在编译过程中挂钩子实现代码生成。得益于此，如dagger之
类的框架实现了编译时依赖注入这样原本只能通过运行时反射支持的
特性。
在了解什么是注解处理器之前，我们先来看看编译器的主要工
作，如图8-3所示。
如图8-3所示，我们可以把编译器看成一个输入为源代码，输出
为目标代码的程序。这个程序的第一步是将源文件解析为AST（抽象
语法树），实现这部分的程序通常被称为解析器（parser）。

Page 530
源代码
注解处理器
解析器
（词法分析和语法分析）
抽象语法树（AST）
生成器
目标代码（。class）
图8-3编译器的主要工作
解析器解析完毕会将AST传给注解处理器。
需要澄清一点,JSR269脱胎于javac,对于eclipse ecj之类的编译
器通常有自己的AST，它需要额外适配到JSR269定义的AST。
这里本来应该是代码生成的最佳场合，理论上应该可以实现对
AST进行修改，然而JSR269是只读API，这就限制了你不能修改任何
传入注解处理器的AST。如果要实现代码生成，只能非常蹩脚地将代
码以字符串形式写入另一个文件，这不得不说是一个非常大的遗憾。

Page 531
下面来看一个例子：
import
javax.annotation.processing.*
import javax.lang.model.element. ElementKind
import javax.lang.model.element. TypeElement
import kotlin.reflect.full.member Properties
import javax.tools.JavaFileObject
annotation class MapperAnnotation
class MapperProcessor: AbstractProcessor() {
private fun genMapperClass(pkg: String, clazzName: String, props: List<St
TODO()
}
override fun process(set: MutableSet<out TypeElement>?, env: Round Env
val el = env?.getElementsAnnotated With (MapperAnnotation::class.java)
if (el?.kind == ElementKind.CLASS) {
val pkg = el.javaClass.`package`.name
val cls= el.javaClass.simpleName
val props = el.javaClass.kotlin.member Properties.map { it.name}
val mapperClass = genMapperClass(pkg, cls, props)
val jfo = processingEnv.filer.createSourceFile(
cls + "Mapper")
val writer = jfo.openWriter()
writer.write(mapperClass)
writer.close()

Page 532
}
}
}
return true;
在这个例子中，我们根据Mapper注解获取对应的类系信息，并
生成一个XXXMapper类,里面实现自动转化为Mapper的方法。可以
看到,Annotation Processor没有能力直接修改AST,而只能创建一个
文件，并将代码写入该文件。
就像上面的geMapperClass函数，我们只能以字符串形式生成
Java代码:
private fun genMapperClass(pkg: String, clazzName: String, props: List<Strin
return
package $pkg;
import java.util.*;
public class ${clazzName}Mapper {
public Map<String, Object> toMap($clazzName a) {
Map<String, Object> m = new HashMap<String, Object>();
${
props.map {
"m。put（\"${it}\"，a。${it}）"
}

Page 533
}
}
注解处理器的使用方法也和Java一样：
1)添加注解处理器信息。这需要在classpath里包含META-INFO/
services/javax.annotation.processing.Processor文件,并将注解处理器
包名和类名写入该文件。
2)使用 kapt 插件。如果是gradle工程可以通过 apply
plugin:'kotlin-kapt'添加注解处理器支持。
kapt也支持生成Kotlin代码。如上述例子中，我们可以将
genMapperClass中的代码替换为Kotlin代码,并且将其存储在
processingEnv.options["kapt.kotlin.generated"目录中。
虽然annotation processor允许开发人员访问程序AST,但没有提
供行之有效的代码生成方案，目前仅有的代码生成方案也仅仅是将代
码以字符串的形式写入新文件，而无法做到直接将生成的AST作为程
序。这也说明了Java和Kotlin目前不具备同像性。

Page 534
8。4本章小结
（1）元编程
编程语言自身描述自身的一种手段，主要分为运行时期的元编程
和编译时期的元编程，不同的编程语言对它们的支持程度不尽相同。
(2)Kotlin反射
Kotlin目前只支持运行时期的元编程———反射，涉及的类有主要
有KClass,KCallable,KParameter,KFunction,KProperty等。我们
已经详细介绍了它们的用法。总的来说，Kotlin的元编程和Java的非
常接近，但得益于本身语法特性，Kotlin的反射API使用更加简洁高效。
（3）注解
一种可以代替配置文件的手段，可以通过反射在运行期间获取。
具体介绍了如何定义及使用注解，以及如何控制注解作用的位置。
（4）注解处理器
介绍了注解处理器的原理和使用方法，但是比较遗憾的是，
Kotlin目前和Java一样没有简单优雅的代码生成方案，开发人员要么
通过注解处理器手工将代码写入文件，要么直接依赖javac的treeapi

Page 535
牺牲可移植性。这两种方案不管哪种都不是很理想，使用起来颇为费
力。

Page 536
潜入篇
Kotlin探索
·第9章设计模式
第10章函数式编程
·第11章异步和并发

Page 537
第9章设计模式
设计模式是一个老生常谈的东西了，它不是一个类、包或类库，
而是软件工程中解决特定问题的一种指南。我们通常所说的经典的设
计模式，是指软件设计领域的四位大师（GoF）在《设计模式：可复
用面向对象软件的基础》中所阐述的23种设计模式。
这些二十几年前就提出来的代码设计的总结，主要采用了类和对
象的方式，至今依旧被广泛用于C++、Java等面向对象的语言。然而，
Kotlin是一门多范式的语言，在之前的章节中我们已经感受过它如何
用函数式的语言特性，在程序设计中会带来更多的可能性。我们已经
知道，Kotlin中不需要所谓的“单例模式”，因为它在语言层面就已经
支持了这一特性。所以也有人说，设计模式无非只是一些编程语言没
有支持的特性罢了。某种程度上看确实如此，然而也未必准确，因为
越高级的语法特性伴随而来的设计模式也会更加高级。
因此，本章的主要内容是通过Kotlin的语言特性，来重新思考
Java中常见的设计模式，由此我们可以进一步认识Kotlin语言特点，
以及了解如何在实际代码设计中运用它们。

Page 538
需要注意的是，本章内容论述的形式依旧采用了GoF针对常见设
计模式的分类方式，即创建型模式、行为型模式、结构型模式。同时，
基于Kotlin崭新的语言特性，我们在23种常见的设计模式中，实现或
替代了Java中部分典型的设计模式。其中访问者模式已经在第4章进
行过详细介绍，在Kotlin中可以利用模式匹配和when表达式对其改良，
本章将不会重复提及。

Page 539
9。1创建型模式
在程序设计中，我们做得最多得事情之一就是去创建一个对象。
创建对象虽然看起来简单，但实际的业务或许十分复杂，这些对象的
类可能存在子父类继承关系，或者代表了系统中各种不同的结构和功
能。因此，创建怎样的对象，如何且何时创建它们，以及对类和对象
的配置，都是实际代码编写中需要考虑的问题。
本节将探讨Kotlin中几种最主流的创建型设计模式：工厂方法模
式、抽象工厂模式以及构建者模式。

Page 540
9。1。1伴生对象增强工厂模式
工厂模式是我们最熟悉的设计模式之一，在有些地方会把工厂模
式细分为简单工厂、工厂方法模式以及抽象工厂。本节我们主要介绍
简单工厂的模式，它的核心作用就是通过一个工厂类隐藏对象实例的
创建逻辑，而不需要暴露给客户端。典型的使用场景就是当拥有一个
父类与多个子类的时候，我们可以通过这种模式来创建子类对象。
假设现在有一个电脑加工厂，同时生产个人电脑和服务器主机。
我们用熟悉的工厂模式设计描述其业务逻辑：
interface Computer {
val cpu: String
}
class PC(override val cpu: String = "Core") : Computer
class Server(override val cpu: String = "Xeon") : Computer
enum class Computer Type {
PC, Server
}
class ComputerFactory {
fun produce(type: ComputerType): Computer {
return when (type) {
}
ComputerType.PC -> PC()
ComputerType.Server -> Server()

Page 541
}
}
以上代码通过调用ComputerFactory类的produce方法来创建不同
的Computer子类对象，这样我们就把创建实例的逻辑与客户端之间
实现解耦，当对象创建的逻辑发生变化时（如构造参数的数量发生变
化），该模式只需要修改produce方法内部的代码即可，相比直接创
建对象的方式更加利于维护。
现在我们用设计好的类写一段测试的代码：

>>> val comp = ComputerFactory().produce(ComputerType.PC)
>>> println(comp.cpu)
>>> Core
>>> 这是我们用Kotlin模仿Java中很标准的工厂模式设计，它改善了
>>> 程序的可维护性，但创建对象的表达上却显得不够简洁。当我们在不
>>> 同的地方创建Computer的子类对象时，我们都需要先创建一个
>>> ComputerFactory类对象。在3.5.2节中我们了解到Kotlin天生支持了单
>>> 例，接下来我们就用object关键字以及其相关的特性来进一步简化以
>>> 上的代码设计。
>>> 1。用单例代替工厂类
>>> 我们已经知道的是，Kotlin支持用object来实现Java中的单例模式。

Page 542
所以,我们可以实现一个ComputerFactory单例,而不是一个工厂
类。
object ComputerFactory { // object class
fun produce(type: ComputerType): Computer {
return when (type) {
}
}
}
ComputerType.PC -> PC()
ComputerType.Server -> Server()
然后，我们就可以如此调用：
ComputerFactory.produce(ComputerType.PC)
此外，由于我们通过传入Computer类型来创建不同的对象，所
以这里的produce又显得多余。如果你阅读过第7章，那么就会了解
Kotlin还支持运算符重载，因此我们可以通过operator操作符重载
invoke方法来代替produce,从而进一步简化表达:
object ComputerFactory {
operator fun invoke(type: ComputerType): Computer {

Page 543
}
}
return when (type) {
ComputerType.PC -> PC()
ComputerType.Server -> Server()
}
依靠Kotlin这一特性，我们再创建一个Computer对象就显得非常
简洁，与直接创建一个具体类实例显得没有太大区别：
ComputerFactory(ComputerType.PC)
2。伴生对象创建静态工厂方法
当前的工厂模式实现已经足够优雅，然而也许你依旧觉得不够完
美:我们是否可以直接通过Computer()而不是ComputerFactory)
来创建一个实例呢?
提到这个问题，也许我们还想到了《EffectiveJava》一书的第1
条指导原则：考虑用静态工厂方法代替构造器。相信你已经想到了
Kotlin中的伴生对象，它代替了Java中的static，同时在功能和表达上
拥有更强的能力。通过在Computer接口中定义一个伴生对象，我们
就能够实现以上的需求，代码如下：

Page 544
interface Computer {
val cpu: String
}
companion object {
operator fun invoke(type: ComputerType): Computer {
return when (type) {
}
}
ComputerType.PC -> PC()
ComputerType.Server -> Server()
然后再来测试下：

>>> Computer(ComputerType.PC)
>>> Core
>>> 在不指定伴生对象名字的情况下，我们可以直接通过Computer
>>> 来调用其伴生对象中的方法。当然，如果你觉得还是Factory这个名
>>> 字好，那么也没有问题，我们可以用Factory来命名Computer的伴生
>>> 对象，如下：

Page 545
interface Computer {
val cpu: String
}
companion object Factory {
operator fun invoke(type: ComputerType): Computer {
return when (type) {
}
}
ComputerType.PC -> PC()
ComputerType.Server -> Server()
调用方法如下：
Computer.Factory(ComputerType.PC)
3。扩展伴生对象方法
依靠伴生对象的特性，我们已经很好地实现了经典的工厂模式。
同时，这种方式还有一种优势，它比原有Java中的设计更加强大。假
设实际业务中我们是Computer接口的使用者，比如它是工程引入的
第三方类库，所有的类的实现细节都得到了很好地隐藏。那么，如果
我们希望进一步改造其中的逻辑，Kotlin中伴生对象的方式同样可以
依靠其扩展函数的特性，很好地实现这一需求。

Page 546
比如我们希望给Computer增加一种功能，通过CPU型号来判断
电脑类型，那么就可以如下实现：
fun Computer.Companion.fromCPU(cpu: String): ComputerType? = when(cpi
"Core" -> ComputerType.PC
}
"Xeon" -> ComputerType.Server
else -> null
如果指定了伴生对象的名字为Factory，那么就可以如下实现：
fun Computer.Factory.fromCPU(cpu: String): ComputerType? = ...

Page 547
9。1。2内联函数简化抽象工厂
在第6章中，我们了解到Kotlin中的内联函数有一个很大的作用，
就是可以具体化参数类型。利用这一特性，我们还可以改进一种更复
杂的工厂模式，称为抽象工厂。
工厂模式已经能够很好地处理一个产品等级结构的问题，在上一
节中，我们已经用它很好地解决了电脑厂商生产服务器、PC机的问
题。进一步思考，当问题上升到多个产品等级结构的时候，比如现在
引入了品牌商的概念，我们有好几个不同的电脑品牌，比如Dell、
Asus、Acer，那么就有必要再增加一个工厂类。然而，我们并不希
望对每个模型都建立一个工厂，这会让代码变得难以维护，所以这时
候我们就需要引入抽象工厂模式。
抽象工厂模式
为创建一组相关或相互依赖的对象提供一个接口，而且无须指定它们
的具体类。
在抽象工厂的定义中，我们也可以把“一组相关或相互依赖的对
象”称作“产品族”，在上述的例子中，我们就提到了3个代表不同
电脑品牌的产品族。下面我们就利用抽象工厂，来实现具体的需求：
interface Computer
class Dell: Computer
class Asus: Computer

Page 548
class Acer: Computer
class DellFactory: AbstractFactory() {
override fun produce() = Dell()
}
class AsusFactory: AbstractFactory() {
override fun produce() = Asus()
}
class AcerFactory: Abstract Factory() {
override fun produce() = Acer()
}
abstract class AbstractFactory {
abstract fun produce(): Computer
companion object {
operator fun invoke(factory: AbstractFactory): AbstractFactory {
return factory
}
}
可以看出，每个电脑品牌拥有一个代表电脑产品的类，它们都实
现了Computer接口。此外每个品牌也还有一个用于生产电脑的
AbstractFactory+*,
AbstractFactory*#***#invoke
方法，来构造具体品牌的工厂类对象。

Page 549
fun main(args: Array<String>){
val dellFactory = AbstractFactory(DellFactory())
val dell = dellFactory.produce()
println(dell)
}
运行该测试用例，结果如下：
Dell@1f32e575
由于Kotlin语法的简洁，以上例子的抽象工厂类的设计也比较直
观。然而，当你每次创建具体的工厂类时，都需要传入一个具体的工
厂类对象作为参数进行构造，这个在语法上显然不是很优雅。下面我
们就来看看，如何用Kotlin中的内联函数来改善这一情况。我们所需
要做的,就是去重新实现AbstractFactory类中的invoke方法。
abstract class AbstractFactory {
abstract fun produce(): Computer
companion object {
inline operator fun <reified T: Computer> invoke(): AbstractFactory = wt
Dell::class -> DellFactory()
Asus::class -> AsusFactory()
Acer::class -> AcerFactory()

Page 550
}
}
else
-> throw IllegalArgumentException()
这下我们的invoke方法定义的前缀变长了很多，但是不要害怕，
如果你已经掌握了内联函数的具体应用，应该会很容易理解它。我们
来分析下这段代码：
1）通过将invoke方法用inline定义为内联函数，我们就可以引入
reified关键字，使用具体化参数类型的语法特性；
2）要具体化的参数类型为Computer，在invoke方法中我们通过
判断它的具体类型，来返回对应的工厂类对象。
}
我们来看看如何用上述重写的方法，来改善工厂类的创建语法表
达：
fun main(args: Array<String>){
val dellFactory = AbstractFactory<Dell>()
val dell = dellFactory.produce()
println(dell)
现在我们终于可以用类似创建一个泛型类对象的方式，来构建一

Page 551
个抽象工厂具体对象了。不管是工厂方法还是抽象工厂，利用Kotlin
的语言特性，我们在一定程度上改进、简化了Java中设计模式的实现。
在下一节中，我们将继续讨论Kotlin中的构建者模式，这也是一种非
常经典的设计模式。

Page 552
9。1。3用具名可选参数而不是构建者模式
在Java开发中，你是否写过这样像蛇一样长的构造函数：
//Boolean类型的参数表示Robot是否含有对应固件
Robot robot = new Robot(1, true, true, false, false, false, false, false, false)
刚写完时回头看你还能看懂，一天后你可能已经忘记大半了，再
过一个星期你已经不知道这是什么东西了。面对这样的业务场景时，
我们惯常的做法是通过Builder（构建者）模式来解决。
构建者模式
构建者模式与单例模式一样，也是Gof设计模式中的一种。它主要做
的事情就是将一个复杂对象的构建与它的表示分离，使得同样的构建
过程可以创建不同的表示。
工厂模式和构造函数都存在相同的问题，就是不能很好地扩展到
大量的可选参数。假设我们现在有个机器人类，它含有多个属性：代
号、名字、电池、重量、高度、速度、音量等。很多产品都不具有其
中的某些属性，比如不能走、不能发声，甚至有的机器人也不需要电
池。
一种糟糕的做法就是设计一个一开头你所看到Robot类，把所有
的属性都作为构造函数的参数。或者，你也可能采用过重叠构造器
(telescoping constructor)模式,即先提供一个只有必要参数的构造

Page 553
函数，然后再提供其他更多的构造函数，分别具有不同情况的可选属
性。虽然这种模式在调用的时候改进不少，但同样存在明显的缺点。
因为随着构造函数的参数数量增加，很快我们就会失去控制，代码变
得难以维护。
构建者模式可以避免以上的问题，我们用Kotlin来实现Java中的
构建者模式，如代码清单9-1所示。
代码清单9-1
class Robot private constructor(
val code: String,
val battery: String?,
val height: Int?,
val weight: Int?){
class Builder(val code: String) {
private var battery: String? = null
private var height: Int? = null
private var weight: Int? = null
fun setBattery(battery: String?): Builder {
this.battery = battery
return this
}

Page 554
}
}
fun setHeight(height: Int): Builder {
this.height = height
return this
}
fun setWeight(weight: Int): Builder {
this.weight = weight
return this
}
fun build(): Robot {
return Robot(code, battery, height, weight)
}
为了避免代码过于冗长，以上的例子我们只选择了4个属性，其
中code(机器人代号)为必需属性,battery(电池)、height(高
度）、weight（重量）为可选属性。我们再看看如何用这种方式来声
明一个Robot对象:
val robot = Robot.Builder("007")
.setBattery("R6")
.setHeight(100)
.setWeight(80)
.build()

Page 555
我们来分析下它的具体思路：
·Robot类内部定义了一个嵌套类Builder,由它负责创建Robot对象;
·Robot类的构造函数用private进行修饰，这样可以确保使用者无法直
接通过Robot声明实例；
·通过在Builder类中定义set方法来对可选的属性进行设置；
·最终调用Builder类中的build方法来返回一个Robot对象。
这种链式调用的设计看起来确实优雅了不少，同时对于可选参数
的设置也显得比较语义化，它有点近似2。3。8节中介绍的柯里化语
法。此外，构建者模式另外一个好处就是解决了多个可选参数的问题，
当我们创建对象实例时，只需要用set方法对需要的参数进行赋值即
可。
然而，构建者模式也存在一些不足：
1）如果业务需求的参数很多，代码依然会显得比较冗长；
2）你可能会在使用Builder的时候忘记在最后调用build方法；
3）由于在创建对象的时候，必须先创建它的构造器，因此额外
增加了多余的开销，在某些十分注重性能的情况下，可能就存在一定
的问题。
事实上，当用Kotlin设计程序时，我们可以在绝大多数情况下避

Page 556
免使用构建者模式。《EffectiveJava》在介绍构建者模式时，这样
子描述它的：本质上builder模式模拟了具名的可选参数，就像Ada和
Python中的一样。幸运的是，Kotlin也是这样一门拥有具名可选参数
的编程语言。
2。具名的可选参数
Kotlin中的函数和构造器都支持这一特性，我们已经在第3章介绍
过相关知识，现在再来回顾下。它主要表现为两点：
1）在具体化一个参数的取值时，可以通过带上它的参数名，而
不是它在所有参数中的位置决定；
2）由于参数可以设置默认值，这允许我们只给出部分参数的取
值，而不必是所有的参数。
因此，我们可以直接使用Kotlin中原生的语法特性来实现构建者
模式的效果。现在重新设计以上的Robot例子：
class Robot(
val code: String,
val battery: String? = null,
val height: Int? = null,
val weight: Int? = null
）
val robot1 = Robot(code = "007")

Page 557
val robot2 = Robot(code = "007", battery = "R6")
val robot3 = Robot(code = "007", height = 100, weight = 80)
可以发现，相比构建者模式，通过具名的可选参数构造类具有很
多优点：
1）代码变得十分简单，这不仅表现在Robot类的结构体代码
量，我们在声明Robot对象时的语法也要更加简洁；
2）声明对象时，每个参数名都可以是显式的，并且无须按照顺
序书写，非常方便灵活；
3）由于Robot类的每个对象都是val声明的，相较构建者模式者
中用var的方案更加安全，这在要求多线程并发安全的业务场景中会
显得更有优势。
此外，如果你的类的功能足够简单，更好的思路是用dataclass
直接声明一个数据类。如你所知，数据类同样支持以上的所有特性。
3。require方法对参数进行约束
我们再来看看那构建者模式的另外一个作用，就是可以在build方
法中对参数添加约束条件。举个例子，假设一个机器人的重量必须根
据电池的型号决定，那么在未传入电池型号之前，你便不能对weight
属性进行赋值，否则就会抛出异常。现在我们再来重新改下代码清单
9-1中的build方法实现：

Page 558
fun build(): Robot {
if (weight != null && battery == null) {
throw IllegalArgumentException("Battery should be determined when set
}
}else {
return Robot(code, battery, height, weight)
}
运行下具体的测试用例：
val robot = Robot.Builder("007")
.setWeight(100)
.build()
然后就会发现以下的异常信息：
Exception in thread "main" java.lang.IllegalArgumentException: Battery shoulk
这种在build方法中对参数进行约束的手段，可以让业务变得更加
安全。那么，通过具名的可选参数来构造类的方案该如何实现呢?
显然，我们同样可以在Robot类的init方法中增加以上的校验代码。
然而在Kotlin中，我们在类或函数中还可以使用require关键字进行函

Page 559
数参数限制，本质上它是一个内联的方法，有点类似于Java中的
assert。
class Robot(
）{
}
val code: String,
val battery: String? = null,
val height: Int? = null,
val weight: Int? = null
init {
}
null || battery != null) {
"Battery should be determined when setting weight."
}
require(weight: ==
不难发现，如果我们在创建Robot对象时有不符合require条件的
行为，就会导致抛出异常。

>>> val robot = Robot(code="007", weight = 100)
>>> java.lang.IllegalArgumentException: Battery should be determined when setti
>>> 可见，Kotlin的require方法可以让我们的参数约束代码在语义上

Page 560
变得更加友好。总的来说，在Kotlin中我们应该尽量避免使用构建者
模式，因为Kotlin支持具名的可选参数，这让我们可以在构造一个具
有多个可选参数类的场景中，设计出更加简洁并利于维护的代码。

Page 561
9。2行为型模式
当我们用创建型模式创建出类对象之后，就需要在不同对象之间
划分职责、产生交互。那些用来识别对象之间的常用交流模式就是本
节要讲述的行为型模式。类似上一节，我们同样会用Kotlin的语法来
重新思考几种主流的行为型模式，包括：观察者模式、策略模式、模
板方法模式、迭代器模式、责任链模式及状态模式。

Page 562
9。2。1Kotlin中的观察者模式
观察者模式是我们接触最多的设计模式之一，尤其是在Android
开发中，诸多设计都是基于观察者模式来实现的，如MVC架构、
rxJava类库的设计等。同时，我们也肯定逃不了用该模式来管理视图
变化的逻辑响应。我们先来看看它的定义：
观察者模式定义了一个一对多的依赖关系，让一个或多个观察者对象
监听一个主题对象。这样一来，当被观察者状态发生改变时，需要通
知相应的观察者，使这些观察者对象能够自动更新。
简单来说，观察者模式无非做两件事情：
·订阅者（也称为观察者observer）添加或删除对发布者（也称为观察
者publisher)的状态监听;
·发布者状态改变时，将事件通知给监听它的所有观察者，然后观察
者执行响应逻辑。
Java 自身的标准库提供了java.util.Observable 类和
java。util。Observer接口，来帮助实现观察者模式。接下来我们就采用
它们来实现一个动态更新股价的例子。
import java.util.*
class StockUpdate: Observable() {
val observers = mutableSetOf<Observer>();

Page 563
fun setStockChanged(price: Int) {
this.observers.forEach { it.update(this, price) }
}
}
}
class StockDisplay: Observer {
override fun update(o: Observable, price: Any) {
if (o is StockUpdate) {
println("The latest stock price is ${price}.")
}
}
在上述例子中，我们首先创建了一个可被观察的发布者类
StockUpdate,它维护了一个监听其变化的观察者对象observers,通
过它的add和remove方法来进行管理。当StockUpdate类对象执行
setStockChanged方法之后，表明股价已经改变，那么就会将更新的
股价传递给观察者，执行其update方法来执行响应逻辑。这些观察者
都是StockDisplay的对象,当发现接收到的订阅者类型为StockUpdate
时，就会打印最新的股价。
下面我们就来创建一个测试用例：
fun main(args: Array<String>) {
val su =
StockUpdate()

Page 564
val sd = : StockDisplay()
su.observers.add(sd)
su.setStockChanged(100)
}
//运行结果
The latest stock price is 100.
由于Kotlin在语法上相比Java要更简洁，所以如果用Java实现以
上的例子会需要更多的代码。然而它们的实现的思路是一样的，都是
利用了Java标准库中的类和方法。事实上，Kotlin的标准库额外引入
了可被观察的委托属性，也可以利用它来实现同样的场景。
1.Observable
我们先用这一委托属性来改造以上的程序，然后再分析其相关的
语法。
import kotlin.properties.Delegates
interface StockUpdateListener {
fun onRise(price: Int)
fun onFall(price: Int)
}
class StockDisplay: StockUpdateListener {
override fun onRise(price: Int) {
println("The latest stock price has risen to ${price}.")

Page 565
}
override fun onFall(price: Int) {
println("The latest stock price has fell to ${price}.")
}
}
}
class StockUpdate {
var listeners = mutableSetOf<StockUpdateListener>()
var price: Int by Delegates.observable(0) { _, old, new ->
listeners.forEach {
if (new > old) it.onRise(price) else it.onFall(price)
}
}
在该版本中，我们让需求变得更加的具体，当股价上涨或下跌时，
我们会打印不同的个性化报价文案。如果你仔细思考，会发现实现
java.util.Observer接口的类只能覆写update方法来编写响应逻辑,也
就是说如果存在多种不同的逻辑响应，我们也必须通过在该方法中进
行区分实现，显然这会让订阅者的代码显得臃肿。换个角度，如果我
们把发布者的事件推送看成一个第三方服务，那么它提供的API接口
只有一个，API调用者必须承担更多的职能。
显然,使用Delegates.observable()的方案更加灵活。它提供了
3个参数，依次代表委托属性的元数据KProperty对象、旧值以及新值。
通过额外定义一个StockUpdateListener接口,我们可以把上涨和下跌

Page 566
的不同响应逻辑封装成接口方法，从而在StockDisplay中实现该接口
的onRise和onFall方法,实现了解耦。
同样，我们来运行下该方案的测试用例：
fun main(args: Array<String>){
val su = StockUpdate()
val sd = StockDisplay()
su.listeners.add(sd)
su.price = 100
su.price = 98
}
//运行结果
The latest stock price has risen to 100.
The latest stock price has fell to 98.
2.Vetoable
有些时候，我们并不希望监控的值可以被随心所欲地修改。实际
上，你可能希望对某些改值的情况进行否决。Kotlin的标准库中除了
提供observable这个委托属性之外，还提供了另外一个属性：
vetoable。顾名思义,veto代表的是“否决”的意思,vetoable提供了
一种功能，在被赋新值生效之前提前进行截获，然后判断是否接受它。
通过以下的例子你可以更好地了解vetoable的使用：

Page 567
import kotlin.properties.Delegates
var value: Int by Delegates.vetoable(0) { prop, old, new ->
new>0
}

>>>value=1
>>>println(value)
>>>1
>>>value=-1
>>>println(value)
>>>1
>>>我们创建了一个可变的Int对象value，同时用by关键字增加了
>>>Delegates。vetoable委托属性。它的初始化值为0，只接收被正整数赋
>>>值。所以，当我们试图把value改成-1的时候，打印的结果仍然为旧
>>>值1。

Page 568
9。2。2高阶函数简化策略模式、模板方法模式
本节我们会同时讨论策略模式、模板方法模式，一方面它们解决
的问题比较类似，另一方面这两种设计模式都可以依靠Kotlin中的高
阶函数特性进行改良。
1。遵循开闭原则：策略模式
假设现在有一个表示游泳运动员的抽象类Swimmer，有一个游泳
的方法swim，表示如下：
class Swimmer {
fun swim() {
println("I am swimming...")
}
}
我们用Swimmer类来创建一个对象shaw:
val shaw = Swimmer()

>>> shaw.swim()
>>> I am swimming...
>>> 由于shaw在游泳方面很有天赋，他很快掌握了蛙泳、仰泳、自

Page 569
由泳多种姿势。所以我们必须对Swim方法进行改造，变成代表3种不
同游泳姿勢的方法。
class Swimmer {
}
fun breaststroke() {
println("I am breaststroking...")
}
fun backstroke() {
println("I am backstroke...")
}
fun freestyle() {
}
println("I am freestyling...")
然而这并不是一个很好的设计。首先，并不是所有的游泳运动员
都掌握了这3种游泳姿势，如果每个Swimmer类对象都可以调用所有
方法，显得比较危险。其次，后续难免会有新的行为方法加入，通过
修改Swimmer类的方式违背了开放封闭原则。
因此，更好的做法是将游泳这个行为封装成接口，根据不同的场
景我们可以调用不同的游泳方法。比如shaw计划周末游自由泳，其
他时间则游蛙泳。策略模式就是一种解决这种场景很好的思路。
策略模式定义了算法族，分别封装起来，让它们之间可以相互替

Page 570
换，此模式让算法的变化独立于使用算法的客户。
本质上，策略模式做的事情就是将不同的行为策略（Strategy）
进行独立封装，与类在逻辑上解耦。然后根据不同的上下文
（Context）切换选择不同的策略，然后用类对象进行调用。下面我们
用熟悉的方式重新实现游泳的例子：
interface SwimStrategy {
fun swim()
}
class Breaststroke: SwimStrategy {
override fun swim() {
println("I am breaststroking...")
}
}
class Backstroke: SwimStrategy {
override fun swim() {
println("I am backstroke...")
}
}
}
class Freestyle: SwimStrategy {
override fun swim() {
println("I am freestyling...")
}

Page 571
class Swimmer(val strategy: SwimStrategy) {
fun swim() {
strategy.swim()
}
}
fun main(args: Array<String>){
val weekendShaw = Swimmer(Freestyle())
weekendShaw.swim()
val weekdaysShaw = Swimmer(Breaststroke())
weekdaysShaw.swim()
}
//运行结果
I am freestyling...
I am breaststroking...
这个方案实现了解耦和复用的目的，且很好实现了在不同场景切
换采用不同的策略。然而，该版本的代码量也比之前多了很多。下面
我们来看看Kotlin如何用高阶函数来简化策略模式。
2。高阶函数抽象算法
我们用高阶函数的思路来重新思考下策略类，显然将策略封装成
一个函数然后作为参数传递给Swimmer类会更加的简洁。由于策略类
的目的非常明确，仅仅是针对行为算法的一种抽象，所以高阶函数式
是一种很好的替代思路。

Page 572
fun breaststroke() { println("I am breaststroking...") }
fun backstroke() { println("I am backstroking...") }
fun freestyle() { println("I am freestyling...")}
现在，利用高阶函数我们重新实现这个例子：
class Swimmer(val swimming: () -> Unit) {
fun swim() {
swimming()
}
}
}
fun main(args: Array<String>){
val weekendShaw = Swimmer(::freestyle)
weekendShaw.swim()
val weekdaysShaw = Swimmer(::breaststroke)
weekdaysShaw.swim()
代码量一下子变得非常少，而且结构上也更加容易阅读。由于策
略算法都封装成了一个个函数，我们在初始化Swimmer类对象时，可
以用函数引用的语法（参见2。3节）传递构造参数。当然，我们也可
以把函数用val声明成Lambda表达式，那么在传递参数的时候会变得
更加简洁直观。

Page 573
3。模板方法模式：高阶函数代替继承
另一个可用高阶函数函数改良的设计模式，就是模板方法模式。
某种程度上，模板方法模式和策略模式要解决的问题是相似的，它们
都可以分离通用的算法和具体的上下文。然而，如果说策略模式采用
的思路是将算法进行委托，那么传统的模板方法模式更多是基于继承
的方式实现的。现在来看看模板方法模式的定义：
定义一个算法中的操作框架，而将一些步骤延迟到子类中，使得子类
可以不改变算法的结构即可重定义该算法的某些特定步骤。
与策略模式不同，模板方法模式的行为算法具有更明晰的大纲结
构，其中完全相同的步骤会在抽象类中实现，可个性化的某些步骤则
在其子类中进行定义。举个例子，如果我们去市民事务中心办事时，
一般都会有以下几个具体的步骤：
1）排队取号等待；
2）根据自己的需求办理个性化的业务，如获取社保清单、申请
市民卡、办理房产证；
3）对服务人员的态度进行评价。
这是一个典型的适用模板方法模式的场景，办事步骤整体是一个
中步骤1）和步骤3）都是相
而步骤2）可
算法大
以根据实际需求个性化选择。接下来我们就用代码实现一个抽象类，
它定义了这个例子的操作框架：

Page 574
abstract class CivicCenterTask {
fun execute() {
this.lineUp()
}
this.askForHelp()
this.evaluate()
}
private fun lineUp() {
println("line up to take a number");
}
private fun evaluate() {
println("evaluaten service attitude");
}
abstract fun askForHelp()
其中askForHelp方法是一个抽象方法。接下来我们再定义具体的
子类来继承CivicCenter-Task类,然后对抽象的步骤进行实现。
class PullSocial Security: CivicCenterTask {
override fun askForHelp() {
println("ask for pulling the social security")
}
}
class ApplyForCitizenCard: CivicCenterTask {

Page 575
}
override fun askForHelp() {
println("apply for a citizen card")
}
然后写个测试用例来创建这些子类，进行调用：
val pss = PullSocialSecurity()

>>> pss.execute()
>>> line up to take a number
>>> ask for pulling the social security
>>> evaluaten service attitude
>>> val afcc = ApplyForCitizenCard()
>>> afcc.execute()
>>> line up to take a number
>>> apply for a citizen card
>>> evaluaten service attitude
>>> 不出意料，两者的步骤2）的执行结果是不一样的。
>>> 不得不说，模板方式模式的代码复用性已经非常高了，但是我们
>>> 还是得根据不同的业务场景都定义一个具体的子类。幸运的是，在
>>> Kotlin中我们同样可以用改造策略模式的类似思路，来简化模板方法
>>> 模式。依靠高阶函数，我们可以在只需一个CivicCenterTask类的情况

Page 576
下，代替继承实现相同的效果。
class CivicCenterTask {
fun execute(askForHelp: () -> Unit) {
this.lineUp()
askForHelp()
this.evaluate()
}
private fun lineUp() {
println("line up to take a number");
}
}
private fun evaluate() {
println("evaluaten service attitude");
}
}
fun pullSocial Security() {
println("ask for pulling the social security")
}
fun applyForCitizenCard() {
println("apply for a citizen card")
代码量果真又减少了许多。再来看看该方案如何调用逻辑：

Page 577
val task1 = CivicCenterTask()

>>> task1.execute(::pullSocial Security)
>>> line up to take a number
>>> ask for pulling the social security
>>> evaluaten service attitude
>>> val task2= CivicCenterTask()
>>> task2.execute(::applyForCitizenCard)
>>> line up to take a number
>>> apply for a citizen card
>>> evaluaten service attitude
>>> 如你所见，在高阶函数的帮助下，我们可以更加轻松地实现模板
>>> 方式模式。

Page 578
9。2。3运算符重载和迭代器模式
迭代器（iterator）是Java中我们非常熟悉的东西了，数据结构如
List和Set都內置了迭代器，我们可以用它提供的方法来顺序地访问一
个聚合对象中各个元素。
有些时候，我们会定义某些容器类，这些类中包含了大量相同类
型的对象。如果你想给这个容器类的对象直接提供迭代的方法，如
hasNext、next、first等，那么就可以自定义一个迭代器。然而通常情
况下，我们不需要自己再实现一个迭代器，因为Java标准库提供了
java。util。lterator接口，你可以用容器类实现该接口，然后再实现需要
的迭代器方法。
这种设计模式就是迭代器模式，它的核心作用就是将遍历和实现
分离开来，在遍历的同时不需要暴露对象的內部表示。迭代器模式非
常容易理解，你可能已经非常熟悉。但我们还是举个具体的例子来介
绍下这种模式，接着引出Kotlin中相关的语法特性，继而进行改良。
1.方案1:实现lterator接口
data class Book(val name: String)
class Bookcase(val books: List<Book>): Iterator<Book> {
private val iterator: Iterator<Book>
init {
this.iterator = books.iterator()

Page 579
}
override fun hasNext() = this.iterator.hasNext()
override fun next() = this.iterator.next()
}
fun main(args: Array<String>) {
val bookcase = Bookcase(
listOf(Book("Dive into Kotlin"), Book("Thinking in Java"))
}
）
while(bookcase.hasNext()) {
println("The book name is ${bookcase.next().name}")
}
}
//运行结果
The book name is Dive into Kotlin
The book name is Thinking in Java
由于Bookcase对象拥有与List<Book>实例相同的迭代器,我们就
可以直接调用后者迭代器所有的方法。一种更简洁的遍历打印方式如
下：
for (book in bookcase) {
println("The book name is ${book.name}")

Page 580
2.方案2:重载iterator方法
我们说过，Kotlin还有更好的解决方案。Kotlin有一个非常强大的
语言特性，那就是利用operator关键字内置了很多运算符重载功能。
我们就可以通过重载Bookcase类的iterator方法,实现一种语法上更
加精简的版本：
data class Book(val name: String)
class Bookcase(val books: List<Book>) {
operator fun iterator(): Iterator<Book> = this.books.iterator()
}
很棒吧?我们用一行代码就实现了以上所有的效果。还没完，由
于Kotlin还支持扩展函数，这意味着我们可以给所有的对象都内置一
个迭代器。
3。方案3：通过扩展函数
假设现在的Book是引入的一个类，你并不能修改它的源码，下
面我们就演示如何用扩展的语法来给Bookcase类对象增加迭代的功
能：
data class Book(val name: String)
class Bookcase(val books: List<Book>) {}
operator fun Bookcase.iterator(): Iterator<Book> = books.iterator()

Page 581
代码依旧非常简洁，假如你想对迭代器的逻辑有更多的控制权，
那么也可以通过object表达式来实现：
operator fun Bookcase.iterator(): Iterator<Book> = object : Iterator<Book> {
val iterator = books.iterator()
}
override fun hasNext() = iterator.hasNext()
override fun next() = iterator.next()
总的来说，迭代器模式并不是一种很常用的设计模式，但通过它
我们可以进一步了解Kotlin中的扩展函数的应用，以及运算符重载功
能的强大之处。

Page 582
9。2。4用偏函数实现责任链模式
如果你拥有一定程度的Java开发经验，想必接触过责任链模式。
假设我们遇到这样的业务需求场景：希望使得多个对象都有机会处理
某种类型的请求。那么可能就需要考虑是否可以采用责任链模式。
典型的例子就是Servlet中的Filter和FilterChain接口,它们就采用
了责任链模式。利用责任链模式我们可以在接收到一个Web请求时，
先进行各种filter逻辑的操作,filter都处理完之后才执行servlet。在这
个例子中，不同的filter代表了不同的职责，最终它们形成了一个责任
链。
简单来说，责任链模式的目的就是避免请求的发送者和接收者之
间的耦合关系，将这个对象连成一条链，并沿着这条链传递该请求，
直到有一个对象处理它为止。
现在我们来举一个更加具体的例子。计算机学院的学生会管理了
一个学生会基金，用于各种活动和组织人员工作的开支。当要发生一
笔支出时，如果金额在100元之内，可由各个分部长审批；如果金额
超过了100元，那么就需要会长同意；但假使金额较大，达到了500
元以上，那么就需要学院的辅导员陈老师批准。此外，学院里还有一
个不宣的规定，经费的上限为1000元，如果超出则默认打回申请。
当然我们可以用最简单的if-else来实现经费审批的需求。然而根
据开闭原则，我们需要将其中的逻辑进行解耦。下面我们就用面向对
象的思路结合责任链模式，来设计一个程序。

Page 583
data class ApplyEvent(val money: Int, val title: String)
interface ApplyHandler {
val successor: ApplyHandler?
fun handleEvent(event: ApplyEvent)
}
class GroupLeader(override val successor: ApplyHandler?): ApplyHandler {
override fun handleEvent(event: ApplyEvent) {
when {
}
}
}
event.money <= 100 -> println("Group Leader handled application: ${
else -> when(successor) {
}
class President(override val successor: ApplyHandler?): ApplyHandler {
override fun handleEvent(event: ApplyEvent) {
}
}
is ApplyHandler -> successor.handleEvent(event)
else ->println("Group Leader: This application cannot be handdle.")
when {
event.money <= 500 ->println("President handled application: ${event.ti
else -> when(successor) {
is ApplyHandler -> successor.handleEvent(event)
else -> println("President: This application cannot be handdle.")

Page 584
}
}
class College(override val successor: ApplyHandler?): ApplyHandler {
override fun handleEvent(event: ApplyEvent) {
when {
}
}
}
event.money > 1000 -> println("College: This application is refused.")
else -> println("College handled application: ${event.title}.")
在这个例子中,我们声明了GroupLeader、President、College三
个类来代表学生会部长、分部长、会长及学院，它们都实现了
ApplyHandler接口。接口包含了一个可空的后继者对象successor,以
及对申请事件的处理方法handleEvent。
当我们把一个申请经费的事件传递给GroupLeader对象进行处理
时，它会根据具体的经费金额来判断是否将申请转交给successor对
象，也就是President类来处理。以此类推，最终形成了一个责任链的
机制。
fun main(args: Array<String>) {
val college = College(null)
val president = President(college)

Page 585
}
val groupLeader = GroupLeader(president)
groupLeader.handleEvent(ApplyEvent(10,
"buy a pen"))
"team building"))
groupLeader.handleEvent(ApplyEvent(200,
groupLeader.handleEvent(ApplyEvent(600,
"hold a debate match"))
groupLeader.handleEvent(ApplyEvent(1200, "annual meeting of the colleg
运行结果：
Group Leader handled application: buy a pen.
President handled application: team building.
College handled application: hold a debate match.
College: This application is refused.
现在我们再来重新思考下责任链的机理，你会发现整个链条的每
个处理环节都有对其输入参数的校验标准，在上述例子中主要是对申
请经费事件的金额有要求。当输入参数处于某个责任链环节的有效接
收范围之内，该环节才能对其做出正常的处理操作。在编程语言中，
我们有一个专门的术语来描述这种情况，这就是“偏函数”。
1.实现偏函数类型:PartialFunction
我们来看看什么是偏函数?
偏函数

Page 586
偏函数是个数学中的概念，指的是定义域X中可能存在某些值在值域
Y中没有对应的值。
为了方便理解，我们可以把偏函数与普通函数进行比较。在一个
普通函数中，我们可以给指定类型的参数传入任意该类型的值，比如
（Int）->Unit，可以接收任何Int值。而在一个偏函数中，指定类型的
参数并不接收任意该类型的值，比如：
fun mustGreaterThan5(x: Int): Boolean {
if（x>5）{
return true
} else throw Exception("x must be greator than 5")
}

>>> mustGreaterThan5(6)
>>> true
>>> mustGreaterThan5(1)
>>> java.lang.Exception: x must be greator than 5
>>> at Line57.mustGreaterThan5(Unknown Source) // 必须传入大于5的值
>>> 之所以提到偏函数是因为在一些函数式编程语言中，如Scala，
>>> 有一种PartialFunction类型，我们可以用它来简化责任链模式的实
>>> 现。由于Kotlin的语言特性足够灵活强大，虽然它的标准库并没有支
>>> 持PartialFunction,然而一些开源库(如funKTionale)已经实现了这
>>> 个功能。我们来看看如何定义PartialFunction类型:

Page 587
class PartialFunction<in P1, out R>(private val definetAt: (P1) -> Boolean, pri
override fun invoke(p1: P1): R {
if(definetAt(p1)) {
return f(p1)
}else {
throw IllegalArgumentException("Value: ($p1) isn't supported by this fi
}
}
fun isDefinedAt(p1: P1) = definetAt(p1)
}
现在来分析下PartialFunction类的具体作用:
·声明类对象时需接收两个构造参数，其中definetAt为校验函数，f为
处理函数；
·当PartialFunction类对象执行invoke方法时,definetAt会对输出参数
p1进行有效性校验；
·如果校验结果通过，则执行f函数，同时将p1作为参数传递给它；反
之则抛出异常。
想必你已经发现,PartialFunction类可以解决责任链模式中各个
环节对于输入的校验及处理逻辑的问题，但是依旧有一个问题需要解
决，就是如何将请求在整个链条中进行传递。

Page 588
接下来我们再利用Kotlin的扩展函数给PartialFunction类增加一个
orElse方法。在此之前,我们先注意下这个类中的isDefinedAt方法,
它其实并没有什么特殊之处，仅仅只是作为拷贝definetAt的一个内部
方法，为了在orElse方法中能够被调用。
infix fun <P1, R> PartialFunction<P1, R>.orElse(that: PartialFunction<P1, R>
return PartialFunction({ this.isDefinedAt(it) || that.isDefinedAt(it) }) {
when {
}
}
}
this.isDefinedAt(it) -> this(it)
else -> that(it)
可以看出,在orElse方法中可以传入另一个PartialFunction类对象
that，它也就是责任链模式中的后继者。当isDefinedAt方法执行结果
为false的时候，那么就调用that对象来继续处理申请。
这里用infix关键字来让orElse成为一个中缀函数，从而让链式调
用的语法变得更加直观。
2。用orElse构建责任链
接下来我们就用设计好的PartialFunction类及扩展的orElse方法,
来重新实现一下最开始的例子。首先来看看如何用PartialFunction定

Page 589
义groupLeader对象:
data class ApplyEvent(val money: Int, val title: String)
val groupLeader = {
val definetAt: (ApplyEvent) -> Boolean = { it.money <= 200 }
val handler: (ApplyEvent) -> Unit = { println("Group Leader handled applica
Partial Function(definetAt, handler)
}（）
这里我们借助了自运行Lambda的语法来构建一个PartialFunction
的对象groupLeader。definetAt用于校验申请的经费金额是否在学生
会部长可审批的范围之内，handler函数用来处理通过金额校验后的
审批操作。
同理,我们用类似的方法再定义剩下的president和college对象:
val president = {
val definetAt: (ApplyEvent) -> Boolean = { it.money <= 500 }
val handler: (ApplyEvent) -> Unit = { println("President handled application:
Partial Function(definetAt, handler)
}（
val college = {
val definetAt: (ApplyEvent) -> Boolean = { true }
val handler: (ApplyEvent) -> Unit = {

Page 590
}（
}
when {
it.money > 1000 -> println("College: This application is refused.")
else -> println("College handled application: ${it.title}.")
}
PartialFunction(definetAt, handler)
最后，我们再用orElse来构建一个基于责任链模式和
PartialFunction类型的中缀表达式applyChain:
val applyChain = groupLeader orElse president orElse college
然后我们再运行一个测试用例：

>>> applyChain(ApplyEvent(600, "hold a debate match"))
>>> College handled application: hold a debate match.
>>> 借助PartialFunction类的封装，我们不仅大幅度减少了程序的代
>>> 码量，而且在构建责任链时，可以用orElse获得更好的语法表达。

Page 591
9。2。5ADT实现状态模式
我们在第4章中介绍了什么是ADT（代数数据类型），以及如何
用它结合模式匹配来抽象业务。ADT是函数式语言中一种强大的语言
特性，这一节我们会继续介绍如何用它来实现状态模式。
状态模式与策略模式存在某些相似性，它们都可以实现某种算
法、业务逻辑的切换。以下是状态模式的定义：
状态模式允许一个对象在其内部状态改变时改变它的行为，对象看起
来似乎修改了它的类。
状态模式具体表现在：
·状态决定行为，对象的行为由它内部的状态决定。
·对象的状态在运行期被改变时，它的行为也会因此而改变。从表面
上看，同一个对象，在不同的运行时刻，行为是不一样的，就像是类
被修改了一样。
再次与策略模式做比较，你也会发现两种模式之间的不同：策略
模式通过在客户端切换不同的策略实现来改变算法；而在状态模式
中，对象通过修改內部的状态来切换不同的行为方法。
在我们就来看个饮水机的例子，假设一个饮水机有3种工作状
态，分别为未启动、制冷模式、制热模式。如果你已经了解了第4章
的内容，应该会很自然地联想到，可以用密封类来封装一个代表不同
饮水机状态的ADT。

Page 592
sealed class Water MachineState(open val machine: WaterMachine) {
fun turnHeating() {
if (this !is Heating) {
} else {
println("The state is already heating mode.")
}
println("turn heating")
machine.state = machine.heating
}
fun turnCooling() {
if (this !is Cooling) {
}
} else {
println("The state is already cooling mode.")
println("turn cooling")
machine.state = machine.cooling
}
fun turnOff() {
if (this !is Off) {
}
println("turn off")
machine.state = machine.off
} else {
println("The state is already off.")

Page 593
}
}
class Off(override val machine: WaterMachine): WaterMachineState(machine
class Heating(override val machine: WaterMachine): WaterMachineState(mar
class Cooling(override val machine: WaterMachine): WaterMachineState(mac
来分析下这段代码：

1) WaterMachineState是一个密封类,拥有一个构造参数为
   WaterMachine类对象，我们等下再来定义它；
    2)在WaterMachineState类外部我们分别定义了Off、Heating、
   Cooling来代表饮水机的3种不同的工作状态，它们都继承了
    WaterMachineState类的machine成员属性及3个状态切换的方法;
   3）在每个切换状态的方法中，我们通过改变machine对象的
   state，来实现切换饮水机状态的目的。
    接下来我们再来设计下WaterMachine类:
    class WaterMachine {
    var state: Water Machine State
    val off = Off(this)
    val heating = Heating(this)
    val cooling = Cooling(this)

Page 594
}
init {
this.state = off
}
fun turnHeating() {
this.state.turnHeating()
}
fun turnCooling() {
}
this.state.turnCooling()
}
fun turnOff() {
this.state.turnOff()
WaterMachine类非常简单，它的內部主要包含了以下成员属性
和方法：
·引用可变的WaterMachineState类对象state,用来表示当前饮水机所
处的工作状态；
分别表示3种不同状态的成员属性,off、heating、cooling,它们也是
WaterMachineState类的3种子类对象;它们通过传入this进行构造,
从而实现在WaterMachineState状态类内部,改变WaterMachine类的
state引用值;当WaterMachine类对象初始化时,state默认为off,即
饮水机处于未启动状态；

Page 595
·3个直接调用的饮水机操作方法，分别执行对应state对象的3种操作，
供客户端调用。
夏天到了，办公室的小伙伴都喜欢喝冷水，早上一来就会把饮水
机调整为制冷模式，但Shaw有吃泡面的习惯，他想泡面的时候，就
会把饮水机变为制热，所以每次他吃了泡面，下一个喝水的同事就需
要再切换回制冷。最后要下班了，Kim就会关闭饮水机的电源。
为了满足以上的需求，我们就可以利用WaterMachine类设计一
个waterMachineOps函数:
enum class Moment {
EARLY_MORNING, // 早上上班
DRINKING_WATER, // 日常饮水
INSTANCE_NOODLES, // Shaw 吃泡面
AFTER_WORK // 下班
}
fun waterMachineOps(machine: WaterMachine, moment: Moment) {
when(moment) {
Moment.EARLY_MORNING,
Moment.DRINKING_WATER -> when(machine.state) {
!is Cooling -> machine.turnCooling()
}
Moment.INSTANCE_NOODLES -> when(machine.state) {
!is Heating -> machine.turnHeating()

Page 596
}
}
}
}
Moment.AFTER_WORK -> when(machine.state) {
!is Off -> machine.turnOff()
}
else -> Unit
这个方法很好地处理了不同角色在不同需求场景下，应该对饮水
机执行的不同操作。此外，正如我们之前在了解密封类和when表达
式时所知晓的细节，当用when表达式与处理枚举类时，默认的情况
必须用else进行处理。然而，由于密封类在类型安全上的额外设计，
我们在处理machine对象的state对象时，则不需要考虑这一细节，在
语言表达上要简洁得多。
最后,我们来测试下以上的waterMachineOps方法:
fun main(args: Array<String>){
val machine = WaterMachine()
waterMachineOps(machine, Moment.DRINKING_WATER)
waterMachineOps(machine, Moment.INSTANCE_NOODLES)
waterMachineOps(machine, Moment.DRINKING_WATER)
waterMachineOps(machine, Moment.AFTER_WORK)

Page 597
执行结果如下：
turn cooling
turn heating
turn cooling
turn off

Page 598
9。3结构型模式
最后一种设计模式的大类是结构型模式，在对象被创建之后，对
象的组成及对象之间的依赖关系就成了我们关注的焦点，这与程序的
可维护性息息相关。在这一节中，我们会重点介绍装饰者模式，与
Java中传统的设计方法不同，Kotlin依靠类委托和扩展的语言特性，
给开发者提供了更多的选择。

Page 599
9。3。1装饰者模式：用类委托减少样板代码
在Java中，当我们要给一个类扩展行为的时候，通常有两种选择：
·设计一个继承它的子类；
·使用装饰者模式对该类进行装饰，然后对功能进行扩展。
目前为止，我们已经清楚地明白，不是所有场合都适合采用继承
的方式来满足类扩展的需求（第3章讨论过“里氏替换原则”），所以
很多时候装饰者模式成了我们解决此类问题更好的思路。
装饰者模式
在不必改变原类文件和使用继承的情况下，动态地扩展一个对象的功
能。该模式通过创建一个包装对象，来包裹真实的对象。
总结来说，装饰者模式做的是以下几件事情：
·创建一个装饰类，包含一个需要被装饰类的实例；
·装饰类重写所有被装饰类的方法；
·在装饰类中对需要增強的功能进行扩展。
可以发现，装饰者模式很大的优势在于符合“组合优于继承”的
设计原则，规避了某些场景下继承所带来的问题。然而，它有时候也
会显得比较啰唆，因为要重写所有的装饰对象方法，所以可能存在大
量的样板代码。

Page 600
在Kotlin中，我们可以让装饰者模式的实现变得更加优雅。猜想
你已经想到了它的类委托特性，我们可以利用by关键字，将装饰类的
所有方法委托给一个被装饰的类对象，然后只需覆写需要装饰的方法
即可。
下面我们来实现一个具体的例子：
interface MacBook {
fun getCost(): Int
fun getDesc(): String
fun getProdDate(): String
class MacBookPro: MacBook {
override fun getCost() = 10000
override fun getDesc() = "Macbook Pro"
override fun getProdDate() = "Late 2011"
}
//装饰类
class Processor Upgrade Macbook Pro(val macbook: MacBook): MacBook by
override fun getCost() = macbook.getCost() + 219
override fun getDesc() = macbook.getDesc() + ", +1G Memory"
}
如代码所示，我们创建一个代表MacBookPro的类，它实现了

Page 601
MacBook的接口的3个方法，分别表示它的预算、机型信息，以及生
产的年份。当你觉得原装MacBook的内存配置不够的时候，希望再加
入一条1G的内存，这时候配置信息和预算方法都会受到影响。
所以通过Kotlin的类委托语法，我们实现了一个
ProcessorUpgradeMacbookPro类,该类会把MacBook接口所有的方
法都委托给构造参数对象macbook。因此，我们只需通过覆写的语法
来重写需要变更的cost和getDesc方法。由于生产年份是不会改变
的,所以不需重写,ProcessorUpgradeMacbookPro类会自动调用装
饰对象的getProdDate方法。
运行一下测试用例：
fun main(args: Array<String>) {
val macBookPro = MacBookPro()
val processorUpgradeMacbook Pro = ProcessorUpgradeMacbook Pro(mac
println(processorUpgradeMacbookPro.getCost())
println(processorUpgradeMacbookPro.getDesc())
}
//运行结果
10219
Macbook Pro, +1G Memory
总的来说，Kotlin通过类委托的方式减少了装饰者模式中的样板
代码，否则在不继承Macbook类的前提下，我们得创建一个装饰类和

Page 602
被装饰类的公共父抽象类。接下来，我们再来看看Kotlin中另一种代
替装饰类的实现思路。

Page 603
9。3。2通过扩展代替装饰者
我们已经在第7章了解到“扩展”这种Kotlin中强大的语言特性，
它很灵活的应用就是实现特设多态。特设多态可以针对不同的版本实
现完全不同的行为，这与装饰者模式不谋而合，因为后者也是给一个
特定对象添加额外行为。
在上一节中，我们已经了解了如何用类委托的语法来简化装饰者
模式。实际上，在某些场景中，我们可以利用Kotlin的扩展语法来代
替装饰类实现类似的目的。下面就来看一个具体的例子：
class Printer {
}
fun drawLine() {
println("-
}
fun drawDottedLine() {
println（"-----"）
}
fun drawStars() {
println（"********"）
}
这一次，我们定义了一个Printer绘图类，它有3个画图方法，分

Page 604
别可以绘制实线、虚线及星号线。接下来，我们新增了一个需求，就
是希望在每次绘图开始和结束后有一段文字说明，来标记整个绘制的
过程。
一种思路是对每个绘图的方法装饰新增的功能，然而这肯定显得
冗余，尤其是未来Printer类可能新增其他的绘图方法，这不是一种优
雅的设计思路。
现在我们来看看用扩展来代替装饰类，提供更好的解决方案：
fun Printer.startDraw(decorated: Printer.() -> Unit) {
println("+++ start drawing +++")
this.decorated()
println("+++ end drawing +++")
}
你肯定对扩展方法的语法再熟悉不过了，上述代码中我们给
Printer类扩展了一个startDraw方法,它包含一个可执行的Printer类方
法decorated,当我们调用startDraw时,会在decorated方法执行的前
后，分别打印一段表明“绘图开始”和“绘图结束”的文字说明。
那么我们再来看看如何使用这个startDraw方法：
fun main(args: Array<String>) {
Printer().run {

Page 605
}
}
startDraw {
drawLine()
}
startDraw {
drawDottedLine()
}
startDraw {
}
drawStars()
还记得前面介绍的run方法吗?它接收一个lambda函数为参数，
以闭包形式返回，返回值为最后一行的值或者指定的return的表达
式。结合run的语法，我们就可以比较优雅地实现我们的需求。
以上测试结果如下：
+++ start drawing +++
+++ end drawing +++
+++ start drawing +++
+++ end drawing +++

Page 606
+++ start drawing +++

********

+++ end drawing +++

Page 607
9。4本章小结
（1）改造工厂模式
Kotlin的object是天生的单例，同时通过伴生对象的语法来创建更
加简洁的工厂模式，以及静态工厂方法。此外，由于伴生对象也支持
扩展，这使得Kotlin中改造后的工厂模式比Java中的更加灵活强大。
（2）内联函数简化抽象工厂
内联函数的一大奇特之处在于可以获取具体的参数类型，这一特
性在实现抽象工厂的场景中大放光彩，我们终于可以用类似创建一个
泛型类对象的方式，来构建一个抽象工厂具体对象。
（3）弱化构建者模式的使用
构建者模式的本质在于模拟了具名的可选参数，就像Ada和
Python中的一样。幸运的是，Kotlin也是这样一门拥有具名可选参数
的编程语言。因此，在用Kotlin设计程序时，我们很少会使用构建者
模式，而是直接利用类的原生特性来规避构造参数过长的问题。同时，
我们还可以利用类原生的require方法对参数的值进行约束。
（4）用委托属性实现观察者模式

Page 608
Kotlin的标准库中直接支持了observable这一委托属性,这使其在
实现观察者模式的时候相比Java要更加容易和方便。
（5）高阶函数简化设计模式
由于Kotlin支持高阶函数的语法，这给它在实现策略模式及模板
方法模式时带来了便利。在策略模式中，我们可以用高阶函数来抽象
算法，在模板方法模式中，可以直接利用高阶函数的特性来代替继承
实现类似的效果。
(6)重载iterator方法
Kotlin支持运算符重载功能，我们可以利用operator关键词来重载
iterator方法,这个巧妙的特性可以替代传统Java中依赖Iterator接口的
设计。同时，结合扩展函数的语法，我们可以实现更简洁、更加强大
的迭代器模式。
（7）偏函数实现责任链模式
Kotlin的语法使其能够构建一套基于偏函数的责任链模式语法，
通过中缀表达式的形式，结合orElse方法，我们可以在调用责任链的
时候更加直观优雅。
（8）ADT实现状态模式
我们曾用了一章的篇幅来介绍什么是ADT（代数数据类型），以
及如何用它结合模式匹配来抽象业务。ADT是函数式语言中一种强大
的语言特性，利用它实现状态模式是一个很好的优势体现。

Page 609
（9）装饰者模式实现新思路
相比Java，Kotlin在实现装饰者模式上有更多的选择。依靠类委
托的语法，我们可以避免大量的样板代码。此外某些场景下，通过扩
展来代替装饰类是更好的选择。

Page 610
第10章函数式编程
迄今为止，你已经领略了Kotlin新增的函数式语言特性，以及如
何改变熟悉的Java开发工作。在前一章中，我们展示了怎样利用
Kotlin的新特性，去尝试改良传统经典的设计模式，也讨论了不一样
的模式设计思路，给程序开发提供一种新的选择。
本章我们会深入“函数式编程”这个话题本身。在第1章中，我
们介绍了Kotlin是一门集成面向对象与函数式的多范式语言，但它并
没有像Scala那样彻底拥抱函数式编程。相对地，Kotlin仅是克制地采
纳了部分基础的函数式语言特性，如高阶函数､（部分）模式匹配的
能力等。究其原因，是因为高度函数式化的编程方式是一种截然不同
的思维，这与Kotlin的设计哲学相悖，因为它的定位是成为一门“更
好的Java语言”。
另一方面，本书的第3部分的定位是“Kotlin探索”。探索则意味
着我们可以打破边界，去思考Kotlin语言特性的能力上限。尽管Kotlin
并没有直接支持函数式语言的某些高级特性，如Typeclass、高阶类
型，但它的扩展却是一种非常强大的语言特性，利用它我们同样可以

Page 611
实现函数式编程中一些高级的数据结构和结构转换功能。
在本章接下来的内容中，我们将深入探索什么是函数式编程，以
及函数式编程的优势。需要注意的是，如果你之前完全没有函数式编
程的相关经验，在阅读本章内容的时候可能会显得吃力，建议结合其
他函数式相关的书籍进行阅读,比如《Learn You a Haskell for Great
Good!》。

Page 612
10。1函数式编程的特征
在开始之前，我们先来看看函数式编程的概念。定义“函数式编
程”不是一件容易的事情，因为业界对于所谓的“函数式编程”有着
不同的标准。如果你细心观察，肯定会发现函数式编程已经变得越来
越流行，这里所指的语言并不是古老的Haskell、ML或Lisp，它们是
函数式语言的鼻祖，而是更加现代化的编程语言如Scala、Clojure、
JavaScript（包括我们正在讨论的Kotlin），这些语言都在某种程度上
宣称过自己是一门函数式的编程语言。那么，到底什么才是函数式语
言呢?

Page 613
10。1。1函数式语言之争
其实，我们可以从狭义和广义两个方面去解读所谓的函数式语
言。所谓狭义的函数式语言，有着非常简单且严格的语言标准，即只
通过纯函数进行编程，不允许有副作用。这是以Haskell为代表的纯
函数式语言所理解的函数式编程，你会发现在狭义的函数式语言中进
行编程，纯函数就像是数学中函数一样，给它同样的输入，会有相同
的输出，因此程序也非常适合推理，我们会稍后介绍函数式编程中这
一非常棒的特性。
然而，纯函数式的编程语言也有着一些明显的劣势，典型的就是
绝对的无副作用，以及所有的数据结构都是不可变的。这使得它在设
计一些如今我们认为非常简单的程序的时候，也变得十分麻烦，如实
现一个随机数函数。因此，站在纯函数式语言肩膀上发展过来的更现
代化的编程语言，如Scala和Kotlin，都允许了可变数据的存在，我们
仍然可以在程序代码中拥有“状态”。此外，它们也都继承了Java中
面向对象的特性。因此，在纯函数式语言的信徒看来，Scala、Kotlin
这些语言并不能称为真正意义上的函数式语言。
同时，也有很多人对此并不赞同。在他们看来，所谓函数式编程
语言，不应该只是严格的刻板标准，它应该根据需求的变化而发展。
Scala的作者马丁就针对“函数式语言之争”的话题，发表过一篇文
章来阐明类似的观点。在他看来，Scala这种拥有更多语言特性选择
的编程语言，是一种“后函数式”的编程语言，即它在几乎拥有所有
函数式编程语言特性的同时，又符合了编程语言发展的趋势。从广义

Page 614
上看，任何“以函数为中心进行编程”的语言都可称为函数式编程。
在这些编程语言中，我们可以在任何位置定义函数，同时也可以将函
数作为值进行传递。
因此，广义的函数式编程语言并不需要强调函数是否都是“纯”
的，我们来列举一些最常见的函数式语言特性：
·函数是头等公民；
·方便的闭包语法；
·递归式构造列表(list comprehension);
·柯里化的函数；
·惰性求值；
·模式匹配；
·尾递归优化。
如果是支持静态类型的函数式语言，那么它们还可能支持：
·强大的泛型能力，包括高阶类型；
·Typeclass;
·类型推导。
Kotlin支持以上具有代表性的函数式语言特性列表中的绝大多

Page 615
数，因此它可以被称为广义上的函数式语言。在用Kotlin编程时，我
们经常可以利用函数式的特性来设计程序。
读到这，相信你已经不会再纠结“到底什么才是函数式编程”这
个问题本身，本章介绍的函数式编程也并不是唯一精准的定义。由于
如今现代化编程语言中的函数式思想，几乎都可以追溯到纯函数式的
编程语言，如Haskell，因此本章接下来所探讨的函数式编程，主要
是围绕狭义上的函数式语言的思想进行讨论，即仅通过纯函数来设计
程序。

Page 616
10。1。2纯函数与引用透明性
在第2章我们已经介绍过什么是“副作用”。结合实际生活场景
进行理解，我们在药品的说明书上可能会看到标明“副作用”的字
眼，意为该药品除了发挥主要的药效以外，还会产生额外的不良反应。
编程中的副作用也是类似的道理，一个带有副作用的函数的不良反应
会让程序变得危险，也可能让代码变得难以测试。在了解“纯函数”
之前，我们先来看一个带有副作用的程序设计。
sealed class Format
data class Print(val text: String): Format()
object Newline: Format()
val string = listOf<Format>(Print("Hello"), Newline, Print("Kotlin"))
fun unsafeInterpreter(str: List<Format>) {
str.forEach {
}
when(it) {
is Print -> print(it.text)
is Newline -> println()
}
}
我们创建一个名为unsafeInterpreter函数来将一个Format类对象
的列表格式化为普通的字符串。虽然是很简单的功能，但如果我们仔

Page 617
细思考，这个函数会由于引入了副作用而导致一些问题：
1）缺乏可测试性。开发中我们经常需要写单元测试，当我们希
望对unsafeInterpreter函数的代码逻辑进行测试时,可能你会说:没
什么问题呀，虽然并没有采用类似assert断言，但打印结果不是很好
地反映了格式转化的正确性吗?再换个角度思考，如果改天我们写了
另一个类似的方法，內部的副作用不是print，而是写入数据库的方法，
那么这是否会让我们的测试工作变得异常烦琐?
2)难以被组合复用。因为unsafeInterpreter函数内部混杂了副作
用及字符串格式转化的逻辑，当我们想对转化后的结果进行复用时，
就会产生很大问题。试想下，如果这里不是打印操作，而是一个持久
化到数据库中的操作，显然它就不能被当作转化字符串的功能方法来
使用。
接下来，我们看看如何利用纯函数来解决这些问题。
1。纯函数消除副作用
所谓“纯函数”，首先它典型的特征就是没有副作用。在解释纯
函数之前，我们先来写一个上述例子的纯函数版本：
fun stringInterpreter(str: List<Format>) = str.fold("") { fullText, s->
when(s) {
is Print -> fullText + s.text
is Newline -> fullText + "\n"

Page 618
}
}
这里我们使用fold实现了一个stringInterpreter函数,它会返回格
式化结果的字符串值（如果你还不熟悉fold方法的使用，可以阅读6。2
节）。可以看出，在消除了副作用了之后，不管是在测试性还是代码
的可复用性上都得到了很好的提升。
stringInterpreter是一个典型的纯函数,我们会发现,只要传递给
它的参数一致，每次我们都可以获得相同的返回结果值。下面我们来
探究下关于纯函数更具体的定义。
2。基本法则：具有引用透明性
我们说过，编程中的纯函数十分接近于数学中的函数，因此它的
评判标准也是来源于数学中的一个基本原则，那就是需要具备引用透
明性。
关于引用透明性，我们不打算深究它在数学中的精确定义，你可
以把这一原则简单地理解为：一个表达式在程序中可以被它等价的值
替换，而不影响结果。当谈论一个具体的函数时，如果它具备引用透
明性，只要它的输入相同，对应的计算结果也会相同。
这里的“计算结果”非常耐人寻味，它到底指的是什么?在上述
例子中，我们发现纯函数每次返回的结果值都是相同的。然而，在
unsafeInterpreter函数中,它的返回结果值都是Unit,我们也可以看成

Page 619
相同的结果值，但它是有副作用的，因此，“计算结果”不仅针对返
回结果值。假使一个函数具备引用透明性，那么它内部的行为不会改
变外部的状态。如unsafeInterpreter中的print操作,每次执行都会在
控制台打印信息，所以具有副作用行为的函数也违背了引用透明性原
则。
当我们尽量遵循引用透明性原则去编写程序的时候，我们就具备
了函数式编程的基础。正如本书中好几处所探讨的观点，避免副作用
可以让程序代码变得更加安全可靠，利于测试，同时也易于组合。这
些特点构成了函数式编程的一个非常大的优点，就是近似于数学中的
等式推理。
3。纯函数与局部可变性
现在我们已经非常清楚的一点是，函数式编程倡导我们使用纯函
数来编程，促进这一过程的一大语言特性就是不可变性。关于不可变
性，我们在第2章中就做过详细的介绍，它能够有效帮我们尽可能地
避免副作用的发生。
这时候，另一个有趣的话题出现了———纯函数，或者说引用透
明性是否就意味着我们不能使用任何可变的变量呢?更具体地说，我
们就必须在函数式编程中放弃用var来声明变量吗?
举个非常简单的例子：
fun foo(x: Int): Int {

Page 620
}
vary=0；
y=y+x；
return y;
这个例子中，即使我们在foo函数内部定义了可变的变量y，当我
们传入相同的x参数值时，计算结果依旧相同，所以它完全可以说是
引用透明性的，也是一个纯函数。
因此，当我们谈论引用透明性的时候，需要结合上下文来解读。
foo函数具备局部可变性，但当它被外部执行调用的时候，函数整体
会被看成一个黑盒，程序依旧符合引用透明性。
关于副作用
当我们讨论副作用时，需要将话题限定在一定的抽象层次，因为没有
绝对的“无副作用”。即使是纯函数，也会使用内存，占用CPU。
正如第2章我们讨论过的推荐使用var的场景，局部可变性有时候
能够让我们的程序设计变得更加自然，性能更好。所以，函数式编程
并不意味着拒绝可变性，相反，合理地结合可变性和不可变性，能够
发挥更好的作用。
纯函数的局限性
虽然纯函数绝大多数场景都利于我们的程序设计，但也有其不胜任的
时候。试想下常见的随机数函数（random），它们每一次调用都没有
参数，但每次输出的随机数都是不同的。可以看出，随机数函数并不

Page 621
是“纯函数”。

Page 622
10。1。3代换模型与惰性求值
我们来看一段符合引用透明性的代码：
fun f1(x: Int, y: Int) = x
fun f2(x: Int): Int = f2(x)

>>>f1（1，f2（2））
>>>你看了可能相当气愤，因为这是一段自杀式的代码，如果我们执
>>>行了它，那么f2必然被不断调用，从而导致evaltobottom，产生死循
>>>环。
>>>一个尴尬的事实是，纯函数所谓“相同的计算结果”还可以是死
>>>循环。
>>>这时候，一个会Haskell的程序员路过，花了10秒将其翻译成以
>>>下的版本：
>>>f1：：Int->Int->Int
>>>f1xy=x+y
>>>f2：：Int->Int
>>>f2x=x
>>>奇怪的是，用Haskell写的这个版本竟然成功返回了结果1。这到

Page 623
底是怎么回事呢?
1。应用序与正则序
也许你至今未曾思考过这个问题：编程语言中的表达式求值策略
是怎样的?其实，编程语言中存在两种不同的代换模型：应用序和正
则序。大部分我们熟悉的语言如Kotlin、C、Java是“应用序”语
言，当要执行一个过程时，就会对过程参数进行求值，这也是上述
Kotlin代码导致死循环的原因：当我们调用f1（1，f2（2））的时候，
程序会先对f2（2）进行求值，从而不断地调用f2函数。
然而，Haskell采用了不一样的逻辑，它会延迟对过程参数的求
值，直到确实需要用到它的时候，才进行计算，这就是所谓的“正则
序”，是一个惰性求值的过程。当我们调用f1（1（f2（2））后，由于
f1的过程中压根不需要用到y，所以它就不会对f2（2）进行求值，直
接返回x值，也就是1。
2。惰性求值
Haskell是默认采用惰性求值的语言，在Kotlin和其他一些语言中
（如Scala和Swift），我们也可以利用lazy关键字来声明惰性的变量和
函数。惰性求值可以带来很多优势，如“无限长的列表结构”。当然，
它也会制造一些麻烦，比如它会让程序求值模型变得更加复杂，滥用
惰性求值也会导致效率下降。
这里我们主要探究惰性求值是如何实现的。在Haskell中，惰性
求值主要是靠Thunk这种机制来实现的。

Page 624
为了更好地理解它，我们来模拟实现Thunk的过程。要理解
Thunk其实很容易，比如针对println函数，它是一个非纯函数，我们
就可以如此改造，让它变得“lazy"：
fun lazyPrintln(msg: String) = { println(msg)}
如此,当我们的程序调用lazyPrintln("I am a IO operation.")的
时候，它仅仅只是返回一个可以进行println的函数，它是惰性的，也
是可替代的。这样，我们就可以在程序中将这些IO操作进行组合，最
后再执行它们。我们会在10。3节中利用类似的思路来组合业务中的副
作用。

Page 625
10.2 实现Typeclass
通过10。1节的介绍我们发现，函数式是一种更加抽象的编程思维
方式，它所做的事情就是高度抽象业务对象，然后对其进行组合。
谈及抽象，你在Java中会经常接触到一阶的参数多态，这也是我
们所熟悉的泛型。利用泛型多态，在很大程度上可以减少大量相同的
代码。然而，当我们需要更高阶的抽象的时候，泛型也避免不了代码
冗余。如你所知，标准库中的List、Set等都实现了Iterable接口，它
们都有相同的方法，如filter、remove。现在我们来尝试通过泛型设计
Iterable:
interface Iterable<T> {
fun filter(p: (T) -> Boolean): Iterable<T>
fun remove(p: (T) -> Boolean): Iterable<T> = filter { x -> !p(x) }
}
当我们用List去实现Ite le时,由于filter、remove方法需要返回
具体的容器类型，你需要重新实现这些方法：

Page 626
interface List<T>: Iterable<T> {
override fun filter(p: (T) -> Boolean): List<T>
override fun remove(p: (T) -> Boolean): List<T> = filter { x -> !p(x) }
}
相同的道理,Set也需要重新实现filter和remove方法:
interface Set<T>: Iterable<T> {
override fun filter(p: (T) -> Boolean): Set<T>
override fun remove(p: (T) -> Boolean): Set<T> = filter { x -> !p(x) }
}
如上所示，这种利用一阶参数多态的技术依旧存在代码冗余。现
在我们停下来想一想，假使类型也能像函数一样支持高阶，也就是可
以通过类型来创造新的类型，那么多阶类型就可以上升到更高的抽
象，从而进一步消除冗余的代码，这便是我们接下来要谈论的高阶类
型(higher-order kind)
o

Page 627
10。2。1高阶类型：用类型构造新类型
要理解高阶类型，我们需要先了解什么是“类型构造器（type
constructor）”。谈到构造器，你应该非常熟悉所谓的“值构造器
(value constructor)
99
（x：Int）->x
。
很多情况下，值构造器可以是一个函数，我们可以给一个函数传
递一个值参数，从而构造出一个新的值。如下所示：
如果是类型构造器，就可以传递一个类型变量，然后构造出一个
新的类型。比如List[T]，当我们传入Int时，就可以构造出List[Int]类型。
在上述例子中，值构造函数的返回结果x是具体的值，List[T]传
入类型变量后，也是具体的类型（如List[Int]）。当我们讨论“一阶”
概念的时候，具体的值或信息就是构造的结果。因此，我们可以进一
步做如下推导。
一阶值构造器：通过传入一个具体的值，然后构造出另一个具体的
值。
·一阶类型构造器：通过传入一个具体的类型变量，然而构造出另一
个具体的类型。
在理解了上述的概念之后，高阶函数就更好理解了。它突破了一

Page 628
阶值构造器，可以支持传入一个值构造器，或者返回另一个值构造器。
如：
{x：（Int）->Int->x（1）}
{x：Int->{y：Int->x+y}}
同样的道理，高阶类型可以支持传入构造器变量，或构造出另一
个类型构造器。如在最开始的例子中，假设Kotlin支持高阶类型的语
法，我们可以定义一种类型构造器Container，然后将其作为另一个
类型构造器Interable的类型变量:
interface Iterable<T, Container<X>>
然后，我们再用这种假设的语言特性重新实现List、Set，这时会
惊喜地发现冗余的代码消失了。
interface Iterable<T, Container<X>> {
fun filter(p: (T) -> Boolean): Container<T>
fun remove(p: (T) -> Boolean): Container<T> = filter { x -> !p(x) }
}
interface List<T>: Iterable<T, List>
interface Set<T>: Iterable<T, Set>

Page 629
为了避免误导，这里再次声明，Kotlin当前并不支持以上语法。
但如果Kotlin支持高阶类型，那么就可以写出更加抽象和強大的代
码。

Page 630
66
10.2.2 高阶类型和Typeclass
相信你已经有点感觉到高阶类型的强大之处了，但也可能心生疑
惑：高阶类型固然不错，但是Kotlin并不支持它，那么又有什么意义
呢?
事实上，在Haskell中高阶类型的特性天然催生了这门语言中一
项非常强大的语言特性————Typeclass。在本章接下来的内容中，我
们将利用Kotlin扩展的语法，来代替高阶类型实现这一特性。然而，
在这之前，我们先用Scala这门语言，来实现一个很常见的Typeclass
例子:Functor(函子)。继而理解到底什么是Typeclass。
函子：高阶类型之间的映射。
当你第一次接触到“函子”这个概念的时候，可能会有点怵，因
为函数式编程非常近似数学，更准确地说，函数式编程思想的背后理
论，是一套被叫作范畴论的学科。
关于范畴论
范畴论是抽象地处理数学结构以及结构之间联系的一门数学理论，以
抽象的方法来处理数学概念，将这些概念形式化成一组组“物件”及
态射”。
然而，你千万不要被这些术语吓到。因为本质上它们是非常容易
理解的东西。我们先来看看上面提到的“映射”，你肯定在学习集合
论的时候遇到过它。在编程中，函数其实就可以看成具体类型之间的
映射关系。那么，当我们来理解函子的时候，其实只要将其看成高阶

Page 631
类型的参数类型之间的映射，就很容易理解了。
下面我们来用Scala定义一个高阶类型Functor:
trait Functor[F[]] {
def fmap[A, B](fa: F[A], f: A => B): F[B]
}
现在来分析下Functor的实现：
1)Scala的trait近似于Kotlin中的interface,因为它支持高阶类型,
所以Functor支持传入类型变量F，这也是一个高阶类型。
2）Functor中实现了一个fmap方法，它接收一个类型为F[A]的参
数变量fa，以及一个函数f，通过它我们可以把fa中的元素类型A映射
为B，即fmap方法返回的结果类型为F[B]。
如果你仔细思考，会发现Functor的应用非常广泛。举个例子，
我们希望将一个List[Int]中的元素都转化为字符串。下面我们就来看
看在Scala中,如何让List[T]集成Functor的功能:
implicit val listFunctor = new Functor[List] {
def fmap(fa: List[A])(f: A => B) = fa.map(f)
}

Page 632
10。2。3用扩展方法实现Typeclass
Kotlin不支持高阶类型,像上面例子Functor[F[J]中的FU,在
Kotlin中并没有与之对应的概念。庆幸的是Jeremy Yallop和Leo White
曾经在论文《Lightweight higher-kinded polymorphism》中阐述了一种
模拟高阶类型的方法。我们仍旧以Functor为例，来看看这种方法是
如何模拟出高阶类型的。
interface Kind<out F, out A>
interface Functor<F> {
fun <A, B> Kind<F, A>.map(f: (A) -> B): Kind<F, B>
}
首先，我们定义了类型Kind<outF，outA>来表示类型构造器F应
用类型参数A产生的类型，当然F实际上并不能携带类型参数。
接下来，我们看看这个高阶类型如何应用到具体类型中。为此我
们自定义了List类型，如下：
sealed class List<out A> : Kind<List.K, A> {
object K
}
object Nil : List<Nothing>()
data class Cons<A>(val head: A, val tail: List<A>) : List<A>()

Page 633
List由两个状态构成，一个是Nil代表空的列表，另一个是Cons表
示由head和tail连接而成的列表。
注意到,List实现了Kind<List.K,A>,代入上面Kind的定义,我
们得到List<A>是类型构造器List。K应用类型参数A之后得到的类型。
由此我们就可以用List。K代表List这个高阶类型。
FunctorT, RIRÈS List Functor:
@Suppress("UNCHECKED_CAST", "NOTHING_TO_INLINE")
inline fun <A> Kind<List.K, A>.unwrap(): List<A> =
this as List<A>
object ListFunctor: Functor<List.K> {
override fun <A, B> Kind<List.K, A>.map(f: (A) -> B): Kind<List.K, B> {
return when (this) {
is Cons -> {
val t = this.tail.map(f).unwrap()
Cons<B>(f(this.head), t)
}
}
}
}
else -> Nil

Page 634
如上面例子所示，我们就构造出了List类型的Functor实例。现在
还差最后的关键一步：如何使用这个实例。
众所周知，Kotlin无法将object内部的扩展方法直接导入进来，也
就是说以下的代码是不行的：
import ListFunctor.*
Cons(1, Nil).map{ it + 1}
我们没法直接导入定义在object里的扩展方法直接import，庆幸
的是,Kotlin中的receiver机制可以将object中的成员引入作用域,所
以我们只需要使用run函数，就可以使用这个实例了。
ListFunctor.run {
Cons(1, Nil).map { it + 1 }
}

Page 635
10。2。4Typeclass设计常见功能
现在你已经了解了在Kotlin中如何模拟实现Typeclass,我们来总
结下具体做法：
·利用类型的扩展语法定义通用的Typeclass接口；
·通过object定义具体类型的Typeclass实例;
·在实例run函数的闭包中，目标类型的对象或值随之支持了相应的
Typeclass的功能。
在这一节中，我们将利用这些方法来实现几个常见的功能。
1。Eq
首先，我们来设计一个名为Eq的Typeclass，只要为一种类型定
义一个Eq的Typeclass实例，就可以在实例run函数中对该类型的对象
或值进行判等操作。根据以上总结的实现Typeclass的方法，我们可
以很容易地定义Eq：
interface Eq<F> {
fun F.eq(that: F): Boolean
}
Eq接口非常简单。接下来我们来看看如何应用这个Typeclass。

Page 636
先以最常见的Int类型为例：
object IntEq: Eq<Int> {
override fun Int.eq(that: Int): Boolean {
return this == that
}
}
现在你就可以利用IntEq来对整型的值进行判等了。来测试一
下：
IntEq.run {
vala=1
println(a.eq(1))
println(a.eq(2))
}
//运行结果
true
false
我们再来增加挑战的难度，看看如何用Eq來支持高阶类型。在
之前的Functor小节中，我们自定义了一个List类型，下面同样以
Kind<List.K,A>为例,来实现一个ListEq的Typeclass。

Page 637
abstract class ListEq<A>(val a: Eq<A>) : Eq<Kind<List.K, A>> {
override fun Kind<List.K, A>.eq(that: Kind<List.K, A>): Boolean {
val curr = this
}
return if (curr is Cons && that is Cons) {
val headEq = a.run {
curr.head.eq(that.head)
}
if (headEq) curr.tail.eq(that.tail) else false
} else if (curr is Nil && that is Nil) {
true
} else false
ListEq是一个抽象类，它接收一个类型为Eq<A>的构造参数a，
即一个Eq的实例。由于要模拟支持高阶类型的效果，ListEq又实现了
Eq<Kind<List.K,A>>。当为Kind<List.K,A>类型扩展eq方法的时候,
我们就可以在它的内部实现中调用a的eq方法了。
显然，ListEq比单纯的Eq前进了一大步。接下来，我们来展示如
何用它支持List类型的判等操作。
object IntListEq : ListEq<Int>(IntEq)

Page 638
IntListEq.run {
val a = Cons(1, Cons(2, Nil))
println(a.eq(Cons(1, Cons(2, Nil))))
println(a.eq(Cons(1, Nil)))
}
//运行结果
true
false
2.Show和Foldable
第二个要实现的Typeclass同样常见，相信你已经非常熟悉如何
在Java中给某个类实现一个toString的方法。现在我们通过设计一个
叫作Show的Typeclass,来实现类似的功能。
interface Show<F> {
fun F.show(): String
}
假设现在有一个Book类，然后我们定义一个BookShow的
Typeclass实例:
class Book(val name: String)
object BookShow : Show<Book> {

Page 639
}
override fun Book.show(): String = this.name
测试一下：
BookShow.run {
println(Book("Dive Into Kotlin").show())
}
//运行结果
Dive Into Kotlin
那么，如何让List类型像以上Eq一样也支持Show的操作呢?这次
可能不太乐观，因为与Eq不同，List的打印结果需要将元素的打印结
果都拼装起来，也就是说我们需要再对List类型增加一个类似fold的操
作。
因此，在实现List支持Show功能之前，我们先来设计另外一个支
持高阶类型效果的Foldable。在本章的后面部分,这个Typeclass将依
旧扮演非常重要的作用。
interface Foldable<F> {
fun <A, B> Kind<F, A>.fold(init: B): ((B, A) -> B) -> B
}

Page 640
@Suppress("UNCHECKED_CAST",
inline fun <A> Kind<List.K, A>.unwrap(): List<A> =
this as List<A>
然后,创建一个ListFoldable的实例:
}
object ListFoldable: Foldable<List.K> {
override fun <A, B> Kind<List.K, A>.fold (init: B): ((B, A) -> B) -> B = {f->
}
fun fold0(1: List<A>, v: B): B {
return when (1) {
is Cons -> •{
}
}
fold0(l.tail, f(v, I.head))
"NOTHING_TO_INLINE")
}
else -> V
fold0(this.unwrap(), init)
Foldable Kind<List.K, A>*fold, TEZ
后,我们就可以开始实现ListShow了。ListShow的设计思路与ListEq
相似，只是我们需要Foldable的额外帮助。

Page 641
abstract class ListShow<A>(val a: Show<A>): Show<Kind<List.K, A>> {
override fun Kind<List.K, A>.show(): String {
val fa = this
return "[" + ListFoldable.run {
fa.fold (listOf<String>()){r, i ->
r+ a.run { i.show()}
}
}
}
}).join ToString() + "]"
如上，我们实现了与ListEq类似的一个抽象类ListShow。同样，
**JBookListShow:
object BookListShow: ListShow<Book>(BookShow)
, WFBookListShow:
BookListShow.run {
println(
Cons(
Book("Dive into Kotlin"),
Cons(Book("Thinking in Java"), Nil)

Page 642
）
).show()
//运行结果
[Dive into Kotlin, Thinking in Java]

Page 643
10。3函数式通用结构设计
在上一节中我们介绍了如何在Kotlin中模拟Typeclass,并且实现
了Eq和Show。也许你会感觉其中采用的方法烦琐，因为针对这些简
单的功能，我们完全可以直接采用Kotlin的扩展来实现，非常方便。
确实，Kotlin中的扩展是很奇特的功能，我们在第7章中专门探讨
过它的强大之处。然而Typeclass这种多态的技术也十分适合函数式
编程，例如我们在实现Show的时候，引入了另外一个Foldable。
Typeclass之间的组合使得用它们进行程序设计非常灵活且低耦合。
在本节中，你会进一步了解到Typeclass的強大作用，我们会用
它来构建函数式编程中一些更加通用的结构。也许你早已听说过
Monad，却在理解它时感觉一头雾水，从而对函数式编程望而却步。
我们曾经说过，所谓函数式编程其实是个很宽泛的概念，所以即使没
有Monad，我们依然可以进行某种程度上的函数式编程。然而，
Monad也的确是这种编程范式中最通用的抽象结构，利用它你可以运
用组合的思想来抽象绝大部分的事物。
因此，我们有必要在本章的后半部分介绍下Monad，以及如何在
Kotlin中模拟实现它。那么到底什么是Monad呢?一个非常有名的解
读来自于Phillip Wadler:

Page 644
Monad无非就是个自函子范畴上的幺半群。
是不是感觉很迷惑?不急，在理解Monad之前，我们先来看看所
谓的幺半群吧，它也被称为Monoid。

Page 645
10.3.1 Monoid
在第4章中我们曾引入数学中“代数”的概念来解释什么是代数
数据类型。提到Monoid，一方面，它其实是一个很简单的Typeclass；
另一方面，Monoid这个术语也被用来描述某一种代数，这类代数遵
循了Monoid法则，即结合律和同一律。
1.什么是Monoid
现在我们终于体会到了编程和数学这门学科之间的紧密联系。如
同结合律、同一律是非常基础的数学法则，一个Monoid也是非常容
易理解的概念。它由以下几部分组成：
·一个抽象类型A；
·一个满足结合律的二元操作append，接收任何两个A类型的参数，
然后返回一个A类型的结果；
·一个单位元zero，它同样也是A类型的一个值。
下面来具体看看monoid如何满足两个数学法则：
·结合律。 append(a, append(b,c)) ==append(append(a,
b），c），这个等式对于任何A类型的值（a、b、c）均成立。
·同一律。append(a,zero)==a或append(zero,a)==a,单位元
zero与任何A类型的值（a）的append操作，结果都等于a。

Page 646
我们再用Kotlin来表达下Monoid这个数据类型，它是一个新的
Typeclass:
interface Monoid<A> {
fun zero(): A
fun A.append(b: A): A
}
现在我们来思考下能用Monoid这个抽象类型做什么。相信你已
经想到了字符串拼装的操作，它是一个典型的符合Monoid法则的具
体例子：
·抽象类型A具体化为String；
·任何3个字符串的拼接操作满足结合律，如：
("Dive"+"into")+"Kotlin"=="Dive"+("into"+"Kotlin");
·单位元zero为空字符串，即zero=""。
下面我们就来创建具体的Monoid实例stringConcatMonoid:
object stringConcatMonoid: Monoid<String> {
override fun String.append(b: String): String = this + b
override fun zero(): String = """
}

Page 647
好了,定义stringConcatMonoid的过程丝毫没有难度。那么这样
做到底有什么用呢?
2.Monoid和折叠列表
我们说过，Monoid是一种通用的数据结构，这意味着我们可以
利用它来编写通用的代码。如果你只是单纯看Monoid的定义，其实
非常简单。然而当它与列表结构联系在一起时，就可以发挥很大的作
用。
假设我们现在想要对前文定义的List类型扩展一个sum方法，该
方法支持使用者指定一种二元操作，可以对列表的元素进行操作。很
快你可能就会联想到之前的ListFoldable，显然这是一个典型的fold操
作：
fun <A> List<A>.sum(ma: Monoid<A>): A {
val fa = this
return ListFoldable.run {
fa.fold(ma.zero())({ s, i ->
}）
ma.run {
}
s.append(i)

Page 648
你应该注意到，sum方法接收了一个Monoid<A>类型的参数ma，
现在是不是一下子就明白了?Monoid这种抽象结构非常适合fold这种
折叠操作。
下面我们再来回顾下Kotlin集合库中对fold相关方法的定义：
inline fun <T, R> Iterable<T>.fold(
initial: R,
operation: (acc: R, T) -> R
）：R
果然,fold方法接收的两个参数initial和operation恰好对应了
Monoid<A>中的zero单位元和append 操作。现在,我们可以用
stringConcatMonoid来做点什么了:
println(
Cons(
"Dive",
Cons(
"into".
Cons("Kotlin", Nil)
）
).sum(stringConcatMonoid)

Page 649
//运行结果
Dive into Kotlin
除了字符串拼装之外，我们还可以找到其他很多同样适合使用
Monoid法则的操作，比如加法。当然，这些例子也比较简单，其实
你可以利用Monoid来抽象更加复杂的业务。然而由于篇幅有限，本
书不再举例，你可以自己尝试。

Page 650
10.3.2Monad
本节我们将介绍Monad，这是函数式编程中最通用的数据结构。
在介绍它之前，我们先来回味下Monoid，它很好地展现了函数式编
程的特点。
实际上，当我们用Monoid<A>、Monoid<B>组合出一个新的
Monoid<C>时,这个新的Monoid依旧遵循Monoid法则,即满足同一
律和结合律。这便是函数式编程的魅力之一，我们只要像遵循数学定
理一样进行组合，无须关注过程中具体的类型（如A、B）的细节，
最终推导出的结果依旧遵循正确的法则，这便省去了测试的工作。
1。函子定律
同样的特点也存在于10。2。2节所介绍的Functor中，它被称为函子。
这也是一种非常通用的抽象数据结构，它为类型Kind<F，A>定义了
map操作,返回另一个类型Kind<F,B>。现在来回顾下Functor的具
体实现：
interface Kind<out F, out A>
interface Functor<F> {
fun <A, B> Kind<F, A>.map(f: (A) -> B): Kind<F, B>
}
我们曾提到，这里的类型参数F模拟了高阶类型中的类型构造器。

Page 651
在之前的例子中，我们用List。K来替代F，代表这是一个列表的容器。
实际上，我们的F当然还可以是其他的类型构造器，比如：
·Kind<Effect。K，A>，d代表可空或存在的高阶类型；
·Kind<Effect。K，A>，代表拥有副作用的高阶类型；
·Kind<Effect。K，A>，代表解析器的高阶类型。
尽管这些构造器虽然容器不同(Option.K、Effect.K、Parser.K),
并且它们容器内的值只有一个，如Option。K容器內只存在两种可能的
取值（空或者存在的值），然而它们都可以看成“阉割”版的List。K，
并且都可以用来派生出Functor的具体Typeclass实例。如:
object OptionFunctor: Functor<Option.K> {
override def fun <A, B> Kind<Option.K, A>.map(f: (A) -> B): Kind<Option.k
}
}
object EffectFunctor: Functor<Effect.K> {
override def fun <A, B> Kind<Effect.K, A>.map(f: (A) -> B): Kind<Effect.K,
}
}
object ParserFunctor: Functor<Parser.K> {
override def fun <A, B> Kind<Parse.K, A>.map(f: (A) -> B): Kind<Parser.K

Page 652
}
}
这些Functor的实例都遵循函子定律：
1）同一律法则。假设存在一个identity的函数，接收A类型的参
数a，则返回结果还是a。
fun identity<A>(a: A) = a
那么，当我们调用函子实例的map方法，执行identity函数时，显
然返回的结果还是实例本身。如：
ListFunctor.run {
println(Cons(1, Nil).map { indentity(it) })
}
//运行结果
Cons(1, Nil)
2）用map进行的组合满足结合律。这条法则指的是，当我们对
函子实例先应用函数f进行map，再将转化的结果应用函数g进行map，
这个操作最终得到的结果，与直接对函子实例应用两个函数组合的新

Page 653
函数进行map的结果相同。如：
fun f(a: Int) = a +1
fun g(a: Int) = a * 2
ListFunctor.run {
val r1 = Cons(1, Nil).map { f(it) }.map { g(t) }
val r2 = Cons(1, Nil).map { f(g(it))}
println(r1 == r2)
}
//运行结果
true
函子定律保证了实例本身的容器F不变，但是我们可以改变容器
内部的程序状态，主要通过map方法来实现，并且map施用的函数可
以进行组合。
然而，Functor的作用显得比较有限。在10。1节我们曾介绍过，
函数式编程的思维就是站在更高的层次去抽象业务，然后进行组合。
显然Functor的map操作并没有为我们提供足够高的抽象组合能力。
假如我们把高阶类型Kind<F，A>比作一个管道，Functor提供了
一种能力，支持对管道内的状态进行转化操作，可简化表示为一个
map操作:

Page 654
fun <A, B> map(fa: Kind<F, A>, f: (A) -> B): Kind<F, B>
再进一步思考，那些拥有相同容器类型F的管道其实规格相同，
表明它们容易被组合。在现实世界中，如果我们能够对不同的管道进
行组合，拼装成一个新的管道，新的管道规格保持不变，即容器依旧
保持不变，利用递归的思想（类似Pair可以构建出List），我们就可以
创造出一个无穷尽的世界，就好比贪吃蛇的游戏。因此，我们需要有
一个新的map2函数来支持以下的操作：
fun <A, B, C> map2(fa: Kind<F, A>, fb: Kind<F, B>, f: (A, B) -> C): Kind<F, C
当有了支持map2的操作之后，你会发现整个抽象层次就更高
了。与纯的map操作不同，现实世界充满了副作用，它们无法在业务
中被避免。然而，正如10。1。2节所介绍的那样，假使我们将副作用限
制在管道容器之内，并将管道视为一个拥有原子性的整体（正如贪吃
蛇的方块），那么就这个层面而言，它依旧是符合引用透明性的。于
是，我们可以将相同容器內的副作用操作利用函数f进行组合，尽量
推迟到最后执行，这就是典型的函数式编程。
2。flatMap实现更复杂的组合
那么，如何为高阶类型实现map2的效果呢?先来思考直接利用
map的效果，我们可能会得到一个嵌套容器的结构。例如你对类型
Kind<F，A>进行map，应用一个返回Kind<F，B>的函数，那么得到

Page 655
的结果将是Kind<F,Kind<F,B>>。显然,我们需要一个flatten的操
作，可以把嵌套的容器F提取出来，转化结果为Kind<F，B>。
阅读过6.2.5节的读者已经发现,Kotlin中的flatMap支持flatten操
作，本质上它可以看成map与flatten的结合操作。因此，要实现map2
函数的效果，一种可行的思路就是给我们的高阶类型也扩展一个
flatMap方法。
fun <A, B> Kind<F, A>.flatMap(f: (A) -> Kind<F, B>): Kind<F, B>
flatMap跟map一样，也是一个高阶函数。它的参数是一个函数
f，该函数接收类型A的参数，然后返回另一个Kind<F，B>的值。
flatMap最终返回的结果类型也是Kind<F,B>。
高阶类型如果有了flatMap方法，我们就可以很容易地实现map2
函数。
fun <A, B, C> map2(fa: Kind<F, A>, fb: Kind<F, B>, f: (A, B) -> C): Kind<F, C
fa.flatMap { a => fb.map( b => f(a, b)) }
}
看来在利用高阶类型进行函数式编程时，flatMap是一个至关重
要的方法。更有趣的是，如果我们再引入一个pure方法，那么map方
法同样也可以用flatMap来实现。

Page 656
pure有时候也被叫作unit(在Haskell中它对应的是return,
flatMap则代表bind），它核心的作用，就是将一个A类型的参数，转
化为Kind<F，A>类型。
fun <A> pure(a: A): Kind<F, A>
下面我们来看看如何利用unit和flatMap方法来定义map:
fun <A, B> flatMap(fa: Kind<F, A>, f: (A) -> Kind<F, B>): Kind<F, B>
fun <A, B> map(fa: Kind<F, A>, f: (A) -> B): Kind<F, B> = {
flatMap(fa) { a => pure(f(a)) }
}
由此可见，pure和flatMap可作为一种最小的原始操作集合，利用
这两个函数的组合我们可以实现map、map2及更加复杂的数据转换
操作。那么请你再思考下，如果我们再定义一种新的Typeclass，同
时包含了pure和flatMap操作，那么它将是一种最通用的函数式结构。
讲到这，你也许已经发现了，这就是Monad。
3.什么是Monad
谈论Monad的时候,我们需要对Monad Typeclass及Monad概念
本身进行区分。准确地说，Monad是满足Monad法则的一个最小集的
实现，它可被称为单子。然而这个实现的组合并不是唯一的，比如我

Page 657
compose**.
pure flatMap↑ÆN, AĦŁJpure.
因此,我们接下来要定义的名为Monad<F>的Typeclass,只是其
中的一种版本，然而它必须满足Monad法则。下面我们先来看看
Monad<F>#X:
interface Monad<F> {
fun <A> pure(a: A): Kind<F, A>
fun <A, B> Kind<F, A>.flatMap(f: (A) -> Kind<F, B>): Kind<F, B>
}
如之前所言,我们为Monad<F>定义了pure方法,以及利用Kotlin
语言的特性，为模拟的高阶类型Kind<F，A>扩展了flatMap方法。在
用了Monad<F>之后,我们先用它来创建一个ListMonad实例:
object ListMonad : Monad<List.K> {
private fun <A> append(fa: Kind<List.K, A>, fb: Kind<List.K, A>): Kind<List
return if (fa is Cons) {
Cons(fa.head, append(fa.tail, fb).unwrap())
} else {
fb
}

Page 658
}
override fun <A> pure(a: A): Kind<List.K, A> {
return Cons(a, Nil)
}
override fun <A, B> Kind<List.K, A>.flatMap(f: (A) -> Kind<List.K, B>): Kinc
val fa = this
}
val empty: Kind<List.K, B> = Nil
return ListFoldable.run {
fa.fold(empty)({r, I ->
append(r, f(l))
}
}
4.ApplicativeXMonad
当前我们已经知晓的是，用pure和flatMap可以实现map。那么你
肯定也能够猜到，所有的Monad其实都可以是Functor，那么我们是
否可以在定义Monad<F>的时候，直接实现Functor<F>呢?方法如下：
interface Monad<F>: Functor<F> {}
这当然是可以的，这样我们就给所有的Monad<F>操作扩展了

Page 659
map的操作。事实上，数学中的3种代数结构存在如下依赖关系：
Functor -> Applicative -> Monad
也就是说所有的Monad都是Applicative,所有的Applicative都是
Functor。在Haskell的发展历史中,Monad跳过了Applicative被更早地
发现了,这个也容易理解,因为相比Applicative,Monad要更加通用
一些。下面我们来定义一个具体的Applicative<F>,来看看Applicative
到底是怎样的结构：
interface Applicative<F> : Functor<F> {
fun <A> pure(a: A): Kind<F, A>
fun <A, B> Kind<F, A>.ap(f: Kind<F, (A) -> B>): Kind<F, B>
}
override fun <A, B> Kind<F, A>.map(f: (A) -> B): Kind<F, B> {
return ap(pure(f))
}
如你所见,Applicative<F>直接实现了Functor<F>,然后在其内
部为高阶类型扩展了一个ap方法。ap方法接收一个高阶类型为
Kind<F，（A）->B>的参数，然后返回Kind<F，B>。
在有了Applicative<F>之后，我们就可以用它来重新定义
Monad<F>:

Page 660
interface Monad<F> : Applicative<F> {
fun <A, B> Kind<F, A>.flatMap(f: (A) -> Kind<F, B>): Kind<F, B>
override fun <A, B> Kind<F, A>.ap(f: Kind<F, (A) -> B>): Kind<F, B> {
return f.flatMap { fn ->
this.flatMap { a ->
pure(fn(a))
}
}
}
*, Monad<F>-Functor<F>, X-Applicative<F>,
所以它也同时定义了map和ap方法。

Page 661
10。3。3Monad组合副作用
讲了这么多Monad，我们必须来展现它的威力了。Monad被创造
的一个很大的使命，就是可以用来组合现实中的副作用，由此我们可
以发挥函数式编程的优点（引用透明性和等式推理），来设计准确、
容易测试的程序。接下来，我们就举一个实例。
说到副作用，很常见的就是IO操作。我们先来创建一个代表标准
输入和输出的类型StdIO<A>,它实现了Kind<StdIO.K,A>:
@Suppress("UNCHECKED_CAST", "NOTHING_TO_INLINE")
inline fun <A> Kind<StdIO.K, A>.unwrap(): StdIO<A> =
this as StdlO<A>
sealed class StdIO<A> : Kind<StdIO.K, A> {
object K
companion object {
fun read(): StdIO<String> {
return ReadLine
}
fun write(l: String): StdlO<Unit> {
return WriteLine(I)
}
fun <A> pure(a: A): StdIO<A> {
return Pure(a)
}

Page 662
}
}
object ReadLine : StdlO<String>()
data class WriteLine(val line: String) : StdlO<Unit>()
data class Pure<A>(val a: A) : StdO<A>()
在上述例子中，我们创建了单例对象ReadLine、数据类
WriteLine来表示读写行操作，以及一个数据类Pure，接收一个A类型
的参数，然后表示为一个StdIO<A>实例。同时，我们还在StdIO的伴
生对象中实现了read、write及pure方法。下面，我们再来实现一个
StdlOMonad,它提供了可组合的方法:
data class FlatMap<A, B>(val fa: StdIO<A>, val f: (A) -> StdIO<B>) : StdlO<E
object StdIOMonad : Monad<StdIO.K> {
override fun <A, B> Kind<StdIO.K, A>.flatMap(f: (A) -> Kind<StdIO.K, B>):
return FlatMap<A, B>(this.unwrap(), ({ a ->
f(a).unwrap()
}
}））
}
override fun <A> pure(a: A): Kind<StdIO.K, A> {
return Pure(a)
}

Page 663
如你所见,StdlOMonad 实现了Monad<StdIO.K>,并为
Kind<StdIO.K,A>扩展了flatMap操作。接着我们就用StdIO以及
StdlOMonad来实现一个具体的读写业务例子。
假设现在要读取两个数字进行加法操作，然后输出结果。先来实
现一个perform方法，该方法接收一个StdIO<A>类型的参数，然后实
现相应的操作：
fun <A> perform(stdlO: StdIO<A>): A {
fun <C, D> runFlatMap(fm: FlatMap<C, D>) {
perform(fm.f(perform(fm.fa)))
}
}
@Suppress("UNCHECKED_CAST")
return when (stdlO) {
is ReadLine -> readLine() as A
is Pure<A> -> stdlO.a
is FlatMap<*, A> -> runFlatMap(stdlO) as A
is WriteLine -> println(stdlO.line) as A
}
在这个例子中，存在3个副作用的操作：读入第1个值、读入第2
个值，将结果进行打印。我们可以用StdIO对象的read和write方法来
分别处理读写操作，由于这些方法返回的结果类型都实现了

Page 664
Kind<StdIO.K,A>,因此都可以调用flatMap方法。所以,我们可以
这样来实现这个例子：
val io = StdIOMonad.run {
}
StdIO.read().flatMap { a ->
StdIO.read().flatMap
{b->
StdIO.write((a.toInt() + b.tolnt()).toString())
}
}
perform(io.unwrap())
以上我们通过flatMap组合了StdIO对象，并将所有操作定义为一
个名为io的变量。当io变量被定义时，业务逻辑也同时被定义，然而
读写并没有发生。至此整个程序依旧符合引用透明的原则，由于组合
满足Monad定律，因此我们也完全相信，只要编译通过，各环节的类
型检查无误，那么这段代码就是正确的。
最终等你执行了perform方法，那么整个io操作才会被触发。

Page 665
10。4类型代替异常处理错误
在了解完通用的函数式结构之后，我们再来看看如何用函数式编
程的方式来处理业务中的意外错误。
需要注意的是,Kotlin抛弃了Java中的受检异常(Checked
Exception）。众所周知，Java中的受检异常必须被捕获或者传播，由
于编译器强制检查，这样就不会忘记处理异常，可以在编译期提前发
现程序bug。然而，也存在很多反对的声音。比如受检异常虽然在简
短的程序中显得特别有用，但如果强制在大型软件工程中应用，则会
让编码变得异常烦琐，降低生产力。所以类似C#这种语言也没有采
用受检异常。
关于受检异常还是非受检异常的话题，已经有过非常多的争论，
本节不会过多讨论这个问题。我们需要真正关心的是，“用异常来处
理错误”的这种做法是否适合函数式编程。
相信你很快就已经发现，抛出异常这种做法本身其实是一种副作
用，它破坏了“引用透明性”。那么这又是否意味着函数式编程中我
们就需要抛弃错误处理吗?当然不是，任何健壮的程序都需要对具体
的错误进行捕捉并且给出正确的反馈。其实我们可以换一种思路，在
上一节的内容中，你已经接触到了高阶类型及Monad这种通用的函数

Page 666
式结构，事实上，我们完全可以利用这种更抽象的数据结构，来代替
异常处理错误。此外，用类型来处理错误的方式有另一个优点，那就
是类型安全。

Page 667
10.4.1 Option与OptionT
在5。2节中我们已经介绍了Kotlin的可空类型，某种程度上这就是
利用类型代替Checked Exception来防止NPE问题。在学会如何用
Kotlin模拟高阶类型之后，其实我们还可以自定义一个Option类型：
@Suppress("UNCHECKED_CAST", "NOTHING_TO_INLINE")
inline fun <A> Kind<Option.K, A>.unwrap(): Option<A> =
this as Option<A>
sealed class Option<out A> : Kind<Option.K, A> {
object K
}
data class Some<V>(val value: V) : Option<V>()
object None : Option<Nothing>()
Kind<Option.K,A>跟Kind<List.K,A>一样模拟了一种高阶类型,
用它我们可以表示存在值或者空值这两种状态，分别对应了数据类
Some以及单例对象None,其中None实现了Option<Nothing>() 。
在有了具体的Option类后,我们就可以创建一个OptionMonad,
来给Option类型扩展flatMap、pure及map方法,从而使它具备强大的
组合能力。

Page 668
object OptionMonad : Monad<Option.K> {
override fun <A, B> Kind<Option.K, A>.flatMap(f: (A) -> Kind<Option.K, B>
val oa = this
}
}
return when (oa) {
}
}
is Some -> f(oa.value)
else -> None
override fun <A> pure(a: A): Kind<Option.K, A> {
return Some(a)
接下来,我们看看如何应用Option和OptionMonad。在10.3.3节
中，我们举了一个两次读值，再进行求和输出的例子。现实中，这个
例子是可能发生业务逻辑错误的。因为输入的值可能并不是数字，而
是字母或者特殊符号，所以当我们将toInt方法应用到读值结果时，就
可能发生错误。所以，我们需要通过某种手段来处理这些错误。
一种可行的思路是通过Option<Int>类型来表示读取的结果，当检
测到读取的值并非数字的时候，我们就可以把它当成None。只要用
户的输入存在一次None值，那么最终的计算结果也为None，即非合
理的情况。我们先来实现这样一个名为readInt的方法：

Page 669
fun readint(): StdlO<Option<Int>> {
return StdlOMonad.run {
val r = StdlO.read().map {
when {
}
}
}
}
it.matches(Regex("[0-9]+")) -> Some(it.tolnt())
else -> None
}
r.unwrap()
然后，一个比较核心的操作就是对两个类型为Option<Int>的变量
进行求和操作，我们通过一个名为addOption的函数来实现它：
fun addOption(oa: Option<Int>, ob: Option<Int>) = {
OptionMonad.run {
oa.flatMap { a ->
ob。map{b->a+b}
}

Page 670
可以发现,addOption的操作是依赖OptionMonad扩展的flatMap
方法来实现两个读值之间的组合，最终它的返回结果也是Option<Int>
类型。
于是,你就可以定义一个errorHandleWithOption函数来实现这个
需求：
fun errorHandleWithOption() {
StdlOMonad.run {
}
}
readInt().flatMap { oi ->
readInt().flatMap { oj ->
}
val r = addOption(oi, oj)
val display = when (r) {
is Some<*> -> r.value.toString()
else->"""
}
StdIO.write(display)
再一次我们通过神奇的Monad实现了常见的业务场景。然而，你
可能依旧不满意，因为从计算资源利用率角度来说，这个方案并没有

Page 671
达到最优。如果第1次读值就出现了错误，那么最理想的处理方案就
是马上返回非正常的结果，而当前的方案依旧会进行第2次读值。
同时，上面的代码对StdIO进行组合时，由于其内部都是Option
类型，每次都必须先对该Option类型的值进行模式匹配，然后再处理。
如果能把StdIO<Option<T>>中的StdlO<Option<*>>看成一个整体,就
可以直接对T进行组合操作，这样就能进一步提升可读性。OptionT正
是为此设计的数据类型。
data class OptionT<F, A>(val value: Kind<F, Option<A>>) {
object K
companion object {
fun <F, A> pure(AP: Applicative<F>): (A) -> OptionT<F, A> = { v ->
OptionT(AP.pure(Some(v)))
}
fun <F, A> none(AP: Applicative<F>): OptionT<F, A> {
return OptionT(AP.pure(None))
}
fun <F, A> liftF(M: Functor<F>): (Kind<F, A>) -> OptionT<F, A> = { fa ->
val v = M.run {
fa.map {
}
Some(it)
}
OptionT(v)

Page 672
}
}
fun <B> flatMap(M: Monad<F>, f: (A) -> OptionT<F, B>): OptionT<F, B> {
val r = M.run {
value.flatMap { oa ->
when (oa) {
is Some -> f(oa.value).value
else -> M.pure(None)
}
}
}
return OptionT(r)
}
fun <B> flatMapF(M: Monad<F>, f: (A) -> Kind<F, B>): OptionT<F, B> {
val ob = M.run {
value.flatMap {
when (it) {
is Some -> f(it.value).map {
Some(it)
}
}
}
else -> pure(None)
}
return OptionT(ob)

Page 673
}
}
fun <B> map(F: Functor<F>, f: (A) -> B): OptionT<F, B> {
val r: Kind<F, Option<B>> = F.run {
value.map {ov ->
}
}
OptionMonad.run {
ov.map(f).unwrap()
}
}
return OptionT(r)
}
fun getOrElseF(M: Monad<F>, fa: Kind<F, A>): Kind<F, A> {
return M.run {
}
value.flatMap {
when (it) {
}
is Some -> M.pure(it.value)
else -> fa
乍一看，OptionT的实现比Option要复杂很多。我们先来看看数

Page 674
据类OptionT的参数value,它的类型是Kind<F,Option<A>>的。这也
就意味着如果存在一个Option类型的值，我们就可以给它套上类型构
造器类型F，然后再包裹一个OptionT类型。这样做有什么用呢?
先来看看OptionT中的pure和none方法,应该不难理解,首先,
由于它们接收的参数只需拥有一个pure方法，所以类型是
Applicative<F>就足够了,而不用必须是一个Monad<F>。其次,是最
核心的flatMap方法，注意了，flatMap方法在定义时存在一个等号，
熟悉Kotlin定义函数语法的我们应该可以明白，这其实是一个表达式
函数体。因此，这里flatMap的返回值是一个lambda，类型为（（A）-

>OptionT<F,B>)->OptionT<F,B>。看到这个类型你可能又有点被
>绕晕了。
>不急，我们再来看看flatMap的具体实现：
>1)当OptionT类型的对象flatMap一个Monad<F>实例时,我们就
>可以再调用一个具体的处理函数f，该函数类型为（A）->OptionT<F，
>B>，即接受一个变量，然后再返回一个OptionT类型的对象；
>2)如果调用flatMap的OptionT实例,内部value对应的Option<A>
>类型部分的值不存在，则直接返回一个None值转化的Monad<F>实
>例，然后再用OptionT类型包裹；
>3)如果value对应的Option<A>类型部分的值存在,也就是Some
>类型的对象，那么就会用函数f接收该对象的value进行处理，最终返
>回一个处理后的新的OptionT对象。

Page 675
如果我们仔细思考，会发现OptionT本质上是在应用Option时，
特定场景下一种表达上的简化。
回顾上述读值求和的例子，如果我们要实现输入值错误时，程序
立即输出非正常结果，那么必须对每一次读取的Option类型的值进行
判断，只有当该值为Some类型时，才进行下一步操作。然而，如果
要组合的场景变得更多，这种做法会在语法表达上呈现出很多层的嵌
套结构，显得十分不优雅。
OptionT直接消除了这种嵌套的层级，我们可以将这种思路简单
理解为：用一种OptionT类型的对象去做组合，然后产生新的OptionT
对象可以继续做其他的组合，一旦某次组合结果返回的Option<T>部
分为None，则停止。
不要被OptionT吓住
不得不承认的是，函数式编程中的抽象数据类型就像数学中的公式，
在定义上会显得抽象，然而如果我们足够耐心，一步步去推演其中的
逻辑，那么就会发现这个过程显得无比正确。
好了，下面我们就用OptionT来实现之前的例子：
fun errorHandleWithOptionT() {
fun readInt(): OptionT<StdIO.K, Int> {
val r = StdIOMonad.run {
val r = StdIO.read().map {
when {

Page 676
}
}
}
it.matches(Regex("[0-9]+")) -> Some(it.tolnt()
else -> None
}
r.unwrap()
}
return OptionT(r)
}
val add = readlnt().flatMap(StdIOMonad) { i->
}
readInt().flatMapF(StdIOMonad) { j ->
StdlO.write((i+j).toString())
add.getOrElseF(StdIOMonad, StdlO.write("input error"))
在运用了OptionT之后，我们成功解决了之前的问题，同时又保
证了语法表达上的简洁。

Page 677
10.4.2 Either与EitherT
一个新的问题出现了，现实中的业务有时候错误的种类是多样化
的，而不仅仅是一种。针对不同的错误，我们最好能够提供不同的处
理方式。还是上述的例子，我们已经知晓，如果读取值是非数字，那
么就会产生错误。此外，即使是数字，如果输入的位数过长，那么也
会产生整型溢出的问题，这也是另一种错误的情况时。这时候如果仅
仅用Option显然不能对非正常的情况做到很好的区分，因此我们需要
思考一种更加通用的抽象数据类型。
也许你已经想到了Either，我们在5。2。2节中已经实现了一个简陋
的Either版本，它是这样的：
sealed class Either<A,B>() {
class Left<A,B>(val value: A): Either<A,B>()
class Right<A,B>(val value: B) : Either<A,B>()
}
简单来说，Either类型用于表示非A即B的值，从这个角度上看，
Option也可以认为是一种特殊的Either，只是它仅仅代表了是否存在
的关系。由于Either更加通用，所以你会看到它需要接收两个类型变
量。然而，该版本的Either并没有支持高阶类型。因此，我们来写一
个新的Either,因为Either的特殊需求,我们也需要定义Kind2<F,
A，B>，这是通过类型别名定义的。

Page 678
typealias Kind2<F, A, B> = Kind<Kind<F, A>, B>
现在来看下新版本的Either实现：
@Suppress("UNCHECKED_CAST", "NOTHING_TO_INLINE")
inline fun <A, B> Kind2<Either.K, A, B>.unwrap(): Either<A, B> =
this as Either<A, B>
sealed class Either<out A, out B> : Kind2<Either.K, A, B> {
object K
}
data class Right<B>(val value: B): Either<Nothing, B>()
data class Left<A>(val value: A): Either<A, Nothing>()
经过之前的“磨炼”，相信你在理解Either的实现上已经毫无难度
了。作为构建函数式通用结构的基本套路，我们还需要给这个Either
类型增加一个EitherMonad:
class EitherMonad<C> : Monad<Kind<Either.K, C>> {
override fun <A, B> Kind<Kind<Either.K, C>, A>.flatMap(f: (A) -> Kind<Kin
val eab this
return when (eab) {
is Right -> f(eab.value)
is Left -> eab

Page 679
}
}
}
}
override fun <A> pure(a: A): Kind<Kind<Either.K, C>, A> {
return Right(a)
else -> TODO()
当然，Either也存在类似Option一样的窘境，当面临多组合场景
的情况时，我们还是需要一个类似OptionT的Either版本来解决相似的
问题。同样的命令方式，它就是EitherT。此外，也是类似OptionT改
进的思路，我们可以如此来定义EitherT：
data class EitherT<F, L, A>(val value: Kind<F, Either<L, A>>) {
companion object {
fun <F, A, B> pure(AP: Applicative<F>): (B) -> EitherT<F, A, B> = { b->
EitherT(AP.pure(Right(b)))
}
}
fun <B> flatMap(M: Monad<F>): ((A) -> EitherT<F, L, B>) -> EitherT<F, L,
val v = M.run {
value.flatMap {ela ->
when (ela) {
is Left -> M.pure(Left(ela.value))

Page 680
}
}
}
is Right -> f(ela.value).value
}
}
EitherT(v)
}
fun <B> map(F: Functor<F>): (((A) -> B) -> EitherT<F, L, B>) = { f->
val felb = F.run {
value.map { ela ->
}
EitherMonad<L>().run {
ela.map(f).unwrap()
}
Either T (felb)
最后，结合之前读值求和的例子，我们可以很容易地将基于
Either的例子改写为如下内容：
fun errorHandleWithEitherT() {
fun readlnt(): EitherT<StdlO.K, String, Int> {
val r = StdlOMonad.run {

Page 681
}
}
StdlO.read().map {
when {
it.matches (Regex("[0-9]+")) -> Right(it.tolnt())
else -> Left("${it} is not a number")
}
}
}
val add = readlnt().flatMap(Stdl OMonad) { i->
readInt().flatMapF(StdlOMonad) { j ->
StdlO.write((i+j).toString())
}
}
}
return EitherT(r)
add.valueOrF(StdIOMonad) { err ->
StdlO.write(err)
不难发现，使用EitherT之后，代码的可读性得到了极大改善。

Page 682
66
10。5本章小结
（1）函数式语言
函数式语言的定义存在狭义和广义两种。狭义的函数式语言以
Haskell为代表，有着非常简单且严格的语言标准，即只通过纯函数
进行编程，不允许有副作用，且仅采用不可变的值。而从广义上来看，
任何“以函数为中心进行编程”的语言都可称为函数式编程。
（2）引用透明性和副作用
判断一段程序是否具备引用透明性的依据是：一个表达式在程序
中是否可以被它等价的值替换，而不影响结果。具有副作用行为的函
数违背了引用透明性原则，会导致不容易被测试及难以被组合。
（3）纯函数与局部可变性
如果一个函数输入相同，对应的计算结果也相同，那么它就具备
引用透明性”，可被称为“纯函数”。不可变性在很大程度上促进了
纯函数的创建，但这并不意味着需要放弃可变变量。如果一个函数存
在局部可变性，当它被外部执行调用的时候，整体可以被看成一个黑
盒，程序依旧符合引用透明性。
(4)模拟高阶类型和Typeclass

Page 683
高阶类型支持传入构造器变量，或构造出另一个类型构造器。虽
然Kotlin不支持高阶类型,但是通过interface和泛型可以在Kotlin中模
拟出高阶类型的效果。在此基础上,类似Haskell的Typeclass也可以
被模拟创造，这为抽象业务提供了另一种不同的思路。
(5)Monoid
Monoid是一种很简单的抽象数据类型，只要满足Monoid法则中
的同一律和结合律，就可以定义一个Monoid结构，Monoid天然适合
fold操作。
(6)Monad
Monad是最通用的函数式抽象数据结构，它的核心是为高阶类型
扩展flatMap操作，再结合pure操作，就能以最小的操作集合创造出其
他组合的操作，从而构建出一个无穷的世界。利用Monad结构可以很
好地组合副作用，从而构建易于测试和推理的程序。
（7）用类型处理错误
函数式数据类型,如Option、OptionT、Either、EitherT,为业务
中的错误处理提供了一种新的思路，即抛弃传统的异常处理，基于高
阶类型来定义和区分业务中非正常的情况。这种思路依然符合引用透
明性，让函数式编程显得格外具有特色。

Page 684
第11章异步和并发
异步与并发是一个非常值得关注的话题，异步编程模型旨在让我
们的系统能承载更大的并发量，而线程安全又是系统在高并发时能正
确运转业务的一种保证，如何理解它们的原理并设计出更优的方案是
值得探讨的。本章先带你了解最基本的线程模型及Kotlin的协程，接
着回顾传统方式中如何保证线程安全，然后引入两个新的概念—
Actor及CQRS架构,最终结合Kotlin实践,领略并发编程之美。

Page 685
11。1同步到异步
在我们进行开发的时候，“同步”和“异步”这两个词语经常会
被提及，同时，“阻塞”和“非阻塞”也会相应被提到。这几个概念
经常被混淆。本节我们将介绍同步编程存在的一些问题，然后看看如
何通过异步编程来解决它们。当然异步编程也不是万能的，它也存在
一些弊端。在介绍同步和异步的概念时，我们也会详细介绍阻塞与非
阻塞。

Page 686
11。1。1同步与阻塞的代价
同步”与“阻塞”这两个概念经常会被放在一起，非常容易给
我们一种“同步即阻塞阻塞即同步”的错觉。其实这两个概念并
没有太强的联系，接下来就让我们通过一个例子来理解这两个概念。
66
相信你一定有过在线购物的经历，假如现在有一个在线商城，商
家设置的是“下单减库存”。当我们点击下单按钮的时候，会向服务
端发送一个下单的请求，这个时候在服务端就会有如下操作：
·查询相关商品的信息；
·整理商品信息（比如价格，数量等）；向数据库中插入订单快照同时
减掉库存（这里我们不考虑事务，假设是先插入订单再减掉库存）。
上面的操作表现在代码层面，通常是这样的：
public void createOrder(String productNo){
if(productNo == null || '''.equals(productNo)){
return;
}
//获取商品信息
ProductInfo productInfo = getltemInfo(productNo);
if(productinfo == null){
return;
}

Page 687
}
//整理订单信息
OrderInfo orderInfo = convert2OrderInf(productInfo);
//插入订单并减库存
insertRecord(orderInfo);
reduceStore(productNo);
上面的实现代码用到的是我们在Java中经常采用的同步实现方
式。那么这些代码是怎样在服务端执行的呢?如果你熟悉Java
Web,那你对Apache Tomcat一定不会陌生,我们在使用Java Web框
架开发需求的时候，ApacheTomcat是最常采用的服务器。我们来看
看在Apache Tomcat上面是如何完成这些操作的。
我们知道ApacheTomcat采用的是线程模型，就是多线程的工作
方式（更多关于多线程的内容我们会在下一节介绍），如图11-1所示。
(HTTP请求
接收者线程
accepter
thread
请求连接队列
0000
request
request
request
request
请求处理线程
请求处理线程
请求处理线程

Page 688
图11-1 Apache Tomcat的工作方式
接收者线程(acceptor thread)接收客户端的HTTP请求,然后
将这些请求分配给请求处理线程进行处理。这就是Tomcat的工作原
理。
通过图11-1我们可以知道，当Tomcat中接收到多个下单请求连
接的时候，它会为每一个连接分配一个线程，然后再由这些线程去执
行相应的操作。对于下单这个操作，在单个线程中就是以下面这种方
式进行操作的，如图11-2所示。
插入订单
获取商品信息
等待商品信息获取的结果
减库存
等待插入结果
图11-2下单的处理过程
等待减库存结果
我们知道，解析请求、查询商品信息、插入快照和减库存的操作
都是IO操作，但IO操作相对会慢一些。在Tomcat分配的线程中执行
的时候，每当执行到IO操作时，程序就会处于等待状态，同时该线程
会处于挂起状态，也就是该线程不能执行其他操作，而必须等待相应

Page 689
结果返回之后才能继续执行。
当执行IO操作时，程序必须要等待IO操作完成之后才能继续执
行，这种方式称之为同步调用。同时我们也能看到线程被挂起了，也
就是线程没有被执行，这就是阻塞。所以上面操作的执行方式是同步
阻塞的。
这里就需要知道同步其实与阻塞是两个不同的概念了。同步指的
是一个行为，当执行IO操作的时候，在代码层面我们需要主动去等待
结果，直到结果返回。而阻塞指的是一种状态，当执行IO操作的时候，
线程处于挂起状态，就是该线程没有执行了。所以同步不是阻塞，同
步也可以是非阻塞的，比如我们在执行同步代码块的时候，线程可以
不阻塞而是一直在后台运行。
同步描述的是一种行为，而阻塞描述的是一种状态（异步与非阻
塞也是如此）。
接着回到下单这个逻辑上来，通过上面线程执行操作的图我们还
可以知道，该线程在执行开始到执行结束这个时间段内，有大部分的
时间用在了等待上面，这样就极大地消耗了资源。像Tomcat这种多
线程的机制，若每个线程都采用这种机制，消耗的资源将会成倍增加。
当处理的请求不算太多的时候，这种模型是不会有什么大问题
的。我们知道，Tomcat能分配的线程是有限的，一旦客户端发来的
请求数远远大于Tomcat所能处理的最大线程数，没有得到处理的请
求就会处于阻塞和等待的状态，反映到用户层面就是页面迟迟得不到
响应。如果等待时间过长，耐心的用户也许会看到请求超时的错误，

Page 690
而急性子的用户早早地就关掉了页面。

Page 691
11。1。2利用异步非阻塞来提高效率
前一节我们通过一个例子解释了同步阻塞是如何工作的，也知道
同步阻塞的方式会带来许多的问题。为了解决这些问题，我们引入了
异步非阻塞，下面我们就来看看如何利用异步非阻塞的方式去实现上
一节所提到的需求，以及用这种方式能带来哪些优势。
首先，在代码层面我们可以将同步的逻辑转换为异步的逻辑，比
如上面的同步代码就可以采用异步的实现方式，代码的实现我们将放
在下一节详细讲解。
那么采用异步实现的好处是什么?首先，我们来看一下什么是异
步。异步是区别于同步的，我们知道，程序在执行IO操作时候，如果
是同步代码块，程序会一直处于阻塞状态，也就是必须等待该IO操作
返回出结果，程序才能继续执行下去。如果采用了异步的实现方式，
那么当执行IO操作的时候程序可以不用等待，还可以继续执行其他代
码块，比如执行其他异步的IO操作。假设该程序是多线程的，如果采
用同步的实现方式，那么该程序就会在这一个线程上面等待，并且其
他的线程也必须等待该线程的完成。采用异步的方式，当程序执行IO
操作的时候，程序可以去执行其他线程的代码，不用在这里一直等着，
当有结果返回的时候，程序再回来执行该代码块。这样就节省了许多
资源。
通过上面的方式，我们就将同步形式改成了异步形式。将同步的
代码换成异步的代码能解决一些性能上的问题，但是并不能解决阻塞
调用所带来的瓶颈，即使在代码层面已经优化得非常好了，也不能带

Page 692
来质的提升。这是因为一个系统的性能好坏，往往由最弱的那一环来
决定，如果在服务端进行阻塞调用的时候有大部分线程都处于挂起状
态，即使程序采用异步调用也不能解决问题。
我们可以将服务端的阻塞调用改为非阻塞调用，当执行IO操作的
时候，该线程并没有挂起，还是处于执行状态，这时该线程还可以去
执行其他代码，不用在这里等待且浪费大量的时间。

Page 693
11。1。3回调地狱
在上一节，我们介绍了在编码层面采用异步的方式来执行IO操
作，在服务器层面让线程改为非阻塞调用，这样就很好地优化了系统
的性能。服务端线程的非阻塞调用已经有比较成熟的方案（我们在上
一节说过），但是在代码层面，我们往往会使用回调来进行IO操作。
但是当处理的逻辑比较复杂时，回调就会一层套着一层，最终出现我
们常见的回调地狱。在大部分语言中，处理异步的时候都会出现回调
地狱。比如，我们将前面的下单逻辑改为异步的方式，这样，如果我
们采用回调的实现方式就会写出如下代码：
public void createOrder(String productNo){
//创建获取订单信息的任务
GetOrderInfoTask task = new GetOrderInfoTask(productNo);
//设置创建订单的回调
task.setCallBack(new CreateOrderBack() {
@Override
public void createOrder(OrderInfo orderInfo) {
//创建插入订单的任务
InsertOrderTask insertOrderTask = new InsertOrderTask(orderInfo
//设置减库存的回调
insertOrderTask.setReduceStoreBack(new ReduceStoreBack() {
@Override
public void reduceStore(String producerNo) {

Page 694
}
/**
}
}
}）；
}
reduce Store(orderInfo.getProducerNo());
}）；
//执行获取订单信息的任务
threadPool.submit(task);
threadPool.submit(insertOrder Task);
*
获取订单信息任务
*/
public static class GetOrderInfoTask implements Runnable{
private String productNo;
private CreateOrderBack callBack;
public getOrderInfoTask(String productNo) {
this.productNo= productNo;
@Override
public void run() {
if(productNo == null || "".equals(productNo)){
return;
}
//获取商品信息

Page 695
}
}
}
public void setCallBack(CreateOrderBack callBack) {
this.callBack = callBack;
**
ProductInfo productinfo = getItemInfo(productNo);
if(productinfo == null){
return;
}
//整理订单信息
Orderinfo orderinfo = convert2OrderInf(productInfo);
//在这里执行创建订单回调任务
callBack.createOrder(orderInfo);
*插入订单任务
*/
}
public static class InsertOrderTask implements Runnable{
private OrderInfo orderInfo;
private ReduceStoreBack reduceStoreBack;
public InsertOrder Task(OrderInfo orderinfo){
this.orderInfo = orderInfo;
@Override
public void run() {
insertRecord (orderInfo);

Page 696
//在这里执行减库存回调
reduceStoreBack.reduceStore(orderInfo.getProducerNo());
}
public void setReduceStoreBack(ReduceStoreBack reduceStoreBack) {
this.reduceStoreBack = reduceStoreBack;
}
}
public interface CreateOrderBack{
void createOrder(Object obj);
}
public interface ReduceStoreBack{
void reduceStore(String producerNo);
}
其实，上面的代码就执行了3步操作：
第一步查询商品的信息；查询完之后执行回调，回调中的逻辑为
整理商品信息，然后将商品信息插入数据库中；插入成功之后再执行
一个回调，在这个回调中减掉库存。可以看到，上面的代码与用同步
实现相比要复杂得多，而且不易维护。当嵌套的层级增多的时候，就
会出现我们常见的回调地狱。

Page 697
11.2 Kotlin的Coroutine
Kotlin在当前的版本引入了协程(Coroutine)来支持更好的异步
操作，虽然当前它仍是一个实验性的语言特性，然而却有着非常大的
价值。利用它我们可以避免在异步编程中使用大量的回调，同时相比
传统多线程技术，它更容易提升系统的高并发处理能力。
在具体介绍协程之前，我们先来探讨下多线程的问题。

Page 698
11。2。1多线程一定优于单线程吗
对于多线程的概念想必你应该不太陌生，为了能在一个程序内或
者说进程内同时执行多个任务，我们引入了多线程的概念。还是基于
我们前面的那个例子，假设这个商城系统在某个时间段内有多个人同
时下单。如果只用一个线程去处理，那么一次只能处理一位用户的请
求，后面的人必须等待。如果某个人处理的时间非常长，那么后面等
待的时间就会很长，这样效率非常低下。现在我们引入了多线程，就
可以同时处理多个用户的请求，从而提高了效率。
前面我们说过，传统的JavaWeb框架所采用的服务器通常是
Tomcat，而Tomcat所采用的就是多线程的方式。当有请求接入服务
器的时候，Tomcat会为每一个请求连接分配一个线程。当请求不是
很多的时候，系统是不会出现什么问题的，一旦请求数多于Tomcat
所能分配的最大线程数时，如果这时有多个请求被阻塞住了，就会出
现一些问题。
我们知道，多线程在执行的时候，只是看上去是同时执行的，因
为线程的执行是通过CPU来进行调度的，CPU通过在每个线程之间快
速切换，使得其看上去是同时执行的一样。其实CPU在某一个时间片
内只能执行一个线程，当这个线程执行一会儿之后，它就会去执行其
他线程。当CPU从一个线程切换到另一个线程的时候会执行许多操作，
主要有如下两个操作：
·保存当前线程的执行上下文；

Page 699
·载入另外一个线程的执行上下文。
注意，这种切换所产生的开销是不能忽视的，当线程池中的线程
有许多被阻塞住了，CPU就会将该线程挂起，去执行别的线程，那么
就产生了线程切换。当切换很频繁的时候，就会消耗大量的资源在切
换线程操作上，这就会导致一个后果———采用多线程的实现方式并
不优于单线程。

Page 700
11。2。2协程：一个更轻量级的“线程”
在前面一节中我们说过，当线程过多的时候，线程切换的开销将
会变得不可忽视。那么怎么去解决线程切换所带来的弊端呢?在
Kotlin中，我们引入了协程，在具体介绍Kotlin的协程之前，我们先来
看看什么是协程。
协程并不是一个非常新的概念，它早在1963年就已经被提出来
了。
协程是一个无优先级的子程序调度组件，允许子程序在特定的地方挂
起恢复。线程包含于进程，协程包含于线程。只要内存足够，一个线
程中可以有任意多个协程，但某一时刻只能有一个协程在运行，多个
协程分享该线程分配到的计算机资源。
通过上面的概念你可能对协程有了一点模糊的了解。我们先来看
一个简单的例子：
import kotlinx.coroutines.experimental.*
fun main(args: Array<String>) {
GlobalScope.launch { // 在后台启动一个协程
}
delay（1000L）//延迟1秒（非阻塞）
println("World!") // 延迟之后输出
println（"Hello，"）//协程被延迟了1秒，但是主线程继续执行

Page 701
}
Thread。sleep（2000L）//为了使JVM保活，阻塞主线程2秒钟（若将这段代
上面就是Kotlin中最简单的协程了。我们首先通过launch构造了
一个协程，该协程内部调用了delay方法，该方法会挂起协程，但是
不会阻塞线程，所以在协程延迟1秒的时间段内，线程中的“Hello，”
会被先输出，然后“World!”才会被输出。
通过上面的例子我们可以看出，协程与线程非常类似。那么为什
么我们说协程是轻量级的线程呢?它又是如何来帮助我们解决前面所
提出的问题的呢?我们知道，线程是由操作系统来进行调度的，前面
说过，当操作系统切换线程的时候，会产生一定的消耗。而协程不一
样，协程是包含于线程的，也就是说协程是工作在线程之上的，协程
的切换可以由程序自己来控制，不需要操作系统去进行调度。这样的
话就大大降低了开销。接下来我们就通过一个简单的例子来看一下，
采用协程为何能够降低开销。
import kotlinx.coroutines.experimental.*
fun main(args: Array<String>) = runBlocking {
repeat（100_000）{
launch {
}
}
println("Hello")

Page 702
}
在上面的代码中，我们启动了10万个协程去执行了一个输出
66
Hello”的操作，当我们执行这段代码之后，“Hello”就会被陆续地
打印出来。但是，如果我们启动10万个线程去做的话，就可能会出
现“ out of memory”的错误了。

Page 703
11。2。3合理地使用协程
在上一节中我们了解到了协程的一些优势，也简单地接触到了协
程。但是你可能对于Kotlin中的协程还是比较陌生，比如什么时候该
用什么方法，如何合理地创建一个协程等。那么本节我们将会通过一
些例子来详细地了解一下协程。
1.launch与runBlocking
在上一节中，我们实现了一个Kotlin中最简单的协程：
import kotlinx.coroutines.experimental.*
fun main(args: Array<String>) {
launch {
}
}
//在后台启动一个协程
delay（1000L）//延迟1秒（非阻塞）
println("World!") // 延迟之后输出
println（"Hello，"）//协程被延迟了1秒，但是主线程继续执行
Thread。sleep（2000L）//为了使JVM保活，阻塞主线程2秒钟（若将这段代
我们给出这个例子主要是为了说明协程与线程的相似之处。其实
上面的代码中存在着一些不合理的地方。这是我们既使用了delay方
法又使用了sleep方法，但是：

Page 704
·delay只能在协程內部使用，它用于挂起协程，不会阻塞线程；
·sleep用来阻塞线程。
混用这两个方法会使得我们不容易弄清楚哪个是阻塞式的，哪个
又是非阻塞式的。为了改良上述实现方式，我们引入runBlocking：
import kotlinx.coroutines.experimental.*
fun main(args: Array<String>) = runBlocking {
launch {
}
}
delay(1000L)
println("World!")
println("Hello,")
delay(2000L)
在上面的代码中,我们利用runBlocking将整个main函数包裹起来
了，这里我们就不再需要使用sleep方法，而是全部用非阻塞式的
delay方法。但是运行结果与上面一样。通过这两个例子，我们认识
了两个函数— -launch与runBlocking。这两个函数都会启动一个协程,
不同的是,runBlocking为最高级的协程,也就是主协程,launch创建
的协程能够在runBlocking中运行（反过来是不行的）。所以上面的代
码可以看作在一个线程中创建了一个主协程，然后在主协程中创建了
一个输出为“World!”的子协程。

Page 705
66
需要注意的是，runBlocking方法仍旧会阻塞当前执行的线程。
2。协程的生命周期与join
在前面的代码中，我们在程序的最后都加上了一行这样的代码：
Thread.sleep(2000L)
或者：
delay(2000L)
这样做的原因是为了让程序不要过早地结束。这两行代码的意思
都可以理解为：2秒之后，结束该程序或者说程序在这2秒之內保
活。如果没有这两行代码，那么上面的例子运行之后只会输出
Hello，”，因为主线程没有被阻塞，程序会立即执行，不会等待协程
执行完之后再结束。
可是我们在执行IO操作的时候并不知道该操作要执行多久，比
如：
}
launch {
search()

Page 706
我们要在上面的协程中执行一个查询数据库的操作，但我们并不
知道该查询操作要执行多久，所以没有办法去设定一个合理的时间来
让程序一直保活。为了能够让程序在协程执行完毕之前一直保活，我
们可以使用join：
import kotlinx.coroutines.experimental.*
fun main(args: Array<String>) = runBlocking {
val job = launch {
search()
}
}
println("Hello,")
job.join()
}
suspend fun search() {
delay(1000L)
println("World!")
在上面的代码中，我们定义了一个查询操作（假设该操作为IO操
作），我们不知道该操作会执行多久，所以我们在程序的最后增加了：
job.join()

Page 707
这样程序就会一直等待，直到我们启动的协程结束。注意，这里
的等待是非阻塞式的等待，不会将当前线程挂起。
当然，有时也需要给程序定时，比如我们不需要某个IO操作执行
很长时间，超过一定时间之后就报超时的错误，在这种情况下我们就
不必使用join。
在上面的代码中，还出现了一个关键字：suspend。用suspend
修饰的方法在协程內部使用的时候和普通的方法没什么区别，不同的
是在suspend修饰的方法内部还可以调用其他suspend方法。比如，
我们在上面的search方法中调用的delay就是一个suspend修饰的方
法，这些方法只能在协程內部或者其他suspend方法中执行，不能在
普通的方法中执行。

Page 708
11。2。4用同步方式写异步代码
通过前面几节的介绍，相信你应该知道怎么去使用协程了。你也
了解到了协程可以用来实现非阻塞的程序。说到非阻塞，你肯定会想
到异步，那么本节我们将介绍协程的另外一个特性，就是利用协程来
优雅地处理异步逻辑。
在具体介绍如何用协程处理异步逻辑之前，我们先来看看代码在
协程中的执行顺序是怎样的：
suspend fun searchitemlOne(): String {
delay(1000L)
return "item-one"
}
suspend fun searchitemTwo(): String {
delay(1000L)
return "item-two"
}
fun main(args: Array<String>) = runBlocking<Unit> {
val one = searchitemlOne()
val two = searchitemTwo()
println("The items is ${one} and ${two}")
}

Page 709
在上面的代码中，我们首先定义了两个查询商品的方法，分别是
searchItemlOne与searchitemITwo,然后在主协程中执行这两个方法,
最后输出两个商品的信息。在我们执行这两个查询操作的时候，在协
程内部，这两个方法其实是顺序执行的，也就是说，先执行
searchitemlOne,再执行searchItemlOne,这有点类似我们在11.1.1节
中利用Java实现的同步代码。在这个例子中，顺序执行其实是不合理
的，因为这两个查询操作不会相互依赖，也就是说，第2个查询操作
不需要等第1个查询操作完成之后再去执行，它们的关系应该是并行
的。
为了让上面两个操作并行执行，我们可以使用Kotlin中的async与
await。我们先来看看上面的代码改造之后是什么样子的：
fun main(args: Array<String>) = runBlocking<Unit> {
val one = async { searchItemlOne() }
val two = async { searchltemTwo() }
println("The items is ${one.await()} and ${two.await()}")
}
可以看到，我们将两个查询操作利用async包裹了起来，类似于
我们前面讲过的launch。使用async也相当于创建了一个子协程，它
会和其他子协程一样并行工作，与launch不同的是，async会返回一
个Deferred对象。
Deferred值是一个非阻塞可取消的future,它是一个带有结果的job。

Page 710
我们知道，launch也会返回一个job对象，但是没有返回值。
回到上面的代码，在输出商品的时候，我们用到了await方法，
这是因为这两个商品结果都是非阻塞的future。future的意思是说，将
来会返回一个结果，利用await方法可以等待这个值查询到之后，然
后将它获取出来。
通过使用async与await我们就实现了异步并行的代码。但是在风
格上，上面的代码与同步代码也没有什么区别。我们可以通过对上面
两段代码的执行时间做一个比较来得出结论。
val time = measureTimeMillis {
val one = searchitemlOne()
}
val two = searchitemTwo()
println("The items is ${one} and ${two}")
println("Cost time is ${time} ms")
不使用async与await时的执行结果:
The items is item-one and item-two
Cost time is 2035 ms
接下来,我们使用async与await方法:

Page 711
val time = measureTimeMillis {
val one = async { searchltemlOne() }
val two = async { searchItemTwo() }
println("The items is ${one.await()} and ${two.await()}")
}
println("Cost time is ${time} ms")
执行结果为：
The items is item-one and item-two
Cost time is 1038 ms
可以看到，执行时间几乎缩短了一半。
通过利用协程来异步实现业务逻辑，不仅能够大大节省程序的执
行时间，而且能够提高代码的可读性。比如上面的查询操作都是异步
操作，必须等待这两个商品都被查出来之后才能输出商品信息，按照
以前编写异步逻辑的方法，我们还需要使用回调。现在直接能够用同
步风格的代码来实现异步逻辑了，使得代码的可维护性大大增强了。
在前面我们介绍了Kotlin协程的一些优点。但是协程也不是万能
的，我们也不能去滥用协程。Kotlin的协程还存在一些弊端。这是因
为Kotlin的协程目前还处于实验阶段，在业务逻辑中，尤其是非常重

Page 712
要的业务逻辑中使用它可能会出现一些未知的问题。另外，滥用协程
可能会使得代码变得更加复杂，不利于后期的维护。

Page 713
11。3共享资源控制
这一节我们就来看看并发中的另外一块重要的內容，那就是共享
资源控制。共享资源可以是一个共享变量，或者是数据库中的数据等。
那么如何保证共享资源的正确性，在并发编程中至关重要。下面我们
就来看看具体怎么做。

Page 714
11。3。1锁模式
最直观的办法就是对共享资源加锁。因为前面讲到，一段代码块
可以由多个线程执行，那么存在两个甚至多个线程对共享资源进行操
作，则可能会导致共享资源不一致的问题。比如，一个商品的库存在
一个抢购的活动中由于高并发量可能出现超卖的情况，所以我们需要
对商品库存这种共享资源进行加锁，保证同一时刻只有一个线程能对
其进行读写。Java程序员对如何给代码加锁应该比较熟悉了，最常见
的便是synchronized关键字，它可以作用在方法及代码块上。虽然
Kotlin是基于Java改良过来的语言,但是它没有synchronized,取而代
之,它使用了@Synchronized注解和synchronized()来实现等同的效
果。比如：
class Shop {
val goods = hashMapOf<Long,Int>()
init {
}
goods.put(1,10)
goods.put(2,15)
@Synchronized fun buyGoods(id: Long) {
val stock = goods.getValue(id)
goods.put(id, stock - · 1)
}

Page 715
}
fun buyGoods2(id: Long) {
synchronized(this) {
val stock = goods.getValue(id)
goods.put(id, stock - 1)
}
}
在Kotlin中,使用@Synchronized注解来声明一个同步方法,另
外使用synchronized（）来对一个代码块进行加锁。你可能不喜欢用
synchronized方式来写一个同步代码，因为它在有些时候性能表现很
一般。确实synchronized在并发激烈的情况下，不是一个很好的选择。
但是在实际开发中，我们要根据具体场景来设计方案，比如我们明知
并发量不会很大，却一味地追求所谓的高并发，最终只会导致复杂臃
肿的设计及众多基本无用的代码。软件设计中有一句名言：
过早的优化是万恶之源。
在竞争不是很激烈的情况下，使用synchronized相对来说更加简
单，也更加语义化。
Kotlin除了支持Java中synchronized这种并发原语外,也同样支持
其他一些并发工具,比如volatile关键字,java.util.concurrent.*下面的
并发工具。当然,Kotlin也做了一些改造,比如volatile关键字在Kotlin
中也变成了注解：

Page 716
@Volatile private var running = false
除了可以用synchronized这种方式来对代码进行同步加锁以外，
在Java中还可以用Lock的方式来对代码进行加锁。所以我们试着改造
一下上面的buyGoods方法:
var lock: Lock = ReentrantLock()
fun buyGoods(id: Long) {
}
lock.lock()
try {
val stock = goods.getValue(id)
goods.put(id, stock - 1)
} catch (ex: Exception) {
println("[Exception] is ${ex}")
} finally {
}
lock.unlock()
但是这种写法似乎有如下不好之处：
·若是在同一个类内有多个同步方法，将会竞争同一把锁；
·在加锁之后，编码人员很容易忘记解锁操作；

Page 717
·重复的模板代码。
那么，我们现在试着对它进行改进，提高这个方式的抽象程度：
fun <T> withLock (lock: Lock, action: () -> T): T {
lock.lock()
try{
}
return action()
} catch (ex: Exception) {
println("[Exception] is ${ex}")
} finally {
}
lock.unlock()
withLock方法支持传入一个lock对象和一个Lamada表达式,所以
我们现在可以不用关心对buyGoods进行加锁了，只需要在调用的时
候传入一个lock对象即可。
fun buyGoods(id: Long) {
val stock = goods.getValue(id)
goods.put(id, stock - 1)
}
var lock: Lock = ReentrantLock()

Page 718
withLock(lock, {buyGoods(1)})
Kotlin似乎也想到了这一点，所以在类库中提供了相应的方法。
var lock: Lock = ReentrantLock()
lock.withLock {buyGoods(1)}
上面，我们探讨了如何在Kotlin中更优雅地书写加锁代码。然而
还没有涉及并发性能。现在我们来思考一个场景，前面是一个商家卖
货，而现在是多个商家卖货，所有的顾客购买时都会调用buyGoods
方法。似乎用上面的方式也可以，那么真的合理吗?
其实仔细思考一下，上面的方法并不是一个好的方式。因为不同
商家之间的商品库存并不会有并发冲突，比如从A商家购买衣服和从
B商家购买鞋子是可以同时进行的，但是如果用上面的方式将不会被
允许，因为它同一时刻只能被一个线程调用，从而会导致锁竞争激烈，
线程堵塞直至程序崩溃。
其实解决这个问题的核心就在于如何对并发时最会发生冲突的部
分进行加锁。那么能不能为具体商家的buyGoods进行加锁呢?我们
试着改造一下上面的逻辑：
class Shop (private var goods: HashMap<Long, Int>) {
private val lock: Lock = ReentrantLock()

Page 719
fun buyGoods(id: Long) {
lock.withLock {
}
}
}
class ShopApi {
private val A_goods = hashMapOf<Long, Int>()
private val B_goods = hashMapOf<Long, Int>()
val stock = goods.getValue(id)
goods.put(id, stock - 1)
private var shopA: Shop
private var shopB: Shop
init {
}
A_goods.put(1, 10)
A_goods.put(2, 15)
B_goods.put(1, 20)
B_goods.put(2, 10)
shopA = Shop(A_goods)
shopB = Shop(B_goods)
fun buyGoods(shopName: String, id: Long) {

Page 720
}
when (shopName) {
"A" -> shopA.buyGoods(id) //不同商家使用不同的model处理
"B" -> shopB.buyGoods(id)
else->{}
}
}
val shopApi = Shopapi()
shopApi.buyGoods("A", 1)
shopApi.buyGoods("B", 2)
我们实现了一个简化版本的业务锁分离，只对同一个商家的购物
操作进行加锁，不同商家之间的购物不受影响。当然，为了实现这种
方式，似乎花费了很大的功夫，需要初始化多个Shop。当然也可以
在运行时初始化它们，不过这样就要考虑初始化的线程安全问题。另
外，要是有成千上万个商家，使用when来匹配可能是一个灾难。再
比如，这种方式无法支持异步，所以这种模式还是有很多问题的。但
是现在我们已经可以很清晰地知道如何来改善这种方式：
·独立的一个单元，可以有状态，可以处理逻辑（比如上面的Shop
类）；
·每个单元有独特的标识，且系统中最多只能有一个实例；
·每个单元可以顺序地处理逻辑，不会有并发问题，方法同步是一种
方案，线程安全的消息队列也是一种方案；

Page 721
·最好能支持异步操作，处理成功后可以有返回值。
以上几点是我们完善这个模型所需要的关键点。下面我们就来看
看如何达到要求。

Page 722
11。3。2Actor：有状态的并行计算单元
其实上面我们已经实现了一个简单的、有状态的并行计算单元，
就是Shop类。但是它还有很多缺陷。下面我们就来看一个真正的、
有状态的并行计算单元————Actor。可能很多读者之前都没听说过
Actor,其实Actor这个概念已经存在很久了,它由Carl Hewitt、Peter
Bishop及Richard Steiger在1973年的论文中提出,但直到这种概念在
Erlang中应用后，才逐渐被大家所熟知。而且现在Actor模型已经被应
用在生产环境中，比如Akka（一个基于Actor模型的并发框架）。另
外很多语言也支持Actor模型,比如Scala、Java,包括Kotlin也內置了
Actor模型。其实Actor模型所要做的事情很简单：
·用另一种思维来解决并发问题，而不是只有共享内存这一种方式；
·提高锁抽象的程度，尽量不在业务中出现锁，减少因为使用锁出现
的问题，比如死锁；
·为解决分布式并发问题提供一种更好的思路。
光看概念你可能还是很迷糊，Actor到底是一个什么东西。举个
简单的例子：假定现实中的两个人，他们只知道对方的地址，他们想
要交流，给对方传递信息，但是又没有手机、电话、网络之类的其他
途径，所以他们之间只能用信件传递消息。很像现实中的邮政系统，
你要寄一封信，只需根据地址把信投寄到相应的信箱中，具体它是如
何帮你处理送达的，你就不需要了解了。你也有可能收到收信人的回
复，这相当于消息反馈。上述例子中的信件就相当于Actor中的消

Page 723
息，Actor与Actor之间只能通过消息通信。Actor系统如图11-3所示。
信件
邮箱←
Actor
信件
信件
图11-3Actor系统
邮箱
Actor
信件
Actor
邮箱
看过上面的例子，你似乎知道了Actor是一个怎么样的东西。但
是又很好奇，Actor跟并发又有什么关系?我们还是通过上面这个例
子来讲解。首先使用Actor模式，不同人之间的邮件投递可以并行处
理，反映到应用中，就是可以利用多核的处理器。另外，信件信息是
不可变的，你不能在发出这封信件后又去修改它的内容，同时接收信
件的人是从它的信箱里有序地处理信件，这两点就可以保证消息的一
致性，不再需要使用共享内存。另外，顺序地处理消息，Actor内部
的状态将不会有线程安全问题。

Page 724
现在我们就来尝试使用Actor来解决上面的购物例子，鉴于Kotlin
內置的Actor功能并不是很完善，而且目前只是实验版，并没有加入
正式的Kotlin标准库里,所以这里我们就不讲解Kotlin中内置的Actor
了，感兴趣的读者可以自行学习Kotlin协程库中Actor部分的內容：
https://github.com/Kotlin/kotlinx.coroutines. 1]**÷Œµ**ÚJ
基于Actor的框架— -Akka. Akka
Scala Java, Kotlin
分百兼容Java,所以Akka也可以在Kotlin中使用。使用Akka需要引入
相关的依赖包，使用Maven和Gradle都可，暂时只需要引入核心的
akka-actor包即可。由于Akka是使用Scala编写的,所以这里我们需要
引入Scala的核心包。
(1) Mavent
<dependency>
<groupId>com.typesafe.akka</groupId>
<artifactId>akka-actor_2.12</artifactId>
<version>2.5.14</version>
</dependency>
<dependency>
<groupId>org.scala-lang</groupId>
<artifactId>scala-library</artifactId>
<version>2.12.4</version>
</dependency>

Page 725
(2) Gradlet
compile 'com.typesafe.akka:akka-actor_2.12:2.5.14'
compile 'org.scala-lang:scala-library:2.12.4'
接下来，我们先来实现一个简化版的方案，将购物消息发送给商
家Actor，商家Actor进行减库存操作，并返回一个唯一的订单号，支
持查询当前库存。
，
ShopActor:
import akka.actor.ActorRef
import akka.actor.ActorSystem
import akka.actor.Props
import akka.actor. UntypedAbstractActor
import akka.pattern.Patterns
import akka.util. Timeout
import scala.concurrent.Await
import scala.concurrent.duration.Duration
import java.util.*
class ShopActor(val stocks: HashMap<Long, Int>): Untyped AbstractActor() {
var orderNumber = 1L
override fun onReceive(message: Any?) {
when (message) {

Page 726
}
}
is Action.Buy -> {
val stock = stocks.getValue(message.id)
if (stock > message.amount) {
}
stocks.plus(Pair(message.id, stock - message.amount))
sender.tell(orderNumber, self)
}
orderNumber++
} else {
sender.tell("low stocks", self)
}
is Action.GetStock -> {
sender.tell(stocks.get(message.id), self)
sealed class Action {
data class BuyOrlnit(val id: Long, val userld: Long, val amount: Long, val sl
data class Buy(val id: Long, val userld: Long, val amount: Long): Action()
data class GetStock(val id: Long): Action()
data class GetStockOrInit(val id: Long, val shopName: String, val stocks: M
}
class ManageActor : UntypedAbstractActor() { //ShopActor
override fun onReceive(message: Any?) {
when (message) {

Page 727
}
}
}
is Action.BuyOrlnit -> getOrInit(message.shopName, message.stocks)
is Action.GetStockOrlnit -> getOrInit(message.shopName, message.st
}
fun getOrlnit(shopName: String, stocks: Map<Long, Int>): ActorRef {
return context.findChild("shop-actor-${shopName}").orElseGet { context.
ShopActor↑R, stocks orderNumber,
代表库存和订单号。另外，我们定义了一个sealedclass，用它来表
示用户请求行为。同时ShopActor内部有一个onReceive方法,根据用
户的不同请求来做不同的处理。最后，我们定义了一个ManageActor，
由它来负责管理和初始化ShopActor。现在我们尝试来使用这个这个
方案：
fun main(args: Array<String>) {
val stocksA = hashMapOf(Pair(1L, 10), Pair(2L, 5), Pair(3L, 20))
val stocksB = hashMapOf(Pair(1L, 15), Pair(2L, 8), Pair(3L, 30))
val actorSystem = ActorSystem.apply("shop-system") //Actor
val manageActor = actorSystem.actorOf(Props.create(ManageActor::class
val timeout = Timeout(Duration.create(3, "seconds"))
val resA = Patterns.ask(manageActor, Action.GetStockOrInit(1L, "A", stock

Page 728
val stock = Await.result(resA, timeout.duration())
println("the stock is ${stock}")
val resB = Patterns.ask(manageActor, Action.BuyOrlnit(2L, 1L, 1,"B", stock
val orderNumber = Await.result(resB, timeout.duration())
println("the orderNumber is ${orderNumber}")
}
result:
the stock is 10
the orderNumber is 1
这里我们首先初始化了一个Actor系统，然后创建了
ManageActor，同时模拟了两个用户的操作，一个读取库存操作，
个购买商品操作。到这里，整个例子已经完成得差不多了。可能很多
读者看到这一堆代码感觉有点压力，所以这里我们将上面的结构用图
11-4表示出来。

Page 729
用户行为
Buy
Buy
ShopActorA
返回结果返回结果，
ManagerActor)
orderNumber
用户行为
GetStock
stock
GetStock
ShopActorB
图11-4基于Actor的购物系统
Actor系统
通过上图你应该能大致清楚了Actor这种设计背后的思想，就是
将一个个行为分解成合适的单位来进行处理。那么这种Actor方案是
如何保证共享资源的正确性的呢?
其中主要的一点是Akka中的Actor共享内存设计理念与传统方式
的不同，Actor模型提倡的是：通过通信来实现共享内存，而不是用
共享内存来实现通讯。这点是与Java解决共享内存最大的区别。举个
例子，在Java中我们要去操作共享内存中的数据时，每个线程都需要
不断地获取共享内存的监视器锁，然后将操作后的数据暴露给其他线
程访问使用，用共享内存来实现各个线程之间的通信。而在Akka
中，我们可以将共享可变的变量作为一个Actor内部的状态，利用
Actor模型本身串行处理消息的机制来保证变量的一致性。

Page 730
当然，要使用该机制也必须满足以下两条原则：
·消息的发送必须先于消息的接收；
同一个Actor对一条消息的处理先于对下一条消息的处理。
第2个原则很好理解，就是上面我们说的Actor内部是串行处理消
息，这样在Actor内部就保证不会出现并发问题。那我们来看看第1个
原则，为什么要保证消息的发送先于消息的接收?这里就需要先介绍
一下Actor的结构。每个Actor都有一个属于自己的MailBox,可以理解
为用于存放消息的队列，比如一下子向一个Actor发送了几十万条消
息，则Actor会将这些消息先存储在MailBox中，然后依次进行处理。
那么这与消息的发送和接收有什么联系呢?
其实，上面这种方式如果没有保证的话则会出现问题，因为这里
面存在两个操作，一个是向MailBox中写入消息，一个是从MailBox中
读取消息，它们不是一个原子操作，可能会出现一条消息在被写入
MailBox中还没结束的时候，就被Actor读取走了，这就有可能出现一
些未知的情况。所以必须保证消息的发送先于消息的接收，简单来说
就是消息必须先完整地写入MailBox才能被接收处理。那么MailBox必
须是线程安全的。虽然我们在使用层面对此没有感知，但是我们还是
需要了解一下MailBox背后是用什么方式实现的，这是Actor能处理并
发问题的核心关键。
首先，MailBox是一个存储消息的队列，而且消息只会添加在队
列的尾部，取消息是在队列的头部，那么这里可以使用
LinkedBlockingDeque来作为MailBox的基础结构,它是基于双向链表

Page 731
实现的，而且也是线程安全的。但是需要说明的一点是，
LinkedBlockingDeque内部还是使用Lock来保证线程安全的。其实还
有其他队列也适合这种场景,比如ConcurrentLinkedQueue,它内部
使用CAS操作来保证线程安全。但是Akka并没有采用这两种方案，
而是自己实现了一个AbstractNodeQueue,有兴趣的读者可以去看一
下源码:https://github.com/akka/akka/blob/master/akka-actor/src/main/
java/akka/dispatch/AbstractNodeQueue.java。从源码可以看出,
AbstractNodeQueue是一个功能更加明确的队列,是专门为Actor这种
需求所设计的。
以上更多的是探讨了使用Actor来设计并发方案的思路及它的基
本模型原理，关于例子中的Akka的知识点没有过多阐述，推荐大家
可以去了解学习一下这个:https://github.com/akka/akka。
有人会说，既然Actor这么强大，那是不是说使用Actor就能解决
并发问题?其实不是，使用Actor这种方案并不一定就会比其他方案
在并发性能上表现得更加优异，每种场景都有最适合自己的方案，这
里更多的是在并发方案设计上的探讨，跳出原有思维，去看看别的解
决方案。其实Actor模型这种思想简单概括来说就是分而治之，把一
个大任务分解成一个个独立的小任务，依靠多核处理器以及多线程来
到达整体的最优。
现在我们回过头来思考一下上面的设计方案，其实它少了一个核
心的部分，就是数据的持久化。前面例子中我们为了方便讲解而使用
Map来存储数据，其实这是有问题的，因为它是存储在内存中的，要
是什么时候系统宕机或者程序崩溃，那么数据就会丢失。这样肯定就

Page 732
无法在生产环境中使用，所以我们需要把数据持久化，比如存储在数
据库中。这个思路很简单，但是又会带来一个问题，本来我们在逻辑
上已经将业务分解了，若是最后又回归到数据库单个表的竞争，那么
前面所有的花费都是徒劳。一般情况下，在系统优化得当的情况下，
并发的瓶颈就在于数据库，主要有两方面：
·数据库的连接和关闭，网络传输需要一定时间；
一些不恰当的或者事务需要锁表的SQL，如果大量执行会导致数据
库执行变慢，甚至崩溃。
以往我们的设计都是将对象的状态实时更新到数据库中，比如商
品被购买一件后便修改数据库里相应的库存数量，而且我们还需要经
常去读取库存，这也就是我们通常所说的CRUD模式。这种模式很好
理解，也很简单，在并发不激烈的情况下并不会有什么问题。但当并
发激烈的时候这样的方案会给数据库带来很大的压力，频繁的锁表事
务操作不仅会让SQL的执行变慢、失败，还会影响整个系统的吞吐量，
甚至引起系统的崩溃。那么面对这种情况，是否有别的方案能解决这
个问题?
我们来试想一下能不能采用读写分离这种思想，最容易想到的是
主从数据库。但是这种方案还是有一些问题，一来避免不了修改库存
时候的并发竞争，二来数据同步也需要大量的消耗。其实我们能运用
另一种方式来解决这个问题,那就是CQRS(Command Query
Responsibility Segregation)架构。下面我们就来看看它到底是一种
怎样的设计。

Page 733
11。4CQRS架构
CQRS是一种命令与查询职责分离的设计原则，简单来说也是一
种读写分离的设计方案。但它与我们普通方式的读写分离有一些区别，
主要体现在写方面，它不再是对记录进行不断修改，而是一种事件溯
源的思维方式。举个简单的例子，它跟数据库备份所使用的binlog方
案很像，数据库会将有修改状态行为的SQL执行情况一条一条地记录
在binlog日志中，利用这些记录便能推导出最终的状态。下面我们就
来一探CQRS的背后。

Page 734
11。4。1EventSourcing事件溯源--记录对象操作轨迹
事件溯源这个名词听起来可能不好理解，其实它的原理很简单，
就是根据一系列事件推导出对象的最新状态。举个简单的例子，假如
你购买一件商品，那么这件商品的库存应该减一，但是你突然又不想
买了，进行了退货，那么这时商品库存又要加一。一来一回商品的库
存并没有发生变化，按照普通的方式你会对数据库中的库存来进行状
态的修改，但是这种方式要是不借助其他记录，我们将无法知晓在该
对象上发生了什么事。所以比较合理的方式应该是记录每次发生在该
对象上的状态变更事件，根据这个事件来推导出对象的最新状态。这
便是事件溯源。
一开始你可能并不容易从CURD模式跳出来，接受一种新的思维
模式，就像你本来用面向对象的思维方式写代码，一下子让你用函数
式的思维去写，肯定会不适应。所以我们先来看一下事件溯源中最关
键的几点：
·以事件为驱动，任何的用户行为都是一种事件，比如上面说的购买
商品、退货等；
·存储所有对于对象状态会有影响的事件，这一点至关重要，因为我
们在程序恢复或者数据校验的时候都需要它；
·用于查询或者显示的视图数据不一定要持久化，比如我们将对象的
状态数据存放在内存中。
第1点很好理解，在前面Actor的例子中我们已经这么做了。

Page 735
sealed class Action {
}
我们将事件行为都声明在Action类中，通过这种方式就可以将业
务行为分成各种事件。比如现在定义一个退货事件：
sealed class Action {
data class Return(val id: Long, val userld: Long, val amount: Long):Action
}
利用事件驱动的方式构建业务逻辑，不仅语意上更加清晰，同时
还天然支持异步操作。使用异步架构可以较为容易地提升程序的吞吐
量。
在讲第2点之前，我们需要来了解两个概念：聚合，聚合根。
聚合顾名思义是一系列对象的集合。比如一个商家里面有商品、
优惠券等，它们的集合就可以看作一个聚合。而聚合根属于这个聚合
中可以被外部访问的元素，比如这里商家便是一个聚合根，经过它我
们才能查看它其中的商品、优惠券等。图11-5所示可用来帮助大家理
解。

Page 736
商品
商家
聚合根
优惠券
聚合
图11-5聚合与聚合根示例
为什么说理解聚合和聚合根很重要呢?因为要结合CQRS、事件
溯源这些设计，我们就要用一种新的思维模式去设计我们的业务，只
能通过聚合根来操作聚合中其他对象的状态，比如只能通过商家去修
改商品的库存，而不允许直接修改库存。这么说可能有点抽象，其实
很简单，就是你原来可能直接在数据库中更改一下商品的库存便可以
了，而现在你需要向商家发一条修改商品库存的信息，然后它会生成
一个库存修改事件，最后才会修改好库存（修改聚合里面对象的状态

Page 737
也可以修改数据库中的记录）。那么本来简单的一个操作反而变复杂
了，它有什么益处呢?
我们以传统的方式来试想一下，假设商家修改了商品库存，但是
后来发现修改错了，一来可能忘记了修改的内容无法回滚，二来即使
可以回滚，付出的代价也是极大的，因为它需要回滚所有与商品库存
有关的操作。数据回滚的操作在现实环境中还是存在的，比如银行、
交易所的业务，如果哪一段时间出现了重大异常，可能就需要回滚数
据。而如果通过一个聚合根来修改聚合中对象的状态，那么这一切将
会变得容易。我们会记录聚合所有的状态更改事件，可以根据这些事
件恢复到任一时刻聚合的状态。
那么这种方式有什么缺点吗，当然也有，因为需要保存每次修改
状态的事件，将会占用大量的存储空间。而且在进行状态恢复时，需
要回放以前所有的事件，这也会有一定的消耗。当然这个问题我们可
以通过引入快照解决。
上面我们更多探讨的是一种设计，可以算是领域驱动设计的一部
分。那么这种设计为什么能改进并发时遇到的问题呢?
前面说到，并发最大的困难就在于对共享资源的竞争，在前一节
我们已经试着将竞争的部分进行分解，达到一个适合的单位。但是某
个具体单位的竞争还是可能会激烈，所以尝试着从业务角度进行优
化，比如将修改和查询分开。但是我们并没有使用传统的思维模式来
解决这个问题，而是通过引入CQRS架构，结合领域驱动设计来解决
这个问题。比如，我们可以将持久数据和视图数据分开存储，再比如，

Page 738
视图数据可以存在内存数据中，提高查询效率。另外，通过保存所有
的状态更改事件使内存中的数据是可靠的，比如减少库存数量的时
候，不必查询数据库中的数据，直接使用內存中的数据即可。同时，
因为事件是不断被添加而且不能修改，所有我们可以选取写效率高的
DB来存储事件，比如cassandra。通过这些优化将会提升程序的性能。
到这里,相信大家对CQRS以及Event Sourcing这种设计思维应
该有所了解了。那么为什么会讲这种模式呢?因为它能跟Kotlin以及
Actor结合得很好。CQRS以及Event Sourcing中最重要的两部分就是
事件与聚合的划分，首先事件我们可以通过Kotlin的Dataclass来实
现，而将一个Actor看成聚合更是一个完美的应用，每个Actor维护自
身的状态，又简洁又高效。接下来我们就将上面的购物例子改造成基
于Kotlin和Actor的CQRS架构。

Page 739
11.4.2 Kotlin with Akka PersistenceActor
前面实现的Actor例子似乎已经应用了各种领域事件，比如购物
事件、查询库存事件。但是我们发现其中有一个很大的欠缺，那就是
我们并没有持久化任何的Actor状态更改事件。那么假如程序出错甚
至崩溃，我们将无法恢复Actor的状态，数据将会出错。既然这样我
们就有必要持久化状态更改事件的机制。Akka为我们提供了简单又
高效的方式,那就是PersistenceActor。顾名思义,PersistenceActor
就是支持持久化的Actor，也就是说它的状态是可靠的。那么
PersistenceActor与普通的Actor又有什么区别呢?
使用PersistenceActor首先需要继承AbstractPersistentActor类。
我们首先来看一下它的关键结构：
fun persistenceld()
fun createReceive Recover()
fun createReceive()
这几个方法是继承的时候必须实现的，其中createReceive方法
与前面例子Actor中的onReceive类似，都是用来接收处理消息的，只
不过是语法上的一点差别，与普通Actor关键的差别在于多了
persistenceld和createReceiveRecover方法。前面我们在CQRS架构的
设计中说过，划分一个聚合是一个关键的步骤，而在这里每一个
Actor都是一个聚合，那么它必须要有一个聚合标识，这个便是

Page 740
persistenceld的用处。简单地说,每个Actor的persistenceld都要不同,
这样才能标识持久化的事件到底是属于哪个聚合的，对Actor的状态
恢复起到了至关重要的作用。那么Actor的状态恢复又是怎么实现的
?
createReceive Recover, createReceiveRecover
方法会在每次Actor重新启动的时候执行回放事件恢复Actor的内部状
态。下面我们就用PersistenceActor来优化上面使用Actor实现的购物
例子,另外使用PersistenceActor需要添加相应的依赖和配置。
依赖如下：
compile group: 'com.typesafe.akka', name: 'akka-persistence_2.12', version: "
compile group: 'org.iq80.leveldb', name: 'leveldb', version: '0.10'
compile group: 'com.twitter', name: 'chill-akka_2.12', version: '0.9.2'
application.conf:
akka.persistence.journal.plugin = "akka.persistence.journal.leveldb"
akka.persistence.snapshot-store.plugin = "akka.persistence.snapshot-store.lc
akka.persistence.journal.leveldb.dir="log/journal"
akka.persistence.snapshot-store.local.dir="log/snapshots"
akka.actor.serializers {
kryo = "com.twitter.chill.akka.AkkaSerializer"
}
akka.actor.serialization-bindings {

Page 741
}
"scala.Product" = kryo
"akka.persistence.PersistentRepr" = kryo
这个配置的主要目的是设置持久化事件的存储方式。这里使用
Akka默认提供的leveldb的方式，当然你也可以使用其他的存储方
式,比如Cassandra、Redis、MySQL等。一般推荐写性能较好的DB,
因为它的基本需求就是写入事件。另外，我们需要配置持久化事件时
使用的序列化方式，因为我们知道存储的事件将会非常多，所以需要
将事件序列化后再进行存储。减少存储事件的大小，这里使用了kryo，
当然你也可以使用其他的序列化方式。下面就是利用
PersistenceActor实现的购物例子:
import akka.actor.ActorRef
import akka.actor.ActorSystem
import akka.actor.Props
import akka.actor. Untyped AbstractActor
import akka.pattern.Patterns
import akka.persistence.Abstract PersistentActor
import akka.util. Timeout
import scala.concurrent.Await
import scala.concurrent.duration.Duration
import java.util.HashMap
class ShopStateActor(val shopName: String,var stocks: HashMap<Long, Int>

Page 742
override fun persistenceld() = "ShopStateActor-${shopName}"
var orderNumber = 1L
override fun createReceive Recover(): Receive receiveBuilder().match(St
fun recoverReduceStock(evt: ShopEvt.ReduceStock) {
val stock = stocks.getValue(evt.id)
stocks.plus(Pair(evt.id, stock - evt.amount))
orderNumber = evt.orderNumber
orderNumber++
//self.tell(viewData, viewActor)viewActor
}
fun persistReduceStockAfter(evt: ShopEvt.ReduceStock) {
val stock = stocks.getValue(evt.id)
orderNumber++
}
stocks.plus(Pair(evt.id, stock - evt.amount))
sender.tell(orderNumber, self)
//self.tell(viewData, viewActor)viewActor
}
fun buyProcess(cmd:Action.Buy) {
val stock = stocks.getValue(cmd.id)
if (stock > cmd.amount) {
persist(ShopEvt.Reduce Stock(cmd.id, cmd.userld,cmd.amount,ordert
} else {
sender.tell("low stocks", self)
}

Page 743
override fun createReceive(): Receive = receiveBuilder().match(Action.Buy
}
sealed class ShopEvt {
object Snapshot : ShopEvt()
data class SnapshotData(val orderNumber: Long, val stocks: Map<Long, Ir
data class ReduceStock(val id: Long, val userld: Long, val amount: Long, v
data class AddStock(val id: Long, val amount: Long): ShopEvt()
}
sealed class Action {
data class BuyOrlnit(val id: Long, val userld: Long, val amount: Long, val s
data class Buy(val id: Long, val userld: Long, val amount: Long): Action()
data class GetStock(val id: Long): Action()
data class GetStockOrInit(val id: Long, val shopName: String, val stocks: M
}
class ManageStateActor : UntypedAbstractActor() {
override fun onReceive(message: Any?) {
when (message) {
}
is Action.BuyOrlnit ->
{print(message)
getOrInit(message.shopName, message.stocks).forward(Action.Buy
is Action.GetStockOrlnit -> getOrInit(message.shopName,message.st
}
fun getOrlnit(shopName: String, stocks: Map<Long, Int>): ActorRef {
return context.findChild("shop-actor-${shopName}").orElseGet { context.

Page 744
}
fun main(args: Array<String>) {
val stocksB = hashMapOf(Pair(1L, 15), Pair(2L, 8), Pair(3L, 30))
val actorSystem = ActorSystem.apply("shop-system") //
}
}
val manageStateActor = actorSystem.actorOf(Props.create(ManageStateA
val timeout= Timeout(Duration.create(3, "seconds"))
val resB = Patterns.ask(manageStateActor, Action.BuyOrlnit(2L, 1L, 1,"B",
val orderNumber = Await.result(resB, timeout.duration())
println("the orderNumber is ${orderNumber}")
代码看起来比普通Actor实现的方式稍微复杂点，但是仔细来
看，主要多了两个关键的步骤。我们来看一下：
}
fun buyProcess(cmd:Action.Buy) {
val stock = stocks.getValue(cmd.id)
if (stock > cmd.amount) {
persist(ShopEvt.Reduce Stock(cmd.id, cmd.userld,cmd.amount,orderNui
} else {
sender.tell("low stocks", self)
}

Page 745
这个是我们前面讲过的EventSouring的关键部分，它存储了改变
Actor状态的所有事件,比如这里是ReduceStock事件。另外,
PersistentActor中的persist提供了持久化事件成功后的回调,我们可
以在回调中修改Actor的状态，向其他Actor发送消息，或者存储视图
数据等操作。另外一个关键的部分就是事件的回放：
override fun createReceiveRecover(): Receive = receiveBuilder()
.match(ShopEvt.ReduceStock::class.java,
this::recoverReduceStock)
.build()
fun recoverReduceStock(evt: ShopEvt.ReduceStock) {
val stock = stocks.getValue(evt.id)
stocks.plus(Pair(evt.id, stock - evt.amount))
orderNumber = evt.orderNumber
orderNumber++
//self.tell(viewData, viewActor) 视图数据发送给viewActor用于查询
}
在Actor重启的时候，会回放所有的持久化事件，比如上面说的
ReduceStock事件,然后可以根据这些事件来恢复Actor关闭或者出错
时候的状态。前面我们说过，这种方式在Actor恢复的时候会回放大
量的事件，导致恢复时间过长。为了解决这个问题，我们可以引入
Actor快照存储的方式。比如：

Page 746
fun saveSnapshot() {
saveSnapshot(ShopEvt.SnapshotData(orderNumber, stocks))
}
override fun createReceive(): Receive = receiveBuilder()
.match(Action.Buy::class.java,
this::buyProcess)
.match(ShopEvt. Snapshot::class.java,this::saveSnapshot)
.build()
我们可以隔一段时间发送ShopEvt.Snapshot消息要求Actor进行
快照保存。有了快照保存之后，便可以利用快照来恢复Actor的状态
了。
override fun createReceiveRecover(): Receive = receiveBuilder().match(Shop
fun recoverSnapshotData(evt: ShopEvt.SnapshotData) {
stocks = evt.stocks
orderNumber = evt.orderNumber
}
Actor恢复的时候会优先选用快照恢复，然后再利用事件恢复。
利用这种机制就能大大减少Actor重启恢复状态时候的消耗了。
以上的部分主要讲解了如何利用PersistentActor来实现CQRS架
构，其中关于查询的部分并没有深入讲解。其实实现查询的方案有很
多种，比如将需要的查询数据发送给另一个Actor或者将数据存储在

Page 747
读效率高的DB中,也可以使用Akka自身提供的 akka-persistence-
query。当然,需要注意的一点是,我们在使用Event sourcing和
CQRS这种架构来设计系统的时候，一定要根据具体场景来设计，比
如系统是写要求高还是读要求高，根据不同的需求采用不同的方案。
假设我们对写入的要求很高，如上面例子中一次事件执行一次写入，
即使真正写入DB的时间非常短，但是每次网络通信的消耗也非常大，
这时我们就可以利用批量存储这种方式来改进。PersistentActor也提
供了这种方式，那就是persistAll，通过它我们可以批量地持久化事件。
比如：
persistAll (listOf(event...), processAfterPersist)
当然使用批量持久化后，逻辑会变得稍微复杂一点，比如在批处
理的时候减库存就不能只依靠上面那种方式，因为被减少的库存并没
有真正持久化到DB中。这里我们可以通过引入一个临时变量来解决
这个问题。因为Actor是串行处理的，所以我们不必担心这个变量会
有线程安全问题。
现在来回顾一下我们是如何一步一步解决多商店购物并发时的线
程安全问题，并不断改进方案的。首先，从最简单也最熟悉的方式
-业务加锁开始，从整个方法加锁到局部加锁，学习了利用Kotlin
的简洁语法优化加锁代码，并引出了Actor模型，一种有状态的并行
计算单元，利用Actor我们可以实现业务上的无锁并发；接着，在
Actor的基础上,介绍了CQRS架构以及Event sourcing的思维方式;

Page 748
最后,利用Akka的PersistentActor实现了最终的版本。从整个过程下
来，不断地面对问题，然后思考用一种好的方案去解决它。相信大家
不仅了解了这些概念设计，更多的是学会跳出原有思维，拥抱不一样
的思维方式。

Page 749
11。5本章小结
（1）同步异步与阻塞非阻塞
同步异步指的是一个行为，比如同步操作。当我们执行IO操作的
时候，在代码层面我们需要主动去等待结果，直到结果返回。而阻塞
与非阻塞指的是一种状态，比如阻塞，当执行IO操作的时候，线程处
于挂起状态，就是该线程没有执行了。所以同步不只是阻塞的，同步
也可以是非阻塞的。比如，我们在执行同步代码块的时候，线程可以
不阻塞，而是一直在后台运行。
（2）异步非阻塞能够提高效率
代码采用异步编写的时候，若程序执行IO操作，可以先去执行其
他线程的代码，不用在这里一直等着，当有结果返回的时候，程序再
回来执行该代码块，这样就节省了许多资源。将服务端的阻塞调用改
为非阻塞调用，当执行IO操作的时候，该线程并没有挂起，还是处于
执行状态。该线程还可以去执行其他代码，不用在这里等待，从而避
免浪费大量的时间。
（3）多线程不一定优于单线程
多线程之间切换的开销是不容忽视的，当线程池中的线程有许多

Page 750
被阻塞住了，CPU就会将该线程挂起，去执行别的线程。这样就产生
了线程切换。当切换的次数非常多的时候，就会消耗大量的资源。
（4）协程可以看成是一个轻量级的线程
协程在某些方面与线程类似，比如挂起、切换等。但是协程是包
含于线程的，也就是说协程是工作在线程之上的。协程的切换可以由
程序自己来控制，不需要操作系统去进行调度，这样就减少了切换所
带来的开销。
(5) launch与runBlocking
runBlocking为最高级的协程,也就是主协程,launch创建的协程
能够在runBlocking中运行（反过来是不行的）。
(6)async和await
我们可以利用async来将协程执行的操作异步化，采用async会返
回一个Deferred对象，该对象是一个非阻塞可取消的future，我们可
以通过awai方法来取出这个值。
（7）并发线程安全问题
学习通过锁来保证在并发时共享资源的一致性，并利用Kotlin的
简洁语法优化加锁代码，在代码层面简化加锁代码带来冗余代码量。
(8) Actor
了解Actor的基础结构以及设计思维，探究为什么使用Actor能在

Page 751
业务代码层面实现无锁并发，并结合Akka进行实践练习。
（9）CQRS架构
了解CQRS架构的原理，与通常的CRUD架构进行比较，并讲解
了CQRS架构中重要的两个设计,领域模型设计以及Event sourcing,
简要说明这两个设计的基本原理。
(10) Kotlin with PersistentActor
如何使用Akka的PersistentActor来实现CQRS架构设计,并讲解
了它的基础结构和实现原理，以及一些实践上的优化。

Page 752
遨游篇
Kotlin实战
·第12章 基于Kotlin的Android架构
·第13章开发响应式Web应用

Page 753
第12章基于Kotlin的Android架构
在移动端发展的早期，我们通常会提及App的架构，此时总会有
些大材小用的感觉，因为移动端并没有复杂的业务处理、高并发等场
景，甚至我们需要做的只是简单地“将数据展示在屏幕上”。但是随
着移动端的飞速发展，产生了一些问题：
·移动端App中业务逻辑越来越复杂，用户渴望更好的体验及更新颖的
功能；
·不断地迭代让项目结构复杂化，维护成本越来越高。
所以，我们需要一个良好的架构模式，拆分视图和数据，解除模
块之间的耦合，提高模块內部的聚合度，让系统更稳健。本章谈论的
架构，即是对客户端的代码组织/职责进行的划分。
我们知道,自从在Google IO大会被提名后,Kotlin就在Android中
迅速发展。作为Kotlin的学习者，相信你也对其在Android架构中发挥
的作用十分感兴趣。在本章中，我们将会以传统的MVC及当下流行
的MVP、MVVM架构为例，为读者展现Kotlin在实现这些架构时的魅

Page 754
力。
除此之外，本章还会为大家介绍一种比较新颖的事物——基于
单向数据流的Android架构。有前端经验的读者已经对其有所体会，
在iOS中，这种架构也已经获得较高的关注。我们会基于一个名为
ReKotlin的开源项目来实现一个完整的Android架构。

Page 755
12。1架构方式的演变
首先我们来回顾一下近几年内移动端架构模式的演变。本章将其
分为MV*与单向数据流两大类。由于Kotlin在Android中的特殊地位，
以下內容我们都将以Android架构为例。

Page 756
12。1。1经典的MVC问题
Android架构的鼻祖，自然是经典的MVC了。在用户界面比业务
逻辑更容易发生变化的时候，客户端和后端开发需要一种分离用户界
面功能的方式，这时候，MVC模式应运而生。MVC对应Model、View、
Controller,如图12-1所示。
·Model（数据层）：负责管理业务逻辑和处理网络或数据库API。
·View（视图层）：让数据层的数据可视化。在Android中对应用户交
互、UI绘制等。
·Controller（逻辑层）：获得用户行为的通知，并根据需要更新Model。
数据改变
用户操作
Model
更新数据
Controller
数据改变后通知绑定的视图
图12-1经典的MVC架构
更新视图
View

Page 757
很多人对于经典的MVC架构中的Model一直存在误解，认为其代
表的只是一个实体模型。其实，准确来说它还应该包含大量的业务逻
辑处理。相对而言,Controller只是在View和Model层之间建立一个桥
梁而已。
我们将以上结构细分如下。
·Model层：数据访问（数据库、文件、网络等）、缓存（图片、文件
等)、配置文件(shared perference)等;
·View层：数据展示与管理、用户交互、UI组件的绘制、列表Adapter
等；
·Controller层：初始化配置（定义全局变量等）、数据加工（加工成
UI层需要的数据）、数据变化的通知机制等。
当你在Stack Overflow中搜索类似“ 如何在Android应用中使用
Activity”的问题时，你会发现最高频的答案就是：一个Activity既是
View又是Controller。这看起来好像对新手非常不友好，但是当时解
决的重点问题是使Model可测试。这也让很多开发者在项目结构中出
现了很多Free Style的代码,导致Activity中代码量庞大并且难以维
护。
经过大量时间与项目的验证，我们更加明确：Activities、
Fragments 和 Views都应该被划分到MVC的View层中,而不是
Controller或Model中。
1。MVC的优势

Page 758
Model类没有对Android类的任何引用，因此可以直接进行单元测
试。Controller不会扩展或实现任何Android类,并且应该引用View的
接口类。通过这种方式，也可以对控制器进行单元测试。如果View
遵循单一责任原则，那么它们的角色就是为每个用户事件更新
Controller，只显示Model中的数据，而不实现任何业务逻辑。在这种
理想的作用下，UI测试应该足以覆盖所有的View的功能。
总结以上介绍我们发现，MVC模式高度支持职责的分离。这种
优势不仅增加了代码的可测试性，而且使其更容易扩展，从而可以相
当容易地实现新功能。
2。MVC容易产生的问题
代码相对冗余。我们知道，MVC模式中View对Model是有着强依
赖的。当View非常复杂的时候，为了最小化View中的逻辑，Model应
该能够为要显示的每个视图提供可测试的方法——这将增加大量的
类和方法。
灵活性较低。由于View依赖于Controller和Model,Ul逻辑中的一
个更改可能导致需要修改很多类，这降低了灵活性，并且导致UI难以
测试。
可维护性低。Android的视图组件中，有着非常明显的生命周
期,如Activity、Fragment等。对于MVC模式,我们有时不得不将处
理视图逻辑的代码都写在这些组件中，造成它们十分臃肿。
所以，Android中最初的MVC架构问题显而易见：过于臃肿的

Page 759
Controller层大大降低了工程的可维护性及可测试性。

Page 760
12。1。2MVP
直到MVP架构模式的出现，传统MVC架构才从真正意义上得到
解脱。MVP分别对应Model、View、Presenter,如图12-2所示。
·Model（数据层）。负责管理业务逻辑和处理网络或数据库API。
·View（视图层）。显示数据并将用户操作的信息通知给Presenter。
·Presenter(逻辑层)。从Model中检索数据,应用Ul逻辑并管理View
的状态，决定显示什么，以及对View的事件做出响应。
相对于MVC,MVP模式设计思路的核心是提出了Presenter层,
它是View层与Model层沟通的桥梁，对业务逻辑进行处理。这更符合
了我们理想中的单一职责原则。
1。传统MVP
如果你是一名Android开发者，你一定非常熟悉Android架构蓝图
的 todo-app(https://github.com/googlesamples/android-
中
architecture），它允许用户创建、读取、更新和删除“待办事项”任
务，以及对任务列表进行分类显示。
在处理Model的时候，我们一般都会使用远程和本地数据源来获
取和保存数据。以获取彳办事项列表为例：当我
据时，
Model优先尝试从本地获取，如果为空，则查询网络更新本地数据并
返回。部分代码如下：

Page 761
fun getTasks(callback: TasksDataSource.LoadTasksCallback) {
//如果本地有缓存并且缓存正常，则直接返回缓存
if (cached Tasks.isNotEmpty() && !cachelsDirty) {
callback.onTasksLoaded(ArrayList(cached Tasks.values))
}
return
}
if (cachels Dirty) {
//如果缓存过期或被污染，则需要从服务端获取最新的数据
get Tasks FromRemoteDataSource(callback)
} else {
//如果本地存在缓存数据则从本地获取，否则从服务端获取
tasksLocalDataSource.getTasks(object : TasksDataSource.Load Task
override fun onTasksLoaded(tasks: List<Task>) {
refreshCache(tasks)
}
}）
callback.onTasksLoaded(ArrayList(cached Tasks.values))
}
override fun onDataNotAvailable() {
getTasksFromRemote DataSource(callback)
}

Page 762
数据改变
Model
更新数据
Presenter
12-2MVP
用户操作
更新视图
View
它接收通用回调类型TasksDataSource.LoadTasksCallback作为
参数，使其完全独立于任何Android类，因此易于使用JUnit进行单元
测试。例如，如果我们要模拟本地数据不准确的情况，可以这么实现：
private lateinit var tasksRepository: TasksRepository
@Mock private lateinit var load TasksCallback: TasksDataSource.Load Tasks
@Mock private lateinit var tasksRemote DataSource: TasksDataSource
@Mock private lateinit var tasksLocalDataSource: TasksDataSource
private val TASKS = Lists.newArrayList(Task(TASK_TITLE_1, TASK_GENEF
Task(TASK_TITLE_2, TASK_GENERIC_DESCRIPTION))
@Before fun setupTasks Repository() {
MockitoAnnotations.initMocks(this)

Page 763
}
@Test fun getTasksWithLocal DataSource Unavailable_tasksAreRetrieved Fro
tasksRepository.getTasks(load TasksCallback)
tasksRepository = TasksRepository.getInstance(tasksRemoteDataSourc
tasksLocalDataSource)
}
}
setTasksNotAvailable(tasksLocalDataSource)
setTasksAvailable(tasksRemoteDataSource, TASKS)
verify(load TasksCallback).onTasksLoaded(TASKS)
在界面展示数据的时候，View通过Presenter来发送获取数据的
MVP, Activity. Fragment
X***
View中。在Todo项目中,所有View都实现了允许设置Presenter的
BaseView接口。
interface BaseView<T> {
var presenter: T
View模块通常在生命周期函数onResume）中，调用
subscribe()方法通知Presenter:“嘿,哥们,我准备好被更新了,
请随时下达指令。”然后在onPause()中调用subscribe()解除绑
定。而在Kotlin中，我们通常的做法是在View中声明一个延迟初始化

Page 764
presenter (ViewTaskFragment):
// TasksContract 契约类,我们通常把View和Presenter的接口写在其中,便
interface TasksContract {
interface View : BaseView<Presenter> {
fun showTasks(tasks: List<Task>)
fun showTaskDetails Ui(taskld: String)
fun showLoading TasksError()
fun showNoTasks()
}
interface Presenter: BasePresenter {
}
fun load Tasks(forceUpdate: Boolean)
}
class TasksFragment: Fragment(), TasksContract. View {
override lateinit var presenter: TasksContract.Presenter
override fun onResume() {
super.onResume()
presenter。start（）//请求加载当前视图初始化需要的数据

Page 765
}
}
在承载视图的TasksActivity上,我们初始化视图TasksFragment
TasksPresenter:
class TasksActivity: AppCompatActivity() {
private lateinit var tasksPresenter: TasksPresenter
override fun onCreate(savedInstanceState: Bundle?) {
val tasksFragment = supportFragmentManager.findFragmentById(R.id.c
as TasksFragment? ?: TasksFragment.newInstance().also {
replaceFragmentInActivity(it, R.id.contentFrame)
}
// 创建 presenter
tasksPresenter = TasksPresenter(Injection.provide Tasks Repository(applica
//加载历史数据
}
KAR, LØRÆT###Presenter View
绑定的操作。其实,TasksPresenter中另有玄机:

Page 766
class TasksPresenter(val tasksRepository: TasksRepository, val tasksView: 1
: TasksContract.Presenter {
init {
}
tasksView.presenter = this
}
override fun start() {
loadTasks(false)
}
原来,得益于init(),在TasksPresenter初始化的同时,我们也
对View中的Presenter进行赋值,这样就不必每次都写subscribe和
unsubscribe方法了。当然，我们利用依赖注入也能实现这样的需
求,比如dagger。
当页面结束的时候会终止网络请求，我们应该及时释放Presenter中
的引用,防止内存泄漏。通常使用的是RxLifeCycle(https://
github.com/trello/RxLifecycle),有兴趣的读者可以自行研究。
这便是基于Kotlin创建的MVP架构模式中的一种。除此之外，我
们还能通过结合很多框架，如dagger、rxKotlin，来让工程更加通
透。
2。MVP容易产生的问题

Page 767
1）接口粒度难以掌控。MVP模式将模块职责进行了良好的分离。
但在开发小规模App或原型时，这似乎增加了开销——对于每个业务
场景,我们都要写Activity-View-Presenter-Contract这4个类。为了缓
解这种情况,一些开发者删除了Contract接口类和Presenter的接口。
另外，Presenter与View的交互是通过接口实现的，如果接口粒度过
大，解耦程度就不高，反之会造成接口数量暴增的情况。
从工程的严谨角度来说，这或许并不是缺点，只是创造一个良好工程
架构带来的额外工作量。
2)Presenter逻辑容易过重。当我们将UI的逻辑移动到Presenter
中时，Presenter变成了有数千行代码的类，或许会难以维护。要解
决这个问题，我们只可能更多地拆分代码，创建便于单元测试的单一
职责的类。
3)Presenter和View相互引用。我们在Presenter和View中都会保
持一份对方的引用,所以需要用subscribe和unsubscribe来绑定和解
除绑定。在操作UI的时候，我们需要判断UI生命周期，否则容易造成
内存泄露。
当然，以上的“缺点”我们都可以通过良好的编码习惯及严谨的
设计来规避。如果我们想要一个基于事件且View会对此事件变化做
出反应的架构，该怎么实现呢?

Page 768
12。1。3MWM
相较于MVC和MVP模式，MVM在定义上就明确得多。维基百科
上对其是这么介绍的：
MVVM有助于将图形用户界面的开发与业务逻辑或后端逻辑（数据模
型）的开发分离开来，这是通过置标语言或GUI代码实现的。MVVM
的视图模型是一个值转换器，这意味着视图模型负责从模型中暴露
（转换）数据对象，以便轻松管理和呈现对象。在这方面，视图模型
比视图做得更多，并且处理大部分视图的显示逻辑。视图模型可以实
现中介者模式，组织对视图所支持的用例集的后端逻辑的访问。
MVVM也被称为model-view-binder,如图12-3所示。它的主要构
成如下。
Model（数据模型）：与ViewModel配合，可以获取和保存数据。
‧View（视图）：即将用户的动作通知给ViewModel（视图模型）。
·ViewModel（视图模型）：暴露公共属性与View相关的数据流，通常
为Model和View的绑定关系。
作为MV*家族的一员，它看起来与MVP模式有所相似：它们都擅
长抽象视图行为和状态。
如果MVP模式意味着Presenter直接告诉View要显示的内容,那
么在MVVM中,ViewModel会公开Views可以绑定的事件流。这样,
ViewModel不再需要保持对View的引用,但发挥了Presenter一样的作

Page 769
用。这也意味着MVP模式所需的所有接口现在都被删除了。这对介
意接口数量过多的开发者来说是个福音。
View还会通知ViewModel进行不同的操作。因此,MVVM模式支
持View和ViewModel之间的双向数据绑定,并且View和ViewModel之
间存在多对一关系。View具有对ViewModel的引用,但ViewModel没
有关于View的信息。因为数据的使用者应该知道生产者，但生产者
ViewModel不需要知道，也不关心谁使用数据。
Model
获取数据
更新数据
ViewModel
图12-3MVVM架构
双向绑定
<?xml version="1.0" encoding="utf-8"?>
View
光有概念部分读者可能还不能感受到MVVM的特点。我们以官方
的todo-app中的addTask模块为例，先来看看它的布局
addtask_frag.xml:

Page 770
<layout xmlns:android="http://schemas.android.com/apk/res/android"
xmlns:app="http://schemas.android.com/apk/res-auto">
<data>
<import type="android.view.View"/>
<variable
name="viewmodel"
type="com.example.android.architecture.blueprints.todoapp.addedittask.AddE
</data>
<com.example.android.architecture.blueprints.todoapp. Scroll ChildSwipeRe
android:id="@+id/refresh_layout"
android:layout_width="match_parent"
android:layout_height="match_parent"
app:enabled="@{viewmodel.dataLoading}"
app:refreshing="@{viewmodel.dataLoading}">
<ScrollView
android:layout_width="match_parent"
android:layout_height="match_parent">
<LinearLayout
android:layout_width="match_parent"
android:layout_height="wrap_content"
android:orientation="vertical"
android:paddingBottom="@dimen/activity_vertical_margin"
android:paddingLeft="@dimen/activity_horizontal_margin"

Page 771
android:paddingRight="@dimen/activity_horizontal_margin"
android:paddingTop="@dimen/activity_vertical_margin"
android:visibility="@{viewmodel.dataLoading? View.GONE : View.
<Edit Text
android:id="@+id/add_task_title"
android:layout_width="match_parent"
android:layout_height="wrap_content"
android:hint="@string/title_hint"
android:singleLine="true"
android:text="@={viewmodel.title}"
</layout>
android:textAppearance="@style/TextAppearance.AppCompat.T
<Edit Text
android:id="@+id/add_task_description"
android:layout_width="match_parent"
android:layout_height="350dp"
android:gravity="top"
android:hint="@string/description_hint"
android:text="@={viewmodel.description}"/>
</LinearLayout>
</ScrollView>
</com.example.android.architecture.blueprints.todoapp.Scroll ChildSwipeR

Page 772
之前没有接触过MVVM模式的读者，应该会对<data>标签感到疑
. ** Data Binding (https://developer.android.com/topic/
libraries/data-binding/)
4：
使用Data Binding让xml绑定数据,我们需要以<layout>为根布局,并
且声明<data>,其中type对应Model(需要指定完整类名),name相
当于Model在当前视图中对应的对象，我们在xml中就可以用
android: text="@={viewmodel.description}" . 当
viewmodel.description变化的时候,EditText也会改变;反之,当我们
编辑EditText的时候,viewmodel.description的值也会相应变化。
这个时候你可能会对viewmodel的结构感到好奇，让我们一起来
AddEdit TaskView Model.kt:
class AddEdit TaskViewModel
internal constructor(context: Context, private val mTasks Repository: TasksRe
: TasksDataSource.GetTaskCallback {
val title = ObservableField<String>()
val description = ObservableField<String>()
val dataLoading = ObservableBoolean(false)
val snackbarText = ObservableField<String>()
private val mContext: Context //AFL*, £IÈApplication
private var mTaskld: String? = null
private var isNewTask: Boolean = false

Page 773
private var mlsDataLoaded = false
private var mAddEditTaskNavigator: AddEditTaskNavigator? = null
init {
mContext = context.application Context // Application context
}
fun onActivityCreated(navigator: AddEdit TaskNavigator) {
mAddEdit TaskNavigator = navigator
}
fun onActivity Destroyed() {
//释放不需要的引用
mAddEdit TaskNavigator = null
}
fun start(taskld: String?) {
if (dataLoading.get()) {
return
}
mTaskld = taskld
if (taskld == null) {
}
isNewTask = true
return
}
if (mlsDataLoaded) {
return
isNewTask = false

Page 774
}
override fun on TaskLoaded(task: Task) {
title.set(task.title)
}
dataLoading.set(true)
description.set(task.description)
dataLoading.set(false)
mlsDataLoaded = true
//这里我们不需要像MVP模式那样主动改变View，因为我们已经使用C
}
override fun onDataNotAvailable() {
dataLoading.set(false)
mTasksRepository.getTask(taskld, this)
}
fun saveTask() {
}
if (isNewTask) {
create Task(title.get(), description.get())
} else {
update Task(title.get(), description.get())
}
fun getSnackbarTextString(): String {
return snackbar Text.get()

Page 775
}
private fun createTask(title: String, description: String) {
val newTask = Task(title, description)
if (newTask.isEmpty) {
} else {
mTasks Repository.save Task(newTask)
navigateOnTaskSaved()
}
}
snackbarText.set(mContext.getString(R.string.empty_task_message))
}
private fun update Task(title: String, description: String) {
if (isNewTask) {
throw RuntimeException("update Task() was called but task is new.")
}
mTasksRepository.saveTask(Task(title, description, mTaskld))
navigateOnTaskSaved() // 编辑完成,返回task列表界面
}
private fun navigateOnTaskSaved() {
if (mAddEditTaskNavigator != null) {
mAddEdit TaskNavigator!!.onTaskSaved()
}

Page 776
可以看到，我们将大部分操作数据的逻辑都放这个类中，在维护
的时候就能体会到这其中的优势。我们再看一下绑定View的另一部
Add TaskFragment.kt:
分，
class AddEdit TaskFragment: Fragment() {
private var mViewModel: AddEdit TaskViewModel? = null
private lateinit var mViewDataBinding: AddtaskFragBinding
override fun onResume() {
super.onResume()
if (arguments != null) {
}
mViewModel?.start(arguments.getString(ARGUMENT_EDIT_TASK_I
} else {
}
mViewModel?.start(null)
}
fun setViewModel(viewModel: AddEdit TaskViewModel) {
mViewModel = viewModel
override fun onCreateView(inflater: LayoutInflater?, container: ViewGroup?
savedInstanceState: Bundle?): View? {
val root = container?.inflate(R.layout.addtask_frag)
mViewDataBinding = AddtaskFragBinding.bind(root)

Page 777
}
}
mViewDataBinding.viewmodel = mViewModel
setHasOptionsMenu(true)
retainInstance = false
return mViewDataBinding.root
companion object {
val ARGUMENT_EDIT_TASK_ID = "EDIT_TASK_ID"
fun newInstance(): AddEditTaskFragment {
return AddEdit TaskFragment()
}
从以上代码我们不难看出：
1)通过View来创建一个ViewDataBinding的对象:
2)将mViewModel赋值到XML文件<data> 里进行声明的
ViewModel的具体对象当中,从而使ViewModel和XML文件创建关

Page 778
联：
mViewDataBinding.viewmodel = mViewModel
除此之外，与MVP类似，我们在Fragment的各个生命周期中，
调用mViewModel对应的方法来响应View的变化。不同的是，在
MVVM中我们只需要改变viewModel中的数据,View的响应已经自动
完成了(比如通过Data Binding)。
这样代码的结构比之前更加通透，我们核心关注的就是数据的改
变——这简直太让人身心愉悦了。如此便捷的背后，依旧存在一些
问题。
MVVM容易造成的问题如下：
1）需要更多精力定位Bug。由于双向绑定，视图中的异常排查
起来会比较麻烦，你需要检查View中的代码，还需要检查Model中的
代码。另外你可能多处复用了Model，一个地方导致的异常可能会扩
散到其他地方，定位错误源可能并不会太简单。
2）通用的View需要更好的设计。当一个View要变成通用组件时，
该View对应的Model通常不能复用。在整体架构设计不够完善时，我
们很容易创冗余的Model。
如果说双向数据流这种“自动管理状态”的特性会给我们造成困
扰，除了在编码上规避，还有其他的解决方案吗?答案是肯定的，这

Page 779
里我们推荐使用谷歌官方的Android Architecture Components,感兴
趣的读者可以自行了解。

Page 780
12。2单向数据流模型
既然有双向数据绑定的架构MVVM，那自然少不了单向数据流。
如果你接触过前端，你肯定听说过Flux，它是最经典的单向数据流架
构之一。我们可以通过它来了解单向数据流模型，如图12-4所示。
Flux组成通常分为以下4个部分。
·View（视图）：显示UI。
Action（动作）：用户操作界面时，视图层发出的消息（比如用户点
击按钮、输入文字等）。
·Dispatcher(分发器):用来接收Actions,执行回调函数。
·Store（数据层）：类似于MV*的Model层。用来存放应用的状态，
旦发生变动，就提醒View更新页面。

Page 781
Actions
福
Action Creators
User Interactions
Web App Utils
Web API
Dispatcher
React Views
Callbacks
Store
Change Events+
Store Queries
图12-4单向数据流模型
用户通过与view交互或者外部产生一个Action,Dispatcher接收
到Action并执行那些已经注册的回调,向所有Store分发Action。通过
注册的回调，Store响应那些与它们所保存的状态有关的Action。然后
Store会触发一个change事件，来提醒对应的View数据已经发生了改
变。View监听这些事件并重新从Store中获取数据。这些View调用它
们自己的setState（）方法，重新渲染自身及相关联的组件。
除了Flux，当前Web前端比较常用的React也是比较典型的单向数据
流框架，它也是基于Redux模型实现的。

Page 782
12。2。1Redux
Redux作为Flux模型一个友好简洁的实现，它基于一个严格的单
向数据流：应用中的所有数据都是通过组件在一个方向上流动。
Redux希望确保应用的视图是根据确定的状态来呈现的——即在任何
阶段，应用的状态总是确定、有效的，并且可以转换到另一个可预测、
有效的状态，视图将根据所处的状态来进行对应的展示。
1.Redux基本概念
Redux的核心为3个部分。
·Store：保存应用的状态并提供方法来存取对应的状态，分发状态，
并注册监听。
·Actions：与Flux类似。包含要传递给Store的信息，表明我们希望怎
样改变应用的状态。比如，在Kotlin中我们可以定义如下action：
data class AddTodoAction(val title: String, val content: String)
然后由store进行分发：
store.dispatch(AddTodoAction("Finish your homeWork", "English And Math"))
·Reducers: Store收到Action以后,必须给出一个新的State,这样

Page 783
View才会发生变化。这种State的计算过程就叫作Reducer。如下所示：
fun reduce(oldState: AppState, action: Action): AppState {
return when (action) {
}
}
is AddToDoAction -> {
oldState.copy(todo = ...)
}
else -> oldState
Redux数据流图如图12-5所示。
Actions
请求数据返回数据
事件传递
HTTP Request
触发事件
Middlewares
数据传递
Views
用户操作界面
User
Reducers
图12-5Redux数据流图
更新state
更新UI
Store(states)

Page 784
对比Flux，我们可以发现一些不同点，如表12-1所示。
表12-1
Flux与Redux模型比较
数据源
分发机制
Store
Flux
一个应用有多个数据源（通常
是一个业务场景一个Store）
利用一个单例对象 Dispatcher
进行所有事件分发
可读并可写，对数据的操作
逻辑一般放在Store中
Redux
通常仅有一个Store
没有调度对象实体，Store中已经完成了dispatch，我们使用其
暴露的接口完成事件分发
只可读，逻辑放在Reducer中，它接收先前的状态和一个动作，
并根据该动作返回新的状态，Reducer通常是一个纯函数，如果无
法确保其为纯函数，可以使用Middleware
经过以上对单向数据流模型的介绍，相信你应该对其有了一定的
了解。但是很多读者可能还是没有足够的理由说服自己使用这个架构：
单向数据流到底有什么好处呢?让我们看看下一节。

Page 785
12。2。2单向数据流的优势
单向数据流架构的最大优势在于整个应用中的数据流以单向流动
的方式，从而使得拥有更好的可预测性与可控性，这样可以保证应用
各个模块之间的松耦合性。
1。优秀的数据追溯能力
在MVVM中，数据变动时由框架自动帮我们实现视图的同步变
更，更改一个地方的数据，可能会影响很多地方的状态，并且它是不
可预期的，很难维护和调试。而单向数据流的架构中，整个应用状态
是可预测的，我们可以监听到数据变动，从而采取自定义的操作。
对于一个组件来说，数据入口只有唯一一个。当数据发生改变时，
UI也会发生改变。反之UI的变化并不会直接变动数据。这不仅使得程
序更直观、更容易理解，而且更有利于应用的可维护性。
2。更简洁的单元测试
因为Dispatcher是所有Action的处理中心,即使没有对应的事件
发生，我们也可以“伪造”一个出来，只需要用Action对象向
Dispatcher描述当前的事件，就可以执行对应的逻辑。在Redux中，
由于Reducer是纯函数而没有内部状态，对于给定的输入状态和操作，
它们将始终返回相同的输出状态。因为State和Action相对是轻量级的，
所以我们可以把测试重点放在Reducer上。在Kotlin中代码可能是这样
的：

Page 786
class TodoReducer {
fun reduce(state: AppState, action: Action): AppState {
// todo
}
}
data class TodoAction(val text: String)
val todoReducer = TodoReducer()
val originalState = AppState({
// todo
}）
val todoAction = TodoAction(text = 'just haha'})
val newState = todoReducer.reduce(originalState, todoAction)
//判断newState与预期是否一致
assert(newState...)
如果数据需要从多个地方获取（比如，本地存储或网络中获取），
我们可以改变Action的结构：
class TodoAction(val dataOfLocal: String, val dataOfApi: String) {
companion object {
fun create(localStore: LocalStore, apiResponse: ApiResponse): TodoAct
val dataOfLocal = localStore.targetData
val dataOfApi = apiResponse.targetData
TodoAction(dataOfLocal = dataOfLocal, dataOfApi= dataOfApi)

Page 787
}
}
}
这样测试起来也是非常容易：
val todoAction = TodoAction(dataOfLocal = "i'm from sqlite", dataOfApi = "i'm
val newState = reducer.reduce(originalState, todoAction)
3。单向数据流遇上Kotlin
因为Redux是基于Flux的思想产生的，所以在Redux架构中构造
组件，通常也会产生许多样板代码。对于JavaScript来说，这可能难
以优化。而使用Kotlin，我们能更加方便地管理样板代码。
当我们在Reducer中匹配不同类型的Action时,按照Java的套路
可能会这样写：
AppState reduce(Action action, oldState: AppState) {
switch (action.type) {
case TodoAction.TYPE.ADD_TODO_ITEM:

Page 788
}
return addTodoAction(oldState, action);
case TodoAction.TYPE.CHANGE_STATE:
return changeAction(oldState, action);
default:
}
return oldState;
}
return oldState;
或者当Action结构相对比较复杂时，我们不想再添加一个type字
段，而是直接判断Action属于什么类：
AppState reduce(Action action, oldState: AppState) {
if (action instanceof AddTodoAction) {
return addTodoAction (oldState, action);
} else if (action instanceof Change TodoAction) {
return changeAction(oldState, action);
}elseif（。。。）{
}
return oldState;

Page 789
这个时候，如果action非常多，就会给开发者带来巨大的痛苦。
但是别着急，我们可以用Kotlin的when来拯救它：
fun reduce(Action action, oldState: AppState): AppState {
return when (action) {
is AddTodoAction -> reduceAddTodoAction(oldState, action)
is RemoveTodoAction -> reduceRemoveTodoAction(oldState, action)
else -> oldState
}
}
并且，我们还能利用SmartCasts，在数据处理的同时避免不必
要的判断。当然，这里只是用Kotlin提升Redux架构便捷性的冰山一
角，更多内容将在下一节呈现。
虽然Redux起源于Web端，但从它的构建中，我们可以看到很多
非常好的想法，这都是值得学习并可以尝试引入Android的。即使我
们的平台、语言和工具可能不同，但在架构层面，我们面对着许多相
同的基本问题，比如，尽可能降低View和业务逻辑代码的耦合度
等。

Page 790
12.3 ReKotlin
如果你是一名Android开发者，你应该知道：在国内的项目中，
鲜有单向数据流架构的痕迹。甚至一些经验不够丰富的Android开发
者，可能都不知道“单向数据流”。
在iOS中,有一个著名的单向数据流框架:ReSwift(https://
github.com/ReSwift/ReSwift),它在github上的被关注度还不错。随着
Kotlin在Android中的地位不断提高，利用其优秀的语言特性，也派生
出了类似的框架:ReKotlin(https://github.com/ReKotlin/ReKotlin)
它的出现，也宣布了Android即将“跨入单向数据流时代”。
。

Page 791
12.3.1 初见ReKotlin
基于经典的Redux模型,ReKotlin也奉行以下设计。
1）TheStore：以单一数据结构管理整个App的状态，状态只能
通过dispatching Actions来进行修改。每当Store中的状态改变了,它
就会通知所有的Observers。
2）Actions：通过陈述的形式来描述一次状态变更，操作中不包
含任何代码,通过Store转发给 Reducers。 Reducers会接收这些
Actions，然后进行相应的状态逻辑变更。
3)Reducers:基于当前的Action和App状态,通过纯函数来返回
一个新的App状态。
因为核心思想与Redux基本是一致的，所以这里我们就尽可能简
单地对其进行概括：单向数据流意味着应用程序的State不应该保存
在许多不同的地方。相反，存储组件将所有State保持在中心位置。
View会对此State的更改做出反应，而不是在內部处理它。Action是触
发State更改的唯一方法，它不会通过它们自己来更改状态，而更像
是一些指令———表示某些內容将发生变化。这些“指令”是针对使
用执行实际状态更改的Reducers的Store对象发出的。另外，还有
Middleware（中间件），它主要用来处理副作用，这会在后面介绍。

Page 792
12。3。2创建基于ReKotlin的项目
前面看到许多概念，也许你已经跃跃欲试了。现在我们就来看看
FReKotlin
Android I.
1.3 Rekotlin
GradleReKotlin, 1.0.0W, @N✯1]
加上一些日常需要的框架（版本仅供参考，引入实际项目时可酌情调
整）。
dependencies {
implementation 'com.android.support: recyclerview-v7:27.1.1'
implementation 'com.android.support:cardview-v7:27.1.1'
implementation 'com.android.support:design:27.1.1'
// reKotlin
implementation "org.rekotlin:rekotlin:1.0.0"
// http
implementation 'com.squareup.retrofit2:retrofit:2.3.0'
implementation 'com.squareup.retrofit2:converter-gson:2.3.0'
// imageLoader
implementation 'com.squareup.picasso:picasso:2.5.2'
//json

Page 793
}
implementation 'com.google.code.gson:gson:2.8.2¹
// log
implementation 'com.jakewharton.timber:timber:4.6.0'
2。整体结构
我们本次的示例主要是做一个电影列表。这里我们从一个开源
API中获取数据，然后将其显示到App中。我们先来看一下实例项目
的文件清单：

- actions
- MovieListActions.kt
- middlewares
- MovieMiddleWare.kt
- NetworkMiddleWare.kt
- model
- Movie.kt
    network
- Api.kt
- HttpClient.kt
- reducers
- AppReducer.kt
- MovieListReducer.kt

Page 794

- states
- AppState.kt
- MovieListState.kt
  -ui
    BaseActivity.kt
- MovieDetailActivity.kt
- MovieListAdapter.kt
  -
    MovieListFragment.kt
- MainActivity.kt
- utils
- ImageLoder.kt
- Logger.kt
- MovieApplication.kt
    其中model、network、ui、utils文件夹与我们平常的项目结构类
    似，由于篇幅限制，这些目录我们将不会详细讲解，读者可以在
    https://github.com/DivelntoKotlin/DiveIntoKotlinSamples查看完整的项
    目代码。
    然后我们把目光聚焦在新增加的actions、middlewares、reducer、
    states目录上。我们在12。3。1节中已经对它们进行过介绍。结合示例
    项目，它们发挥的作用如下。
    ·actions：所有更新State的行为我们都可以抽象成Action，并且根据
    不同的场景分布在不同文件下。

Page 795
·reducers: 不同Action对应的响应中心,会返回一个新的Reducer。
·middlewares:由于Action的接收方Reducer都是纯函数,不会也不能
产生副作用，如果我们想加入一些额外的操作，例如打印日志、操作
SQLite数据库等，我们可以将这些操作放到该文件夹中。
·states：所有状态的声明都放在这个目录下。
了解目录结构后，让我们一起来看看ReKotlin集成的主要步骤。
在12。3。1节中我们介绍过：在ReKotlin中，每个App对应只有一个
数据管理中心（Store）。所以，我们可以在Application中将其初始化，
项目中我们使用的自定义的Application名为MovieApplication。
MovieApplication.kt:
import android.app.Application
import
dripower.rekotlinsimpleexample.middlewares.movieMiddleware
import dripower.rekotlinsimpleexample.middlewares.networkMiddleware
import dripower.rekotlinsimpleexample.ruducer.appReducer
import org.rekotlin.Store
val store = Store(
reducer = ::appReducer,
state = null
）
class MovieApplication: Application() {

Page 796
}
import
android.support.v4.app.FragmentTransaction
import android.support.v7.app.AppCompatActivity
abstract class BaseActivity: AppCompatActivity() {
inline fun BaseActivity.transFragment(action: FragmentTransaction.()
supportFragmentManager.beginTransaction().apply {
}
View, Activity+Fragment.
MainActivity.kt:
}
action()
}.commit()
MainActivity.kt:
import android.os.Bundle
import android.support.v4.app.Fragment
import dripower.rekotlinsimpleexample.R
import
class MainActivity: BaseActivity() {
dripower.rekotlinsimpleexample.ui.movieList.MovieListFragment
->Ur

Page 797
}
override fun onCreate(savedInstanceState: Bundle?) {
}
private fun showFragment(fragment: Fragment) {
transFragment {
replace(R.id.container, fragment)
}
super.onCreate(savedInstanceState)
setContentView(R.layout.activity_main)
showFragment(MovieListFragment())
}
以上逻辑即在MainActivity渲染出MovieListFragment,就不做详
44。
IA*MovieListFragment.kt:
}
class MovieListFragment: Fragment(), StoreSubscriber<MovieListState?> {
private lateinit var movieListAdapter: MovieListAdapter
override fun newState(state: MovieListState?) {
state?.movieObjects?.let {
initializeAdapter(it)
}
override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?,
savedInstanceState: Bundle?): View? =

Page 798
inflater.inflate(R.layout.fragment_movie_list, container, false)
override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
super.onViewCreated(view, savedInstanceState)
store.dispatch(LoadTop250MovieList())
}
private fun initializeAdapter(movieData: List<Subject>) {
val activity = this.activity as MainActivity
movieListAdapter = MovieListAdapter(movieData, {id -> movieListToDet
movieList.layoutManager = GridLayoutManager(context, 2)
movieList.adapter = movieListAdapter
}
private fun movieListToDetail (subject: Subject, activity: MainActivity) {
val intent = Intent(activity, MovieDetailActivity::class.java)
intent.putExtra("id", subject.id)
intent.putExtra("title", subject.title)
startActivity (intent)
}
override fun onStart() {
super.onStart()
store.subscribe(this) {
it.select {
it.movieListState
}.skipRepeats()

Page 799
}
}
}
override fun onStop() {
super.onStop()
store.unsubscribe(this)
}
通常，我们在需要与数据打交道的界面中，都会实现
StoreSubscriber<TState>接口(这是Rekotlin中实现的,我们可以直
接使用），并且分别在生命周期中做以下事情：
1)override fun newState(state:MovieListState?)。这里相当
于一个数据流管道的出口，当数据state变化时，我们可以对其做一
些相应的操作，有点类似前端中的Watch机制。示例中，每次数据变
化我们都更新列表数据，重新渲染。
2）onViewCreated。通常我们在这个生命周期里发起数据请求
（网络或者本地数据库）。示例中，我们仅做了网络请求。
3)onStart。我们通常在这里进行store的绑定。
4）onStop。相应地，我们需要在视图不显示的时候，解除store
绑定，防止内存泄漏等问题。

Page 800
其余的代码为列表适配器绑定以跳转MovieDetailActivity,有
Android经验的读者应该能很容易地看懂。
MovieListAdapter.kt:
class MovieListAdapter(private val movieData: List<Subject>, private val imag
RecyclerView.Adapter<MovieListAdapter. MovieltemHolder>() {
override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): Movi
return MovieltemHolder(LayoutInflater.from(parent.context).inflate(R.lay
parent, false), imageClickCallBack)
}
override fun onBindViewHolder(holder: MovieltemHolder, position: Int) {
val movieltem = movieData[position]
holder.apply{
}
}
movieRating.text = movieltem.rating.average.toString()
movieTitle.text = movieltem.title
movielmage.load Image(movieltem.images.large)
override fun getItemCount(): Int=movieData.size
inner class MovieltemHolder(itemView: View?, imageClickCallBack: (Subje
lateinit var movieRating: TextView
lateinit var movieTitle: TextView
lateinit var movielmage: ImageView

Page 801
}
}
init {
itemView?.apply {
movieRating = findViewById(R.id.movie_rating)
movie Title = findViewById(R.id.movie_title)
movielmage = findViewById(R.id.movie_image)
movielmage.setOnClickListener {
movieData[adapterPosition].apply {
}
}
}
image
on
ClickCallBack(movieData[adapterPosition])
BindViewHolder(this@MovieltemHolder, adapterPosition)
MovieDetailActivity的界面很简单:包含一个返回按钮,两个文本
movie name id.
MovieDetailActivity.kt:
import android.os.Bundle
import dripower.rekotlinsimpleexample.R

Page 802
import
dripower.rekotlinsimpleexample.ui.BaseActivity
import kotlinx.android.synthetic.main.activity_movie_detail.*
class MovieDetailActivity:BaseActivity() {
override fun onCreate(savedInstanceState: Bundle?){
}
}
super.onCreate(savedInstanceState)
setContentView(R.layout.activity_movie_detail)
val id = intent.extras?.get("id")
val title = intent.extras?.get("title")
tv_movie_id.text = id as String
tv_movie_title.text = title as String
btn_back.setOnClickListener { this.finish()}
然后让我们来看看单向数据流部分。既然称为单向数据流，我们
最核心的地方肯定都是围绕数据展开的。对于某个场景来说，我们的
数据为该场景的状态（State）服务，而状态直接决定了该场景视图
显示的内容。所以我们需要先确定好这些状态。对于当前示例，我们
需要显示movieList，所以可以进行如下创建。
MovieListState.kt:
import dripower.rekotlinsimpleexample.model.Subject

Page 803
import org.rekotlin.StateType
data class MovieListState(
var movieObjects: List<Subject>? = null
) : StateType
一个App中会对应很多场景，我们同样需要进行统一管理。当前
示例中我们将其放入AppState。
AppState.kt:
data class AppState(
var movieListState: MovieListState? = null
) : StateType
以上，我们已经确定了movieList界面的最终显示效果。这时候，
我们可以打开数据流的开关，并且控制它们的流向，我们可以为当前
场景的操作定义不同的动作（Action）。
MovieListActitions.kt:
class InitMovieList(val movieData: List<Subject>) : Action
class LoadTop250MovieList: Action
class ShowMovieList(val movieData: List<Subject>) : Action

Page 804
的变化。
MovieListAction,
ƒŒÐ。¥
store.dispatch (Action () Z, Reducer State
AppReducer.kt:
fun appReducer(action: Action, appState: AppState?): AppState =
AppState (movieListState = movieListReducer(action, appState?.movieList
MovieListReducer.kt
}
fun movieListReducer(action: Action, movieListState: MovieListState?): Movie
var state = movieListState ?: MovieListState()
when (action) {
is ShowMovieList -> {
state = state.copy(movieObjects = action.movieData)
}
}
return state
我们知道，Reducer是一个没有副作用的处理，所以如果需要对
数据进行中间加工或者打印日志等，都需要放到中间件Middleware中。
Middleware, Store
Middleware. **1#MovieApplication Store,
需要进行如下更改：

Page 805
val store= Store(
middleware = listOf(networkMiddleware, movieMiddleware)
）
本示例中，我们将网络请求获取MovieList的逻辑放在
networkMiddleware中,当返回正确的结果时,我们进行渲染
movieList,
E
internal val networkMiddleware: Middleware<AppState> = { dispatch, _ ->
{next->
{action->
}
NetworkMiddleware.kt:
}
}
when (action) {
is Load Top250MovieList -> {
getTop250MovieList(dispatch)
}
}
next(action)

Page 806
//这里即获取movie数据的核心逻辑
private fun getTop250MovieList(dispatch: DispatchFunction) {
val apiService = HttpClient.client?.create(Api::class.java)
val call = apiService?.getTop250MovieList()
}
call?.enqueue(object : Callback<MovieResponse> {
override fun onFailure(call: Call<MovieResponse>?, t: Throwable?) {
Logger.error(t)
}）
}
override fun onResponse(call: Call<MovieResponse>?, response: Resp
val movieObjects = response?.body()?.subjects
movieObjects?.let {
dispatch(InitMovieList(it))
}
}
同时，我们在初始化MovieList的时候（即发送
InitMovieListAction), Action Middleware+.
MovieMiddleware.kt:
import dripower.rekotlinsimpleexample.actions. InitMovieList

Page 807
import dripower.rekotlinsimpleexample.actions.ShowMovieList
import
import
import org.rekotlin.DispatchFunction
import org.rekotlin.Middleware
internal val movieMiddleware: Middleware<AppState> = { dispatch, _ ->
{next->
{action->
}
}
dripower.rekotlinsimpleexample.model. Subject
dripower.rekotlinsimpleexample.states.AppState
when (action) {
}
is InitMovieList -> {
processMovies(action.movieData, dispatch)
}
next(action)
private fun processMovies(movieObjects: List<Subject>, dispatch: DispatchFi
//你可以在这里对movieList进行一些有副作用的操作，例如：打印日志、
dispatch(ShowMovieList(movieObjects))
MovieListReducer
state movieObjects.
ShowMovieListJaction, #AT#
MovieListFragment

Page 808
StoreSubscriber<MovieListState?>接口吗?当MovieListState发生变
化时,将会触发newState(state:MovieListState?)方法,这样就会
重新渲染movieList。
如果你的代码正确，此时一个完整的列表界面就呈现出来了。如
果你还是不太清楚，让我们再通过一张图来理一理整个项目的逻辑，
如图12-6所示。
事件传递
LoadTop250MovieListAction
HTTP Request
请求数据返回数据
NetMiddlewares
分发载入movieList的action
MovieListFragment
数据传递
MovieListReducers
MovieListView
用户操作界面
User
图12-6示例App的数据流图
返回新的state
MovieListState
StoreSubscriber监听到
MovieListStater
则更新UI
这样，一个单向数据流架构的App就完成了。相对传统App的架
构，你是否有新的感受?可以访问链接https：//github。com/
DivelntoKotlin/DivelntoKotlinSamples,查看完整代码。
当然，这样还不是最理想的使用方式。在单元测试的时候，可能

Page 809
会被一个问题所烦恼：我们在单元测试的时候，依旧局限于单个视图
下的数据操作，即我们只能保证数据流的验证（虽然在单向数据流
中，这已经足够验证我们的视图正确显示了——除非你的UI显示逻
辑显示错误）。要是我们能够对视图进行测试，那该多好啊!

Page 810
12。4解耦视图导航
经过以上的介绍，相信你已经能够掌控数据流了。现在，我们要
解决另一个问题：如何解耦视图导航。

Page 811
12。4。1传统导航的问题
在移动端，我们需要借助视图导航来完成页面切换及数据传递。
随着App的业务不断复杂化，传统的视图导航存在着许多不便之处，
让我们一起来看看。
1.高耦合的Activity.class
在传统的Android开发中,显示跳转Activity我们一般这样写:
val intent = Intent()
intent.setClass(this, TargetActivity::class.java)
startActivity(intent)
这是绝大多数Android开发者的首选做法。所以这看上去非常和
谐，不存在任何问题。但是实际上造成了很高的耦合性：当前Activity
如果要跳转到TargetActivity,就一定要引用TargetActivity。这衍生出
了两个问题：
·如果项目中存在多个Module,杂底层Module中Activity不能跳转到上
层的Activity。
·如果TargetActivity类名变化，调用的地方需要相应改动。
2.难以管理的intent-filter

Page 812
在Android中,我们通常用intent-filter来隐式启动跳转Activity:
val intent = Intent()
intent.action = Intent.ACTION_SENDTO
intent.data = : Uri.parse("smsto:10000")
context.startActivity(intent)
如果项目中存在多个Module,Activity,需要在各自Module的
AndroidManifest.xml中声明配置,容易重复,难以统一管理。
3.不友好的Hybird
在React Native、Weex、Flutter大行其道的现实环境下,我们难
免会与混合开发打交道。当H5页面需要跳转到Native，并且需要把相
关数据传递过去时，通常情况下，我们会采取两种做法：
·直接根据目标Activity的Action中的Schemel跳过去。
·Native维护一个<关键字,Activity>的Map,H5传过来Activiy的「关键
字」，Native在Map中查到后进行跳转。
第1种情况下,Action命名需要符合iOS和Android两个平台的规
范，如果当前版本的Native不支持该Action，还需要进行跳转失败的
处理。
第2种情况下，维护<关键字，Activity>的Map比较麻烦。另外，

Page 813
Activity的存储及生命周期的处理都会存在问题。
并且在两种情况下，我们都可能难以获取到Context的引用，这
时候需要使用Application的Context。

Page 814
12.4.2 rekotlin-router
以上几种都是传统导航中存在的问题。作为国内开发者，我们应
该接触过著名的开源框架ARouter(https://github.com/alibaba/
ARouter），它能够给以上问题一个很好的解决方案，并且还能解决
其他额外的很多问题。但是对于我们来说，这也许有些“重”，我们
可以使用与ReKotlin配套的rekotlin-router(https://github.com/ReKotlin/
rekotlin-router)。
ReKotlin的主要贡献者对rekotlin-router是这么阐述的:ReKotlin的
声明式路由，允许开发者以Web上使用URL类似的方式声明路由。
我们可以在项目Gradle中直接引入：
implementation 'org.rekotlinrouter:rekotlin-router:0.1.9'
然后将原有AppState扩展出导航的状态：
import
org.rekotlinrouter.HasNavigation State
import org.rekotlinrouter.Navigation State
data class AppState(
override var navigation State: NavigationState

Page 815
): StateType, HasNavigation State
在初始化AppState之后，我们需要创建Router的实例。需要传入
***store Routable:
router = Router(store = mainStore,
rootRoutable = RootRoutable(context = applicationContext),
state Transform = {subscription ->
subscription.select { state Type ->
stateType.navigation State
}）
}
然后我们封装一个跳转Route的Action:
import org.rekotlin.Action
import org.rekotlinrouter. Route
import org.rekotlinrouter. StandardAction
import org.rekotlinrouter. StandardAction Convertible
class SetRouteAction(private var route: Route,
private var animated: Boolean = true,
action: StandardAction? = null): StandardActionConvertible {
companion object

Page 816
const val type = "RE_KOTLIN_ROUTER_SET_ROUTE"
}
init {
}
if (action != null) {
route = action.payload?.keys?.toTypedArray() as Route
animated = action.payload!!["animated"] as Boolean
}
}
override fun toStandardAction(): StandardAction {
val payloadMap: HashMap<String,Any> = HashMap()
payloadMap.put("route",this.route)
payloadMap.put("animated", this.animated)
return StandardAction (type = type,
payload = payloadMap,
isTypedAction = true)
}
class SetRouteSpecificData (val route: Route, val data: Any): Action
综上，我们就可以这样调用：
private fun movieListToDetailRoute() {
val routes = arrayListOf(Routers.mainActivityRoute, Routers.movieDetailA

Page 817
}
val action = SetRouteAction(route = routes)
store.dispatch(action)
这样是否比之前优雅了很多?就算在复杂的项目中，我们也能很
好地管理页面跳转。

Page 818
12。5本章小结
（1）主流的客户端架构
目前比较主流的客户端架构即MV*家族：MVC、MVP、MVVM。
其中MVC适合小而简单的App,而MVP和MVVM的选择需要从App具
体业务场景出发。从MVC到MVP的演变完成了View与Model的解耦,
改进了职责分配与可测试性。而从MVP到MVVM，添加了View与
ViewModel之间的数据绑定,使得View完全无状态化。
（2）从MV*到单向数据流
单向数据流在前端页面中是一种非常流行的架构方式，在React
和Vue中其优点得到极致的体现。从MV*到单向数据流的变迁采用了
消息队列式的数据流驱动的架构，并且以Redux为代表的方案将原本
MV*中碎片化的状态管理变为统一的状态管理，保证了状态的有序性
与可回溯性。
(3)ReKotlin
Kotlin的崛起,让Android能够顺滑地支持ReSwift的思想。利用
ReKotlin，我们可以在Android中更容易地实现单向数据流架构，在强
有力的状态的有序性与可回溯性前提下，我们能够提供比MV*架构更

Page 819
详尽的单元测试。并且在复杂的业务场景下，也不易出现难以排查的
问题和冗杂的代码。

Page 820
第13章开发响应式Web应用
随着计算机软件行业的发展，不仅诞生了各种各样的编程语言，
也产生了很多编程范式，从一开始的命令式编程，到后面的面向对象
编程及函数式编程，现在，响应式编程也流行起来了。但与前几种范
式不同，响应式编程并非不建立在特定的语言基础上，很多语言，比
如Java、Kotlin、Scala等都可以进行响应式编程,尤其是在Web开发
上的应用变得越来越流行。本章将会带读者了解响应式编程的核心特
点，并介绍一个适配Kotlin且原生支持响应式开发的Web框架-
Spring5。最后还将介绍如何动手去实现一个简单响应式Web应用。

Page 821
13。1响应式编程的关键：非阻塞异步编程模型
很多人都听说过响应式编程，也使用过这种范式进行过开发，但
还是有很多人没有真正理解它背后的思想。下面我们就来看看为什么
会诞生响应式编程，以及它到底是为了解决什么问题。
假设一个用户要购物下单，我们需要先获取商品详情和用户的地
址，然后根据这些信息进行下单操作。一开始你可能会这么去实现：
data class Goods(val id: Long, val name: String, val stock: Int)
data class Address(val userld: Long, val location: String)
fun getGoodsFromDB(goodsld: Long): Goods { //获取商品详情
//模拟IO操作
Thread.sleep(1000)
return Goods(goodsld, "深入Kotlin",10)
}
fun getAddressFromDB(userld: Long): Address { //获取地址详情
Thread.sleep(1000)
//模拟IO操作
return Address(userld, "杭州")
}
fun doOrder(goods: Goods, address: Address): Long { //进行下单操作
Thread.sleep(1000)
//模拟IO操作

Page 822
return 1L
}
fun order(goodsld: Long, userld: Long) {
val goods = getGoodsFromDB(goodsld)
val address = getAddressFromDB(userld)
doOrder(goods, address)
}
这是我们通常的做法，很简单也很好理解。但是这种做法有一个
缺点：它是一种同步阻塞的方式，在第11章中我们提到了同步阻塞
的劣势。这段程序虽然简单，然而更好的方式是将获取商品信息、获
取地址这两个没有关联的操作设计成并行执行，这样就可以拥有更快
的响应速度。假设我们每次IO操作耗时是100ms，那么上面这段代码
的执行时间起码是300ms，其实理论上可以将时间控制在200ms左右。
下面我们来看看具体如何去做。

Page 823
13.1.1 使用CompletableFuture实现异步非阻塞
其实在第11章中也讲过改进这种问题的方案，那就是让这些IO
操作能够并行执行且整个过程都是非阻塞的。若要实现异步非阻塞，
在Kotlin中有两种方式，一种是利用Java标准库中的
CompletableFuture,另一种则是通过协程来实现。这里我们使用
CompletableFuture来改进上面的代码:
fun getGoodsFromDB(goodsld: Long): CompletableFuture<Goods> {
//返回的是CompletableFuture<Goods>
return
}
CompletableFuture.supplyAsync {
}
Thread.sleep(1000) //模拟IO操作
Goods(goodsld, "深入Kotlin", 10)
}
fun
getAddressFromDB(userld: Long): CompletableFuture<Address> {
//返回的是CompletableFuture<Address>
return
CompletableFuture.supplyAsync {
Thread.sleep(1000) //模拟IO操作
Address(userId, "杭州")
}
fun doOrder(goods: Goods, address: Address): CompletableFuture<Long> {
return CompletableFuture.supplyAsync {

Page 824
}
}
Thread.sleep(1000)//IO
1L
}
fun main(args: Array<String>) {
val goodsF = getGoodsFromDB(1)
val addressF = getAddressFromDB(1)
CompletableFuture.allOf(goodsF, addressF).thenApply { //O
Stream.of(goodsF, addressF).map { it.join() }.collect(Collectors.toList<Ar
}.thenApply {
doOrder(it[0] as Goods, it[1] as Address)
}.join()
在Java 8之后我们确实可以使用CompletableFuture来写异步非阻
塞代码,但是我们发现对CompletableFuture的操作却不怎么直观。
比如上面的合并操作，还需要借助Stream来得到结果，这让我们开
发变得烦琐，不容易理解。

Page 825
13。1。2使用RxKotlin进行响应式编程
一种更直观的实现异步非阻塞程序的解决方案是利用RxJava，
它同样适用于SE8之前的Java版本。你很可能知道Rx系列的类库，
它的一个主要作用就是提供统一的接口来帮助我们更方便地处理异步
数据流。其中RxJava提供了对Java的支持，但这里我们将会使用
RxKotlin,它的实现基于RxJava,但是增加了一些Kotlin独有的特
性。下面我们就利用RxKotlin来实现一个新的版本：
val threadCount = Runtime.getRuntime().availableProcessors()
val threadPoolExecutor = Executors.newFixedThreadPool(threadCount) //线
val scheduler = Schedulers.from(threadPoolExecutor)
//调度器
fun getGoodsFromDB(goodsld: Long): Observable<Goods> { //返回的是一个
return Observable.defer {
Thread.sleep(1000)
}
}
}
fun getAddressFromDB(userld: Long): Observable<Address> {
return Observable.defer {
Thread.sleep(1000)
}
//模拟IO操作
Observable.just(Goods(goodsld, "深入Kotlin", 10))
Observable.just(Address(userId, "杭州"))
//模拟IO操作

Page 826
fun rxOrder(goodsld: Long, userld: Long) {
var goods: Goods? = null
var address: Address? = null
val goodsF = getGoodsFromDB(1).subscribeOn(scheduler) //方法再指定
val addressF = getAddressFromDB(1).subscribeOn(scheduler) //方法再指
}
Observable.merge(goodsF, addressF).subscribeBy( //合并两个Observable
onNext = { when(it) {
is Goods -> goods = it
is Address -> address = it
}}，
onComplete = { //全部执行后
doOrder(goods!!, address!!)
}
看上去以上程序代码比较多，但使用RxKotlin带来了以下优势：
·将异步编程变得优雅、直观，不用对每个异步请求都执行一个回调，
同时还可以组合多个异步任务；
·不需要书写多线程代码，只需指定相应的策略便可使用多线程的功
能；
·Java6及以上的版本都可用。

Page 827
这让我们在实现需求的同时，又保持了代码的简洁和优雅。响应
式编程除了异步编程模型这个特点外，还有另一个特点，那就是数据
流处理。简单来说就是将数据处理的过程变得像流水线一样，比如
A=>B=>C=>。。。。。，后继者不需要阻塞等待结果，而是由前一个处理者
将结果通知它。
举个例子，假设下单之后需要给商家及消费者推送消息，那么用
流处理如下表示：
doOrder()
.map(doNotifyCustomer)
.map(doNotifyShop)
.map(doOther)
我们可以对原始数据进行处理，生成一个新的数据然后传递给下
一个处理者。这些处理过程都是异步非阻塞的。可以看出，流式调用
相对于回调的方式实在是优雅得太多了，不再需要编写大量的嵌套回
调函数，从而使代码更加简洁易懂。

Page 828
13。1。3响应式Web编程框架
通过上面的这些例子可以发现，应用响应式编程拥有诸多优势。
应用一些第三方响应式的类库则能帮助我们更快地进行响应式程序开
发，而不必关心异步、线程等细节，只着重于业务逻辑的处理。
既然响应式编程有这么多优点，那么为什么在以前的JavaWeb
生态中应用得却不那么广泛呢?原因有以下几点：
1)传统的Servlet容器,比如Tomcat是同步阻塞的模型(Servlet
3.1 Async IO之前);
2）主流的JavaWeb框架对响应式的支持不是很好，比如Spring
MVC、Spring Boot等,当然也有支持响应式编程的Web框架,比如
Vertx、Play! Framework;
3）一些主流的第三方类库的实现是同步阻塞的，比如连接
MySQL的驱动包，所以很难使整个系统真正做到异步非阻塞。
这些原因使得响应式编程在JavaWeb领域使用得不是很多。当
然，如果用Play!进行Web开发的话，你自然就会进行响应式编程，
因为它就是全面支持响应式编程。幸运的是，随着Spring5的发布，
这种局面将会被打破，因为Spring5开始全面拥抱响应式编程，而且
适配Kotlin。下面我们就来看看Spring5到底给我们带来了些什么。

Page 829
13。2Spring5：响应式Web框架
Spring的大名每个Java程序员都应该听过,但Spring 5或许很多
人并不是很了解，它是2017年9月才发布的，引入的一些崭新的特性，
带来的不仅仅是技术上的改变，更多的是开发思维上的变化。下面我
们就来看看Spring5的这些新特性。

Page 830
13。2。1支持响应式编程
前面一节我们已经说了响应式编程的好处，但在Spring5版本以
前它并不是原生支持响应式编程的，主要原因是底层Web容器的限
制。Tomcat等容器在Servlet 3.1支持Async IO之前,并不能做到真正
的异步非阻塞，而集成一些支持异步非阻塞的容器，比如Netty，又
相对比较复杂。然而，在Spring5发布后，你可以轻松选择自己所需
的Web容器,比如Tomcat或者Netty等,这给Spring支持响应式编程
提供了底层基础。而传统的SpringMVC并不原生支持响应式编程，
所以Spring 5引入了一个全新的Web框架,那就是Spring Webflux。
SpringWebflux主要帮助我们在框架层面实现响应式编程，它不
再使用传统基于 Servlet 实现的 HttpServletRequest 和
HttpServletResponse,而是采用全新的 ServerRequest 和
ServerResponse。同时Spring Webflux还要求请求的返回数据类型为
Flux，这是一种响应式的数据流类型，比如我们在上一节中提到的
Observable类型。
不过需要注意的一点是，Spring5并没有使用RxJava2作为程序
的响应式类库，默认集成的是Reactor库。那么这是基于什么考量呢?
其实了解响应式编程的读者应该对两个库都比较熟悉，我们不能说谁
好谁坏。但RxJava库早于Reactor库诞生,所以RxJava一开始是处于
响应式编程的探索阶段，当时Java并没有提出相应的响应式编程规
范，所以RxJava2受限于兼容RxJava遗留的历史包袱，有些方面使
用起来并不是很方便。而Reactor则完全是基于响应式流规范设计和

Page 831
实现的类库，同时JDK的最低版本是JDK8，所以可以使用JDK8提供
的流操作。如果你想写更加简洁、更加函数式的代码，Reactor或许
是个更好的选择。下面我们就来看一下SpringWebflux中最基础的两
个数据类型。
1.Mono
在传统的SpringMVC里，请求的返回直接是一个对象，比如查
询一个用户，返回的是一个User对象或者一个null。而在Spring
WebFlux则是使用了Mono，它代表的是0~1个元素，比如它的返回类
型为Mono<User>，代表返回流中只有一个数据或者为空数据。
2.Flux
在业务开发中，我们除了返回一个简单的对象外，有时还会返回
集合对象，比如查询一批用户，那么返回值为List<User>。而在
Spring WebFlux中则使用了Flux,它代表的是0~N个元素,比如它的
返回类型为Flux<User>，代表返回流中有0~N个数据。
Spring 5除了引入Spring Webflux来提供响应式编程特性以外,它
还有另一个特性让Kotlin开发者非常兴奋，那就是适配Kotlin。

Page 832
13。2。2适配Kotlin
为什么这里我们会讲Spring5而不是其他的支持响应式的Web框
架呢?除了它受众面比较广以外，另一个原因是它全面适配Kotlin。
Kotlin虽然一直在安卓开发中被广泛采用，但在Web开发中却少见其
身影，一个很重要的原因就是没有一个好的Web框架适配它。虽然在
Spring 5之前已经有了Ktor、Javalin等框架支持Kotlin,但由于相对比
较小众，并没有被广泛应用。而Spring5全面适配Kotlin，将会是
Kotlin在Web开发中大展拳脚的一个好机会，利用Spring完善的生态
及Kotlin全面兼容Java等特性,可以让很多Java开发人员转移到Kotlin
阵营。与此同时，我们还知道，Kotlin在Java的基础上拥抱了很多函
数式语言特性，比如高阶函数、DataClasses等，可以让开发的效率
变得更高，代码简洁而不失优雅。
流处理在响应式编程中占据着一个很重要的角色，而Kotlin无疑
是一个非常好的选择，它原生提供的各种流操作，结合Reactor库来
开发响应式应用将会非常便捷。基于Spring5和Kotlin编写响应式Web
应用未来可能是一个趋势。
同时Spring还支持Kotlin DSL,让我们在开发应用的时候配置更
加灵活。比如一开始在Spring中声明bean是用XML，后来变成了用注
解声明。比如下面这个例子：
@CONFIGURATION
CLASS USERBEAN {

Page 833
@BEAN //注解声明一个BEAN
VAL USERDAO = USERDAO()
@BEAN
VAL USERSERVICE = USERSERVICE(USERDAO)
}
而在Spring 5中,利用Kotlin DSL我们就可以这么做:
import
fun beans = beans {
bean<UserDao>()
bean<UserService>()
}
org.springframework.context.support.beans
beans().initialize(GenericApplication Context) //beant
我们发现，使用KotlinDSL使代码变得非常简洁，格式非常统一，
更具语义化，而且还便于统一管理。总的来看，Spring并非只是简单
地支持Kotlin而已，而是结合Kotlin的很多特性，给我们带来不一样的
编程体验。

Page 834
13。2。3函数式路由
路由配置是一个Web框架的特色，Spring从最早的XML配置到后
来的注解配置，现在也支持了函数式路由。当然，现在大多数人还是
使用注解来作为Spring的路由配置。我们不去探讨注解配置好还是函
数式路由配置好，而是着重介绍一下函数式路由能实现以前用注解无
法实现的功能。
我们知道，用注解来配置路由虽然很简单，也很直接，但是随着
微服务及模块化程序开发趋势的发展，路由分模块化统一管理是一个
需求，但用传统的注解方式却很难做到。而Spring5最新支持的函数
式路由却可以实现这个功能，而且结合KotlinDSL，语法也非常简
洁。我们来看一个简单的例子。
假设现在有 2 个 handler,分别是UserHandler 以及
CustomerHandler，里面都有3个方法。若是用注解的方式，我们会这
么做：
@Component
class UserHandler {
@RequestMapping(value = "user/getUser", method = [RequestMethod.GE
fun getUser() {}
@RequestMapping(value = "user/addUser", method = [RequestMethod.PC
fun addUser() {}
@RequestMapping(value = "user/updateUser", method = [RequestMethod

Page 835
}
fun updateUser() {}
@Component
class CustomerHandler {
@RequestMapping(value = "customer/getCustomer", method = [RequestM
fun getCustomer() {}
@RequestMapping(value = "customer/addCustomer", method = [Requestl
fun addCustomer() {}
@RequestMapping(value = "customer/updateCustomer", method = [Reque
fun updateCustomer() {}
}
我们发现这种方式虽然直接方便，但是如果Handler里面方法一
多，路由信息与方法掺杂在一起，会导致整个类变得臃肿，不易维护。
所以我们希望有一种方式既能保持声明路由的简洁性和功能性，比如
支持REST请求、指定请求及返回的数据类型等，同时又方便统一管
理。Spring5中的函数式路由能帮我们解决这个问题。下面我们就来
看一下改造后的代码：
import org.springframework.http.MediaType
@Component
class UserHandler { //类中没有路由信息

Page 836
}
fun getUser() {
fun addUser() {
fun updateUser() {
@Component
class CustomerHandler {
fun getCustomer() {}
fun addCustomer() {
fun updateCustomer() {
}
@Configuration
class Routes(userHandler: UserHandler, customerHandler: CustomerHandler
//定义路由类统一管理
@Bean
fun userRouter() = router { //¯*#*µƒÐ¶Ð
"user".nest {
GET("/getUser").nest { //#REST
accept(APPLICATION_JSON, userHandler::getUser)
}
POST("/addUser").nest {
}
accept(APPLICATION_JSON, userHandler::addUser)
PUT("/updateUser").nest {
accept(APPLICATION_JSON, userHandler::updateUser)
}

Page 837
}
}
}
@Bean
fun customerRouter() = router {
"customer".nest {
GET("/getCustomer").nest {
accept(APPLICATION_JSON, userHandler::getCustomer)
}
}
}
POST("/addCustomer").nest {
accept(APPLICATION_JSON, userHandler::addCustomer)
}
PUT("/updateCustomer").nest {
accept(APPLICATION_JSON, userHandler::updateCustomer)
}
乍一看这种方式似乎并没有简单多少，甚至感觉代码更多了。但
仔细思考一下，其实这是一个更合理的方式，它帮助我们将配置与业
务逻辑分离，而且统一管理，功能点上也没有很大的缺失。同时这种
方式也更符合函数式编程的风格，结合KotlinDSL使代码变得更加精
简优雅，可读性也更好。

Page 838
13。2。4异步数据库驱动
如果一个请求在执行过程中有一部分是同步阻塞的，那么整个应
用就不能算异步非阻塞。而我们知道，在实际的业务场景中与数据库
打交道是无法避免的，也就是说如果想要实现整个系统保证异步非阻
塞的架构，那么数据库操作也必须是异步非阻塞的，程序与数据库通
信的驱动需要支持异步非阻塞，比如现在Spring支持的MongoDB、
Redis等。但我们在很多场景用的是MySQL，由于我们使用的JDBC
驱动是同步阻塞的，所以我们将无法达到全异步非阻塞的架构。那么
如果我们需要使用MySQL，并且还要保证整个系统是异步非阻塞的
架构，就需要一个支持异步非阻塞操作的数据库驱动。
其实在Scala上已经有了这么一个驱动:postgresql-async(项目
地址:https://github.com/mauricio/postgresql-async),全异步,基于
Netty实现,同时支持MySQL和Postgresql。一些开源项目和公司也已
经在实际中使用它了,比如Quill(官网地址:http://getquill.io/),该
项目的github地址:https://github.com/mauricio/postgresql-async。有
兴趣的读者可以去看看。但是不幸的是，这个项目的作者声明已经不
再维护了。
因为受限于这个项目实现使用了很多Scala才有的数据类型，比
如 Future(与Java中的Future不一样),所以我们无法在Java以及
Kotlin的环境中使用它。但幸运的是有个Kotlin的社区人员将这个项目
用Kotlin重写了一遍,项目叫作jasync-sql,基于Java8 的
CompletableFuture,完全适配Java及 Kotlin,与 Spring 5最新的

Page 839
webflux也可以结合得很好。当然这只是一个小众项目，没有经历过
大量的测试以及实践的考验，仅供学习，不推荐大家在一些大型项目
中使用。这个项目的github地址:https://github.com/jasync-sql/jasync-
sql。
这里给大家简单演示一下,如何使用jasync-sql与Spring Webflux
相结合：
//创建一个数据库连接
Connection connection = new MySQLConnection(
new Configuration(
"root",
"localhost",
3306，
"123456"，
"test"
）
//执行连接
CompletableFuture<Connection> connectFuture = connection.connect()
//执行数据库操作
CompletableFuture<QueryResult> queryResult = connection.sendPreparedS
val result: Mono<QueryResult> = Mono.fromFuture(queryResult)

Page 840
其实书写方式跟我们以前用JDBC写数据库操作很类似，也是先
创建连接，然后执行数据库操作。不同的在于返回的数据类型，不是
简单的QueryResult,而是一个CompletableFuture<T>类型。它不同
于Future，不仅仅是异步执行的，而且获取值的时候也是非阻塞的，
同时CompletableFuture<T>类型的值转化为Webflux所要求的数据类
型很容易,比如使用Mono.fromFuture 就可以将一个
CompletableFuture类型的值转换为Mono或者Flux,所以,我们可以
使用jasync-sql来构建基于MySQL和Spring Webflux响应式应用。

Page 841
13。3Spring5响应式编程实战
本节将会带大家基于Spring WebFlux+Kotlin+MySQL,实现一个
简化的股票行情实时推送功能。本示例需要对Spring以及gradle有基
本的了解。
实现这种需求有很多方式，比如Ajax轮询、长轮询、WebSocket
等。但这个例子中我们将使用另外一种方式，那就是ServerSent
Event。它虽然不能像WebSocket一样实现双工通信，只能由服务器
不断地向客户端发送消息，但它也有自己的优势，比如基于Http协议，
会自动断开重连等。所以这里我们就通过这种方式来模拟实现股票行
情的实时推送，因为查看股票行情实时行情，往往只需要服务端向客
户端不断推送消息即可。
这里我们使用gradle来构建我们的项目，同时我们将加入13。2节
所讲的MySQL异步数据库驱动，来保证我们在使用MySQL作为存储
DB进行数据库操时也是异步非阻塞的。最终这个项目的目录结构大
致如下：
main
kotlin

Page 842
TIL
IIIL
Application.kt
handler
StockHandler.kt
JasyncPool.kt
models
StockQuotation.kt
Routes.kt
service
StockService.kt
resources
application.properties
static
_index.js
templates
index.mustache
build.gradle.kts:
import org.jetbrains.kotlin.gradle.tasks.KotlinCompile
import org.jetbrains.kotlin.gradle.plugin.KotlinPluginWrapper
group = "spring-kotlin-jasync-sql"
version="1.0-SNAPSHOT"
val springBootVersion: String by extra
plugins {

Page 843
}
application
kotlin("jvm") version "1.2.70"
kotlin("plugin.spring").version("1.2.70")
}
id("org.springframework.boot").version("1.5.9.RELEASE")
id("io.spring.dependency-management") version "1.0.5.RELEASE"
buildscript {
val springBootVersion: String by extra { "2.0.0.M7"}
dependencies {
}
classpath("org.springframework.boot:spring-boot-gradle-plugin:$spring B
repositories {
}
mavenCentral()
jcenter()
maven {
url= uri("https://repo.spring.io/milestone")
}
extra["kotlin.version"]=
repositories {
mavenCentral()
jcenter()
maven {
plugins.getPlugin(KotlinPluginWrapper::class.java).ko

Page 844
}
}
url= uri("https://repo.spring.io/snapshot")
}
maven {
url= uri("https://repo.spring.io/milestone")
}
dependencies {
compile(kotlin("stdlib-jdk8"))
}
compile("org.jetbrains.kotlin:kotlin-reflect")
compile("org.jetbrains.kotlin:kotlin-stdlib-jdk8")
compile("com.github.jasync-sql:jasync-mysql:0.8.32") //jasync-mysqlfi
compile("com.samskivert:jmustache")
compile("org.springframework.boot:spring-boot-starter-actuator:$springBoc
compile("org.springframework.boot:spring-boot-starter-webflux:$springBoo
compile("org.springframework.boot:spring-boot-starter-thymeleaf:$springB
configure<JavaPluginConvention> {
sourceCompatibility = JavaVersion.VERSION_1_8
}
tasks.with Type<KotlinCompile> {
kotlinOptions.jvmTarget="1.8" //**
接下来，我们先来定义一下model，这里我们使用dataclass：

Page 845
data class StockQuotation(
val id: Long,
val stock_id: Long, //
val stock_name: String, //
val price: Int, //*
val time: String //
）
data class StockQuotationResult(
val queryTime: String, //]
val stockQuotation: StockQuotation //
）
因为我们这里需要使用Jasync-sql，所以我们需要配置相应的数
据库连接池：
@Component
class DB {
private val configuration = Configuration( //I
"test",
"localhost",
3306，
"123456"，
"test")

Page 846
private val poolConfiguration = PoolConfiguration ( //£ULI
maxObjects = 100,
maxldle = TimeUnit. MINUTES.toMillis(15),
maxQueueSize = 10_000,
validationInterval= TimeUnit.SECONDS.toMillis(30)
）
val connectionPool = ConnectionPool(factory = MySQLConnection Factory
}
接下来，是整个项目中比较重要的一部分，那就是如何以响应式
编程的方式获取我们所需的数据：
@Component
class StockService(val db: DB) {
val repeat = Flux.interval(Duration.of Millis(1000)) // (1)
fun getStockQuotation(): Flux<StockQuotation Result> {
val query = "select * from stock_quotation order by id desc limit 1;"
fun stockQuotation(time: DateTime) = Mono.fromFuture(db.connectionP
StockQuotationResult(time.toString("YYYY-MM-dd hh:mm:ss"), transf
}
}//（5）
return repeat.flatMap {
insertStockQuotation()
stockQuotation (DateTime.now()) }

Page 847
}
private fun transRowDataToStockQuotation(rowData: RowData): StockQuc
return StockQuotation(
rowData.get("id").toString().toLong(),
rowData.get("stock_id").toString().toLong(),
rowData.get("stock_name").toString(),
rowData.get("price").toString().toInt(),
(rowData.get("time") as LocalDateTime).toString("YYYY-MM-dd hh:
}
private fun insertStockQuotation() { (6)
valmax=74000
valmin=72000
}
val price = Random().nextInt(max - min) + min
val query = "insert into stock_quotation (stock_id, stock_name, price, tim
db.connectionPool.sendPreparedStatement(query)
我们一步一步来看着代码：
1）我们创建了一个定时循环的Flux，用来控制模拟定时循环查
询数据库；
2）利用创建的数据库连接池从数据库中查询数据，返回的数据
类型是:Completable-Future<QueryResult>;
3）因为我们只需要第1列数据，所以这里使用

Page 848
it.rows.orEmpty().first()来获取第1列数据;
4)将RowData类型数据转化为我们定义的data class对象,这里
我们没有使用第三方ORM框架，需要自己手动转换；
5)使用Mono.fromFuture将一个CompletableFuture<T>类型数据
转换为Mono<T>类型；
6）模拟定时生成股票价格。
以上是这段代码的一个大致逻辑，其实重点是第2步和第5步。
我们知道,CompletableFuture相比Future一个很大的优势就是它获取
值的时候不必阻塞等待，这便保证了整个查询过程是异步非阻塞的。
同时Reactor提供了将CompletableFuture转化为Mono的方法,这样就
可以完全适配SpringWebflux所要求的返回数据的类型格式。当然，
前面我们说过，这个例子我们使用的是ServerSentEvent，所以我们
需要指定返回数据的形式：
ok().bodyToServerSentEvents(stockService.getStockQuotation())
在写完业务逻辑后，还有一块比较重要的就是Router，这里我们
将会使用Spring5最新的函数式Router。当然你也可以使用传统的、
基于Spring MVC的注解方式。所以最终我们的Router如下:
@Configuration

Page 849
class Routes(val userHandler: StockHandler) {
@Bean
fun Router() = router {
accept(MediaType.TEXT_HTML).nest {
GET("/") { ok().render("index") }
}
}
"/api.nest { //api开头的请求
GET("/getStockQuotation").nest {
accept(TEXT_EVENT_STREAM, userHandler::getStockQuotation)
}
}
resources("/**", ClassPathResource("static/")) //静态文件访问路径
}.filter { request, next ->
next.handle(request).flatMap {
if (it is RenderingResponse) RenderingResponse.from(it).build() else i
}
用这种方式定义router相对传统方式来说，更加语义化也更容易
管理，而且还支持对Response进行不同处理。
至此，整个项目的后台开发已经完成，下面我们来看一下前端部
分应该怎么做。

Page 850
虽然目前很多项目多是采用前后端分离的架构，但是这里为了更
方便演示示例，以便让大家更容易搭建这个项目，这里前端页面渲染
采用了Mustache模板引擎。另外，需要注意的一点是浏览器是否支
持Server Sent Event这种传输格式,当前IE及Edge的所有版本都不支
持，所以要测试这个例子最好使用其他浏览器。最终我们的前端代码
包括以下两个部分。
模板如下：

<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>股票行情</title>
<script src="index.js"></script>
<style>
#stockQuotations{
margin: 0 auto;
text-align: center;
}
#stockQuotations li {
list-style-type:none;
margin-bottom: 5px;
}
</style>


Page 851
</head>
<body>

<div id="stockQuotations">
</div>

</body>
</html>
js文件如下：
var eventSource = new EventSource("/api/getStockQuotation");
eventSource.onmessage = function(e) {
var li = document.createElement("li");
var data = JSON.parse(e.data);
li.innerText = ": " + data.stockQuotation.stock_id + ":" +
document.getElementById("stockQuotations").appendChild(li);
}
这里我们需要使用EventSource,而不是我们常见的Ajax方式请
求,同时用eventSource.onmessage来监听返回的数据来进行处理。
REF. Ø±ÙËZ‡: http://localhost:8282/,
我们会看到图13-1所示界面。

Page 852
D股票行情
① localhost:8282
股票代码：600519股票名称：贵州茅台当前价格：725。77
股票代码：600519股票名称：贵州茅台当前价格：737。76
股票代码：600519股票名称：贵州茅台当前价格：731。19
股票代码：600519股票名称：贵州茅台当前价格：739。93
股票代码：600519股票名称：贵州茅台当前价格：721。94
股票代码：600519股票名称：贵州茅台当前价格：736。20
股票代码：600519股票名称：贵州茅台当前价格：729。57
股票代码：600519股票名称：贵州茅台当前价格：725。47
股票代码：600519股票名称：贵州茅台当前价格：738。14
股票代码：600519股票名称：贵州茅台当前价格：724。48
。。。。。
图13-1浏览器中打开的界面
源码已经上传到github上面，有兴趣的读者可以去看看：https：//
github.com/godpan/reactive-spring-kotlin-app。
本节主要是带大家将之前所讲的知识点进行一个总结串联。自己
动手去写一个Demo，能帮助大家更好地理解相关知识点，加深印象。

Page 853
13。4本章小结
（1）响应式编程
了解什么是响应式编程的关键，响应式编程相对于传统编程范式
的优势，同时如何利用一些第三方类库来帮助我们在程序中进行响应
式开发。
（2）Spring5支持响应式编程
简单了解Spring5支持响应式编程的背景，同时介绍了它的一些
新特性，比如函数式路由以及适配Kotlin等。
（3）异步非阻塞MySQL数据库驱动
介绍了一个基于Netty且用Kotlin实现的全异步非阻塞的MySQL数
据库驱动:Jasync-sql,以及如何在Spring Webflux中使用它。
(4)Spring Webflux+Kotlin示例
了解如何Kotlin如何使用Spring Webflux来进行响应式Web应用开
发。