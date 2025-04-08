> <font style="color:#333333;">addr  :代表8位地址    addr16:代表16位地址     data  :立即数</font>
>

# <font style="color:#333333;">数据传送指令</font>
<font style="color:#333333;">//LDA--由存储器取数送入累加器 M→A</font>

<font style="color:#333333;">符号码格式 指令操作码 寻址方式 </font>

<font style="color:#333333;">LDA ($addr,X) A1 先变址X后间址 </font>

<font style="color:#333333;">LDA $addr A5 零页寻址 </font>

<font style="color:#333333;">LDA #$data A9 立即寻址 </font>

<font style="color:#333333;">LDA $addr16 AD 绝对寻址 </font>

<font style="color:#333333;">LDA ($addr),Y B1 后变址Y间址 </font>

<font style="color:#333333;">LDA $addr,X B5 零页X变址 </font>

<font style="color:#333333;">LDA $addr16,Y B9 绝对Y变址 </font>

<font style="color:#333333;">LDA $addr16,X BD 绝对X变址 </font>



<font style="color:#333333;">//LDX--由存储器取数送入累加器 M→X</font>

<font style="color:#333333;">符号码格式 指令操作码 寻址方式 </font>

<font style="color:#333333;">LDX #$data A2 立即寻址 </font>

<font style="color:#333333;">LDX $addr A6 零页寻址 </font>

<font style="color:#333333;">LDX $addr16 AE 绝对寻址 </font>

<font style="color:#333333;">LDX $addr,Y B6 零页Y变址 </font>

<font style="color:#333333;">LDX $addr16,Y BE 绝对Y变址 </font>



<font style="color:#333333;">//LDY--由存储器取数送入累加器 M→Y</font>

<font style="color:#333333;">符号码格式 指令操作码 寻址方式 </font>

<font style="color:#333333;">LDY #$data A0 立即寻址 </font>

<font style="color:#333333;">LDY $addr A4 零页寻址 </font>

<font style="color:#333333;">LDY $addr16 AC 绝对寻址 </font>

<font style="color:#333333;">LDY $addr,X B4 零页X变址 </font>

<font style="color:#333333;">LDY $addr16,X BC 绝对X变址 </font>



<font style="color:#333333;">//STA--将累加器的内容送入存储器 A--M</font>

<font style="color:#333333;">符号码格式 指令操作码 寻址方式 </font>

<font style="color:#333333;">STA ($addr,X) 81 先变址X后间址 </font>

<font style="color:#333333;">STA $addr 85 零页寻址 </font>

<font style="color:#333333;">STA $addr16 8D 绝对寻址 </font>

<font style="color:#333333;">STA ($addr),Y 91 后变址Y间址 </font>

<font style="color:#333333;">STA $addr,X 95 零页X变址 </font>

<font style="color:#333333;">STA $addr16,Y 99 绝对Y变址 </font>

<font style="color:#333333;">STA $addr16,X 9D 绝对X变址 </font>



<font style="color:#333333;">//STX--将寄存器X的内容送入存储器 X--M</font>

<font style="color:#333333;">符号码格式 指令操作码 寻址方式 </font>

<font style="color:#333333;">STX $addr 86 零页寻址 </font>

<font style="color:#333333;">STX $addr16 8E 绝对寻址 </font>

<font style="color:#333333;">STX $addr,Y 96 零页Y变址 </font>



<font style="color:#333333;">//STY--将寄存器Y的内容送入存储器 Y--M</font>

<font style="color:#333333;">符号码格式 指令操作码 寻址方式 </font>

<font style="color:#333333;">STY $addr 84 零页寻址 </font>

<font style="color:#333333;">STY $addr16 8C 绝对寻址 </font>

<font style="color:#333333;">STY $addr,X 94 零页X变址 </font>



<font style="color:#333333;">//寄存器和寄存器之间的传送</font>

<font style="color:#333333;">符号码格式 指令操作码 寻址方式 指令作用 </font>

<font style="color:#333333;">TAX AA 寄存器寻址 将累加器A的内容送入变址寄存器X </font>

