import random
from zlapi import Message

des = {
    'version': "1.0.0",
    'credits': "ngbao",
    'description': "Bói Bài",
    'power': "Thành viên"
}
# Danh sách các lá bài
cards = [
    "🃙 1 Bích", "🃙 2 Bích", "🃙 3 Bích", "🃙 4 Bích", "🃙 5 Bích",
    "🃙 6 Bích", "🃙 7 Bích", "🃙 8 Bích", "🃙 9 Bích", "🃙 10 Bích",
    "🃙 J Bích", "🃙 Q Bích", "🃙 K Bích", "🃙 1 Đỏ", "🃙 2 Đỏ",
    "🃙 3 Đỏ", "🃙 4 Đỏ", "🃙 5 Đỏ", "🃙 6 Đỏ", "🃙 7 Đỏ",
    "🃙 8 Đỏ", "🃙 9 Đỏ", "🃙 10 Đỏ", "🃙 J Đỏ", "🃙 Q Đỏ", "🃙 K Đỏ",
    "🃙 1 Rô", "🃙 2 Rô", "🃙 3 Rô", "🃙 4 Rô", "🃙 5 Rô",
    "🃙 6 Rô", "🃙 7 Rô", "🃙 8 Rô", "🃙 9 Rô", "🃙 10 Rô",
    "🃙 J Rô", "🃙 Q Rô", "🃙 K Rô", "🃙 1 Cơ", "🃙 2 Cơ",
    "🃙 3 Cơ", "🃙 4 Cơ", "🃙 5 Cơ", "🃙 6 Cơ", "🃙 7 Cơ",
    "🃙 8 Cơ", "🃙 9 Cơ", "🃙 10 Cơ", "🃙 J Cơ", "🃙 Q Cơ", "🃙 K Cơ"
]

