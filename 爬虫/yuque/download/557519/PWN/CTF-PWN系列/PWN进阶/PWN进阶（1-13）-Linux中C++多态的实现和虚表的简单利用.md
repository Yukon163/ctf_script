> 附件：
>
> 链接: [https://pan.baidu.com/s/14C5Q8sPDYbR5EwZEdyUPQA](https://pan.baidu.com/s/14C5Q8sPDYbR5EwZEdyUPQA) 提取码: scer
>

# 前言
之前没有学好C++，现在我来恶补基础知识了，顺带会从内存和汇编的角度分析C++多态的实现。

# 源码及编译
这篇文章当中所使用的源码如下：

> 源码来自菜鸟教程：[https://www.runoob.com/cplusplus/cpp-polymorphism.html](https://www.runoob.com/cplusplus/cpp-polymorphism.html)
>

```cpp
#include <iostream> 
using namespace std;
 
class Shape {
   protected:
      int width, height;
   public:
      Shape( int a=0, int b=0){     
         width = a;                 
         height = b;
      }
      int area() {
         cout << "Parent class area :" <<endl;
         return 0;
      }
};
class Rectangle: public Shape{   
   public:
      Rectangle( int a=0, int b=0):Shape(a, b) { }   
      int area (){ 
         cout << "Rectangle class area :" <<endl;
         return (width * height); 
      }
};
class Triangle: public Shape{     
   public:
      Triangle( int a=0, int b=0):Shape(a, b) { }   
      int area (){ 
         cout << "Triangle class area :" <<endl;
         return (width * height / 2); 
      }
};
int main( ){
   Shape *shape;  
   Rectangle rec(10,7); 
   Triangle  tri(10,5);
   shape = &rec;   
   shape->area(); 
   shape = &tri;   
   shape->area(); 
   return 0;
}
```

我们将上述源码进行编译：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637196506043-06c34e52-54de-468d-b90e-d64d7034e0b6.png)

# 源码分析
## C++的类与对象
下面的例子是通过类来计算长方形和三角形的面积。

> Rectangle长方形，Triangle三角形。
>

为了能顺利的看懂上面的代码，这里先拿上面代码的Shape类来说明：

```cpp
class Shape {
   protected:
      int width, height;
   public:
      Shape( int a=0, int b=0){     
         width = a;                 
         height = b;
      }
      int area() {
         cout << "Parent class area :" <<endl;
         return 0;
      }
};
```

在C++中可以使用关键字class来定义一个类，这个类中可以具有多个成员（如函数、变量等）。但是有的时候我们并不想在类之外的地方访问类内的某些数据，所以C++提供了一种叫“数据封装”的方式来避免受到外界的干扰和误用。可以使用public、protected、private这三个类访问修饰符对其中的成员赋予不同的访问权限，默认情况下成员在类中的定义都是private的。

> 具体请参考：[https://www.runoob.com/cplusplus/cpp-class-access-modifiers.html](https://www.runoob.com/cplusplus/cpp-class-access-modifiers.html)
>

类中可以有许多的函数，但是假如我想在实例化对象时直接向类中传参？C++提供了“构造函数”来满足这个要求。

构造函数说白了就是其名称与类名称完全相同的函数，并且此种函数不会返回任何类型（包括void），构造函数可用于为某些成员变量设初始值。

> 更详细的内容可以到：[https://www.runoob.com/cplusplus/cpp-constructor-destructor.html](https://www.runoob.com/cplusplus/cpp-constructor-destructor.html)
>

现在回到上面的代码：

+ 第2行到第3行：定义了两个protected成员变量width和height，这意味着我们只能通过类本身和其派生类（子类）进行访问。
+ 第4行到第8行：定义了构造函数Shape，当每次创建一个新的类对象即实例化时会自动调用此函数。
+ 第9行到第12行：定义了public的成员函数area，可以在类外对其进行访问。

> 构造函数也可以是私有“private”的。
>

接下来定义了两个公有继承自类Shape的类--Rectangle和Triangle，由于这两者的类结构近乎相同这里只对Rectangle类进行说明：

```cpp
class Rectangle: public Shape{    //公有继承
   public:
      Rectangle( int a=0, int b=0):Shape(a, b) { }   //public
      int area (){ 
         cout << "Rectangle class area :" <<endl;
         return (width * height); 
      }
};

#shape类
class Shape {
   protected:
      int width, height;          //protected：可以通过其子类进行访问
   public:         
      Shape( int a=0, int b=0){   //public
         width = a;                 
         height = b;
      }
      int area() {
         cout << "Parent class area :" <<endl;
         return 0;
      }
};
```

具体的继承规则如下：

+ public 继承：基类 public 成员，protected 成员，private 成员的访问属性在派生类中分别变成：public, protected, private
+ protected 继承：基类 public 成员，protected 成员，private 成员的访问属性在派生类中分别变成：protected, protected, private
+ private 继承：基类 public 成员，protected 成员，private 成员的访问属性在派生类中分别变成：private, private, private	

因为Rectangle是公有继承自Shape，所以继承后前者的成员访问权限并没有发生变化，另外在继承后Rectangle可以直接访问shape中的构造函数。当然其中还定义了一个area函数，可以看出这个函数的目的是重写基类（父类）中的area，但是这种写法真的正确吗？先来看一下程序的运行结果：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637201924434-cdca380f-0530-4bee-9c61-57b851b31a86.png)

可以看到，在Rectangle类中并没有调用自己的area方法而是调用了父类，这并不符合我们的期待：

```cpp
// 程序的主函数
int main( ){
   Shape *shape;        //指向类Shape的指针
   Rectangle rec(10,7); //实例化类
   Triangle  tri(10,5);
   shape = &rec;        // 获取rec对象的地址
   shape->area();  		// 调用Rectangle的方法area->求矩形的面积
   shape = &tri;   		// 获取tri对象的地址
   shape->area();  		// 调用Triangle的方法area->求三角形的面积
   return 0;
}
```

在IDA中直接看一下调用过程中的汇编指令：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637205849406-f15949e3-3cc6-4bac-ac59-672c8eb31125.png)

在调用成员函数时用到了this指针：[https://www.runoob.com/cplusplus/cpp-this-pointer.html](https://www.runoob.com/cplusplus/cpp-this-pointer.html)；举一个例子就懂了：

```cpp
#include <iostream>
using namespace std;
class Box{
   public:
      Box(double l=2.0, double b=2.0, double h=2.0){  //构造函数
         cout <<"Constructor called." << endl;
         length = l;
         breadth = b;
         height = h;
      }
      double Volume(){
         return length * breadth * height;
      }
      int compare(Box box){
         return this->Volume() > box.Volume(); //注意这里
      }
   private:
      double length;     // Length of a box
      double breadth;    // Breadth of a box
      double height;     // Height of a box
};

int main(void){
   Box Box1(3.3, 1.2, 1.5);    // 实例化对象
   Box Box2(8.5, 6.0, 2.0);   
   if(Box1.compare(Box2)){
      cout << "Box2 is smaller than Box1" <<endl;
   }
   else{
      cout << "Box2 is equal to or larger than Box1" <<endl;
   }
   return 0;
}
```

整个main函数的调用链过程如下：

1. 自动调用class Box中的构造方法，现在Box1的length，breadth，height分别为3.3、1.2、1.5，Box2相同
2. 调用Box1的compare方法，这个成员函数的参数为对象Box2。
    1. 调用this->Volume()，也就是调用Box1的Volume方法。
    2. 调用Box2.Volume()
3. 将这两个Volume方法的结果进行比较并返回。

**所以在C++的每一个对象都能通过this指针在类的内部调用本类的方法，this指针的具体实现会在稍后说明。**回到IDA中，main函数的伪代码如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637206459291-09a986d0-e4ba-4a5f-b611-cc69e9f8ca6a.png)

进入Shape::area(&rec.0)【源码中的shape->area()】，查看该函数的伪代码：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637203001241-485dfec8-556a-4130-ad24-eec2870888d7.png)

