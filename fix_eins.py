import csv
import requests
import time
import os
import sys

# --- Constants ---
INPUT_FILE = "unique_eins_open_closed_v2_longitudinal_2000_2018.csv"
OUTPUT_FILE = "unique_eins_corrected.csv"
BASE_PATH = r"c:\Users\terre\Documents\Victor Dissertation Project - Gemini\pdf download 990"
SEARCH_API_URL = "https://projects.propublica.org/nonprofits/api/v2/search.json"

# Headers to mimic a browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

def search_ein_by_name(name):
    """
    Searches ProPublica for the organization name and returns the top EIN result.
    """
    if not name:
        return None, None
        
    params = {"q": name}
    try:
        response = requests.get(SEARCH_API_URL, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        organizations = data.get('organizations', [])
        if organizations:
            # Return the first (best) match
            top_match = organizations[0]
            return top_match.get('ein'), top_match.get('name')
            
        return None, None
    except requests.exceptions.RequestException as e:
        print(f"  Error searching for '{name}': {e}")
        return None, None

def main():
    print("---------------------------------------------------------")
    print("Starting EIN Correction Process")
    
    input_path = os.path.join(BASE_PATH, INPUT_FILE)
    output_path = os.path.join(BASE_PATH, OUTPUT_FILE)

    print(f"Input File: {input_path}")
    
    # 1. Read unique institutions from input
    unique_institutions = {} # Name -> Original EIN
    all_rows = []
    input_fieldnames = []

    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return

    print("Reading input CSV...")
    try:
        with open(input_path, mode='r', newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            input_fieldnames = reader.fieldnames
            
            for row in reader:
                all_rows.append(row)
                name = row.get("Institution Name")
                ein = row.get("EIN")
                if name:
                    unique_institutions[name] = ein
                    
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    print(f"Found {len(unique_institutions)} unique institutions.")

    # 2. Build Correction Map
    # Map[Name] = Corrected_EIN
    correction_map = {}
    
    sorted_names = sorted(list(unique_institutions.keys()))
    total_names = len(sorted_names)
    
    print("\n--- Searching ProPublica for Correct EINs ---")
    
    for i, name in enumerate(sorted_names, 1):
        sys.stdout.write(f"\rProcessing [{i}/{total_names}]: {name[:40]:<40}")
        sys.stdout.flush()
        
        # Search API
        new_ein, found_name = search_ein_by_name(name)
        
        if new_ein:
            correction_map[name] = {"ein": new_ein, "found_name": found_name}
        else:
            # Keep original if not found
            correction_map[name] = {"ein": unique_institutions[name], "found_name": "NOT_FOUND"}
            
        # Rate limit
        time.sleep(0.2)
        
    print(f"\n\nFinished searching for {total_names} institutions.")

    # 3. Create Corrected CSV
    print("Writing corrected dataset...")
    
    output_fieldnames = list(input_fieldnames)
    if "Corrected_EIN" not in output_fieldnames:
        output_fieldnames.insert(1, "Corrected_EIN") # Insert after EIN usually
    if "ProPublica_Name" not in output_fieldnames:
        output_fieldnames.append("ProPublica_Name")

    try:
        with open(output_path, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=output_fieldnames)
            writer.writeheader()
            
            for row in all_rows:
                name = row.get("Institution Name")
                orig_ein = row.get("EIN")
                
                # Get corrected data
                if name in correction_map:
                    corrected_data = correction_map[name]
                    row["Corrected_EIN"] = corrected_data["ein"]
                    row["ProPublica_Name"] = corrected_data["found_name"]
                else:
                    row["Corrected_EIN"] = orig_ein
                    row["ProPublica_Name"] = ""
                
                writer.writerow(row)
                
        print("---------------------------------------------------------")
        print(f"Done! Corrected file saved to: {OUTPUT_FILE}")
        print(f"Full path: {output_path}")

    except Exception as e:
        print(f"Error writing output CSV: {e}")

if __name__ == "__main__":
    main()
