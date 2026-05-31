"""
本代码实现：
1.抽取关键beat（主人公影响后续剧情的动作）为创建分支剧情做准备。抽取方法：每章抽取一个关键beat，首先让用户根据重要人物角色列表，选择一个角色作为关键beat的执行者，然后遍历总数据结构的每一个章节，每章让大语言模型选择一个该角色最重要的行为或语言作为关键beat，最终所有章节构成一个由场景-章节-动作类型（语言或行为）-动作内容构成的动作列表。
2.将beat图片和文案连接成游戏场景，其中关键beat可由玩家type他的选择
3.实现玩家type选择后，对于新场景的撰写、数据提取、数字资产生成以及最终游戏生成的流程。在关键beat，存在默认选项和type选项，选择默认选项，则会按照原有流程继续进行，选择type选项，AI会根据你输入的内容创建新的剧情线。向大语言模型传递全部章节原文，关键及之前beat前的数据结构，以及玩家type的内容。大语言模型需要编写之后的章节，连接上玩家的type。新的内容存储在输出文件的新的文件夹下。并将新的内容提取为数据，并参考之前的流程生成新的一段游戏场景。
"""
import json
import os
from openai import OpenAI
from config import API_KEY, BASE_URL, MODEL, ALLOUPUTDIR, CHAROUPUTDIR, BEATIMGOUTPUTDIR, BEATTEXTOUTPUTDIR, max_retries
import log


def call_llm(prompt, system_prompt=""):
    """调用大语言模型，返回文本响应"""
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    response = client.chat.completions.create(model=MODEL, messages=messages, temperature=0.1)
    return response.choices[0].message.content


def extract_key_beats():
    """抽取关键beat：让用户选择关键角色，遍历每章让LLM选择该角色最重要的行为或语言作为关键beat"""
    with open(ALLOUPUTDIR, "r", encoding="utf-8") as f:
        data = json.load(f)
    with open(CHAROUPUTDIR, "r", encoding="utf-8") as f:
        important_chars = json.load(f)
    
    print("重要角色:", ", ".join(important_chars))
    key_char = input("请选择关键beat的执行者: ").strip()
    if key_char not in important_chars:
        log.warning_logger.error(f"角色 {key_char} 不在重要角色列表中")
        return []
    
    key_beats = []
    for chapter in data.get("chapters", []):
        chapter_id = chapter.get("chapter_id", "unknown")
        chapter_title = chapter.get("chapter_title", "未知")
        
        chapter_beats = []
        for scene in chapter.get("scenes", []):
            scene_id = scene.get("scene_id", "unknown")
            for beat in scene.get("beats", []):
                beat_type, speaker, content = beat
                if speaker == key_char and beat_type in ["dialogue", "action"]:
                    chapter_beats.append({
                        "scene_id": scene_id,
                        "beat_type": beat_type,
                        "content": content
                    })
        
        if not chapter_beats:
            continue
        
        beats_str = json.dumps(chapter_beats, ensure_ascii=False, indent=2)
        prompt = f""""
        你是一个游戏设计师，需要明确一个故事在哪里需要加入分支，以下是故事的抽象数据：\n{data}\n\n
        以下是第{chapter_id}章中{key_char}的所有行为和对话，请选择最重要的一个（能够影响后续情节和人物命运）（返回scene_id和content即可）：
        output format:
        {
            "chapter_id": "ch1",
            "scene_id": "s1",
            "beat_type": "dialogue",
            "content": "你好，我是{key_char}，我是一个学生。"
        }

        以下是该人物的所有行为和对话：
        \n{beats_str}

        output format:
        {
            "chapter_id": "ch1",
            "scene_id": "s1",
            "beat_type": "dialogue",
            "content": "你好，我是{key_char}，我是一个学生。"
        }

        注意content必须与行为列表中的content完全一致。
        """
        result = call_llm(prompt)
        
        try:
            selected = json.loads(result)
            key_beats.append({
                "chapter_id": chapter_id,
                "chapter_title": chapter_title,
                "scene_id": selected.get("scene_id", ""),
                "beat_type": selected.get("beat_type", ""),
                "content": selected.get("content", "")
            })
        except:
            log.warning_logger.error(f"解析LLM输出失败: {result}")
    
    log.run_logger.info(f"关键beat列表: {key_beats}")
    return key_beats


