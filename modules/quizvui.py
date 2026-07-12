import random
import threading
import time
from zlapi.models import Message

des = {
    "version": "1.2",
    "credits": "ngbao",
    "description": "Quiz vui",
    "power": "Thành Viên"
}

QUESTION_TIME = 15
DELETE_AFTER = 300

active_quiz = {}
scores = {}

QUESTIONS = [
    {"q": "Thủ đô của Việt Nam là?", "choices": {"A": "Hà Nội", "B": "Hồ Chí Minh", "C": "Đà Nẵng", "D": "Huế"}, "ans": "A"},
    {"q": "AI là viết tắt của từ nào?", "choices": {"A": "Automatic Input", "B": "Artificial Intelligence", "C": "Auto Index", "D": "Active Interface"}, "ans": "B"},
    {"q": "Món ăn truyền thống của Nhật Bản gồm cơm cuốn với cá sống là?", "choices": {"A": "Sushi", "B": "Ramen", "C": "Tempura", "D": "Okonomiyaki"}, "ans": "A"},
]

def _delete_msg(client, msg, delay=DELETE_AFTER):
    def _task():
        try:
            time.sleep(delay)
            client.unsendMessage(msg.uid)
        except Exception:
            pass
    threading.Thread(target=_task, daemon=True).start()

def _end_question(thread_id, client):
    qstate = active_quiz.get(thread_id)
    if not qstate:
        return
    correct = qstate["answer"]
    answers = qstate["answers"]
    if not answers:
        text = f"⏰ Hết giờ! Không ai trả lời. Đáp án đúng: {correct}."
    else:
        winners = [uid for uid, ch in answers.items() if ch.upper() == correct.upper()]
        if winners:
            for uid in winners:
                scores[uid] = scores.get(uid, 0) + 1
            winners_txt = "\n".join(f"- UID: {uid}" for uid in winners)
            text = f"✅ Đáp án đúng là {correct}.\nNgười trả lời đúng:\n{winners_txt}\n(+1 điểm)"
        else:
            text = f"❌ Không ai đúng! Đáp án là {correct}."
    msg = client.sendMessage(Message(text=text), thread_id=thread_id, thread_type="GROUP")
    _delete_msg(client, msg)
    active_quiz.pop(thread_id, None)

def do_quiz(message, message_object, thread_id, thread_type, author_id, client):
    if thread_id in active_quiz:
        msg = client.replyMessage(Message(text="⚠️ Đang có câu hỏi diễn ra, chờ chút nhé!"), message_object, thread_id=thread_id, thread_type=thread_type)
        _delete_msg(client, msg)
        return
    q = random.choice(QUESTIONS)
    choices_text = "\n".join([f"{k}. {v}" for k, v in q["choices"].items()])
    text = f"🎯 Quiz nhanh! Bạn có {QUESTION_TIME}s để trả lời.\n\n{q['q']}\n\n{choices_text}\n\n👉 Trả lời bằng: !answer <A|B|C|D>"
    msg = client.replyMessage(Message(text=text), message_object, thread_id=thread_id, thread_type=thread_type)
    _delete_msg(client, msg)
    timer = threading.Timer(QUESTION_TIME, _end_question, args=(thread_id, client))
    active_quiz[thread_id] = {"question": q["q"], "answer": q["ans"], "answers": {}, "timer": timer, "ts": time.time()}
    timer.start()

def do_answer(message, message_object, thread_id, thread_type, author_id, client):
    parts = message.strip().split()
    if len(parts) < 2:
        msg = client.replyMessage(Message(text="⚠️ Gõ đúng: !answer A|B|C|D."), message_object, thread_id=thread_id, thread_type=thread_type)
        _delete_msg(client, msg)
        return
    choice = parts[1].strip().upper()
    if choice not in ["A", "B", "C", "D"]:
        msg = client.replyMessage(Message(text="⚠️ Chỉ chấp nhận A/B/C/D."), message_object, thread_id=thread_id, thread_type=thread_type)
        _delete_msg(client, msg)
        return
    qstate = active_quiz.get(thread_id)
    if not qstate:
        msg = client.replyMessage(Message(text="⚠️ Hiện không có câu hỏi nào!"), message_object, thread_id=thread_id, thread_type=thread_type)
        _delete_msg(client, msg)
        return
    qstate["answers"][author_id] = choice
    correct = qstate["answer"]
    if choice == correct:
        scores[author_id] = scores.get(author_id, 0) + 1
        msg = client.replyMessage(Message(text=f"🎉 Chính xác! +1 điểm 🧠 (Đáp án: {correct})"), message_object, thread_id=thread_id, thread_type=thread_type)
    else:
        msg = client.replyMessage(Message(text=f"❌ Sai rồi! Đáp án đúng là {correct}."), message_object, thread_id=thread_id, thread_type=thread_type)
    _delete_msg(client, msg)

def do_score(message, message_object, thread_id, thread_type, author_id, client):
    pts = scores.get(author_id, 0)
    msg = client.replyMessage(Message(text=f"📊 UID {author_id}: {pts} điểm 🧠"), message_object, thread_id=thread_id, thread_type=thread_type)
    _delete_msg(client, msg)

def do_leaderboard(message, message_object, thread_id, thread_type, author_id, client):
    if not scores:
        msg = client.replyMessage(Message(text="📊 Chưa có ai ghi điểm!"), message_object, thread_id=thread_id, thread_type=thread_type)
        _delete_msg(client, msg)
        return
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    text = "🏆 Bảng xếp hạng Quiz:\n"
    for i, (uid, pts) in enumerate(ranked[:10], start=1):
        text += f"{i}. UID {uid} — {pts} điểm\n"
    msg = client.replyMessage(Message(text=text), message_object, thread_id=thread_id, thread_type=thread_type)
    _delete_msg(client, msg)

def do_resetquiz(message, message_object, thread_id, thread_type, author_id, client):
    for t in list(active_quiz.values()):
        timer = t.get("timer")
        if timer:
            timer.cancel()
    active_quiz.clear()
    scores.clear()
    msg = client.replyMessage(Message(text="🧹 Reset quiz và bảng điểm xong!"), message_object, thread_id=thread_id, thread_type=thread_type)
    _delete_msg(client, msg)

def PTA():
    return {
        "quiz": do_quiz,
        "answer": do_answer,
        "score": do_score,
        "leaderboard": do_leaderboard,
        "resetquiz": do_resetquiz
    }