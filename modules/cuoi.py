import requests
import threading
import random
import os
import urllib.parse
from zlapi.models import Message

# Cấu hình thư mục lưu trữ âm thanh tạm thời
CACHE_PATH = "modules/cache"
if not os.path.exists(CACHE_PATH):
    os.makedirs(CACHE_PATH)

des = {
    'version': "1.0.0",
    'credits': "ngbao",
    'description': "Kể chuyện cười ngẫu nhiên kèm giọng nói",
    'power': "Thành viên"
}

def get_random_joke():
    # Sử dụng API truyện cười công khai hoặc danh sách tự định nghĩa
    # Ở đây tôi dùng một danh sách mẫu để đảm bảo bot luôn có nội dung hay
    jokes = [
        "Vợ bảo chồng: 'Anh ơi, máy giặt hỏng rồi.' - Chồng: 'Thế em đã kiểm tra ổ cắm chưa?' - Vợ: 'Kiểm tra rồi, vẫn cắm tốt.' - Chồng: 'Thế em đã bật nút chưa?' - Vợ: 'Bật rồi, nhưng nó không quay.' - Chồng: 'Thế em đã cho quần áo vào chưa?' - Vợ: 'Chưa, em đang thử máy mà!'",
        "Con: 'Bố ơi, tại sao con vịt lại kêu cạp cạp?' - Bố: 'Tại vì nó không biết nói tiếng người chứ sao!' - Con: 'Thế tại sao bố lại nói nhiều thế?' - Bố: 'Tại vì bố không phải là con vịt!'",
        "Trong giờ kiểm tra, thầy giáo thấy Tí cứ nhìn bài bạn. Thầy nhắc: 'Tí, em không được nhìn bài bạn!' - Tí đáp: 'Thưa thầy, em đâu có nhìn bài bạn, em đang kiểm tra xem bạn có chép giống em không thôi ạ!'",
        "Vợ: 'Anh ơi, anh thấy em hôm nay có gì khác không?' - Chồng: 'Có chứ, hôm nay em hỏi câu này sớm hơn mọi khi 2 tiếng!'"
    ]
    return random.choice(jokes)

def handle_joke_command(message, message_object, thread_id, thread_type, author_id, client):
    def process():
        audio_path = None
        try:
            client.sendReaction(message_object, "😆", thread_id, thread_type)
            
            # 1. Lấy nội dung truyện
            joke_text = get_random_joke()
            
            # 2. Tạo Voice bằng Google TTS (Tiếng Việt)
            # URL này không cần API Key
            tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={urllib.parse.quote(joke_text)}&tl=vi&client=tw-ob"
            
            audio_path = os.path.join(CACHE_PATH, f"joke_{author_id}.mp3")
            
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(tts_url, headers=headers, stream=True)
            
            with open(audio_path, 'wb') as f:
                f.write(r.content)

            # 3. Gửi văn bản trước
            client.replyMessage(Message(text=f"📖 Chuyện cười:\n\n{joke_text}"), message_object, thread_id, thread_type)
            
            # 4. Gửi file voice (Sử dụng hàm sendLocalVoice hoặc sendLocalAudio tùy bản zlapi)
            # Thường là sendLocalAudio cho file mp3
            client.sendLocalAudio(
                audio_path,
                thread_id,
                thread_type
            )

        except Exception as e:
            print(f"Lỗi kể chuyện: {e}")
            client.replyMessage(Message(text="⚠️ Bot đang bị đau họng, không kể chuyện được rồi!"), message_object, thread_id, thread_type)
        finally:
            if audio_path and os.path.exists(audio_path):
                try: os.remove(audio_path)
                except: pass

    threading.Thread(target=process, daemon=True).start()

def PTA():
    return {'cuoi': handle_joke_command, 'kechuyen': handle_joke_command}