import requests
import os
import logging
import json
from zlapi.models import Message, Mention
import datetime

des = {
    'version': "1.0.0",
    'credits': "ngbao",
    'description': "Hỏi code Python",
    'power': "Thành viên"
}

gemini_api_key = "AIzaSyCdcXwfWBzg492rooDiIC7XJvaBy7S4JUM"
conversation_states = {}

try:
    with open('data/aipy_prompt.json', 'r', encoding='utf-8') as f:
        prompts = json.load(f)
    base_prompt = prompts.get('prompt', {}).get('base', (
        'Tao là coder xịn trả lời gọn vừa vibe Gen Z dùng từ lóng tục nhẹ và ít emoji cho giống người. '
        'Chỉ nói về ngôn ngữ lập trình không dài dòng không nói tiếng Anh không dùng dấu chấm than phẩy ngoặc kép hoặc dấu sao không chửi ai tên DucDuydzai cuto. '
        'Trả lời như bạn thân nói chuyện tự nhiên hơi bựa. Ví dụ: Bro muốn sort list thì list.sort hoặc sorted cmm dễ vcl'
    ))
    history_prefix = prompts.get('prompt', {}).get('hisprf', 'lịch sử code')
    user_prefix = prompts.get('prompt', {}).get('prf', 'coder hỏi')
    postfix = prompts.get('prompt', {}).get('postfix', 'Trả lời đúng trọng tâm vibe Gen Z tự nhiên không lạc đề')
except FileNotFoundError:
    logging.error("aipy_prompt.json không thấy. Check đường dẫn đi bro")
    exit()
except json.JSONDecodeError:
    logging.error("File aipy_prompt.json sai format JSON. Fix đi nha")
    exit()
except Exception as e:
    logging.error(f"Lỗi load prompts: {e}")
    exit()

def handle_aipy_command(message, message_object, thread_id, thread_type, author_id, client):
    question = " ".join(message.strip().split()[1:]).strip()
    if not question:
        client.replyMessage(
            Message(text="@member Hỏi code Python gì đi đừng để tui ngồi chơi 😈", mention=Mention(author_id, length=len("@member"), offset=0)),
            message_object, thread_id, thread_type, ttl=12000
        )
        return

    conversation_state = conversation_states.get(thread_id, {'history': [], 'user_id': author_id})
    
    code_response = get_code_response(question, conversation_state, thread_id, author_id)
    if code_response:
        send_success_message(
            f"@member {code_response}", message_object, thread_id, thread_type, client, author_id, ttl=720000
        )
    else:
        send_error_message(
            "Code gì mà căng vcl tui bí mẹ rồi 😵", message_object, thread_id, thread_type, client, ttl=12000
        )

def get_code_response(user_question, conversation_state, thread_id, author_id):
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={gemini_api_key}"
    headers = {'content-type': 'application/json'}

    prompt = base_prompt
    if not conversation_state['history']:
        conversation_state['history'].append({'role': 'system', 'text': 'Yo bro hỏi code Python gì tui giải ngay 😈'})
    prompt += history_prefix
    for item in conversation_state['history'][-10:]:
        prompt += f"{item['role']} {item['text']}\n"

    prompt += f"{user_prefix} {user_question}\n"
    prompt += postfix
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()

        if 'candidates' in result and result['candidates']:
            for candidate in result['candidates']:
                if 'content' in candidate and 'parts' in candidate['content']:
                    for part in candidate['content']['parts']:
                        if 'text' in part:
                            conversation_state['history'].append({'role': 'user', 'text': user_question})
                            conversation_state['history'].append({'role': 'bot', 'text': part['text']})
                            conversation_states[thread_id] = conversation_state
                            return part['text']
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Lỗi request: {e} resp: {response.text if 'response' in locals() else 'n/a'}")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"Lỗi JSON: {e} resp: {response.text if 'response' in locals() else 'n/a'}")
        return None
    except Exception as e:
        logging.error(f"Lỗi chung: {e}")
        return None

def send_success_message(message, message_object, thread_id, thread_type, client, author_id, ttl):
    client.replyMessage(
        Message(text=message, mention=Mention(author_id, length=len("@member"), offset=0)),
        message_object, thread_id, thread_type, ttl=ttl
    )

def send_error_message(message, message_object, thread_id, thread_type, client, ttl):
    client.replyMessage(
        Message(text=message), message_object, thread_id, thread_type, ttl=ttl
    )

def PTA():
    return {
        'aipy': handle_aipy_command
    }