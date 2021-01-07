# 流

## Java7自动关闭流的研究

Java的IO流一般需要在finaly中进行关闭，Java7之后将流的初始化放在try后面的括号中，它会自动关闭。

```java
private static void testIO() {
    try (InputStream in = new FileInputStream("test.txt")) {
        byte[] bytes = new byte[20];
        int len = in.read(bytes);
        String str = new String(bytes, 0, len);
        System.out.println(str);
    } catch (IOException e) {
        e.printStackTrace();
    }
}
```

原理其实是在编译的时候自动加了close。下面是编译之后，反编译的结果：

```java
private static void testIO() {
    try {
        InputStream in = new FileInputStream("test.txt");
        Throwable var1 = null;

        try {
            byte[] bytes = new byte[20];
            int len = in.read(bytes);
            String str = new String(bytes, 0, len);
            System.out.println(str);
        } catch (Throwable var13) {
            var1 = var13;
            throw var13;
        } finally {
            if (in != null) {
                if (var1 != null) {
                    try {
                        in.close();
                    } catch (Throwable var12) {
                        var1.addSuppressed(var12);
                    }
                } else {
                    in.close();
                }
            }

        }
    } catch (IOException var15) {
        var15.printStackTrace();
    }

}
```

可以看到外部加了一个try-catch，对性能会有影响，实际的执行时间：

```
abc
用时：780861ns//Java7写法
abc
用时：65381ns//普通的写法
```

## BufferedxxxStream

流的每次读写（IO）是耗时的，BufferedxxxStream一次性读写到内存，不用频繁的IO操作

# 