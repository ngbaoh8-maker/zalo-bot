from zlapi.models import Message, ZaloAPIException, ThreadType, Mention, MultiMention
from config import ADMIN
import time
import random
import json

des = {
    'version': "1.0.3",
    'credits': "ngbao",
    'description': "Lệnh tagall ẩn nhóm.",
    'power': "Quản trị viên Bot"
}

def is_admin(author_id):
    try:
        import os
        import json
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'seting.json')
        if not os.path.exists(path):
            path = 'seting.json'
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        admin_main = str(data.get('admin', ''))
        vip = [str(x) for x in data.get('vip_adm', [])]
        adm_list = [str(x) for x in data.get('adm', [])]
        
        author_str = str(author_id)
        
        try:
            from config import ADMIN
            config_admin = str(ADMIN)
        except:
            config_admin = ""
            
        admins = set([admin_main, config_admin] + vip + adm_list)
        if "" in admins:
            admins.remove("")
            
        return author_str in admins
    except Exception as e:
        print(f"Error checking admin in tagall: {e}")
        return str(author_id) == str(ADMIN)

def getIDsGroup(self, url):
    params = {
        "zpw_ver": 648,
        "zpw_type": 30
    }
    payload = {
        "params": self._encode({
            "link": str(url),
            "clientLang": "vi"
        })
    }

    try:
        response = self._post("https://tt-group-wpa.chat.zalo.me/api/group/link/ginfo",
                              params=params,
                              data=payload)

        data = response.json()
        results = data.get("data") if data.get("error_code") == 0 else None

        if results:
            results = self._decode(results)
            results = results.get("data") if results.get("data") else results

            if results is None:
                results = {"error_code": 1337, "error_message": "Data is None"}

            if isinstance(results, str):
                try:
                    results = json.loads(results)
                except:
                    results = {"error_code": 1337, "error_message": results}

            return results

        error_code = data.get("error_code")
        error_message = data.get("error_message") or data.get("data")
        raise ZaloAPIException(f"Error #{error_code} when sending requests: {error_message}")

    except ZaloAPIException as e:
        raise e
    except Exception as e:
        raise ZaloAPIException(f"An unexpected error occurred: {e}")

def handle_tagall_command(message, message_object, thread_id, thread_type, author_id, client):
    if not is_admin(author_id):
        client.send(
            Message(text="Bạn không có quyền sử dụng lệnh này! Chỉ quản trị viên mới có thể dùng lệnh tagall."),
            thread_id=thread_id,
            thread_type=thread_type,
            ttl=60000
        )
        return

    try:
        parts = message.split(" ", 2)
        group_link = None
        tagall_message = None
        target_thread_id = thread_id

        if len(parts) == 2:
            tagall_message = parts[1].strip()
        elif len(parts) == 3:
            group_link = parts[1].strip()
            tagall_message = parts[2].strip()
        else:
            client.send(
                Message(text="Vui lòng cung cấp đúng định dạng: 'all <nội dung>' hoặc 'all <link nhóm Zalo> <nội dung>'"),
                thread_id=thread_id,
                thread_type=thread_type,
                ttl=60000
            )
            return

        if group_link:
            if not group_link.startswith("https://zalo.me/g/"):
                client.send(
                    Message(text="Link nhóm Zalo không hợp lệ! Vui lòng cung cấp link bắt đầu bằng https://zalo.me/g/"),
                    thread_id=thread_id,
                    thread_type=thread_type,
                ttl=60000
                )
                return

            try:
                group_info = client.getIDsGroup(group_link)
                if group_info.get("error_code") == 1337:
                    client.send(
                        Message(text=f"Lỗi khi lấy thông tin nhóm: {group_info.get('error_message')}"),
                        thread_id=thread_id,
                        thread_type=thread_type,
                ttl=60000
                    )
                    return
                target_thread_id = group_info.get("groupId")
                if not target_thread_id:
                    client.send(
                        Message(text="Không thể lấy ID nhóm từ link cung cấp!"),
                        thread_id=thread_id,
                        thread_type=thread_type,
                ttl=60000
                    )
                    return
            except ZaloAPIException as e:
                client.send(
                    Message(text=f"Lỗi API khi lấy thông tin nhóm: {e}"),
                    thread_id=thread_id,
                    thread_type=thread_type,
                ttl=60000
                )
                return

        try:
            group_info = client.fetchGroupInfo(target_thread_id).gridInfoMap[target_thread_id]
            members = group_info.get('memVerList', [])
            if not members:
                client.send(
                    Message(text="Nhóm không có thành viên hoặc không thể lấy danh sách thành viên!"),
                    thread_id=thread_id,
                    thread_type=thread_type,
                ttl=60000
                )
                return

            text = f"<b>{tagall_message}</b>"
            mentions = []
            offset = len(text)

            for member in members:
                member_parts = member.split('_', 1)
                if len(member_parts) != 2:
                    continue
                user_id, user_name = member_parts
                mention = Mention(uid=user_id, offset=offset, length=len(user_name) + 1, auto_format=False)
                mentions.append(mention)
                offset += len(user_name) + 2

            multi_mention = MultiMention(mentions)

            try:
                client.send(
                    Message(text=text, mention=multi_mention, parse_mode="HTML"),
                    thread_id=target_thread_id,
                    thread_type=ThreadType.GROUP
                )
            except Exception as e:
                client.send(
                    Message(text=f"Lỗi khi gửi tin nhắn: {e}"),
                    thread_id=thread_id,
                    thread_type=thread_type,
                ttl=60000
                )

        except Exception as e:
            client.send(
                Message(text=f"Lỗi khi lấy thông tin nhóm: {e}"),
                thread_id=thread_id,
                thread_type=thread_type,
                ttl=60000
            )

    except ZaloAPIException as e:
        client.send(
            Message(text=f"Lỗi API: {e}"),
            thread_id=thread_id,
            thread_type=thread_type,
                ttl=60000
        )
    except Exception as e:
        client.send(
            Message(text=f"Lỗi chung: {e}"),
            thread_id=thread_id,
            thread_type=thread_type,
                ttl=60000
        )

def PTA():
    return {
        'all': handle_tagall_command
    }