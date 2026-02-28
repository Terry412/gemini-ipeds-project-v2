import csv
import requests
import time
import os
import sys

# --- Constants ---
INPUT_FILE = "unique_eins_open_closed_v2_longitudinal_2000_2018.csv"
OUTPUT_FILE = "unique_eins_with_pdf_links.csv"
BASE_PATH = r"c:\Users\terre\Documents\Victor Dissertation Project - Gemini\pdf download 990"
API_BASE_URL = "https://projects.propublica.org/nonprofits/api/v2/organizations"

# Headers to mimic a browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

def get_filings(ein):
    """Queries the ProPublica Nonprofits API for an organization's filings."""
    if not ein: return None
    url = f"{API_BASE_URL}/{ein}.json"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 404: return None
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

def main():
    print("---------------------------------------------------------")
    print("Starting PDF Link Matching Process")
    
    input_path = os.path.join(BASE_PATH, INPUT_FILE)
    output_path = os.path.join(BASE_PATH, OUTPUT_FILE)

    # 1. Read the input CSV
    print(f"Reading: {INPUT_FILE}...")
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return

    all_rows = []
    unique_eins = set()
    input_fieldnames = []

    try:
        # utf-8-sig handles BOM if present
        with open(input_path, mode='r', newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            input_fieldnames = reader.fieldnames
            if not input_fieldnames:
                print("Error: Empty CSV or no headers found.")
                return
            for row in reader:
                all_rows.append(row)
                if row.get("EIN"):
                    unique_eins.add(row["EIN"])
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    print(f"Found {len(all_rows)} rows and {len(unique_eins)} unique EINs.")

    # 2. Build Filing Cache
    filing_cache = {} # structure: filing_cache[EIN] = { 2012: "url", ... }
    sorted_eins = sorted(list(unique_eins))
    total = len(sorted_eins)
    
    print("\n--- Fetching Data from ProPublica ---")
    for i, ein in enumerate(sorted_eins, 1):
        sys.stdout.write(f"\rProcessing EIN [{i}/{total}]: {ein}     ")
        sys.stdout.flush()
        
        clean_ein = str(ein).replace("-", "").strip()
        filing_cache[ein] = {}
        
        data = get_filings(clean_ein)
        if data:
            # Combine 'filings_with_data' and 'filings_without_data' (older years often in 'without')
            f_with = data.get('filings_with_data', []) or []
            f_without = data.get('filings_without_data', []) or []
            all_filings = f_with + f_without
            
            for filing in all_filings:
                year_val = filing.get('tax_prd_yr')
                pdf = filing.get('pdf_url')
                if year_val and pdf:
                    try:
                        filing_cache[ein][int(year_val)] = pdf
                    except ValueError: pass
        
        time.sleep(0.2) # Rate limit

    # 3. Match and Write Output
    print("\n\nMatching rows and writing output...")
    output_fieldnames = list(input_fieldnames)
    if "990_PDF_URL" not in output_fieldnames:
        output_fieldnames.append("990_PDF_URL")
    
    matches_found = 0
    try:
        with open(output_path, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=output_fieldnames)
            writer.writeheader()
            
            for row in all_rows:
                ein = row.get("EIN")
                year_str = row.get("Year")
                pdf_link = ""
                
                if ein and year_str:
                    try:
                        # Check our cache for this specific EIN and Year
                        y = int(year_str)
                        if ein in filing_cache and y in filing_cache[ein]:
                            pdf_link = filing_cache[ein][y]
                            matches_found += 1
                    except ValueError: pass
                
                row["990_PDF_URL"] = pdf_link
                writer.writerow(row)
                
        print("---------------------------------------------------------")
        print(f"Done! Output saved to: {OUTPUT_FILE}")
        print(f"Matched {matches_found} links out of {len(all_rows)} rows.")

    except Exception as e:
        print(f"Error writing output: {e}")

if __name__ == "__main__":
    main()