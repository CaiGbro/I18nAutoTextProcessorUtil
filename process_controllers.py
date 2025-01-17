import os
import re

def process_java_files(directory):
    """
    遍历指定目录下的所有 .java 文件，并根据规则修改 Controller 文件。
    主要目的是将控制器方法中的返回值用 I18nAutoTextProcessorUtil.translate() 方法进行包裹，
    实现返回值的自动翻译，同时利用 I18nAutoTextProcessorUtil.extractAndWrite() 方法提取返回值中可能包含的中文文本，以便进行国际化。


    思路如下：
    遍历所有以.java结尾的文件（文件的编码格式统一为utf-8），对于所有以Controller结尾的文件，遍历文件的每一行内容，
    对于包括注释符号//的行不处理
    如果某行存在package则在它的下一行插入
    import com.itla.imh.common.util.I18nAutoTextProcessorUtil;（防止出现因不自动导包而报错）
    如果某行出现return则将离return最近的(与离下一个;最近的)之间的内容以,为标志依次进行提取，
    例如(aaa)被提取为aaa例如fasf(asf,fasf)被提取为asf和fasf
    提取后的内容用规则R进行过滤，
    如果提取的内容不为空，设经过规则R过滤后的内容为A、B等等，在其return所在行的上一行以同样的缩进插入
    I18nAutoTextProcessorUtil.extractAndWrite(A);
    I18nAutoTextProcessorUtil.extractAndWrite(B)；
    等等。
    并在对应的A、B等处换成I18nAutoTextProcessorUtil.translate(A)、I18nAutoTextProcessorUtil.translate(B)等等

    规则R：
    去掉所提取内容的空格或换行等------------------------------------（防止return在跨多行的情况下出现错误）
    对于提取的内容符合以下条件才进行保留：
    1.不包含英文双引号--------------------------------------------- (这是硬编码内容，由processing_hardcoded_words.py进行处理）
    2.必须存在小写字母，如果存在大写字母则需要同时存在小写字母--------- (仅对变量做处理，防止出现怪问题）
    3.参数不包含 “->” 符号----------------------------------------- (extractAndWrite不接受lamda表达式）


    Args:
        directory: 要遍历的目录路径。
    """

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".java"):
                filepath = os.path.join(root, file)
                process_java_file(filepath)

