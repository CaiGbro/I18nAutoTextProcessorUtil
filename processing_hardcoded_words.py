import os
import re
 
def processing_hardcoded_words(folder_path):
    """
    用于提取代码中硬编码的词句，将这些词句提取到messages_zh_CN.properties中，
    并将这些词句作为键，加入由该键在资源文件中寻找对应的值的代码，

    例如.
    原代码
        errStr.append("早期BPD1(mm)只能输入10位以内数字或小数！");
    提取到messages_zh_CN.properties的内容为
        早期BPD1只能输入10位以内数字或小数.message=早期BPD1(mm)只能输入10位以内数字或小数！
    代码集成工具类的功能变为
        errStr.append(getMessage("早期BPD1只能输入10位以内数字或小数.message"));    


    思路是：
        遍历文件夹中所有后缀为.java的文件，并逐行对文件里的代码进行处理，
        对于每一行代码每找到一个""就将里面的内容按规则R进行处理，
        每处理完一个文件在控制台打印这个文件的名字。       ------------------------只对英文双引号的内容进行处理
        规则R：
        1.必须包含中文
        2.按顺序提取中文、字母或数字，其余跳过，设提取的内容为A，例如
        ""中的原内容为B，将B以getMessage("A.message")的行形式代替，
        然后将提取的内容以A.message=B的形式添加到messages_zh_CN.properties文件的下一行中，
        在添加时如果A在文件中已经存在则判断已经存在的A对应的B是否与要插入的B相同，
        如果相同则跳过，如果不同则将向A后添加1然后重试，如A1、A2、A3这种形式重试。 ------------------------因为i18n资源文件的键对格式有很多限制，
        ----------------------------------------------------------------------------为了避免出现怪问题，将键的格式统一为中文字母和数字的组合。
        3.如果这一行以@或者大写字母开头则跳过这一行------------------忽略自定义注解
        4.如果以logger或者log开头则跳过这一行  ---------------------忽略日志内容
        5.这一行的=左边存在大写字母则跳过这一行 ---------------------类似于这种private static final String[] NUMS = {"零", "一", "二", "三", "四", "五", "六", "七", "八", "九",};
        6.如果文件名为StringUtil则跳过这个文件 ---------------------类似于这种str = str.replaceAll("【", "[").replaceAll("】", "]").replaceAll("！", "!");

    局限：
        如规则R中5、6那样，需要根据实际项目情况做一些改动

        可能会出现一些没有考虑到的bug，如

        if(CollectionUtils.isEmpty(codes) || StringUtil.isEmpty(typeCode)){
            I18nAutoTextProcessorUtil.extractAndWrite(result);
            return ParamUtils.getSuccessResult(I18nAutoTextProcessorUtil.translate(result));}
        PageData tPd = new PageData();
        
        报错是因为这个 if 没有 {}，原本 if 后只有一行，
        但是插入I18nAutoTextProcessorUtil.extractAndWrite(result);后变成了两行，此时没有 {} 就会报错。

        我没有修复这个问题，也算给朋友们的一个提醒

    Args:
        folder_path: 文件夹路径。
    """

    messages_file = "oringin_messages_zh_CN.properties"
    messages_dict = load_messages(messages_file)

    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".java") and file != "StringUtil.java" and not file.endswith("Mapper.java"):
                file_path = os.path.join(root, file)
                print(f"Processing: {file_path}")
                process_file(file_path, messages_dict)

    write_messages(messages_file, messages_dict)

def load_messages(messages_file):
    """
    加载已有的messages_zh_CN.properties文件内容。

    Args:
        messages_file: messages_zh_CN.properties文件路径。

    Returns:
        包含messages_zh_CN.properties内容的字典。
    """

    messages_dict = {}
    try:
        with open(messages_file, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    messages_dict[key] = value
    except FileNotFoundError:
        pass
    return messages_dict

def process_file(file_path, messages_dict):
    """
    处理单个.java文件。

    Args:
        file_path: .java文件路径。
        messages_dict: 包含messages_zh_CN.properties内容的字典。
    """

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 找到第一个package所在的行
    package_line_index = -1
    for i, line in enumerate(lines):
        if line.strip().startswith("package"):
            package_line_index = i
            break

    # 在package定义行的下一行插入import语句
    if package_line_index != -1:
         lines.insert(package_line_index + 1, "import " + package_path + "I18nAutoTextProcessorUtil;\n")

    new_lines = []
    for line in lines:
        new_line = process_line(line, messages_dict)
        new_lines.append(new_line)

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

def process_line(line, messages_dict):
    """
    处理一行代码。

    Args:
        line: 一行代码。
        messages_dict: 包含messages_zh_CN.properties内容的字典。

    Returns:
        处理后的一行代码。
    """

    if line.strip().startswith("@") or line.strip()[0:1].isupper() if line.strip() else False:
        return line
    if line.strip().startswith("logger.") or line.strip().startswith("log."):
        return line
    if any(c.isupper() for c in line.split("=")[0]) if "=" in line else False:
        return line

    new_line = ""
    last_end = 0
    for match in re.finditer(r'"(.*?)"', line):
        start, end = match.span()
        new_line += line[last_end:start]

        original_text = match.group(1)

        # 检查是否包含中文
        if any('\u4e00' <= c <= '\u9fff' for c in original_text):
            extracted_text = extract_content(original_text)

            if extracted_text:
                message_key = find_message_key(extracted_text, original_text, messages_dict)
                new_line += f'I18nAutoTextProcessorUtil.getMessage("{message_key}")' # 修改为 I18nAutoTextProcessorUtil.getMessage()
            else:
                new_line += f'"{original_text}"'
        else:
            new_line += f'"{original_text}"'  # 不包含中文，保持原样

        last_end = end

    new_line += line[last_end:]
    return new_line

def extract_content(text):
    """
    根据规则R提取内容，现在可以提取完整的句子。

    Args:
        text: 原始文本。

    Returns:
        提取后的内容。
    """

    extracted = ""
    for char in text:
        if '\u4e00' <= char <= '\u9fff' or 'a' <= char <= 'z' or 'A' <= char <= 'Z' or '0' <= char <= '9':
            extracted += char
        # else:
        #   extracted += char # 如果需要将其他字符也提取到键名中，例如括号，则取消这行的注释
    
    return extracted if extracted else None

def find_message_key(extracted_text, original_text, messages_dict):
    """
    查找或生成message key。

    Args:
        extracted_text: 提取的内容。
        original_text: 原始文本。
        messages_dict: 包含messages_zh_CN.properties内容的字典。

    Returns:
        message key。
    """

    base_key = extracted_text + ".message"
    key = base_key
    counter = 1

    while key in messages_dict:
        if messages_dict[key] == original_text:
            return key
        else:
            key = base_key + str(counter)
            counter += 1

    messages_dict[key] = original_text
    return key

def write_messages(messages_file, messages_dict):
    """
    将messages写入messages_zh_CN.properties文件。

    Args:
        messages_file: messages_zh_CN.properties文件路径。
        messages_dict: 包含messages_zh_CN.properties内容的字典。
    """

    with open(messages_file, "w", encoding="utf-8") as f:
        for key, value in messages_dict.items():
            f.write(f"{key}={value}\n")

# 示例用法：
package_path = "com.itla.imh.common.util"  # I18nAutoTextProcessorUtil 工具所在的包路径

folder_path = "./"  # 处理当前工程下的所有 .java 文件, 注意换成你的实际项目路径
processing_hardcoded_words(folder_path)