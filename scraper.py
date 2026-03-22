import requests
from bs4 import BeautifulSoup
import json
import datetime
import os

# 1. වෙබ් අඩවියෙන් දත්ත ලබා ගැනීම
url = "https://www.ideabeam.com/finance/rates/goldprice.php"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')

    # සටහන: මෙහි ඇති 'selector' එක ideabeam වෙබ් අඩවියේ HTML ව්‍යුහය අනුව වෙනස් විය හැක.
    # සාමාන්‍යයෙන් මේවා <td> හෝ <div> ටැග් ඇතුලේ තියෙන්නේ. 
    # (උදාහරණයක් ලෙස 24K පවුමක මිල ගන්න විදිහක් පහත දැක්වේ)
    
    # අපි උපකල්පනය කරමු මිල තියෙන තැන මෙහෙම හොයාගන්න පුළුවන් කියලා:
    # මේක සයිට් එකේ ඇත්ත structure එක අනුව පොඩ්ඩක් වෙනස් කරන්න වෙන්න පුළුවන්.
    price_element = soup.select_first("table tr:nth-of-type(2) td:nth-of-type(2)") 
    
    if price_element:
        # රුපියල් ලකුණු සහ කොමා අයින් කරලා අංකය විතරක් ගන්නවා
        price_text = price_element.text.replace("Rs.", "").replace(",", "").strip()
        gold_price = int(price_text)
    else:
        gold_price = 0 # හොයාගන්න බැරි වුනොත්

except Exception as e:
    print(f"Error fetching data: {e}")
    gold_price = 0

# 2. JSON ෆයිල් එක යාවත්කාලීන කිරීම (Update)
file_path = 'data.json'

# කලින් දත්ත තියෙනවද බලනවා
if os.path.exists(file_path):
    with open(file_path, 'r') as file:
        try:
            data = json.load(file)
        except json.JSONDecodeError:
            data = []
else:
    data = []

# අද දිනය
today = datetime.datetime.now().strftime("%Y-%m-%d")

# අද දිනයට අදාලව කලින් දත්ත තියෙනවද කියලා චෙක් කරනවා (දවසට දෙපාරක් run වුනොත් එකම දිනේ දෙපාරක් වැටෙන එක නවත්තන්න)
existing_entry = next((item for item in data if item["date"] == today), None)

if existing_entry:
    existing_entry["price"] = gold_price
else:
    data.append({
        "date": today,
        "price": gold_price
    })

# අලුත් දත්ත ටික ආපහු JSON ෆයිල් එකට සේව් කරනවා
with open(file_path, 'w') as file:
    json.dump(data, file, indent=4)

print(f"Successfully updated price for {today}: Rs. {gold_price}")
