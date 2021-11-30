# View绘制流程

![20180924152946](http://111.230.96.19:8081/image/20180924152946.png)

![20181029224232](http://111.230.96.19:8081/image/20181029224232.png)

## ViewRoot

ViewRoot是连接WindowMananger和DecorView的纽带，View的三大流程是通过ViewRoot来完成的。

## 绘制流程

绘制流程从ViewRootImpl的performTraversals方法开始，performTraversals方法会依次调用performMeasure、performLayout、performDraw方法来绘制顶级View（DecorView）。

> performMeasure、performLayout、performDraw是ViewRootImp的方法。View和ViewGroup都没有这些方法

在performMeasure方法中，会调用View的measure方法（final）进行测量（实际操作是在onMeasure中，来自measure方法的注释），然后在onMeasure（protected）中对子元素进行measure，子元素重复此过程。

performLayout也是如此，在performLayout方法中，会调用View的layout方法（不是final，但注释说不应该重写此方法，应该重写onLayout）进行布局，然后在onLayout（在View中是一个空方法，在ViewGroup中是一个抽象方法）中对子元素进行layout，子元素重复此过程。

performDraw有点区别。performDraw调用View的draw（draw不建议重写，如果一定要重写，需要调用super）绘制，draw调用drawBackground绘制背景，调用onDraw（onDraw是一个空方法）绘制内容，dispatchDraw绘制子View，onDrawScrollBars绘制装饰。

## 绘制方法介绍

Measure完成后，可以同getMeasureWidth和getMeasureHeight获得测量后的宽高，在几乎所有的情况下等于最终的宽高（因为View需要多次measure才能确定自己的测量宽高）。

Layout后可以通过getTop、getBottom、getLeft、getRight来拿到View的四个顶点的位置，并可以通过getWidth和getHeight来获得最终的宽高

Draw过程决定了View的显示，只有draw方法后，view的内容才会显示在屏幕上

## DecorView

DecorView实际上是一个FrameLayout，内部包含一个竖直方向的LinearLayout，这个LinearLayout有两个部分，上面是标题栏，下面是内容栏。获取content:

```java
ViewGroup content = findViewById(android.R.id.content);
```

获取设置的View

```java
View view = content.getChildAt(0);
```

## MeasureSpec

MeasureSpec很大程度上决定了一个View的尺寸规格，这个过程受父容器的影响，因为父容器影响View的MeasureSpec的创建过程。

MeasureSpec是一个32位int值，高两位是SpecMode（测量模式），低30位是SpecSize（规格大小）

### SpecMode

- **UNSPECIFIED**：一般用于系统内部，表示一种测量的状态
- **EXACTLY**：View所需要的精确大小，最终大小就是SpecSize指定的值，对应match_patent和具体的数值
- **AT_MOST**：父容器指定了一个可用大小即SpecSize，View的大小不能大于这个值，对应wrap_content

### MeasureSpec和LayoutParams的对应关系

对于DecorView是由窗口的尺寸和其LayoutParams来共同决定的

- **match_patent**：大小就是窗口的大小
- **wrap_content**：大小不定，但是不能超过窗口的大小
- **固定大小**：指定大小

对于普通View是由父容器的MeasureSpec和其LayoutParams来共同决定的

- 当View采用固定宽高的时候，不管父容器的MeasureSpec是什么，View的MeasureSpec都是精确模式并且大小遵循LayoutParams中的大小。
- 当View采用match_parent的时候，如果父容器是精确模式，那么View也是精确模式并且大小是父容器的剩余空间。如果父容器是最大模式，那么View也是最大模式，并且不会超过父容器的剩余空间。
- 当View采用wrap_content的时候，View总是最大模式，并且不会超过父容器的剩余空间

![ViewMeasureSpec](http://111.230.96.19:8081/image/ViewMeasureSpec.png)

### 实验

这里的xml文件如下：

```xml
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:background="#ddd">

    <FrameLayout
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:background="#FF0000">

        <TextView
            android:layout_width="match_parent"
            android:layout_height="match_parent"
            android:background="#3858FF"
            android:text="@string/test"
            android:textSize="20sp" />
    </FrameLayout>

</LinearLayout>
```

只需要关注FrameLayout和内部的TextView。Parent为红色，Child为蓝色

这里只调整高度height。

#### Parent为px/dp

##### Child为px/dp

![23](/Users/mezzsy/知识点/img/23.jpg)

##### Child为match_parent

![24](/Users/mezzsy/知识点/img/24.jpg)

##### Child为wrap_content

![25](/Users/mezzsy/知识点/img/25.jpg)

#### Parent为match_parent

##### Child为px/dp

![26](/Users/mezzsy/知识点/img/26.jpg)

##### Child为match_parent

![27](/Users/mezzsy/知识点/img/27.jpg)

##### Child为wrap_content

![28](/Users/mezzsy/知识点/img/28.jpg)

#### Parent为wrap_content

##### Child为px/dp

![31](/Users/mezzsy/知识点/img/31.jpg)

##### Child为match_parent

![30](/Users/mezzsy/知识点/img/30.jpg)

##### Child为wrap_content

![29](/Users/mezzsy/知识点/img/29.jpg)



## Measure

- 直接继承View的自定义控件需要重写onMeasure方法并设置wrap_content时自身的大小，否则在布局中使用wrap_content就相当于使用match_parent。
- 在某些情况下，系统可能会多次measure才会确定最终的测量宽高，在这种情况下，在onMeasure方法中拿到的宽高可能不准。一个比较好的习惯是在onLayout方法中获取宽高
- 在onCreate、onStart、onResume无法获取正确宽高，因为View的measure和Activity的生命周期不是同步的。**四个获取宽高的方法**：

1. **Activity/View#onWindowFocusChanged**：这个方法的含义是View已经初始化完毕了，宽高已经准备好了。当Activity获得焦点和失去焦点的时候会调用一次，具体的说，是当onResume和onPause的时候会被调用。
2. **view.post(runnable)**:通过post将一个runnable投到消息队列的尾部，等待Looper调用此runnable的时候，View已经初始化好了。

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

3.**ViewTreeObserver**:使用ViewTreeObserver的回调可以完成这个功能

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

4.**view.measure(int widthMeasureSpec，int heightMeasureSpec)**：通过手动对View进行measure来得到View的宽高。要根据LayoutParams：

**match_parent**：直接放弃，无法直接measure出具体的宽高。

**wrap_content**：略

**具体的数值**：略

> View的measure方法是final方法，不能继承，建议在onMeasure写逻辑。

## Layout

在ViewGroup的位置确定后，会在onLayout中遍历所有的子元素并调用其layout方法，在layout中onLayout方法又会被调用。

> onLayout在ViewGroup是抽象方法，layout是由父容器在onlayout中调用。

## Draw

draw方法

```java
/**
 * Manually render this view (and all of its children) to the given Canvas.
 * The view must have already done a full layout before this function is
 * called.  When implementing a view， implement
 * {@link #onDraw(android.graphics.Canvas)} instead of overriding this method.
 * If you do need to override this method， call the superclass version.
 *
 * @param canvas The Canvas to which the View is rendered.
 */
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

    if (!dirtyOpaque) {
        drawBackground(canvas);
    }

    // skip step 2 & 5 if possible (common case)
    //...
    if (!verticalEdges && !horizontalEdges) {
        // Step 3， draw the content
        if (!dirtyOpaque) onDraw(canvas);

        // Step 4， draw the children
        dispatchDraw(canvas);

        drawAutofilledHighlight(canvas);

        // Overlay is part of the content and draws beneath Foreground
        if (mOverlay != null && !mOverlay.isEmpty()) {
            mOverlay.getOverlayView().dispatchDraw(canvas);
        }

        // Step 6， draw decorations (foreground， scrollbars)
        onDrawForeground(canvas);

        // Step 7， draw the default focus highlight
        drawDefaultFocusHighlight(canvas);

        if (debugDraw()) {
            debugDrawFocus(canvas);
        }

        // we're done...
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

View有个特殊的方法（**setWillNotDraw**），如果一个View不需要绘制任何内容，那么设置这个标记位为true后，系统会进行相应的优化。默认情况下，View不启用，ViewGroup启用。当明确知道一个ViewGroup需要启用时，需要显式的关闭这个标记位。

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

这是绘制圆形的情况，其他图案可以更改部分代码。

## **布局优化**

### 避免过度绘制

过度绘制会浪费很多的cpu，Gpu资源，例如系统默认会绘制Activity的背景，如果在给布局重新绘制了重叠的背景，那么默认的Activity的背景就属于无效的过度绘制。

过度绘制（Overdraw）也是很浪费CPU/GPU资源的，系统也提供了检测工具Debug GPU Overdraw来查看界面overdraw的情况。该工具会使用不同的颜色绘制屏幕，来指示overdraw发生在哪里以及程度如何，其中：
没有颜色： 意味着没有overdraw。像素只画了一次。
蓝色： 意味着overdraw 1倍。像素绘制了两次。大片的蓝色还是可以接受的（若整个窗口是蓝色的，可以摆脱一层）。
绿色： 意味着overdraw 2倍。像素绘制了三次。中等大小的绿色区域是可以接受的但你应该尝试优化、减少它们。
浅红： 意味着overdraw 3倍。像素绘制了四次，小范围可以接受。
暗红： 意味着overdraw 4倍。像素绘制了五次或者更多。这是错误的，要修复它们。

**不绘制Activity的背景**

去掉DecorView的背景。定义一个style theme。应用到需要的Activity或者Application。

```xml
<resources>
    <style name="Theme.NoBackground" parent="android:Theme">
        <item name="android:windowBackground">@null</item>
    </style>
</resources>
```

### 优化布局层次

在Android中，系统对View的进行测量、布局和绘制时，都是通过对View树的遍历来进行操作的。如果一个View的高度太高，就会影响测量、布局和绘制的速度，因此优化布局的第一个方法就是降低View树的高度，Google在器API文档中也建议View树的高度不超过10层。
避免嵌套过多无用布局：

1. **使用\<include\>标签重用layout**
   主要用于布局重用。
   注：根容器id与include id必须相同
   如给include所加载的layout布局的根容器设置了id属性，也在include标签中设置了id属性，同时需要在代码中获取根容器的控件对象时，一定要将这两个id设置相同的名称！否则，将获取不到根容器对象，即为null。
2. **merge标签**
   merge标签可以自动消除当一个布局插入到另一个布局时产生的多余的View Group。用法就是直接使用merge标签作为复用布局的根节点，再使用include标签复用到其他布局中，这时，系统会自动忽略merge标签，直接把两个Button替换到include标签的位置。 
   也就是说，include和merge是配合使用的。
   **需要注意的地方：**
   - merge标签只能作为复用布局的root元素来使用。
   - 使用它来inflate一个布局时，必须指定一个ViewGroup实例作为其父元素并且设置attachToRoot属性为true（参考 inflate(int， android.view.ViewGroup， boolean) 方法的说明 ）。
3. **使用\<ViewStub\>实现view的延迟加载**
   **\<ViewStub\>**是一个非常轻量级的组件，它不仅不可见，而且大小为0。
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

首先，通过普通的findViewById（）方法找到\<ViewStub>组件，这点与一般的组件基本相同：

`mViewStub = (ViewStub)findViewById(R.id.not_often_use);`

接下来，有两种方式重新显示这个View.

（1）VISIBLE

通过调用ViewStub的setVisibility()方法来显示这个View，代码如下所示：

`mViewStub.setVisibility(View.VISIBLE);`

( 2 ) inflate

通过调用ViewStub的inflate（）方法来显示这个View，代码如下：

`View inflateView = mViewStub.inflate();`

这两种方式都可以让ViewStub重新展开，显示引用的布局，而唯一的区别就是inflate（）方法可以返回引用的布局，从而可以在通过View.findViewById()方法来找到对应的控件，代码如下：

```java
View inflateView = mViewStub.inflate();
TextView textview  = (TextView) inflateView.findViewById(R.id.Tv);
textView.setText(“Hello“);
```

**ViewStub和View.GONE有啥区别？**
它们的共同点是初始时都不会显示，但是前者只会在显示时才去渲染整个布局，而后者在初始化布局树的时候就已经添加到布局树上了，相比之下前者的布局具有更高的效率。

### LinearLayout、RelativeLayout、FrameLayout的特性及对比，并介绍使用场景。

RelativeLayout会对子View做两次measure。 
首先RelativeLayout中子View的排列方式是基于彼此的依赖关系，而这个依赖关系可能和布局中View的顺序并不相同，在确定每个子View的位置的时候，就需要先给所有的子View排序一下。 

如果不使用weight属性，LinearLayout会在当前方向上进行一次measure的过程，如果使用weight属性，LinearLayout会避开设置过weight属性的view做第一次measure，完了再对设置过weight属性的view做第二次measure。由此可见，weight属性对性能是有影响的，而且本身有大坑，请注意避让。

总结：

1.RelativeLayout会让子View调用2次onMeasure，LinearLayout 在有weight时，也会调用子View2次onMeasure

2.RelativeLayout的子View如果高度和RelativeLayout不同，则会引发效率问题，当子View很复杂时，这个问题会更加严重。如果可以，尽量使用padding代替margin。

3.在不影响层级深度的情况下，使用LinearLayout和FrameLayout而不是RelativeLayout。

4.能用两层LinearLayout，尽量用一个RelativeLayout，在时间上此时RelativeLayout耗时更小。另外LinearLayout慎用layout_weight，也将会增加一倍耗时操作。由于使用LinearLayout的layout_weight，大多数时间是不一样的，这会降低测量的速度。这只是一个如何合理使用Layout的案例，必要的时候，你要小心考虑是否用layout weight。总之减少层级结构，才是王道，让onMeasure做延迟加载，用viewStub，include等一些技巧。

**选择LinearLayout还是RelativeLayout？**

谷歌的官方说明

> A RelativeLayout is a very powerful utility for designing a user interface because it can eliminate nested view groups and keep your layout hierarchy flat， which improves performance. If you find yourself using several nested LinearLayout groups， you may be able to replace them with a single RelativeLayout
>

Google的意思是“性能至上”， RelativeLayout 在性能上更好，因为在诸如 ListView 等控件中，使用 LinearLayout 容易产生多层嵌套的布局结构，这在性能上是不好的。而 RelativeLayout 因其原理上的灵活性，通常层级结构都比较扁平，很多使用LinearLayout 的情况都可以用一个 RelativeLayout 来替代，以降低布局的嵌套层级，优化性能。所以从这一点来看，Google比较推荐开发者使用RelativeLayout，因此就将其作为Blank Activity的默认布局了。

## 自定义View

1. 让View支持wrap_content
   这是因为直接维承View或者ViewGroup的控件，如果不在onMeasure中对wrap_content做特殊处理，那么当外界在布局中使用wrap_content时就无法达到预期的效果。
2. 如果有必要，让你的View支持padding
   这是因为直接继承View的控件，如果不在draw方法中处理padding，那么padding居性是无法起作用的。另外，直接继承自ViewGroup的控件需要在onMeasure和onLayout中考虑padding和子元素的margin对其造成的影响，不然将导致padding和子元素的margin失效。
3. 尽量不要在View中使用Handler(没必要)
   这是因为View内部本身就提供了post系列的方法，完全可以替代Handler的作用，当然除非你很明确地要使用Handler来发送消息。
4. View中如果有线程或者动画，需要及时停止，参考View#onDetachedFromWindow。
   这一条也很好理解，如果有线程或者动画需要停止时，那么onDetachedFromWindow是一个很好的时机。当包含此View的Activity退出或者当前View被remove 时，View的onDetachedFromWindow方法会被调用，和此方法对应的是onAtachedToWindow， 当包含此View的Activity启动时，View的onAtachedToWindow方法会被调用。同时，当View变得不可见时我们也需要停止线程和动画，如果不及时处理这种问题，有可能会造成内存泄漏。
5. View带有滑动嵌套情形时，需要处理好滑动冲突
   如果有滑动冲突的话，那么要合适地处理滑动冲突，否则将会严重影响View的效果。

## invalidate()

该方法的调用会引起View树的重绘，常用于内部调用(比如 setVisiblity())或者需要刷新界面的时候，需要在主线程(即UI线程)中调用该方法。

invalidate()会不断调用父View的invalidate()方法，一直调用ViewRootImpl的invalidate()方法，在ViewRootImpl的invalidate()方法中，最后会调用performTraversals()，但没有设置重新测量的标记，所以只会调用onDraw。

**postInvalidate()**
这个方法与invalidate方法的作用是一样的，都是使View树重绘，但两者的使用条件不同，postInvalidate是在非UI线程中调用，invalidate则是在UI线程中调用。 

## requestLayout()

当动态移动一个View的位置，或者View的大小、形状发生了变化的时候，可以在View中调用这个方法。

从源码注释看出，如果当前View在请求布局的时候，View树正在进行布局流程的话，该请求会延迟到布局流程完成后或者绘制流程完成且下一次布局出现的时候再执行。

在View的requestLayout方法中，首先会设置View的标记位，PFLAG_FORCE_LAYOUT表示当前View要进行重新布局，PFLAG_INVALIDATED表示要进行重新绘制。

requestLayout方法中会一层层向上调用父布局的requestLayout方法，设置PFLAG_FORCE_LAYOUT标记，最终调用的是ViewRootImpl中的requestLayout方法。

可以看到ViewRootImpl中的requestLayout方法中会调用scheduleTraversals方法，scheduleTraversals方法最后会调用performTraversals方法开始执行View的三大流程，会分别调用View的measure、layout、draw方法。

### 总结

requestLayout方法会标记PFLAG_FORCE_LAYOUT，然后一层层往上调用父布局的requestLayout方法并标记PFLAG_FORCE_LAYOUT，最后调用ViewRootImpl中的requestLayout方法开始View的三大流程，然后被标记的View就会进行测量、布局和绘制流程，调用的方法为onMeasure、onLayout和onDraw。

## post方法

Android是消息驱动的模式，View.post的Runnable任务会被加入任务队列，并且等待第一次TraversalRunnable执行结束后才执行，此时已经执行过一次measure，layout过程了，所以在后面执行post的Runnable时，已经有measure的结果，因此此时可以获取到View的宽高。

源码

```java
public boolean post(Runnable action) {
    final AttachInfo attachInfo = mAttachInfo;
    if (attachInfo != null) {
        return attachInfo.mHandler.post(action);
    }

    // Postpone the runnable until we know on which thread it needs to run.
    // Assume that the runnable will be successfully placed after attach.
    getRunQueue().post(action);
    return true;
}
```

如果 <strong>mAttachInfo</strong> 不为空，那就调用 <strong>mAttachInfo.mHanlder.post()</strong> 方法，如果为空，则调用 <strong>getRunQueue().post()</strong> 方法。
我们使用 <strong>View.post()</strong> 时，其实内部它自己分了两种情况处理，当 View 还没有 <strong>attachedToWindow</strong> 时，通过 <strong>View.post(Runnable)</strong> 传进来的 Runnable 操作都先被缓存在 HandlerActionQueue，然后等 View 的 <strong>dispatchAttachedToWindow()</strong> 被调用时，就通过 <strong>mAttachInfo.mHandler</strong> 来执行这些被缓存起来的 Runnable 操作。从这以后到 View 被 <strong>detachedFromWindow</strong> 这段期间，如果再次调用 <strong>View.post(Runnable)</strong> 的话，那么这些 Runnable 不用再缓存了，而是直接交给 <strong>mAttachInfo.mHanlder</strong> 来执行。

<strong>dispatchAttachedToWindow() 是什么时候被调用的？</strong>

<strong>mAttachInfo 是在哪里初始化的？</strong>

在 Activity 首次进行 View 树的遍历绘制时，ViewRootImpl 会将自己的 <strong>mAttachInfo</strong> 通过根布局 DecorView 传递给所有的子 View 。

# View事件分发机制

点击事件即是MotionEvent，由三个方法构成：dispatchTouchEvent、onInterceptTouchEvent、onTouchEvent。

- dispatchTouchEvent：用来事件的分发。如果事件能传递给当前View，那么此方法一定会被调用。

- onInterceptTouchEvent：用来判断是否拦截某个事件。

- onTouchEvent：在dispatchTouchEvent中调用，用来处理点击事件。

上述方法的关系的伪代码:

```java
public boolean dispatchTouchEvent(MotionEvent ev){
	boolean consume = false;
	if  (onInterceptTouchEvent (ev)) {
		consume = onTouchEvent (ev) ;
	}else{
		consume = child.dispatchTouchEvent (ev) ;
	}
	return consume ;
}
```

ViewGroup的dispatchTouchEvent源码简单分析：
参考https://www.jianshu.com/p/e6413de93fff

```java
final boolean intercepted;
if (actionMasked == MotionEvent.ACTION_DOWN || mFirstTouchTarget != null) {
    final boolean disallowIntercept = (mGroupFlags & FLAG_DISALLOW_INTERCEPT) != 0;
    if (!disallowIntercept) {
        intercepted = onInterceptTouchEvent(ev);
        ev.setAction(action);
    } else {
        intercepted = false;
    }
} else {
    intercepted = true;
}
```

以上这段代码是用来判断是否拦截事件，可以看到只有当事件是ACTION_DOWN或
`mFirstTouchTarget != null`时才会去调用`onInterceptTouchEvent()`方法来判断是否拦截该事件。这里mFirstTouchTarget是什么呢？
mFirstTouchTarget是ViewGroup的一个内部类。`mFirstTouchTarget`对象指向的是接受触摸事件的View所组成的链表的起始节点。也就是说，当事件由ViewGroup传递给子元素成功处理时，`mFirstTouchTarget`对象就会被赋值，换种方式来说，也就是说当ViewGroup不拦截事件传递，`mFirstTouchTarget!=null`。如果拦截事件，`mFirstTouchTarget!=null`就不成立。此时如果事件序列中的ACTION_MOVE、ACTION_UP事件再传递过来时，由于`(actionMasked == MotionEvent.ACTION_DOWN || mFirstTouchTarget != null)`条件为false，就不会再调用`onInterceptTouchEvent()`方法，是否被拦截的标志变量也会设置为`intercepted = true`，并且后续同一事件序列的其他事件都会默认交给它处理。

这里还有一种特殊情况，那就是FLAG_DISALLOW_INTERCEPT标记位，这个标记位是通过`requestDisallowInterceptTouchEvent()`方法来设置的。FLAG_DISALLOW_INTERCEPT这个标记位一旦设置后，ViewGroup就无法拦截除ACTION_DOWN以外的其他点击事件。

## **总结**

当一个点击事件产生后，先传递给Activity，Activity 通过Window（实现类是PhoneWindow）来分发，最后PhoneWindow交给了DecorView。DecorView接收到事件后，就会按照View的事件分发机制去分发事件，点击事件的传递规则：

对于一个根ViewGroup来说，点击事件产生后，首先会传递给它，这时它的dispatchTouchEvent就会被调用。如果这个ViewGroup的onInterceptTouceEvent（默认为false）方法返回true就表示它要拦截当前事件，接着事件就会交给这个ViewGroup的onTouchEvent方法处理；如果onInterceptTouchEvent方法返回false就表示它不拦截当前事件，这时当前事件就会继续传递给它的子元素，接着子元素的dispatchTouchEvent方法就会被调用，如此反复直到事件被最终处理。（即上面的伪代码）

当一个View需要处理事件时，如果它设置了OnTouchListener，那么OnTouchListener
中的onTouch方法会被回调。这时事件如何处理还要看onTouch的返回值，如果返回false，则当前View的onTouchEvent方法会被调用；如果返回true，那么onTouchEvent方法将不会被调用。由此可见，给View设置的OnTouchListener，其优先级比onTouchEvent要高。
在onTouchEvent方法中，如果当前设置的有OnClickListener，那么它的onClick方法会被
调用。可以看出，平时用的OnClickListener，其优先级最低，即处于事件传递的尾端。

另外，如果一个View的onTouchEvent（ACTION_DOWN）返回false，那么它的父容器的onTouchEvent将会被调用，依此类推。如果所有的元素都不处理这个事件，那么这个事件将会最终传递给Activity处理。如果非ACTION_DOWN返回了false，那么父容器不会调用自己的onTouchEvent，最终是由Activity处理。

## **几个结论**

1. 同一个事件序列是指从手指接触屏幕的那一刻起，到手指离开屏幕的那一刻结束，在这个过程中所产生的一系列事件，这个事件序列以down事件开始，中间含有数量不定的move事件，最终以up事件结束。
2. 正常情况下，一个事件序列只能被一个View拦截且消耗。这条的原因可以参考 （3），因为一旦一个元素拦截了某此事件，那么同一个事件序列内的所有事件都会直接交给它处理，因此同一个事件序列中的事件不能分别由两个View同时处理，但是通过特殊手段可以做到，比如一个View将本该自己处理的事件通过onTouchEvent强行传递给其他View处理。
3. 某个View一旦决定拦截，那么这一个事件序列都只能由它来处理（如果事件序列能够传递给它的话），并且它的onInterceptTouchEvent不会再被调用。这条也很好理解，就是说当一个View决定拦截一个事件后， 那么系统会把同一个事件序列内的其他方法都直接交给它来处理，因此就不用再调用这个View的onInterceptTouchEvent去询问它是否要拦截了。
4. 某个View一旦开始处理事件， 如果它不消耗ACTION_DOWN事件（onTouchEvent返回了false）， 那么同一事件序列中的其他事件都不会再交给它来处理；并且事件将重新交由它的父元素去处理，即父元素的onTouchEvent会被调用。意思就是事件一旦交给一个View处理，那么它就必须消耗掉，否则同一事件序列中剩下的事件就不再交给它来处理了。
5. 如果View不消耗除ACTION_DOWN以外的其他事件，那么这个点击事件会消失，此时父元素的onTouchEvent 并不会被调用，并且当前View可以持续收到后续的事件，最终这些消失的点击事件会传递给Activity处理。（这么做的原因：个人猜测：此时这个View已经拦截了ACTION_DOWN事件，由3可知，这一系列的事件由此View处理，而非ACTION_DOWN事件不处理，其它View也不能处理，只能交给最顶级的Activity处理）
6. ViewGroup默认不拦截任何事件，Android源码中ViewGroup的onInterceptTouchEvent方法默认返回false。
7. View没有onInterceptTouchEvent方法，一旦有点击事件传递给它，那么它的onTouchEvent方法就会被调用。
8. View的onTouchEvent默认都会消耗事件（返回true）除非它是不可点击的（clickable和longClickable同时为false）。 View的longClickable属性默认都为false， clickable属性要分情况，比如Button的clickable属性默认为true，而TextView的clickable属性默认为false。
9. View的enable属性不影响onTouchEvent的默认返回值。哪怕个View是disable状态的，只要它的clickable或者longClickable有一个为true，那么它的onTouchEvent就返true。
10. onClick会发生的前提是当前View是可点击的，并且它收到了down和up的事件。
11. 事件传递过程是由外向内的，即事件总是先传递给父元素，然后再由父元素分发给子View，通过requestDisallowInterceptTouchEvent方法可以在子元素中干预父元素的事件分发过程，但是ACTION_DOWN事件除外。 

![20180920171512](http://111.230.96.19:8081/image/20180920171512.png)

![20180920171520](http://111.230.96.19:8081/image/20180920171520.png)

## 实验

实验对象：Activity、ViewGroup、View。

### 实验一

Activity、ViewGroup、View的onTouch和onTouchEvent返回false，其余方法返回super。

日志：

```
MyActivity: dispatchTouchEvent: 
MyActivity: dispatchTouchEvent: ACTION_DOWN
MyViewGroup: dispatchTouchEvent: 
MyViewGroup: dispatchTouchEvent: ACTION_DOWN
MyViewGroup: onInterceptTouchEvent: 
MyViewGroup: onInterceptTouchEvent: ACTION_DOWN
MyView: dispatchTouchEvent: 
MyView: dispatchTouchEvent: ACTION_DOWN
MyView: onTouch: 
MyView: onTouch: ACTION_DOWN
MyView: onTouchEvent: 
MyView: onTouchEvent: ACTION_DOWN
MyViewGroup: onTouch: 
MyViewGroup: onTouch: ACTION_DOWN
MyViewGroup: onTouchEvent: 
MyViewGroup: onTouchEvent: ACTION_DOWN
MyActivity: onTouchEvent: 
MyActivity: onTouchEvent: ACTION_DOWN
MyActivity: dispatchTouchEvent: 
MyActivity: dispatchTouchEvent: ACTION_UP
MyActivity: onTouchEvent: 
MyActivity: onTouchEvent: ACTION_UP
```

实验一表示对于一个点击事件，三个对象都不拦截。日志显示，最终Activity会处理事件。此实验结果证明了结论中的第4个结论。

在上面的基础上，更改Activity的ACTION_DOWN和ACTION_UP的返回值，情况与上一样。可以说明，Activity的onTouchEvent对事件分发没有影响。

### 实验二

在实验一的基础上，将View的onTouchEvent的ACTION_DOWN返回true。

```
D/zzsy@MyActivity: dispatchTouchEvent: 
D/zzsy@MyActivity: dispatchTouchEvent: ACTION_DOWN
D/zzsy@MyViewGroup: dispatchTouchEvent: 
D/zzsy@MyViewGroup: dispatchTouchEvent: ACTION_DOWN
D/zzsy@MyViewGroup: onInterceptTouchEvent: 
D/zzsy@MyViewGroup: onInterceptTouchEvent: ACTION_DOWN
D/zzsy@MyView: dispatchTouchEvent: 
D/zzsy@MyView: dispatchTouchEvent: ACTION_DOWN
D/zzsy@MyView: onTouch: 
D/zzsy@MyView: onTouch: ACTION_DOWN
D/zzsy@MyView: onTouchEvent: 
D/zzsy@MyView: onTouchEvent: ACTION_DOWN
D/zzsy@MyActivity: dispatchTouchEvent: 
D/zzsy@MyActivity: dispatchTouchEvent: ACTION_UP
D/zzsy@MyViewGroup: dispatchTouchEvent: 
D/zzsy@MyViewGroup: dispatchTouchEvent: ACTION_UP
D/zzsy@MyViewGroup: onInterceptTouchEvent: 
D/zzsy@MyViewGroup: onInterceptTouchEvent: ACTION_UP
D/zzsy@MyView: dispatchTouchEvent: 
D/zzsy@MyView: dispatchTouchEvent: ACTION_UP
D/zzsy@MyView: onTouch: 
D/zzsy@MyView: onTouch: ACTION_UP
D/zzsy@MyView: onTouchEvent: 
D/zzsy@MyView: onTouchEvent: ACTION_UP
D/zzsy@MyActivity: onTouchEvent: 
D/zzsy@MyActivity: onTouchEvent: ACTION_UP
```

实验二的结果显示，View的onTouchEvent拦截了ACTION_DOWN，其余不拦截，那么，不会调用ViewGroup的onTouchEvent，而是直接调用Activity的onTouchEvent方法。此实验证明了结论5。

### 实验三

实验三将ouTouch的返回变为true，结果显示onTouchEvent不再调用。

### 实验四

之前的实验一直没有出现onClick的日志，查看源码发现onClick是在onTouchEvent中调用，如果不调用super方法，onClick会失效。如果给一个View设置了onClickListener，那么就会表示View是clickable的了，所以默认的onTouchEvent会返回true。

当View的onTouchEvent返回false，那么ViewGroup的onClick会被调用。

## 滑动冲突

内外两层同时可以滑动，这个时候就会产生滑动冲突。

### 常见的滑动冲突场景

1. 外部滑动方向和内部滑动方向不一致
2. 外部滑动方向和内部滑动方向一致
3. 上面两种情况的嵌套

### 滑动冲突的处理规则

对于场景1：**当用户左右滑动的时候，需要让外部的View拦截点击事件，当用户上下滑动时，需要让内部View拦截事件**。

### 滑动冲突的解决方式

两种方式：**外部拦截法**、**内部拦截法**。

#### **外部拦截法**

所谓外部拦截法是指点击事情都先经过父容器的拦截处理，如果父容器需要此事件就拦截，如果不需要此事件就不拦截，这样就可以解决滑动冲突的问题，这种方法比较符合点击事件的分发机制。

伪代码：

```java
@Override
public boolean onInterceptTouchEvent(MotionEvent event) {
    boolean intercepted = false;
    int x = (int) event.getX();
    int y = (int) event.getY();

    switch (event.getAction()) {
    case MotionEvent.ACTION_DOWN: {
        intercepted = false;
        break;
    }
    case MotionEvent.ACTION_MOVE: {
        if (父容器需要的事件) {
            intercepted = true;
        } else {
            intercepted = false;
        }
        break;
    }
    case MotionEvent.ACTION_UP: {
        intercepted = false;
        break;
    }
    default:
        break;
    }

    mLastXIntercept = x;
    mLastYIntercept = y;

    return intercepted;
}
```

#### **内部拦截法**

是指父容器默认拦截除ACTION_DOWN以外所有事件，所有的事件都传递给子元素，如果子元素需要此事件就直接消耗掉，否则就交由父容器进行处理，这种方法和Android分发机制不一致，需要配合requestDisallowinterceptTouchEvent方法才能正常工作，使用比较复杂。

伪代码：

```java
//父容器所做的修改
public boolean onInterceptTouchEvent(MotionEvent event) {
    int action = event.getAction();
    if (action == MotionEvent.ACTION_DOWN) {
        return false;//如果返回true，那么之后的事件就不会传入到子View中
    } else {
        return true;
    }
}
```

```java
//子元素的dispatchTouchEvent
@Override
public boolean dispatchTouchEvent(MotionEvent event) {
    int x = (int) event.getX();
    int y = (int) event.getY();

    switch (event.getAction()) {
    case MotionEvent.ACTION_DOWN: {
        parent.requestDisallowInterceptTouchEvent(true);
        break;
    }
    case MotionEvent.ACTION_MOVE: {
        int deltaX = x - mLastX;
        int deltaY = y - mLastY;
        if (父容器需要的事件) {
        	//当子元素调用此方法时，父元素才能拦截所需事件
            parent.requestDisallowInterceptTouchEvent(false);
        }
        break;
    }
    case MotionEvent.ACTION_UP: {
        break;
    }
    default:
        break;
    }

    mLastX = x;
    mLastY = y;
    return super.dispatchTouchEvent(event);
}
```

### 两者区别

个人认为，两者没什么区别。一定要有的话在冲突不同的情况下，比如ViewPager+ListView，这里用外部拦截法，

# Android的线程和线程池

AsyncTask底层用线程池，IntentService和HandlerThread底层用了线程。

## AsyncTask

AsyncTask是一个抽象类，它是由Android封装的一个轻量级异步类（轻量体现在使用方便、代码简洁），它可以在线程池中执行后台任务，然后把执行的进度和最终结果传递给主线程并在主线程中更新UI。

### 基本使用

1. onPreExecute()
   这个方法会在后台任务开始执行之前调用，用于进行一些界面上的初始化操作，比如显示一个进度条对话框等。
   在调用execute(params)后会调用。
2. doInBackground(Params...)
   这个方法中的所有代码都会在子线程中运行，我们应该在这里去处理所有的耗时任务。任务一旦完成就可以通过return语句来将任务的执行结果返回，如果AsyncTask的第三个泛型参数指定的是Void，就可以不返回任务执行结果。注意，在这个方法中是不可以进行UI操作的，如果需要更新UI元素，比如说反馈当前任务的执行进度，可以调用publishProgress(Progress...)方法来完成。
   在执行任务的时候调用。
3. publishProgress(Progress... values)
   在doInBackground中调用，内部会用一个Handler切换到主线程。
4.  onProgressUpdate(Progress...)
   当在后台任务中调用了publishProgress(Progress...)方法后 ，onProgressUpdate(Progress...)方法就会很快被调用，该方法中携带的参数就是在后台任务中传递过来的。在这个方法中可以对UI进行操作，利用参数中的数值就可以对界面元素进行相应的更新。
5. onPostExecute (Result)
   当后台任务执行完毕并通过return语句进行返回时，这个方法就很快会被调用。返回的数据会作为参数传递到此方法中，可以利用返回的数据来进行一些UI操作，比如说提醒任务执行的结果，以及关闭掉进度条对话框等。
   任务执行完会调用postResult方法，这个方法会用Handler发送一个消息来运行此方法。

### 分析

从起点execute开始分析，这个方法return一个executeOnExecutor。一个进程的所有AsyncTask都在一个串行线程池排队执行。在executeOnExecutor中，onPreExecute(）最先执行，然后线程池执行。

首先系统会把AsyncTask的params封装成FutureTask对象，起到Runnable的作用。然后交给SerialExecutor的execute方法处理。execute方法会把FutureTask对象插入到任务队列中，如果没有正在活动的AsyncTask，那么scheduleNext方法就会执行下一个AsyncTask任务，**这一点可以看出，AsyncTask默认是串行执行的**

AsyncTask有两个线程池（SerialExecutor和THREAD_POOL_EXECUTOR）和一个Handler（InternalHandler），SerialExecutor用于任务的排队，THREAD_POOL_EXECUTOR用于执行任务。InternalHandler用于将执行环境从线程池切换到主线程。

**个人思考：为什么用两个线程池，为什么不直接用一个线程池？**

第一个线程池的源码：

```java
private static class SerialExecutor implements Executor {
    final ArrayDeque<Runnable> mTasks = new ArrayDeque<Runnable>();
    Runnable mActive;

    public synchronized void execute(final Runnable r) {
        //...
    }

    protected synchronized void scheduleNext() {
        if ((mActive = mTasks.poll()) != null) {
            THREAD_POOL_EXECUTOR.execute(mActive);
        }
    }
}
```

接口Executor的源码：

```java
public interface Executor {
    void execute(Runnable command);
}
```

SerialExecutor除了将任务交给第二个线程池外，其余没有涉及线程的地方，因此猜测任务的排队所在的线程在调用AsyncTask.execute(Params)的线程。所以SerialExecutor名字叫线程池，但与线程池关系不大。

### AsyncTask的机制原理

- AsyncTask的本质是一个静态的线程池，AsyncTask派生的子类可以实现不同的异步任务，这些任务都是提交到静态的线程池中执行。
- 线程池中的工作线程执行doInBackground()方法执行异步任务。
- 当任务状态改变之后，工作线程会向UI线程发送消息，AsyncTask内部的InternalHandler响应这些消息，并调用相关的回调函数。

### 注意

- AsyncTask不适合大量数据的请求，因为AsyncTask中线程池**一个时间只能执行一个，因为使用了同步锁**；

- 由于Handler需要和主线程交互，而Handler又是内置于AsyncTask中，所以AsyncTask的创建必须在主线程。
- AsyncTaskResult的doInBackground(Params)方法执行异步任务运行在子线程中，其他方法运行在主线程中，可以操作UI组件。
- 不要手动的去调用AsyncTask的onPreExecute，doInBackground，onProgressUpdate，onPostExecute方法。
- 一个AsyncTask任务只能被执行一次。
- 运行中可以随时调用cancel(boolean)方法取消任务，如果成功调用isCancel()会返回true，并不会执行onPostExecute()，取而代之的是调用onCancelled()。从源码看，如果这个任务已经执行了这个时候调用cancel是不会真正的把task结束，而是继续执行，只不过改变的是执行之后的回调方法的onPostExecute还是onCancelled。
- 可能存在内存泄露情况，即非静态内部类持有外部类引用，解决办法同，Handler内存泄露解决办法一样，（在activity的onDestory 方法中调用 AsyncTask的cancel()方法）
- 并行或串行：在android 1.6之前的版本asynctask都是串行，即把任务放线程池中一串一串的执行，1.6到2.3改成并行，2.3之后为了维护系统稳定改成串行，但是任然可以执行并行操作。

### AsyncTask线程数目

```java
private static final int CORE_POOL_SIZE = Math.max(2, Math.min(CPU_COUNT - 1, 4));
private static final int MAXIMUM_POOL_SIZE = CPU_COUNT * 2 + 1;
private static final int KEEP_ALIVE_SECONDS = 30;

private static final BlockingQueue<Runnable> sPoolWorkQueue =
            new LinkedBlockingQueue<Runnable>(128);

ThreadPoolExecutor threadPoolExecutor = new ThreadPoolExecutor(
        CORE_POOL_SIZE, MAXIMUM_POOL_SIZE, KEEP_ALIVE_SECONDS, TimeUnit.SECONDS,
        sPoolWorkQueue, sThreadFactory);
```

至少2个，至多4个核心线程。

任务数量最大128。

> 个人总结:
>
> AsyncTask是一个轻量级的异步任务类，内部有2个线程池和一个Handler，SerialExecutor用于任务的排队，内部的execute和scheduleNext方法加了同步锁，保证了任务的顺序执行，THREAD_POOL_EXECUTOR用来真正的执行任务，官方注释说可以并行执行任务，但由于锁机制，导致也只能异步执行。Handler是一个InternalHandler，用来将线程切换到主线程。

### AsyncTask使用不当的后果

1. 生命周期
   AsyncTask不与任何组件绑定生命周期，所以在Activity/或者Fragment中创建执行AsyncTask时，最好在Activity/Fragment的onDestory()调用 cancel(boolean)；

2. 内存泄漏
   如果AsyncTask被声明为Activity的非静态的内部类，那么AsyncTask会保留一个对创建了AsyncTask的Activity的引用。如果Activity已经被销毁，AsyncTask的后台线程还在执行，它将继续在内存里保留这个引用，导致Activity无法被回收，引起内存泄露。解决方式和Handler差不多。

3. 结果丢失
   屏幕旋转或Activity在后台被系统杀掉等情况会导致Activity的重新创建，之前运行的AsyncTask（非静态的内部类）会持有一个之前Activity的引用，这时调用onPostExecute()再去更新界面将不再生效。

## HandlerThread

HandlerThread继承了Thread，内部创建了一个Looper，所以可以使用Handler，HandlerThread具体使用的场景是IntentService。

## 线程池

### 简单介绍

线程池的优点：

1. 重用线程池中的线程，避免因为线程的创建和销毁所带来的性能开销。
2. 能有效控制线程池的最大并发数，避免大量的线程之间因互相抢占系统资源而导致阻塞。
3. 能对线程进行简单的管理，并提供定时执行以及指定间隔循环执行等功能。

Android中最常见的四类具有不同功能特性的线程池，都是用ThreadPoolExecutor直接或间接实现自己的特性的：FixedThreadPool、CachedThreadPool、ScheduledThreadPool、SingleThreadExecutor。

### 线程池的分类

核心线程指不会被回收的线程。非核心线程指最大线程数减核心线程数，会被回收。

**FixedThreadPool：**

- 线程数量固定（需用户指定），当线程处于空闲状态也不会被回收，除非线程池被关闭。
- 只有核心线程，并且没有超时机制，另外任务队列没有大小限制。

**CachedThreadPool：**

- 线程数量不定，只有非核心线程，最大的线程数为Integer.MAX_VALUE
- 空闲线程具有超时机制，超过60秒就会被回收。
- 适合大量耗时少的任务。

**ScheduledThreadPool：**

- 核心线程数量固定，非核心线程没有限制，非核心线程闲置时会被立即回收。
- 主要用于执行定时任务和具有固定周期的重复任务。

**SingleThreadExecutor：**

- 只有一个核心线程，确保所有的任务都在同一个线程按顺序执行
- 意义在于统一所有的外界任务到一个线程，使得不需要处理同步问题。

### 自定义线程池

ThreadPoolExecutor是线程池的真正实现。

### 笔记

见笔记[Android线程和线程池](https://mezzsy.github.io/2019/06/23/Android/Android线程和线程池/)

# 性能优化

## Bitmap优化

### 加载图片

BitmapFactory类提供了四类方法：decodeFile、decodeResource、 decodeSteam和decodeByteAray分别用于支持从文件系统、资源、输入流以及字节数组中加载出一个Bitmap对象，其中decodeFile和decodeResource又间接调用了decodeStream方法，这四类方法最终是在Android的底层实现的，对应着BitmapFactory类的几个native方法。

### 高效加载Bitmap

采用BitmapFactory.Options来加载所需尺寸的图片。

通过BitmapFactory.Options来缩放图片，主要是用到了它的inSampleSize参数，即**采样率**。
当inSampleSize为1时，采样后的图片大小为图片的原始大小；
当inSampleSize大于1时，比如为2，那么采样后的图片其宽/高均为原图大小的1/2，而像素数为原图的1/4。可以发现采样率inSampleSize必须是大于1的整数图片才会有缩小的效果，并且采样率同时作用于宽/高。
当inSampleSize小于1时，其作用相当于1，即无缩放效果。

考虑实际的情况，比如ImageView的大小是100x100像素，而图片的原始大小为200x200，那么只需将采样率inSampleSize设为2即可。但是如果图片大小为200x300呢？这个时候采样率还应该选择2，这样缩放后的图片大小为100x150 像素，仍然是适合imageView的，如果采样率为3，那么缩放后的图片大小就会小于ImageView所期望的大小这样图片就会被拉伸从而导致模糊。

**获取采样率**

获取采样率也很简单，遵循如下流程：

1. 将BitmapFactory.Options的inJustDecodeBounds参数设为tnue并加载图片。
2. 从BitmapFactory.Options中取出图片的原始宽高信息，它们对应于outWidth和outHeight参数。
3. 根据采样率的规则并结合目标View的所需大小计算出采样率inSampleSize。
4. 将BitmapFactory.Options的inJustDecodeBounds参数设为false，然后重新加载图片。

经过上面4个步骤，加载出的图片就是最终缩放后的图片，当然也有可能不需要缩放。
这里说明一下inJustDecodeBounds参数，当此参数设为true时，BitmapFactory只会解析图片的原始宽高信息，并不会去真正地加载图片，所以这个操作是轻量级的。

### 优化策略

使用适当分辨率和大小的图片；

及时回收内存：从Android 3.0开始，Bitmap被放置到了堆中，其内存由GC管理，所以不用手动调用bitmap.recycle()方法进行释放了；

1. 对图片质量进行压缩

   ```java
   public static Bitmap compressImage(Bitmap bitmap){  
   		ByteArrayOutputStream baos = new ByteArrayOutputStream();  
   		//质量压缩方法，这里100表示不压缩，把压缩后的数据存放到baos中              				bitmap.compress(Bitmap.CompressFormat.JPEG， 100， baos);  
   		int options = 100;  
   		//循环判断如果压缩后图片是否大于50kb，大于继续压缩  
   		while ( baos.toByteArray().length / 1024>50) {                 
   			//清空baos  
   			baos.reset();  
   			bitmap.compress(Bitmap.CompressFormat.JPEG， options， baos);  
   			options -= 10;//每次都减少10  
   		}  
   		//把压缩后的数据baos存放到ByteArrayInputStream中  
   		ByteArrayInputStream isBm = new ByteArrayInputStream(baos.toByteArray());  
   		//把ByteArrayInputStream数据生成图片  
   		Bitmap newBitmap = BitmapFactory.decodeStream(isBm， null， null);  
   		return newBitmap;  
   } 
   ```

2. 对图片尺寸进行压缩

   ```java
   public static Bitmap compressImageFromBitmap(Bitmap bitmap， int pixelW， int pixelH) {
           ByteArrayOutputStream os = new ByteArrayOutputStream();
           bitmap.compress(Bitmap.CompressFormat.JPEG， 100， os);
           if( os.toByteArray().length / 1024>512) {//判断如果图片大于0.5M，进行压缩避免在生成图片（BitmapFactory.decodeStream）时溢出
               os.reset();
               bitmap.compress(Bitmap.CompressFormat.JPEG， 50， os);//这里压缩50%，把压缩后的数据存放到baos中
           }
           ByteArrayInputStream is = new ByteArrayInputStream(os.toByteArray());
           BitmapFactory.Options options = new BitmapFactory.Options();
           options.inJustDecodeBounds = true;
           options.inPreferredConfig = Bitmap.Config.RGB_565;
           BitmapFactory.decodeStream(is， null， options);
           options.inJustDecodeBounds = false;
           options.inSampleSize = 计算尺寸;
           is = new ByteArrayInputStream(os.toByteArray());
           Bitmap newBitmap = BitmapFactory.decodeStream(is， null， options);
           return newBitmap;
   }
   ```

3. 使用图片缓存
   设计内存缓存和磁盘缓存可以更好地利用Bitmap。

## 布局优化

- 删除无用控件和减少层级
- 选择性能较低的ViewGroup
- 利用merag和include进行布局重用
- 利用ViewStub进行延迟加载

具体见View绘制流程的布局优化

## 绘制优化

- 不要在onDraw里创建对象
- 不要在onDraw里做耗时操作

### 过度绘制优化

可以利用开发者选项的显示过度绘制区域来显示过度绘制区域，也可以利用Layout Inspector来查看View树。

具体见View绘制流程的过度绘制优化

可以从这几个方面进行优化：

1. 去除无用背景
   当布局中有多重背景时会导致视图的过度绘制，通过删除删除布局中不需要的背景来减少视图的过度绘制。
   在布局中，如果存在多个线性布局重叠时，可以考虑只针对最上层的布局设置背景色，而不需要每一个布局（例如LinearLayout）都设置背景色，过多的相同的背景色会导致过度绘制。
2. 在自定义view的onDraw中过度绘制问题
   在自定义view的onDraw中，如果涉及到重叠的绘制view时，可以考虑利用局部绘制避免过度绘制。
   考虑到效率和性能问题，界面是有一定刷新频率的，每一次刷新都会调用View的onDraw方法，而View提前绘制就是在onDraw中进行，避免在onDraw创建对象，避免在onDraw进行绘制，应在构造函数中画好，交给onDraw。

## 内存优化

### 内存泄漏优化

#### 静态变量导致的内存泄漏

单例对象也是如此。

#### 属性动画

无限循环的属性动画没有及时关闭。

#### 注册解注册

对于一些需要注册的对象，需要及时解注册。

#### Handler

##### 具体原理分析

通过Handler发送延时Message的时候，Message没有被及时处理，Message是持有Handler的引用，而Handler是通过匿名内部类的形式创建的，会默认持有外部类Activity的引用。这样在GC垃圾回收机制进行回收时发现这个Activity居然还有其他引用存在，因而就不会去回收这个Activity。 

##### 解决方案

**1.在Activity结束时将Handler里面的Message清空**

由于在Activity结束后，Handler里面的消息还没有被处理导致，消息不处理完Handler的引用就一直存在。因而我们可以在onDestroy中将Handler里面的消息给清空了，这样就不会有消息引用Handler了，也就不会因为Handler引用Activity导致Activity无法释放了。

```java
@Override
protected void onDestroy() {
    super.onDestroy();
    //将Handler里面消息清空了。
    mHandler.removeCallbacksAndMessages(null);
}
```

**2.静态内部类+弱引用**

为了避免非静态内部类&匿名内部类持有外部类引用可以采用静态内部类或者直接在外部编写该Handler的继承类。如果该类需要使用Activity相关变量，可以采用弱引用的方式将Activity的变量传过去。在获取Activity的时候还可以加上判断当前Activity是不是isFinishing的代码，避免因为当前Activity已经进入了finish状态，还去引用这个Activity。

```java
public class MainActivity extends Activity {
private CustomHandler mHandler;
 
@Override
protected void onCreate(Bundle savedInstanceState) {
super.onCreate(savedInstanceState);
        mHandler = new CustomHandler(this);
    }
 
static class CustomHandler extends Handler {
// 内部声明一个弱引用，引用外部类
private WeakReference<MainActivity > activityWeakReference;
public MyHandler(MyActivity activity) {
            activityWeakReference= new WeakReference<MainActivity >(activity);
        }
// ... ...   
    }
}
```

### 缓存对象

避免重复创建对象。

#### 缓存策略

目前常用的一种缓存算法是LRU (Least Recently Used)，LRU是近期最少使用算法，它的**核心思想是当缓存满时，会优先淘汰那些近期最少使用的缓存对象。**采用LRU算法的缓存有两种：LruCache和DiskLruCache，LruCache用于实现内存缓存，而DiskLruCache则充当了存储设备缓存。

**LruCache**

[LruCache源码分析](/Applications/Projects/Blog/源码分析/LruCache源码分析.md)

LruCache是一个泛型类，它内部采用一个LinkedHashMap以强引用的方式存储外界的缓存对象，其提供了get和put方法来完成缓存的获取和添加操作，当缓存满时，LruCache会移除较早使用的缓存对象，然后再添加新的缓存对象。

LruCache是线程安全的，用synchronized来同步。

基本使用

```java
int maxMemory = (int)(Runtime.getRuntime().maxMemory()/1024);
int cacheSize = maxMemory / 8;
mMemoryCache = new LruCache<String， Bitmap> (cacheSize) {
      @Override
      protected int sizeOf(String key， Bitmap bitmap) {
          return bitmap.getRowBytes() * bitmap .getHeight() / 1024;
      }
};
```

在上面的代码中，只需要提供缓存的总容量大小并重写sizeOf方法即可。
sizeOf方法的作用是计算缓存对象的大小，这里大小的单位需要和总容量的单位一致。对于上面的示例代码来说，总容量的大小为当前进程的可用内存的1/8，单位为KB，而sizeOf方法则完成了Bitmap对象的大小计算。很明显，之所以除以1024也是为了将其单位转换为KB。

一些特殊情况下，还需要重写LruCache的entryRemoved方法，LruCache移除旧缓存时会调用entryRemoved方法，因此可以在entryRemoved中完成些资源回收工作 (如果需要的话)。

除了LruCache的创建以外，还有缓存的获取和添加，这也很简单，从LruCache中获取一个缓存对象，如下所示。

`mMemoryCache.get(key)`

向LruCache中添加一个缓存对象，如下所示。

`mMemoryCache.put(key， bitmap)`

LruCache还支持删除操作，通过remove方法即可删除个指定的缓存对象。

**DiskLruCache**

DiskLruCache用于实现存储设备缓存，即磁盘缓存，它通过将缓存对象写入文件系统从而实现缓存的效果。DiskLruCache得到了Android官方文档的推荐，但它不属于AndroidSDK的一部分。

**三级缓存策略**

先从内存缓存获取，如果没有，再从硬盘缓存获取，如果没有，最后从网络获取。

#### Glide的缓存方式

[Glide源码分析](/Applications/Projects/Blog/源码分析/Glide源码分析.md)

### OOM 问题如何处理

OOM主要原因有两个：

1. 内存泄露，资源造成得不到释放。
2. 保存了多个内存过大的对象（如Bitmap），造成内存超出限制。

针对图片过大的OOM的解决方法：

1. 高效加载大图片，利用图片压缩。
   见Bitmap优化

2. 利用图片缓存技术
   见缓存对象

减少内存占用的方法：

1. 使用更加轻量的数据结构

2. 避免在Android里面使用Enum

3. 减小Bitmap对象的内存占用

4. Bitmap对象的复用
   除了缓存还有一种方式
   **inBitMap高级特性**：利用inBitmap的高级特性提高Android系统在Bitmap分配与释放执行效率。使用inBitmap属性可以告知Bitmap解码器去尝试使用已经存在的内存区域，新解码的Bitmap会尝试去使用之前那张Bitmap在Heap中所占据的pixel data内存区域，而不是去问内存重新申请一块区域来存放Bitmap。利用这种特性，即使是上千张的图片，也只会仅仅只需要占用屏幕所能够显示的图片数量的内存大小
5. 使用更小的图片
6. 避免在onDraw方法里面执行对象的创建
7. 避免对象的内存泄露

### 其他内存优化

- 使用一些Android特有的数据结构，比如SparseArray和Pair等，它们都具有更好的性能
- 适当使用软引用和弱引用

## 启动优化

app启动分为冷启动（Cold start）、热启动（Hot start）和温启动（Warm start）三种。

### 冷启动（Cold start）

冷启动是指APP在手机启动后第一次运行，或者APP进程被kill掉后在再次启动。
可见冷启动的必要条件是该APP进程不存在，这就意味着系统需要创建进程，APP需要初始化。

在这三种启动方式中，冷启动耗时最长，对于冷启动的优化也是最具挑战的。

在冷启动开始时，系统有三个任务。这些任务是： 

1. 加载并启动应用程序
2. 启动后立即显示应用程序的空白启动窗口
3. 创建应用程序进程

当系统创建了应用进程之后，开始创建应用程序对象。

1、启动主线程 2、创建主Activity 3、加载布局 4、屏幕布局 5、执行初始绘制

应用程序进程完成第一次绘制后，系统进程会交换当前显示的背景窗口，将其替换为主活动。此时，用户可以开始使用该应用程序。至此启动完成。

### Application创建

当Application启动时，空白的启动窗口将保留在屏幕上，直到系统首次完成绘制应用程序。此时，系统进程会交换应用程序的启动窗口，允许用户开始与应用程序进行交互。这就是为什么程序启动时会先出现一段时间的黑屏(白屏)。

如果有Application，系统会`onCreate()`在Application对象上调用该方法。之后，应用程序会生成主线程（也称为UI线程），并通过创建主要活动来执行任务。

从这一点开始，App就按照他的应用程序生命周期阶段进行。

### Activity创建

应用程序进程创建活动后，活动将执行以下操作：

1. 初始化值。
2. 调用构造函数。
3. 调用回调方法，例如 Activity.onCreate()，对应Activity的当前生命周期状态。

通常，该onCreate()方法对加载时间的影响最大，因为它以最高的开销执行工作：加载和膨胀视图，以及初始化活动运行所需的对象。

### 热启动（Hot start）

App进程存在，并且Activity对象仍然存在内存中没有被回收。可以重复避免对象初始化，布局解析绘制。
场景就类似你打开微信聊了一会天这时候出去看了下日历 在打开微信 微信这时候启动就属于热启动。

热启动显示与冷启动方案相同的屏幕行为：系统进程显示空白屏幕，直到应用程序完成呈现活动。

### 温启动（Warm start）

App进程存在，当时Activity可能因为内存不足被回收。这时候启动App不需要重新创建进程，但是Activity的onCreate还是需要重新执行的。场景类似打开淘宝逛了一圈然后切到微信去聊天去了，过了半小时再次回到淘宝。这时候淘宝的进程存在，但是Activity可能被回收，这时候只需要重新加载Activity即可。

场景：

- 用户退出您的应用，但随后重新启动它。该过程可能已继续运行，但应用程序必须通过调用从头开始重新创建Activity 的onCreate()。
- 系统将您的应用程序从内存中逐出，然后用户重新启动它。需要重新启动进程和活动，但是在调用onCreate()的时候可以从Bundle（savedInstanceState）获取数据。

因此在创建应用程序和创建Activity期间都可能会出现性能问题。

这里是慢的定义：

- 冷启动需要5秒或更长时间。
- 温启动需要2秒或更长时间。
- 热启动需要1.5秒或更长时间。

无论何种启动，优化点都是： **Application、Activity创建以及回调等过程**

谷歌官方给的建议是：

1. 利用提前展示出来的Window，快速展示出来一个界面，给用户快速反馈的体验
2. 避免在启动时做密集沉重的初始化（Heavy app initialization）
3. 避免I/O操作、反序列化、网络操作、布局嵌套等

### 具体做法

#### 利用提前展示出来的Window，快速展示出来一个界面

在style中自定义一个样式Lancher，在其中放一张背景图片，或是广告图片之类的

```xml
<style name="AppTheme.Launcher">
    <item name="android:windowBackground">@drawable/ic_launcher_background</item>
</style>
```

把这个样式设置给启动的Activity

```xml
<activity android:name=".MainActivity"
    android:theme="@style/AppTheme.Launcher">
```

然后在Activity的onCreate方法，把Activity设置回原来的主题

```java
@Override
protected void onCreate(Bundle savedInstanceState) {
    setTheme(R.style.AppTheme);
    super.onCreate(savedInstanceState);
    setContentView(R.layout.activity_main);
    //...
}
```

这样在启动时就通过给用户看一张图片或是广告来防止黑白屏的尴尬。

#### 避免在启动时做密集沉重的初始化

假设MyApplication的初始化操作有友盟，百度，bugly，数据库，IM，神策，图片加载库，网络请求库，广告sdk，地图，推送等。这些会导致Application加载缓慢，需要异步执行：

1. 比如像友盟，bugly这样的业务非必要的可以的异步加载。 
2. 比如地图，推送等，非第一时间需要的可以在主线程做延时启动。当程序已经启动起来之后，在进行初始化。 
3. 对于图片，网络请求框架必须在主线程里初始化了。

同时因为一般会有闪屏页面，也可以把延时启动的地图，推动的启动在这个时间段里，这样合理安排时间片的使用，极大的提高了启动速度。

#### 避免I/O操作、反序列化、网络操作、布局嵌套

略。

### 总结

1. 利用提前展示出来的Window，快速展示出来一个界面，给用户快速反馈的体验；
2. 避免在启动时做密集沉重的初始化（Heavy app initialization）；
3. 避免I/O操作、反序列化、网络操作、布局嵌套等。 

## 包体优化

<img src="/Users/mezzsy/知识点/img/1.jpg" alt="1" style="zoom:50%;" />

- **assets文件夹** 存放一些配置文件、资源文件，assets不会自动生成对应的 ID，而是通过 AssetManager 类的接口获取。
- **res目录** res 是 resource 的缩写，这个目录存放资源文件，会自动生成对应的 ID 并映射到 .R 文件中，访问直接使用资源 ID。
- **META-INF** 保存应用的签名信息，签名信息可以验证 APK 文件的完整性。
- **AndroidManifest.xml** 这个文件用来描述 Android 应用的配置信息，一些组件的注册信息、可使用权限等。
- **classes.dex** Dalvik 字节码程序，让 Dalvik 虚拟机可执行，一般情况下，Android 应用在打包时通过 Android SDK 中的 dx 工具将 Java 字节码转换为 Dalvik 字节码。
- **resources.arsc** 记录着资源文件和资源 ID 之间的映射关系，用来根据资源 ID 寻找资源。

需要从代码和资源两个方面去减少响应的大小。

1、首先可以使用 lint 工具，如果有没有使用过的资源就会打印如下的信息：

```
res/layout/preferences.xml: Warning: The resource R.layout.preferences appears to be unused [UnusedResources]
```

2、同时可以开启资源压缩，自动删除无用的资源

```
android {
    ...
    buildTypes {
        release {
            shrinkResources true
            minifyEnabled true
            proguardFiles getDefaultProguardFile('proguard-android.txt'), 'proguard-rules.pro'
        }
    }
```

可以使用可绘制对象，某些图像不需要静态图像资源；框架可以在运行时动态绘制图像。Drawable对象（`<shape>`以XML格式）可以占用APK中的少量空间。此外，XML Drawable对象产生符合“材料设计”准则的单色图像。

简单说来就是尽量用XML写Drawable。

3、重用资源，比如一个三角按钮，点击前三角朝上代表收起的意思，点击后三角朝下，代表展开，一般情况下会用两张图来切换，完全可以用旋转的形式去改变。

```xml
<?xml version="1.0" encoding="utf-8"?>
<rotate xmlns:android="http://schemas.android.com/apk/res/android"
    android:drawable="@drawable/ic_thumb_up"
    android:pivotX="50%"
    android:pivotY="50%"
    android:fromDegrees="180" />
```

比如同一图像的着色不同，可以用android:tint和tintMode属性，低版本（5.0以下）可以使用ColorFilter。

4、压缩PNG和JPEG文件 您可以减少PNG文件的大小，而不会丢失使用工具如图像质量 pngcrush，pngquant，或zopflipng。所有这些工具都可以减少PNG文件的大小，同时保持感知的图像质量。

5、使用WebP文件格式 可以使用图像的WebP文件格式，而不是使用PNG或JPEG文件。WebP格式提供有损压缩（如JPEG）以及透明度（如PNG），但可以提供比JPEG或PNG更好的压缩。

可以使用Android Studio将现有的BMP，JPG，PNG或静态GIF图像转换为WebP格式。

6、使用矢量图形 可以使用矢量图形来创建与分辨率无关的图标和其他可伸缩Image。使用这些图形可以大大减少APK大小。一个100字节的文件可以生成与屏幕大小相关的清晰图像。

但是，系统渲染每个VectorDrawable对象需要花费大量时间 ，而较大的图像需要更长的时间才能显示在屏幕上。因此，请考虑仅在显示小图像时使用这些矢量图形。

不要把AnimationDrawable用于创建逐帧动画，因为这样做需要为动画的每个帧包含一个单独的位图文件，这会大大增加APK的大小。

7、代码混淆 使用proGuard 代码混淆器工具，它包括压缩、优化、混淆等功能。

```
android {
    buildTypes {
        release {
            minifyEnabled true
            proguardFiles getDefaultProguardFile(‘proguard-android.txt'),
                    'proguard-rules.pro'
        }
    }
```

8、插件化。 比如功能模块放在服务器上，按需下载，可以减少安装包大小。

## 耗电优化

谷歌在耗电优化这方面显得有些无力，略。

## ANR

Activity：5秒
Broadcast：10秒
Service：20秒
会报ANR，都是在主线程中运行的

三种常见类型：

1. KeyDispatchTimeout(5 seconds) 

   按键或触摸事件在特定时间内无响应

2. BroadcastTimeout(10 seconds)

   BroadcastReceiver在特定时间内无法处理完成

3. ServiceTimeout(20 seconds) 

   Service在特定的时间内无法处理完成

如果在开发过程中遇到了ANR，那么怎么定位问题呢？

当一个进程发生ANR了以后，系统会在/data/anr目录下创建一个文件traces.txt，通过分析这个文件就能定位出ANR的原因。

## Fragment懒加载

在Fragment中有一个setUserVisibleHint方法，而且这个方法比onCreate()先执行，它会通过isVisibleToUser来判断当前Fragment是否可见，可以在可见的时候再进行网络加载。

```java
public void setUserVisibleHint(boolean isVisibleToUser)
```

只有可见时，isVisibleToUser为true，否则为false。所可以重写`setUserVisibleHint`方法，然后在可见时进行网络加载数据：

```java
@Override
public void setUserVisibleHint(boolean isVisibleToUser) {
    Log.d("TAG"， mTagName + " setUserVisibleHint() --> isVisibleToUser = " + isVisibleToUser);

    if (isVisibleToUser) {
        pullData();
    }
    super.setUserVisibleHint(isVisibleToUser);
}
```

# Drawable

见笔记：[Drawable](https://mezzsy.github.io/2019/08/09/Android/Drawable/)

# Android动画

笔记：[Android动画](/Applications/Projects/Blog/Android/Android动画.md)

Android的动画可以分为三种：View动画、帧动画和属性动画。

## 帧动画

帧动画是顺序播放一组预先定义好的图片，类似于电影播放。不同于View动画，系统提供了另一个类AnimationDrawable来使用帧动画。

## View动画（补间动画）

它支持4种动画效果，分别是平移动画、缩放动画、旋转动画和透明度动画。

View动画的四种变换效果对应着Animation的4个子类：TranslateAnimation、ScaleAnimation、RotateAnimation和AlphaAnimation。

### 特殊使用场景

VIew动画还可以在一些特殊场景下使用，比如ViewGroup中可以控制子元素的出场效果，在Activity中可以实现不同Activity之间的切换效果。

## 属性动画

如果只需要对View进行移动、缩放、旋转和淡入淡出操作，那么补间动画确实已经足够健全了。但是很显然，这些功能是不足以覆盖所有的场景的，一旦需求超出了移动、缩放、旋转和淡入淡出这四种对View的操作，那么补间动画就不能实现了，也就是说它在功能和可扩展方面都有相当大的局限性。

补间动画只能够作用在View上的。也就是说，可以对一个Button、TextView、甚至是LinearLayout、或者其它任何继承自View的组件进行动画操作，但是如果想要对一个非View的对象进行动画操作，补间动画就不能使用了。怎么会需要对一个非View的对象进行动画操作呢？
这里举一个简单的例子，比如说有一个自定义的View，在这个View当中有一个Point对象用于管理坐标，然后在onDraw()方法当中就是根据这个Point对象的坐标值来进行绘制的。也就是说，如果可以对Point对象进行动画操作，那么整个自定义View的动画效果就有了。显然，补间动画是不具备这个功能的，这是它的第一个缺陷。

然后补间动画还有一个缺陷，就是它只能够实现移动、缩放、旋转和淡入淡出这四种动画操作，那如果希望可以对View的背景色进行动态地改变呢？说白了，之前的补间动画机制就是使用硬编码的方式来完成的，功能限定死就是这些，基本上没有任何扩展性可言。

最后，补间动画还有一个致命的缺陷，就是它只是改变了View的显示效果而已，而不会真正去改变View的属性。什么意思呢？比如说，现在屏幕的左上角有一个按钮，然后我们通过补间动画将它移动到了屏幕的右下角，现在你可以去尝试点击一下这个按钮，点击事件是绝对不会触发的，因为实际上这个按钮还是停留在屏幕的左上角，只不过补间动画将这个按钮绘制到了屏幕的右下角而已。

# Android虚拟机与Java虚拟机

## Dalvik虚拟机

Dalvik是Google公司自己设计用于Android平台的Java虚拟机，它是Android平台的重要组成部分，支持dex格式（Dalvik Executable）的Java应用程序的运行。dex格式是专门为Dalvik设计的一种压缩格式，适合内存和处理器速度有限的系统。Google对其进行了特定的优化，使得Dalvik具有高效、简洁、节省资源的特点。

Dalvik作为面向Linux、为嵌入式操作系统设计的虚拟机，主要负责完成对象生命周期管理、堆栈管理、线程管理、安全和异常管理，以及垃圾回收等。另外，Dalvik早期并没有JIT编译器，直到Android2.2才加入了对JIT的技术支持。

### 特点

- 体积小，占用内存空间小；

- 专有的DEX可执行文件格式，体积更小，执行速度更快；

- 常量池采用32位索引值，寻址类方法名，字段名，常量更快；

- 基于寄存器架构，并拥有一套完整的指令系统；

- 提供了对象生命周期管理，堆栈管理，线程管理，安全和异常管理以及垃圾回收等重要功能；

- 所有的Android程序都运行在Android系统进程里，每个进程对应着一个Dalvik虚拟机实例。

### 结构

![32](/Users/mezzsy/知识点/img/32.png)

一个应用首先经过DX工具将class文件转换成Dalvik虚拟机可以执行的dex文件，然后由类加载器加载原生类和Java类，接着由解释器根据指令集对Dalvik字节码进行解释、执行。最后，根据dvm_arch参数选择编译的目标机体系结构。

## ART虚拟机

### 什么是ART

Android Runtime（缩写为ART），在Android 5.0及后续Android版本中作为正式的运行时库取代了以往的Dalvik虚拟机。ART能够把应用程序的字节码转换为机器码，是Android所使用的一种新的虚拟机。它与Dalvik的主要不同在于：Dalvik采用的是JIT技术，字节码都需要通过即时编译器（just in time ，JIT）转换为机器码，这会拖慢应用的运行效率，而ART采用Ahead-of-time（AOT）技术，应用在第一次安装的时候，字节码就会预先编译成机器码，这个过程叫做预编译。

ART模式相比原来的Dalvik，会在安装APK的时候，使用Android系统自带的dex2oat工具把APK里面的.dex文件转化成OAT文件，OAT文件是一种Android私有ELF文件格式，它不仅包含有从DEX文件翻译而来的本地机器指令，还包含有原来的DEX文件内容。这使得我们无需重新编译原有的APK就可以让它正常地在ART里面运行，也就是我们不需要改变原来的APK编程接口。ART模式的系统里，同样存在DexClassLoader类，包名路径也没变，只不过它的具体实现与原来的有所不同，但是接口是一致的。实际上，ART运行时就是和Dalvik虚拟机一样，实现了一套完全兼容Java虚拟机的接口。

### 优点

1. 系统性能的显著提升。
2. 应用启动更快、运行更快、体验更流畅、触感反馈更及时。
3. 更长的电池续航能力。
4. 支持更低的硬件。

### 缺点

1. 更大的存储空间占用，可能会增加10%-20%。
2. 更长的应用安装时间。

## Dalvik虚拟机和Java虚拟机的区别

Dalvik虚拟机与传统的Java虚拟机有着许多不同点，两者并不兼容，它们显著的不同点主要表现在以下几个方面：

**Java虚拟机运行的是Java字节码，Dalvik虚拟机运行的是Dalvik字节码。**

传统的Java程序经过编译，生成Java字节码保存在class文件中，Java虚拟机通过解码class文件中的内容来运行程序。而Dalvik虚拟机运行的是Dalvik字节码，所有的Dalvik字节码由Java字节码转换而来，并被打包到一个DEX（Dalvik Executable）可执行文件中。Dalvik虚拟机通过解释DEX文件来执行这些字节码。

**Dalvik可执行文件体积小。Android SDK中有一个叫dx的工具负责将Java字节码转换为Dalvik字节码。**

dx工具对Java类文件重新排列，消除在类文件中出现的所有冗余信息，避免虚拟机在初始化时出现反复的文件加载与解析过程。一般情况下，Java类文件中包含多个不同的方法签名，如果其他的类文件引用该类文件中的方法，方法签名也会被复制到其类文件中，也就是说，多个不同的类会同时包含相同的方法签名，同样地，大量的字符串常量在多个类文件中也被重复使用。这些冗余信息会直接增加文件的体积，同时也会严重影响虚拟机解析文件的效率。消除其中的冗余信息，重新组合形成一个常量池，所有的类文件共享同一个常量池。由于dx工具对常量池的压缩，使得相同的字符串，常量在DEX文件中只出现一次，从而减小了文件的体积。

简单来讲，dex格式文件就是将多个class文件中公有的部分统一存放，去除冗余信息。

**Java虚拟机与Dalvik虚拟机架构不同。**

这也是Dalvik与JVM之间最大的区别。

Java虚拟机基于栈架构，程序在运行时虚拟机需要频繁的从栈上读取或写入数据，这个过程需要更多的指令分派与内存访问次数，会耗费不少CPU时间，对于像手机设备资源有限的设备来说，这是相当大的一笔开销。Dalvik虚拟机基于寄存器架构。数据的访问通过寄存器间直接传递，这样的访问方式比基于栈方式要快很多。

## ART虚拟机与Dalvik虚拟机的区别

**预编译**

在dalvik中，应用启动的时候先将dex文件转换成机器码，结果就是启动时间有可能变慢，这就是Dalvik虚拟机的JIT(Just in Time)特性。

而在ART中，ART除了兼容了Dalvik虚拟机的特性之外，还有一个很好的特性AOT(Ahead of Time)，这个特性就是把dex文件转换成机器码这个步骤提前到了应用安装的时候，ART虚拟机将dex文件转换成可直接运行的oat文件，ART虚拟机天生支持多dex，所以也不会有一个合包的过程，因此会极大的提升APP冷启动速度。

**垃圾回收机制**

首先介绍下dalvik的GC的过程。主要有有四个过程：

1. 当gc被触发时候，其会去查找所有活动的对象，这个时候整个程序与虚拟机内部的所有线程就会挂起，这样目的是在较少的堆栈里找到所引用的对象；
   - 注意：这个回收动作和应用程序**非并发**；
2. gc对符合条件的对象进行标记；
3. gc对标记的对象进行回收；
4. 恢复所有线程的执行现场继续运行。

dalvik这么做的好处是，当pause了之后，GC势必是相当快速的。但是如果出现GC频繁并且内存吃紧势必会导致UI卡顿、掉帧、操作不流畅等。

后来ART改善了这种GC方式， 主要的改善点在将其非并发过程改成了部分并发，还有就是对内存的重新分配管理。

当ART GC发生时:

1. GC将会锁住Java堆，扫描并进行标记；
2. 标记完毕释放掉Java堆的锁，并且挂起所有线程；
3. GC对标记的对象进行回收；
4. 恢复所有线程的执行现场继续运行；
5. 重复2-4直到结束。

可以看出整个过程做到了部分并发使得时间缩短。据官方测试数据说GC效率提高2倍。

**提高内存使用，减少碎片化**

Dalvik内存管理特点是：内存碎片化严重，当然这也是Mark and Sweep算法带来的弊端。

可以看出每次GC后内存千疮百孔，本来连续分配的内存块变得碎片化严重，之后再分配进入的对象再进行内存寻址变得困难。

ART的解决：在ART中，它将Java分了一块空间命名为Large-Object-Space，这块内存空间的引入用来专门存放large object。同时ART又引入了moving collector的技术，即将不连续的物理内存块进行对齐。对齐了后内存碎片化就得到了很好的解决。Large-Object-Space的引入是因为moving collector对大块内存的位移时间成本太高。根官方统计，ART的内存利用率提高10倍了左右，大大提高了内存的利用率。

**64K问题**

见64K问题

## AndroidAPK编译打包流程

![32](/Users/mezzsy/知识点/img/32.png)

1. Java编译器对工程本身的java代码进行编译，这些java代码有三个来源：app的源代码，由资源文件生成的R文件(aapt工具)，以及有aidl文件生成的java接口文件(aidl工具)。产出为.class文件。
   - 用AAPT编译R.java文件
   - 编译AIDL的java文件
   - 把java文件编译成class文件

2. class文件和依赖的三方库文件通过dex工具生成Delvik虚拟机可执行的.dex文件，包含了所有的class信息，包括项目自身的class和依赖的class。产出为.dex文件。

3. apkbuilder工具将.dex文件和编译后的资源文件生成未经签名对齐的apk文件。这里编译后的资源文件包括两部分，一是由aapt编译产生的编译后的资源文件，二是依赖的三方库里的资源文件。产出为未经签名的.apk文件。

4. 分别由Jarsigner和zipalign对apk文件进行签名和对齐，生成最终的apk文件。

总结为：编译>DEX>打包>签名

## 64K问题

**Android 5.0 之前**，安卓系统是Dalvik虚拟机，在编译时Java源文件打包成dex文件，Dalvik虚拟机在执行dex文件的时候，使用short类型索引方法，short类型的范围是（-32,768~32,767），正好是64k，也就是说单个dex文件中方法做多只有65535个，随着项目的不断壮大，引用各种lib、以及项目本身java文件的增加，64k方法已经不能满足需要，因此会报64k问题。
**Android 5.0 之后**，安卓系统采用的是ART虚拟机，如果方法超过65535个，会自动分包，天然支持有多个dex文件，ART 在应用安装时执行预编译，将多个dex文件合并成一个oat文件执行。

# RecyclerView和ListView

## ListView的优化

主要分为三个方面：

-   采用ViewHolder并避免在getView中执行耗时操作
-   根据列表的滑动状态来控制任务的执行频率，比如当列表快速滑动时显然是不太适合开启大量的异步任务的
-   尝试开启硬件加速来使Listview的滑动更加流畅

大致使用

![34](/Users/mezzsy/知识点/img/34.jpg)

## RecyclerView

adapter的几个重要方法：

```java
//创建ViewHolder实例的，viewType由getItemViewType提供
public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent， int viewType) {}

public int getItemViewType(int position) {}

//对RecyclerView子项的数据进行赋值，每个子项在滚动到屏幕的时候会执行。
@Override
public void onBindViewHolder(RecyclerView.ViewHolder holder， int position) {}

//一共有多少子项
@Override
public int getItemCount() {}
```

## RecyclerView和ListView的区别

**相同点：**

1.  都可以通过ViewHolder来复用视图。

2.  都是以列表的方式展示大量相似布局的视图。

**不同点：**

1.  在ListView中，ViewHolder不是必须的。而在RecyclerView中ViewHolder变成了必须。
2.  Item 回收/复用方面：ListView是以convertView 作为回收单位，需要手动添加ViewHolder ，而RecyclerView则是以ViewHolder作为回收单位，convertView 被内置到了ViewHolder 中作为 ViewHolder 的成员变量。
3.  ListView只能在垂直方向上滚动。RecyclerView支持水平和竖直方向、交叉网格风格，支持网格展示，可以水平或者竖直滚动。
4.  RecyclerView.ItemAnimator则被提供item添加、删除或移动时的动画效果。

5.  在ListView中如果想要在item之间添加间隔符，只需要在布局文件中对ListView添加如下属性即可：

```xml
android:divider="@android:color/transparent"
android:dividerHeight="5dp"
```

RecyclerView需要通过ItemDecoration来进行。

## RecyclerView图片错乱问题

### 问题产生原因

根本原因：因为ViewHolder的重用机制，每一个item在移出屏幕后都会被重新使用以节省资源，避免滑动卡顿。

**场景A：**

1.  第一次进入页面，RecyclerView载入，不做任何触摸操作
2.  Adapter经过onCreateViewHolder创建当前显示给用户的N个ViewHolder对象，并且在onBindViewHolder时启动了N条线程加载图片
3.  N张图片全部加载完毕，并且显示到对应的ImageView上
4.  控制屏幕向下滑动，前K个item离开屏幕可视区域，后K个item进入屏幕可视区域
5.  前K个item被回收，重用到后K个item。后K个item显示的图片是前K个item的图片
6.  开启了K条线程，加载后K张图片。等待几秒，后K个item显示的图片突然变成了正确的图片

经过分析可以看出：如果当前网络速度很快，第6个步骤的加载速度在1秒甚至0.5秒内，就会造成人眼看到的图片闪烁问题，后K个item的图片闪了一下变成了正确的图片。

**场景B：**

1.  第一次进入页面，RecyclerView载入，不做任何触摸操作
2.  Adapter经过onCreateViewHolder创建当前显示给用户的N个ViewHolder对象，并且在onBindViewHolder时启动了N条线程加载图片
3.  结果N张图片全部加载完毕，并且显示到对应的ImageView上，但还有1张未加载完(假设是第一张图片未加载完)
4.  控制屏幕向下滑动，前K个item离开屏幕可视区域，后K个item进入屏幕可视区域
5.  前K个item被回收，重用到后K个item。场景A的问题不再说，后K张图片加载完毕(看上去一切正常)
6.  等待几秒，第一张图片终于加载完成，后K个item中的某一个突然从正确的图片(当前positon应该显示的图片)变成不正确的图片(第一个item的图片)

以上过程是场景B，问题出在加载第一张图片的线程T，持有了item1的ImageView对象引用，而这张图片加载速度非常慢，直到item1已经被重用到后面item后，过了一段时间，线程T才把图片一加载出来，并设置到item1的ImageView上，然而线程T并不知道item1已经不存在且已复用成其他item，于是，图片发生错乱了。

**场景C：**

1.  第一次进入页面，RecyclerView载入，不做任何触摸操作
2.  Adapter经过onCreateViewHolder创建当前显示给用户的N个ViewHolder对象，并且在onBindViewHolder时启动了N条线程加载图片
3.  忽略图片加载情况，直接向下滚动，再向上滚动，再向下滚动，来回操作
4.  由于离开了屏幕的item是随机被回收并重用的，所以向下滚动时我们假设item1、item3被回收重用到item9、item10，item2、item4被回收重用到item11、item12
5.  向上滚动时，item9、item12被回收重用到item1、item2，item10、item11被回收重用到item3、item4
6.  多次上下滚动后，停下，最后发现某一个item的图片在不停变化，最后还不一定是正确的图片

以上过程是场景C，问题出现在ViewHolder的回收重用顺序是随机的，回收时会从离开屏幕范围的item中随机回收，并分配给新的item，来回操作数次，就会造成有多条加载不同图片的线程，持有同一个item的ImageView对象，造成最后在同一个item上图片变来变去，错乱更加严重。

### 解决方案

**一、设置占位图**

Glide有两种方法设置占位图

1、直接在链式请求中加placeholder()：

```java
Glide.with(this)
        .load(picUrl)
        .placeholder(R.drawable.ic_loading)
        .into(holder.ivThumb)
```

2、添加监听，在回调方法中设置

```java
Glide.with(mContext)
     .load(picUrl)
     .error(R.drawable.ic_loading)
     .into(new SimpleTarget<GlideDrawable>() {
         @Override
         public void onResourceReady(GlideDrawable glideDrawable, GlideAnimation<? super  GlideDrawable> glideAnimation) {
                     holder.ivThumb.setImageDrawable(glideDrawable);
         }

         @Override
         public void onStart() {
             super.onStart();
             holder.ivThumb.setImageResource(R.drawable.ic_loading);
         }
     });
```

>   以上方法个人觉得不可行，设置占位图似乎不能解决错乱的问题，但这个方法依然保留。

**二、设置TAG**

使用`setTag`方式。但是，Glide图片加载也是使用这个方法，所以需要使用`setTag(key，value)`方式进行设置，取值`getTag(key)`，当异步请求回来的时候对比下tag是否一样，再判断是否显示图片，这里可以将position设置tag。

```java
@Override
public void onBindViewHolder(final VideoViewHolder holder, final int position) {
	holder.thumbView.setTag(R.id.tag_dynamic_list_thumb, position);
	Glide.with(mContext)
		.load(picUrl)
		.error(R.drawable.video_thumb_loading)
		.into(new SimpleTarget<GlideDrawable>() {
			@Override
			public void onResourceReady(GlideDrawable glideDrawable, GlideAnimation<? super GlideDrawable> glideAnimation {
				if (position != (Integer) holder.thumbView.getTag(R.id.tag_dynamic_list_thumb))
					return;
                
				holder.thumbView.setImageDrawable(glideDrawable);
			}

			@Override
            public void onStart() {
            	super.onStart();
           		holder.thumbView.setImageResource(R.drawable.ic_loading);
            }
		});
}
```

**三、在onViewRecycled方法中重置item的ImageView并取消网络请求**

流程：在onBindViewHolder中发起加载请求，然后在view被回收时取消网络请求
代码

```java
@Override
public void onBindViewHolder(VideoViewHolder holder, int position) {
    String istrurl = mImgList.get(position).getImageUrl();
    if (null == holder || null == istrurl || istrurl.equals("")) {
        return;
    }
    Glide.with(mContext)
            .load(picUrl)
            .placeholder(R.drawable.ic_loading)
            .into(holder.thumbView);
}

@Override
public void onViewRecycled(VideoViewHolder holder) {
    if (holder != null) {
        Glide.clear(holder.thumbView);
        holder.thumbView.setImageResource(R.drawable.ic_loading);
    }
    super.onViewRecycled(holder);
}
```

# 几个问题

## Android中的进程

### 前台进程

- 处于正在与用户交互的activity
- 与前台activity绑定的service
- 调用了startForeground（）方法的service
- 进程中包含正在执行onReceive（）方法的BroadcastReceiver。

系统中的前台进程并不会很多，而且一般前台进程都不会因为内存不足被杀死。特殊情况除外。当内存低到无法保证所有的前台进程同时运行时，才会选择杀死某个进程。

### 可视进程

- 为处于前台，但仍然可见的activity（例如：调用了onpause（）而还没调用onstop（）的activity）。典型情况是：运行activity时，弹出对话框（dialog等），此时的activity虽然不是前台activity，但是仍然可见。
- 可见activity绑定的service。（处于上诉情况下的activity所绑定的service）

可视进程一般也不会被系统杀死，除非为了保证前台进程的运行不得已而为之。

### 服务进程

- 已经启动的service

### 后台进程

- 不可见的activity（调用onstop（）之后的activity）

后台进程不会影响用户的体验，为了保证前台进程，可视进程，服务进程的运行，系统随时有可能杀死一个后台进程。当一个正确实现了生命周期的activity处于后台被杀死时，如果用户重新启动，会恢复之前的运行状态。

### 空进程

- 任何没有活动的进程

系统会杀死空进程，但这不会造成影响。空进程的存在无非为了一些缓存，以便于下次可以更快的启动。

## Android中的dp、px、dip、sp相关概念

- px：pixel，像素Android原生API，UI设计计量单位，如获取屏幕宽高。 
  屏幕分辨率：指在纵向和横向方向上的像素点数，单位是px，一般显示方式是纵向像素数量\*横向像素数量，如1920*1080。 
  屏幕尺寸：一般是屏幕对角线长度，单位是英寸，常见尺寸有3.5，4.0，4.3，4.7，5.0，6.0等。

- dpi屏幕像素密度：ppi pixel per inch的缩写，意思是每英寸屏幕上的像素数，因为屏幕尺寸是商家生产时就规定好的，屏幕尺寸一样的手机，屏幕宽高却不一定一样，所以通常取屏幕对角线像素数量和屏幕尺寸（屏幕对角线长度）来计算屏幕像素密度，**计算公式就是通过勾股定理和分辨率计算得到屏幕对角线像素数量，再除以屏幕尺寸**。

- dp /dip ：一个基于屏幕密度的抽象单位，如果一个160dpi的屏幕，1dp=1px
  公式：

$$
px = dp * (dpi / 160)
$$

- sp ：同dp相似，但还会根据用户的字体大小偏好来缩放(建议使用sp作为文本的单位，其它用dip)
- drawable-mdpi： 屏幕密度为160的手机设备（ Android规定此为baseline，其他均以此为基准，在此设备上，1dp = 1px）
  drawable-hdpi： 屏幕密度为240的手机设备 1dp=1.5px
  drawable-xhdpi： 屏幕密度为320的手机设备 1dp=2px
  drawable-xxhdpi：屏幕密度为480的手机设备 1dp=3px
  drawable-xxxhdpi：屏幕密度为640的手机设备 1dp=4px

## Android存储路径

以下内部存储为应用内部存储，外部存储为应用外部存储。

1. Environment.getDataDirectory() = /data 
   这个方法是获取内部存储的根路径 
2. getFilesDir().getAbsolutePath() = /data/user/0/packname/files 
   这个方法是获取某个应用在内部存储中的files路径 
3. getCacheDir().getAbsolutePath() = /data/user/0/packname/cache 
   这个方法是获取某个应用在内部存储中的cache路径 
4. getDir(“myFile”， MODE_PRIVATE).getAbsolutePath() = /data/user/0/packname/app_myFile 
   这个方法是获取某个应用在内部存储中的自定义路径 
   方法2，3，4的路径中都带有包名，说明他们是属于某个应用 
5. Environment.getExternalStorageDirectory().getAbsolutePath() = /storage/emulated/0 
   这个方法是获取外部存储的根路径 
6. Environment.getExternalStoragePublicDirectory(“”).getAbsolutePath() = /storage/emulated/0 
   这个方法是获取外部存储的根路径 
7. getExternalFilesDir(“”).getAbsolutePath() = /storage/emulated/0/Android/data/packname/files 
   这个方法是获取某个应用在外部存储中的files路径 
8. getExternalCacheDir().getAbsolutePath() = /storage/emulated/0/Android/data/packname/cache 
   这个方法是获取某个应用在外部存储中的cache路径 

## 如何避免 WebView 的内存泄露问题

1. 可以将 Webview 的 Activity 新起一个进程，结束的时候直接System.exit(0)；退出当前进程；
2. 不在xml中定义 WebView，而是在代码中创建，使用 getApplicationgContext() 作为传递的 Conetext；
3. 在 Activity 销毁的时候，将 WebView 置空

## onCreate方法里面有三行代码，第一行代码是打印a，第二行代码调用handler的post方法，在run方法里面打印b，第三行代码是打印c，请问abc的输出顺序是什么?

acb，activity的生命周期是由handler来处理的，handler的post方法将runnable放入MessageQueue中，按照先进先出原则，先执行onCreate方法，再执行run方法。

## Activity和Fragment的区别

1. 生命周期：
   Activity的生命周期：**onCreate**、**onStart**、**onResume**、**onPause**、**onStop**、**onDestroy**、**onRestart**。
   Fragment的生命周期：**onAttach**、**onCreate**、**onCreateView**、**onActivityCreated**、**onStart**、**onResume**、**onPause**、**onStop**、**onDestroyView**、**onDestroy**、**onDetach**。

2. 灵活性：
   Activity是四大组件之一，Fragment的显示要依赖于Activity。

   1）Fragment相比较与Activity来说更加灵活，可以在XML文件中直接进行写入，也可以在Activity中动态添加。

   2）可以使用show()/hide()或者replace()随时对Fragment进行切换，并且切换的时候不会出现明显的效果，用户体验会好；Activity虽然也可以进行切换，但是Activity之间切换会有明显的翻页或者其他的效果，在小部分内容的切换上给用户的感觉不是很好。

### 什么时候使用Activity，什么时候使用Fragment

看需求。

一般固定界面用Activity，如登录界面。

灵活的界面用Fragment，如新闻界面；另外在平板上，Fragment多一点。

## FragmentActivity和Activity的区别

fragment是3.0以后的东西，为了在低版本中使用fragment就要用到android-support-v4.jar兼容包，而fragmentActivity就是这个兼容包里面的，它提供了操作fragment的一些方法，其功能跟3.0及以后的版本的Activity的功能一样。

1. fragmentactivity继承自activity，用来解决android3.0之前没有fragment的api，所以在使用的时候需要导入support包，同时继承fragmentActivity，这样在activity中就能嵌入fragment来实现你想要的布局效果。 

2. 当然3.0之后你就可以直接继承自Activity，并且在其中嵌入使用fragment了。 

3. 获得Manager的方式也不同

   3.0以下：getSupportFragmentManager() 
   3.0以上：getFragmentManager()

## 如何保证Service不被杀死？如何保证进程不被杀死？

同时开启了两个进程和服务，我猜想它应该是相互监听，如果有一方被kill掉，另一个捕获到立即启动，以达到service永远都在运行的状态。

## **Activity之间的通信方式**

1. Intent
2. Broadcast

## **Fragment状态保存**

- fragment的状态保存和恢复

实际上，fragment的状态保存和恢复机制和activity是完全一致的。说明解决方案之前，我们首先应该弄清楚下边的几个问题：

1. 什么时候保存状态，什么时候恢复状态
2. 保存和恢复什么状态（fragment的状态还是view的状态？）
3. setRetainInstance(true)

- 什么时候保存状态，什么时候恢复状态？

当系统认为你的fragment存在被销毁的可能时（不包括用户主动退出fragment导致其被销毁，比如按BACK键后fragment被主动销毁）， onSaveInstanceState 就会被调用，给你一个机会来保存状态。以下几种情况可能导致fragment被异常销毁；

1. 按HOME键返回桌面时
2. 按菜单键回到系统后台，并选择了其他应用时
3. 按电源键时
4. 屏幕方向切换时

这四种情况中，前三种情况都是因为应用处于后台，根据Android系统的缓存机制，为了保持系统的流畅运行，处于后台的应用有很大的可能被清除，既然应用已经不在了，fragment自然也被销毁了；最后一种情况是由于屏幕方向切换导致配置改变，activity被销毁，fragment也随之被销毁了。 

在这些情况下，我们就可以通过 onSaveInstanceState 方法将数据保存到它的参数bundle对象中了。以上触发onSaveInstanceState 的状况和activity完全一致。 

有了保存，就应该有恢复。和activity不同的是，fragment没有onRestoreInstanceState方法，但是我们可以**在onActivityCreated中恢复数据**，它的参数中的bundle对象包含了在异常销毁前保存的数据。

参考：https://blog.csdn.net/zephyr_g/article/details/53516568

## **startActivityForResult是哪个类的方法，在什么情况下使用？**

Activity。

## **fragment之间传递数据的方式？**

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

## **AlertDialog，popupWindow，Activity区别**

- AlertDialog：用来提示用户一些信息，用起来也比较简单，设置标题内容和按钮即可，如果是加载的自定义的view ，调用 dialog.setView(layout)；加载布局即可(其他的设置标题内容这些就不需要了)
- popupWindow：就是一个悬浮在Activity之上的窗口，可以用展示任意布局文件
- activity：Activity是Android系统中的四大组件之一，可以用于显示View。Activity是一个与用记交互的系统模块，几乎所有的Activity都是和用户进行交互的

区别：

AlertDialog是非阻塞式对话框：AlertDialog弹出时，后台还可以做事情；

而PopupWindow是阻塞式对话框：PopupWindow弹出时，程序会等待，在PopupWindow退出前，程序一直等待，只有当我们调用了dismiss方法的后，PopupWindow退出，程序才会向下执行。

在此状态下的生命周期不会发生变化。

## Application 和 Activity 的 Context 对象的区别

在需要传递Context参数的时候，如果是在Activity中，我们可以传递this（这里的this指的是Activity.this，是当前Activity的上下文）或者Activity.this。这个时候如果我们传入getApplicationContext()，我们会发现这样也是可以用的。可是大家有没有想过传入Activity.this和传入getApplicationContext()的区别呢？首先Activity.this和getApplicationContext()返回的不是同一个对象，一个是当前Activity的实例，一个是项目的Application的实例，这两者的生命周期是不同的，它们各自的使用场景不同，this.getApplicationContext()取的是这个应用程序的Context，它的生命周期伴随应用程序的存在而存在；而Activity.this取的是当前Activity的Context，它的生命周期则只能存活于当前Activity，这两者的生命周期是不同的。getApplicationContext() 生命周期是整个应用，当应用程序摧毁的时候，它才会摧毁；Activity.this的context是属于当前Activity的，当前Activity摧毁的时候，它就摧毁。

![1044471-20170624233207429-120613450](http://111.230.96.19:8081/image/1044471-20170624233207429-120613450.png)

我们就只看Activity和Application，可以看到前三个操作不在Application中出现，也就是Show a Dialog、Start an Activity和Layout Inflation。开发的过程中，我们主要记住一点，凡是跟UI相关的，都用Activity做为Context来处理。

## **谈谈对接口与回调的理解**

回调是在某个事件发生时应该采取的动作。

可以把使用**实现了某一接口的类**创建的对象的引用，赋给该接口声明的**接口变量**，那么该接口变量就可以**调用被类实现的接口的方法**。实际上，当接口变量调用被类实现的接口中的方法时，就是**通知相应的对象调用接口的方法**，这一过程称为对象功能的接口回调。

## **Android中数据存储方式**

1 使用SharedPreferences存储数据：键值对保存数据。

2 文件存储数据：适用于存储一些简单的文本数据或者二进制数据。

3 SQLite数据库存储数据：存储大量复杂的关系型数据。

4 使用ContentProvider存储数据；

5 网络存储数据；

## SharedPreferences的apply和commit的区别

这两个方法的区别在于： 
1. apply没有返回值，而commit返回boolean表明修改是否提交成功 
2. apply是将修改数据原子提交到内存, 而后异步真正提交到硬件磁盘，而commit是同步的提交到硬件磁盘，因此，在多个并发的提交commit的时候，他们会等待正在处理的commit保存到磁盘后在操作，从而降低了效率。而apply只是原子的提交到内容，后面有调用apply的函数的将会直接覆盖前面的内存数据，这样从一定程度上提高了很多效率。 
3. apply方法不会提示任何失败的提示。 
由于在一个进程中，sharedPreference是单实例，一般不会出现并发冲突，如果对提交的结果不关心的话，建议使用apply，当然需要确保提交成功且有后续操作的话，还是需要用commit的。

## Json解析方式

比起XML，Json体积更小，在网络上传输的时候可以更省流量。

**JsonObject**

JSONArray获取数组，JSONObject获取Json对象。

JSONObject和JsonObject的区别：

1. JSONObject是Android原生的json类，通过import org.json.JSONObject来导入。 
   JsonObject需要添加gson jar包，通过com.google.gson.JsonObject来导入。
2. JSONObject通过HashMap来保存键值对。 
   JsonObject使用LinkedTreeMap来保存键值对。
3. JSONObject：添加value为null的键值对，Map保存的时候会删掉这一键值对； 
   JsonObject：添加value为null的键值对，Map会保留value值是null的键值对。

**GSON** 

