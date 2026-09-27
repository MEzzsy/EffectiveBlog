它主要的作用就是将程序的内部的数据和外部进行共享，为数据提供外部访问接口，被访问的数据主要以数据库的形式存在，而且还可以选择共享哪一部分的数据。这样一来，对于程序当中的隐私数据可以不共享，从而更加安全。contentprovider是android中一种跨程序共享数据的重要组件。

**ContentProvider、ContentResolver、ContentObserver 之间的关系**

- ContentProvider来提供内容给别的应用来操作。
- ContentResolver来操作别的应用数据，当然在自己的应用中也可以。 
- ContentObserver——内容观察者，目的是观察(捕捉)特定Uri引起的数据库的变化，继而做一些相应的处理，每次通过insert、delete、update改变数据库内容时，都会调用ContentObserver的onChange方法，因此，可以在这个方法内做出针对数据库变化的反应，比如更新UI等。



**奇妙的用法**

```xml
<provider
    android:name=".basic.provider.TestContentProvider"
    android:authorities="mezzsy.test.provider"
    android:enabled="true"
    android:exported="true"></provider>
```

```
I/TestContentProvider: onCreate: 
I/MyApplication: onCreate: 
```

注册一个provider，在应用启动时，TestContentProvider的onCreate会比Application的onCreate要早，基于这个性质，第三方库可以通过注册provider省去手动调用init的代码
