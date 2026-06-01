from datetime import datetime

API_KEY = "sk-***"
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL = "qwen3.6-plus"
INPUTDIR = "input"
OUTPUTDIR = "output"

#数字资产存储地址
ALLOUPUTDIR = "assets/fromstr/merged.json"
CHAROUPUTDIR = "assets/fromstr/important_characters.json"
CHAIMGOUTPUTDIR = "assets/character_img"
SCENEIMGOUTPUTDIR = "assets/scen_img"
BEATIMGOUTPUTDIR = "assets/beat_img"
BEATTEXTOUTPUTDIR = "assets/str"







WARNINGS_PATH="log_and_warn/warnings"
LOG_PATH="log_and_warn/log"

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "chapter_id": {"type": "string"},
        "chapter_title": {"type": "string"},
        "scenes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "scene_id": {"type": "string"},
                    "scene_title": {"type": "string"},
                    "location": {"type": "string"},
                    "environment_description": {"type": "string"},
                    "beats": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 3,
                            "maxItems": 3
                        }
                    }
                },
                "required": ["scene_id", "scene_title", "time", "location", "environment_description", "beats"]
            }
        }
    },
    "required": ["chapter_id", "chapter_title", "scenes"]
}

EXPLAIN="""
- chapter_id: 章节编号，如ch1、ch2
- chapter_title: 章节标题
- scenes: 场景列表，按时间顺序排列
  - scene_id: 场景编号，如s1、s2
  - scene_title: 场景标题，简短概括场景内容
  - location: 场景发生地点
  - environment_description: 场景的环境描写，包括时间、氛围、光线、天气等，需要贴合原文内容，最好与原文内容一致或简单改写
  - beats: 节拍列表，按发生顺序排列，每个节拍为三元组 [类型, 执行者, 内容]
    - 类型: dialogue（对话）、action（行为）、internal_thought（心理活动）、environment（环境变化）
    - 执行者: 角色名称，environment类型固定为"环境"
    - 内容: 具体的对话内容、行为描述、心理活动或环境变化
    """

EXAMPLE = {
    "chapter_id": "ch1",
    "chapter_title": "初遇",
    "scenes": [
        {
            "scene_id": "s1",
            "scene_title": "教室里的早晨",
            "time": "2024-09-01 08:00",
            "location": "教室",
            "environment_description": "清晨的阳光透过玻璃窗洒在整洁的课桌上，教室里还空无一人",
            "beats": [
                ["environment", "环境", "走廊传来脚步声"],
                ["action", "小明", "推开门走进教室"],
                ["internal_thought", "小明", "今天又是新的一天"],
                ["dialogue", "小明", "早上好！"]
            ]
        },
        {
            "scene_id": "s2",
            "scene_title": "操场上的相遇",
            "time": "2024-09-01 10:00",
            "location": "操场",
            "environment_description": "操场上微风轻拂，远处的篮球架在阳光下闪闪发光",
            "beats": [
                ["action", "小红", "在跑道上慢跑"],
                ["environment", "环境", "一阵风吹过，树叶沙沙作响"],
                ["dialogue", "小红", "你也来跑步吗？"],
                ["dialogue", "小明", "是啊，一起吧"]
            ]
        }
    ]
}

date_str = datetime.now().strftime('%Y%m%d%H')
#日志与警告
URL_WARNING_FILENAME=f"{WARNINGS_PATH}/{date_str}_get_url_warnings.json"
CONTENT_WARNING_FILENAME=f"{WARNINGS_PATH}/{date_str}_get_content_warnings.json"
DOWNLOAD_WARNING_FILENAME=f"{WARNINGS_PATH}/{date_str}_attackment_load_warnings.json"

RUN_LOG_FILENAME=f"{LOG_PATH}/{date_str}_running_log.json"
SAVE_LOG_FILENAME=f"{LOG_PATH}/{date_str}_save_log.json"
ERROR_RECORD=f"{WARNINGS_PATH}/content_blank/{date_str}_error_record.txt"

#最大重试次数
max_retries=3

#生图模型配置
IMG_API_KEY = "sk-***"
IMG_BASE_URL = 'https://dashscope.aliyuncs.com/api/v1'
IMG_MODEL = "wan2.7-image"