可以看到在程序编译时并没有将两个子类的area方法编译到可执行文件中：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637307068145-425c7565-3636-4ec1-a8ef-8397ac784bf7.png)

要想解决这个问题需要了解一下C++的虚函数。

## C++多态的实现--虚函数
C++的多态的实现和虚函数密不可分：假如我们在基类的函数之前加上virtual关键字并在派生类中重写该函数，运行时就会根据对象的实际类型来调用相应的函数。如果对象类型是派生类，就调用派生类的函数；如果对象类型是基类，就调用基类的函数。根据定义，我们将之前的代码稍微改动一下：

```cpp
class Shape {
   protected:
      int width, height;
   public:
      Shape( int a=0, int b=0){    
         width = a;               
         height = b;
      }
      virtual int area() {  //对需要在子类中需要重写的函数加入virtual关键字
         cout << "Parent class area :" <<endl;
         return 0;
      }
};
```

> 编译命令：g++ -g C_plus_plus_2.cpp -o C_plus_plus_2
>

再次运行一下程序：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637218083827-39bbe19b-9552-4d0f-ac41-8ef5a319dc99.png)

可以看到，现在程序的运行结果就符合我们预期了，但是具体是怎么实现的？在gdb中对main函数下断点，然后run；并在IDA中查看main函数的伪代码：

