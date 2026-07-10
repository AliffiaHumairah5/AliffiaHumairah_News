import streamlit as st
import os
from supabase import create_client
import pandas as pd
import plotly.express as px

# 1. KONFIGURASI HALAMAN STREAMLIT
st.set_page_config(
    page_title="AI-Based News Trend Intelligence Dashboard",
    page_icon="📊",
    layout="wide"
)

# 2. KONEKSI SUPABASE
# Mengambil variabel env dari Streamlit Secrets atau Local Env
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Kredensial SUPABASE_URL atau SUPABASE_KEY belum diatur di Streamlit Secrets!")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 3. HEADER DASHBOARD
st.title("📊 AI-Based News Trend Intelligence Dashboard")
st.caption("Sistem Analisis Tren & Sentimen Berita untuk Digo News & Urban Radio")
st.markdown("---")

# 4. MEMBUAT TATA LETAK KOLOM (KIRI & KANAN)
col_left, col_right = st.columns([3, 2])

# ==================== KOLOM KIRI: REKOMENDASI TOPIK ====================
with col_left:
    st.subheader("💡 Rekomendasi Topik Hari Ini")
    
    try:
        # Ambil data rekomendasi dari database Supabase
        recommendations = supabase.table("recommendation").select("*").order("recommendation_score", desc=True).execute().data
        
        if not recommendations:
            st.info("Belum ada data rekomendasi. Silakan jalankan pipeline pengolah data terlebih dahulu.")
        else:
            # Menggunakan enumerate(recommendations) untuk menjamin 'index' unik pada setiap tombol widget
            for index, rec in enumerate(recommendations):
                with st.expander(f"📌 {rec['topic_name']} (Skor: {rec['recommendation_score']})"):
                    st.write(f"**Alasan Rekomendasi:** {rec['reason']}")
                    
                    st.markdown("---")
                    st.write("📰 **Artikel Berita Terkait dalam Tren Ini:**")
                    
                    # Ekstraksi kata kunci utama dari text nama topik untuk mencarian relasi berita
                    clean_keywords = rec['topic_name'].replace("Topik:", "").split(",")
                    main_keyword = clean_keywords[-1].strip() if clean_keywords else ""
                    
                    if main_keyword and len(main_keyword) > 2:
                        # Cari maksimal 5 berita di tabel 'news' yang judulnya mirip kata kunci ini
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
                    
                    # Bagian Tombol Aksi Redaksi dengan KEY yang unik (menggunakan gabungan indeks dan potongan nama topik)
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button("✅ Gunakan Topik", key=f"use_{index}_{rec['topic_name'][:10]}"):
                            st.success(f"Topik '{rec['topic_name']}' berhasil dipilih untuk produksi berita!")
                    with btn_col2:
                        if st.button("❌ Abaikan", key=f"ignore_{index}_{rec['topic_name'][:10]}"):
                            st.warning("Topik diabaikan.")
                            
    except Exception as e:
        st.error(f"Gagal memuat data rekomendasi: {e}")

# ==================== KANAN: GRAFIK ANALISIS SENTIMEN ====================
with col_right:
    st.subheader("📈 Sekilas Sentimen Terakhir")
    
    try:
        # Ambil data dari tabel sentiment di Supabase
        sentiment_data = supabase.table("sentiment").select("sentiment").execute().data
        
        if not sentiment_data:
            st.info("Data sentimen belum tersedia.")
        else:
            # Konversi hasil query database ke bentuk DataFrame Pandas
            df_sentiment = pd.DataFrame(sentiment_data)
            
            # Hitung jumlah total kemunculan tiap kategori sentiment (positif, negatif, netral)
            sentiment_counts = df_sentiment['sentiment'].value_counts().reset_index()
            sentiment_counts.columns = ['Sentimen', 'Jumlah']
            
            # Skema warna grafik agar serasi dan profesional
            color_map = {
                'positif': '#2ecc71', # Hijau
                'netral': '#3498db',  # Biru
                'negatif': '#e74c3c'  # Merah
            }
            
            # Membuat visualisasi grafik batang interaktif menggunakan Plotly
            fig = px.bar(
                sentiment_counts, 
                x='Sentimen', 
                y='Jumlah',
                color='Sentimen',
                color_discrete_map=color_map,
                text_auto=True
            )
            
            fig.update_layout(
                showlegend=False,
                margin=dict(l=20, r=20, t=20, b=20),
                height=350
            )
            
            # Tampilkan chart di dashboard Streamlit
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"Gagal memuat data grafik sentimen: {e}")
