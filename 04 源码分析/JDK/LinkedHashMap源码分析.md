# 介绍

LinkedHashMap继承了HashMap，和HashMap一样内部有个Hash表，而且还有一个链表，这个链表在迭代的时候会有到。这个特性是由键值对节点决定的。

```java
static class LinkedHashMapEntry<K,V> extends HashMap.Node<K,V> {
    LinkedHashMapEntry<K,V> before, after;
    LinkedHashMapEntry(int hash, K key, V value, Node<K,V> next) {
        super(hash, key, value, next);
    }
}
```

# 构造方法

```java
public LinkedHashMap(int initialCapacity,
                     float loadFactor,
                     boolean accessOrder) {
    super(initialCapacity, loadFactor);
    this.accessOrder = accessOrder;
}
```

这是参数最多的构造方法，其余的参数和HashMap一样，accessOrder是迭代顺序，如果是ture，那么会按照访问（插入算一次访问）的顺序，如果是false（也就是按照HashMap的迭代方式），那么会按照插入的顺序，默认是false。

如：

```java
LinkedHashMap<Integer, Integer> map
        = new LinkedHashMap<>(16, 0.75f,true);
for (int i = 0; i < 10; i++) {
    map.put(i, i);
}
for (Map.Entry<Integer, Integer> entry : map.entrySet()) {
    System.out.println(entry);
}
System.out.println("------------------");
map.get(2);
map.get(5);
for (Map.Entry<Integer, Integer> entry : map.entrySet()) {
    System.out.println(entry);
}
```

输出结果：

```
0=0
1=1
2=2
3=3
4=4
5=5
6=6
7=7
8=8
9=9
------------------
0=0
1=1
3=3
4=4
6=6
7=7
8=8
9=9
2=2
5=5
```

# afterNodeAccess

afterNodeAccess与accessOrder有关，如果accessOrder为ture调用了get或者getOrDefault那么会调用此方法。

```java
void afterNodeAccess(Node<K,V> e) { // move node to last
    LinkedHashMapEntry<K,V> last;
    if (accessOrder && (last = tail) != e) {
        LinkedHashMapEntry<K,V> p =
            (LinkedHashMapEntry<K,V>)e, b = p.before, a = p.after;
        p.after = null;
        if (b == null)
            head = a;
        else
            b.after = a;
        if (a != null)
            a.before = b;
        else
            last = b;
        if (last == null)
            head = p;
        else {
            p.before = last;
            last.after = p;
        }
        tail = p;
        ++modCount;
    }
}
```

afterNodeAccess方法主要是将节点移到链表的末尾。算法的思想是将当前节点删除然后添加到结尾。

# put

无，调用的是父类HashMap的put方法，但期间也会调用LinkedHashMap的某些方法。看一下HashMap的put相关方法。

```java
public V put(K key, V value) {
    return putVal(hash(key), key, value, false, true);
}
final V putVal(int hash, K key, V value, boolean onlyIfAbsent,
               boolean evict) {
    Node<K,V>[] tab; Node<K,V> p; int n, i;
    if ((tab = table) == null || (n = tab.length) == 0)
        n = (tab = resize()).length;
    if ((p = tab[i = (n - 1) & hash]) == null)
        tab[i] = newNode(hash, key, value, null);//1.这里调用的是LinkedHashMap的newNode方法。
    else {
        Node<K,V> e; K k;
        if (p.hash == hash &&
            ((k = p.key) == key || (key != null && key.equals(k))))
            e = p;
        else if (p instanceof TreeNode)
            e = ((TreeNode<K,V>)p).putTreeVal(this, tab, hash, key, value);
        else {
            for (int binCount = 0; ; ++binCount) {
                if ((e = p.next) == null) {
                    p.next = newNode(hash, key, value, null);
                    if (binCount >= TREEIFY_THRESHOLD - 1) 
                        treeifyBin(tab, hash);
                    break;
                }
                if (e.hash == hash &&
                    ((k = e.key) == key || (key != null && key.equals(k))))
                    break;
                p = e;
            }
        }
      
      	//新值代替旧值并返回旧值。
        if (e != null) { 
            V oldValue = e.value;
            if (!onlyIfAbsent || oldValue == null)
                e.value = value;
            afterNodeAccess(e);//2.调用LinkedHashMap的afterNodeAccess方法。
            return oldValue;
        }
    }
    ++modCount;
    if (++size > threshold)
        resize();
    afterNodeInsertion(evict);//3.节点插入后的回调
    return null;
}
```

## 代码1

```java
Node<K,V> newNode(int hash, K key, V value, Node<K,V> e) {
    LinkedHashMapEntry<K,V> p =
        new LinkedHashMapEntry<K,V>(hash, key, value, e);
    linkNodeLast(p);//将新节点添加到链表末尾。
    return p;
}
```

