# 知识点总结

1. HashMap 使用数组和链表/红黑树存储键值对。数组中的一个位置称为一个桶，桶入口为 `null` 或该桶的首节点。多个 key 定位到同一个桶时，通过链表或红黑树组织节点。
2. `capacity` 是桶数组 `table` 的长度，`size` 是整个 Map 的键值对数量。
3. `loadFactor` 是构造时设置的加载因子，默认值为 `0.75`，可以大于 `1`。它与当前装载程度 `size / capacity` 是两个概念。数组初始化后，扩容阈值 `threshold` 通常按 `(int)(capacity * loadFactor)` 计算；普通 `put` 新增键值对后，如果 `size > threshold`，会调用 `resize()`。
4. 已分配的桶数组长度是 2 的幂，最大为 `1 << 30`。普通扩容将容量翻倍；到达最大容量后不再扩大数组，并将 `threshold` 设为 `Integer.MAX_VALUE`。这个值是扩容阈值的特殊取值，不是加载因子的最大值。
5. `HashMap<K, V>` 的泛型参数使用引用类型，基本类型需要装箱。HashMap 允许一个 `null` key 和多个 `null` value。`hash(null)` 返回 `0`，因此 null key 位于第 0 个桶；该桶也可能树化，null key 不一定是首节点。
6. HashMap 不保证遍历顺序，也不提供线程安全保证。线程安全和迭代器的 fail-fast 是不同的问题，见后面的面试题。

## 常量与成员变量

| 名称 | 类型及取值 | 含义 |
| --- | --- | --- |
| `DEFAULT_INITIAL_CAPACITY` | `static final int`，`1 << 4` | 默认初始容量为 16；无参构造时尚未分配数组 |
| `MAXIMUM_CAPACITY` | `static final int`，`1 << 30` | 桶数组最大容量为 2³⁰ |
| `DEFAULT_LOAD_FACTOR` | `static final float`，`0.75f` | 默认加载因子 |
| `MIN_TREEIFY_CAPACITY` | `static final int`，`64` | 允许树化的最小数组长度；小于 64 时优先扩容 |
| `TREEIFY_THRESHOLD` | `static final int`，`8` | 树化阈值；普通 `put` 向已有至少 8 个节点的链表追加新节点时尝试树化 |
| `UNTREEIFY_THRESHOLD` | `static final int`，`6` | 扩容拆分树桶时，某侧节点数不超过 6，则将该侧转回普通链表 |
| `threshold` | `int` | 数组分配前暂存目标初始容量；分配后通常为扩容阈值 |
| `size` | `transient int` | 已存储的键值对数量 |
| `loadFactor` | `final float` | 当前实例设置的加载因子 |
| `table` | `transient Node<K,V>[]` | 桶数组，每个位置保存桶的首节点引用 |
| `modCount` | `transient int` | 结构修改计数，供迭代器等执行 fail-fast 检查 |

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

指定初始容量的构造方法只检查参数、设置加载因子，并把 `tableSizeFor(initialCapacity)` 存入 `threshold`，此时 `table` 仍为 `null`。以随后调用普通 `put` 为例，第一次插入时才通过 `resize()` 分配数组。

`tableSizeFor` 将容量向上调整到 2 的幂，结果限制在 `1` 到 `MAXIMUM_CAPACITY` 之间。先执行 `cap - 1`，是为了让已经为 2 的幂的输入保持不变；连续的右移和按位或将最高有效位以下填成 `1`，最后加 `1` 得到目标容量。

例如，`new HashMap<>(10)` 使用默认加载因子，其状态变化如下：

| 阶段 | `table` | `threshold` | `size` |
| --- | --- | --- | --- |
| 构造完成 | `null` | `16`，暂存目标初始容量 | `0` |
| 第一次 `put` 完成 | 长度为 `16` 的数组 | `12`，即 `16 × 0.75` | `1` |

无参构造只设置默认加载因子，`threshold` 初始为 `0`，第一次普通 `put` 时使用容量 `16`、阈值 `12`。因此，构造参数表示初始桶容量，不是承诺无需扩容即可容纳的键值对数量。

### hash

```java
// HashMap 计算扰动后的 hash
static final int hash(Object key) {
    int h;
    return (key == null) ? 0 : (h = key.hashCode()) ^ (h >>> 16);
}
// 下面是下标计算表达式，n 为已初始化的 table.length
// int index = (n - 1) & hash;
```

当数组长度为 2 的幂时，`(n - 1) & hash` 只使用 hash 的低若干位。如果 key 的原始哈希码只在高位不同，它们可能被分到同一个桶。

`h ^ (h >>> 16)` 将高 16 位的信息混入低 16 位，使高位差异也有机会影响桶下标。它是确定性的位混合，不能保证消除冲突；原本 `hashCode()` 相同的 key，扰动后的 hash 仍然相同。

