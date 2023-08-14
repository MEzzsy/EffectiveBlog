# 基础

点击事件即是MotionEvent，由三个方法构成：dispatchTouchEvent、onInterceptTouchEvent、onTouchEvent。

- dispatchTouchEvent：用来事件的分发。如果事件能传递给当前View，那么此方法一定会被调用。

- onInterceptTouchEvent：用来判断是否拦截某个事件。（只有ViewGroup有）

- onTouchEvent：在dispatchTouchEvent中调用，用来处理点击事件。

上述方法的关系的伪代码:

```java
public boolean dispatchTouchEvent(MotionEvent ev) {
	boolean consume = false;
	if (onInterceptTouchEvent(ev)) {
		consume = onTouchEvent(ev);
	} else{
		consume = child.dispatchTouchEvent(ev);
	}
	return consume;
}
```

# 源码分析

## Activity传递

```java
public boolean dispatchTouchEvent(MotionEvent ev) {
    if (ev.getAction() == MotionEvent.ACTION_DOWN) {
        // 默认是空实现
        onUserInteraction();
    }
    if (getWindow().superDispatchTouchEvent(ev)) {
        return true;
    }
    return onTouchEvent(ev);
}
```

Activity将事件传递给Window，如果事件没有被消费，那么就由Activity自己处理。

## Window传递

```java
public boolean superDispatchTouchEvent(MotionEvent event) {
    return mDecor.superDispatchTouchEvent(event);
}
```

```java
public boolean superDispatchTouchEvent(MotionEvent event) {
    return super.dispatchTouchEvent(event);
}
```

PhoneWindow的传递是将事件透传给DecorView。

## ViewGroup传递

ViewGroup的dispatchTouchEvent源码分析：

>   参考https://www.jianshu.com/p/e6413de93fff

```java
public boolean dispatchTouchEvent(MotionEvent ev) {
    // ...
    boolean handled = false;
    if (onFilterTouchEventForSecurity(ev)) {
        final int action = ev.getAction();
        final int actionMasked = action & MotionEvent.ACTION_MASK;

        // 注释1
        if (actionMasked == MotionEvent.ACTION_DOWN) {
            cancelAndClearTouchTargets(ev);
            resetTouchState();
        }

        // 注释2，检查父View是否需要拦截
        final boolean intercepted;
        if (actionMasked == MotionEvent.ACTION_DOWN
                || mFirstTouchTarget != null) {
            // 通过requestDisallowInterceptTouchEvent来改变mGroupFlags的值
            final boolean disallowIntercept = (mGroupFlags & FLAG_DISALLOW_INTERCEPT) != 0;
            if (!disallowIntercept) {
                intercepted = onInterceptTouchEvent(ev);
                ev.setAction(action);
            } else {
                intercepted = false;
            }
        } else {
            // There are no touch targets and this action is not an initial down
            // so this view group continues to intercept touches.
            intercepted = true;
        }
		// ...
        // 如果viewFlag被设置了PFLAG_CANCEL_NEXT_UP_EVENT，那么就表示下一步应该是Cancel事件，或者如果当前的Action为取消，那么当前事件应该就是取消了。
        final boolean canceled = resetCancelNextUpFlag(this)
                || actionMasked == MotionEvent.ACTION_CANCEL;
		// 。。。
        TouchTarget newTouchTarget = null;
        boolean alreadyDispatchedToNewTouchTarget = false;
        if (!canceled && !intercepted) {
			// 。。。
            if (actionMasked == MotionEvent.ACTION_DOWN
                    || (split && actionMasked == MotionEvent.ACTION_POINTER_DOWN)
                    || actionMasked == MotionEvent.ACTION_HOVER_MOVE) {
                // 。。。
                final int childrenCount = mChildrenCount;
                if (newTouchTarget == null && childrenCount != 0) {
                    // 。。。
                    final View[] children = mChildren;
                    for (int i = childrenCount - 1; i >= 0; i--) {
                        final int childIndex = getAndVerifyPreorderedIndex(
                                childrenCount, i, customOrder);
                        final View child = getAndVerifyPreorderedView(
                                preorderedList, children, childIndex);
                        // 。。。
                        newTouchTarget = getTouchTarget(child);
                        if (newTouchTarget != null) {
                            // Child is already receiving touch within its bounds.
                            // Give it the new pointer in addition to the ones it is handling.
                            newTouchTarget.pointerIdBits |= idBitsToAssign;
                            break;
                        }

                        resetCancelNextUpFlag(child);
                        if (dispatchTransformedTouchEvent(ev, false, child, idBitsToAssign)) {
                            // 。。。
                            newTouchTarget = addTouchTarget(child, idBitsToAssign);
                            alreadyDispatchedToNewTouchTarget = true;
                            break;
                        }
						// 。。。
                    }
                    // 。。。
                }
                // 。。。
            }
        }

        if (mFirstTouchTarget == null) {
            handled = dispatchTransformedTouchEvent(ev, canceled, null,
                    TouchTarget.ALL_POINTER_IDS);
        } else {
            TouchTarget predecessor = null;
            TouchTarget target = mFirstTouchTarget;
            while (target != null) {
                final TouchTarget next = target.next;
                if (alreadyDispatchedToNewTouchTarget && target == newTouchTarget) {
                    handled = true;
                } else {
                    final boolean cancelChild = resetCancelNextUpFlag(target.child)
                            || intercepted;
                    if (dispatchTransformedTouchEvent(ev, cancelChild,
                            target.child, target.pointerIdBits)) {
                        handled = true;
                    }
                    if (cancelChild) {
                        if (predecessor == null) {
                            mFirstTouchTarget = next;
                        } else {
                            predecessor.next = next;
                        }
                        target.recycle();
                        target = next;
                        continue;
                    }
                }
                predecessor = target;
                target = next;
            }
        }

       // 。。。重置状态
    }
	// 。。。
    return handled;
}
```

