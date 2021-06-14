使用很简单，put放入键值对，get获取键值对，remove移除

# 思想

主要是CAS操作+Synchronized锁分段。

# 成员变量

- table：默认为null，初始化发生在第一次插入操作，默认大小为16的数组，用来存储Node节点数据，扩容时大小总是2的幂次方。
- nextTable：默认为null，扩容时新生成的数组，其大小为原数组的两倍。
- sizeCtl ：默认为0，用来控制table的初始化和扩容操作，具体应用在后续会体现出来。 
  -1 代表table正在初始化 
  -(1+N) 表示有N个线程正在进行扩容操作 
  其余情况： 
  1、如果table未初始化，表示table需要初始化的大小。 
  2、如果table初始化完成，表示table的容量，默认是table大小的0.75倍，居然用这个公式算0.75（n - (n >>> 2)）。
- Node：保存key，value及key的hash值的数据结构。 
  其中value和next都用volatile修饰，保证并发的可见性。

- ForwardingNode：一个特殊的Node节点，hash值为-1，其中存储nextTable的引用。 
  只有table发生扩容的时候，ForwardingNode才会发挥作用，作为一个占位符放在table中表示当前节点为null或则已经被移动。

# 构造方法

```java
public ConcurrentHashMap() {
}
```

无参构造方法，所有的值都是默认值

```java
public ConcurrentHashMap(int initialCapacity) {
    if (initialCapacity < 0)
        throw new IllegalArgumentException();
    int cap = ((initialCapacity >= (MAXIMUM_CAPACITY >>> 1)) ?
               MAXIMUM_CAPACITY :
               tableSizeFor(initialCapacity + (initialCapacity >>> 1) + 1));
    this.sizeCtl = cap;
}
```

指定初始table大小，会将其扩充为2的幂次方。默认为16。

```java
public ConcurrentHashMap(int initialCapacity, float loadFactor) {
    this(initialCapacity, loadFactor, 1);
}
```

```java
public ConcurrentHashMap(int initialCapacity,
                         float loadFactor, int concurrencyLevel) {
    if (!(loadFactor > 0.0f) || initialCapacity < 0 || concurrencyLevel <= 0)
        throw new IllegalArgumentException();
    if (initialCapacity < concurrencyLevel)   // Use at least as many bins
        initialCapacity = concurrencyLevel;   // as estimated threads
    long size = (long)(1.0 + (long)initialCapacity / loadFactor);
    int cap = (size >= (long)MAXIMUM_CAPACITY) ?
        MAXIMUM_CAPACITY : tableSizeFor((int)size);
    this.sizeCtl = cap;
}
```

指定初始table大小，加载因子，和并发的线程数。

# put方法

put方法放入键值对，返回旧值。

```java
public V put(K key, V value) {
    return putVal(key, value, false);
}
```

真正的实现在putVal方法中。为了方便查看，将解析写在注释中。

```java
final V putVal(K key, V value, boolean onlyIfAbsent) {
    if (key == null || value == null) throw new NullPointerException();//与HashMap不同，不能传入null的键或值。
    int hash = spread(key.hashCode());
    int binCount = 0;
    for (Node<K,V>[] tab = table;;) {
        Node<K,V> f; int n, i, fh;
        if (tab == null || (n = tab.length) == 0)
            tab = initTable();//如果是第一次put，则初始化table
        else if ((f = tabAt(tab, i = (n - 1) & hash)) == null) {
            if (casTabAt(tab, i, null, new Node<K,V>(hash, key, value, null)))
                break;                   
        }//代码1
        else if ((fh = f.hash) == MOVED)//代码2
            tab = helpTransfer(tab, f);
        else {//代码3
            V oldVal = null;
            synchronized (f) {
                if (tabAt(tab, i) == f) {
                    if (fh >= 0) {
                        binCount = 1;
                        for (Node<K,V> e = f;; ++binCount) {
                            K ek;
                            if (e.hash == hash &&
                                ((ek = e.key) == key ||
                                 (ek != null && key.equals(ek)))) {
                                oldVal = e.val;
                                if (!onlyIfAbsent)
                                    e.val = value;
                                break;
                            }
                            Node<K,V> pred = e;
                            if ((e = e.next) == null) {
                                pred.next = new Node<K,V>(hash, key,
                                                          value, null);
                                break;
                            }
                        }
                    }
                    else if (f instanceof TreeBin) {
                        Node<K,V> p;
                        binCount = 2;
                        if ((p = ((TreeBin<K,V>)f).putTreeVal(hash, key,
                                                       value)) != null) {
                            oldVal = p.val;
                            if (!onlyIfAbsent)
                                p.val = value;
                        }
                    }
                    else if (f instanceof ReservationNode)
                        throw new IllegalStateException("Recursive update");
                }
            }
            if (binCount != 0) {//代码4
                if (binCount >= TREEIFY_THRESHOLD)
                    treeifyBin(tab, i);
                if (oldVal != null)
                    return oldVal;
                break;
            }
        }
    }
    addCount(1L, binCount);
    return null;
}
```

