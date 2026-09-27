

# 绘制流程

绘制流程从ViewRootImpl的performTraversals方法开始，performTraversals方法会依次调用performMeasure、performLayout、performDraw方法来绘制顶级View（DecorView）。

> performMeasure、performLayout、performDraw是ViewRootImp的方法。View和ViewGroup都没有这些方法

```
performMeasure -> measure(final) -> onMeasure(protected)
```

- performMeasure：从根 View 开始，发起测量
- measure：当前 View 的测量入口，处理是否需要测量等逻辑，再调用 `onMeasure()`
- onMeasure：计算自身测量宽高，通过 `setMeasuredDimension()` 保存；容器还会在这里测量子 View

Measure完成后，可以同getMeasureWidth和getMeasureHeight获得测量后的宽高，在几乎所有的情况下等于最终的宽高（因为View需要多次measure才能确定自己的测量宽高）。

```
performLayout -> layout -> onLayout
```

- performLayout：从根 View 开始，发起布局
- layout：设置当前 View 的上下左右边界，并在需要时调用 `onLayout()`
  - 不是final，但注释说不应该重写此方法，应该重写onLayout
- onLayout：容器在这里确定子 View 的位置，调用各子 View 的 `layout()`；普通 View 默认为空
  - 在View中是一个空方法，在ViewGroup中是一个抽象方法

Layout后可以通过getTop、getBottom、getLeft、getRight来拿到View的四个顶点的位置，并可以通过getWidth和getHeight来获得最终的宽高

```
performDraw -> draw -> drawBackground | onDraw | dispatchDraw | onDrawScrollBars
```

- performDraw：发起本帧的绘制流程
- draw：组织当前 View 的绘制顺序：背景、自身内容、子 View、前景等
- onDraw：绘制当前 View 自身的内容，例如文字、图形

drawBackground绘制背景，调用onDraw（onDraw是一个空方法）绘制内容，dispatchDraw绘制子View，onDrawScrollBars绘制装饰。

Draw过程决定了View的显示，只有draw方法后，view的内容才会显示在屏幕上。

# Measure

## MeasureSpec

**MeasureSpec 是父容器传给子 View 的“测量要求”，包含测量模式和尺寸两个信息。** 子 View 在 `onMeasure()` 中结合这些要求和自身内容，计算出测量宽高。

理解它时，可以先分清三个概念：

| 概念           | 表达的意思                 | 示例                                    |
| -------------- | -------------------------- | --------------------------------------- |
| `LayoutParams` | 子 View 希望怎么占用空间   | `100dp`、`match_parent`、`wrap_content` |
| `MeasureSpec`  | 父容器对本次测量提出的要求 | 宽度必须是 `300px`，或最多 `300px`      |
| 测量宽高       | 子 View 按要求计算出的结果 | `getMeasuredWidth()` 返回 `180px`       |

父容器结合自身约束、子 View 的 `LayoutParams` 和布局规则，生成子 View 的 MeasureSpec。

### SpecMode

MeasureSpec 有三种模式，假设传入的 size 为 `300px`：

| 模式          | 对子 View 的要求                 | size 的含义    |
| ------------- | -------------------------------- | -------------- |
| `EXACTLY`     | 测量尺寸应当为 `300px`           | 确定的尺寸     |
| `AT_MOST`     | 自己决定尺寸，但不能超过 `300px` | 尺寸上限       |
| `UNSPECIFIED` | 根据自身需要决定尺寸             | 不作为尺寸上限 |

宽度和高度各有一个 MeasureSpec。

它实际使用一个 32 位 `int` 存储信息：高 2 位保存模式，低 30 位保存 size，尺寸单位是 px。

```
// 构造：“最多 300px”
int spec = View.MeasureSpec.makeMeasureSpec(
        300, View.MeasureSpec.AT_MOST);

// 拆解
int mode = View.MeasureSpec.getMode(spec); // AT_MOST
int size = View.MeasureSpec.getSize(spec); // 300
```



**父view一般怎么选择传递给子view的SpecMode**

一般结合父 View 的模式 + 子 View 的 LayoutParams：

- 固定尺寸 → `EXACTLY`
- match_parent → 与父 View 的模式相同
- wrap_content → 通常为 `AT_MOST`；父模式为 `UNSPECIFIED` 时也是 `UNSPECIFIED`

特殊容器可以自行制定规则。

### Lp和Spec的对应关系