1.   注释1
     对Touch事件初始化，虽然在dispatchTouchEvent中会在最后进行初始化，但是因为在一些异常情况下（app切换，anr等等）并没有进行到初始化的代码，所以在每次touch事件流程开始的时候就再进行一次初始化。
2.   注释2
     判断父View是否拦截事件，可以看到只有当事件是ACTION_DOWN或
     `mFirstTouchTarget != null`时才会去调用`onInterceptTouchEvent()`方法来判断是否拦截该事件。

这里mFirstTouchTarget是什么呢？

TouchTarget是ViewGroup的一个内部类。`mFirstTouchTarget`对象指向的是接受触摸事件的View所组成的链表的起始节点。也就是说，当事件由ViewGroup传递给子元素成功处理时，`mFirstTouchTarget`对象就会被赋值，换种方式来说，也就是说当ViewGroup不拦截事件传递，`mFirstTouchTarget!=null`。如果拦截事件，`mFirstTouchTarget!=null`就不成立。此时如果事件序列中的ACTION_MOVE、ACTION_UP事件再传递过来时，由于`(actionMasked == MotionEvent.ACTION_DOWN || mFirstTouchTarget != null)`条件为false，就不会再调用`onInterceptTouchEvent()`方法，是否被拦截的标志变量也会设置为`intercepted = true`，并且后续同一事件序列的其他事件都会默认交给它处理。

这里还有一种特殊情况，那就是FLAG_DISALLOW_INTERCEPT标记位，这个标记位是通过`requestDisallowInterceptTouchEvent()`方法来设置的。FLAG_DISALLOW_INTERCEPT这个标记位一旦设置后，ViewGroup就无法拦截除ACTION_DOWN以外的其他点击事件。

**只要DOWN事件返回true遍历就会结束，那mFirstTouchTarget应该就只有一个元素，为什么还要用一个链表？**

思考：除了DOWN事件可以添加View到mFirstTouchTarget链表，多点触碰时

```java
if (actionMasked == MotionEvent.ACTION_DOWN
                    || (split && actionMasked == MotionEvent.ACTION_POINTER_DOWN)
                    || actionMasked == MotionEvent.ACTION_HOVER_MOVE) 
```

上面另外两个事件也可以将view添加到mFirstTouchTarget

## View处理

```java
public boolean dispatchTouchEvent(MotionEvent event) {
    // ...
    if (onFilterTouchEventForSecurity(event)) {
        // ...
        // 处理OnTouchListener
        ListenerInfo li = mListenerInfo;
        if (li != null && li.mOnTouchListener != null
                && (mViewFlags & ENABLED_MASK) == ENABLED
                && li.mOnTouchListener.onTouch(this, event)) {
            result = true;
        }

        if (!result && onTouchEvent(event)) {
            result = true;
        }
    }
	// 。。。
    return result;
}
```

1.   如果存在OnTouchListener，那么回调onTouch方法。
2.   如果OnTouchListener的onTouch返回false，那么继续执行View的onTouchEvent方法。
3.   在View的onTouchEvent方法里，对Click进行了处理。如果直接重写onTouchEvent，而没有处理点击事件，那么OnClickListener将得不到回调。

