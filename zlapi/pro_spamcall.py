import threading
import time
from core.bot_sys import admin_cao, get_user_name_by_id, read_settings
from zlapi.models import *

def extract_uids_from_mentions(message_object):
    uids = []
    if message_object.mentions:
        uids = [mention['uid'] for mention in message_object.mentions if 'uid' in mention]
    return uids

def handle_spamcall_command(bot, message_object, author_id, thread_id, thread_type, command):
    def call():
        try:
            if not admin_cao(bot, author_id):
                bot.replyMessage(Message(text="❌ Bạn không phải admin bot!"), 
                               message_object, thread_id=thread_id, 
                               thread_type=thread_type, ttl=100000)
                return

            # Parse command and mentions
            parts = command.split()
            if len(parts) < 2:
                bot.replyMessage(Message(text="➜ ❌ Sai cú pháp! Dùng: call [số lần] + tag người dùng"), 
                               message_object, thread_id=thread_id, 
                               thread_type=thread_type, ttl=100000)
                return

            try:
                spam_count = int(parts[1])
                if spam_count <= 0 or spam_count > 1000000000000000000:
                    raise ValueError
            except ValueError:
                bot.replyMessage(Message(text="➜ ❌ Số lần phải là số nguyên dương (1-100)."), 
                               message_object, thread_id=thread_id, 
                               thread_type=thread_type, ttl=100000)
                return

            # Get target IDs from mentions
            target_ids = extract_uids_from_mentions(message_object)
            if not target_ids:
                bot.replyMessage(Message(text="➜ ❌ Vui lòng tag ít nhất một người dùng!"), 
                               message_object, thread_id=thread_id, 
                               thread_type=thread_type, ttl=100000)
                return

            # Process each target
            target_names = []
            for target_id in target_ids:
                user_name = get_user_name_by_id(bot, target_id)
                if user_name:
                    target_names.append(user_name)

            if not target_names:
                bot.replyMessage(Message(text="➜ ❌ Không tìm thấy người dùng nào hợp lệ!"), 
                               message_object, thread_id=thread_id, 
                               thread_type=thread_type, ttl=100000)
                return

            # Send initial notification
            targets_str = ", ".join(target_names)
            bot.replyMessage(Message(text=f"➜ 📞 Alo alo {targets_str} ơi! Chuẩn bị tinh thần đón nhận {spam_count} cuộc gọi nha! 🌪️"), 
                           message_object, thread_id=thread_id, 
                           thread_type=thread_type, ttl=100000)

            # Execute spam calls for each target
            for target_id in target_ids:
                for i in range(spam_count):
                    callid_random = bot.TaoIDCall()
                    bot.sendCall(target_id, callid_random)
                    time.sleep(2)

            # Send completion message
            bot.replyMessage(Message(text=f"➜ Đã gọi {spam_count} lần đến {targets_str}"), 
                           message_object, thread_id=thread_id, 
                           thread_type=thread_type, ttl=100000)

        except Exception as e:
            bot.replyMessage(Message(text=f"➜ 🐞 Lỗi: {str(e)}"), 
                           message_object, thread_id=thread_id, 
                           thread_type=thread_type, ttl=100000)

    try:
        thread = threading.Thread(target=call)
        thread.daemon = True
        thread.start()
    except Exception as e:
        bot.replyMessage(Message(text=f"➜ 🐞 Lỗi khi tạo thread: {str(e)}"), 
                        message_object, thread_id=thread_id, 
                        thread_type=thread_type, ttl=100000)