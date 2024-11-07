# path1 = "C:\\Users\\HW\\Desktop\\tupper"
#
# import os
# import regex as re
#
# def natural_sort_key(file_name):
#     # 将文件名分割成数字和非数字部分
#     return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', file_name)]
#
# def traverse_files_numerical_order(directory):
#     for root, dirs, files in os.walk(directory):
#         for file in sorted(files, key=natural_sort_key):
#             file_path = os.path.join(root, file)
#             # print(f"Reading content of file: {file_path}")
#
#             try:
#                 with open(file_path, 'r') as file_handle:
#                     content = file_handle.read()
#                     print(content, end="")
#             except Exception as e:
#                 print(f"Error reading file: {file_path}, {str(e)}")
#
# # 用法示例
# traverse_files_numerical_order(path1)
#


import numpy as np
import matplotlib.pyplot as plt


def Tupper_self_referential_formula(k):
    aa = np.zeros((17, 106))

    def f(x, y):
        y += k
        a1 = 2 ** -(-17 * x - y % 17)
        a2 = (y // 17) // a1
        return 1 if a2 % 2 > 0.5 else 0

    for y in range(17):
        for x in range(106):
            aa[y, x] = f(x, y)

    return aa[:, ::-1]


k = 14278193432728026049298574575557534321062349352543562656766469704092874688354679371212444382298821342093450398907096976002458807598535735172126657504131171684907173086659505143920300085808809647256790384378553780282894239751898620041143383317064727136903634770936398518547900512548419486364915399253941245911205262493591158497708219126453587456637302888701303382210748629800081821684283187368543601559778431735006794761542413006621219207322808449232050578852431361678745355776921132352419931907838205001184
aa = Tupper_self_referential_formula(k)
plt.figure(figsize=(15, 10))
plt.imshow(aa, origin='lower')
plt.gca().invert_xaxis()#x轴反方向反转
plt.show()