**代码1**
此处是当前table位置为null的情况。注意，table是volatile的，但是它内部的元素并不是volatile的，所以这里获取table元素的时候用了原子操作getObjectVolatile。

```java
static final <K,V> Node<K,V> tabAt(Node<K,V>[] tab, int i) {
    return (Node<K,V>)U.getObjectVolatile(tab, ((long)i << ASHIFT) + ABASE);
}
```

**代码2**

此处发生在扩容中，当前节点为ForwardingNode。调用helpTransfer方法。helpTransfer方法主要是放回扩容后的table（nextTable）。获取到新table之后，会进入下一个循环，根据新的table来再次尝试放入。

**代码3**

如果产生Hash冲突，那么锁住当前分段（table的第i个位置）。

然后和HashMap相似，如果当前位置的类型是链表，如果有这个键那么更新值，否则放入链表的最后节点。如果当前位置的类型是树，那么就放入树中。

**代码4**

如果此时是新增而不是更新，那么binCount表示table当前位置的节点数量。如果binCount大于树化阈值（TREEIFY_THRESHOLD = 8），会调用treeifyBin方法进行树化。

# initTable初始化table

```java
private final Node<K,V>[] initTable() {
    Node<K,V>[] tab; int sc;
    while ((tab = table) == null || tab.length == 0) {
        if ((sc = sizeCtl) < 0)
            Thread.yield(); // lost initialization race; just spin（进行自旋）
        else if (U.compareAndSwapInt(this, SIZECTL, sc, -1)) {
            try {
                if ((tab = table) == null || tab.length == 0) {
                    int n = (sc > 0) ? sc : DEFAULT_CAPACITY;
                    @SuppressWarnings("unchecked")
                    Node<K,V>[] nt = (Node<K,V>[])new Node<?,?>[n];
                    table = tab = nt;
                    sc = n - (n >>> 2);
                }
            } finally {
                sizeCtl = sc;
            }
            break;
        }
    }
    return tab;
}
```

table的初始化被延迟到了第一次put前。如果sizeCtl为负，表示其他线程正在初始化，那么次线程就不需要进行初始化，让出CPU。如果当前线程获取到了CPU时间，那么进入下一个循环，再次判断，直到初始化完成（自旋）。

> Thread.yield()
>
> 就是说当一个线程使用了这个方法之后，它就会把自己CPU执行的时间让掉，让自己或者其它线程运行。

如果sizeCtl不为负，一般此时为默认值0，会用CAS操作将其变为-1，防止其他线程初始化。初始化完成后，sizeCtl变为table大小的0.75，也就是扩容阈值。

> public final native boolean compareAndSwapInt(Object o, long offset, int expected, int x);
>
> 第一个参数是需要改变的对象，第二个是相对地址值，第三个是预期值，第四个是置换值。
>
> 每次循环调本地方法时，传最新的预期值，和符合修改值。由本地方法中硬件层具体实现，如果预期值和最新值相同，将AtomicInteger对象的value值改为符合修改值。

**为什么要延迟初始化？**

官方文档这么说：

```java
/**
* Lazy table initialization minimizes footprint until first use,
* and also avoids resizings when the first operation is from a
* putAll, constructor with map argument, or deserialization.
* These cases attempt to override the initial capacity settings,
* but harmlessly fail to take effect in cases of races.
**/
```

如果一开始就设定容量，那么第一次操作如果是putAll这类的，会导致扩容，效率低下。

# treeifyBin树化

