from zlapi.models import Message
import random
import datetime

des = {
    'version': "1.0.9",
    'credits': "ngbao",
    'description': "Tạo thơ với tên người yêu",
    'power': "Thành viên"
}

# Emoji theo chủ đề
love_emojis = ["💖", "❤️", "💘", "💞", "💓", "💗", "💝", "💌", "💕"]
dream_emojis = ["🌙", "🌠", "✨", "🌌", "🪐", "🌟", "🦋"]
nature_emojis = ["🌸", "🌻", "🌼", "🌷", "🍃", "🌹", "🌺"]
weather_emojis = ["☀️", "🌧️", "🌤️", "⛅", "🌈", "❄️", "🌪️"]
other_emojis = ["📜", "🎵", "💬", "🕰️", "📅", "📖", "🫶"]

# Sticker dễ thương và tình yêu
LOVE_STICKERS = [
    {"sticker_type": 3, "sticker_id": "21296", "category_id": "10093"},
    {"sticker_type": 3, "sticker_id": "21297", "category_id": "10093"},
    {"sticker_type": 3, "sticker_id": "21301", "category_id": "10093"},
    {"sticker_type": 3, "sticker_id": "21304", "category_id": "10093"},
    {"sticker_type": 3, "sticker_id": "21306", "category_id": "10093"},
]

def pick_unique_emojis(n):
    all_emojis = love_emojis + dream_emojis + nature_emojis + weather_emojis + other_emojis
    return random.sample(all_emojis, n)

def generate_love_poem(name: str) -> str:
    templates = [
        "{0}{name} ơi, em là ánh nắng {1},\nSoi sáng tim anh từng ngày {2}.\nDẫu gió cuốn qua bao mùa {3},\nYêu em là điều chẳng thể đổi thay {4}.",
        "Trái tim anh mang tên {name} {0},\nTựa bản nhạc du dương đêm vắng {1}.\nTừng vần thơ anh viết về em {2},\nMỗi chữ là một giấc mơ trong sáng {3}.",
        "Anh không giỏi viết thơ {0},\nNhưng vì {name} mà lòng đầy cảm hứng {1}.\nNụ cười em như hoa nở trong nắng {2},\nLàm lòng anh xao xuyến không ngừng {3}.",
        "{name} là giấc mơ anh từng ước {0},\nLà vì sao sáng giữa trời đêm {1}.\nAnh viết lên ngàn câu yêu thương {2},\nChỉ mong em mãi là của riêng anh {3}.",
        "Từ khi gặp {name}, lòng anh khác lạ {0},\nTim đập nhanh mỗi khi em cười {1}.\nTừng ánh mắt, từng hơi thở {2},\nĐều khiến anh mộng mơ khôn nguôi {3}.",
        "Anh gửi yêu thương theo làn gió {0},\nMong rằng {name} sẽ đón nhận {1}.\nTình anh trao trọn chẳng phai {2},\nNhư cánh hoa giữa trời lộng gió {3}.",
        "{name} – người khiến anh nhớ nhung {0},\nTừng ngày qua là một chương tình thơ {1}.\nDù thời gian có đổi thay {2},\nYêu em vẫn là điều tuyệt vời nhất {3}.",
        "{name} à, em là tia nắng nhỏ {0},\nSưởi ấm tim anh giữa ngày đông {1}.\nChỉ cần em ở cạnh bên {2},\nMọi thứ đều trở nên màu hồng {3}.",
        "Nếu anh là bản tình ca {0},\nThì em là nốt nhạc ngọt ngào nhất {1}.\nDẫu cuộc đời muôn ngả lối đi {2},\nTim anh vẫn chọn {name} trước nhất {3}.",
        "Ngày gặp {name}, bầu trời xanh hơn {0},\nNắng cũng nhẹ nhàng, gió cũng dịu êm {1}.\nTừ ánh mắt đến nụ cười ấy {2},\nĐều khiến tim anh lạc trong mê cung êm đềm {3}.",
        "Từng dòng tin nhắn anh gửi {0},\nLà từng nhịp tim nhớ {name} mỗi đêm {1}.\nDù chẳng nói nhiều bằng lời {2},\nNhưng tình anh là thật, không mềm không phai {3}.",
        "{name}, em là định nghĩa của dịu dàng {0},\nLà bài thơ anh viết mãi không dừng {1}.\nChẳng cần mùa xuân hay hạ sang {2},\nChỉ cần em, là cả bầu trời yêu thương {3}.",

        # Phiên chợ tình
        "Phiên chợ tình anh mua nhầm em {0},\nTưởng hàng trưng bày ai ngờ là vợ {1}.\nDù giá chẳng niêm yết rõ ràng {2},\nNhưng tim này đã trao chẳng nỡ trả hàng {3}.",
        "{name} à, anh lỡ mua nhầm em phiên chợ tình {0},\nNgỡ chỉ thoáng qua, ai ngờ lòng rung động thật nhanh {1}.\nTừ ánh mắt đến nụ cười ấy {2},\nAnh đành gói ghém tim mình gửi em luôn {3}.",
        "Phiên chợ tình mù sương lối nhỏ {0},\nAnh thấy em như thấy nắng qua đồi {1}.\nChẳng mặc cả, chẳng cần suy nghĩ {2},\nMua em rồi – trọn đời chẳng đổi thôi {3}.",
        "Anh đi chợ tình mua chút mộng mơ {0},\nChẳng ngờ vướng ánh mắt ngẩn ngơ của {name} {1}.\nMột lời nói khiến tim anh rối cả mùa {2},\nGiờ muốn trả cũng lỡ rồi... yêu luôn cho vừa {3}.",
        "Bán không em, anh xin một ánh nhìn {0},\nChợ tình hôm ấy {name} đứng một mình {1}.\nAnh ngỡ mình chỉ ghé qua cho biết {2},\nAi ngờ mang về cả cuộc đời rung rinh {3}.",
    ]
    emoji_set = pick_unique_emojis(5)
    template = random.choice(templates)
    poem = template.format(*emoji_set, name=name)
    date = datetime.datetime.now().strftime("%d/%m/%Y")
    return f"*Thơ tỏ tình dành cho {name} - {date}*\n\n{poem}"

def handle_lovebykai_command(message, message_object, thread_id, thread_type, author_id, client):
    text = message.split()
    if len(text) < 2:
        error_message = Message(text="🚦 Vui lòng nhập tên người bạn muốn tỏ tình. Ví dụ: love bin")
        client.sendMessage(error_message, thread_id, thread_type, ttl=60000)
        return

    name = " ".join(text[1:]).strip().title()
    poem = generate_love_poem(name)

    # Gửi thơ
    client.replyMessage(
        Message(text=poem),
        message_object,
        thread_id,
        thread_type,
        ttl=150000
    )

    # Gửi sticker
    try:
        sticker = random.choice(LOVE_STICKERS)
        client.sendSticker(
            sticker['sticker_type'],
            sticker['sticker_id'],
            sticker['category_id'],
            thread_id,
            thread_type,
            ttl=150000
        )
    except Exception as e:
        print(f"[LovePoem] Gửi sticker lỗi: {e}")

    # Thả reaction
    reactions = love_emojis + dream_emojis + nature_emojis + weather_emojis + other_emojis
    for reaction in random.sample(reactions, 6):
        try:
            client.addReaction(reaction, message_object, thread_id, thread_type)
        except Exception as e:
            print(f"[LovePoem] Thêm reaction lỗi: {e}")

def PTA():
    return {
        'totinh': handle_lovebykai_command
    }