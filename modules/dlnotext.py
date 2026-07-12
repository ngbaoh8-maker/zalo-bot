from zlapi.models import Message
import requests
import re
import tempfile
import os
import shutil
from core.bot_sys import get_user_name_by_id

class TikTokDownloader:
    def __init__(self):
        self.apis = {
            'tiktok1': 'https://www.tikwm.com/api/?url=',
            'tiktok2': 'https://tikdown.org/api/?url=',
            'tiktok3': 'https://ssstik.io/abc?url=',
        }
        self.headers_list = [
            {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Accept': 'application/json'},
            {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X)', 'Accept': 'application/json'},
            {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)', 'Accept': '*/*'}
        ]
        self.current_header = 0

    def get_headers(self):
        h = self.headers_list[self.current_header]
        self.current_header = (self.current_header + 1) % len(self.headers_list)
        return h

    def make_request(self, url, method='GET', data=None):
        try:
            if method == 'POST':
                r = requests.post(url, headers=self.get_headers(), data=data, timeout=15)
            else:
                r = requests.get(url, headers=self.get_headers(), timeout=15)
            if r.status_code == 200:
                return r
        except:
            pass
        return None

    def detect_platform(self, url):
        if re.search(r"(tiktok\.com|vt\.tiktok\.com)", url, re.IGNORECASE):
            return "tiktok"
        return None

    def fetch_tiktok(self, url):
        try:
            r = self.make_request(self.apis['tiktok1'] + url)
            if r:
                data = r.json()
                p = data.get("data", {})
                if p.get("play"):
                    return {
                        "video_url": p["play"],
                        "duration": int(float(p.get("duration", 60))),
                        "file_type": "video"
                    }
        except:
            pass
        try:
            r = self.make_request(self.apis['tiktok2'] + url)
            if r:
                data = r.json()
                if data.get("video"):
                    return {"video_url": data["video"], "duration": 60, "file_type":"video"}
        except:
            pass
        try:
            r = self.make_request(self.apis['tiktok3'], 'POST', data={'id': url})
            if r:
                m = re.search(r'href="([^"]*\.mp4[^"]*)"', r.text)
                if m:
                    return {"video_url": m.group(1), "duration": 60, "file_type":"video"}
        except:
            pass
        return None

    def download_video(self, url):
        platform = self.detect_platform(url)
        if not platform:
            return None, "❌ Vui lòng gửi link TikTok hợp lệ!"
        v = self.fetch_tiktok(url)
        if v:
            return v, platform
        return None, "❌ Không thể tải TikTok"

downloader = TikTokDownloader()

def handle_dl_command(message, message_object, thread_id, thread_type, author_id, client):
    args = message.strip().split()
    if len(args) < 2:
        client.replyMessage(Message(text="❌ Vui lòng gửi link TikTok!"), message_object, thread_id, thread_type)
        return

    url = args[1]
    platform = downloader.detect_platform(url)
    if not platform:
        client.replyMessage(Message(text="❌ Vui lòng gửi link TikTok hợp lệ!"), message_object, thread_id, thread_type)
        return

    info, res = downloader.download_video(url)
    if not info:
        client.replyMessage(Message(text=res), message_object, thread_id, thread_type)
        return

    # TikTok dạng dọc HD
    w, h = 720, 1280
    try:
        client.sendRemoteVideo(
            videoUrl=info['video_url'],
            thumbnailUrl=None,
            duration=info.get('duration', 60),
            thread_id=thread_id,
            thread_type=thread_type,
            width=w,
            height=h
        )
    except TypeError:
        try:
            client.sendRemoteVideo(
                videoUrl=info['video_url'],
                thumbnailUrl=None,
                duration=info.get('duration', 60),
                thread_id=thread_id,
                thread_type=thread_type,
                width=w,
                height=h
            )
        except:
            client.replyMessage(Message(text="⚠️ Gửi video thất bại. Xem log server."), message_object, thread_id, thread_type)

des = {
    'version': "1.0.5",
    'credits': "ngbao",
    'description': "Tải video TikTok dạng dọc HD, chỉ video không text",
    'power': "Thành viên"
}

def PTA():
    return {
        'dlnotext': handle_dl_command
    }