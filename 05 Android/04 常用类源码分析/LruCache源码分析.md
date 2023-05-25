# 源码及分析

源码并不多，这里就全部复制进来。

LruCache与LinkedHashMap息息相关，LinkedHashMap源码分析见[LinkedHashMap源码分析](LinkedHashMap源码分析.md)。

```java
public class LruCache<K, V> {
    private final LinkedHashMap<K, V> map;
  
    private int size;//键值对的总大小，如果没有重写sizeOf方法，那么表示键值对的总数
    private int maxSize;
    private int putCount;
    private int createCount;
    private int evictionCount;
    private int hitCount;
    private int missCount;

  	//如果没有重写sizeOf方法，那么maxSize就是此缓存entries数量的最大值。如果重写了，那么就是entries大小总和的最大值
    public LruCache(int maxSize) {
        if (maxSize <= 0) {
            throw new IllegalArgumentException("maxSize <= 0");
        }
        this.maxSize = maxSize;
        this.map = new LinkedHashMap<K, V>(0, 0.75f, true);
    }
		
  	//返回key对应的value，如果value是非null的，那么根据最近最少使用算法，它会移到队列的最前面。
    public synchronized final V get(K key) {
        if (key == null) {
            throw new NullPointerException("key == null");
        }
        V result = map.get(key);
        if (result != null) {
            hitCount++;
            return result;
        }
        missCount++;
        result = create(key);
        if (result != null) {
            createCount++;
            size += safeSizeOf(key, result);
            map.put(key, result);
            trimToSize(maxSize);
        }
        return result;
    }

  	//放入键值对，并且value会移到队列的最前端。返回旧的value
    public synchronized final V put(K key, V value) {
        if (key == null || value == null) {
            throw new NullPointerException("key == null || value == null");
        }
        putCount++;
        size += safeSizeOf(key, value);
        V previous = map.put(key, value);
        if (previous != null) {
            size -= safeSizeOf(key, previous);
        }
        trimToSize(maxSize);
        return previous;
    }

  	//如果此缓存中的size超过了maxSize，那么会删除一些键值对。
    private void trimToSize(int maxSize) {
        while (size > maxSize && !map.isEmpty()) {
            Map.Entry<K, V> toEvict = map.entrySet().iterator().next();
            if (toEvict == null) {
                break; 
            }
            K key = toEvict.getKey();
            V value = toEvict.getValue();
            map.remove(key);
            size -= safeSizeOf(key, value);
            evictionCount++;
            entryEvicted(key, value);
        }
        if (size < 0 || (map.isEmpty() && size != 0)) {
            throw new IllegalStateException(getClass().getName()
                    + ".sizeOf() is reporting inconsistent results!");
        }
    }
  
   	//删除某个键值对
    public synchronized final V remove(K key) {
        if (key == null) {
            throw new NullPointerException("key == null");
        }
        V previous = map.remove(key);
        if (previous != null) {
            size -= safeSizeOf(key, previous);
        }
        return previous;
    }

  	//对那些队列末尾并被移除的键值对进行回调，默认什么都不做
    protected void entryEvicted(K key, V value) {
    }

  	//如果在get方法中key没有返回一个非null的value，那么会调用此方法来创建一个对应的value，默认不创建（返回null）。
    protected V create(K key) {
        return null;
    }

  	//计算键值对的大小，如果没有重写sizeOf方法，那么返回的是键值对的数量。
    private int safeSizeOf(K key, V value) {
        int result = sizeOf(key, value);
        if (result < 0) {
            throw new IllegalStateException("Negative size: " + key + "=" + value);
        }
        return result;
    }

  	//计算键值对的大小。默认返回的是1（表示1个键值对）
    protected int sizeOf(K key, V value) {
        return 1;
    }
  
  	//清空缓存
    public synchronized final void evictAll() {
        trimToSize(-1);
    }

    public synchronized final int size() {
        return size;
    }

    public synchronized final int maxSize() {
        return maxSize;
    }

    public synchronized final int hitCount() {
        return hitCount;
    }

    public synchronized final int missCount() {
        return missCount;
    }

    public synchronized final int createCount() {
        return createCount;
    }

    public synchronized final int putCount() {
        return putCount;
    }

    public synchronized final int evictionCount() {
        return evictionCount;
    }

    public synchronized final Map<K, V> snapshot() {
        return new LinkedHashMap<K, V>(map);
    }

    @Override
    public synchronized final String toString() {
        int accesses = hitCount + missCount;
        int hitPercent = accesses != 0 ? (100 * hitCount / accesses) : 0;
        return String.format("LruCache[maxSize=%d,hits=%d,misses=%d,hitRate=%d%%]", maxSize, hitCount, missCount, hitPercent);
    }
}
```

# 总结

LruCache\<K,V\>是一种根据最近最少使用算法的缓存策略，内部持有一个LinkedHashMap，在创建LruCache对象的时候需要设定maxSize，当缓存的键值对的数量/大小超过了maxSize（具体见上面的解析），那么会调整大小，将不使用的缓存去除。

放入或者获取缓存会将缓存移到队列的前端，而这个队列就是LinkedHashMap的链表，链表的顺序是头节点是最旧的节点，尾节点是最新操作的节点，迭代顺序也是如此，所以在LruCache的trimToSize方法中会从头开始，删除一些节点。