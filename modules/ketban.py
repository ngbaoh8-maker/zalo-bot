from zlapi.models import *
import time
import json

des = {
    'version': "2.0.0",
    'credits': "ngbao",
    'description': "Module kết bạn full chức năng",
    'power': "Admin"
}


def handle_ketban_command(message, message_object, thread_id, thread_type, author_id, self):
    try:
        if hasattr(message_object, "text") and isinstance(message_object.text, str):
            message_text = message_object.text.strip()
        else:
            message_text = str(message or "")

        args = message_text.split()

        # Hiển thị hướng dẫn
        if len(args) < 2:
            help_text = (
                "📘 LỆNH KẾT BẠN 📘\n"
                "━━━━━━━━━━━━━━━\n"
                "➡️ ?ketban add @user       → Gửi lời mời kết bạn\n"
                "➡️ ?ketban remove @user    → Xóa bạn bè\n"
                "➡️ ?ketban block @user     → Chặn người dùng\n"
                "➡️ ?ketban unblock @user   → Mở chặn người dùng\n"
                "➡️ ?ketban all             → Gửi kết bạn toàn bộ 1 nhóm\n"
                "➡️ ?ketban allgroup        → Gửi kết bạn toàn bộ TẤT CẢ NHÓM BOT ĐANG THAM GIA\n"
                "━━━━━━━━━━━━━━━"
            )
            self.replyMessage(Message(text=help_text), message_object, thread_id, thread_type, ttl=60000)
            return

        sub = args[1].lower()
        if sub == "add":
            addfrito(message, message_object, thread_id, thread_type, author_id, self)
        elif sub == "remove":
            removefrito(message, message_object, thread_id, thread_type, author_id, self)
        elif sub == "block":
            blockto(message, message_object, thread_id, thread_type, author_id, self)
        elif sub == "unblock":
            unblockto(message, message_object, thread_id, thread_type, author_id, self)
        elif sub == "all":
            ketban_in_group(message, message_object, thread_id, thread_type, author_id, self)
        elif sub == "allgroup":
            ketban_all_group(message, message_object, thread_id, thread_type, author_id, self)
        else:
            self.replyMessage(Message(text=f"❌ Lệnh không hợp lệ: {sub}"),
                              message_object, thread_id, thread_type, ttl=60000)

    except Exception as e:
        self.replyMessage(
            Message(text=f"🚦 Lỗi khi thực hiện lệnh ketban: {str(e)}"),
            message_object, thread_id, thread_type, ttl=60000
        )



def blockto(message, message_object, thread_id, thread_type, author_id, self):
    user_id = get_target_user(message_object, thread_id, thread_type, self)
    if not user_id:
        return
    try:
        profile = get_profile(self, user_id)
        self.blockUser(user_id)
        self.replyMessage(Message(text=f"🚦 Đã chặn {profile}."), message_object, thread_id, thread_type, ttl=60000)
    except Exception as e:
        self.replyMessage(Message(text=f"🚦 Không thể chặn người dùng. Lỗi: {str(e)}"),
                          message_object, thread_id, thread_type, ttl=60000)


def unblockto(message, message_object, thread_id, thread_type, author_id, self):
    user_id = get_target_user(message_object, thread_id, thread_type, self)
    if not user_id:
        return
    try:
        profile = get_profile(self, user_id)
        self.unblockUser(user_id)
        self.replyMessage(Message(text=f"🚦 Đã mở chặn {profile}."), message_object, thread_id, thread_type, ttl=60000)
    except Exception as e:
        self.replyMessage(Message(text=f"🚦 Không thể mở chặn người dùng. Lỗi: {str(e)}"),
                          message_object, thread_id, thread_type, ttl=60000)


