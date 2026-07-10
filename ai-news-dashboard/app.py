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

# --- KODE UNTUK MENAMPILKAN DETAIL TOPIK DI APP.PY ---

st.subheader("💡 Rekomendasi Topik Hari Ini")

# Ambil data rekomendasi dari Supabase
recommendations = supabase.table("recommendation").select("*").execute().data

if not recommendations:
    st.info("Belum ada data rekomendasi. Silakan jalankan pipeline pengolah data terlebih dahulu.")
else:
    for rec in recommendations:
        # Membuat kotak dropdown yang bisa diklik (Expander)
        with st.expander(f"📌 {rec['topic_name']} (Skor: {rec['recommendation_score']})"):
            st.write(f"**Alasan Rekomendasi:** {rec['reason']}")
            
            # --- BAGIAN DETAIL TAMBAHAN (BIAR LEBIH DETAIL) ---
            st.markdown("---")
            st.write("📰 **Artikel Berita Terkait dalam Tren Ini:**")
            
            # Kita bersihkan teks kata kunci untuk mencari berita yang mirip di database
            # Misal dari "Topik: di, jampidsus, korupsi" diambil kata kuncinya saja
            clean_keywords = rec['topic_name'].replace("Topik:", "").split(",")
            main_keyword = clean_keywords[-1].strip() if clean_keywords else ""
            
            if main_keyword and len(main_keyword) > 2:
                # Cari berita di database yang judul atau kontennya mengandung kata kunci utama ini
                related_news = supabase.table("news")\
                    .select("title", "source", "url")\
                    .ilike("title", f"%{main_keyword}%")\
                    .limit(5)\
                    .execute().data
                
                if related_news:
                    for news in related_news:
                        st.markdown(f"- [{news['title']}]({news['url']}) *({news['source']})*")
                else:
                    st.write("*Detail artikel sedang dimuat atau klasifikasi topik sangat umum.*")
            else:
                st.write("*Menampilkan kumpulan berita campuran makro harian.*")
            
            st.markdown("---")
            # --- AKHIR BAGIAN DETAIL TAMBAHAN ---

            # Tombol aksi redaksi
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Gunakan Topik", key=f"use_{rec['id']}"):
                    st.success("Topik berhasil dipilih untuk produksi berita!")
            with col2:
                if st.button("❌ Abaikan", key=f"ignore_{rec['id']}"):
                    st.warning("Topik diabaikan.")
