# -*- coding: utf-8 -*-
"""Ma Sói (Werewolf) Game Engine - Core logic"""
import random
import threading
import time
import json
import os


os.makedirs("modules/cache", exist_ok=True)

# ==================== ROLES ====================
ROLES_CONFIG = {
    3: {"soi": 1, "tien_tri": 1, "dan": 1},
    4: {"soi": 1, "tien_tri": 1, "bao_ve": 1, "dan": 1},
    5: {"soi": 1, "tien_tri": 1, "bao_ve": 1, "dan": 2},
    6: {"soi": 2, "tien_tri": 1, "bao_ve": 1, "tho_san": 1, "dan": 1},
}

ROLE_NAMES = {
    "soi": "🐺 Sói",
    "tien_tri": "🔮 Tiên Tri",
    "bao_ve": "🛡️ Bảo Vệ",
    "tho_san": "🏹 Thợ Săn",
    "dan": "👨‍🌾 Dân Làng",
}

ROLE_DESC = {
    "soi": "🐺 SÓI: Ban đêm bạn được chọn 1 người để giết. Dùng: !masoi giet <STT>",
    "tien_tri": "🔮 TIÊN TRI: Ban đêm bạn soi 1 người để biết vai. Dùng: !masoi soi <STT>",
    "bao_ve": "🛡️ BẢO VỆ: Ban đêm bạn bảo vệ 1 người khỏi sói. Dùng: !masoi bv <STT>",
    "tho_san": "🏹 THỢ SĂN: Khi bạn chết, bạn bắn 1 người chết theo. Dùng: !masoi ban <STT>",
    "dan": "👨‍🌾 DÂN LÀNG: Ban ngày hãy thảo luận và vote treo cổ sói!",
}

COLORS = ["#db342e", "#f27806", "#f7b503", "#15a85f", "#FFFFFF"]


