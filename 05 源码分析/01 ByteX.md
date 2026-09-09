官方介绍：https://github.com/bytedance/ByteX/blob/master/README_zh.md

# 宿主的实现

宿主：base-plugin

```java
public class ByteXPlugin implements Plugin<Project> {
    @Override
    public void apply(@NotNull Project project) {
        AppExtension android = project.getExtensions().getByType(AppExtension.class);
        ByteXExtension extension = project.getExtensions().create("ByteX", ByteXExtension.class);
        android.registerTransform(new ByteXTransform(new Context(project, android, extension)));
    }
}
```

会在当前的project创建一个ByteXExtension，其它插件apply的时候会获取此ByteXExtension，并实现注册。

```java
try {
    ByteXExtension byteX = project.getExtensions().getByType(ByteXExtension.class);
    byteX.registerPlugin(this);
    isRunningAlone = false;
} catch (UnknownDomainObjectException e) {
    android.registerTransform(getTransform());
    isRunningAlone = true;
}
```

