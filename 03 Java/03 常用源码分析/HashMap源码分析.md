# 知识点总结

1.   HashMap内部采用数组+链表/红黑树，使用散列表解决碰撞冲突的问题，其中数组的每个元素是单链表的头结点，链表/红黑树是用来解决冲突的。
2.   HashMap有两个重要的参数：初始容量和加载因子。初始容量是hash数组的长度，当前加载因子=当前hash数组元素/hash数组长度，最大加载因子为最大能容纳的数组元素个数（默认最大加载因子为0.75，最大值为Integer.MAX_VALUE），当hash数组中的元素个数超出了最大加载因子和容量的乘积时，要对hashMap进行扩容，扩容过程存在于hashmap的put方法中，扩容过程始终以2次方增长。
3.   HashMap是泛型类，key和value可以为任何类型，包括null类型。key为null的键值对永远都放在以table[0]为头结点的链表中。

## 常量介绍

1. static final int DEFAULT_INITIAL_CAPACITY = 1 << 4; -> 数组默认初始容量：16
2. static final int MAXIMUM_CAPACITY = 1 << 30; -> 数组最大容量2 ^ 30 次方
3. static final float DEFAULT_LOAD_FACTOR = 0.75f; -> 默认负载因子的大小：0.75
4. static final int MIN_TREEIFY_CAPACITY = 64; -> 树形最小容量：哈希表的最小树形化容量，超过此值允许表中桶(Node)转化成红黑树
5. static final int TREEIFY_THRESHOLD = 8; -> 树形阈值：当链表长度达到8时，将链表转化为红黑树
6. static final int UNTREEIFY_THRESHOLD = 6; -> 树形阈值：当链表长度小于6时，将红黑树转化为链表
7. int threshold; -> 可存储key-value 键值对的临界值 需要扩充时;值 = 容量 * 加载因子
8. transient int size; 已存储key-value 键值对数量
9. final float loadFactor; -> 负载因子
10. transient Node< K,V>[] table; -> 链表数组（用于存储hashmap的数据）

## 部分方法解析

### 构造方法

```java
public HashMap(int initialCapacity, float loadFactor) {
    if (initialCapacity < 0)
        throw new IllegalArgumentException("Illegal initial capacity: " +
                                           initialCapacity);
    if (initialCapacity > MAXIMUM_CAPACITY)
        initialCapacity = MAXIMUM_CAPACITY;
    if (loadFactor <= 0 || Float.isNaN(loadFactor))
        throw new IllegalArgumentException("Illegal load factor: " +
                                           loadFactor);
    this.loadFactor = loadFactor;
    this.threshold = tableSizeFor(initialCapacity);
}
```

```java
static final int tableSizeFor(int cap) {
    int n = cap - 1;
    n |= n >>> 1;
    n |= n >>> 2;
    n |= n >>> 4;
    n |= n >>> 8;
    n |= n >>> 16;
    return (n < 0) ? 1 : (n >= MAXIMUM_CAPACITY) ? MAXIMUM_CAPACITY : n + 1;
}
```

如果初始容量

### hash

```java
// HashMap计算hash的方式
static final int hash(Object key) {
    int h;
    return (key == null) ? 0 : (h = key.hashCode()) ^ (h >>> 16);
}
// HashMap计算index的方式，n为当前table的len
i = (n - 1) & hash
```

hash方法使用异或运算的目的是为了让哈希码的高位和低位都参与到哈希值的计算中，从而减少哈希冲突的可能性。具体来说，异或运算可以将哈希码的高16位和低16位进行混合，从而增加哈希值的随机性，减少哈希冲突的概率。

### put

1.   计算hash，然后根据hash计算在table中的index。
2.   如果当前位置没有key，那么将键值对放入。
3.   如果有冲突：
     如果是同一个key，那么更新value。
     如果是数组中的节点是红黑树节点，那么就放入树中。
     如果是链表节点，那么放入单链表中的最后一个：
     如果链表的长度超过树化阈值（8），如果数组长度小于64，那么扩容，否则将此链表转化为红黑树。
4.   放入键值对后，如果当前键值对数量超过阈值，那么resize。

### resize

