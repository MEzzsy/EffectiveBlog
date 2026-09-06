当key为int类型的时候可以使用SparseArray。

成员变量

```java
private static final Object DELETED = new Object();
private boolean mGarbage = false;
private int[] mKeys;
private Object[] mValues;
private int mSize;
```

默认大小是10

mKeys是升序排序的。

# 放入（put方法)

1.   二分搜索寻找key在数组中的位置，如果key存在，更新值。反之，返回二分搜索得到的下标。
2.   下标小于size并且该下标被标记为删除，那么更新值。
3.   如果垃圾标记位为true并且size超出容量，那么就运行gc方法，再重新二分搜索，返回新的下标。
4.   如果新的size小于数组长度，则不扩容，反之2倍扩容。然后根据最新的下标，将kv插入到相应的位置。

# 移除（remove方法）

根据key，二分搜索找到下标i。如果有这个key的话（i>=0）

```java
if (i >= 0) {
    if (mValues[i] != DELETED) {
        mValues[i] = DELETED;
        mGarbage = true;
    }
}
```

将其标记为DELETED，并将mGarbage设置为true。

# 删除（gc方法）

如果在放入的时候，mGarbage标记位为true并且size大于等于数组的长度，那么进行垃圾删除。

```java
private void gc() {
    int n = mSize;
    int o = 0;
    int[] keys = mKeys;
    Object[] values = mValues;

    for (int i = 0; i < n; i++) {
        Object val = values[i];

        if (val != DELETED) {
            if (i != o) {
                keys[o] = keys[i];
                values[o] = val;
                values[i] = null;
            }

            o++;
        }
    }
    mGarbage = false;
    mSize = o;
}
```

就是把非DELETED的往前移。很简单。