# 事件分发例子

https://blog.csdn.net/yyo201/article/details/107654346

实验代码：Activity、LinearLayout子类（MyTestLinearLayout）、TextView子类（MyTestTextView）

```java
class MyTestLinearLayout extends LinearLayout {
    @Override
    public boolean dispatchTouchEvent(MotionEvent ev) {
        Log.i(TAG, "dispatchTouchEvent: " + AppHelper.toStringOfMotionEvent(ev));
        return super.dispatchTouchEvent(ev);
    }

    @Override
    public boolean onInterceptTouchEvent(MotionEvent ev) {
        Log.i(TAG, "onInterceptTouchEvent: " + AppHelper.toStringOfMotionEvent(ev));
        return true;
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        Log.i(TAG, "onTouchEvent: " + AppHelper.toStringOfMotionEvent(event));
        return true;
    }
}
```

```java
class MyTestTextView extends androidx.appcompat.widget.AppCompatTextView {
    @Override
    public boolean dispatchTouchEvent(MotionEvent ev) {
        Log.i(TAG, "dispatchTouchEvent: " + AppHelper.toStringOfMotionEvent(ev));
        return super.dispatchTouchEvent(ev);
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        Log.i(TAG, "onTouchEvent: " + AppHelper.toStringOfMotionEvent(event));
        return true;
    }
}
```

## 例子1：ViewGroup拦截所有事件

```java
public boolean onInterceptTouchEvent(MotionEvent ev) {
	Log.i(TAG, "onInterceptTouchEvent: " + AppHelper.toStringOfMotionEvent(ev));
	return true;
}
```

```
I/TTE-MyViewGroup: dispatchTouchEvent: ACTION_DOWN
I/TTE-MyViewGroup: onInterceptTouchEvent: ACTION_DOWN
I/TTE-MyViewGroup: onTouchEvent: ACTION_DOWN

I/TTE-MyViewGroup: dispatchTouchEvent: ACTION_MOVE
I/TTE-MyViewGroup: onTouchEvent: ACTION_MOVE

I/TTE-MyViewGroup: dispatchTouchEvent: ACTION_UP
I/TTE-MyViewGroup: onTouchEvent: ACTION_UP
```

结论：

ViewGroup部分：ACTION_DOWN时会调用onInterceptTouchEvent，其余事件不会调用。

View部分：不会收到手势事件。

## 例子2：ViewGroup只拦截DOWN

```java
class MyTestLinearLayout extends LinearLayout {
    @Override
    public boolean onInterceptTouchEvent(MotionEvent ev) {
        Log.i(TAG, "onInterceptTouchEvent: " + AppHelper.toStringOfMotionEvent(ev));
        return ev.getAction() == MotionEvent.ACTION_DOWN;
    }
}
```

```
I/TTE-MyViewGroup: dispatchTouchEvent: ACTION_DOWN
I/TTE-MyViewGroup: onInterceptTouchEvent: ACTION_DOWN
I/TTE-MyViewGroup: onTouchEvent: ACTION_DOWN

I/TTE-MyViewGroup: dispatchTouchEvent: ACTION_MOVE
I/TTE-MyViewGroup: onTouchEvent: ACTION_MOVE
I/TTE-MyViewGroup: dispatchTouchEvent: ACTION_MOVE
I/TTE-MyViewGroup: onTouchEvent: ACTION_MOVE
I/TTE-MyViewGroup: dispatchTouchEvent: ACTION_MOVE
I/TTE-MyViewGroup: onTouchEvent: ACTION_MOVE

I/TTE-MyViewGroup: dispatchTouchEvent: ACTION_UP
I/TTE-MyViewGroup: onTouchEvent: ACTION_UP
```

结论：情况和拦截所有事件一样。

## 例子3：ViewGroup拦截除了DOWN的所有事件

```java
@Override
public boolean onInterceptTouchEvent(MotionEvent ev) {
    Log.i(TAG, "onInterceptTouchEvent: " + AppHelper.toStringOfMotionEvent(ev));
    return ev.getAction() != MotionEvent.ACTION_DOWN;
}
```

