import streamlit as st
from PyPDF2 import PdfReader
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
import os

# --- 1. إعدادات الصفحة والفخامة ---
st.set_page_config(page_title="خبير المعرفة الذكي", page_icon="🧠", layout="wide")

# --- 2. سطر المفتاح الآمن (الذي سيقرأ من Streamlit Secrets) ---
if "GOOGLE_API_KEY" in st.secrets:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("يرجى إضافة GOOGLE_API_KEY في إعدادات Secrets في Streamlit Cloud")

# --- 3. وظائف استخراج النص (PDF & YouTube) ---
def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        try:
            pdf_reader = PdfReader(pdf)
            for page in pdf_reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted
        except Exception as e:
            st.error(f"خطأ في قراءة ملف PDF: {e}")
    return text

def get_youtube_text(video_url):
    try:
        # استخراج المعرف سواء كان الرابط طويل أو قصير (v= أو be/)
        if "v=" in video_url:
            video_id = video_url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in video_url:
            video_id = video_url.split("youtu.be/")[1].split("?")[0]
        else:
            st.error("رابط اليوتيوب غير صحيح")
            return None
            
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ar', 'en'])
        return " ".join([i['text'] for i in transcript])
    except Exception as e:
        st.error(f"لا يمكن جلب النص من هذا الفيديو (قد لا تتوفر ترجمة مصاحبة): {e}")
        return None

# --- 4. معالجة النصوص والبحث الدلالي ---
def get_vector_store(text):
    # تقطيع النص بأسلوب هندسي دقيق لضمان عدم ضياع السياق
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(text)
    
    # تحويل النص لمتجهات عددية (Embeddings)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    
    # بناء قاعدة البيانات وتخزينها محلياً في السيرفر
    vector_store = FAISS.from_texts(chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")

def get_conversational_chain():
    # تصميم الـ Prompt بأسلوب يمنع الهلوسة
    prompt_template = """
    أنت خبير ذكاء اصطناعي متخصص في تحليل المحتوى. 
    استخدم السياق المقدم فقط للإجابة على السؤال. 
    إذا لم تجد الإجابة في السياق، قل بوضوح: "هذه المعلومة غير مذكورة في المصدر الذي زودتني به".
    لا تحاول اختلاق إجابات من خارج النص.

    السياق:\n {context}?\n
    سؤال المستخدم: \n{question}\n

    الإجابة التفصيلية:
    """
    model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    return load_qa_chain(model, chain_type="stuff", prompt=prompt)

# --- 5. واجهة المستخدم (Streamlit UI) ---
st.markdown("<h1 style='text-align: center;'>🧠 خبير المعرفة التفاعلي</h1>", unsafe_allow_html=True)
st.sidebar.title("🛠️ لوحة التحكم والمصادر")

source_type = st.sidebar.radio("اختر مصدر البيانات:", ("ملف PDF", "رابط YouTube"))

# تهيئة قاعدة البيانات عند الرفع
if source_type == "ملف PDF":
    pdf_docs = st.sidebar.file_uploader("ارفع ملفات الـ PDF", accept_multiple_files=True, type=['pdf'])
    if st.sidebar.button("تحليل المستندات"):
        if pdf_docs:
            with st.spinner("جاري قراءة الملفات وتحويلها لبيانات ذكية..."):
                raw_text = get_pdf_text(pdf_docs)
                if raw_text:
                    get_vector_store(raw_text)
                    st.sidebar.success("تم التحليل! يمكنك السؤال الآن.")
        else:
            st.sidebar.warning("يرجى رفع ملف أولاً.")

else:
    youtube_url = st.sidebar.text_input("ضع رابط فيديو اليوتيوب:")
    if st.sidebar.button("تحليل الفيديو"):
        if youtube_url:
            with st.spinner("جاري استخراج الكلام من الفيديو..."):
                raw_text = get_youtube_text(youtube_url)
                if raw_text:
                    get_vector_store(raw_text)
                    st.sidebar.success("تم تحليل الفيديو! يمكنك السؤال الآن.")
        else:
            st.sidebar.warning("يرجى وضع الرابط أولاً.")

# --- 6. التفاعل مع المستخدم ---
user_question = st.text_input("💬 اسأل الخبير عن أي تفصيل في المحتوى المرفوع:")

if user_question:
    if os.path.exists("faiss_index"):
        with st.spinner("جاري البحث في المصادر وتوليد الإجابة..."):
            embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
            # السماح بالتحميل الآمن لقاعدة البيانات
            new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
            docs = new_db.similarity_search(user_question)
            
            chain = get_conversational_chain()
            response = chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)
            
            st.markdown("### 🤖 إجابة الخبير:")
            st.info(response["output_text"])
    else:
        st.warning("يرجى تحليل مصدر (PDF أو YouTube) قبل طرح الأسئلة.") 
                    