> 记得关闭系统的ALSR：echo 0 > /proc/sys/kernel/randomize_va_space
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637219564172-65c8c090-f402-4fdf-a149-08e365d7ad7c.png)

在gdb中进入Rectangle::Rectangle(&rec, 10, 7);也就是源码中的实例化对象：Rectangle rec(10,7);

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637219886627-5fd19c74-7d51-429f-bdfa-7a34f3ca3daf.png)

然后我们单步步入call 0x400a6e：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637220077657-878bf49c-4ecb-4082-92cb-c11e86340e54.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637220292777-a284dd05-3ebb-4de8-92ff-3144dcb2e1a7.png)

上图是执行Shape中的构造函数，有必要对这个函数进行调试。根据64位的函数传参规则，函数间参数的传递优先放入寄存器中，所以寄存器rdi、rsi、rdx存放的是当前传入Shape类的构造函数参数：

```cpp
Rectangle rec(10,7);  
# rsi==this指针
# rdi==10
# rdx==7
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637235525883-f7ee7ef3-f54a-47c8-8b48-2309683cc519.png)

直接来看IDA中的伪代码：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637237248633-14f04e76-a9c5-483e-bddf-5c30be3b54d2.png)

变量_vptr_Shape很明显是Vtable Pointer（虚函数表指针）的缩写，所以0x400CC8处存放的是基类Shape的虚表（vtable）：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637240137251-285d8bcd-1037-4571-83a3-f758d4aad9a7.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637240203808-17976567-61f5-4f28-9cc8-11773080652d.png)

> 根据IDA中的注释，基类Shape的虚表应当是从地址0x400CB8处开始。但是为了严谨起见，我们将0x400CB8称为Shape虚表的起始地址，将地址0x400CD0称之为此虚表的结束地址。
>

根据IDA中显示的内容，可以模糊的得到虚表的数据结构：

+ 参数1：this指针所在类在类中的偏移量
+ 参数2：类的基本信息，也是一个指针
+ 参数3：_vptr_class_name指针【如：_vptr.Shape】，在本例子中指向基类Shape的虚函数area。![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637241901303-671310ee-349f-4a20-b7bf-bec35aa684bf.png)

另外可以看到与文章中的前一个例子不相同，一旦在类中定义了虚函数，程序编译后在rodata（read only data）段就会出现虚表，换而言之虚表信息**<font style="color:#F5222D;">不可修改</font>**。顺带浏览下其他的两个子类：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637243984096-d7129da8-9465-4e72-9194-78499b10fd9e.png)

来到Shape的构造函数中的ret指令，现在的this指针如下：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637245416116-2bd6fc15-fdf7-445c-8f25-c5bd77123c4d.png)

> 注意：上图中的this指针属于基类Shape。
>

返回到下图中所示的地方:

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637246769356-161895fa-dae3-4d26-9b74-791a86055e1e.png)

继续调试发现下面的指令全部都是恢复Rectangle类的this指针：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637281347994-cea313a7-1392-4995-ad49-e72bc73a92d8.png)

```cpp
06:0030│ rax rdi  0x7fffffffe200 —▸ 0x400cc8 —▸ 0x400aa0 (Shape::area()) ◂— push   rbp
执行过后：
06:0030│ rax rdi  0x7fffffffe200 —▸ 0x400cb0 —▸ 0x400b06 (Rectangle::area()) ◂— push   rbp
```

> 在调试过程中发现，基类Shape的this指针和子类Rectangle的this指针地址相同，编译器真会省空间...
>

**所以现在我们可以知道为什么网上的资料都说this指针是****<font style="color:#F5222D;">隐式的</font>****：它并不出现在源代码中，而是在编译阶段由编译器****<font style="color:#F5222D;">默默地</font>****将它添加到参数列表中。this指针的本质是成员函数中的局部变量，只能在成员函数的内部进行调用，并且只有在通过对象调用成员函数时才给 this 赋值。一旦某个class的成员函数调用完成，在函数返回后会立即恢复原有的this指针。**有关的汇编代码如下：

```cpp
.text:0000000000400AD0 ; void __cdecl Rectangle::Rectangle(Rectangle *const this, int a, int b)
.text:0000000000400AD0                 public _ZN9RectangleC2Eii ; weak
.text:0000000000400AD0 _ZN9RectangleC2Eii proc near            ; CODE XREF: main+28↑p
.text:0000000000400AD0
.text:0000000000400AD0 b               = dword ptr -10h
.text:0000000000400AD0 a               = dword ptr -0Ch
.text:0000000000400AD0 this            = qword ptr -8
.text:0000000000400AD0
.text:0000000000400AD0 ; __unwind {
.text:0000000000400AD0                 push    rbp
.text:0000000000400AD1                 mov     rbp, rsp
.text:0000000000400AD4                 sub     rsp, 10h
.text:0000000000400AD8                 mov     [rbp+this], rdi
.text:0000000000400ADC                 mov     [rbp+a], esi
.text:0000000000400ADF                 mov     [rbp+b], edx
.text:0000000000400AE2                 mov     rax, [rbp+this]
.text:0000000000400AE6                 mov     edx, [rbp+b]    ; b
.text:0000000000400AE9                 mov     ecx, [rbp+a]
.text:0000000000400AEC                 mov     esi, ecx        ; a
.text:0000000000400AEE                 mov     rdi, rax        ; this
.text:0000000000400AF1                 call    _ZN5ShapeC2Eii  ; Shape::Shape(int,int)
.text:0000000000400AF6                 mov     edx, offset off_400CB0 ; _ZN9Rectangle4areaEv--子类Rectangle中的area()
.text:0000000000400AFB                 mov     rax, [rbp+this]
.text:0000000000400AFF                 mov     [rax], rdx
.text:0000000000400B02                 nop
.text:0000000000400B03                 leave
.text:0000000000400B04                 retn
.text:0000000000400B04 ; } // starts at 400AD0
.text:0000000000400B04 _ZN9RectangleC2Eii endp


