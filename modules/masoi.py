# -*- coding: utf-8 -*-
import random, threading, time, json, os
from zlapi.models import Message, MultiMsgStyle, MessageStyle, Mention, ThreadType
from config import ADMIN
from modules.masoi_game import (
    WerewolfGame, active_games, wolf_boxes,
    save_wolfbox, load_wolfbox, ROLE_NAMES, ROLE_DESC, COLORS
)

des = {
    'version': "2.0.0",
    'credits': "Bot Ma Sói",
    'description': "Game Ma Sói tự động trên Zalo",
    'power': "Thành viên"
}

def send_color_msg(client, thread_id, thread_type, text, mentions=None):
    lines = text.strip().split('\n')
    colors = COLORS[:]
    random.shuffle(colors)
    styles_list = []
    current_offset = 0
    for i, line in enumerate(lines):
        if not line:
            current_offset += 1
            continue
        c = colors[i % len(colors)]
        styles_list.append(MessageStyle(offset=current_offset, length=len(line), style="color", color=c, auto_format=False))
        styles_list.append(MessageStyle(offset=current_offset, length=len(line), style="bold", auto_format=False))
        current_offset += len(line) + 1
    style = MultiMsgStyle(styles_list) if styles_list else None
    msg = Message(text=text, style=style)
    if mentions:
        msg.mentions = mentions
    client.send(msg, thread_id, thread_type)

def get_name(client, uid):
    try:
        info = client.fetchUserInfo(uid)
        return info.changed_profiles[uid].zaloName
    except:
        return "Người chơi"

def check_friend(client, uid):
    """Kiểm tra KB bằng fetchAllFriends - lấy danh sách bạn bè thực tế"""
    try:
        friends = client.fetchAllFriends()
        if isinstance(friends, list):
            for f in friends:
                fid = getattr(f, 'userId', None) or getattr(f, 'uid', None)
                if fid is None and isinstance(f, dict):
                    fid = f.get('userId') or f.get('uid')
                if str(fid) == str(uid):
                    return True
        return False
    except:
        return False

def auto_add_friend(client, uid, name):
    """Check KB thật, nếu chưa KB thì gửi lời mời và return False"""
    is_friend = check_friend(client, uid)
    if not is_friend:
        try:
            client.sendFriendRequest(uid, f"Kết bạn để chơi Ma Sói nhé {name}!")
        except:
            pass
        return False
    return True

# ====== SETBOX SOI (Admin only) ======
def handle_setbox(msg, message_object, thread_id, thread_type, author_id, client):
    if str(author_id) not in [str(a) for a in (ADMIN if isinstance(ADMIN, list) else [ADMIN])]:
        send_color_msg(client, thread_id, thread_type, "🚫 Chỉ admin mới dùng được lệnh này!")
        return
    parts = msg.strip().split()
    if len(parts) < 2:
        send_color_msg(client, thread_id, thread_type, "📌 Cú pháp:\n!setbox soi <ID box sói> → Set box\n!setbox huy → Hủy box sói")
        return

    action = parts[1].lower()

    # !setbox huy → Hủy box sói đã set
    if action == "huy":
        if thread_id in wolf_boxes:
            del wolf_boxes[thread_id]
            save_wolfbox()
            send_color_msg(client, thread_id, thread_type, "✅ Đã hủy box sói cho nhóm này!")
        else:
            send_color_msg(client, thread_id, thread_type, "⚠️ Nhóm này chưa set box sói!")
        return

    # !setbox soi <ID> → Set box sói
    if action == "soi":
        if len(parts) < 3:
            # Nếu không có ID, hiện box đang set
            current = wolf_boxes.get(thread_id)
            if current:
                send_color_msg(client, thread_id, thread_type, f"📌 Box sói hiện tại: {current}\nDùng !setbox huy để hủy")
            else:
                send_color_msg(client, thread_id, thread_type, "📌 Cú pháp: !setbox soi <ID box sói>")
            return
        wolf_box_id = parts[2]
        wolf_boxes[thread_id] = wolf_box_id
        save_wolfbox()
        send_color_msg(client, thread_id, thread_type,
            f"✅ Đã set box sói: {wolf_box_id}\n"
            f"📁 Đã lưu vào file, tắt/bật bot vẫn giữ!\n"
            f"Dùng !setbox huy để hủy")
        return

    send_color_msg(client, thread_id, thread_type, "📌 Cú pháp:\n!setbox soi <ID box sói> → Set box\n!setbox huy → Hủy box sói")

