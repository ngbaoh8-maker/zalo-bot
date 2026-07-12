import os
import json
import time
import threading
import logging
import requests
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image, ImageDraw, ImageFont
from zlapi.models import Message, ThreadType
from config import ADMIN

des = {
    'version': "1.6.0",
    'credits': "Bii Hot",
    'description': "rai ALL nhóm + Card set + Disbox + Custom Thumbnail + 2 ảnh cùng lúc + Tùy chỉnh thời gian",
    'power': "ADMIN"
}

logger = logging.getLogger(__name__)

rai_ALL_RUNNING = False
rai_START_TIME = None      
rai_LAST_CYCLE_TIME = None  # Thời điểm bắt đầu vòng rãi gần nhất
rai_DELAY_MINUTES = 60  # Mặc định 60 phút
STEP_DELAY = 0.3        # Delay giữa các payload trong 1 nhóm
GROUP_DELAY = 0.5       # Delay giữa 2 nhóm
RAI_WORKERS = 5         # Số nhóm gửi song song cùng lúc

rai_DISBOX_LIST = set()

CONFIG_PATH = "modules/cache/rai_config.json"
LOCAL_IMAGE_PATH_1 = "modules/cache/rai_image_1.png"
LOCAL_IMAGE_PATH_2 = "modules/cache/rai_image_2.png"

# Giữ lại LOCAL_IMAGE_PATH để tương thích cũ
LOCAL_IMAGE_PATH = LOCAL_IMAGE_PATH_1

def is_disboxed(gid):
    return str(gid) in rai_DISBOX_LIST

CARD_DATA = {
    "uid": "1262618053229730684",
    "content": "cần dịch vụ thì ib acc này 💝"
}

def get_all_group_ids(client):
    try:
        all_groups = client.fetchAllGroups()
        if all_groups and hasattr(all_groups, 'gridVerMap'):
            return list(all_groups.gridVerMap.keys())
    except Exception as e:
        logger.error(f"Lỗi lấy nhóm: {e}")
    return []

# URL ảnh (hỗ trợ tối đa 2 ảnh)
IMAGE_URL = "https://photo-stal-13.zdn.vn/gr/jxl/f8f139116b20aa7ef331/2887499661097496742.jxl"
IMAGE_URL_2 = ""  # URL ảnh thứ 2, mặc định rỗng

# Text hiển thị khi rãi
THUMBNAIL_TEXT = "Nhận code theo web theo yc và tool mua bot dis, bot mess python, và bot zalo, tele tool get xu hosting mỗi ngày bao API key bypass capcha và chỉ lấy auth acc các loại tool mess,dis,zalo bán các via cổ fb, fb tick bán các API nhận rãi thuê 24/24 cân dịch v gi ib sđt này ạ 0993637159"

link_payloads = [
    {
        "linkUrl": "https://zalo.me/g/rgoajpgcfuufmu17x7d6",
        "title": "Nhận code theo web theo yc và tool mua bot dis, bot mess python, và bot zalo, tele tool get xu hosting mỗi ngày bao API key bypass capcha và chỉ lấy auth acc các loại tool mess,dis,zalo bán các via cổ fb, fb tick bán các API nhận rãi thuê 24/24 cân dịch v gi ib sđt này ạ 0993637159",
        "domainUrl": "zalo.me",
        "desc": "Chéo kéo"
    },
]

def load_config():
    global IMAGE_URL, IMAGE_URL_2, THUMBNAIL_TEXT, rai_DELAY_MINUTES, rai_DISBOX_LIST, CARD_DATA, link_payloads
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
                IMAGE_URL = config.get("image_url", IMAGE_URL)
                IMAGE_URL_2 = config.get("image_url_2", IMAGE_URL_2)
                THUMBNAIL_TEXT = config.get("rai_text", THUMBNAIL_TEXT)
                rai_DELAY_MINUTES = config.get("delay_minutes", rai_DELAY_MINUTES)
                rai_DISBOX_LIST = set(config.get("disbox_list", list(rai_DISBOX_LIST)))
                CARD_DATA = config.get("card_data", CARD_DATA)
                
                # Update link payloads title
                if len(link_payloads) > 0:
                    link_payloads[0]["title"] = THUMBNAIL_TEXT
        except Exception as e:
            logger.error(f"Lỗi load config rãi: {e}")

