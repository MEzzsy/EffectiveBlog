# 基本使用

```java
private void retrofit() {
    Retrofit retrofit = new Retrofit.Builder()
            .client(new OkHttpClient())
            .addCallAdapterFactory(RxJava2CallAdapterFactory.create())
            .baseUrl(HOST)
            .build();

    RequestService service = retrofit.create(RequestService.class);

    service.getDefaultUser()
            .subscribeOn(Schedulers.io())
            .observeOn(AndroidSchedulers.mainThread())
            .subscribe(responseBody -> {
                Log.d(TAG, "retrofit: \n" + responseBody.string());
            });
}

/**
 * Retrofit2所需接口
 */
interface RequestService {
    @GET("/demo/getDefaultUser")
    Observable<ResponseBody> getDefaultUser();
}
```

# 对外接口

## Call\<T\>

真正发出请求的对象接口。

### 接口方法

**Response\<T\> execute()**

同步发送请求和返回结果。

**void enqueue(Callback\<T\> callback);**

异步发送请求和返回结果。

**boolean isExecuted()**

是否同步执行完。

**void cancel()**

取消请求。

**boolean isCanceled()**

是否取消。

**Request request()**

最初的HTTP请求。

## CallAdapter<R, T>

可以把`Call`对象转化为另外一个对象，如`Observable`

## Callback\<T\>

这个接口就是retrofit请求数据返回的接口，只有两个方法void onResponse(Response\<T\> response)和void onFailure(Throwable t)

## Converter<F, T>

这个接口主要的作用就是将HTTP返回的数据解析成Java对象，主要有Xml、Gson、protobuf等等，你可以在创建`Retrofit`对象时添加你需要使用的`Converter`实现

# Retrofit的创建

```java
Retrofit retrofit = new Retrofit.Builder()
                .client(new OkHttpClient())
                .addCallAdapterFactory(RxJava2CallAdapterFactory.create())
                .baseUrl(HOST)
                .build();
```

用build模式来创建

```java
Builder(Platform platform) {
  this.platform = platform;
}

public Builder() {
  this(Platform.get());
}
```

platform这个类是用来识别当前是什么平台，因为Retrofit可以用在Java和Android平台。

另外，Retrofit内部嵌了OkHttp，我之前还想怎么把这两者封装，多此一举。

```java
public Builder client(OkHttpClient client) {
  return callFactory(checkNotNull(client, "client == null"));
}
```

```java
okhttp3.Call.Factory callFactory = this.callFactory;
if (callFactory == null) {
  callFactory = new OkHttpClient();
}
```

# Service代理对象的创建

```java
RequestService service = retrofit.create(RequestService.class);
```

create源码

```java
public <T> T create(final Class<T> service) {
  //判断Service是否合法
  Utils.validateServiceInterface(service);
  //提前验证Service，一般validateEagerly为false，这里略过。
  if (validateEagerly) {
    eagerlyValidateMethods(service);
  }
  //返回一个代理对象
  return (T) Proxy.newProxyInstance(service.getClassLoader(), new Class<?>[] { service },
      new InvocationHandler() {
        private final Platform platform = Platform.get();
        private final Object[] emptyArgs = new Object[0];

        @Override public Object invoke(Object proxy, Method method, @Nullable Object[] args)
            throws Throwable {        
          if (method.getDeclaringClass() == Object.class) {
            return method.invoke(this, args);
          }       
          if (platform.isDefaultMethod(method)) {
            return platform.invokeDefaultMethod(method, service, proxy, args);
          }
          return loadServiceMethod(method).invoke(args != null ? args : emptyArgs);
        }
      });
}
```

