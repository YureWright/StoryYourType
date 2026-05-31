"""
本代码用于创造数字资产
1.遍历assets/fromstr/important_characters.json中的列表，同时读取assets/fromstr/merged.json，以及用户输入风格，LLM生成生图提示词，传给生图模型生成重要人物立绘图，按要求保存
2.用户输入风格，遍历每个场景，传给LLM生成场景描述，传给生图模型生成场景图片，按要求保存
3.遍历每个beat，传给LLM对应场景图描述，让LLM生成符合场景风格的提示词，若beat中存在重要人物，也要把人物立绘传给LLM，最后将提示词、人物立绘和对应场景图一并传给生图模型生成beat图片，按要求保存;含重要人物的beat必须与立绘人物形象尽可能一致，保持重要人物的一致性
4.遍历每个beat，传递给大语言模型，将beat三元组组成一句话形成文案，按要求保存
要求：以上所有数字资产必须能够一一对应，可通过命名方式对beat图片、文案进行排序并一一对应；场景图片用chapterid和scenid命名
"""
from config import CHAIMGOUTPUTDIR, SCENEIMGOUTPUTDIR, BEATIMGOUTPUTDIR, BEATTEXTOUTPUTDIR, ALLOUPUTDIR, CHAROUPUTDIR
from config import IMG_API_KEY, IMG_BASE_URL, IMG_MODEL, API_KEY, BASE_URL, MODEL, max_retries
import log
import json
import os
import base64
import requests
from openai import OpenAI
import time


def image_to_base64(image_path):
    import base64
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')


def call_llm_text(prompt, images=None, system_prompt=""):
    """调用文本大语言模型，支持传入图片列表，返回模型响应内容"""
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    content = []
    if images:
        log.run_logger.info(f"正在添加图片 {images} 到提示词")
        for img_path in images:
            if os.path.exists(img_path):
                b64 = image_to_base64(img_path)
                content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
    content.append({"type": "text", "text": prompt})
    messages.append({"role": "user", "content": content})
    
    log.run_logger.info(f"正在调用模型 {MODEL} 生成提示词: {prompt}")
    response = client.chat.completions.create(model=MODEL, messages=messages, temperature=0.1)
    return response.choices[0].message.content



def call_llm_image(prompt, output_path, reference_images=None):
    """调用生图模型（同步接口），根据提示词和参考图生成图片并保存到指定路径，支持重试"""
    for attempt in range(1, max_retries + 1):
        log.run_logger.info(f"正在调用模型 {IMG_MODEL} 第 {attempt} 次尝试")
        try:
            headers = {
                "Authorization": f"Bearer {IMG_API_KEY}",
                "Content-Type": "application/json"
            }
            
            # 构建 content 数组（文本 + 参考图）
            messages_content = [{"text": prompt}]
            
            if reference_images:
                log.run_logger.info(f"正在添加参考图: {reference_images}")
                for img_path in reference_images:
                    if os.path.exists(img_path):
                        # 将本地图片转为 Data URL
                        mime = "image/png" if img_path.lower().endswith(".png") else "image/jpeg"
                        b64 = image_to_base64(img_path)  # 假设该函数返回纯 base64 字符串
                        messages_content.append({"image": f"data:{mime};base64,{b64}"})
                    else:
                        log.run_logger.warning(f"参考图不存在: {img_path}")
            
            # 构建请求体（同步多模态生成 API）
            payload = {
                "model": IMG_MODEL,
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": messages_content
                        }
                    ]
                },
                "parameters": {
                    "n": 1,
                    "size": "1K",          # 可配置为 "2K"
                    "watermark": False,
                    "prompt_extend": False # 可选，是否自动扩展提示词
                }
            }
            
            # 同步生成接口地址（注意与异步不同）
            create_url = f"{IMG_BASE_URL}/services/aigc/multimodal-generation/generation"
            resp = requests.post(create_url, headers=headers, json=payload, timeout=120)
            
            log.run_logger.debug(f"API 响应状态码: {resp.status_code}")
            log.run_logger.debug(f"API 响应内容: {resp.text}")
            
            if resp.status_code != 200:
                raise Exception(f"HTTP {resp.status_code}: {resp.text}")
            
            result = resp.json()
            
            # 检查业务错误
            if "error" in result:
                error_msg = result["error"].get("message", str(result["error"]))
                raise Exception(f"API 错误: {error_msg}")
            
            # 解析同步响应中的图片 URL
            # 响应结构: {"output": {"choices": [{"message": {"content": [{"image": "https://..."}]}}]}}
            if "output" not in result or "choices" not in result["output"]:
                log.run_logger.error(f"完整响应: {result}")
                raise KeyError("响应中缺少 'output.choices'")
            
            choices = result["output"]["choices"]
            if not choices:
                raise Exception("响应中没有生成结果")
            
            image_url = None
            for item in choices[0]["message"]["content"]:
                if "image" in item:
                    image_url = item["image"]
                    break
            
            if not image_url:
                raise Exception("未能从响应中提取图片URL")
            
            # 下载并保存图片
            img_resp = requests.get(image_url, timeout=60)
            img_resp.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(img_resp.content)
            log.run_logger.info(f"图片已保存: {output_path}")
            return True
            
        except Exception as e:
            log.warning_logger.error(f"生图失败 (尝试 {attempt}/{max_retries}): {e}")
            if attempt == max_retries:
                # 可选：删除不完整的输出文件
                if os.path.exists(output_path):
                    os.remove(output_path)
                return False
            # 重试前等待（指数退避）
            time.sleep(2 ** attempt)
    return False

