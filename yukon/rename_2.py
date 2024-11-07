# import os
# import re
#
#
# def rename_files(directory):
#     pattern = re.compile(r'(E\d{8})[_\-\s]*(\w{2,3})')
#     submitted_ids = set()
#
#     for filename in os.listdir(directory):
#         match = pattern.search(filename)
#         if match:
#             student_id = match.group(1)
#             name = match.group(2)
#             submitted_ids.add(student_id)
#             new_filename = f"{student_id}_{name}_网络安全作业1.pdf"
#             old_path = os.path.join(directory, filename)
#             new_path = os.path.join(directory, new_filename)
#
#             if old_path != new_path:
#                 try:
#                     os.rename(old_path, new_path)
#                     print(f"重命名: {filename} -> {new_filename}")
#                 except Exception as e:
#                     print(f"重命名失败: {filename}, 错误: {e}")
#             else:
#                 print(f"文件名已符合格式: {filename}")
#         else:
#             print(f"未找到匹配项: {filename}")
#
#     missing_ids = [f"E{str(i).zfill(8)}" for i in range(42214002, 42214094, 2) if f"E{str(i).zfill(8)}" not in submitted_ids]
#     with open("未交名单.txt", "w", encoding="utf-8") as f:
#         f.write("未交作业名单:\n")
#         f.write("\n".join(missing_ids))
#     print("未交名单已保存至未交名单.txt")
#
#
# if __name__ == "__main__":
#     rename_files(".")
import os
import re


def rename_files(directory, name111="网络安全作业2"):
    directory = directory + '\\'
    pattern = re.compile(r'(E\d{8})[_\-\s]*(\w{2,3})')
    submitted_ids = set()

    for filename in os.listdir(directory):
        match = pattern.search(filename)
        if match:
            student_id = match.group(1)
            submitted_ids.add(student_id)
            name = match.group(2)
            new_filename = f"{student_id}_{name}_{name111}.pdf"
            old_path = os.path.join(directory, filename)
            new_path = os.path.join(directory, new_filename)

            if old_path != new_path:
                try:
                    os.rename(old_path, new_path)
                    print(f"重命名: {filename} -> {new_filename}")
                except Exception as e:
                    print(f"重命名失败: {filename}, 错误: {e}")
            else:
                print(f"文件名已符合格式: {filename}")
        else:
            print(f"未找到匹配项: {filename}")

    missing_ids = [f"E{str(i).zfill(8)}" for i in range(42214002, 42214094, 2) if f"E{str(i).zfill(8)}" not in submitted_ids]
    with open(directory + "未交名单.txt", "w", encoding="utf-8") as f:
        f.write("未交作业名单:\n")
        f.write(" ".join(missing_ids))
    print("未交名单已保存至未交名单.txt")


def generate_missing_list_ldfx(dir_now='./'):
    dir_now = dir_now + '\\'
    start_id = 42214002
    end_id = 42214092
    lab_dir = dir_now + "Lab"
    pre_dir = dir_now + "Pre"
    lab_num = input("请输入 reLab 编号: ").strip()
    pre_num = input("请输入 rePre 编号: ").strip()

    lab_missing = []
    pre_missing = []

    for student_id in range(start_id, end_id + 1, 2):
        student_id_str = f"E{student_id}"

        lab_files = [f for f in os.listdir(lab_dir) if f.startswith(student_id_str) and f"_reLab{lab_num}.pdf" in f]
        pre_files = [f for f in os.listdir(pre_dir) if f.startswith(student_id_str) and f"_rePre{pre_num}.pdf" in f]

        if not lab_files:
            lab_missing.append(student_id_str)

        if not pre_files:
            pre_missing.append(student_id_str)

    with open(dir_now + "未交名单.txt", "w", encoding="utf-8") as f:
        f.write(f"未交 reLab{lab_num} 的学生：\n")
        f.write("无\n" if not lab_missing else " ".join(lab_missing) + "\n")

        f.write(f"\n未交 rePre{pre_num} 的学生：\n")
        f.write("无\n" if not pre_missing else " ".join(pre_missing) + "\n")

    print("统计完成，结果已写入 未交名单.txt")

if __name__ == "__main__":
    rename_files("C:\\Users\\Yukon\\Desktop\\网络安全实验", "网络安全实验一")
    # generate_missing_list_ldfx("C:\\Users\\Yukon\\Desktop\\nxgc_2")