def build_game_scenes(key_beats):
    """将beat图片和文案连接成游戏场景，关键beat提供type选项"""
    with open(os.path.join(BEATTEXTOUTPUTDIR, "beat_texts.json"), "r", encoding="utf-8") as f:
        texts = json.load(f)
    
    key_beats_set = {(kb["chapter_id"], kb["scene_id"], kb["content"]) for kb in key_beats}
    
    game_scenes = []
    for item in texts:
        idx = item["index"]
        text = item["text"]
        img_path = os.path.join(BEATIMGOUTPUTDIR, f"{idx:04d}.png")
        
        is_key = False
        for kb in key_beats:
            if kb["content"] == text:
                is_key = True
                break
        
        scene = {
            "index": idx,
            "image": img_path,
            "text": text,
            "is_key_beat": is_key
        }
        game_scenes.append(scene)
    
    log.run_logger.info(f"游戏场景构建完成，共 {len(game_scenes)} 个场景")
    return game_scenes


def play_game(game_scenes, key_beats):
    """运行游戏，在关键beat处提供默认继续或type输入选项"""
    for scene in game_scenes:
        print(f"\n--- 场景 {scene['index']} ---")
        if os.path.exists(scene["image"]):
            print(f"[图片: {scene['image']}]")
        print(scene["text"])
        
        if scene["is_key_beat"]:
            print("\n[关键选择点]")
            choice = input("输入 'type' 自定义行动，或回车继续: ").strip()
            if choice.lower() == "type":
                player_input = input("请输入你的行动: ").strip()
                log.run_logger.info(f"玩家type输入: {player_input}")
                return player_input
    
    return None


def generate_new_content(player_input, data):
    """根据玩家type输入，LLM生成新剧情并返回新数据结构"""
    chapters_str = json.dumps(data.get("chapters", []), ensure_ascii=False, indent=2)
    prompt = f"""玩家输入：{player_input}

请根据玩家输入，续写后续剧情。要求：
1. 连接玩家的输入，保持剧情连贯
2. 输出JSON格式，结构与原数据一致（包含scenes、beats等）
3. 只输出JSON，不要其他解释

原数据结构：
{chapters_str}

请输出新剧情JSON："""
    
    result = call_llm(prompt)
    try:
        new_data = json.loads(result)
        return new_data
    except:
        log.warning_logger.error(f"解析新剧情失败: {result}")
        return None


def save_new_branch(new_data, branch_name="branch_1"):
    """保存新分支剧情到输出文件夹"""
    output_dir = os.path.join("output", branch_name)
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, "new_chapter.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)
    
    log.run_logger.info(f"新分支已保存到 {output_path}")
    return output_path


