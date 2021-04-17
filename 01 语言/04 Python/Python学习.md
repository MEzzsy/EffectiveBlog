# 变量和简单的数据类型

## 变量

```python
message = "Hello World!!!"
print(message)
```

output:

```
Hello World!!!
```

```python
message = "Hello World!!!"
print(message)

message = "Hello Mezzsy!!!"
print(message)
```

output:

```
Hello World!!!
Hello Mezzsy!!!
```

在程序中可以随时修改变量的值，而Python始终记录变量的最新值。

### 变量的命名和使用

- 变量名只能包含字母、数字、下划线。可以以字母下划线开头，但是不能以数字开头
- 不能含有空格，可以用下划线来分隔单词
- 不能将关键字和函数名作为变量

> 建议使用小写的Python变量名

## 字符串

在Python中，用引号括起来的都是字符串，引号可以是双引号也可以是单引号。

### 修改字符串的大小写

```python
message="hello mezzsy"
print(message.title())#首字母大写
print(message.upper())#全大写
print(message.lower())#全小写
```

output：

```
Hello Mezzsy
HELLO MEZZSY
hello mezzsy
```

> Python注释是用#

### 字符串拼接

```python
a_string = "aaa"
b_string = "bbb"
c_string = a_string + " " + b_string + " !"
print(c_string)
```

output：

```
aaa bbb !
```

### 去空格

```python
value = " aaa bbb "
print(value + "ccc")  # 原文
print(value.rstrip() + "ccc")  # 尾空格去掉
print("ccc" + value.lstrip())  # 头空格去掉
print("ccc" + value.strip() + "ccc")  # 两边去掉
```

output：

```
 aaa bbb ccc
 aaa bbbccc
cccaaa bbb 
cccaaa bbbccc
```

## 数字

\*\*两个\*表示乘方

```python
v = 2 ** 4
print(v)
```

output:

```
16
```

### str()类型转换

```python
int_val = 2
v = "1 + 1 = " + int_val
print(v)


Traceback (most recent call last):
  File "/Users/mezzsy/Projects/DemoCompilation/PythonDemo/main.py", line 9, in <module>
    v = "1 + 1 = " + int_val
TypeError: can only concatenate str (not "int") to str
```

需要通过str转化为字符串，str()用于将非字符串值变为字符串值

```python
int_val = 2
v = "1 + 1 = " + str(int_val)
print(v)
```

output:

```
1 + 1 = 2
```

# 列表

```python
list = ["zzsy", "skk", "huchar", "lmh", "kk"]
print(list)
```

output:

```
['zzsy', 'skk', 'huchar', 'lmh', 'kk']
```

访问某个元素list[0]

注意，在Python中索引指定为-1，可以访问最后一个元素

```python
list = ["zzsy", "skk", "huchar", "lmh", "kk"]
print(list[-1])

output:
kk
```

-2可以访问倒数第二个，-3可以访问倒数第三个，以此类推

## 添加元素

### 在尾部添加

append()方法

```python
list = ["zzsy", "skk", "huchar", "lmh", "kk"]
list.append("mezzsy")
print(list)

output:
['zzsy', 'skk', 'huchar', 'lmh', 'kk', 'mezzsy']
```

### 插入

insert()方法

```python
list = ["zzsy", "skk", "huchar", "lmh", "kk"]
list.insert(1,"mezzsy")
print(list)

output:
['zzsy', 'mezzsy', 'skk', 'huchar', 'lmh', 'kk']
```

### 删除

#### del语句

```python
list = ["zzsy", "skk", "huchar", "lmh", "kk"]
del list[0]
print(list)

output:
['skk', 'huchar', 'lmh', 'kk']
```

#### pop()方法

pop方法用于删除尾部元素，并让你直接用它

```python
list = ["zzsy", "skk", "huchar", "lmh", "kk"]
print(list.pop())
print(list)

output:
kk
['zzsy', 'skk', 'huchar', 'lmh']
```

添加参数以删除任意位置

```python
list = ["zzsy", "skk", "huchar", "lmh", "kk"]
print(list.pop(2))
print(list)

output:
huchar
['zzsy', 'skk', 'lmh', 'kk']
```

#### 根据值删除元素

remove()方法

```python
list = ["zzsy", "skk", "huchar", "lmh", "kk"]
list.remove("zzsy")
print(list)

output:
['skk', 'huchar', 'lmh', 'kk']
```

## 排序

