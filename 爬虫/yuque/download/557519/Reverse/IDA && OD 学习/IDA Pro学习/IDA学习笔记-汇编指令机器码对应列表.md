> 文章来自：[https://blog.csdn.net/liqiang981/article/details/51895009](https://blog.csdn.net/liqiang981/article/details/51895009)
>

指令集依照机器操作码、汇编助记符和汇编操作数来描述指令，遵循下列约定：

l     reg8: 8位寄存器。

l     reg16: 16位寄存器。

l     mem8: 8位内存数值。

l     mem16: 16位内存数值。

l     immed8: 8位立即数值。

l     immed16: 16位立即数值。

l     immed32: 32位立即数值。

l     segReg: 16位段寄存器。



机器操作码

 汇编助记符和操作数

 

00

 ADD reg8/mem8,reg8

 

01

 ADD reg16/mem16,reg16

 

02

 ADD reg8,reg8/mem8

 

03

 ADD reg16,reg16/mem16

 

04

 ADD AL,immed8

 

05

 ADD AX,immed16

 

06

 PUSH es

 

07

 POP es

 

08

 OR reg8/mem8,reg8

 

09

 OR reg16/mem16,reg16

 

0A

 OR reg8,reg8/mem8

 

0B

 OR reg16,reg16/mem16

 

0C

 OR al,immed8

 

0D

 OR ax,immed16

 

0E

 PUSH cs

 

0F

 Not used

 

10

 ADC reg8/mem8,reg8

 

11

 ADC reg16/mem16,reg16

 

12

 ADC reg8,reg8/mem8

 

13

 ADC reg16,reg16/mem16

 

14

 ADC al,immed8

 

15

 ADC ax,immed16

 

16

 PUSH ss

 

17

 POP ss

 

18

 SBB reg8/mem8,reg8

 

19

 SBB reg16/mem16,reg16

 

1A

 SBB reg8,reg8/mem8

 

1B

 SBB reg16,reg16/mem16

 

1C

 SBB al,immed8

 

1D

 SBB ax,immed16

 

1E

 PUSH ds

 

1F

 POP ds

 

20

 AND reg8/mem8,reg8

 

21

 AND reg16/mem16,reg16

 

22

 AND reg8,reg8/mem8

 

23

 AND reg16,reg16/mem16

 

24

 AND al,immed8

 

25

 AND ax,immed16

 

26

 Segment override

 

27

 DAA

 

28

 SUB reg8/mem8,reg8

 

29

 SUB reg16/mem16,reg16

 

2A

 SUB reg8,reg8/mem8

 

2B

 SUB reg16,reg16/mem16

 

2C

 SUB al,immed8

 

2D

 SUB ax,immed16

 

2E

 Segment override

 

2F

 DAS

 

30

 XOR reg8/mem8,reg8

 

31

 XOR reg16/mem16,reg16

 

32

 XOR reg8,reg8/mem8

 

33

 XOR reg16,reg16/mem16

 

34

 XOR al,immed8

 

35

 XOR ax,immed16

 

36

 Segment override

 

37

 AAA

 

38

 CMP reg8/mem8,reg8

 

39

 CMP reg16/mem16,reg16

 

3A

 CMP reg8,reg8/mem8

 

3B

 CMP reg16,reg16/mem16

 

3C

 CMP al,immed8

 

3D

 CMP ax,immed16

 

3E

 Segment override

 

3F

 AAS

 

40

 INC ax

 

41

 INC cx

 

42

 INC dx

 

43

 INC bx

 

44

 INC sp

 

45

 INC bp

 

46

 INC si

 

47

 INC di

 

48

 DEC ax

 

49

 DEC cx

 

4A

 DEC dx

 

4B

 DEC bx

 

4C

 DEC sp

 

4D

 DEC bp

 

4E

 DEC si

 

4F

 DEC di

 

50

 PUSH ax

 

51

 PUSH cx

 

52

 PUSH dx

 

53

 PUSH bx

 

54

 PUSH sp

 

55

 PUSH bp

 

56

 PUSH si

 

57

 PUSH di

 

58

 POP ax

 

59

 POP cx

 

5A

 POP dx

 

5B

 POP bx

 

5C

 POP sp

 

5D

 POP bp

 

5E

 POP si

 

5F

 POP di

 

60

 PUSHA

 

61

 POPA

 

62

 BOUND reg16/mem16,reg16

 

63

 Not used

 

64

 Not used

 

65

 Not used

 

66

 Not used

 

67

 Not used

 

68

 PUSH immed16

 

69

 IMUL reg16/mem16,immed16

 

6A

 PUSH immed8

 

6B

 IMUL reg8/mem8,immed8

 

6C

 INSB

 

6D

 INSW

 

6E

 OUTSB

 

6F

 OUTSW

 

70

 JO immed8

 

71

 JNO immed8

 

72

 JB immed8

 

73

 JNB immed8

 

74

 JZ immed8

 

75

 JNZ immed8

 

76

 JBE immed8

 

77

 JA immed8

 

78

 JS immed8

 

79

 JNS immed8

 

7A

 JP immed8

 

7B

 JNP immed8

 

7C

 JL immed8

 

7D

 JNL immed8

 

7E

 JLE immed8

 

7F

 JG immed8

 

80

 Table2 reg8

 

81

 Table2 reg16

 

82

 Table2 reg8

 

83

 Table2 reg8, reg16

 

84

 TEST reg8/mem8,reg8

 

85

 TEST reg16/mem16,reg16

 

86

 XCHG reg8,reg8

 

87

 XCHG reg16,reg16

 

88

 MOV reg8/mem8,reg8

 

89

 MOV reg16/mem16,reg16

 

8A

 MOV reg8,reg8/mem8

 

8B

 MOV reg16,reg16/mem16

 

8C

 MOV reg16/mem16,segReg

 

8D

 LEA reg16,reg16/mem16

 

8E

 MOV segReg,reg16/mem16

 

8F

 POP reg16/mem16

 

90

 NOP

 

91

 XCHG ax,cx

 

92

 XCHG ax,dx

 

93

 XCHG ax,bx

 

94

 XCHG ax,sp

 

95

 XCHG ax,bp

 

96

 XCHG ax,si

 

97

 XCHG ax,di

 

98

 CBW 99CWD

 

9A

 CALL immed32

 

9B

 WAIT

 

9C

 PUSHF

 

9D

 POPF

 

9E

 SAHF

 

9F

 LAHF

 

A0

 MOV al,[mem8]

 

A1

 MOV ax,[mem16]

 

A2

 MOV [mem8],al

 

A3

 MOV [mem16],ax

 

A4

 MOVSB

 

A5

 MOVSW

 

A6

 CMPSB

 

A7

 CMPSW

 

A8

 TEST al,[mem8]

 

A9

 TEST ax,[mem16]

 

AA

 STOSB

 

AB

 STOSW

 

AC

 LODSB

 

AD

 LODSW

 

AE

 SCASB

 

AF

 SCASW

 

B0

 MOV al,immed8

 

B1

 MOV cl,immed8

 

B2

 MOV dl,immed8

 

B3

 MOV bl,immed8

 

B4

 MOV ah,immed8

 

B5

 MOV ch,immed8

 

B6

 MOV dh,immed8

 

B7

 MOV bh,immed8

 

B8

 MOV ax,immed16

 

B9

 MOV cx,immed16

 

BA

 MOV dx,immed16

 

BB

 MOV bx,immed16

 

BC

 MOV sp,immed16

 

BD

 MOV bp,immed16

 

BE

 MOV si,immed16

 

BF

 MOV di,immed16

 

C0

 Table1 reg8

 

C1

 Table1 reg8, reg16

 

C2

 RET immed16

 

C3

 RET

 

C4

 LES reg16/mem16,mem16

 

C5

 LDS reg16/mem16,mem16

 

C6

 MOV reg8/mem8,immed8

 

C7

 MOV reg16/mem16,immed16

 

C8

 ENTER immed16, immed8

 

C9

 LEAVE

 

CA

 RET immed16

 

CB

 RET

 

CC

 INT 3

 

CD

 INT immed8

 

CE

 INTO

 

CF

 IRET

 

D0

 Table1 reg8

 

D1

 Table1 reg16

 

D2

 Table1 reg8

 

D3

 Table1 reg16

 

D4

 AAM

 

D5

 AAD

 

D6

 Not used

 

D7

 XLAT [bx]

 

D8

 ESC immed8

 

D9

 ESC immed8

 

DA

 ESC immed8

 

DB

 ESC immed8

 

DC

 ESC immed8

 

DD

 ESC immed8

 

DE

 ESC immed8

 

DF

 ESC immed8

 

E0

 LOOPNE immed8

 

E1

 LOOPE immed8

 

E2

 LOOP immed8

 

E3

 JCXZ immed8

 

E4

 IN al,immed8

 

E5

 IN ax,immed16

 

E6

 OUT al,immed8

 

E7

 OUT ax,immed16

 

E8

 CALL immed16

 

E9

 JMP immed16

 

EA

 JMP immed32

 

EB

 JMP immed8

 

EC

 IN al,dx

 

ED

 IN ax,dx

 

EE

 OUT al,dx

 

EF

 OUT ax,dx

 

F0

 LOCK

 

F1

 Not used

 

F2

 REPNE

 

F3

 REP

 

F4

 HLT

 

F5

 CMC

 

F6

 Table3 reg8

 

F7

 Table3 reg16

 

F8

 CLC

 

F9

 STC

 

FA

 CLI

 

FB

 STI

 

FC

 CLD

 

FD

 STD

 

FE

 Table4 reg8

 

FF

 Table4 reg16

————————————————

版权声明：本文为CSDN博主「liqiang981」的原创文章，遵循CC 4.0 BY-SA版权协议，转载请附上原文出处链接及本声明。

原文链接：[https://blog.csdn.net/liqiang981/java/article/details/51895009](https://blog.csdn.net/liqiang981/java/article/details/51895009)

