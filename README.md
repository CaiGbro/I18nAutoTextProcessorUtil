# I18nAutoTextProcessorUtil: Java 项目自动国际化工具

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

## 简介

`I18nAutoTextProcessorUtil` 是一个便捷的 基于i18n的Java工具类，旨在解决传统 i18n 方案在多语言切换过程中无法自动化处理的问题，并支持针对动态内容的国际化支持。它可以自动提取java代码里需要进行多语言转换的中文词句，并将它们集成到资源文件中，无需手动查找和植入代码，同时支持在运行时动态收集需要翻译的文本。

## 背景

在开发多语言支持的 Java 应用程序时，传统的 i18n 方案有以下痛点：

1. **手动提取和植入代码的繁琐性**：
   - 开发人员需要手动识别代码中需要进行多语言处理的文本内容，然后手动将这些文本与资源文件中的翻译条目进行关联，并在代码中插入相应的资源文件查找代码。此过程不仅费时，而且容易出现人为错误，导致代码的可维护性降低。
   - 对于大型项目或复杂代码库，手动操作难以确保全面覆盖，可能会遗漏一些需要翻译的文本，影响多语言用户体验。

2. **动态内容处理的难题**：
   - 程序在运行过程中会产生各种动态内容，如用户输入、从外部 API 获取的数据、数据库存储的信息或其他动态生成的文本。传统 i18n 方法很难对这些动态内容进行自动化的语言转换处理，限制了应用程序的多语言适应性。

## 优势

`I18nAutoTextProcessorUtil` 通过以下方式解决了上述痛点：

1. **自动化处理：** 在数据返回给前端的最后环节进行处理，实现多语言切换和新词句收集，覆盖所有可能的多语言数据。
    - `translate()` 方法：自动翻译对象中的文本属性。
    - `extractAndWrite()` 方法：自动收集需要翻译的文本。
2. **配套脚本，简化集成：**
    - `process_controllers.py`：自动将 `translate()` 和 `extractAndWrite()` 方法集成到 Spring MVC 控制器的返回值中。
    - `processing_hardcoded_words.py`：自动提取 Java 代码中的硬编码文本，并替换为从资源文件获取翻译的代码。
    - `find_new_content.py`：对比提取的文本和现有的资源文件，找出需要更新的词句。
3. **灵活的文本处理：** 可以处理各种类型的文本，包括硬编码文本、动态生成的文本以及对象中的属性值。
4. **易于使用：** 只需要简单的几步配置，即可将工具类集成到项目中。
5. **处理复杂场景：** 考虑了各种复杂的代码结构和场景，例如多层嵌套的对象、不同的返回类型等。

## 解决方案

`I18nAutoTextProcessorUtil` 通过以下创新的方式解决了上述问题：

1. **在数据返回前端的最后环节进行处理**：
    - `translate` 方法是核心功能之一，它在控制器将数据返回给前端之前发挥作用。
    - **原理**：
        1. 首先，将传入的对象转换为 `JsonNode` 树形结构，利用 Jackson 库的强大功能，将对象表示为一种便于遍历和操作的树形 JSON 结构。
        2. 接着，递归遍历这个 `JsonNode` 的每个节点，对其中的文本类型节点进行翻译操作。
        3. 最后，将翻译后的 `JsonNode` 转换回原始对象的类型，确保返回的数据类型与输入一致。
    - **使用示例**：
    假设我们有一个 `Product` 类：
    ```java
    public class Product {
        private Long id;
        private String name;
        private String description;
        // ... 省略getter和setter ...
    }
    ```

    我们的控制器中有一个方法返回 `Product` 对象：

    ```java
    @GetMapping("/product/{id}")
    public Product getProduct(@PathVariable Long id) {
        Product product = productService.getProductById(id);
        product.setName("产品名称");
        product.setDescription("这是一个产品描述");
        return product;
    }
    ```
    集成 `I18nAutoTextProcessorUtil` 后，代码变为：

    ```java
    @GetMapping("/product/{id}")
    public Product getProduct(@PathVariable Long id) {
        Product product = productService.getProductById(id);
        product.setName("产品名称");
        product.setDescription("这是一个产品描述");
        I18nAutoTextProcessorUtil.extractAndWrite(product); // 收集动态文本
        return I18nAutoTextProcessorUtil.translate(product); // 翻译后返回
    }
    ```

    - 这种方法确保了在数据输出的最后一道关卡，对所有可能的文本内容进行多语言处理，保证了多语言支持的完整性。

