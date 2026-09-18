# 🌟总结

1. 因为H和代理Handler的类型不一样，不能直接把H改为代理Handler。所以需要把代理Handler的super class改为H。
2. Class对象中有superClass字段。受隐藏 API 限制时，普通反射可能无法取得该字段。
3. 但是可以从art虚拟机角度，通过Class对象遍历目标类的ART字段表并获取每个ArtField地址，最后将ArtField转为java层面的Field。从中取得superClass的Field。
4. 最后通过Field来修改。

# 核心思路

`ActivityThread` 通过内部的 `H`（继承 `Handler`）处理应用主线程上的部分框架消息。这种 Hook 方式先准备一个重写 `handleMessage()` 的代理，再修改代理类的父类元数据，尝试让它被识别为 `H` 的子类，最后将代理写入 `ActivityThread.mH`。

代理收到消息后打印日志，再调用原 `H.handleMessage()`。这是修改 ART 类元数据的实验性技巧，当前 Demo 仅经过静态检查，未验证设备上的运行兼容性。

# 为什么不能直接用 Handler 替换 mH

框架中的类型关系可以简化为：

```java
class H extends Handler { /* 框架消息处理 */ }
final H mH = new H();
```

`mH` 的声明类型是 `H`。如果自定义 `HProxy extends Handler`，那么 `HProxy` 和 `H` 都是 `Handler` 的子类，两者并不存在继承关系，因此普通反射赋值不能把 `HProxy` 当成 `H`。

把原 `H` 向上转型为 `Handler` 只改变引用的使用方式，不会改变对象的实际类型，也不会放宽 `mH` 的字段类型要求。这里需要处理的是代理与 `H` 的类型关系。参见 [ActivityThread 源码][activity-thread]。

# 从虚拟机看字段的存储与读写

下面以 **Android 16 的 ART** 为例。理解字段需要分清三样东西：描述字段的元数据、Java 反射返回的 `Field` 对象，以及对象中实际保存的字段值。

## 字段信息与字段值存在哪里

| 内容 | 存储位置与作用 |
| --- | --- |
| `ArtField` | ART 的原生字段元数据，记录声明类、访问标志、DEX 字段索引和字段偏移 `offset_` |
| `java.lang.reflect.Field` | Java 堆中的反射对象，保存声明类、类型、字段索引、偏移等信息，供反射操作使用 |
| 实例字段的值 | 保存在每个实例对象内部；不同实例各有一份 |
| 静态字段的值 | 保存在声明类的 `Class` 对象的静态字段区；同一个运行时类共享一份 |

`ArtField` 不保存某个实例的字段值。同一个 `count` 字段的描述可以用于读取 `a.count` 和 `b.count`，具体读到哪个值取决于传入哪个对象。基本类型字段直接保存数值，引用字段保存对象引用，而不是把目标对象嵌入字段中。[ArtField 定义][art-field]、[反射 Field 定义][reflect-field]

ART 的 `Class` 对象保存字段表地址。Android 16 的 `fields_` 指向带长度的连续 `ArtField` 数组，数组只描述该类直接声明的字段；父类声明的字段在父类自己的字段表中。实例对象则包含继承而来的字段存储空间。[Class 字段表][class-layout]

## 字段如何通过偏移定位

类链接时，ART 为字段安排存储位置，将相对对象起始位置的字节偏移写入 `ArtField.offset_`。布局会考虑父类大小、字段类型与对齐，不保证与源码声明顺序一致。[字段布局计算][field-layout]

定位过程可以简化为：

```text
实例字段位置 = 实例对象起始地址 + 字段偏移
静态字段位置 = 声明类的 Class 对象起始地址 + 字段偏移

同一个 count 字段，偏移为 δ：
a 对象 ── +δ ──> a.count 的值
b 对象 ── +δ ──> b.count 的值
```

`obj.count` 的普通读写在 DEX 中对应 `iget` / `iput` 指令族，静态字段对应 `sget` / `sput`。指令中的字段索引经解析得到运行时字段信息；确定布局后，实际读写通常按偏移完成，不需要每次按字段名搜索。[DEX 字段指令][dex-bytecode]

