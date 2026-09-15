简单理解就是HashTable的put、get、remove方法都有锁。

```
 public synchronized V get(Object key)
 public synchronized V put(K key, V value)
 public synchronized V remove(Object key)
```