# ====== MAIN HANDLER ======
def handle_masoi(msg, message_object, thread_id, thread_type, author_id, client):
    parts = msg.strip().split()
    if len(parts) < 2:
        send_color_msg(client, thread_id, thread_type,
            "🐺 MA SÓI - HƯỚNG DẪN 🐺\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "!masoi tao → Tạo phòng\n"
            "!masoi thamgia → Tham gia\n"
            "!masoi batdau → Bắt đầu game\n"
            "!masoi giet <STT> → Sói giết (đêm)\n"
            "!masoi soi <STT> → Tiên tri soi (đêm)\n"
            "!masoi bv <STT> → Bảo vệ (đêm)\n"
            "!masoi ban <STT> → Thợ săn bắn (khi chết)\n"
            "!masoi stop → Dừng game\n"
            "!setbox soi <ID> → Set box sói (admin)\n"
            "━━━━━━━━━━━━━━━━━━")
        return

    sub = parts[1].lower()

    if sub == "help":
        cmd_help(thread_id, thread_type, client)
    elif sub == "tao":
        cmd_tao(thread_id, thread_type, author_id, client, message_object)
    elif sub == "thamgia":
        cmd_join(thread_id, thread_type, author_id, client, message_object)
    elif sub == "batdau":
        cmd_start(thread_id, thread_type, author_id, client, message_object)
    elif sub == "giet":
        stt = int(parts[2]) if len(parts) > 2 else None
        cmd_wolf_kill(thread_id, thread_type, author_id, client, message_object, stt)
    elif sub == "soi":
        stt = int(parts[2]) if len(parts) > 2 else None
        cmd_seer(thread_id, thread_type, author_id, client, message_object, stt)
    elif sub == "bv":
        stt = int(parts[2]) if len(parts) > 2 else None
        cmd_guard(thread_id, thread_type, author_id, client, message_object, stt)
    elif sub == "ban":
        stt = int(parts[2]) if len(parts) > 2 else None
        cmd_hunter(thread_id, thread_type, author_id, client, message_object, stt)
    elif sub == "stop":
        cmd_stop(thread_id, thread_type, author_id, client, message_object)
    else:
        send_color_msg(client, thread_id, thread_type, "❌ Lệnh không hợp lệ! Gõ !masoi help để xem hướng dẫn.")

def cmd_help(thread_id, thread_type, client):
    send_color_msg(client, thread_id, thread_type,
        "🐺 MA SÓI - TẤT CẢ LỆNH 🐺\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 LỆNH CƠ BẢN:\n"
        "  !masoi help → Xem tất cả lệnh\n"
        "  !masoi tao → Tạo phòng mới\n"
        "  !masoi thamgia → Tham gia phòng\n"
        "  !masoi batdau → Bắt đầu game\n"
        "  !masoi stop → Dừng game\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🌙 LỆNH BAN ĐÊM (IB riêng):\n"
        "  !masoi giet <STT> → 🐺 Sói chọn giết\n"
        "  !masoi soi <STT> → 🔮 Tiên tri soi vai\n"
        "  !masoi bv <STT> → 🛡️ Bảo vệ cứu người\n"
        "  !masoi ban <STT> → 🏹 Thợ săn bắn (khi chết)\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚙️ LỆNH ADMIN:\n"
        "  !setbox soi <ID> → Set box sói\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎭 CÁC VAI TRÒ:\n"
        "  🐺 Sói → Giết người ban đêm\n"
        "  🔮 Tiên Tri → Soi vai ban đêm\n"
        "  🛡️ Bảo Vệ → Bảo vệ 1 người\n"
        "  🏹 Thợ Săn → Bắn khi chết\n"
        "  👨‍🌾 Dân Làng → Vote treo cổ sói\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📋 LUẬT CHƠI:\n"
        "  • Tối đa 6 người, tối thiểu 3\n"
        "  • Đêm: Khóa chat, các vai hành động\n"
        "  • Sáng: Mở chat, thảo luận 5 phút\n"
        "  • Vote: Tạo poll bình chọn treo cổ\n"
        "  • Sói hết = Dân thắng\n"
        "  • Sói >= Dân = Sói thắng\n"
        "━━━━━━━━━━━━━━━━━━━━━━━")