def save_config():
    try:
        config = {
            "image_url": IMAGE_URL,
            "image_url_2": IMAGE_URL_2,
            "rai_text": THUMBNAIL_TEXT,
            "delay_minutes": rai_DELAY_MINUTES,
            "disbox_list": list(rai_DISBOX_LIST),
            "card_data": CARD_DATA
        }
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Lỗi save config rãi: {e}")

def download_image_to_path(url, path):
    """Tải ảnh từ URL và lưu vào path, trả về True nếu thành công."""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(response.content)
        return True
    except Exception as e:
        logger.error(f"Lỗi tải ảnh từ {url}: {e}")
        return False

def ensure_default_image():
    if not os.path.exists(LOCAL_IMAGE_PATH_1):
        logger.info(f"Đang tải ảnh mặc định từ: {IMAGE_URL}")
        if download_image_to_path(IMAGE_URL, LOCAL_IMAGE_PATH_1):
            logger.info("Đã lưu ảnh mặc định 1 thành công.")
    if IMAGE_URL_2 and not os.path.exists(LOCAL_IMAGE_PATH_2):
        logger.info(f"Đang tải ảnh mặc định 2 từ: {IMAGE_URL_2}")
        if download_image_to_path(IMAGE_URL_2, LOCAL_IMAGE_PATH_2):
            logger.info("Đã lưu ảnh mặc định 2 thành công.")

def create_thumbnail_with_text(image_url, text, output_width=600):
    """Tạo thumbnail: ảnh trên + text dưới"""
    try:
        # Download ảnh từ URL
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content)).convert("RGB")
        
        # Resize ảnh giữ tỷ lệ
        aspect_ratio = img.height / img.width
        new_height = int(output_width * aspect_ratio)
        img = img.resize((output_width, new_height), Image.Resampling.LANCZOS)
        
        # Tính chiều cao vùng text
        try:
            font = ImageFont.truetype("modules/cache/font/BeVietnamPro-Regular.ttf", 28)
        except:
            try:
                font = ImageFont.truetype("/system/fonts/DroidSans.ttf", 28)
            except:
                font = ImageFont.load_default()
        
        # Tạo canvas tạm để đo text
        temp_draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
        lines = text.split('\n')
        line_heights = []
        max_width = 0
        
        for line in lines:
            bbox = temp_draw.textbbox((0, 0), line, font=font)
            line_height = bbox[3] - bbox[1]
            line_width = bbox[2] - bbox[0]
            line_heights.append(line_height)
            max_width = max(max_width, line_width)
        
        text_height = sum(line_heights) + (len(lines) - 1) * 10 + 40  # padding
        
        # Tạo canvas mới: ảnh + vùng text
        final_height = new_height + text_height
        canvas = Image.new('RGB', (output_width, final_height), '#1a1a1a')
        
        # Paste ảnh vào trên
        canvas.paste(img, (0, 0))
        
        # Vẽ text
        draw = ImageDraw.Draw(canvas)
        y_offset = new_height + 20
        
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (output_width - text_width) // 2
            
            # Shadow
            draw.text((x+2, y_offset+2), line, font=font, fill='#000000')
            # Text chính
            draw.text((x, y_offset), line, font=font, fill='#ffffff')
            
            y_offset += line_heights[i] + 10
        
        # Save
        output = BytesIO()
        canvas.save(output, format='PNG', quality=95)
        output.seek(0)
        
        return output
        
    except Exception as e:
        logger.error(f"Lỗi tạo thumbnail: {e}")
        return None

