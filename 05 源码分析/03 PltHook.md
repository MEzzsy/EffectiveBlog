# 代码

libtest-hook.so的代码：

```c++
#include "TestHook.h"

namespace mezzsy {

void testHook(int &out) {
  int *i = new int(123);
  out = *i;
  delete i;
}

}  // namespace mezzsy
```

# ELF

## 概述

ELF（Executable and Linkable Format）是一种行业标准的二进制数据封装格式，主要用于封装可执行文件、动态库、object 文件和 core dumps 文件。

其中最重要的部分是：ELF 文件头、SHT（section header table）、PHT（program header table）。

## ELF 文件头

ELF 文件的起始处，有一个固定格式的定长的文件头（32 位架构为 52 字节，64 位架构为 64 字节）。ELF 文件头以 magic number `0x7F 0x45 0x4C 0x46` 开始（其中后 3 个字节分别对应可见字符 `E` `L` `F`）。

```
libtest-hook.so 的 ELF 文件头信息：

> readelf64 -h libtest-hook.so 
ELF Header:
  Magic:   7f 45 4c 46 02 01 01 00 00 00 00 00 00 00 00 00 
  Class:                             ELF64
  Data:                              2's complement, little endian
  Version:                           1 (current)
  OS/ABI:                            UNIX - System V
  ABI Version:                       0
  Type:                              DYN (Shared object file)
  Machine:                           AArch64
  Version:                           0x1
  Entry point address:               0xcfa0
  Start of program headers:          64 (bytes into file)
  Start of section headers:          1227280 (bytes into file)
  Flags:                             0x0
  Size of this header:               64 (bytes)
  Size of program headers:           56 (bytes)
  Number of program headers:         8
  Size of section headers:           64 (bytes)
  Number of section headers:         35
  Section header string table index: 32
```

ELF 文件头中包含了 SHT 和 PHT 在当前 ELF 文件中的起始位置和长度。

例如，libtest-hook.so 的 SHT 起始位置为 1227280，长度 64 字节；PHT 起始位置为 64，长度 56 字节。

## SHT（section header table）

ELF 以 section 为单位来组织和管理各种信息。ELF 使用 SHT 来记录所有 section 的基本信息。主要包括：section 的类型、在文件中的偏移量、大小、加载到内存后的虚拟内存相对地址、内存中字节的对齐方式等。

