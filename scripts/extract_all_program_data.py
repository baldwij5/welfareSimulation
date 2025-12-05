"""
Extract Calibration Data - All Programs

Extracts and processes:
- TANF: Families → Adults conversion
- SNAP: Persons (direct match)
- SSI: Persons (direct match)

Handles unit mismatches and creates calibration targets.

Run with: python scripts/extract_all_program_data.py
"""

import pandas as pd
import numpy as np
import sys
sys.path.insert(0, 'src')

from data.data_loader import load_acs_county_data


def extract_tanf_state_data(filepath):
    """
    Extract TANF families and recipients by state.
    
    Returns:
        DataFrame: State-level TANF data with family→adult conversion
    """
    print("\n" + "="*70)
    print("EXTRACTING TANF DATA")
    print("="*70)
    
    # Read with proper header row
    df = pd.read_excel(filepath, sheet_name='FYCY2022-Families', skiprows=3)
    
    # Get column names from row 0
    df.columns = ['State', 'Total_Families', 'Two_Parent', 'One_Parent', 'No_Parent',
                  'Total_Recipients', 'Adults', 'Children', 'Two_Parent_Rec',
                  'One_Parent_Rec', 'No_Parent_Rec']
    
    # Remove header rows and totals
    df_clean = df[df['State'].notna()].copy()
    df_clean = df_clean[~df_clean['State'].str.contains('U.S. Totals|State', na=False)]
    
    # Convert to numeric
    for col in df_clean.columns[1:]:
        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
    
    # UNIT CONVERSION: Families → Adults
    # Method 1: Use Adults column directly (if available)
    df_clean['TANF_Adults'] = df_clean['Adults']
    
    # Method 2: Estimate from families (backup)
    # Typical TANF: 1.2 adults per family (mostly single-parent)
    df_clean['TANF_Adults_Estimated'] = df_clean['Total_Families'] * 1.2
    
    # Use actual if available, otherwise estimate
    df_clean['TANF_Adults_Final'] = df_clean['TANF_Adults'].fillna(
        df_clean['TANF_Adults_Estimated']
    )
    
    print(f"\nExtracted {len(df_clean)} states")
    print(f"\nSample (first 10 states):")
    print(df_clean[['State', 'Total_Families', 'TANF_Adults', 'TANF_Adults_Final']].head(10))
    
    print(f"\nMassachusetts:")
    ma = df_clean[df_clean['State'].str.contains('Massachusetts', na=False)]
    if len(ma) > 0:
        print(f"  Families: {ma['Total_Families'].values[0]:,.0f}")
        print(f"  Adults (direct): {ma['TANF_Adults'].values[0]:,.0f}")
        print(f"  Adults (estimated): {ma['TANF_Adults_Estimated'].values[0]:,.0f}")
        print(f"  → Use for calibration: {ma['TANF_Adults_Final'].values[0]:,.0f} adults")
    
    return df_clean[['State', 'Total_Families', 'TANF_Adults_Final']].copy()


def extract_snap_state_data(filepath):
    """
    Extract SNAP persons by state.
    
    SNAP counts PERSONS (not households) - direct match to seekers!
    
    Returns:
        DataFrame: State-level SNAP persons
    """
    print("\n" + "="*70)
    print("EXTRACTING SNAP DATA")
    print("="*70)
    
    print("\n⚠️  FY22.xlsx appears to have regional, not state-level data")
    print("   Would need different data source for state breakdowns")
    print("   Or can use national average as reference")
    
    # From US Summary
    try:
        df = pd.read_excel(filepath, sheet_name='US Summary', skiprows=6)
        
        # Get October 2021 - September 2022 average
        persons_cols = [col for col in df.columns if 'Persons' in str(col)]
        if len(persons_cols) > 0:
            persons = df[persons_cols[0]].iloc[:12]  # First 12 months
            persons_numeric = pd.to_numeric(persons, errors='coerce')
            avg_persons = persons_numeric.mean()
            
            print(f"\nNational SNAP (FY2022):")
            print(f"  Average persons enrolled: {avg_persons:,.0f} (in millions)")
            print(f"  This is: {avg_persons * 1000000:,.0f} individuals")
            
            return pd.DataFrame({
                'State': ['United States'],
                'SNAP_Persons': [avg_persons * 1000000]
            })
    except Exception as e:
        print(f"Error: {e}")
    
    return None


def extract_ssi_state_data(filepath):
    """
    Extract SSI recipients by state.
    
    SSI counts PERSONS - direct match to seekers!
    
    Returns:
        DataFrame: State-level SSI persons
    """
    print("\n" + "="*70)
    print("EXTRACTING SSI DATA")
    print("="*70)
    
    # SSI data appears to be national totals in these tables
    # Would need different table for state breakdowns
    
    try:
        # Try Table 3 (recipients by year)
        df = pd.read_excel(filepath, sheet_name='Table 3', skiprows=2)
        
        # Get 2022 data
        df_2022 = df[df.iloc[:, 0] == 2022]
        
        if len(df_2022) > 0:
            total_col = df_2022.columns[1]
            total_recipients = pd.to_numeric(df_2022[total_col].values[0], errors='coerce')
            
            print(f"\nNational SSI (2022):")
            print(f"  Total recipients: {total_recipients:,.0f} persons")
            
            return pd.DataFrame({
                'State': ['United States'],
                'SSI_Persons': [total_recipients]
            })
    except Exception as e:
        print(f"Error: {e}")
    
    return None


