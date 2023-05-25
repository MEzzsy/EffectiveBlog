# 跨进程通信

[跨进程通信](./Android的跨进程通信.md)

# Android的多进程模式

在Android中使用多进程只有一种方法，就是给四大组件在AndroidMenifest中指定android:process属性。

指定有三种方式：

- `android:process=":remote"`，这种方式是简写，完整的进程名是com.zzsy:remote，表示该进程是当前应用的私有进程，其他应用的组件不会和它跑到一个进程。
- `android:process="com.zzsy.remote"`，这种进程属于全局进程，其他应用可以通过ShareUID可以和它跑到同一个进程中。
- 不指定，不指定默认是当前包名。

使用多进程模式可能会产生的问题：

1. 静态成员和单例模式完全失效
2. 线程同步进制完全失效。
3. SharePreferences的可靠性降低
4. Application会被多次创建

分析问题原因：

1. Android会为每个应用或者进程分配一个独立的虚拟机，不同的虚拟机在内存分配上有不同的分配空间，导致同一个类的对象会有多个副本。
2. 和第一个类似，因为不同进程锁的不是同一个对象。
3. SharePreferences不支持两个进程同时执行写操作，否则会一定几率导致数据丢失。因为SharePreferences底层是通过XML文件来实现的，系统对它的读写有一定的缓存策略，即在内存中会有一份SharePreferences文件的缓存，并发写可能会出现问题
4. 系统创建新的进程会分配独立的虚拟机，相当于启动一个应用。或者这么说，运行在同一个进程的组件是属于同一个虚拟机和同一个Application的。

可以这么理解：一个应用的多进程，相当于两个不同的应用采用了ShareUID的模式。

# IPC基础概念

## 序列化

### Parcelable接口

**简单使用**

### Serializable和Parcelable的区别

Serializable使用IO读写存储在硬盘上。序列化过程使用了反射技术，并且期间产生临时对象，容易引发频繁的gc。优点代码少。

Parcelable是直接在内存中读写，我们知道内存的读写速度肯定优于硬盘读写速度，所以Parcelable序列化方式性能上要优于Serializable方式很多。但是代码写起来相比Serializable方式麻烦一些。

在这两种情况下建议使用Serializable：将对象序列化到存储设备，将序列化对象通过网络传输。

### Intent对象为什么要序列化

假如两个avtivity传递的是一个对象，那么当在TwoActivity里继续操作MainActivity的对象那么必将造成内存泄漏。

## Binder

这部分内容可以略过，直接看总结。

Binder是客户端和服务端进行通信的媒介。

Android开发中，Binder主要用在Service中，包括AIDL和Messenger，其中普通的Service中的Binder不涉及进程间通信。

首先看客户端和服务端在不在同一个进程，如果在的就不会走跨进程的transact过程，直接返回服务端的Stub对象，反之会走跨进程的transact过程，返回代理对象，也就是Stub.Proxy。（因为不在同一进程，不能传递同一对象，所以这里传递代理对象）

以下代码是自动生成的，为了方便看，我把分析写在代码的注释上。