### 永久排序

sort()方法

如果要反序，只需传递参数`reverse=True`

```python
alist = ["zzsy", "skk", "huchar", "lmh", "kk"]
blist = [132, 14, 15, 5, 1, 51]
alist.sort()
blist.sort(reverse=True)
print(alist)
print(blist)

output:
['huchar', 'kk', 'lmh', 'skk', 'zzsy']
[132, 51, 15, 14, 5, 1]
```

### 临时排序

sorted()方法

```python
alist = ["zzsy", "skk", "huchar", "lmh", "kk"]
blist = [132, 14, 15, 5, 1, 51]
print(sorted(alist))
print(sorted(blist, reverse=True))
print("----------------------")
print(alist)
print(blist)

output:
['huchar', 'kk', 'lmh', 'skk', 'zzsy']
[132, 51, 15, 14, 5, 1]
----------------------
['zzsy', 'skk', 'huchar', 'lmh', 'kk']
[132, 14, 15, 5, 1, 51]
```

### 永久倒序

reverse()方法

```python
alist = ["zzsy", "skk", "huchar", "lmh", "kk"]
blist = [132, 14, 15, 5, 1, 51]
alist.reverse()
blist.reverse()
print(alist)
print(blist)

output:
['kk', 'lmh', 'huchar', 'skk', 'zzsy']
[51, 1, 5, 15, 14, 132]
```

### 确定长度

```python
alist = ["zzsy", "skk", "huchar", "lmh", "kk"]
blist = [132, 14, 15, 5, 1, 51]
print(len(alist))
print(len(blist))

output:
5
6
```

## 遍历

```python
alist = ["zzsy", "skk", "huchar", "lmh", "kk"]
blist = [132, 14, 15, 5, 1, 51]
for a in alist:
    print(a)
print("-----")
for b in blist:
    print(b)
    
output:    
zzsy
skk
huchar
lmh
kk
-----
132
14
15
5
1
51    
```

**Python的for循环的结束标志是缩进！！！**

## 数值列表

### range()

range(a,b)生成从a到b-1的数字

```python
for v in range(1,5):
    print(v)
    
output: 
1
2
3
4
```

如果想创建一个列表，可以用list()

```python
numbers = list(range(1, 6))
print(numbers)
print("----------------")
numbers = range(1, 6)
print(numbers)

output: 
[1, 2, 3, 4, 5]
----------------
range(1, 6)
```

另外发现，如果不加list会打印出=后面的东西

**指定步长**

```python
numbers = list(range(2, 11, 2))
print(numbers)

output: 
[2, 4, 6, 8, 10]
```

**小技巧**

前10个数的平方

```python
numbers = []
for v in range(1, 11):
    number = v ** 2;
    numbers.append(number)
print(numbers)

output: 
[1, 4, 9, 16, 25, 36, 49, 64, 81, 100]
```

**其余方法**

```python
numbers = []
for v in range(1, 11):
    number = v ** 2;
    numbers.append(number)
print("最小值：" + str(min(numbers)))
print("最大值：" + str(max(numbers)))
print("总  和：" + str(sum(numbers)))

output: 
最小值：1
最大值：100
总  和：385
```

### 列表解析

另一种创建平方数组的方法

```python
numbers = [n ** 2 for n in range(1, 11)]
print(numbers)

output: 
[1, 4, 9, 16, 25, 36, 49, 64, 81, 100]
```

## 使用列表的部分元素

Python称使用列表的部分元素为**切片**

```python
numbers = [n ** 2 for n in range(1, 11)]
print(numbers[1:4])

output: 
[4, 9, 16]
```

取出第二个到第四个元素

如果没有指定起始索引，默认从头开始

```python
numbers = [n ** 2 for n in range(1, 11)]
print(numbers[:4])

output:
[1, 4, 9, 16]
```

终止索引不指定就默认到尾结束

### 复制列表

不指定起始索引和终止索引

```python
a_numbers = [n ** 2 for n in range(1, 11)]
b_numbers = a_numbers[:]
a_numbers.append(111)
b_numbers.append(222)
print("list a :")
print(a_numbers)
print("list b :")
print(b_numbers)

output:
list a :
[1, 4, 9, 16, 25, 36, 49, 64, 81, 100, 111]
list b :
[1, 4, 9, 16, 25, 36, 49, 64, 81, 100, 222]
```

## 元组

列表里的内容可改变，而元组里的内容不可变，用圆括号来标识

