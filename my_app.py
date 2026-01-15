import streamlit as st
import pandas as pd
import plotly.express as px

# 1. إعدادات الصفحة
st.set_page_config(page_title="محلل البيانات الاحترافي", layout="wide")

st.title("📊 محطة معالجة البيانات الذكية")
st.markdown("قم برفع ملفك وسأقوم بتنظيفه وتحليله لك فوراً")

# 2. منطقة رفع الملف
uploaded_file = st.file_uploader("اختر ملف (CSV أو Excel)", type=['csv', 'xlsx'])

if uploaded_file:
    # قراءة الملف حسب نوعه
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # 3. عرض البيانات الأصلية في تبويب
    tab1, tab2, tab3 = st.tabs(["🔍 استعراض البيانات", "🛠 تنظيف آلي", "📈 رسوم بيانية"])
    
    with tab1:
        st.subheader("عينة من بياناتك قبل المعالجة")
        st.dataframe(df.head(10))
        st.write(f"عدد الصفوف: {df.shape[0]} | عدد الأعمدة: {df.shape[1]}")

    with tab2:
        st.subheader("إجراءات التنظيف")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("حذف الصفوف المكررة"):
                old_count = len(df)
                df = df.drop_duplicates()
                st.info(f"تم حذف {old_count - len(df)} صف مكرر")
        
        with col2:
            if st.button("ملء الفراغات بقيمة (0)"):
                df = df.fillna(0)
                st.success("تم ملء جميع القيم المفقودة!")

        st.markdown("---")
        st.write("البيانات بعد التعديل:")
        st.dataframe(df.head(5))
        
        # زر التحميل
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("💾 تحميل الملف المنظف", data=csv, file_name="cleaned_data.csv", mime="text/csv")

    with tab3:
        st.subheader("تحليل سريع")
        # اختيار عمود للرسم البياني (يختار الأعمدة الرقمية فقط)
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if numeric_cols:
            selected_col = st.selectbox("اختر عموداً لرؤية توزيعه:", numeric_cols)
            fig = px.histogram(df, x=selected_col, title=f"توزيع قيم {selected_col}", color_discrete_sequence=['#00CC96'])
            st.plotly_chart(fig)
        else:
            st.warning("لا توجد أعمدة رقمية لرسمها!")

else:
    st.info("💡 بانتظار رفع الملف للبدء...")