2. **自动化集成**：
    - 配合 `process_controllers.py` 脚本，将 `translate` 和 `extractAndWrite` 方法无缝集成到控制器代码中。
    - **原理**：
        1. 该脚本会遍历指定目录下的所有 `.java` 文件，查找包含 `Controller` 关键字的类。
        2. 对于每个控制器类，解析其方法中的 `return` 语句。
        3. 智能识别需要处理的对象，通过排除硬编码字符串、lambda 表达式等元素，确保只处理合适的数据。
        4. 在 `return` 语句之前插入 `extractAndWrite` 调用，以收集需要翻译的文本，然后将 `return` 语句中的对象用 `translate` 方法包裹，确保输出数据的语言转换。
    - **使用示例**：
    假设你的项目目录是 `/Users/yourname/myproject`，你只需在命令行中执行：

    ```bash
    python process_controllers.py /Users/yourname/myproject
    ```

    执行后，控制器中返回 `Product` 的方法会自动变为类似上面的示例。

    ​		或者直接进python编辑器，把方法的参数改为项目的根路径，然后右键run即可。
    
3. **硬编码文本处理**：
    - 借助 `processing_hardcoded_words.py` 脚本，自动收集代码中的硬编码文本并替换为 `getMessage` 调用。
    - **原理**：
        1. 遍历项目中的所有 `.java` 文件。
        2. 仔细识别硬编码的中文字符串，同时排除一些不应该被处理的部分，如日志信息、注解、常量等。
        3. 对于提取的硬编码字符串，提取其中的中文字符和字母数字，生成唯一的键值，例如将提取的文本添加 `.message` 后缀。
        4. 将硬编码字符串替换为 `I18nAutoTextProcessorUtil.getMessage("生成的键值")`，并将生成的键值和原始文本添加到 `messages_zh_CN.properties` 文件中。
    - **使用示例**：

    假设你的项目中有一个工具类 `StringUtil`，其中有一个方法包含硬编码中文：

    ```java
    public class StringUtil {
        public static String getWelcomeMessage() {
            return "欢迎使用本系统！";
        }
    }
    ```

    执行脚本（假设项目目录为 `/Users/yourname/myproject`）：

    ```bash
    python processing_hardcoded_words.py /Users/yourname/myproject
    ```

    或者直接进python编辑器，把方法的参数改为你的实际参数，然后右键run即可。

    执行后，`StringUtil` 类会变为：
    
    ```java
    public class StringUtil {
        public static String getWelcomeMessage() {
            return I18nAutoTextProcessorUtil.getMessage("欢迎使用本系统.message");
        }
}
    ```

    同时，`messages_zh_CN.properties` 文件中会新增一行：
    
    ```properties
    欢迎使用本系统.message=欢迎使用本系统！
    ```

## 核心功能

### 1. `translate` 方法

-   **功能**：将对象中所有文本类型的属性值翻译成目标语言，确保在将数据返回给前端时，用户看到的是根据其语言偏好翻译好的文本内容。
-   **输入参数**：
    
    -   `data`：需要进行翻译的对象，可以是任何 Java 对象，通常是控制器方法返回的数据对象。
-   **输出结果**：
    
    -   与输入对象类型相同，但其中文本类型的属性值已根据当前语言环境进行翻译。
-   **示例**：
    假设有一个 `Order` 类：

    ```java
    public class Order {
        private Long id;
        private String orderNumber;
        private String status;
    
        // 构造方法、Getter 和 Setter 方法
        public Order(Long id, String orderNumber, String status) {
            this.id = id;
            this.orderNumber = orderNumber;
            this.status = status;
        }
    
        // ...省略了Getter 和 Setter 方法...
    }
    ```

    控制器中返回 `Order` 对象：

    ```java
    @GetMapping("/order/{id}")
    public Order getOrder(@PathVariable Long id) {
        Order order = new Order(1L, "20231026001", "待支付");
        return I18nAutoTextProcessorUtil.translate(order);
    }
    ```

    如果当前语言环境是英文 (en_US)，且 `messages_en_US.properties` 中有以下内容：

    ```properties
    待支付.message=Pending Payment
    ```

    那么返回给前端的 `Order` 对象的 `status` 属性值将被翻译成 "Pending Payment"。

### 2. `extractAndWrite` 方法

-   **功能**：提取对象中可能需要翻译的文本，特别是那些包含中文的文本，将它们写入文件，为生成或更新国际化资源文件提供便利。
-   **输入参数**：
    
    -   `data`：需要提取文本的对象，通常是控制器方法返回的数据对象。
-   **操作过程**：
    1. 将对象转换为 JSON 字符串，利用 Jackson 库的序列化功能。
    2. 将 JSON 字符串解析为 `JsonNode` 树形结构。
    3. 递归遍历 `JsonNode`，提取包含中文字符的文本值。
    4. 将提取的文本及其生成的键值写入指定文件（默认为 `提取数据库词句.txt`），为后续手动翻译提供基础。