接下来最关键的是：**LayoutParams 和 MeasureSpec 的模式并非固定的一一对应关系。**

下面是 `ViewGroup.getChildMeasureSpec()` 的基础转换规则。设 `S` 为父规格尺寸扣除本次测量中 padding、margin、已用空间等之后的可用值，`D` 为子 View 指定的固定像素尺寸：

| 父容器的模式  | 子 View 为固定尺寸 `D` | 子 View 为 `match_parent` | 子 View 为 `wrap_content` |
| ------------- | ---------------------- | ------------------------- | ------------------------- |
| `EXACTLY`     | `EXACTLY D`            | `EXACTLY S`               | `AT_MOST S`               |
| `AT_MOST`     | `EXACTLY D`            | `AT_MOST S`               | `AT_MOST S`               |
| `UNSPECIFIED` | `EXACTLY D`            | `UNSPECIFIED`             | `UNSPECIFIED`             |

这是通用辅助方法的规则，具体容器可以采用自己的测量策略或进行多轮测量。



例如，忽略 margin 并且宽高都相同。父容器收到 `EXACTLY 300px`，左右 padding 各为 `20px`，可用宽度就是 `260px`：

```
父View的onMeasure：EXACTLY 300px
父View有左右 padding 各 20px

子View的onMeasure的：XX	260px（XX为specmode，不确定。但是size就是260px）
```

- 子 View 设置 `100px`：收到 `EXACTLY 100px`。
- 子 View 设置 `match_parent`：收到 `EXACTLY 260px`。
- 子 View 设置 `wrap_content`：收到 `AT_MOST 260px`，随后根据内容决定需要多少宽度。



子 View 收到这些规格之后，通常会在 `onMeasure()` 中先计算期望尺寸，再处理父容器的约束。对于按内容确定大小的自定义 View，可以使用 `resolveSize()`：

```
@Override
protected void onMeasure(int widthMeasureSpec, int heightMeasureSpec) {
    // 示例期望尺寸，单位 px；实际应结合内容、padding、最小尺寸计算
    int desiredWidth = 200;
    int desiredHeight = 100;

    setMeasuredDimension(
            resolveSize(desiredWidth, widthMeasureSpec),
            resolveSize(desiredHeight, heightMeasureSpec)
    );
}
```

resolveSize的处理规则是：

- `EXACTLY`：采用规格尺寸。
- `AT_MOST`：采用期望尺寸和规格上限中的较小值。
- `UNSPECIFIED`：采用期望尺寸。

但这需要 View 的测量实现主动处理。基础 `View` 默认的 `onMeasure()` 在 `AT_MOST` 下会直接采用规格上限，因此直接继承 `View` 做自定义控件时，通常需要重写它，才能让 `wrap_content` 按自己的内容收缩。

**`setMeasuredDimension(width, height)` 用来保存当前 View 本次测量得到的宽高，是 `onMeasure()` 提交测量结果的方法。** 调用后，就能通过 `getMeasuredWidth()` 和 `getMeasuredHeight()` 读取结果。

## measure

- 直接继承View的自定义控件需要重写onMeasure方法并设置wrap_content时自身的大小，否则在布局中使用wrap_content就相当于使用match_parent。
- 在某些情况下，系统可能会多次measure才会确定最终的测量宽高，在这种情况下，在onMeasure方法中拿到的宽高可能不准。一个比较好的习惯是在onLayout方法中获取宽高。

### 获取宽高的方法

在onCreate、onStart、onResume无法获取正确宽高，因为View的measure和Activity的生命周期不是同步的。**四个获取宽高的方法**：

1. **Activity/View#onWindowFocusChanged**
    这个方法的含义是View已经初始化完毕了，宽高已经准备好了。当Activity获得焦点和失去焦点的时候会调用一次，具体的说，是当onResume和onPause的时候会被调用。

2. **view.post(runnable)**
    通过post将一个runnable投到消息队列的尾部，等待Looper调用此runnable的时候，View已经初始化好了。

    ```java
    @Override
    protected void onStart() {
        super.onStart();
        ViewGroup viewGroup = findViewById(android.R.id.content);
        final View view = viewGroup.getChildAt(0);
        view.post(new Runnable() {
    
            @Override
            public void run() {
                int width = view.getMeasuredWidth();
                int height = view.getMeasuredHeight();
            }
        });
    }
    ```