def cmd_tao(thread_id, thread_type, author_id, client, mo):
    if thread_id in active_games and active_games[thread_id].phase != "ended":
        send_color_msg(client, thread_id, thread_type, "⚠️ Đang có game trong phòng này!")
        return
    game = WerewolfGame()
    game.thread_id = thread_id
    game.creator_id = author_id
    name = get_name(client, author_id)
    game.add_player(author_id, name)
    active_games[thread_id] = game
    send_color_msg(client, thread_id, thread_type,
        f"🐺 PHÒNG MA SÓI ĐÃ TẠO 🐺\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 Chủ phòng: {name}\n"
        f"👥 Người chơi: 1/6\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Gõ !masoi thamgia để vào!\n"
        f"Gõ !masoi batdau khi đủ người!")

def cmd_join(thread_id, thread_type, author_id, client, mo):
    game = active_games.get(thread_id)
    if not game or game.phase != "waiting":
        send_color_msg(client, thread_id, thread_type, "❌ Chưa có phòng! Gõ !masoi tao")
        return
    name = get_name(client, author_id)
    # Check KB thật
    is_friend = auto_add_friend(client, author_id, name)
    if not is_friend:
        mention = Mention(uid=author_id, offset=0, length=len(f"@{name}"))
        send_color_msg(client, thread_id, thread_type,
            f"@{name}\n⚠️ Bạn chưa kết bạn với bot!\n📩 Bot đã gửi lời mời KB, hãy chấp nhận rồi gõ lại !masoi thamgia",
            mentions=[mention])
        return
    ok, msg = game.add_player(author_id, name)
    plist = game.get_player_list_text(show_dead=False)
    send_color_msg(client, thread_id, thread_type,
        f"🐺 PHÒNG MA SÓI 🐺\n━━━━━━━━━━━━━━━━━━\n{msg}\n\n📋 DANH SÁCH:\n{plist}\n━━━━━━━━━━━━━━━━━━")

