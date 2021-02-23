Navigation的主要元素：

1. Navigation Graph
    这是一种新型的XML资源文件，其中包含应用程序所有的页面，以及页面间的关系。
2. NavHostFragment
    这是一个特殊的Fragment, 你可以认为它是其他 Fragment的“容器”，Navigation Graph 中的Fragment正是通过NavHostFragment进行展示的。
3. NavController
    这是一个Java/Kotlin对象，用于在代码中完成NavigationGraph中具体的页面切换工作。

当想切换Fragment时，使用NavController对象，告诉它想要去Navigation Graph中的哪个Fragment，NavController会将想去的Fragment展示在NavHostFragment中。