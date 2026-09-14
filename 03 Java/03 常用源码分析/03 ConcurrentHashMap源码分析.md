> 本文以 [OpenJDK 8u402，标签 jdk8u402-b06](https://github.com/openjdk/jdk8u/blob/jdk8u402-b06/jdk/src/share/classes/java/util/concurrent/ConcurrentHashMap.java) 为基准。源码片段调整了注释和排版；`tryPresize` 省略了一个不可达分支，具体见该节。不同 JDK 更新版本的细节可能不同。

# 思想

JDK 8 的 `ConcurrentHashMap` 使用数组、链表和红黑树存储数据，通过 **CAS、桶级 `synchronized` 和 volatile 读写**协调并发访问。

- 向空桶插入节点时，通过 CAS 竞争该数组位置。
- 更新非空桶时，以桶头节点为锁对象；树桶的锁对象是 `TreeBin`。
- 普通 `get` 不获取桶的 `synchronized` 锁，依靠节点和数组元素的可见性，以及特殊节点的查找逻辑读取数据。
- 扩容时，多个线程可以领取不同的桶区间，共同完成迁移。

JDK 7 的 `Segment` 分段锁与这里的桶级锁不同。JDK 8 虽然保留了用于序列化兼容的 `Segment` 类型，但常规读写不再依赖它。

# 成员变量

## 主要字段和节点类型

| 字段或类型 | 含义 |
| --- | --- |
| `table` | volatile 数组引用，构造时通常为 `null`，实际分配延迟到插入或预分配路径。数组长度为 2 的幂；无参构造后首次普通 `put` 默认分配 16 个桶。 |
| `nextTable` | 扩容中的新数组引用，每轮迁移分配的长度为旧数组的两倍；扩容提交后清空该字段。 |
| `sizeCtl` | 初始化和扩容的控制状态，未扩容时也用来保存初始容量或扩容阈值。 |
| `transferIndex` | 下一个可领取迁移区间的上界，通过 CAS 从数组尾部向前分配工作。 |
| `baseCount`、`counterCells` | 元素计数由基础计数与各个 `CounterCell` 的计数共同组成，分散并发更新的竞争。 |
| `cellsBusy` | 通过 CAS 获取的控制标记，用于协调 `counterCells` 的初始化、扩展和单元创建。 |
| `Node` | 普通节点，`hash`、`key` 为 final，`val`、`next` 为 volatile。 |
| `TreeNode`、`TreeBin` | `TreeNode` 是树中的数据节点；`TreeBin` 是放在桶位置的容器，保存树根、链表入口和树的读写协调状态，hash 为 `TREEBIN = -2`。 |
| `ForwardingNode` | hash 为 `MOVED = -1`，保存新数组引用。放入旧桶后表示该桶已处理，包括原来为空的桶；后续访问可以转向新数组。 |
| `ReservationNode` | hash 为 `RESERVED = -3`，用于 `computeIfAbsent`、`compute` 等方法计算映射时占位，不保存普通键值对。 |

## sizeCtl 的状态含义

| 状态 | 含义 |
| --- | --- |
| `0` 且数组未初始化 | 使用默认初始容量。 |
| 正数且数组未初始化 | 待分配的数组长度。 |
| 正数且数组已初始化、未扩容 | 下一次检查扩容时使用的元素数量阈值，通常通过 `n - (n >>> 2)` 计算。 |
| `-1` | 一个线程获得了初始化资格。 |
| 扩容编码的负数 | 高 16 位保存扩容戳，低 16 位在常规迁移阶段保存参与迁移的线程数加一。 |

设旧数组长度为 `n`，记 `R = resizeStamp(n) << RESIZE_STAMP_SHIFT`，其中 `RESIZE_STAMP_SHIFT = 16`。扩容发起者通过 CAS 将 `sizeCtl` 从阈值改成 `R + 2`；后续线程成功加入时加一，退出时减一。

例如，旧数组长度为 16 时，`resizeStamp(16) = 0x801b`，`R = 0x801b0000`，作为 Java 的有符号 int 是负数：

```text
12（扩容阈值）
  → R + 2（1 个迁移线程）
  → R + 3（2 个迁移线程）
  → R + 2（一个线程退出）
  → R + 1（最后一个线程执行收尾扫描，禁止新线程加入）
  → 24（新数组长度为 32，恢复扩容阈值）
```

因此，不能直接用 `-(1 + N)` 解释整个 `sizeCtl`；收尾扫描阶段也不能再把低位减一当成仍在执行代码的线程数。原源码字段注释中的简化说法应结合实际位编码理解。

## 数组元素的可见性

`table` 是 volatile 引用，不等于 `table[i]` 自动具有 volatile 语义。JDK 8 使用 `Unsafe` 为数组元素提供相应的访问方式：

| 方法 | 底层操作 | 用途 |
| --- | --- | --- |
| `tabAt` | `getObjectVolatile` | 以 volatile 语义读取桶头节点。 |
| `casTabAt` | `compareAndSwapObject` | 原子比较并替换桶头，例如向空桶插入节点。 |
| `setTabAt` | `putObjectVolatile` | 以 volatile 语义发布桶头，例如发布树桶或转发节点。 |

# 构造方法

```java
public ConcurrentHashMap() {
}
```

无参构造方法不分配数组，`table` 为 `null`，`sizeCtl` 为 0。首次普通 `put` 初始化时使用默认数组长度 16。

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

`initialCapacity` 表示预期容纳的元素数量，不是直接指定数组长度。构造方法先计算 `initialCapacity + (initialCapacity >>> 1) + 1`，再通过 `tableSizeFor` 向上取整为 2 的幂，并保存到 `sizeCtl`。

例如，`new ConcurrentHashMap<>(16)` 会将 `sizeCtl` 设为 32，首次普通插入时分配 32 个桶；这与无参构造的默认 16 个桶不同。

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

这组构造方法根据预期元素数量、负载因子和预估并发度计算初始容量：

- `concurrencyLevel` 在这里是容量估算提示，通过提高 `initialCapacity` 的下限发挥作用，不会创建对应数量的锁，也不限制实际线程数。
- `loadFactor` 只参与初始容量计算，不会作为实例字段保存。后续初始化和扩容完成后的阈值仍由源码中的固定公式计算。
- 这些构造方法同样只设置 `sizeCtl`，不会立即分配 `table`。

# put方法

`put` 放入键值对。键已存在时替换并返回旧值；新增映射时返回 `null`。

```java
public V put(K key, V value) {
    return putVal(key, value, false);
}
```

真正的实现在 `putVal` 中。`onlyIfAbsent` 为 true 时保留已有值，`putIfAbsent` 复用的就是这条路径。`spread` 将 hash 的高 16 位混入低位并清除符号位，随后通过 `(n - 1) & hash` 定位桶。

```java
final V putVal(K key, V value, boolean onlyIfAbsent) {
    // 禁止 null 键和值；普通 hash 通过 spread 清除符号位。
    if (key == null || value == null) throw new NullPointerException();
    int hash = spread(key.hashCode());
    int binCount = 0;
    for (Node<K,V>[] tab = table;;) {
        Node<K,V> f; int n, i, fh;
        if (tab == null || (n = tab.length) == 0)
            tab = initTable();
        else if ((f = tabAt(tab, i = (n - 1) & hash)) == null) {
            if (casTabAt(tab, i, null,
                         new Node<K,V>(hash, key, value, null)))
                break;                   // no lock when adding to empty bin
        }
        // 旧桶已处理，尝试协助迁移并转向新表。
        else if ((fh = f.hash) == MOVED)
            tab = helpTransfer(tab, f);
        else {
            V oldVal = null;
            synchronized (f) {
                // 等待锁期间桶头可能变化，必须重新验证。
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
                }
            }
            // 更新已有键时也会经过这里；具体含义见下文。
            if (binCount != 0) {
                if (binCount >= TREEIFY_THRESHOLD)
                    treeifyBin(tab, i);
                if (oldVal != null)
                    return oldVal;
                break;
            }
        }
    }
    // 只有新增映射才会到达这里。
    addCount(1L, binCount);
    return null;
}
```

## 执行流程

1. 拒绝 `null` 键和 `null` 值；如果数组未初始化，调用 `initTable`。
2. 桶为空时尝试 CAS 插入。CAS 失败说明该位置发生了竞争，回到循环重新读取，不会覆盖其他线程的节点。
3. 桶头为 `ForwardingNode` 时，调用 `helpTransfer` 尝试参与迁移，并取得新数组继续操作。
4. 对普通非空桶执行 `synchronized (f)`，获取锁后再验证 `tabAt(tab, i) == f`。等待锁期间桶头可能已被删除、树化或替换为转发节点，验证失败就重试。
5. 链表中找到键就按 `onlyIfAbsent` 决定是否更新，否则在尾部插入；树桶通过 `TreeBin.putTreeVal` 查找或插入。
6. 满足条件时调用 `treeifyBin`。覆盖旧值直接返回，只有新增映射才执行 `addCount(1L, binCount)`。

## binCount 与树化阈值

`binCount` 不总是桶内节点总数：在链表尾部新增节点时，它等于插入前的链表长度；找到已有键时，它等于遍历到该节点的计数；树桶路径直接赋值为 2。

源码判断是 `binCount >= TREEIFY_THRESHOLD`，阈值为 8。因此在这里的普通链表 `put` 路径中，向已有 8 个节点的链表插入第 9 个节点时会请求树化。实际转成树还要求数组长度至少为 64，否则优先尝试扩容。

`treeifyBin` 的调用发生在返回旧值之前，因此不能概括为“只有新增才检查树化”。

# initTable

```java
private final Node<K,V>[] initTable() {
    Node<K,V>[] tab; int sc;
    while ((tab = table) == null || tab.length == 0) {
        if ((sc = sizeCtl) < 0)
            Thread.yield(); // 提示调度器让出执行机会，然后循环检查
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

数组未初始化且 `sizeCtl` 为负时，当前线程调用 `Thread.yield()`，再回到循环检查状态。[`yield` 的 API 文档](https://docs.oracle.com/javase/8/docs/api/java/lang/Thread.html#yield--)明确说明，这只是向调度器提示愿意让出执行机会，调度器可以忽略，不保证切换到其他线程。

`sizeCtl` 非负时，线程通过 CAS 尝试将其改为 -1，以获得初始化资格。成功后再次检查数组是否仍需初始化，完成分配后在 `finally` 中发布阈值 `n - (n >>> 2)`。对于通常的数组容量，该值为容量的 0.75 倍；很小的容量以整数公式的结果为准，例如 `n = 2` 时阈值为 2。

这里的 `compareAndSwapInt(this, SIZECTL, sc, -1)` 操作的是当前 map 的 `sizeCtl`：只有实际值仍等于预期的 `sc` 时，才原子地写入 -1 并返回 true。它与 `AtomicInteger` 的字段无关。

## 为什么延迟初始化

延迟分配可以减少尚未使用的 map 的内存开销。`putAll`、传入 Map 的构造方法和反序列化还可以根据元素规模安排容量，减少先按较小默认容量分配、随后再扩容的开销。

# treeifyBin树化

```java
private final void treeifyBin(Node<K,V>[] tab, int index) {
    Node<K,V> b; int n, sc;
    if (tab != null) {
        // 数组过小时先尝试扩容，本次不树化。
        if ((n = tab.length) < MIN_TREEIFY_CAPACITY)
            tryPresize(n << 1);
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
                    // 构建新的树桶后发布，原普通链表仍可供读线程遍历。
                    setTabAt(tab, index, new TreeBin<K,V>(hd));
                }
            }
        }
    }
}
```

1. 数组长度小于 `MIN_TREEIFY_CAPACITY = 64` 时调用 `tryPresize(n << 1)`，尝试通过扩容分散冲突；本次调用不执行树化。
2. 数组足够大时，锁住桶头并重新验证，复制链表节点生成 `TreeNode` 链表，再创建 `TreeBin` 并发布到桶位置。

原普通链表的 `next` 不会因为树化而被改写，已经拿到旧链表的读取线程可以继续遍历；后来读取桶头的线程则通过 `TreeBin` 查找。

# tryPresize扩容

`tryPresize(size)` 尝试预分配容量或推动扩容，参数是估算的元素数量。

以下保留该版本的有效执行路径，省略原实现内层 `if (sc < 0)` 分支：外层循环已保证局部变量 `sc >= 0`，进入该分支前也没有重新给 `sc` 赋负值，因此它不可达。其他线程修改的是字段 `sizeCtl`，不会改变当前线程已经读取的局部变量 `sc`；并发变化由后续 CAS 校验。

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
            // 先获得扩容戳，再移入 sizeCtl 的高位。
            int rs = resizeStamp(n);
            if (U.compareAndSwapInt(this, SIZECTL, sc,
                                   (rs << RESIZE_STAMP_SHIFT) + 2))
                transfer(tab, null);
        }
    }
}
```