如果尝试改变会报错

```python
list = (1, 2)
list[0] = 3

output:
Traceback (most recent call last):
  File "E:/Python/Hello/Hello.py", line 2, in <module>
    list[0] = 3
TypeError: 'tuple' object does not support item assignment
```

但可以重新定义

```python
list = (1, 2)
print(list)
list = (3, 4)
print(list)

output:
(1, 2)
(3, 4)
```

# if语句

```python
list = range(1, 11)
for v in list:
    if v % 2 == 0:
        print(str(v) + " 偶数")
    else:
        print(str(v) + " 奇数")
        
output:
1 奇数
2 偶数
3 奇数
4 偶数
5 奇数
6 偶数
7 奇数
8 偶数
9 奇数
10 偶数
```

## 条件测试

### 检查多个条件

#### 与

使用**and**连起来

```python
# 20以内2和3的倍数
list = range(1, 21)
for v in list:
    if (v % 2 == 0) and (v % 3 == 0):
        print(v)
        
output:
6
12
18        
```

#### 或

使用**or**连起来

```python
# 20以内2或3的倍数
list = range(1, 21)
for v in list:
    if (v % 2 == 0) or (v % 3 == 0):
        print(v)
        
output:
2
3
4
6
8
9
10
12
14
15
16
18
20        
```

### 判断是否在列表

用关键词in

```python
list = [1, 2, 3]
print(1 in list)

output:
True
```

### 判断是否不在列表

用关键词not in

```python
list = [1, 2, 3]
print(1 not in list)

output:
False	
```

### if-elif-else

```python
list = [1, 2, 3, 4, 5]
for v in list:
    if v < 2:
        print("a")
    elif v < 4:
        print("b")
    else:
        print("c")
        
output:
a
b
b
c
c
```

### 判断列表是不是空的

将列表名用在条件表达式中

```python
a_list = []
b_list = [1]
if a_list:
    print("True")
else:
    print("False")
print("---------")
if b_list:
    print("True")
else:
    print("False")
    
output:
False
---------
True    
```

如果是空的，返回false。

# 字典

在Python中，字典是一系列键值对

```python
amap = {"a": "1", "b": "2", "c": "3", "d": "4"}
print(amap["a"])

output:
1
```

## 添加键值对

```python
amap = {"a": 1, "b": 2, "c": 3, "d": 4}
print(amap)
#添加
amap["e"] = 5
amap["f"] = 6
print(amap)

output:
{'a': 1, 'b': 2, 'c': 3, 'd': 4}
{'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6}
```

## 修改

```python
amap = {"a": 1, "b": 2, "c": 3, "d": 4}
print(amap)
#修改
amap["d"] = 5
print(amap)

output:
{'a': 1, 'b': 2, 'c': 3, 'd': 4}
{'a': 1, 'b': 2, 'c': 3, 'd': 5}
```

## 删除

```python
amap = {"a": 1, "b": 2, "c": 3, "d": 4}
print(amap)
#删除
del amap["d"]
print(amap)

output:
{'a': 1, 'b': 2, 'c': 3, 'd': 4}
{'a': 1, 'b': 2, 'c': 3}
```

## 遍历

```python
amap = {
    "a": 1,
    "b": 2,
    "c": 3,
    "d": 4
}
for k, v in amap.items():
    print("Key: " + k + "\n" + "Value: "+str(v))
    print("----")

output:
Key: a
Value: 1
----
Key: b
Value: 2
----
Key: c
Value: 3
----
Key: d
Value: 4
----
```

### 遍历键

```python
amap = {
    "a": 1,
    "b": 2,
    "c": 3,
    "d": 4
}
for k in amap.keys():
    print("Key: " + k)
    
output:
Key: a
Key: b
Key: c
Key: d
```

遍历字典时，会默认遍历所有的键，因此`for k in amap.keys()`换为`for k in amap`，输出不会改变

### 遍历值

`values()`

```python
amap = {
    "a": 1,
    "b": 2,
    "c": 3,
    "d": 4,
    "e": 4
}
for v in amap.values():
    print(str(v) + "   ")
print("-------")
#除去重复元素
for v in set(amap.values()):
    print(str(v) + "   ")
    
output:
1   
2   
3   
4   
4   
-------
1   
2   
3   
4  
```

**字典里也可以嵌套列表、字典，列表里也可以嵌套字典，列表**

# 输入

input()