# Lời giải thích cho từng lá bài
explanations = {
    "🃙 1 Bích": "Bạn có khả năng lãnh đạo mạnh mẽ và biết cách định hướng cuộc sống của mình. Hãy tự tin vào quyết định của bạn.",
    "🃙 2 Bích": "Sự cân bằng là điều quan trọng đối với bạn. Hãy tìm cách duy trì sự ổn định trong cuộc sống.",
    "🃙 3 Bích": "Bạn là người sáng tạo và luôn tìm kiếm cơ hội mới. Hãy theo đuổi đam mê của mình.",
    "🃙 4 Bích": "Sự ổn định sẽ mang lại cho bạn niềm vui và hạnh phúc. Hãy xây dựng nền tảng vững chắc cho tương lai.",
    "🃙 5 Bích": "Hãy tự tin trong quyết định của mình, bạn đang đi đúng hướng. Đừng ngại ngần thể hiện bản thân.",
    "🃙 6 Bích": "Sự quan tâm đến người khác sẽ mang lại cho bạn những mối quan hệ tốt đẹp. Hãy chăm sóc cho những người thân yêu.",
    "🃙 7 Bích": "Bạn cần dành thời gian cho bản thân để tìm kiếm những điều tốt đẹp. Hãy thư giãn và làm điều bạn yêu thích.",
    "🃙 8 Bích": "Hãy mở lòng và chấp nhận những cơ hội mới đến với bạn. Cuộc sống luôn có những bất ngờ thú vị.",
    "🃙 9 Bích": "Bạn luôn biết mình cần gì và không thích theo đám đông. Cuộc sống của bạn sẽ như bạn mong muốn nếu bạn kiên trì theo đuổi mục tiêu.",
    "🃙 10 Bích": "Tự do sẽ dẫn đến sự sáng tạo, hãy khám phá những điều mới mẻ. Đừng ngại trải nghiệm.",
    "🃙 J Bích": "Hãy tin tưởng vào trực giác của bạn, nó sẽ dẫn dắt bạn đến thành công. Đôi khi cảm giác là điều tốt nhất.",
    "🃙 Q Bích": "Sự khôn ngoan sẽ giúp bạn đưa ra những quyết định đúng đắn. Hãy học hỏi từ những người xung quanh.",
    "🃙 K Bích": "Bạn là người có sức ảnh hưởng lớn, hãy sử dụng nó để làm điều tốt. Đừng ngại dẫn dắt người khác.",
    
    "🃙 1 Rô": "Bạn là người rất kiên định và có năng lực. Hãy theo đuổi ước mơ của mình mà không lo lắng.",
    "🃙 2 Rô": "Cuộc sống của bạn sẽ có nhiều cơ hội. Hãy sẵn sàng nắm bắt chúng.",
    "🃙 3 Rô": "Hãy dành thời gian cho gia đình và bạn bè, họ sẽ mang lại cho bạn niềm vui.",
    "🃙 4 Rô": "Sự bình yên và ổn định đang ở gần bạn. Hãy trân trọng những gì bạn đang có.",
    "🃙 5 Rô": "Hãy mạo hiểm hơn trong cuộc sống. Đôi khi điều tốt nhất đến từ sự táo bạo.",
    "🃙 6 Rô": "Sự sáng tạo của bạn sẽ dẫn dắt bạn đến thành công. Đừng ngại thử nghiệm.",
    "🃙 7 Rô": "Bạn sẽ gặp gỡ những người bạn mới. Hãy mở lòng để kết nối.",
    "🃙 8 Rô": "Có thể có những thay đổi lớn trong cuộc sống của bạn, hãy chấp nhận chúng.",
    "🃙 9 Rô": "Hãy tin tưởng vào bản thân, bạn đang trên con đường đúng đắn.",
    "🃙 10 Rô": "Cuộc sống đang mở ra cho bạn nhiều lựa chọn. Hãy cẩn trọng khi đưa ra quyết định.",
    "🃙 J Rô": "Hãy là người dẫn dắt và truyền cảm hứng cho người khác.",
    "🃙 Q Rô": "Sự nhạy bén của bạn sẽ giúp bạn vượt qua mọi khó khăn.",
    "🃙 K Rô": "Bạn có khả năng lãnh đạo bẩm sinh. Hãy sử dụng sức mạnh đó để giúp đỡ người khác.",

    "🃙 1 Đỏ": "Sự nhiệt huyết trong bạn sẽ dẫn dắt bạn đến thành công. Hãy giữ lửa đam mê.",
    "🃙 2 Đỏ": "Tình bạn và tình yêu sẽ mang lại cho bạn nhiều niềm vui. Hãy trân trọng chúng.",
    "🃙 3 Đỏ": "Hãy để những điều tốt đẹp đến với bạn, hãy mở lòng với cuộc sống.",
    "🃙 4 Đỏ": "Cuộc sống của bạn sẽ có những khởi đầu mới. Hãy nắm bắt cơ hội này.",
    "🃙 5 Đỏ": "Hãy sống hết mình với những gì bạn yêu thích. Đừng bỏ lỡ những khoảnh khắc đẹp.",
    "🃙 6 Đỏ": "Sự sáng tạo của bạn sẽ mang lại cho bạn nhiều điều bất ngờ. Hãy khám phá nó.",
    "🃙 7 Đỏ": "Hãy tìm kiếm niềm vui từ những điều đơn giản trong cuộc sống.",
    "🃙 8 Đỏ": "Sự tự do sẽ mang đến cho bạn nhiều hạnh phúc. Hãy đón nhận nó.",
    "🃙 9 Đỏ": "Bạn có thể tạo ra hạnh phúc cho chính mình. Hãy dũng cảm theo đuổi nó.",
    "🃙 10 Đỏ": "Cuộc sống sẽ tràn đầy những cơ hội mới, hãy nắm bắt chúng.",
    "🃙 J Đỏ": "Sự ngọt ngào của tình yêu sẽ đến với bạn. Hãy mở lòng đón nhận.",
    "🃙 Q Đỏ": "Hãy là người bạn tốt nhất cho chính mình. Đừng quên yêu thương bản thân.",
    "🃙 K Đỏ": "Sự mạnh mẽ và quyết đoán sẽ giúp bạn vượt qua mọi thử thách.",

    "🃙 1 Cơ": "Bạn có trực giác rất mạnh mẽ. Hãy lắng nghe nó để đưa ra những quyết định đúng.",
    "🃙 2 Cơ": "Hãy luôn giữ niềm tin vào bản thân, bạn sẽ vượt qua mọi khó khăn.",
    "🃙 3 Cơ": "Tình yêu sẽ đến với bạn từ những nơi bất ngờ. Hãy mở lòng.",
    "🃙 4 Cơ": "Hãy dành thời gian cho gia đình, họ sẽ mang lại cho bạn sức mạnh.",
    "🃙 5 Cơ": "Cuộc sống có thể khó khăn, nhưng bạn sẽ tìm thấy cách vượt qua.",
    "🃙 6 Cơ": "Hãy tìm kiếm những điều tích cực trong cuộc sống, ngay cả khi khó khăn.",
    "🃙 7 Cơ": "Những người bạn thân thiết sẽ là chỗ dựa vững chắc cho bạn.",
    "🃙 8 Cơ": "Sự chân thành sẽ mở ra nhiều cánh cửa mới trong cuộc sống của bạn.",
    "🃙 9 Cơ": "Hãy làm những điều bạn yêu thích, nó sẽ mang lại hạnh phúc.",
    "🃙 10 Cơ": "Bạn có sức mạnh để thay đổi cuộc đời mình. Hãy dũng cảm thực hiện điều đó.",
    "🃙 J Cơ": "Tình yêu và sự ấm áp sẽ đến từ những người xung quanh bạn.",
    "🃙 Q Cơ": "Hãy tự tin vào bản thân và khả năng của bạn, bạn có thể làm được.",
    "🃙 K Cơ": "Sự trưởng thành sẽ mang lại cho bạn những quyết định đúng đắn trong cuộc sống."
}