.text:0000000000400A6E ; void __cdecl Shape::Shape(Shape *const this, int a, int b)
.text:0000000000400A6E                 public _ZN5ShapeC2Eii ; weak
.text:0000000000400A6E _ZN5ShapeC2Eii  proc near               ; CODE XREF: Rectangle::Rectangle(int,int)+21↓p
.text:0000000000400A6E                                         ; Triangle::Triangle(int,int)+21↓p
.text:0000000000400A6E
.text:0000000000400A6E b               = dword ptr -10h
.text:0000000000400A6E a               = dword ptr -0Ch
.text:0000000000400A6E this            = qword ptr -8
.text:0000000000400A6E
.text:0000000000400A6E ; __unwind {
.text:0000000000400A6E                 push    rbp             ; Alternative name is 'Shape::Shape(int, int)'
.text:0000000000400A6F                 mov     rbp, rsp
.text:0000000000400A72                 mov     [rbp+this], rdi
.text:0000000000400A76                 mov     [rbp+a], esi
.text:0000000000400A79                 mov     [rbp+b], edx
.text:0000000000400A7C                 mov     edx, offset off_400CC8 ; _ZN5Shape4areaEv--基类Shape中的虚函数area()
.text:0000000000400A81                 mov     rax, [rbp+this]
.text:0000000000400A85                 mov     [rax], rdx
.text:0000000000400A88                 mov     rax, [rbp+this]
.text:0000000000400A8C                 mov     edx, [rbp+a]
.text:0000000000400A8F                 mov     [rax+8], edx
.text:0000000000400A92                 mov     rax, [rbp+this]
.text:0000000000400A96                 mov     edx, [rbp+b]
.text:0000000000400A99                 mov     [rax+0Ch], edx
.text:0000000000400A9C                 nop
.text:0000000000400A9D                 pop     rbp
.text:0000000000400A9E                 retn
.text:0000000000400A9E ; } // starts at 400A6E
.text:0000000000400A9E _ZN5ShapeC2Eii  endp
.text:0000000000400A9E
```

同理Triangle的实例化tri(10,5)也是完全相同的步骤。所以站在源代码角度上来说，上述的指令都是对类进行实例化：

```cpp
   Shape *shape;   //指向类的指针
   Rectangle rec(10,7); //实例化类
   Triangle  tri(10,5);
