# BufferQueue

frameworks/native/libs/gui/include/gui/IGraphicBufferProducer.h

客户端类型：BpGraphicBufferProducer （代码也在IGraphicBufferProducer.cpp中）

```cpp
virtual status_t dequeueBuffer(int* buf, sp<Fence>* fence, uint32_t width, uint32_t height, PixelFormat format, uint64_t usage, uint64_t* outBufferAge, FrameEventHistoryDelta* outTimestamps) {
    Parcel data, reply;
    bool getFrameTimestamps = (outTimestamps != nullptr);
	data.writeInterfaceToken(IGraphicBufferProducer::getInterfaceDescriptor());
    data.writeUint32(width);
    data.writeUint32(height);
    data.writeInt32(static_cast<int32_t>(format));
    data.writeUint64(usage);
    data.writeBool(getFrameTimestamps);

    status_t result = remote()->transact(DEQUEUE_BUFFER, data, &reply);
    // 。。。
    result = reply.readInt32();
    return result;
}
```

通过Binder传输到SurfaceFlinger进程中。

服务端类型：BnGraphicBufferProducer （代码也在IGraphicBufferProducer.cpp中）

```cpp
status_t BnGraphicBufferProducer::onTransact(uint32_t code, const Parcel& data, Parcel* reply, uint32_t flags) {
    switch(code) {
        // ...
        case DEQUEUE_BUFFER: {
            // ...
            // 在服务进程中调用了dequeueBuffer
            int result = dequeueBuffer(&buf, &fence, width, height, format, usage, &bufferAge, getTimestamps ? &frameTimestamps : nullptr);
            // ...
            reply->writeInt32(result);
            return NO_ERROR;
        }
        // ...
    }
}
```

最终调用了BufferQueueProducer的dequeueBuffer
frameworks/native/libs/gui/BufferQueueProducer.cpp

```cpp
status_t BufferQueueProducer::dequeueBuffer(int* outSlot, sp<android::Fence>* outFence, uint32_t width, uint32_t height, PixelFormat format, uint64_t usage, uint64_t* outBufferAge, FrameEventHistoryDelta* outTimestamps) {
    // ...

    status_t returnFlags = NO_ERROR;
    EGLDisplay eglDisplay = EGL_NO_DISPLAY;
    EGLSyncKHR eglFence = EGL_NO_SYNC_KHR;
    bool attachedByConsumer = false;

    { // Autolock scope
        //. ..
        int found = BufferItem::INVALID_BUFFER_SLOT;
        while (found == BufferItem::INVALID_BUFFER_SLOT) {
            //1. 寻找可用的Slot，可用指Buffer状态为FREE
            status_t status = waitForFreeSlotThenRelock(FreeSlotCaller::Dequeue, lock, &found);
			// ...
            const sp<GraphicBuffer>& buffer(mSlots[found].mGraphicBuffer);
			// ...
        }

        const sp<GraphicBuffer>& buffer(mSlots[found].mGraphicBuffer);
        // ...
        *outSlot = found;
        // 。。。
		//2.找到可用的Slot，将Buffer状态设置为DEQUEUED，由于步骤1找到的Slot状态为FREE，因此这一步完成了FREE到DEQUEUED的状态切换
        mSlots[found].mBufferState.dequeue();

        // //3. 找到的Slot如果需要申请GraphicBuffer，则申请GraphicBuffer，这里采用了懒加载机制，如果内存没有申请，申请内存放在生产者来处理
        if ((buffer == nullptr) ||
                buffer->needsReallocation(width, height, format, BQ_LAYER_COUNT, usage))
        {
            mSlots[found].mAcquireCalled = false;
            mSlots[found].mGraphicBuffer = nullptr;
            mSlots[found].mRequestBufferCalled = false;
            mSlots[found].mEglDisplay = EGL_NO_DISPLAY;
            mSlots[found].mEglFence = EGL_NO_SYNC_KHR;
            mSlots[found].mFence = Fence::NO_FENCE;
            mCore->mBufferAge = 0;
            mCore->mIsAllocating = true;

            returnFlags |= BUFFER_NEEDS_REALLOCATION;
        } else {
            // We add 1 because that will be the frame number when this buffer
            // is queued
            mCore->mBufferAge = mCore->mFrameCounter + 1 - mSlots[found].mFrameNumber;
        }
        // ...
    }
	// ...
    return returnFlags;
}
```

关键在于寻找可用Slot，waitForFreeSlotThenRelock的流程如下：

```cpp
status_t BufferQueueProducer::waitForFreeSlotThenRelock(FreeSlotCaller caller, std::unique_lock<std::mutex>& lock, int* found) const {
    auto callerString = (caller == FreeSlotCaller::Dequeue) ?
            "dequeueBuffer" : "attachBuffer";
    bool tryAgain = true;
    while (tryAgain) {
        // ...

        //1. mQueue 是否太多
        const int maxBufferCount = mCore->getMaxBufferCountLocked();
        bool tooManyBuffers = mCore->mQueue.size()
                            > static_cast<size_t>(maxBufferCount);
        if (tooManyBuffers) {
            // ...
        } else {
            // 2. 先查找mFreeBuffers中是否有可用的，mFreeBuffers中的元素关联了GraphicBuffer，直接可用
            if (mCore->mSharedBufferMode && mCore->mSharedBufferSlot !=
                    BufferQueueCore::INVALID_BUFFER_SLOT) {
                *found = mCore->mSharedBufferSlot;
            } else {
                if (caller == FreeSlotCaller::Dequeue) {
                    // If we're calling this from dequeue, prefer free buffers
                    int slot = getFreeBufferLocked();
                    if (slot != BufferQueueCore::INVALID_BUFFER_SLOT) {
                        *found = slot;
                    } else if (mCore->mAllowAllocation) {
                        *found = getFreeSlotLocked();
                    }
                } else {
                    // If we're calling this from attach, prefer free slots
                    int slot = getFreeSlotLocked();
                    if (slot != BufferQueueCore::INVALID_BUFFER_SLOT) {
                        *found = slot;
                    } else {
                        *found = getFreeBufferLocked();
                    }
                }
            }
        }

        // If no buffer is found, or if the queue has too many buffers
        // outstanding, wait for a buffer to be acquired or released, or for the
        // max buffer count to change.
        tryAgain = (*found == BufferQueueCore::INVALID_BUFFER_SLOT) ||
                   tooManyBuffers;
        if (tryAgain) {
            // Return an error if we're in non-blocking mode (producer and
            // consumer are controlled by the application).
            // However, the consumer is allowed to briefly acquire an extra
            // buffer (which could cause us to have to wait here), which is
            // okay, since it is only used to implement an atomic acquire +
            // release (e.g., in GLConsumer::updateTexImage())
            if ((mCore->mDequeueBufferCannotBlock || mCore->mAsyncMode) &&
                    (acquiredCount <= mCore->mMaxAcquiredBufferCount)) {
                return WOULD_BLOCK;
            }
            if (mDequeueTimeout >= 0) {
                std::cv_status result = mCore->mDequeueCondition.wait_for(lock,
                        std::chrono::nanoseconds(mDequeueTimeout));
                if (result == std::cv_status::timeout) {
                    return TIMED_OUT;
                }
            } else {
                mCore->mDequeueCondition.wait(lock);
            }
        }
    } // while (tryAgain)

    return NO_ERROR;
}
```

# SurfaceFlinger分析

## SurfaceFlinger进程的启动