这里的地址公式只用于解释定位原理。对象可能随 GC 移动，引用也有 ART 自己的表示方式，不能把 Java 引用直接当作永久有效的原生地址。[对象字段访问实现][object-fields]

## 反射如何读取和修改字段

`Field.get(obj)` 和 `Field.set(obj, value)` 最终操作的仍是同一块字段存储。Android 16 中，它们进入 ART 的原生实现；以 `Field.set()` 为例：

1. **确定目标对象**：实例字段检查 `obj` 是否非空且符合声明类类型；静态字段使用声明类的 `Class` 对象，并在需要时触发类初始化。
2. **检查能否赋值**：检查值的类型，必要时对基本类型进行拆箱和允许的类型转换，并执行适用的访问权限与写入限制检查。`setAccessible(true)` 不会取消接收对象和值的类型要求。
3. **按偏移写入**：读取 `Field` 保存的偏移和类型，调用相应的存储操作；例如整数使用 `SetField32()`，对象引用使用 `SetFieldObject()`。读取则使用对应的 `GetField*()`，`Field.get()` 返回基本类型值时还会装箱。[反射读写实现][reflect-field-native]

引用字段写入还要配合 **GC 写屏障**，让垃圾回收器记录引用关系的变化；`volatile` 字段走满足其内存语义的读写路径。因此，虚拟机层面的字段修改不只是随意覆盖几个字节。[对象字段读写与屏障][object-fields]

# 修改 superClass 如何影响类型检查

Android 的 `java.lang.Class` 对象保存运行时类信息，其中包含指向父类的隐藏字段 `superClass`。修改的目标是 **`HProxy.class` 这个 Class 对象中的父类指针**，并不是普通代理实例里的某个字段。参见 [Android 16 Class 源码][class-source]。

```text
编译时的继承关系：
HProxy → Handler → Object
H      → Handler → Object

修改后的父类指针链：
HProxy → H → Handler → Object
```

Android 16 的 ART 源码中，`Class::IsSubClass()` 会沿父类链判断类型关系。因此，在能够修改相应元数据的环境中，把代理的父类指针设为 `H`，可能让相关类型检查接受它。[ART 类型检查实现][art-class]

## 如何找到隐藏字段

字段名来自 Android 的 `java.lang.Class` 源码，其中声明了 `private transient Class<? super T> superClass`。[Android 16 Class 源码][class-source]

直接调用 `Class.class.getDeclaredField("superClass")` 可能受隐藏 API 限制而抛出 `NoSuchFieldException`。`setAccessible(true)` 用于跳过 Java 访问权限检查，不能找回在查找阶段已被过滤的字段。[隐藏 API 限制][hidden-api-restrictions]

Demo 使用 `HiddenApiBypass 6.1` 枚举隐藏实例字段，再同时匹配字段名和类型：

```java
private static Field findSuperClassField() throws NoSuchFieldException {
    for (Field field : HiddenApiBypass.getInstanceFields(Class.class)) {
        if ("superClass".equals(field.getName()) && field.getType() == Class.class) {
            field.setAccessible(true);
            return field;
        }
    }
    throw new NoSuchFieldException("无法获取 Class.superClass，当前 ART 实现可能不兼容");
}
```

`getInstanceFields()` 的关键是从 ART 元数据取得字段，绕开普通反射的字段查找入口：

1. 初始化时，通过 `CoreOjClassLoader` 获取布局参考类，用 `Unsafe.objectFieldOffset()` 计算 `fields` / `iFields` 等字段的偏移；再用库自身的两个探针字段推导 `ArtField` 的大小和首项偏移。
2. 用 `Unsafe` 从传入的 `Class.class` 对象读取字段表地址，再从表头取得字段数量，逐项计算 `ArtField` 地址。
3. 把一个已有 `MethodHandle` 的 `artFieldOrMethod` 指针改为当前字段地址，再通过 `MethodHandles.reflectAs(Field.class, handle)` 得到 `Field`，只保留非静态字段。[HiddenApiBypass 6.1 实现][hidden-api]