```

但是站在汇编语言的角度来说，最重要的就是对两个子类的虚表指针初始化过程：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637283386940-0bc44df6-bab3-4330-96a3-3f4e3a59633e.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637283593859-8e54a4f6-fda9-4492-bfc0-3b41afea5c61.png)

到目前为止，两个子类的虚表指针都已经初始化并且都存放到了stack上：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637309314452-67a70b6c-0473-4b5a-be5a-d2621e63322e.png)

下面来到两个call rax：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637220624301-1decc853-9593-4d7e-b457-f0036a8826e3.png)

在call第一次rax之前，程序执行了多条汇编指令：

```cpp
.text:00000000004009C9                 lea     rax, [rbp+rec]       //操作rax（步骤1）
//赋值后的rax为0x7fffffffe200 —▸ 0x400cb0 —▸ 0x400b06 (Rectangle::area()) ◂— push   rbp
.text:00000000004009CD                 mov     [rbp+shape], rax
.text:00000000004009D1                 mov     rax, [rbp+shape]		//操作rax（步骤2）
//赋值后的rax为0x7fffffffe200 —▸ 0x400cb0 —▸ 0x400b06 (Rectangle::area()) ◂— push   rbp
.text:00000000004009D5                 mov     rax, [rax]			//操作rax（步骤3）
//赋值后的rax为0x400cb0 —▸ 0x400b06 (Rectangle::area()) ◂— push   rbp
.text:00000000004009D8                 mov     rax, [rax]			//操作rax（步骤4）
//赋值后的rax为0x400b06 (Rectangle::area()) ◂— push   rbp
.text:00000000004009DB                 mov     rdx, [rbp+shape]
.text:00000000004009DF                 mov     rdi, rdx
.text:00000000004009E2                 call    rax
```

**<font style="color:#F5222D;">这里是通过rec对象获取之前初始化的Rectangle虚表指针_vptr，进而获取子类Rectangle中的area()成员函数地址</font>**：

```cpp
#源代码
shape = &rec;   // 获取rec对象的地址:shape==0x7fffffffe200
shape->area();  // 调用矩形的求面积函数 area
```

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637304433500-5431911c-09f8-4b18-8071-a0791c04443e.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637282723795-72494784-8b0a-4d51-94f5-2d28a79f4668.png)

> 这里的shape指针就相当于之前初始化Triangle的this指针，this指针均是通过stack进行传递的，Rectangle同理。
>

单步进入此函数后就打印出来了“Rectangle class area”：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637304224591-a60b056c-2137-4a3c-8e14-faee3e7fc7c6.png)

# pwn
## 解题
接下来我们看一道虚表的题，将题目下载下来，检查一下其文件保护：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637392760545-0ad77c04-71cf-4be1-b244-454d78336e7e.png)

可执行程序中已经内置了后门函数：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637392880197-3cf840f8-a94f-4602-aab8-d925394d5f3d.png)

接下来了解一下程序的流程，直接来到main函数：

> C++看不懂的话建议和源码进行对照，我也是第一次看C++的题...
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637393030271-11532f1b-de34-4ac3-91c4-99bdeaa4f2e5.png)

这里使用new方法分别对类Man和Woman进行实例化，创建的对象分别为m和w。然后到功能语句：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637393554446-4f8f49ed-177a-4569-ae0b-3f7f26c2ef33.png)

首先来看选择1：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637393640760-c5b77e0f-3f22-4faf-84c4-e25b599287e7.png)

这里反编译的伪代码实在是一言难尽，我们还是通过调试来看一下，下断点到0x400fcd处：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637394411442-80362217-dde1-4f21-83de-91a270dd42b5.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637397353076-c71856f6-1a02-40b5-bf07-1c884bfa1bd8.png)

第一张图中的两个红箭头分别是Man和Woman的虚表指针：0x401570、0x401550，第二张图中是各个类中的虚表指针。可以看到一旦子类继承了父类，子类的虚表中就会出现父类的**所有**成员函数。并且因为give_shell函数并没有在子类中重写，所以子类的give_shell和父类完全相同：

```cpp
源代码：
    Human类：
        private：virtual void give_shell()
        protected：age、name
        public：virtual void introduce()
    Man类，继承自Human：
        public：
            构造函数：Man()
            virtual void introduce()
    Woman类，继承自Human：
        public:
            构造函数：Woman()
             virtual void introduce()
