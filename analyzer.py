import json
import os
import requests
from bs4 import BeautifulSoup
import datetime

def get_sentiment():
    """ලෝක පුවත් කියවා Trend එක බලයි"""
    try:
        url = "https://www.kitco.com/rss/gold-news/"
        # User-Agent එකක් දීම අනිවාර්යයි නැත්නම් Block වෙන්න පුළුවන්
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=15)
        
        # XML පාවිච්චි නොකර සරලව html.parser එකෙන්ම headlines ටික ගමු
        soup = BeautifulSoup(resp.content, 'html.parser')
        headlines = soup.find_all('title')
        
        text = " ".join([t.text.lower() for t in headlines])
        
        pos_words = ['rise', 'high', 'jump', 'bullish', 'increase', 'gain', 'strong', 'up']
        neg_words = ['fall', 'low', 'drop', 'bearish', 'decrease', 'loss', 'weak', 'down']
        
        pos_score = sum(text.count(word) for word in pos_words)
        neg_score = sum(text.count(word) for word in neg_words)
        
        if pos_score > neg_score: return 0.002 # 0.2% growth
        if neg_score > pos_score: return -0.002 # 0.2% drop
        return 0
    except Exception as e:
        print(f"Sentiment Analysis Error: {e}")
        return 0

def run_analysis():
    try:
        # 1. data.json කියවීම
        if not os.path.exists('data.json'):
            print("Error: data.json not found!")
            return

        with open('data.json', 'r') as f:
            data = json.load(f)

        # දත්ත structure එක පරීක්ෂා කිරීම (List එකක්ද නැද්ද යන්න)
        if isinstance(data, dict) and "history" in data:
            history = data["history"]
        else:
            history = data # සරල List එකක් නම්

        if not history:
            print("Error: No history data found!")
            return

        last_entry = history[-1]
        sentiment = get_sentiment()
        
        # 2. අනාවැකිය (Forecast) සෑදීම
        forecast = []
        curr_22 = float(last_entry.get('price_22k_8g', 0))
        curr_24 = float(last_entry.get('price_24k_1g', 0))

        # ඉදිරි දින 5 සඳහා
        for i in range(1, 6):
            curr_22 = int(curr_22 * (1 + sentiment))
            curr_24 = int(curr_24 * (1 + sentiment))
            
            # දින වකවානු සෑදීම
            future_date = (datetime.datetime.now() + datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            
            forecast.append({
                "date": future_date,
                "price_22k_8g": curr_22,
                "price_24k_1g": curr_24
            })

        # 3. analysis.json ලෙස සේව් කිරීම
        result = {
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "sentiment": "Bullish" if sentiment > 0 else "Bearish" if sentiment < 0 else "Neutral",
            "forecast": forecast
        }

        with open('analysis.json', 'w') as f:
            json.dump(result, f, indent=4)
            
        print("Analysis completed successfully!")

    except Exception as e:
        print(f"Main Analysis Error: {e}")

if __name__ == "__main__":
    run_analysis()