```
I/TTE-MyViewGroup: dispatchTouchEvent: ACTION_DOWN
I/TTE-MyViewGroup: onInterceptTouchEvent: ACTION_DOWN
I/TTE-MyChildView: dispatchTouchEvent: ACTION_DOWN
I/TTE-MyChildView: onTouchEvent: ACTION_DOWN

I/TTE-MyViewGroup: dispatchTouchEvent: ACTION_MOVE
I/TTE-MyViewGroup: onInterceptTouchEvent: ACTION_MOVE
I/TTE-MyChildView: dispatchTouchEvent: MotionEvent { action=ACTION_CANCEL, actionButton=0, id[0]=0, x[0]=252.0, y[0]=323.0, toolType[0]=TOOL_TYPE_FINGER, buttonState=0, classification=NONE, metaState=0, flags=0x0, edgeFlags=0x0, pointerCount=1, historySize=0, eventTime=2805046, downTime=2804655, deviceId=5, source=0x1002, displayId=0, eventId=323094984 }
I/TTE-MyChildView: onTouchEvent: MotionEvent { action=ACTION_CANCEL, actionButton=0, id[0]=0, x[0]=252.0, y[0]=323.0, toolType[0]=TOOL_TYPE_FINGER, buttonState=0, classification=NONE, metaState=0, flags=0x0, edgeFlags=0x0, pointerCount=1, historySize=0, eventTime=2805046, downTime=2804655, deviceId=5, source=0x1002, displayId=0, eventId=323094984 }

I/TTE-MyViewGroup: dispatchTouchEvent: ACTION_MOVE
I/TTE-MyViewGroup: onTouchEvent: ACTION_MOVE
I/TTE-MyViewGroup: dispatchTouchEvent: ACTION_MOVE
I/TTE-MyViewGroup: onTouchEvent: ACTION_MOVE

I/TTE-MyViewGroup: dispatchTouchEvent: ACTION_UP
I/TTE-MyViewGroup: onTouchEvent: ACTION_UP
```

结论：子View消费了ACTION_DOWN事件，但是其它事件被ViewGroup拦截，那么其它事件会转为ACTION_CANCEL传递给子View，并且后续事件不会再传给子View。

## 例子4

**如果某个ViewGroupe拦截了事件，并且onTouchEvent返回了false，那么事件还会继续传递给其他兄弟ViewGroup吗？**

思考：ViewGroup如果存在兄弟节点，一定存在父节点，父节点没有拦截事件而是遍历子节点分发事件，如果其中的一个子节点（不论是view还是ViewGroup）没有消费事件，那么肯定是会继续遍历分发的。

源码分析：onInterceptTouchEvent返回true，而onTouchEvent返回false，那么dispatchTouchEvent还是会返回false，即dispatchTransformedTouchEvent返回false。在view的遍历中，不会break，而是继续遍历。

## 例子5

**问题3：onTouchEvent的ActionDown如果返回了false，那么这个View将不再会接收到后续的MOVE、UP事件。onTouchEvent的返回值和dispatchTouchEvent的返回值有什么关联？**

DOWN事件下发时，只要有一个子节点返回了true，就会跳出遍历循环，并且将子view添加到mFirstTouchTarget。

如果DOWN事件返回false，那么将不会把这个view添加到mFirstTouchTarget里面，MOVE 、UP等事件分发时，只会分发给mFirstTouchTarget链表里面记录的view。如果DOWN事件返回true其他事件返回false，那么事件会返回到Activity。

ViewGroupe dispatchTouchEvent的返回值跟view的dispatchTouchEvent相关，view的dispatchTouchEvent 与ontouchListener、clickable相关。

## 例子6：onTouchEvent都返回false

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

表示对于一个点击事件，三个对象都不拦截。日志显示，最终Activity会处理事件。

在上面的基础上，更改Activity的ACTION_DOWN和ACTION_UP的返回值，情况与上一样。可以说明，Activity的onTouchEvent对事件分发没有影响。

## 例子7：View的onTouchEvent的ACTION_DOWN返回true

在上面的基础上，将View的onTouchEvent的ACTION_DOWN返回true。

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

结果显示，View的onTouchEvent拦截了ACTION_DOWN，其余不拦截，那么，不会调用ViewGroup的onTouchEvent，而是直接调用Activity的onTouchEvent方法。此实验证明了结论5。

## 例子8

实验三将ouTouch的返回变为true，结果显示onTouchEvent不再调用。

## 例子9

之前的实验一直没有出现onClick的日志，查看源码发现onClick是在onTouchEvent中调用，如果不调用super方法，onClick会失效。如果给一个View设置了onClickListener，那么就会表示View是clickable的了，所以默认的onTouchEvent会返回true。

当View的onTouchEvent返回false，那么ViewGroup的onClick会被调用。

## 例子10：子View消费DOWN，其余不消费

