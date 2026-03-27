import os
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai

# API key nên lưu trong biến môi trường
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("Thiếu biến môi trường GEMINI_API_KEY")

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel("gemini-3-flash-preview")

# Hàm cho vanchan: Chat Đông y
def vanchan_chat(user_msg, chat_history):
    SYSTEM_PROMPT = """
Bạn là chuyên gia Đông y.

YÊU CẦU:
- Trả lời tối đa 5-7 câu
- Câu ngắn, rõ, không lan man
- Phân tích dựa trên thông tin người dùng trả lời

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
        return response.text if hasattr(response, "text") and response.text else "Không có phản hồi"
    except Exception as e:
        return f"Lỗi: {str(e)}"


# Hàm cho tienthien: Phân tích thể trạng
def tienthien_analyze(data):
    dob = data.get("dob", "")
    birth_time = data.get("birth_time", "")
    gender = data.get("gender", "")

    prompt = f"""Bạn là chuyên gia Đông y.

Đây KHÔNG phải chuẩn đoán bệnh.

Thông tin:
- Ngày sinh: {dob}
- Giờ sinh: {birth_time}
- Giới tính: {gender}

Hãy phân tích NGẮN GỌN:

1. Tổng quan thể chất (âm/dương, hàn/nhiệt)
2. Điểm mạnh cơ thể
3. Điểm cần chú ý
4. Gợi ý ăn uống & sinh hoạt

Viết dễ hiểu, không dài dòng."""

    try:
        response = model.generate_content(prompt)
        clean_text = response.text.replace("**", "").replace("##", "").strip()
        return {
            "constitution": "Phân tích tiên thiên",
            "advice": clean_text
        }
    except Exception as e:
        return {
            "error": str(e),
            "constitution": "Lỗi",
            "advice": f"Chi tiết lỗi: {str(e)}"
        }


app = Flask(__name__)
chat_history = []


@app.route("/")
def home():
    return """
    <h2>AI Đông y</h2>
    <p>Chọn chức năng:</p>
    <ul>
        <li><a href="/vanchan">Vấn chẩn (chat AI)</a></li>
        <li><a href="/tienthien">Phân tích thể trạng</a></li>
    </ul>
    """

@app.route("/vanchan")
def vanchan_ui():
    return render_template("vanchan.html")

@app.route("/tienthien")
def tienthien_ui():
    return render_template("tienthien.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json or {}
    message = data.get("message")
    if not message:
        return jsonify({"error": "Thiếu trường message"}), 400

    chat_history.append(f"User: {message}")
    reply = vanchan_chat(message, chat_history)
    chat_history.append(f"AI: {reply}")
    return jsonify({"reply": reply})


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json or {}
    if not data:
        return jsonify({"error": "Không có dữ liệu"}), 400

    result = tienthien_analyze(data)
    return jsonify(result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
