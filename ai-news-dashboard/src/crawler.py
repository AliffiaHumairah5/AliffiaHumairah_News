import feedparser
from bs4 import BeautifulSoup
import datetime

def fetch_rss_news():
    # Contoh sumber RSS sesuai PRD-mu
    rss_urls = {
        'Detik': 'https://feed.detik.com/rss/berita',
        'Kompas': 'https://news.kompas.com/rss/index.xml'
    }
    
    all_news = []
    
    for source, url in rss_urls.items():
        feed = feedparser.parse(url)
        for entry in feed.entries:
            # Bersihkan deskripsi berita dari tag HTML jika ada
            soup = BeautifulSoup(getattr(entry, 'summary', ''), 'html.parser')
            content = soup.get_text()
            
            all_news.append({
                'title': entry.title,
                'content': content if content else entry.title,
                'source': source,
                'url': entry.link,
                'published_at': getattr(entry, 'published', datetime.datetime.now().isoformat())
            })
            
    return all_news