def addfrito(message, message_object, thread_id, thread_type, author_id, self):
    try:
        user_id = get_target_user(message_object, thread_id, thread_type, self)
        if not user_id or user_id == self.uid:
            return

        profile = get_profile(self, user_id)
        self.sendFriendRequest(user_id, "Xin chào, mình muốn kết bạn!")
        self.replyMessage(Message(text=f"🚦 Đã gửi lời mời kết bạn đến {profile}."),
                          message_object, thread_id, thread_type, ttl=60000)
    except Exception as e:
        self.replyMessage(Message(text=f"🚦 Không thể kết bạn. Lỗi: {str(e)}"),
                          message_object, thread_id, thread_type, ttl=60000)


def removefrito(message, message_object, thread_id, thread_type, author_id, self):
    try:
        user_id = get_target_user(message_object, thread_id, thread_type, self)
        if not user_id or user_id == self.uid:
            return

        profile = get_profile(self, user_id)
        self.unfriendUser(user_id)
        self.replyMessage(Message(text=f"🚦 Đã xóa kết bạn {profile}."),
                          message_object, thread_id, thread_type, ttl=60000)
    except Exception as e:
        self.replyMessage(Message(text=f"🚦 Không thể xóa kết bạn. Lỗi: {str(e)}"),
                          message_object, thread_id, thread_type, ttl=60000)


def ketban_in_group(message, message_object, thread_id, thread_type, author_id, self):
    from zlapi.models import MultiMsgStyle, MessageStyle

    if thread_type != ThreadType.GROUP:
        self.replyMessage(Message(text="🚦 Lệnh này chỉ hoạt động trong nhóm."),
                          message_object, thread_id, thread_type, ttl=60000)
        return

    try:
        group_info_raw = self.fetchGroupInfo(thread_id)
        if isinstance(group_info_raw, str):
            group_info_raw = json.loads(group_info_raw)

        if hasattr(group_info_raw, "gridInfoMap"):
            group_info = group_info_raw.gridInfoMap.get(thread_id, {})
        else:
            group_info = group_info_raw.get("gridInfoMap", {}).get(thread_id, {})

        members = group_info.get("memVerList", [])
        total = len(members)

        header = "KẾT BẠN TOÀN NHÓM"
        msg = f"{header}\n➜ Tổng thành viên: {total}\n➜ Đang gửi lời mời..."

        style = MultiMsgStyle([
            MessageStyle(offset=0, length=len(header), style="bold", auto_format=False),
            MessageStyle(offset=0, length=len(header), style="color", color="#db342e", auto_format=False)
        ])

        self.replyMessage(Message(text=msg, style=style),
                          message_object, thread_id, thread_type, ttl=120000)

        success, fail = 0, 0

        for mem in members:
            uid = mem.get("uid")
            if uid == self.uid:
                continue

            try:
                name = get_profile(self, uid)
                self.sendFriendRequest(uid, f"Xin chào {name}! Kết bạn nhé?")
                success += 1
                time.sleep(0.15 if success < 40 else 0.5)
                if success >= 50:
                    break
            except:
                fail += 1

        result = f"{header}\n➜ Thành công: {success}\n➜ Thất bại: {fail}\nGiới hạn 50 lời mời."
        self.replyMessage(Message(text=result, style=style),
                          message_object, thread_id, thread_type, ttl=120000)

    except Exception as e:
        self.replyMessage(Message(text=f"❌ Lỗi: {str(e)}"),
                          message_object, thread_id, thread_type, ttl=60000)