```
libtest-hook.so 的 SHT：

> readelf64 -S libtest-hook.so
There are 35 section headers, starting at offset 0x12ba10:

Section Headers:
  [Nr] Name              Type             Address           Offset
       Size              EntSize          Flags  Link  Info  Align
  [ 0]                   NULL             0000000000000000  00000000
       0000000000000000  0000000000000000           0     0     0
  [ 1] .note.gnu.build-i NOTE             0000000000000200  00000200
       0000000000000024  0000000000000000   A       0     0     4
  [ 2] .hash             HASH             0000000000000228  00000228
       0000000000000988  0000000000000004   A       4     0     8
  [ 3] .gnu.hash         GNU_HASH         0000000000000bb0  00000bb0
       00000000000009f8  0000000000000000   A       4     0     8
  [ 4] .dynsym           DYNSYM           00000000000015a8  000015a8
       0000000000002058  0000000000000018   A       5     3     8
  [ 5] .dynstr           STRTAB           0000000000003600  00003600
       00000000000015f0  0000000000000000   A       0     0     1
  [ 6] .gnu.version      VERSYM           0000000000004bf0  00004bf0
       00000000000002b2  0000000000000002   A       4     0     2
  [ 7] .gnu.version_r    VERNEED          0000000000004ea8  00004ea8
       0000000000000040  0000000000000000   A       5     2     8
  [ 8] .rela.dyn         RELA             0000000000004ee8  00004ee8
       0000000000007710  0000000000000018   A       4     0     8
  [ 9] .rela.plt         RELA             000000000000c5f8  0000c5f8
       00000000000005b8  0000000000000018  AI       4    20     8
  [10] .plt              PROGBITS         000000000000cbb0  0000cbb0
       00000000000003f0  0000000000000010  AX       0     0     16
  [11] .text             PROGBITS         000000000000cfa0  0000cfa0
       0000000000017f68  0000000000000000  AX       0     0     4
  [12] .rodata           PROGBITS         0000000000024f08  00024f08
       0000000000002499  0000000000000000   A       0     0     8
  [13] .eh_frame_hdr     PROGBITS         00000000000273a4  000273a4
       0000000000000cfc  0000000000000000   A       0     0     4
  [14] .eh_frame         PROGBITS         00000000000280a0  000280a0
       00000000000038e8  0000000000000000   A       0     0     8
  [15] .gcc_except_table PROGBITS         000000000002b988  0002b988
       000000000000039c  0000000000000000   A       0     0     4
  [16] .note.android.ide NOTE             000000000002bd24  0002bd24
       0000000000000098  0000000000000000   A       0     0     4
  [17] .fini_array       FINI_ARRAY       000000000002d048  0002c048
       0000000000000010  0000000000000008  WA       0     0     8
  [18] .data.rel.ro      PROGBITS         000000000002d058  0002c058
       0000000000002b08  0000000000000000  WA       0     0     8
  [19] .dynamic          DYNAMIC          000000000002fb60  0002eb60
       00000000000001e0  0000000000000010  WA       5     0     8
  [20] .got              PROGBITS         000000000002fd40  0002ed40
       00000000000002c0  0000000000000008  WA       0     0     8
  [21] .data             PROGBITS         0000000000030000  0002f000
       0000000000000028  0000000000000000  WA       0     0     8
  [22] .bss              NOBITS           0000000000030030  0002f028
       0000000000000480  0000000000000000  WA       0     0     16
  [23] .comment          PROGBITS         0000000000000000  0002f028
       00000000000000dc  0000000000000001  MS       0     0     1
  [24] .debug_aranges    PROGBITS         0000000000000000  0002f104
       0000000000000060  0000000000000000           0     0     1
  [25] .debug_info       PROGBITS         0000000000000000  0002f164
       0000000000044ce4  0000000000000000           0     0     1
  [26] .debug_abbrev     PROGBITS         0000000000000000  00073e48
       0000000000003308  0000000000000000           0     0     1
  [27] .debug_line       PROGBITS         0000000000000000  00077150
       0000000000017a5f  0000000000000000           0     0     1
  [28] .debug_str        PROGBITS         0000000000000000  0008ebaf
       00000000000213a7  0000000000000001  MS       0     0     1
  [29] .debug_loc        PROGBITS         0000000000000000  000aff56
       000000000004b13f  0000000000000000           0     0     1
  [30] .debug_macinfo    PROGBITS         0000000000000000  000fb095
       000000000000000e  0000000000000000           0     0     1
  [31] .debug_ranges     PROGBITS         0000000000000000  000fb0a3
       0000000000019870  0000000000000000           0     0     1
  [32] .shstrtab         STRTAB           0000000000000000  0012b8a5
       0000000000000167  0000000000000000           0     0     1
  [33] .symtab           SYMTAB           0000000000000000  00114918
       000000000000b8e0  0000000000000018          34   1630     8
  [34] .strtab           STRTAB           0000000000000000  001201f8
       000000000000b6ad  0000000000000000           0     0     1
```

比较重要，且和 hook 关系比较大的几个 section 是：

