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
    print("--- STARTING SCRAPER ---")
    response = requests.get(url, headers=headers, timeout=15)
    print(f"Website Status Code: {response.status_code}")
    
    soup = BeautifulSoup(response.content, 'html.parser')
    scraped_data = {}
    
    tables = soup.find_all('table')
    print(f"Found {len(tables)} tables on the page.")

    for i, table in enumerate(tables):
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['th', 'td'])
            
            # තීරු 2ක් හෝ වැඩි ගණනක් තියෙනවා නම්
            if len(cells) >= 2:
                first_col = cells[0].text.strip()
                
                # දිනයක්දැයි හඳුනාගැනීම (අංක තිබිය යුතුයි, නමුත් Rs, Ounce, Gram වැනි වචන නොතිබිය යුතුයි)
                has_numbers = any(char.isdigit() for char in first_col)
                invalid_words = ['Rs', 'Ounce', 'Gram', 'Carat']
                is_invalid = any(word in first_col for word in invalid_words)
                
                if has_numbers and not is_invalid and len(first_col) <= 20:
                    date_text = first_col
                    
                    # මේ පේළියේ තියෙන ඔක්කොම මිල ගණන් ටික ගන්නවා
                    prices = []
                    for cell in cells[1:]:
                        clean_num = re.sub(r'[^\d]', '', cell.text.split('.')[0])
                        if clean_num:
                            prices.append(int(clean_num))
                    
                    if len(prices) >= 2:
                        print(f"Found Date: {date_text} | Prices in row: {prices}")
                        
                        # ස්වයංක්‍රීයව මිල තෝරාගැනීම (තීරු මාරු වී තිබුණද මෙය ක්‍රියාත්මක වේ)
                        p_24k_1g = 0
                        p_22k_8g = 0
                        
                        # ග්‍රෑම් 1ක සාමාන්‍ය මිල 10,000-80,000 අතර වන අතර පවුමක මිල 100,000 ට වැඩිය.
                        gram_prices = [p for p in prices if 10000 < p < 80000]
                        pawn_prices = [p for p in prices if p > 100000]
                        
                        # ග්‍රෑම් 1 හි වැඩිම අගය 24k ලෙසද, පවුමේ අඩුම අගය 22k ලෙසද තෝරයි
                        if gram_prices:
                            p_24k_1g = max(gram_prices) 
                        if pawn_prices:
                            p_22k_8g = min(pawn_prices) 
                        
                        # අගයන් දෙකම හම්බුනා නම් විතරක් Dictionary එකට එකතු කරනවා
                        if p_24k_1g > 0 and p_22k_8g > 0:
                            scraped_data[date_text] = {
                                "price_24k_1g": p_24k_1g,
                                "price_22k_8g": p_22k_8g
                            }

    print(f"\nTotal Valid Records Scraped: {len(scraped_data)}")

    file_path = 'data.json'
    existing_data = []
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            try:
                existing_data = json.load(file)
            except:
                pass

    merged_dict = {}
    for item in existing_data:
        merged_dict[item["date"]] = {
            "price_24k_1g": item.get("price_24k_1g", 0),
            "price_22k_8g": item.get("price_22k_8g", item.get("price", 0))
        }
    
    for date, prices in scraped_data.items():
        merged_dict[date] = prices

    # දින අනුව Sort කිරීම
    sorted_dates = sorted(merged_dict.keys())
    
    final_data = []
    for k in sorted_dates:
        if merged_dict[k]["price_24k_1g"] > 0 and merged_dict[k]["price_22k_8g"] > 0:
            final_data.append({
                "date": k,
                "price_24k_1g": merged_dict[k]["price_24k_1g"],
                "price_22k_8g": merged_dict[k]["price_22k_8g"]
            })

    with open(file_path, 'w') as file:
        json.dump(final_data, file, indent=4)

    print(f"Successfully saved {len(final_data)} records to data.json")
    print("--- SCRAPER FINISHED ---")

except Exception as e:
    print(f"CRITICAL ERROR: {e}")