1.   首先创建新的数组，长度为原来的2倍，阈值也变为原来的2倍。
2.   然后对原数组的每一个位置进行遍历，如果有链表，那么会把链表分为2份。

> 这里分为2份的原理是，具体代码见下面的源码部分：
>
> 比如之前的长度10000（16），一个key为1111，一个key为11111，那么根据
> [hash&(n-1)]，它们放在同一个位置。
>
> 扩容后的长度100000。在扩容的方法中利用的是[hash&oldcap]（oldcap为原来的长度）来区分。那么，1111的是0，11111的不为0，这里就分出了2个链表。
>
> 如果有多个key，情况也是如此，最终会分为2个链表，一个low，一个high，low的位置为[原来的坐标]，high的坐标为[原来的坐标+oldcap]。

3.   如果是红黑树（TreeNode不仅表示树节点，也可以表示链表节点），把红黑树当成链表处理，将链表一分为二，一个low，一个high。如果分割后的链表小于阈值，那么保持链表的状态，如果大于阈值，则转为红黑树。

### 树化（treeifyBin方法）

1.   先将单链表节点转为红黑树节点，再转为红黑树。红黑树节点的数据结构不仅能表示树节点，也能表示双向链表节点，所以HashMap的红黑树不仅能表示成树，也能表示成链表。

**什么时候树化？**

桶为数组中的一个节点，size为HashMap中键值对数量，capacity为数组长度。MIN_TREEIFY_CAPACITY(64)树形最小容量，TREEIFY_THRESHOLD(8)树形阈值，UNTREEIFY_THRESHOLD(6)，threshold阈值。

1.   当单链表中的长度>TREEIFY_THRESHOLD，但是capacity<MIN_TREEIFY_CAPACITY，不会变成红黑树，会进行扩容。
2.   当单链表中的长度>TREEIFY_THRESHOLD，而且capacity>=MIN_TREEIFY_CAPACITY，将此单链表转为红黑树。
3.   只要size>threshold，就会进行扩容。
4.   在扩容的时候，桶中元素个数小于非树化阈值（6），就会把树形的桶元素还原为单链表结构。

> 为什么单链表要转为红黑树？
>
> 红黑树所有的操作最坏情况都是O（log（n））的。
> 红黑树的平均查找长度是log(n)，长度为8，查找长度为log(8)=3。
> 链表的平均查找长度为n/2，当长度为8时，平均查找长度为8/2=4，这才有转换成树的必要。链表长度如果是小于等于6，6/2=3，虽然速度也很快的，但是转化为树结构和生成树的时间并不会太短。

### remove

1.   根据key的hash值和数组长度得出key在数组中的位置。
2.   如果当前位置有key，而且key就是要删除的那个key，那么移除。
3.   否则，要么从红黑树中找到那个节点或者从单链表中找到那个节点，然后移除。

移除：

1.   如果是红黑树，按照红黑树的移除操作。（注意，如果红黑树节点个数较少，即使移除后数量小于阈值，也不一定变为链表）
2.   如果是单链表的头部，那么头部变为节点的下一个。
3.   如果是单链表的中间，那么前一个节点的next变为当前结点的下一个。

## 感悟

Java的HashMap实现的方式很巧妙，首先保证table的长度是2的次方，也就是1 << n。在此基础下，当Map扩容时，链表可以一分为二，而且可以保证2个链表放置的位置不会被其他index的链表干扰。

如果table的长度是任意长度，就做不到这么快扩容。

如果kv放置的方式是hash % len，虽然也能保证不越界，但是在扩容时，原链表节点可能会散落在新table各个index上。

# 几个问题

## HashMap和Hashtable区别？

简单总结有几点：

1.  HashMap支持null Key和null Value；Hashtable不允许。这是因为HashMap对null进行了特殊处理，将null的hashCode值定为了0，从而将其存放在哈希表的第0个bucket。

2.  HashMap是非线程安全，HashMap实现线程安全方法为`Map map = Collections.synchronziedMap(new HashMap())；`
    Hashtable是线程安全。

3.  HashMap默认长度是16，扩容是原先的2倍
    Hashtable默认长度是11，扩容是原先的2n+1

4.  HashMap继承AbstractMap
    Hashtable继承了Dictionary

