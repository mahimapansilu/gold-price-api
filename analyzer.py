import json
import os
import datetime
import urllib.request
import xml.etree.ElementTree as ET

def get_market_data():
    """ලෝක පුවත් කියවා Trend එක සහ පුවත් සිරස්තල ලබා ගනී"""
    sentiment = 0
    news_headlines = []
    
    try:
        # Google News RSS හරහා අලුත්ම ක්‍රමයට දත්ත ලබා ගැනීම (Block වීම අවමයි)
        url = "https://news.google.com/rss/search?q=gold+market+price&hl=en-US&gl=US&ceid=US:en"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req, timeout=15)
        xml_data = response.read()
        
        # XML දත්ත නිවැරදිව කියවීම
        root = ET.fromstring(xml_data)
        
        for item in root.findall('.//item')[:5]:
            title = item.find('title').text
            if " - " in title:
                title = title.rsplit(" - ", 1)[0]
            news_headlines.append(title.strip())
            
        if not news_headlines:
             news_headlines = ["ලෝක රත්‍රන් වෙළඳපොළේ සුවිශේෂී පුවත් අද දින වාර්තා වී නොමැත."]

        full_text = " ".join([t.lower() for t in news_headlines])
        
        pos_words = ['rise', 'high', 'jump', 'bullish', 'increase', 'gain', 'strong', 'up', 'soar', 'record', 'buy']
        neg_words = ['fall', 'low', 'drop', 'bearish', 'decrease', 'loss', 'weak', 'down', 'crash', 'sell']
        
        pos_score = sum(full_text.count(word) for word in pos_words)
        neg_score = sum(full_text.count(word) for word in neg_words)
        
        if pos_score > neg_score: sentiment = 0.0005  
        elif neg_score > pos_score: sentiment = -0.0005 
        
    except Exception as e:
        print(f"News Analysis Error: {e}")
        news_headlines = ["දැනට ලෝක වෙළඳපොළ පුවත් ලබාගැනීම තාවකාලිකව ඇනහිට ඇත."]
        sentiment = 0 
        
    return sentiment, news_headlines

def run_analysis():
    try:
        if not os.path.exists('data.json'): return

        with open('data.json', 'r') as f:
            data = json.load(f)

        history = data.get("history", data) if isinstance(data, dict) else data

        if not history or len(history) < 2: return

        last_entry = history[-1]
        prev_entry = history[-2]
        
        curr_22 = float(last_entry.get('price_22k_8g', 0))
        curr_24 = float(last_entry.get('price_24k_1g', 0))
        prev_22 = float(prev_entry.get('price_22k_8g', 0))
        
        initial_24 = curr_24
        initial_22 = curr_22

        trend_diff = curr_22 - prev_22 
        
        sentiment, news_list = get_market_data()
        
        reason = ""
        status = ""
        
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

        for i in range(1, 6):
            current_trend = current_trend * 0.6 
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

        result = {
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "sentiment": status,
            "reason": reason, 
            "news": news_list,
            "forecast": forecast
        }

        with open('analysis.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=4, ensure_ascii=False)

    except Exception as e:
        print(f"Main Analysis Error: {e}")

if __name__ == "__main__":
    run_analysis()
