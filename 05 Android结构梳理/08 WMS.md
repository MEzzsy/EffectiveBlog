# WMS的职责

1. **窗口管理**

	WMS是窗口的管理者，它负责窗口的启动、添加和删除，另外窗口的大小和层级也是由WMS进行管理的。窗口管理的核心成员有DisplayContent、WindowToken和WindowState。

2. **窗口动画**

	窗口间进行切换时，使用窗口动画可以显得更炫一些，窗口动画由WMS的动画子系统来负责，动画子系统的管理者为WindowAnimator。
3. **输入系统的中转站**

	通过对窗口的触摸从而产生触摸事件，InputManagerService(IMS)会对触摸事件进行处理，它会寻找一个最合适的窗口来处理触摸反馈信息，WMS是窗口的管理者，用它作为输入系统的中转站。

4. **Surface管理**
窗口并不具备绘制的功能，因此每个窗口都需要有块Surface来供自己绘制，为每个窗口分配Surface是由WMS来完成的。

# WMS的创建过程

SystemServer在启动过程中会启动三种服务：分别是引导服务、核心服务、其他服务。

WMS属于其他服务。

```java
//启动其他服务的代码
private void startOtherServices() {
  	//...
    try {
        //。。。

        traceBeginAndSlog("StartInputManagerService");
        inputManager = new InputManagerService(context);
        traceEnd();

        //。。。
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

上面代码的`WindowManagerService.main`内部会创建一个WMS，因为WMS和输入事件有关，所以WMS的创建需要InputManagerService。

在Binder通信中说到，Server端会向ServiceManager注册。说的就是代码中：

```java
ServiceManager.addService(Context.WINDOW_SERVICE, wm);
ServiceManager.addService(Context.INPUT_SERVICE, inputManager);
```

这样如果某个客户端想要使用WMS，就需要先去ServiceManager中查询信息，然后根据信息与WMS所在的进程建立通信通路，客户端就可以使用WMS了。

# Window的操作

## WMS的添加Window

```java
public int addWindow(Session session, IWindow client, int seq,
        WindowManager.LayoutParams attrs, int viewVisibility, int displayId,
        Rect outContentInsets, Rect outStableInsets, Rect outOutsets,
        InputChannel outInputChannel) {
    int[] appOp = new int[1];
    //检查权限
    int res = mPolicy.checkAddPermission(attrs, appOp);
    if (res != WindowManagerGlobal.ADD_OKAY) {
        return res;
    }
	//...
    synchronized(mWindowMap) {
        //...
        //根据displayId决定添加到哪个DisplayContent上，DisplayContent用来描述一块屏幕（这里的屏幕应该指的是物理屏幕）
        final DisplayContent displayContent = mRoot.getDisplayContentOrCreate(displayId);
        if (displayContent == null) {
            Slog.w(TAG_WM, "Attempted to add window to a display that does not exist: "
                    + displayId + ".  Aborting.");
            return WindowManagerGlobal.ADD_INVALID_DISPLAY;
        }
        //。。。
		//对子窗口进行判断
        if (type >= FIRST_SUB_WINDOW && type <= LAST_SUB_WINDOW) {
            parentWindow = windowForClientLocked(null, attrs.token, false);
            if (parentWindow == null) {
                Slog.w(TAG_WM, "Attempted to add window with token that is not a window: "
                      + attrs.token + ".  Aborting.");
                return WindowManagerGlobal.ADD_BAD_SUBWINDOW_TOKEN;
            }
            if (parentWindow.mAttrs.type >= FIRST_SUB_WINDOW
                    && parentWindow.mAttrs.type <= LAST_SUB_WINDOW) {
                Slog.w(TAG_WM, "Attempted to add window with token that is a sub-window: "
                        + attrs.token + ".  Aborting.");
                return WindowManagerGlobal.ADD_BAD_SUBWINDOW_TOKEN;
            }
        }
		//...
        //获取WindowToken
        WindowToken token = displayContent.getWindowToken(
                hasParent ? parentWindow.mAttrs.token : attrs.token);
        //获取rootType
        final int rootType = hasParent ? parentWindow.mAttrs.type : type;
		//根据WindowToken和rootType来判断需要add的Window是否有效。
        //。。。
		//创建WindowState，它存有窗口的所有的状态信息，在WMS中它代表一个窗口。
        final WindowState win = new WindowState(this, session, client, token, parentWindow,
                appOp[0], seq, attrs, viewVisibility, session.mUid,
                session.mCanAddInternalSystemWindow);
        //。。。
        //用于准备将窗口添加到系统中
        res = mPolicy.prepareAddWindowLw(win, attrs);
        if (res != WindowManagerGlobal.ADD_OKAY) {
            return res;
        }
		//。。。
        //将WindowState添加到该WindowState对应的WindowToken中(实际是保存在WindowToken的父类WindowContainer中)，这样WindowToken就包含了同一个组件的WindowState。
        win.mToken.addWindow(win);
        //。。。
    }
    return res;
}
```

下面按照代码顺序解读：

1.  WMS的addWindow返回的是addWindow的各种状态，比如添加Window成功，无效的display 等，这些状态被定义在WindowManagerGlobal中。

2.  调用WMP（具体实现为PhoneWindowManager）的checkAddPermission方法来检查权限，如果没有权限则不会执行后续的代码逻辑。
    Window的type分为应用程序窗口、子窗口和系统窗口，检查权限主要检查是否是这些类型。对于系统窗口类型还要进一步检查权限（添加系统级别的Window需要注册权限）。

3.  处理WindowToken，根据WindowToken和rootType来判断需要add的Window是否有效。WindowToken有2个作用，一是相当于窗口令牌，如果应用程序需要创建一个窗口，那么需要有效的WindowToken；另一个作用是管理同一个组件（如同一个Activity）的窗口（WindowState）。
4.  创建WindowState，它存有窗口的所有的状态信息，在WMS中它代表一个窗口。

## WMS的删除Window

```java
void removeWindow(Session session, IWindow client) {
    synchronized(mWindowMap) {
        WindowState win = windowForClientLocked(session, client, false);
        if (win == null) {
            return;
        }
        win.removeIfPossible();
    }
}
```

```java
void removeIfPossible() {
    super.removeIfPossible();
    removeIfPossible(false /*keepVisibleDeadWindow*/);
}
```

```java
private void removeIfPossible(boolean keepVisibleDeadWindow) {
    //。。。判断条件
    removeImmediately();
    //。。。
}
```

removeIfPossible方法并不是直接执行删除操作的，而是进行多个条件判断过滤，满足其中一个条件就会return，推迟删除操作。比如Window正在运行一个动画，这时就得推迟删除操作，直到动画完成。否则执行removeImmediately方法。

removeImmediately方法主要是清理和释放和Window有关的资源。