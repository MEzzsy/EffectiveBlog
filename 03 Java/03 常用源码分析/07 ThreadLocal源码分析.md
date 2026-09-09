# get

```java
public T get() {
    Thread t = Thread.currentThread();
    ThreadLocalMap map = getMap(t);
    if (map != null) {
        ThreadLocalMap.Entry e = map.getEntry(this);
        if (e != null) {
            T result = (T)e.value;
            return result;
        }
    }
    return setInitialValue();
}
```

```java
private T setInitialValue() {
    T value = initialValue();
    Thread t = Thread.currentThread();
    ThreadLocalMap map = getMap(t);
    if (map != null)
        map.set(this, value);
    else
        createMap(t, value);
    return value;
}
```

```java
void createMap(Thread t, T firstValue) {
    t.threadLocals = new ThreadLocalMap(this, firstValue);
}
```

1.   从当前线程取出ThreadLocalMap。
2.   调用ThreadLocalMap的getEntry获取该线程的本地变量。
3.   如果没有本地变量，那么就调用initialValue方法初始化一个，默认是null，需要子类实现。
4.   如果没有ThreadLocalMap，就创建一个ThreadLocalMap，并设置给当前线程（懒加载）。

# set

```java
public void set(T value) {
    Thread t = Thread.currentThread();
    ThreadLocalMap map = getMap(t);
    if (map != null)
        map.set(this, value);
    else
        createMap(t, value);
}
```

1.   如果有ThreadLocalMap，那么就set进ThreadLocalMap中。
2.   如果没有ThreadLocalMap，那么就懒加载ThreadLocalMap。

# ThreadLocalMap的set

```java
private void set(ThreadLocal<?> key, Object value) {
    Entry[] tab = table;
    int len = tab.length;
    int i = key.threadLocalHashCode & (len-1);

    for (Entry e = tab[i];
         e != null;
         e = tab[i = nextIndex(i, len)]) {
        ThreadLocal<?> k = e.get();

        if (k == key) {
            e.value = value;
            return;
        }

        if (k == null) {
            replaceStaleEntry(key, value, i);
            return;
        }
    }

    tab[i] = new Entry(key, value);
    int sz = ++size;
    if (!cleanSomeSlots(i, sz) && sz >= threshold)
        rehash();
}
```

```java
private static int nextIndex(int i, int len) {
    return ((i + 1 < len) ? i + 1 : 0);
}
```

1.   ThreadLocalMap有个Entry类型的数组，存放所有的本地线程变量。一个线程对应一个ThreadLocalMap，所以不需要考虑线程安全。
2.   根据ThreadLocal的hash值算出该变量的存放位置，如果出现hash冲突，解决办法就是往后挪一个，如果到尾了，就放在0位置。
3.   然后根据最终的存放位置，new一个Entry并放入table中。

# ThreadLocalMap的get

```java
private Entry getEntry(ThreadLocal<?> key) {
    int i = key.threadLocalHashCode & (table.length - 1);
    Entry e = table[i];
    if (e != null && e.get() == key)
        return e;
    else
        return getEntryAfterMiss(key, i, e);
}

private Entry getEntryAfterMiss(ThreadLocal<?> key, int i, Entry e) {
    Entry[] tab = table;
    int len = tab.length;

    while (e != null) {
        ThreadLocal<?> k = e.get();
        if (k == key)
            return e;
        if (k == null)
            expungeStaleEntry(i);
        else
            i = nextIndex(i, len);
        e = tab[i];
    }
    return null;
}
```

1.   根据ThreadLocal的hash值算出存放位置。
2.   如果对应位置不对，那么出现hash冲突，解决办法就是往后挪一个。
3.   如有返回，没有返回null。

# 总结

1.   当某些数据是以线程为作用域且在不同线程具有不同的数据副本时，就可以考虑使用ThreadLocal（比如Looper）。
2.   一个ThreadLocal对象对应一个线程本地变量。
3.   每个线程内部有一个ThreadLocalMap变量，以ThreadLocal对象为key，对应的对象为value。
4.   ThreadLocalMap是懒加载，只有操作ThreadLocal时，才会初始化，table的初始大小是16。
5.   Entry本身是ThreadLocal的弱引用。用弱引用是因为，有些线程是长时间存在的（如主线程），如果使用强引用，可能会导致内存泄露。
6.   当一个线程想要获取或者放置一个对象时，通过ThreadLocal的get和set方法。
7.   set方法
      先获取Thread，再取出这个Thread的ThreadLocalMap。 
      然后根据hash值和table数组长度获取数组位置。 如果产生hash冲突，解决办法是位置+1，如果超出了数组长度就归0。 
      找到合适的位置后，放入数组中。
      如果超出阈值就扩容，扩容是容量*2。
8.   get方法
      先获取Thread，再取出这个Thread的ThreadLocalMap。
      然后根据此ThreadLocal取出值，如果有值就返回。
      如果没有值，就放置一个初始值，默认值是null，可以由ThreadLocal的子类实现。最后返回初始值。