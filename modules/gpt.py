from zlapi.models import Message
import requests
import random
import time

des = {
    'version': "FREE-1.0",
    'credits': "ngbao",
    'description': "Hỏi GPT",
    'power': "Thành Viên"
}

# Danh sách API free (luân phiên)
FREE_GPT_APIS = [
    "https://gptgo.ai/api/chat",
    "https://api.chatanywhere.tech/v1/chat/completions"
]

def ask_gpt_free(prompt):
    api = random.choice(FREE_GPT_APIS)

    if "gptgo.ai" in api:
        r = requests.post(
            api,
            json={
                "prompt": prompt,
                "model": "gpt-3.5-turbo"
            },
            timeout=30
        )
        return r.text

    if "chatanywhere" in api:
        r = requests.post(
            api,
            headers={"Content-Type": "application/json"},
            json={
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            },
            timeout=30
        )
        data = r.json()
        return data["choices"][0]["message"]["content"]

    return None

def handle_gpt_command(message, message_object, thread_id, thread_type, author_id, client):
    print(f"[GPT FREE] {author_id}: {message}")

    try:
        parts = message.split(" ", 1)
        if len(parts) < 2:
            client.replyMessage(
                Message(text="🤖 Dùng: .gpt <câu hỏi>"),
                message_object, thread_id, thread_type
            )
            return

        prompt = parts[1].strip()
        if not prompt:
            client.replyMessage(
                Message(text="❌ Câu hỏi không được trống."),
                message_object, thread_id, thread_type
            )
            return

        try:
            client.sendReaction(message_object, "⏳", thread_id, thread_type, reactionType=75)
        except:
            pass

        answer = ask_gpt_free(prompt)

        if not answer:
            client.replyMessage(
                Message(text="❌ GPT free hiện không phản hồi, thử lại sau."),
                message_object, thread_id, thread_type
            )
            return

        client.replyMessage(
            Message(text=f"🤖 GPT Free:\n\n{answer}"),
            message_object, thread_id, thread_type, ttl=120000
        )

        try:
            client.sendReaction(message_object, "✅", thread_id, thread_type, reactionType=75)
        except:
            pass

    except Exception as e:
        print(f"[GPT FREE ERROR] {e}")
        client.replyMessage(
            Message(text="❌ Lỗi GPT free."),
            message_object, thread_id, thread_type
        )

def PTA():
    return {
        'gpt': handle_gpt_command
    }
