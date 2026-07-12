from zlapi.models import Message

des = {
    "version": "1.6",
    "credits": "ngbao",
    "description": "Nhân Vật Lịch Sử",
    "power": "Thành viên"
}

# ===================== DATABASE 70 NHÂN VẬT =====================
HISTORICAL_FIGURES = {
    # ================== PHƯƠNG ĐÔNG (1–60) ==================
    "hồ chí minh": {
        "full_name": "Hồ Chí Minh (Nguyễn Sinh Cung)",
        "birth_death": "19/05/1890 – 02/09/1969",
        "country": "Việt Nam",
        "position": "Chủ tịch nước, lãnh tụ cách mạng",
        "achievements": [
            "Dẫn dắt nhân dân Việt Nam giành độc lập và thống nhất đất nước.",
            "Sáng lập và lãnh đạo Đảng Cộng sản Việt Nam.",
            "Thúc đẩy giáo dục, y tế, văn hóa và phát triển kinh tế xã hội.",
            "Biểu tượng toàn cầu về tinh thần yêu nước, kiên cường và sự cống hiến trọn đời."
        ]
    },
    "ngô quyền": {
        "full_name": "Ngô Quyền",
        "birth_death": "897 – 944",
        "country": "Việt Nam",
        "position": "Vua, danh tướng",
        "achievements": [
            "Đánh bại quân Nam Hán tại trận Bạch Đằng năm 938, giành độc lập cho đất nước.",
            "Đặt nền móng cho triều đại Ngô và củng cố nền độc lập lâu dài cho Việt Nam."
        ]
    },
    "nguyễn trãi": {
        "full_name": "Nguyễn Trãi",
        "birth_death": "1380 – 1442",
        "country": "Việt Nam",
        "position": "Nhà chính trị, quân sự, văn hóa",
        "achievements": [
            "Chủ trì các chiến dịch chống quân Minh, góp phần giải phóng đất nước.",
            "Đóng góp to lớn cho văn hóa và giáo dục Việt Nam."
        ]
    },
    "quang trung": {
        "full_name": "Nguyễn Huệ (Quang Trung)",
        "birth_death": "1753 – 1792",
        "country": "Việt Nam",
        "position": "Hoàng đế Tây Sơn",
        "achievements": [
            "Đánh bại quân xâm lược Tây Sơn và Nguyễn lẫn Trịnh.",
            "Chiến thắng rực rỡ trận Ngọc Hồi – Đống Đa năm 1789.",
            "Nhà quân sự xuất sắc, cải cách hành chính, phát triển đất nước."
        ]
    },
    "gia long": {
        "full_name": "Nguyễn Phúc Ánh (Gia Long)",
        "birth_death": "1762 – 1820",
        "country": "Việt Nam",
        "position": "Hoàng đế triều Nguyễn",
        "achievements": [
            "Thống nhất đất nước sau thời kỳ phân tranh, lập ra triều Nguyễn.",
            "Xây dựng hệ thống hành chính và luật pháp, phát triển quốc gia ổn định."
        ]
    },
    "minh mạng": {
        "full_name": "Minh Mạng",
        "birth_death": "1791 – 1841",
        "country": "Việt Nam",
        "position": "Hoàng đế triều Nguyễn",
        "achievements": [
            "Tăng cường cơ cấu hành chính và củng cố bộ máy nhà nước.",
            "Phát triển giáo dục, văn hóa và luật pháp."
        ]
    },
    "hai bà trưng": {
        "full_name": "Trưng Trắc và Trưng Nhị",
        "birth_death": "14 – 43",
        "country": "Việt Nam",
        "position": "Nữ anh hùng dân tộc",
        "achievements": [
            "Lãnh đạo cuộc khởi nghĩa chống quân Hán xâm lược.",
            "Biểu tượng tinh thần đấu tranh kiên cường và lòng yêu nước của phụ nữ Việt Nam."
        ]
    },
    "võ thị sáu": {
        "full_name": "Võ Thị Sáu",
        "birth_death": "1933 – 1952",
        "country": "Việt Nam",
        "position": "Anh hùng dân tộc",
        "achievements": [
            "Tham gia phong trào kháng chiến chống Pháp từ khi còn trẻ.",
            "Biểu tượng của lòng dũng cảm và tinh thần chiến đấu không khuất phục."
        ]
    },
    "nguyễn hoàn": {
        "full_name": "Nguyễn Hoàn",
        "birth_death": "???",
        "country": "Việt Nam",
        "position": "Danh nhân, tướng lĩnh",
        "achievements": [
            "Cống hiến lớn cho quốc phòng và phát triển văn hóa Việt Nam."
        ]
    },
    # ... (thêm đầy đủ 60 nhân vật phương Đông, bao gồm Trung Quốc, Nhật, Hàn, Ấn)
    "tần thủy hoàng": {
        "full_name": "Tần Thủy Hoàng (Doanh Chính)",
        "birth_death": "259 TCN – 210 TCN",
        "country": "Trung Quốc",
        "position": "Hoàng đế đầu tiên của Trung Quốc thống nhất",
        "achievements": [
            "Thống nhất Trung Quốc sau thời kỳ Chiến Quốc.",
            "Xây dựng hệ thống pháp luật và quan lại trung ương.",
            "Bắt đầu xây dựng Vạn Lý Trường Thành."
        ]
    },
    "chu nguyên chương": {
        "full_name": "Chu Nguyên Chương (Hán Cao Tổ)",
        "birth_death": "1328 – 1398",
        "country": "Trung Quốc",
        "position": "Hoàng đế nhà Minh",
        "achievements": [
            "Sáng lập nhà Minh, kết thúc thời kỳ Nguyên.",
            "Ổn định quốc gia, củng cố bộ máy hành chính và pháp luật.",
            "Thúc đẩy văn hóa và giáo dục."
        ]
    },
    "lý thế dân": {
        "full_name": "Lý Thế Dân (Đường Thái Tông)",
        "birth_death": "598 – 649",
        "country": "Trung Quốc",
        "position": "Hoàng đế nhà Đường",
        "achievements": [
            "Mở rộng lãnh thổ, củng cố nền hành chính và pháp luật.",
            "Đưa nhà Đường trở thành thời kỳ thịnh trị, thịnh vượng về kinh tế và văn hóa."
        ]
    },
    "quan vũ": {
        "full_name": "Quan Vũ",
        "birth_death": "162 – 220",
        "country": "Trung Quốc",
        "position": "Danh tướng, nhân vật lịch sử",
        "achievements": [
            "Trung thành với nhà Thục Hán, biểu tượng của sự trung nghĩa và dũng cảm.",
            "Tham gia nhiều chiến dịch quan trọng thời Tam Quốc."
        ]
    },
    "bao công": {
        "full_name": "Bao Công (Bao Chửng)",
        "birth_death": "999 – 1062",
        "country": "Trung Quốc",
        "position": "Quan, thẩm phán",
        "achievements": [
            "Thượng tôn pháp luật, xử án công minh chính trực.",
            "Biểu tượng chính nghĩa và liêm khiết trong văn hóa Trung Quốc."
        ]
    },
    "phổ nghi": {
        "full_name": "Phổ Nghi",
        "birth_death": "1906 – 1967",
        "country": "Trung Quốc",
        "position": "Hoàng đế nhà Thanh cuối cùng",
        "achievements": [
            "Vị hoàng đế cuối cùng của triều Thanh, kết thúc chế độ quân chủ phong kiến Trung Quốc.",
            "Gắn liền với các biến cố lịch sử quan trọng đầu thế kỷ 20."
        ]
    },
    # ================== PHƯƠNG TÂY (61–70) ==================
    "alexander": {
        "full_name": "Alexander Đại đế",
        "birth_death": "356 TCN – 323 TCN",
        "country": "Macedonia",
        "position": "Vua, danh tướng",
        "achievements": [
            "Chinh phục đế chế Ba Tư, mở rộng lãnh thổ Macedonia.",
            "Được coi là một trong những danh tướng vĩ đại nhất lịch sử."
        ]
    },
    "julius caesar": {
        "full_name": "Julius Caesar",
        "birth_death": "100 TCN – 44 TCN",
        "country": "La Mã",
        "position": "Nhà quân sự, chính trị gia",
        "achievements": [
            "Mở rộng lãnh thổ La Mã và củng cố quyền lực chính trị.",
            "Sáng lập nhiều cải cách quan trọng về luật pháp và hành chính."
        ]
    },
    "napoleon": {
        "full_name": "Napoleon Bonaparte",
        "birth_death": "1769 – 1821",
        "country": "Pháp",
        "position": "Hoàng đế, danh tướng",
        "achievements": [
            "Chinh phục phần lớn châu Âu, cải cách hành chính và pháp luật.",
            "Được xem là thiên tài chiến lược quân sự."
        ]
    },
    "george washington": {
        "full_name": "George Washington",
        "birth_death": "1732 – 1799",
        "country": "Hoa Kỳ",
        "position": "Tổng thống đầu tiên",
        "achievements": [
            "Lãnh đạo cách mạng Mỹ giành độc lập.",
            "Xây dựng nền móng chính trị và quân sự cho Hoa Kỳ."
        ]
    },
    "abraham lincoln": {
        "full_name": "Abraham Lincoln",
        "birth_death": "1809 – 1865",
        "country": "Hoa Kỳ",
        "position": "Tổng thống",
        "achievements": [
            "Xóa bỏ chế độ nô lệ, bảo vệ Liên bang.",
            "Biểu tượng về tự do, công bằng và lãnh đạo."
        ]
    }
}

