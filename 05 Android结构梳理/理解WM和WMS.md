# Window、WindowManager和WMS

Window是一个抽象类，具体的实现类为PhoneWindow，它对View进行管理。
WindowManager是个接口类，继承自接口ViewManager，是用来管理Window的，实现类为WindowManagerlmpl。如果要对Window(View)进行添加、更新和删除操作就可以使用WindowManager。
WindowManager会将具体的工作交由WMS来处理，WindowManager和WMS通过Binder来进行跨进程通信。

<img src="assets/284.jpg" alt="284" style="zoom:50%;" />

Window包含了View并对View进行管理，Window用虚线来表示是因为Window是一个抽象概念，用来描述一个窗口，并不是真实存在的，Window的实体其实也是View。

WindowManager用来管理Window，而WindowManager所提供的功能最终会由WMS进行
处理。

# WindowManager的关联类

WindowManager是一个接口类，继承自接口ViewManager，ViewManager中定义了3个方法，分别用来添加、更新和删除View：

```java
public interface ViewManager{
    public void addView(View view, ViewGroup.LayoutParams params);
    public void updateViewLayout(View view, ViewGroup.LayoutParams params);
    public void removeView(View view);
}
```

WindowManager也继承了这些方法，而这些方法传入的参数都是View 类型，说明Window是以View的形式存在的。

WindowManager在继承VewManager的同时，又加入了很多功能，包括Window的类型和层级相关的常量、内部类以及些方法， 其中有两个方法是根据Window的特性加入的：

```java
public Display getDefaultDisplay(); 
public void removeViewImmediate(View view);
```

getDefaultDisplay方法能够得知这个WindowManager实例将Window添加到哪个屏幕上了，换句话说，就是得到WindowManager所管理的屏幕(Display)。

removeViewImmediate方法则规定在这个方法返回前要立即执行View.onDetachedFromWindow方法，来完成传入的View相关的销毁工作。

Window是一个抽象类 ，它的具体实现类为PhoneWindow，PhoneWindow是何时创建
的呢？
在Activity启动过程中会调用ActivityThread的performLaunchActivity方法，performLaunchActivity方法中又会调用Activity的attach方法，PhoneWindow就是在Activity的attach方法中创建的。

```java
final void attach(Context context, ActivityThread aThread, Instrumentation instr, IBinder token, int ident, Application application, Intent intent, ActivityInfo info, CharSequence title, Activity parent, String id, NonConfigurationInstances lastNonConfigurationInstances, Configuration config, String referrer, IVoiceInteractor voiceInteractor, Window window, ActivityConfigCallback activityConfigCallback) {
    //...
    mWindow = new PhoneWindow(this, window, activityConfigCallback);
    //...
    mWindow.setWindowManager((WindowManager)context.getSystemService(Context.WINDOW_SERVICE), mToken, mComponent.flattenToString(), (info.flags & ActivityInfo.FLAG_HARDWARE_ACCELERATED) != 0);
    //...
}
```

这里创建了一个PhoneWindow ，并调用setWindowManager方法设置一个Manager，这个方法在PhoneWindow的父类Window中实现。

```java
public void setWindowManager(WindowManager wm, IBinder appToken, String appName, boolean hardwareAccelerated) {
    mAppToken = appToken;
    mAppName = appName;
    mHardwareAccelerated = hardwareAccelerated || SystemProperties.getBoolean(PROPERTY_HARDWARE_UI, false);
    if (wm == null) {
        wm = (WindowManager)mContext.getSystemService(Context.WINDOW_SERVICE);
    }
    mWindowManager = ((WindowManagerImpl)wm).createLocalWindowManager(this);
}
```

这里获取WindowManager的方式利用getSystemService方法并传入名称Context.WINDOW_SERVICE来进行获取的。
其中具体的逻辑分析略过，这里会获取一个WindowManagerImpl实例，是WindowManager的具体实现。

setWindowManager方法会调用createLocalWindowManager方法，createLocalWindowManager同样也是创建WindowManagerImpl，不同的是这次创建
WindowManagerlmpl时将创建它的Window作为参数传了进来，这WindowManagerImpl
就持有了Window的引用，可以对Window进行操作。如addView方法：

```java
public void addView(@NonNull View view, @NonNull ViewGroup.LayoutParams params) {
    applyDefaultToken(params);
    mGlobal.addView(view, params, mContext.getDisplay(), mParentWindow);
}
```

调用了WindowManagerGlobal的addView 方法，其中最后一个参数mParentWindow就是上面提到的Window，可以看出WindowManagerlmpl虽然是WindowManager的实现类，但是没有实现什么功能，而是将功能实现委托给了WindowManagerGlobal，这里用到的是桥接模式。

```java
public final class WindowManagerImpl implements WindowManager {
    private final WindowManagerGlobal mGlobal = WindowManagerGlobal.getInstance();//注释1
    private final Context mContext;
    private final Window mParentWindow;//注释2
		//...
    private WindowManagerImpl(Context context, Window parentWindow) {
        mContext = context;
        mParentWindow = parentWindow;//注释3
    }
  	//...
}
```

