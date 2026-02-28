import pandas as pd

file_path = r'c:\Users\terre\Documents\Victor Dissertation Project - Gemini\pdf download 990\single_university_summary.xlsx'

try:
    df = pd.read_excel(file_path)
    print("DataFrame Head:")
    print(df.head())
    print("\nDataFrame Info:")
    print(df.info())
    print("\nMissing Values:")
    print(df.isnull().sum())
    
    # Check for "2 successful rows" as requested
    if len(df) >= 2:
        print("\nChecking the first 2 rows for anomalies:")
        print(df.iloc[:2])
    else:
        print(f"\nThe dataframe has only {len(df)} rows.")

except Exception as e:
    print(f"Error reading excel file: {e}")
