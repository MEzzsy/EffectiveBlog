# ThreadLocal

>   具体见源码分析

1.   当某些数据是以线程为作用域且在不同线程具有不同的数据副本时，就可以考虑使用ThreadLocal（比如Looper）。
2.   一个ThreadLocal对象对应一个线程本地变量。
3.   一个线程对应一个ThreadLocalMap，ThreadLocalMap里有个数组table存放Entry类型的对象。
4.   Entry本身是ThreadLocal的弱引用，一个Entry对应一个ThreadLocal和一个value。用弱引用是因为，有些线程是长时间存在的（如主线程），如果使用强引用，可能会导致内存泄露。
5.   ThreadLocal的set方法放入需要的值，先获取Thread，再取出这个Thread的ThreadLocalMap。
     先根据ThreadLocal的hash值和table数组长度获取数组位置。
     如果产生hash冲突，解决办法是位置+1，如果超出了数组长度就放在0位置。
     找到合适的位置后，放入数组中。
     如果超出阈值就扩容。扩容是容量*2。
6.   ThreadLocal的get方法：
     先获取Thread，再取出这个Thread的ThreadLocalMap，然后根据此ThreadLocal取出值。
7.   ThreadLocalMap的初始化是懒加载，table的初始大小是16。