```java
@Override
public boolean onTouchEvent(MotionEvent event) {
    Log.i(TAG, "onTouchEvent: " + AppHelper.toStringOfMotionEvent(event));
    return event.getAction() == MotionEvent.ACTION_DOWN;
}
```

```
I/TTE-MyViewGroup: dispatchTouchEvent: ACTION_DOWN
I/TTE-MyViewGroup: onInterceptTouchEvent: ACTION_DOWN
I/TTE-MyChildView: dispatchTouchEvent: ACTION_DOWN
I/TTE-MyChildView: onTouchEvent: ACTION_DOWN

I/TTE-MyViewGroup: dispatchTouchEvent: ACTION_MOVE
I/TTE-MyViewGroup: onInterceptTouchEvent: ACTION_MOVE
I/TTE-MyChildView: dispatchTouchEvent: ACTION_MOVE
I/TTE-MyChildView: onTouchEvent: ACTION_MOVE
I/TTE-MyActivity: onTouchEvent: ACTION_MOVE

I/TTE-MyViewGroup: dispatchTouchEvent: ACTION_UP
I/TTE-MyViewGroup: onInterceptTouchEvent: ACTION_UP
I/TTE-MyChildView: dispatchTouchEvent: ACTION_UP
I/TTE-MyChildView: onTouchEvent: ACTION_UP
I/TTE-MyActivity: onTouchEvent: ACTION_UP
```

结论：如果子View消费了ACTION_DOWN，后续事件会交给它处理。如果后续事件没有消费，那么直接交给Activity处理。

# 源码总结

>   说明：处理事件指调用了dispatchTouchEvent，消费事件指dispatchTouchEvent返回true。

## Activity部分

当一个手势事件产生后，先传递给Activity，Activity通过Window（PhoneWindow）来分发，而Window的展示实体是View（DecorView），那么手势事件进入View的分发体系。

如果所有View没有处理该手势事件，那么最终Activity来处理。

## ViewGroup部分

1.   对于一个ViewGroup来说，手势事件产生后，首先会传递给它，这时它的dispatchTouchEvent就会被调用。
     只有ACTION_DOWN（还有ACTION_POINTER_DOWN和ACTION_HOVER_MOVE，但是这里只讨论ACTION_DOWN）时才会遍历子View分发，如果有一个子View消费了该事件，将其加入到TouchTarget里，并停止分发。
     后续的事件遍历TouchTarget来分发。
2.   然后判断是否要拦截。
     判断拦截有前提，如果`actionMasked == MotionEvent.ACTION_DOWN || mFirstTouchTarget != null`。
     条件满足时，还要判断FLAG_DISALLOW_INTERCEPT标记是否被设置，这个标记位是通过`requestDisallowInterceptTouchEvent()`方法来设置的。这个标记位一旦设置后，ViewGroup就无法拦截除ACTION_DOWN以外的其他点击事件（因为在ACTION_DOWN时，mGroupFlags会被重置，所以disallowIntercept默认是false）。
3.   mFirstTouchTarget的意义：
     TouchTarget是ViewGroup的一个内部类。`mFirstTouchTarget`对象指向的是接受触摸事件的View所组成的链表的起始节点。也就是说，当事件由ViewGroup传递给子元素成功处理时，`mFirstTouchTarget`对象就会被赋值。
     如果拦截事件，`mFirstTouchTarget!=null`就不成立。此时如果事件序列中的ACTION_MOVE、ACTION_UP事件再传递过来时，由于`(actionMasked == MotionEvent.ACTION_DOWN || mFirstTouchTarget != null)`条件为false，就不会再调用`onInterceptTouchEvent()`方法，是否被拦截的标志变量也会设置为`intercepted = true`，并且后续同一事件序列的其他事件都会默认交给它处理。
4.   如果ViewGroup拦截了ACTION_DOWN，那么mFirstTouchTarget为null，不会分发给子View，而是调用自己的onTouchEvent。
5.   如果ViewGroup拦截了除了ACTION_DOWN的其它事件，那么将事件转为CANCEL分发给TouchTarget，并移除出TouchTarget。后续的事件则ViewGroup自己处理（onTouchEvent）。

dispatchTouchEvent的核心代码，所有的结论都可以在这里找到出处：

