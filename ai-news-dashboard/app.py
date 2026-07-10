import streamlit as st
import os
from supabase import create_client
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# 1. KONFIGURASI HALAMAN STREAMLIT
st.set_page_config(
    page_title="AI-Based News Trend Intelligence Dashboard",
    page_icon="📊",
    layout="wide"
)

# Pemicu refresh otomatis setiap 5 menit (300.000 milidetik)
st_autorefresh(interval=300000, key="supabase_data_sync_dashboard")

# 2. KONEKSI SUPABASE
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
            for index, rec in enumerate(recommendations):
                with st.expander(f"📌 {rec['topic_name']} (Skor: {rec['recommendation_score']})"):
                    st.write(f"**Alasan Rekomendasi:** {rec['reason']}")
                    
                    st.markdown("---")
                    st.write("📰 **Artikel Berita Terkait dalam Tren Ini:**")
                    
                    # Logika ekstraksi kata kunci
                    clean_text = rec['topic_name'].replace("Topik:", "").strip()
                    keywords = [k.strip() for k in clean_text.split(",") if len(k.strip()) > 2]
                    
                    main_keyword = ""
                    stop_words = ['di', 'dan', 'yang', 'untuk', 'ke', 'dari', 'dengan', 'dalam']
                    for kw in keywords:
                        if kw.lower() not in stop_words:
                            main_keyword = kw
                            break
                    
                    if not main_keyword and keywords:
                        main_keyword = keywords[0]
                    
                    if main_keyword:
                        related_news = supabase.table("news")\
                            .select("title", "source", "url")\
                            .ilike("title", f"%{main_keyword}%")\
                            .limit(5)\
                            .execute().data
                        
                        if related_news:
                            for news in related_news:
                                st.markdown(f"- [{news['title']}]({news['url']}) *({news['source']})*")
                        else:
                            st.write(f"*Tidak ada artikel di tabel 'news' yang spesifik memuat kata '{main_keyword}'.*")
                    else:
                        st.write("*Menampilkan kumpulan berita campuran makro harian.*")
                    
                    st.markdown("---")
                    
                    # Bagian Tombol Aksi Redaksi
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
        # --- KEMBALI KE TABEL SENTIMENT ---
        # Mengambil semua kolom dari tabel 'sentiment' agar kita aman memproses nama kolomnya
        sentiment_data = supabase.table("sentiment").select("*").execute().data
        
        if not sentiment_data:
            st.info("Data sentimen di database belum tersedia.")
        else:
            # Konversi ke DataFrame
            df_sentiment = pd.DataFrame(sentiment_data)
            
            # Deteksi otomatis nama kolom yang menampung label (misal namanya 'sentiment' atau 'label' atau 'prediction')
            kolom_target = None
            for col in df_sentiment.columns:
                if col.lower() in ['sentiment', 'label', 'prediction', 'hasil']:
                    kolom_target = col
                    break
            
            # Jika tidak sengaja nama kolomnya beda, pakai kolom pertama yang bertipe teks
            if not kolom_target:
                kolom_target = df_sentiment.columns[0]
                
            # Hitung kemunculan kategori
            sentiment_counts = df_sentiment[kolom_target].value_counts().reset_index()
            sentiment_counts.columns = ['Sentimen', 'Jumlah']
            
            # Skema warna grafik
            color_map = {
                'positif': '#2ecc71', 'netral': '#3498db', 'negatif': '#e74c3c',
                'positive': '#2ecc71', 'neutral': '#3498db', 'negative': '#e74c3c'
            }
            
            # Membuat grafik batang
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
            
            st.plotly_chart(fig, use_container_width=True)
                
    except Exception as e:
        st.error(f"Gagal memuat data grafik sentimen: {e}")