```java
//所有可以在Binder中传输的接口都需要继承IInterface，同时自己是一个接口。
public interface IBookManager extends android.os.IInterface {
    //首先声明了两个方法，这两个方法是在之前的IBookManager.aidl文件中声明的。
    public java.util.List<com.mezzsy.androidlearn.Book> getBookList() throws android.os.RemoteException;

    public void addBook(com.mezzsy.androidlearn.Book book) throws android.os.RemoteException;

    //声明了一个内部类Stub，这个Stub是一个Binder类，当客户端和服务端都位于同一个进程时，方法调用不会走跨进程的transact过程，而当两者位于不同进程时，方法调用需要走transact过程，这个逻辑由Stub的内部代理类Proxy来完成，所以这个接口的核心就在Stub和Proxy。
    public static abstract class Stub extends android.os.Binder implements com.mezzsy.androidlearn.IBookManager {
        //声明两个整型的id分别用于标识这两个方法，这两个id用于标识在transact过程中客户端所请求的到底是哪个方法。
        static final int TRANSACTION_getBookList = (android.os.IBinder.FIRST_CALL_TRANSACTION + 0);
        
        static final int TRANSACTION_addBook = (android.os.IBinder.FIRST_CALL_TRANSACTION + 1);
        
        //Binder的唯一标识，一般用于当前Binder的类名表示。
        private static final java.lang.String DESCRIPTOR = "com.mezzsy.androidlearn.IBookManager";

        public Stub() {
            this.attachInterface(this， DESCRIPTOR);
        }

        //用于将服务端的Binder对象转换成客户端所需的AIDL接口类型的对象，这种转换是区分进程的，如果客户端和服务端位于同一进程，那么此方法返回的就是服务端的Stub对象本身，否则返回的就是系统封装后的Stub.Proxy。
        public static com.mezzsy.androidlearn.IBookManager asInterface(android.os.IBinder obj) {
            if ((obj == null)) {
                return null;
            }
            android.os.IInterface iin = obj.queryLocalInterface(DESCRIPTOR);
            if (((iin != null) && (iin instanceof com.mezzsy.androidlearn.IBookManager))) {
                return ((com.mezzsy.androidlearn.IBookManager) iin);
            }
            return new com.mezzsy.androidlearn.IBookManager.Stub.Proxy(obj);//返回代理对象
        }

        //返回当前的Binder
        @Override
        public android.os.IBinder asBinder() {
            return this;
        }

        //这个方法运行在服务端中的Binder线程池，当客户端发起跨线程请求时，远程请求会通过系统底层封装后交给此方法来处理。
        @Override
        public boolean onTransact(int code， android.os.Parcel data， android.os.Parcel reply， int flags) throws android.os.RemoteException {
            switch (code) {
                case INTERFACE_TRANSACTION: {
                    reply.writeString(DESCRIPTOR);
                    return true;
                }
                case TRANSACTION_getBookList: {
                    data.enforceInterface(DESCRIPTOR);
                    java.util.List<com.mezzsy.androidlearn.Book> _result = this.getBookList();
                    reply.writeNoException();
                    reply.writeTypedList(_result);
                    return true;
                }
                case TRANSACTION_addBook: {
                    data.enforceInterface(DESCRIPTOR);
                    com.mezzsy.androidlearn.Book _arg0;
                    if ((0 != data.readInt())) {
                        _arg0 = com.mezzsy.androidlearn.Book.CREATOR.createFromParcel(data);
                    } else {
                        _arg0 = null;
                    }
                    this.addBook(_arg0);
                    reply.writeNoException();
                    return true;
                }
            }
            return super.onTransact(code， data， reply， flags);
        }

        private static class Proxy implements com.mezzsy.androidlearn.IBookManager {
            private android.os.IBinder mRemote;

            Proxy(android.os.IBinder remote) {
                mRemote = remote;
            }

            @Override
            public android.os.IBinder asBinder() {
                return mRemote;
            }

            public java.lang.String getInterfaceDescriptor() {
                return DESCRIPTOR;
            }

            //这个方法运行在客户端
            @Override
            public java.util.List<com.mezzsy.androidlearn.Book> getBookList() throws android.os.RemoteException {
                android.os.Parcel _data = android.os.Parcel.obtain();
                android.os.Parcel _reply = android.os.Parcel.obtain();
                java.util.List<com.mezzsy.androidlearn.Book> _result;
                try {
                    _data.writeInterfaceToken(DESCRIPTOR);
                    mRemote.transact(Stub.TRANSACTION_getBookList， _data， _reply， 0);
                    _reply.readException();
                    _result = _reply.createTypedArrayList(com.mezzsy.androidlearn.Book.CREATOR);
                } finally {
                    _reply.recycle();
                    _data.recycle();
                }
                return _result;
            }

            //这个方法运行在客户端
            @Override
            public void addBook(com.mezzsy.androidlearn.Book book) throws android.os.RemoteException {
                android.os.Parcel _data = android.os.Parcel.obtain();
                android.os.Parcel _reply = android.os.Parcel.obtain();
                try {
                    _data.writeInterfaceToken(DESCRIPTOR);
                    if ((book != null)) {
                        _data.writeInt(1);
                        book.writeToParcel(_data， 0);
                    } else {
                        _data.writeInt(0);
                    }
                    mRemote.transact(Stub.TRANSACTION_addBook， _data， _reply， 0);
                    _reply.readException();
                } finally {
                    _reply.recycle();
                    _data.recycle();
                }
            }
        }
    }
}
```

补充说明：

首先，当客户端发起远程请求时，由于当前线程会被挂起直至服务端进程返回数据，所以**如果一个远程方法是很耗时的**，那么不能在UI线程中发起此远程请求；

其次，由于服务端的Binder方法运行在Binder的线程池中，所以Binder方法不管是否耗时都应该采用同步的方式去实现，因为它已经运行在一个线程中了。

