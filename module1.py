"""
编写函数：输入一个文件夹，调用check_input_files函数
"""
import os
from check_data import check_input_files
from book2data import run_conversion
import log
from config import INPUTDIR, OUTPUTDIR

if check_input_files(INPUTDIR):
    log.run_logger.info("所有输入文件验证通过")
    _,ch_list=check_input_files(INPUTDIR)
else:
    log.warning_logger.error("输入文件验证失败,请检查文件命名格式")

for chapter in ch_list:
    log.run_logger.info(f"开始处理章节: {chapter}")
    OUTPUT = os.path.join(OUTPUTDIR, chapter.replace(".txt", "_data.json"))
    input=os.path.join(INPUTDIR, chapter)
    run_conversion(input, OUTPUT)
    log.run_logger.info(f"章节: {chapter} 处理完成")
    # 读取章节内容
    
