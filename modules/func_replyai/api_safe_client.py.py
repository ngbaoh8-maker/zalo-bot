# -*- coding: utf-8 -*-
# api_safe_client.py — lớp bọc an toàn cho Zalo API
# Dùng để tránh lỗi "Không thể gửi danh thiếp (API lỗi)" trong pro_replyai.py

import logging
from zlapi.models import ThreadType, Message

logger = logging.getLogger("SafeClient")

class SafeClient:
    def __init__(self, client):
        """
        Bọc đối tượng client gốc của zlapi để xử lý lỗi API an toàn.
        """
        self.client = client

    # ===========================================
    # === GỬI DANH THIẾP AN TOÀN (CÓ FALLBACK) ===
    # ===========================================
    def sendBusinessCardSafe(self, user_id, thread_id, thread_type, phone="Liên hệ chủ bot"):
        """
        Gửi danh thiếp thật nếu API hoạt động.
        Nếu API lỗi hoặc bị chặn, tự động gửi fallback link Zalo.
        """
        try:
            qr_url = None

            # --- Thử lấy QR user ---
            try:
                qr_data = self.client.getQrUser(user_id, thread_type=ThreadType.USER)
                qr_url = qr_data.get(str(user_id), "") if qr_data else None
                logger.info(f"[SafeClient] QR URL: {qr_url}")
            except Exception as e:
                logger.warning(f"[SafeClient] Lỗi khi gọi getQrUser: {e}")

            # --- Thử gửi danh thiếp thật ---
            if qr_url:
                try:
                    self.client.sendBusinessCard(
                        userId=user_id,
                        qrCodeUrl=qr_url,
                        thread_id=thread_id,
                        thread_type=thread_type,
                        phone=phone,
                        ttl=300000
                    )
                    logger.info(f"✅ Gửi danh thiếp thật thành công cho {user_id}")
                    return True
                except Exception as e:
                    logger.warning(f"[SafeClient] API chặn sendBusinessCard: {e}")

            # --- Fallback: gửi link thông tin ---
            info_text = (
                f"📇 Thông tin chủ bot:\n"
                f"👤 卍 Bii Lov Yae Miko 卍\n"
                f"🆔 {user_id}\n"
                f"📞 {phone}\n"
                f"🔗 Liên hệ trực tiếp: https://zalo.me/{user_id}\n"
                f"⚠️ API Zalo chặn gửi danh thiếp, gửi link thay thế."
            )
            self.client.sendMessage(Message(text=info_text), thread_id, thread_type)
            logger.info(f"[SafeClient] Fallback gửi link QR thành công cho {user_id}")
            return False

        except Exception as e:
            logger.error(f"[SafeClient] Lỗi nghiêm trọng khi gửi danh thiếp: {e}")
            try:
                self.client.sendMessage(
                    Message(text="⚠️ Không thể gửi danh thiếp (API lỗi hoặc bị chặn)."),
                    thread_id, thread_type
                )
            except:
                pass
            return False
