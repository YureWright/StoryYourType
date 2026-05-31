# Story Your Type

> **这一次，由你改写所有未尽的遗憾。**

<p align="center">
  <img src="intro-animation.gif" alt="从线性到树状的蜕变动画" width="600">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/LLM-Qwen3.6--plus-blue" alt="LLM">
  <img src="https://img.shields.io/badge/Image-Wanx2.1-purple" alt="Image">
  <img src="https://img.shields.io/badge/Platform-DashScope-green" alt="Platform">
</p>

<p align="center">
  <strong>输入一本文本作品，AI 自动生成一款完整的 Galgame 游戏</strong><br>
  <em>不再预设选项，由玩家亲手书写专属结局</em>
</p>

---

## 🎬 项目理念

### 从线性到无限可能

传统的 Galgame 由开发者预设所有选项，用树状结构储存剧情分支。但开发复杂的树状结构门槛极高——尤其是对于非技术背景的创作者。

**Story Your Type 换了一种思路：**

```
线性结构（开发者搭建） → 玩家输入 → AI 实时生成 → 无限树状剧情
```

开发阶段只需搭建基础线性数据结构，那些复杂、庞大、千变万化的多结局树状剧情，全部交由每一位玩家来创造、来填充。

### 为什么做这个项目？

文学作品与历史故事里，总有太多让人耿耿于怀的意难平：

- 《红楼梦》的落幕悲歌
- 《三体》中云天明与程心那一刹的万年错过
- 《平凡的世界》里被洪水卷走的田晓霞和那本再也无法送达的日记

我们总忍不住想：**如果当初剧情稍有不同，结局会不会全然改写？**

那些让人遗憾、心生不甘的剧情，现在，你可以亲手掌控故事走向，改写既定结局，圆满心中所有的意难平。

### 核心乐趣

大语言模型的出现，彻底打破了传统游戏中**自由度与简易度**的核心矛盾：

| 维度 | 传统游戏 | Story Your Type |
|------|----------|-----------------|
| 自由度 | 受限于预设选项 | 自然语言输入，创作空间无限 |
| 反馈多样性 | 固定分支 | 寥寥数语差别，AI 生成完全不同剧情 |
| 操作门槛 | 学习成本各异 | 只要会打字，任何人都能参与 |

### 全民剧情共创

这不止是一款单机游戏，更是一场属于所有人的**全民剧情共创狂欢**。

未来将打造专属的游戏共创平台：玩家创作的原创支线会被收录整合，成为游戏常驻剧情选项。作品不再属于某一个人，而是所有玩家共同铸就的**集体创作**。

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

编辑 `config.py`，设置 API 密钥和模型：

```python
API_KEY = "your-api-key"
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL = "qwen3.6-plus"
IMG_API_KEY = "your-api-key"
IMG_MODEL = "wan2.7-image"
```

### 3. 准备输入

将小说章节放入 `input/` 目录，命名格式：`ch_01.txt`, `ch_02.txt`...

### 4. 运行流程

```bash
# 步骤1：小说转 JSON
python book2data.py

# 步骤2：数据校验
python check_data.py

# 步骤3：角色提取与合并
python extract_and_join.py

# 步骤4：生成数字资产
python asset_crea.py

# 步骤5：生成游戏网页
python asset2game.py
```

---

## 📁 项目结构

```
story-your-type/
├── input/                  # 输入小说章节（ch_01.txt, ch_02.txt...）
├── output/                 # 各章节转换后的 JSON 数据
├── assets/                 # 生成的数字资产
│   ├── character_img/      # 角色立绘
│   ├── scen_img/           # 场景图片
│   ├── beat_img/           # beat 图片
│   ├── str/                # beat 文案
│   └── fromstr/            # 中间数据
├── log_and_warn/           # 日志和警告
├── config.py               # 配置文件（API、模型、路径等）
├── book2data.py            # 小说转 JSON
├── check_data.py           # 数据校验
├── extract_and_join.py     # 角色提取与合并
├── asset_crea.py           # 数字资产生成
├── asset2game.py           # 游戏生成
└── requirements.txt        # 依赖
```

---

## 🛠️ 模块说明

### book2data.py
将小说章节转换为结构化 JSON，包含场景、节拍（对话/行为/心理/环境变化）。

### check_data.py
- `check_llm_output()` - 校验 LLM 输出是否符合 Schema
- `check_input_files()` - 校验输入文件格式和章节连续性

### extract_and_join.py
- `extract_characters()` - 提取所有角色列表
- `merge_json_files()` - 合并所有章节 JSON
- `merge_characters()` - 交互式合并角色
- `select_important_characters()` - 选择重要角色

### asset_crea.py
- `generate_character_images()` - 生成角色立绘
- `generate_scene_images()` - 生成场景图片
- `generate_beat_images()` - 生成 beat 图片（参考场景图和角色立绘）
- `generate_beat_texts()` - 生成 beat 文案

### asset2game.py
- `extract_key_beats()` - 抽取关键剧情 beat
- `build_game_scenes()` - 构建游戏场景列表
- `generate_game_html()` - 生成可交互网页游戏

---

## 📊 数据结构

```json
{
  "chapter_id": "ch1",
  "chapter_title": "第一章",
  "scenes": [
    {
      "scene_id": "s1",
      "scene_title": "场景标题",
      "time": "2024-09-01 08:00",
      "location": "地点",
      "environment_description": "环境描述",
      "beats": [
        ["dialogue", "角色名", "对话内容"],
        ["action", "角色名", "行为描述"],
        ["internal_thought", "角色名", "心理活动"],
        ["environment", "环境", "环境变化"]
      ]
    }
  ]
}
```

---

## 🎮 游戏特性

- 全屏图片展示，带淡入淡出流动效果
- 文案叠加在图片底部
- 点击或空格切换场景
- 关键剧情点提供分支选择
- 支持自定义剧情输入，AI 实时生成新故事线

---

## 💡 创作经历

这是我第一次尝试 Vibe Coding，也是第一次参与黑客松类赛事。

最初规划时，整个开发路径看起来清晰可行，但作为纯新手，在实际开发中遇到了远超预期的难题。后期因为项目体量过大、过度依赖 AI、开发顺序规划不科学等问题，整个编码过程彻底脱离了掌控，前两次开发尝试最终都半途而废。

直到第三次，复盘总结了前两次的失败经验，一步步调整优化，项目才终于迎来了可控的进展。

作品完成度虽然还有很多不足，但对我而言，这是一次珍贵的成长与尝试。未来会顺着这套核心思路，持续打磨、不断优化项目，学习更多相关知识，迭代升级作品。

---

## 🌟 未来规划

- [ ] 打造专属游戏共创平台
- [ ] 玩家原创支线收录整合
- [ ] 更多 AI 模型支持
- [ ] 更丰富的交互体验

---

## 🤝 交流反馈

游戏能改写赛博世界的故事线，而我们，正在亲手书写自己的未来。

本次创作全程一步一步摸索完成，作为新手，作品还有很多不成熟、待完善的地方。真心欢迎各位老师和同好多多批评指正，也期待和大家深入交流想法、互换思路。

---

## 📄 License

MIT
