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

# Surface相关

## SurfaceView

[SurfaceView官方介绍](https://source.android.com/docs/core/graphics/arch-sv-glsv?hl=zh-cn)

```
public class SurfaceView extends View implements ViewRootImpl.SurfaceChangedCallback
```

1.   SurfaceView继承了View类，可以嵌入到 View 层次结构中。
2.   SurfaceView 的内容是透明的，因为SurfaceView有一个单独的Surface，独立于主线程的Surface，可以在子线程中单独渲染。
3.   当使用外部缓冲区来源（例如 GL 上下文和媒体解码器）进行渲染时，需要从缓冲区来源复制缓冲区，以便在屏幕上显示这些缓冲区。为此，可以使用 SurfaceView。
4.   网上说SurfaceView不支持平移，缩放，旋转等动画，但是经个人测试，在android11手机上可以执行这些操作。

## GLSurfaceView

```
public class GLSurfaceView extends SurfaceView implements SurfaceHolder.Callback2
```

GLSurfaceView继承了SurfaceView，具有SurfaceView的特性。除此之外，GLSurfaceView 会创建一个渲染线程，并在线程上配置 EGL 上下文。

可以理解为：GLSurfaceView是带有gl环境的SurfaceView。

## SurfaceTexture

[SurfaceTexture官方介绍](https://source.android.com/docs/core/graphics/arch-st?hl=zh-cn)

基本使用：

1.   OpenGl创建Texture并返回textureId。
2.   通过textureId来创建SurfaceTexture。
3.   生产Buffer
4.   SurfaceTexture会回调onFrameAvailable，并在其中调用updateTexImage释放Buffer。这样OpenGl可以将此Buffer作为外部纹理使用。

生产Buffer的一种方式：

1.   通过这个SurfaceTexture来创建一个Surface。
2.   再通过这个Surface的lockCanvas和unlockCanvas来生产Buffer。

## TextureView

[TextureView官方介绍](https://source.android.com/docs/core/graphics/arch-tv?hl=zh-cn)

TextureView封装了SurfaceTexture，当外层生产了Buffer，TextureView在onFrameAvailable回调中调用View的invalidate。

View的invalidate会触发TextureView的draw方法。

1.   一般的View通过draw方法的Canvas来生产Buffer，而TextureView并直接没有使用Canvas，而是通过TextureLayer绘制的。
2.   TextureView的绘制需要硬件渲染。因为draw方法判断了`canvas.isHardwareAccelerated()`

## SurfaceView和TextureView的区别

两者的介绍见上，从介绍中可以看出区别。

SurfaceView的性能较好，因为可以单独渲染。而TextureView需要将Buffer合到主线程中，再通过主线程渲染。

