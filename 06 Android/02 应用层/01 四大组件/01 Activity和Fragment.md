# 生命周期

基本使用：`onCreate(xxx)`初始化，`onResume()`注册、拉取数据，`onPause()`反注册，`onDestroy()`释放资源

1. onCreate
   在活动第一次被创建的时候调用。完成Activity的初始化，比如加载布局，绑定事件。
2. onStart
   该方法回调表示Activity正在启动，此时Activity处于可见状态，只是还没有在前台显示，因此用户也无法交互。可以简单理解为Activity已显示却无法被用户看见。
3. onResume
   此方法回调时，Activity已在在屏幕上显示UI并允许用户操作了。从流程图可见，当Activity停止后（onPause、onStop方法被调用），重新回到前台时也会调用onResume方法。可以在onResume方法中初始化一些资源，比如打开相机或开启动画。
4. onPause
   表示`activity`正在停止，此时可以做一些存储数据，停止动画等工作，注意不能太耗时，因为这会影响到新`activity`的显示，`onPause`必须先执行完，新的`activity`的`onResume`才会执行。
5. onStop
   此方法回调时，Activity即将停止或者完全被覆盖（Stopped形态），此时Activity不可见，仅在后台运行。同样地，在onStop方法可以做一些资源释放的操作，不能太耗时。 
6. onDestroy
   这个方法在活动被销毁前调用，之后的活动变为销毁状态。
7. onRestart
   这个方法在活动由停止状态（onStop）变为运行状态（onStart）之前调用，也就是活动被重新启动了。

# 常见生命周期情况

 [03 [测试日志] Android生命周期.md](03 [测试日志] Android生命周期.md) 

# Activity启动模式

 [04 [测试日志] Android启动模式研究.md](04 [测试日志] Android启动模式研究.md) 

## 启动模式

> 使用命令**adb shell dumpsys activity activities**可进行查看任务栈情况。

```xml
<activity android:name=".MainActivity"
    android:launchMode="standard"/>
```

在activity的标签中用launchMode来指定启动模式。

目前有四种启动模式：

1. **standard**，标准模式，系统默认的模式。
   每次启动Activity都会重新创建一个新的实例，不管这个实例是否存在。注意：如果用ApplicationContext去启动Activity会报错，因为标准模式的Activity会默认进入启动它的Activity的任务栈，而ApplicationContext没有任务栈，所以会有问题。解决办法就是指定FLAG—ACTIVITY—NEW—TASK标记位，这样启动的时候就会为它创建一个新的任务栈，而此时启动模式实际上是singleTask。

2. **singleTop**，栈顶复用模式。
   如果新的Activity已经位于任务栈的栈顶，那么此Activity不会被创建，同时它的onNewIntent方法会被回调，这个时候onCreate和onStart不会被调用，因为没有发生改变，onResume会被回调。
   如果新Activity已经存在但是不是位于栈顶仍然会被创建。
   **standard和singleTop启动模式都是在原任务栈中新建Activity实例，不会启动新的Task，即使你指定了taskAffinity属性。自己实验显示确实如此，而且taskAffinity的值是自己设的值。**

3. **singleTask**，栈内复用模式。
   如果Activity在一个栈中存在，那么启动此Activity不会创建实例，和singleTop一样会调用其onNewIntent方法。**app首页基本是用这个**，几个例子：

   - A以singleTask的模式启动，而其所需的任务栈是s1，s1和A都没有，那么就会先创建s1然后创建A再压入s1中。

   - 如果s1已经存在，而A不存在，那么创建A再将A压入s1中。

   - 如果s1和A都存在，且s1的情况为DABC，那么A不会被创建，而是调用栈顶并调用onNewIntent方法，同时singleTask默认有clearTop的效果，会清除A上面的Activity，此时栈情况为DA。

4. **singleInstance**，单实例模式。
   一种加强的singleTask模式，除了具有singleTask的特性，还加强了一点，就是此模式下的Activity只能单独位于一个栈中。

### 启动的Flags

启动模式不光可以在xml里设置，还可以在Intent设置标记位。通常情况下，是不需要设置的。

-   FLAG_ACTIVITY_NEW_TASK
    指定singleTask模式
-   FLAG_ACTIVITY_SINGLE_TOP
    指定singleTop模式
-   FLAG_ACTIVITY_CLEAR_TOP
    启动时，在同一个任务栈中位于它上面的活动会出栈，同时调用onNewIntent方法
-   FLAG_ACTIVITY_EXCLUDE_FROM_RECENTS
    具有这个标记位的Activity不会出现在历史列表中，等同于在XML文件中设置`android:excludeFromRecents="true"`。

### taskAffinity

taskAffinity属性可以简单的理解为任务相关性。

taskAffinity在下面两种情况时会产生效果：

1.   taskAffinity与FLAG_ACTIVITY_NEW_TASK或者singleTask配合。
     如果新启动Activity的taskAffinity和栈的taskAffinity相同则加入到该栈中；如果不同，就会创建新栈。
2.   taskAffinity与allowTaskReparenting配合。
     如果allowTaskReparenting为true，举个例子，2个应用A和B，A启动B的C，按home键回到桌面，再打开B会显示C。可以这么理解，由于A启动了C，这个时候C只能运行在A的任务栈中，但C属于B，当B启动时，B会创建自己的任务栈，这个时候系统发现C需要的任务栈已经创建了，那么就会把C从A的任务栈移到B中。

taskAffinity介绍：

- 这个参数标识了一个Activity所需任务栈的名字，默认情况下，所有Activity所需的任务栈的名字为应用的包名
- 可以单独指定每一个Activity的taskAffinity属性覆盖默认值
- 一个任务的affinity决定于这个任务的根activity（root activity）的taskAffinity
- 在概念上，具有相同的affinity的activity（即设置了相同taskAffinity属性的activity）属于同一个任务
- 为一个activity的taskAffinity设置一个空字符串，表明这个activity不属于任何task

