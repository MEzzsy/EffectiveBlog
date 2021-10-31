# 主要流程

## Activity的创建

1.   在Activity创建过程中，会创建一个Window，该Window由WindowManager进行管理。
2.   Window是以View的形式存在的，对Window的操作本质是对View的操作。对Window的操作会通过IPC与WMS进程通信。
3.   在WM的addView时会创建ViewRootImpl，ViewRootImpl用来管理整个View树，比如触发View的测量、布局和绘制（requestLayout）。

## View的绘制流程

1.   在ViewRootImpl的requestLayout中会触发经典的performTraversals，在performTraversals中会调用会调用performMeasure、performLayout、performDraw触发View的绘制。
2.   Android中Window、Surface、View的关系：Window相当于一个画框、Surface相当于一个画布，而View相当于绘制的图形。

## Surface的操作

1.   在ViewRootImpl的performTraversals中会调用relayoutWindow从Native层获取一个新的Surface。
2.   在ViewRootImpl的performTraversals的draw方法里，会调用Surface的lockCanvas和unlockCanvasAndPost。lockCanvas用于获取buffer，而unlockCanvasAndPost释放buffer。
3.   buffer和Canvas绑定，对Canvas的操作就是填充buffer。这部分逻辑由draw来完成（TODO）。

## Layer的创建

1.   addWindow过程中，应用进程会和WMS建立通信，而WMS会和SF进程通信。
2.   在WMS创建一个新的Surface时，会通过IPC在SF进程创建一个Layer。
3.   Layer的类型有很多，以BufferQueueLayer为例，在创建BufferQueueLayer期间，会创建一个BufferQueue，一个生产者IGraphicBufferProducer，一个消费者IGraphicBufferConsumer。

## BufferQueue的循环