>   和书中说的不同，SurfaceFlinger单独放在了一个进程。
>
>   参考：[surfaceflinger 进程启动](https://blog.csdn.net/u012439416/article/details/79733178)

surfaceflinger进程对应的配置不是在init.rc中，而是在surfaceflinger.rc中，对应的main文件：frameworks/native/services/surfaceflinger/main_surfaceflinger.cpp

```cpp
int main(int, char**) {
    // ...
    // 创建SurfaceFlinger对象，SurfaceFlinger的构造函数里没有复杂逻辑
    // instantiate surfaceflinger
    sp<SurfaceFlinger> flinger = surfaceflinger::createSurfaceFlinger();
    
    // ...
    // 执行SurfaceFlinger的init函数，init函数也没有复杂逻辑
    // initialize before clients can connect
    flinger->init();
    
    // 添加系统服务
    // publish surface flinger
    sp<IServiceManager> sm(defaultServiceManager());
    sm->addService(String16(SurfaceFlinger::getServiceName()), flinger, false,
                   IServiceManager::DUMP_FLAG_PRIORITY_CRITICAL | IServiceManager::DUMP_FLAG_PROTO);
    
    // 执行SurfaceFlinger的run函数
    // ...
    // run surface flinger in this thread
    flinger->run();
    return 0;
}
```

frameworks/native/services/surfaceflinger/SurfaceFlinger.cpp

在SurfaceFlinger的其他方法之前，onFirstRef方法会被调用，onFirstRef方法如下：

```cpp
void SurfaceFlinger::onFirstRef() {
    mEventQueue->init(this);
}
```

```cpp
void MessageQueue::init(const sp<SurfaceFlinger>& flinger) {
    mFlinger = flinger;
    mLooper = new Looper(true);
    mHandler = new Handler(*this);
}
```

创建了类似Android Java层中Handler的一套消息机制，最后调用SurfaceFlinger的run函数等待消息。

```cpp
void SurfaceFlinger::run() {
    while (true) {
        mEventQueue->waitMessage();
    }
}
```

小结：

SurfaceFlinger的启动主要是这几步：

1.   启动SurfaceFlinger进程。
2.   创建SurfaceFlinger对象。
3.   调用SurfaceFlinger的init函数。
4.   调用SurfaceFlinger的run函数，等待Message。





8。5。2SF工作线程分析
SF中的工作线程就是用来做图像混合的，比起AudioFlinger来，它相当简单，下面是
它的代码：
[-->SurfaceFlinger。cpp]
boolSurfaceFlinger：：threadLoop()
{
waitForEvent();//①等待什么事件呢?
if(UNLIKELY(mConsoleSignals)){
handleConsoleEvents();
}
if(LIKELY(mTransactionCount==0)){
constuint32_tmask=eTransactionNeeded|eTraversalNeeded;
uint32_ttransactionFlags
if(LIKELY(transactionFlags)){
7/Transaction(事务)处理，放到本节最后来讨论。
handleTransaction(transactionFlags);
}
}
getTransactionFlags(mask);
//®*PageFlippingI#。
handlePageFlip();
constDisplayHardware&hw(graphicPlane(0)。displayHardware());
if(LIKELY(hw。canDraw()
&&!isFrozen())){
1/③处理重绘。
handleRepaint();
hw。compositionComplete();
//@BackBuffer。
unlockClients();
postFramebuffer();
}else{
unlockClients();
usleep(16667);
}
returntrue;
}
ThreadLoop一共有四个关键点(即①~④)，这里分析除Transaction外的三个关键点。
1。waitForEvent
SF工作线程一上来就等待事件，那会是什么事件呢?来看代码：
[-->SurfaceFlinger。cpp}
voidSurfaceFlinger：：waitForEvent()


Page378
360
深入理解Android：卷」
{
while(true){
nsecsttimeout=-1;
constnsecs_tfreezeDisplayTimeout=ms2ns(5000);
MessageList：：value_typemsg=mĒventQueue。waitMessage(timeout);
1/还有一些和冻屏相关的内容。
if(msg!=0){
switch(msg->what){
1/千辛万苦就等这一个重绘消息。
caseMessageQueue：：INVALIDATE：
return;
}
}
}
SF收到重绘消息后，将退出等待。那么，是谁发送的这个重绘消息呢?还记得在
unlockCanvasAndPost函数中调用的signal吗?它在SF端的实现代码如下：
[-->SurfaceFlinger]
voidSurfaceFlinger：：signal()const{
const_cast<SurfaceFlinger*>(this)->signalEvent();
}
voidSurfaceFlinger：：signalEvent({
mEventQueue。invalidate();//à%&ElPINVALIDATE。
}
2。handlePageFlipA
SF工作线程从waitForEvent中返回后，下一步要做的就是处理事务和handlePageFlip
了。先看handlePageFlip，从名字上可知，它和PageFlipping工作有关。
注意事务处理将在8。5。3节中介绍。
代码如下所示：
(->SurfaceFlinger。cpp]
voidSurfaceFlinger：：handlePageFlip()
{
boolvisibleRegions
mVisibleRegionsDirty;
/*
还记得前面所说的mCurrentState吗?它保存了所有显示层的信息，而绘制的时候使用的
mDrawingstate则保存了当前需要显示的显示层信息。
*/


Page379
第8章深入理解Surface系统
361
LayerVector&currentLayers
%3D
const_cast<LayerVector&>(mDrawingState。layersSortedByZ);
//OAAlockPageFlip。
visibleRegions|=lockPageFlip(currentLayers);
graphicPlane(0)。displayHardware();
constDisplayHardware&hw=
1/取得屏幕的区域。
constRegionscreenRegion(hw。bounds());
if(visibleRegions){
RegionopaqueRegion;
computeVisibleRegions(currentLayers，mDirtyRegion，opaqueRegion);
mWormholeRegion
mVisibleRegionsDirty
}
screenRegion。subtract(opaqueRegion);
%3D
false;
%3D
//®unlockPageFlip。
unlockPageFlip(currentLayers);
mDirtyRegion。andSelf(screenRegion);
}
hanldePageFlip调用了两个看起来是一对的函数：lockPageFlip和unlockPageFlip。这两
个函数会干些什么呢?
(1)lockPageFlip
先看lockPageFlip函数，代码如下所示：
[-->SurfaceFlinger。cpp]
boolSurfaceFlinger：：lockPageFlip(constLayerVector&currentLayers)
{
boolrecomputeVisibleRegions
=false;
size_tcount=
currentLayers。size();
currentLayers。array();
sp<LayerBase>const*layers
for(size_ti=0;i<count;i++){
%3D
constsp<LayerBase>&layer
layers[i];
%3D
1/调用每个显示层的lockPageFlip。
layer->lockPageFlip(recomputeVisibleRegions);
}
returnrecomputeVisibleRegions;
}
假设当前的显示层是Layer类型，那么得转到Layer类去看它的lockPageFlip函数了，
代码如下所示：
[-->Layer。cpp]
voidLayer：：lockPageFlip(bool&recomputeVisibleRegions)
{
//1cblkSharedBufferServer，retireAndLockh*eFrontBuffertj
1/索引号。
ssizetbuf=1cblk->retireAndLock();


Page380
362
深入理解Android：卷!
mFrontBufferIndex=buf;
//FrontBufferGraphicBuffer。
sp<GraphicBuffer>newFrontBuffer(getBuffer(buf)};
if(newFrontBuffer!=NULL){
1/取出脏区域。
constRegiondirty(lcblk->getDirtyRegion(buf));
1/和GraphicBuffer所表示的区域进行裁剪，得到一个脏区域。
mPostedDirtyRegion
dirty。intersect(newFrontBuffer->getBounds());
%3D
constLayer：：State&front(drawingState());
front。requested_w&&e
==front。requested_h)
if(newFrontBuffer->getWidth()
newFrontBuffer->getHeight()
{
if((front。w!=front。requested_w)||
(front。h!=front。requested_h))
{
1/需要重新计算可见区域。
recomputeVisibleRegions
=true;
}
mFreezeLock。clear(;
}
}else{
mPostedDirtyRegion。clear();
}
if(lcblk->getQueuedCount()){
MFlinger->signalEvent();
如果脏区域不为空，则需要绘制成纹理，reloadTexture将绘制一张纹理保存在
mTextures数组中，里边涉及很多OpenGL的操作，读者有兴趣可以自己研究。
*/
if(!mPostedDirtyRegion。isEmpty()){
reloadTexture(mPostedDirtyRegion);
}
}
我们知道，Layer的lockPageFlip将根据FrontBuffer的内容生成一张纹理。那么，
unlockPageFlip会做些什么呢?
(2)unlockPageFlip
unlockPageFlip的代码如下所示：
[-->SurfaceFlinger。cpp]
voidSurfaceFlinger：：unlockPageFlip(constLayerVector&currentLayers)
{
constGraphicPlane&plane(graphicPlane(0));
constTransform&planeTransform(plane。transform());


Page381
第8章深入理解Surface系统
363
size_tcount=currentLayers。size();
sp<LayerBase>const*layers
=currentLayers。array();
for(sizeti=0;i<count;i++){
layers[i];
constsp<LayerBase>&layer
1/调用每个显示层的unlockPageFlip，Layer的unlockPageFlip主要做一些
1/区域的清理工作，读者可以自己看看。
layer->unlockPageFlip(planeTransform，mDirtyRegion);
}
(3)关于handiePageFlip的总结
handlePageFlip的工作其实很简单，以Layer类型为例来总结一下：
各个Layer需要从FrontBuffer中取得新数据，并生成一张OpenGL中的纹理。纹理可
以看做是一个图片，这个图片的内容就是FrontBuffer中的图像。
现在每一个Layer都准备好了新数据，下一步的工作当然就是绘制了。来看
handleRepaintA。
3。handleRepainta
handleRepaint函数的代码如下所示：
[-->SurfaceFlinger。cpp]
voidSurfaceFlinger：：handleRepaint()
{
mInvalidRegion。orself(mDirtyRegion);
if(mInvalidRegion。isEmpty()){
return;
}
constDisplayHardware&hw(graphicPlane(0)。displayHardware());
glMatrixMode(GL_MODELVIEW);
glLoadIdentity();
uint32_tflags
hw。getFlags();
if((flags&DisplayHardware：：SWAP_RECTANGLE)||
(flags&DisplayHardware：：BUFFER_PRESERVED))
{
-//it#mDirtyRegion。
}
1/在脏区域上进行绘制。
composeSurfaces(mDirtyRegion);
mDirtyRegion。clear();
}
其中，composeSurfaces将不同的显示层内容进行混合，其实就是按Z轴的顺序由里到


Page382
364
深入理解Android：卷!
外依次绘制。当然，最后绘制的数据有可能遮盖前面绘制的数据，代码如下所示：
[-->SurfaceFlinger。cpp]
voidSurfaceFlinger：：composeSurfaces(constRegion&dirty)
{
constSurfaceFlinger&flinger(*this);
constLayerVector&drawingLayers(mDrawingState。layersSortedByZ);
constsize_tcount
drawingLayers。size();
sp<LayerBase>const*constlayers
drawingLayers。array();
%3D
for(size_ti=0;i<count;++i){
constsp<LayerBase>&layer
layers(i];
constRegion&visibleRegion(layer->visibleRegionScreen);
if(!visibleRegion。isEmpty())
constRegionclip(dirty。intersect(visibleRegion));
if(!clip。isEmpty()){
layer->draw(clip);//调用各个显示层的1ayer函数。
}
}
}
}
draw函数在LayerBase类中实现，代码如下所示：
[-->LayerBase。cpp]
voidLayerBase：：draw(constRegion&inclip)const
{
glEnable(GL_SCISSOR_TEST);
onDraw(clip);//onDraw。
}
至于Layer是怎么实现这个onDraw函数的，代码如下所示：
[-->Layer。cpp]
voidLayer：：onDraw(constRegion&clip)const
{
intindex=mFrontBufferIndex;
if(mTextures[index]。image
==EGL_NO_IMAGE_KHR)
index
0;
GLuinttextureName
=mTextures[index)。name;
Regionholes(clip。subtract(under));
if(!holes。isEmpty()){
clearwithOpenGL(holes);
}
return;
}
1/index是FrontBuffer对应生成的纹理，在lockPageFlip函数中就已经生成了。


Page383
第8章深入理解Surface系统
365
drawwithOpenGL(clip，mTextures[index]);//将纹理画上去，里面有很多和OpenGL相关的内容。
}
drawWithOpenGL函数由LayerBase实现，看它是不是使用了这张纹理，代码如下所示：
[-->LayerBase。cpp]
voidLayerBase：：drawWithOpenGL(constRegion&clip，constTexture&texture)const
{
constDisplayHardware&hw(graphicPlane(0)。displayHardware());
constuint32_tfbHeight
constState&s(drawingState());
hw。getHeight();
%3D
1/validateTexture函数内部将绑定指定的纹理。
validateTexture(texture。name);
7/下面就是OpenGL操作函数了。
glEnable(GL_TEXTURE_2D);
glMatrixMode(GL_TEXTURE);
glLoadIdentity();
1/坐标旋转。
switch(texture。transform){
caseHAL_TRANSFORM_ROT_90：
glTranslatef(0，1，0);
glRotatef(-90，0，0，1);
break;
caseHAL_TRANSFORM_ROT_180：
glTranslatef(1，1，0);
glRotatef(-180，0，0，1);
break;
caseHAL_TRANSFORM_ROT_270：
glTranslatef(1，0，0);
glRotatef(-270，0，0，1);
break;
}
if(texture。NPOTAdjust){
1/编放处理。
glScalef(texture。wScale，texture。hScale，1。0f);
1/使能纹理坐标
glEnableClientState(GL_TEXTURE_COORD_ARRAY);
1/设置顶点坐标。
glVertexPointer(2，GL_FIXED，0，mVertices);
1/设置纹理坐标。
glTexCoordPointer(2，GL_FIXED，0，texCoords);


Page384
366
深入理解Android：卷!
while(it!=end){
constRect&r
=*it++;
r。height());
constGLintsy=fbHeight
1/裁剪。
glscissor(r。left，sy，r。width(0，r。height());
1/画矩形。
(r。top+
glDrawArrays(GL_TRIANGLE_FAN，
}
1/禁止纹理坐标。
glDisableClientState(GL_TEXTURE_COORDARRAY);
}
0，4);
纹理绑定是OpenGL的常用函数，其代码如下所示。
[-->LayerBase。cpp]
voidLayerBase：：validateTexture(GLinttextureName)
{
/下面这个函数将绑定纹理。
glBindTexture(GL_TEXTURE_2D，textureName);
const
//其他一些设置
}
handleRepaint这个函数基本上就是按Z轴的顺序对每一层进行重绘，重绘的方法就是使
用OPENGL。
注意我在Android平台上有几个月的OpenGL开发经历，还该不上很深刻，不过整理了一
些资料，希望能够给感兴趣的读者提供参考。
1)OpenGL的入门教材当选NeHe的资料，大喀看前几章即可。
2)Android平台上关于OpenGLES的开发，有一篇很详细的Word文档叫《OpenGL
ESTutorialforAndroid》。该文详细地描述了在Android平台上进行OpenGL开发的流程。大
家可跟着这篇教材，在模拟器上做一些练习。那里面所涉及的一些基础知识，可从前面介绍
的入门教材中学到。
3)有了前面两点的基础后，就需要对整个OpenGL有比較完整深入的了解了。我在那
时所看的书是《OpenGLProgrammingGuide(7thEdition)》。该书很厚，有1000多页。里面
有一些内容可能与工作无关，只要大概知道有那回事就行了，暂时不必深入学习，等需要时
再进一步学习并运用。我在开发的项目中曾用到的光照、雾化等效果，都是之前先知道有这
个东西，后来在项目中才逐漸学习运用的。
4)嵌入式平台上用的其实是OpenGLES。这里，还有一本书叫《OpenGLES2。0
ProgrammingGuide》，它介绍了OpenGLES的开发，读者可认真学习。
5)在AndroidSDK文档中，对OpenGLAPI的描述只有家寥数语。怎么办?不过，由
于它使用了J2ME中的javax。microedition。khronos。opengles包，所以J2ME的SDK文档中对
OpenGL的API有着非常详细的描述，读者手头应该要有一个J2ME的文档。


Page385
第8章深入理解Surface系统
367
6)如果想做深入开发，就不得不学习计算机图形学了。我后来买了书，可惜没时间学了。
4。unlockClients1postFrameBufferT
在绘制完图后，还有两项工作需要做，一个涉及unlockClients函数，另外一个涉及
postFrameBuffer函数，这两个函数分别干了什么呢?unlockClients的代码如下所示：
[-->SurfaceFlinger。epp]
voidSurfaceFlinger：：unlockClients()
{
constLayerVector&drawingLayers(mDrawingState。layersSortedByZ);
constsizetcount=
drawingLayers。size();
sp<LayerBase>const*constlayers
i<count;++i){
drawingLayers。array();
for(size_ti=0;
constsp<LayerBase>&layer
layers[i];
%3D
layer->finishPageFlip();
}
}
再看Layer的finishPageFlip函数，代码如下所示：
[-->Layer。cpp]
voidLayer：：finishPageFlip()
{
//#*FrontBufferIndex。
status_terr=lcblk->unlock(mFrontBufferIndex);
}
原来，unlockClients会释放之前占着的FrontBuffer的索引号。下面看最后一个函数
postFrameBuffer，fE3T：
[-->SurfaceFlinger。cpp]
voidSurfaceFlinger：：postFramebuffer()
{
if(!mInvalidRegion。isEmpty()){
constDisplayHardware&hw(graphicPlane(0)。displayHardware()};
constnsecstnow=systemTime();
mDebugInSwapBuffers
=now;
1/调用这个函教后，混合后的图像就会传递到屏幕中显示了。
hw。flip(mInvalidRegion);
mLastSwapBufferTime=systemTime()
now;
mDebugInSwapBuffers
mInvalidRegion。clear(;
}
=0;
}


Page386
368
深入理解Android：卷」
flip*aDisplayHardware-eglSwapBuffer☆，UtFrameBuffer
的PageFlip操作，代码如下所示：
[-->DisplayHardware。cpp]
voidDisplayHardware：：flip(constRegion&dirty)const
{
checkGLErrors();
EGLDisplaydpy
EGLSurfacesurface=mSurface;
MDisplay;
if(mFlags&PARTIAL_UPDATES){
MNativeWindow->setUpdateRectangle(dirty。getBounds());
}
mPageFlipCount++;
eglSwapBuffers(dpy，surface);//PageFlipping，HÉBR!
}
8。5。3TransactionT
Transaction是“事务”的意思。在我脑海中，关于事务的知识来自数据库。在数据库操
作中，事务意味着一次可以提交多个SQL语句，然后一个commit就可让它们集中执行，而
且数据库中的事务还可以回滚，即恢复到事务提交前的状态。
SurfaceFlinger为什么需要事务呢?从上面对数据库事务的描述来看，是不是意味着一
次执行多个请求呢?如直接盯着SF的源码来分析，可能不太容易搞清楚事务的前因后果，
用老办法，从一个例子人手吧。
在WindowManagerService。java中有一个函数之前已分析过，现在再看看，代码如下所示：
[-->WindowManagerService。java：WinState]
SurfacecreateSurfaceLocked(){
Surface。openTransaction();//#to-iktransaction。
try{
try{
mSurfaceX=mFrame。left+mXOffset;
=mFrame。top+mYOffset;
mSurfaceY
1/设置Surface的位置。
mSurface。setPosition(mSurfaceX，mSurfaceY);
}
}finally{
Surface。closeTransaction();//****。
}


Page387
第8章深入理解Surface系统
369
这个例子很好地展示了事务的调用流程，它会依次调用：
OopenTransaction
setPosition
closeTransaction
下面就来分析这几个函数的调用。
1。openTransactioni
看JNI对应的函数，代码如下所示：
[-->android_View_Surface。cpp]
staticvoidSurface_openTransaction(JNIEnv*env，jobjectclazz)
{
//SurfaceComposerClient#ýopenGlobalTransaction*。
SurfaceComposerClient：：openGlobalTransaction();
}
下面转到SurfaceComposerClient，代码如下所示：
[-->SurfaceComposerClient。cpp]
voidSurfaceComposerClient：：openGlobalTransaction()
{
Mutex：：Autolock
1(gLock);
constsize_tN=gActiveConnections。size();
for(size_ti=0;i<N;i++){
sp<SurfaceComposerClient>
client(gActiveConnections。valueAt(i)。promote());
1/gopenTransactions存储当前提交事务请求的Client。
if(client!=0&&gOpenTransactions。index0f(client)<0){
//Client*☆ttgActiveConnections+SurfaceComposerClient
1/对象，调用它的openTransaction。
if(client->openTransaction()
if(gOpenTransactions。add(client)
==NOERROR){
<0){
client->closeTransaction();
}
}
}
}
上面是一个静态函数，内部调用了各个SurfaceComposerClient对象的openTranscation，
代码如下所示：


Page388
370
深入理解Android：卷!
[-->SurfaceComposerClient。cpp]
status_tSurfaceComposerClient：：openTransaction()
{
if(mStatus!=NOERROR)
returnmStatus;
Mutex：：Autolock
1(mLock);
mTransactionopen++;//一个计数值，用来控制事务的提交。
if(mPrebuiltLayerState==0){
mPrebuiltLayerState=
newlayer_state_t;
returnNO_ERROR;
}
layer_state_t是用来保存Surface的一些信息的，比如位置、宽、高等信息。实际上，调
用的setPosition等函数，就是为了改变这个layer_state_t中的值。
2。setPosition
上文说过，SFC中有一个layer_state_t对象用来保存Surface的各种信息。这里以
setPosition为例来看它的使用情况。这个函数是用来改变Surface在屏幕上的位置的，代码
如下所示：
[-->android_View_Surface。cpp]
staticvoidSurface_setPosition(JNIEnv*env，jobjectclazz，jintx，jinty)
{
constsp<SurfaceControl>&surface(getSurfaceControl(env，clazz));
if(surface
==0)return;
surface->setPosition(x，y);
status_terr
[-->Surface。cpp]
status_tSurfaceControl：：setPosition(int32_tx，int32_ty){
constsp<SurfaceComposerClient>&client(mClient);
status_terr=validate();
if(err<0)returnerr;
//SurfaceComposerClientésetPositionk*。
returnclient->setPosition(mToken，x，y);
}
[-->SurfaceComposerClient。cpp]
status_tSurfaceComposerClient：：setPosition(SurfaceIDid，int32_tx，int32_ty)
{
_lockLayerState(id);//Kayer_state_t。
layer_state_t*s
if(!s)returnBADINDEX;
s->what|=ISurfaceComposer：：ePositionChanged;


Page389
第8章深入理解Surface系统
371
S->X=x;
s->y=y;
1/上面几句修改了这块layer的参数。
_unlockLayerState();//该函数将unlock一个同步对象，其他没有做什么工作。
returnNO_ERROR;
}
setPosition修改了layer_state_t中的一些参数，那么，这个状狀态是什么时候传递到
SurfaceFlinger#?
3。closeTransaction
相信读者此时已明白为什么叫“事务”了。原来，在openTransaction和closeTransaction
中可以有很多操作，然后会由closeTransaction一次性地把这些修改提交到SF上，来看代码：
[-->android_View_Surface。cpp]
staticvoidSurface_closeTransaction(JNIEnv*env，jobjectclazz)
{
SurfaceComposerClient：：closeGlobalTransaction();
}
[-->SurfaceComposerClient。cpp}
voidSurfaceComposerClient：：closeGlobalTransaction()
{
constsize_tN=clients。size();
sp<ISurfaceComposer>sm(getComposerService());
//OtASFopenGlobalTransaction。
sm->openGlobalTransaction();
for(size_ti=0;i<N;i++){
//OAEASurfaceComposerClientgcloseTransaction。
clients[i)->closeTransaction();
}
//®EASFcloseGlobalTransaction。
sm->closeGlobalTransaction();
}
上面一共列出了三个函数，它们都是跨进程的调用，下面对其一一进行分析。
(1)SurfaceFlingerfjopenGlobalTransaction
这个函数其实很简单，略看一下就行了。
[-->SurfaceFlinger。cpp]
voidSurfaceFlinger：：openGlobalTransaction()
{
android_atomic_inc(&mTransactionCount);//l-fit。
}


Page390
372
深入理解Android：卷」
(2)SurfaceComposerClient#jcloseTransaction
代码如下所示：
[-->SurfaceComposerClient。cpp]
status_tSurfaceComposerClient：：closeTransaction()
{
if(mStatus!=NOERROR)
returnmStatus;
Mutex：：Autolock
1(mLock);
constssizetcount
=mStates。size();
if(count){
//mStatesit↑SurfaceComposerClient+*layer_state_ta，ŁiŁ
1/每个Surface一个。然后调用跨进程的setState。
mClient->setState(count，mStates。array());
mstates。clear();
}
returnNO_ERROR;
}
BClient的setState，最终会转到SF的setClientState上，代码如下所示：
[-->SurfaceFlinger。cpp]
statustSurfaceFlinger：：setClientState(ClientIDcid，int32_tcount，
constlayer_statet*states)
Mutex：：Autolock
1(mStateLock);
uint32_tflags
=0;
cid<<=16;
i<count;i++){
for(inti=0;
constlayer_state_t&s=states[i];
sp<LayerBaseClient>layer(getLayerUser_1(s。surface|cid));
if(layer!=0){
constuint32_twhat=
s。what;
if(what&ePositionChanged){
if(layer->setPosition(s。x，s。y))
1/eTraversalNeeded表示需要遍历所有显示层。
flags=eTraversalNeeded;
}
if(flags){
setTransactionFlags(flags);//threadLooph。
}
returnNO_ERROR;
}
[-->SurfaceFlinger。cpp]
uint32_tSurfaceFlinger：：setTransactionFlags(uint32_tflags，nsecs_tdelay)


Page391
第8章深入理解Surface系统
373
{
android_atomic_or(flags，&mTransactionFlags);
uint32_told
if((old&flags)==0){
if(delay>0){
signalDelayedEvent(delay);
}else{
signalEvent();
%3D
1/设置完mTransactionFlags后，触发事件。
}
returnold;
}
(3)SurfaceFlingerJcloseGlobalTransaction
来看代码：
[-->SurfaceFlinger。cpp]
voidSurfaceFlinger：：closeGlobalTransaction()
{
if(android_atomic_dec(&mTransactionCount)
//注意下面语句的执行条件，当mTransactionCount变为零时才执行，这意味着
//openGlobalTransaction*，R$-closeGlobalTransaction
1/才会真正地提交事务。
signalEvent();
==1){
Mutex：：Autolock
1(mStateLock);
1/如果这次事务涉及尺寸调整，则需要等一段时间。
while(mResizeTransationPending){
statusterr
=mTransactionCV。waitRelative(mStateLock，s2ns(5));
if(CC_UNLIKELY(err!=NO_ERROR)){
mResizeTransationPending
=false;
break;
}
}
}
关于事务的目的，相信读者已经比较清楚了：
就是将一些控制操作(例如setPosition)的修改结果一次性地传递给SF进行处理。
那么，哪些操作需要通过事务来传递呢?查看Surface。h可以知道，下面这些操作需
要通过事务来传递(这里只列出了几个经常用的函数)：setPosition、setAlpha、show/hide、
setSize，setFlag。
由于这些修改不像重绘那么简单，有时它会涉及其他的显示层，例如在显示层A的位置
调整后，之前被A遮住的显示层B，现在可能变得可见了。对于这种情况，所提交的事务会
设置eTraversalNeeded标志，这个标志表示要遍历所有显示层进行处理。关于这一点，我们
可以看看工作线程中的事务处理。


Page392
374や深入理解Android：卷!
4。工作线程中的事务处理
还是从代码入手分析，如下所示：
[-->SurfaceFlinger。cpp]
boolSurfaceFlinger：：threadLoop()
{
waitForEvent();
if(LIKELY(mTransactionCount==0)){
constuint32_tmask=eTransactionNeeded|eTraversalNeeded;
uint32_ttransactionFlags
if(LIKELY(transactionFlags)){
getTransactionFlags(mask);
handleTransaction(transactionFlags);
}
}
}
getTransactionFlags函数的实现蛮有意思，不妨看看其代码，如下所示：
[-->SurfaceFlinger。cpp]
uint32_tSurfaceFlinger：：getTransactionFlags(uint32_tflags)
1/先通过原子操作去掉mTransactionFlags中对应的位。
1/而后原子操作返回的旧值和flags进行与操作
returnandroid_atomic_and(~flags，&mTransactionFlags)&flags;
}
getTransactionFlags所做的工作不仅仅是get那么简单，它还设置了mTransactionFlags，
从这个角度来看，getTransactionFlags这个名字有点名不副实。
接着来看最重要的handleTransaction函数，代码如下所示：
[-->SurfaceFlinger。cpp]
voidSurfaceFlinger：：handleTransaction(uint32_ttransactionFlags)
{
Vector<sp<LayerBase>>ditchedLayers;
{
Mutex：：Autolockl(mStateLock);
//handleTransactionLocked*。
handleTransactionLocked(transactionFlags，ditchedLayers);
}
constsizetcount
ditchedLayers。size();
%3D
for(sizeti=0;i<count;i++){
if(ditchedLayers(i]!=0){
//ditch是丟弃的意思，有些显示层可能被hide了，所以这里做些收尾的工作。


Page393
第8章深入理解Surface系统
375
ditchedLayers[i]->ditch();
}
}
}
[-->SurfaceFlinger。cpp]
voidSurfaceFlinger：：handleTransactionLocked(
uint32_ttransactionFlags，Vector<sp<LayerBase>>&ditchedLayers)
{
1/这里使用了mCurrentState，它的layerssortedByz数组存储了SF中所有的显示层。
constLayerVector&currentLayers(mCurrentState。layersSortedByZ);
constsizetcount
=currentLayers。size();
constboollayersNeedTransaction
transactionFlags&eTraversalNeeded;
1/如果需要遍历所有显示层的话。
if(layersNeedTransaction){
for(sizeti=0;
i<count;i++){
constsp<LayerBase>&layer
currentLayers[i];
%3D
uint32_ttrFlags
layer->getTransactionFlags(eTransactionNeeded);
%3D
if(!trFlags)continue;
1/调用各个显示层的doTransaction函数。
constuint32_tflags
if(flags&Layer：：eVisibleRegion)
mVisibleRegionsDirty
layer->doTransaction(0);
%3D
true;
%3D
}
}
if(transactionFlags&eTransactionNeeded){
if(mCurrentState。orientation!=mDrawingState。orientation){
1/横坚屏如果发生切换，需要对应变換设置。
constintdpy
=0;
constintorientation=mCurrentState。orientation;
constuint32_ttype=mCurrentState。orientationType;
GraphicPlane&plane(graphicPlane(dpy));
plane。setOrientation(orientation);
}
mLayersRemoved变量在显示层被移除的时候设置，例如removeLayer函数，这些函数
LAf*handleTranscation*6*ti。
*/
if(mLayersRemoved){
mLayersRemoved=false;
mVisibleRegionsDirty
true;
constLayerVector&previousLayers(mDrawingState。layersSortedByZ);
constsize_tcount
for(size_ti=0;i<count;i++){
constsp<LayerBase>&layer(previousLayers(i]);
if(currentLayers。indexof(layer)<0){
ditchedLayers。add(layer);
mDirtyRegionRemovedLayer。orSelf(layer->visibleRegionScreen);
=previousLayers。size();


Page394
376
深入理解Android：卷1
}
}
}
freeresources_1(});
}
1/提交事务处理，有必要进去看看。
commitTransaction();
}
每个显示层对事务的具体处理，都在它们的doTransaction函数中，读者若有兴趣，可
进去看看。需要说明的是，每个显示层内部也有一个状态变量，doTransaction会更新这些状
态变量。
回到上面的函数，最后它将调用commitTransaction提交事务，代码如下所示：
[-->SurfaceFlinger。cpp]
voidSurfaceFlinger：：commitTransaction()
{
//mDrawingState#emCurrentState，
mDrawingState=mCurrentState;
mResizeTransationPending=false;
1/触发一个条件变量，这样等待在closeGlobalTransaction函数中的线程可以放心地返回了。
mTransactionCV。broadcast();
}
8。5。4关于SurfaceFlinger的总结
前面的分析让我们感受了SurfaceFlinger的风采。从整体上看，SurfaceFlinger不如
AudioFlinger复杂，它的工作集中在工作线程中，下面用图8-23来总线一下SF工作线程：
调用waitForEvent等待
AApostFrameBuffer，*
重绘或者事务处理
混合后的内容投递到屏幕
如果有事务处理请求，则
调用unlockClients，它会遍历
调用handleTransaction进行处理
各个显示层的finishPageFlip函数
调用handlePageFlip，对各个
调用handleRepaint，它会遍历
显示层进行PageFlip。对于Layer
各个显示层的onDraw函数
类，它会生成一个新的纹理
图8-23SF工作线程的流程总结


Page395
第8章深入理解Surface系统
377
8。6拓展思考
本章的拓展思考分三个部分：
口介绍SharedBufferServer和SharedBufferClient的工作流程。
口关于ViewRoot的一些问题的总结。
ロLayerBuffer的工作原理分析。
8。6。1
Surface系统的CB对象分析
根据前文的分析可知，Surface系统中的CB，其实是指SharedBuffer家族，它们是
Surface系统中对生产者和消费者进行步调控制的中枢机构。先通过图8-24来观察整体的工
作流程是怎样的。
为了书写方便，我们简称：
OSharedBufferServerSBS。
OSharedBufferClientSBC。
OSharedBufferStackSBT，
其中SBC和SBS都是建立在同一个SBT上的，所以应先看SBT，下面的代码列出了其
中几个与读写控制有关的成员变量：
SharedClientĐ
设置同一个SharedBufferStack
SharedBufferServer£J
SharedBufferClient£
dequeue得到BackBuffer索引号
retireAndUnlockAFrontBuffer
的索引号
lock对应索引号的Buffer
unlockFrontBuffer
queue入队使用完的Buffer
图8-24SharedBuffer家族的使用流程
[-->SharedBufferStack。h]
classSharedBufferStack{


Page396
378*深入理解Android：卷!
虽然PageFlipping使用Front和Back两个Buffer就可以了，但是SBT的结构和相关算法
是支持多个缓冲的。另外，缓冲是按照块来获取的，也就是一次获得一块緩冲，每块缓冲用
一个编号表示(这一点在之前的分析中已经介绍过了)。
*/
int32_thead;
1/当前可用的空闲缓冲个数。
//SBC投递的脏缓冲个数。
7/SBS当前正在使用的缓冲编号。
。//上面这几个参数联合SBC中的tail，我称之为控制参数。
int32tavailable;
int32_tqueued;
int32_tinUse;
}
SBT创建好后，下面就是SBS和SBC的创建了，它们会做什么特殊工作吗?
1。SBS和SBC的创建
下面分别看SBS和SBC的创建，代码如下所示：
[-->SharedBufferStack。cpp]
SharedBufferServer：：SharedBufferServer(SharedClient*sharedClient，
intsurface，intnum，int32_tidentity)
：SharedBufferBase(sharedClient，surface，num，identity)
mSharedStack->init(identity);//iż^*tiinUse*-1。
1/下面设置SBT中的参数，我们关注前三个。
mSharedStack->head
num-1;
%D
mSharedStack->available=
num;
mSharedStack->queued=0;
//iIÈÉ，head=2-1=1，available=2，queued=0，inUse=-1
mSharedStack->reallocMask=0;
memset(mSharedStack->dirtyRegion，0，sizeof(mSharedStack->dirtyRegion));
}
再看SBC的创建，代码如下所示：
[-->SharedBufferStack。cpp]
SharedBufferClient：：SharedBufferClient(SharedClient*sharedClient，
intsurface，intnum，int32_tidentity)
SharedBufferBase(sharedClient，surface，num，identity)，tail(0)
{
tail=
computeTail();//tail是SBC定义的变量，注意它不是SBT定义的。
}
看computeTail函数的代码，如下所示：
[-->SharedBufferStack。cpp]
int32_tSharedBufferClient：：computeTail(Oconst
{

Page397
第8章深入理解Surface系统
379
SharedBufferStack&stack(*mSharedStack);
int32_tnewTail;
int32_tavail;
int32_thead;
do{
avail=stack。available;//available=2，head=1
head=stack。head;
}while(stack。available!=avail);
newTail=head-avail+1;//newTail=1-2+1=0
if(newTail<0){
newTail+=mNumBuffers;
}elseif(newTail>=mNumBuffers){
-=mNumBuffers;
newTail
}
returnnewTail;//itnewTail=0
}
来看SBC和SBS创建后控制参数的变化，如图8-25所示：
head
tail
inUse=-1
queuedX
1号缓冲
0号缓冲
availableX
图8-25
SBC/SBS创建后的示意图
2。SBC端流程分析
下面看SBC端的工作流程。
(1)dequeue
先看SBC的dequeue函数：
[-->SharedBufferStack。cpp]
ssize_tSharedBufferClient：：dequeue()
{
SharedBufferStack&stack(*mSharedStack);
//DequeueCondition*。
DequeueConditioncondition(this);
status_terr=waitForCondition(condition);
7/成功以后，available减1，表示当前可用的空闲buffer只有1个。
if(android_atomic_dec(&stack。available)
==0){
}
intdequeued
=tail;//tail值为0，所以dequeued的值为0。


Page398
380
深入理解Android;卷!
1/tail加1。如果超过2，则重新置为0，这表明tail的值在0，1间循环。
((tail+1>=mNumBuffers)?0：tail+1);
tail
%3D
1/返回的这个dequeued值为零，也就是tail加1操作前的旧值。这一点请读考务必注意。
returndequeued;
}
其中DequeueCondition的操作函数很简单，代码如下所示：
boolSharedBufferClient：：DequeueCondition：：operator()0{
returnstack。availab1le>0;//只要available大于0就算满足条件，第一次进来肯定满足。
}
用图8-26来表示dequeue的结果：
dequeued
tail
head
inUse=-1i
queuedt
1号缓冲
0号缓冲
available区域，个数为1
图8-26dequeue结果图
注意在图8-26中，0号缓冲用虚线表示，SBC的dequeue函数的返回值用dequeued表示，
它指向这个0号缓冲。正如代码中注释的那样，由于dequeued的值用的是tail的1旧值，而
tail是SBC定义的变量，不是SBT定义的变量，所以tail在SBS端是不可见的。这就带来
了一个潜在危险，即0号缓冲不能保证当前是真正空闲的，因为SBS可能正在用它，怎么
办?试看下面的lock。
(2)lock分析
lock使用了LockCondition，其中传入的参数buf的值为0，也就是上图中的dequeue的
值，代码如下所示：
[-->SharedBufferStack。cpp]
statustSharedBufferClient：：lock(intbuf)
{
LockConditioncondition(this，buf);
status_terr
waitForCondition(condition);
returnerr;
}
来看LockCondition的()函数，代码如下所示：
boolSharedBufferClient：：LockCondition：：operator()(){


Page399
第8章深入理解Surface系统
381
这个条件其实就是判断编号为buf的Buffer是不是被使用了。
buf伍为0，head值为1，queued为0，inUse为-1
*/
return(buf!=stack。head||
(stack。queued>0&&stack。inUse!=buf));
}
现在知道为什么SBC需要调用dequeue和lock函数了吗?原来：
口dequeue只是根据本地变量taili计算一个本次应当使用的Buffer编号，其实也就是在
0，1之间循环。上次用0号缓冲，那么这次就用1号缓冲。
口lock函数要确保这个编号的Buffer没有被SF当作FrontBuffer使用。
(3)queue分析
Activity端在绘制完UI后，将把BackBuffer投递出去以便显示。接着看上面的流程，
这个BackBuffer的编号是0。待Activity投递完后，才会调用signal函数触发SF消费，所
以在此之前格局不会发生变化。试看投递用的queue函数，注意传入的buf参数为0，代码
如下所示：
[-->SharedBufferStack。cpp]
status_tSharedBufferclient：：queue(intbuf)
{
QueueUpdateupdate(this);
status_terr=updateCondition(update);
。。。。。
returnerr;
}
1/直接看这个QueueUpdate函数对象。
ssize_tSharedBufferClient：：QueueUpdate：：operator()({
android_atomic_inc(&stack。queued);//queued*1，Lkàib**1。
returnNOERROR;
至此，SBC端走完一个流程了，结果是什么?如图8-27所示：
queued区域
head
tail
inUse=-1
0号缓冲
1号缓冲
availableZ
图8-27
queue结果图


Page400
382
深入理解Android：卷」
0号缓冲被移到了queue的区域，可目前还没有变量指向它。假设SBC端此后没有绘制
UI的需求，那么它就会沉默一段时间。
3。SBS端分析
SBS的第一个函数是retireAndLock，它使用了RetireUpdate函数对象，代码如下所示：
[-->SharedBufferStack。cpp]
ssize_tSharedBufferServer：：retireAndLock()
{
RetireUpdateupdate(this，mNumBuffers);
ssize_tbuf=
updateCondition(update);
returnbuf;
}
这个RetireUpdate对象的代码如下所示：
ssize_tSharedBufferServer：：RetireUpdate：：operator()(){
//先取得head值，为1。
int32_thead=stack。head;
//inuse被设置为1。表明要使用1吗?目前的脏缓冲应该是0才对。
android_atomic_write(head，&stack。inUse);
int32_tqueued;
do{
queued
=stack。queued;//queuedAÍ☆1。
if(queued
==0){
returnNOT_ENOUGHDATA;
}
1/下面这个原子操作使得stack。queued减1。
}while(android_atomic_cmpxchg(queued，queued-1，&stack。queued));
1/while循环退出后，queued减1，又变为0。
1/head值也在0，1间循环，现在head值变为0了。
head=
((head+1
>=numBuffers)?0：head+1);
>1/inUse被设置为0。
>android_atomic_write(head，&stack。inUse);
>//head值被设为0。
>android_atomic_write(head，&stack。head);
>//available1，E☆2。
>android_atomic_inc(&stack。available);
>returnhead;//i0。
>}
>retireAndLock的结果是什么呢?看看图8-28就知道了。


Page401
第8章深入理解Surface系统
383
tail
bead
inUse
queued区域
0号缓冲
1号缓冲
0号缓冲
|available区域，个数为2
图8-28
retireAndLock
注意上面的available区域，1号缓冲右边的0号缓冲是用虚线表示的，这表示该0号缓
冲实际上并不存在于available区域，但available的个数却变成2了。这样不会出错吗?当
然不会，因为SBC的lock函数要确保这个缓冲没有被SBS使用。
我们来看SBS端的最后一个函数，它调用了SBS的unlock，这个unlock使用了
UnlockUpdate函数对象，就直接了解它好了，代码如下所示：
[-->SharedBufferStack。cpp]
ssize_tSharedBufferServer：：UnlockUpdate：：operator()(){
android_atomic_write(-1，&stack。inUse);//inUse*-1。
returnNO_ERROR;
}
unlock后最终的结果是什么呢?如图8-29所示：
tail
head
inUse=-1
queued区域
1号缓冲
0号缓冲
availableX
图8-29unlock结果图
比较一下图8-29和图8-25，可能会发现两图中tail和head刚好反了，这就是PageFlip。
另外，上面的函数大量使用了原子操作。原子操作的目的就是为了避免锁的使用。值得指
出的是，updateConditon函数和waitForCondition函数都使用了Mutex，也就是说，上面
这些函数对象又都是在Mutex锁的保护下执行的，为什么会这样呢?先来看一段代码：
像下面这样的代码，如果有锁控制的话根本用不着一个while循环，因为有锁的保护，没有其他线程
能够修改stack。queued的值，所以用while来循环判断android_atomic_cmpxchg没有什么意义。
int32_tqueued;
do{
queued=stack。queued;
if(queued
0){
==
returnNOTENOUGHDATA;


Page402
384
深入理解Android：卷!
}
}while(android_atomic_cmpxchg(queued，queued-1，&stack。queued));
对于上面这个问题，我目前还不知道答案，但对其进行修改后，把函数对象放在锁外执
行，结果在真机上运行没有出现任何异常现象。也许Google或哪位读者能给这个问题一个
较好的解释。
说明为什么我对生产/消费的同步控制如此感兴趣呢?这和自己工作的经历有些关系。因
为之前曾做过一个单写多读的跨进程缓冲类，也就是一个生产者，多个消费者。为了保证正
确性和一定的效率，我们在算法上曾做了很多改进，但还是大量使用了锁，所以我很好奇
Google是怎么做到的，这也体现了一个高手的内功修养。要是由读者自己来实现，结果会怎
样呢?
8。6。2ViewRoot的你问我答
ViewRoot是Surfac系统甚至UI系统中一个非常关键的类，下面把网上一些关于
ViewRoot的问题做个总结，希望这能帮助读者对ViewRoot有更加清楚的认识。
ViewRoot和View类的关系是什么?
ViewRoot是View视图体系的根。每一个Window(注意是Window，比如PhoneWindow)
有一个ViewRoot，它的作用是处理layout和View视图体系的绘制工作。那么视图体系又是什
么呢?它包括Views和ViewGroups，也就是SDK中能看到的View类都属于视图体系。根
据前面的分析可知，这些View是需要通过draw画出来的。而ViewRoot就是用来draw它们
的，ViewRoot本身没有draw/onDraw函数。
ViewRoot和它所控制的View及其子View使用同一个Canvas吗?
这个问题的答案就很简单了，我们在ViewRoot的performTraversals中见过。ViewRoot
提供Canvas给它所控制的View，所以它们使用同一个Canvas。但Canvas使用的内存却不
是固定的，而是通过Surface的lockCanvas得到的。
View、Surface和Canvas之间的关系是怎样的?我认为，每一个view将和一个
Canvas，以及一个surface绑定到一起(这里的“我”表示提问人)。
这个问题的答案也很简单。一个Window将和一个Surface绑定在一起，绘制前
-
ViewRoot会从Surface中lock出一个Canvas。
Canvas有一个bitmap，那么绘制UI时，数据是画在Canvas的这个bitmap中吗?
答案是肯定的，bitmap实际上包括了一块内存，绘制的数据最终都在这块内存上。
同一个ViewRoot下，不同类型的View(不同类型指不同的UI单元，例如按钮、文本
框等)使用同一个Surface吗?
是的，但是SurfaceView要除外。因为SurfaceView的绘制一般在单独的线程上，并且
由应用层主动调用lockCanvas、draw和unlockCanvasAndPost来完成绘制流程。应用层相当


Page403
第8章深入理解Surface系统
385
于抛开了ViewRoot的控制直接和屏幕打交道，这在camera、
video方面用得最多。
8。6。3LayerBuffer
T
前面介绍了Normal属性显示层中的第一类Layer，这里将介绍其中的第二类
LayerBuffer。LayerBuffer会在视频播放和摄像机预览等场景中用到，下面就以Camera的
View(预览)为例，来分析LayerBuffer的工作原理。
1。LayerBuffer@J
先看LayerBuffer的创建，它通过SF的createPushBuffersSurfaceLocked得到，代码如
下所示：
[-->SurfaceFlinger。cpp]
sp<LayerBaseClient>SurfaceFlinger：：createPushBuffersSurfaceLocked(
constsp<Client>&client，DisplayIDdisplay，
int32_tid，uint32_tw，uint32_th，uint32_tflags)
{
newLayerBuffer(this，display，client，id);
sp<LayerBuffer>layer
layer->initStates(w，h，flags);
addLayer_1(layer);
%3D
returnlayer;
}
LayerBuffer的派生关系如图8-30所示：
LayerBaseCient
Surface
LayerBuffer
Source
Buffer
Surfacelayerbuffer
BufferSource
OverlaySource
图8-30LayerBuffer的派生关系示意图


Page404
386
深入理解Android：卷」
从上图中可以发现：
ロLayerBuffer定义了一个内部类Source类，它有两个派生类BufferSource和Overlay-
Source。根据它们的名字，可以猜测到Source代表数据的提供者。
OLayerBuffer#mSurfaceI**NRSurfaceLayerBuffer。
LayerBuffer创建好了，不过该怎么用呢?和它相关的调用流程是怎样的呢?下面来分析
Camera。
2。CamerapreViewF
Camera是一个单独的Service，全称是CameraService，先看CameraService的
registerPreviewBuffers函数。这个函数会做什么呢?代码如下所示：
[-->CameraService。cpp]
status_tCameraService：：Client：：registerPreviewBuffers()
{
intw，h;
CameraParametersparams(mHardware->getParameters0);
params。getPreviewSize(&w，&h);
mHardware代表Camera设备的HAL对象。本书讨论CameraHardwareStub设备，它其实是
一个虚拟的设备，不过其代码却具有参考价值。
BufferHeap定义为ISurface的內部类，其实就是对IMemoryHeap的封装。
*/
ISurface：：BufferHeapbuffers(w，h，w，h，
HAL_PIXELFORMAT_YCrCb_
420SP，
morientation，
0，
mHardware->getPreviewHeap());
//®ASurfaceLayerBufferéýregisterBuffers。
status_tret=mSurface->registerBuffers(buffers);
returnret;
}
上面代码中列出了两个关键点，逐一来分析它们。
(1)êlBufferHeap
BufferHeap是ISurface定义的一个内部类，它的声明如下所示：
[-->ISurface。h]
classBufferHeap{
public：
1/使用这个构造函数。
BufferHeap(uint32_tw，uint32_th，
int32_thor_stride，int32_tver_stride，
PixelFormatformat，constsp<IMemoryHeap>&heap);


Page405
第8章深入理解Surface系统
387
-BufferHeaр();
uint32_tw;
uint32_th;
int32_thor_stride;
int32_tver_stride;
PixelFormatformat;
uint32_ttransform;
uint32_tflags;
sp<IMemoryHeap>heap;//heap☆。
};
从上面的代码可发现，BufferHeap基本上就是封装了一个IMemoryHeap对象，根据我
们对IMemoryHeap的了解，它应该包含了真实的存储对象，这个值由CameraHardwareStub
对象的getPreviewHeap得到，这个函数的代码如下所示：
[-->CameraHardwareStub。cpp]
sp<IMemoryHeap>CameraHardwareStub：：getP
{
returnmPreviewHeap;//返回一个成员变量，它又是在哪创建的呢?
}
1/上面的mPreivewHeap对象由initHeapLocked函数创建，该函数在HAL对象创建的时候被调用
voidCameraHardwarestub：：initHeapLocked()
{
eviewHeap(const
/*
&-AMemoryHeapBase，**mPreviewFrameSize*kBufferCount，*
kBufferCount为4。注意这是一段连续的缓冲。
*/
mPreviewHeap
newMemoryHeapBase(mPreviewFrameSize*kBufferCount);
7/mBuffer为MemoryBase数组，元素为4。
for(inti=0;i<kBufferCount;i++){
mBuffers[i]
=newMemoryBase(mPreviewHeap，
i*mPreviewFrameSize，mPreviewFrameSize);
}
}
从上面这段代码中可以发现，CameraHardwareStub对象创建的用于preView的内存结构
是按图8-31所示的方式来组织的：
BufferHeap
heap
mPreviewHeap
МеmогуВaselo]|MemoryBase[1]|MemoryBase[2]|MemoryBase[3]
图8-31
CameraHardwareStub用于preView的内存结构图


Page406
388
深入理解Android：卷」
其中：
口BufferHeap的heap变量指向一块MemoryHeap，这就是mPreviewHeap。
口在这块MemoryHeap上构建了4个MemoryBase。
(2)registerBuffers
BufferHeap准备好后，要调用ISurface的registerBuffers函数，ISurface在SF端的真实
类型是SurfaceLayerBuffer，所以要直接地看它的实现，代码如下所示：
[-->LayerBuffer。cpp]
statustLayerBuffer：：SurfaceLayerBuffer：：registerBuffers(
constISurface：：BufferHeap&buffers)
{
sp<LayerBuffer>owner(getOwner());
if(owner!=0)
//调用外部类对象的registerBuffers，所以SurfaceLayerBuffer也是一个Proxy哦。
returnowner->registerBuffers(buffers);
returnNOINIT;
}
1/外部类是LayerBuffer，调用它的registerBuffers函数。
status_tLayerBuffer：：registerBuffers(constISurface：：BufferHeap&buffers)
{
Mutex：：Autolock
1(mLock);
1/创建数据的来源Buffersource，注意我们其实把MemoryHeap设置上去了。
newBufferSource(*this，buffers);
sp<BufferSource>source
%3D
statustresult=
source->getStatus(;
if(result==NO_ERROR){
mSource
=source;//保存这个数据源为mSource。
}
returnresult;
}
BufferSource，曾在图8-30中见识过，它内部有一个成员变量mBufferHeap指向传人的
buffers参数，所以registerBuffers过后，就得到了图8-32：
BufferSource
BufferHeap
mPreviewHeap
heap
mBufferHeap
图8-32registerBuffers的结果示意图
请注意上图的箭头指向，不论中间有多少层封装，最终的数据存储区域还是
mPreivewHeap。
3。数据的传输
至此，Buffer在SF和Camera两端都准备好了，那么数据是怎么从Camera传递到SF
的呢?先来看数据源是怎么做的。


Page407
第8章深入理解Surface系统
389
(1)数据传输分析
CameraHardwareStub有一个preview线程，这个线程会做什么呢?代码如下所示：
[-->CameraHardwareStub。cpp]
1/preview线程从Thread类派生，下面这个函数在threadLoop中循环调用。
intCameraHardwareStub：：previewThread()
{
mLock。lock();
//mCurrentPreviewFrame1。
ssizetoffset
mCurrentPreviewFrame
*mPreviewFrameSize;
sp<MemoryHеарBase>heaр
mPreviewHeap;
FakeCamera*fakeCamera
mFakeCamera;//虚拟的摄像机设备。
%3D
1/从mBuffers中取一块內存，用于接收来自硬件的数据。
sp<MemoryBase>buffer=mBuffers[mCurrentPreviewFrame);
mLock。unlock();
if(buffer!=0){
(int)(1000000。0f/float(previewFrameRate));
void*base=heap->base();//base是mPreviewHeap的起始位置。
intdelay
//下面这个frame代表buffer在mPreviewHeap中的起始位置，还记得图8-31吗?
//四块MemoryBase的起始位置由下面这个代码计算得来。
uint8t*frame=
((uint8_t*)base)
+offset;
//取出一帧数据，放到对应的MemoryBase中。
fakeCamera->getNextFrameAsYuv422(frame);
1/①把含有帧数据的buffer传递到上层。
if(mMsgEnabled&CAMERA_MSG_PREVIEW_FRAME)
mDataCb(CAMERA_MSG_PREVIEW_FRAME，buffer，mCallbackCookie);
7/mCurrentPreviewFrame遴增，在0到3之间循环。
mCurrentPreviewFrame=
(mCurrentPreviewFrame+1)%kBufferCount;
usleep(delay);//模拟真实硬件的延时。
一
returnNO_ERROR;
}
读者是否明白Camerapreview的工作原理了?就是从四块内存中取一块出来接收
数据，然后再把这块内存传递到上层去处理。从缓冲使用的角度来看，mBuffers数组
构成了一个成员个数为四的缓冲队列。preview通过mData这个回调函数，把数据传递
到上层，而CameraService则实现了mData这个回调函数，这个回调函数最终会调用
handlePreviewData，直接看handlePreviewData即可，代码如下所示：


Page408
390
深入理解Android：卷1
[-->CameraService。cpp]
voidCameraService：：Client：：handlePreviewData(constsp<IMemory>&mem)
{
ssize_toffset;
size_tsize;
1/注意传入的mem参教，它实际上是CameraHAL创建的mBuffers教组中的一个。
//offset返回的是这个数组在mPreviewHeap中的偏移量。
sp<IMemoryНеар»heap%3
if(!mUseOverlay)
{
Mutex：：AutolocksurfaceLock(mSurfaceLock);
if(mSurface!=NULL){
1/调用ISurface的postBuffer，注意我们传入的参数是offset。
mSurface->postBuffer(offset);
}
mem->getMemory(&offset，&size);
}
}
上面的代码是什么意思?我们到底给ISurface传什么了?答案很明显：
handlePreviewData就是传递了一个偏移量，这个偏移量是mBuffers数组成员的首地址。
可用图8-33来表示：
offset0
offset1
offset2
offset3
mBuffers[0]mBuffers[1}mBuffers[2]mBuffers[3]
A8-33handlePreviewDataJËR
有了图8-33，读者明白数据传递的工作原理了吗?
下面看SurfaceLayerBuffer的postBuffer函数，不过它只是一个小小的代理，真正的工
作由外部类LayerBuffer完成，直接看它好了，代码如下所示：
[-->LayerBuffer。cpp]
voidLayerBuffer：：postBuffer(ssize_toffset)
{
sp<Source>source(getSource());//getSourceikemSource，BufferSourceA。
if(source!=0)
source->postBuffer(offset);//BufferSourceipostBuffer。
}
[-->LayerBuffer。cpp]
voidLayerBuffer：：BufferSource：：postBuffer(ssize_toffset)
{


Page409
第8章深入理解Surface系统
391
ISurface：：BufferHeapbuffers;
{
Mutex：：Autolock
1(mBufferSourceLock);
buffers
mBufferHeap;//还记得图8-32吗?
%3D
if(buffers。heap!=0){
7/BufferHeap的heap变量指向MemoryHeap，下面取出它的大小。
constsize_tmemorySize
1/做一下检查，判断这个offset是不是有问题。
=buffers。heap->getSize();
+mBufferSize)>memorySize){
if((size_t(offset)
LOGE("LayerBuffer：：BufferSource：：postBuffer()
11
"invalidbuffer(offset=%d，size=%d，heap-size=%d"，
int(offset)，int(mBufferSize)，int(memorySize));
return;
}
}
}
sp<Buffer>buffer;
if(buffers。heap!=0){
//&-LayerBuffer：：Buffer。
buffer=
newLayerBuffer：：Buffer(buffers，offset，mBufferSize);
if(buffer->getStatus()
buffer。clear();
setBuffer(buffer);//setBuffer?$f。
!=NO_ERROR)
1/mLayer就是外部类LayerBuffer，调用它的invalidate函数将触发SF的重绘。
mLayer。invalidate();
}
}
voidLayerBuffer：：BufferSource：：setBuffer(
constsp<LayerBuffer：：Buffer>&buffer)
{
1/setBuffer函数就是简单地将new出来的Buffer设置给成员变量mBuffer，这么做会有问题吗?
Mutex：：Autolock
1(mBufferSourceLock);
mBuffer=buffer;//*bufferiimBuffer，mBufferAß-delete。
}
从数据生产者的角度看，postBuffer函数将不断地new一个Buffer出来，然后将它赋值
给成员变量mBuffer，也就是说，mBuffer会不断变化。现在从缓冲的角度来思考一下这种情
况的结果：
口数据生产者有一个含四个成员的缓冲队列，也就是mBuffers数组。
消费者只有一个mBuffer。
这种情况会有什么后果呢?请记住这个问题，我们到最后再来揭示。下面先看mBuffer
的类型Buffer是什么。
(2)数据使用分析
Buffer被定义成LayerBuffer的内部类，代码如下所示：


Page410
392
深入理解Android：卷：
[-->LayerBuffer。cpp]
LayerBuffer：：Buffer：：Buffer(constISurface：：BufferHeap&buffers，
ssize_toffset，size_tbufferSize)
：mBufferHeap(buffers)，mSupportsCopybit(false)
{
7/注意，这个src被定义为引用，所以修改src的信息相当于修改mNativeBuffer的信息。
NativeBuffer&src(mNativeBuffer);
src。crop。1=0;
src。crop。t=0;
src。crop。r=buffers。w;
src。crop。b=buffers。h;
=buffers。hor_stride?：buffers。w;
=buffers。verstride?：buffers。h;
=buffers。format;
src。img。w
src。img。h
src。img。format
1/这个base将指向对应的内存起始地址。
+offset);
src。img。base
src。img。handle
gralloc_module_tconst*module=LayerBuffer：：getGrallocModule();
1/做一些处理，有兴趣的读者可以去看看。
if(module&&module->perform){
(void*)(intptr_t(buffers。heap->base())
%3D
=0;
interr=
module->perform(module，
GRALLOC_MODULE_PERFORM_CREATE_HANDLE_FROM_BUFFER，
buffers。heap->heapID()，bufferSize，
offset，buffers。heap->base()，
&src。img。handle);
mSupportsCopybit
(err==NO_ERROR);
}
}
上面是Buffer的定义，其中最重要的就是这个mNativeBuffer了，它实际上保存了
mBuffers数组成员的首地址。
下面看绘图函数，也就是LayerBuffer的onDraw函数，这个函数由SF的工作线程调
用，代码如下所示：
[-->LayerBuffer。cpp]
voidLayerBuffer：：onDraw(constRegion&clip)const
{
sp<Source>source(getSource());
if(LIKELY(source!=0)){
source->onDraw(clip);//sourceIBufferSource，fn。
}else{
clearWithOpenGL(clip);
}
voidLayerBuffer：：BufferSource：：onDraw(constRegion&clip)const


Page411
第8章深入理解Surface系统
393
{
sp<Buffer>ourBuffer(getBuffer(O);
。。//使用这个Buffer，注意使用的时候没有锁控制。
mLayer。drawwithopenGL(clip，mTexture);//生成一个贴图，然后绘制它。
一
。。。。
其中getBuffer函数返回mBuffer，代码如下所示：
sp<LayerBuffer：：Buffer>LayerBuffer：：BufferSource：：getBuffer()const
{
Mutex：：Autolock
1(mBufferSourceLock);
returnmBuffer;
}
从上面的代码中能发现，mBuffer的使用并没有锁的控制，这会导致什么问题发生呢?
请再次回到前面曾强调要记住的那个问题上。此时生产者的队列有四个元素，而消费者的队
列只有一个元素，它可用图8-34来表示：
使用
mBuffer
postBuffer
生产
mBuffers[0]]mBuffers[1]mBuffers[2]]mBuffers[3]
图8-34数据传递的问题示意图
从上图可以知道：
口使用者使用mBuffer，这是在SF的工作线程中做到的。假设mBuffer实际指向的内存
mBuffers[0]。
口数据生产者循环更新mBuffers数组各个成员的数据内容，这是在另外一个线程中完
成的。由于这两个线程之间没有锁同步，这就造成了当使用者还在使用mBuffers[0]
时，生产者又更新了mBuffers[0]。这会在屏幕上产生混杂的图像。
经过实际测试得知，如果给数据使用端加上一定延时，屏幕就会出现不连续的画面，即
前一帧和后一帧的数据混杂在一起输出。
说明从代码的分析来看，这种方式确实有问题。我在真实设备上测试的结果也在一定程度
上验证了这一点。通过修改LayerBuffer来解决这问题的难度比较大，是否可在读写具体缓
存时加上同步控制呢(例如使用mBuffers[0]的时候调用一下lock，用完后调用unlock)?
这样就不用修改LayerBuffer了。读者可再深入研究这个问题。

Page412
394
深入理解Android：卷!
8。7本章小结
本章可能是全书难度最大的一章了。在这一章的讲解中，我们把打通任督二脉做为破解
Surface系统的突破口：
口应用程序和Surface的关系，这是任脉。
OSurface和SurfaceFlinger的关系，这是督脉。
其中，打通任脉的过程是比较曲折的，从应用程序的Activity开始，一路追踪到
ViewRoot、WindowManagerService。任脉被打通后，还只是解决了Java层的问题，而督脉
则集中在Native层。在必杀技aidl工具的帮助下，我们首先成功找到了Surface乾坤大挪移
的踪迹。此后在精简流程方法的帮助下，乘胜追击，对Surface及SurfaceFlinger进行了深入
分析。我希望读者在阅读过程中，也要把握流程，这样就不至于迷失在代码中了。
在拓展部分，对Surface系统中CB对象的工作流程、ViewRoot的一些问题，以及
LayerBuffer进行了较为详细的介绍。