# Lời khuyên ngẫu nhiên
advice = [
    "Hãy chuẩn bị cho bất ngờ sắp tới! 🍍🍀",
    "Thời gian sẽ chữa lành mọi vết thương. 🌻",
    "Luôn tin tưởng vào bản thân mình! 🌈",
    "Sống với đam mê sẽ mang lại niềm vui. 🌟",
    "Hãy chia sẻ yêu thương với mọi người! ❤️",
]

# Lưu trữ các lá bài đã được bốc
used_cards = []

def fortune_telling(message, message_object, thread_id, thread_type, author_id, client):
    # Lấy ID của người dùng
    user_id = author_id

    # Kiểm tra xem người dùng đã bốc bài chưa
    for card in used_cards:
        if card['user_id'] == user_id:
            drawn_card = card['card']
            explanation = explanations.get(drawn_card, "Không có thông tin cho lá bài này.")
            random_advice = random.choice(advice)
            
            # Hiển thị kết quả qua tin nhắn
            result_message = (
                "🎉 Chào mừng đến với 🧙‍♂️ Bói bài Jocker!\n"
                f"➜ 🧙‍♂️ Con đã bốc được lá: {drawn_card}\n"
                f"➜ 🪄 Để Thầy giải xem nào: {explanation}\n"
                f"➜ 🌻 Lời khuyên: {random_advice}"
            )
            client.replyMessage(Message(text=result_message), message_object, thread_id, thread_type)
            return

    # Nếu người dùng chưa bốc bài, chọn một lá bài ngẫu nhiên
    drawn_card = random.choice(cards)
    explanation = explanations.get(drawn_card, "Không có thông tin cho lá bài này.")
    random_advice = random.choice(advice)

    # Lưu lá bài và ID người dùng vào danh sách đã sử dụng
    used_cards.append({'user_id': user_id, 'card': drawn_card})

    # Hiển thị kết quả qua tin nhắn
    result_message = (
        "🎉 Chào mừng đến với 🧙‍♂️ Bói bài Jocker!\n"
        f"➜ 🧙‍♂️ Con đã bốc được lá: {drawn_card}\n"
        f"➜ 🪄 Để Thầy giải xem nào: {explanation}\n"
        f"➜ 🌻 Lời khuyên: {random_advice}"
    )

    client.replyMessage(Message(text=result_message), message_object, thread_id, thread_type)

def PTA():
    return {
        'boibai': fortune_telling  # Lệnh để gọi hàm bói bài Jocker
    }
    