### put

`put(key, value)` 先计算 hash，再调用 `putVal`，主要流程如下：

1. 如果 `table` 尚未初始化，先调用 `resize()` 分配数组，再根据 `(n - 1) & hash` 计算桶下标。
2. 如果桶为空，直接创建普通节点放入。
3. 如果桶非空，先检查首节点。匹配要求 hash 相同，并且 key 满足以下任一条件：引用相同；传入的 key 非 null，且 `key.equals(节点的 key)` 为 `true`。
4. 首节点不匹配时，如果是树桶，调用 `putTreeVal` 查找或插入；如果是普通链表，则遍历查找，未找到才在尾部追加节点。
5. 向已有至少 8 个节点的链表追加新节点后，调用 `treeifyBin`。数组长度小于 64 时扩容，否则将该桶树化。
6. 如果找到已有 key，只更新 value 并返回旧值，不增加 `size` 或 `modCount`，也不会因为此次覆盖进入末尾的扩容检查。
7. 如果新增了键值对，则增加 `modCount` 和 `size`；若 `size > threshold`，调用 `resize()`，最后返回 `null`。

桶冲突和 key 相等是两回事：桶下标相同不代表 hash 相同，hash 相同也不代表 key 相等。

### resize

`resize()` 同时承担数组初始化和扩容，不能一概理解为“容量和阈值翻倍”：

1. 数组尚未分配时，使用 `threshold` 暂存的初始容量，或者使用默认容量。
2. 已有数组且未达到容量上限时，将数组长度翻倍。通常也将阈值翻倍；对于小容量或接近上限等情况，源码会重新计算或设置特殊阈值。
3. 已达到 `MAXIMUM_CAPACITY` 时，将 `threshold` 设为 `Integer.MAX_VALUE`，直接返回旧数组。

真正扩容时，先创建新数组，再逐桶迁移：单节点直接计算新下标；普通链表按 `hash & oldCap` 拆成 low、high 两组，保留各组内部的相对顺序；树桶调用 `TreeNode.split()`。

由于容量翻倍后，下标掩码只增加一个有效位，因此旧桶下标为 `j` 的节点只有两个去向：

| 判断条件 | 分组 | 新桶下标 |
| --- | --- | --- |
| `(hash & oldCap) == 0` | low | `j` |
| `(hash & oldCap) != 0` | high | `j + oldCap` |

例如，旧容量为 `16`（二进制 `10000`），两个节点保存的 hash 分别为 `15`（`01111`）和 `31`（`11111`）。它们在旧数组中都位于下标 `15`；扩容到 `32` 后，分别位于下标 `15` 和 `31`。这里参与运算的是节点保存的 hash，不是 key 本身，迁移时也不需要重新调用 key 的 `hashCode()`。

树桶同样沿节点的 `next` 链拆分，并统计两侧节点数。某侧非空且节点数 `<= 6` 时，将该侧转换为普通链表；超过 6 时保留树节点。如果两侧都有节点，需要为保留树形的一侧重建树；若全部节点都留在同一侧且仍超过 6，则可沿用原树结构。

### 树化与退化

`treeifyBin` 先检查数组长度：小于 `MIN_TREEIFY_CAPACITY`（64）时调用 `resize()`，否则把普通 `Node` 替换为 `TreeNode`，再建立红黑树。树节点同时维护 `parent/left/right` 等树指针和 `prev/next` 链接，因此树桶既能按树查找，也能沿链遍历。

在 JDK 8 的普通 `put` 路径中，`binCount` 从 `0` 开始，追加节点时检查 `binCount >= TREEIFY_THRESHOLD - 1`。链表原有 8 个节点时，走到尾节点的 `binCount` 为 7，因此插入第 9 个节点才触发树化尝试。实际树化还要求数组长度 `>= 64`。

这个“第 9 个”的结论针对 `putVal`。JDK 8 的 `computeIfAbsent`、`compute`、`merge` 有各自的遍历计数与插入逻辑，不能把同一个节点数结论直接套到所有写入方法。

扩容拆分树桶时，某侧节点数 `<= UNTREEIFY_THRESHOLD`（6）会退化；普通 `remove` 则根据树的结构判断是否过小，并不是直接统计剩余节点数后与 6 比较。

树化用于改善长链表的查找成本。红黑树高度为 `O(log n)`，但 HashMap 的树桶查找还取决于 key 的比较方式：hash 能区分，或 hash 相同但 key 可以有效比较排序时，能够沿树查找；若大量 key 的 hash 相同且无法有效比较排序，查找可能搜索多个分支，最坏仍可达到 `O(n)`。这里的 `n` 是桶内节点数。