class WerewolfGame:
    def __init__(self):
        self.players = {}       # {uid: {"name": str, "role": str, "alive": bool, "stt": int}}
        self.phase = "waiting"  # waiting, night, day, voting, ended
        self.round_num = 0
        self.wolf_target = None
        self.seer_target = None
        self.guard_target = None
        self.last_guard = None
        self.hunter_pending = None
        self.wolf_votes = {}    # {wolf_uid: target_stt}
        self.thread_id = None
        self.wolf_box_id = None
        self.creator_id = None
        self.timer_thread = None
        self.day_timer = None
        self.vote_poll_id = None

    def add_player(self, uid, name):
        if uid in self.players:
            return False, "Bạn đã tham gia rồi!"
        if len(self.players) >= 6:
            return False, "Phòng đã đủ 6 người!"
        if self.phase != "waiting":
            return False, "Game đang diễn ra!"
        stt = len(self.players) + 1
        self.players[uid] = {"name": name, "role": None, "alive": True, "stt": stt}
        return True, f"✅ {name} đã tham gia! ({len(self.players)}/6)"

    def assign_roles(self):
        count = len(self.players)
        if count < 3:
            return False, "Cần ít nhất 3 người!"
        cfg = ROLES_CONFIG.get(count)
        if not cfg:
            # Fallback for counts not in config
            cfg = ROLES_CONFIG[6] if count > 6 else ROLES_CONFIG[max(3, count)]
        
        roles = []
        for role, num in cfg.items():
            roles.extend([role] * num)
        
        # Pad with "dan" if needed
        while len(roles) < count:
            roles.append("dan")
        roles = roles[:count]
        random.shuffle(roles)

        uids = list(self.players.keys())
        for i, uid in enumerate(uids):
            self.players[uid]["role"] = roles[i]
        return True, "Đã phát chức năng!"

    def get_alive_players(self):
        return {uid: p for uid, p in self.players.items() if p["alive"]}

    def get_wolves(self):
        return {uid: p for uid, p in self.players.items() if p["role"] == "soi" and p["alive"]}

    def get_player_by_stt(self, stt):
        for uid, p in self.players.items():
            if p["stt"] == stt:
                return uid, p
        return None, None

    def get_alive_non_wolves(self):
        return {uid: p for uid, p in self.players.items() if p["role"] != "soi" and p["alive"]}

    def process_night(self):
        """Process night actions, return who died"""
        killed_uid = None
        killed_name = None

        # Wolf kill
        if self.wolf_votes:
            # Count votes
            vote_count = {}
            for wolf_uid, target_stt in self.wolf_votes.items():
                vote_count[target_stt] = vote_count.get(target_stt, 0) + 1
            max_votes = max(vote_count.values())
            targets = [stt for stt, v in vote_count.items() if v == max_votes]
            chosen_stt = random.choice(targets)
            target_uid, target_p = self.get_player_by_stt(chosen_stt)
            if target_uid:
                self.wolf_target = target_uid

        # Guard protection
        protected = False
        if self.guard_target:
            g_uid, _ = self.get_player_by_stt(self.guard_target)
            if g_uid and g_uid == self.wolf_target:
                protected = True

        # Apply kill
        if self.wolf_target and not protected:
            if self.wolf_target in self.players and self.players[self.wolf_target]["alive"]:
                self.players[self.wolf_target]["alive"] = False
                killed_uid = self.wolf_target
                killed_name = self.players[self.wolf_target]["name"]
                # Check hunter
                if self.players[self.wolf_target]["role"] == "tho_san":
                    self.hunter_pending = self.wolf_target

        # Seer result
        seer_result = None
        if self.seer_target:
            s_uid, s_p = self.get_player_by_stt(self.seer_target)
            if s_uid:
                is_wolf = s_p["role"] == "soi"
                seer_result = (s_uid, s_p["name"], is_wolf)

        # Reset
        self.wolf_target = None
        self.wolf_votes = {}
        self.seer_target = None
        self.last_guard = self.guard_target
        self.guard_target = None

        return killed_uid, killed_name, seer_result, protected

    def check_win(self):
        """Return winner: 'soi', 'dan', or None"""
        alive = self.get_alive_players()
        wolves = sum(1 for p in alive.values() if p["role"] == "soi")
        villagers = sum(1 for p in alive.values() if p["role"] != "soi")
        if wolves == 0:
            return "dan"
        if wolves >= villagers:
            return "soi"
        return None

    def vote_kill(self, target_stt):
        """Kill player by vote"""
        uid, p = self.get_player_by_stt(target_stt)
        if uid and p["alive"]:
            p["alive"] = False
            if p["role"] == "tho_san":
                self.hunter_pending = uid
            return uid, p["name"], p["role"]
        return None, None, None

    def get_roles_summary(self):
        """Get list of roles in game (without player assignment)"""
        roles = {}
        for p in self.players.values():
            r = p["role"]
            rname = ROLE_NAMES.get(r, r)
            roles[rname] = roles.get(rname, 0) + 1
        lines = []
        for rname, count in roles.items():
            lines.append(f"  {rname}: {count}")
        return "\n".join(lines)

    def get_player_list_text(self, show_dead=True):
        lines = []
        for uid, p in self.players.items():
            status = "💀" if not p["alive"] else "✅"
            if not show_dead and not p["alive"]:
                continue
            lines.append(f"  {p['stt']}. {p['name']} {status}")
        return "\n".join(lines)

    def get_non_wolf_list(self):
        """For wolf box - show only non-wolf players"""
        lines = []
        for uid, p in self.players.items():
            if p["role"] == "soi":
                continue
            status = "💀" if not p["alive"] else "✅"
            lines.append(f"  {p['stt']}. {p['name']} {status}")
        return "\n".join(lines)


# Global game storage: {thread_id: WerewolfGame}
active_games = {}
# Wolf box mapping: {thread_id: wolf_box_thread_id}
wolf_boxes = {}

WOLFBOX_FILE = "data/masoi_wolfbox.json"
os.makedirs("data", exist_ok=True)

def save_wolfbox():
    """Lưu box sói ra file riêng - giữ khi tắt/bật bot"""
    try:
        with open(WOLFBOX_FILE, "w", encoding="utf-8") as f:
            json.dump(wolf_boxes, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[MASOI] Lỗi lưu wolfbox: {e}")

def load_wolfbox():
    """Load box sói từ file khi khởi động"""
    global wolf_boxes
    try:
        if os.path.exists(WOLFBOX_FILE):
            with open(WOLFBOX_FILE, "r", encoding="utf-8") as f:
                wolf_boxes = json.load(f)
            print(f"[MASOI] Đã load {len(wolf_boxes)} box sói từ file")
        else:
            wolf_boxes = {}
    except Exception as e:
        print(f"[MASOI] Lỗi load wolfbox: {e}")
        wolf_boxes = {}

# Load khi module được import
load_wolfbox()
