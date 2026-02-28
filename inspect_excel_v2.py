import pandas as pd
import numpy as np

file_path = r'c:\Users\terre\Documents\Victor Dissertation Project - Gemini\pdf download 990\single_university_summary.xlsx'

try:
    df = pd.read_excel(file_path)
    
    # Filter for successful rows (where 'Total_Assets' is not null)
    successful_rows = df[df['Total_Assets'].notnull()]
    
    print(f"Found {len(successful_rows)} successful rows.")
    
    print("\nDetailed Description of Successful Rows:")
    for index, row in successful_rows.iterrows():
        print(f"\n--- Row {index} ---")
        for col in df.columns:
            print(f"  {col}: {row[col]}")

    # specific checks for anomalies
    print("\nAnomaly Checks on Successful Rows:")
    for index, row in successful_rows.iterrows():
        issues = []
        
        # Check basic accounting equation: Assets = Liabilities + Net Assets
        # Net Assets = Assets - Liabilities
        calculated_net_assets = row['Total_Assets'] - row['Total_Liabilities']
        reported_net_assets = row['Total_Net_Assets']
        
        if not pd.isna(row['Total_Assets']) and not pd.isna(row['Total_Liabilities']):
             if abs(reported_net_assets - calculated_net_assets) > 1000.0: # allow some leeway for rounding errors
                diff = reported_net_assets - calculated_net_assets
                issues.append(f"Net Assets mismatch: Reported {reported_net_assets} vs Calc {calculated_net_assets} (Diff: {diff})")

        # Check for negative values where unexpected
        if row['Total_Assets'] < 0:
            issues.append(f"Total_Assets is negative: {row['Total_Assets']}")
        if row['Total_Liabilities'] < 0:
            issues.append(f"Total_Liabilities is negative: {row['Total_Liabilities']}")
        if row['Total_Expenses'] < 0:
            issues.append(f"Total_Expenses is negative: {row['Total_Expenses']}")

        if not issues:
            print(f"Row {index}: No obvious anomalies found.")
        else:
            print(f"Row {index}: Anomalies found:")
            for issue in issues:
                print(f"  - {issue}")

    # Inspect errors
    print("\nError Summary:")
    error_rows = df[df['error'].notnull()]
    print(error_rows[['filename', 'error']])

except Exception as e:
    print(f"Error: {e}")
