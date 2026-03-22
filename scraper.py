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

    scraped_data = {}

    tables = soup.find_all('table')
    
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            
            if len(cols) >= 5:
                date_text = cols[0].text.strip()
                
                # දිනය නිවැරදිදැයි පරීක්ෂා කිරීම
                if re.match(r"^\d{4}-\d{2}-\d{2}$", date_text):
                    
                    price_24k_text = cols[2].text.strip() # 24 Carat 1 Gram (3 වෙනි තීරුව)
                    price_22k_text = cols[4].text.strip() # 22 Carat 8 Grams (5 වෙනි තීරුව)
                    
                    try:
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

    # පරණ දත්ත තියෙනවා නම් ඒවා අරගන්නවා (කලින් තිබ්බ "price" එකත් 22k_8g විදිහටම ගන්නවා)
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

    with open(file_path, 'w') as file:
        json.dump(final_data, file, indent=4)

    print(f"Successfully scraped and updated records. Total records: {len(final_data)}")

except Exception as e:
    print(f"Error: {e}")