```java
private final void treeifyBin(Node<K,V>[] tab, int index) {
    Node<K,V> b; int n;
    if (tab != null) {
        if ((n = tab.length) < MIN_TREEIFY_CAPACITY)//代码1
            tryPresize(n << 1);
      	//将当前位置的链表变为树结构
        else if ((b = tabAt(tab, index)) != null && b.hash >= 0) {
            synchronized (b) {
                if (tabAt(tab, index) == b) {
                    TreeNode<K,V> hd = null, tl = null;
                    for (Node<K,V> e = b; e != null; e = e.next) {
                        TreeNode<K,V> p =
                            new TreeNode<K,V>(e.hash, e.key, e.val,
                                              null, null);
                        if ((p.prev = tl) == null)
                            hd = p;
                        else
                            tl.next = p;
                        tl = p;
                    }
                    setTabAt(tab, index, new TreeBin<K,V>(hd));
                }
            }
        }
    }
}
```

**代码1**

如果table长度小于最小树化能力（MIN_TREEIFY_CAPACITY = 64），那么不进行树化，而是选择扩容。

# tryPresize扩容

```java
private final void tryPresize(int size) {
    int c = (size >= (MAXIMUM_CAPACITY >>> 1)) ? MAXIMUM_CAPACITY :
        tableSizeFor(size + (size >>> 1) + 1);
    int sc;
    while ((sc = sizeCtl) >= 0) {
        Node<K,V>[] tab = table; int n;
        if (tab == null || (n = tab.length) == 0) {
            n = (sc > c) ? sc : c;
            if (U.compareAndSwapInt(this, SIZECTL, sc, -1)) {
                try {
                    if (table == tab) {
                        @SuppressWarnings("unchecked")
                        Node<K,V>[] nt = (Node<K,V>[])new Node<?,?>[n];
                        table = nt;
                        sc = n - (n >>> 2);
                    }
                } finally {
                    sizeCtl = sc;
                }
            }
        }
        else if (c <= sc || n >= MAXIMUM_CAPACITY)
            break;
        else if (tab == table) {
            int rs = resizeStamp(n);//此处暂不理解为什么要获取一个邮票
            if (U.compareAndSwapInt(this, SIZECTL, sc,
                                    (rs << RESIZE_STAMP_SHIFT) + 2))
                transfer(tab, null);
        }
    }
}
```

首先将传入的size变为2倍，为超过了MAXIMUM_CAPACITY，就另其等于MAXIMUM_CAPACITY 。

然后如果没有初始化就初始化table，这点与上面initTable相似。

如果扩容后的大小c比阈值sizeCtl小或者已经到达最大容量，则不进行扩容。

反之进行真正的扩容。

# transfer真正的扩容

