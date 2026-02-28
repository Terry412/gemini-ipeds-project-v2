import csv
import requests
import time
import os
import sys

# --- Constants ---
INPUT_FILE = "unique_eins_corrected.csv"
OUTPUT_FILE = "unique_eins_with_pdf_links_v2.csv"
BASE_PATH = r"c:\Users\terre\Documents\Victor Dissertation Project - Gemini\pdf download 990"
API_BASE_URL = "https://projects.propublica.org/nonprofits/api/v2/organizations"

# Headers to mimic a browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

def get_filings(ein):
    """
    Queries the ProPublica Nonprofits API for an organization's filings.
    """
    if not ein:
        return None
        
    url = f"{API_BASE_URL}/{ein}.json"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        # If 404, it just means no data for this EIN, return None
        if response.status_code == 404:
            return None
            
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

def main():
    print("---------------------------------------------------------")
    print("Starting PDF Link Matching Process (v2 - Corrected EINs)")
    
    input_path = os.path.join(BASE_PATH, INPUT_FILE)
    output_path = os.path.join(BASE_PATH, OUTPUT_FILE)

    print(f"Input File: {input_path}")
    print("---------------------------------------------------------")

    # 1. Read the input CSV
    print("Reading input CSV...")
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return

    all_rows = []
    unique_corrected_eins = set()
    input_fieldnames = []

    try:
        # Use utf-8-sig to handle potential BOM
        with open(input_path, mode='r', newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            input_fieldnames = reader.fieldnames
            if not input_fieldnames:
                print("Error: Empty CSV or no headers found.")
                return
            
            # Store all rows
            for row in reader:
                all_rows.append(row)
                cein = row.get("Corrected_EIN")
                if cein:
                    unique_corrected_eins.add(cein)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    print(f"Found {len(all_rows)} total rows.")
    print(f"Found {len(unique_corrected_eins)} unique Corrected EINs to process.")

    # 2. Build Filing Cache
    # Structure: filing_cache[Corrected_EIN] = { 2012: "url", 2013: "url" }
    filing_cache = {}
    
    sorted_eins = sorted(list(unique_corrected_eins))
    total_eins = len(sorted_eins)
    
    print("\n--- Fetching Data from ProPublica ---")
    
    for i, ein in enumerate(sorted_eins, 1):
        # Progress indicator
        sys.stdout.write(f"\rProcessing EIN [{i}/{total_eins}]: {ein}     ")
        sys.stdout.flush()
        
        # Clean EIN (remove dashes)
        clean_ein = str(ein).replace("-", "").strip()
        
        # Initialize cache entry for this EIN
        if ein not in filing_cache:
            filing_cache[ein] = {}
        
        data = get_filings(clean_ein)
        
        if data:
            # Combined list of filings (with and without data)
            filings_with = data.get('filings_with_data', []) or []
            filings_without = data.get('filings_without_data', []) or []
            all_filings = filings_with + filings_without
            
            for filing in all_filings:
                # We need the tax year and the PDF url
                tax_year_val = filing.get('tax_prd_yr')
                pdf_url = filing.get('pdf_url')
                
                if tax_year_val and pdf_url:
                    try:
                        year = int(tax_year_val)
                        if year not in filing_cache[ein]:
                            filing_cache[ein][year] = pdf_url
                    except ValueError:
                        pass
        
        # Rate limit
        time.sleep(0.2)
    
    print(f"\n\nFinished fetching data for {total_eins} EINs.")

    # 3. Match and Write Output
    print("Matching rows and writing output...")
    
    output_fieldnames = list(input_fieldnames)
    if "990_PDF_URL" not in output_fieldnames:
        output_fieldnames.append("990_PDF_URL")
    
    matches_found = 0
    
    try:
        with open(output_path, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=output_fieldnames)
            writer.writeheader()
            
            for row in all_rows:
                # Get the Corrected EIN and Year from the row
                cein = row.get("Corrected_EIN")
                year_str = row.get("Year") 
                
                pdf_link = ""
                
                if cein and year_str:
                    try:
                        year = int(year_str)
                        if cein in filing_cache and year in filing_cache[cein]:
                            pdf_link = filing_cache[cein][year]
                    except ValueError:
                        pass 
                
                if pdf_link:
                    matches_found += 1
                
                row["990_PDF_URL"] = pdf_link
                writer.writerow(row)
                
    except Exception as e:
        print(f"Error writing output CSV: {e}")
        return

    # 4. Summary
    coverage = (matches_found / len(all_rows) * 100) if len(all_rows) > 0 else 0
    
    print("\n---------------------------------------------------------")
    print(f"Done! Output saved to: {OUTPUT_FILE}")
    print(f"Rows Matched: {matches_found} / {len(all_rows)}")
    print(f"Coverage: {coverage:.2f}%")
    print(f"Full path: {output_path}")
    print("---------------------------------------------------------")

if __name__ == "__main__":
    main()