def upload_to_uguu(file_obj, filename="thumbnail.png"):
    """Upload ảnh lên uguu.se"""
    try:
        files = {'files[]': (filename, file_obj, 'image/png')}
        response = requests.post('https://uguu.se/upload.php', files=files, timeout=15)
        response.raise_for_status()
        
        # Kiểm tra response không rỗng trước khi parse JSON
        raw = response.text.strip()
        if not raw:
            logger.error("Lỗi upload uguu: response rỗng")
            return None
        
        try:
            data = response.json()
        except ValueError as je:
            logger.error(f"Lỗi parse JSON uguu (response: {raw[:100]}): {je}")
            return None
        
        if data.get('success') and len(data.get('files', [])) > 0:
            return data['files'][0]['url']
        logger.error(f"Lỗi upload uguu: success=False, data={data}")
    except Exception as e:
        logger.error(f"Lỗi upload uguu: {e}")
    return None

def get_thumbnail_url():
    """Tạo và upload thumbnail, cache URL. Luôn trả về URL an toàn, không raise exception."""
    try:
        if not hasattr(get_thumbnail_url, 'cached_url'):
            thumbnail = create_thumbnail_with_text(IMAGE_URL, THUMBNAIL_TEXT)
            if thumbnail:
                url = upload_to_uguu(thumbnail)
                if url:
                    get_thumbnail_url.cached_url = url
                    logger.info(f"✅ Đã tạo thumbnail: {url}")
                    return url
            # Fallback về ảnh gốc nếu upload thất bại
            logger.warning("⚠️ Không tạo được thumbnail, fallback về ảnh gốc")
            get_thumbnail_url.cached_url = IMAGE_URL
        return get_thumbnail_url.cached_url
    except Exception as e:
        logger.error(f"Lỗi get_thumbnail_url: {e}")
        return IMAGE_URL

def send_all_payloads(client, gid):  # noqa: C901
    # Lấy thumbnail URL
    thumbnail_url = get_thumbnail_url()
    
    # 1. Gửi các link payloads
    for link in link_payloads:
        try:
            client.sendLink(
                linkUrl=link["linkUrl"],
                title=link["title"],
                domainUrl=link["domainUrl"],
                desc=link["desc"],
                thumbnailUrl=thumbnail_url,
                thread_id=gid,
                thread_type=ThreadType.GROUP
            )
        except Exception as e:
            logger.error(f"Lỗi gửi link rãi gid={gid}: {e}")
        time.sleep(STEP_DELAY)

    # 2. Gửi card
    for key in ["uid"]:
        if CARD_DATA.get(key):
            try:
                uid = CARD_DATA[key]
                user_info = client.fetchUserInfo(uid).get(uid, {})
                avatar_url = user_info.get("avatar", "")
                client.sendBusinessCard(
                    userId=uid,
                    qrCodeUrl=avatar_url,
                    phone=CARD_DATA["content"],
                    thread_id=gid,
                    thread_type=ThreadType.GROUP
                )
                time.sleep(0.3)
            except:
                pass

    # 3. Gửi text + ảnh cùng lúc (tối đa 2 ảnh)
    has_img1 = os.path.exists(LOCAL_IMAGE_PATH_1)
    has_img2 = os.path.exists(LOCAL_IMAGE_PATH_2) and IMAGE_URL_2

    if has_img1 and has_img2:
        # Gửi ảnh 1 kèm text (ngôn)
        try:
            client.sendLocalImage(
                imagePath=LOCAL_IMAGE_PATH_1,
                thread_id=gid,
                thread_type=ThreadType.GROUP,
                message=Message(text=THUMBNAIL_TEXT)
            )
            time.sleep(STEP_DELAY)
        except Exception as e:
            logger.error(f"Lỗi gửi ảnh 1 rãi: {e}")

        # Gửi ảnh 2 liền sau (cùng "lúc", cách nhau 1 dòng trắng bằng delay ngắn)
        try:
            client.sendLocalImage(
                imagePath=LOCAL_IMAGE_PATH_2,
                thread_id=gid,
                thread_type=ThreadType.GROUP,
                message=Message(text="\n")
            )
            time.sleep(STEP_DELAY)
        except Exception as e:
            logger.error(f"Lỗi gửi ảnh 2 rãi: {e}")

    elif has_img1:
        # Chỉ có 1 ảnh: gửi kèm text
        try:
            client.sendLocalImage(
                imagePath=LOCAL_IMAGE_PATH_1,
                thread_id=gid,
                thread_type=ThreadType.GROUP,
                message=Message(text=THUMBNAIL_TEXT)
            )
            time.sleep(STEP_DELAY)
        except Exception as e:
            logger.error(f"Lỗi gửi ảnh rãi: {e}")

