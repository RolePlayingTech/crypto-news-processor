# cryptoNewsProcessor.py
import os
import feedparser
import requests
from datetime import datetime
import json
from openai import OpenAI
from dotenv import load_dotenv

# -------------------- Configuration --------------------
CRYPTO_NEWS_FEEDS = [
    'https://cointelegraph.com/rss',
    'https://cryptopotato.com/feed/',
    'https://cryptobriefing.com/feed/'
]

COINGECKO_API = "https://api.coingecko.com/api/v3"

REPORTS = {
    'en': {
        'title': "Crypto Daily Report",
        'market_overview': "Market Overview",
        'top_news': "Top News Analysis",
        'source': "Source",
        'summary': "Summary",
        'key_points': "Key Points",
        'sentiment': "Sentiment",
        'impact': "Potential Impact",
        'explanation': "Simple Explanation"
    },
    'pl': {
        'title': "Codzienne Podsumowanie Kryptowalut",
        'market_overview': "Przegląd Rynku",
        'top_news': "Analiza Najważniejszych Nowości",
        'source': "Źródło",
        'summary': "Podsumowanie",
        'key_points': "Kluczowe Punkty",
        'sentiment': "Nastrój",
        'impact': "Potencjalny Wpływ",
        'explanation': "Proste Wyjaśnienie"
    }
}

# -------------------- News Fetching --------------------
def fetch_crypto_news():
    """Collect news from multiple RSS feeds"""
    all_news = []
    
    for feed_url in CRYPTO_NEWS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                all_news.append({
                    'title': entry.title,
                    'summary': entry.summary if 'summary' in entry else '',
                    'link': entry.link,
                    'published': entry.published if 'published' in entry else '',
                    'source': feed_url.split('/')[2]
                })
        except Exception as e:
            print(f"Error fetching {feed_url}: {str(e)}")
    
    return all_news[:15]

# -------------------- Market Data Fetching --------------------
def get_market_data():
    """Get essential market data from CoinGecko"""
    try:
        response = requests.get(f"{COINGECKO_API}/coins/markets", params={
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': 10,
            'page': 1,
            'sparkline': False
        })
        return response.json()
    except Exception as e:
        print(f"Error fetching market data: {str(e)}")
        return []

# -------------------- AI Processing --------------------
def process_with_ai(content, api_key, language):
    """Use AI to analyze and summarize content"""
    client = OpenAI(api_key=api_key)
    
    system_prompt = {
        'en': """Analyze this crypto information. Perform:
        1. English summary (if foreign language)
        2. Key points extraction
        3. Sentiment analysis
        4. Potential market impact assessment
        5. Simple explanation (ELI5)
        Format response as JSON with these keys: summary, key_points, sentiment, market_impact, eli5""",
        
        'pl': """Przeanalizuj informacje o kryptowalutach. Wykonaj:
        1. Podsumowanie po polsku 
        2. Wyodrębnienie kluczowych punktów
        3. Analizę sentymentu
        4. Ocena potencjalnego wpływu na rynek
        5. Proste wyjaśnienie (ELI5) do każdego wyjaśnienia dodaj zabawny tekst w stylu krypto degena i imprezowicza"
        Format odpowiedzi jako JSON z kluczami: summary, key_points, sentiment, market_impact, eli5"""
    }
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "system",
                "content": system_prompt[language]
            }, {
                "role": "user",
                "content": str(content)
            }],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"AI processing error: {str(e)}")
        return None

# -------------------- Report Generation --------------------
def generate_report(processed_data, market_data, language):
    """Create a markdown format report"""
    lang = REPORTS[language]
    report = f"# {lang['title']} - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    
    # Market Overview
    report += f"## {lang['market_overview']}\n"
    for coin in market_data:
        report += f"- **{coin['symbol'].upper()}**: ${coin['current_price']} ({coin['price_change_percentage_24h']:.2f}%)\n"
    
    # News Analysis
    report += f"\n## {lang['top_news']}\n"
    for item in processed_data:
        report += f"### {item['title']}\n"
        report += f"**{lang['source']}**: {item['source']}\n"
        report += f"**{lang['summary']}**: {item['ai_analysis']['summary']}\n"
        report += f"**{lang['key_points']}**:\n"
        for point in item['ai_analysis']['key_points']:
            report += f"- {point}\n"
        report += f"**{lang['sentiment']}**: {item['ai_analysis']['sentiment']}\n"
        report += f"**{lang['impact']}**: {item['ai_analysis']['market_impact']}\n"
        report += f"**{lang['explanation']}**: {item['ai_analysis']['eli5']}\n\n"
    
    return report

# -------------------- Main Workflow --------------------
def main():
    # Load environment
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("Missing OpenAI API key in .env file")
        return
    
    # Language selection
    lang = input("Choose language (en/pl): ").strip().lower()
    if lang not in ['en', 'pl']:
        print("Invalid language choice. Defaulting to English.")
        lang = 'en'
    
    # Fetch data
    print("Fetching crypto data...")
    news_articles = fetch_crypto_news()
    market_data = get_market_data()
    
    # Process news with AI
    processed_news = []
    for article in news_articles:
        print(f"Processing: {article['title'][:50]}...")
        analysis = process_with_ai(article, api_key, lang)
        if analysis:
            processed_news.append({
                **article,
                'ai_analysis': analysis
            })
    
    # Generate and save report
    report = generate_report(processed_news, market_data, lang)
    filename = f"Crypto_Report_{datetime.now().strftime('%Y%m%d_%H%M')}_{lang}.md"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Report generated: {filename}")

if __name__ == "__main__":
    main()