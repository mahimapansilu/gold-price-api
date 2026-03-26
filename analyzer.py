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
        # හරියටම රත්‍රන් මිලට පමණක් අදාළ Google News ලබා ගැනීම
        url = "https://news.google.com/rss/search?q=gold+price&hl=en-US&gl=US&ceid=US:en"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = requests.get(url, headers=headers, timeout=15)
        
        soup = BeautifulSoup(resp.content, 'xml')
        items = soup.find_all('item')
        
        # ප්‍රධාන පුවත් 5
        for item in items[:5]:
            title = item.find('title').text.strip()
            # Google News වල අගට එන News Channel එකේ නම අයින් කිරීම (පැහැදිලි බව සඳහා)
            if " - " in title:
                title = title.rsplit(" - ", 1)[0]
            news_headlines.append(title)
        
        text = " ".join([t.lower() for t in news_headlines])
        
        pos_words = ['rise', 'high', 'jump', 'bullish', 'increase', 'gain', 'strong', 'up', 'soar', 'record', 'buy']
        neg_words = ['fall', 'low', 'drop', 'bearish', 'decrease', 'loss', 'weak', 'down', 'crash', 'sell', 'plunge']
        
        pos_score = sum(text.count(word) for word in pos_words)
        neg_score = sum(text.count(word) for word in neg_words)
        
        # ඉතා කුඩා අගයක් ලබා දෙමු (එවිට News වලින් Trend එක Over-power නොකරයි)
        if pos_score > neg_score: sentiment = 0.0005  
        elif neg_score > pos_score: sentiment = -0.0005 
        
    except Exception as e:
        print(f"News Analysis Error: {e}")
        news_headlines = ["ලෝක රත්‍රන් වෙළඳපොළ පුවත් ලබාගැනීම ප්‍රමාද වී ඇත."]
        sentiment = 0 
        
    return sentiment, news_headlines

def run_analysis():
    try:
        if not os.path.exists('data.json'):
            return

        with open('data.json', 'r') as f:
            data = json.load(f)

        history = data.get("history", data) if isinstance(data, dict) else data

        if not history or len(history) < 2: return

        # අවසන් දින 2
        last_entry = history[-1]
        prev_entry = history[-2]
        
        curr_22 = float(last_entry.get('price_22k_8g', 0))
        curr_24 = float(last_entry.get('price_24k_1g', 0))
        prev_22 = float(prev_entry.get('price_22k_8g', 0))
        
        initial_24 = curr_24
        initial_22 = curr_22

        trend_diff = curr_22 - prev_22 # ඇත්තටම දින දෙක අතර මිල වෙනස
        
        sentiment, news_list = get_market_data()
        
        reason = ""
        status = ""
        
        # 💡 Trend එක සහ News එක ගැලපෙන ආකාරය අනුව නිවැරදි හේතුවක් දීම
        if trend_diff < 0 and sentiment <= 0:
            status = "Bearish (පහළ යෑමේ ප්‍රවණතාවයක්)"
            reason = "පසුගිය දිනවල දේශීය වෙළඳපොලේ රත්‍රන් මිලෙහි පැහැදිලි අඩුවීමක් දක්නට ලැබෙන අතර, ලෝක පුවත් ද මීට සමානුපාතිකව පවතී. මේ හේතුවෙන් ඉදිරි දිනවලද මිල පහළ යනු ඇතැයි අපේක්ෂා කෙරේ."
        elif trend_diff > 0 and sentiment >= 0:
            status = "Bullish (ඉහළ යෑමේ ප්‍රවණතාවයක්)"
            reason = "රත්‍රන් මිලෙහි පැහැදිලි වර්ධනයක් (Uptrend) දක්නට ලැබෙන අතර, ලෝක ආර්ථික පුවත් ද මීට සහාය දක්වයි. එබැවින් ඉදිරි දිනවල මිල තවදුරටත් ඉහළ යා හැක."
        elif trend_diff < 0 and sentiment > 0:
            status = "Slightly Bearish (මිලෙහි සුළු පසුබෑමක්)"
            reason = "ලෝක වෙළඳපොලේ ධනාත්මක පුවත් පැවතියද, දේශීය වෙළඳපොලේ පසුගිය දිනවල දක්නට ලැබුණු මිල අඩුවීමේ ප්‍රවණතාවය (Correction) තවදුරටත් සුළු වශයෙන් බලපෑම් කළ හැක."
        elif trend_diff > 0 and sentiment < 0:
            status = "Slightly Bullish (මිලෙහි සුළු වර්ධනයක්)"
            reason = "ලෝක වෙළඳපොලේ තරමක පසුබෑමක් ගැන පුවත් පළ වුවද, දේශීයව පවතින ඉල්ලුම නිසා මිලෙහි යම් සුළු වර්ධනයක් පවත්වා ගනු ඇතැයි අනුමාන කෙරේ."
        else:
            status = "Neutral (ස්ථායී මට්ටමක)"
            reason = "මේ මොහොතේ රත්‍රන් වෙළඳපොළෙහි විශාල මිල වෙනස්වීමක් දක්නට නොලැබෙන අතර, මිල ගණන් එක්තරා ස්ථාවර මට්ටමක පවතිනු ඇතැයි අනුමාන කෙරේ."

        forecast = []
        current_trend = trend_diff

        # අනාගත දින 5 සඳහා Prediction ගණනය කිරීම
        for i in range(1, 6):
            # දිනෙන් දින Trend එකේ වේගය අඩු කිරීම (Curve එකක් සෑදීමට)
            current_trend = current_trend * 0.6 
            
            # News වල බලපෑම ඉතා සුළු වශයෙන් එකතු කිරීම
            sentiment_push = curr_22 * sentiment
            
            daily_change_22 = current_trend + sentiment_push
            daily_change_24 = daily_change_22 * (initial_24 / initial_22)
            
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

        with open('analysis.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=4, ensure_ascii=False)
            
        print("Analysis and News fetched successfully!")

    except Exception as e:
        print(f"Main Analysis Error: {e}")

if __name__ == "__main__":
    run_analysis()