```java
private final void transfer(Node<K,V>[] tab, Node<K,V>[] nextTab) {
    int n = tab.length, stride;
  	// stride为此次需要迁移的桶的数目
  	// NCPU为当前主机CPU数目
    // MIN_TRANSFER_STRIDE为每个线程最小处理的组数目
    // 1. 在多核中stride为当前容量的1/8对CPU数目取整,例如容量为16时,CPU为2时结果是1
   	// 2. 在单核中stride为n就为当前数组容量
 		// stride最小为16，被限定死。
    if ((stride = (NCPU > 1) ? (n >>> 3) / NCPU : n) < MIN_TRANSFER_STRIDE)
        stride = MIN_TRANSFER_STRIDE; // subdivide range
  	//创建一个大小为原来2倍的table
    if (nextTab == null) {            // initiating
        try {
            @SuppressWarnings("unchecked")
            Node<K,V>[] nt = (Node<K,V>[])new Node<?,?>[n << 1];
            nextTab = nt;
        } catch (Throwable ex) {      // try to cope with OOME
            sizeCtl = Integer.MAX_VALUE;
            return;
        }
        nextTable = nextTab;
        transferIndex = n;
    }
    int nextn = nextTab.length;
    ForwardingNode<K,V> fwd = new ForwardingNode<K,V>(nextTab);
  
  	//上面是数据准备，以下为具体的逻辑
    boolean advance = true;
    boolean finishing = false; 
    for (int i = 0, bound = 0;;) {
        Node<K,V> f; int fh;
      	// 该while代码块根据if的顺序功能分别是
        // --i: 负责迁移区域的向前推荐，i为桶下标
        // nextIndex: 在没有获取负责区域时，检查是否还需要扩容
        // CAS: 负责获取此次for循环的区域，每次都为stride个桶
        while (advance) {
            int nextIndex, nextBound;
          	// 这个--i每次都会进行,每次都会向前推进一个位置
            if (--i >= bound || finishing)
                advance = false;
          	// 因此如果当transferIndex<=0时,表示扩容的区域分配完
            else if ((nextIndex = transferIndex) <= 0) {
                i = -1;
                advance = false;
            }
          	// CAS替换transferIndex的值，新值为旧值减去分到的stride
            // stride就表示此次的迁移区域，nextIndex就代表了下次起点
            // 从这里可以看出扩容是从数组末尾开始向前推进的
            else if (U.compareAndSwapInt
                     (this, TRANSFERINDEX, nextIndex,
                      nextBound = (nextIndex > stride ?
                                   nextIndex - stride : 0))) {
                bound = nextBound;
                i = nextIndex - 1;
                advance = false;
            }
        }
      	// 1. 此if判定扩容的结果,中间是三种异常值
        // 1). i < 0的情况时上面第二个if跳出的线程
        // 2). i > 旧数组的长度
        // 3). i+n大于新数组的长度
        if (i < 0 || i >= n || i + n >= nextn) {
            int sc;
            if (finishing) {
                nextTable = null;
                table = nextTab;
                sizeCtl = (n << 1) - (n >>> 1);
                return;
            }
            if (U.compareAndSwapInt(this, SIZECTL, sc = sizeCtl, sc - 1)) {
                if ((sc - 2) != resizeStamp(n) << RESIZE_STAMP_SHIFT)
                    return;
                finishing = advance = true;
                i = n; // recheck before commit
            }
        }
      	// 2. 扩容时发现负责的区域有空的桶直接使用ForwardingNode填充
        // ForwardingNode持有nextTable的引用
        else if ((f = tabAt(tab, i)) == null)
            advance = casTabAt(tab, i, null, fwd);
      	//3. 表示处理完毕
        else if ((fh = f.hash) == MOVED)
            advance = true;
      	// 4. 迁移桶的操作
        else {
            synchronized (f) {
              	// 进入synchronized之后重新判断,保证数据的正确性没有在中间被修改
              	//与HashMap中的相似
                if (tabAt(tab, i) == f) {
                    Node<K,V> ln, hn;
                    if (fh >= 0) {
                        int runBit = fh & n;
                        Node<K,V> lastRun = f;
                        for (Node<K,V> p = f.next; p != null; p = p.next) {
                            int b = p.hash & n;
                            if (b != runBit) {
                                runBit = b;
                                lastRun = p;
                            }
                        }
                        if (runBit == 0) {
                            ln = lastRun;
                            hn = null;
                        }
                        else {
                            hn = lastRun;
                            ln = null;
                        }
                        for (Node<K,V> p = f; p != lastRun; p = p.next) {
                            int ph = p.hash; K pk = p.key; V pv = p.val;
                            if ((ph & n) == 0)
                                ln = new Node<K,V>(ph, pk, pv, ln);
                            else
                                hn = new Node<K,V>(ph, pk, pv, hn);
                        }
                        setTabAt(nextTab, i, ln);
                        setTabAt(nextTab, i + n, hn);
                        setTabAt(tab, i, fwd);
                        advance = true;
                    }
                  	// 树的桶迁移操作
                    else if (f instanceof TreeBin) {
                        TreeBin<K,V> t = (TreeBin<K,V>)f;
                        TreeNode<K,V> lo = null, loTail = null;
                        TreeNode<K,V> hi = null, hiTail = null;
                        int lc = 0, hc = 0;
                        for (Node<K,V> e = t.first; e != null; e = e.next) {
                            int h = e.hash;
                            TreeNode<K,V> p = new TreeNode<K,V>
                                (h, e.key, e.val, null, null);
                            if ((h & n) == 0) {
                                if ((p.prev = loTail) == null)
                                    lo = p;
                                else
                                    loTail.next = p;
                                loTail = p;
                                ++lc;
                            }
                            else {
                                if ((p.prev = hiTail) == null)
                                    hi = p;
                                else
                                    hiTail.next = p;
                                hiTail = p;
                                ++hc;
                            }
                        }
                        ln = (lc <= UNTREEIFY_THRESHOLD) ? untreeify(lo) :
                            (hc != 0) ? new TreeBin<K,V>(lo) : t;
                        hn = (hc <= UNTREEIFY_THRESHOLD) ? untreeify(hi) :
                            (lc != 0) ? new TreeBin<K,V>(hi) : t;
                        setTabAt(nextTab, i, ln);
                        setTabAt(nextTab, i + n, hn);
                        setTabAt(tab, i, fwd);
                        advance = true;
                    }
                }
            }
        }
    }
}
```

