import streamlit as st
from PyPDF2 import PdfReader
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import os

# --- إعدادات الصفحة ---
st.set_page_config(page_title="خبير المعرفة", page_icon="🧠")

# --- جلب المفتاح بأمان ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("يرجى إضافة المفتاح في Secrets")

# --- وظائف بسيطة ومباشرة ---
def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
    return text

def get_youtube_text(video_url):
    try:
        video_id = video_url.split("v=")[1].split("&")[0] if "v=" in video_url else video_url.split("/")[-1]
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ar', 'en'])
        return " ".join([i['text'] for i in transcript])
    except:
        return None

# --- الواجهة ---
st.title("🧠 مساعدك الذكي البسيط")
source = st.radio("المصدر:", ("PDF", "YouTube"))

content = ""
if source == "PDF":
    files = st.file_uploader("ارفع الملف", accept_multiple_files=True)
    if st.button("تحليل"):
        content = get_pdf_text(files)
        st.session_state['content'] = content
        st.success("تم الحفظ!")
else:
    url = st.text_input("رابط اليوتيوب:")
    if st.button("تحليل"):
        content = get_youtube_text(url)
        st.session_state['content'] = content
        st.success("تم الحفظ!")

# --- سؤال وجواب ---
question = st.text_input("اسأل أي شيء:")
if question and 'content' in st.session_state:
    model = genai.GenerativeModel('gemini-pro')
    prompt = f"بناءً على هذا النص: {st.session_state['content']}\n\nأجب على السؤال: {question}"
    response = model.generate_content(prompt)
    st.write(response.text)
    
