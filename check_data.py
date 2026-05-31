"""
第一个函数：检查大语言模型的输出是否符合要求
第二个函数：检查输入文件夹的的所有文件是否都为txt格式，是否存在ch_{章节编号}.txt文件的，且所有以这些文件的章节编号是否递增，如果是则返回文件名列表
"""

import json
import os
import re
from jsonschema import validate, ValidationError
from config import OUTPUT_SCHEMA
import log


def check_llm_output(json_data):
    log.run_logger.info("开始检查大语言模型输出")
    try:
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data
        validate(instance=data, schema=OUTPUT_SCHEMA)
        
        for scene in data.get("scenes", []):
            for beat in scene.get("beats", []):
                if len(beat) != 3:
                    log.warning_logger.error(f"beat三元组长度错误: {beat}")
                    return False, f"beat三元组长度错误: {beat}"
                beat_type, speaker, content = beat
                if beat_type not in ["dialogue", "action", "internal_thought", "environment"]:
                    log.warning_logger.error(f"beat类型错误: {beat_type}")
                    return False, f"beat类型错误: {beat_type}"
                if beat_type == "environment" and speaker != "环境":
                    log.warning_logger.error(f"environment类型的执行者必须为'环境': {beat}")
                    return False, f"environment类型的执行者必须为'环境': {beat}"
                if beat_type in ["dialogue", "internal_thought"] and not speaker:
                    log.warning_logger.error(f"dialogue和internal_thought必须有执行者: {beat}")
                    return False, f"dialogue和internal_thought必须有执行者: {beat}"
        
        log.run_logger.info("所有beat验证通过")
        return True, "验证通过"
    except json.JSONDecodeError as e:
        log.warning_logger.error(f"JSON解析失败: {e}")
        return False, f"JSON解析失败: {e}"
    except ValidationError as e:
        log.warning_logger.error(f"Schema验证失败: {e.message}")
        return False, f"Schema验证失败: {e.message}"
    except Exception as e:
        log.warning_logger.error(f"未知错误: {e}")
        return False, f"未知错误: {e}"


def check_input_files(input_dir):


    log.run_logger.info(f"开始检查目录: {input_dir}")

    if not os.path.exists(input_dir):
        log.warning_logger.error(f"目录不存在: {input_dir}")
        return False, f"目录不存在: {input_dir}"
    
    files = os.listdir(input_dir)
    txt_files = [f for f in files if f.endswith(".txt")]
    
    if len(txt_files) != len(files):
        non_txt = [f for f in files if not f.endswith(".txt")]
        log.warning_logger.error(f"存在非txt文件: {non_txt}")
        return False, f"存在非txt文件: {non_txt}"
    
    pattern = re.compile(r"^ch_(\d+)\.txt$")
    chapter_files = []
    
    for f in txt_files:
        match = pattern.match(f)
        if match:
            log.warning_logger.info(f"匹配到文件: {f}，章节编号: {match.group(1)}")
            chapter_files.append((int(match.group(1)), f))
        else:
            log.warning_logger.error(f"文件名格式错误: {f}，应为ch_章节编号.txt")
            return False, f"文件名格式错误: {f}，应为ch_{{章节编号}}.txt"


            
    
    chapter_files.sort(key=lambda x: x[0])
    
    for i, (num, _) in enumerate(chapter_files):
        if i > 0 and num != chapter_files[i-1][0] + 1:
            log.warning_logger.error(f"章节编号不连续: 缺少ch_{chapter_files[i-1][0] + 1}.txt")
            return False, f"章节编号不连续: 缺少ch_{chapter_files[i-1][0] + 1}.txt"
    
    log.run_logger.info("所有文件检查通过")
    return True, [f for _, f in chapter_files]