注释1处可以看出WindowManagerGlobal 是一个单例，说明在一个进程中只有一个WindowManagerGlobal实例。
注释2处的代码结合注释3处的代码说明这个WindowManagerlmpl实例会作为哪个Window 的子Window，这也就说明在一个进程中WindowManagerlmpl可能会有多个实例。

WindowManager的关联类如图所示：

<img src="assets/285.jpg" alt="285" style="zoom:50%;" />

# Window的属性

## Window的类型和显示次序

Window的类型有很多种，比如应用程序窗口、系统错误窗口、输入法窗口、PopupWindow、Toast、Dialog等。总的来说Window分为三大类型，分别是：

- Application Window(应用程序窗口)
- Sub Window(子窗口)
- System Window(系统窗口)

每个大类型中又包含了很多种类型，它们都定义在WindowManager的静态内部类LayoutParams 中。

### 应用程序窗口

Activity就是一个典型的应用程序窗口，应用程序窗口包含的类型如下所示：

```java
public interface WindowManager extends ViewManager {
  	//...

    public static class LayoutParams extends ViewGroup.LayoutParams implements Parcelable {
				public static final int FIRST_APPLICATION_WINDOW = 1;//表示应用程序窗口类型初始值
				public static final int TYPE_BASE_APPLICATION = 1;//窗口的基础值，其他的窗口值要大于这个值
      	public static final int TYPE_APPLICATION = 2;//普通的应用程序窗口类型
      	public static final int TYPE_APPLICATION_STARTING = 3;//应用程序启动窗口类型，用于系统在应用程序窗口启动前显示的窗口
      	public static final int LAST_APPLICATION_WINDOW = 99;//表示应用程序窗口类型结束值，也就是说应用程序窗口的Type值范围为1~99
      	
      	//...
    }
}
```

还有一些数值未列出，这些数值的大小涉及窗口的层级。

### 子窗口

子窗口，它不能独立存在，需要附着在其他窗口才可以，PopupWindow就属于子窗口。
子窗口的类型定义如下所示：

```java
public static final int FIRST_SUB_WINDOW = 1000;
public static final int TYPE_APPLICATION_PANEL = FIRST_SUB_WINDOW;
public static final int TYPE_APPLICATION_MEDIA = FIRST_SUB_WINDOW + 1;
public static final int TYPE_APPLICATION_SUB_PANEL = FIRST_SUB_WINDOW + 2;
public static final int TYPE_APPLICATION_ATTACHED_DIALOG = FIRST_SUB_WINDOW + 3;
public static final int TYPE_APPLICATION_MEDIA_OVERLAY  = FIRST_SUB_WINDOW + 4;
public static final int TYPE_APPLICATION_ABOVE_SUB_PANEL = FIRST_SUB_WINDOW + 5;
public static final int LAST_SUB_WINDOW = 1999;
```

子窗口的Type值范围为1000 ~ 1999。

### 系统窗口

Toast、输入法窗口、系统音量条窗口、系统错误窗口都属于系统窗口。系统窗口的类型定义如下所示：

```java
public static final int FIRST_SYSTEM_WINDOW     = 2000;

public static final int TYPE_STATUS_BAR         = FIRST_SYSTEM_WINDOW;

public static final int TYPE_SEARCH_BAR         = FIRST_SYSTEM_WINDOW+1;

@Deprecated
public static final int TYPE_PHONE              = FIRST_SYSTEM_WINDOW+2;

@Deprecated
public static final int TYPE_SYSTEM_ALERT       = FIRST_SYSTEM_WINDOW+3;

public static final int TYPE_KEYGUARD           = FIRST_SYSTEM_WINDOW+4;

@Deprecated
public static final int TYPE_TOAST              = FIRST_SYSTEM_WINDOW+5;
//...
public static final int LAST_SYSTEM_WINDOW      = 2999;
```

这里只列出了一小部分，系统窗口的Type值范围为2000~ 2999。

### 窗口显示次序

当一个进程向WMS申请一个窗口时，WMS会为窗口确定显示次序。为了方便窗口显示次序的管理，手机屏幕可以虚拟地用X、Y、Z轴来表示，其中Z轴垂直于屏幕，从屏幕内指向屏幕外，这样确定窗口显示次序也就是确定窗口在Z轴上的次序，这个次序称为Z-Oder。

Type值是Z-Oder排序的依据，应用程序窗口的Type值范围为1~ 99，子窗口1000~1999，系统窗口2000~2999，在一般情况下，Type值越大则Z-Oder排序越靠前，就越靠近用户。

这只是基本规则，实际的逻辑复杂的多，这里不再讨论。

## Window 的标志

