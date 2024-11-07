import math

# Rail-Fence Cipher栅栏解密，输入加密分组中每组中的字符个数
def fun_deCrypto(string_M, Ek):
    Dk = int(len(string_M) / Ek)
    string_C = ''
    yushu = len(string_M) % Ek
    steps = []

    if len(string_M) % Ek == 0:
        print('不存在余数')
        step = Dk
        for i in range(Ek):
            steps.append(step)
        # print(steps)

    else:
        print('存在余数')

        big_step = math.ceil(len(string_M) / Ek)
        small_step = int(len(string_M) / Ek)
        for p in range(yushu):
            steps.append(big_step)
        for q in range(Ek - yushu):
            steps.append(small_step)
        # print(steps)

    n_column = 0
    while n_column < math.ceil(len(string_M) / Ek):
        count_steps = 0
        for one_step in steps:
            if len(string_C) == len(string_M):
                break
            else:
                string_C += string_M[n_column + count_steps]
                count_steps += one_step
        n_column += 1
    return string_C


cipher = "CrudreasrsheheanaulhfouCmhlaopiaeifltouermrtdpiyeCntpmafhnpbgmbaoagspeuteuwtecwokpetwutileolctnreoicottievhetepriogoseIretodaiithgottfeorhersnueualtebtfamtnseetehrnieipooilrshashyhsrmttmanariaictntgutdeeonmotaudeowuselctnfeoghrtsbaCrgarhtbprthcirarQktodbeatees"


for i in range(1, 12):
    print(i, ":", end="")
    print(fun_deCrypto(cipher, i))