### 🌟启动模式和任务栈总结

1.   启动模式的效果在上面已经说明。
2.   taskAffinity标识了一个Activity的任务栈，一个任务栈对应任务管理器的一个卡片。
3.   未指定任务栈时，默认在当前任务栈启动Activity。指定任务栈时会创建相应的任务栈（如无），然后根据启动模式执行Activity的启动效果。
4.   singleInstance模式下，任务栈只能有一个Activity实例。当singleInstance启动默认任务栈Activity的时候，默认任务栈Activity会在默认任务栈中启动，而不是singleInstance对应的任务栈。
5.   singleInstance模式下，如果启动相同任务栈名的Activity，该Activity不会出现在singleInstance的任务栈下，而是起一个新的任务栈，该任务栈名相同，但是id不同。

## 几个问题

**MainActivity启动了CActivity，(当前在C界面)按下home键，再点击应用图标启动的是main，这可能是什么原因造成的？**

C的启动模式为SingleTask。

> MainActivity启动，进入应用程序默认的任务栈，启动C，C进入自己的任务栈。按Home键，返回桌面，再按图标进入（个人理解：点击图标默认进入默认的任务栈），此时显示MainActivity。
>
> 那么C哪去了？
>
> 自己实践发现：在手机的任务管理器，一个任务栈对应一个任务。通过任务管理器切换可以回到CActivity。

# IntentFilter的匹配规则

本节讨论通过 `startActivity()` 隐式启动 Activity 的场景。

IntentFilter 从 `action`、`category`、`data` 三个方面匹配 Intent。三项必须在**同一个** `<intent-filter>` 中全部通过，不能分别匹配不同过滤器后拼凑结果。一个 Activity 可以声明多个过滤器，通过任意一个即可成为候选 Activity；

## action匹配规则

1. Intent 显式指定的 action 必须与过滤器中的某个 `<action>` 字符串完全一致，区分大小写。
2. 一个过滤器可以声明多个 action，Intent 的 action 匹配其中任意一个即可。
3. 一个 Intent 同时只有一个 action 值，但可以多次调用 `setAction()`；后一次会覆盖前一次。

例如：

```java
Intent intent = new Intent();
intent.setAction("com.mezzsy.test.intentfilter.OLD_ACTION");
// 覆盖旧值，最终 action 为 ACTION。
intent.setAction("com.mezzsy.test.intentfilter.ACTION");
```

允许未指定 action 的 Intent 在过滤器至少包含一个 action 时通过这一项测试。

## category匹配规则

1. Intent 中的每一个 category 都必须出现在同一个过滤器中，字符串匹配区分大小写。
2. 过滤器可以声明 Intent 没有携带的 category，不影响匹配。即 Intent 的 category 集合必须是过滤器 category 集合的子集。
3. Intent 没有 category 时，基础 category 测试可以通过；但隐式启动 Activity 还有下面的 `DEFAULT` 要求。