def combine_with_acs(tanf_data, snap_data, ssi_data, acs_filepath):
    """
    Combine program data with ACS to calculate participation rates.
    
    Returns:
        DataFrame: State-level calibration targets
    """
    print("\n" + "="*70)
    print("COMBINING WITH ACS DATA")
    print("="*70)
    
    # Load ACS
    acs = load_acs_county_data(acs_filepath)
    acs['state'] = acs['county_name'].str.split(', ').str[1]
    
    # Aggregate to state level
    state_acs = acs.groupby('state').agg({
        'total_county_population': 'sum',
        'poverty_rate': 'mean',  # Population-weighted would be better
        'black_pct': 'mean',
        'hispanic_pct': 'mean'
    }).reset_index()
    
    # Estimate eligible populations
    # TANF: Families with children below poverty
    # Rough estimate: 40% of poverty population has children
    state_acs['tanf_eligible_adults'] = (
        state_acs['total_county_population'] * 
        (state_acs['poverty_rate'] / 100) * 
        0.40  # Has children multiplier
    )
    
    # SNAP: Income < 130% poverty (broader than TANF)
    # Our simulation: income < $30k ≈ 41.7% of working-age
    state_acs['snap_eligible'] = state_acs['total_county_population'] * 0.417
    
    # Merge with program data
    if tanf_data is not None:
        calibration = state_acs.merge(
            tanf_data, 
            left_on='state', 
            right_on='State', 
            how='left'
        )
        
        # Calculate participation rates
        calibration['tanf_participation_rate'] = (
            calibration['TANF_Adults_Final'] / calibration['tanf_eligible_adults']
        )
        
        print(f"\nTANF Participation Rates (sample):")
        print(calibration[['state', 'TANF_Adults_Final', 'tanf_eligible_adults', 
                          'tanf_participation_rate']].head(10))
        
        return calibration
    
    return state_acs


def create_calibration_targets(calibration_df):
    """
    Create calibration targets for simulation.
    
    Returns:
        dict: Targets by state
    """
    print("\n" + "="*70)
    print("CALIBRATION TARGETS")
    print("="*70)
    
    targets = {}
    
    for _, row in calibration_df.iterrows():
        state = row['state']
        
        if pd.notna(row.get('TANF_Adults_Final')):
            targets[state] = {
                'tanf_enrolled_adults': row['TANF_Adults_Final'],
                'tanf_eligible_adults': row['tanf_eligible_adults'],
                'tanf_participation_rate': row.get('tanf_participation_rate', None),
                'total_population': row['total_county_population']
            }
    
    # Show Massachusetts
    if 'Massachusetts' in targets:
        print(f"\nMassachusetts Calibration Targets:")
        ma = targets['Massachusetts']
        print(f"  TANF adults enrolled: {ma['tanf_enrolled_adults']:,.0f}")
        print(f"  TANF eligible (estimated): {ma['tanf_eligible_adults']:,.0f}")
        print(f"  Participation rate: {ma['tanf_participation_rate']:.1%}")
        print(f"\n  → Simulation should produce ~{ma['tanf_enrolled_adults']:,.0f} TANF adults")
        print(f"  → From ~{ma['tanf_eligible_adults']:,.0f} eligible adults")
    
    return targets


def main():
    """Extract all program data for calibration."""
    print("\n" + "="*70)
    print("EXTRACT CALIBRATION DATA - ALL PROGRAMS")
    print("="*70)
    
    print("\nObjective: Extract real enrollment to calibrate simulation")
    print("\nHandling unit mismatches:")
    print("  TANF: Families → Adults (multiply by 1.2)")
    print("  SNAP: Persons (direct match)")
    print("  SSI: Persons (direct match)")
    
    # Extract TANF
    tanf = extract_tanf_state_data('data/uploads/fy2022_tanf_caseload.xlsx')
    
    # Extract SNAP
    snap = extract_snap_state_data('data/uploads/FY22.xlsx')
    
    # Extract SSI
    ssi = extract_ssi_state_data('data/uploads/ssi_asr23.xlsx')
    
    # Combine with ACS
    calibration = combine_with_acs(
        tanf, snap, ssi,
        'src/data/us_census_acs_2022_county_data.csv'
    )
    
    # Create targets
    targets = create_calibration_targets(calibration)
    
    # Save
    import os
    os.makedirs('data', exist_ok=True)
    
    if calibration is not None:
        calibration.to_csv('data/calibration_targets.csv', index=False)
        print(f"\n✓ Saved: data/calibration_targets.csv")
    
    print("\n" + "="*70)
    print("NEXT STEPS")
    print("="*70)
    
    print("\n1. Use these targets to calibrate:")
    print("   - Seeker count (to produce realistic applications)")
    print("   - Capacity (to produce realistic enrollment)")
    
    print("\n2. For Massachusetts:")
    print("   - Should simulate ~38,000 TANF-eligible adults")
    print("   - Capacity calibrated so ~38,000 end up enrolled")
    print("   - This matches real 31,967 families (× 1.2 adults/family)")
    
    print("\n3. Re-run Monte Carlo with calibrated parameters")
    print("   - See if -2.15pp effect persists")


if __name__ == "__main__":
    main()