def ketban_all_group(message, message_object, thread_id, thread_type, author_id, self):
    from zlapi.models import MultiMsgStyle, MessageStyle

    header = "KẾT BẠN TOÀN BỘ TẤT CẢ NHÓM"
    msg = f"{header}\n➜ Đang quét danh sách nhóm..."

    style = MultiMsgStyle([
        MessageStyle(offset=0, length=len(header), style="bold", auto_format=False),
        MessageStyle(offset=0, length=len(header), style="color", color="#db342e", auto_format=False)
    ])

    self.replyMessage(Message(text=msg, style=style),
                      message_object, thread_id, thread_type, ttl=120000)

    try:

        groups_raw = self.fetchAllGroups()

        # Nếu API trả về string -> convert JSON
        if isinstance(groups_raw, str):
            try:
                groups_raw = json.loads(groups_raw)
            except:
                self.replyMessage(Message(text="❌ Lỗi khi đọc danh sách nhóm."),
                                  message_object, thread_id, thread_type, ttl=60000)
                return

        # Lấy danh sách nhóm đúng chuẩn
        if hasattr(groups_raw, "gridVerMap"):
            group_ids = list(groups_raw.gridVerMap.keys())
        elif isinstance(groups_raw, dict):
            group_ids = list(groups_raw.get("gridVerMap", {}).keys())
        else:
            group_ids = []

        if not group_ids:
            self.replyMessage(Message(text="❌ Không tìm thấy nhóm nào."),
                              message_object, thread_id, thread_type, ttl=60000)
            return

        success, fail = 0, 0
        sent = set()  # tránh gửi trùng


        for gid in group_ids:

            group_info_raw = self.fetchGroupInfo(str(gid))

            # Nếu API trả về string -> convert JSON
            if isinstance(group_info_raw, str):
                try:
                    group_info_raw = json.loads(group_info_raw)
                except:
                    continue

            # Lấy dữ liệu group đúng chuẩn bất kể API trả về gì
            if hasattr(group_info_raw, "gridInfoMap"):
                group_info = group_info_raw.gridInfoMap.get(str(gid), {})
            elif isinstance(group_info_raw, dict):
                group_info = group_info_raw.get("gridInfoMap", {}).get(str(gid), {})
            else:
                group_info = {}

            members = group_info.get("memVerList", [])
            if not isinstance(members, list):
                continue


            for mem in members:

                # chuẩn hóa UID
                if isinstance(mem, dict):
                    uid = mem.get("uid")
                else:
                    uid = str(mem).split("_")[0]

                if not uid or uid == self.uid or uid in sent:
                    continue

                try:
                    # lấy tên người dùng (có xử lý lỗi)
                    name = "Bạn mới"
                    try:
                        info = self.fetchUserInfo(uid)
                        profile = info.changed_profiles.get(uid, {})
                        name = profile.get("zaloName", name)
                    except:
                        pass

                    # gửi lời mời
                    self.sendFriendRequest(uid, f"Xin chào {name}, kết bạn nhé!")

                    success += 1
                    sent.add(uid)

                    # tránh bị chặn API
                    time.sleep(0.15 if success < 40 else 0.5)

                    if success >= 50:  # giới hạn tối đa
                        break

                except:
                    fail += 1
                    time.sleep(0.2)

            if success >= 50:
                break


        result = (
            f"{header}\n"
            f"➜ Tổng nhóm: {len(group_ids)}\n"
            f"➜ Thành công: {success}\n"
            f"➜ Thất bại: {fail}\n"

        )

        self.replyMessage(Message(text=result, style=style),
                          message_object, thread_id, thread_type, ttl=120000)

    except Exception as e:
        self.replyMessage(Message(text=f"❌ Lỗi khi chạy allgroup: {str(e)}"),
                          message_object, thread_id, thread_type, ttl=60000)


def get_target_user(message_object, thread_id, thread_type, client):
    if thread_type == ThreadType.USER:
        return thread_id
    if message_object.mentions:
        return message_object.mentions[0]['uid']
    client.replyMessage(Message(text="🚦 Vui lòng tag người dùng."),
                        message_object, thread_id, thread_type, ttl=60000)
    return None


def get_profile(client, uid):
    try:
        info = client.fetchUserInfo(uid)
        profile = info.changed_profiles.get(uid, {})
        return profile.get("zaloName", "Không xác định")
    except:
        return "Không xác định"


def PTA():
    return {
        'ketban': handle_ketban_command
    }
