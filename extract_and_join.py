"""
本代码实现：
1.遍历output文件，提取所有beat列表下第二个数据的唯一值形成任务列表（剔出环境）
2.将output合并为一个json文件
3.允许用户从角色列表列表中将某几个人物合并成一个任务，同时将数据结构中对应人物名称进行合并后替换
4.允许用户从任务列表中选择重要人物
"""


import json
import os
import glob
import log
from config import OUTPUTDIR,ALLOUPUTDIR,CHAROUPUTDIR



def extract_characters(json_dir):
    log.run_logger.info("开始提取角色列表")
    characters = set()
    for f in glob.glob(os.path.join(json_dir, "*.json")):
        with open(f, "r", encoding="utf-8") as file:
            data = json.load(file)
        for scene in data.get("scenes", []):
            for beat in scene.get("beats", []):
                if beat[1] != "环境":
                    characters.add(beat[1])
    log.run_logger.info(f"角色列表提取完成，共 {len(characters)} 个角色")
    log.run_logger.info(f"角色列表: {sorted(characters)}")
    return sorted(characters)


def merge_json_files(json_dir, output_file):
    log.run_logger.info("开始合并json文件")
    merged = {"chapters": []}
    try:
        for f in sorted(glob.glob(os.path.join(json_dir, "ch_*.json"))):
            with open(f, "r", encoding="utf-8") as file:
                merged["chapters"].append(json.load(file))
    except Exception as e:
        log.warning_logger.error(f"合并json文件时出错: {e}")
        return None
    try:
        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(merged, file, ensure_ascii=False, indent=2)
        log.run_logger.info(f"json文件合并完成，已保存到 {output_file}")
    except Exception as e:
        log.warning_logger.error(f"合并json文件时出错: {e}")
        return None
    return merged


def merge_characters(json_file, characters):
    log.run_logger.info("开始合并角色")
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        log.warning_logger.error(f"加载全文数据出错: {e}")
        return None
    
    print("角色列表:", ", ".join(characters))
    merge_map = {}
    while True:
        names = input("请输入要合并的角色（逗号分隔，回车跳过）: ").strip()
        if not names:
            break
        name_list = [n.strip() for n in names.split(",") if n.strip()]
        if len(name_list) < 2:
            print("至少需要两个角色")
            continue
        new_name = input(f"为 {name_list} 指定唯一名字: ").strip()
        if not new_name:
            print("名字不能为空")
            continue
        for name in name_list:
            merge_map[name] = new_name
    
    log.run_logger.info("开始合并角色")
    for chapter in data.get("chapters", []):
        for scene in chapter.get("scenes", []):
            for beat in scene.get("beats", []):
                if beat[1] in merge_map:
                    beat[1] = merge_map[beat[1]]
    
    try:
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.warning_logger.error(f"合并角色时出错: {e}")
        return None
    log.run_logger.info(f"角色合并完成，已保存到 {json_file}")
    return data


def select_important_characters(characters, char_file):
    print("可选角色:", ", ".join(characters))
    selected = input("请输入重要角色（逗号分隔）: ").strip()
    selected = [c.strip() for c in selected.split(",") if c.strip()]
    log.run_logger.info(f"重要角色: {selected}")
    with open(char_file, "w", encoding="utf-8") as f:
        json.dump(selected, f, ensure_ascii=False, indent=2)
    log.run_logger.info(f"重要角色已保存到 {char_file}")
    return selected

if __name__ == "__main__":
    log.run_logger.info("开始处理数据")
    json_dir = OUTPUTDIR
    output_file =ALLOUPUTDIR
    characters = extract_characters(json_dir)
    merged = merge_json_files(json_dir, output_file)
    if merged:
        merge_characters(output_file, characters)
        if characters:
            characters = select_important_characters(characters, CHAROUPUTDIR)
            if characters:
                log.run_logger.info("重要角色选择完成")
                log.run_logger.info(f"重要角色: {characters}")
                log.run_logger.info("数据处理完成")
