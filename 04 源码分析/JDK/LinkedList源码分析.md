# 成员变量

```java
transient int size = 0;
transient Node<E> first;
transient Node<E> last;
```

# 几个方法

**添加**

```java
public boolean add(E e) {
    linkLast(e);
    return true;
}

void linkLast(E e) {
        final Node<E> l = last;
        final Node<E> newNode = new Node<>(l, e, null);
        last = newNode;
        if (l == null)
            first = newNode;
        else
            l.next = newNode;
        size++;
        modCount++;
}
```

在链表的结尾添加这个节点，另外，可以添加null元素。

**是否含有**

```java
public boolean contains(Object o) {
    return indexOf(o) != -1;
}

public int indexOf(Object o) {
        int index = 0;
        if (o == null) {
            for (Node<E> x = first; x != null; x = x.next) {
                if (x.item == null)
                    return index;
                index++;
            }
        } else {
            for (Node<E> x = first; x != null; x = x.next) {
                if (o.equals(x.item))
                    return index;
                index++;
            }
        }
        return -1;
}
```

返回第一个出现的元素的下标，没有就返回-1。

**移除**

```java
public boolean remove(Object o) {
    if (o == null) {
        for (Node<E> x = first; x != null; x = x.next) {
            if (x.item == null) {
                unlink(x);
                return true;
            }
        }
    } else {
        for (Node<E> x = first; x != null; x = x.next) {
            if (o.equals(x.item)) {
                unlink(x);
                return true;
            }
        }
    }
    return false;
}

E unlink(Node<E> x) {
        // assert x != null;
        final E element = x.item;
        final Node<E> next = x.next;
        final Node<E> prev = x.prev;

        if (prev == null) {
            first = next;
        } else {
            prev.next = next;
            x.prev = null;
        }

        if (next == null) {
            last = prev;
        } else {
            next.prev = prev;
            x.next = null;
        }

        x.item = null;
        size--;
        modCount++;
        return element;
}
```

删除。

**获取**

```java
public E get(int index) {
    checkElementIndex(index);
    return node(index).item;
}

Node<E> node(int index) {
        // assert isElementIndex(index);

        if (index < (size >> 1)) {
            Node<E> x = first;
            for (int i = 0; i < index; i++)
                x = x.next;
            return x;
        } else {
            Node<E> x = last;
            for (int i = size - 1; i > index; i--)
                x = x.prev;
            return x;
        }
    }
```

获取第index个元素，如果越界，会报错。另外，获取的时候是按二分搜索的方式寻找的。

**更改**

```java
public E set(int index, E element) {
    checkElementIndex(index);
    Node<E> x = node(index);
    E oldVal = x.item;
    x.item = element;
    return oldVal;
}
```

**指定位置添加**

```java
public void add(int index, E element) {
    checkPositionIndex(index);

    if (index == size)
        linkLast(element);
    else
        linkBefore(element, node(index));
}

void linkBefore(E e, Node<E> succ) {
        // assert succ != null;
        final Node<E> pred = succ.prev;
        final Node<E> newNode = new Node<>(pred, e, succ);
        succ.prev = newNode;
        if (pred == null)
            first = newNode;
        else
            pred.next = newNode;
        size++;
        modCount++;
    }
```

# Queue操作

**peek**

```java
public E peek() {
    final Node<E> f = first;
    return (f == null) ? null : f.item;
}
```

获取队列第一个节点，但不删除。如果队列为空就返回null。

**element**

```java
public E element() {
    return getFirst();
}

public E getFirst() {
        final Node<E> f = first;
        if (f == null)
            throw new NoSuchElementException();
        return f.item;
    }
```

获取队列第一个节点，但不删除。如果队列为空就报错。

**poll**

```java
public E poll() {
    final Node<E> f = first;
    return (f == null) ? null : unlinkFirst(f);
}
```

获取队列第一个节点，并删除。如果队列为空就返回null。

**remove**

```java
public E remove() {
    return removeFirst();
}

public E removeFirst() {
        final Node<E> f = first;
        if (f == null)
            throw new NoSuchElementException();
        return unlinkFirst(f);
    }
```

获取队列第一个节点，并删除。如果队列为空就抛出异常。

**offer**

```java
public boolean offer(E e) {
    return add(e);
}
```

在队列结尾添加一个元素，可以为null。

# Stack操作

**push**

```java
public void push(E e) {
    addFirst(e);
}
```

在链表的头部添加一个元素。

**pop**

```java
public E pop() {
    return removeFirst();
}
```

# 操作总结

-   add
    放在链表的尾部
-   addFirst
    放在链表的头部
-   addLast
    和add一样，放在链表的尾部
-   element
    获取链表的头元素，如果为null，报出异常。
-   offer
    和add一样，放在链表的尾部
-   peek
    获取链表的头元素，可以为null。
-   poll
    获取链表的头元素，可以为null，并弹出。
-   pop
    获取链表的头元素，如果为null，报出异常，并弹出。
-   push
    和add一样，放在链表的尾部
-   remove
    移除链表第一个元素，如果为null，报出异常。