```java
public boolean dispatchTouchEvent(MotionEvent ev) {
    boolean handled = false;
    // 判断是否拦截
    final boolean intercepted;
    if (actionMasked == MotionEvent.ACTION_DOWN || mFirstTouchTarget != null) {
        // 在ACTION_DOWN时，mGroupFlags会被重置，所以disallowIntercept默认是false
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

    // 寻找需要消费事件的子View
    if (!intercepted) {
        if (actionMasked == MotionEvent.ACTION_DOWN
                || (split && actionMasked == MotionEvent.ACTION_POINTER_DOWN)
                || actionMasked == MotionEvent.ACTION_HOVER_MOVE) {
            for (int i = childrenCount - 1; i >= 0; i--) {
                if (dispatchTransformedTouchEvent(ev, false, child, idBitsToAssign)) {
                    break;
                }
            }
        }
    }

    if (mFirstTouchTarget == null) {
        // ViewGroup自己处理
        handled = dispatchTransformedTouchEvent(ev, canceled, null,
                TouchTarget.ALL_POINTER_IDS);
    } else {
        // 交给mFirstTouchTarget及其后面的target处理，这部分代码还是贴一下，有用。
        TouchTarget predecessor = null;
        TouchTarget target = mFirstTouchTarget;
        // 遍历TouchTarget链表，一般情况下就一个。
        while (target != null) {
            final TouchTarget next = target.next;
            // 如果已经处理过了，就不需要再次处理。
            if (alreadyDispatchedToNewTouchTarget && target == newTouchTarget) {
                handled = true;
            } else {// 如果还没处理
                // cancelChild的赋值涉及到了intercepted，如果子View消费了ACTION_DOWN，但是其它事件被父View拦截，那么子View的事件变成ACTION_CANCEL，并且mFirstTouchTarget移除该子View。
                final boolean cancelChild = resetCancelNextUpFlag(target.child)
                        || intercepted;
                if (dispatchTransformedTouchEvent(ev, cancelChild,
                        target.child, target.pointerIdBits)) {
                    handled = true;
                }
                if (cancelChild) {
                    if (predecessor == null) {
                        mFirstTouchTarget = next;
                    } else {
                        predecessor.next = next;
                    }
                    target.recycle();
                    target = next;
                    continue;
                }
            }
            predecessor = target;
            target = next;
        }
    }
    return handled;
}
```


如果onInterceptTouchEvent方法返回false（默认为false）就表示它不拦截当前事件，这时当前事件就会继续传递给它的子元素，接着子元素的dispatchTouchEvent方法就会被调用，如此反复直到事件被最终处理。

>   看结论其实有点绕，看上面的源码一清二楚。

## View部分

对于一个View来说，如果它设置了OnTouchListener，那么OnTouchListener中的onTouch方法会被回调。
如果onTouch返回false，则当前View的onTouchEvent方法会被调用；如果返回true，那么onTouchEvent方法将不会被调用。由此可见，给View设置的OnTouchListener，其优先级比onTouchEvent要高。
在onTouchEvent方法中，如果当前设置的有OnClickListener，那么它的onClick方法会被
调用。可以看出，平时用的OnClickListener，其优先级最低，即处于事件传递的尾端。

另外，如果一个View的onTouchEvent（ACTION_DOWN）返回false，那么它的父容器的onTouchEvent将会被调用，依此类推。如果所有的元素都不处理这个事件，那么这个事件将会最终传递给Activity处理。
如果非ACTION_DOWN返回了false，那么父容器不会调用自己的onTouchEvent，最终是由Activity处理。

# 简单总结

手势事件分发主要是dispatchTouchEvent、onInterceptTouchEvent、onTouchEvent。

## dispatchTouchEvent

dispatchTouchEvent用于分发事件，返回值表示是否消费此次事件。

当事件为ACTION_DOWN时，会遍历子View分发该事件，如果有子View消费了该事件，那么将子View加入到TouchTarget。

其余事件，会遍历TouchTarget来分发。

## onInterceptTouchEvent

onInterceptTouchEvent用于拦截事件，只有ViewGroup才有。

当事件为ACTION_DOWN或者TouchTarget不为空时才会判断，在此基础上，还会判断FLAG_DISALLOW_INTERCEPT标记是否被设置，这个标记位是通过`requestDisallowInterceptTouchEvent()`方法来设置的。这个标记位一旦设置后，ViewGroup就无法拦截除ACTION_DOWN以外的其他点击事件（因为在ACTION_DOWN时，mGroupFlags会被重置，所以disallowIntercept默认是false）。

如果选择拦截：

1.   如果没有TouchTarget，那么调用ViewGroup自身的onTouchEvent。
2.   如果有TouchTarget，那么会转为ACTION_CANCEL事件分发给该子View，并移除该TouchTarget。注意此次事件期间，ViewGroup不会调用自身的onTouchEvent。后续的事件才会。

