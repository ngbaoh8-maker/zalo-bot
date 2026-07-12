import os, importlib, time, traceback
from zlapi.models import Message, ThreadType

des = {
    'version': "2.2.0",
    'credits': "ngbao",
    'description': "Reload toàn bộ command siêu nhanh, đẹp, có emoji trạng thái",
    'power': "Quản trị viên Bot"
}

ADMIN_ID = "637876082720685615"
MODULES_PATH = "modules"

# ===============================
# HÀM PHỤ TRỢ
# ===============================
def is_admin(uid):
    return str(uid) == str(ADMIN_ID)

def format_status(text, emoji):
    return f"{emoji} {text}"

# ===============================
# LỆNH CHÍNH
# ===============================
def handle_cmd_reload(message, message_object, thread_id, thread_type, author_id, client):


    start_time = time.time()
    reloaded = []
    failed = []

    try:
        client.replyMessage(
            Message(text="🔄 Đang reload toàn bộ module... chờ chút nhé 💫"),
            message_object, thread_id, thread_type
        )

        # Duyệt tất cả file .py trong folder modules
        for file in os.listdir(MODULES_PATH):
            if not file.endswith(".py") or file.startswith("_"):
                continue

            module_name = file[:-3]
            full_import = f"{MODULES_PATH}.{module_name}"

            try:
                if full_import in importlib.sys.modules:
                    importlib.reload(importlib.sys.modules[full_import])
                else:
                    importlib.import_module(full_import)
                reloaded.append(module_name)
            except Exception as e:
                failed.append((module_name, str(e)))

        duration = round(time.time() - start_time, 2)
        total = len(reloaded) + len(failed)

        msg = "⚙️ Kết quả Reload Module:\n\n"
        msg += f"{format_status('Đã kiểm tra:', '📦')} {total} modules\n"
        msg += f"{format_status('Thành công:', '✅')} {len(reloaded)}\n"
        msg += f"{format_status('Thất bại:', '❌')} {len(failed)}\n"
        msg += f"{format_status('Thời gian:', '⏱️')} {duration}s\n\n"

        if reloaded:
            msg += "✨ Danh sách reload thành công:\n" + ", ".join(reloaded[:15])
            if len(reloaded) > 15:
                msg += f" ... và {len(reloaded)-15} module khác.\n"
            msg += "\n"

        if failed:
            msg += "💀 Module lỗi:\n"
            for name, err in failed[:5]:
                msg += f"• {name}: {err}\n"
            if len(failed) > 5:
                msg += f"... và {len(failed)-5} module khác gặp lỗi.\n"

        msg += "\n🚀 Bot đã sẵn sàng hoạt động lại!"

        # Reaction + gửi kết quả
        try:
            if failed:
                client.sendReaction(message_object, "⚠️", thread_id, thread_type)
            else:
                client.sendReaction(message_object, "✅", thread_id, thread_type)
        except:
            pass

        client.replyMessage(Message(text=msg), message_object, thread_id, thread_type)

    except Exception as e:
        traceback.print_exc()
        client.replyMessage(
            Message(text=f"💥 Lỗi không mong muốn khi reload:\n{e}"),
            message_object, thread_id, thread_type
        )
        try:
            client.sendReaction(message_object, "❌", thread_id, thread_type)
        except:
            pass

# ===============================
# EXPORT CHO BOT LOAD
# ===============================
def PTA():
    return {
        "reload": handle_cmd_reload
    }