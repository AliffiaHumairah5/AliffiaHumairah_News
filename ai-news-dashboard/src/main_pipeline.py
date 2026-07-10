import os
from supabase import create_client
import pandas as pd
from crawler import fetch_rss_news
from analyzer import analyze_sentiment, extract_topics

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def main():
    print("1. Memulai crawling berita...")
    raw_news = fetch_rss_news()
    
    print(f"Berhasil mengambil {len(raw_news)} berita. Menyimpan ke Supabase...")
    
    inserted_news = []
    for item in raw_news:
        try:
            # Gunakan upsert atau insert dengan ignore untuk menghindari duplikasi URL
            res = supabase.table("news").upsert({
                "title": item['title'],
                "content": item['content'],
                "source": item['source'],
                "url": item['url']
            }, on_conflict="url").execute()
            
            if res.data:
                inserted_news.append(res.data[0])
        except Exception as e:
            print(f"Skip/Gagal menyimpan: {e}")
            
    if not inserted_news:
        print("Tidak ada berita baru untuk dianalisis.")
        return
        
    df_news = pd.DataFrame(inserted_news)
    
    print("2. Menjalankan Analisis Sentimen...")
    sentiments = []
    for idx, row in df_news.iterrows():
        label, score = analyze_sentiment(row['title'], row['content'])
        sentiments.append({
            "news_id": row['id'],
            "sentiment": label,
            "confidence": score
        })
    supabase.table("sentiment").insert(sentiments).execute()
    
    print("3. Menjalankan Topic Modeling & Rekomendasi...")
    df_analyzed, topic_info = extract_topics(df_news)
    
    print("3. Menjalankan Topic Modeling & Rekomendasi...")
    df_analyzed, topic_info = extract_topics(df_news)
    
    # KODE YANG DIPERBARUI:
    has_recommendation = False
    
    for idx, row in topic_info.iterrows():
        # Ubah logika: Jika belum ada kelompok terbentuk, biarkan outlier (-1) muncul sebagai general topic
        if row['Topic'] == -1 and len(topic_info) > 1: 
            continue # Jika ada topik lain yang terbentuk, skip -1. Jika hanya ada -1, biarkan lolos.
            
        # Ambil kata kunci representatif dari BERTopic
        words_list = topic_model.get_topic(row['Topic'])
        if words_list:
            topic_name = ", ".join([word for word, _ in words_list[:3]])
        else:
            topic_name = "Berita Umum / Campuran"
            
        supabase.table("recommendation").insert({
            "topic_name": f"Topik: {topic_name}",
            "recommendation_score": float(row['Count'] * 1.5),
            "reason": f"Mencakup total {row['Count']} pembahasan berita yang terpantau dalam pipeline terakhir."
        }).execute()
        has_recommendation = True

    # Jika benar-benar tidak ada rekomendasi formal yang lolos
    if not has_recommendation:
        supabase.table("recommendation").insert({
            "topic_name": "Topik: Berita Hangat Harian",
            "recommendation_score": 10.0,
            "reason": "Kumpulan berita campuran terbaru dari media nasional yang siap ditinjau oleh redaksi."
        }).execute()

if __name__ == "__main__":
    main()
