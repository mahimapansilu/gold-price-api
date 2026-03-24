import requests
from bs4 import BeautifulSoup
import json
import re
import os
import datetime

# 1. දත්ත ලබාගන්නා මූලාශ්‍ර
GOLD_URL = "https://www.ideabeam.com/finance/rates/goldprice.php"
NEWS_URL = "https://www.kitco.com/rss/gold-news/" # ලෝක රත්‍රන් පුවත් ලබාගන්නා තැන

headers = {'User-Agent': 'Mozilla/5.0'}

def get_news_sentiment():
    """ලෝක පුවත් කියවා වෙළඳපොළ තත්ත්වය (+1, 0, -1) තීරණය කරයි"""
    sentiment = 0
    try:
        resp = requests.get(NEWS_URL, timeout=10)
        soup = BeautifulSoup(resp.content, 'xml')
        headlines = soup.find_all('title')
        
        positive_words = ['rise', 'high', 'jump', 'bullish', 'increase', 'gain', 'strong']
        negative_words = ['fall', 'low', 'drop', 'bearish', 'decrease', 'loss', 'weak']
        
        text = " ".join([h.text.lower() for h in headlines])
        
        pos_score = sum(text.count(word) for word in positive_words)
        neg_score = sum(text.count(word) for word in negative_words)
        
        if pos_score > neg_score: sentiment = 0.005 # 0.5% වර්ධනයක්
        elif neg_score > pos_score: sentiment = -0.005 # 0.5% අඩුවීමක්
    except:
        pass
    return sentiment

try:
    print("--- SCRAPING STARTED ---")
    # රත්‍රන් මිල Scrape කිරීම (කලින් කළ ආකාරයටම)
    response = requests.get(GOLD_URL, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    scraped_data = {}
    
    tables = soup.find_all('table')
    for table in tables:
        for row in table.find_all('tr'):
            cells = row.find_all(['th', 'td'])
            if len(cells) >= 5:
                date_text = cells[0].text.strip()
                if re.match(r"^\d{4}-\d{2}-\d{2}$", date_text):
                    p24k = int(re.sub(r'[^\d]', '', cells[2].text.split('.')[0]))
                    p22k = int(re.sub(r'[^\d]', '', cells[4].text.split('.')[0]))
                    if p24k > 10000: scraped_data[date_text] = {"price_24k_1g": p24k, "price_22k_8g": p22k}

    # දත්ත ගොනුව කියවීම
    file_path = 'data.json'
    existing_data = []
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            try:
                db = json.load(f)
                existing_data = db.get("history", [])
            except: pass

    # දත්ත ඒකාබද්ධ කිරීම
    merged = {item["date"]: {"price_24k_1g": item["price_24k_1g"], "price_22k_8g": item["price_22k_8g"]} for item in existing_data}
    for d, p in scraped_data.items(): merged[d] = p
    
    sorted_dates = sorted(merged.keys())
    history = [{"date": k, **merged[k]} for k in sorted_dates]

    # --- 🔮 දින 5ක අනාවැකිය ගණනය කිරීම ---
    sentiment_factor = get_news_sentiment()
    last_p22k = history[-1]["price_22k_8g"]
    last_p24k = history[-1]["price_24k_1g"]
    
    forecast = []
    current_p22k, current_p24k = last_p22k, last_p24k
    
    for i in range(1, 6):
        # සරල ගණිතමය ක්‍රමයක් + පුවත් බලපෑම
        current_p22k = int(current_p22k * (1 + sentiment_factor))
        current_p24k = int(current_p24k * (1 + sentiment_factor))
        
        forecast_date = (datetime.datetime.now() + datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        forecast.append({
            "date": forecast_date,
            "price_22k_8g": current_p22k,
            "price_24k_1g": current_p24k
        })

    # අවසාන JSON එක සෑදීම
    output = {
        "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "market_sentiment": "Bullish" if sentiment_factor > 0 else "Bearish" if sentiment_factor < 0 else "Neutral",
        "history": history,
        "forecast": forecast
    }

    with open(file_path, 'w') as f:
        json.dump(output, f, indent=4)
    print("--- SCRAPING COMPLETED ---")

except Exception as e:
    print(f"Error: {e}")
