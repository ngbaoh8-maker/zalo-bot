# -*- coding: utf-8 -*-
import os
import json
import random
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from zlapi.models import Message
from modules.menu import get_font, get_bg_image, autosave, _smart_resize

des = {
    'version': "4.1.6",
    'credits': "ngbao",
    'description': "Game rắn ăn mồi",
    'power': "Thành Viên"
}

CACHE_DIR = "modules/cache"
CACHE_FILE = os.path.join(CACHE_DIR, "snake_games.json")
os.makedirs(CACHE_DIR, exist_ok=True)

BOARD_W = 15
BOARD_H = 15
CELL = 42
MARGIN = 20

def load_games():
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_games(data):
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def random_empty_cell(snake):
    attempts = 0
    while True:
        attempts += 1
        x = random.randrange(0, BOARD_W)
        y = random.randrange(0, BOARD_H)
        if (x, y) not in snake:
            return (x, y)
        if attempts > 500:
            for yy in range(BOARD_H):
                for xx in range(BOARD_W):
                    if (xx, yy) not in snake:
                        return (xx, yy)
            return (0, 0)

def make_initial_snake():
    midx = BOARD_W // 2
    midy = BOARD_H // 2
    return [(midx, midy), (midx-1, midy), (midx-2, midy)]

def dir_to_delta(d):
    return {'up': (0, -1), 'w': (0,-1),
            'down': (0, 1), 's': (0,1),
            'left': (-1, 0), 'a': (-1,0),
            'right': (1, 0), 'd': (1,0)}.get(d.lower())

def _add_safe_padding(img, bg_color=(20, 15, 30, 255)):
    w, h = img.size
    ratio = w / h
    target_ratio = 1.0
    if ratio < target_ratio:
        new_w = int(h * target_ratio)
        new_img = Image.new("RGBA", (new_w, h), bg_color)
        offset = (new_w - w) // 2
        new_img.paste(img, (offset, 0))
        return new_img
    return img

def draw_snake_board(state, title=None):
    width = MARGIN*2 + CELL * BOARD_W
    height = MARGIN*2 + CELL * BOARD_H + 110
    bg = get_bg_image((width, height)).convert("RGBA")
    overlay = Image.new("RGBA", (width, height), (12,6,24,200))
    bg.alpha_composite(overlay)

    draw = ImageDraw.Draw(bg)
    font_title = get_font(36)
    hdr = title or "Snake — Kim Thanh"
    draw.text((MARGIN, 10), hdr, font=font_title, fill=(230,200,255,255), stroke_width=2, stroke_fill=(0,0,0,160))

    panel_x0 = MARGIN
    panel_y0 = MARGIN + 50
    panel_x1 = panel_x0 + CELL * BOARD_W
    panel_y1 = panel_y0 + CELL * BOARD_H

    shadow = Image.new("RGBA", bg.size, (0,0,0,0))
    sd = ImageDraw.Draw(shadow)
    for i in range(8):
        alpha = int(70*(1 - i/8))
        sd.rectangle([panel_x0+i, panel_y0+i, panel_x1+i, panel_y1+i], fill=(0,0,0,alpha))
    shadow = shadow.filter(ImageFilter.GaussianBlur(6))
    bg.alpha_composite(shadow)

    draw.rounded_rectangle([panel_x0, panel_y0, panel_x1, panel_y1], radius=12, fill=(30,20,40,255), outline=(95,60,140,200), width=2)

    for y in range(BOARD_H):
        for x in range(BOARD_W):
            x0 = panel_x0 + x*CELL
            y0 = panel_y0 + y*CELL
            rect = [x0+2, y0+2, x0+CELL-2, y0+CELL-2]
            draw.rectangle(rect, fill=(28,22,36,255) if (x+y)%2==0 else (22,16,32,255))

    fx, fy = state['food']
    fx0 = panel_x0 + fx*CELL + CELL//2
    fy0 = panel_y0 + fy*CELL + CELL//2
    r = CELL//3
    draw.ellipse([fx0-r-6, fy0-r-6, fx0+r+6, fy0+r+6], fill=(255,160,80,60))
    draw.ellipse([fx0-r, fy0-r, fx0+r, fy0+r], fill=(255,120,70,255), outline=(255,200,140,200), width=3)

    snake = state['snake']
    for i, seg in enumerate(snake):
        sx, sy = seg
        x0 = panel_x0 + sx*CELL + 6
        y0 = panel_y0 + sy*CELL + 6
        if i == 0:
            draw.rounded_rectangle([x0, y0, x0+CELL-12, y0+CELL-12], radius=10, fill=(200,230,120,255), outline=(255,255,255,180), width=3)
            ex = x0 + CELL//3
            ey = y0 + CELL//3
            draw.ellipse([ex-4, ey-2, ex+4, ey+6], fill=(20,20,30,255))
            draw.ellipse([ex+8, ey-2, ex+16, ey+6], fill=(20,20,30,255))
        else:
            draw.rounded_rectangle([x0, y0, x0+CELL-12, y0+CELL-12], radius=8, fill=(120,200 - i%10, 140, 255))

    score = state.get('score', 0)
    font_f = get_font(20)
    draw.text((MARGIN, height-70), f"Điểm: {score}   Độ dài: {len(snake)}", font=font_f, fill=(220,220,240,230))
    draw.text((MARGIN, height-40), "Thao Tác: .snake w/a/s/d (hoặc w2/a2/s2/d2)", font=font_f, fill=(180,180,200,200))

    safe_img = _add_safe_padding(_smart_resize(bg, width, height))
    path = autosave(safe_img)
    return path

