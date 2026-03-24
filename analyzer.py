import json
import os
import requests
from bs4 import BeautifulSoup
import datetime

def get_sentiment():
    try:
        url = "https://www.kitco.com/rss/gold-news/"
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.content, 'xml')
        text = " ".join([t.text.lower() for t in soup.find_all('title')])
        pos = sum(text.count(w) for w in ['rise', 'high', 'bull', 'gain', 'up'])
        neg = sum(text.count(w) for w in ['fall', 'low', 'bear', 'loss', 'down'])
        return 0.003 if pos > neg else -0.003 if neg > pos else 0
    except: return 0

# දත්ත කියවීම
with open('data.json', 'r') as f:
    history = json.load(f)

last = history[-1]
sentiment = get_sentiment()
forecast = []

# ඉදිරි දින 5 අනාවැකිය
curr_22 = last['price_22k_8g']
curr_24 = last['price_24k_1g']

for i in range(1, 6):
    curr_22 = int(curr_22 * (1 + sentiment))
    curr_24 = int(curr_24 * (1 + sentiment))
    date = (datetime.datetime.now() + datetime.timedelta(days=i)).strftime("%Y-%m-%d")
    forecast.append({"date": date, "price_22k_8g": curr_22, "price_24k_1g": curr_24})

# වෙනම analysis.json එකකට සේව් කිරීම
result = {
    "sentiment": "Bullish" if sentiment > 0 else "Bearish" if sentiment < 0 else "Neutral",
    "forecast": forecast
}

with open('analysis.json', 'w') as f:
    json.dump(result, f, indent=4)