Window的Flag用于控制Window的显示，同样被定义在WindowManager的内部类LayoutParms中，一共有20多个，这里给出几个比较常用的：

| Flag                            | 描述                                                         |
| ------------------------------- | ------------------------------------------------------------ |
| FLAG_ALLOW_LOCK_WHILE_SCREEN_ON | 只要窗口可见，就允许在开启状态的屏幕上锁屏                   |
| FLAG_NOT_FOCUSABLE              | 窗口不能获得输入焦点，设置该标志的同时，FLAG_NOT_TOUCH_MODAL也会被设置 |
| FLAG_NOT_TOUCHABLE              | 窗口不接收任何触摸事件                                       |
| FLAG_NOT_TOUCH_MODAL            | 将该窗口区城外的触摸事件传递给其他的Window，而自己只会处理窗口区域内的触摸事件 |
| FLAG_KEEP_SCREEN_ON             | 只要窗口可见，屏幕就会一直亮着                               |
| FLAG_LAYOUT_NO_LIMITS           | 允许窗口超过屏幕之外                                         |
| FLAG_FULLSCREEN                 | 隐藏所有的屏称装饰窗口，比如在游戏、播放器中的全屏显示       |
| FLAG_SHOW_WHEN_LOCKED           | 窗口可以在锁屏的窗口之上显示                                 |
| FLAG_IGNORE_CHEEK_PRESSES       | 当用户的脸贴近屏幕时(比如打电话)， 不会去响应此事件          |
| FLAG_TURN_SCREEN_ON             | 窗口显示时将屏幕点亮                                         |

设置Window的Flag有3种方法，第一种是通过Window的addFlags方法：

```java
public void addFlags(int flags) {
    setFlags(flags, flags);
}
```

第二种通过Window的setFlags方法：

```java
public void setFlags(int flags, int mask) {
    final WindowManager.LayoutParams attrs = getAttributes();
    attrs.flags = (attrs.flags&~mask) | (flags&mask);
    mForcedWindowFlags |= mask;
    dispatchWindowAttributesChanged(attrs);
}
```

第三种则是给LayoutParams设置Flag，并通过WindowManager的addView方法进行添加。



WindowManager .LayoutParams mWindowLayoutParams
new WindowManager . LayoutParams() ;
mWindowLayoutParams. flags=WindowManager . LayoutParams . FLAG FULLSCREEN ;
WindowManager mWindowManager = (WindowManager) getSystemService (Context .
WINDOW SERVICE);
TextView mTextView=new TextView (this) ;
mIWi ndowManager . addView (mTextView, mWindowLayoutParams) ;
195



## 软键盘相关模式

窗口和窗口的叠加是十分常见的场景，但如果其中的窗口是软键盘窗口，可能就会出现些问题，比如典型的用户登录界面，默认的情况弹出的软键盘窗口可能会盖住输入框下方的按钮，这样用户体验会非常糟糕。为了使得软键盘窗口能够按照期望来显示，WindowManager的静态内部类LayouParamns中定义了软键盘相关模式，这里给出常用的几个：

| SoftInputMode                  | 描述                                                       |
| ------------------------------ | ---------------------------------------------------------- |
| SOFT_INPUT_STATE_UNSPECIFIED   | 没有指定状态，系统会选择一个合适的状态或依赖于主题的设置   |
| SOFT_INPUT_STATE_UNCHANGED     | 不会改变软键盘状态                                         |
| SOFT_INPUT_STATE_HIDDEN        | 当用户进入该窗口时，软键盘默认隐藏                         |
| SOFT_INPUT_STATE_ALWAYS_HIDDEN | 当窗口获取焦点时，软键盘总是被隐藏                         |
| SOFT_INPUT_ADJUST_RESIZE       | 当软键盘弹出时，窗口会调整大小                             |
| SOFT_INPUT_ADJUST_PAN          | 当软键盘弹出时，窗口不需要调整大小，要确保输入焦点是可见的 |

上面的与AndroidManifest中Activity的属性android:windowSoftInputMode是对应的。因此，除了在AndroidMainfest中为Activity设置android:windowSoftInputMode以外还可以在Java代码中为Window设置SoftInputMode：

```java
getWindow().setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE);
```

# Window的操作

对于Window 的操作，最终都是交由WMS来进行处理的。窗口的操作分为两大部分，一部分是WindowManager处理部分，另一部分是WMS处理部分。
Window分为三大类，分别是Aplication Window(应用程序窗口)、Sub Window(子窗口)和System Window(系统窗口)，对于不同类型的窗口添加过程会有所不同，但是对于WMS处理部分，添加的过程基本上是一样的， WMS对于这三大类的窗口基本是一视同仁的。

这里先分析WindowManager的操作。

## 系统窗口的添加过程

这里主要讲解系统窗口的添加过程。系统窗口的添加过程也会根据不同的系统窗口有所区别，这里以系统窗口StatusBar为例，StatusBar是SystemUI的重要组成部分，具体就是指系统状态栏，用于显示时间、电量和信号等信息。

