import feedparser
from bs4 import BeautifulSoup
import datetime
import urllib.request

def fetch_rss_news():
    # Menggunakan RSS Feed yang dikenal sangat stabil dan mengizinkan crawling metadata
    rss_urls = {
        'Antara News': 'https://www.antaranews.com/rss/top-news.xml',
        'Republika': 'https://www.republika.co.id/rss',
        'Tempo': 'https://rss.tempo.co/nasional'
    }
    
    all_news = []
    
    # Menambahkan User-Agent agar tidak diblokir oleh server portal berita
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    for source, url in rss_urls.items():
        try:
            print(f"Mencoba crawl dari: {source}...")
            # Mengunduh konten RSS menggunakan urllib dengan headers manual
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                html_content = response.read()
                
            # Parsing data XML dari RSS
            feed = feedparser.parse(html_content)
            
            print(f"Ditemukan {len(feed.entries)} artikel potensial di {source}")
            
            for entry in feed.entries:
                # Ambil ringkasan jika ada, kalau tidak ada pakai judul
                summary_text = getattr(entry, 'summary', '')
                if summary_text:
                    soup = BeautifulSoup(summary_text, 'html.parser')
                    content = soup.get_text()
                else:
                    content = entry.title
                
                # Format tanggal publikasi
                pub_date = getattr(entry, 'published', datetime.datetime.now().isoformat())
                
                all_news.append({
                    'title': entry.title,
                    'content': content if content else entry.title,
                    'source': source,
                    'url': entry.link,
                    'published_at': pub_date
                })
        except Exception as e:
            print(f"Gagal mengambil data dari {source}: {e}")
            
    return all_news