编译后：
    Human类：
    	.rodata:0000000000401590 off_401590      dq offset _ZN5Human10give_shellEv
        .rodata:0000000000401590                                         ; DATA XREF: Human::Human(void)+10↑o
        .rodata:0000000000401590                                         ; Human::~Human()+10↑o
        .rodata:0000000000401590                                         ; Human::give_shell(void)
        .rodata:0000000000401598                 dq offset _ZN5Human9introduceEv ; Human::introduce(void)
            __int64 __fastcall Human::introduce(Human *this)
            {
              __int64 v1; // rax
              __int64 v2; // rax
              unsigned int v3; // ebx
              __int64 v4; // rax
              __int64 v5; // rax
              __int64 v6; // rax

              v1 = std::operator<<<std::char_traits<char>>(&std::cout, "My name is ");
              v2 = std::operator<<<char,std::char_traits<char>,std::allocator<char>>(v1, (char *)this + 16);
              std::ostream::operator<<(v2, &std::endl<char,std::char_traits<char>>);
              v3 = *((_DWORD *)this + 2);
              v4 = std::operator<<<std::char_traits<char>>(&std::cout, "I am ");
              v5 = std::ostream::operator<<(v4, v3);
              v6 = std::operator<<<std::char_traits<char>>(v5, " years old");
              return std::ostream::operator<<(v6, &std::endl<char,std::char_traits<char>>);
            }
    Man类，继承自Human：
    	.rodata:0000000000401570 off_401570      dq offset _ZN5Human10give_shellEv
        .rodata:0000000000401570                                         ; DATA XREF: Man::Man(std::string,int)+24↑o
        .rodata:0000000000401570                                         ; Human::give_shell(void)
        .rodata:0000000000401578                 dq offset _ZN3Man9introduceEv ; Man::introduce(void)
            __int64 __fastcall Man::introduce(Man *this)
            {
              __int64 v1; // rax

              Human::introduce(this);
              v1 = std::operator<<<std::char_traits<char>>(&std::cout, "I am a nice guy!");
              return std::ostream::operator<<(v1, &std::endl<char,std::char_traits<char>>);
            }
    Woman类，继承自Human：
    	.rodata:0000000000401550 off_401550      dq offset _ZN5Human10give_shellEv
        .rodata:0000000000401550                                         ; DATA XREF: Woman::Woman(std::string,int)+24↑o
        .rodata:0000000000401550                                         ; Human::give_shell(void)
        .rodata:0000000000401558                 dq offset _ZN5Woman9introduceEv ; Woman::introduce(void)
            __int64 __fastcall Woman::introduce(Woman *this)
            {
              __int64 v1; // rax

              Human::introduce(this);
              v1 = std::operator<<<std::char_traits<char>>(&std::cout, "I am a cute girl!");
              return std::ostream::operator<<(v1, &std::endl<char,std::char_traits<char>>);
            }
       
```

> 父类与子类之间的信息传递是通过this指针进行的，比如：
>

```cpp
virtual void introduce(){
	Human::introduce();   //使用this指针传入到Human的成员函数introduce
	cout << "I am a cute girl!" << endl;
	}