def generate_game_html(game_scenes, key_beats, output_path="output/game.html"):
    """生成可运行的游戏网页，图片拼接成流动感，文案贴在图片上"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    scenes_json = json.dumps(game_scenes, ensure_ascii=False, indent=2)
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Galgame</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: #000; overflow: hidden; font-family: 'Microsoft YaHei', sans-serif; }}
#game-container {{ position: relative; width: 100vw; height: 100vh; }}
.scene {{ position: absolute; width: 100%; height: 100%; opacity: 0; transition: opacity 1.5s ease-in-out; }}
.scene.active {{ opacity: 1; }}
.scene img {{ width: 100%; height: 100%; object-fit: cover; }}
.scene .text-overlay {{ position: absolute; bottom: 10%; left: 50%; transform: translateX(-50%); background: rgba(0,0,0,0.7); color: #fff; padding: 20px 40px; border-radius: 10px; max-width: 80%; font-size: 18px; line-height: 1.6; text-align: center; animation: fadeInUp 1s ease-out; }}
@keyframes fadeInUp {{ from {{ opacity: 0; transform: translateX(-50%) translateY(20px); }} to {{ opacity: 1; transform: translateX(-50%) translateY(0); }} }}
#choice-overlay {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); display: none; justify-content: center; align-items: center; z-index: 100; }}
#choice-box {{ background: #fff; padding: 40px; border-radius: 15px; text-align: center; }}
#choice-box h2 {{ margin-bottom: 20px; color: #333; }}
#choice-box button {{ margin: 10px; padding: 15px 30px; font-size: 16px; border: none; border-radius: 8px; cursor: pointer; transition: all 0.3s; }}
#choice-box .btn-default {{ background: #4CAF50; color: #fff; }}
#choice-box .btn-default:hover {{ background: #45a049; }}
#choice-box .btn-type {{ background: #2196F3; color: #fff; }}
#choice-box .btn-type:hover {{ background: #0b7dda; }}
#type-input {{ display: none; margin-top: 20px; }}
#type-input textarea {{ width: 100%; padding: 10px; font-size: 16px; border: 2px solid #ddd; border-radius: 8px; resize: none; }}
#type-input button {{ margin-top: 10px; padding: 10px 30px; background: #2196F3; color: #fff; border: none; border-radius: 8px; cursor: pointer; }}
#nav-hint {{ position: fixed; bottom: 20px; right: 20px; background: rgba(255,255,255,0.3); color: #fff; padding: 10px 20px; border-radius: 20px; font-size: 14px; }}
</style>
</head>
<body>
<div id="game-container"></div>
<div id="choice-overlay">
<div id="choice-box">
<h2>关键选择点</h2>
<button class="btn-default" onclick="defaultChoice()">继续原剧情</button>
<button class="btn-type" onclick="showTypeInput()">自定义行动</button>
<div id="type-input">
<textarea id="player-input" rows="4" placeholder="请输入你的行动..."></textarea>
<br>
<button onclick="submitType()">提交</button>
</div>
</div>
</div>
<div id="nav-hint">点击屏幕或按空格继续</div>
<script>
const scenes = {scenes_json};
let currentIndex = 0;
let playerChoice = null;

function initGame() {{
    const container = document.getElementById('game-container');
    scenes.forEach((scene, i) => {{
        const div = document.createElement('div');
        div.className = 'scene' + (i === 0 ? ' active' : '');
        div.id = 'scene-' + i;
        const imgPath = scene.image.replace(/\\\\/g, '/');
        div.innerHTML = `<img src="${{imgPath}}" alt="scene"><div class="text-overlay">${{scene.text}}</div>`;
        container.appendChild(div);
    }});
    if (scenes[0].is_key_beat) showChoice();
}}

function nextScene() {{
    if (currentIndex >= scenes.length - 1) {{
        if (playerChoice) {{
            alert('新剧情生成中...');
            fetch('/generate_branch', {{method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify({{input: playerChoice}})}}).then(r => r.json()).then(data => {{
                alert('新剧情已生成！');
            }});
        }}
        return;
    }}
    document.getElementById('scene-' + currentIndex).classList.remove('active');
    currentIndex++;
    document.getElementById('scene-' + currentIndex).classList.add('active');
    if (scenes[currentIndex].is_key_beat) setTimeout(showChoice, 1500);
}}

function showChoice() {{
    document.getElementById('choice-overlay').style.display = 'flex';
}}

function defaultChoice() {{
    document.getElementById('choice-overlay').style.display = 'none';
    nextScene();
}}

function showTypeInput() {{
    document.getElementById('type-input').style.display = 'block';
}}

function submitType() {{
    playerChoice = document.getElementById('player-input').value;
    document.getElementById('choice-overlay').style.display = 'none';
    nextScene();
}}

document.addEventListener('click', () => {{
    if (document.getElementById('choice-overlay').style.display !== 'flex') nextScene();
}});
document.addEventListener('keydown', (e) => {{
    if (e.code === 'Space' && document.getElementById('choice-overlay').style.display !== 'flex') {{
        e.preventDefault();
        nextScene();
    }}
}});

initGame();
</script>
</body>
</html>"""
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    log.run_logger.info(f"游戏网页已生成: {output_path}")
    return output_path


def main():
    """主函数：抽取关键beat、构建游戏场景、生成可运行网页"""
    with open(ALLOUPUTDIR, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    log.run_logger.info("步骤1: 抽取关键beat")
    key_beats = extract_key_beats()
    
    log.run_logger.info("步骤2: 构建游戏场景")
    game_scenes = build_game_scenes(key_beats)
    
    log.run_logger.info("步骤3: 生成游戏网页")
    html_path = generate_game_html(game_scenes, key_beats)
    
    log.run_logger.info(f"完成！请在浏览器中打开: {html_path}")


if __name__ == "__main__":
    main()