- `.dynstr`：保存了所有的字符串常量信息。
- `.dynsym`：保存了符号（symbol）的信息（符号的类型、起始地址、大小、符号名称在 `.dynstr` 中的索引编号等）。函数也是一种符号。
- `.text`：程序代码经过编译后生成的机器指令。
- `.dynamic`：供动态链接器使用的各项信息，记录了当前 ELF 的外部依赖，以及其他各个重要 section 的起始位置等信息。
- `.got`：Global Offset Table。用于记录外部调用的入口地址。动态链接器（linker）执行重定位（relocate）操作时，这里会被填入真实的外部调用的绝对地址。
- `.plt`：Procedure Linkage Table。外部调用的跳板，主要用于支持 lazy binding 方式的外部调用重定位。（Android 目前只有 MIPS 架构支持 lazy binding）
- `.rel.plt`：对外部函数直接调用的重定位信息。
- `.rel.dyn`：除 `.rel.plt` 以外的重定位信息。（比如通过全局函数指针来调用外部函数）

## PHT（program header table）

ELF 被加载到内存时，是以 segment 为单位的。一个 segment 包含了一个或多个 section。ELF 使用 PHT 来记录所有 segment 的基本信息。主要包括：segment 的类型、在文件中的偏移量、大小、加载到内存后的虚拟内存相对地址、内存中字节的对齐方式等。

```
libtest-hook.so 的 PHT：
> readelf64 -l libtest-hook.so

Elf file type is DYN (Shared object file)
Entry point 0xcfa0
There are 8 program headers, starting at offset 64

Program Headers:
  Type           Offset             VirtAddr           PhysAddr
                 FileSiz            MemSiz              Flags  Align
  LOAD           0x0000000000000000 0x0000000000000000 0x0000000000000000
                 0x000000000002bdbc 0x000000000002bdbc  R E    1000
  LOAD           0x000000000002c048 0x000000000002d048 0x000000000002d048
                 0x0000000000002fe0 0x0000000000003468  RW     1000
  DYNAMIC        0x000000000002eb60 0x000000000002fb60 0x000000000002fb60
                 0x00000000000001e0 0x00000000000001e0  RW     8
  NOTE           0x0000000000000200 0x0000000000000200 0x0000000000000200
                 0x0000000000000024 0x0000000000000024  R      4
  NOTE           0x000000000002bd24 0x000000000002bd24 0x000000000002bd24
                 0x0000000000000098 0x0000000000000098  R      4
  GNU_EH_FRAME   0x00000000000273a4 0x00000000000273a4 0x00000000000273a4
                 0x0000000000000cfc 0x0000000000000cfc  R      4
  GNU_STACK      0x0000000000000000 0x0000000000000000 0x0000000000000000
                 0x0000000000000000 0x0000000000000000  RW     10
  GNU_RELRO      0x000000000002c048 0x000000000002d048 0x000000000002d048
                 0x0000000000002fb8 0x0000000000002fb8  R      1

 Section to Segment mapping:
  Segment Sections...
   00     .note.gnu.build-id .hash .gnu.hash .dynsym .dynstr .gnu.version .gnu.version_r .rela.dyn .rela.plt .plt .text .rodata .eh_frame_hdr .eh_frame .gcc_except_table .note.android.ident 
   01     .fini_array .data.rel.ro .dynamic .got .data .bss 
   02     .dynamic 
   03     .note.gnu.build-id 
   04     .note.android.ident 
   05     .eh_frame_hdr 
   06     
   07     .fini_array .data.rel.ro .dynamic .got 
```

所有类型为 `PT_LOAD` 的 segment 都会被动态链接器（linker）映射（mmap）到内存中。

## 连接视图（Linking View）和执行视图（Execution View）

- 连接视图：ELF 未被加载到内存执行前，以 section 为单位的数据组织形式。
- 执行视图：ELF 被加载到内存后，以 segment 为单位的数据组织形式。

hook 操作，属于动态形式的内存操作，因此主要关心的是执行视图，即 ELF 被加载到内存后，ELF 中的数据是如何组织和存放的。

## .dynamic section

这是一个十分重要和特殊的 section，其中包含了 ELF 中其他各个 section 的内存位置等信息。在执行视图中，总是会存在一个类型为 `PT_DYNAMIC` 的 segment，这个 segment 就包含了 .dynamic section 的内容。