来看一下StatusBar的addStatusBarWindow方法，这个方法负责为StatusBar添加Window：

```java
private void addStatusBarWindow() {
    makeStatusBarView();//注释1
    mStatusBarWindowManager = Dependency.get(StatusBarWindowManager.class);
    mRemoteInputController = new RemoteInputController(mHeadsUpManager);
    mStatusBarWindowManager.add(mStatusBarWindow, getStatusBarHeight());//注释2
}
```

在注释1处用于构建StatusBa 的视图。
在注释2处调用了StatusBarWindowManager的add方法，并将StatusBar的视图(StatusBarWindowView)和StatusBar的高度传进去，StatusBarWindowManager的add方法如下所示：

```java
public void add(View statusBarView, int barHeight) {
    mLp = new WindowManager.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,
            barHeight,
            WindowManager.LayoutParams.TYPE_STATUS_BAR,//注释1
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
                    | WindowManager.LayoutParams.FLAG_TOUCHABLE_WHEN_WAKING
                    | WindowManager.LayoutParams.FLAG_SPLIT_TOUCH
                    | WindowManager.LayoutParams.FLAG_WATCH_OUTSIDE_TOUCH
                    | WindowManager.LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS,
            PixelFormat.TRANSLUCENT);
    mLp.token = new Binder();
    mLp.flags |= WindowManager.LayoutParams.FLAG_HARDWARE_ACCELERATED;
    mLp.gravity = Gravity.TOP;
    mLp.softInputMode = WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE;
    mLp.setTitle("StatusBar");
    mLp.packageName = mContext.getPackageName();
    mStatusBarView = statusBarView;
    mBarHeight = barHeight;
    mWindowManager.addView(mStatusBarView, mLp);//注释2
    mLpChanged = new WindowManager.LayoutParams();
    mLpChanged.copyFrom(mLp);
}
```

首先通过创建LayoutParams来配置StatusBar视图的属性。在注释1处，设置了TYPE_STATUS_BAR，表示StatusBar视图的窗口类型是状态栏。
在注释2处调用了WindowManager的addView方法，addView方法定义在WindowManager的父类接口ViewManager中，而addView方法则是在
WindowManagerImpl中实现的：

```java
public void addView(@NonNull View view, @NonNull ViewGroup.LayoutParams params) {
    applyDefaultToken(params);
    mGlobal.addView(view, params, mContext.getDisplay(), mParentWindow);
}
```

addView方法的第一个参数的类型为View，说明窗口也是以View的形式存在的。
addView方法中会调用WindowManagerGlobal的addView方法：

```java
public void addView(View view, ViewGroup.LayoutParams params,
        Display display, Window parentWindow) {
    //...
    final WindowManager.LayoutParams wparams = (WindowManager.LayoutParams) params;
    if (parentWindow != null) {
        parentWindow.adjustLayoutParamsForSubWindow(wparams);//如果当前窗口要作为子窗口，就会根据父窗口对子窗口的WindowManager.LayoutParams类型的wparams对象进行相应调整
    } else {
        final Context context = view.getContext();
        if (context != null && (context.getApplicationInfo().flags & ApplicationInfo.FLAG_HARDWARE_ACCELERATED) != 0) {
            wparams.flags |= WindowManager.LayoutParams.FLAG_HARDWARE_ACCELERATED;
        }
    }

    ViewRootImpl root;
    View panelParentView = null;

    synchronized (mLock) {
        //...
        root = new ViewRootImpl(view.getContext(), display);//创建了ViewRootlmp并赋值给root

        view.setLayoutParams(wparams);

        mViews.add(view);//将添加的View保存到View列表中。
        mRoots.add(root);//将root存入到ViewRootImpl列表中。
        mParams.add(wparams);//将窗口的参数保存到布局参数列表中

        try {
            root.setView(view, wparams, panelParentView);//将窗口和窗口的参数通过setView方法设置到ViewRootImpl中
        } catch (RuntimeException e) {
            if (index >= 0) {
                removeViewLocked(index, true);
            }
            throw e;
        }
    }
}
```

在介绍addView方法前首先要了解WindowManagerGlobal中维护的和Window操作相关的3个列表，在窗口的添加、更新和删除过程中都会涉及这3个列表，它们分别是View列表 `ArrayList<View> mViews`、 布局参数列表 `ArrayList<WindowManager.LayouParamns> mParms`和ViewRootImpl列表 `ArrayList<VievRootlmpl> mRoots`。

了解了这3个列表后，接着分析addView方法。
ViewRootImpl身负了很多职责，主要有以下几点：

- View树的根并管理View树。
- 触发View的测量、布局和绘制。
- 输入事件的中转站。
- 管理Surface。
- 负责与WMS进行进程间通信。

接着来查看ViewRootImpl的setView方法：