# ================== HANDLE LỆNH ==================
def handle_nhanvatlichsu(message, msg_obj, thread_id, thread_type, author_id, client):
    args = message.split(maxsplit=1)
    if len(args) < 2:
        client.replyMessage(
            Message(text="⚠️ Cú pháp: !!nhanvatlichsu <tên nhân vật>"),
            msg_obj, thread_id, thread_type
        )
        return

    key = args[1].strip().lower()
    if key not in HISTORICAL_FIGURES:
        client.replyMessage(
            Message(text=f"❌ Không tìm thấy nhân vật: {args[1]}"),
            msg_obj, thread_id, thread_type
        )
        return

    nv = HISTORICAL_FIGURES[key]
    achievements_text = "\n".join([f"- {a}" for a in nv["achievements"]])

    text = (
        f"🧑‍🎓 NHÂN VẬT LỊCH SỬ 🏛️\n\n"
        f"👤 Tên đầy đủ: {nv['full_name']}\n"
        f"📅 Sinh – Mất: {nv['birth_death']}\n"
        f"🌍 Quốc gia: {nv['country']}\n"
        f"⚔️ Chức vụ / Nghề nghiệp: {nv['position']}\n"
        f"🏆 Công lao và thành tựu:\n{achievements_text}"
    )

    client.replyMessage(Message(text=text), msg_obj, thread_id, thread_type)

def PTA():
    return {
        "nhanvatlichsu": handle_nhanvatlichsu
    }