3. **ViewTreeObserver**
    使用ViewTreeObserver的回调可以完成这个功能

    ```java
    @Override
    protected void onStart() {
        super.onStart();
        ViewGroup viewGroup = findViewById(android.R.id.content);
        final View view = viewGroup.getChildAt(0);
        ViewTreeObserver observer = view.getViewTreeObserver();
        observer.addOnGlobalLayoutListener(new ViewTreeObserver.OnGlobalLayoutListener() {
            @Override
            public void onGlobalLayout() {
                view.getViewTreeObserver().removeGlobalOnLayoutListener(this);
                int width = view.getMeasuredWidth();
                int height = view.getMeasuredHeight();
            }
        });
    }
    ```

4. **view.measure(int widthMeasureSpec，int heightMeasureSpec)**
    具体见下"手动measure"。

### DecorView的测量

MeasureSpec是LayoutParams和父容器的模式所共同影响的，那么，对于DecorView来说，它已经是顶层view了，没有父容器，那么它的MeasureSpec怎么来的呢？

DecorView虽然是顶层View，但是Window是以View的形式存在，而Window具有LayoutParams，这个lp会影响DecorView。在ViewRootImpl#PerformTraveals的方法中，有：

```java
WindowManager.LayoutParams lp = mWindowAttributes;
// ...
int childWidthMeasureSpec = getRootMeasureSpec(mWidth, lp.width);
int childHeightMeasureSpec = getRootMeasureSpec(mHeight, lp.height);
// ...
performMeasure(childWidthMeasureSpec, childHeightMeasureSpec);
```

```java
private static int getRootMeasureSpec(int windowSize, int rootDimension) {
    int measureSpec;
    switch (rootDimension) {

    case ViewGroup.LayoutParams.MATCH_PARENT:
        // Window can't resize. Force root view to be windowSize.
        measureSpec = MeasureSpec.makeMeasureSpec(windowSize, MeasureSpec.EXACTLY);
        break;
    case ViewGroup.LayoutParams.WRAP_CONTENT:
        // Window can resize. Set max size for root view.
        measureSpec = MeasureSpec.makeMeasureSpec(windowSize, MeasureSpec.AT_MOST);
        break;
    default:
        // Window wants to be an exact size. Force root view to be that size.
        measureSpec = MeasureSpec.makeMeasureSpec(rootDimension, MeasureSpec.EXACTLY);
        break;
    }
    return measureSpec;
}
```

思路也很清晰，根据不同的模式来设置MeasureSpec，如果是LayoutParams.MATCH_PARENT模式，则是窗口的大小，WRAP_CONTENT模式则是大小不确定，但是不能超过窗口的大小等等。

### 手动measure

通过手动对View进行measure来得到View的宽/高。这种方法比较复杂，这里要分情况处理，根据View的LayoutParams来分：

1.   match_parent
     仅凭 match_parent 无法确定尺寸，需要结合父容器约束。
     已知父容器的规格、padding、margin 和布局规则时，就可以构造子 View 的规格。例如父宽 EXACTLY 300px，左右 padding 各 20px，无 margin，子宽 match_parent，在通用规则下可以使用 EXACTLY 260px 测量。
     
2.   具体的数值（dp/px）
     比如宽/高都是100px，如下measure：

     ```java
     int widthMeasureSpec = MeasureSpec.makeMeasureSpec(100, MeasureSpec.EXACTLY);
     int heightMeasureSpec = MeasureSpec.makeMeasureSpec(100, MeasureSpec.EXACTLY);
     view.measure(widthMeasureSpec, heightMeasureSpec);
     ```

3.   wrap_content
     如下measure：

     ```java
     int widthMeasureSpec = MeasureSpec.makeMeasureSpec((1 << 30) - 1, MeasureSpec.AT_MOST);
     int heightMeasureSpec = MeasureSpec.makeMeasureSpec((1 << 30) - 1, MeasureSpec.AT_MOST); 
     view.measure(widthMeasureSpecr, heightMeasureSpec);
     ```

     注意到`(1 << 30) - 1`，通过分析MeasureSpec的实现可以知道，View的尺寸使用30位二进制表示，也就是说最大是30个1（即2^30- 1），也就是（1<<30）- 1，在最大化模式下，用View理论上能支持的最大值去构造MeasureSpec是合理的。


**实战例子**

如果需要一个view对应的bitmap（即需要手动触发measure、layout、draw）而这个view不会加入到任意view树中，那该如何measure这个view？