```python
message = input("输入:")
print(message)

output:
输入:zzsy
zzsy
```

input()接受一个参数：向用户显示的说明或提示

使用input()输入字符串，输入数值用int()

# while循环

```python
n = 1
while n <= 5:
    print(n)
    n += 1
    
output:
1
2
3
4
5    
```

使用`break`退出循环

使用`continue`跳过循环

# 函数

用关键字def定义函数

```python
def f():
	"""这是注释"""
    print("Hello !")


f()

output:
Hello !
```

> 在Python中用三引号扩起，生成有关函数的文档

## 传递实参

### 位置实参

实参和形参位置需要相同

```python
def f(name, age):
    print("Hello i am " + name + " ,i am " + str(age) + " years old.")


f("zzsy", 20)

output:
Hello i am zzsy ,i am 20 years old.
```

### 关键字实参

```python
def f(name, age):
    print("Hello i am " + name + " ,i am " + str(age) + " years old.")


f(name="zzsy", age=20)
f(age=20, name="zzsy")

output:
Hello i am zzsy ,i am 20 years old.
Hello i am zzsy ,i am 20 years old.
```

不需要考虑顺序

### 默认值

```python
def f(name="zzsy", age=20):
    print("Hello i am " + name + " ,i am " + str(age) + " years old.")


f()

output:
Hello i am zzsy ,i am 20 years old.
```

#### 可选实参

用空字符串指定默认值

```python
def f(name, age=0):
    if age:
        print("Hello i am " + name + " ,i am " + str(age) + " years old.")
    else:
        print("Hello i am " + name)


f("zzsy")
f("zzsy", 20)

output:
Hello i am zzsy
Hello i am zzsy ,i am 20 years old.
```

## 返回值

用关键字return

```python
def f(name="zzsy", age=20):
    return "Hello i am " + name + " ,i am " + str(age) + " years old."


print(f())

output:
Hello i am zzsy ,i am 20 years old.
```

## 传递列表

```python
def f(numbers):
    numbers.append(1)


numbers = list(range(1, 6))
print(numbers)
f(numbers)
print(numbers)

output:
[1, 2, 3, 4, 5]
[1, 2, 3, 4, 5, 1]
```

这种修改是永久性的

## 传递任意数量实参

用*

```python
def fsum(*numbers):
    s = 0
    for n in numbers:
        s = s + n
    return s


print(fsum(1, 2, 3))
print(fsum(1, 2, 3, 4))
print(fsum(1, 2, 3, 4, 5))

output:
6
10
15
```

## 传递任意数量关键字实参

用两个*

```python
def f(**amap):
    bmap = {}
    for k, v in amap.items():
        bmap[k] = v
    return bmap


print(f(a=1, b=2, c=3))

output:
{'a': 1, 'b': 2, 'c': 3}
```

在输入参数的时候，key不需要加引号。

## 将函数存储在模块中

### 导入模块

创建模块

Mezzsy.py

```python
def f(*numbers):
    sum = 0
    for n in numbers:
        sum = sum + n
    print(sum)
```

Hello.py

```python
import Mezzsy

Mezzsy.f(1, 2, 3)
Mezzsy.f(1, 2, 3, 4)

output:
6
10
```

### 导入函数

**语法：**

`from module_name import function_name`

通过用逗号，可根据需要从模块中导入任意数量的函数：

`from module_name import function_0,function_1,function_2`

用这种方法不需要使用句点，可以直接使用名称。

**别名：**

别名可以表示函数也可以表示模块：

`from module_name import function_name as fn`

`import module_name as mn`

**导入所有函数**

使用*

`from module_name import *`

另外这种方法可以通过名称来使用函数，不需要句点表示法。

# 类

```python
class Mezzsy():
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def hello(self):
        print("Hello " + self.name + " !")

    def how_old(self):
        print("I am " + self.age)
```

根据约定，在Python中，首字母大写的是类。

**\_\_init\_\_（）**是构造函数，第一个参数self是自动传递的，不需要传入参数。

## 创建实例

```python
zzsy = Mezzsy("zzsy", "20")
zzsy.hello()
zzsy.how_old()
print(zzsy.name, zzsy.age)

output:
Hello zzsy !
I am 20
zzsy 20
```

## 继承

一个类继承另一个类时，它将自动获得另一个类的所有属性和方法。

