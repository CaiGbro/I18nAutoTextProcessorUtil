package com.itla.imh.common.util;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.springframework.context.i18n.LocaleContextHolder;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 *
 * 工具类用来解决传统 i18n 解决多语言切换过程中的一系列不能自动化的问题，例如
 * 1.不能自动从代码中提取需要进行多语言转换的词句，并且需手动在需要多语言处理的的词句植入中从资源文件中获取翻译的代码
 * 2.对于程序在运行过程中产生的动动态的需要多语言处理的词句，不能实现自动化收集，例如前端用户自己输入的自定义内容、
 * 外部程序产生的内容、数据库本身更新的内容等等

 * 本方法的思路和方法：
 * 1.在数据返回给前端的最后一个环节进行处理，实现多语言切换和新词句收集，这样可以覆盖到所有可能的多语言数据，也方便处理
 * 一是用 translate 方法在所有控制类的 return 处对返回给前端的对象进行多语言处理。它将对象转为 JsonNode 形式的树形 json数据结构 ，
 * 再递归处理遍历所有属性的值，在遍历的过程中通过 getMessage 方法由属性值从翻译资源里获取对应的翻译内容进行替换。
 * 二用 extractAndWrite 方法对所有可能进行翻译的词句进行收集，处理过程和 translate 类似。
 * 2.使用 process_controllers.py 方法将 translate和 extractAndWrite 自动集成到正确的位置
 * 3.使用processing_hardcoded_words.py方法实现对所有硬编码的词句进行自动收集，并自动植入中从资源文件中获取翻译的代码。

 *难点在于：
 * 1.要用 process_controllers.py 方法将 translate和 extractAndWrite集成到对应的位置，但是 return 所包含的代码结构可能多种多样，
 * 难在总结为一个覆盖所有可能的结构，以实现精确找到对应的对象并用这两个方法对其正确嵌入。（
 * 例如，有些 return只有一行但有些return具有多行，有些return包含多个需要处理的元素，但有的只包含一个或不包含需要处理的元素，
 * 有些元素是一个变量、有的元素是一个方法调用的结果甚至是多重调用的结果，有些元素不能作为提取的目标等等）
 * 2.在用 getMessage 从资源文件获取翻译词句的时候，对什么样的内容进行提取、提取后如何保证在翻译时键名相同且格式正确，还需要区别硬编码和动态词句，
 * 因为前者有.messages后缀，而后者需要正确附加这个后缀，对于不在资源文件里的内容应该原样返回等。
 * 3.在使用 processing_hardcoded_words 进行对硬编码词句的处理时，需要进行处理的词句结构复杂，同样是中文，有些是注释内容、有些是注解内容，
 * 有些是不能更改的常量、有些内容是仅支持中文的，例如它只写死了以某个中文为键进行调用，改成英文就调用不了。
 *
 * 作者：
 * CaiGbro
 */
public class I18nAutoTextProcessorUtil {

    private static final ObjectMapper objectMapper = new ObjectMapper();
    private static final String OUTPUT_FILE = "提取数据库词句.txt";
    private static final Pattern EXTRACT_PATTERN = Pattern.compile("[0-9a-zA-Z\u4e00-\u9fa5]+");
    static {
        objectMapper.configure(SerializationFeature.FAIL_ON_EMPTY_BEANS, false);
    }

    //region 1. translate
    /**
     *
     * 来自Gemini1206的力量（对这些代码的解释，完全符合我的逻辑，基本采纳）
     *
     * 这段代码定义了一个名为 translate 的泛型静态方法，其主要功能是将一个对象（data）中所有文本类型的属性值翻译成目标语言
     * （通过 LocaleContextHolder 获取当前语言环境），并返回一个翻译后的新对象。
     *
     */


