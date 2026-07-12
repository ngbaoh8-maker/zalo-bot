import requests
import re
import yt_dlp
import tempfile
import os
from zlapi.models import Message
des = {
    'version': "1.2.0",
    'credits': "ngbao",
    'description': "download video từ link",
    'power': "all"
}

class SocialMediaDownloader:
    def __init__(self):
        # Mở rộng hỗ trợ thêm Facebook
        self.apis = {
            'tiktok1': 'https://www.tikwm.com/api/?url=',
            'tiktok2': 'https://tikdown.org/api/?url=',
            'tiktok3': 'https://ssstik.io/abc?url=',
        }
        
        # Uguu.se upload API
        self.uguu_api = 'https://uguu.se/upload'
        
        # Headers đa dạng để tránh block
        self.headers_list = [
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.google.com/',
            },
            {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                'Accept': '*/*',
                'X-Requested-With': 'XMLHttpRequest',
            }
        ]
        
        self.current_header = 0
        
        # Cấu hình yt-dlp chung cho YouTube và Facebook
        self.ydl_opts = {
            'format': 'best[height<=480][ext=mp4]/best[ext=mp4]/best',  # Ưu tiên mp4
            'noplaylist': True,
            'no_warnings': True,
            'quiet': True,
            'extractaudio': False,
            'outtmpl': '%(title)s.%(ext)s',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Cấu hình riêng cho Facebook - Tối ưu 480p
        self.facebook_opts = {
            # Format 480p cố định cho Facebook
            'format': (
                'best[height=480][ext=mp4]/best[height<=480][ext=mp4]/'
                'worst[height=480][ext=mp4]/worst[height<=480][ext=mp4]/'
                'best[height<=720][ext=mp4]/worst[ext=mp4]/worst'
            ),
            'noplaylist': True,
            'no_warnings': True,
            'quiet': True,
            'extractaudio': False,
            'outtmpl': '%(title)s.%(ext)s',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            # Giới hạn file size (50MB)
            'max_filesize': 50 * 1024 * 1024,  # 50MB
            # Postprocessors để nén video thêm nếu cần
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }, {
                'key': 'FFmpegMetadata',
            }],
            # Cookiefile để tránh bị block
            'cookiefile': None,
        }
        
        # Cấu hình riêng cho YouTube - Chỉ tải MP3
        self.youtube_opts = {
            'format': 'bestaudio/best',  # Chỉ tải audio
            'noplaylist': True,
            'no_warnings': True,
            'quiet': True,
            'extractaudio': True,  # Bật extract audio
            'audioformat': 'mp3',  # Format MP3
            'audioquality': '192',  # Chất lượng 192kbps
            'outtmpl': '%(title)s.%(ext)s',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }, {
                'key': 'FFmpegMetadata',
            }],
        }

    def detect_platform(self, url):
        """Phát hiện nền tảng từ URL - bao gồm TikTok, YouTube và Facebook"""
        patterns = {
            'tiktok': r'(tiktok\.com|vt\.tiktok\.com)',
            'youtube': r'(youtube\.com|youtu\.be)',
            'facebook': r'(facebook\.com|fb\.watch|fb\.com)',
        }
        
        for platform, pattern in patterns.items():
            if re.search(pattern, url, re.IGNORECASE):
                return platform
        return None

    def get_headers(self):
        """Rotate headers để tránh bị block"""
        headers = self.headers_list[self.current_header]
        self.current_header = (self.current_header + 1) % len(self.headers_list)
        return headers

    def make_request(self, url, method='GET', data=None, json_data=None, retries=3):
        """Request với retry và multiple headers"""
        for attempt in range(retries):
            try:
                headers = self.get_headers()
                
                if method == 'POST':
                    if json_data:
                        response = requests.post(url, headers=headers, json=json_data, timeout=15)
                    else:
                        response = requests.post(url, headers=headers, data=data, timeout=15)
                else:
                    response = requests.get(url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # Rate limited
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    print(f"HTTP {response.status_code} on attempt {attempt + 1}")
                    
            except Exception as e:
                print(f"Request attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    import time
                    time.sleep(1)
                    
        return None

    def fetch_tiktok_video(self, url):
        """Tải video TikTok với multiple APIs"""
        # API 1: TikWM (ổn định nhất)
        try:
            api_url = f"{self.apis['tiktok1']}{url}"
            response = self.make_request(api_url)
            if response:
                data = response.json()
                if data.get("data", {}).get("play"):
                    return {
                        "video_url": data["data"]["play"],
                        "duration": int(float(data["data"].get("duration", 100))),  # Chuyển về int
                        "title": data["data"].get("title", "TikTok Video"),
                        "author": data["data"].get("author", {}).get("nickname", "Unknown")
                    }
        except Exception as e:
            print(f"[TikTok API 1] Error: {e}")

        # API 2: TikDown backup
        try:
            api_url = f"{self.apis['tiktok2']}{url}"
            response = self.make_request(api_url)
            if response:
                data = response.json()
                if data.get("video"):
                    return {
                        "video_url": data["video"],
                        "duration": 100,  # Trực tiếp int
                        "title": data.get("title", "TikTok Video"),
                        "author": data.get("author", "Unknown")
                    }
        except Exception as e:
            print(f"[TikTok API 2] Error: {e}")

        # API 3: SSSTik backup
        try:
            response = self.make_request(self.apis['tiktok3'], 'POST', data={'id': url})
            if response:
                # Parse HTML response for download link
                content = response.text
                video_match = re.search(r'href="([^"]*\.mp4[^"]*)"', content)
                if video_match:
                    return {
                        "video_url": video_match.group(1),
                        "duration": 100,  # Trực tiếp int
                        "title": "TikTok Video",
                        "author": "Unknown"
                    }
        except Exception as e:
            print(f"[TikTok API 3] Error: {e}")

        return None
    
    def compress_video_if_needed(self, file_path, max_size_mb=30):
        """Nén video nếu quá lớn bằng FFmpeg"""
        try:
            import subprocess
            
            # Kiểm tra kích thước file
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            
            if file_size <= max_size_mb:
                return file_path  # Không cần nén
            
            print(f"📦 Video {file_size:.1f}MB, đang nén xuống dưới {max_size_mb}MB...")
            
            # Tạo file output
            compressed_path = file_path.replace('.mp4', '_compressed.mp4')
            
            # Lệnh FFmpeg để nén
            ffmpeg_cmd = [
                'ffmpeg', '-i', file_path,
                '-c:v', 'libx264',  # Video codec
                '-crf', '28',       # Chất lượng (18-28, cao hơn = nhỏ hơn)
                '-preset', 'fast',   # Preset nén
                '-c:a', 'aac',      # Audio codec
                '-b:a', '64k',      # Bitrate audio thấp
                '-movflags', '+faststart',  # Tối ưu streaming
                '-y',               # Overwrite
                compressed_path
            ]
            
            # Chạy FFmpeg
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0 and os.path.exists(compressed_path):
                # Kiểm tra file đã nhỏ hơn chưa
                new_size = os.path.getsize(compressed_path) / (1024 * 1024)
                if new_size < file_size:
                    print(f"✅ Nén thành công: {file_size:.1f}MB → {new_size:.1f}MB")
                    # Xóa file gốc
                    try:
                        os.remove(file_path)
                    except:
                        pass
                    return compressed_path
            
            # Nếu nén thất bại, dùng file gốc
            return file_path
            
        except Exception as e:
            print(f"[Compress] Lỗi nén video: {e}")
            return file_path  # Dùng file gốc nếu lỗi
        """Upload video lên uguu.se"""
        try:
            with open(file_path, 'rb') as f:
                files = {'files[]': f}
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                
                response = requests.post(self.uguu_api, files=files, headers=headers, timeout=300)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success') and len(data.get('files', [])) > 0:
                        return data['files'][0]['url']
                        
        except Exception as e:
            print(f"[Uguu Upload] Error: {e}")
            
        return None

    def download_with_ytdlp(self, url, temp_dir, platform='youtube'):
        """Tải video bằng yt-dlp cho YouTube và Facebook"""
        try:
            # Chọn cấu hình phù hợp
            if platform == 'facebook':
                opts = self.facebook_opts.copy()
            else:
                opts = self.ydl_opts.copy()
                
            # Cấu hình để save vào thư mục tạm
            opts['outtmpl'] = os.path.join(temp_dir, '%(title)s.%(ext)s')
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                # Lấy thông tin và download
                info = ydl.extract_info(url, download=True)
                
                if info:
                    # Tìm file đã download
                    title = info.get('title', 'video')
                    ext = info.get('ext', 'mp4')
                    
                    # Clean filename
                    safe_title = re.sub(r'[^\w\s-]', '', title).strip()[:50]
                    expected_filename = f"{safe_title}.{ext}"
                    file_path = os.path.join(temp_dir, expected_filename)
                    
                    # Tìm file thực tế (yt-dlp có thể thay đổi tên)
                    actual_file = None
                    for file in os.listdir(temp_dir):
                        if file.endswith(('.mp4', '.webm', '.mkv', '.mov')):
                            actual_file = os.path.join(temp_dir, file)
                            break
                    
                    if actual_file and os.path.exists(actual_file):
                        return {
                            "file_path": actual_file,
                            "duration": int(float(info.get('duration', 180))),  # Chuyển về int
                            "title": info.get('title', f'{platform.title()} Video'),
                            "author": info.get('uploader', 'Unknown')
                        }
                        
        except Exception as e:
            print(f"[{platform.title()} Download] Error: {e}")
            
        return None

    def download_facebook_video(self, url, temp_dir):
        """Tải video Facebook với tối ưu dung lượng nhỏ"""
        try:
            opts = self.facebook_opts.copy()
            opts['outtmpl'] = os.path.join(temp_dir, '%(title)s.%(ext)s')
            
            print("🔍 Đang phân tích video Facebook...")
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                # Lấy thông tin trước khi download
                info = ydl.extract_info(url, download=False)
                
                if info:
                    # Kiểm tra duration - từ chối video quá dài
                    duration = info.get('duration', 0)
                    if duration > 300:  # 5 phút
                        print(f"⚠️ Video dài {duration}s, chỉ hỗ trợ video dưới 5 phút")
                        return None
                    
                    # Kiểm tra filesize estimate
                    filesize = info.get('filesize') or info.get('filesize_approx', 0)
                    if filesize and filesize > 80 * 1024 * 1024:  # 80MB
                        print(f"⚠️ Video ước tính {filesize/1024/1024:.1f}MB, quá lớn")
                        return None
                    
                    print("📥 Bắt đầu tải video Facebook...")
                    
                    # Download với format tối ưu
                    info = ydl.extract_info(url, download=True)
                    
                    if info:
                        # Tìm file đã download
                        title = info.get('title', 'facebook_video')
                        ext = info.get('ext', 'mp4')
                        
                        # Clean filename
                        safe_title = re.sub(r'[^\w\s-]', '', title).strip()[:30]  # Ngắn hơn
                        
                        # Tìm file thực tế
                        actual_file = None
                        for file in os.listdir(temp_dir):
                            if file.endswith(('.mp4', '.webm', '.mkv', '.mov')):
                                actual_file = os.path.join(temp_dir, file)
                                break
                        
                        if actual_file and os.path.exists(actual_file):
                            # Nén video nếu cần (chỉ cho video 480p)
                            compressed_file = self.compress_video_if_needed(actual_file, max_size_mb=40)
                            
                            return {
                                "file_path": compressed_file,
                                "duration": int(float(info.get('duration', 180))),  # Chuyển về int
                                "title": info.get('title', 'Facebook Video'),
                                "author": info.get('uploader', 'Facebook User')
                            }
                            
        except Exception as e:
            print(f"[Facebook Download] Error: {e}")
            
        return None

    def download_youtube_audio(self, url, temp_dir):
        """Tải audio MP3 từ YouTube"""
        try:
            opts = self.youtube_opts.copy()
            opts['outtmpl'] = os.path.join(temp_dir, '%(title)s.%(ext)s')
            
            print("🎵 Đang tải audio MP3 từ YouTube...")
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                # Lấy thông tin và download
                info = ydl.extract_info(url, download=True)
                
                if info:
                    # Tìm file MP3 đã download
                    title = info.get('title', 'youtube_audio')
                    
                    # Clean filename
                    safe_title = re.sub(r'[^\w\s-]', '', title).strip()[:40]
                    
                    # Tìm file MP3 thực tế
                    actual_file = None
                    for file in os.listdir(temp_dir):
                        if file.endswith('.mp3'):
                            actual_file = os.path.join(temp_dir, file)
                            break
                    
                    if actual_file and os.path.exists(actual_file):
                        return {
                            "file_path": actual_file,
                            "duration": int(float(info.get('duration', 180))),
                            "title": info.get('title', 'YouTube Audio'),
                            "author": info.get('uploader', 'Unknown'),
                            "file_type": "audio"  # Đánh dấu là audio
                        }
                        
        except Exception as e:
            print(f"[YouTube Audio Download] Error: {e}")
            
        return None

    def download_video(self, url):
        """Tải video từ TikTok, YouTube hoặc Facebook"""
        platform = self.detect_platform(url)
        if not platform:
            return None, "❌ Chỉ hỗ trợ TikTok, YouTube và Facebook"

        if platform == 'tiktok':
            result = self.fetch_tiktok_video(url)
            if result:
                return result, platform
            else:
                return None, "❌ Không thể tải từ TikTok"
                
        elif platform in ['youtube', 'facebook']:
            # Tạo thư mục tạm
            temp_dir = tempfile.mkdtemp()
            
            try:
                if platform == 'youtube':
                    result = self.download_youtube_audio(url, temp_dir)  # Tải MP3
                else:  # facebook
                    result = self.download_facebook_video(url, temp_dir)  # Tải video 480p
                    
                if result:
                    # Upload lên uguu.se
                    print(f"📤 Đang upload video {platform} lên Uguu.se...")
                    uguu_url = self.upload_to_uguu(result['file_path'])
                    
                    if uguu_url:
                        result['video_url'] = uguu_url
                        result['uploaded'] = True
                        return result, platform
                    else:
                        return None, f"❌ Không thể upload video {platform} lên Uguu.se"
                else:
                    return None, f"❌ Không thể tải từ {platform.title()}"
                    
            finally:
                # Cleanup temp files
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except:
                    pass
        
        return None, f"❌ {platform.title()} chưa được hỗ trợ"

def get_user_name_by_id(client, user_id):
    """Lấy tên người dùng theo ID"""
    try:
        user_info = client.getUserInfo(user_id)
        if user_info and isinstance(user_info, dict):
            return user_info.get('displayName', 'Người dùng')
        elif hasattr(user_info, 'displayName'):
            return user_info.displayName
        return 'Người dùng'
    except Exception as e:
        print(f"[get_user_name_by_id] Error: {e}")
        return 'Người dùng'

# Khởi tạo downloader
downloader = SocialMediaDownloader()

def handle_dl_command(message, message_object, thread_id, thread_type, author_id, client):
    """
    Hàm xử lý lệnh download TikTok, YouTube và Facebook
    Sử dụng: {prefix}dl [link]
    """
    try:
        args = message.strip().split()
        
        if len(args) < 2:
            help_text = """
• TikTok - Video HD
• YouTube - Audio MP3 
• Facebook - Video 480p 

🤖 Dịch Vụ Tải Video/Audio, Vui Lòng Điền Link Sau Lệnh dl👉"""
            
            client.replyMessage(
                Message(text=help_text),
                message_object,
                thread_id,
                thread_type
            )
            return

        video_url = args[1]
        
        # Phát hiện nền tảng
        platform = downloader.detect_platform(video_url)
        if not platform:
            client.replyMessage(
                Message(text="🤖Vcl, Mày Đùa Tao À, Đó Có Phải Link Video Đâu Thằng Đần Này!\n\n📱 Tao Hỗ Trợ: TikTok, YouTube và Facebook"),
                message_object,
                thread_id,
                thread_type
            )
            return

        # Emoji cho từng nền tảng
        platform_emojis = {
            'tiktok': '🎵',
            'youtube': '🎧',  # Audio icon
            'facebook': '📹'  # Video icon
        }
        
        emoji = platform_emojis.get(platform, '📱')
        
        # Thông báo đặc biệt cho từng platform
        if platform == 'facebook':
            loading_msg = f"{emoji} Đang tải Facebook Video 480p... ⏳"
        elif platform == 'youtube':
            loading_msg = f"{emoji} Đang tải YouTube Audio MP3... ⏳"
        else:
            loading_msg = f"{emoji} Đang tải từ {platform.title()}... Đợi mình xíu nhé! ⏳"
            
        client.replyMessage(
            Message(text=loading_msg),
            message_object,
            thread_id,
            thread_type
        )

        # Tải video
        info, result_platform = downloader.download_video(video_url)
        
        if not info:
            error_messages = {
                'tiktok': "❌ Tao Đéo Tải Được,Mày Xem Lại Link Coi Đúng Chưa.",
                'youtube': "❌️ Cút Ra Ngoài, Lấy Link Khác Hộ Tao!",
                'facebook': "❌ Xem Lại Link Giúp Tao, Thằng Đần Này."
            }
            
            error_msg = error_messages.get(platform, result_platform)
            client.replyMessage(
                Message(text=error_msg),
                message_object,
                thread_id,
                thread_type
            )
            return

        # Gửi file theo loại (video/audio)
        try:
            user_name = get_user_name_by_id(client, author_id)
            
            # Tạo caption cho từng nền tảng
            platform_names = {
                'tiktok': 'TikTok',
                'youtube': 'YouTube', 
                'facebook': 'Facebook'
            }
            
            platform_name = platform_names.get(platform, platform.title())
            
            caption = f"{platform_name} Của {user_name} Nè, Nghe/Xem Liền Cho Nóng🔥"
            
            # Kiểm tra loại file để gửi
            file_type = info.get('file_type', 'video')
            
            if file_type == 'audio':
                # Gửi file audio MP3
                client.sendRemoteFile(
                    info["video_url"],
                    message=Message(text=caption),
                    thread_id=thread_id,
                    thread_type=thread_type,
                    filename=f"{info.get('title', 'audio')[:30]}.mp3"
                )
            else:
                # Gửi video như cũ
                video_dimensions = {
                    'tiktok': (1080, 1920),    # Portrait
                    'facebook': (854, 480)     # 480p landscape
                }
                
                width, height = video_dimensions.get(platform, (854, 480))
                
                client.sendRemoteVideo(
                    info["video_url"],
                    None,  # Không thumbnail
                    duration=info.get("duration", 60),  # Đã là int
                    message=Message(text=caption),
                    thread_id=thread_id,
                    thread_type=thread_type,
                    width=width,
                    height=height
                )
                
        except Exception as e:
            print(f"[Send Video Error] {e}")
            client.sendMessage(
                Message(text=f"⚠️ Lỗi khi gửi video: {str(e)}\n\n💡 Thử lại hoặc kiểm tra link khác."),
                thread_id,
                thread_type
            )
            
    except Exception as e:
        print(f"[DL Command Error] {e}")
        try:
            client.sendMessage(
                Message(text="❌ Có lỗi xảy ra khi xử lý lệnh. Vui lòng thử lại!"),
                thread_id,
                thread_type
            )
        except:
            pass
            
def PTA():
    return {
        'dl': handle_dl_command
    }
