from zlapi.models import Message, ThreadType
import threading
import time
from datetime import datetime, timedelta
import pytz
import os
import json
from pathlib import Path
import logging
import requests
import re

des = {
    'version': "1.2.0",
    'credits': "ngbao",
    'description':  "Qc nội dung",
    'power': "Admin"
}

# cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='rao.log',
    encoding='utf-8'
)

# cấu hình múi giờ và hằng số
vn_tz = pytz.timezone("Asia/Ho_Chi_Minh")
network_timeout = 10  # timeout cho yêu cầu mạng
message_delay = 0.3   # độ trễ giữa các tin nhắn
max_retries = 3       # số lần thử lại khi tải ảnh/video

# trạng thái toàn cục
rao_threads = {}      # {index: Thread}
rao_running = {}      # {index: bool}
disbox_groups = {}    # {username: [thread_id]}

# ==========================
# xử lý file
# ==========================

def ensure_data_dir(username: str) -> Path:
    """ĐẢM BẢO THƯ MỤC DỮ LIỆU RIÊNG CỦA BOT TỒN TẠI."""
    data_dir = Path(f"rao/{username}")
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"✅ TẠO THƯ MỤC CHO BOT {username}: {data_dir}")
        return data_dir
    except Exception as e:
        logging.error(f"❌ LỖI KHI TẠO THƯ MỤC DỮ LIỆU CHO {username}: {e}")
        return None

def get_file_paths(username: str) -> dict:
    """TẠO ĐƯỜNG DẪN FILE CHO TỪNG BOT."""
    data_dir = ensure_data_dir(username)
    if not data_dir:
        return None
    return {
        "messages": data_dir,
        "disbox": data_dir / "disbox.json"
    }