```java
public void setView(View view, WindowManager.LayoutParams attrs, View panelParentView) {
    synchronized (this) {
        //...
            try {
                mOrigWindowType = mWindowAttributes.type;
                mAttachInfo.mRecomputeGlobalAttributes = true;
                collectViewAttributes();
                res = mWindowSession.addToDisplay(mWindow, mSeq, mWindowAttributes, getHostVisibility(), mDisplay.getDisplayId(), mAttachInfo.mContentInsets, mAttachInfo.mStableInsets, mAttachInfo.mOutsets, mInputChannel);
            } 
      	//....
}
```

在setView方法主要就是调用了mWindowSession的addToDisplay方法，mWindowSession是IWindowSession类型的，它是一个Binder 对象，用于进行进程间通信，IWindowSession是Client端的代理，它的Server端的实现为Session，此前的代码逻辑都是运行在本地进程的，而Session的addToDisplay方法则运行在WMS所在的进程(SystemServer 进程)中。

本地进程的ViewRootImpl要想和WMS进行通信需要经过Session，那么Session为何包含在WMS中呢？

看一下Session的addToDisplay方法：

```java
public int addToDisplay(IWindow window, int seq, WindowManager.LayoutParams attrs, int viewVisibility, int displayId, Rect outContentInsets, Rect outStableInsets, Rect outOutsets, InputChannel outInputChannel) {
    return mService.addWindow(this, window, seq, attrs, viewVisibility, displayId, outContentInsets, outStableInsets, outOutsets, outInputChannel);
}
```

在addToDisplay方法中调用了WMS的addWindow方法，并将自身也就是Session作为参数传了进去，每个应用程序进程都会对应一个 Session，WMS会用ArrayList来保存这此Session。

剩下的工作就交给WMS来处理，在WMS中会为这个添加的窗口分配Surface，并确定窗口显示次序，可见负责显示界面的是画布Surface，而不是窗口本身。WMS会将它所管理的Surface交由SurfaceFlinger处理，SurfaceFlinger会将这些Surface混合并绘制到屏幕上。

## Activity的添加过程

无论是哪种窗口，它的添加过程在WMS处理部分中基本是类似的，只不过会在权限和窗口显示次序等方面会有些不同，但是在WindowManager处理部分会有所不同。

这里以最典型的应用程序窗口Activity为例，Activity在启动过程中，如果Activity所在的进程不存在则会创建新的进程，创建新的进程之后就会运行代表主线程的实例ActivityThread，ActivityThread管理着当前应用程序进程的线程，这在Activity的启动过程中运用得很明显，当界面要与用户进行交互时，会调用ActivityThread的handleResumeActivity方法：

```java
final void handleResumeActivity(IBinder token, boolean clearHide, boolean isForward, boolean reallyResume, int seq, String reason) {
    //...
    r = performResumeActivity(token, clearHide, reason);//performResumeActivity方法最终会调用Activity的onResume方法
		//...
        if (r.window == null && !a.mFinished && willBeVisible) {
            r.window = r.activity.getWindow();
            View decor = r.window.getDecorView();
            decor.setVisibility(View.INVISIBLE);
            ViewManager wm = a.getWindowManager();//得到ViewManager类型的wm对象
            WindowManager.LayoutParams l = r.window.getAttributes();
            a.mDecor = decor;
            l.type = WindowManager.LayoutParams.TYPE_BASE_APPLICATION;
            l.softInputMode |= forwardBit;
            if (r.mPreserveWindow) {
                a.mWindowAdded = true;
                r.mPreserveWindow = false;
                ViewRootImpl impl = decor.getViewRootImpl();
                if (impl != null) {
                    impl.notifyChildRebuilt();
                }
            }
            if (a.mVisibleFromClient) {
                if (!a.mWindowAdded) {
                    a.mWindowAdded = true;
                    wm.addView(decor, l);//注释3
                } else {
                    a.onWindowAttributesChanged(l);
                }
            }
			//...
}
```

在注释3处调用了ViewManager的addView方法，而addView方法则是在WindowManagerlmpl中实现的，此后的过程在上面的系统窗口StatusBar的添加过程中已经讲过，唯一需要注意的是ViewManager的addView方法的第一个参数为DecorView，这说明Acitivty窗口中会包含DecorView。

## Window的更新过程

Window的更新过程和Window的添加过程是类似的。需要调用ViewManager的updateViewLayout方法，updateViewLayout方法在WindowManagerlmpl中实现WindowManagerImpl的updateViewLayout方法会调用WindowManagerGlobal的updateViewLayout方法，如下所示：

```java
public void updateViewLayout(@NonNull View view, @NonNull ViewGroup.LayoutParams params) {
    applyDefaultToken(params);
    mGlobal.updateViewLayout(view, params);
}
```