def send_with_retry(client, gid, max_retries=3):
    """Gửi payload đến 1 nhóm, retry tối đa max_retries lần nếu thất bại."""
    for attempt in range(1, max_retries + 1):
        try:
            send_all_payloads(client, gid)
            return True
        except Exception as e:
            logger.warning(f"[rai] Lỗi nhóm {gid} lần {attempt}/{max_retries}: {e}")
            if attempt < max_retries:
                time.sleep(1 * attempt)  # 1s, 2s
    return False

def _send_task(client, gid):
    """Task wrapper cho ThreadPoolExecutor."""
    ok = send_with_retry(client, gid, max_retries=3)
    return gid, ok

def rai_all_loop(client):
    global rai_ALL_RUNNING, rai_DELAY_MINUTES, rai_LAST_CYCLE_TIME

    while rai_ALL_RUNNING:
        rai_LAST_CYCLE_TIME = time.time()
        
        group_ids = get_all_group_ids(client)
        active_groups = [gid for gid in group_ids if not is_disboxed(gid)]

        logger.info(f"[rai ALL] 🚀 Bắt đầu rãi {len(active_groups)}/{len(group_ids)} nhóm song song ({RAI_WORKERS} luồng)")

        failed_groups = []
        success_count = 0

        # ── Vòng 1: Gửi song song với ThreadPoolExecutor ──
        with ThreadPoolExecutor(max_workers=RAI_WORKERS) as executor:
            futures = {
                executor.submit(_send_task, client, gid): gid
                for gid in active_groups
                if rai_ALL_RUNNING
            }
            for future in as_completed(futures):
                if not rai_ALL_RUNNING:
                    executor.shutdown(wait=False)
                    break
                try:
                    gid, ok = future.result()
                    if ok:
                        success_count += 1
                    else:
                        failed_groups.append(gid)
                        logger.error(f"[rai ALL] ❌ Nhóm {gid} thất bại — sẽ retry sau")
                except Exception as e:
                    gid = futures[future]
                    failed_groups.append(gid)
                    logger.error(f"[rai ALL] ❌ Nhóm {gid} exception: {e}")

        # ── Vòng 2: Retry song song các nhóm thất bại ──
        if failed_groups and rai_ALL_RUNNING:
            logger.info(f"[rai ALL] 🔄 Retry {len(failed_groups)} nhóm chưa rãi được...")
            still_failed = []
            with ThreadPoolExecutor(max_workers=RAI_WORKERS) as executor:
                futures = {
                    executor.submit(_send_task, client, gid): gid
                    for gid in failed_groups
                    if rai_ALL_RUNNING
                }
                for future in as_completed(futures):
                    if not rai_ALL_RUNNING:
                        break
                    try:
                        gid, ok = future.result()
                        if ok:
                            success_count += 1
                            logger.info(f"[rai ALL] ✅ Nhóm {gid} retry thành công!")
                        else:
                            still_failed.append(gid)
                    except Exception as e:
                        gid = futures[future]
                        still_failed.append(gid)

            if still_failed:
                logger.warning(f"[rai ALL] ⚠️ {len(still_failed)} nhóm vẫn thất bại: {still_failed}")
            logger.info(f"[rai ALL] ✅ Hoàn thành — {success_count}/{len(active_groups)} thành công, {len(still_failed)} thất bại")
        else:
            logger.info(f"[rai ALL] ✅ Hoàn thành — {success_count}/{len(active_groups)} nhóm thành công")

        delay_seconds = rai_DELAY_MINUTES * 60
        logger.info(f"[rai ALL] ⏳ Đợi {rai_DELAY_MINUTES} phút ({format_runtime(delay_seconds)}) trước vòng tiếp...")
        
        for _ in range(delay_seconds):
            if not rai_ALL_RUNNING:
                break
            time.sleep(1)