最后return返回一个代理对象，Java的动态代理可以见这篇笔记：[Java反射相关](https://mezzsy.github.io/2019/04/01/Java/Java反射机制和泛型/)

代理模式简单概念：

- **Subject**：抽象主题类，该类的主要职责是声明真实主题与代理的共同接口方法，一般是一个接口。
- **RealSubject**：真实主题类，该类也称为被委托类或者被代理类，该类定义了代理所表示的真实对象，由其执行具体的业务逻辑方法，而客户类则通过代理类间接地调用此类中定义的方法。这里可以认为是ServiceMethod。
- **ProxySubject**：代理类，该类也称为委托类或代理类，该类持有一个对真实主题类的一个引用，在其所实现的接口方法中调用真实主题类中相应的接口方法执行，以此起到代理的作用。

这里create方法并没有太重要的逻辑，重要的是其匿名内部类InvocationHandler的实现

```java
new InvocationHandler() {
  private final Platform platform = Platform.get();
  private final Object[] emptyArgs = new Object[0];

  @Override public Object invoke(Object proxy, Method method, @Nullable Object[] args)
      throws Throwable {
    //代码1
    if (method.getDeclaringClass() == Object.class) {
      return method.invoke(this, args);
    }
    //代码2
    if (platform.isDefaultMethod(method)) {
      return platform.invokeDefaultMethod(method, service, proxy, args);
    }
    //见代理对象的调用
    return loadServiceMethod(method).invoke(args != null ? args : emptyArgs);
  }
}
```

**代码1**

如果调用的Object中的方法，那么就调用此匿名内部类实现的Object方法

```java
Log.d(TAG, "retrofit: \n" + service.toString());
Log.d(TAG, "retrofit: \n" + service.hashCode());

/*
retrofit2.Retrofit$1@f5c53ae
257708974
*/
```

**代码2**

这处是判断调用的方法是否是默认方法，因为Java8之后，接口可以有默认方法。

platform是Android或者Java平台，这里只讨论Android平台。

Android的platform并没有实现invokeDefaultMethod方法，而是调用父类的invokeDefaultMethod方法：

```java
@Nullable Object invokeDefaultMethod(Method method, Class<?> declaringClass, Object object,
    @Nullable Object... args) throws Throwable {
  throw new UnsupportedOperationException();
}
```

直接报异常，实际测试也是这样。

```java
service.hello();
```

```java
default void hello() {
    Log.d(TAG, "hello: ");
}
```

以上的代码分析属于细节，这里分析着玩玩的，不用认真看。

# 代理对象的调用

当创建完代理对象对象后，就可以通过代理代理对象来调用需要的方法。

```java
service.getDefaultUser()
        .subscribeOn(Schedulers.io())
        .observeOn(AndroidSchedulers.mainThread())
        .subscribe(responseBody -> {
            Log.d(TAG, "retrofit: \n" + responseBody.string());
        });
```

而这里的具体实现是InvocationHandler的invoke方法：

```java
return loadServiceMethod(method).invoke(args != null ? args : emptyArgs);
```

看一下loadServiceMethod方法

```java
ServiceMethod<?> loadServiceMethod(Method method) {
  //获取缓存
  ServiceMethod<?> result = serviceMethodCache.get(method);
  if (result != null) return result;

  //如果没有缓存，就新建一个。
  synchronized (serviceMethodCache) {
    result = serviceMethodCache.get(method);
    //再次判空防止再次新建，类似DCL单例模式的实现
    if (result == null) {
      //ServiceMethod对象的创建
      result = ServiceMethod.parseAnnotations(this, method);
      //放入缓存
      serviceMethodCache.put(method, result);
    }
  }
  return result;
}
```

ServiceMethod对象的创建见下面的小节，记得回过来看其invoke方法

```java
@Override ReturnT invoke(Object[] args) {
  return callAdapter.adapt(
      new OkHttpCall<>(requestFactory, args, callFactory, responseConverter));
}
```

由于在创建Retrofit的时候传入的是RxJava2CallAdapterFactory，这里的callAdapter是RxJava2CallAdapter类型，但是这样要分析RxJava2，而这里是分析的Retrofit2，所以换一个相似的Adapter进行分析，思路是一样的。

CompletableFutureCallAdapterFactory中的adapt方法。

```java
@Override public CompletableFuture<R> adapt(final Call<R> call) {
    final CompletableFuture<R> future = new CompletableFuture<R>() {
      @Override public boolean cancel(boolean mayInterruptIfRunning) {
        if (mayInterruptIfRunning) {
          call.cancel();
        }
        return super.cancel(mayInterruptIfRunning);
      }
    };

    call.enqueue(new Callback<R>() {
      @Override public void onResponse(Call<R> call, Response<R> response) {
        if (response.isSuccessful()) {
          future.complete(response.body());
        } else {
          future.completeExceptionally(new HttpException(response));
        }
      }

      @Override public void onFailure(Call<R> call, Throwable t) {
        future.completeExceptionally(t);
      }
    });

    return future;
  }
}
```

这里看到了很熟悉的OkHttp的用法：`call.enqueue`，OkHttp3的分析见[OkHttp3源码分析](https://mezzsy.github.io/2019/07/22/源码分析/OkHttp3源码分析/)，这里简单说一下：

Call封装了请求参数，根据这些参数就可以进行网络请求。

这里用的是enqueue异步请求，在线程池中进行请求，所以外部不用再另起一个线程。

在OkHttp的拦截器中分为应用拦截器和网络拦截器，重要的是ConnectInterceptor（应用拦截器）和CallServerInterceptor（网络拦截器）。

ConnectInterceptor负责打开Socket连接。

CallServerInterceptor负责读写数据流。

请求完成后返回响应体。

这样代理对象就返回了用户需要的响应体。

# ServiceMethod对象的创建

ServiceMethod对象是一个十分重要的对象，每次调用网络请求都会用到它。

看一下创建的方法parseAnnotations：

```java
static <T> ServiceMethod<T> parseAnnotations(Retrofit retrofit, Method method) {
  //代码1
  RequestFactory requestFactory = RequestFactory.parseAnnotations(retrofit, method);

  //检测方法的返回类型
  Type returnType = method.getGenericReturnType();
  if (Utils.hasUnresolvableType(returnType)) {
    throw methodError(method,
        "Method return type must not include a type variable or wildcard: %s", returnType);
  }
  if (returnType == void.class) {
    throw methodError(method, "Service methods cannot return void.");
  }

  //代码2
  return HttpServiceMethod.parseAnnotations(retrofit, method, requestFactory);
}
```

**代码1**

将之前配置的参数和调用Service中的方法的参数进行封装。

```java
RequestFactory(Builder builder) {
  method = builder.method;
  baseUrl = builder.retrofit.baseUrl;
  httpMethod = builder.httpMethod;
  relativeUrl = builder.relativeUrl;
  headers = builder.headers;
  contentType = builder.contentType;
  hasBody = builder.hasBody;
  isFormEncoded = builder.isFormEncoded;
  isMultipart = builder.isMultipart;
  parameterHandlers = builder.parameterHandlers;
}
```

**代码2**

HttpServiceMethod是ServiceMethod的实现类，看一下其parseAnnotations方法

```java
static <ResponseT, ReturnT> HttpServiceMethod<ResponseT, ReturnT> parseAnnotations(
    Retrofit retrofit, Method method, RequestFactory requestFactory) {
  CallAdapter<ResponseT, ReturnT> callAdapter = createCallAdapter(retrofit, method);
  
  Type responseType = callAdapter.responseType();
  if (responseType == Response.class || responseType == okhttp3.Response.class) {
    throw methodError(method, "'"
        + Utils.getRawType(responseType).getName()
        + "' is not a valid response body type. Did you mean ResponseBody?");
  }
  if (requestFactory.httpMethod.equals("HEAD") && !Void.class.equals(responseType)) {
    throw methodError(method, "HEAD method must use Void as response type.");
  }

  Converter<ResponseBody, ResponseT> responseConverter =
      createResponseConverter(retrofit, method, responseType);

  okhttp3.Call.Factory callFactory = retrofit.callFactory;
  
  return new HttpServiceMethod<>(requestFactory, callFactory, callAdapter, responseConverter);
}
```

HttpServiceMethod主要是将请求参数和一些在Retrofit中配置的Adapter封装。

## 小结

ServiceMethod对象的创建和一般的初始化差不多，就是封装了一些参数，便于之后的使用。

# 总结

Retrofit2以动态代理的方式进行网络请求。

用户通过代理对象进行网络请求。

代理对象通过实现InvocationHandler的invoke方法，对每一次网络请求拦截并调用invoke方法。具体实现是ServiceMethod的invoke。

ServiceMethod在缓存中，如果没有就新建，主要是封装了参数。

真正执行网络请求的还是OkHttp。