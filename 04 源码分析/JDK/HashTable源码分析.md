# 构造函数

## 参数

- initialCapacity 初始化容量
- loadFactor  加载因子

## public Hashtable(int initialCapacity, float loadFactor)

1. initialCapacity不能小于0否则报错，等于0会默认成1。
2. loadFactor不能小于0，也不能是个非数（NAN）
3. 原生java里的限制是min(initialCapacity * loadFactor, MAX_ARRAY_SIZE + 1)，而Android里改了，去掉了加载因子。

```
// Android-changed: Ignore loadFactor when calculating threshold from initialCapacity
// threshold = (int)Math.min(initialCapacity * loadFactor, MAX_ARRAY_SIZE + 1);
threshold = (int)Math.min(initialCapacity, MAX_ARRAY_SIZE + 1);
```

## public Hashtable(int initialCapacity)

```
public Hashtable(int initialCapacity) {
    this(initialCapacity, 0.75f);
}
```

默认加载因子是0.75f

## public Hashtable()

```
public Hashtable() {
    this(11, 0.75f);
}
```

默认initialCapacity是11，loadFactor是0.75f

# 值

分派给arrays的最大容量

```
private static final int MAX_ARRAY_SIZE = Integer.MAX_VALUE - 8;
```

MAX_ARRAY_SIZE为2147483639

> 为什么要减去8呢？
>
> 因为某些VM会在数组中保留一些头字，尝试分配这个最大存储容量，可能会导致array容量大于VM的limit，最终导致OutOfMemoryError。

# 方法

## private void addEntry

```
private void addEntry(int hash, K key, V value, int index) {
    modCount++;

    HashtableEntry<?,?> tab[] = table;
    if (count >= threshold) {
        // Rehash the table if the threshold is exceeded
        rehash();

        tab = table;
        hash = key.hashCode();
        index = (hash & 0x7FFFFFFF) % tab.length;
    }

    // Creates the new entry.
    @SuppressWarnings("unchecked")
    HashtableEntry<K,V> e = (HashtableEntry<K,V>) tab[index];
    tab[index] = new HashtableEntry<>(hash, key, value, e);
    count++;
}
```

当调用put方法存入数据的时候会调用此方法，如果此时已存的数量（count）大于设定的阈值（threshold），那么会对HashTable进行扩容。

## protected void rehash()

```
protected void rehash() {
    //...
    int newCapacity = (oldCapacity << 1) + 1;
    if (newCapacity - MAX_ARRAY_SIZE > 0) {
        if (oldCapacity == MAX_ARRAY_SIZE)
            // Keep running with MAX_ARRAY_SIZE buckets
            return;
        newCapacity = MAX_ARRAY_SIZE;
    }
   //...
}
```

提高容量，每次变成2n+1，n为原容量，如果改变之后比MAX_ARRAY_SIZE还大，那么就等于MAX_ARRAY_SIZE。

# 解析

```
//Android-changed: Renamed Entry -> HashtableEntry
```

android里的java的Entry改名为HashtableEntry

## 1、**Hashtable数据存储数组** 

```
private transient HashtableEntry<?,?>[] table;
```

Hashtable中的key-value都是**存储在table数组中的**。 

## 2、**数据节点HashtableEntry的数据结构** 

HashtableEntry实际上就是一个单向链表。这也是为什么我们说Hashtable是通过拉链法解决哈希冲突的。 HashtableEntry实现了Map.Entry 接口，即实现getKey(), getValue(), setValue(V value), equals(Object o), hashCode()这些函数。这些都是基本的读取/修改key、value值的函数。 