5.  如果在创建时给定了初始化大小，那么HashTable会直接使用给定的大小，而HashMap会将其扩充为2的幂次方大小。 

## ConcurrentHashMap和Hashtable的区别

都可以用于多线程的环境，但是当Hashtable的大小增加到一定的时候，性能会急剧下降，因为迭代时需要被锁定很长的时间。因为ConcurrentHashMap引入了分割(segmentation)，不论它变得多么大，仅仅需要锁定map的某个部分，而其它的线程不需要等到迭代完成才能访问map。**简而言之，在迭代的过程中，ConcurrentHashMap仅仅锁定map的某个部分，而Hashtable则会锁定整个map。**

## HashMap、SparseArray、ArrayMap的区别

1.  在数据量小的时候一般认为1000以下，当key为int的时候，使用SparseArray确实是一个很不错的选择，内存大概能节省30%，相比用HashMap，因为key值不需要装箱，所以时间性能平均来看也优于HashMap。
2.  ArrayMap相对于SparseArray，特点就是key值类型不受限，任何情况下都可以取代HashMap，但是通过研究和测试发现，ArrayMap的内存节省并不明显。并且AS会提示使用SparseArray，但是不会提示使用ArrayMap。

## 如何检测HashMap存在线程安全问题？

HashMap每次操作都会`++modCount`，在迭代期间，如果发现modCount发生了变化，那么就抛出ConcurrentModificationException异常。这意味着在单线程的`for-each`中也不能操作（put）。

# 源码

## resize

```java
final Node<K,V>[] resize() {
    Node<K,V>[] oldTab = table;
    int oldCap = (oldTab == null) ? 0 : oldTab.length;
    int oldThr = threshold;
    int newCap, newThr = 0;
    if (oldCap > 0) {
        if (oldCap >= MAXIMUM_CAPACITY) {
            threshold = Integer.MAX_VALUE;
            return oldTab;
        }
        else if ((newCap = oldCap << 1) < MAXIMUM_CAPACITY &&
                 oldCap >= DEFAULT_INITIAL_CAPACITY)
            newThr = oldThr << 1; // double threshold
    }
    else if (oldThr > 0) // initial capacity was placed in threshold
        newCap = oldThr;
    else {               // zero initial threshold signifies using defaults
        newCap = DEFAULT_INITIAL_CAPACITY;
        newThr = (int)(DEFAULT_LOAD_FACTOR * DEFAULT_INITIAL_CAPACITY);
    }
    if (newThr == 0) {
        float ft = (float)newCap * loadFactor;
        newThr = (newCap < MAXIMUM_CAPACITY && ft < (float)MAXIMUM_CAPACITY ?
                  (int)ft : Integer.MAX_VALUE);
    }
    threshold = newThr;
    // 以上代码是计算新的table容量
    Node<K,V>[] newTab = (Node<K,V>[])new Node[newCap];
    table = newTab;
    // 将旧的kv移到新的table里
    if (oldTab != null) {
        for (int j = 0; j < oldCap; ++j) {
            Node<K,V> e;
            if ((e = oldTab[j]) != null) {
                oldTab[j] = null;
                if (e.next == null)
                    newTab[e.hash & (newCap - 1)] = e;
                else if (e instanceof TreeNode)
                    ((TreeNode<K,V>)e).split(this, newTab, j, oldCap);
                else {
                    // 将当前的链表一分为二
                    Node<K,V> loHead = null, loTail = null;
                    Node<K,V> hiHead = null, hiTail = null;
                    Node<K,V> next;
                    do {
                        next = e.next;
                        if ((e.hash & oldCap) == 0) {
                            if (loTail == null)
                                loHead = e;
                            else
                                loTail.next = e;
                            loTail = e;
                        }
                        else {
                            if (hiTail == null)
                                hiHead = e;
                            else
                                hiTail.next = e;
                            hiTail = e;
                        }
                    } while ((e = next) != null);
                    if (loTail != null) {
                        loTail.next = null;
                        newTab[j] = loHead;
                    }
                    if (hiTail != null) {
                        hiTail.next = null;
                        newTab[j + oldCap] = hiHead;
                    }
                }
            }
        }
    }
    return newTab;
}
```