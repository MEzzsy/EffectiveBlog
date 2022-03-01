# 解析

每次新建一个HashMap时，都会初始化一个table数组。table数组的元素为Node节点。

Node为内部类，继承了Map.Entry。

对于一个key，如果hashCode不同，equals一定为false，如果hashCode相同，equals不一定为true。

所以理论上，hashCode可能存在冲突的情况，也叫发生了碰撞，当碰撞发生时，计算出的bucketIndex也是相同的，这时会取到bucketIndex位置已存储的元素，最终通过equals来比较，equals方法就是哈希码碰撞时才会执行的方法，所以说HashMap很少会用到equals。HashMap通过hashCode和equals最终判断出K是否已存在，如果已存在，则使用新V值替换旧V值，并返回旧V值，如果不存在 ，则存放新的键值对<K, V>到bucketIndex位置。

1) 首先判断key是否为null，若为null，则直接调用putForNullKey方法，如果key为null的值，默认就存储到table[0]开头的链表了。然后遍历table[0]的链表的每个节点Entry，如果发现其中存在节点Entry的key为null，就替换新的value，然后返回旧的value，如果没发现key等于null的节点Entry，就增加新的节点。
1) 计算key的hashcode（hash(key.hashCode())），再用计算的结果二次hash（indexFor(hash, table.length)），找到Entry数组的索引i。
1) 遍历以table[i]为头节点的链表，如果发现hash，key都相同的节点时，就替换为新的value，然后返回旧的value，只有hash相同时，循环内并没有做任何处理。
1) modCount++代表修改次数，与迭代相关。
1) 对于hash相同但key不相同的节点以及hash不相同的节点，就增加新的节点。
1) 对于用户给定的大小，HashMap会把它扩充为2的幂次方。

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

# 总结

1.   HashMap结合了数组和链表的优点，使用Hash算法加快访问速度，使用散列表解决碰撞冲突的问题，其中数组的每个元素是单链表的头结点，链表是用来解决冲突的。
2.   HashMap有两个重要的参数：初始容量和加载因子。这两个参数极大的影响了HashMap的性能。初始容量是hash数组的长度，当前加载因子=当前hash数组元素/hash数组长度，最大加载因子为最大能容纳的数组元素个数（默认最大加载因子为0.75），当hash数组中的元素个数超出了最大加载因子和容量的乘积时，要对hashMap进行扩容，扩容过程存在于hashmap的put方法中，扩容过程始终以2次方增长。
3.   HashMap是泛型类，key和value可以为任何类型，包括null类型。key为null的键值对永远都放在以table[0]为头结点的链表中，当然不一定是存放在头结点table[0]中。