<font style="color:#333333;">TXA 8A 寄存器寻址 将变址寄存器X的内容送入累加器A </font>

<font style="color:#333333;">TAY A8 寄存器寻址 将累加器A的内容送入变址寄存器Y </font>

<font style="color:#333333;">TYA 98 寄存器寻址 将变址寄存器Y的内容送入累加器A </font>

<font style="color:#333333;">TSX BA 寄存器寻址 将堆栈指针S的内容送入变址寄存器X </font>

<font style="color:#333333;">TXS 9A 寄存器寻址 将变址寄存器X的内容送入堆栈指针S </font>



# <font style="color:#333333;">算术运算指令</font>
<font style="color:#333333;">1. ADC--累加器,存储器,进位标志C相加,结果送累加器A  A+M+C→A </font>

<font style="color:#333333;">符号码格式 指令操作码 寻址方式            周期 </font>

<font style="color:#333333;">ADC ($addr,X) 61 先变址X后间址          </font>

<font style="color:#333333;">ADC $addr 65 零页寻址 </font>

<font style="color:#333333;">ADC #$data 69 立即寻址 </font>

<font style="color:#333333;">ADC $addr16 6D 绝对寻址 </font>

<font style="color:#333333;">ADC ($addr),Y 71 后变址Y间址 </font>

<font style="color:#333333;">ADC $addr,X 75 零页X变址 </font>

<font style="color:#333333;">ADC $addr16,Y 79 绝对Y变址 </font>

<font style="color:#333333;">ADC $addr16,X 7D 绝对X变址 </font>



<font style="color:#333333;">2. SBC--从累加器减去存储器和进位标志C,结果送累加器  A-M-C→A</font>

<font style="color:#333333;">符号码格式 指令操作码 寻址方式 </font>

<font style="color:#333333;">SBC ($addr,X) E1 先变址X后间址 </font>

<font style="color:#333333;">SBC $addr E5 零页寻址 </font>

<font style="color:#333333;">SBC #$data E9 立即寻址 </font>

<font style="color:#333333;">SBC $addr16 ED 绝对寻址 </font>

<font style="color:#333333;">SBC ($addr),Y F1 后变址Y间址 </font>

<font style="color:#333333;">SBC $addr,X F5 零页X变址 </font>

<font style="color:#333333;">SBC $addr16,Y F9 绝对Y变址 </font>

<font style="color:#333333;">SBC $addr16,X FD 绝对X变址 </font>

<font style="color:#333333;"></font>

<font style="color:#333333;">3. INC--存储器单元内容增1  M+1→M</font>

<font style="color:#333333;">符号码格式 指令操作码 寻址方式 </font>

<font style="color:#333333;">INC $addr E6 零页寻址 </font>

<font style="color:#333333;">INC $addr16 EE 绝对寻址 </font>

<font style="color:#333333;">INC $addr,X F6 零页X变址 </font>

<font style="color:#333333;">INC $addr16,X FE 绝对X变址 </font>



<font style="color:#333333;">4. DEC--存储器单元内容减1  M-1→M</font>

<font style="color:#333333;">符号码格式 指令操作码 寻址方式 </font>

<font style="color:#333333;">DEC $addr C6 零页寻址 </font>

<font style="color:#333333;">DEC $addr16 CE 绝对寻址 </font>

<font style="color:#333333;">DEC $addr,X D6 零页X变址 </font>

<font style="color:#333333;">DEC $addr16,X DE 绝对X变址 </font>



<font style="color:#333333;">5. 寄存器X,Y加1减1</font>

<font style="color:#333333;">符号码格式 指令操作码 寻址方式 </font>

<font style="color:#333333;">INX E8 隐含寻址 </font>

<font style="color:#333333;">DEX CA 隐含寻址 </font>

<font style="color:#333333;">INY C8 隐含寻址 </font>

<font style="color:#333333;">DEY 88 隐含寻址 </font>



# <font style="color:#333333;">逻辑运算指令</font>
<font style="color:#333333;">1.AND--寄存器与累加器相与,结果送累加器  A∧M→A</font>

<font style="color:#333333;">符号码格式 指令操作码 寻址方式 </font>