1. 未触及最大容量限制时，先计算 `size + (size >>> 1) + 1`，再向上取整为 2 的幂得到 `c`，并非直接将 `size` 翻倍。
2. 如果数组未初始化，通过 CAS 获得初始化资格，按 `max(sizeCtl, c)` 分配数组。
3. 如果 `c <= sizeCtl`，或者数组已达到最大容量，结束尝试。这里比较的是 `c` 与扩容阈值，不能直接把 `c` 当作最终数组长度。
4. 否则计算扩容戳，通过 CAS 将 `sizeCtl` 改为扩容状态，调用 `transfer(tab, null)` 发起迁移。一次 `transfer` 将数组长度翻倍；外层循环可能继续发起下一轮扩容。

如果循环读取到负的 `sizeCtl`，本方法直接结束；协助已有扩容的路径主要在 `helpTransfer` 和 `addCount` 中。

## resizeStamp 的作用

`resizeStamp(n)` 根据旧数组长度生成扩容戳，计算公式是 `Integer.numberOfLeadingZeros(n) | (1 << 15)`。同一容量对应同一戳，容量变化后戳也变化；左移 16 位后，其最高位为 1，使扩容状态表现为负数。

高位的戳用于区分不同容量对应的扩容，低位用于线程计数。结合 `table`、`nextTable` 的身份校验和 CAS，线程才能围绕同一次迁移协调工作。