![20180915145224](http://111.230.96.19:8081/image/20180915145224.png)

### Binder源码分析总结

用户创建AIDL接口文件，系统会根据这个文件创建对应的接口。这个接口的核心实现是其内部类Stub和Stub的内部代理类。

服务端会传递一个Binder对象（如果在同一个进程，两个对象的地址相同；否则不同，由上面的通信模型可知，这是一个Binder实体的引用），`mBookManager = IBookManager.Stub.asInterface(service);`，传入asInterface方法获取对象，如果客户端和服务端位于同一进程，那么此方法返回的就是服务端的Stub对象，否则返回的就是系统封装后的代理对象。

以下对于同一进程的情况省略。

当客户端调用方法时，代理对象会将请求交给服务端运行。服务端通过方法标识可以确定客户端所请求的目标方法是什么，接着从data中取出目标方法所需的参数（如果目标方法有参数的话），然后执行目标方法。当目标方法执行完毕后，就向reply中写入返回值（如果目标方法有返回值的话）。此过程在服务端的onTransact方法（运行在Binder线程池）中进行转发。如果此方法返回false，那么客户端的请求会失败，因此可以利用这个特性来做权限验证。

代理对象要做的事情就是，封装客户端请求的参数交给服务端，然后获取回复，根据这个回复返回结果。

本质是代理模式的实现。

### Binder通信模型总结

有不懂的地方可以看笔记：[跨进程通信](./Android的跨进程通信.md)

Binder涉及的4个主要模块，分别是：

- **Binder Client**：相当于客户端。
- **Binder Server**：相当于服务器。
- **ServerManager**：相当于DNS服务器。
- **Binder Driver**：相当于一个路由器。（实现在内核空间里，其余实现在用户空间里）

Binder Driver负责进程之间Binder通信的建立，Binder在进程之间的传递，Binder引用计数管理，数据包在进程之间的传递和交互等一系列底层支持。

Server创建了Binder实体，为其取一个字符形式，可读易记的名字，将这个Binder连同名字以数据包的形式通过Binder驱动发送给ServerManager，向ServerManager注册。

Driver为这个穿过进程边界的Binder创建位于内核中的实体节点以及ServerManager对实体的引用，将名字及新建的引用打包传递给ServerManager。ServerManager收数据包后，从中取出名字和引用填入一张查找表中。

ServerManager是将字符形式的Binder名字转化成Client中对该Binder的引用，使得Client能够通过Binder名字获得对Server中Binder实体的引用。ServerManager本身对其他进程来说是个Server，可以通过0号引用去访问。

Binder Client需要通过名字获得该Binder的引用。先是通过0号引用去访问ServerManager，ServerManager根据提供的名字来返回binder的引用，Binder Client得到引用后就可以像普通方法调用那样调用Binder实体的方法。

>   Client是在一进程，ServerManager是在另一进程。2者如何联系？
>
>   个人理解：Client通过系统调用访问内核空间，从而访问ServerManager。

这跟DNS中存储的域名到IP地址的映射原理类似。

另外，并不是所有Binder都需要注册给ServerManager广而告之的。Server端可以通过已经建立的Binder连接将创建的Binder实体传给Client，当然这条已经建立的Binder连接必须是通过实名Binder实现。由于这个Binder没有向ServerManager注册名字，所以是个匿名Binder。Client将会收到这个匿名Binder的引用，通过这个引用向位于Server中的实体发送请求。匿名Binder为通信双方建立一条私密通道，只要Server没有把匿名Binder发给别的进程，别的进程就无法通过穷举或猜测等任何方式获得该Binder的引用，向该Binder发送请求。

### Android为什么要采用Binder机制

具体见笔记的Binder设计思想。

Android是基于Linux的，Linux中的跨进程通信包括传统的管道，System V IPC，即消息队列/共享内存/信号量，以及socket，其中只有socket支持Client-Server的通信方式。

一方面是传输性能。socket作为一款通用接口，其传输效率低，开销大，主要用在跨网络的进程间通信和本机上进程间的低速通信。消息队列和管道采用存储-转发方式，即数据先从发送方缓存区拷贝到内核开辟的缓存区中，然后再从内核缓存区拷贝到接收方缓存区，至少有两次拷贝过程。共享内存虽然无需拷贝，但控制复杂，难以使用。

还有一点是出于安全性考虑。Android作为一个开放式，拥有众多开发者的的平台，应用程序的来源广泛，确保智能终端的安全是非常重要的。终端用户不希望从网上下载的程序在不知情的情况下偷窥隐私数据，连接无线网络，长期操作底层设备导致电池很快耗尽等等。

### 最终总结

在底层Binder模型中，Driver负责建立Binder通信以及Binder的传递。

Server创建Binder实体并赋予一个名字，通过Driver交给ServerManager注册。
Driver为这个穿过进程边界的Binder创建位于内核中的实体节点以及ServerManager对实体的引用，将名字及新建的引用打包传递给ServerManager。ServerManager收到数据包后，从中取出名字和引用填入一张查找表中。
这里就有两个实体节点，一个位于Server用户空间中，一个位于内核空间中。这里运用了内存映射的方式，对Server实体的修改会立即响应到内核实体节点中。

Client通过0号引用去访问ServerManager，ServerManager根据提供的名字来返回Server的引用。这里因为是两个进程，进程之间会有进程隔离，所以Driver传递的不是实际的对象，而是一个代理对象。

在上层代码中，Server端创建Stub对象并返回此对象。

在Client端中的onServiceConnected方法中获取到了一个对象，这是底层模型中的一个代理对象，将此对象传入asInterface方法中获取一个代理对象（代理了代理对象）。
调用接口方法时，代理对象将参数封装并传递到Server端运行（在Server端的Binder池中运行），Server将运行结果返回。

## IPC方式

### Bundle

一种轻量级的，最简单的IPC方式。

Bundle实现了Parcelable接口，所以它可以方便地在不同的进程间传输。

Bundle的内部结构其实是Map，传递的数据可以是boolean、byte、int、long、float、double、string等基本类型或它们对应的数组，也可以是对象或对象数组。当Bundle传递的是对象或对象数组时，必须实现Serializable 或Parcelable接口。

#### Bundle和Intent.putExtra的区别

现在要从A界面跳转到B界面或者C界面 ，这样的话就需要写2个Intent，还要涉及的传值的话，Intent就要写两遍添加值的方法。如果用1个Bundle  直接把值先存里边 然后再存到Intent可以更简洁。

另外一个例子  如果我现在有  Activity A ，B ，C；
现在我要把值通过A经过B传给C
你怎么传 如果用Intent的话，A-B先写一遍   再在B中都取出来 然后在把值塞到Intent中 再跳到C   累吗？
如果我在A中用了 Bundle 的话  我把Bundle传给B 在B中再转传到C  C就可以直接去了 
这样的话 还有一个好处就是在B中还可以给Bundle对象添加新的 key - value  同样可以在C中取出来 。

### 使用文件共享

通过序列化写文件，反序列化读文件，这样得到的对象只是内容上一样，本质上还是两个对象。

缺点：容易出现并发读/写的问题。

SharedPreferences 是个特例，SharedPreferences 是Android中提供的轻量级存储方案，它通过键值对的方式来存储数据，在底层实现上它采用XML文件来存储键值对，每个应用的SharedPreferences文件都可以在当前包所在的data目录下查看到。

一般来说，它的目录位于/data/data/package_name/shared_prefs 目录下，其中package_name表示的是当前应用的包名。从本质上来说，SharedPreferences 也属于文件的一种， 但是由于系统对它的读/写有一定的缓存策略，即在内存中会有一份SharedPreferences文件的缓存，因此在多进程模式下，系统对它的读/写就变得不可靠，当面对高并发的读/写访问，Sharedpreferences有很大几率会丢失数据，因此，不建议在进程间通信中使用SharedPreferences。

### Messenger

Messenger是一种轻量级的方式，底层实现是AIDL。

对AIDL进行了封装，另外，一次处理一个请求，使用在服务端不用考虑线程同步的问题。

**基本使用见笔记。**

### AIDL

Messenger是以串行的方式处理客户端发来的消息，如果大量的消息同时发生到服务端，服务端只能一个个处理，如果有大量的并发请求，那么Messenger就不合适了。

当需要跨进程调用服务端的方法，这种情形用Messenger就无法做到了，但是可以使用AIDL来实现跨进程的方法调用。

在AIDL中，不是所有文件都可以使用的，以下可以使用：

- 基本数据类型；
- String和CharSequence
- List：只支持ArrayList，里面的元素要能够被AIDL支持。
- Map：只支持HashMap，里面的元素要能够被AIDL支持。
- Parcelable：所有实现了Parcelable接口的对象。
- AIDL：所有的AIDL接口本身也可以在AIDL中使用。

> 另外，AIDL所支持的是抽象的List，而List是一个接口，因此服务器虽然返回的是CopyOnWriteArrayList，但是在Binder中会按照List的规范去访问数据最终形成一个新的ArrayList传递给客户端。与此类似的还有ConcurrentHashMap。

AIDL除了基本数据类型，其他类型的都要标上方向：in、out、inout。

AIDL接口中只支持方法，不支持声明静态常量。

**基本用法见笔记**

回顾流程：

首先创建一个Service和一个AIDL接口，接着创建一个类继承自AIDL接口中的Stub类并实现Stub中的抽象方法，在Service的onBind方法中返回这个类的对象，然后客户端就可以绑定服务端Service，建立连接后就可以访问远程服务端的方法了。

### ContentProvider

底层实现是Binder。

自定义ContentProvider

```java
public class BookProvider extends ContentProvider {
    private static final String TAG = "BookProvider";
    public BookProvider() {
    }

    @Override
    public int delete(Uri uri， String selection， String[] selectionArgs) {
        Log.d(TAG， "delete: ");
        return 0;
    }

    //用来返回一个Uri请求所对应的MIME类型，比如图片、视频等。
    @Override
    public String getType(Uri uri) {
        Log.d(TAG， "getType: ");
        return null;
    }

    @Override
    public Uri insert(Uri uri， ContentValues values) {
        Log.d(TAG， "insert: ");
        return null;
    }

    @Override
    public boolean onCreate() {
        Log.d(TAG， "onCreate: ");
        return false;
    }

    @Override
    public Cursor query(Uri uri， String[] projection， String selection，
                        String[] selectionArgs， String sortOrder) {
        Log.d(TAG， "query: "+Thread.currentThread().getName());
        return null;
    }

    @Override
    public int update(Uri uri， ContentValues values， String selection，
                      String[] selectionArgs) {
        Log.d(TAG， "update: ");
        return 0;
    }
}

public class ProviderActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_provider);
        Uri uri=Uri.parse("content://com.mezzsy.androidlearn.provider");
        getContentResolver().
                query(uri，null，null，null，null);
        getContentResolver().
                query(uri，null，null，null，null);
        getContentResolver().
                query(uri，null，null，null，null);
    }
}
```

```
log：
09-15 18:16:44.112 26489-26489/com.mezzsy.androidlearn D/BookProvider: onCreate: 
09-15 18:16:45.384 26489-26489/com.mezzsy.androidlearn D/BookProvider: query: main
    query: main
    query: main
09-15 18:17:45.928 26489-26489/com.mezzsy.androidlearn D/BookProvider: query: main
    query: main
    query: main
09-15 18:17:49.253 26489-26489/com.mezzsy.androidlearn D/BookProvider: query: main
    query: main
    query: main
09-15 18:17:51.423 26489-26489/com.mezzsy.androidlearn D/BookProvider: query: main
    query: main
    query: main

```

除了onCreate运行在主线程，其他五个方法均由外界回调运行在Binder线程池中。

> 书原文是说query会运行在Binder线程池中，而实际log显示，运行在UI线程中。

### Socket

Socket也称为“套接字”，是网络通信中的概念，它分为流式套接字和用户数据报套接字两种，分别对应于网络的传输层中的TCP和UDP协议。

## Binder连接池

每个业务模块创建自己的AIDL接口并实现此接口，这个时候不同业务模块之间是不能有耦合的，使用实现细节要单独开来，然后向服务端提供自己的唯一标识和其对应的Binder对象；对于服务端来说，只需要一个Service就可以了，服务端提供一个queryBinder接口，这个接口能够根据业务模块的特征来返回相应的Binder对象给它们，不同的业务模块拿到所需的Binder对象后就可以进行远程方法调用了。

![20180915184922](http://111.230.96.19:8081/image/20180915184922.png)

简单说一下：就是在Service的onBind返回一个Binder，这个Binder是一个Binder池（自己定义的），里面有个方法用来让客户端选择需要的Binder。

## 选用合适的IPC方式

![20180915191148](http://111.230.96.19:8081/image/20180915191148.png)

# Android中代理模式的实现

代理模式中的角色：

抽象被代理类、被代理类、代理类、客户类（使用代理类的类）。

Android中有不少关于代理模式的实现，比如AndroidManagerProxy代理类，被代理类是ActivityManagerNative的子类ActivityManagerService。

AndroidManagerProxy实现了IAndroidManager接口，这个接口相当于抽象被代理类

![20190105114105](http://111.230.96.19:8081/image/20190105114105.png)

ActivityManagerService和AndroidManagerProxy分别运行在不同的进程中，它们的通信是通过Binder来进行的。

AndroidManagerProxy将数据打包跨进程传递给ActivityManagerService处理并返回结果。