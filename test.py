import random

# 原始数据
data_ps = [
    74.0, 76.0, 76.0, 78.0, 80, 98, 72.0, 76.0, 98, 77.0, 67.0, 87.0, 99, 75.0,
    88.0, 89.0, 73.0, 95, 71.0, 73.0, 96, 78.0, 69.0, 78.0, 71.0, 75.0, 84.0,
    72.0, 60.0, 64.0, 69.0, 80, 80.0, 81.0, 80.0, 70, 80, 90.0, 75.0, 68.0,
    80.0, 85.0, 77.0, 67.0, 80.0, 74.0
]

data_sy = [
74.0      ,
78.0      ,
76.0      ,
76.0      ,
82        ,
98        ,
72.0      ,
78.0      ,
98        ,
77.0      ,
67.0      ,
89.0      ,
97        ,
75.0      ,
90.0      ,
87.0      ,
79.0      ,
95        ,
75.0      ,
73.0      ,
94        ,
78.0      ,
69.0      ,
78.0      ,
73.0      ,
75.0      ,
84.0      ,
72.0      ,
60.0      ,
64.0      ,
71.0      ,
80        ,
82.0      ,
81.0      ,
80.0      ,
70        ,
80        ,
90.0      ,
75.0      ,
70.0      ,
80.0      ,
85.0      ,
73.0      ,
69.0      ,
80        ,
76.0      ,
]

data_qm = [
74.0,
77.0,
76.0,
77.0,
79  ,
98  ,
72.0,
77.0,
98  ,
77.0,
67.0,
88.0,
98  ,
75.0,
89.0,
88.0,
74.0,
95  ,
73.0,
71.0,
95  ,
76.0,
71.0,
76.0,
68.0,
77.0,
84.0,
70.0,
60.0,
62.0,
68.0,
80  ,
81.0,
81.0,
82.0,
70  ,
80  ,
90.0,
75.0,
69.0,
80.0,
85.0,
75.0,
68.0,
80  ,
77.0,
]

def generate_random_avg_split(value):
    total = round(value * 5)
    splits = []
    for _ in range(4):
        lower_bound = max(0, total - (4 - len(splits)) * 100)
        upper_bound = min(100, total)
        if lower_bound > upper_bound:
            lower_bound, upper_bound = upper_bound, lower_bound
        part = random.randint(lower_bound, upper_bound)
        splits.append(part)
        total -= part
    splits.append(total)
    splits = [max(0, min(100, x)) for x in splits]
    random.shuffle(splits)
    return splits

max_values = [20, 25, 25, 30]

import random

def generate_random_plus_split(value):
    # 设置最大值
    max_values = [20, 25, 25, 30]
    total = int(value)  # 使用整数进行处理
    splits = [0] * 4  # 初始化四个分割值

    quan = value / 100

    for i in range(4):
        splits[i] = int(max_values[i] * quan) + random.randint(-6, 1)
        total -= splits[i]

    if total == 0:
        return splits

    for i in range(4):
        if 0 <= splits[i] + total <= max_values[i]:
            splits[i] += total
            break
        else:
            total -= max_values[i] - splits[i]
            splits[i] = max_values[i]

    return splits


def show_result(data, mode = 0, debug=False):
    """
    :param data: 平时成绩	期末成绩 实验成绩
    :param mode: 平时成绩	 实验成绩 -> 0, 期末成绩 -> 1
    :param debug: 查看原始数据
    """
    if mode:
        randomized_data = [generate_random_plus_split(val) for val in data]
    else:
        randomized_data = [generate_random_avg_split(val) for val in data]

    for original, splits in zip(data, randomized_data):
        if debug:
            if mode:
                print(f"原始值: {original}, 分解值: {splits}, 累加值: {sum(splits)}")
            else:
                print(f"原始值: {original}, 分解值: {splits}, 平均值: {sum(splits) / 5}")
        else:
            for split in splits:
                print(split, end=",")
            print()
    for original, splits in zip(data, randomized_data):
        for split in splits:
            print(split, end=",")
        print()

if __name__ == '__main__':
    # show_result(data_ps, 0)
    # print()
    # show_result(data_sy, 0)
    show_result(data_qm, 1, True)