<font style="color:#333333;">AND ($addr,X) 21 先变址X后间址 </font>

<font style="color:#333333;">AND $addr 25 零页寻址 </font>

<font style="color:#333333;">AND #$data 29 立即寻址 </font>

<font style="color:#333333;">AND $addr16 2D 绝对寻址 </font>

<font style="color:#333333;">AND ($addr),Y 31 后变址Y间址 </font>

<font style="color:#333333;">AND $addr,X 35 零页X变址 </font>

<font style="color:#333333;">AND $addr16,Y 39 绝对Y变址 </font>

<font style="color:#333333;">AND $addr16,X 3D 绝对X变址 </font>

<font style="color:#333333;">     </font>

<font style="color:#333333;">2.ORA--寄存器与累加器相或,结果送累加器  A∨M→A</font>

<font style="color:#333333;">符号码格式 指令操作码 寻址方式 </font>

<font style="color:#333333;">ORA ($addr,X) 01 先变址X后间址 </font>

<font style="color:#333333;">ORA $addr 05 零页寻址 </font>

<font style="color:#333333;">ORA #$data 09 立即寻址 </font>

<font style="color:#333333;">ORA $addr16 0D 绝对寻址 </font>

<font style="color:#333333;">ORA ($addr),Y 11 后变址Y间址 </font>

<font style="color:#333333;">ORA $addr,X 15 零页X变址 </font>

<font style="color:#333333;">ORA $addr16,Y 19 绝对Y变址 </font>

<font style="color:#333333;">ORA $addr16,X 1D 绝对X变址 </font>



<font style="color:#333333;">3.EOR--寄存器与累加器相异或,结果送累加器  A≮M→A</font>

<font style="color:#333333;">符号码格式 指令操作码 寻址方式 </font>

<font style="color:#333333;">EOR ($addr,X) 41 先变址X后间址 </font>

<font style="color:#333333;">EOR $addr 45 零页寻址 </font>

<font style="color:#333333;">EOR #$data 49 立即寻址 </font>

<font style="color:#333333;">EOR $addr16 4D 绝对寻址 </font>

<font style="color:#333333;">EOR ($addr),Y 51 后变址Y间址 </font>

<font style="color:#333333;">EOR $addr,X 55 零页X变址 </font>

<font style="color:#333333;">EOR $addr16,Y 59 绝对Y变址 </font>

<font style="color:#333333;">EOR $addr16,X 5D 绝对X变址 </font>

# <font style="color:#333333;">置标志位指令</font>
<font style="color:#333333;">1. CLC--清除进位标志         0→C   机器码 18     √</font>

<font style="color:#333333;">2. SEC--置进位标志C          1→C   机器码 38     √</font>

<font style="color:#333333;">3. CLD--清除十进制运算标志D  0→D   机器码 D8     ×</font>

<font style="color:#333333;">4. SED--置十进制运算标志D    1→D   机器码 F8     ×</font>

<font style="color:#333333;">5. CLV--清除溢出标志V        0→V   机器码 B8</font>

<font style="color:#333333;">6. CLI--清除中断禁止指令I    0→I   机器码 58     √</font>

<font style="color:#333333;">7. SEI--置位中断禁止标志I    1→I   机器码 78     √</font>

<font style="color:#333333;">　</font>

# <font style="color:#333333;">比较指令</font>
<font style="color:#333333;">1. CMP--累加器和存储器比较</font>

<font style="color:#333333;"></font>

<font style="color:#333333;">符号码格式 指令操作码 寻址方式 </font>

<font style="color:#333333;">CMP ($addr,X) C1 先变址X后间址 </font>

<font style="color:#333333;">CMP $addr C5 零页寻址 </font>

<font style="color:#333333;">CMP #$data C9 立即寻址 </font>

<font style="color:#333333;">CMP $addr16 CD 绝对寻址 </font>

<font style="color:#333333;">CMP ($addr),Y D1 后变址Y间址 </font>

<font style="color:#333333;">CMP $addr,X D5 零页X变址 </font>

<font style="color:#333333;">CMP $addr16,Y D9 绝对Y变址 </font>

