import csv
import requests
import os
import time

# --- Configuration ---
INPUT_FILE = "unique_eins_with_pdf_links_v2.csv"
BASE_PATH = r"c:\Users\terre\Documents\Victor Dissertation Project - Gemini\pdf download 990"
DOWNLOAD_DIR = "downloaded_990s_v2"

# Headers to mimic a browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

def download_file(url, folder, filename):
    """
    Downloads a file from a URL and saves it to a specified folder.
    """
    if not url:
        return False

    filepath = os.path.join(folder, filename)
    
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)

    if os.path.exists(filepath):
        # We check file size to ensure it's not a failed/empty download
        if os.path.getsize(filepath) > 0:
            return "exists"

    try:
        response = requests.get(url, headers=HEADERS, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"\n      Error downloading {url}: {e}")
        return False

def main():
    print("---------------------------------------------------------")
    print("Starting Bulk 990 PDF Downloader (v2)")
    
    input_path = os.path.join(BASE_PATH, INPUT_FILE)
    output_base_dir = os.path.join(BASE_PATH, DOWNLOAD_DIR)

    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return

    if not os.path.exists(output_base_dir):
        os.makedirs(output_base_dir, exist_ok=True)

    rows_to_process = []
    print(f"Reading {INPUT_FILE}...")
    with open(input_path, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Only process rows that actually have a URL
            if row.get("990_PDF_URL") and row["990_PDF_URL"].strip():
                rows_to_process.append(row)

    total = len(rows_to_process)
    print(f"Found {total} rows with PDF links. Starting downloads...")
    print("---------------------------------------------------------")

    success_count = 0
    skipped_count = 0
    error_count = 0

    for i, row in enumerate(rows_to_process, 1):
        ein = row.get("Corrected_EIN") or row.get("EIN")
        year = row.get("Year")
        inst_name = row.get("Institution Name", "Unknown").replace(" ", "_").replace("/", "_")[:30]
        url = row["990_PDF_URL"]
        
        # Sanitize folder name
        safe_name = "".join([c for c in inst_name if c.isalnum() or c == '_'])
        folder = os.path.join(output_base_dir, f"{ein}_{safe_name}")
        
        # Determine filename
        # ProPublica URLs usually end in .pdf or have a unique ID
        file_id = url.split("/")[-1].split("?")[0]
        if not file_id.endswith(".pdf"):
            file_id += ".pdf"
        filename = f"{year}_{file_id}"

        # Progress update
        print(f"[{i}/{total}] {ein} ({year}) - {inst_name}...", end="", flush=True)

        result = download_file(url, folder, filename)
        
        if result == True:
            print(" DONE")
            success_count += 1
            time.sleep(0.5) # Polite delay
        elif result == "exists":
            print(" SKIPPED (Exists)")
            skipped_count += 1
        else:
            print(" FAILED")
            error_count += 1

    print("\n---------------------------------------------------------")
    print("Download Complete!")
    print(f"Successfully Downloaded: {success_count}")
    print(f"Already Existed: {skipped_count}")
    print(f"Failed: {error_count}")
    print(f"Files saved in: {output_base_dir}")
    print("---------------------------------------------------------")

if __name__ == "__main__":
    main()