| 要求                                 | 传入的规格                        |
| ------------------------------------ | --------------------------------- |
| 尺寸固定为 `300px`                   | `makeMeasureSpec(300, EXACTLY)`   |
| 根据内容决定，但最多 `300px`         | `makeMeasureSpec(300, AT_MOST)`   |
| 父级不施加尺寸限制，由 View 自行计算 | `makeMeasureSpec(0, UNSPECIFIED)` |

# layout

Layout的作用是ViewGroup用来确定子元素的位置，当ViewGroup的位置被确定后，它在onLayout中会遍历所有的子元素并调用其layout方法，在layout方法中onLayout方法又会被调用。layout方法确定View本身的位置，而onLayout方法则会确定所有子元素的位置。

layout方法的大致流程如下：首先会通过setFrame方法来设定View的四个顶点的位置，即初始化mLeft、mRight、 mTop和mBottom这四个值，View的四个顶点一旦确定，那么View在父容器中的位置也就确定了：接着会调用onLayout方法，这个方法的用途是父容器确定子元素的位置，和onMeasure方法类似，onLayout 的具体实现同样和具体的布局有关，所以View和ViewGroup均没有真正实现onLayout方法。

> onLayout在ViewGroup是抽象方法，layout是由父容器在onlayout中调用。

## View的测量宽高和最终宽高有什么区别？

这个问题可以具体为：View的getMeasuredWidth和getWidth这两个方法有什么区别？

getMeasuredWidth：

```java
public final int getMeasuredWidth() {
    return mMeasuredWidth & MEASURED_SIZE_MASK;
}
```

getWidth：

```java
public final int getWidth() {
    return mRight - mLeft;
}
```

在View的默认实现中，View的测量宽/高和最终宽/高是相等的，只不过测量宽/高形成于View的measure过程，而最终宽/高形成于View的layout过程，即两者的赋值时机不同，测量宽/高的赋值时机稍微早一些。因此，在日常开发中，可以认为View的测量宽/高就等于最终宽/高。

>   即，一般情况下，两者相等，只是赋值时机不同。

# draw

```java
public void draw(Canvas canvas) {
    //...
    
    /*
     * Draw traversal performs several drawing steps which must be executed
     * in the appropriate order:
     *
     *      1. Draw the background
     *      2. If necessary， save the canvas' layers to prepare for fading
     *      3. Draw view's content
     *      4. Draw children
     *      5. If necessary， draw the fading edges and restore layers
     *      6. Draw decorations (scrollbars for instance)
     */

    // Step 1， draw the background， if needed
    //...
    drawBackground(canvas);

    // skip step 2 & 5 if possible (common case)
    //...
    // Step 3， draw the content
    onDraw(canvas);
    
    // Step 4， draw the children
    dispatchDraw(canvas);
    
    // Step 6， draw decorations (foreground， scrollbars)
    onDrawForeground(canvas);

    // Step 7， draw the default focus highlight
    drawDefaultFocusHighlight(canvas);
    return;
}
```

View的绘制过程（主要）：

1. 绘制背景drawBackground(canvas)
2. 绘制自己（onDraw）
3. 绘制children（dispatchDraw）
4. 绘制装饰（onDrawScrollBars）

源码在注释上步骤写得很详细，主要步骤是这上面四个。



View的绘制过程的传递主要是通过dispatchDraw来实现的。

> View有个特殊的方法（**setWillNotDraw**），如果一个View不需要绘制任何内容，那么设置这个标记位为true后，系统会进行相应的优化。默认情况下，View不启用，ViewGroup启用。当明确知道一个ViewGroup需要启用时，需要显式的关闭这个标记位。
>

draw的时候要考虑padding，让自定义View支持padding：

```java
@Override
protected void onDraw(Canvas canvas) {
    super.onDraw(canvas);
    int paddingLeft=getPaddingLeft();
    int paddingRight=getPaddingRight();
    int paddingTop=getPaddingTop();
    int paddingBottom=getPaddingBottom();
    int width=getWidth()-paddingLeft-paddingRight;
    int height=getHeight()-paddingTop-paddingBottom;
    int radius=Math.min(width，height)/2;
    canvas.drawCircle(paddingLeft+width/2，paddingTop+height/2，radius，paint);
}
```

# 布局优化

## 避免过度绘制