<font style="color:#333333;">CMP $addr16,X DD 绝对X变址 </font>

<font style="color:#333333;"></font>

<font style="color:#333333;">2. CPX--寄存器X的内容和存储器比较</font>

<font style="color:#333333;">符号码格式 指令操作码 寻址方式 </font>

<font style="color:#333333;">CPX #$data E0 立即寻址 </font>

<font style="color:#333333;">CPX $addr E4 零页寻址 </font>

<font style="color:#333333;">CPX $addr16 EC 绝对寻址 </font>



<font style="color:#333333;">这些指令和CMP指令相似,不过前者是寄存器A,后者是寄存器X,另外寻址方式也比较少.</font>



<font style="color:#333333;">3. CPY--寄存器Y的内容和存储器比较</font>

<font style="color:#333333;">符号码格式 指令操作码 寻址方式 </font>

<font style="color:#333333;">CPY #$data C0 立即寻址 </font>

<font style="color:#333333;">CPY $addr C4 零页寻址 </font>

<font style="color:#333333;">CPY $addr16 CC 绝对寻址 </font>

<font style="color:#333333;"></font>

<font style="color:#333333;">这些指令和CPX指令相似,不过前者是寄存器X,后者是寄存器Y.</font>



<font style="color:#333333;">4. BIT--位测试指令</font>

<font style="color:#333333;">符号码格式 指令操作码 寻址方式 </font>

<font style="color:#333333;">BIT $addr 24 零页寻址 </font>

<font style="color:#333333;">BIT $addr16 2C 绝对寻址 </font>





# <font style="color:#333333;">移位指令</font>
<font style="color:#333333;">1. 算术左移指令ASL</font>

<font style="color:#333333;">符号码格式 指令操作码 寻址方式 </font>

<font style="color:#333333;">ASL 0A 累加器寻址 </font>

<font style="color:#333333;">ASL $data 06 零页寻址 </font>

<font style="color:#333333;">ASL $addr16 0E 绝对寻址 </font>

<font style="color:#333333;">ASL $addr,X 16 零页X变址 </font>

<font style="color:#333333;">ASL $addr16,X 1E 绝对X变址 </font>



<font style="color:#333333;">ASL移位功能是将字节内各位依次向左移1位，最高位移进标志位C中，最底位补0</font>

<font style="color:#333333;"></font>

<font style="color:#333333;">2. 逻辑右移指令LSR</font>

<font style="color:#333333;">符号码格式 指令操作码 寻址方式 </font>

<font style="color:#333333;">LSR 4A 累加器寻址 </font>

<font style="color:#333333;">LSR $data 46 零页寻址 </font>

<font style="color:#333333;">LSR $addr16 4E 绝对寻址 </font>

<font style="color:#333333;">LSR $addr,X 56 零页X变址 </font>

<font style="color:#333333;">LSR $addr16,X 5E 绝对X变址 </font>



<font style="color:#333333;">该指令功能是将字节内各位依次向右移1位，最低位移进标志位C，最高位补0.</font>

<font style="color:#333333;"></font>

<font style="color:#333333;">3. 循环左移指令ROL</font>

<font style="color:#333333;">符号码格式 指令操作码 寻址方式 </font>

<font style="color:#333333;">ROL 2A 累加器寻址 </font>

<font style="color:#333333;">ROL $data 26 零页寻址 </font>

<font style="color:#333333;">ROL $addr16 2E 绝对寻址 </font>

<font style="color:#333333;">ROL $addr,X 36 零页X变址 </font>

<font style="color:#333333;">ROL $addr16,X 3E 绝对X变址 </font>



<font style="color:#333333;">ROL的移位功能是将字节内容连同进位C一起依次向左移1位</font>

<font style="color:#333333;"></font>

<font style="color:#333333;">4. 循环右移指令ROR</font>

<font style="color:#333333;">符号码格式 指令操作码 寻址方式 </font>

<font style="color:#333333;">ROR 6A 累加器寻址 </font>

<font style="color:#333333;">ROR $data 66 零页寻址 </font>

<font style="color:#333333;">ROR $addr16 6E 绝对寻址 </font>