```java
public void updateViewLayout(View view, ViewGroup.LayoutParams params) {
    //...

    final WindowManager.LayoutParams wparams = (WindowManager.LayoutParams)params;
    view.setLayoutParams(wparams);//注释1
    synchronized (mLock) {
        int index = findViewLocked(view, true);//注释2
        ViewRootImpl root = mRoots.get(index);//注释3
        mParams.remove(index);//注释4
        mParams.add(index, wparams);//注释5
        root.setLayoutParams(wparams, false);//注释6
    }
}
```

注释1处将更新的参数设置到View中。
注释2处得到要更新的窗口在View列表中的索引。
注释3处在ViewRootImpl列表中根据索引得到窗口的ViewRootImpl。
注释4和注释5处用于更新布局参数列表。
注释6处调用ViewRootImpl的setLayoutParams方法将更新的参数设置到ViewRootImpl 中。

ViewRootImpl的setLayoutParams方法在最后会调用ViewRootImpl的scheduleTraversals方法，如下所示：

```java
void scheduleTraversals() {
    if (!mTraversalScheduled) {
        mTraversalScheduled = true;
        mTraversalBarrier = mHandler.getLooper().getQueue().postSyncBarrier();
        mChoreographer.postCallback(Choreographer.CALLBACK_TRAVERSAL, mTraversalRunnable, null);//注释1
        if (!mUnbufferedInputDispatch) {
            scheduleConsumeBatchedInput();
        }
        notifyRendererOfFramePending();
        pokeDrawLockIfNeeded();
    }
}
```

注释1处的Choreographer译为“舞蹈指导”，用于接收显示系统的VSync信号，在下一个帧渲染时控制执行一些操作。

Choreographer的postCallback方法用于发起添加回调，这个添加的回调将在下一帧被渲染时执行。这个添加的回调指的是注释1处的TraversalRunnable类型的mTraversalRunnable，如下所示：

```java
final class TraversalRunnable implements Runnable {
    @Override
    public void run() {
        doTraversal();
    }
}
```

在TraversalRunnable的run方法中调用了doTraversal方法，如下所示：

```java
void doTraversal() {
    if (mTraversalScheduled) {
        mTraversalScheduled = false;
        mHandler.getLooper().getQueue().removeSyncBarrier(mTraversalBarrier);

        if (mProfile) {
            Debug.startMethodTracing("ViewAncestor");
        }

        performTraversals();

        if (mProfile) {
            Debug.stopMethodTracing();
            mProfile = false;
        }
    }
}
```

在doTraversal方法中又调用了performTraversals方法，performTraversals方法使得ViewTree开始View的工作流程，如下所示：

```java
private void performTraversals() {
		//...
    relayoutResult = relayoutWindow(params, viewVisibility, insetsPending);//注释1
		//。。。

    if (!mStopped || mReportNextDraw) {
      	//。。
        int childWidthMeasureSpec = getRootMeasureSpec(mWidth, lp.width);
        int childHeightMeasureSpec = getRootMeasureSpec(mHeight, lp.height);
        performMeasure(childWidthMeasureSpec, childHeightMeasureSpec);//注释2
    }

    if (didLayout) {
      	//。。。
        performLayout(lp, mWidth, mHeight);//注释3
    }

    if (!cancelDraw && !newSurface) {
      	//。。。
        performDraw();//注释4
    }
}
```

注释1处的relayoutWindow方法内部会调用IWindowSession的relayout方法来更新Window视图，最终会调用WMS的relayoutWindow方法。

除此之外，performTraversals方法还会在注释2、3、4处分别调用performMeasure、performLayout和performDraw方法，这样就完成了View 的工作流程。在performTraversals方法中更新了Window视图，又执行Window中的View的工作流程，这样就完成了Window的更新。

# 理解WMS

## WMS的职责

1. **窗口管理**
	WMS是窗口的管理者，它负责窗口的启动、添加和删除，另外窗口的大小和层级也是由WMS进行管理的。窗口管理的核心成员有DisplayContent、WindowToken和WindowState。

2. **窗口动画**
	窗口间进行切换时，使用窗口动画可以显得更炫一些，窗口动画由WMS的动画子系统来负责，动画子系统的管理者为WindowAnimator。
3. **输入系统的中转站**
	通过对窗口的触摸从而产生触摸事件，InputManagerService(IMS)会对触摸事件进行处理，它会寻找一个最合适的窗口来处理触摸反馈信息，WMS是窗口的管理者，用它作为输入系统的中转站。

4. **Surface管理**
窗口并不具备绘制的功能，因此每个窗口都需要有块Surface来供自己绘制，为每个窗口分配Surface是由WMS来完成的。

## WMS的创建过程

WMS是在SystemServer进程中创建的：

```java
public static void main(String[] args) {
    new SystemServer().run();
}
```