-----------------------------------------------------------------------------------
__int64 __fastcall Woman::introduce(Woman *this){
	__int64 v1; // rax
	Human::introduce(this);
	v1 = std::operator<<<std::char_traits<char>>(&std::cout, "I am a cute girl!");
	return std::ostream::operator<<(v1, &std::endl<char,std::char_traits<char>>);
}
```

另外要注意的是由于使用new方法实例化类，所以两个子类的虚表指针都存在于heap上，因此这两个虚表指针都是可以修改的:

```cpp
pwndbg> x/300gx 0x614c10
0x614c10:       0x0000000000000000      0x0000000000000031 # malloc chunk
0x614c20:       0x0000000000000004      0x0000000000000004
0x614c30:       0x0000000000000000      0x000000006b63614a
    									# Jack
0x614c40:       0x0000000000000000      0x0000000000000021 class Man 对象内存空间
0x614c50:       0x0000000000401570      0x0000000000000019
    			# 虚表指针
0x614c60:       0x0000000000614c38      0x0000000000000031 # malloc chunk
    			#"Jack"字符串指针
0x614c70:       0x0000000000000004      0x0000000000000004
0x614c80:       0x0000000000000000      0x000000006c6c694a
    									# Jill
0x614c90:       0x0000000000000000      0x0000000000000021 class Woman 对象内存空间
0x614ca0:       0x0000000000401550      0x0000000000000015
    			# 虚表指针
0x614cb0:       0x0000000000614c88      0x0000000000000411 缓冲区
    			#"Jill"字符串指针
0x614cc0:       0x0a65657266202e33      0x000000000000000a
    			# 3. free
......(内存为NULL)
0x6150c0:       0x0000000000000000      0x0000000000000411 缓冲区
0x6150d0:       0x0000000000000a31      0x0000000000000000
......(内存为NULL)
0x6154d0:       0x0000000000000000      0x000000000001fb31 top chunk
......(内存为NULL)
0x615560:       0x0000000000000000      0x0000000000000000
pwndbg> 
```

> 这里需要理解堆块的结构。
>

在前面的源码分析中子类的虚表指针只指向了一个成员函数：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637411691402-8523c46a-26f6-417d-b571-d8f16b81affb.png)

而本例中虚表中指向了两个：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637401391422-e3fe3034-82db-4b32-99b0-f5de89df6430.png)

所以程序究竟如何通过虚表调用所需要的函数？

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637413632564-a0b9b8b8-ead2-4421-8185-8b0cbc47d761.png)

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637412471036-0719c7dd-45e1-4029-b35b-5498da6e96cb.png)

所以如果将指针偏移到所需要的大小，当call rdx时就会调用对应的函数。

下面看选项2，如下图所示，这里会根据传入main函数的参数argv[1]创建对应大小的堆块，根据argv[2]将文件内容复制到刚刚的堆块中：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637414274559-876024cf-7ea0-428d-ae4e-cb91b3df74e7.png)

选项3，删除刚刚创建的两个对象，但是存在UAF漏洞。到现在pwn的思路就很明显了，我们创建两个对象，然后free掉两个对象让其进入fastbin：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637414573472-38a7270d-7afe-45a4-aab9-c3a84e3c2106.png)

```cpp
0x20: 0x614c90 —▸ 0x614c40 ◂— 0x0   
0x30: 0x614c60 —▸ 0x614c10 ◂— 0x0 # 该链表不重要
# 0x614c90:class Woman 对象内存空间
# 0x614c40:class Man 对象内存空间
# 后进先出
```

然后我们使用功能2重新申请空间并向其中写入文件：

```cpp
len = atoi(argv[1]);
data = new char[len];
read(open(argv[2], O_RDONLY), data, len);
cout << "your data is allocated" << endl;
```

在正常情况下只会虚表指针只会偏移8从而调用introduce方法，所以我们将虚表指针篡改为原来的vtable-8就能getshell。

```cpp
pwndbg> x/300gx 0x614c10
0x614c10:       0x0000000000000000      0x0000000000000031 # malloc chunk
0x614c20:       0x0000000000000004      0x0000000000000004
0x614c30:       0x0000000000000000      0x000000006b63614a
    									# Jack