过度绘制会浪费很多的cpu，Gpu资源，例如系统默认会绘制Activity的背景，如果在给布局重新绘制了重叠的背景，那么默认的Activity的背景就属于无效的过度绘制。

> 系统提供了检测工具Debug GPU Overdraw来查看界面overdraw的情况。该工具会使用不同的颜色绘制屏幕，来指示overdraw发生在哪里以及程度如何，其中：
>
> - 没有颜色： 意味着没有overdraw。像素只画了一次。
> - 蓝色： 意味着overdraw 1倍。像素绘制了两次。大片的蓝色还是可以接受的（若整个窗口是蓝色的，可以摆脱一层）。
> - 绿色： 意味着overdraw 2倍。像素绘制了三次。中等大小的绿色区域是可以接受的但你应该尝试优化、减少它们。
> - 浅红： 意味着overdraw 3倍。像素绘制了四次，小范围可以接受。
> - 暗红： 意味着overdraw 4倍。像素绘制了五次或者更多。这是错误的，要修复它们。

**不绘制Activity的背景**

去掉DecorView的背景。定义一个style theme。应用到需要的Activity或者Application。

```xml
<resources>
    <style name="Theme.NoBackground" parent="android:Theme">
        <item name="android:windowBackground">@null</item>
    </style>
</resources>
```

## 优化布局层次

在Android中，系统对View的进行测量、布局和绘制时，都是通过对View树的遍历来进行操作的。如果一个View的高度太高，就会影响测量、布局和绘制的速度，因此优化布局的第一个方法就是降低View树的高度，避免嵌套过多无用布局。

### include标签

主要用于布局重用。

> include 上指定的 android:id 会覆盖被引用布局根 View 的 ID。两者不同也能正常获取根 View，只需使用覆盖后的 ID；未指定 include ID 时，才保留原根 ID。

### merge标签

merge标签可以自动消除当一个布局插入到另一个布局时产生的多余的View Group。merge可以配合include使用，也可以通过LayoutInflater直接加载。

**需要注意的地方**

- merge标签只能作为复用布局的root元素来使用。
- 使用它来inflate一个布局时，必须指定一个ViewGroup实例作为其父元素并且设置attachToRoot属性为true（参考 inflate(int， android.view.ViewGroup， boolean) 方法的说明 ）。

**简单示例**

定义复用布局`res/layout/merge_buttons.xml`，使用merge作为根标签：

```xml
<merge xmlns:android="http://schemas.android.com/apk/res/android">
    <Button
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:text="添加" />

    <Button
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:text="删除" />
</merge>
```

在主布局`res/layout/activity_main.xml`中引用：

```xml
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical">

    <include layout="@layout/merge_buttons" />
</LinearLayout>
```

加载后的View树如下，两个按钮由外层LinearLayout竖向排列：

```text
LinearLayout
├── Button（添加）
└── Button（删除）
```

**merge和include都不会生成额外的View节点。**如果复用布局的根标签使用另一个LinearLayout，就会多出一层容器；使用merge可以省掉这一层。

### ViewStub标签：懒加载

ViewStub是一个非常轻量级的组件，它不仅不可见，而且大小为0。

首先创建一个布局，这个布局在初始化加载时不需要显示，只在某些情况下才显示出来，例如查看用户信息的时，只有点击了某个按钮是，用户详细信息才显示出来。写一个简单的布局：

```xml
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout  xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical">
    <TextView
        android:id="@+id/tv"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="not often use layout"
        android:textSize="30sp"/>
</LinearLayout>
```

接下来与使用\<include\>标签类似，在主布局中的\<ViewStub\>中的layout属性来引用上面的布局。

```xml
<ViewStub
    android:id="@+id/not_often_use"
    android:layout_alignParentBottom="true"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout="@layout/not_often_use"/>
```

**如何重新加载显示的布局呢？**

首先，通过普通的findViewById方法找到\<ViewStub>组件，这点与一般的组件基本相同：

```
mViewStub = (ViewStub)findViewById(R.id.not_often_use);
```

接下来，有两种方式重新显示这个View：

1. VISIBLE
   通过调用ViewStub的setVisibility()方法来显示这个View。`mViewStub.setVisibility(View.VISIBLE);`
