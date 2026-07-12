import requests
import os
import logging
import json
from zlapi.models import Message, Mention
import datetime

des = {
    'version': "1.0.0",
    'credits': "ngbao",
    'description': "War cùng AI =))=))",
    'power': "Thành viên"
}

gemini_api_key = "AIzaSyCdcXwfWBzg492rooDiIC7XJvaBy7S4JUM"
conversation_states = {}

try:
    with open('data/promt.json', 'r', encoding='utf-8') as f:
        prompts = json.load(f)
    base_prompt = prompts.get('promt', {}).get('base', 'tao là Tên Hoàng Anh Tuấn, trả lời ngắn gọn không quá 100 từ.')
    history_prefix = prompts.get('promt', {}).get('hisprf', 'lịch sử:')
    user_prefix = prompts.get('promt', {}).get('prf', 'user:')
    postfix = prompts.get('promt', {}).get('postfix', 'trả lời toàn bộ và không chửi ai tên "Quân"!')
except FileNotFoundError:
    logging.error("promt.json không thấy. check lại đường dẫn.")
    exit()
except json.JSONDecodeError:
    logging.error("file promt.json sai format json check lại nội dung file đi.")
    exit()
except Exception as e:
    logging.error(f"lỗi load prompts: {e}")
    exit()

def handle_chat_command(message, message_object, thread_id, thread_type, author_id, client):
    question = " ".join(message.strip().split()[1:]).strip()
    if not question:
        client.replyMessage(
            Message(text="@member sủa?", mention=Mention(author_id, length=len("@member"), offset=0)),
            message_object, thread_id, thread_type, ttl=12000
        )
        return

    conversation_state = conversation_states.get(thread_id, {'history': [], 'user_id': author_id})
    
    chat_response = get_chat_response(question, conversation_state, thread_id, author_id)
    if chat_response:
        send_success_message(
            f"@member {chat_response}", message_object, thread_id, thread_type, client, author_id, ttl=720000
        )
    else:
        send_error_message(
            "đ muốn rep", message_object, thread_id, thread_type, client, ttl=12000
        )

def get_chat_response(user_question, conversation_state, thread_id, author_id):
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_api_key}"
    headers = {'content-type': 'application/json'}

    prompt = base_prompt
    if not conversation_state['history']:
        conversation_state['history'].append({'role': 'system', 'text': 'người dùng mn nha'})
    prompt += history_prefix
    for item in conversation_state['history'][-10:]:
         prompt += f"{item['role']}: {item['text']}\n"

    prompt += f"{user_prefix}{user_question}\n"
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
        logging.error(f"lỗi request: {e}, resp: {response.text if 'response' in locals() else 'n/a'}")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"lỗi json: {e}, resp: {response.text if 'response' in locals() else 'n/a'}")
        return None
    except Exception as e:
        logging.error(f"lỗi chung: {e}")
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
        'chat': handle_chat_command
    }