```java
private void run() {
    try {
        //创建消息Looper
        Looper.prepareMainLooper();

        //加载了动态库libandroid_servers.so
        System.loadLibrary("android_servers");
        performPendingShutdown();
        //创建系统的Context
        createSystemContext();
        //创建SystemServiceManager，它会对系统的服务进行创建、启动和生命周期管理
        mSystemServiceManager = new SystemServiceManager(mSystemContext);
        mSystemServiceManager.setRuntimeRestarted(mRuntimeRestart);
        LocalServices.addService(SystemServiceManager.class, mSystemServiceManager);
        SystemServerInitThreadPool.get();
    } finally {
        traceEnd();
    }

    // Start services.
    try {
        traceBeginAndSlog("StartServices");
      	//启动引导服务
        startBootstrapServices();
      	//启动核心服务
        startCoreServices();
      	//启动其他服务
        startOtherServices();
        SystemServerInitThreadPool.shutdown();
    } catch (Throwable ex) {
        //。。。
    } finally {
        traceEnd();
    }
		//。。。
    Looper.loop();
    throw new RuntimeException("Main thread loop unexpectedly exited");
}
```

在startBootstrapServices方法中用SystermServiceManager启动了ActivityManagerService、PowerManagerService、PackageManagerService等服务。
在startCoreServices方法中启动了DropBoxManagerService、BatteryService、UsageStatsService和WebViewUpdateService。
在startOtherServices方法中启动了CameraService、AlarmManagerService、VrManagerService等服务。

这些服务的父类均为SystemService。可以看出官方把系统服务分为了三种类型，分别是引导服务、核心服务和其他服务，其中其他服务是一些非紧要和不需要立即启动的服务，WMS就是其他服务的一种。

```java
private void startOtherServices() {
  	//...
    try {
        traceBeginAndSlog("InitWatchdog");
        final Watchdog watchdog = Watchdog.getInstance();
        watchdog.init(context, mActivityManagerService);
        traceEnd();

        traceBeginAndSlog("StartInputManagerService");
        inputManager = new InputManagerService(context);
        traceEnd();

        traceBeginAndSlog("StartWindowManagerService");
        // WMS needs sensor service ready
        ConcurrentUtils.waitForFutureNoInterrupt(mSensorServiceStart, START_SENSOR_SERVICE);
        mSensorServiceStart = null;
        wm = WindowManagerService.main(context, inputManager,
                mFactoryTestMode != FactoryTest.FACTORY_TEST_LOW_LEVEL,
                !mFirstBoot, mOnlyCore, new PhoneWindowManager());
        ServiceManager.addService(Context.WINDOW_SERVICE, wm);
        ServiceManager.addService(Context.INPUT_SERVICE, inputManager);
        traceEnd();
				//...

    } catch (RuntimeException e) {
				//...
    }
		//...
    try {
        wm.displayReady();
    } catch (Throwable e) {
				//...
    }
		//...
    try {
        wm.systemReady();
    } catch (Throwable e) {
        //...
    }
    //...
}
```

startOtherServices方法用于启动其他服务，其他服务大概有100个左右。

Watchdog用来监控系统的一些关键服务的运行状况。

**注释1**
执行WMS的main方法，其内部会创建WMS，需要注意的是main方法其中一个传入的参数就是刚刚创建的IMS，WMS是输入事件的中转站，其内部包含了IMS引用并不意外。
这里得知WMS的main方法是运行在SystemServer的run方法中的，换句话说就是运行在“system_server”线程中。

这里看一下WMS的main方法：

```java
public static WindowManagerService main(final Context context, final InputManagerService im, final boolean haveInputMethods, final boolean showBootMsgs, final boolean onlyCore, WindowManagerPolicy policy) {
    DisplayThread.getHandler().runWithScissors(() -> sInstance = new WindowManagerService(context, im, haveInputMethods, showBootMsgs, onlyCore, policy), 0);
    return sInstance;
}
```

这里创建了WMS的实例，这个过程运行在Runnable的run方法中，而Runmable则传到了DisplayThread对应Handler的runWithScissors方法中，说明WMS的创建是运行在android.display线程中的。这里runWithScissors方法的第二个参数传入的是0，后面会提到。

下面来查看Handler的runWithScissors方法做了什么：

```java
public final boolean runWithScissors(final Runnable r, long timeout) {
    if (r == null) {
        throw new IllegalArgumentException("runnable must not be null");
    }
    if (timeout < 0) {
        throw new IllegalArgumentException("timeout must be non-negative");
    }
    if (Looper.myLooper() == mLooper) {//注释1
        r.run();
        return true;
    }

    BlockingRunnable br = new BlockingRunnable(r);
    return br.postAndWait(this, timeout);
}
```

在注释1处根据每个线程只有一个Looper的原理来判断当前的线程(system_server线程)是否是Handler所指向的线程(android.display线程)，如果是则直接执行Runnable的run方法，如果不是则调用BlockingRunnable的postAndWait方法，井将当前线程的Runnable作为参数传进去。

BlockingRunnable是Handler的内部类，代码如下所示：