    /**
     *泛型 T: 表示该方法可以处理任何类型的对象。
     * 输入参数 T data: 要翻译的对象。
     * 返回值 T: 翻译后的对象，类型与输入对象相同。
     * 核心逻辑:
     * 对象转 JsonNode: 使用 objectMapper.valueToTree(data) 将输入对象 data 转换成 Jackson 库的 JsonNode 对象。
     * JsonNode 可以表示 JSON 数据的树形结构。
     * 递归翻译: 调用 translatePropertiesRecursive(rootNode) 方法递归地遍历 JsonNode 的所有节点，并进行翻译。
     * JsonNode 转回对象: 使用 objectMapper.treeToValue(translatedNode, (Class<T>) data.getClass())
     * 将翻译后的 JsonNode 转换回原始的对象类型。
     * 异常处理: 使用 try-catch 块捕获可能发生的异常（例如，对象转换失败），并在发生异常时打印错误信息并返回原始的 data 对象，避免程序崩溃。
     *
     */
    public static <T> T translate(T data) {
        try {
            // Convert the object to a JsonNode
            JsonNode rootNode = objectMapper.valueToTree(data);

            // Translate the properties recursively
            JsonNode translatedNode = translatePropertiesRecursive(rootNode);

            // Convert the translated JsonNode back to the original object type
            return objectMapper.treeToValue(translatedNode, (Class<T>) data.getClass());
        } catch (Exception e) {
            System.err.println("Error translating properties: " + e.getMessage());
            return data; // Return original data on error
        }
    }


    /**
     *输入参数 String key: 要翻译的文本键值（key）。
     * 返回值 String: 翻译后的文本值，如果找不到对应的翻译，则返回原始的 key。
     * 核心逻辑:
     * 获取语言环境: 使用 LocaleContextHolder.getLocale() 获取当前的语言环境（Locale）。
     * 加载资源文件: 使用 ResourceBundle.getBundle("messages.messages", locale)
     * 根据当前的语言环境加载对应的资源文件 messages.properties。
     * 假设资源文件位于 messages 目录下，例如 messages_zh_CN.properties、messages_en_US.properties 等。
     * Key 的处理:
     * 如果 key 以 .message 结尾，则去除其中的空格和特殊字符，然后直接从资源文件中获取翻译。
     * 否则判断 key 如果包含中文字符，则使用正则表达式提取中英文数字字符，并在其后面添加 ".message" 后缀，
     * 然后再从资源文件中获取翻译，如果获取不到返回原始的key。
     * 如果上面的判断都不成立，直接返回原始的 key。
     * 获取翻译: 使用 bundle.getString(key) 根据处理后的 key 从资源文件中获取对应的翻译值。
     * 异常处理: 使用 try-catch 块捕获 MissingResourceException 异常，该异常表示找不到对应的资源文件或键值。
     * 如果发生异常，直接返回原始的 key。
     */
    public static String getMessage(String key) {
        try {
            Locale locale = LocaleContextHolder.getLocale();
//            System.out.println(locale.toString());
            ResourceBundle bundle = ResourceBundle.getBundle("messages.messages", locale);
            // 对 key 进行处理，去除空格和特殊字符
            if (key.endsWith(".message")) {
                return bundle.getString(key.replaceAll("\\s+", ""));
            }else if(containsChinese(key)){
                String new_key = extractAlphanumericAndChinese(key);
                new_key += ".message";
                return bundle.getString(new_key);
            } else  {
                return key;
            }

        } catch (MissingResourceException e) {
            return key;
        }
    }

