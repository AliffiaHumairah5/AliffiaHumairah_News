from transformers import pipeline
from bertopic import BERTopic
import pandas as pd

# Load model IndoBERT untuk sentimen (menggunakan model publik sebagai starting point)
# Pipelining ini akan berjalan di komputer GitHub Actions yang punya RAM 16GB
sentiment_pipeline = pipeline(
    "sentiment-analysis", 
    model="w11wo/indonesian-roberta-base-sentiment-classifier" # Contoh model publik IndoBERT
)

def analyze_sentiment(title, summary):
    text_to_analyze = f"{title} {summary}"[:512] # Batasi panjang token BERT
    result = sentiment_pipeline(text_to_analyze)[0]
    
    # Sesuaikan output label model ke format PRD kamu
    label_map = {'LABEL_0': 'negatif', 'LABEL_1': 'netral', 'LABEL_2': 'positif'}
    sentiment_label = label_map.get(result['label'], 'netral')
    
    return sentiment_label, result['score']

def extract_topics(news_df):
    # Buat model BERTopic sederhana untuk teks Indonesia
    topic_model = BERTopic(language="multilingual")
    
    # Gabungkan judul dan konten untuk pemodelan topik
    docs = (news_df['title'] + " " + news_df['content']).tolist()
    topics, probs = topic_model.fit_transform(docs)
    
    news_df['topic_id'] = topics
    
    # Ambil info representasi kata kunci per topik
    topic_info = topic_model.get_topic_info()
    return news_df, topic_info