```java
private static final class BlockingRunnable implements Runnable {
    private final Runnable mTask;
    private boolean mDone;

    public BlockingRunnable(Runnable task) {
        mTask = task;
    }

    @Override
    public void run() {
        try {
            mTask.run();//注释1
        } finally {
            synchronized (this) {
                mDone = true;
                notifyAll();
            }
        }
    }

    public boolean postAndWait(Handler handler, long timeout) {
        if (!handler.post(this)) {//将当前的 BlockingRunnable 添加到 Handler 的任务队列中
            return false;
        }
				//前面runWithcissors方法的第二个参数为0，因此timeout等于0
        synchronized (this) {
            if (timeout > 0) {
                final long expirationTime = SystemClock.uptimeMillis() + timeout;
                while (!mDone) {
                    long delay = expirationTime - SystemClock.uptimeMillis();
                    if (delay <= 0) {
                        return false; // timeout
                    }
                    try {
                        wait(delay);
                    } catch (InterruptedException ex) {
                    }
                }
            } else {
                while (!mDone) {
                    try {
                        wait();
                    } catch (InterruptedException ex) {
                    }
                }
            }
        }
        return true;
    }
}
```

如果mDone为false的话会一直调用注释3处的wait方法使得当前线程(system_server 线程)进入等待状态，那么等待的是哪个线程呢？

在注释1处执行了传入的Runnable的run方法(运行在android.display线程)，执行完毕后在finally代码块中将mDone设置为true，并调用notifyAll方法唤醒处于等待状态的线程，这样就不会继续调用注释3处的wait方法。

因此得出结论，system_server线程等待的就是android.display线程，一直到android.display线程执行完毕再执行system_server线程，这是因为android.display线程内部执行了WMS的创建，而WMS的创建优先级要更高。以上是WMS的创建，最后查看WMS的构造方法：

```java
private WindowManagerService(Context context, InputManagerService inputManager, boolean haveInputMethods, boolean showBootMsgs, boolean onlyCore, WindowManagerPolicy policy) {
    //...
    mInputManager = inputManager;//注释1
    //...
    mDisplayManager = (DisplayManager)context.getSystemService(Context.DISPLAY_SERVICE);
    mDisplays = mDisplayManager.getDisplays();//注释2
    for (Display display : mDisplays) {
        createDisplayContentLocked(display);//注释3
    }
		//...
    mActivityManager = ActivityManager.getService();//注释4
    //...
    mAnimator = new WindowAnimator(this);//注释5
    mAllowTheaterModeWakeFromLayout = context.getResources().getBoolean(
            com.android.internal.R.bool.config_allowTheaterModeWakeFromWindowLayout);
    LocalServices.addService(WindowManagerInternal.class, new LocalService());
    initPolicy();//注释6
    Watchdog.getInstance().addMonitor(this);//注释7
		//...
}
```

**注释1**

用来保存传进来的IMS，这样WMS持有了IMS的引用。

**注释2**

通过DisplayManager的getDisplays方法得到Display数组(每个显示设备都有一个Display实例)。

**注释3**

接着遍历Display数组，在注释3处的createDisplayContentLocked方法将Display封装成DisplayContent，DisplayContent 用来描述一块屏幕。

**注释4**

得到AMS实例，并赋值给mActivityManager，这样WMS就持有了AMS的引用。

**注释5**

创建了WindowAnimator，它用于管理所有的窗口动画。

**注释6**

初始化了窗口管理策略的接口类WindowManagerPolicy(WMP)，它用来定义一个窗口策略所要遵循的通用规范。

**注释7**

将自身也就是WMS通过addMonitor方法添加到Watchdog中，Watchdog用来监控系统的一些关键服务的运行状况(比如传入的WMS的运行状况)，这些被监控的服务都会实现Watchdog.Monitor接口。Watchdog每分钟都会对被监控的系统服务进行检查，如果被监控的系统服务出现了死锁，则会杀死Watchdog所在的进程，也就是SystemServer进程。

查看注释6处的initPolicy 方法，如下所示：

```java
private void initPolicy() {
    UiThread.getHandler().runWithScissors(new Runnable() {
        @Override
        public void run() {
            WindowManagerPolicyThread.set(Thread.currentThread(), Looper.myLooper());

            mPolicy.init(mContext, WindowManagerService.this, WindowManagerService.this);//注释1
        }
    }, 0);
}
```

initPolicy方法和此前讲的WMS的main方法的实现类似，在注释1处执行了WMP的init方法，WMP是一个接口，init 方法具体在PhoneWindowManager (PWM)中实现。PWM的init方法运行在android.ui线程中，它的优先级要高于initPolicy方法所在的android.display线程，因此android.display 线程要等PWM的init 方法执行完毕后，处于等待状态的android.display线程才会被唤醒从而继续执行下面的代码。本文共提到了3个线程，分别是system_server, android.display 和android.ui，下面给出这3个线程之间的关系：

**此文不再记录**

# 笔记来源

1. 刘望舒《Android进阶解密》