def format_runtime(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h}h {m}m {s}s"

def rai_menu_text():
    return (
        "📢 MENU rai\n"
        "━━━━━━━━━━━━━━\n"
        "🔹 .rai on         → Bật rai toàn bộ nhóm\n"
        "🔹 .rai off        → Tắt rai\n"
        "🔹 .rai test       → Test gửi trong nhóm hiện tại\n"
        "🔹 .rai info       → Xem thời gian rãi tiếp theo\n"
        "\n"
        "⏰ THỜI GIAN\n"
        "🔹 .rai time <phút> → Đặt thời gian delay\n"
        "                      (VD: .rai time 60)\n"
        "\n"
        "🖼 RÃI ẢNH & NGÔN\n"
        "🔹 .rai anh <url>        → Đổi ảnh 1 rãi\n"
        "🔹 .rai anh <url1> <url2>→ Đổi 2 ảnh rãi cùng lúc\n"
        "🔹 .rai ngon <text>      → Đổi ngôn (chữ) rãi\n"
        "\n"
        "🚫 DISBOX (Chặn nhóm)\n"
        "🔹 .rai disbox          → Chặn nhóm hiện tại\n"
        "🔹 .rai disbox <gid>    → Chặn theo ID\n"
        "🔹 .rai undisbox <gid>  → Gỡ chặn\n"
        "🔹 .rai disbox list     → Xem danh sách chặn\n"
        "\n"
        "🪪 DANH THIẾP & STATUS\n"
        "🔹 .rai card set <uid> <nội dung>\n"
        "🔹 .rai status\n"
        "🔹 .rai refresh        → Làm mới thumbnail\n"
    )