    /**
     *输入参数 JsonNode node: 要处理的 JsonNode 节点。
     * 返回值 JsonNode: 处理后的 JsonNode 节点。
     * 核心逻辑:
     * 对象节点 (ObjectNode):
     * 遍历对象的所有字段。
     * 如果字段名不是 "id"、"parentId" 或 "delFlag"，则递归调用 translatePropertiesRecursive 方法处理字段值。
     * 将处理后的字段值设置回对象节点。

     * 数组节点 (ArrayNode):
     * 遍历数组的所有元素。
     * 递归调用 translatePropertiesRecursive 方法处理每个元素。
     * 将处理后的元素设置回数组节点。

     * 文本节点 (Textual):
     * 使用 node.asText() 获取文本值。
     * 调用 getMessage(textValue) 方法翻译文本值。
     * 使用 objectMapper.valueToTree(translatedText) 将翻译后的文本值转换成 JsonNode。

     * 其他节点:
     * 直接返回原始节点。
     */
    private static JsonNode translatePropertiesRecursive(JsonNode node) {
        if (node.isObject()) {
            ObjectNode objectNode = (ObjectNode) node;
            Iterator<Map.Entry<String, JsonNode>> fields = objectNode.fields();
            while (fields.hasNext()) {
                Map.Entry<String, JsonNode> field = fields.next();
                String fieldName = field.getKey();

                JsonNode fieldValue = field.getValue();

                // Ignore specific field names
                if (!fieldName.equals("id") && !fieldName.equals("parentId") && !fieldName.equals("delFlag")) {
                    JsonNode translatedValue = translatePropertiesRecursive(fieldValue);
                    objectNode.set(fieldName, translatedValue);
                }
            }
            return objectNode;
        } else if (node.isArray()) {
            ArrayNode arrayNode = (ArrayNode) node;
            for (int i = 0; i < arrayNode.size(); i++) {
                JsonNode element = arrayNode.get(i);
                JsonNode translatedElement = translatePropertiesRecursive(element);
                arrayNode.set(i, translatedElement);
            }
            return arrayNode;
        } else if (node.isTextual()) {
            // Translate the text value using getMessage
            String textValue = node.asText();
            String translatedText = getMessage(textValue );
//            System.out.println(translatedText);
            return objectMapper.valueToTree(translatedText);
        } else {
            // Return the node as is if it's not an object, array, or text
            return node;
        }
    }

    //endregion

    //region 2. extractAndWrite
    /**
     * 将任意类属性值包含中文内容的词句进行提取，用于收集前端或数据库等在运行时动态产生的词句
     */

    /**
     * 输入参数 Object data: 要处理的对象。
     * 返回值 void: 无返回值。
     * 核心逻辑:
     * 对象转 JSON 字符串: 使用 objectMapper.writeValueAsString(data) 将输入对象 data 转换成 JSON 字符串。
     * JSON 字符串转 JsonNode: 使用 objectMapper.readTree(jsonString) 将 JSON 字符串解析成 JsonNode 对象。
     * 递归提取和写入: 调用 extractAndWriteRecursive(rootNode) 方法递归地遍历 JsonNode 的所有节点，
     * 提取包含中文字符的文本值，并将其写入文件。
     * 异常处理: 使用 try-catch 块捕获可能发生的异常，并在发生异常时打印错误信息。
     */
    public static void extractAndWrite(Object data) {
        try {
            // Convert the object to a JSON string
            String jsonString = objectMapper.writeValueAsString(data);

            // Parse the JSON string to a JsonNode
            JsonNode rootNode = objectMapper.readTree(jsonString);

            // Extract and write the properties recursively
            extractAndWriteRecursive(rootNode);
        } catch (Exception e) {
            System.err.println("Error extracting and writing properties: " + e.getMessage());
        }
    }

    /**
     * 输入参数 JsonNode node: 要处理的 JsonNode 节点。
     * 返回值 void: 无返回值。
     * 核心逻辑:
     * 对象节点 (ObjectNode): 遍历对象的所有字段，递归调用 extractAndWriteRecursive 处理每个字段值。
     * 数组节点 (ArrayNode): 遍历数组的所有元素，递归调用 extractAndWriteRecursive 处理每个元素。
     * 文本节点 (Textual):
     * 使用 node.asText() 获取文本值。
     * 调用 containsChinese(textValue) 判断文本值是否包含中文字符。
     * 如果包含中文字符，则调用 extractAlphanumericAndChinese(textValue) 提取文本中的字母、数字和中文字符。
     * 调用 writeIfUnique(processedValue, textValue) 将处理后的值和原始值写入文件，确保唯一性。
     * 异常处理: 使用 throws IOException 声明可能会抛出 IOException 异常。
     */
    private static void extractAndWriteRecursive(JsonNode node) throws IOException {
        if (node.isObject()) {
            Iterator<Map.Entry<String, JsonNode>> fields = node.fields();
            while (fields.hasNext()) {
                Map.Entry<String, JsonNode> field = fields.next();
                JsonNode fieldValue = field.getValue();
                extractAndWriteRecursive(fieldValue);
            }
        } else if (node.isArray()) {
            for (JsonNode element : node) {
                extractAndWriteRecursive(element);
            }
        } else if (node.isTextual()) {
            String textValue = node.asText();
            if (containsChinese(textValue)) {
                String processedValue = extractAlphanumericAndChinese(textValue);
                writeIfUnique(processedValue, textValue);
            }
        }
    }

