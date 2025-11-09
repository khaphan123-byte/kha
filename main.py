import os
import time
import joblib
import streamlit as st
import google.generativeai as genai
from PIL import Image
from PyPDF2 import PdfReader
import docx

# =================== Cấu hình API key ===================
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_API_KEY ='AIzaSyBjH-YfcE9aoMqic_62XfkcnzXlS0zCxBQ'# ⚠️ set biến môi trường để bảo mật key
if not GOOGLE_API_KEY:
    st.error("API Key chưa được thiết lập! Vui lòng set GOOGLE_API_KEY.")
genai.configure(api_key=GOOGLE_API_KEY)

# =================== Thông tin cá nhân ===================
OWNER_NAME = "Phan Van Kha - My Thai name is Tauwan"
OWNER_TITLE = "Student - Informatics Teacher Education"
OWNER_UNIVERSITY = "Can Tho University, Viet Nam"
CHATBOT_NAME = "KhaBot"
AI_AVATAR_ICON = "🤖"

# =================== System Prompt ===================
SYSTEM_PROMPT = f"""
You are {CHATBOT_NAME}, an intelligent and helpful AI assistant created by {OWNER_NAME},
who is a {OWNER_TITLE} from {OWNER_UNIVERSITY}.
Always introduce yourself as an AI developed by {OWNER_NAME} when asked who you are.
Be polite, supportive, and educational, speaking naturally in Vietnamese or English depending on the user's language.
"""

# =================== Sidebar & Chat ID ===================
new_chat_id = f'{time.time()}'
os.makedirs('data', exist_ok=True)

try:
    past_chats: dict = joblib.load('data/past_chats_list')
except:
    past_chats = {}

with st.sidebar:
    st.markdown(f"### 🧑‍💻 {OWNER_NAME}")
    st.caption(f"{OWNER_TITLE} – {OWNER_UNIVERSITY}")
    st.markdown("---")
    st.write("### 💬 Past Chats")

    if st.session_state.get('chat_id') is None:
        st.session_state.chat_id = st.selectbox(
            label='Select chat',
            options=[new_chat_id] + list(past_chats.keys()),
            format_func=lambda x: past_chats.get(x, 'New Chat')
        )

    if st.button('🆕 New Chat'):
        st.session_state.chat_id = new_chat_id
        st.session_state.messages = []
        st.session_state.gemini_history = []
        st.experimental_rerun()

# =================== Hàm đọc file ===================
def read_file_content(uploaded_file):
    ext = uploaded_file.name.split('.')[-1].lower()
    content = ""
    if ext == "pdf":
        reader = PdfReader(uploaded_file)
        for page in reader.pages:
            content += page.extract_text() + "\n"
    elif ext in ["docx", "doc"]:
        doc = docx.Document(uploaded_file)
        content = "\n".join([p.text for p in doc.paragraphs])
    elif ext in ["txt", "md"]:
        content = uploaded_file.read().decode("utf-8", errors="ignore")
    else:
        content = "(Không thể đọc định dạng file này.)"
    return content.strip()

def chunk_text(text, chunk_size=2000):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

# =================== Gọi Gemini ===================
def send_to_gemini(prompt, history, file_content=None, image_file=None):
    model = genai.GenerativeModel("models/gemini-2.5-pro")  # chọn model có hỗ trợ

    parts = [SYSTEM_PROMPT]
    if prompt:
        parts.append(prompt)
    if file_content:
        parts.append(file_content)
    if image_file:
        parts.append(f"[image: {image_file.name}]")  # hoặc xử lý thực sự hình ảnh theo API

    response = model.generate_content(
        [{"role": "user", "parts": parts}],
        generation_config={"temperature": 0.7}
    )

    reply_text = response.text or "(Không có phản hồi)"
    history.append({"role": "user", "parts": parts})
    history.append({"role": "model", "parts": [reply_text]})
    return reply_text


# =================== Khởi tạo session_state ===================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "gemini_history" not in st.session_state:
    st.session_state.gemini_history = []

# =================== Header ===================
st.title(f"🤖 {CHATBOT_NAME}")
st.caption(f"AI Assistant by {OWNER_NAME} – {OWNER_UNIVERSITY}")

# =================== Hiển thị tin nhắn cũ ===================
for msg in st.session_state.messages:
    with st.chat_message(name=msg["role"], avatar=AI_AVATAR_ICON if msg["role"] == "ai" else "🧑"):
        st.markdown(msg["content"])

# =================== Upload file & ảnh ===================
uploaded_file = st.file_uploader("📄 Tải file (PDF, DOCX, TXT, MD)", type=["pdf", "docx", "txt", "md"])
uploaded_image = st.file_uploader("📷 Tải ảnh (tuỳ chọn)", type=["png", "jpg", "jpeg"])

file_text = ""
if uploaded_file:
    file_text = read_file_content(uploaded_file)
    st.success(f"Đã tải file: {uploaded_file.name}")
    with st.expander("📚 Xem nội dung file"):
        st.text(file_text[:2000] + ("..." if len(file_text) > 2000 else ""))

# =================== Xử lý chat ===================
if prompt := st.chat_input("💬 Nhập câu hỏi hoặc mô tả của bạn..."):
    st.session_state.messages.append(dict(role='user', content=prompt))

    chunks = chunk_text(file_text, chunk_size=2000) if file_text else [""]

    full_reply = ""
    for chunk in chunks:
        reply = send_to_gemini(prompt, st.session_state.gemini_history, file_content=chunk, image_file=uploaded_image)
        full_reply += reply + "\n"

    with st.chat_message(name="ai", avatar=AI_AVATAR_ICON):
        st.markdown(full_reply.strip())

    st.session_state.messages.append(dict(role="ai", content=full_reply.strip()))

    # Lưu lại lịch sử
    past_chats[st.session_state.chat_id] = (
        st.session_state.messages[0]['content'] if st.session_state.messages else 'Untitled'
    )
    joblib.dump(past_chats, 'data/past_chats_list')
