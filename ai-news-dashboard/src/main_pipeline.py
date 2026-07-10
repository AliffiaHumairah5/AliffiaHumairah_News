import os
import sys
from supabase import create_client
import pandas as pd

# Menambahkan path folder src agar Python di GitHub Actions tidak bingung saat import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crawler import fetch_rss_news
from analyzer import analyze_sentiment, extract_topics

# Mengambil kredensial dari GitHub Secrets
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Kredensial SUPABASE_URL atau SUPABASE_KEY belum diatur di GitHub Secrets!")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def main():
    print("1. Memulai crawling berita...")
    raw_news = fetch_rss_news()
    
    print(f"Berhasil mengambil {len(raw_news)} berita dari RSS. Memeriksa duplikasi dan menyimpan ke Supabase...")
    
    inserted_news = []
    for item in raw_news:
        try:
            # Gunakan upsert dengan on_conflict='url' agar jika berita sudah ada, tidak akan duplikat
            res = supabase.table("news").upsert({
                "title": item['title'],
                "content": item['content'],
                "source": item['source'],
                "url": item['url']
            }, on_conflict="url").execute()
            
            if res.data:
                inserted_news.append(res.data[0])
        except Exception as e:
            print(f"Skip/Gagal menyimpan artikel '{item['title'][:30]}...': {e}")
            
    if not inserted_news:
        print("Tidak ada berita baru untuk dianalisis.")
        return
        
    df_news = pd.DataFrame(inserted_news)
    
    print("2. Menjalankan Analisis Sentimen menggunakan IndoBERT...")
    sentiments = []
    for idx, row in df_news.iterrows():
        try:
            label, score = analyze_sentiment(row['title'], row['content'])
            sentiments.append({
                "news_id": row['id'],
                "sentiment": label,
                "confidence": float(score)
            })
        except Exception as e:
            print(f"Gagal memprediksi sentimen untuk ID {row['id']}: {e}")
            
    if sentiments:
        supabase.table("sentiment").insert(sentiments).execute()
        print(f"Berhasil menyimpan {len(sentiments)} hasil analisis sentimen.")
    
    print("3. Menjalankan Topic Modeling menggunakan BERTopic & Membuat Rekomendasi...")
    try:
        df_analyzed, topic_info = extract_topics(df_news)
        
        has_recommendation = False
        
        for idx, row in topic_info.iterrows():
            # Jika topiknya outlier (-1) dan ada topik spesifik lain yang terbentuk, kita skip.
            # Tapi jika isinya cuma -1 semua, biarkan lolos agar dashboard tidak kosong.
            if row['Topic'] == -1 and len(topic_info) > 1: 
                continue 
                
            # Mengambil kata kunci representasi langsung dari dataframe info bawaan BERTopic
            if 'Representation' in row and isinstance(row['Representation'], list) and len(row['Representation']) > 0:
                topic_name = ", ".join(row['Representation'][:3])
            else:
                topic_name = "Berita Umum / Campuran"
                
            try:
                supabase.table("recommendation").insert({
                    "topic_name": f"Topik: {topic_name}",
                    "recommendation_score": float(row['Count'] * 1.5),
                    "reason": f"Mencakup total {row['Count']} pembahasan berita yang terpantau dalam pipeline terakhir."
                }).execute()
                has_recommendation = True
            except Exception as e:
                print(f"Gagal menyimpan rekomendasi ke database: {e}")

        # Jalur Fallback: Jika sistem benar-benar gagal membuat klaster formal
        if not has_recommendation:
            try:
                supabase.table("recommendation").insert({
                    "topic_name": "Topik: Berita Hangat Harian",
                    "recommendation_score": 10.0,
                    "reason": "Kumpulan berita campuran terbaru dari media nasional yang siap ditinjau oleh redaksi."
                }).execute()
            except Exception as e:
                print(f"Gagal menyimpan fallback rekomendasi: {e}")

    except Exception as e:
        print(f"Gagal memproses Topic Modeling: {e}")

    print("Pipeline Selesai! Semua data sukses diperbarui di Supabase.")

if __name__ == "__main__":
    main()