def move_snake(state, steps=1):
    """Di chuyển rắn `steps` bước. Trả về (msg, ate_count)."""
    ate_count = 0
    for _ in range(steps):
        dx, dy = dir_to_delta(state['dir'])
        head = state['snake'][0]
        new_head = (head[0] + dx, head[1] + dy)
        hx, hy = new_head

        if not (0 <= hx < BOARD_W and 0 <= hy < BOARD_H):
            state['game_over'] = True
            return "💀 Bạn đâm vào tường!", ate_count
        if new_head in state['snake']:
            state['game_over'] = True
            return "💀 Bạn cắn phải mình!", ate_count

        state['snake'].insert(0, new_head)
        if new_head == tuple(state['food']):
            state['score'] += 1
            ate_count += 1
            state['food'] = random_empty_cell(state['snake'])
        else:
            state['snake'].pop()
    return None, ate_count

def handle_snake_command(message, message_object, thread_id, thread_type, author_id, client):
    TTL = 300000
    parts = message.strip().split()
    if len(parts) == 1 or parts[1].lower() in ['help','h']:
        help_text = (
            "🐍 HƯỚNG DẪN CHƠI SNAKE\n"
            ".snake start     ➜     Bắt đầu game\n"
            ".snake w/a/s/d ➜ Di chuyển\n\n"
            " W ➜ Đi Lên / S ➜ Đi Xuống / A ➜ Đi Trái / D ➜ Đi Phải\n"
            "⚠️ Lưu Ý : Không Thể Quay Ngược Lại Khi Không Cùng Chiều\n"
            ".snake stop   ➜ Kết thúc game\n"
            ".snake score  ➜ Điểm cao của bạn\n"
            "Đi 2 Bước Nhập Vidu `<a2>`\n"
        )
        client.replyMessage(Message(help_text), message_object, thread_id, thread_type, ttl=TTL)
        return

    sub = parts[1].lower()
    games = load_games()
    uid = str(author_id)
    state = games.get(uid)

    if sub == "start":
        if state and not state.get('game_over', False):
            client.replyMessage(Message("❗ Bạn đang có game chưa kết thúc. Dùng .snake stop để dừng."), message_object, thread_id, thread_type, ttl=TTL)
            return
        snake = make_initial_snake()
        food = random_empty_cell(snake)
        state = {"snake": snake, "dir": "right", "food": food, "score": 0, "game_over": False}
        games[uid] = state
        save_games(games)
        path = draw_snake_board(state, "Snake - Bắt đầu")
        client.sendLocalImage(path, thread_id=thread_id, thread_type=thread_type, ttl=TTL)
        os.remove(path)
        client.replyMessage(Message("✅ Game started! Dùng .snake w/a/s/d để chơi!"), message_object, thread_id, thread_type, ttl=TTL)
        return

    if sub == "stop":
        if not state:
            client.replyMessage(Message("❗ Bạn chưa có game nào."), message_object, thread_id, thread_type, ttl=TTL)
            return
        games.pop(uid, None)
        save_games(games)
        client.replyMessage(Message("🛑 Game stopped."), message_object, thread_id, thread_type, ttl=TTL)
        return

    if sub == "score":
        if not state:
            client.replyMessage(Message("❗ Bạn chưa có game. Dùng .snake start để bắt đầu."), message_object, thread_id, thread_type, ttl=TTL)
            return
        client.replyMessage(Message(f"🏆 Điểm: {state['score']} • Độ dài: {len(state['snake'])}"), message_object, thread_id, thread_type, ttl=TTL)
        return

    dirs = ["up","down","left","right","w","a","s","d"]
    dirs2 = [d+"2" for d in dirs]
    if sub in dirs + dirs2:
        if not state or state.get('game_over', False):
            client.replyMessage(Message("❗ Bạn chưa có game đang chạy. Dùng .snake start để bắt đầu."), message_object, thread_id, thread_type, ttl=TTL)
            return
        steps = 2 if sub.endswith("2") else 1
        new_dir = sub.rstrip("2")
        state['dir'] = new_dir if new_dir in ['up','down','left','right'] else {'w':'up','s':'down','a':'left','d':'right'}.get(new_dir, 'right')

        msg, ate_count = move_snake(state, steps)
        games[uid] = state
        save_games(games)

        title = "Game Over" if state.get('game_over') else f"Score: {state['score']}"
        path = draw_snake_board(state, title)
        client.sendLocalImage(path, thread_id=thread_id, thread_type=thread_type, ttl=TTL)
        os.remove(path)

        if msg:
            client.replyMessage(Message(msg + f" • Điểm: {state['score']}"), message_object, thread_id, thread_type, ttl=TTL)
        else:
            if ate_count > 0:
                client.replyMessage(Message(f"🍎 Bạn ăn được {ate_count} mồi! +{ate_count} điểm."), message_object, thread_id, thread_type, ttl=TTL)
            else:
                step_txt = "đã đi 2 bước 🐍" if steps == 2 else "đã đi 1 bước 🐍"
                client.replyMessage(Message(f"✅ Rắn {step_txt}"), message_object, thread_id, thread_type, ttl=TTL)
        return

    client.replyMessage(Message("❌ Lệnh không hợp lệ. Gõ `{prefix}snake help` để xem hướng dẫn."), message_object, thread_id, thread_type, ttl=TTL)

def PTA():
    return {'snake': handle_snake_command}