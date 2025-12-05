"""
Extract Calibration Data from Administrative Files

Extracts state-level participation and caseload data from:
- FY22.xlsx (SNAP)
- fy2022_tanf_caseload.xlsx (TANF)  
- ssi_asr23.xlsx (SSI)

Run with: python scripts/extract_calibration_data.py
"""

import pandas as pd
import numpy as np


def extract_snap_data(filepath):
    """
    Extract SNAP participation data from FY22.xlsx.
    
    Returns:
        DataFrame: State-level SNAP data
    """
    print("\n" + "="*70)
    print("EXTRACTING SNAP DATA")
    print("="*70)
    
    # The file has regional sheets, we need state-level data
    # Try to find state summary or parse from regional sheets
    
    try:
        # Check if there's a state-level sheet
        xls = pd.ExcelFile(filepath)
        print(f"\nAvailable sheets: {xls.sheet_names}")
        
        # US Summary has national totals
        us_summary = pd.read_excel(filepath, sheet_name='US Summary', skiprows=6)
        print(f"\nUS Summary shape: {us_summary.shape}")
        print(us_summary.head())
        
        # Would need to explore regional sheets for state breakdowns
        print("\n⚠️  SNAP data appears to be monthly national totals")
        print("   State-level data may be in regional sheets (NERO, MARO, etc.)")
        print("   Would need manual extraction or different data source")
        
        return None
        
    except Exception as e:
        print(f"Error: {e}")
        return None


def extract_tanf_data(filepath):
    """
    Extract TANF caseload data.
    
    Returns:
        DataFrame: State-level TANF data
    """
    print("\n" + "="*70)
    print("EXTRACTING TANF DATA")
    print("="*70)
    
    try:
        xls = pd.ExcelFile(filepath)
        print(f"\nSheets: {xls.sheet_names[:10]}")
        
        # Try FYCY2022-Families (fiscal year summary)
        df = pd.read_excel(filepath, sheet_name='FYCY2022-Families')
        print(f"\nFYCY2022-Families shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()}")
        print("\nFirst 15 rows:")
        print(df.head(15))
        
        return df
        
    except Exception as e:
        print(f"Error: {e}")
        return None


def extract_ssi_data(filepath):
    """
    Extract SSI recipient data.
    
    Returns:
        DataFrame: SSI data
    """
    print("\n" + "="*70)
    print("EXTRACTING SSI DATA")
    print("="*70)
    
    try:
        xls = pd.ExcelFile(filepath)
        
        # Try different tables
        for table in ['Table 2', 'Table 3', 'Table 5']:
            print(f"\n{table}:")
            df = pd.read_excel(filepath, sheet_name=table)
            print(f"  Shape: {df.shape}")
            print(f"  First few rows:")
            print(df.head(10))
        
        return None
        
    except Exception as e:
        print(f"Error: {e}")
        return None


def main():
    """Extract all calibration data."""
    print("\n" + "="*70)
    print("ADMINISTRATIVE DATA EXTRACTION")
    print("="*70)
    
    print("\nPurpose: Extract real program participation data")
    print("for capacity calibration")
    
    # Extract SNAP
    snap_data = extract_snap_data('data/uploads/FY22.xlsx')
    
    # Extract TANF  
    tanf_data = extract_tanf_data('data/uploads/fy2022_tanf_caseload.xlsx')
    
    # Extract SSI
    ssi_data = extract_ssi_data('data/uploads/ssi_asr23.xlsx')
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    print("\nThese files contain:")
    print("  ✓ SNAP: Monthly participation (appears to be national/regional)")
    print("  ✓ TANF: Caseload by state")
    print("  ✓ SSI: Annual statistical report")
    
    print("\nNext steps:")
    print("  1. Identify which tables have state-level data")
    print("  2. Extract participation/approval rates by state")
    print("  3. Use for capacity calibration")
    
    print("\nKey metrics we need:")
    print("  - Applications per month (by state/county)")
    print("  - Approval rates (% approved)")
    print("  - Participants (enrolled)")
    print("  - Eligible population (for participation rate)")


if __name__ == "__main__":
    main()