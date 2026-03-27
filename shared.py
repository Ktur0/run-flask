from flask import Flask, request, jsonify, render_template
import google.generativeai as genai

# Cấu hình chung cho Gemini
genai.configure(api_key="AIzaSyC6bFKqRQglZrE_rKbUyGCvL9Za6MbZV_c")  # Sử dụng API key từ tienthien, có thể thay nếu cần

# Model chung
model = genai.GenerativeModel("gemini-3-flash-preview")

# Hàm cho vanchan: Chat Đông y
def vanchan_chat(user_msg, chat_history):
    SYSTEM_PROMPT = """
Bạn là chuyên gia Đông y.

YÊU CẦU:
- Trả lời tối đa 3-4 câu
- Câu ngắn, rõ, không lan man

FORMAT HTML:
Thể trạng:...
Nguyên nhân:...
Đề xuẩt ăn uống:...
Gợi ý:...

Nếu CHƯA đủ thông tin:
→ chỉ hỏi 1 câu ngắn (KHÔNG phân tích)

Không viết ngoài format.
"""
    full_prompt = SYSTEM_PROMPT + "\n" + "\n".join(chat_history)
    try:
        response = model.generate_content(contents=full_prompt)
        reply = response.text if hasattr(response, "text") and response.text else "Không có phản hồi"
    except Exception as e:
        reply = f"Lỗi: {str(e)}"
    return reply

# Hàm cho tienthien: Phân tích thể trạng
def tienthien_analyze(data):
    # Logic rule-based
    cold = str(data.get("cold", "")).lower()
    hot = str(data.get("hot", "")).lower()
    tired = str(data.get("tired", "")).lower()
    result = []
    if "có" in cold or "yes" in cold or "y" in cold:
        result.append("Dương hư (thiên về lạnh)")
    if "có" in hot or "yes" in hot or "y" in hot:
        result.append("Nhiệt")
    if "có" in tired or "yes" in tired or "y" in tired or "mệt" in tired:
        result.append("Khí hư")
    if not result:
        result.append("Cân bằng")
    constitution = ", ".join(result)

    # Prompt cho Gemini
    prompt = f"""Bạn là chuyên gia Đông y.
Đây KHÔNG phải chuẩn đoán bệnh.

Thông tin:
- Thể chất: {constitution}
- Ngày sinh: {data.get("dob")}
- Tính cách: {data.get("personality")}
- Hay lạnh: {data.get("cold")}
- Hay nóng: {data.get("hot")}
- Hay mệt: {data.get("tired")}
- Mong muốn: {data.get("request")}

Hãy trả về lời khuyên ngắn gọn:
1. Tổng quan thể chất
2. Lời khuyên ăn uống
3. Lối sống hợp lý

Viết dễ hiểu, không quá dài."""

    try:
        response = model.generate_content(prompt)
        clean_text = response.text.replace("**", "").replace("##", "").strip()
        return {"constitution": constitution, "advice": clean_text}
    except Exception as e:
        return {"error": str(e), "constitution": "Lỗi phân tích", "advice": f"Chi tiết lỗi: {str(e)}"}

# Hàm tạo app vanchan
def create_vanchat_app():
    app = Flask(__name__)
    chat_history = []

    @app.route("/")
    def home():
        return render_template("vanchan.html")  # Giả sử template chung hoặc riêng

    @app.route("/chat", methods=["POST"])
    def chat():
        user_msg = request.json.get("message")
        print("USER:", user_msg)
        chat_history.append(f"User: {user_msg}")
        reply = vanchan_chat(user_msg, chat_history)
        print("AI:", reply)
        chat_history.append(f"AI: {reply}")
        return jsonify({"reply": reply})

    return app

# Hàm tạo app tienthien
def create_tienthien_app():
    app = Flask(__name__)

    @app.route("/")
    def home():
        return render_template("tienthien.html")

    @app.route("/analyze", methods=["POST"])
    def analyze():
        data = request.json
        if not data:
            return jsonify({"error": "Không có dữ liệu"}), 400
        result = tienthien_analyze(data)
        return jsonify(result)

    return app

if __name__ == "__main__":
    # Chạy cả hai app trên các port khác nhau
    import threading

    vanchan_app = create_vanchat_app()
    tienthien_app = create_tienthien_app()

    def run_vanchat():
        vanchan_app.run(debug=False, port=5000)

    def run_tienthien():
        tienthien_app.run(debug=False, port=5001)

    threading.Thread(target=run_vanchat).start()
    threading.Thread(target=run_tienthien).start()