```python
class Person():
    def __init__(self, name, age):
        self.name = name
        self.age = age


class Man(Person):
    def __init__(self, name, age):
        super().__init__(name, age)

    def hello(self):
        print("Hello i am a man !")
```

创建子类的时候，父类必须包含在当前文件中，且位于子类的前面。

super()是一个特殊函数，将子类和父类关联起来。

### 重写方法

对于父类的方法，只要它不符合子类模拟的实物的行为，都可对其进行重写。

### 将实例作为变量

```python
class Person():
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def hello(self):
        print("Hello i am " + self.name + ", i am " + self.age)


class Man(Person):
    def __init__(self, name, age):
        super().__init__(name, age)
        self.person = Person(name, age)

    def hello(self):
        print("Hello i am a man !")
        self.person.hello()


person = Person("zzsy", "20")
person.hello()
print("-----------")
man = Man("zzsy", "20")
man.hello()

output:
Hello i am zzsy, i am 20
-----------
Hello i am a man !
Hello i am zzsy, i am 20
```

## 导入类

person.py

```python
class Person():
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def hello(self):
        print("Hello i am " + self.name + ", i am " + self.age)
```

Hello.py

```python
from person import Person

person = Person("zzsy", "20")
person.hello()

output:
Hello i am zzsy, i am 20
```

**从一个模块导入多个类**

`from module_nameimport class_0,class_1`

**导入整个模块**

`import module_name`

用句点表示法来访问需要的类。

**导入所有类**

`from module_name import *`不推荐这种用法。

# 文件

在当前目录下创建txt文件

```python
with open("txt") as file:
    contents=file.read()
    print(contents)
    
output：
a
bb
ccc
dddd
eeeee

```

要使用文件，需要用open函数打开文件。

关键词with在不再需要访问文件后将其关闭。也可以用open和close函数来打开和关闭文件，但这样如果出现了bug，导致close未执行，文件将不会关闭。**使用建议使用with**。

另外显示内容最后会出现一行空行，因为read方法到达文件末尾的时候会返回一个空字符串，这个空字符串显示出来就是一行空行。要删除可以用rstrip，`print(contents.rstrip())`

如果要指定路径，在Linux和OS X是斜杠，在window下是反斜杠。

## 逐行读取

```python
with open("txt") as file:
    for content in file:
        print(content)
        
output：
a

bb

ccc

dddd

eeeee

```

会发现空行更多了，因为文件的每行末尾有个换行，而print会有一个换行，所以导致出现许多空行。可以用rstrip消除空行。

## 小玩意

精确到100w位的π。

```python
s = ""
with open("pi_million_digits.txt") as file:
    for content in file:
        s += content.strip()

print(s[:52] + "...")#显示小数点后50位
print(len(s))

output：
3.14159265358979323846264338327950288419716939937510...
1000002
```

π是否包含自己的生日

```python
s = ""
with open("pi_million_digits.txt") as file:
    for content in file:
        s += content.strip()

print(s[:52] + "...")
print(len(s))

birthday = input("输入你的生日：")
if birthday in s:
    print("在的")
else:
    print("不在")
    
output：
3.14159265358979323846264338327950288419716939937510...
1000002
输入你的生日：980618
在的
```

## 写入文件

```python
filename = "zzsy.txt"
with open(filename, "w") as file:
    file.write("I am zzsy.")
```

open第二个参数表明要以写入模式打开这个文件。

> 读取模式r，写入模式w，附加模式a，读取和写入r+，不写默认只读。

write不会在写入的时候添加换行符，需要自己添加。

### 添加内容到文件

指定模式a

```python
filename = "zzsy.txt"
with open(filename, "a") as file:
    file.write("I am Mezzsy.")
```

## 存储

一种简单的方式就是用json开存储数据。

写入dump

```python
import json

nums = [1, 2, 3, 4, 5, 6]
with open("j.json", "w") as f:
    json.dump(nums, f)
    
生成j.json文件：
[1, 2, 3, 4, 5, 6]
```
读取load
```python
import json

with open("j.json") as f:
    nums = json.load(f)

print(nums)

output：
[1, 2, 3, 4, 5, 6]
```

# 异常

使用try-except语句。

```python
try:
    print(1 / 0)
except ZeroDivisionError:
    print("除数不能为0")
    
output：
除数不能为0
```

ZeroDivisionError除数不能为0，FileNotFoundError找不到文件。

```python
try:
    print(1 / 0)
except ZeroDivisionError:
    pass
```

可以用pass来让Python什么都不做。

