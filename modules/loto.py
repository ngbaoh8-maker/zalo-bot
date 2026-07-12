# modules/loto.py
import random, time
from zlapi.models import Message

des = {
    "version": "2.0",
    "credits": "ngbao",
    "description": "Game Lô Tô",
    "power": "Thành Viên"
}

ACTIVE = {}  # lưu danh sách người chơi và số đã chọn

def normalize_numbers(nums):
    cleaned = []
    for n in nums:
        try:
            n = int(n)
            if 0 <= n <= 99:
                cleaned.append(n)
        except:
            pass
    return sorted(set(cleaned))

def format_nums(nums):
    return " ".join(f"{n:02d}" for n in sorted(nums))

def do_loto(message, message_object, thread_id, thread_type, author_id, client):
    ACTIVE[str(thread_id)] = {}
    text = (
        "🎰 *LÔ TÔ BẮT ĐẦU!*\n"
        "Hãy chọn 5 số từ 00–99 bằng lệnh:\n"
        "👉 `!lotocs 03 15 27 45 88`\n\n"
        "📌 Mỗi người chỉ được chọn *một lần mỗi ván*.\n"
        "Bot sẽ tự quay sau khi bạn chọn số 😎"
    )
    client.replyMessage(Message(text=text), message_object, thread_id, thread_type, ttl=180000)

def do_lotocs(message, message_object, thread_id, thread_type, author_id, client):
    if str(thread_id) not in ACTIVE:
        msg = "⚠️  Gõ `!loto` để bắt đầu ván mới🎰"
        client.replyMessage(Message(text=msg), message_object, thread_id, thread_type, ttl=180000)
        return

    user_data = ACTIVE[str(thread_id)]
    if author_id in user_data:
        msg = "🚫 Bạn đã chọn số rồi, đợi ván mới nha 😅"
        client.replyMessage(Message(text=msg), message_object, thread_id, thread_type, ttl=180000)
        return

    args = message.strip().split()[1:]
    if len(args) != 5:
        msg = "⚠️ Bạn phải nhập đúng *5 số từ 00–99*!\nVí dụ: `!lotocs 03 15 27 45 88`"
        client.replyMessage(Message(text=msg), message_object, thread_id, thread_type, ttl=180000)
        return

    numbers = normalize_numbers(args)
    if len(numbers) != 5:
        msg = "⚠️ Có số không hợp lệ! Hãy nhập lại 5 số khác từ 00–99 nha 🎯"
        client.replyMessage(Message(text=msg), message_object, thread_id, thread_type, ttl=180000)
        return

    user_data[author_id] = numbers
    chosen = format_nums(numbers)

    msg = f"🎟️ <@{author_id}> đã chọn số: {chosen}\n🎲 Chuẩn bị quay..."
    client.replyMessage(Message(text=msg), message_object, thread_id, thread_type, ttl=180000)

    # Delay quay
    time.sleep(3)

    # Tạo kết quả dễ trúng hơn 1–3 số
    base = random.sample(numbers, k=random.choice([1, 2, 3]))
    while len(base) < 5:
        n = random.randint(0, 99)
        if n not in base:
            base.append(n)
    draw = sorted(base)
    draw_text = format_nums(draw)

    matched = len(set(numbers) & set(draw))
    if matched == 5:
        result = "💥 JACKPOT! Bạn trúng 5/5 số 🎉"
    elif matched == 4:
        result = "💸 Gần trúng độc đắc! Bạn trúng 4/5 số 😎"
    elif matched == 3:
        result = "✨ Bạn trúng 3/5 số! Cũng hên lắm đó 🍀"
    elif matched == 2:
        result = "😄 Trúng 2/5 số, hên nhẹ nè!"
    elif matched == 1:
        result = "😅 Trúng 1/5 số, khởi đầu may mắn đó!"
    else:
        result = "😭 Không trúng số nào... Thử vận may ván sau nha!"

    final = (
        f"🎰 *KẾT QUẢ QUAY SỐ*\n"
        f"🧾 Kết quả: {draw_text}\n"
        f"🎯 {result}"
    )
    client.replyMessage(Message(text=final), message_object, thread_id, thread_type, ttl=180000)

def PTA():
    return {
        "loto": do_loto,
        "lotocs": do_lotocs
    }