`startActivity()` 解析隐式 Intent 时使用 `MATCH_DEFAULT_ONLY`，只考虑包含 `android.intent.category.DEFAULT` 的过滤器。因此，**用于接收这类隐式启动的 `<intent-filter>` 必须声明 `DEFAULT`**，自定义 category 不能替代它。调用方不必手动执行 `addCategory(Intent.CATEGORY_DEFAULT)`，这也不表示系统会修改 Intent 对象、往其 categories 中加入 `DEFAULT`。[官方 API 说明](https://developer.android.com/reference/android/content/pm/PackageManager#MATCH_DEFAULT_ONLY)

## data匹配规则

data 匹配同时考虑 **URI 和 MIME 类型**。两者都可以为空，是否需要提供取决于过滤器的声明；`putExtra()` 传入的附加参数不参与这项匹配。

`<data>` 的常用属性如下，并不要求全部填写：

```xml
<data
    android:scheme="string"
    android:host="string"
    android:port="string"
    android:path="string"
    android:pathPattern="string"
    android:pathPrefix="string"
    android:mimeType="string"/>
```

`mimeType` 表示媒体类型，如 `image/png`、`text/plain`；过滤器也可以使用 `image/*`、`*/*` 等通配类型。

### URI及其匹配属性

常见的带主机名的 URI 可以写成下面的形式，方括号表示可选部分：

```text
scheme://host[:port][/path][?query][#fragment]
```

这不是所有 URI 的必备结构。例如 `tel:12345`、`mailto:user@example.com` 都没有 host，仍是合法 URI；没有 scheme 的相对 URI 引用也不能一概判为无效。

| 属性 | 匹配含义 |
| --- | --- |
| `scheme` | 协议或方案，如 `http`、`content`、`tel` |
| `host` | 主机名，如 `www.example.com` |
| `port` | 端口号；未声明时不限制端口 |
| `path` | 精确匹配完整路径，如 `/articles/123` |
| `pathPrefix` | 匹配路径前缀，如 `/articles/` |
| `pathPattern` | 使用简单模式匹配完整路径 |

这些 URI 匹配属性存在依赖：过滤器未声明 `scheme` 时，`host`、`port`、路径属性不起作用；未声明 `host` 时，`port` 和路径属性不起作用。只声明 `scheme="http"`，就只检查 URI 的 scheme，不限制 host 和 path。Android 的 scheme、host 及 MIME 类型匹配区分大小写，建议统一使用小写。

`pathPattern` 使用简单 glob 规则，不支持完整正则表达式：`.` 表示任意单个字符，`*` 表示前一个字符重复零次或多次，`.*` 表示任意长度的字符序列。不能把单独的 `*` 理解为任意字符串，也不要套用正则表达式的分组、选择或回溯规则。XML 中匹配字面量 `*` 写作 `\\*`，匹配字面量反斜杠写作 `\\\\`；例如匹配 `/articles/` 下的路径可以使用 `android:pathPattern="/articles/.*"`。[官方属性说明](https://developer.android.com/guide/topics/manifest/data-element)

### URI与MIME类型的组合规则

下表按 Intent 的内容区分常见情况；其中 MIME 类型包含显式设置的类型，以及系统从 `content:` URI 的 ContentProvider 推断出的类型。

| Intent 的内容 | 通过 data 匹配的条件 |
| --- | --- |
| URI 和 MIME 类型都为空 | 过滤器也未声明 URI 和 MIME 类型 |
| 只有 URI，没有 MIME 类型 | URI 满足过滤器的 URI 条件，且过滤器未声明 MIME 类型 |
| 只有 MIME 类型，没有 URI | 类型匹配，且过滤器未声明 URI scheme 条件 |
| URI 和 MIME 类型都有 | 类型必须匹配；URI 也必须满足过滤器的 URI 条件。如果过滤器只声明 MIME 类型、未声明 scheme，还可接受 `content:` 或 `file:` URI |

因此，“Intent 必须有 data”是错误的；同样，过滤器未声明 data，也不是接受任意 URI 或 MIME 类型，而是要求两者都为空。[官方 data 匹配规则](https://developer.android.com/guide/components/intents-filters#DataTest)

设置数据时，`setData()` 会清除已有的 MIME 类型，`setType()` 会清除已有的 URI。需要同时设置两者时使用 `setDataAndType()`：

```java
intent.setDataAndType(Uri.parse("content://com.example.provider/images/1"), "image/png");
```

这里假设 URI 指向有效的 ContentProvider 数据；示例只展示设置方式。[Intent API 说明](https://developer.android.com/reference/android/content/Intent#setDataAndType(android.net.Uri,%20java.lang.String))

### 多个data元素共同组成过滤条件

同一个 `<intent-filter>` 下的多个 `<data>` 会共同组成一个过滤器，不能理解为“完整匹配某一行 `<data>` 就行”。例如：

```xml
<intent-filter>
    <action android:name="com.mezzsy.test.intentfilter.ACTION" />
    <category android:name="android.intent.category.DEFAULT" />
    <data android:scheme="http" android:host="a.example.com" />
    <data android:scheme="https" android:host="b.example.com" />
</intent-filter>
```

这里的 scheme 集合是 `http`、`https`，host 集合是 `a.example.com`、`b.example.com`，所以 `http://b.example.com`、`https://a.example.com` 也能通过 URI 匹配。如果只想接受 `http://a.example.com` 和 `https://b.example.com` 两种组合，应拆成两个独立的 `<intent-filter>`，各自声明 action、`DEFAULT` 和对应 data。[官方合并规则](https://developer.android.com/guide/topics/manifest/data-element)

## 例子1

以下示例由同一应用内的 Activity 发起调用。过滤器只要求 HTTP URI，没有声明 MIME 类型。

```xml
<activity
    android:name=".basic.activity.intentfilter.SimpleIntentFilterActivity"
    android:exported="false">
    <intent-filter>
        <action android:name="com.mezzsy.test.intentfilter.ACTION" />
        <!-- 隐式启动 Activity 时，只考虑包含 DEFAULT 的过滤器。 -->
        <category android:name="android.intent.category.DEFAULT" />
        <category android:name="com.mezzsy.test.intentfilter.category" />

        <data android:scheme="http" />
    </intent-filter>
</activity>
```

```java
public void onClick(View v) {
    Log.i(TAG, "onClick:");
    Intent intent = new Intent();
    intent.setAction("com.mezzsy.test.intentfilter.ACTION");
    intent.addCategory("com.mezzsy.test.intentfilter.category");
    intent.setData(Uri.parse("http://www.baidu.com"));
    try {
        startActivity(intent);
    } catch (ActivityNotFoundException e) {
        Log.i(TAG, "onClick: no such activity.");
    }
}
```

```
I/隐式启动: onClick:
I/隐式启动: onCreate: 
```

这里能启动，是因为 action 相同、Intent 携带的 category 已在过滤器中声明、过滤器包含 `DEFAULT`，并且 URI 的 scheme 为 `http`、MIME 类型为空。过滤器没有约束 host 和 path，因此 `www.baidu.com` 可以通过；这不代表已经声明的 URI 条件可以不匹配。

`android:exported="false"` 允许同应用内调用。若要接收其他应用的调用，需要按用途设置为 `true`。对于 targetSdkVersion >= 31 的应用，带 `<intent-filter>` 的 Activity 必须显式声明 `android:exported`。[Android 12 变更说明](https://developer.android.com/about/versions/12/behavior-changes-12#exported)

## 例子2

沿用例子1的过滤器，只在 Intent 中多添加一个 category：

```java
public void onClick(View v) {
    Log.i(TAG, "onClick:");
    Intent intent = new Intent();
    intent.setAction("com.mezzsy.test.intentfilter.ACTION");
    intent.addCategory("com.mezzsy.test.intentfilter.category");
    intent.addCategory("com.mezzsy.test.intentfilter.category2");
    intent.setData(Uri.parse("http://www.baidu.com"));
    try {
        startActivity(intent);
    } catch (ActivityNotFoundException e) {
        Log.i(TAG, "onClick: no such activity.");
    }
}
```

```
I/隐式启动: onClick:
I/隐式启动: onClick: no such activity.
```

该过滤器没有声明 `com.mezzsy.test.intentfilter.category2`，因此 category 匹配失败，不能解析到示例 Activity。假设没有其他可处理这个 Intent 的 Activity，`startActivity()` 会抛出 `ActivityNotFoundException`，得到上面的日志。

## 不携带data的例子

只声明 action 和 `DEFAULT`，不声明 `<data>`：

```xml
<activity
    android:name=".basic.activity.intentfilter.SimpleIntentFilterActivity"
    android:exported="false">
    <intent-filter>
        <action android:name="com.mezzsy.test.intentfilter.OPEN" />
        <category android:name="android.intent.category.DEFAULT" />
    </intent-filter>
</activity>
```

同应用内可以这样隐式启动，不需要调用 `setData()` 或 `setType()`：

```java
Intent intent = new Intent("com.mezzsy.test.intentfilter.OPEN");
startActivity(intent);
```

双方都没有 URI 和 MIME 类型，data 测试通过。如果反而给这个 Intent 设置了 URI 或 MIME 类型，就无法匹配这个过滤器。

# Fragment

## 生命周期

碎片相比活动多了几个周期。

1. **onAttach**，当碎片和活动建立关联的时候调用。
2. **onCreate**
3. **onCreateView**，为碎片创建视图（加载布局）的时候调用。
4. **onActivityCreated**，确保与碎片相关联的活动一定已经创建完毕的时候调用。
5. **onStart**
6. **onResume**，Fragment中的onResume和Activity不一样，即使Fragment是不可见的（如ViewPager中的Fragment），但也还是会调用此周期，
7. **onPause**
8. **onStop**
9. **onDestroyView**，当与碎片关联的视图被移除的时候调用。
10. **onDestroy**
11. **onDetach**，当碎片和活动解除关联的时候调用。

可见与获取焦点相关的生命周期与Fragment无关，只与其Activty有关。

### 【测试日志】Activity和Fragment一起的生命周期

在Activity中添加Fragment

```kotlin
override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    setContentView(R.layout.activity_test_fragment_life)
    Log.d(TAG, "onCreate: ")

    supportFragmentManager.beginTransaction()
            .add(R.id.fragment_container, firstFragment).commit();
}
```

```
2023-04-18 23:13:08.444 25050-25050/? D/测试FragmentActivity: onCreate: before
2023-04-18 23:13:08.448 25050-25050/? D/测试FragmentActivity: onCreate: after
2023-04-18 23:13:08.448 25050-25050/? D/测试FragmentActivity: onStart: before
2023-04-18 23:13:08.448 25050-25050/? I/firstFragment: onAttach: 
2023-04-18 23:13:08.448 25050-25050/? I/firstFragment: onCreate: 
2023-04-18 23:13:08.448 25050-25050/? I/firstFragment: onCreateView: 
2023-04-18 23:13:08.449 25050-25050/? I/firstFragment: onActivityCreated: 
2023-04-18 23:13:08.449 25050-25050/? I/firstFragment: onStart: 
2023-04-18 23:13:08.449 25050-25050/? D/测试FragmentActivity: onStart: after
2023-04-18 23:13:08.449 25050-25050/? D/测试FragmentActivity: onResume: before
2023-04-18 23:13:08.449 25050-25050/? D/测试FragmentActivity: onResume: after
2023-04-18 23:13:08.450 25050-25050/? I/firstFragment: onResume: 
// 按返回键
2023-04-18 23:13:22.831 25050-25050/? D/测试FragmentActivity: onPause: before
2023-04-18 23:13:22.831 25050-25050/? I/firstFragment: onPause: 
2023-04-18 23:13:22.831 25050-25050/? D/测试FragmentActivity: onPause: after
2023-04-18 23:13:23.386 25050-25050/? D/测试FragmentActivity: onStop: before
2023-04-18 23:13:23.386 25050-25050/? I/firstFragment: onStop: 
2023-04-18 23:13:23.386 25050-25050/? D/测试FragmentActivity: onStop: after
2023-04-18 23:13:23.386 25050-25050/? D/测试FragmentActivity: onDestroy: before
2023-04-18 23:13:23.387 25050-25050/? I/firstFragment: onDestroyView: 
2023-04-18 23:13:23.387 25050-25050/? I/firstFragment: onDestroy: 
2023-04-18 23:13:23.387 25050-25050/? I/firstFragment: onDetach: 
2023-04-18 23:13:23.387 25050-25050/? D/测试FragmentActivity: onDestroy: after
```

从这两行可以看出（注：fragment是在onCreate回调中添加）：

```
2023-04-18 23:13:08.444 25050-25050/? D/测试FragmentActivity: onCreate: before
2023-04-18 23:13:08.448 25050-25050/? D/测试FragmentActivity: onCreate: after
```

fragment的添加是有个post操作的，并不是立即生效。

### 【测试日志】AB两个Fragment

```
2023-04-19 22:17:27.256 25739-25739/? I/firstFragment: onAttach: 
2023-04-19 22:17:27.256 25739-25739/? I/firstFragment: onCreate: 
2023-04-19 22:17:27.256 25739-25739/? I/firstFragment: onCreateView: 
2023-04-19 22:17:27.257 25739-25739/? I/firstFragment: onActivityCreated: 
2023-04-19 22:17:27.257 25739-25739/? I/firstFragment: onStart: 
2023-04-19 22:17:27.259 25739-25739/? I/firstFragment: onResume: 
// 替换成SecondFragment
2023-04-19 22:17:38.688 25739-25739/? I/secondFragment: onAttach: 
2023-04-19 22:17:38.689 25739-25739/? I/secondFragment: onCreate: 
2023-04-19 22:17:38.689 25739-25739/? I/firstFragment: onPause: 
2023-04-19 22:17:38.690 25739-25739/? I/firstFragment: onStop: 
2023-04-19 22:17:38.690 25739-25739/? I/firstFragment: onDestroyView: 
2023-04-19 22:17:38.692 25739-25739/? I/firstFragment: onDestroy: 
2023-04-19 22:17:38.692 25739-25739/? I/firstFragment: onDetach: 
2023-04-19 22:17:38.693 25739-25739/? I/secondFragment: onCreateView: 
2023-04-19 22:17:38.694 25739-25739/? I/secondFragment: onActivityCreated: 
2023-04-19 22:17:38.694 25739-25739/? I/secondFragment: onStart: 
2023-04-19 22:17:38.694 25739-25739/? I/secondFragment: onResume: 
// 按返回键
2023-04-19 22:17:52.184 25739-25739/? I/secondFragment: onPause: 
2023-04-19 22:17:52.748 25739-25739/? I/secondFragment: onStop: 
2023-04-19 22:17:52.749 25739-25739/? I/secondFragment: onDestroyView: 
2023-04-19 22:17:52.749 25739-25739/? I/secondFragment: onDestroy: 
2023-04-19 22:17:52.749 25739-25739/? I/secondFragment: onDetach: 
```

```kotlin
supportFragmentManager
        .beginTransaction()
        .remove(firstFragment)
        .add(R.id.fragment_container, secondFragment)
        .commit()
```

### 【测试日志】AB两个Fragment addToBackStack(null)

```
2023-04-19 22:30:56.452 29263-29263/? I/firstFragment: onAttach: 
2023-04-19 22:30:56.452 29263-29263/? I/firstFragment: onCreate: 
2023-04-19 22:30:56.452 29263-29263/? I/firstFragment: onCreateView: 
2023-04-19 22:30:56.452 29263-29263/? I/firstFragment: onActivityCreated: 
2023-04-19 22:30:56.453 29263-29263/? I/firstFragment: onStart: 
2023-04-19 22:30:56.453 29263-29263/? I/firstFragment: onResume: 
// 替换成SecondFragment
2023-04-19 22:30:58.883 29263-29263/? I/secondFragment: onAttach: 
2023-04-19 22:30:58.883 29263-29263/? I/secondFragment: onCreate: 
2023-04-19 22:30:58.883 29263-29263/? I/firstFragment: onPause: 
2023-04-19 22:30:58.883 29263-29263/? I/firstFragment: onStop: 
2023-04-19 22:30:58.884 29263-29263/? I/firstFragment: onDestroyView: 
2023-04-19 22:30:58.884 29263-29263/? I/secondFragment: onCreateView: 
2023-04-19 22:30:58.885 29263-29263/? I/secondFragment: onActivityCreated: 
2023-04-19 22:30:58.885 29263-29263/? I/secondFragment: onStart: 
2023-04-19 22:30:58.886 29263-29263/? I/secondFragment: onResume: 
// 按返回键
2023-04-19 22:31:01.044 29263-29263/? I/secondFragment: onPause: 
2023-04-19 22:31:01.044 29263-29263/? I/secondFragment: onStop: 
2023-04-19 22:31:01.044 29263-29263/? I/secondFragment: onDestroyView: 
2023-04-19 22:31:01.045 29263-29263/? I/secondFragment: onDestroy: 
2023-04-19 22:31:01.045 29263-29263/? I/secondFragment: onDetach: 
2023-04-19 22:31:01.045 29263-29263/? I/firstFragment: onCreateView: 
2023-04-19 22:31:01.045 29263-29263/? I/firstFragment: onActivityCreated: 
2023-04-19 22:31:01.045 29263-29263/? I/firstFragment: onStart: 
2023-04-19 22:31:01.045 29263-29263/? I/firstFragment: onResume: 
// 按返回键
2023-04-19 22:31:04.319 29263-29263/? I/firstFragment: onPause: 
2023-04-19 22:31:04.319 29263-29263/? I/firstFragment: onStop: 
2023-04-19 22:31:04.319 29263-29263/? I/firstFragment: onDestroyView: 
2023-04-19 22:31:04.320 29263-29263/? I/firstFragment: onDestroy: 
2023-04-19 22:31:04.320 29263-29263/? I/firstFragment: onDetach: 
```

```kotlin
supportFragmentManager
        .beginTransaction()
        .replace(R.id.fragment_container, firstFragment)
        .addToBackStack(null)
        .commit()

findViewById<Button>(R.id.btn_replace_fragment).setOnClickListener {
    supportFragmentManager
            .beginTransaction()
            .replace(R.id.fragment_container, secondFragment)
            .addToBackStack(null)
            .commit()
}
```

## Activity和Fragment的通信

- 如果Activity中包含自己管理的Fragment的引用，可以通过引用直接访问所有的Fragment的public方法
- 如果Activity中未保存任何Fragment的引用，那么没关系，每个Fragment都有一个唯一的TAG或者ID，可以通过getFragmentManager.findFragmentByTag()或者findFragmentById()获得任何Fragment实例，然后进行操作
- Fragment中可以通过getActivity()得到当前绑定的Activity的实例，然后进行操作。
- EventBus等等观察者模式

## Fragment解析

### 小结

1. 通过fragmentManager开启一个事务记录操作并提交事务
2. 初始化 Fragment：`FragmentManager` 执行事务，关联宿主 Activity，回调 `onAttach()` → `onCreate()`。
3. 创建并挂载 View：通过 `onCreateView()` 创建视图，将其加入指定容器，再回调 `onViewCreated()`。
4. 推进生命周期：根据宿主状态和事务限制，继续执行 `onStart()`、`onResume()`。

### Transaction的开启

```kotlin
private fun addFragment() {
    val fragmentManager = supportFragmentManager
    val transaction = fragmentManager.beginTransaction()
}
```

```java
public FragmentTransaction beginTransaction() {
    return new BackStackRecord(this);//this为fragmentManager
}
```

Transaction的具体类型为BackStackRecord。

### Fragment的replace

Fragment的添加分为静态添加和动态添加。

静态添加就是在布局文件里写死的fragment标签，动态添加则是在运行期，往一个容器里动态地添加fragment。

最长参数的replace方法为：

```java
public final FragmentTransaction replace(@IdRes int containerViewId,
        @NonNull Class<? extends Fragment> fragmentClass,
        @Nullable Bundle args, @Nullable String tag) {
    return replace(containerViewId, createFragment(fragmentClass, args), tag);
}
```

第一个参数表示容器id，第二个为Fragment的class对象，第三个为传入的构造参数，第四个为fragment的tag。

```java
@NonNull
private Fragment createFragment(@NonNull Class<? extends Fragment> fragmentClass,
        @Nullable Bundle args) {
    //...
    Fragment fragment = mFragmentFactory.instantiate(mClassLoader, fragmentClass.getName());
    if (args != null) {
        fragment.setArguments(args);
    }
    return fragment;
}
```

```java
public Fragment instantiate(@NonNull ClassLoader classLoader, @NonNull String className) {
    try {
        Class<? extends Fragment> cls = loadFragmentClass(classLoader, className);
        return cls.getConstructor().newInstance();
    } 
  	//。。。catch
}
```

createFragment方法内部会根据传入的Class对象，反射创建一个Fragment对象，调用的是无参构造方法，所以自定义Fragment时，不能没有无参构造方法。如果需要传递参数，可以通过Bundle。

最终的replace方法：

```java
public FragmentTransaction replace(@IdRes int containerViewId, @NonNull Fragment fragment,
        @Nullable String tag)  {
    if (containerViewId == 0) {
        throw new IllegalArgumentException("Must use non-zero containerViewId");
    }
    doAddOp(containerViewId, fragment, tag, OP_REPLACE);
    return this;
}
```

```java
void doAddOp(int containerViewId, Fragment fragment, @Nullable String tag, int opcmd) {
    final Class<?> fragmentClass = fragment.getClass();
    final int modifiers = fragmentClass.getModifiers();
  	
  	// 传入的Fragment需要时public的静态类。
    if (fragmentClass.isAnonymousClass() || !Modifier.isPublic(modifiers)
            || (fragmentClass.isMemberClass() && !Modifier.isStatic(modifiers))) {
        throw new IllegalStateException("Fragment " + fragmentClass.getCanonicalName()
                + " must be a public static class to be  properly recreated from"
                + " instance state.");
    }

  	// tag只能添加，不能替换。
    if (tag != null) {
        if (fragment.mTag != null && !tag.equals(fragment.mTag)) {
            throw new IllegalStateException("Can't change tag of fragment "
                    + fragment + ": was " + fragment.mTag
                    + " now " + tag);
        }
        fragment.mTag = tag;
    }

  	// fragment的容器id只能添加，不能替换。
    if (containerViewId != 0) {
        if (containerViewId == View.NO_ID) {
            throw new IllegalArgumentException("Can't add fragment "
                    + fragment + " with tag " + tag + " to container view with no id");
        }
        if (fragment.mFragmentId != 0 && fragment.mFragmentId != containerViewId) {
            throw new IllegalStateException("Can't change container ID of fragment "
                    + fragment + ": was " + fragment.mFragmentId
                    + " now " + containerViewId);
        }
        fragment.mContainerId = fragment.mFragmentId = containerViewId;
    }

    addOp(new Op(opcmd, fragment));
}
```

最终将操作指令opcmd（此时是OP_REPLACE）和fragment封装成Op对象。

```java
void addOp(Op op) {
    mOps.add(op);
    op.mEnterAnim = mEnterAnim;
    op.mExitAnim = mExitAnim;
    op.mPopEnterAnim = mPopEnterAnim;
    op.mPopExitAnim = mPopExitAnim;
}
```

将封装的op对象放入List中。

#### 小结

FragmentTransaction内部有个存放Op对象的List。一次FragmentTransaction可以执行多次操作，这些操作会将临时存放在List中，等待提交执行。

FragmentTransaction除了可以设置操作，还可以设置Fragment的一些动画。

### commit提交

commitallowingstateloss和commit的区别见下，这里分析commit。

commit会调用commitInternal方法。

```java
//allowStateLoss，commit传的是false，commitallowingstateloss传的是true
int commitInternal(boolean allowStateLoss) {
    if (mCommitted) throw new IllegalStateException("commit already called");
    //...
    mCommitted = true;
    if (mAddToBackStack) {
        mIndex = mManager.allocBackStackIndex();
    } else {
        mIndex = -1;
    }
    mManager.enqueueAction(this, allowStateLoss);
    return mIndex;
}
```

从第一行代码可以看出commit不允许多次提交。

```java
void enqueueAction(@NonNull OpGenerator action, boolean allowStateLoss) {
    // 。。。检查状态是否丢失
    synchronized (mPendingActions) {
        // 。。。检查状态是否丢失
        mPendingActions.add(action);
        scheduleCommit();
    }
}
```

BackStackRecord实现了OpGenerator接口，将BackStackRecord放入mPendingActions中。

```java
void scheduleCommit() {
    synchronized (mPendingActions) {
        //。。。
        if (postponeReady || pendingReady) {
            mHost.getHandler().removeCallbacks(mExecCommit);
            mHost.getHandler().post(mExecCommit);
            updateOnBackPressedCallbackEnabled();
        }
    }
}
```

post了一个mExecCommit，mExecCommit会执行execPendingActions方法：

```java
boolean execPendingActions(boolean allowStateLoss) {
    ensureExecReady(allowStateLoss);

    boolean didSomething = false;
  	// generateOpsForPendingActions方法内部将mPendingActions的内容转移到mTmpRecords
    while (generateOpsForPendingActions(mTmpRecords, mTmpIsPop)) {
        mExecutingActions = true;
        try {
          	//删除重复操作，优化处理。
            removeRedundantOperationsAndExecute(mTmpRecords, mTmpIsPop);
        } finally {
            cleanupExec();
        }
        didSomething = true;
    }
		//。。。
    return didSomething;
}
```

removeRedundantOperationsAndExecute会调用executeOpsTogether，而executeOpsTogether方法会调用executeOps方法。

```java
private static void executeOps(@NonNull ArrayList<BackStackRecord> records,
        @NonNull ArrayList<Boolean> isRecordPop, int startIndex, int endIndex) {
    for (int i = startIndex; i < endIndex; i++) {
        final BackStackRecord record = records.get(i);
        final boolean isPop = isRecordPop.get(i);
      	// isPop一般为false
        if (isPop) {
            //...
        } else {
            record.bumpBackStackNesting(1);
            record.executeOps();
        }
    }
}
```

BackStackRecord的executeOps方法：

```java
void executeOps() {
    final int numOps = mOps.size();
    for (int opNum = 0; opNum < numOps; opNum++) {
        final Op op = mOps.get(opNum);
        final Fragment f = op.mFragment;
        if (f != null) {
            f.setNextTransition(mTransition);
        }
        switch (op.mCmd) {
            case OP_ADD: //。。。
            case OP_REMOVE: //。。。
            case OP_HIDE: //。。。
            case OP_SHOW: //。。。
            case OP_DETACH: //。。。
            case OP_ATTACH: //。。。
            case OP_SET_PRIMARY_NAV: //。。。
            case OP_UNSET_PRIMARY_NAV: //。。。
            case OP_SET_MAX_LIFECYCLE: //。。。
            default: //。。。
        }
        //。。。
    }
    if (!mReorderingAllowed) {
        mManager.moveToState(mManager.mCurState, true);
    }
}
```

switch里没有OP_REPLACE是因为在removeRedundantOperationsAndExecute方法内部被拆分为remove和add（如果此fragment已经添加，那么移除此操作）。

最后会调用`void moveToState(int newState, boolean always)`方法，在进行传参的时候会传`mManager.mCurState`，mManager是FragmentManager，mCurState表示当前的状态，mCurState的赋值是在FragmentActivity的生命周期回调里进行的，见下“Fragment状态的改变”。

```java
void moveToState(int newState, boolean always) {
   	//。。。

    mCurState = newState;

    for (Fragment f : mFragmentStore.getFragments()) {
        moveFragmentToExpectedState(f);
    }
		//...
}
```

```java
void moveFragmentToExpectedState(Fragment f) {
   	//...
    int nextState = mCurState;
    if (f.mRemoving) {
        if (f.isInBackStack()) {
            nextState = Math.min(nextState, Fragment.CREATED);
        } else {
            nextState = Math.min(nextState, Fragment.INITIALIZING);
        }
    }
    moveToState(f, nextState, f.getNextTransition(), f.getNextTransitionStyle(), false);
		//...
}
```

```java
void moveToState(Fragment f, int newState, int transit, int transitionStyle,
                 boolean keepActive) {
    //....
    if (f.mState <= newState) {
        //....
        switch (f.mState) {
            case Fragment.INITIALIZING:
                if (newState > Fragment.INITIALIZING) {
                    //...
                }
            case Fragment.CREATED:
                if (newState > Fragment.CREATED) {
                    //...
                }
            case Fragment.ACTIVITY_CREATED:
                if (newState > Fragment.ACTIVITY_CREATED) {
                  	//...
                }
            case Fragment.STARTED:
                if (newState > Fragment.STARTED) {
                  	//...
                }
        }
    } else if (f.mState > newState) {
        switch (f.mState) {
            case Fragment.RESUMED:
                if (newState < Fragment.RESUMED) {
                    //...
                }
            case Fragment.STARTED:
                if (newState < Fragment.STARTED) {
                    //...
                }
            case Fragment.ACTIVITY_CREATED:
                if (newState < Fragment.ACTIVITY_CREATED) {
                    //...
                }
            case Fragment.CREATED:
                if (newState < Fragment.CREATED) {
                    //...
                }
        }
    }

    //...
}
```

在此方法中会依次调用Fragment的performXXX方法。而在performXXX方法里会调用具体的生命周期回调。

moveToState内部分两条线，状态跃升，和状态降低，里面各有一个switch判断，switch里每个case都没有break，这意味着，状态可以持续变迁，比如从INITIALIZING，一直跃升到RESUMED，将每个case都走一遍，每次case语句内，都会改变state的值。

这就会产生一种现象：当Activity已经onResume了，此时创建fragment，那么fragment的生命周期回调是从onAttach一直到onResume。

### commitallowingstateloss和commit的区别

commit会报错的原因

```java
//allowStateLoss，commit传的是false，commitallowingstateloss传的是true
    public void enqueueAction(OpGenerator action, boolean allowStateLoss) {
        if (!allowStateLoss) {
            checkStateLoss();
        }

        synchronized (this) {
            if (mDestroyed || mHost == null) {
               throw new IllegalStateException("Activity has been destroyed");
            }
        
            if (mPendingActions == null) {
                mPendingActions = new ArrayList<>();
            }
            
            mPendingActions.add(action);
            scheduleCommit();
       }

    }
```

```java
//当Activity已经调用onSaveInstanceState方法时，mStateSaved为true，所以会出现crash
private void checkStateLoss() {
    if (mStateSaved) {
      throw new IllegalStateException("Can not perform this action after onSaveInstanceState");
    }

    if (mNoTransactionsBecause!= null) {
      throw new IllegalStateException("Can not perform this action inside of " + mNoTransactionsBecause);
    }
}
```

commit方法是在Activity的onSaveInstanceState()之后调用的，这样会出错，因为onSaveInstanceState方法是在该Activity即将被销毁前调用，来保存Activity数据的，如果在保存完状态后再给它添加Fragment就会出错。解决办法就是把commit()方法替换成commitAllowingStateLoss()就行了，其效果是一样的。

### Fragment状态的改变

在Activity的生命周期回调方法里会更改Fragment的状态，如onCreate方法（FragmentActivity的onCreate方法）：

```java
protected void onCreate(@Nullable Bundle savedInstanceState) {
    //...
    mFragments.dispatchCreate();
}
```

onCreate方法里会调用FragmentController的dispatchCreate方法，而dispatchCreate会调用FragmentManager的dispatchCreate方法：

```java
public void dispatchCreate() {
    mStateSaved = false;
    mStopped = false;
    dispatchStateChange(Fragment.CREATED);
}
```

```java
private void dispatchStateChange(int nextState) {
  	//...
  	moveToState(nextState, false);
    //...
}
```

```java
void moveToState(int newState, boolean always) {
    //...
    mCurState = newState;
		//...
}
```

这样就在onCreate更改了FragmentManager的状态。

其它的生命周期回调也类似，会调用dispatchXXX方法，然后内部会更改状态。

**所有的状态**

```java
static final int INITIALIZING = 0;     // Not yet created.
static final int CREATED = 1;          // Created.
static final int ACTIVITY_CREATED = 2; // Fully created, not started.
static final int STARTED = 3;          // Created and started, not resumed.
static final int RESUMED = 4;          // Created started and resumed.
```

并没有pause或者stop的字段，是因为pause复用了STARTED，stop复用了STARTED，destroy复用了INITIALIZING。

## Activity和Fragment的区别

1. 生命周期：
   Activity的生命周期：**onCreate**、**onStart**、**onResume**、**onPause**、**onStop**、**onDestroy**、**onRestart**。
   Fragment的生命周期：**onAttach**、**onCreate**、**onCreateView**、**onActivityCreated**、**onStart**、**onResume**、**onPause**、**onStop**、**onDestroyView**、**onDestroy**、**onDetach**。

2. 灵活性：
   Activity是四大组件之一，Fragment的显示要依赖于Activity。
   1. Fragment相比较与Activity来说更加灵活，可以在XML文件中直接进行写入，也可以在Activity中动态添加。
   2. 可以使用show()/hide()或者replace()随时对Fragment进行切换，并且切换的时候不会出现明显的效果，用户体验会好；Activity虽然也可以进行切换，但是Activity之间切换会有明显的翻页或者其他的效果，在小部分内容的切换上给用户的感觉不是很好。

## FragmentActivity和Activity的区别

fragment是3.0以后的东西，为了在低版本中使用fragment就要用到android-support-v4.jar兼容包，而fragmentActivity就是这个兼容包里面的，它提供了操作fragment的一些方法，其功能跟3.0及以后的版本的Activity的功能一样。

1. fragmentactivity继承自activity，用来解决android3.0之前没有fragment的api，所以在使用的时候需要导入support包，同时继承fragmentActivity，这样在activity中就能嵌入fragment来实现你想要的布局效果。 

2. 当然3.0之后你就可以直接继承自Activity，并且在其中嵌入使用fragment了。 

3. 获得Manager的方式也不同

   3.0以下：getSupportFragmentManager() 
   3.0以上：getFragmentManager()

## Fragment状态保存

实际上，fragment的状态保存和恢复机制和activity是完全一致的。说明解决方案之前，我们首先应该弄清楚下边的几个问题：

1. 什么时候保存状态，什么时候恢复状态
2. 保存和恢复什么状态（fragment的状态还是view的状态？）
3. setRetainInstance(true)



什么时候保存状态，什么时候恢复状态？

当系统认为你的fragment存在被销毁的可能时（不包括用户主动退出fragment导致其被销毁，比如按BACK键后fragment被主动销毁）， onSaveInstanceState 就会被调用，给你一个机会来保存状态。以下几种情况可能导致fragment被异常销毁；

1. 按HOME键返回桌面时
2. 按菜单键回到系统后台，并选择了其他应用时
3. 按电源键时
4. 屏幕方向切换时

这四种情况中，前三种情况都是因为应用处于后台，根据Android系统的缓存机制，为了保持系统的流畅运行，处于后台的应用有很大的可能被清除，既然应用已经不在了，fragment自然也被销毁了；最后一种情况是由于屏幕方向切换导致配置改变，activity被销毁，fragment也随之被销毁了。 

在这些情况下，我们就可以通过 onSaveInstanceState 方法将数据保存到它的参数bundle对象中了。以上触发onSaveInstanceState 的状况和activity完全一致。 

有了保存，就应该有恢复。和activity不同的是，fragment没有onRestoreInstanceState方法，但是我们可以**在onActivityCreated中恢复数据**，它的参数中的bundle对象包含了在异常销毁前保存的数据。

## fragment之间传递数据的方式？

1. 在创建Fragment的需要添加tag(标签)，然后在发送数据的fragment中根据tag找到接收数据的fragment

```java
Bundle bundle = new Bundle();
bundle.putString("data"，"改变图片了");
FragmentRight fragmentRight = (FragmentRight) getActivity()
                        .getFragmentManager()
                        .findFragmentByTag("fRight");
fragmentRight.setData(bundle);
```

2. 接口
3. EventBus