```java
private void linkNodeLast(LinkedHashMapEntry<K,V> p) {
    LinkedHashMapEntry<K,V> last = tail;
    tail = p;
    if (last == null)
        head = p;
    else {
        p.before = last;
        last.after = p;
    }
}
```

## 代码2

```java
//将节点移到链表的末尾，注意这里的节点已经是更新后的节点。
void afterNodeAccess(Node<K,V> e) {
    LinkedHashMapEntry<K,V> last;
    if (accessOrder && (last = tail) != e) {
        LinkedHashMapEntry<K,V> p =
            (LinkedHashMapEntry<K,V>)e, b = p.before, a = p.after;
        p.after = null;
        if (b == null)
            head = a;
        else
            b.after = a;
        if (a != null)
            a.before = b;
        else
            last = b;
        if (last == null)
            head = p;
        else {
            p.before = last;
            last.after = p;
        }
        tail = p;
        ++modCount;
    }
}
```

## 代码3

```java
void afterNodeInsertion(boolean evict) { // possibly remove eldest
    LinkedHashMapEntry<K,V> first;
    if (evict && (first = head) != null && removeEldestEntry(first)) {
        K key = first.key;
        removeNode(hash(key), key, null, false, true);
    }
}
```

```java
protected boolean removeEldestEntry(Map.Entry<K,V> eldest) {
    return false;
}
```

这个方法是将最老的节点（链表的头节点）删除，但由于removeEldestEntry默认返回false，这个方法一般不会作什么处理。

## 总结

put调用后会将节点放入Hash表中或者更新节点，并且都会将节点放在LinkedHashMap的链表的末尾。

# get

```java
public V get(Object key) {
    Node<K,V> e;
    if ((e = getNode(hash(key), key)) == null)
        return null;
    if (accessOrder)
        afterNodeAccess(e);
    return e.value;
}
```

和HashMap类似，只是多了一个accessOrder的判断，afterNodeAccess的内容见上。

# remove

无，调用的是HashMap的remove方法，调用完后会回调一个`void afterNodeRemoval(Node<K,V> e)`方法。

```java
void afterNodeRemoval(Node<K,V> e) { // unlink
    LinkedHashMapEntry<K,V> p =
        (LinkedHashMapEntry<K,V>)e, b = p.before, a = p.after;
    p.before = p.after = null;
    if (b == null)
        head = a;
    else
        b.after = a;
    if (a == null)
        tail = b;
    else
        a.before = b;
}
```

很简单，就是删除链表节点。

# 迭代

在构造方法那一章做了一个示例，这里再做一次：

```java
LinkedHashMap<Integer, Integer> map
        = new LinkedHashMap<>(16, 0.75f,true);
for (int i = 0; i < 5; i++) {
    map.put(i, i);
}
for (Map.Entry<Integer, Integer> entry : map.entrySet()) {
    System.out.println(entry);
}
System.out.println("------------------");
map.get(1);
map.get(3);
for (Map.Entry<Integer, Integer> entry : map.entrySet()) {
    System.out.println(entry);
}
```

结果

```
0=0
1=1
2=2
3=3
4=4
------------------
0=0
2=2
4=4
1=1
3=3
```

最新的访问（插入）在迭代的时候会出现在最后。这和链表的结构以及迭代方式有关，最新操作的节点总是会放在链表的最后面，而迭代是从头跌代。

```java
abstract class LinkedHashIterator {
    LinkedHashMapEntry<K,V> next;
    LinkedHashMapEntry<K,V> current;
    int expectedModCount;

    LinkedHashIterator() {
        next = head;//从头开始跌代
        expectedModCount = modCount;
        current = null;
    }

    public final boolean hasNext() {
        return next != null;
    }

    final LinkedHashMapEntry<K,V> nextNode() {
        LinkedHashMapEntry<K,V> e = next;
        if (modCount != expectedModCount)
            throw new ConcurrentModificationException();
        if (e == null)
            throw new NoSuchElementException();
        current = e;
        next = e.after;
        return e;
    }

    public final void remove() {
        Node<K,V> p = current;
        if (p == null)
            throw new IllegalStateException();
        if (modCount != expectedModCount)
            throw new ConcurrentModificationException();
        current = null;
        K key = p.key;
        removeNode(hash(key), key, null, false, false);
        expectedModCount = modCount;
    }
}
```

# 总结

LinekedHashMap继承了HashMap，总体上与HashMap一致，不同点在于LinekedHashMap内部有一个双向链表，这个双向链表决定了迭代的顺序。

accessOrder为false（默认），那么按照put的顺序进行迭代；如果为true，那么按照操作（put、get）的顺序。

