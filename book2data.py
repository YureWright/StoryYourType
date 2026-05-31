import os
from openai import OpenAI
from config import API_KEY, BASE_URL, MODEL, OUTPUT_SCHEMA, EXPLAIN, EXAMPLE
import json
import log
from check_data import check_llm_output

"""
本脚本实现：
1. 从输入文件中读取小说章节内容
2. 调用OpenAI模型，将小说章节转换为JSON格式
3. 将转换后的JSON内容写入输出文件中
"""
def build_prompt(chapter_text):
    prompt = f"""你是一个小说结构化分析助手。请将以下小说章节转换为JSON格式。

输出格式必须严格遵循以下JSON Schema：
{json.dumps(OUTPUT_SCHEMA, ensure_ascii=False, indent=2)}

字段说明：\n{EXPLAIN}


要求：
1. 只输出JSON，不要包含任何其他解释或markdown标记
2. 根据内容自动识别场景(scene)和节拍(beat)
3. 每个beat是一个三元组数组：[类型, 执行者, 内容]
4. 类型只能是：dialogue（对话）、action（行为）、internal_thought（心理活动）、environment（环境变化）
5. environment类型的执行者固定为"环境"

示例输出：
{json.dumps(EXAMPLE, ensure_ascii=False, indent=2)}

小说内容：
---
{chapter_text}
---

请输出JSON："""
    return prompt


def call_llm(prompt):
    api_key = API_KEY or os.getenv("OPENAI_API_KEY")
    base_url = BASE_URL or os.getenv("OPENAI_BASE_URL")
    model = MODEL or os.getenv("LLM_MODEL", "gpt-4")
    log.run_logger.info(f"调用模型: {model}")

    if not api_key:
        log.warning_logger.error("未设置API密钥，请通过环境变量OPENAI_API_KEY或参数--api-key提供")
        raise ValueError("未设置API密钥，请通过环境变量OPENAI_API_KEY或参数--api-key提供")

    client = OpenAI(api_key=api_key, base_url=base_url)

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        log.run_logger.info(f"第 {attempt}/{max_retries} 次调用模型")
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            is_valid, msg = check_llm_output(content)
            if not is_valid:
                log.warning_logger.error(f"模型输出不符合要求: {msg}")
                if attempt == max_retries:
                    raise ValueError(f"模型输出不符合要求，已重试 {max_retries} 次: {msg}")
                continue

            log.run_logger.info(f"调用模型: {model} 成功")
            log.run_logger.info(f"模型输出: {content}")
            return content

        except ValueError:
            raise
        except Exception as e:
            log.warning_logger.error(f"调用模型: {model} 失败: {e}")
            if attempt == max_retries:
                raise ValueError(f"调用模型失败，已重试 {max_retries} 次: {e}")

    raise ValueError(f"调用模型失败，已重试 {max_retries} 次")


def convert_txt_to_json(input_txt, output_json):
    log.run_logger.info(f"开始输入文件: {input_txt}")


    try:
    # 尝试 GBK 编码读取
        try:
            log.run_logger.info(f"尝试使用 GBK 编码读取文件: {input_txt}")
            with open(input_txt, "r", encoding="gbk") as f:
                chapter_text = f.read()
        except UnicodeDecodeError:
            # GBK 失败则尝试 UTF-8
            log.run_logger.info(f"尝试使用 UTF-8 编码读取文件: {input_txt}")
            with open(input_txt, "r", encoding="utf-8") as f:
                chapter_text = f.read()
    except Exception as e:
        log.warning_logger.error(f"读取输入文件: {input_txt} 失败: {e}")
        raise e
    log.run_logger.info(f"输入文件: {input_txt} 读取完毕")

    log.run_logger.info(f"开始构建提示词")
    prompt = build_prompt(chapter_text)
    result_json = call_llm(prompt)

    try:
        with open(output_json, "w", encoding="utf-8") as f:
            log.run_logger.info(f"开始保存输出文件: {output_json}")
            f.write(result_json)
    
    except Exception as e:
        log.warning_logger.error(f"保存输出文件: {output_json} 失败: {e}")
        raise e

    print(f"转换完成，已保存到: {output_json}")
    log.run_logger.info(f"转换完成，已保存到: {output_json}")


def run_conversion(input,output):
    if not input:
        print("错误：未在config.py中指定INPUT")
        log.run_logger.error("未在config.py中指定INPUT")
        return

    if not output:
        print("错误：未在config.py中指定OUTPUT")
        log.run_logger.error("未在config.py中指定OUTPUT")
        return


    if not os.path.exists(input):
        print(f"错误：输入文件不存在: {input}")
        log.run_logger.error(f"输入文件不存在: {input}")
        return

    convert_txt_to_json(
        input_txt=input,
        output_json=output,
    )


