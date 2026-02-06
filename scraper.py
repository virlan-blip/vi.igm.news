import feedparser
import json
import time
import re
from datetime import datetime
import urllib.parse
from collections import Counter

# --- CONFIGURATION ---
RSS_BASE = "https://news.google.com/rss/search?hl=en-US&gl=US&ceid=US:en&q="

# Your categories
QUERIES = {
    'top_stories': '"online gambling" OR "online casino" OR "igaming news"',
    'all': 'iGaming OR "online casino" OR "sports betting" OR "gambling news"',
    'casino': '"new slot release" OR "table game" OR "Pragmatic Play" OR "Evolution Gaming" OR "Play’n GO" OR "game mechanics" OR Megaways OR "buy bonus" OR RTP OR "jackpot win" OR "live casino innovation" OR "crypto casino launch"',
    'industry': '"gambling regulation" OR "gambling license" OR "payment methods casino" OR "provably fair" OR "casino merger" OR "gambling affiliate" OR "responsible gambling tools"',
    'sports_betting': '"odds movement" OR "betting market shifts" OR "injury reports betting" OR "sharp money" OR "betting tips" OR "player props" OR "micro-bets" OR "same game parlay" OR "live betting"',
    'legal': '"gambling legalization" OR "betting tax" OR "gambling license approval" OR "gambling blacklist" OR "gambling advertising rules"',
    'bonuses': '"welcome bonus" OR "free bets" OR "low wager bonus" OR "wager free" OR "VIP promo" OR "high roller bonus" OR "casino promo code" OR "limited time offer"',
    'strategy': '"betting strategy" OR "bankroll management" OR "RTP explanation" OR "poker math" OR "blackjack strategy" OR "sports betting model" OR "betting mistakes"',
    'tech': '"AI betting tools" OR "blockchain gambling" OR "NFT gambling" OR "VR casino" OR "metaverse casino" OR "gamification betting" OR "crash games"',
    'scandals': '"huge casino win" OR "match fixing" OR "betting scandal" OR "casino dispute" OR "player ban" OR "famous bettor"',
    'esports': '"esports betting" OR "CS2 betting" OR "LoL odds" OR "Dota 2 betting" OR "Valorant betting" OR "esports market movement" OR "esports match fixing"',
    'fantasy': '"daily fantasy sports" OR DFS OR "player projections" OR "best ball" OR "fantasy prize pool" OR DraftKings OR FanDuel OR "fantasy legal news"',
    'lottery': '"lottery jackpot" OR "lottery results" OR "online lottery" OR "instant win games" OR "lottery strategy" OR "syndicate"',
    'skill': '"skill based casino" OR "arcade betting" OR "real money mini games" OR "PvP casino" OR "gambling tournaments"',
    'crypto': '"crypto betting" OR "tokenized gambling" OR "DAO casino" OR "NFT utility gambling" OR "on-chain jackpot" OR "no-kyc casino"',
    'social': '"social casino" OR "sweepstakes casino" OR "free to play casino" OR "social betting" OR "influencer casino"',
    'emerging': '"new igaming market" OR "latam betting" OR "asian gambling market" OR "african betting market" OR "igaming localization"'
}

def clean_html(raw_html):
    # Google News descriptions contain HTML tags. We remove them.
    cleanr = re.compile('<.*?>')
    text = re.sub(cleanr, '', raw_html)
    return text.replace("&nbsp;", " ").strip()

def clean_title(title):
    if " - " in title:
        return title.rsplit(" - ", 1)[0]
    return title

def get_source(title):
    if " - " in title:
        return title.rsplit(" - ", 1)[1]
    return "News"

def get_trending_keywords(all_titles):
    # Join all titles, lowercase, remove common stop words
    text = " ".join(all_titles).lower()
    # Simple stop words list
    stop_words = set(['the', 'a', 'in', 'to', 'of', 'and', 'for', 'on', 'with', 'at', 'is', 'it', 'new', 'best', 'online', 'casino', 'betting', 'gambling', 'games', 'game', 'how', 'play', 'guide', 'review', 'top', '2024', '2025', '2026', 'us', 'uk', 'vs', 'what', 'why', 'from', 'by', 'an', 'as'])
    
    words = re.findall(r'\b[a-z]{4,15}\b', text)
    filtered_words = [w for w in words if w not in stop_words]
    
    # Get top 5 most common words
    return [word for word, count in Counter(filtered_words).most_common(5)]

def fetch_feed(category, query):
    encoded_query = urllib.parse.quote(query + " when:7d")
    url = f"{RSS_BASE}{encoded_query}"
    
    print(f"Fetching {category}...")
    feed = feedparser.parse(url)
    
    news_items = []
    
    for entry in feed.entries[:20]:
        # Intelligent Description Cleaning
        desc = ""
        if 'summary' in entry:
            desc = clean_html(entry.summary)
            # If description is too short or just repeats title, skip it
            if len(desc) < 20 or desc.startswith("View full coverage"):
                desc = ""

        item = {
            "title": clean_title(entry.title),
            "desc": desc, # New Field
            "source": get_source(entry.title),
            "link": entry.link,
            "timestamp": time.mktime(entry.published_parsed) if entry.published_parsed else time.time()
        }
        news_items.append(item)
        
    return news_items

def main():
    all_titles_for_trending = []
    
    database = {
        "last_updated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "trending_tags": [], # New Field
        "data": {}
    }

    for cat, query in QUERIES.items():
        try:
            items = fetch_feed(cat, query)
            database["data"][cat] = items
            
            # Collect titles for analysis
            for item in items:
                all_titles_for_trending.append(item['title'])
                
        except Exception as e:
            print(f"Error fetching {cat}: {e}")
            database["data"][cat] = []

    # Calculate Trending Keywords from ALL collected news
    database["trending_tags"] = get_trending_keywords(all_titles_for_trending)

    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(database, f, indent=2)
    
    print("Database updated with SEO descriptions.")

if __name__ == "__main__":
    main()
