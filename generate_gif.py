from PIL import Image, ImageDraw, ImageFont
import math
import os

frames = []
width, height = 800, 600
bg_color = (10, 10, 10)
line_color = (102, 126, 234)
colors = [
    (102, 126, 234), (118, 75, 162), (240, 147, 251), (79, 172, 254),
    (67, 233, 123), (250, 112, 154), (254, 225, 64), (48, 207, 208)
]

branch_data = [
    {'y': 450, 'angle': -30, 'length': 80, 'color': 0},
    {'y': 420, 'angle': 25, 'length': 90, 'color': 1},
    {'y': 380, 'angle': -35, 'length': 100, 'color': 2},
    {'y': 350, 'angle': 30, 'length': 110, 'color': 3},
    {'y': 320, 'angle': -25, 'length': 95, 'color': 4},
    {'y': 290, 'angle': 35, 'length': 105, 'color': 5},
    {'y': 260, 'angle': -30, 'length': 85, 'color': 6},
    {'y': 230, 'angle': 28, 'length': 95, 'color': 7},
]

total_frames = 60

for frame_idx in range(total_frames):
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    progress = frame_idx / total_frames
    
    main_line_height = min(300, progress * 400)
    draw.line([(400, 500), (400, 500 - main_line_height)], fill=line_color, width=4)
    
    branch_progress = max(0, (progress - 0.3) / 0.7)
    
    for i, data in enumerate(branch_data):
        branch_start = 0.3 + (i / len(branch_data)) * 0.5
        branch_end = branch_start + 0.15
        
        if progress < branch_start:
            continue
        
        branch_prog = min(1, (progress - branch_start) / (branch_end - branch_start))
        
        rad = math.radians(data['angle'])
        length = data['length'] * branch_prog
        
        x1, y1 = 400, data['y']
        x2 = x1 + math.sin(rad) * length
        y2 = y1 - math.cos(rad) * length * 0.5
        
        color = colors[data['color']]
        draw.line([(x1, y1), (x2, y2)], fill=color, width=3)
        
        if i % 2 == 0 and branch_prog > 0.5:
            sub_prog = (branch_prog - 0.5) * 2
            sub_angle = data['angle'] + (40 if i % 4 == 0 else -40)
            sub_rad = math.radians(sub_angle)
            sub_length = 60 * sub_prog
            
            sx2 = x2 + math.sin(sub_rad) * sub_length
            sy2 = y2 - math.cos(sub_rad) * sub_length
            
            sub_color = colors[(data['color'] + 2) % len(colors)]
            draw.line([(x2, y2), (sx2, sy2)], fill=sub_color, width=2)
    
    if progress > 0.85:
        alpha = min(255, int((progress - 0.85) / 0.15 * 255))
        try:
            font = ImageFont.truetype("msyh.ttc", 36)
        except:
            font = ImageFont.load_default()
        
        text = "从线性到无限可能"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        draw.text(((width - text_width) // 2, 520), text, fill=(255, 255, 255, alpha), font=font)
    
    frames.append(img)

output_path = os.path.join(os.path.dirname(__file__), 'intro-animation.gif')
frames[0].save(
    output_path,
    save_all=True,
    append_images=frames[1:],
    duration=50,
    loop=0,
    optimize=True
)

print(f"GIF 已生成: {output_path}")
