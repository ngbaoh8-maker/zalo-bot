import time
import threading
import json
import os
import logging
from zlapi.models import Message, ThreadType
from config import ADMIN

des = {
    "version": "1.0.0",
    "credits": "Bii Hot",
    "description": "Auto rãi quảng cáo (ADV) tới tất cả nhóm với thời gian tuỳ chỉnh",
    "power": "ADMIN"
}

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════
# CONFIG FILE - Lưu trạng thái adv vào file
# ═══════════════════════════════════════════
ADV_CONFIG_FILE = "modules/cache/adv_config.json"
_config_lock = threading.Lock()

def _ensure_cache_dir():
    os.makedirs(os.path.dirname(ADV_CONFIG_FILE), exist_ok=True)

def load_adv_config():
    """Load config từ file JSON"""
    with _config_lock:
        try:
            with open(ADV_CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            default = {
                "message": "",
                "delay_minutes": 60,
                "running": False,
                "disbox": []
            }
            _ensure_cache_dir()
            with open(ADV_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(default, f, indent=2, ensure_ascii=False)
            return default

def save_adv_config(config):
    """Lưu config vào file JSON"""
    with _config_lock:
        _ensure_cache_dir()
        with open(ADV_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

# ═══════════════════════════════════════════
# BIẾN TRẠNG THÁI RUNTIME
# ═══════════════════════════════════════════
adv_RUNNING = False
adv_THREAD = None
adv_START_TIME = None
adv_LAST_CYCLE_TIME = None


def get_all_group_ids(client):
    """Lấy tất cả group ID bot đang tham gia"""
    try:
        all_groups = client.fetchAllGroups()
        if all_groups and hasattr(all_groups, 'gridVerMap'):
            return list(all_groups.gridVerMap.keys())
    except Exception as e:
        logger.error(f"[ADV] Lỗi lấy danh sách nhóm: {e}")
    return []


def format_runtime(seconds):
    """Format thời gian đẹp"""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    parts = []
    if h > 0:
        parts.append(f"{h}h")
    if m > 0:
        parts.append(f"{m}m")
    parts.append(f"{s}s")
    return " ".join(parts)


def send_adv_to_group(client, gid, message_text):
    """Gửi tin nhắn quảng cáo tới 1 nhóm"""
    try:
        client.sendMessage(
            Message(text=message_text),
            thread_id=gid,
            thread_type=ThreadType.GROUP
        )
        return True
    except Exception as e:
        logger.error(f"[ADV] Lỗi gửi nhóm {gid}: {e}")
        return False


def adv_loop(client):
    """Vòng lặp chính: rãi adv → đợi → lặp lại"""
    global adv_RUNNING, adv_LAST_CYCLE_TIME

    while adv_RUNNING:
        config = load_adv_config()
        adv_message = config.get("message", "")
        delay_minutes = config.get("delay_minutes", 60)
        disbox_list = config.get("disbox", [])

        if not adv_message.strip():
            logger.warning("[ADV] Nội dung quảng cáo trống, bỏ qua vòng này...")
            # Đợi 30 giây rồi kiểm tra lại
            for _ in range(30):
                if not adv_RUNNING:
                    return
                time.sleep(1)
            continue

        # Đánh dấu thời điểm bắt đầu vòng rãi
        adv_LAST_CYCLE_TIME = time.time()

        # Lấy danh sách nhóm
        group_ids = get_all_group_ids(client)
        active_groups = [gid for gid in group_ids if str(gid) not in disbox_list]

        total = len(group_ids)
        active = len(active_groups)
        skipped = total - active

        logger.info(f"[ADV] Bắt đầu rãi: {active}/{total} nhóm (disbox: {skipped})")

        success_count = 0
        fail_count = 0

        for gid in active_groups:
            if not adv_RUNNING:
                break
            ok = send_adv_to_group(client, gid, adv_message)
            if ok:
                success_count += 1
            else:
                fail_count += 1
            time.sleep(1.5)  # Delay giữa các nhóm để tránh spam

        logger.info(f"[ADV] Xong vòng rãi: ✅ {success_count} | ❌ {fail_count} — Đợi {delay_minutes} phút")

        # Sleep từng giây nhỏ để dừng nhanh khi off
        delay_seconds = delay_minutes * 60
        for _ in range(delay_seconds):
            if not adv_RUNNING:
                break
            time.sleep(1)


# ═══════════════════════════════════════════
# MENU HƯỚNG DẪN
# ═══════════════════════════════════════════
def adv_menu_text(prefix=""):
    return (
        "📢 MENU ADV — Auto Quảng Cáo\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "\n"
        "📝 CÀI ĐẶT NỘI DUNG\n"
        f"🔹 {prefix}adv set <nội dung>  → Đặt ngôn quảng cáo\n"
        f"🔹 {prefix}adv view            → Xem ngôn đã set\n"
        "\n"
        "⏰ THỜI GIAN\n"
        f"🔹 {prefix}adv time <phút>     → Đặt chu kỳ (VD: adv time 60)\n"
        "\n"
        "🚀 ĐIỀU KHIỂN\n"
        f"🔹 {prefix}adv on              → Bật auto rãi\n"
        f"🔹 {prefix}adv off             → Tắt auto rãi\n"
        f"🔹 {prefix}adv test            → Test gửi nhóm hiện tại\n"
        "\n"
        "📊 THÔNG TIN\n"
        f"🔹 {prefix}adv info            → Xem trạng thái & thời gian\n"
        f"🔹 {prefix}adv status          → Xem tổng quan\n"
        "\n"
        "🚫 DISBOX (Chặn nhóm)\n"
        f"🔹 {prefix}adv disbox          → Chặn nhóm hiện tại\n"
        f"🔹 {prefix}adv disbox <gid>    → Chặn theo ID\n"
        f"🔹 {prefix}adv undisbox <gid>  → Gỡ chặn\n"
        f"🔹 {prefix}adv disbox list     → Xem danh sách chặn\n"
    )


# ═══════════════════════════════════════════
# HANDLER CHÍNH
# ═══════════════════════════════════════════
def handle_adv_command(message_text, message_object, thread_id, thread_type, author_id, client):
    global adv_RUNNING, adv_THREAD, adv_START_TIME, adv_LAST_CYCLE_TIME

    # Kiểm tra quyền admin
    if str(author_id) != str(ADMIN):
        client.replyMessage(
            Message(text="❌ Bạn không có quyền sử dụng lệnh này!"),
            message_object, thread_id, thread_type
        )
        return

    parts = message_text.strip().split(maxsplit=2)
    if len(parts) < 2:
        client.replyMessage(
            Message(text=adv_menu_text()),
            message_object, thread_id, thread_type
        )
        return

    cmd = parts[1].lower()
    config = load_adv_config()

    # ══════ SET — Đặt nội dung quảng cáo ══════
    if cmd == "set":
        if len(parts) < 3:
            client.replyMessage(
                Message(text="❌ Thiếu nội dung!\n\nCú pháp: adv set <nội dung quảng cáo>"),
                message_object, thread_id, thread_type
            )
            return

        # Lấy toàn bộ nội dung sau "adv set" (giữ nguyên xuống dòng)
        # Tìm vị trí "set" trong message gốc rồi lấy phần sau
        raw_msg = message_text.strip()
        set_idx = raw_msg.lower().find("set")
        if set_idx != -1:
            content = raw_msg[set_idx + 3:].strip()
        else:
            content = parts[2].strip()

        if not content:
            client.replyMessage(
                Message(text="❌ Nội dung trống!"),
                message_object, thread_id, thread_type
            )
            return

        config["message"] = content
        save_adv_config(config)

        preview = content[:100] + "..." if len(content) > 100 else content
        client.replyMessage(
            Message(text=f"✅ Đã đặt nội dung quảng cáo!\n\n📝 Nội dung:\n{preview}"),
            message_object, thread_id, thread_type
        )
        return

    # ══════ VIEW — Xem nội dung đã set ══════
    if cmd == "view":
        msg = config.get("message", "")
        if not msg:
            client.replyMessage(
                Message(text="📝 Chưa đặt nội dung quảng cáo!\n\nDùng: adv set <nội dung>"),
                message_object, thread_id, thread_type
            )
        else:
            client.replyMessage(
                Message(text=f"📝 NỘI DUNG QUẢNG CÁO HIỆN TẠI:\n━━━━━━━━━━━━━━\n{msg}"),
                message_object, thread_id, thread_type
            )
        return

    # ══════ TIME — Đặt thời gian chu kỳ ══════
    if cmd == "time":
        if len(parts) >= 3:
            try:
                minutes = int(parts[2])
                if minutes <= 0:
                    client.replyMessage(
                        Message(text="❌ Số phút phải lớn hơn 0!"),
                        message_object, thread_id, thread_type
                    )
                    return
                config["delay_minutes"] = minutes
                save_adv_config(config)
                client.replyMessage(
                    Message(text=f"✅ Đã đặt chu kỳ rãi: {minutes} phút"),
                    message_object, thread_id, thread_type
                )
            except ValueError:
                client.replyMessage(
                    Message(text="❌ Số phút không hợp lệ!\n\nCú pháp: adv time <số phút>"),
                    message_object, thread_id, thread_type
                )
        else:
            current = config.get("delay_minutes", 60)
            client.replyMessage(
                Message(text=f"⏰ Chu kỳ rãi hiện tại: {current} phút\n\nCú pháp: adv time <số phút>"),
                message_object, thread_id, thread_type
            )
        return

    # ══════ ON — Bật auto rãi ══════
    if cmd == "on":
        if adv_RUNNING:
            client.replyMessage(
                Message(text="⚠️ ADV đang chạy rồi!\n\nDùng: adv off để tắt trước"),
                message_object, thread_id, thread_type
            )
            return

        # Kiểm tra nội dung đã set chưa
        msg_content = config.get("message", "")
        if not msg_content.strip():
            client.replyMessage(
                Message(text="❌ Chưa đặt nội dung quảng cáo!\n\nDùng: adv set <nội dung> trước khi bật"),
                message_object, thread_id, thread_type
            )
            return

        adv_RUNNING = True
        adv_START_TIME = time.time()
        adv_LAST_CYCLE_TIME = None
        config["running"] = True
        save_adv_config(config)

        adv_THREAD = threading.Thread(target=adv_loop, args=(client,), daemon=True)
        adv_THREAD.start()

        delay = config.get("delay_minutes", 60)
        preview = msg_content[:50] + "..." if len(msg_content) > 50 else msg_content

        client.replyMessage(
            Message(text=(
                "✅ ĐÃ BẬT AUTO RÃI QUẢNG CÁO!\n"
                "━━━━━━━━━━━━━━\n"
                f"📝 Nội dung: {preview}\n"
                f"⏰ Chu kỳ: {delay} phút/vòng\n"
                "🚀 Đang bắt đầu rãi vòng đầu tiên..."
            )),
            message_object, thread_id, thread_type
        )
        return

    # ══════ OFF — Tắt auto rãi ══════
    if cmd == "off":
        if not adv_RUNNING:
            client.replyMessage(
                Message(text="❌ ADV chưa được bật!\n\nDùng: adv on để bật"),
                message_object, thread_id, thread_type
            )
            return

        adv_RUNNING = False
        adv_LAST_CYCLE_TIME = None
        config["running"] = False
        save_adv_config(config)

        runtime = ""
        if adv_START_TIME:
            runtime = f"\n⏱ Tổng thời gian chạy: {format_runtime(int(time.time() - adv_START_TIME))}"

        client.replyMessage(
            Message(text=f"✅ Đã tắt Auto Rãi Quảng Cáo!{runtime}"),
            message_object, thread_id, thread_type
        )
        return

    # ══════ TEST — Test gửi nhóm hiện tại ══════
    if cmd == "test":
        if thread_type != ThreadType.GROUP:
            client.replyMessage(
                Message(text="⚠️ Lệnh test chỉ dùng trong nhóm!"),
                message_object, thread_id, thread_type
            )
            return

        msg_content = config.get("message", "")
        if not msg_content.strip():
            client.replyMessage(
                Message(text="❌ Chưa đặt nội dung! Dùng: adv set <nội dung>"),
                message_object, thread_id, thread_type
            )
            return

        ok = send_adv_to_group(client, thread_id, msg_content)
        if ok:
            client.replyMessage(
                Message(text="✅ Test gửi thành công!"),
                message_object, thread_id, thread_type
            )
        else:
            client.replyMessage(
                Message(text="❌ Test gửi thất bại!"),
                message_object, thread_id, thread_type
            )
        return

    # ══════ INFO — Xem thông tin thời gian ══════
    if cmd == "info":
        if not adv_RUNNING:
            delay = config.get("delay_minutes", 60)
            msg_content = config.get("message", "")
            has_msg = "✅ Đã set" if msg_content.strip() else "❌ Chưa set"

            client.replyMessage(
                Message(text=(
                    "📊 THÔNG TIN ADV\n"
                    "━━━━━━━━━━━━━━\n"
                    "• Trạng thái: ❌ ĐANG TẮT\n"
                    f"• Nội dung: {has_msg}\n"
                    f"• Chu kỳ: {delay} phút\n"
                    "\nDùng: adv on để bật"
                )),
                message_object, thread_id, thread_type
            )
            return

        delay = config.get("delay_minutes", 60)

        if adv_LAST_CYCLE_TIME is None:
            client.replyMessage(
                Message(text="⏳ Đang khởi động vòng rãi đầu tiên..."),
                message_object, thread_id, thread_type
            )
            return

        elapsed = int(time.time() - adv_LAST_CYCLE_TIME)
        delay_seconds = delay * 60
        remaining = max(0, delay_seconds - elapsed)

        if remaining == 0:
            status_detail = "• Đang rãi vòng hiện tại..."
        else:
            status_detail = (
                f"• Thời gian đã chờ: {format_runtime(elapsed)}\n"
                f"• Thời gian còn lại: {format_runtime(remaining)}"
            )

        runtime = format_runtime(int(time.time() - adv_START_TIME)) if adv_START_TIME else "N/A"

        client.replyMessage(
            Message(text=(
                "📊 THÔNG TIN ADV\n"
                "━━━━━━━━━━━━━━\n"
                "• Trạng thái: ✅ ĐANG CHẠY\n"
                f"• Thời gian chạy: {runtime}\n"
                f"• Chu kỳ: {delay} phút\n"
                f"{status_detail}"
            )),
            message_object, thread_id, thread_type
        )
        return

    # ══════ STATUS — Tổng quan ══════
    if cmd == "status":
        msg_content = config.get("message", "")
        delay = config.get("delay_minutes", 60)
        disbox_count = len(config.get("disbox", []))

        try:
            group_ids = get_all_group_ids(client)
            total_groups = len(group_ids)
        except:
            total_groups = "N/A"

        preview = msg_content[:80] + "..." if len(msg_content) > 80 else (msg_content or "Chưa set")

        client.replyMessage(
            Message(text=(
                "📊 TỔNG QUAN ADV\n"
                "━━━━━━━━━━━━━━\n"
                f"• Trạng thái: {'✅ ĐANG CHẠY' if adv_RUNNING else '❌ ĐANG TẮT'}\n"
                f"• Tổng nhóm: {total_groups}\n"
                f"• Nhóm bị disbox: {disbox_count}\n"
                f"• Chu kỳ: {delay} phút\n"
                f"• Nội dung: {preview}\n"
                f"• Thời gian chạy: {format_runtime(int(time.time() - adv_START_TIME)) if adv_RUNNING and adv_START_TIME else 'Chưa chạy'}"
            )),
            message_object, thread_id, thread_type
        )
        return

    # ══════ DISBOX — Chặn nhóm ══════
    if cmd == "disbox":
        disbox = config.get("disbox", [])

        if len(parts) == 2:
            # Chặn nhóm hiện tại
            gid = str(thread_id)
            if gid not in disbox:
                disbox.append(gid)
                config["disbox"] = disbox
                save_adv_config(config)
                client.replyMessage(
                    Message(text=f"✅ Đã disbox nhóm này!\nID: {gid}"),
                    message_object, thread_id, thread_type
                )
            else:
                client.replyMessage(
                    Message(text=f"⚠️ Nhóm này đã bị disbox rồi!\nID: {gid}"),
                    message_object, thread_id, thread_type
                )
        elif len(parts) >= 3 and parts[2].strip().lower() == "list":
            if disbox:
                text = "📋 DANH SÁCH DISBOX:\n" + "\n".join([f"• {gid}" for gid in disbox])
            else:
                text = "📋 Chưa có nhóm nào bị disbox"
            client.replyMessage(
                Message(text=text),
                message_object, thread_id, thread_type
            )
        else:
            gid = parts[2].strip()
            if gid not in disbox:
                disbox.append(gid)
                config["disbox"] = disbox
                save_adv_config(config)
                client.replyMessage(
                    Message(text=f"✅ Đã thêm vào disbox!\nID: {gid}"),
                    message_object, thread_id, thread_type
                )
            else:
                client.replyMessage(
                    Message(text=f"⚠️ ID {gid} đã bị disbox rồi!"),
                    message_object, thread_id, thread_type
                )
        return

    # ══════ UNDISBOX — Gỡ chặn nhóm ══════
    if cmd == "undisbox":
        disbox = config.get("disbox", [])
        if len(parts) >= 3:
            gid = parts[2].strip()
            if gid in disbox:
                disbox.remove(gid)
                config["disbox"] = disbox
                save_adv_config(config)
                client.replyMessage(
                    Message(text=f"✅ Đã gỡ disbox!\nID: {gid}"),
                    message_object, thread_id, thread_type
                )
            else:
                client.replyMessage(
                    Message(text=f"❌ ID {gid} chưa bị disbox!"),
                    message_object, thread_id, thread_type
                )
        else:
            # Gỡ nhóm hiện tại
            gid = str(thread_id)
            if gid in disbox:
                disbox.remove(gid)
                config["disbox"] = disbox
                save_adv_config(config)
                client.replyMessage(
                    Message(text=f"✅ Đã gỡ disbox nhóm này!\nID: {gid}"),
                    message_object, thread_id, thread_type
                )
            else:
                client.replyMessage(
                    Message(text=f"❌ Nhóm này chưa bị disbox!"),
                    message_object, thread_id, thread_type
                )
        return

    # ══════ MENU — Hiện hướng dẫn ══════
    if cmd == "menu":
        client.replyMessage(
            Message(text=adv_menu_text()),
            message_object, thread_id, thread_type
        )
        return

    # ══════ LỆNH KHÔNG HỢP LỆ ══════
    client.replyMessage(
        Message(text=f"❌ Lệnh không hợp lệ!\n\nGõ: adv menu để xem hướng dẫn"),
        message_object, thread_id, thread_type
    )


# ═══════════════════════════════════════════
# ĐĂNG KÝ MODULE VỚI BOT (PTA pattern)
# ═══════════════════════════════════════════
def PTA():
    return {
        'adv': handle_adv_command,
    }
