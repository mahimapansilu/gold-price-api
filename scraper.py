import requests
from bs4 import BeautifulSoup
import json
import re
import os

url = "https://www.ideabeam.com/finance/rates/goldprice.php"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')

    scraped_data = {}

    tables = soup.find_all('table')
    
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            # <th> (Table Header) සහ <td> (Table Data) කියන දෙකම ගන්නවා
            cells = row.find_all(['th', 'td'])
            
            # තීරු 6ක් හෝ ඊට වඩා තියෙන පේළි විතරක් තෝරනවා
            if len(cells) >= 6:
                date_text = cells[0].text.strip()
                
                # දිනය නිවැරදිදැයි පරීක්ෂා කිරීම (උදා: 2026-03-20)
                if re.match(r"^\d{4}-\d{2}-\d{2}$", date_text):
                    
                    price_24k_text = cells[2].text.strip() # 24 Carat 1 Gram (3 වෙනි තීරුව)
                    price_22k_text = cells[4].text.strip() # 22 Carat 8 Grams (5 වෙනි තීරුව)
                    
                    try:
                        # සත ගණන් (.00) ඉවත් කර පිරිසිදු අංකය ලබා ගැනීම
                        clean_24k = int(re.sub(r'[^\d]', '', price_24k_text.split('.')[0]))
                        clean_22k = int(re.sub(r'[^\d]', '', price_22k_text.split('.')[0]))
                        
                        if clean_24k > 0 and clean_22k > 0:
                            scraped_data[date_text] = {
                                "price_24k_1g": clean_24k,
                                "price_22k_8g": clean_22k
                            }
                    except ValueError:
                        continue

    file_path = 'data.json'
    
    existing_data = []
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            try:
                existing_data = json.load(file)
            except json.JSONDecodeError:
                pass

    # පරණ දත්ත තියෙනවා නම් ඒවා අරගන්නවා
    merged_dict = {}
    for item in existing_data:
        merged_dict[item["date"]] = {
            "price_24k_1g": item.get("price_24k_1g", 0),
            "price_22k_8g": item.get("price_22k_8g", item.get("price", 0))
        }
    
    # අලුත් දත්ත වලින් යාවත්කාලීන කිරීම
    for date, prices in scraped_data.items():
        merged_dict[date] = prices

    # දින අනුව Sort කිරීම
    sorted_dates = sorted(merged_dict.keys())
    
    final_data = []
    for k in sorted_dates:
        # මිල 0 ට වඩා වැඩි ඒවා පමණක් සේව් කරනවා
        if merged_dict[k]["price_24k_1g"] > 0 and merged_dict[k]["price_22k_8g"] > 0:
            final_data.append({
                "date": k,
                "price_24k_1g": merged_dict[k]["price_24k_1g"],
                "price_22k_8g": merged_dict[k]["price_22k_8g"]
            })

    # GitHub Action එකේ Log එකක් පෙන්නන්න print කරනවා
    print(f"Scraped {len(scraped_data)} valid records from the website.")

    with open(file_path, 'w') as file:
        json.dump(final_data, file, indent=4)

    print(f"Successfully saved to json. Total records in file: {len(final_data)}")

except Exception as e:
    print(f"Error: {e}")