<font style="color:#333333;">ROR $addr,X 76 零页X变址 </font>

<font style="color:#333333;">ROR $addr16,X 7E 绝对X变址 </font>



<font style="color:#333333;">ROR的移位功能是将字节内容连同进位C一起依次向右移1位</font>



<font style="color:#333333;">addr  :代表8位地址    addr16:代表16位地址     data  :立即数</font>

# <font style="color:#333333;"></font>
# <font style="color:#333333;">堆栈操作指令</font>
<font style="color:#333333;">1. 累加器进栈指令 PHA</font>

<font style="color:#333333;">   PHA是隐含寻址方式的单字节指令，操作码是 48</font>

<font style="color:#333333;">   功能是把累加器A的内容按堆栈指针S所指示的位置送入堆栈，然后堆栈指针减1</font>

<font style="color:#333333;">   该指令不影响标志寄存器P的状态</font>

<font style="color:#333333;"></font>

<font style="color:#333333;">2. 累加器出栈指令 PLA</font>

<font style="color:#333333;">   PLA是隐含寻址方式的单字节指令，操作码是 68</font>

<font style="color:#333333;">   功能是先让堆栈指针S+1，然后取加过1的S所指向的单元的内容，把它送累加器A</font>

<font style="color:#333333;">   该指令影响标志寄存器P中的N，Z两标志位</font>



<font style="color:#333333;">3. 标志寄存器P进栈指令 PHP</font>

<font style="color:#333333;">   PHP是隐含寻址方式的单字节指令，操作码是 08</font>

<font style="color:#333333;">   功能是把标志寄存器P的内容按堆栈指针S所指示的位置送入堆栈，然后堆栈指针减1</font>

<font style="color:#333333;">   该指令不影响标志寄存器P的状态</font>



<font style="color:#333333;">4. 标志寄存器P出栈指令 PLP</font>

<font style="color:#333333;">   PLP是隐含寻址方式的单字节指令，操作码是 28</font>

<font style="color:#333333;">   功能是先让堆栈指针S+1，然后取加过1的S所指向的单元的内容，把它送标志寄存器P</font>

<font style="color:#333333;">　</font>

# 跳转指令
<font style="color:#333333;">1. JMP--无条件转移指令</font>

<font style="color:#333333;">符号码格式 指令操作码 寻址方式 </font>

<font style="color:#333333;">JMP  $data16 4C 绝对寻址 </font>

<font style="color:#333333;">JMP ($data16) 5C 间接寻址 </font>



<font style="color:#333333;">2. 条件转移指令</font>

<font style="color:#333333;">符号码格式 指令操作码 寻址方式 指令功能 </font>

<font style="color:#333333;">BEQ $data16 F0 相对寻址 如果标志位Z=1则转移，否则继续 </font>

<font style="color:#333333;">BNE $data16 D0 相对寻址 如果标志位Z=0则转移，否则继续 </font>

<font style="color:#333333;">BCS $data16 B0 相对寻址 如果标志位C=1则转移，否则继续 </font>

<font style="color:#333333;">BCC $data16 90 相对寻址 如果标志位C=0则转移，否则继续 </font>

<font style="color:#333333;">BMI $data16 30 相对寻址 如果标志位N=1则转移，否则继续 </font>

<font style="color:#333333;">BPL $data16 10 相对寻址 如果标志位N=0则转移，否则继续 </font>

<font style="color:#333333;">BVS $data16 70 相对寻址 如果标志位V=1则转移，否则继续 </font>



<font style="color:#333333;">3. 转移到子程序指令JSR和从主程序返回指令RTS</font>

<font style="color:#333333;">JSR指令仅仅是 绝对寻址，它的操作码是 20</font>

<font style="color:#333333;">RTS指令是     隐含寻址，它的操作码是 60 </font>



# <font style="color:#333333;">中断指令</font>
<font style="color:#333333;">  在文曲星（红白机的一种）内部大量使用了这种指令,该指令占三个字节.</font>

<font style="color:#333333;">  操作符为 INT,机器码为 00</font>

<font style="color:#333333;">  例如 INT $8A01</font>

<font style="color:#333333;">          INT $C001</font>