# helpTransfer帮助扩容

```java
final Node<K,V>[] helpTransfer(Node<K,V>[] tab, Node<K,V> f) {
    Node<K,V>[] nextTab; int sc;
    if (tab != null && (f instanceof ForwardingNode) &&
        (nextTab = ((ForwardingNode<K,V>)f).nextTable) != null) {
        int rs = resizeStamp(tab.length);
        while (nextTab == nextTable && table == tab &&
               (sc = sizeCtl) < 0) {
            if ((sc >>> RESIZE_STAMP_SHIFT) != rs || sc == rs + 1 ||
                sc == rs + MAX_RESIZERS || transferIndex <= 0)
                break;
            if (U.compareAndSwapInt(this, SIZECTL, sc, sc + 1)) {
                transfer(tab, nextTab);
                break;
            }
        }
        return nextTab;
    }
    return table;
}
```

主要是返回扩容后的table。

# addCount方法

```java
private final void addCount(long x, int check) {
    CounterCell[] as; long b, s;
  	//利用CAS方法更新baseCount的值
    if ((as = counterCells) != null ||
        !U.compareAndSwapLong(this, BASECOUNT, b = baseCount, s = b + x)) {
        CounterCell a; long v; int m;
        boolean uncontended = true;
        if (as == null || (m = as.length - 1) < 0 ||
            (a = as[ThreadLocalRandom.getProbe() & m]) == null ||
            !(uncontended =
              U.compareAndSwapLong(a, CELLVALUE, v = a.value, v + x))) {
            fullAddCount(x, uncontended);
            return;
        }
        if (check <= 1)
            return;
        s = sumCount();
    }
  	//如果check值大于等于0 则需要检验是否需要进行扩容操作
    if (check >= 0) {
        Node<K,V>[] tab, nt; int n, sc;
        while (s >= (long)(sc = sizeCtl) && (tab = table) != null &&
               (n = tab.length) < MAXIMUM_CAPACITY) {
            int rs = resizeStamp(n);
            if (sc < 0) {
                if ((sc >>> RESIZE_STAMP_SHIFT) != rs || sc == rs + 1 ||
                    sc == rs + MAX_RESIZERS || (nt = nextTable) == null ||
                    transferIndex <= 0)
                    break;
              	//如果已经有其他线程在执行扩容操作
                if (U.compareAndSwapInt(this, SIZECTL, sc, sc + 1))
                    transfer(tab, nt);
            }
          	//当前线程是唯一的或是第一个发起扩容的线程  此时nextTable=null
            else if (U.compareAndSwapInt(this, SIZECTL, sc,
                                         (rs << RESIZE_STAMP_SHIFT) + 2))
                transfer(tab, null);
            s = sumCount();
        }
    }
}
```

把当前ConcurrentHashMap的元素个数+1。这个方法一共做了两件事：更新baseCount的值，检测是否进行扩容。

# get方法

```java
public V get(Object key) {
    Node<K,V>[] tab; Node<K,V> e, p; int n, eh; K ek;
    int h = spread(key.hashCode());
    if ((tab = table) != null && (n = tab.length) > 0 &&
        (e = tabAt(tab, (n - 1) & h)) != null) {
        if ((eh = e.hash) == h) {//如果table当前位置的节点正好是key，则返回值。
            if ((ek = e.key) == key || (ek != null && key.equals(ek)))
                return e.val;
        }
      	//代码1
        else if (eh < 0)
            return (p = e.find(h, key)) != null ? p.val : null;
        while ((e = e.next) != null) {//遍历链表获取需要的键值对
            if (e.hash == h &&
                ((ek = e.key) == key || (ek != null && key.equals(ek))))
                return e.val;
        }
    }
    return null;//找不到就返回null。
}
```

