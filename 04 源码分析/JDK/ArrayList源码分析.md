# 源码分析

```java
private static final int DEFAULT_CAPACITY = 10;
```

默认的初始容量为10

```java
transient Object[] elementData;
```

内部存放数据的数组

```java
private int size;
```

ArrayList中实际数据的数量

```java
public void trimToSize() {
    modCount++;
    if (size < elementData.length) {
        elementData = (size == 0)
          ? EMPTY_ELEMENTDATA
          : Arrays.copyOf(elementData, size);
    }
}
```

将当前容量值设为当前实际元素大小

```java
private void grow(int minCapacity) {
    // overflow-conscious code
    int oldCapacity = elementData.length;
    int newCapacity = oldCapacity + (oldCapacity >> 1);
    if (newCapacity - minCapacity < 0)
        newCapacity = minCapacity;
    if (newCapacity - MAX_ARRAY_SIZE > 0)
        newCapacity = hugeCapacity(minCapacity);
    // minCapacity is usually close to size, so this is a win:
    elementData = Arrays.copyOf(elementData, newCapacity);
}
```

ArrayLIst的默认初始化容量是10 ，容量不够的时候会变成原来的1.5倍

```java
public void add(int index, E element) {
    if (index > size || index < 0)
        throw new IndexOutOfBoundsException(outOfBoundsMsg(index));

    ensureCapacityInternal(size + 1);  // Increments modCount!!
    System.arraycopy(elementData, index, elementData, index + 1,
                     size - index);
    elementData[index] = element;
    size++;
}
```

```java
public E get(int index) {
    if (index >= size)
        throw new IndexOutOfBoundsException(outOfBoundsMsg(index));

    return (E) elementData[index];
}
```

```java
public E set(int index, E element) {
    if (index >= size)
        throw new IndexOutOfBoundsException(outOfBoundsMsg(index));

    E oldValue = (E) elementData[index];
    elementData[index] = element;
    return oldValue;
}
```

```
public boolean add(E e) {
    ensureCapacityInternal(size + 1);  // Increments modCount!!
    elementData[size++] = e;
    return true;
}
```

时间复杂度为O(1)

```java
public void add(int index, E element) {
    if (index > size || index < 0)
        throw new IndexOutOfBoundsException(outOfBoundsMsg(index));

    ensureCapacityInternal(size + 1);  // Increments modCount!!
    System.arraycopy(elementData, index, elementData, index + 1,
                     size - index);
    elementData[index] = element;
    size++;
}
```

用native方法arraycopy将elementData数组在index位置向后移一位，然后在index位置插入element。

```java
public E remove(int index) {
    if (index >= size)
        throw new IndexOutOfBoundsException(outOfBoundsMsg(index));

    modCount++;
    E oldValue = (E) elementData[index];

    int numMoved = size - index - 1;
    if (numMoved > 0)
        System.arraycopy(elementData, index+1, elementData, index,
                         numMoved);
    elementData[--size] = null; // clear to let GC do its work

    return oldValue;
}
```

需要把剩下的右移，所以时间复杂度为O(1)

**ArrayList遍历方式**

1、通过迭代器遍历。

2、随机访问，通过索引值去遍历，由于ArrayList实现了RandomAccess接口。

3、for循环遍历。

# ArrayList源码总结

默认容量是10，可以自定义容量。

成员变量有个数组`Object[] elementData`，用来存储数据。

## 部分方法解析

**添加数据（add方法）**

在最后面的位置添加。

```
elementData[size++] = e;
```

**插入**

将当前位置的后面的数据往后移，然后在当前位置插入新的数据。

**删除（remove方法）**

如果是最后一个，那么直接令其为null，否则将后面的元素往前移。

**扩容**

在添加和插入之前，会进行扩容判定，如果添加后（size+1）会超出容量，那么会进行扩容。

容量变为原来的1.5倍。

## 总结

-   ArrayList是基于动态数组实现的，随机存取快，但是在增删时候，需要数组的拷贝复制，这个时候明显劣势。
-   它不是线程安全的。
-   它能存放null值。
-   ArrayList的默认初始化容量是10，每次扩容时候增加原先容量的一半，也就是变为原来的1.5倍

# 几个问题

## LinkedList和ArrayList的区别

1. ArrayList是实现了基于动态数组的数据结构，而LinkedList是基于链表的数据结构
2. 对于随机访问get和set，ArrayList要优于LinkedList，因为LinkedList要移动指针
3. 对于添加和删除操作add和remove，ArrayList要移动数据；LinkedList的添加和删除是O(1)的，但是寻找元素需要时间，它是利用折半的方法查找的，如果index小于size的一半就从前往后，反之从后往前。总的来说LinkedList略占优势。

## 数组或者容器的最大长度

数组的length是int类型，最大值为2的31次方-1，当设置了这个值后会导致内存溢出。那么实际的最大长度是多少呢？这个和虚拟机的参数有关，可以通过设置参数来更改内存最大值。