无论是执行 hook 操作时，还是动态链接器执行动态链接时，都需要通过 `PT_DYNAMIC` segment 来找到 .dynamic section 的内存位置，再进一步读取其他各项 section 的信息。

libtest-hook.so 的 .dynamic section：

```
> readelf64 -d libtest-hook.so

Dynamic section at offset 0x2eb60 contains 26 entries:
  Tag        Type                         Name/Value
 0x0000000000000001 (NEEDED)             Shared library: [libm.so]
 0x0000000000000001 (NEEDED)             Shared library: [libdl.so]
 0x0000000000000001 (NEEDED)             Shared library: [libc.so]
 0x000000000000000e (SONAME)             Library soname: [libtest-hook.so]
 0x000000000000001a (FINI_ARRAY)         0x2d048
 0x000000000000001c (FINI_ARRAYSZ)       16 (bytes)
 0x0000000000000004 (HASH)               0x228
 0x000000006ffffef5 (GNU_HASH)           0xbb0
 0x0000000000000005 (STRTAB)             0x3600
 0x0000000000000006 (SYMTAB)             0x15a8
 0x000000000000000a (STRSZ)              5616 (bytes)
 0x000000000000000b (SYMENT)             24 (bytes)
 0x0000000000000003 (PLTGOT)             0x2fd40
 0x0000000000000002 (PLTRELSZ)           1464 (bytes)
 0x0000000000000014 (PLTREL)             RELA
 0x0000000000000017 (JMPREL)             0xc5f8
 0x0000000000000007 (RELA)               0x4ee8
 0x0000000000000008 (RELASZ)             30480 (bytes)
 0x0000000000000009 (RELAENT)            24 (bytes)
 0x000000000000001e (FLAGS)              BIND_NOW
 0x000000006ffffffb (FLAGS_1)            Flags: NOW
 0x000000006ffffffe (VERNEED)            0x4ea8
 0x000000006fffffff (VERNEEDNUM)         2
 0x000000006ffffff0 (VERSYM)             0x4bf0
 0x000000006ffffff9 (RELACOUNT)          886
 0x0000000000000000 (NULL)               0x0
```

# 动态链接器（linker）

安卓中的动态链接器程序是 linker。动态链接（比如执行 dlopen）的大致步骤是：

1. 检查已加载的 ELF 列表。（如果 libtest-hook.so 已经加载，就不再重复加载了，仅把 libtest-hook.so 的引用计数加一，然后直接返回。）

2. 从 libtest-hook.so 的 .dynamic section 中读取 libtest-hook.so 的外部依赖的 ELF 列表，从此列表中剔除已加载的 ELF，最后得到本次需要加载的 ELF 完整列表（包括 libtest-hook.so 自身）。

3. 逐个加载列表中的 ELF。加载步骤：

   - 用 mmap 预留一块足够大的内存，用于后续映射 ELF。（MAP_PRIVATE 方式）

   - 读 ELF 的 PHT，用 mmap 把所有类型为 PT_LOAD 的 segment 依次映射到内存中。

   - 从 .dynamic segment 中读取各信息项，主要是各个 section 的虚拟内存相对地址，然后计算并保存各个 section 的虚拟内存绝对地址。

   - 执行重定位操作（relocate），这是最关键的一步。重定位信息可能存在于下面的一个或多个 secion 中：.rel.plt, .rela.plt, .rel.dyn, .rela.dyn, .rel.android, .rela.android。动态链接器需要逐个处理这些 .relxxx section 中的重定位诉求。根据已加载的 ELF 的信息，动态链接器查找所需符号的地址（比如 libtest-hook.so 的符号 malloc），找到后，将地址值填入 .relxxx 中指明的目标地址中，这些“目标地址”一般存在于.got 或 .data 中。

   - ELF 的引用计数加一。

