import requests
from bs4 import BeautifulSoup
import json
import re
import os

url = "https://www.ideabeam.com/finance/rates/goldprice.php"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')

    scraped_data = []

    # වෙබ් අඩවියේ ඇති සියලුම tables හොයනවා
    tables = soup.find_all('table')
    
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            # දිනය සහ මිල තීරුවල තියෙන නිසා, තීරු 2ක් හෝ වැඩි ගණනක් තියෙනවද බලනවා
            if len(cols) >= 2:
                date_text = cols[0].text.strip()
                price_text = cols[1].text.strip()
                
                # දිනයක් විදිහට හඳුනාගන්න (අංක තියෙනවද බලනවා)
                if any(char.isdigit() for char in date_text):
                    # මිලෙන් අංක විතරක් වෙන් කරගන්නවා ("Rs." සහ කොමා අයින් කරලා)
                    clean_price = re.sub(r'[^\d]', '', price_text)
                    
                    # රත්‍රන් මිලක් සාමාන්‍යයෙන් රුපියල් 10,000 ට වඩා වැඩියි 
                    # (මේකෙන් වගුවේ තියෙන වෙනත් අදාළ නැති කුඩා අංක අයින් වෙනවා)
                    if clean_price and int(clean_price) > 10000:
                        scraped_data.append({
                            "date": date_text,
                            "price": int(clean_price)
                        })

    file_path = 'data.json'
    
    existing_data = []
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            try:
                existing_data = json.load(file)
            except json.JSONDecodeError:
                pass

    # දත්ත Dictionary එකක් විදිහට හදාගන්නවා (Date එක key එක විදිහට)
    merged_dict = {item["date"]: item["price"] for item in existing_data if item["price"] > 0}
    
    # අලුතින් scrape කරපු දත්ත වලින් ඒක update කරනවා
    # Site එකේ පරණම දවසේ ඉඳන් අලුත්ම දවසට පිළිවෙලට තියෙන්න අපි list එක reverse කරනවා
    scraped_data.reverse()
    
    for item in scraped_data:
        merged_dict[item["date"]] = item["price"]

    # ආයෙමත් JSON එකට ගැලපෙන විදිහට list එකක් කරනවා
    final_data = [{"date": k, "price": v} for k, v in merged_dict.items()]

    # File එකට ලියනවා
    with open(file_path, 'w') as file:
        json.dump(final_data, file, indent=4)

    print(f"Successfully scraped and updated records. Total records: {len(final_data)}")

except Exception as e:
    print(f"Error: {e}")