# helpTransfer帮助扩容

```java
final Node<K,V>[] helpTransfer(Node<K,V>[] tab, Node<K,V> f) {
    Node<K,V>[] nextTab; int sc;
    if (tab != null && (f instanceof ForwardingNode) &&
        (nextTab = ((ForwardingNode<K,V>)f).nextTable) != null) {
        // rs 已左移，可以与完整的 sizeCtl 编码比较。
        int rs = resizeStamp(tab.length) << RESIZE_STAMP_SHIFT;
        while (nextTab == nextTable && table == tab &&
               (sc = sizeCtl) < 0) {
            if (sc == rs + MAX_RESIZERS || sc == rs + 1 ||
                transferIndex <= 0)
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

遇到 `ForwardingNode` 表示当前旧桶已经处理，可以通过节点中保存的 `nextTable` 转向新数组，但不代表整个扩容已完成。

当前线程只有在旧表、新表仍匹配本次扩容、状态允许加入且还有待领取区间时，才通过 CAS 将 `sizeCtl` 加一，随后调用 `transfer` 帮忙。`transferIndex <= 0` 只表示区间已分配完，其他线程可能仍在迁移已经领取的桶。

即使不能加入迁移，只要取得了该转发节点的新表引用，也会返回它，让调用方继续操作。`get` 则直接调用 `ForwardingNode.find` 查找，不走帮助扩容的路径。

这里 `rs` 已经是左移后的扩容戳，`rs + 1` 表示收尾状态，`rs + MAX_RESIZERS` 表示已达编码允许的加入上限。旧片段中以未左移的 `rs` 与完整的负数 `sizeCtl` 比较不匹配；阅读不同版本时，需要同时检查 `rs` 的定义和使用位置。

# transfer真正的扩容

```java
private final void transfer(Node<K,V>[] tab, Node<K,V>[] nextTab) {
    int n = tab.length, stride;
    // 每次领取区间的目标长度，下限为 16；剩余区间可能更短。
    if ((stride = (NCPU > 1) ? (n >>> 3) / NCPU : n) < MIN_TRANSFER_STRIDE)
        stride = MIN_TRANSFER_STRIDE; // 按区间分配迁移工作
    if (nextTab == null) {            // 发起者创建新表，帮助者复用传入的新表
        try {
            @SuppressWarnings("unchecked")
            Node<K,V>[] nt = (Node<K,V>[])new Node<?,?>[n << 1];
            nextTab = nt;
        } catch (Throwable ex) {      // 分配失败时停止后续常规扩容尝试
            sizeCtl = Integer.MAX_VALUE;
            return;
        }
        nextTable = nextTab;
        transferIndex = n;
    }
    int nextn = nextTab.length;
    ForwardingNode<K,V> fwd = new ForwardingNode<K,V>(nextTab);
    boolean advance = true;
    boolean finishing = false; // 提交新表前再扫描一遍旧表
    for (int i = 0, bound = 0;;) {
        Node<K,V> f; int fh;
        // 当前区间处理完后，通过 CAS 领取 [nextBound, nextIndex)。
        while (advance) {
            int nextIndex, nextBound;
            if (--i >= bound || finishing)
                advance = false;
            else if ((nextIndex = transferIndex) <= 0) {
                i = -1;
                advance = false;
            }
            else if (U.compareAndSwapInt
                     (this, TRANSFERINDEX, nextIndex,
                      nextBound = (nextIndex > stride ?
                                   nextIndex - stride : 0))) {
                bound = nextBound;
                i = nextIndex - 1;
                advance = false;
            }
        }
        // 当前区间处理完且无区间可领，进入退出或收尾流程。
        if (i < 0 || i >= n || i + n >= nextn) {
            int sc;
            if (finishing) {
                nextTable = null;
                table = nextTab;
                sizeCtl = (n << 1) - (n >>> 1);
                return;
            }
            if (U.compareAndSwapInt(this, SIZECTL, sc = sizeCtl, sc - 1)) {
                // sc 是减一前的状态，R + 2 对应最后一个常规迁移线程。
                if ((sc - 2) != resizeStamp(n) << RESIZE_STAMP_SHIFT)
                    return;
                finishing = advance = true;
                i = n; // 最后一个线程从尾部重新扫描
            }
        }
        // 空桶也发布转发节点，防止后续写入留在旧表。
        else if ((f = tabAt(tab, i)) == null)
            advance = casTabAt(tab, i, null, fwd);
        else if ((fh = f.hash) == MOVED)
            advance = true; // 此桶已处理
        else {
            // 锁住旧桶头，并在获得锁后验证它仍是当前桶头。
            synchronized (f) {
                if (tabAt(tab, i) == f) {
                    Node<K,V> ln, hn;
                    if (fh >= 0) {
                        // 找到最后一段分组位相同的连续后缀，供新链表复用。
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
                        // 只复制 lastRun 之前的节点，不改写旧链表的 next。
                        for (Node<K,V> p = f; p != lastRun; p = p.next) {
                            int ph = p.hash; K pk = p.key; V pv = p.val;
                            if ((ph & n) == 0)
                                ln = new Node<K,V>(ph, pk, pv, ln);
                            else
                                hn = new Node<K,V>(ph, pk, pv, hn);
                        }
                        // 先发布新表两侧桶，再将旧桶替换为转发节点。
                        setTabAt(nextTab, i, ln);
                        setTabAt(nextTab, i + n, hn);
                        setTabAt(tab, i, fwd);
                        advance = true;
                    }
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
                        // 树桶拆分后，小的一侧转回链表；未分裂的大树可复用。
                        ln = (lc <= UNTREEIFY_THRESHOLD) ? untreeify(lo) :
                            (hc != 0) ? new TreeBin<K,V>(lo) : t;
                        hn = (hc <= UNTREEIFY_THRESHOLD) ? untreeify(hi) :
                            (lc != 0) ? new TreeBin<K,V>(hi) : t;
                        // 先发布新表两侧桶，再将旧桶替换为转发节点。
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

## 领取迁移区间

扩容发起者创建长度为 `2n` 的新数组，并设置 `nextTable` 和 `transferIndex = n`；帮助迁移的线程复用这个数组。

`stride` 是每次领取区间的目标长度，按 CPU 数和数组长度计算，下限为 16，但最后剩余区间可以不足 16 个桶。线程用 CAS 把 `transferIndex` 从 `nextIndex` 减至 `nextBound`，获得区间 `[nextBound, nextIndex)`，再从后向前处理。

`i` 是当前桶下标，`bound` 是当前区间的下界。处理完一个区间后，线程可以继续领取，不是每个线程固定只处理一段。领取区间的先后有序，不代表不同线程完成各桶迁移的顺序也有序。

## 迁移一个桶

1. 空桶：CAS 发布 `ForwardingNode`，将后续访问引向新表。如果 CAS 失败，重新处理这个位置。
2. 已是 `ForwardingNode`：说明这个桶已经处理，跳过。
3. 普通链表或树桶：锁住旧桶头 `f`，重新验证桶头身份后迁移。锁住的是旧桶的节点，不是新数组中的某个位置。
4. 节点按 `hash & n` 分组：为 0 的放在新数组 `i`，非 0 的放在 `i + n`，无需重新调用 key 的 `hashCode()`。
5. 先通过 `setTabAt` 发布新表的两个桶，再把旧桶替换为 `ForwardingNode`。观察到转发节点的读线程可以读取已经发布的新桶。

树桶拆分时分别统计两侧数量，某侧节点数 `<= UNTREEIFY_THRESHOLD = 6` 就将该侧转回链表；仍需树结构且发生两侧拆分时创建新 `TreeBin`。如果全部节点都落在同一侧且无需转回链表，则复用原 `TreeBin`。

## lastRun 如何复用链表尾部

迁移普通链表时，源码先寻找最后一段 `hash & n` 相同的连续节点，`lastRun` 指向这段后缀的开头。这些节点在新表中仍属于同一个桶，而且 `next` 无需变化，因此可以整段复用；`lastRun` 之前的节点则复制并通过头插法分别接入两条新链表。

例如，旧桶中各节点的 `hash & n` 如下，带撇号表示新创建的节点：

```text
旧链表：
A(0) → B(n) → C(0) → D(n) → E(n)
                     ↑ lastRun

新表 i：    C′ → A′
新表 i+n：  B′ → D → E
```

`D → E` 被复用，`A`、`B`、`C` 被复制。整个迁移过程不改写旧普通节点的 `next`，所以已经持有旧链表引用的读线程仍能沿旧链表查找。不能将这段逻辑概括为“全部新建两条链表”，也不能说它像 `HashMap` 一样直接重连所有旧节点。

## 最后一个线程如何提交扩容

没有剩余区间可领取时，迁移线程通过 CAS 将 `sizeCtl` 减一。判断使用的是 CAS 前的 `sc`：只有 `sc - 2 == R`，当前线程才是最后退出常规迁移阶段的线程。

它将 `finishing` 设为 true，重新扫描旧数组，确认各桶均已处理，然后清空 `nextTable`、将 `table` 指向新数组，并将 `sizeCtl` 恢复为新容量对应的阈值。在收尾期间，其他线程仍可以通过旧桶的转发节点访问新表。

# addCount方法

```java
private final void addCount(long x, int check) {
    CounterCell[] as; long b, s;
    // 无计数单元时先尝试基础计数，否则转入单元更新。
    if ((as = counterCells) != null ||
        !U.compareAndSwapLong(this, BASECOUNT, b = baseCount, s = b + x)) {
        CounterCell a; long v; int m;
        boolean uncontended = true;
        if (as == null || (m = as.length - 1) < 0 ||
            (a = as[ThreadLocalRandom.getProbe() & m]) == null ||
            !(uncontended =
              U.compareAndSwapLong(a, CELLVALUE, v = a.value, v + x))) {
            // 该路径完成计数后直接返回，本次不检查扩容。
            fullAddCount(x, uncontended);
            return;
        }
        if (check <= 1)
            return;
        s = sumCount();
    }
    // 只有未提前返回且 check 非负时，才执行扩容检查。
    if (check >= 0) {
        Node<K,V>[] tab, nt; int n, sc;
        while (s >= (long)(sc = sizeCtl) && (tab = table) != null &&
               (n = tab.length) < MAXIMUM_CAPACITY) {
            // 使用已左移的扩容戳。
            int rs = resizeStamp(n) << RESIZE_STAMP_SHIFT;
            if (sc < 0) {
                if (sc == rs + MAX_RESIZERS || sc == rs + 1 ||
                    (nt = nextTable) == null || transferIndex <= 0)
                    break;
                if (U.compareAndSwapInt(this, SIZECTL, sc, sc + 1))
                    transfer(tab, nt);
            }
            else if (U.compareAndSwapInt(this, SIZECTL, sc, rs + 2))
                transfer(tab, null);
            s = sumCount();
        }
    }
}
```

## 更新计数

`addCount(x, check)` 按 `x` 增减元素计数：普通新增传入 1，删除传入 -1，`clear` 也可以传入累计的负增量。它不是固定“元素个数加一”。

没有 `counterCells` 时，先尝试 CAS 更新 `baseCount`；如果已有计数单元，或者更新基础计数失败，则根据线程探针定位到一个 `CounterCell` 并尝试更新。单元不存在或仍有竞争时，交给 `fullAddCount` 完成初始化、重试或扩展等工作。

计数汇总相当于 `baseCount + 各 CounterCell.value 之和`。这是类似 `LongAdder` 的分散计数思路，可以减少线程争用同一个计数器。`sumCount()` 逐项读取，没有锁住整个 map，因此并发修改时得到的是瞬时汇总，不保证是某一时刻的精确快照。

## 检查扩容

`check` 控制是否尝试检查扩容，但非负不代表一定执行到检查代码：

- 走到 `fullAddCount` 后直接返回，本次不再检查扩容。
- CAS 更新 `CounterCell` 成功后，如果 `check <= 1`，直接返回。
- 未提前返回且 `check >= 0` 时，才执行扩容检查；例如删除使用 `check = -1`，跳过检查，也不会因此缩容。

达到阈值且当前没有扩容时，通过 CAS 将 `sizeCtl` 改为 `R + 2` 并发起迁移。如果已在扩容且仍允许加入，则尝试增加参与线程计数并帮助迁移。迁移返回后重新汇总计数，必要时继续下一轮检查。

# get方法

```java
public V get(Object key) {
    Node<K,V>[] tab; Node<K,V> e, p; int n, eh; K ek;
    int h = spread(key.hashCode());
    if ((tab = table) != null && (n = tab.length) > 0 &&
        (e = tabAt(tab, (n - 1) & h)) != null) {
        if ((eh = e.hash) == h) {
            if ((ek = e.key) == key || (ek != null && key.equals(ek)))
                return e.val;
        }
        // 特殊节点分别转向新表、树桶或占位节点的查找逻辑。
        else if (eh < 0)
            return (p = e.find(h, key)) != null ? p.val : null;
        while ((e = e.next) != null) {
            if (e.hash == h &&
                ((ek = e.key) == key || (ek != null && key.equals(ek))))
                return e.val;
        }
    }
    return null;
}
```

先检查桶头是否匹配，再处理特殊节点，否则沿普通链表的 `next` 查找。`spread` 会清除普通 hash 的符号位，因此负 hash 可以作为特殊节点的标记。`get(null)` 会在调用 `key.hashCode()` 时抛出 `NullPointerException`。

## ForwardingNode.find

`hash = -1` 时，调用 `ForwardingNode.find`，使用节点里保存的 `nextTable` 定位目标桶。如果在新表中又遇到转发节点，会继续转向下一张表，以处理连续扩容的情况。

该方法只查找，不帮助迁移，也不等待全表扩容完成。新表目标桶为空或没有对应键时，返回 `null`。

## TreeBin.find

`hash = -2` 时调用 `TreeBin.find`。`TreeBin` 同时保存红黑树结构和以 `first` 为入口的链表，因此查找有两条路径：

| 观察到的状态 | 查找方式 |
| --- | --- |
| `lockState` 中有 `WRITER` 或 `WAITER` | 有线程持有或等待树结构写锁，当前读线程先沿 `first/next` 链表查找，不阻塞等待写锁。 |
| 没有上述标记，且 CAS 增加 `READER` 成功 | 从 `root` 查树，结束后释放读计数，必要时唤醒等待中的写线程。 |
| CAS 增加读计数失败 | 重新读取状态并尝试。 |

链表查找过程中，每次循环都会重新观察锁状态，所以状态允许时也可能转入树查找。这里是 `TreeBin` 内部的读写协调机制，并非直接使用 `ReentrantReadWriteLock`。

树写操作先获取桶的 `synchronized` 锁，以串行化同桶更新；对需要与树读者互斥的旋转、平衡等操作，再通过 `lockState` 协调。因此“`get` 不获取桶锁”不等于“树读取完全没有同步操作”。

## ReservationNode.find

`hash = -3` 时遇到的是计算映射时的占位节点，其 `find` 返回 `null`。计算尚未发布映射时，并发 `get` 可以观察到该键当前没有值。

# 如何保证线程安全

## 一个线程put另一个线程也put

不同非空桶使用不同的桶头锁，同桶的更新则通过同一个锁串行化。对空桶的竞争由 CAS 决定胜者，失败者回到循环重试。

即使暂时只有一个线程更新，只要走到这里的普通非空桶路径，也会执行 `synchronized`，不能概括为“没有实际线程冲突就不加锁”。获取锁后还需重新检查桶头身份。

扩容线程迁移非空桶时也锁住旧桶头。写线程若先读到了这个旧桶头，可能等待该锁；若已经读到转发节点，则尝试帮助迁移并转向新表。初始化和计数更新还分别通过 `sizeCtl` 和计数相关的 CAS 协调。

## 一个线程put另一线程get

可见性需要结合整个发布和访问过程理解：桶头通过带 volatile 语义的数组操作读取和发布，节点的 `hash`、`key` 为 final，`val` 和 `next` 为 volatile，写入已构造节点后，读线程才能安全取得其内容。

更新已有映射时写入 `val`，链表追加时写入前驱的 `next`，`get` 使用相应的可见性保证读取。这不意味着与 `put` 同时进行的 `get` 必须返回新值；并发重叠时可能观察到旧值或新值。对于某个键，更新与报告该更新结果的非空读取之间具有 happens-before 关系，具体语义见 [ConcurrentHashMap API](https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/ConcurrentHashMap.html)。

## 在扩容或者树化的过程中get

扩容时，如果读线程拿到的是普通旧桶，就继续查旧链表；迁移不会重连这条旧链表。如果读到的是 `ForwardingNode`，则沿它转向已发布的新桶。安全性来自发布顺序、可见性和旧结构仍可遍历，不是因为 `get` 获取了迁移线程的锁。

树化会创建新树结构并替换桶头，已经拿到原链表的读线程仍能继续查找；读到 `TreeBin` 的线程使用上节介绍的树或链表查找路径。

## 线程安全的边界

单次映射操作的线程安全不等于多次调用组合后仍然原子。例如 `get` 后自行加一再 `put` 可能丢失其他线程的更新，需要根据语义使用 `merge`、`compute` 等原子复合操作。map 也不会自动保证 value 对象内部字段的并发修改安全。

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
        // 数组或桶不存在，正常返回未找到。
        if (tab == null || (n = tab.length) == 0 ||
            (f = tabAt(tab, i = (n - 1) & hash)) == null)
            break;
        // 返回新表继续操作，不要求整个扩容已经完成。
        else if ((fh = f.hash) == MOVED)
            tab = helpTransfer(tab, f);
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

`replaceNode` 同时供删除和替换操作复用：`value = null` 表示删除，非 null 表示替换；`cv` 非 null 时要求当前值与预期值匹配，用于带条件的删除或替换。

1. 数组或目标桶不存在时直接返回，属于正常的未找到情况。
2. 遇到转发节点时，尝试帮助迁移并转向新数组。
3. 锁住桶头并验证身份。链表删除通过修改前驱的 `next` 或桶头完成；树桶删除调用 `removeTreeNode`，必要时转回链表。
4. 实际删除成功才调用 `addCount(-1L, -1)`，减少计数并跳过扩容检查；普通 `remove(key)` 返回被删除的旧值，未找到则返回 `null`。

这里的 `removeTreeNode` 根据树的结构判断是否转回链表，不能直接套用“节点数不超过 6 就退化”的规则；明确按数量比较 `UNTREEIFY_THRESHOLD` 的是扩容拆分树桶的路径。

# 总结

| 场景 | 关键机制 |
| --- | --- |
| 初始化 | CAS 将 `sizeCtl` 设为 -1，获得资格后再次检查数组。 |
| 向空桶插入 | CAS 竞争桶位置，失败后重试。 |
| 更新非空桶 | 桶头 `synchronized` 加锁并重新验证身份。 |
| 普通读取 | volatile 数组元素访问和节点字段可见性，不获取桶锁。 |
| 树桶读取 | 使用读计数查树，遇到树写入或等待状态时沿链表查找。 |
| 扩容 | 多线程领取区间，桶级迁移；复用可保留的节点，通过转发节点连接新旧表。 |
| 元素计数 | `baseCount` 与 `CounterCell` 分散更新，并按路径选择是否检查扩容。 |

理解这些机制时，应把桶内互斥、读线程可见性和全表扩容协调分开分析，再结合起来解释一次完整操作。

# CAS的简单使用

CAS 的含义是：仅当当前值仍等于预期值时，原子地替换为新值。下面用 `AtomicInteger` 演示相同的比较并更新语义，避免通过反射修改 map 内部用于协调扩容的字段。

```java
import java.util.concurrent.atomic.AtomicInteger;

public class CasDemo {
    public static void main(String[] args) {
        AtomicInteger count = new AtomicInteger(0);

        System.out.println(count.compareAndSet(0, 100));
        System.out.println(count.get());

        // 当前值已是 100，预期值 0 不匹配，更新失败。
        System.out.println(count.compareAndSet(0, 200));
        System.out.println(count.get());

        // 预期值匹配，更新成功。
        System.out.println(count.compareAndSet(100, 200));
        System.out.println(count.get());
    }
}
```

输出：

```text
true
100
false
100
true
200
```

在并发环境中，读取预期值与执行 CAS 之间可能发生其他更新，所以 CAS 失败是正常的竞争结果。是否重试、是否重新读取其他状态，取决于具体算法；例如 `putVal` 会回到循环重新判断桶的状态。API 语义见 [`AtomicInteger.compareAndSet`](https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/atomic/AtomicInteger.html#compareAndSet-int-int-)。

# 参考

## 源码与官方文档

- [ConcurrentHashMap 源码：OpenJDK 8u402，jdk8u402-b06](https://github.com/openjdk/jdk8u/blob/jdk8u402-b06/jdk/src/share/classes/java/util/concurrent/ConcurrentHashMap.java)
- [ConcurrentHashMap：Java 8 API](https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/ConcurrentHashMap.html)
- [Thread.yield：Java 8 API](https://docs.oracle.com/javase/8/docs/api/java/lang/Thread.html#yield--)
- [AtomicInteger.compareAndSet：Java 8 API](https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/atomic/AtomicInteger.html#compareAndSet-int-int-)

## 原文延伸阅读

以下保留原文参考链接；涉及实现细节时，应以本文标注的源码版本为准。

- [CAS 方法讨论](https://coding.imooc.com/learn/questiondetail/49806.html)
- [Java Thread.yield 详解](https://blog.csdn.net/dabing69221/article/details/17426953)
- [ConcurrentHashMap 源码分析：JDK 8 版本](https://blog.csdn.net/programmer_at/article/details/79715177)
- [深度剖析 JDK 7 ConcurrentHashMap 中的知识点](https://www.jianshu.com/p/464065e4a043)
- [ConcurrentHashMap 源码阅读](https://juejin.im/post/5c40a1fa51882525ed5c4ac2#heading-11)