def cmd_start(thread_id, thread_type, author_id, client, mo):
    game = active_games.get(thread_id)
    if not game or game.phase != "waiting":
        send_color_msg(client, thread_id, thread_type, "❌ Không có phòng chờ!")
        return
    if author_id != game.creator_id:
        send_color_msg(client, thread_id, thread_type, "❌ Chỉ chủ phòng mới bắt đầu được!")
        return
    if len(game.players) < 3:
        send_color_msg(client, thread_id, thread_type, "❌ Cần ít nhất 3 người!")
        return

    ok, msg = game.assign_roles()
    if not ok:
        send_color_msg(client, thread_id, thread_type, f"❌ {msg}")
        return

    # Send roles privately to each player
    for uid, p in game.players.items():
        role_desc = ROLE_DESC.get(p["role"], "Vai trò không xác định")
        role_name = ROLE_NAMES.get(p["role"], p["role"])
        try:
            send_color_msg(client, uid, ThreadType.USER,
                f"🐺 MA SÓI - VAI TRÒ CỦA BẠN 🐺\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🎭 Vai: {role_name}\n"
                f"📝 {role_desc}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"Chúc bạn chơi vui! 🎮")
        except:
            pass

    # Show roles summary (not who has what)
    roles_summary = game.get_roles_summary()
    plist = game.get_player_list_text(show_dead=False)

    # Build mentions for all players
    mentions = []
    mention_text_parts = []
    offset = 0
    for uid, p in game.players.items():
        tag = f"@{p['name']}"
        mentions.append(Mention(uid=uid, offset=offset, length=len(tag)))
        mention_text_parts.append(tag)
        offset += len(tag) + 1

    mention_line = " ".join(mention_text_parts)

    send_color_msg(client, thread_id, thread_type,
        f"{mention_line}\n"
        f"🐺 GAME MA SÓI BẮT ĐẦU! 🐺\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📋 Người chơi:\n{plist}\n\n"
        f"🎭 Chức năng trong trận:\n{roles_summary}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📩 Vai trò đã gửi riêng cho mỗi người!\n"
        f"🌙 Đêm bắt đầu... Khóa chat!",
        mentions=mentions)

    # Add wolves to wolf box
    wolf_box = wolf_boxes.get(thread_id)
    wolves = game.get_wolves()
    
    # Auto-create wolf box if not set
    if not wolf_box:
        try:
            group_name = f"🐺 Hang Sói - {str(thread_id)[-4:]}"
            wolf_uids = list(wolves.keys())
            res = client.createGroup(name=group_name, members=wolf_uids)
            if res and isinstance(res, dict) and "groupId" in res:
                wolf_box = str(res["groupId"])
            elif res and hasattr(res, "groupId"):
                wolf_box = str(res.groupId)
                
            if wolf_box:
                wolf_boxes[thread_id] = wolf_box
                save_wolfbox()
                send_color_msg(client, thread_id, ThreadType.GROUP, "✅ Đã tự động tạo Hang Sói cho ván này!")
        except Exception as e:
            pass

    if wolf_box:
        for wuid in wolves:
            try:
                client.addUsersToGroup(wuid, wolf_box)
            except:
                pass
        # Send target list to wolf box
        non_wolf_list = game.get_non_wolf_list()
        send_color_msg(client, wolf_box, ThreadType.GROUP,
            f"🐺 DANH SÁCH MỤC TIÊU 🐺\n━━━━━━━━━━━━━━━━━━\n{non_wolf_list}\n━━━━━━━━━━━━━━━━━━\nDùng: !masoi giet <STT>")

    # Lock chat & start night
    game.phase = "night"
    game.round_num = 1
    try:
        client.changeGroupSetting(thread_id, lockSendMsg=1)
    except:
        pass

    # Night timer - 2 minutes then auto process
    def night_timer():
        time.sleep(120)
        if game.phase == "night":
            process_dawn(thread_id, client, game)

    game.timer_thread = threading.Thread(target=night_timer, daemon=True)
    game.timer_thread.start()

def cmd_wolf_kill(thread_id, thread_type, author_id, client, mo, stt):
    # Check if command from wolf box or main thread
    game = None
    main_tid = None
    for tid, g in active_games.items():
        if g.phase == "night" and author_id in g.get_wolves():
            game = g
            main_tid = tid
            break
    if not game:
        send_color_msg(client, thread_id, thread_type, "❌ Không có game đang ở pha đêm!")
        return
    if not stt:
        send_color_msg(client, thread_id, thread_type, "❌ Dùng: !masoi giet <STT>")
        return
    target_uid, target_p = game.get_player_by_stt(stt)
    if not target_uid or not target_p["alive"]:
        send_color_msg(client, thread_id, thread_type, "❌ STT không hợp lệ hoặc đã chết!")
        return
    if target_p["role"] == "soi":
        send_color_msg(client, thread_id, thread_type, "❌ Không thể giết đồng đội sói!")
        return
    game.wolf_votes[author_id] = stt
    wolves = game.get_wolves()
    if len(game.wolf_votes) >= len(wolves):
        send_color_msg(client, thread_id, thread_type, f"🐺 Tất cả sói đã chọn! Mục tiêu: STT {stt}")
        # Auto process if all roles done
        check_all_night_done(main_tid, client, game)
    else:
        send_color_msg(client, thread_id, thread_type, f"🐺 Đã ghi nhận! Đợi sói khác...")

def cmd_seer(thread_id, thread_type, author_id, client, mo, stt):
    game = find_game_for_player(author_id)
    if not game or game.phase != "night":
        send_color_msg(client, thread_id, thread_type, "❌ Không phải pha đêm!")
        return
    if game.players.get(author_id, {}).get("role") != "tien_tri":
        send_color_msg(client, thread_id, thread_type, "❌ Bạn không phải Tiên Tri!")
        return
    if not stt:
        send_color_msg(client, thread_id, thread_type, "❌ Dùng: !masoi soi <STT>")
        return
    target_uid, target_p = game.get_player_by_stt(stt)
    if not target_uid or not target_p["alive"]:
        send_color_msg(client, thread_id, thread_type, "❌ STT không hợp lệ!")
        return
    game.seer_target = stt
    is_wolf = target_p["role"] == "soi"
    result = "🐺 SÓI!" if is_wolf else "👨‍🌾 KHÔNG PHẢI SÓI"
    send_color_msg(client, author_id, ThreadType.USER,
        f"🔮 KẾT QUẢ SOI\n{target_p['name']} là: {result}")
    main_tid = find_main_thread(author_id)
    if main_tid:
        check_all_night_done(main_tid, client, game)

def cmd_guard(thread_id, thread_type, author_id, client, mo, stt):
    game = find_game_for_player(author_id)
    if not game or game.phase != "night":
        send_color_msg(client, thread_id, thread_type, "❌ Không phải pha đêm!")
        return
    if game.players.get(author_id, {}).get("role") != "bao_ve":
        send_color_msg(client, thread_id, thread_type, "❌ Bạn không phải Bảo Vệ!")
        return
    if not stt:
        send_color_msg(client, thread_id, thread_type, "❌ Dùng: !masoi bv <STT>")
        return
    if stt == game.last_guard:
        send_color_msg(client, thread_id, thread_type, "❌ Không thể bảo vệ cùng 1 người 2 đêm liên tiếp!")
        return
    game.guard_target = stt
    send_color_msg(client, author_id, ThreadType.USER, f"🛡️ Đã bảo vệ STT {stt}!")
    main_tid = find_main_thread(author_id)
    if main_tid:
        check_all_night_done(main_tid, client, game)

def cmd_hunter(thread_id, thread_type, author_id, client, mo, stt):
    game = find_game_for_player(author_id)
    if not game:
        return
    if game.hunter_pending != author_id:
        send_color_msg(client, thread_id, thread_type, "❌ Bạn không có quyền bắn!")
        return
    if not stt:
        send_color_msg(client, thread_id, thread_type, "❌ Dùng: !masoi ban <STT>")
        return
    target_uid, target_p = game.get_player_by_stt(stt)
    if not target_uid or not target_p["alive"]:
        send_color_msg(client, thread_id, thread_type, "❌ STT không hợp lệ!")
        return
    target_p["alive"] = False
    game.hunter_pending = None
    main_tid = find_main_thread(author_id)
    if main_tid:
        send_color_msg(client, main_tid, ThreadType.GROUP,
            f"🏹 Thợ săn đã bắn chết {target_p['name']}!")
        check_win_and_end(main_tid, client, game)

def cmd_stop(thread_id, thread_type, author_id, client, mo):
    game = active_games.get(thread_id)
    if not game:
        send_color_msg(client, thread_id, thread_type, "❌ Không có game!")
        return
    admins = ADMIN if isinstance(ADMIN, list) else [ADMIN]
    if author_id != game.creator_id and str(author_id) not in [str(a) for a in admins]:
        send_color_msg(client, thread_id, thread_type, "❌ Chỉ chủ phòng/admin dừng được!")
        return
    end_game(thread_id, client, game, "⛔ Game đã bị dừng!")

def find_game_for_player(uid):
    for tid, g in active_games.items():
        if uid in g.players:
            return g
    return None

def find_main_thread(uid):
    for tid, g in active_games.items():
        if uid in g.players:
            return tid
    return None

def check_all_night_done(thread_id, client, game):
    wolves = game.get_wolves()
    all_wolves_voted = len(game.wolf_votes) >= len(wolves)
    # Check seer
    seer_done = True
    guard_done = True
    for uid, p in game.players.items():
        if p["role"] == "tien_tri" and p["alive"] and not game.seer_target:
            seer_done = False
        if p["role"] == "bao_ve" and p["alive"] and game.guard_target is None:
            guard_done = False
    if all_wolves_voted and seer_done and guard_done:
        process_dawn(thread_id, client, game)

def process_dawn(thread_id, client, game):
    if game.phase != "night":
        return
    game.phase = "day"
    killed_uid, killed_name, seer_result, protected = game.process_night()

    # Unlock chat
    try:
        client.changeGroupSetting(thread_id, lockSendMsg=0)
    except:
        pass

    # Build announcement
    if killed_uid:
        death_msg = f"💀 {killed_name} đã bị sói giết!"
    elif protected:
        death_msg = "🛡️ Bảo vệ đã cứu sống 1 người! Không ai chết đêm nay!"
    else:
        death_msg = "😇 Không ai chết đêm nay!"

    alive_list = game.get_player_list_text()

    # Mention alive players
    mentions = []
    mention_parts = []
    offset = 0
    for uid, p in game.players.items():
        if p["alive"]:
            tag = f"@{p['name']}"
            mentions.append(Mention(uid=uid, offset=offset, length=len(tag)))
            mention_parts.append(tag)
            offset += len(tag) + 1
    mention_line = " ".join(mention_parts)

    send_color_msg(client, thread_id, ThreadType.GROUP,
        f"{mention_line}\n"
        f"☀️ TRỜI SÁNG - NGÀY {game.round_num} ☀️\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{death_msg}\n\n"
        f"📋 Danh sách:\n{alive_list}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💬 Thảo luận 5 phút!\nSau đó sẽ tạo bình chọn treo cổ!",
        mentions=mentions)

    # Check win
    winner = game.check_win()
    if winner:
        end_game(thread_id, client, game,
            f"🐺 SÓI THẮNG!" if winner == "soi" else "👨‍🌾 DÂN LÀNG THẮNG!")
        return

    # Hunter pending
    if game.hunter_pending:
        hunter_name = game.players[game.hunter_pending]["name"]
        try:
            send_color_msg(client, game.hunter_pending, ThreadType.USER,
                f"🏹 Bạn đã chết! Hãy chọn 1 người bắn theo!\nDùng: !masoi ban <STT>")
        except:
            pass

    # Day timer: 5 min discuss then create poll
    def day_flow():
        time.sleep(300)  # 5 min
        if game.phase != "day":
            return
        create_vote_poll(thread_id, client, game)

    threading.Thread(target=day_flow, daemon=True).start()

def create_vote_poll(thread_id, client, game):
    if game.phase != "day":
        return
    game.phase = "voting"
    alive = game.get_alive_players()
    options = [f"{p['stt']}. {p['name']}" for uid, p in alive.items()]

    try:
        result = client.createPoll(
            question=f"🗳️ BÌNH CHỌN TREO CỔ - Ngày {game.round_num}",
            options=options,
            groupId=thread_id,
            expiredTime=0,
            pinAct=True,
            multiChoices=False,
            allowAddNewOption=False,
            hideVotePreview=False,
            isAnonymous=False
        )
        
        # Save poll_id to lock it later
        if result:
            if isinstance(result, dict) and "poll_id" in result:
                game.vote_poll_id = result["poll_id"]
            elif hasattr(result, "poll_id"):
                game.vote_poll_id = result.poll_id
            elif isinstance(result, dict) and "pollId" in result:
                game.vote_poll_id = result["pollId"]
            elif hasattr(result, "pollId"):
                game.vote_poll_id = result.pollId

        send_color_msg(client, thread_id, ThreadType.GROUP,
            "🗳️ BÌNH CHỌN ĐÃ TẠO!\n━━━━━━━━━━━━━━━━━━\nHãy vote người bạn nghi là sói!\n⏰ 2 phút để bình chọn!")
    except Exception as e:
        send_color_msg(client, thread_id, ThreadType.GROUP,
            f"⚠️ Không tạo được poll: {e}\nDùng !masoi vote <STT> để vote thủ công!")

    # 2 min then process vote
    def vote_timer():
        time.sleep(120)
        if game.phase == "voting":
            process_vote_result(thread_id, client, game)
    threading.Thread(target=vote_timer, daemon=True).start()

def process_vote_result(thread_id, client, game):
    # Lock chat & lock poll
    try:
        client.changeGroupSetting(thread_id, lockSendMsg=1)
    except:
        pass
        
    try:
        if hasattr(game, "vote_poll_id") and game.vote_poll_id:
            client.lockPoll(game.vote_poll_id)
            game.vote_poll_id = None
    except:
        pass

    # Since we can't easily read poll results, announce and move to night
    send_color_msg(client, thread_id, ThreadType.GROUP,
        f"⏰ Hết giờ bình chọn!\n🌙 Đêm {game.round_num + 1} bắt đầu...\n━━━━━━━━━━━━━━━━━━\nCác vai trò hãy hành động qua tin nhắn riêng!")

    game.phase = "night"
    game.round_num += 1

    # Send wolf box update
    wolf_box = wolf_boxes.get(thread_id)
    if wolf_box:
        non_wolf_list = game.get_non_wolf_list()
        send_color_msg(client, wolf_box, ThreadType.GROUP,
            f"🐺 ĐÊM {game.round_num} 🐺\n━━━━━━━━━━━━━━━━━━\n{non_wolf_list}\n━━━━━━━━━━━━━━━━━━\nDùng: !masoi giet <STT>")

    # Night timer
    def night_timer():
        time.sleep(120)
        if game.phase == "night":
            process_dawn(thread_id, client, game)
    threading.Thread(target=night_timer, daemon=True).start()

def check_win_and_end(thread_id, client, game):
    winner = game.check_win()
    if winner:
        end_game(thread_id, client, game,
            "🐺 SÓI THẮNG!" if winner == "soi" else "👨‍🌾 DÂN LÀNG THẮNG!")

def end_game(thread_id, client, game, result_msg):
    game.phase = "ended"
    # Unlock chat
    try:
        client.changeGroupSetting(thread_id, lockSendMsg=0)
    except:
        pass

    # Show all roles
    role_reveal = []
    for uid, p in game.players.items():
        rname = ROLE_NAMES.get(p["role"], p["role"])
        status = "💀" if not p["alive"] else "✅"
        role_reveal.append(f"  {p['stt']}. {p['name']} → {rname} {status}")
    reveal_text = "\n".join(role_reveal)

    send_color_msg(client, thread_id, ThreadType.GROUP,
        f"🏆 KẾT QUẢ GAME 🏆\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{result_msg}\n\n"
        f"🎭 Vai trò:\n{reveal_text}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Cảm ơn đã chơi! Gõ !masoi tao để chơi lại!")

    # Kick all from wolf box
    wolf_box = wolf_boxes.get(thread_id)
    if wolf_box:
        for uid in game.players:
            try:
                client.kickUsersInGroup(uid, wolf_box)
            except:
                pass

    # Cleanup
    if thread_id in active_games:
        del active_games[thread_id]

def PTA():
    return {
        'masoi': handle_masoi,
        'setbox': handle_setbox,
    }
