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
        # Kitco වෙනුවට කිසිදා Block නොවන Yahoo Finance Gold RSS එක භාවිත කිරීම
        url = "https://finance.yahoo.com/rss/headline?s=GC=F"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/114.0.0.0 Safari/537.36'
        }
        resp = requests.get(url, headers=headers, timeout=15)
        
        # XML දත්ත HTML Parser එක හරහා ආරක්ෂිතව කියවීම
        soup = BeautifulSoup(resp.content, 'html.parser')
        items = soup.find_all('item')
        
        for item in items[:5]: # ප්‍රධාන පුවත් 5ක් පමණක් තෝරාගැනීම
            title_tag = item.find('title')
            if title_tag:
                news_headlines.append(title_tag.text.strip())
        
        text = " ".join([t.lower() for t in news_headlines])
        
        # වෙළඳපොළට බලපාන ධනාත්මක සහ සෘණාත්මක වචන
        pos_words = ['rise', 'high', 'jump', 'bullish', 'increase', 'gain', 'strong', 'up', 'soar', 'buy', 'record']
        neg_words = ['fall', 'low', 'drop', 'bearish', 'decrease', 'loss', 'weak', 'down', 'crash', 'sell', 'plunge']
        
        pos_score = sum(text.count(word) for word in pos_words)
        neg_score = sum(text.count(word) for word in neg_words)
        
        if pos_score > neg_score: sentiment = 0.004
        elif neg_score > pos_score: sentiment = -0.004
        
    except Exception as e:
        print(f"News Analysis Error: {e}")
        news_headlines = ["ලෝක වෙළඳපොළ පුවත් ලබාගැනීම ප්‍රමාද වී ඇත. කරුණාකර පසුව උත්සාහ කරන්න."]
        sentiment = 0 
        
    return sentiment, news_headlines

def run_analysis():
    try:
        if not os.path.exists('data.json'):
            print("Error: data.json not found!")
            return

        with open('data.json', 'r') as f:
            data = json.load(f)

        history = data.get("history", data) if isinstance(data, dict) else data

        if not history or len(history) < 2: return

        # අවසන් දින 2ක මිල ගණන් ලබාගැනීම
        last_entry = history[-1]
        prev_entry = history[-2]
        
        curr_22 = float(last_entry.get('price_22k_8g', 0))
        curr_24 = float(last_entry.get('price_24k_1g', 0))
        prev_22 = float(prev_entry.get('price_22k_8g', 0))
        
        trend_diff = curr_22 - prev_22 # දින දෙකක මිලෙහි වෙනස
        
        sentiment, news_list = get_market_data()
        
        # 💡 වඩාත් යථාර්ථවාදී සහ වෘත්තීය හේතු දැක්වීම් නිර්මාණය කිරීම
        reason = ""
        status = ""
        
        if sentiment > 0 and trend_diff >= 0:
            status = "Bullish (ශක්තිමත් ඉහළ යෑමක්)"
            reason = "පසුගිය දින කිහිපය තුළ රත්‍රන් මිලෙහි පැහැදිලි වර්ධනයක් (Uptrend) දක්නට ලැබෙන අතර, ලෝක ආර්ථිකයේ අවිනිශ්චිතතා සහ ආයෝජකයින්ගේ ඉල්ලුම ඉහළ යාම මෙයට ප්‍රධාන වශයෙන් හේතු වී ඇත. ජාත්‍යන්තර පුවත් ද මීට සහාය දක්වයි."
        elif sentiment < 0 and trend_diff <= 0:
            status = "Bearish (ශක්තිමත් පහළ යෑමක්)"
            reason = "ලෝක වෙළඳපොලේ රත්‍රන් අලෙවි කිරීමේ ප්‍රවණතාවයක් (Sell-off) සහ ඩොලරයේ අගය ශක්තිමත් වීම හේතුවෙන්, ඉදිරි දිනවලද රත්‍රන් මිල පහළ යාමේ අවදානමක් පවතී."
        elif trend_diff > 0:
            status = "Slightly Bullish (සුළු ඉහළ යෑමක්)"
            reason = "දේශීය වෙළඳපොලේ රත්‍රන් සඳහා පවතින සාමාන්‍ය ඉල්ලුම සහ ආනයන සීමා/බදු හේතුවෙන් මිලෙහි යම් සුළු වර්ධනයක් පෙන්වයි. ලෝක පුවත් වල විශාල බලපෑමක් දැනට දක්නට නොලැබේ."
        elif trend_diff < 0:
            status = "Slightly Bearish (සුළු පහළ යෑමක්)"
            reason = "පසුගිය දින කිහිපය තුළ දේශීය හා ජාත්‍යන්තර වෙළඳපොලේ දක්නට ලැබෙන සුළු පසුබෑම (Correction) හේතුවෙන් මිලෙහි මෙම අඩුවීම අපේක්ෂා කෙරේ. ආයෝජකයින් ලාභ ලැබීම සඳහා රත්‍රන් විකිණීම මීට හේතු විය හැක."
        else:
            status = "Neutral (ස්ථායී මට්ටමක)"
            reason = "මේ මොහොතේ රත්‍රන් වෙළඳපොළෙහි විශාල උච්චාවචනයක් (විශාල මිල වෙනස්වීමක්) දක්නට නොලැබෙන අතර, මිල ගණන් එක්තරා ස්ථාවර මට්ටමක පවතිනු ඇතැයි අනුමාන කෙරේ."

        # අනාගත දින 5 සඳහා Prediction ගණනය කිරීම
        forecast = []
        for i in range(1, 6):
            # දිනකට වෙනස් වන ප්‍රමාණය (පසුගිය වෙනසෙන් 25% ක් + පුවත් වල බලපෑම)
            daily_change_22 = (trend_diff * 0.25) + (curr_22 * sentiment)
            daily_change_24 = (trend_diff * 0.25 * (curr_24/curr_22)) + (curr_24 * sentiment)
            
            curr_22 += daily_change_22
            curr_24 += daily_change_24
            
            future_date = (datetime.datetime.now() + datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            forecast.append({
                "date": future_date,
                "price_22k_8g": int(curr_22),
                "price_24k_1g": int(curr_24)
            })

        if len(news_list) == 0:
             news_list = ["නවතම ලෝක පුවත් තවමත් යාවත්කාලීන වී නොමැත."]

        result = {
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "sentiment": status,
            "reason": reason, 
            "news": news_list,
            "forecast": forecast
        }

        # සිංහල අකුරු නිවැරදිව සේව් කිරීම සඳහා ensure_ascii=False යෙදීම
        with open('analysis.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=4, ensure_ascii=False)
            
        print("Analysis and News fetched successfully!")

    except Exception as e:
        print(f"Main Analysis Error: {e}")

if __name__ == "__main__":
    run_analysis()