4. 逐个调用列表中 ELF 的构造函数（constructor），这些构造函数的地址是之前从 .dynamic segment 中读取到的（类型为 DT_INIT 和 DT_INIT_ARRAY）。各 ELF 的构造函数是按照依赖关系逐层调用的，先调用被依赖 ELF 的构造函数，最后调用 libtest-hook.so 自己的构造函数。（ELF 也可以定义自己的析构函数（destructor），在 ELF 被 unload 的时候会被自动调用）
     等一下！我们似乎发现了什么！再看一遍重定位操作（relocate）的部分。难道我们只要从这些 .relxxx 中获取到“目标地址”，然后在“目标地址”中重新填上一个新的函数地址，这样就完成 hook 了吗？也许吧。

# Hook

看一下 `.rel.plt`：

```
readelf64 -r libtest-hook.so

Relocation section '.rela.plt' at offset 0xc5f8 contains 61 entries:
  Offset          Info           Type           Sym. Value    Sym. Name + Addend
00000002fef8  001f00000402 R_AARCH64_JUMP_SL 0000000000000000 malloc@LIBC + 0
```

`malloc` 的地址存放在 `2fef8` 里，但是不能直接用这个地址：

1. `2fef8` 是个相对内存地址，需要把它换算成绝对地址。
2. `2fef8` 对应的绝对地址很可能没有写入权限，直接对这个地址赋值会引起段错误。
3. 新的函数地址即使赋值成功了，`my_malloc` 也不会被执行，因为处理器有指令缓存（instruction cache）。

## 计算绝对地址

### 获取基地址

在进程的内存空间中，各种 ELF 的加载地址是随机的，只有在运行时才能拿到加载地址，也就是基地址。调用 `dl_iterate_phdr`来获取基地址。

### 内存访问权限

如果要执行 hook，就需要写入的权限，可以使用 `mprotect` 来完成：

```
#include <sys/mman.h>
int mprotect(void *addr, size_t len, int prot);
```

