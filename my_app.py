import streamlit as st
from PyPDF2 import PdfReader
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import os

# --- 1. إعدادات الصفحة والتصميم الجمالي ---
st.set_page_config(page_title="AI Knowledge Hub", page_icon="🧠", layout="centered")

# إضافة لمسات جمالية باستخدام CSS (تكبير الخط وتحسين الألوان)
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #4CAF50;
        color: white;
        font-size: 18px;
        font-weight: bold;
    }
    h1 {
        color: #1E3A8A;
        font-family: 'Arial';
        font-size: 40px !important;
        text-align: center;
    }
    .stTextInput>div>div>input {
        font-size: 20px !important;
    }
    .stRadio>div {
        flex-direction: row;
        justify-content: center;
        gap: 20px;
        font-size: 22px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إعداد المفتاح بأمان ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.warning("⚠️ يرجى إضافة GOOGLE_API_KEY في إعدادات Secrets.")

# --- 3. وظائف المعالجة ---
def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
    return text

def get_youtube_text(video_url):
    try:
        if "v=" in video_url:
            video_id = video_url.split("v=")[1].split("&")[0]
        else:
            video_id = video_url.split("/")[-1]
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ar', 'en'])
        return " ".join([i['text'] for i in transcript])
    except:
        return None

# --- 4. واجهة المستخدم الرئيسية (بدون Sidebar) ---
st.markdown("<h1>🧠 خبير المعرفة الذكي</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 20px;'>ارفع ملفاتك أو ضع رابط فيديو وابدأ الدردشة مع المحتوى</p>", unsafe_allow_html=True)
st.markdown("---")

# تبديل المصدر في الصفحة الرئيسية
source_type = st.radio("اختر مصدر البيانات:", ("📄 ملف PDF", "🎥 رابط YouTube"))

# مساحة لحفظ النص في الجلسة
if 'final_context' not in st.session_state:
    st.session_state['final_context'] = ""

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    if source_type == "📄 ملف PDF":
        uploaded_files = st.file_uploader("ارفع ملفات الـ PDF هنا", accept_multiple_files=True, type=['pdf'])
        if st.button("تحليل المستندات"):
            if uploaded_files:
                with st.spinner("جاري القراءة..."):
                    st.session_state['final_context'] = get_pdf_text(uploaded_files)
                    st.success("✅ تم التحليل بنجاح!")
            else:
                st.error("يرجى اختيار ملف!")

    else:
        yt_link = st.text_input("ضع رابط YouTube هنا:", placeholder="https://www.youtube.com/watch?v=...")
        if st.button("تحليل الفيديو"):
            if yt_link:
                with st.spinner("جاري استخراج النص..."):
                    st.session_state['final_context'] = get_youtube_text(yt_link)
                    if st.session_state['final_context']:
                        st.success("✅ تم تحليل الفيديو!")
                    else:
                        st.error("تعذر جلب النص. تأكد من وجود ترجمة للفيديو.")

st.markdown("---")

# --- 5. منطقة الدردشة ---
st.markdown("<h3 style='text-align: center;'>💬 اسأل أي سؤال حول المحتوى:</h3>", unsafe_allow_html=True)
user_query = st.text_input("", placeholder="اكتب سؤالك هنا...")

if user_query:
    if st.session_state['final_context']:
        try:
            with st.spinner("جاري التفكير..."):
                # استخدام الموديل الأكثر استقراراً لتجنب خطأ 404
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                full_prompt = f"""
                أنت مساعد ذكي. بناءً على النص التالي فقط، أجب على السؤال بدقة واحترافية.
                إذا لم تكن الإجابة موجودة، قل 'المعلومة غير متوفرة في المصدر'.
                
                نص المصدر:
                {st.session_state['final_context'][:15000]}
                
                السؤال:
                {user_query}
                """
                
                response = model.generate_content(full_prompt)
                st.markdown("---")
                st.markdown("### 🤖 الإجابة:")
                st.info(response.text)
        except Exception as e:
            st.error(f"حدث خطأ في الاتصال: {e}")
    else:
        st.warning("⚠️ حلل مصدراً أولاً (PDF أو YouTube) لكي أتمكن من إجابتك.")
        
