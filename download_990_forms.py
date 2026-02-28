import requests
import os
import time

# --- Configuration ---
# 1. Edit this list with the EINs you want to process.
#    EINs should be strings (e.g., "042103580").
#    You can find EINs on ProPublica or Charity Navigator.
EIN_LIST = [
    "010215213",  # Example: MIT
    
    # "135600077",  # Example: Cornell (Uncomment to add)
] 

# 2. Set the range of tax years you are interested in.
START_YEAR = 2000
END_YEAR = 2018

# 3. Base directory for downloads
DOWNLOAD_DIR = "downloaded_990s"

# ProPublica API Base URL
API_BASE_URL = "https://projects.propublica.org/nonprofits/api/v2/organizations"

# Headers to mimic a browser/legitimate client
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

def get_filings(ein):
    """
    Queries the ProPublica Nonprofits API for an organization's filings.
    """
    url = f"{API_BASE_URL}/{ein}.json"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status() 
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for EIN {ein}: {e}")
        return None

def download_file(url, folder, filename):
    """
    Downloads a file from a URL and saves it to a specified folder.
    """
    if not url:
        return

    filepath = os.path.join(folder, filename)
    
    # Create valid directory structure if it doesn't exist
    if not os.path.exists(folder):
        os.makedirs(folder)

    # Skip if file already exists
    if os.path.exists(filepath):
        print(f"  Skipping {filename} (already exists)")
        return

    try:
        print(f"  Downloading {filename}...")
        response = requests.get(url, headers=HEADERS, stream=True)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"  Saved to {filepath}")
        return True # Success
    except requests.exceptions.RequestException as e:
        print(f"  Failed to download {url}: {e}")
        return False # Failure

def main():
    print("---------------------------------------------------------")
    print(f"Starting download process for {len(EIN_LIST)} organizations")
    print(f"Target Tax Years: {START_YEAR} to {END_YEAR}")
    print("---------------------------------------------------------")

    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    for ein in EIN_LIST:
        print(f"\nProcessing EIN: {ein}")
        
        # Query API
        data = get_filings(ein)
        
        if not data:
            continue
            
        # The organization name is useful for context
        org = data.get('organization', {})
        org_name = org.get('name', 'Unknown Org')
        print(f"Organization: {org_name}")
        
        # Combine lists from the API response
        # filings_with_data = processed returns (usually XML based, newer)
        # filings_without_data = raw PDF scans (older)
        filings = data.get('filings_with_data', []) + data.get('filings_without_data', [])
        
        if not filings:
            print("  No filings found.")
            continue

        download_count = 0
        
        for filing in filings:
            tax_year_val = filing.get('tax_prd_yr')
            pdf_url = filing.get('pdf_url')
            
            # Basic validation
            if not tax_year_val or not pdf_url:
                continue
                
            try:
                tax_year = int(tax_year_val)
            except ValueError:
                continue

            # Check year range
            if START_YEAR <= tax_year <= END_YEAR:
                form_type = filing.get('formtype_str', 'Unknown')
                
                # Attempt to infer form type from URL if unknown
                if form_type == 'Unknown' and pdf_url:
                    if '_990_' in pdf_url:
                        form_type = '990'
                    elif '_990EZ_' in pdf_url:
                        form_type = '990EZ'
                    elif '_990PF_' in pdf_url:
                        form_type = '990PF'
                
                # Sanitize filename
                form_type = form_type.replace('/', '_')
                
                # Use tax_prd_id for uniqueness (handles amended returns)
                filing_id = filing.get('tax_prd_id', '') 
                
                # Construct filename: {Year}_Form{form_type}_{ID}.pdf
                # Example: 2012_Form990_123456789.pdf
                filename = f"{tax_year}_Form{form_type}"
                if filing_id:
                    filename += f"_{filing_id}"
                filename += ".pdf"
                
                # Filings are grouped by EIN folder
                ein_folder = os.path.join(DOWNLOAD_DIR, ein)
                
                if download_file(pdf_url, ein_folder, filename):
                    download_count += 1
                    # Be polite to the server
                    time.sleep(1)
        
        print(f"Finished {ein}. Downloaded {download_count} files.")
        
        # Delay between organizations
        time.sleep(1)

    print("\nAll operations complete.")

if __name__ == "__main__":
    main()
