import streamlit as st
from supabase import create_client
import os

# Konfigurasi halaman
st.set_page_config(page_title="News Trend Intelligence Dashboard", layout="wide")

# Inisialisasi Supabase (Sebaiknya gunakan st.secrets di Streamlit Cloud)
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "URL_LOKAL_KAMU_JIKA_TES")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "KEY_LOKAL_KAMU_JIKA_TES")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("📊 AI-Based News Trend Intelligence Dashboard")
st.caption("Sistem Analisis Tren & Sentimen Berita untuk Digo News & Urban Radio")
st.markdown("---")

# Layout Kolom Utama
col1, col2 = st.columns([2, 1])

with col1:
    st.header("💡 Rekomendasi Topik Hari Ini")
    
    # Ambil data rekomendasi terbaru dari gudang data Supabase
    response = supabase.table("recommendation").select("*").order("created_at", desc=True).limit(10).execute()
    recommendations = response.data
    
    if recommendations:
        for rec in recommendations:
            with st.expander(f"📌 {rec['topic_name']} (Skor: {rec['recommendation_score']})"):
                st.write(f"**Alasan Rekomendasi:** {rec['reason']}")
                st.write(f"**Status Saat Ini:** `{rec['status']}`")
                
                # Fitur Feedback Loop sesuai FR-11 di PRD kamu
                col_btn1, col_btn2 = st.columns(2)
                if col_btn1.button("✅ Gunakan Topik", key=f"use_{rec['id']}"):
                    supabase.table("recommendation").update({"status": "digunakan"}).eq("id", rec['id']).execute()
                    st.success("Status diperbarui!")
                    
                if col_btn2.button("❌ Abaikan", key=f"ignore_{rec['id']}"):
                    supabase.table("recommendation").update({"status": "tidak digunakan"}).eq("id", rec['id']).execute()
                    st.error("Rekomendasi diabaikan.")
    else:
        st.info("Belum ada data rekomendasi. Silakan jalankan pipeline pengolah data terlebih dahulu.")

with col2:
    st.header("📈 Sekilas Sentimen Terakhir")
    
    # Ambil 5 data sentimen berita terbaru untuk visualisasi ringkas
    sent_res = supabase.table("sentiment").select("sentiment").order("created_at", desc=True).limit(100).execute()
    
    if sent_res.data:
        import pandas as pd
        df_sent = pd.DataFrame(sent_res.data)
        sentiment_counts = df_sent['sentiment'].value_counts()
        
        # Tampilkan metrik sederhana
        st.bar_chart(sentiment_counts)
    else:
        st.info("Data sentimen belum tersedia.")