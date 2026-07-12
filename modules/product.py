import os
import json
import requests
from io import BytesIO
from zlapi.models import Message, ThreadType
from zlapi import _util

des = {
    'version': "1.1.0",
    'credits': "ngbao",
    'description': "Quản lý và gửi sản phẩm Zalo.\n⚙️Các lệnh có sẵn:\n- product create [tên] [giá] (Reply vào ảnh)\n- product send [tên]\n- product list\n- product delete [tên].",
    'power': "Quản trị viên"
}

PRODUCTS_FILE = 'products.json'

def load_products():
    if not os.path.exists(PRODUCTS_FILE):
        return {}
    try:
        with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_products(products):
    with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=4, ensure_ascii=False)

def get_image_url_from_quote(quote):
    if not quote or not quote.attach:
        return None
    
    attach_data = None
    if isinstance(quote.attach, str):
        try:
            attach_data = json.loads(quote.attach)
        except json.JSONDecodeError:
            return None
    elif isinstance(quote.attach, dict):
        attach_data = quote.attach
    else:
        return None

    return attach_data.get('hdUrl') or attach_data.get('oriUrl') or attach_data.get('thumb')


def upload_to_catbox_from_url(image_url):
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        file_ext = os.path.splitext(image_url.split('?')[0])[-1] or '.jpg'
        file_name = f"product_thumb{file_ext}"

        files = {'fileToUpload': (file_name, BytesIO(response.content))}
        upload_response = requests.post("https://catbox.moe/user/api.php", files=files, data={"reqtype": "fileupload"}, timeout=5)
        
        if upload_response.status_code == 200:
            return upload_response.text.strip()
        return None
    except Exception as e:
        print(f"❌ Lỗi khi upload ảnh lên Catbox: {e}")
        return None

def handle_product_command(message, message_object, thread_id, thread_type, author_id, client):
    
    args = message.split()
    
    if len(args) < 2:
        client.replyMessage(Message(text=des['description']), message_object, thread_id, thread_type, ttl=120000)
        return

    sub_command = args[1].lower() 
    products = load_products()

    if sub_command == "create":
        if len(args) < 4:
            client.replyMessage(Message(text="⚠️ Sai cú pháp! Vui lòng dùng: product create [tên sản phẩm] [giá]"), message_object, thread_id, thread_type, ttl=120000)
            return
        if not message_object.quote:
            client.replyMessage(Message(text="⚠️ Vui lòng reply vào ảnh để đặt làm ảnh đại diện cho sản phẩm."), message_object, thread_id, thread_type, ttl=120000)
            return

        image_url = get_image_url_from_quote(message_object.quote)
        if not image_url:
            client.replyMessage(Message(text="⚠️ Không tìm thấy ảnh trong tin nhắn được reply."), message_object, thread_id, thread_type, ttl=120000)
            return
        
        client.replyMessage(Message(text="⏳ Đang xử lý và tải ảnh lên, vui lòng chờ..."), message_object, thread_id, thread_type, ttl=120000)
        public_image_url = upload_to_catbox_from_url(image_url)
        if not public_image_url:
            client.replyMessage(Message(text="❌ Lỗi khi tải ảnh sản phẩm. Vui lòng thử lại với ảnh khác."), message_object, thread_id, thread_type, ttl=120000)
            return

        product_name_parts = args[2:-1] 
        product_name = " ".join(product_name_parts)
        product_price = args[-1]
        
        product_id = product_name.lower().replace(" ", "_") + f"_{_util.now()}"

        products[product_name] = {
            "id": product_id,
            "name": product_name,
            "price": product_price,
            "thumbnail_url": public_image_url
        }
        save_products(products)
        client.replyMessage(Message(text=f"✅ Đã tạo thành công sản phẩm: {product_name}"), message_object, thread_id, thread_type, ttl=120000)

    elif sub_command == "send":
        if len(args) < 3:
            client.replyMessage(Message(text="⚠️ Sai cú pháp! Vui lòng dùng: product send [tên sản phẩm]"), message_object, thread_id, thread_type, ttl=120000)
            return
        
        product_name = " ".join(args[2:])
        product_data = products.get(product_name)
        if not product_data:
            client.replyMessage(Message(text=f"❌ Không tìm thấy sản phẩm với tên: {product_name}"), message_object, thread_id, thread_type, ttl=120000)
            return
        
        try:
            client.sendProduct(
                product_id=product_data["id"],
                product_name=product_data["name"],
                product_price=product_data["price"],
                thumbnail_url=product_data["thumbnail_url"],
                thread_id=thread_id,
                thread_type=thread_type
            )
        except Exception as e:
             client.replyMessage(Message(text=f"❌ Lỗi khi gửi sản phẩm: {e}"), message_object, thread_id, thread_type, ttl=120000)

    elif sub_command == "list":
        if not products:
            client.replyMessage(Message(text="📦 Hiện chưa có sản phẩm nào được tạo."), message_oject, thread_id, thread_type, ttl=120000)
            return
        
        product_list_str = "📦 Danh sách sản phẩm hiện có:\n\n"
        for name in products.keys():
            product_list_str += f"- {name}\n"
        
        client.replyMessage(Message(text=product_list_str.strip()), message_object, thread_id, thread_type, ttl=120000)
        
    elif sub_command == "delete":
        if len(args) < 3:
            client.replyMessage(Message(text="⚠️ Sai cú pháp! Vui lòng dùng: product delete [tên sản phẩm]"), message_object, thread_id, thread_type, ttl=120000)
            return
        
        product_name = " ".join(args[2:])
        if product_name in products:
            del products[product_name]
            save_products(products)
            client.replyMessage(Message(text=f"🗑️ Đã xóa thành công sản phẩm: {product_name}"), message_object, thread_id, thread_type, ttl=120000)
        else:
            client.replyMessage(Message(text=f"❌ Không tìm thấy sản phẩm với tên: {product_name}"), message_object, thread_id, thread_type, ttl=120000)
            
    else:
        client.replyMessage(Message(text=f"⚠️ Lệnh không hợp lệ: '{sub_command}'.\n\n" + des['description']), message_object, thread_id, thread_type, ttl=120000)


def PTA():
    return {
        'product': handle_product_command
    }