    private static boolean containsChinese(String text) {
        return text.codePoints().anyMatch(c -> c >= 0x4e00 && c <= 0x9fa5);
    }

    private static String extractAlphanumericAndChinese(String text) {
        Matcher matcher = EXTRACT_PATTERN.matcher(text);
        StringBuilder sb = new StringBuilder();
        while (matcher.find()) {
            sb.append(matcher.group());
        }
        return sb.toString();
    }

    /**
     * 输入参数 String processedValue: 处理后的值（提取了字母、数字和中文字符）。
     * 输入参数 String originalValue: 原始的文本值。
     * 返回值 void: 无返回值。
     * 核心逻辑:
     * 构建 key：将 processedValue 后面加上 ".message" 作为键值。
     * 读取文件内容：
     * 如果输出文件 OUTPUT_FILE 存在，则读取文件的所有行到 lines 列表中。
     * 构建现有键值对的映射：
     * 遍历 lines 列表，将每一行按 "=" 分割成键和值，存储到 existingEntries 的 HashMap 中。
     * 检查键值对是否已存在：
     * 如果 existingEntries 中不存在 key，或者 key 对应的值与 originalValue 不同，则将 key 和 originalValue 写入文件。
     * 写入文件：
     * 使用 FileWriter 以追加模式打开 OUTPUT_FILE。
     * 写入 key + "=" + originalValue + System.lineSeparator() 到文件。
     * 关闭 FileWriter。
     * 异常处理: 使用 throws IOException 声明可能会抛出 IOException 异常。
     */
    private static void writeIfUnique(String processedValue, String originalValue) throws IOException {
        String key = processedValue + ".message";
        List<String> lines = new ArrayList<>();

        File outputFile = new File(OUTPUT_FILE);
        if (outputFile.exists()) {
            lines = Files.readAllLines(Paths.get(OUTPUT_FILE), StandardCharsets.UTF_8);
        }

        Map<String, String> existingEntries = new HashMap<>();
        for (String line : lines) {
            if (line.contains("=")) {
                String[] parts = line.split("=", 2);
                existingEntries.put(parts[0], parts[1]);
            }
        }

        if (!existingEntries.containsKey(key) || !existingEntries.get(key).equals(originalValue)) {
            // 使用 OutputStreamWriter 指定 UTF-8 编码
            OutputStreamWriter writer = new OutputStreamWriter(new FileOutputStream(outputFile, true), StandardCharsets.UTF_8);
            writer.write(key + "=" + originalValue + System.lineSeparator());
            writer.close();
        }
    }

    //endregion


    public static void main(String[] args) throws IOException {
        String folderPath = "./"; // 将此路径替换为你的项目文件夹路径

//      该工具类配合 process_controllers.py 和 processing_hardcoded_words.py使用

//      1.先运行process_controllers.py，作用是将控制器方法中的返回值用 I18nAutoTextProcessorUtil.translate() 方法进行包裹，
//      以实现返回值的自动翻译，同时利用 I18nAutoTextProcessorUtil.extractAndWrite() 方法提取返回值中可能包含的中文文本，以便进行国际化。
//      2.再运行 processing_hardcoded_words.py，作用是将硬编码内容提取出来，并用getMessage()方法进行包裹，
//      以实现对硬编码词句的自动翻译
//      3.代码运行后会自动收集词句的文件，可用find_new_content.py将这个文件相对于现有资源文件新的内容提取出来，以更新旧有资源

//      为什么不将这两个python根据集成到这个类里：
//      我一开始就是准备这么干的，但后来我发现，在使用AI模型编写这些代码的时候，用 java 语言总是写不对，甚至一些简单的错误反复踏步不能解决
//      更有甚者即让它们使用正确的python转换为java代码居然也出现些简单的错误反复踏步不能解决的问题
//      或许python在数据处理上具有先天大优势吧，所以我没有将这两个方法集成到这个工具类里了

    }
}
