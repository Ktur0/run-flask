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
        return response.text if hasattr(response, "text") and response.text else "Không có phản hồi"
    except Exception as e:
        return f"Lỗi: {str(e)}"


# Hàm cho tienthien: Phân tích thể trạng
def tienthien_analyze(data):
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

    prompt = f"""Bạn là chuyên gia Đông y.
Đây KHÔNG phải chuẩn đoán bệnh.

Thông tin:
- Thể chất: {constitution}
- Ngày sinh: {data.get('dob')}
- Tính cách: {data.get('personality')}
- Hay lạnh: {data.get('cold')}
- Hay nóng: {data.get('hot')}
- Hay mệt: {data.get('tired')}
- Mong muốn: {data.get('request')}

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


app = Flask(__name__)
chat_history = []


@app.route("/")
def home():
    # Nếu không có template, trả text đơn giản
    try:
        return render_template("vanchan.html")
    except Exception:
        return "API Service is running. Use /chat và /analyze endpoints."


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