注意修改内存访问权限时，只能以“页”为单位。`mprotect` 的详细说明见 [这里](http://man7.org/linux/man-pages/man2/mprotect.2.html)。

### 指令缓存

注意 `.got` 和 `.data` 的 section 类型是 `PROGBITS`，也就是执行代码。处理器可能会对这部分数据做缓存。修改内存地址后，需要清除处理器的指令缓存，让处理器重新从内存中读取这部分指令。方法是调用 `__builtin___clear_cache`：

```
void __builtin___clear_cache (char *begin, char *end);
```

注意清除指令缓存时，也只能以“页”为单位。`__builtin___clear_cache` 的详细说明见 [这里](https://gcc.gnu.org/onlinedocs/gcc/Other-Builtins.html)。

## 完整代码

```c++
void testPltHook() {
#ifdef ANDROID
  SY_LOG("hook前：");
  int i;
  testHook(i);
  SY_LOG("testPltHook i=%d", i);

  pltHookMalloc();

  SY_LOG("hook后：");
  testHook(i);
  SY_LOG("testPltHook i=%d", i);

#endif
}

#define PAGE_START(addr) ((addr) & PAGE_MASK)
#define PAGE_END(addr) (PAGE_START(addr) + PAGE_SIZE)

static void * my_malloc(size_t size) {
  SY_LOG("my_malloc size=%zu", size);
  return malloc(size);
}

static int LoadedSoCallback(dl_phdr_info *info, size_t size, void *data) {
  std::string so_name = info->dlpi_name;
  if (ends_with(so_name, "libtest-hook.so")) {
    SY_LOG("找到libtest-hook.so address=%llu", info->dlpi_addr);
    // 获取绝对地址
    uintptr_t base_addr = info->dlpi_addr;
    uintptr_t address = base_addr + 0x2fef8;
    // 赋予读写权限
    // #include <sys/mman.h>
    mprotect((void *)PAGE_START(address), PAGE_SIZE, PROT_READ | PROT_WRITE);
    // 替换地址
    *(void **)address = (void *)my_malloc;
    // 清除指令缓存
    __builtin___clear_cache((char *) PAGE_START(address), (char *) PAGE_END(address));
  }
  return 0;
}

void pltHookMalloc() {
  SY_LOG("开始plt hook");
  // #include <link.h>
  dl_iterate_phdr(LoadedSoCallback, nullptr);
}
```

```
2023-07-31 11:40:50.400 28194-28194/com.mezzsy.myapplication I/NDK_DEMO: hook前：
2023-07-31 11:40:50.401 28194-28194/com.mezzsy.myapplication I/NDK_DEMO: testPltHook i=123
2023-07-31 11:40:50.401 28194-28194/com.mezzsy.myapplication I/NDK_DEMO: 开始plt hook
2023-07-31 11:40:50.401 28194-28194/com.mezzsy.myapplication I/NDK_DEMO: 找到libtest-hook.so address=522285015040
2023-07-31 11:40:50.401 28194-28194/com.mezzsy.myapplication I/NDK_DEMO: my_malloc size=128
2023-07-31 11:40:50.401 28194-28194/com.mezzsy.myapplication I/NDK_DEMO: hook后：
2023-07-31 11:40:50.401 28194-28194/com.mezzsy.myapplication I/NDK_DEMO: my_malloc size=4
2023-07-31 11:40:50.401 28194-28194/com.mezzsy.myapplication I/NDK_DEMO: testPltHook i=123
```

# PLT和GOT

编译器在生成so时并不知道malloc的绝对内存地址，而运行时无法修改代码段 (so是共享库，如果修改了代码段，就无法做到所有进程共享一个so文件），只能将malloc重定位到数据段。同时生成一小段代码，这部分代码调用真实的malloc函数，调用malloc的地方替换为调用这一小段代码。ELF使用GOT和PLT辅助执行运行时重定位。

PLT主要用于外部调用重定位，它只是一个跳板，帮助跳到正确的符号地址。（这种技术称之为“蹦床”）。

PLT跳到了GOT。 GOT (Global Offset Table)记录了外部调用的绝对地址。在动态链接器执行重定位操作时，GOT会被填入真实的外部调用的绝对地址（汇编中的GOT并没有实际意义）。

## 问题1

既然GOT记录了绝对内存地址，那么为什么函数不直接跳转到GOT，而是多一步PLT？

程序运行过程中，可能很多函数在程序执行完时都不会被用到，所以ELF采用了延迟绑定(Lazy Binding)的做法。即：当函数第一次被用到时才进行绑定，如果没有用到则不进行鄉定。PLT就是为了实现延迟绑定。

参考：https://blog.csdn.net/u014377094/article/details/124391914

首次调用：

1. 调用plt相对应项 
2. 进入got后又跳转回到plt表 
3. 跳转到plt表首项 
4. 调用_dl_runtime_resolve，got表对应项刷新 
5. 完成调用

后续调用：

1. 调用plt相对应项 
2. 获得got表对应项 
3. 完成调用

## 问题2

在Android的动态链接过程中提到了会将函数地址填入到GOT中，这不是和延迟鄉定矛盾了？

Android的动态链接器采用的不是linux中的链接器，而是Android自带的linker。linker并没有使用延时绑定的技巧，而是在装载时将所有引用的函数地址都解析出来了。

因为Android的所有用户进程都是fork出来的，在zygote进程中将所有地址都解析出来后，fork出的子进程就可以直接使用了，如果再延时绑定反而更浪费时间。

另外PLT的实现方式也有区别：Linux平台下PLT的做法是第一次绑定，后续直接调用；而Android的PLT是直接跳到GOT。

# 总结

函数调用malloc，由于编译时malloc内存地址不可知，所以需要一个跳板（PLT) 去寻找真实的地址 (GOT)，真实的地址在so被加载时写入。

```
(test函数调用malloc) -> (指令跳到PLT表中) -> (运行时，malloc的真实地址记录在GOT表中)
```