因此，库并未预先提供名为 `superClass` 的专用接口；它提供字段枚举能力，Demo 再从结果中定位目标字段。

## 如何修改父类指针

安装的核心顺序如下，省略异常处理、失败回滚和重复安装保护；这段代码不是独立可运行的完整实现：

```java
// originalH、activityThread 和 mHField 已通过反射获取。
Class<?> hClass = Class.forName("android.app.ActivityThread$H");
Field superClassField = findSuperClassField();
if (superClassField.get(HProxy.class) != Handler.class) {
    throw new IllegalStateException("代理的原始父类不是 Handler");
}

// 先创建实例，此时构造器的直接父类仍是 Handler。
HProxy proxy = new HProxy(originalH);

// 接收对象是 HProxy.class，写入的值是 H 对应的 Class 对象。
superClassField.set(HProxy.class, hClass);

if (superClassField.get(HProxy.class) != hClass || !hClass.isInstance(proxy)) {
    throw new IllegalStateException("修改 superClass 后仍未通过 H 类型检查");
}
mHField.set(activityThread, proxy);
```

`Field.set(接收对象, 新值)` 根据字段信息，把值写入接收对象的对应位置。这里的接收对象是 **`HProxy.class`**，新值是 **`hClass`**，相当于把前者保存的父类引用从 `Handler.class` 改为 `H.class`。不能传入 `proxy`，因为它是 `Handler` 实例而非 `Class` 实例；也不能传入 `null`，因为 `superClass` 不是静态字段。

从内存布局看，这次操作可以对应为：

```text
字段描述：Class 声明的 superClass，类型为 Class，偏移为 δ
接收对象：HProxy.class
写入位置：HProxy.class 对象起始地址 + δ
写入内容：hClass 引用（指向 H 的 Class 对象）
```

这里没有修改描述 `superClass` 的 `ArtField.offset_`，而是修改了 `HProxy.class` 内的字段值。特殊之处在于：这个值对应 ART `mirror::Class` 的 `super_class_`，本身就是虚拟机用来表达父类关系的元数据。[ART Class 布局][class-layout]

随后，`mHField.set(activityThread, proxy)` 才是另一处写入：修改 `ActivityThread` 实例中的 `mH` 引用。前一步改变类元数据，后一步替换框架持有的处理器对象。

父类元数据属于整个类，修改会影响该类的所有实例。它不会重建虚方法表和实例布局，因此通过上述类型检查仍不代表已经得到完整、可靠的 `H` 子类。[ART 类实现][art-class]

[activity-thread]: https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/core/java/android/app/ActivityThread.java
[class-source]: https://android.googlesource.com/platform/libcore/+/refs/heads/android16-release/ojluni/src/main/java/java/lang/Class.java
[art-class]: https://android.googlesource.com/platform/art/+/refs/heads/android16-release/runtime/mirror/class-inl.h
[hidden-api]: https://github.com/LSPosed/AndroidHiddenApiBypass/blob/v6.1/library/src/main/java/org/lsposed/hiddenapibypass/HiddenApiBypass.java
[hidden-api-restrictions]: https://developer.android.com/guide/app-compatibility/restrictions-non-sdk-interfaces
[art-field]: https://android.googlesource.com/platform/art/+/refs/heads/android16-release/runtime/art_field.h
[reflect-field]: https://android.googlesource.com/platform/libcore/+/refs/heads/android16-release/ojluni/src/main/java/java/lang/reflect/Field.java
[class-layout]: https://android.googlesource.com/platform/art/+/refs/heads/android16-release/runtime/mirror/class.h
[field-layout]: https://android.googlesource.com/platform/art/+/refs/heads/android16-release/runtime/class_linker.cc
[dex-bytecode]: https://source.android.com/docs/core/runtime/dalvik-bytecode
[reflect-field-native]: https://android.googlesource.com/platform/art/+/refs/heads/android16-release/runtime/native/java_lang_reflect_Field.cc
[object-fields]: https://android.googlesource.com/platform/art/+/refs/heads/android16-release/runtime/mirror/object-inl.h