def handle_rai_command(message_text, message_object, thread_id, thread_type, author_id, client):
    global rai_ALL_RUNNING, CARD_DATA, rai_DISBOX_LIST, rai_DELAY_MINUTES, rai_START_TIME, rai_LAST_CYCLE_TIME, IMAGE_URL, IMAGE_URL_2, THUMBNAIL_TEXT

    # Lấy danh sách admin từ client (đúng, tránh bug so sánh string)
    admin_list = [str(client.ADMIN)] + [str(a) for a in getattr(client, 'ADM', [])]
    if str(author_id) not in admin_list:
        client.replyMessage(
            Message(text="⚠️ Bạn không có quyền sử dụng lệnh này."),
            message_object, thread_id, thread_type
        )
        return

    parts = message_text.strip().split(maxsplit=3)
    if len(parts) < 2:
        # Không có sub-lệnh → hiện menu
        client.replyMessage(Message(text=rai_menu_text()), message_object, thread_id, thread_type)
        return

    cmd = parts[1]

    # ── MENU ──
    if cmd == "menu":
        client.replyMessage(Message(text=rai_menu_text()), message_object, thread_id, thread_type)
        return


    # ── TIME COMMAND ──
    if cmd == "time":
        if len(parts) >= 3:
            try:
                minutes = int(parts[2])
                if minutes <= 0:
                    client.replyMessage(Message(text="❌ Số phút phải lớn hơn 0"), message_object, thread_id, thread_type)
                    return
                rai_DELAY_MINUTES = minutes
                save_config()
                client.replyMessage(Message(text=f"✅ Đã đặt thời gian delay: {minutes} phút"), message_object, thread_id, thread_type)
            except ValueError:
                client.replyMessage(Message(text="❌ Số phút không hợp lệ"), message_object, thread_id, thread_type)
        else:
            client.replyMessage(Message(text=f"⏰ Thời gian delay hiện tại: {rai_DELAY_MINUTES} phút\n\nCú pháp: .rai time <phút>"), message_object, thread_id, thread_type)
        return

    # ── ANH (URL) COMMAND ──
    # Hỗ trợ: .rai anh <url1> hoặc .rai anh <url1> <url2>
    if cmd == "anh":
        after_anh = message_text.split("anh", 1)[1].strip()
        if not after_anh:
            client.replyMessage(
                Message(text="❌ Cú pháp:\n.rai anh <url_ảnh_1>\n.rai anh <url_ảnh_1> <url_ảnh_2>"),
                message_object, thread_id, thread_type
            )
            return

        # Tách 2 URL (phân cách bằng khoảng trắng)
        url_parts = after_anh.split()
        url1 = url_parts[0].strip().strip("()")
        url2 = url_parts[1].strip().strip("()") if len(url_parts) >= 2 else ""

        client.replyMessage(
            Message(text=f"⏳ Đang tải {'2 ảnh' if url2 else 'ảnh'} từ URL..."),
            message_object, thread_id, thread_type
        )

        # Tải ảnh 1
        try:
            response = requests.get(url1, timeout=20)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content))
            img.verify()
            os.makedirs(os.path.dirname(LOCAL_IMAGE_PATH_1), exist_ok=True)
            with open(LOCAL_IMAGE_PATH_1, "wb") as f:
                f.write(response.content)
            IMAGE_URL = url1
        except OSError as e:
            import errno as _errno
            if e.errno == _errno.ENOSPC:
                client.replyMessage(Message(text="❌ Lỗi tải ảnh 1: Máy chủ/VPS đã hết sạch dung lượng đĩa (Disk Full)! Vui lòng dọn dẹp disk."), message_object, thread_id, thread_type)
            else:
                client.replyMessage(Message(text=f"❌ Lỗi tải ảnh 1: {str(e)}"), message_object, thread_id, thread_type)
            return
        except Exception as e:
            client.replyMessage(Message(text=f"❌ Lỗi tải ảnh 1: {str(e)}"), message_object, thread_id, thread_type)
            return

        # Tải ảnh 2 nếu có
        if url2:
            try:
                response2 = requests.get(url2, timeout=20)
                response2.raise_for_status()
                img2 = Image.open(BytesIO(response2.content))
                img2.verify()
                os.makedirs(os.path.dirname(LOCAL_IMAGE_PATH_2), exist_ok=True)
                with open(LOCAL_IMAGE_PATH_2, "wb") as f:
                    f.write(response2.content)
                IMAGE_URL_2 = url2
                save_config()

                # Reset cached thumbnail
                if hasattr(get_thumbnail_url, 'cached_url'):
                    delattr(get_thumbnail_url, 'cached_url')

                client.replyMessage(
                    Message(text="✅ Đã tải và cài 2 ảnh rãi thành công!\n🖼 Ảnh 1: " + url1 + "\n🖼 Ảnh 2: " + url2),
                    message_object, thread_id, thread_type
                )
            except OSError as e:
                IMAGE_URL_2 = ""
                save_config()
                if hasattr(get_thumbnail_url, 'cached_url'):
                    delattr(get_thumbnail_url, 'cached_url')
                import errno as _errno
                if e.errno == _errno.ENOSPC:
                    client.replyMessage(
                        Message(text="⚠️ Đã cài ảnh 1 thành công nhưng lỗi ảnh 2: Máy chủ/VPS hết sạch dung lượng đĩa (Disk Full)!"),
                        message_object, thread_id, thread_type
                    )
                else:
                    client.replyMessage(
                        Message(text=f"⚠️ Đã cài ảnh 1 thành công nhưng lỗi ảnh 2: {str(e)}\nChỉ dùng 1 ảnh khi rãi."),
                        message_object, thread_id, thread_type
                    )
            except Exception as e:
                # Ảnh 1 OK nhưng ảnh 2 lỗi
                IMAGE_URL_2 = ""
                save_config()
                if hasattr(get_thumbnail_url, 'cached_url'):
                    delattr(get_thumbnail_url, 'cached_url')
                client.replyMessage(
                    Message(text=f"⚠️ Đã cài ảnh 1 thành công nhưng lỗi ảnh 2: {str(e)}\nChỉ dùng 1 ảnh khi rãi."),
                    message_object, thread_id, thread_type
                )
        else:
            # Chỉ 1 ảnh — xóa ảnh 2 cũ nếu có
            IMAGE_URL_2 = ""
            if os.path.exists(LOCAL_IMAGE_PATH_2):
                try:
                    os.remove(LOCAL_IMAGE_PATH_2)
                except:
                    pass
            save_config()
            if hasattr(get_thumbnail_url, 'cached_url'):
                delattr(get_thumbnail_url, 'cached_url')
            client.replyMessage(
                Message(text="✅ Đã tải và cài đặt ảnh rãi mới thành công!"),
                message_object, thread_id, thread_type
            )
        return

    # ── NGON / TEXT COMMAND ──
    if cmd in ["ngon", "text"]:
        if len(parts) >= 3:
            new_text = message_text.split(cmd, 1)[1].strip()
            THUMBNAIL_TEXT = new_text
            if len(link_payloads) > 0:
                link_payloads[0]["title"] = new_text
            save_config()
            
            # Reset cached thumbnail
            if hasattr(get_thumbnail_url, 'cached_url'):
                delattr(get_thumbnail_url, 'cached_url')
                
            client.replyMessage(Message(text=f"✅ Đã cập nhật ngôn từ rãi mới:\n{new_text}"), message_object, thread_id, thread_type)
        else:
            client.replyMessage(Message(text="❌ Cú pháp: .rai ngon <nội dung rãi>"), message_object, thread_id, thread_type)
        return

    # ── INFO COMMAND ──
    if cmd == "info":
        if not rai_ALL_RUNNING:
            client.replyMessage(Message(text="❌ rai chưa được bật\nDùng .rai on để bật"), message_object, thread_id, thread_type)
            return
        
        if rai_LAST_CYCLE_TIME is None:
            client.replyMessage(Message(text="⏳ Đang khởi động vòng rãi đầu tiên..."), message_object, thread_id, thread_type)
            return
        
        # Tính thời gian đã trôi qua kể từ vòng rãi gần nhất
        elapsed_seconds = int(time.time() - rai_LAST_CYCLE_TIME)
        delay_seconds = rai_DELAY_MINUTES * 60
        remaining_seconds = max(0, delay_seconds - elapsed_seconds)
        
        if remaining_seconds == 0:
            info_text = (
                "⏰ THÔNG TIN RÃI\n"
                "━━━━━━━━━━━━━━\n"
                "• Trạng thái: ✅ ĐANG RÃI\n"
                "• Đang trong vòng rãi hiện tại..."
            )
        else:
            info_text = (
                "⏰ THÔNG TIN RÃI\n"
                "━━━━━━━━━━━━━━\n"
                f"• Trạng thái: 💤 ĐANG ĐỢI\n"
                f"• Thời gian đã chờ: {format_runtime(elapsed_seconds)}\n"
                f"• Thời gian còn lại: {format_runtime(remaining_seconds)}\n"
                f"• Delay mỗi vòng: {rai_DELAY_MINUTES} phút"
            )
        
        client.replyMessage(Message(text=info_text), message_object, thread_id, thread_type)
        return

    # ── DISBOX COMMANDS ──
    if cmd == "disbox":
        if len(parts) == 2:
            gid = str(thread_id)
            rai_DISBOX_LIST.add(gid)
            save_config()
            client.replyMessage(Message(text=f"✅ Đã disbox nhóm này\nID: {gid}"), message_object, thread_id, thread_type)
        elif len(parts) > 2 and parts[2].strip() == "list":
            if rai_DISBOX_LIST:
                text = "📋 DANH SÁCH DISBOX:\n" + "\n".join([f"• {gid}" for gid in rai_DISBOX_LIST])
            else:
                text = "📋 Hiện chưa có nhóm nào bị disbox"
            client.replyMessage(Message(text=text), message_object, thread_id, thread_type)
        else:
            gid = parts[2].strip()
            rai_DISBOX_LIST.add(gid)
            save_config()
            client.replyMessage(Message(text=f"✅ Đã thêm vào disbox\nID: {gid}"), message_object, thread_id, thread_type)
        return

    if cmd == "undisbox":
        if len(parts) > 2:
            gid = parts[2].strip()
            if gid in rai_DISBOX_LIST:
                rai_DISBOX_LIST.remove(gid)
                save_config()
                client.replyMessage(Message(text=f"✅ Đã gỡ disbox\nID: {gid}"), message_object, thread_id, thread_type)
            else:
                client.replyMessage(Message(text=f"❌ ID {gid} chưa bị disbox"), message_object, thread_id, thread_type)
        return

    # ── MENU ──
    if cmd == "menu":
        client.replyMessage(Message(text=rai_menu_text()), message_object, thread_id, thread_type)
        return
    
    # ── REFRESH ──
    if cmd == "refresh":
        if hasattr(get_thumbnail_url, 'cached_url'):
            delattr(get_thumbnail_url, 'cached_url')
        new_url = get_thumbnail_url()
        client.replyMessage(Message(text=f"✅ Đã làm mới thumbnail\n{new_url}"), message_object, thread_id, thread_type)
        return

    # ── STATUS ──
    if cmd == "status":
        disbox_count = len(rai_DISBOX_LIST)
        thumbnail_status = "✅ Đã tạo" if hasattr(get_thumbnail_url, 'cached_url') else "⏳ Chưa tạo"
        img2_status = f"✅ {IMAGE_URL_2[:40]}..." if IMAGE_URL_2 else "❌ Chưa cài"
        status_text = (
            "📊 STATUS rai\n"
            "━━━━━━━━━━━━━━\n"
            f"• Trạng thái: {'✅ ĐANG CHẠY' if rai_ALL_RUNNING else '❌ ĐANG TẮT'}\n"
            f"• Thời gian chạy: {format_runtime(int(time.time() - rai_START_TIME)) if rai_ALL_RUNNING and rai_START_TIME else 'Chưa chạy'}\n"
            f"• Delay giữa các vòng: {rai_DELAY_MINUTES} phút\n"
            f"• Nhóm bị disbox: {disbox_count}\n"
            f"• Thumbnail: {thumbnail_status}\n"
            f"• Ảnh 2: {img2_status}\n"
        )
        client.replyMessage(Message(text=status_text), message_object, thread_id, thread_type)
        return

    # ── ON (thay cho ALL) ──
    if cmd == "on" or cmd == "all":
        if rai_ALL_RUNNING:
            client.replyMessage(Message(text="⚠️ rai đang chạy rồi!"), message_object, thread_id, thread_type)
            return
        rai_ALL_RUNNING = True
        rai_START_TIME = time.time()
        threading.Thread(target=rai_all_loop, args=(client,), daemon=True).start()
        client.replyMessage(Message(text=f"✅ Đã bật rai\n⏰ Delay: {rai_DELAY_MINUTES} phút/vòng"), message_object, thread_id, thread_type)
        return

    # ── OFF ──
    if cmd == "off":
        rai_ALL_RUNNING = False
        rai_LAST_CYCLE_TIME = None
        client.replyMessage(Message(text="✅ Đã tắt rai"), message_object, thread_id, thread_type)
        return

    # ── TEST ──
    if cmd == "test":
        if thread_type != ThreadType.GROUP:
            client.replyMessage(Message(text="⚠️ Chỉ dùng trong nhóm"), message_object, thread_id, thread_type)
            return
        send_all_payloads(client, thread_id)
        client.replyMessage(Message(text="✅ Test thành công"), message_object, thread_id, thread_type)
        return

    # ── CARD ──
    if cmd == "card":
        if len(parts) >= 4 and parts[2] == "set":
            sub = parts[3].split(maxsplit=1)
            if len(sub) >= 2:
                CARD_DATA["uid"] = sub[0].strip()
                CARD_DATA["content"] = sub[1].strip()
                save_config()
                client.replyMessage(Message(text=f"✅ Đã set card\nUID: {CARD_DATA['uid']}\nNội dung: {CARD_DATA['content']}"), message_object, thread_id, thread_type)
            else:
                client.replyMessage(Message(text="❌ Cú pháp: .rai card set <uid> <nội dung>"), message_object, thread_id, thread_type)
        return


# ── Aliases để bot.py import không lỗi ──
handle_rai_command = handle_rai_command

def start_rai_scheduler(client):
    pass

# Load config and download default image if not present on import
load_config()
ensure_default_image()

def PTA():
    return {
        'rai': handle_rai_command,
    }