阈值 8 和 6 是时间、空间和转换成本之间的折中。源码注释指出，树节点占用的空间大约是普通节点的两倍，哈希分布良好时长桶又很少出现；树化与退化采用不同阈值，也有助于避免频繁转换。不能通过 `log₂8 = 3` 与 `8 / 2 = 4` 的比较推导这些阈值。参见 [HashMap 源码的实现说明和 TreeNode 方法](https://github.com/openjdk/jdk8u/blob/master/jdk/src/share/classes/java/util/HashMap.java)。

### remove

1. 根据 key 的 hash 和数组长度定位桶；若数组未初始化或桶为空，直接返回 `null`。
2. 按 hash 和 key 相等条件检查首节点，再按桶类型搜索红黑树或链表。找不到 key 时，不修改 Map。
3. 找到后，普通链表通过调整桶入口或前驱节点的 `next` 移除节点；树桶调用 `removeTreeNode`，维护链关系和树结构，必要时转回普通链表。
4. 成功删除后，增加 `modCount`、减少 `size`，返回旧 value。删除不存在的 key 不改变这两个计数。

普通 `remove` 不会缩小桶数组。树桶退化为链表也不意味着 `table` 容量变小。另外，返回 `null` 既可能表示 key 不存在，也可能表示被删除的旧 value 本来就是 `null`。

## 感悟

HashMap 把容量保持为 2 的幂，使桶定位可以使用 `(n - 1) & hash`，扩容时可以用 `hash & oldCap` 判断节点是否移动。一次遍历就能拆分链表，并保留两组各自的相对顺序。

不过，“翻倍后只有两个去向”并非位运算独有。对非负整数 hash，若使用取模定位，设旧下标 `j = hash % n`，则 `hash = q * n + j`，所以 `hash % (2 * n)` 仍只可能为 `j` 或 `j + n`，与 `q` 的奇偶性有关，即使 `n` 不是 2 的幂也成立。

2 的幂使上述定位与拆分可以直接通过位运算实现。如果新容量不是旧容量的两倍，则不能套用这套 low/high 拆分规则。Java 的 `%` 对负数可能得到负余数，直接用 `hash % len` 还需要处理负下标。

# 面试题

## 🌟🌟 HashMap 和 Hashtable 有什么区别？

| 对比项 | HashMap | Hashtable |
| --- | --- | --- |
| null 支持 | 允许 null key 和 null value | key 和 value 均不允许 null |
| 线程安全 | 不提供同步保证 | `get`、`put`、`remove` 等方法通过对象锁同步 |
| 默认初始容量 | 16，无参构造时延迟分配数组 | 11，构造时分配数组 |
| 常规扩容 | 原容量的 2 倍 | `2 * 原容量 + 1`，另有容量上限处理 |
| 指定初始容量 | 调整到 2 的幂并受最大容量限制，延迟分配 | 正数直接使用；传入 0 时按 1 分配 |
| 继承关系 | 继承 `AbstractMap` | 继承 `Dictionary` |

HashMap 对 null key 的处理是 `hash(null) == 0`，并不是调用 null 的 `hashCode()`。Hashtable 的构造、扩容和同步方式见 [OpenJDK 8u Hashtable 源码](https://github.com/openjdk/jdk8u/blob/master/jdk/src/share/classes/java/util/Hashtable.java)。

需要同步包装时，可以使用：

```java
Map<String, Integer> map = Collections.synchronizedMap(new HashMap<>());

// 遍历集合视图时，需要在返回的 map 对象上同步
synchronized (map) {
    for (Map.Entry<String, Integer> entry : map.entrySet()) {
        System.out.println(entry);
    }
}
```

所有并发访问都应经过包装后的 Map。多个独立方法调用组成的复合操作，也需要额外同步或使用合适的原子方法；单个方法线程安全不代表整个操作序列原子化。参见 [Collections.synchronizedMap 文档](https://docs.oracle.com/javase/8/docs/api/java/util/Collections.html#synchronizedMap-java.util.Map-)。

## 🌟🌟 ConcurrentHashMap 和 Hashtable 有什么区别？

两者均支持并发访问，并且都不允许 null key 和 null value，但同步方式不同。

1. Hashtable 的 `get`、`put`、`remove` 等方法使用同一个对象锁，多线程调用这些方法时会竞争该锁。
2. JDK 8 的 ConcurrentHashMap 不再使用 Segment 作为主要存储和分段锁结构。以普通 `put` 为例，空桶插入使用 CAS，非空桶更新通常在桶首节点上使用 `synchronized`；`get` 通常不加锁。具体流程见 [ConcurrentHashMap 源码](https://github.com/openjdk/jdk8u/blob/master/jdk/src/share/classes/java/util/concurrent/ConcurrentHashMap.java)。
3. ConcurrentHashMap 的迭代器具有弱一致性，可以与更新并发执行，不保证得到某一时刻的完整快照，也不会因并发修改抛出 `ConcurrentModificationException`。不能将其描述为“迭代时锁住某个部分”。参见 [ConcurrentHashMap 文档](https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/ConcurrentHashMap.html)。
4. Hashtable 的集合视图迭代器是 fail-fast，并不会自动为整个迭代过程持有对象锁。如果需要防止遍历期间被其他线程修改，应显式在 Hashtable 对象上同步整个遍历过程。其 `keys()`、`elements()` 返回的 Enumeration 不属于 fail-fast 迭代器。参见 [Hashtable 文档](https://docs.oracle.com/javase/8/docs/api/java/util/Hashtable.html)。

ConcurrentHashMap 更细的同步粒度有利于并发访问，但实际性能还取决于竞争程度、key 分布和操作类型，不能概括成“Hashtable 大到一定程度就必然急剧变慢”。

## 🌟 HashMap、SparseArray、ArrayMap 有什么区别？

SparseArray 和 ArrayMap 是 Android 提供的容器，重点是减少内存开销。

| 对比项 | HashMap | SparseArray | ArrayMap |
| --- | --- | --- | --- |
| key 类型 | 引用类型，基本类型需要装箱 | `int`，无需为 key 装箱 | 引用类型，基本类型需要装箱 |
| 主要结构 | 桶数组和节点 | 有序 int key 数组和 value 数组 | 有序 hash 数组和 key/value 数组 |
| 查找方式 | hash 定位后搜索桶 | 对 key 二分查找 | 对 hash 二分查找，再比较 key |
| 内存特点 | 每个键值对需要节点对象 | 不需要独立节点或装箱 key | 不需要为每个键值对创建独立节点 |
| 使用考虑 | 通用映射容器 | 较小规模的 int key 映射 | 较小规模、重视内存占用的通用 key 映射 |

Android 官方文档说明，SparseArray 和 ArrayMap 通常比 HashMap 慢，因为查找需要二分搜索，插入和删除涉及数组处理；它们不适合不加区分地替换大规模 HashMap。SparseArray 还通过删除标记延迟整理数组。参见 [SparseArray 文档](https://developer.android.com/reference/android/util/SparseArray)和 [ArrayMap 文档](https://developer.android.com/reference/android/util/ArrayMap)。

是否值得替换，应结合数据规模、读写比例和设备上的测量结果判断。不能把“1000 以下”“节省 30%”或 IDE 是否提示替换当作普遍保证。

## 🌟🌟🌟 fail-fast 能检测 HashMap 的线程安全问题吗？

不能可靠检测。fail-fast 用于尽力发现迭代期间的结构修改，不提供同步、可见性或原子性保证；即使没有抛出异常，也不能说明并发访问安全。参见 [HashMap 官方文档](https://docs.oracle.com/javase/8/docs/api/java/util/HashMap.html)。

HashMap 迭代器创建时将 `modCount` 保存为 `expectedModCount`。后续执行 `next()`、迭代器的 `remove()` 等操作时，如果两个计数不一致，就会抛出 `ConcurrentModificationException`。检查不是持续发生的，`hasNext()` 也不会执行这项检查。

| 操作 | 对 `modCount` 的影响 |
| --- | --- |
| `get`、覆盖已有 key 的 value、`Map.Entry.setValue` | 不增加 |
| `put` 新增 key | 增加 |
| `remove` 成功删除 key | 增加；删除不存在的 key 不增加 |
| `clear` | 增加，JDK 8 中即使 Map 已为空也会增加 |
| 当前迭代器自己的 `remove()` | 增加，并更新该迭代器的 `expectedModCount` |

因此，单线程 `for-each` 中直接新增 key 或删除已有 key，也可能在后续迭代检查时抛出异常；只覆盖已有 key 的 value 不会因此触发 fail-fast。需要边遍历边删除时，使用显式迭代器的 `remove()`：

```java
Map<String, Integer> map = new HashMap<>();
map.put("keep", 1);
map.put("remove", 0);

Iterator<Map.Entry<String, Integer>> iterator = map.entrySet().iterator();
while (iterator.hasNext()) {
    Map.Entry<String, Integer> entry = iterator.next();
    if (Integer.valueOf(0).equals(entry.getValue())) {
        iterator.remove();
    }
}
```

这是单线程迭代删除的正确用法，不会使 HashMap 自动变得线程安全。并发修改时仍需要外部同步，或者使用 ConcurrentHashMap 等并发容器。

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
    // 以上代码计算新的 table 容量和扩容阈值
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