def process_java_file(filepath):
    """
    处理单个 .java 文件，根据规则修改 Controller 文件。

    Args:
        filepath: 要处理的 .java 文件路径。
    """

    print(f"Processing file: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if not is_controller_file(lines):
        return

    modified_lines = []
    package_line_found = False
    for i, line in enumerate(lines):
        if line.strip().startswith("//"):
            modified_lines.append(line)
            continue

        if "package " in line and not package_line_found:
            modified_lines.append(line)
            # modified_lines.append("import com.itla.imh.common.util.I18nAutoTextProcessorUtil;\n")
            package_line_found = True
        elif "return " in line:
            extracted_values = extract_values_from_return(line)
            filtered_values = []
            translate_only_values = []
            for value in extracted_values:
                if rule_r(value):
                    if "->" in value:
                        translate_only_values.append(value)
                    else:
                        filtered_values.append(value)
                

            if filtered_values:
                indent = get_indentation(line)
                insert_lines = [
                    f"{indent}I18nAutoTextProcessorUtil.extractAndWrite({value});\n"
                    for value in filtered_values
                ]
                modified_lines.extend(insert_lines)

            # Replace extracted values with I18nAutoTextProcessorUtil.translate()
            modified_return_line = replace_with_translate(line, filtered_values + translate_only_values)
            modified_lines.append(modified_return_line)
        else:
            modified_lines.append(line)

    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(modified_lines)

def is_controller_file(lines):
    """
    判断是否是 Controller 文件。

    Args:
        lines: 文件内容行列表。

    Returns:
        如果是 Controller 文件返回 True，否则返回 False。
    """
    for line in lines:
        if "Controller" in line:
            return True
    return False

def extract_values_from_return(line):
    """
    从 return 语句中提取括号内的值。

    Args:
        line: 包含 return 语句的行。

    Returns:
        提取的值列表。
    """
    match = re.search(r"return .*?\((.*?)\);", line)
    if match:
        content = match.group(1)
        # Find the nearest ( to the return, and the nearest ) to the next ;
        start_index = line.find('return') + len('return')
        first_open_paren = line.find('(', start_index)

        last_close_paren = -1
        next_semicolon = line.find(';', start_index)

        if next_semicolon != -1:
            
            open_count = 0
            for i in range(first_open_paren, next_semicolon):
                if line[i] == '(':
                    open_count += 1
                elif line[i] == ')':
                    open_count -= 1
                    if open_count == 0:
                        last_close_paren = i
                        break

        if last_close_paren != -1:
            content = line[first_open_paren+1: last_close_paren]
        else:
            content = match.group(1)

        
        
        parts = content.split(",")

        
        values = []
        current_value = ""
        paren_count = 0
        for part in parts:
            
            for char in part:
                if char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1
                current_value += char
            
            if paren_count == 0:
                values.append(current_value.strip())
                current_value = ""
            else:
                current_value += ","

        return values

    return []

def rule_r(value):
    """
    规则 R：过滤提取的值。

    Args:
        value: 要过滤的值。

    Returns:
        如果符合规则返回 True，否则返回 False。
    """
    value = value.strip()
    if not value:
        return False
    if '"' in value:
        return False
    has_uppercase = any(c.isupper() for c in value)
    has_lowercase = any(c.islower() for c in value)
    return not has_uppercase or (has_uppercase and has_lowercase)

def get_indentation(line):
    """
    获取行的缩进。

    Args:
        line: 要获取缩进的行。

    Returns:
        行的缩进字符串。
    """
    return line[: len(line) - len(line.lstrip())]

def replace_with_translate(line, values):
    """
    将提取的值替换为 I18nAutoTextProcessorUtil.translate()。

    Args:
        line: 包含 return 语句的行。
        values: 要替换的值列表。

    Returns:
        替换后的行。
    """
    return_index = line.find("return")
    if return_index == -1:
        return line

    open_paren_index = line.find("(", return_index)
    if open_paren_index == -1:
        return line

    # Find matching closing parenthesis
    close_paren_index = -1
    paren_count = 1
    for i in range(open_paren_index + 1, len(line)):
        if line[i] == '(':
            paren_count += 1
        elif line[i] == ')':
            paren_count -= 1
        if paren_count == 0:
            close_paren_index = i
            break

    if close_paren_index == -1:
        return line

    # Replace values within the parentheses
    before_paren = line[:open_paren_index + 1]
    within_paren = line[open_paren_index + 1:close_paren_index]
    after_paren = line[close_paren_index:]
    
    
    replace_history = set()

    for value in values:
        new_within_paren = ""
        index = 0
        
        while index < len(within_paren):
            found_index = within_paren.find(value, index)
            
            if found_index == -1:
                new_within_paren += within_paren[index:]
                break
            
            
            
            can_replace = True
            for start, end in replace_history:
                if start <= found_index <= end:
                    can_replace = False
                    break
            
            if can_replace:
                new_within_paren += within_paren[index:found_index]
                new_within_paren += f"I18nAutoTextProcessorUtil.translate({value})"
                replace_history.add((found_index, found_index + len(f"I18nAutoTextProcessorUtil.translate({value})")))
                index = found_index + len(value)
            else:
                new_within_paren += within_paren[index: found_index + len(value)]
                index = found_index + len(value)
                
        within_paren = new_within_paren
    

    return before_paren + within_paren + after_paren

# 示例用法
process_java_files("./")  # 处理当前工程下的所有 .java 文件, 注意换成你的实际项目路径