**代码1**

hash<0有这么几种情况：

1. hash=-1：Node的实际类型是ForwardingNode，会调用Node的实际类型是ForwardingNode的find方法，从nextTable方法中查找。
2. hash=-2：Node的实际类型是TreeBin，调用TreeBin的find方法遍历红黑树，由于红黑树有可能正在旋转变色，所以find里会有读写锁。

## 为什么get方法不需要加锁？

**如果在put过程中get**

put方法会将需要更改的节点加锁，保证操作正确。如果get的节点正好是锁的节点，那么会等待，如果不是，那么没有其他线程修改，不需要考虑并发问题。

**在扩容或者树化的过程中get**

扩容和树化过程会通过CAS操作来设置值，保证可见性，所以get获取到正确的值。

> 我看有些博客说是volatile，我感觉不对，volatile对于对象只是内存地址的可见性而不是内容的可见性。

# remove方法

```java
public V remove(Object key) {
    return replaceNode(key, null, null);
}
```

```java
final V replaceNode(Object key, V value, Object cv) {
    int hash = spread(key.hashCode());
    for (Node<K,V>[] tab = table;;) {
        Node<K,V> f; int n, i, fh;
      	//1.异常情况，此时返回null
        if (tab == null || (n = tab.length) == 0 ||
            (f = tabAt(tab, i = (n - 1) & hash)) == null)
            break;
      	//2.hash=MOVED(-1)表示此时正在扩容，这里返回扩容后的table，并进入下一个循环
        else if ((fh = f.hash) == MOVED)
            tab = helpTransfer(tab, f);
      	//见代码3
        else {
            V oldVal = null;
            boolean validated = false;
            synchronized (f) {
                if (tabAt(tab, i) == f) {
                    if (fh >= 0) {
                        validated = true;
                        for (Node<K,V> e = f, pred = null;;) {
                            K ek;
                            if (e.hash == hash &&
                                ((ek = e.key) == key ||
                                 (ek != null && key.equals(ek)))) {
                                V ev = e.val;
                                if (cv == null || cv == ev ||
                                    (ev != null && cv.equals(ev))) {
                                    oldVal = ev;
                                    if (value != null)
                                        e.val = value;
                                    else if (pred != null)
                                        pred.next = e.next;
                                    else
                                        setTabAt(tab, i, e.next);
                                }
                                break;
                            }
                            pred = e;
                            if ((e = e.next) == null)
                                break;
                        }
                    }
                    else if (f instanceof TreeBin) {
                        validated = true;
                        TreeBin<K,V> t = (TreeBin<K,V>)f;
                        TreeNode<K,V> r, p;
                        if ((r = t.root) != null &&
                            (p = r.findTreeNode(hash, key, null)) != null) {
                            V pv = p.val;
                            if (cv == null || cv == pv ||
                                (pv != null && cv.equals(pv))) {
                                oldVal = pv;
                                if (value != null)
                                    p.val = value;
                                else if (t.removeTreeNode(p))
                                    setTabAt(tab, i, untreeify(t.first));
                            }
                        }
                    }
                    else if (f instanceof ReservationNode)
                        throw new IllegalStateException("Recursive update");
                }
            }
            if (validated) {
                if (oldVal != null) {
                    if (value == null)
                        addCount(-1L, -1);
                    return oldVal;
                }
                break;
            }
        }
    }
    return null;
}
```

**代码3**

与put类似，会锁住当前节点。

如果节点类型是链表，那么就删除链表节点

如果节点类型是树，那么就删除树节点

# 总结

put与remove类似，所以这里围绕put和get来进行总结。

# 参考

（CAS方法）https://coding.imooc.com/learn/questiondetail/49806.html

（Java Thread.yield详解）https://blog.csdn.net/dabing69221/article/details/17426953

（ConcurrentHashMap源码分析（JDK8版本））https://blog.csdn.net/programmer_at/article/details/79715177

（深度剖析 JDK7 ConcurrentHashMap 中的知识点）https://www.jianshu.com/p/464065e4a043

（ConcurrentHashMap源码阅读）https://juejin.im/post/5c40a1fa51882525ed5c4ac2#heading-11