## onTouchEvent

处理手势逻辑。

1.   存在OnTouchListener，调用OnTouchListener中的onTouch方法。
2.   如果onTouch返回false，则调用View的onTouchEvent方法。如果返回true，那么onTouchEvent方法将不会被调用。
3.   在onTouchEvent方法中，如果当前设置的有OnClickListener，那么它的onClick方法会被
     调用。

由此可见，给View设置的OnTouchListener，其优先级比onTouchEvent要高。OnClickListener，其优先级最低，即处于事件传递的尾端。

如果一个View的onTouchEvent（ACTION_DOWN）返回false，那么它的父容器的onTouchEvent将会被调用，依此类推。如果所有的元素都不处理这个事件，那么这个事件将会最终传递给Activity处理。

如果一个View的非ACTION_DOWN返回了false，那么父容器不会调用自己的onTouchEvent，最终是由Activity处理。
注意，这条和拦截有点区别。后续的事件还会传到子View中，子View并没有从TouchTarget中移除。（见例子10）

# 几个结论

1. 同一个事件序列是指从手指接触屏幕的那一刻起，到手指离开屏幕的那一刻结束，在这个过程中所产生的一系列事件，这个事件序列以down事件开始，中间含有数量不定的move事件，最终以up事件结束。
2. 正常情况下，一个事件序列只能被一个View拦截且消耗。这条的原因可以参考 （3），因为一旦一个元素拦截了某此事件，那么同一个事件序列内的所有事件都会直接交给它处理，因此同一个事件序列中的事件不能分别由两个View同时处理，但是通过特殊手段可以做到，比如一个View将本该自己处理的事件通过onTouchEvent强行传递给其他View处理。
3. 某个View一旦决定拦截，那么这一个事件序列都只能由它来处理（如果事件序列能够传递给它的话），并且它的onInterceptTouchEvent不会再被调用（View.java没有onInterceptTouchEvent方法）。就是说当一个View决定拦截一个事件后， 那么系统会把同一个事件序列内的其他方法都直接交给它来处理，因此就不用再调用这个View的onInterceptTouchEvent去询问它是否要拦截了。
4. 某个View一旦开始处理事件， 如果它不消耗ACTION_DOWN事件（onTouchEvent返回了false）， 那么同一事件序列中的其他事件都不会再交给它来处理；并且事件将重新交由它的父元素去处理，即父元素的onTouchEvent会被调用。意思就是事件一旦交给一个View处理，那么它就必须消耗掉，否则同一事件序列中剩下的事件就不再交给它来处理了。
5. 如果View不消耗除ACTION_DOWN以外的其他事件，那么这个点击事件会消失，此时父元素的onTouchEvent并不会被调用，并且当前View可以持续收到后续的事件，最终这些消失的点击事件会传递给Activity处理。
6. ViewGroup默认不拦截任何事件，Android源码中ViewGroup的onInterceptTouchEvent方法默认返回false。
7. View没有onInterceptTouchEvent方法，一旦有点击事件传递给它，那么它的onTouchEvent方法就会被调用。
8. View的onTouchEvent默认都会消耗事件（返回true）除非它是不可点击的（clickable和longClickable同时为false）。 View的longClickable属性默认都为false， clickable属性要分情况，比如Button的clickable属性默认为true，而TextView的clickable属性默认为false。
9. View的enable属性不影响onTouchEvent的默认返回值。哪怕个View是disable状态的，只要它的clickable或者longClickable有一个为true，那么它的onTouchEvent就返true。
10. onClick会发生的前提是当前View是可点击的，并且它收到了down和up的事件。
11. 事件传递过程是由外向内的，即事件总是先传递给父元素，然后再由父元素分发给子View，通过requestDisallowInterceptTouchEvent方法可以在子元素中干预父元素的事件分发过程，但是ACTION_DOWN事件除外。 

# 滑动冲突

内外两层同时可以滑动，这个时候就会产生滑动冲突。

## 常见的滑动冲突场景

1. 外部滑动方向和内部滑动方向不一致
2. 外部滑动方向和内部滑动方向一致
3. 上面两种情况的嵌套

## 滑动冲突的处理规则

对于场景1：当用户左右滑动的时候，需要让外部的View拦截点击事件，当用户上下滑动时，需要让内部View拦截事件。

对于场景2：当手指开始滑动的时候，系统无法知道用户到底是想让哪一层滑动，所以当手指滑动的时候就会出现问题，要么只有一层能滑动，要么就是内外两层都滑动，最终的效果取决于产品效果。

