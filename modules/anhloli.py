from zlapi.models import Message
import requests
import os

des = {
    'version': "1.1.0",
    'credits': "ngbao",
    'description': "Quản lý và gửi sản phẩm Zalo.\n⚙️Các lệnh có sẵn:\n- product create [tên] [giá] (Reply vào ảnh)\n- product send [tên]\n- product list\n- product delete [tên].",
    'power': "Quản trị viên"
}


def handle_anhgai_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        url = "https://api.ntmdz.online/images/loli"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        thinh = data.get('data')

        sendmess = f"{thinh}"
        message_to_send = Message(text=sendmess)

        api_url = 'https://api.ntmdz.online/images/loli'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }

        response = requests.get(api_url, headers=headers)
        response.raise_for_status()

        data = response.json()
        image_url = data['url']

        image_response = requests.get(image_url, headers=headers)
        image_path = 'temp_image.jpeg'

        with open(image_path, 'wb') as f:
            f.write(image_response.content)

        client.sendLocalImage(
            image_path, 
           
            thread_id=thread_id,
            thread_type=thread_type,
            width=1200,
            height=1600
        )

        os.remove(image_path)

    except requests.exceptions.RequestException as e:
        error_message = Message(text=f"Đã xảy ra lỗi khi gọi API: {str(e)}")
        client.sendMessage(error_message, thread_id, thread_type)
    except Exception as e:
        error_message = Message(text=f"Đã xảy ra lỗi: {str(e)}")
        client.sendMessage(error_message, thread_id, thread_type)

def PTA():
    return {
        'anhloli': handle_anhgai_command
    }