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

    boolean reportNewConfig = false;
    WindowState parentWindow = null;
    long origId;
    final int callingUid = Binder.getCallingUid();
    final int type = attrs.type;

    synchronized(mWindowMap) {
        if (!mDisplayReady) {
            throw new IllegalStateException("Display has not been initialialized");
        }

        final DisplayContent displayContent = mRoot.getDisplayContentOrCreate(displayId);
        if (displayContent == null) {
            Slog.w(TAG_WM, "Attempted to add window to a display that does not exist: "
                    + displayId + ".  Aborting.");
            return WindowManagerGlobal.ADD_INVALID_DISPLAY;
        }
        if (!displayContent.hasAccess(session.mUid)
                && !mDisplayManagerInternal.isUidPresentOnDisplay(session.mUid, displayId)) {
            Slog.w(TAG_WM, "Attempted to add window to a display for which the application "
                    + "does not have access: " + displayId + ".  Aborting.");
            return WindowManagerGlobal.ADD_INVALID_DISPLAY;
        }

        if (mWindowMap.containsKey(client.asBinder())) {
            Slog.w(TAG_WM, "Window " + client + " is already added");
            return WindowManagerGlobal.ADD_DUPLICATE_ADD;
        }

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

        if (type == TYPE_PRIVATE_PRESENTATION && !displayContent.isPrivate()) {
            Slog.w(TAG_WM, "Attempted to add private presentation window to a non-private display.  Aborting.");
            return WindowManagerGlobal.ADD_PERMISSION_DENIED;
        }

        AppWindowToken atoken = null;
        final boolean hasParent = parentWindow != null;
        // Use existing parent window token for child windows since they go in the same token
        // as there parent window so we can apply the same policy on them.
        WindowToken token = displayContent.getWindowToken(
                hasParent ? parentWindow.mAttrs.token : attrs.token);
        // If this is a child window, we want to apply the same type checking rules as the
        // parent window type.
        final int rootType = hasParent ? parentWindow.mAttrs.type : type;

        boolean addToastWindowRequiresToken = false;

        if (token == null) {
            if (rootType >= FIRST_APPLICATION_WINDOW && rootType <= LAST_APPLICATION_WINDOW) {
                Slog.w(TAG_WM, "Attempted to add application window with unknown token "
                      + attrs.token + ".  Aborting.");
                return WindowManagerGlobal.ADD_BAD_APP_TOKEN;
            }
            if (rootType == TYPE_INPUT_METHOD) {
                Slog.w(TAG_WM, "Attempted to add input method window with unknown token "
                      + attrs.token + ".  Aborting.");
                return WindowManagerGlobal.ADD_BAD_APP_TOKEN;
            }
            if (rootType == TYPE_VOICE_INTERACTION) {
                Slog.w(TAG_WM, "Attempted to add voice interaction window with unknown token "
                      + attrs.token + ".  Aborting.");
                return WindowManagerGlobal.ADD_BAD_APP_TOKEN;
            }
            if (rootType == TYPE_WALLPAPER) {
                Slog.w(TAG_WM, "Attempted to add wallpaper window with unknown token "
                      + attrs.token + ".  Aborting.");
                return WindowManagerGlobal.ADD_BAD_APP_TOKEN;
            }
            if (rootType == TYPE_DREAM) {
                Slog.w(TAG_WM, "Attempted to add Dream window with unknown token "
                      + attrs.token + ".  Aborting.");
                return WindowManagerGlobal.ADD_BAD_APP_TOKEN;
            }
            if (rootType == TYPE_QS_DIALOG) {
                Slog.w(TAG_WM, "Attempted to add QS dialog window with unknown token "
                      + attrs.token + ".  Aborting.");
                return WindowManagerGlobal.ADD_BAD_APP_TOKEN;
            }
            if (rootType == TYPE_ACCESSIBILITY_OVERLAY) {
                Slog.w(TAG_WM, "Attempted to add Accessibility overlay window with unknown token "
                        + attrs.token + ".  Aborting.");
                return WindowManagerGlobal.ADD_BAD_APP_TOKEN;
            }
            if (type == TYPE_TOAST) {
                // Apps targeting SDK above N MR1 cannot arbitrary add toast windows.
                if (doesAddToastWindowRequireToken(attrs.packageName, callingUid,
                        parentWindow)) {
                    Slog.w(TAG_WM, "Attempted to add a toast window with unknown token "
                            + attrs.token + ".  Aborting.");
                    return WindowManagerGlobal.ADD_BAD_APP_TOKEN;
                }
            }
            final IBinder binder = attrs.token != null ? attrs.token : client.asBinder();
            token = new WindowToken(this, binder, type, false, displayContent,
                    session.mCanAddInternalSystemWindow);
        } else if (rootType >= FIRST_APPLICATION_WINDOW && rootType <= LAST_APPLICATION_WINDOW) {
            atoken = token.asAppWindowToken();
            if (atoken == null) {
                Slog.w(TAG_WM, "Attempted to add window with non-application token "
                      + token + ".  Aborting.");
                return WindowManagerGlobal.ADD_NOT_APP_TOKEN;
            } else if (atoken.removed) {
                Slog.w(TAG_WM, "Attempted to add window with exiting application token "
                      + token + ".  Aborting.");
                return WindowManagerGlobal.ADD_APP_EXITING;
            }
        } else if (rootType == TYPE_INPUT_METHOD) {
            if (token.windowType != TYPE_INPUT_METHOD) {
                Slog.w(TAG_WM, "Attempted to add input method window with bad token "
                        + attrs.token + ".  Aborting.");
                  return WindowManagerGlobal.ADD_BAD_APP_TOKEN;
            }
        } else if (rootType == TYPE_VOICE_INTERACTION) {
            if (token.windowType != TYPE_VOICE_INTERACTION) {
                Slog.w(TAG_WM, "Attempted to add voice interaction window with bad token "
                        + attrs.token + ".  Aborting.");
                  return WindowManagerGlobal.ADD_BAD_APP_TOKEN;
            }
        } else if (rootType == TYPE_WALLPAPER) {
            if (token.windowType != TYPE_WALLPAPER) {
                Slog.w(TAG_WM, "Attempted to add wallpaper window with bad token "
                        + attrs.token + ".  Aborting.");
                  return WindowManagerGlobal.ADD_BAD_APP_TOKEN;
            }
        } else if (rootType == TYPE_DREAM) {
            if (token.windowType != TYPE_DREAM) {
                Slog.w(TAG_WM, "Attempted to add Dream window with bad token "
                        + attrs.token + ".  Aborting.");
                  return WindowManagerGlobal.ADD_BAD_APP_TOKEN;
            }
        } else if (rootType == TYPE_ACCESSIBILITY_OVERLAY) {
            if (token.windowType != TYPE_ACCESSIBILITY_OVERLAY) {
                Slog.w(TAG_WM, "Attempted to add Accessibility overlay window with bad token "
                        + attrs.token + ".  Aborting.");
                return WindowManagerGlobal.ADD_BAD_APP_TOKEN;
            }
        } else if (type == TYPE_TOAST) {
            // Apps targeting SDK above N MR1 cannot arbitrary add toast windows.
            addToastWindowRequiresToken = doesAddToastWindowRequireToken(attrs.packageName,
                    callingUid, parentWindow);
            if (addToastWindowRequiresToken && token.windowType != TYPE_TOAST) {
                Slog.w(TAG_WM, "Attempted to add a toast window with bad token "
                        + attrs.token + ".  Aborting.");
                return WindowManagerGlobal.ADD_BAD_APP_TOKEN;
            }
        } else if (type == TYPE_QS_DIALOG) {
            if (token.windowType != TYPE_QS_DIALOG) {
                Slog.w(TAG_WM, "Attempted to add QS dialog window with bad token "
                        + attrs.token + ".  Aborting.");
                return WindowManagerGlobal.ADD_BAD_APP_TOKEN;
            }
        } else if (token.asAppWindowToken() != null) {
            Slog.w(TAG_WM, "Non-null appWindowToken for system window of rootType=" + rootType);
            // It is not valid to use an app token with other system types; we will
            // instead make a new token for it (as if null had been passed in for the token).
            attrs.token = null;
            token = new WindowToken(this, client.asBinder(), type, false, displayContent,
                    session.mCanAddInternalSystemWindow);
        }

        final WindowState win = new WindowState(this, session, client, token, parentWindow,
                appOp[0], seq, attrs, viewVisibility, session.mUid,
                session.mCanAddInternalSystemWindow);
        if (win.mDeathRecipient == null) {
            // Client has apparently died, so there is no reason to
            // continue.
            Slog.w(TAG_WM, "Adding window client " + client.asBinder()
                    + " that is dead, aborting.");
            return WindowManagerGlobal.ADD_APP_EXITING;
        }

        if (win.getDisplayContent() == null) {
            Slog.w(TAG_WM, "Adding window to Display that has been removed.");
            return WindowManagerGlobal.ADD_INVALID_DISPLAY;
        }

        mPolicy.adjustWindowParamsLw(win.mAttrs);
        win.setShowToOwnerOnlyLocked(mPolicy.checkShowToOwnerOnly(attrs));

        res = mPolicy.prepareAddWindowLw(win, attrs);
        if (res != WindowManagerGlobal.ADD_OKAY) {
            return res;
        }

        final boolean openInputChannels = (outInputChannel != null
                && (attrs.inputFeatures & INPUT_FEATURE_NO_INPUT_CHANNEL) == 0);
        if  (openInputChannels) {
            win.openInputChannel(outInputChannel);
        }

        // If adding a toast requires a token for this app we always schedule hiding
        // toast windows to make sure they don't stick around longer then necessary.
        // We hide instead of remove such windows as apps aren't prepared to handle
        // windows being removed under them.
        //
        // If the app is older it can add toasts without a token and hence overlay
        // other apps. To be maximally compatible with these apps we will hide the
        // window after the toast timeout only if the focused window is from another
        // UID, otherwise we allow unlimited duration. When a UID looses focus we
        // schedule hiding all of its toast windows.
        if (type == TYPE_TOAST) {
            if (!getDefaultDisplayContentLocked().canAddToastWindowForUid(callingUid)) {
                Slog.w(TAG_WM, "Adding more than one toast window for UID at a time.");
                return WindowManagerGlobal.ADD_DUPLICATE_ADD;
            }
            // Make sure this happens before we moved focus as one can make the
            // toast focusable to force it not being hidden after the timeout.
            // Focusable toasts are always timed out to prevent a focused app to
            // show a focusable toasts while it has focus which will be kept on
            // the screen after the activity goes away.
            if (addToastWindowRequiresToken
                    || (attrs.flags & LayoutParams.FLAG_NOT_FOCUSABLE) == 0
                    || mCurrentFocus == null
                    || mCurrentFocus.mOwnerUid != callingUid) {
                mH.sendMessageDelayed(
                        mH.obtainMessage(H.WINDOW_HIDE_TIMEOUT, win),
                        win.mAttrs.hideTimeoutMilliseconds);
            }
        }

        // From now on, no exceptions or errors allowed!

        res = WindowManagerGlobal.ADD_OKAY;
        if (mCurrentFocus == null) {
            mWinAddedSinceNullFocus.add(win);
        }

        if (excludeWindowTypeFromTapOutTask(type)) {
            displayContent.mTapExcludedWindows.add(win);
        }

        origId = Binder.clearCallingIdentity();

        win.attach();
        mWindowMap.put(client.asBinder(), win);
        if (win.mAppOp != AppOpsManager.OP_NONE) {
            int startOpResult = mAppOps.startOpNoThrow(win.mAppOp, win.getOwningUid(),
                    win.getOwningPackage());
            if ((startOpResult != AppOpsManager.MODE_ALLOWED) &&
                    (startOpResult != AppOpsManager.MODE_DEFAULT)) {
                win.setAppOpVisibilityLw(false);
            }
        }

        final AppWindowToken aToken = token.asAppWindowToken();
        if (type == TYPE_APPLICATION_STARTING && aToken != null) {
            aToken.startingWindow = win;
            if (DEBUG_STARTING_WINDOW) Slog.v (TAG_WM, "addWindow: " + aToken
                    + " startingWindow=" + win);
        }

        boolean imMayMove = true;

        win.mToken.addWindow(win);
        if (type == TYPE_INPUT_METHOD) {
            win.mGivenInsetsPending = true;
            setInputMethodWindowLocked(win);
            imMayMove = false;
        } else if (type == TYPE_INPUT_METHOD_DIALOG) {
            displayContent.computeImeTarget(true /* updateImeTarget */);
            imMayMove = false;
        } else {
            if (type == TYPE_WALLPAPER) {
                displayContent.mWallpaperController.clearLastWallpaperTimeoutTime();
                displayContent.pendingLayoutChanges |= FINISH_LAYOUT_REDO_WALLPAPER;
            } else if ((attrs.flags&FLAG_SHOW_WALLPAPER) != 0) {
                displayContent.pendingLayoutChanges |= FINISH_LAYOUT_REDO_WALLPAPER;
            } else if (displayContent.mWallpaperController.isBelowWallpaperTarget(win)) {
                // If there is currently a wallpaper being shown, and
                // the base layer of the new window is below the current
                // layer of the target window, then adjust the wallpaper.
                // This is to avoid a new window being placed between the
                // wallpaper and its target.
                displayContent.pendingLayoutChanges |= FINISH_LAYOUT_REDO_WALLPAPER;
            }
        }

        // If the window is being added to a stack that's currently adjusted for IME,
        // make sure to apply the same adjust to this new window.
        win.applyAdjustForImeIfNeeded();

        if (type == TYPE_DOCK_DIVIDER) {
            mRoot.getDisplayContent(displayId).getDockedDividerController().setWindow(win);
        }

        final WindowStateAnimator winAnimator = win.mWinAnimator;
        winAnimator.mEnterAnimationPending = true;
        winAnimator.mEnteringAnimation = true;
        // Check if we need to prepare a transition for replacing window first.
        if (atoken != null && atoken.isVisible()
                && !prepareWindowReplacementTransition(atoken)) {
            // If not, check if need to set up a dummy transition during display freeze
            // so that the unfreeze wait for the apps to draw. This might be needed if
            // the app is relaunching.
            prepareNoneTransitionForRelaunching(atoken);
        }

        if (displayContent.isDefaultDisplay) {
            final DisplayInfo displayInfo = displayContent.getDisplayInfo();
            final Rect taskBounds;
            if (atoken != null && atoken.getTask() != null) {
                taskBounds = mTmpRect;
                atoken.getTask().getBounds(mTmpRect);
            } else {
                taskBounds = null;
            }
            if (mPolicy.getInsetHintLw(win.mAttrs, taskBounds, displayInfo.rotation,
                    displayInfo.logicalWidth, displayInfo.logicalHeight, outContentInsets,
                    outStableInsets, outOutsets)) {
                res |= WindowManagerGlobal.ADD_FLAG_ALWAYS_CONSUME_NAV_BAR;
            }
        } else {
            outContentInsets.setEmpty();
            outStableInsets.setEmpty();
        }

        if (mInTouchMode) {
            res |= WindowManagerGlobal.ADD_FLAG_IN_TOUCH_MODE;
        }
        if (win.mAppToken == null || !win.mAppToken.isClientHidden()) {
            res |= WindowManagerGlobal.ADD_FLAG_APP_VISIBLE;
        }

        mInputMonitor.setUpdateInputWindowsNeededLw();

        boolean focusChanged = false;
        if (win.canReceiveKeys()) {
            focusChanged = updateFocusedWindowLocked(UPDATE_FOCUS_WILL_ASSIGN_LAYERS,
                    false /*updateInputWindows*/);
            if (focusChanged) {
                imMayMove = false;
            }
        }

        if (imMayMove) {
            displayContent.computeImeTarget(true /* updateImeTarget */);
        }

        // Don't do layout here, the window must call
        // relayout to be displayed, so we'll do it there.
        displayContent.assignWindowLayers(false /* setLayoutNeeded */);

        if (focusChanged) {
            mInputMonitor.setInputFocusLw(mCurrentFocus, false /*updateInputWindows*/);
        }
        mInputMonitor.updateInputWindowsLw(false /*force*/);

        if (localLOGV || DEBUG_ADD_REMOVE) Slog.v(TAG_WM, "addWindow: New client "
                + client.asBinder() + ": window=" + win + " Callers=" + Debug.getCallers(5));

        if (win.isVisibleOrAdding() && updateOrientationFromAppTokensLocked(false, displayId)) {
            reportNewConfig = true;
        }
    }

    if (reportNewConfig) {
        sendNewConfiguration(displayId);
    }

    Binder.restoreCallingIdentity(origId);

    return res;
}
```

下面按照代码顺序解读：

WMS的addWindow返回的是addWindow的各种状态，比如添加Window成功，无效的display 等，这些状态被定义在WindowManagerGlobal中。

调用WMP（具体实现为PhoneWindowManager）的checkAddPermission方法来检查权限，如果没有权限则不会执行后续的代码逻辑。
Window的type分为应用程序窗口、子窗口和系统窗口，检查权限主要检查是否是这些类型。对于系统窗口类型还要进一步检查权限（添加系统级别的Window需要注册权限）。







在注释2
处通过displayId来获得窗口要添加到哪个DisplayContent上，如果没有找到
DisplayContent，则返回WindowManagerGlobal.ADD_ INVALID_ DISPLAY这一状态，其
中DisplayContent用来描述一块屏幕。 在注释3处，type代表-一个窗口的类型，它的数值
介于FIRST_ SUB_ _WINDOW和LAST_ _SUB_ WINDOW之间(1000~1999),这个数值定义
在WindowManager中，说明这个窗口是-一个子窗口。在注释4处，attrs.token 是IBinder 类型的对象，windowForClientLocked 方法内部会根据attrs.token 作为key 值从mWindowMap .
中得到该子窗口的父窗口。接着对父窗口进行判断，如果父窗口为null或者type的取值
范围不正确则会返回错误的状态。

在注释1处通过displayContent的getWindowToken方法得到WindowToken。在注释
2处，如果有父窗口就将父窗口的type值赋值给rootType， 如果没有将当前窗口的type 
值赋值给rootType。接下来如果WindowToken为null,则根据rootType 或者type 的值进
行区分判断，如果rootType值等于TYPE_ INPUT_ _METHOD、TYPE_ _WALLPAPER等值
时，则返回状态值WindowManagerGlobal.ADD_ _BAD_ APP_ TOKEN,说明rootType值等
于TYPE_ _INPUT_ _METHOD、TYPE_ WALLPAPER等值时是不允许WindowToken为null
的。通过多次的条件判断筛选，最后会在注释3处隐式创建WindowToken,这说明当我们
添加窗口时可以不向WMS提供WindowToken,前提是rootType和type 的值不为前面条件
判断筛选的值。WindowToken 隐式和显式的创建肯定是要加以区分的，注释3处的第4个
参数为false就代表这个WindowToken是隐式创建的。接下来的代码逻辑就是WindowToken
不为null的情况，根据rootType和type的值进行判断，比如在注释4处判断如果窗口为应
用程序窗口，在注释5处将WindowToken转换为专门针对应用程序窗口的
AppWindowToken,然后根据AppWindowToken的值进行后续的判断。

在注释1处创建了WindowState, 它存有窗口的所有的状态信息，在WMS中它代表一
个窗口。在创建WindowState传入的参数中，this 指的是WMS，client 指的是IWindow ,
IWindow会将WMS中窗口管理的操作回调给ViewRootImpl,token指的是WindowToken紧
接着在注释2和注释3处分别判断请求添加窗口的客户端是否已经死亡、窗口的
DisplayContent是否为null, 如果是则不会再执行下面的代码逻辑。在注释4处调用了WMP
的adjustWindowParamsLw方法，该方法在PhoneWindowManager中实现，此方法会根据窗
口的type 对窗口的LayoutParams 的一 些成员变量进行修改。在注释5处调用WMP的
prepareAddWindowLw方法，用于准备将窗口添加到系统中。在注释6处将WindowState
添加到mWindowMap中。在注释7处将WindowState 添加到该WindowState 对应的
WindowToken中(实 际是保存在WindowToken 的父类WindowContainer 中)，这样
WindowToken就包含了同- -个组件的WindowState。