import json
import os
import requests
from bs4 import BeautifulSoup
import datetime

def get_market_data():
    """ලෝක පුවත් කියවා Trend එක සහ පුවත් සිරස්තල ලබා ගනී"""
    sentiment = 0
    news_headlines = []
    try:
        url = "https://www.kitco.com/rss/gold-news/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=15)
        
        soup = BeautifulSoup(resp.content, 'html.parser')
        headlines = soup.find_all('title')
        
        # ප්‍රධාන පුවත් 5ක් පමණක් ලබා ගැනීම
        for t in headlines[1:6]:  # පළමු එක බොහෝවිට channel name එක විය හැක
            if t.text.strip():
                news_headlines.append(t.text.strip())
        
        text = " ".join([t.text.lower() for t in headlines])
        
        pos_words = ['rise', 'high', 'jump', 'bullish', 'increase', 'gain', 'strong', 'up']
        neg_words = ['fall', 'low', 'drop', 'bearish', 'decrease', 'loss', 'weak', 'down']
        
        pos_score = sum(text.count(word) for word in pos_words)
        neg_score = sum(text.count(word) for word in neg_words)
        
        if pos_score > neg_score: sentiment = 0.002
        elif neg_score > pos_score: sentiment = -0.002
        
    except Exception as e:
        print(f"News Analysis Error: {e}")
        news_headlines = ["දැනට ලෝක වෙළඳපොළ පුවත් යාවත්කාලීන වෙමින් පවතී."]
        
    return sentiment, news_headlines

def run_analysis():
    try:
        if not os.path.exists('data.json'):
            print("Error: data.json not found!")
            return

        with open('data.json', 'r') as f:
            data = json.load(f)

        if isinstance(data, dict) and "history" in data:
            history = data["history"]
        else:
            history = data 

        if not history: return

        last_entry = history[-1]
        sentiment, news_list = get_market_data()
        
        forecast = []
        curr_22 = float(last_entry.get('price_22k_8g', 0))
        curr_24 = float(last_entry.get('price_24k_1g', 0))

        for i in range(1, 6):
            curr_22 = int(curr_22 * (1 + sentiment))
            curr_24 = int(curr_24 * (1 + sentiment))
            future_date = (datetime.datetime.now() + datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            forecast.append({
                "date": future_date,
                "price_22k_8g": curr_22,
                "price_24k_1g": curr_24
            })

        status = "Bullish (ඉහළ යෑමේ ප්‍රවණතාවයක්)" if sentiment > 0 else "Bearish (පහළ යෑමේ ප්‍රවණතාවයක්)" if sentiment < 0 else "Neutral (ස්ථායී මට්ටමක)"

        result = {
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "sentiment": status,
            "news": news_list,  # පුවත් එකතු කළ ස්ථානය
            "forecast": forecast
        }

        with open('analysis.json', 'w') as f:
            json.dump(result, f, indent=4)
            
        print("Analysis and News fetched successfully!")

    except Exception as e:
        print(f"Main Analysis Error: {e}")

if __name__ == "__main__":
    run_analysis()