-   **示例**：

    假设有一个 `User` 类：

    ```java
    public class User {
        private Long id;
        private String username;
        private String nickname;
        // ...省略了Getter 和 Setter 方法...
    }
    ```

    控制器中返回 `User` 对象：

    ```java
    @PostMapping("/user")
    public User createUser(@RequestBody User user) {
        user.setNickname("测试用户");
        I18nAutoTextProcessorUtil.extractAndWrite(user);
        return user;
    }
    ```
    执行后，`提取数据库词句.txt` 文件中会添加一行（假设用户输入的用户名为 `testuser`）：
    ```
    测试用户.message=测试用户
    ```

### 3. `getMessage` 方法

- **功能**：根据键值从资源文件中获取对应的翻译文本，确保在代码中使用资源文件中的翻译内容，而不是硬编码的文本。

-   **输入参数**：
    
    -   `key`：要查找的翻译键值，通常是一个字符串，如 `"这是一个需要翻译的文本.message"`。
    
-   **操作过程**：
    1. 根据当前语言环境（通过 `LocaleContextHolder.getLocale()` 获取）加载相应的资源文件。
    2. 对键值进行处理，例如去除空格、特殊字符，并添加 `.message` 后缀等，以确保与资源文件中的键值匹配。
    3. 从资源文件中查找相应的翻译，如果找不到，将返回原始键值。
    
-   **使用示例**：

    假设在你的代码中，有一处需要返回错误信息：

    ```java
    if (someCondition) {
        throw new RuntimeException("操作失败，请重试！");
    }
    ```

    使用 `getMessage` 方法后，代码变为：

    ```java
    if (someCondition) {
        throw new RuntimeException(I18nAutoTextProcessorUtil.getMessage("操作失败请重试.message"));
    }
    ```
    同时，在 `messages_zh_CN.properties` 文件中添加：
    ```properties
    操作失败请重试.message=操作失败，请重试！
    ```

## 配套脚本

### 1. `process_controllers.py`

-   **功能：** 自动将 `I18nAutoTextProcessorUtil.translate()` 和 `I18nAutoTextProcessorUtil.extractAndWrite()` 方法集成到 Spring MVC 控制器的返回值中。
-   **使用方法：** 将脚本放在项目根目录下，然后执行 `python process_controllers.py`。
-   **输入参数**：
    
    -   `<项目目录>`：需要扫描和修改的 Java 项目目录。
-   **工作流程**：
    1. 遍历指定目录下的所有 `.java` 文件。
    2. 对类名中包含 `Controller` 的文件进行解析。
    3. 找出方法中的 `return` 语句，提取需要处理的对象。
    4. 根据内置规则过滤提取的对象，确保只对合适的对象进行处理。
    5. 在 `return` 语句之前插入 `extractAndWrite` 调用，并将 `return` 语句中的对象用 `translate` 方法包裹。
-   **示例**：
    假设你的 Spring MVC 控制器类中有一个方法：

    ```java
    @GetMapping("/greeting")
    public String sayHello() {
        String greeting = "大家好！";
        return greeting;
    }
    ```
```
    
运行 `process_controllers.py` 脚本后，该方法会被修改为：
    
    ```java
    @GetMapping("/greeting")
    public String sayHello() {
        String greeting = "大家好！";
        I18nAutoTextProcessorUtil.extractAndWrite(greeting);
        return I18nAutoTextProcessorUtil.translate(greeting);
    }
