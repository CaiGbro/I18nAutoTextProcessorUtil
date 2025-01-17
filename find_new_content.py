def find_new_content(file1_path, file2_path, output_file_path):
    """
    找出两个文件中不同的内容并输出到新文件。
    在提取的数据库词句中找到没在现有的语言资源文件（messages_zh_CN.properties）中的内容，
    用于找到需要更新的词句内容。

    Args:
        file1_path: 第一个文件的路径。
        file2_path: 第二个文件的路径。
        output_file_path: 输出文件的路径。
    """

    try:
        with open(file1_path, 'r', encoding='utf-8') as file1, \
                open(file2_path, 'r', encoding='utf-8') as file2:
            lines1 = file1.readlines()
            lines2 = file2.readlines()

        set1 = set(lines1)
        set2 = set(lines2)

        different_lines = set1 - set2  # 在file1中但不在file2中的行

        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            for line in sorted(different_lines):  # 排序输出，使结果更清晰
                output_file.write(line)

        print(f"不同的内容已写入到 {output_file_path}")

    except FileNotFoundError:
        print(f"错误：找不到文件。请检查文件路径是否正确。")
    except Exception as e:
        print(f"发生错误：{e}")

# 使用示例
file1_path = "./提取到的数据库词句.txt"
file2_path = "./messages_zh_CN.properties"          # 目前的资源文件
output_file_path = "新发现的词句.properties"         #  提取到的数据库词句中不包含在messages_zh_CN.properties中的内容

find_new_content(file1_path, file2_path, output_file_path)
