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
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = requests.get(url, headers=headers, timeout=15)
        
        # RSS Feed එක නිවැරදිව කියවීම
        soup = BeautifulSoup(resp.content, 'xml')
        items = soup.find_all('item')
        
        for item in items[:5]: # ප්‍රධාන පුවත් 5
            if item.title:
                news_headlines.append(item.title.text.strip())
        
        text = " ".join([t.lower() for t in news_headlines])
        
        pos_words = ['rise', 'high', 'jump', 'bullish', 'increase', 'gain', 'strong', 'up', 'soar']
        neg_words = ['fall', 'low', 'drop', 'bearish', 'decrease', 'loss', 'weak', 'down', 'crash']
        
        pos_score = sum(text.count(word) for word in pos_words)
        neg_score = sum(text.count(word) for word in neg_words)
        
        if pos_score > neg_score: sentiment = 0.003
        elif neg_score > pos_score: sentiment = -0.003
        
    except Exception as e:
        print(f"News Analysis Error: {e}")
        news_headlines = ["ලෝක රත්‍රන් වෙළඳපොළ පුවත් ලබාගැනීම තාවකාලිකව ඇනහිට ඇත."]
        
    return sentiment, news_headlines

def run_analysis():
    try:
        with open('data.json', 'r') as f:
            data = json.load(f)

        history = data.get("history", data) if isinstance(data, dict) else data

        if not history or len(history) < 2: return

        # අවසන් දින 2ක මිල ගණන්
        last_entry = history[-1]
        prev_entry = history[-2]
        
        curr_22 = float(last_entry.get('price_22k_8g', 0))
        curr_24 = float(last_entry.get('price_24k_1g', 0))
        prev_22 = float(prev_entry.get('price_22k_8g', 0))
        
        trend_diff = curr_22 - prev_22 # පසුගිය දින දෙකේ වෙනස
        
        sentiment, news_list = get_market_data()
        
        # 💡 හේතුව (Reason) සහ තත්ත්වය නිර්මාණය කිරීම
        reason = ""
        status = ""
        
        if sentiment > 0 and trend_diff >= 0:
            status = "Bullish (මිල ඉහළ යෑමේ ප්‍රවණතාවයක්)"
            reason = "පසුගිය දිනවල මිල ඉහළ යෑමේ රටාවක් පෙන්වන අතර, ලෝක වෙළඳපොලේ ධනාත්මක පුවත් ද මීට හේතු වී ඇත. එබැවින් ඉදිරි දිනවල මිල තවදුරටත් ඉහළ යා හැක."
        elif sentiment < 0 and trend_diff <= 0:
            status = "Bearish (මිල පහළ යෑමේ ප්‍රවණතාවයක්)"
            reason = "ලෝක වෙළඳපොලේ පවතින අහිතකර පුවත් සහ පසුගිය දිනවල මිල පහළ යෑමේ රටාව අනුව, ඉදිරි දිනවලද මිල තවදුරටත් අඩුවීමේ ප්‍රවණතාවයක් පවතී."
        elif trend_diff > 0:
            status = "Slightly Bullish (සුළු ඉහළ යෑමක්)"
            reason = "ලෝක පුවත් වල විශාල බලපෑමක් නොමැති වුවද, දේශීය වෙළඳපොලේ මිල ඉහළ යෑමේ ප්‍රවණතාවයක් පවතින බැවින් මිල සුළු වශයෙන් ඉහළ යා හැක."
        elif trend_diff < 0:
            status = "Slightly Bearish (සුළු පහළ යෑමක්)"
            reason = "ලෝක පුවත් වල විශාල බලපෑමක් නොමැති වුවද, දේශීය වෙළඳපොලේ මිල අඩුවීමේ ප්‍රවණතාවයක් පවතින බැවින් මිල තවදුරටත් පහළ යා හැක."
        else:
            status = "Neutral (ස්ථායී මට්ටමක)"
            reason = "වෙළඳපොලේ විශාල වෙනසක් පෙන්නුම් නොකරන අතර, ලෝක පුවත් ද මධ්‍යස්ථ බැවින් මිල ගණන් ස්ථායීව පවතිනු ඇතැයි අපේක්ෂා කෙරේ."

        # අනාගත දින 5 සඳහා Prediction එක හැදීම (Trend + News එකතු කර)
        forecast = []
        for i in range(1, 6):
            # දිනකට වෙනස් වන ප්‍රමාණය (පසුගිය වෙනසෙන් 30% ක් + පුවත් වල බලපෑම)
            daily_change_22 = (trend_diff * 0.3) + (curr_22 * sentiment)
            daily_change_24 = (trend_diff * 0.3 * (curr_24/curr_22)) + (curr_24 * sentiment)
            
            curr_22 += daily_change_22
            curr_24 += daily_change_24
            
            future_date = (datetime.datetime.now() + datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            forecast.append({
                "date": future_date,
                "price_22k_8g": int(curr_22),
                "price_24k_1g": int(curr_24)
            })

        result = {
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "sentiment": status,
            "reason": reason, # අලුතින් එකතු කළ හේතුව
            "news": news_list,
            "forecast": forecast
        }

        with open('analysis.json', 'w') as f:
            json.dump(result, f, indent=4)
            
        print("Analysis completed successfully!")

    except Exception as e:
        print(f"Main Analysis Error: {e}")

if __name__ == "__main__":
    run_analysis()