0x614c40:       0x0000000000000000      0x0000000000000021 class Man 对象内存空间
0x614c50:       0x0000000000401570      0x0000000000000019
    			# 虚表指针
0x614c60:       0x0000000000614c38      0x0000000000000031 # malloc chunk
    			#"Jack"字符串指针
0x614c70:       0x0000000000000004      0x0000000000000004
0x614c80:       0x0000000000000000      0x000000006c6c694a
    									# Jill
0x614c90:       0x0000000000000000      0x0000000000000021 class Woman 对象内存空间
0x614ca0:       0x0000000000401550      0x0000000000000015
    			# 虚表指针
0x614cb0:       0x0000000000614c88      0x0000000000000411 缓冲区
    			#"Jill"字符串指针
0x614cc0:       0x0a65657266202e33      0x000000000000000a
    			# 3. free
......(内存为NULL)
0x6150c0:       0x0000000000000000      0x0000000000000411 缓冲区
0x6150d0:       0x0000000000000a31      0x0000000000000000
......(内存为NULL)
0x6154d0:       0x0000000000000000      0x000000000001fb31 top chunk
......(内存为NULL)
0x615560:       0x0000000000000000      0x0000000000000000
pwndbg> 
```

注意要将这两个对象的vtable都要修改，由于fastbin的特性为后进先出，所以在申请时**<font style="color:#F5222D;">相同大小的chunk</font>**时会先申请到Woman的内存空间再申请到Man的内存空间。如果只修改Woman的，因为功能1的m->introduce()先会调用，在delete m后其堆块的fd位也就是vtable的地方为NULL，add rax,8后vtable == 0x8，访问这个地址肯定会段错误：

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637420785195-6417743f-e517-4896-9dab-4ae678a021ba.png)

> 可以使用：gdb --args ./uaf 24 ./payload命令进行调试。
>

![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637472282135-a2b7857d-d33d-407f-8248-84f26202208d.png)

注意一下，程序中的UAF漏洞是起到很大的作用，因为如果在free的时候将m和w指针置NULL：

```cpp
delete m;
delete w;
m = w = NULL;
```

在接下来的申请空间的过程中虽然会申请到原来的m和w对象的chunk，但是指针却赋值给了另外一个指针data，也就是说现在的m和w指针仍为空，因此在执行m->introduce()时程序会崩溃。另外申请的堆块空间大小可以不为24，只要进行内存对其后能申请到原来的对象chunk即可。

## exp
## ![](https://cdn.nlark.com/yuque/0/2021/png/574026/1637420440837-d21df1e9-7b3a-43cb-9b35-12f407b25269.png)
## 题目源码
```cpp
#include <fcntl.h>
#include <iostream>
#include <cstring>
#include <cstdlib>
#include <unistd.h>
using namespace std;

class Human{
private:
	virtual void give_shell(){
		system("/bin/sh");
	}
protected:
	int age;
	string name;
public:
	virtual void introduce(){
		cout << "My name is " << name << endl;
		cout << "I am " << age << " years old" << endl;
	}
};
class Man: public Human{
public:
        Man(string name, int age){
                this->name = name;
                this->age = age;
        }
        virtual void introduce(){
                Human::introduce();
                cout << "I am a nice guy!" << endl;
        }
};

class Woman: public Human{
public:
        Woman(string name, int age){
                this->name = name;
                this->age = age;
        }
        virtual void introduce(){
                Human::introduce();
                cout << "I am a cute girl!" << endl;
        }
};

int main(int argc, char* argv[]){
        Human* m = new Man("Jack", 25);
        Human* w = new Woman("Jill", 21);

        size_t len;
        char* data;
        unsigned int op;
        while(1){
                cout << "1. use\n2. after\n3. free\n";
                cin >> op;

                switch(op){
                        case 1:
                                m->introduce();
                                w->introduce();
                                break;
                        case 2:
                                len = atoi(argv[1]);
                                data = new char[len];
                                read(open(argv[2], O_RDONLY), data, len);
                                cout << "your data is allocated" << endl;
                                break;
                        case 3:
                                delete m;
                                delete w;
                                break;
                        default:
                                break;
                }
        }

        return 0;
}
```

