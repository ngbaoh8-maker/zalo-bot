from zlapi.models import Message, ThreadType

# biến nhớ số hiện tại
CURRENT_NUMBER = None
GAME_RUNNING = False

des = {
    "version": "1.0",
    "credits": "ngbao",
    "description": "Mini-game đếm số bằng text",
    "power": "Thành viên"
}


def handle_demso(message, msg_obj, thread_id, thread_type, author_id, client):
    global CURRENT_NUMBER, GAME_RUNNING

    text = message.strip().lower()

    # ===== BẮT ĐẦU GAME =====
    if text == "bắt đầu đếm":
        CURRENT_NUMBER = 1
        GAME_RUNNING = True
        client.replyMessage(
            Message(text="🎮 Game bắt đầu!\nBot: **1**"),
            msg_obj, thread_id, thread_type
        )
        return

    # Nếu chưa bắt đầu mà gõ số → bỏ qua
    if not GAME_RUNNING:
        return

    # ===== NGƯỜI CHƠI TRẢ SỐ =====
    if text.isdigit():
        num = int(text)

        # số người chơi phải nói = CURRENT_NUMBER + 1
        expected = CURRENT_NUMBER + 1

        if num != expected:
            client.replyMessage(
                Message(text=f"❌ Sai rồi!\nBạn phải nói: **{expected}**"),
                msg_obj, thread_id, thread_type
            )
            return

        # cập nhật số
        CURRENT_NUMBER = num + 1

        # nếu vượt 100 → thắng game
        if CURRENT_NUMBER > 100:
            client.replyMessage(
                Message(text="🎉 Chúc mừng! Bạn đã đếm tới **100**!\n🏁 Game kết thúc ❤️"),
                msg_obj, thread_id, thread_type
            )
            GAME_RUNNING = False
            return

        # bot gửi số tiếp theo
        client.replyMessage(
            Message(text=f"{CURRENT_NUMBER}"),
            msg_obj, thread_id, thread_type
        )


def PTA():
    return {
        "demso": handle_demso
    }