def generate_character_images(style):
    """遍历重要角色列表，LLM生成生图提示词，调用生图模型生成角色立绘并保存"""
    with open(CHAROUPUTDIR, "r", encoding="utf-8") as f:
        characters = json.load(f)
    with open(ALLOUPUTDIR, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    os.makedirs(CHAIMGOUTPUTDIR, exist_ok=True)
    
    log.run_logger.info(f"正在生成立绘提示词")
    for char in characters:
        prompt = call_llm_text(
            f"""
# Role
你现在是一名资深的游戏立绘设计师，擅长从角色的故事背景中提炼视觉元素，生成高质量、可用于AI绘画的提示词。

# Task
根据以下提供的角色故事数据，深入理解该人物的性格、经历、关系与命运走向，为其设计一张符合游戏美术风格的立绘。

# Input Data
故事背景：\n{data}

# Requirements
1. 请严格为角色 **{char}** 生成立绘提示词（Prompt）。
2. 提示词需覆盖以下维度，并确保逻辑自洽：
   - **外貌特征**：年龄、脸型、五官、发型、发色、瞳色等，需体现人物性格。
   - **服装设计**：样式、颜色、材质、装饰细节，需反映其身份、阶层或时代背景。
   - **姿态与动作**：站姿、手势、身体朝向，需暗示其当前心理状态或战斗/日常姿态。
   - **表情神态**：眼神、嘴角、眉毛形态，传递情绪（如坚毅、忧郁、狡黠、温柔等）。
   - **光影与氛围**：主光源方向、色调、背景元素（简洁或特定场景），增强故事感。
3. 整体风格必须统一为 **{style}**。
4. 提示词应当直接、详细、无解释性文字，便于复制到AI绘画工具中使用。

# Output Format
仅输出最终的提示词内容，不要包含任何额外说明、注释或角色名以外的标题。

现在，请生成：
""" 
        )

        output_path = os.path.join(CHAIMGOUTPUTDIR, f"{char}.png")
        log.run_logger.info(f"生成角色 {char} 立绘，提示词: {prompt}")
        call_llm_image(prompt, output_path)
        log.run_logger.info(f"角色 {char} 立绘生成完成，保存到 {output_path}")


def generate_scene_images(style):
    """遍历所有场景，LLM生成场景描述提示词，调用生图模型生成场景图片并按chapterid_sceneid命名保存"""
    with open(ALLOUPUTDIR, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    os.makedirs(SCENEIMGOUTPUTDIR, exist_ok=True)
    
    for chapter in data.get("chapters", []):
        chapter_id = chapter.get("chapter_id", "unknown")
        for scene in chapter.get("scenes", []):
            scene_id = scene.get("scene_id", "unknown")
            env_desc = scene.get("environment_description", "")
            location = scene.get("location", "")
            
            log.run_logger.info(f"正在生成场景 {chapter_id}_{scene_id} 提示词")
            prompt = call_llm_text(
f"""
# Role
你现在是一名专业的游戏场景概念设计师，擅长将故事背景与场景描述融合，生成富有叙事氛围和沉浸感的画面提示词。

# Task
根据以下故事背景、地点名称和环境描述，设计一张符合游戏美术风格的场景画面提示词，用于AI绘画生成。

# Input Data
- 故事背景：\n{data}
- 地点名称：{location}
- 环境详细描述：{env_desc}

# Requirements
1. 提示词需充分结合故事背景中的情节、情绪或隐喻，让场景具有叙事性和情感张力。
2. 提示词需包含以下维度：
   - **空间构成**：视角（俯视/平视/仰视）、景别（远景/中景/近景）、构图重心。
   - **环境元素**：标志性物体、植被、建筑、光影、天气、时间（昼夜/季节），以及与故事相关的细节（例如残留的战斗痕迹、旧照片、特定道具等）。
   - **氛围情绪**：色调（冷/暖/对比）、光线方向、空气透视、动静感（如飘雪、摇曳的灯光），呼应故事基调（压抑/希望/孤独/紧张等）。
   - **风格统一**：整体美术风格必须为 **{style}**。
   - **细节层次**：可包含前景、中景、背景的层次划分，以及可选的色彩参考。
3. 提示词应直接、具体、无解释性文字，便于复制到AI绘画工具中使用。
4. 仅输出最终提示词，不要添加任何额外说明或标题。

# Output Format
仅输出生成的提示词内容。

现在，请生成：
"""            )
            output_path = os.path.join(SCENEIMGOUTPUTDIR, f"{chapter_id}_{scene_id}.png")
            log.run_logger.info(f"生成场景 {chapter_id}_{scene_id} 图片，提示词: {prompt}")
            call_llm_image(prompt, output_path)
            log.run_logger.info(f"场景 {chapter_id}_{scene_id} 图片生成完成")


def generate_beat_images(style):
    """遍历所有beat，LLM生成符合场景风格的提示词，若存在重要人物则关联立绘，调用生图模型生成beat图片并按序号保存"""
    with open(ALLOUPUTDIR, "r", encoding="utf-8") as f:
        data = json.load(f)
    with open(CHAROUPUTDIR, "r", encoding="utf-8") as f:
        important_chars = json.load(f)
    
    os.makedirs(BEATIMGOUTPUTDIR, exist_ok=True)
    
    char_imgs = {c: os.path.join(CHAIMGOUTPUTDIR, f"{c}.png") for c in important_chars if os.path.exists(os.path.join(CHAIMGOUTPUTDIR, f"{c}.png"))}
    
    beat_idx = 0
    for chapter in data.get("chapters", []):
        chapter_id = chapter.get("chapter_id", "unknown")
        for scene in chapter.get("scenes", []):
            scene_id = scene.get("scene_id", "unknown")
            scene_img = os.path.join(SCENEIMGOUTPUTDIR, f"{chapter_id}_{scene_id}.png")
            env_desc = scene.get("environment_description", "")
            
            for beat in scene.get("beats", []):
                beat_type, speaker, content = beat
                beat_idx += 1
                
                log.run_logger.info(f"正在生成beat {beat_idx} 提示词")
                log.run_logger.info(f"正在加载参考图片")
                ref_images = [scene_img] if os.path.exists(scene_img) else []
                if speaker in char_imgs and os.path.exists(char_imgs[speaker]):
                    ref_images.append(char_imgs[speaker])
                    log.run_logger.info(f"添加角色 {speaker} 立绘到参考图片")
                
                if not ref_images: 
                    log.warning_logger.info(f"beat {beat_idx} 没有参考图片，跳过")

                log.run_logger.info(f"正在调用模型 LLM 生成提示词")    
                prompt = call_llm_text(
f"""
# Role
你是一名游戏CG构图师，需要根据场景描述、叙事节拍（Beat），以及已有的人物立绘与场景参考图，生成一张可用于AI绘画的最终画面提示词。

# Task
生成一张符合 {style} 风格的场景画面，该画面需要：
- 基于场景描述（{env_desc}）和节拍信息（Beat: [{beat_type}, {speaker}, {content}]）构建构图与情绪。
- **如果提供了人物立绘图片**：画面中出现该角色时，其外貌、服装、体型必须严格与立绘保持一致。  
- **如果提供了场景参考图**：画面背景的地标、建筑风格、材质、光影色调需与参考图保持统一，但可以调整局部细节以适应节拍。

# Available Inputs
- 人物立绘参考图：{'无' if not speaker in char_imgs else '已提供（见附图）'}
- 场景参考图：{'无' if not scene_img else '已提供（见附图）'}
- 风格限定：{style}

# Requirements for the output prompt
1. 提示词必须包含以下维度：
   - **人物一致性约束**：若立绘存在，需显式描述该角色的外貌特征（发型、发色、瞳色、服装、体态），确保生成结果与立绘匹配。
   - **场景一致性约束**：若场景参考图存在，需描述关键背景元素（地标、材质、色调、透视），避免产生冲突。
   - **叙事节拍**：根据 beat 的类型（对话/行动/心理/环境）、说话者/执行者、内容，确定画面的动态瞬间——例如对话时的人物互动、行动时的关键姿势、心理活动时的神态与构图。
   - **氛围与光影**：结合场景描述与 beat 的情绪，指定光色（暖/冷/对比）、明暗分布、空气感等。
   - **构图与视角**：推荐景别（特写/中景/全景）、角度（平视/俯视/仰视）、角色位置关系。
2. 仅输出最终的提示词正文，不要输出任何额外说明。
3. 节拍信息必须是画面的主要内容，再次提示节拍信息：{beat_type}, {speaker}, {content}

# Output Format
[直接输出提示词]

#现在，请生成：
""",                    images=ref_images if ref_images else None
                )
                
                output_path = os.path.join(BEATIMGOUTPUTDIR, f"{beat_idx:04d}.png")
                log.run_logger.info(f"生成beat {beat_idx} 图片，提示词: {prompt}")
                log.run_logger.info(f"参考图: {ref_images}")
                call_llm_image(prompt, output_path, reference_images=ref_images if ref_images else None)
                log.run_logger.info(f"beat {beat_idx} 图片生成完成，保存到 {output_path}")


def generate_beat_texts():
    """遍历所有beat，LLM将三元组组成一句话文案，按序号保存到JSON文件"""
    with open(ALLOUPUTDIR, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    os.makedirs(BEATTEXTOUTPUTDIR, exist_ok=True)
    
    beat_idx = 0
    texts = []
    for chapter in data.get("chapters", []):
        for scene in chapter.get("scenes", []):
            for beat in scene.get("beats", []):
                beat_type, speaker, content = beat
                beat_idx += 1
                
                text = call_llm_text(
                    f"将以下beat三元组组成一句话文案：\n类型：{beat_type}\n执行者：{speaker}\n内容：{content}\n只输出文案，不要解释。"
                )
                texts.append({"index": beat_idx, "text": text})
                log.run_logger.info(f"beat {beat_idx} 文案: {text}")
    
    output_path = os.path.join(BEATTEXTOUTPUTDIR, "beat_texts.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(texts, f, ensure_ascii=False, indent=2)
    log.run_logger.info(f"文案已保存到 {output_path}")


def main():
    """主函数：获取用户输入的美术风格，依次执行角色立绘、场景图片、beat图片、beat文案生成"""
    style = input("请输入美术风格: ").strip()
    if not style:
        style = "日系动漫"
    
    log.run_logger.info(f"开始生成数字资产，风格: {style}")
    
    log.run_logger.info("步骤1: 生成角色立绘")
    generate_character_images(style)
    
    log.run_logger.info("步骤2: 生成场景图片")
    generate_scene_images(style)
    
    log.run_logger.info("步骤3: 生成beat图片")
    generate_beat_images(style)
    
    log.run_logger.info("步骤4: 生成beat文案")
    generate_beat_texts()
    
    log.run_logger.info("所有数字资产生成完成")


if __name__ == "__main__":
    main()