def load_rao_messages(username: str) -> list:
    """ĐỌC TẤT CẢ FILE JSON TIN NHẮN TRONG THƯ MỤC CỦA BOT."""
    file_paths = get_file_paths(username)
    if not file_paths:
        return []
    
    messages = []
    data_dir = file_paths["messages"]
    json_files = sorted(data_dir.glob("*.json"), key=lambda x: int(x.stem) if x.stem.isdigit() else float('inf'))
    
    for file_path in json_files:
        try:
            if file_path.name == "disbox.json":
                continue
            with file_path.open("r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    data = json.loads(content)
                    if not data.get("index"):
                        data["index"] = int(file_path.stem)
                    data["created_at"] = datetime.fromisoformat(data["created_at"])
                    messages.append(data)
            logging.info(f"ĐÃ TẢI TIN NHẮN RAO TỪ {file_path}")
        except Exception as e:
            logging.error(f"LỖI KHI ĐỌC {file_path} CHO {username}: {e}")
    
    return sorted(messages, key=lambda x: int(x.get("index", 0)))

def save_rao_message(username: str, message_data: dict, index: int) -> None:
    """LƯU MỘT TIN NHẮN RAO VÀO FILE JSON."""
    file_paths = get_file_paths(username)
    if not file_paths:
        return
    
    file_path = file_paths["messages"] / f"{index}.json"
    try:
        message_data_copy = message_data.copy()
        message_data_copy["created_at"] = message_data_copy["created_at"].isoformat()
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(message_data_copy, f, indent=4, ensure_ascii=False)
        logging.info(f"ĐÃ LƯU TIN NHẮN RAO {index} CHO {username}")
    except Exception as e:
        logging.error(f"LỖI KHI LƯU TIN NHẮN RAO {index} CHO {username}: {e}")

def load_disbox(username: str) -> list:
    """TẢI DANH SÁCH NHÓM BỊ CHẶN TỪ FILE DISBOX.JSON."""
    file_paths = get_file_paths(username)
    if not file_paths:
        return []
    file_path = file_paths["disbox"]
    try:
        if file_path.exists():
            with file_path.open("r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
        return []
    except Exception as e:
        logging.error(f"LỖI KHI ĐỌC DISBOX.JSON CHO {username}: {e}")
        return []

def save_disbox(username: str, disbox_ids: list) -> None:
    """LƯU DANH SÁCH NHÓM BỊ CHẶN VÀO FILE DISBOX.JSON."""
    file_paths = get_file_paths(username)
    if not file_paths:
        return
    file_path = file_paths["disbox"]
    try:
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(disbox_ids, f, indent=4, ensure_ascii=False)
        logging.info(f"ĐÃ LƯU DANH SÁCH DISBOX CHO {username}")
    except Exception as e:
        logging.error(f"LỖI KHI LƯU DISBOX.JSON CHO {username}: {e}")

def download_images(link_list: list, save_folder: str = "temp_images") -> list:
    """TẢI ẢNH TỪ DANH SÁCH LINK VÀ LƯU VÀO THƯ MỤC TẠM."""
    os.makedirs(save_folder, exist_ok=True)
    paths = []
    for idx, link in enumerate(link_list):
        for attempt in range(max_retries):
            try:
                if not link.startswith(('http://', 'https://')):
                    link = f"https://{link}"
                res = requests.get(link, timeout=network_timeout)
                if res.status_code != 200:
                    logging.error(f"THỬ {attempt + 1}/{max_retries} - KHÔNG THỂ TẢI ẢNH {link}: MÃ TRẠNG THÁI {res.status_code}")
                    continue
                file_path = os.path.join(save_folder, f"img_{idx}_{int(time.time())}.jpg")
                with open(file_path, "wb") as f:
                    f.write(res.content)
                paths.append(file_path)
                logging.info(f"✅ ĐÃ TẢI ẢNH: {link} -> {file_path}")
                break
            except Exception as e:
                logging.error(f"THỬ {attempt + 1}/{max_retries} - LỖI KHI TẢI ẢNH {link}: {e}")
                if attempt == max_retries - 1:
                    logging.error(f"❌ BỎ QUA ẢNH {link} SAU {max_retries} LẦN THỬ")
    return paths

def validate_url(url: str) -> bool:
    """KIỂM TRA TÍNH HỢP LỆ CỦA URL."""
    if not url.startswith(('http://', 'https://')):
        url = f"https://{url}"
    try:
        response = requests.head(url, timeout=network_timeout, allow_redirects=True)
        return response.status_code == 200
    except Exception as e:
        logging.error(f"LỖI KIỂM TRA URL {url}: {e}")
        return False

# ==========================
# xử lý thời gian
# ==========================

def parse_time_input(time_str: str) -> int:
    """CHUYỂN ĐỔI THỜI GIAN DẠNG VĂN BẢN THÀNH SỐ PHÚT SO VỚI HIỆN TẠI."""
    try:
        return max(1, int(time_str))
    except ValueError:
        time_str = time_str.lower().strip()
        now = datetime.now(vn_tz)
        
        time_match = re.match(r"(\d{1,2})(?:h|:)?(\d{0,2})?\s*(trưa|sáng|chiều|tối)?\s*(mai|hôm nay)?", time_str)
        if not time_match:
            raise ValueError("ĐỊNH DẠNG THỜI GIAN KHÔNG HỢP LỆ!")

        hour = int(time_match.group(1))
        minute = int(time_match.group(2) or 0)
        period = time_match.group(3) or ""
        day = time_match.group(4) or ""

        if period == "chiều" or period == "tối":
            if 0 <= hour <= 12:
                hour = (hour % 12) + 12
        elif period == "sáng" and hour == 12:
            hour = 0

        target_date = now
        if day == "mai":
            target_date = now + timedelta(days=1)

        target_time = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if target_time < now and day != "mai":
            target_time += timedelta(days=1)
        
        delta = (target_time - now).total_seconds() / 60
        if delta <= 0:
            raise ValueError("THỜI GIAN ĐÃ QUA HOẶC KHÔNG HỢP LỆ!")
        
        return max(1, int(delta))

# ==========================
# vòng lặp rao
# ==========================

def rao_loop(client, index: int, username: str):
    """VÒNG LẶP GỬI TIN NHẮN RAO: GỬI MỘT LẦN CHO TẤT CẢ NHÓM, SAU ĐÓ CHỜ ĐẾN LẦN TIẾP THEO."""
    try:
        while rao_running.get(index, False):
            rao_data = next((r for r in load_rao_messages(username) if r["index"] == index), None)
            if not rao_data:
                logging.error(f"KHÔNG TÌM THẤY DỮ LIỆU RAO SỐ {index}")
                break

            interval = rao_data["interval"]
            all_groups = client.fetchAllGroups()
            allowed_thread_ids = list(all_groups.gridVerMap.keys()) if all_groups and hasattr(all_groups, 'gridVerMap') else []
            disbox_ids = load_disbox(username)
            allowed_thread_ids = [tid for tid in allowed_thread_ids if tid not in disbox_ids]

            # gửi tin nhắn đến tất cả nhóm không bị chặn
            for thread_id in allowed_thread_ids:
                for attempt in range(max_retries):
                    try:
                        # 1. gửi ảnh (nếu có)
                        image_links = [link for link in rao_data.get("images", []) if validate_url(link)]
                        if image_links:
                            local_image_paths = download_images(image_links)
                            if local_image_paths:
                                client.sendMultiLocalImage(
                                    local_image_paths,
                                    thread_id=thread_id,
                                    thread_type=ThreadType.GROUP,
                                    ttl=3600000
                                )
                                logging.info(f"GỬI ẢNH TỚI NHÓM {thread_id} CHO RAO {index}")
                                for path in local_image_paths:
                                    try:
                                        os.remove(path)
                                        logging.info(f"ĐÃ XÓA ẢNH TẠM: {path}")
                                    except Exception as e:
                                        logging.error(f"LỖI XÓA ẢNH TẠM {path}: {e}")
                                time.sleep(message_delay)

                        # 2. gửi video (nếu có)
                        video_data_list = rao_data.get("videos", [])
                        for video_data in video_data_list:
                            video_url = video_data.get("normalUrl", "")
                            if not video_url or not validate_url(video_url):
                                logging.error(f"URL VIDEO KHÔNG HỢP LỆ: {video_url}")
                                continue

                            thumb_url = video_data.get("thumb", video_url)
                            duration = video_data.get("duration", 10000)
                            width = video_data.get("width", 720)
                            height = video_data.get("height", 720)

                            client.sendRemoteVideo(
                                videoUrl=video_url,
                                thumbnailUrl=thumb_url,
                                duration=duration,
                                width=width,
                                height=height,
                                thread_id=thread_id,
                                thread_type=ThreadType.GROUP,
                                ttl=3600000
                            )
                            logging.info(f"✅ GỬI VIDEO TỚI NHÓM {thread_id} CHO RAO {index}: {video_url}")
                            time.sleep(message_delay)

                        # 3. gửi nội dung văn bản (nếu có)
                        message_text = rao_data.get("message", "")
                        if message_text:
                            client.sendMessage(
                                message=Message(text=message_text),
                                thread_id=thread_id,
                                thread_type=ThreadType.GROUP,
                                ttl=3600000
                            )
                            logging.info(f"GỬI TIN NHẮN TỚI NHÓM {thread_id} CHO RAO {index}: {message_text}")
                            time.sleep(message_delay)

                        # 4. gửi danh thiếp (nếu có)
                        card_data = rao_data.get("card", {})
                        if card_data and card_data.get('uid') and card_data.get('content'):
                            user_info = client.fetchUserInfo(card_data['uid']).get(card_data['uid'], {})
                            avatar_url = user_info.get('avatar', '') if user_info else ''
                            client.sendBusinessCard(
                                userId=card_data['uid'],
                                qrCodeUrl=avatar_url,
                                phone=card_data['content'],
                                thread_id=thread_id,
                                thread_type=ThreadType.GROUP,
                                ttl=3600000
                            )
                            logging.info(f"GỬI DANH THIẾP TỚI NHÓM {thread_id} CHO RAO {index}: UID {card_data['uid']}")
                            time.sleep(message_delay)

                        break  # thoát vòng lặp thử lại nếu gửi thành công
                    except Exception as e:
                        logging.error(f"THỬ {attempt + 1}/{max_retries} - LỖI GỬI TỚI NHÓM {thread_id} CHO RAO {index}: {e}")
                        if attempt == max_retries - 1:
                            logging.error(f"❌ BỎ QUA NHÓM {thread_id} SAU {max_retries} LẦN THỬ")
                        time.sleep(1)

            # ngủ đúng khoảng thời gian interval
            sleep_seconds = interval * 60
            logging.info(f"RAO {index} SẼ NGỦ {sleep_seconds:.2f} GIÂY ĐẾN LẦN GỬI TIẾP THEO")
            time.sleep(sleep_seconds)

    except Exception as e:
        logging.error(f"LỖI NGHIÊM TRỌNG TRONG RAO_LOOP SỐ {index} CHO {username}: {e}")
    finally:
        rao_running[index] = False
        if index in rao_threads:
            del rao_threads[index]
        logging.info(f"DỪNG RAO_LOOP SỐ {index} CHO {username}")

# ==========================
# xử lý lệnh chính
# ==========================

def handle_rao_command(message, message_object, thread_id, thread_type, author_id, client):
    username = client.me_name if hasattr(client, 'me_name') else "BOT KHÔNG TÊN"
    ensure_data_dir(username)

    rao_list = load_rao_messages(username)
    parts = message.strip().split(maxsplit=5)

    # nếu chỉ gõ "rao"
    if len(parts) == 1:
        client.replyMessage(
            Message(text="📢 HỆ THỐNG AUTO RAO\nSỬ DỤNG: `rao <nội dung> <thời gian> on/off`\nVÍ DỤ: `rao chào mọi người 120 on`\nNHẬP `rao help` ĐỂ XEM CHI TIẾT!"),
            message_object, thread_id, thread_type, ttl=120000
        )
        return

    # lệnh help
    if len(parts) == 2 and parts[1].lower() == "help":
        help_text = (
            "📋 HỆ THỐNG AUTO RAO 🤖\n"
            "LƯU Ý: INDEX là số thứ tự.\n\n"
            "CÚ PHÁP CƠ BẢN: `rao <nội dung> <thời gian> on/off`\n"
            "ví dụ: `rao chào mọi người 120 on`\n\n"
            "🔧 QUẢN LÝ NỘI DUNG:\n"
            "  - `rao set <index> <nội dung>`: cập nhật nội dung rao\n"
            "  - `rao time <index> <phút>`: chỉnh thời gian lặp\n"
            "📷 QUẢN LÝ ẢNH:\n"
            "  - `rao image add <index>` + đính kèm hoặc nhập link\n"
            "  - `rao image remove <index> <số>` / `rao image clear <index>`\n"
            "🎥 QUẢN LÝ VIDEO:\n"
            "  - `rao video add <index>` + đính kèm hoặc nhập link\n"
            "  - `rao video remove <index> <số>` / `rao video clear <index>`\n"
            "📇 DANH THIẾP:\n"
            "  - `rao card <index> <uid> <nội dung>` / `rao card clear <index>`\n"
            "🚫 CHẶN NHÓM:\n"
            "  - `rao disbox` / `rao undisbox`\n"
            "📊 KHÁC:\n"
            "  - `rao list`, `rao info <index>`, `rao on/off <index>`\n"
        )
        client.replyMessage(Message(text=help_text), message_object, thread_id, thread_type, ttl=120000)
        return

    # xử lý disbox
    if len(parts) == 2 and parts[1].lower() == "disbox":
        disbox_ids = load_disbox(username)
        if thread_id not in disbox_ids:
            disbox_ids.append(thread_id)
            save_disbox(username, disbox_ids)
            client.replyMessage(Message(text="🚫 ĐÃ THÊM NHÓM VÀO DANH SÁCH CHẶN!"), message_object, thread_id, thread_type, ttl=120000)
        else:
            client.replyMessage(Message(text="⚠️ NHÓM NÀY ĐÃ TRONG DANH SÁCH CHẶN!"), message_object, thread_id, thread_type, ttl=120000)
        return

    if len(parts) == 2 and parts[1].lower() == "undisbox":
        disbox_ids = load_disbox(username)
        if thread_id in disbox_ids:
            disbox_ids.remove(thread_id)
            save_disbox(username, disbox_ids)
            client.replyMessage(Message(text="✅ ĐÃ GỠ NHÓM KHỎI DANH SÁCH CHẶN!"), message_object, thread_id, thread_type, ttl=120000)
        else:
            client.replyMessage(Message(text="⚠️ NHÓM KHÔNG TRONG DANH SÁCH CHẶN!"), message_object, thread_id, thread_type, ttl=120000)
        return

    # 🖼️ IMAGE ADD - giống rai.py
    if len(parts) >= 4 and parts[1].lower() == "image" and parts[2].lower() == "add":
        try:
            index = int(parts[3])
            rao_data = next((r for r in rao_list if r["index"] == index), None)
            if not rao_data:
                client.replyMessage(Message(text="⚠️ SỐ THỨ TỰ KHÔNG HỢP LỆ!"), message_object, thread_id, thread_type, ttl=120000)
                return

            images = rao_data.get("images", [])
            attachments = getattr(message_object, "attachments", None)
            added_links = []

            if attachments:
                for att in attachments:
                    if isinstance(att, dict) and att.get("type") == "image" and att.get("url"):
                        img_url = att["url"]
                        if img_url not in images:
                            images.append(img_url)
                            added_links.append(img_url)

            if not added_links and len(parts) >= 5:
                img_link = parts[4].strip()
                if not img_link.startswith(("http://", "https://")):
                    img_link = f"https://{img_link}"
                if validate_url(img_link) and img_link not in images:
                    images.append(img_link)
                    added_links.append(img_link)

            if added_links:
                rao_data["images"] = images
                rao_data["created_at"] = datetime.now(vn_tz)
                save_rao_message(username, rao_data, index)
                reply_text = f"✅ ĐÃ THÊM {len(added_links)} ẢNH VÀO SỐ {index}:\n" + "\n".join(added_links)
            else:
                reply_text = "⚠️ KHÔNG PHÁT HIỆN ẢNH HỢP LỆ!"
            client.replyMessage(Message(text=reply_text), message_object, thread_id, thread_type, ttl=120000)
        except ValueError:
            client.replyMessage(Message(text="⚠️ SỐ THỨ TỰ PHẢI LÀ SỐ!"), message_object, thread_id, thread_type, ttl=120000)
        return

    # 🎥 VIDEO ADD - giống rai.py
    if len(parts) >= 4 and parts[1].lower() == "video" and parts[2].lower() == "add":
        try:
            index = int(parts[3])
            rao_data = next((r for r in rao_list if r["index"] == index), None)
            if not rao_data:
                client.replyMessage(Message(text="⚠️ SỐ THỨ TỰ KHÔNG HỢP LỆ!"), message_object, thread_id, thread_type, ttl=120000)
                return

            videos = rao_data.get("videos", [])
            video_list_added = []
            attachments = getattr(message_object, "attachments", None)

            if attachments:
                for att in attachments:
                    if isinstance(att, dict) and att.get("type") == "video" and att.get("url"):
                        vurl = att["url"]
                        if not vurl.startswith(("http://", "https://")):
                            vurl = f"https://{vurl}"
                        if vurl not in [v["normalUrl"] for v in videos]:
                            videos.append({
                                "normalUrl": vurl,
                                "thumb": att.get("thumbnailUrl", vurl),
                                "duration": 10000,
                                "width": 720,
                                "height": 720
                            })
                            video_list_added.append(vurl)

            if not video_list_added and len(parts) >= 5:
                vlink = parts[4].strip()
                if not vlink.startswith(("http://", "https://")):
                    vlink = f"https://{vlink}"
                if validate_url(vlink) and vlink not in [v["normalUrl"] for v in videos]:
                    videos.append({
                        "normalUrl": vlink,
                        "thumb": vlink,
                        "duration": 10000,
                        "width": 720,
                        "height": 720
                    })
                    video_list_added.append(vlink)

            if video_list_added:
                rao_data["videos"] = videos
                rao_data["created_at"] = datetime.now(vn_tz)
                save_rao_message(username, rao_data, index)
                reply_text = f"✅ ĐÃ THÊM {len(video_list_added)} VIDEO VÀO SỐ {index}:\n" + "\n".join(video_list_added)
            else:
                reply_text = "⚠️ KHÔNG PHÁT HIỆN VIDEO HỢP LỆ!"
            client.replyMessage(Message(text=reply_text), message_object, thread_id, thread_type, ttl=120000)
        except ValueError:
            client.replyMessage(Message(text="⚠️ SỐ THỨ TỰ PHẢI LÀ SỐ!"), message_object, thread_id, thread_type, ttl=120000)
        return


    # lệnh rao info <index>
    if len(parts) == 3 and parts[1].lower() == "info":
        try:
            index = int(parts[2])
            rao_data = next((r for r in rao_list if r["index"] == index), None)
            if rao_data:
                status = "BẬT" if rao_running.get(index, False) else "TẮT"
                images = rao_data.get("images", [])
                videos = rao_data.get("videos", [])
                card = rao_data.get("card", {})
                info_text = (
                    f"📋 CHI TIẾT NỘI DUNG RAO SỐ {index}\n\n"
                    f"NỘI DUNG: {rao_data['message'] or 'không có'}\n"
                    f"THỜI GIAN: {rao_data['interval']} phút\n"
                    f"TRẠNG THÁI: {status}\n"
                    f"ẢNH: {len(images)} ảnh\n" + 
                    (f"  - " + "\n  - ".join(images) + "\n" if images else "") +
                    f"VIDEO: {len(videos)} video\n" +
                    (f"  - " + "\n  - ".join(v["normalUrl"] for v in videos) + "\n" if videos else "") +
                    f"DANH THIẾP: {card.get('status', 'chưa thiết lập')}\n" +
                    (f"  UID: {card.get('uid', 'chưa thiết lập')}\n  NỘI DUNG: {card.get('content', 'chưa thiết lập')}\n" if card.get('uid') else "") +
                    f"TẠO LÚC: {rao_data['created_at'].strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                client.replyMessage(
                    Message(text=info_text),
                    message_object, thread_id, thread_type, ttl=120000
                )
            else:
                client.replyMessage(
                    Message(text="⚠️ SỐ THỨ TỰ KHÔNG HỢP LỆ!"),
                    message_object, thread_id, thread_type, ttl=120000
                )
        except ValueError:
            client.replyMessage(
                Message(text="⚠️ SỐ THỨ TỰ PHẢI LÀ SỐ NGUYÊN!"),
                message_object, thread_id, thread_type, ttl=120000
            )
        return

    # lệnh rao list
    if len(parts) == 2 and parts[1].lower() == "list":
        if not rao_list:
            client.replyMessage(
                Message(text="📪 DANH SÁCH NỘI DUNG RAO TRỐNG!"),
                message_object, thread_id, thread_type, ttl=120000
            )
            return

        list_text = f"📜 DANH SÁCH NỘI DUNG RAO ({len(rao_list)})\n\n"
        for rao in rao_list:
            index = rao["index"]
            status = "BẬT" if rao_running.get(index, False) else "TẮT"
            images = rao.get("images", [])
            videos = rao.get("videos", [])
            card = rao.get("card", {})
            list_text += (
                f"{index}. NỘI DUNG: {rao['message'] or 'không có'}\n"
                f"   THỜI GIAN: {rao['interval']} phút\n"
                f"   TRẠNG THÁI: {status}\n"
                f"   ẢNH: {len(images)} ảnh\n" + 
                (f"     - " + "\n     - ".join(images) + "\n" if images else "") +
                f"   VIDEO: {len(videos)} video\n" +
                (f"     - " + "\n     - ".join(v["normalUrl"] for v in videos) + "\n" if videos else "") +
                f"   DANH THIẾP: {card.get('status', 'chưa thiết lập')}\n" +
                (f"     UID: {card.get('uid', 'chưa thiết lập')}\n     NỘI DUNG: {card.get('content', 'chưa thiết lập')}\n" if card.get('uid') else "") +
                f"   TẠO LÚC: {rao['created_at'].strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )
        
        client.replyMessage(
            Message(text=list_text),
            message_object, thread_id, thread_type, ttl=120000
        )
        return

    # lệnh rao off <index>
    if len(parts) == 3 and parts[1].lower() == "off":
        try:
            index = int(parts[2])
            rao_data = next((r for r in rao_list if r["index"] == index), None)
            if rao_data:
                rao_running[index] = False
                rao_data["enabled"] = False
                save_rao_message(username, rao_data, index)
                if index in rao_threads:
                    thread = rao_threads[index]
                    if thread.is_alive():
                        thread.join(timeout=1.0)
                    del rao_threads[index]
                reply_text = f"✅ ĐÃ TẮT RAO SỐ {index}"
                client.replyMessage(
                    Message(text=reply_text),
                    message_object, thread_id, thread_type, ttl=120000
                )
            else:
                client.replyMessage(
                    Message(text="⚠️ SỐ THỨ TỰ KHÔNG HỢP LỆ!"),
                    message_object, thread_id, thread_type, ttl=120000
                )
        except ValueError:
            client.replyMessage(
                Message(text="⚠️ SỐ THỨ TỰ PHẢI LÀ SỐ NGUYÊN!"),
                message_object, thread_id, thread_type, ttl=120000
            )
        return

    # lệnh rao on <index>
    if len(parts) == 3 and parts[1].lower() == "on":
        try:
            index = int(parts[2])
            rao_data = next((r for r in rao_list if r["index"] == index), None)
            if rao_data:
                if rao_running.get(index, False):
                    reply_text = f"⚠️ RAO SỐ {index} ĐÃ ĐƯỢC BẬT RỒI!"
                else:
                    rao_running[index] = True
                    rao_data["enabled"] = True
                    save_rao_message(username, rao_data, index)
                    thread = threading.Thread(
                        target=rao_loop,
                        args=(client, index, username),
                        daemon=True,
                        name=f"raothread-{index}-{username}"
                    )
                    rao_threads[index] = thread
                    thread.start()
                    reply_text = (
                        f"TIẾN HÀNH KHỞI ĐỘNG SỐ {index}\n"
                        f"THỜI GIAN: {rao_data['interval']} PHÚT\n"
                        f"NỘI DUNG: \n {rao_data['message'] or 'KHÔNG CÓ'}\n"
                        f"ẢNH: {len(rao_data.get('images', []))} ẢNH\n"
                        f"VIDEO: {len(rao_data.get('videos', []))} VIDEO\n"
                        f"CARD: {rao_data.get('card', {}).get('status', 'CHƯA THIẾT LẬP')}"
                    )
                client.replyMessage(
                    Message(text=reply_text),
                    message_object, thread_id, thread_type, ttl=120000
                )
            else:
                client.replyMessage(
                    Message(text="⚠️ SỐ THỨ TỰ KHÔNG HỢP LỆ!"),
                    message_object, thread_id, thread_type, ttl=120000
                )
        except ValueError:
            client.replyMessage(
                Message(text="⚠️ SỐ THỨ TỰ PHẢI LÀ SỐ NGUYÊN!"),
                message_object, thread_id, thread_type, ttl=120000
            )
        return

    # lệnh rao time <index> <thời gian>
    if len(parts) == 4 and parts[1].lower() == "time":
        try:
            index = int(parts[2])
            new_interval = parse_time_input(parts[3])
            rao_data = next((r for r in rao_list if r["index"] == index), None)
            if rao_data:
                rao_data["interval"] = new_interval
                save_rao_message(username, rao_data, index)
                reply_text = f"✅ ĐÃ ĐẶT THỜI GIAN RAO SỐ {index} THÀNH {new_interval} PHÚT."
            else:
                reply_text = "⚠️ SỐ THỨ TỰ KHÔNG HỢP LỆ!"
            client.replyMessage(
                Message(text=reply_text),
                message_object, thread_id, thread_type, ttl=120000
            )
        except ValueError as e:
            client.replyMessage(
                Message(text=f"⚠️ LỖI: {str(e)}"),
                message_object, thread_id, thread_type, ttl=120000
            )
        return

    # lệnh rao set <index> <nội dung mới>
    if len(parts) >= 3 and parts[1].lower() == "set":
        try:
            index = int(parts[2])
            rao_data = next((r for r in rao_list if r["index"] == index), None)
            if rao_data:
                new_message = " ".join(parts[3:])
                if not new_message:
                    reply_text = "⚠️ VUI LÒNG NHẬP NỘI DUNG MỚI!"
                else:
                    rao_data["message"] = new_message
                    rao_data["created_at"] = datetime.now(vn_tz)
                    save_rao_message(username, rao_data, index)
                    reply_text = f"✅ ĐÃ CẬP NHẬT NỘI DUNG RAO SỐ {index}: {new_message}"
            else:
                reply_text = "⚠️ SỐ THỨ TỰ KHÔNG HỢP LỆ!"
            client.replyMessage(
                Message(text=reply_text),
                message_object, thread_id, thread_type, ttl=120000
            )
        except ValueError:
            client.replyMessage(
                Message(text="⚠️ SỐ THỨ TỰ PHẢI LÀ SỐ NGUYÊN!"),
                message_object, thread_id, thread_type, ttl=120000
            )
        return

    # lệnh rao image add <index> <link>
    if len(parts) >= 4 and parts[1].lower() == "image" and parts[2].lower() == "add":
        try:
            index = int(parts[3])
            rao_data = next((r for r in rao_list if r["index"] == index), None)
            if rao_data:
                images = rao_data.get("images", [])
                image_link = parts[4].strip()
                if validate_url(image_link):
                    if image_link not in images:
                        images.append(image_link)
                        rao_data["images"] = images
                        rao_data["created_at"] = datetime.now(vn_tz)
                        save_rao_message(username, rao_data, index)
                        reply_text = f"✅ ĐÃ THÊM ẢNH VÀO SỐ {index}: {image_link}"
                    else:
                        reply_text = "⚠️ ẢNH ĐÃ CÓ TRONG DANH SÁCH!"
                else:
                    reply_text = f"⚠️ LINK ẢNH KHÔNG HỢP LỆ: {image_link}"
                client.replyMessage(
                    Message(text=reply_text),
                    message_object, thread_id, thread_type, ttl=120000
                )
            else:
                client.replyMessage(
                    Message(text="⚠️ SỐ THỨ TỰ KHÔNG HỢP LỆ!"),
                    message_object, thread_id, thread_type, ttl=120000
                )
        except ValueError:
            client.replyMessage(
                Message(text="⚠️ SỐ THỨ TỰ PHẢI LÀ SỐ NGUYÊN!"),
                message_object, thread_id, thread_type, ttl=120000
            )
        return

    # lệnh rao image remove <index> <image_index>
    if len(parts) == 5 and parts[1].lower() == "image" and parts[2].lower() == "remove":
        try:
            index = int(parts[3])
            image_index = int(parts[4]) - 1
            rao_data = next((r for r in rao_list if r["index"] == index), None)
            if rao_data:
                images = rao_data.get("images", [])
                if 0 <= image_index < len(images):
                    removed_image = images.pop(image_index)
                    rao_data["images"] = images
                    rao_data["created_at"] = datetime.now(vn_tz)
                    save_rao_message(username, rao_data, index)
                    reply_text = f"✅ ĐÃ XÓA ẢNH SỐ {image_index + 1} KHỎI SỐ {index}: {removed_image}"
                else:
                    reply_text = "⚠️ CHỈ SỐ ẢNH KHÔNG HỢP LỆ!"
                client.replyMessage(
                    Message(text=reply_text),
                    message_object, thread_id, thread_type, ttl=120000
                )
            else:
                client.replyMessage(
                    Message(text="⚠️ SỐ THỨ TỰ KHÔNG HỢP LỆ!"),
                    message_object, thread_id, thread_type, ttl=120000
                )
        except ValueError:
            client.replyMessage(
                Message(text="⚠️ SỐ THỨ TỰ VÀ CHỈ SỐ ẢNH PHẢI LÀ SỐ NGUYÊN!"),
                message_object, thread_id, thread_type, ttl=120000
            )
        return

    # lệnh rao image clear <index>
    if len(parts) == 4 and parts[1].lower() == "image" and parts[2].lower() == "clear":
        try:
            index = int(parts[3])
            rao_data = next((r for r in rao_list if r["index"] == index), None)
            if rao_data:
                rao_data["images"] = []
                rao_data["created_at"] = datetime.now(vn_tz)
                save_rao_message(username, rao_data, index)
                reply_text = f"✅ ĐÃ XÓA TẤT CẢ ẢNH KHỎI SỐ {index}!"
                client.replyMessage(
                    Message(text=reply_text),
                    message_object, thread_id, thread_type, ttl=120000
                )
            else:
                client.replyMessage(
                    Message(text="⚠️ SỐ THỨ TỰ KHÔNG HỢP LỆ!"),
                    message_object, thread_id, thread_type, ttl=120000
                )
        except ValueError:
            client.replyMessage(
                Message(text="⚠️ SỐ THỨ TỰ PHẢI LÀ SỐ NGUYÊN!"),
                message_object, thread_id, thread_type, ttl=120000
            )
        return

    # lệnh rao video add <index> <link>
    if len(parts) >= 4 and parts[1].lower() == "video" and parts[2].lower() == "add":
        try:
            index = int(parts[3])
            rao_data = next((r for r in rao_list if r["index"] == index), None)
            if rao_data:
                video_link = parts[4].strip()
                if validate_url(video_link):
                    videos = rao_data.get("videos", [])
                    if video_link not in [v["normalUrl"] for v in videos]:
                        video_data = {
                            "normalUrl": video_link,
                            "thumb": video_link,
                            "duration": 10000,
                            "width": 720,
                            "height": 720
                        }
                        videos.append(video_data)
                        rao_data["videos"] = videos
                        rao_data["created_at"] = datetime.now(vn_tz)
                        save_rao_message(username, rao_data, index)
                        reply_text = f"✅ ĐÃ THÊM VIDEO VÀO SỐ {index}: {video_link}"
                    else:
                        reply_text = "⚠️ VIDEO ĐÃ CÓ TRONG DANH SÁCH!"
                else:
                    reply_text = f"⚠️ LINK VIDEO KHÔNG HỢP LỆ: {video_link}"
                client.replyMessage(
                    Message(text=reply_text),
                    message_object, thread_id, thread_type, ttl=120000
                )
            else:
                client.replyMessage(
                    Message(text="⚠️ SỐ THỨ TỰ KHÔNG HỢP LỆ!"),
                    message_object, thread_id, thread_type, ttl=120000
                )
        except ValueError:
            client.replyMessage(
                Message(text="⚠️ SỐ THỨ TỰ PHẢI LÀ SỐ NGUYÊN!"),
                message_object, thread_id, thread_type, ttl=120000
            )
        return

    # lệnh rao video remove <index> <video_index>
    if len(parts) == 5 and parts[1].lower() == "video" and parts[2].lower() == "remove":
        try:
            index = int(parts[3])
            video_index = int(parts[4]) - 1
            rao_data = next((r for r in rao_list if r["index"] == index), None)
            if rao_data:
                videos = rao_data.get("videos", [])
                if 0 <= video_index < len(videos):
                    removed_video = videos.pop(video_index)
                    rao_data["videos"] = videos
                    rao_data["created_at"] = datetime.now(vn_tz)
                    save_rao_message(username, rao_data, index)
                    reply_text = f"✅ ĐÃ XÓA VIDEO SỐ {video_index + 1} KHỎI SỐ {index}: {removed_video['normalUrl']}"
                else:
                    reply_text = "⚠️ CHỈ SỐ VIDEO KHÔNG HỢP LỆ!"
                client.replyMessage(
                    Message(text=reply_text),
                    message_object, thread_id, thread_type, ttl=120000
                )
            else:
                client.replyMessage(
                    Message(text="⚠️ SỐ THỨ TỰ KHÔNG HỢP LỆ!"),
                    message_object, thread_id, thread_type, ttl=120000
                )
        except ValueError:
            client.replyMessage(
                Message(text="⚠️ SỐ THỨ TỰ VÀ CHỈ SỐ VIDEO PHẢI LÀ SỐ NGUYÊN!"),
                message_object, thread_id, thread_type, ttl=120000
            )
        return

    # lệnh rao video clear <index>
    if len(parts) == 4 and parts[1].lower() == "video" and parts[2].lower() == "clear":
        try:
            index = int(parts[3])
            rao_data = next((r for r in rao_list if r["index"] == index), None)
            if rao_data:
                rao_data["videos"] = []
                rao_data["created_at"] = datetime.now(vn_tz)
                save_rao_message(username, rao_data, index)
                reply_text = f"✅ ĐÃ XÓA TẤT CẢ VIDEO KHỎI SỐ {index}!"
                client.replyMessage(
                    Message(text=reply_text),
                    message_object, thread_id, thread_type, ttl=120000
                )
            else:
                client.replyMessage(
                    Message(text="⚠️ SỐ THỨ TỰ KHÔNG HỢP LỆ!"),
                    message_object, thread_id, thread_type, ttl=120000
                )
        except ValueError:
            client.replyMessage(
                Message(text="⚠️ SỐ THỨ TỰ PHẢI LÀ SỐ NGUYÊN!"),
                message_object, thread_id, thread_type, ttl=120000
            )
        return

    # lệnh rao card <index> <uid> <nội dung>
    if len(parts) >= 5 and parts[1].lower() == "card" and parts[2].isdigit():
        try:
            index = int(parts[2])
            uid = parts[3].strip()
            content = " ".join(parts[4:]).strip()
            rao_data = next((r for r in rao_list if r["index"] == index), None)
            if rao_data:
                if not uid.isdigit():
                    reply_text = "⚠️ UID PHẢI LÀ SỐ HỢP LỆ!"
                elif not content:
                    reply_text = "⚠️ NỘI DUNG DANH THIẾP KHÔNG ĐƯỢC ĐỂ TRỐNG!"
                else:
                    rao_data["card"] = {
                        "status": "SAVED",
                        "uid": uid,
                        "content": content
                    }
                    rao_data["created_at"] = datetime.now(vn_tz)
                    save_rao_message(username, rao_data, index)
                    reply_text = f"✅ ĐÃ LƯU DANH THIẾP SỐ {index}:\nUID: {uid}\nNỘI DUNG: {content}"
                client.replyMessage(
                    Message(text=reply_text),
                    message_object, thread_id, thread_type, ttl=120000
                )
            else:
                client.replyMessage(
                    Message(text="⚠️ SỐ THỨ TỰ KHÔNG HỢP LỆ!"),
                    message_object, thread_id, thread_type, ttl=120000
                )
        except ValueError:
            client.replyMessage(
                Message(text="⚠️ SỐ THỨ TỰ PHẢI LÀ SỐ NGUYÊN!"),
                message_object, thread_id, thread_type, ttl=120000
            )
        return

    # lệnh rao card clear <index>
    if len(parts) == 4 and parts[1].lower() == "card" and parts[2].lower() == "clear":
        try:
            index = int(parts[3])
            rao_data = next((r for r in rao_list if r["index"] == index), None)
            if rao_data:
                rao_data["card"] = {}
                rao_data["created_at"] = datetime.now(vn_tz)
                save_rao_message(username, rao_data, index)
                reply_text = f"✅ ĐÃ XÓA DANH THIẾP SỐ {index}!"
                client.replyMessage(
                    Message(text=reply_text),
                    message_object, thread_id, thread_type, ttl=120000
                )
            else:
                client.replyMessage(
                    Message(text="⚠️ SỐ THỨ TỰ KHÔNG HỢP LỆ!"),
                    message_object, thread_id, thread_type, ttl=120000
                )
        except ValueError:
            client.replyMessage(
                Message(text="⚠️ SỐ THỨ TỰ PHẢI LÀ SỐ NGUYÊN!"),
                message_object, thread_id, thread_type, ttl=120000
            )
        return

    # lệnh rao <nội dung> <thời gian> <on/off>
    try:
        enabled = parts[-1].lower() == "on"
        interval = parse_time_input(parts[-2])
        message_text = " ".join(parts[1:-2]) if len(parts) > 3 else ""
    except ValueError as e:
        client.replyMessage(
            Message(text=f"⚠️ LỖI: {str(e)}"),
            message_object, thread_id, thread_type, ttl=120000
        )
        return

    if not message_text:
        client.replyMessage(
            Message(text="⚠️ VUI LÒNG NHẬP NỘI DUNG RAO!"),
            message_object, thread_id, thread_type, ttl=120000
        )
        return

    # tìm số thứ tự lớn nhất
    file_paths = get_file_paths(username)
    json_files = sorted(file_paths["messages"].glob("*.json"), key=lambda x: int(x.stem) if x.stem.isdigit() else float('inf'))
    next_index = max([int(f.stem) for f in json_files if f.stem.isdigit()] + [0]) + 1

    # thêm tin nhắn vào danh sách
    message_data = {
        "index": next_index,
        "message": message_text,
        "interval": interval,
        "enabled": enabled,
        "created_at": datetime.now(vn_tz),
        "images": [],
        "videos": [],
        "card": {}
    }
    rao_list.append(message_data)
    save_rao_message(username, message_data, next_index)

    # bật rao mới nếu được yêu cầu
    if enabled:
        rao_running[next_index] = True
        thread = threading.Thread(
            target=rao_loop,
            args=(client, next_index, username),
            daemon=True,
            name=f"raothread-{next_index}-{username}"
        )
        rao_threads[next_index] = thread
        thread.start()

    status_text = "✅ ĐÃ BẬT TỰ ĐỘNG RAO" if enabled else "✅ ĐÃ LƯU"
    reply_text = (
        f"{status_text}\n"
        f"SỐ THỨ TỰ: {next_index}\n"
        f"THỜI GIAN: {interval} PHÚT\n"
        f"NỘI DUNG: {message_text}"
    )
    client.replyMessage(
        Message(text=reply_text),
        message_object, thread_id, thread_type, ttl=120000
    )
    
def PTA():
    return {
        'rao': handle_rao_command
    }