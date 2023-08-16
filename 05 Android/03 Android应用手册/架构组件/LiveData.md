# 介绍

LiveData 是一种可观察的数据存储器类。与常规的可观察类不同，LiveData 具有生命周期感知能力，意指它遵循其他应用组件（如 activity、fragment 或 service）的生命周期。这种感知能力可确保 LiveData 仅更新处于活跃生命周期状态的应用组件观察者。

# 生命周期感知能力

生命周期感知能力是通过LifecycleOwner来实现的。

```
currentName.observe(this, nameObserver)	// this是Activity
```

# 观察者

观察者是通过传入一个Observer接口对象。

```
val nameObserver = Observer<String> {
    Log.i(TAG, "Observer onChanged")
    tvLog.text = it
}

// 在传递 nameObserver 参数的情况下调用 observe() 后，系统会立即调用 onChanged()，
// 从而提供 currentName 中存储的最新值。
// 如果 LiveData 对象尚未在 currentName 中设置值，则不会调用 onChanged()。
currentName.observe(this, nameObserver)
```