2. inflate
   通过调用ViewStub的inflate方法来显示这个View。`View inflateView = mViewStub.inflate();

这两种方式都可以让ViewStub重新展开，显示引用的布局，而唯一的区别就是inflate方法可以返回引用的布局，从而可以在通过View.findViewById方法来找到对应的控件，代码如下：

```java
View inflateView = mViewStub.inflate();
TextView textview  = (TextView) inflateView.findViewById(R.id.Tv);
textView.setText(“Hello“);
```



**ViewStub和View.GONE有啥区别？**
它们的共同点是初始时都不会显示，但是前者只会在显示时才去渲染整个布局，而后者在初始化布局树的时候就已经添加到布局树上了，相比之下前者的布局具有更高的效率。

# 自定义View

1. 让View支持wrap_content
    这是因为直接维承View或者ViewGroup的控件，如果不在onMeasure中对wrap_content做特殊处理，那么当外界在布局中使用wrap_content时就无法达到预期的效果。
2. 如果有必要，让View支持padding
    这是因为直接继承View的控件，如果不在draw方法中处理padding，那么padding居性是无法起作用的。另外，直接继承自ViewGroup的控件需要在onMeasure和onLayout中考虑padding和子元素的margin对其造成的影响，不然将导致padding和子元素的margin失效。
3. 尽量不要在View中使用Handler(没必要)
    这是因为View内部本身就提供了post系列的方法，完全可以替代Handler的作用，当然除非你很明确地要使用Handler来发送消息。
4. View中如果有线程或者动画，需要及时停止，参考View#onDetachedFromWindow。
    这一条也很好理解，如果有线程或者动画需要停止时，那么onDetachedFromWindow是一个很好的时机。当包含此View的Activity退出或者当前View被remove 时，View的onDetachedFromWindow方法会被调用，和此方法对应的是onAtachedToWindow， 当包含此View的Activity启动时，View的onAtachedToWindow方法会被调用。同时，当View变得不可见时也需要停止线程和动画，如果不及时处理这种问题，有可能会造成内存泄漏。
5. View带有滑动嵌套情形时，需要处理好滑动冲突
    如果有滑动冲突的话，那么要合适地处理滑动冲突，否则将会严重影响View的效果。

# postInvalidate

这个方法与invalidate方法的作用是一样的，都是使View树重绘，但两者的使用条件不同，postInvalidate是在非UI线程中调用，invalidate则是在UI线程中调用。 

# post方法

Android是消息驱动的模式，View.post的Runnable任务会被加入任务队列，并且等待第一次TraversalRunnable执行结束后才执行，此时已经执行过一次measure，layout过程了，所以在后面执行post的Runnable时，已经有measure的结果，因此此时可以获取到View的宽高。

源码

```java
public boolean post(Runnable action) {
    final AttachInfo attachInfo = mAttachInfo;
    if (attachInfo != null) {
        return attachInfo.mHandler.post(action);
    }
    getRunQueue().post(action);
    return true;
}
```

未dispatchAttachedToWindow时，将runnable操作缓存，等View的dispatchAttachedToWindow被调用时，就通过mAttachInfo.mHandler来执行这些被缓存起来的Runnable操作。

从这以后到 View被detachedFromWindow这段期间，如果再次调用View.post(Runnable)的话，那么这些Runnable不用再缓存了，而是直接交给mAttachInfo.mHanlder来执行。

一些问题：

dispatchAttachedToWindow的调用时机？mAttachInfo是在哪里初始化的？

```java
void dispatchAttachedToWindow(AttachInfo info, int visibility) {
    // 初始化mAttachInfo
    mAttachInfo = info;
    // ...
    // 执行缓存的runnable
    if (mRunQueue != null) {
        mRunQueue.executeActions(info.mHandler);
        mRunQueue = null;
    }
    // ...
    // 回调
    onAttachedToWindow();
    // ...
}
```

dispatchAttachedToWindow的调用是在ViewRootImpl的performTraversals方法里。

```java
void dispatchDetachedFromWindow() {
    // 回调
    onDetachedFromWindow();
    // ...
	// 置空
    mAttachInfo = null;
    // ...
}
```

1.   通过View post一个runnable。
     如果当前View已经dispatchAttachedToWindow，那么将该消息post到消息队列的末尾。
     如果当前View还没有dispatchAttachedToWindow，那么缓存该消息。
2.   当View dispatchAttachedToWindow时，会将缓存消息post，而View的dispatchAttachedToWindow是在ViewRootImpl的performTraversals方法里。
3.   performTraversals会进行测量，布局，这些是同步操作。
4.   所以View的post方法可以拿到宽高。