```

### 2. `processing_hardcoded_words.py`

-   **功能**：自动收集代码中的硬编码文本，将其替换为 `getMessage` 调用，并将提取的文本添加到 `messages_zh_CN.properties` 文件。
-   **输入参数**：
    
    -   `<项目目录>`：需要扫描和修改的 Java 项目目录。
-   **工作流程**：
    1. 遍历指定目录下的所有 `.java` 文件。
    2. 识别硬编码字符串，排除不相关的部分，如日志、注解、常量等。
    3. 提取硬编码字符串中的中文字符和字母数字，生成唯一的键值。
    4. 将硬编码字符串替换为 `I18nAutoTextProcessorUtil.getMessage("生成的键值")`。
    5. 将键值和原始文本添加到 `messages_zh_CN.properties` 文件。
-   **示例**：

    假设你的代码中有一处硬编码的错误提示：

    ```java
    if (!isValid) {
        System.out.println("输入的数据无效！");
    }
    ```

    运行 `processing_hardcoded_words.py` 脚本后，该代码会被修改为：

    ```java
    if (!isValid) {
        System.out.println(I18nAutoTextProcessorUtil.getMessage("输入的数据无效.message"));
    }
    ```

    同时，`messages_zh_CN.properties` 文件中会添加：

    ```properties
    输入的数据无效.message=输入的数据无效！
    ```

### 3. `find_new_content.py`

-   **功能**：找出 `extractAndWrite` 方法提取的文本文件中，哪些内容在 `messages_zh_CN.properties` 文件中尚未存在。
-   **输入参数**：
    -   `<提取的文本文件>`：`extractAndWrite` 方法生成的文本文件，如 `提取数据库词句.txt`。
    -   `<messages_zh_CN.properties>`：现有的中文资源文件。
    -   `<输出文件>`：存储新发现的需要翻译的词句的文件，例如 `新发现的词句.properties`。
-   **工作流程**：
    1. 读取 `extractAndWrite` 方法生成的文本文件和现有的 `messages_zh_CN.properties` 文件。
    2. 比较两个文件的内容，找出在前者中出现但不在后者中的行。
    3. 将这些新内容写入指定的输出文件。
-   **示例**：

    假设 `extractAndWrite` 方法生成的 `提取数据库词句.txt` 文件内容如下：

    ```
    新用户注册成功.message=新用户注册成功
    订单已创建.message=订单已创建
    产品名称.message=产品名称
    ```

    `messages_zh_CN.properties` 文件内容如下：

    ```properties
    订单已创建.message=订单已创建
    ```

    运行 `find_new_content.py` 脚本：

    ```bash
    python find_new_content.py 提取数据库词句.txt messages_zh_CN.properties 新发现的词句.properties
    ```

    生成的 `新发现的词句.properties` 文件内容如下：

    ```
    新用户注册成功.message=新用户注册成功
    产品名称.message=产品名称
    ```

## 使用步骤

1. **添加依赖**：
    -   将 `I18nAutoTextProcessorUtil.java` 文件复制到你的项目中。
    -   确保你的项目包含 Jackson 库，可通过 Maven 添加依赖：

    ```xml
    <dependency>
        <groupId>com.fasterxml.jackson.core</groupId>
        <artifactId>jackson-databind</artifactId>
        <version>2.13.3</version>
    </dependency>
    ```

2. **集成自动化脚本**：
    -   运行 `process_controllers.py` 脚本，对项目中的控制器代码进行自动修改。
    -   运行 `processing_hardcoded_words.py` 脚本，处理硬编码文本。

3. **手动翻译**：
    -   将 `extractAndWrite` 方法生成的 `提取数据库词句.txt` 文件（或 `find_new_content.py` 脚本生成的 `新发现的词句.properties` 文件）中的文本翻译成目标语言。
    -   将翻译后的内容添加到相应的资源文件中，遵循 Java 的 `ResourceBundle` 命名规范，如 `messages_en_US.properties`、`messages_zh_CN.properties` 等，将资源文件放在 `messages` 目录下。

4. **运行应用程序**：
   
    -   启动你的 Java 应用程序，`I18nAutoTextProcessorUtil` 会根据当前语言环境自动加载相应的资源文件，并将翻译后的文本返回给前端。

## 注意事项

1. **一定要备份原代码**:
    -   本方案会直接修改你的代码，但是不能保证在所有的情况下都修改正确，万一产生无法预知的错误，保留原代码可以避免损失。
2. **资源文件命名**：
    -   国际化资源文件应严格遵循 Java 的 `ResourceBundle` 命名规范，如 `messages_zh_CN.properties`、`messages_en_US.properties` 等，并放置在 `src/main/resources/messages` 目录下。
    -   确保不同语言的资源文件命名正确，以便工具能够准确加载相应的翻译内容。
3. **编码**：
    -   所有 `.java` 文件和资源文件都应使用 UTF-8 编码，以支持多语言字符集。
4. **脚本规则调整**：
    -   配套脚本中的过滤规则可能需要根据你的项目实际情况进行调整，例如不同的项目可能有不同的命名约定或代码结构，你可能需要修改脚本以更好地适应项目需求。
5. **测试和验证**：
    -   在使用本工具之后，务必对应用程序进行充分测试，确保所有文本都能正确翻译，特别是对于动态内容和复杂的数据结构，要进行各种语言环境的测试，以保证多语言支持的完整性和准确性。
6. **其它**：
    -   如果出现部分内容无法正常切换，可尝试重新在Meven里clean然后compile重试。
    -   在运行脚本时务必查看脚本代码中的注意事项，确保你项目中这个工具类实际所在的包位置和其它路径等信息设置正确。
7. **局限**：
    -   本方法适用以中文为基础的多语言处理，如果以其它语言为基础则不适用，需要根据语言特点修改提取的逻辑。
    -   作者水平有限，恐无法覆盖所有情况。

## 贡献

欢迎广大开发者提交 issue 或 pull request 来改进 `I18nAutoTextProcessorUtil`，共同推动该工具的发展和完善。

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 作者

CaiGbro

## 联系方式

如果你对该项目有任何疑问、建议或需要帮助，请通过 CaiGbro@163.com 联系我。

希望这份 README 文档能帮助你更好地理解和使用 `I18nAutoTextProcessorUtil` 工具类。请根据你的实际情况对文档中的细节进行修改和完善，以满足你的项目需求。