## 滑动冲突的解决方式

两种方式：**外部拦截法**、**内部拦截法**。

### **外部拦截法**

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

### **内部拦截法**

是指父容器默认拦截除ACTION_DOWN以外所有事件，所有的事件都传递给子元素，如果子元素需要此事件就直接消耗掉，否则就交由父容器进行处理，这种方法和Android分发机制不一致，需要配合requestDisallowInterceptTouchEvent方法才能正常工作，使用比较复杂。

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

### 内部拦截法demo

```java
class MyTestLinearLayout extends LinearLayout {
    @Override
    public boolean onInterceptTouchEvent(MotionEvent ev) {
        Log.i(TAG, "onInterceptTouchEvent: " + AppHelper.toStringOfMotionEvent(ev));
        return ev.getAction() != MotionEvent.ACTION_DOWN;
    }
}
```

```java
class MyTestTextView extends androidx.appcompat.widget.AppCompatTextView {
    @Override
    public boolean onTouchEvent(MotionEvent event) {
        Log.i(TAG, "onTouchEvent: " + AppHelper.toStringOfMotionEvent(event));
        switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN:
                getParent().requestDisallowInterceptTouchEvent(true);
                break;
            case MotionEvent.ACTION_MOVE: {
                getParent().requestDisallowInterceptTouchEvent(false);
                break;
            }
            default:
                break;
        }
        return true;
    }
}
```

```
I/TTE-MyViewGroup: dispatchTouchEvent: ACTION_DOWN
I/TTE-MyViewGroup: onInterceptTouchEvent: ACTION_DOWN
I/TTE-MyChildView: dispatchTouchEvent: ACTION_DOWN
I/TTE-MyChildView: onTouchEvent: ACTION_DOWN

I/TTE-MyViewGroup: dispatchTouchEvent: ACTION_MOVE
I/TTE-MyChildView: dispatchTouchEvent: ACTION_MOVE
I/TTE-MyChildView: onTouchEvent: ACTION_MOVE

I/TTE-MyViewGroup: dispatchTouchEvent: ACTION_MOVE
I/TTE-MyViewGroup: onInterceptTouchEvent: ACTION_MOVE
I/TTE-MyChildView: dispatchTouchEvent: MotionEvent { action=ACTION_CANCEL, actionButton=0, id[0]=0, x[0]=553.0, y[0]=239.0, toolType[0]=TOOL_TYPE_FINGER, buttonState=0, classification=NONE, metaState=0, flags=0x40000, edgeFlags=0x0, pointerCount=1, historySize=0, eventTime=24875373, downTime=24875128, deviceId=5, source=0x1002, displayId=0, eventId=136834927 }
I/TTE-MyChildView: onTouchEvent: MotionEvent { action=ACTION_CANCEL, actionButton=0, id[0]=0, x[0]=553.0, y[0]=239.0, toolType[0]=TOOL_TYPE_FINGER, buttonState=0, classification=NONE, metaState=0, flags=0x40000, edgeFlags=0x0, pointerCount=1, historySize=0, eventTime=24875373, downTime=24875128, deviceId=5, source=0x1002, displayId=0, eventId=136834927 }

I/TTE-MyViewGroup: dispatchTouchEvent: ACTION_MOVE
I/TTE-MyViewGroup: onTouchEvent: ACTION_MOVE

I/TTE-MyViewGroup: dispatchTouchEvent: ACTION_MOVE
I/TTE-MyViewGroup: onTouchEvent: ACTION_MOVE

I/TTE-MyViewGroup: dispatchTouchEvent: ACTION_UP
I/TTE-MyViewGroup: onTouchEvent: ACTION_UP
```

结论：requestDisallowInterceptTouchEvent的那一个事件并不会立即调用Parent的onTouchEvent，而是要等到下一次事件。（不过外部拦截法也不会，见例子10）

## 两者区别

个人认为：

1. 外部滑动方向和内部滑动方向不一致：
    可以用外部拦截法和内部拦截法。
2. 外部滑动方向和内部滑动方向一致：
    如果使用外部拦截法，因为方向一致，那么父View的onInterceptTouchEvent方法只能返回false，因为一旦拦截，那么子View就无法执行了。
    只能使用内部拦截法，在子View的onTouchEvent里处理事件，但不消费事件（除了ACTION_DOWN），另外再配合requestDisallowInterceptTouchEvent，可以做到父View处理事件，