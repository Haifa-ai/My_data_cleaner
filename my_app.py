import streamlit as st
from PyPDF2 import PdfReader
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import os

# --- 1. إعدادات الصفحة والتصميم الجمالي الفخم ---
st.set_page_config(page_title="AI Knowledge Hub", page_icon="🧠", layout="centered")

# إضافة CSS مخصص (تحسين الخطوط، الأزرار، وبطاقة الإجابة)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
        text-align: right;
    }
    .main { background-color: #f0f2f6; }
    
    /* تصميم الأزرار */
    .stButton>button {
        width: 100%;
        border-radius: 15px;
        height: 3.5em;
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white;
        font-size: 20px !important;
        font-weight: bold;
        border: none;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    
    /* تصميم بطاقة الإجابة (بدل الرمادي) */
    .answer-card {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 15px;
        border-right: 5px solid #1e3a8a;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        font-size: 22px !important;
        line-height: 1.6;
        color: #1f2937;
        margin-top: 20px;
    }
    
    h1 { color: #1e3a8a; font-size: 45px !important; text-align: center; }
    .stTextInput input { font-size: 20px !important; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إعداد المفتاح ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("⚠️ لم يتم العثور على المفتاح!")

# --- 3. وظائف معالجة البيانات المحدثة ---
def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        try:
            pdf_reader = PdfReader(pdf)
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
        except: continue
    return text

def get_youtube_text(video_url):
    try:
        # استخراج ID الفيديو
        if "v=" in video_url:
            video_id = video_url.split("v=")[1].split("&")[0]
        else:
            video_id = video_url.split("/")[-1]
        
        # محاولة جلب الترجمة (عربي، ثم إنجليزي، ثم آلي)
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        try:
            # البحث عن ترجمة يدوية بالعربي أو الإنجليزي
            transcript = transcript_list.find_transcript(['ar', 'en'])
        except:
            # إذا لم توجد، نبحث عن الترجمة الآلية
            transcript = transcript_list.find_generated_transcript(['ar', 'en'])
            
        data = transcript.fetch()
        return " ".join([i['text'] for i in data])
    except Exception as e:
        return None

# --- 4. واجهة المستخدم الرئيسية ---
st.markdown("<h1>🧠 خبير المعرفة الذكي</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 22px; color: #64748b;'>حلل المحتوى واسأل بذكاء</p>", unsafe_allow_html=True)
st.markdown("---")

source_type = st.radio("", ("📄 ملف PDF", "🎥 فيديو YouTube"), horizontal=True)

if 'final_context' not in st.session_state:
    st.session_state['final_context'] = ""

col_main = st.columns([1, 4, 1])[1]
with col_main:
    if source_type == "📄 ملف PDF":
        uploaded_files = st.file_uploader("ارفع الملفات", accept_multiple_files=True, type=['pdf'])
        if st.button("🚀 ابدأ تحليل المستندات"):
            if uploaded_files:
                with st.spinner("جاري التحليل..."):
                    st.session_state['final_context'] = get_pdf_text(uploaded_files)
                    st.success("✅ تمت قراءة الملفات!")
    else:
        yt_link = st.text_input("رابط اليوتيوب:")
        if st.button("🚀 ابدأ تحليل الفيديو"):
            if yt_link:
                with st.spinner("جاري جلب نص الفيديو..."):
                    text = get_youtube_text(yt_link)
                    if text:
                        st.session_state['final_context'] = text
                        st.success("✅ تم جلب نص الفيديو بنجاح!")
                    else:
                        st.error("❌ لم يتم العثور على ترجمة لهذا الفيديو.")

st.markdown("---")

# --- 5. منطقة الدردشة ---
user_query = st.text_input("💬 اسأل أي سؤال حول المحتوى:")

if user_query:
    if st.session_state['final_context']:
        try:
            with st.spinner("جاري البحث عن إجابة..."):
                # نظام الاكتشاف التلقائي للموديل
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                selected_model = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in available_models else available_models[0]
                
                model = genai.GenerativeModel(selected_model)
                prompt = f"بناءً على النص، أجب بدقة:\n{st.session_state['final_context'][:15000]}\nالسؤال: {user_query}"
                
                response = model.generate_content(prompt)
                
                # عرض الإجابة داخل "بطاقة" فخمة بدل الرمادي
                st.markdown(f"""
                    <div class="answer-card">
                        <strong>🤖 الإجابة:</strong><br>
                        {response.text}
                    </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"خطأ: {e}")
    else:
        st.warning("⚠️ حلل مصدراً أولاً.")
        
