"""
State-Level Multi-Program Calibration Data Extraction

Extracts real enrollment for ALL 50 states across all 3 programs:
- TANF: Adults from Recipients sheet
- SNAP: Persons from regional sheets  
- SSI: Persons from Table 31

Creates calibration targets for each state.

Run with: python scripts/extract_state_calibration.py
"""

import pandas as pd
import numpy as np
import sys
sys.path.insert(0, 'src')

from data.data_loader import load_acs_county_data


def extract_tanf_all_states(filepath):
    """
    Extract TANF adult recipients for all states.
    
    Returns:
        DataFrame: State, TANF_Adults
    """
    print("\n" + "="*70)
    print("EXTRACTING TANF ADULTS (ALL STATES)")
    print("="*70)
    
    # Read Recipients sheet (has adults column)
    df = pd.read_excel(filepath, sheet_name='FYCY2022-Recipients', skiprows=3)
    
    # Clean columns
    df.columns = ['State', 'Total_Recipients', 'Adults', 'Children',
                  'Two_Parent_Rec', 'CY_Total', 'CY_Adults', 'CY_Children', 'CY_Other']
    
    # Remove totals and clean
    df_clean = df[df['State'].notna()].copy()
    df_clean = df_clean[~df_clean['State'].astype(str).str.contains('U.S. Totals|State', na=False)]
    
    # Convert to numeric
    df_clean['Adults'] = pd.to_numeric(df_clean['Adults'], errors='coerce')
    df_clean['Total_Recipients'] = pd.to_numeric(df_clean['Total_Recipients'], errors='coerce')
    df_clean['Children'] = pd.to_numeric(df_clean['Children'], errors='coerce')
    
    # Clean state names
    df_clean['State'] = df_clean['State'].str.strip()
    
    result = df_clean[['State', 'Adults', 'Total_Recipients', 'Children']].copy()
    result.columns = ['State', 'TANF_Adults', 'TANF_Total_Recipients', 'TANF_Children']
    
    print(f"\n✓ Extracted TANF data for {len(result)} states")
    print(f"\nSample:")
    print(result[['State', 'TANF_Adults']].head(10))
    
    print(f"\nMassachusetts: {result[result['State']=='Massachusetts']['TANF_Adults'].values[0]:,.0f} adults")
    
    return result


def extract_snap_all_states(filepath):
    """
    Extract SNAP persons for all states from regional sheets.
    
    Regional sheets:
    - NERO: Northeast
    - MARO: Mid-Atlantic  
    - SERO: Southeast
    - MWRO: Midwest
    - SWRO: Southwest
    - MPRO: Mountain Plains
    - WRO: Western
    
    Returns:
        DataFrame: State, SNAP_Persons
    """
    print("\n" + "="*70)
    print("EXTRACTING SNAP PERSONS (ALL STATES)")
    print("="*70)
    
    regional_sheets = ['NERO', 'MARO', 'SERO', 'MWRO', 'SWRO', 'MPRO', 'WRO']
    
    all_states = []
    
    for region in regional_sheets:
        print(f"\nProcessing {region}...")
        
        try:
            df = pd.read_excel(filepath, sheet_name=region, skiprows=6)
            
            # Find state sections (state name followed by 12 months)
            state_indices = []
            for i, val in enumerate(df.iloc[:, 0]):
                if pd.notna(val) and isinstance(val, str):
                    # Check if next rows have month names
                    if i+1 < len(df) and 'Oct' in str(df.iloc[i+1, 0]):
                        state_indices.append((i, val))
            
            # Extract data for each state
            for idx, state_name in state_indices:
                # Get 12 months of persons data (last column)
                months = df.iloc[idx+1:idx+13, -1]
                months_numeric = pd.to_numeric(months, errors='coerce')
                
                if months_numeric.notna().sum() > 0:
                    avg_persons_thousands = months_numeric.mean()
                    avg_persons = avg_persons_thousands * 1000
                    
                    all_states.append({
                        'State': state_name.strip(),
                        'SNAP_Persons': avg_persons,
                        'Region': region
                    })
            
            print(f"  Found {len(state_indices)} states")
            
        except Exception as e:
            print(f"  Error: {e}")
    
    snap_df = pd.DataFrame(all_states)
    
    print(f"\n✓ Extracted SNAP data for {len(snap_df)} states")
    print(f"\nSample:")
    print(snap_df[['State', 'SNAP_Persons']].head(10))
    
    if len(snap_df[snap_df['State']=='Massachusetts']) > 0:
        ma_snap = snap_df[snap_df['State']=='Massachusetts']['SNAP_Persons'].values[0]
        print(f"\nMassachusetts: {ma_snap:,.0f} persons")
    
    return snap_df


def extract_ssi_all_states(filepath):
    """
    Extract SSI recipients for all states from Table 31.
    
    Table 31: Noncitizens by state
    But has Total column with all recipients!
    
    Returns:
        DataFrame: State, SSI_Persons
    """
    print("\n" + "="*70)
    print("EXTRACTING SSI PERSONS (ALL STATES)")
    print("="*70)
    
    # Read Table 31
    df = pd.read_excel(filepath, sheet_name='Table 31', skiprows=2)
    
    # Columns appear to be: State, ???, ???, Total, ...
    # Need to identify Total column
    
    print(f"Table structure:")
    print(df.head(5))
    
    # Clean
    df_clean = df.copy()
    df_clean.columns = ['State', 'Col1', 'Col2', 'Total', 'Category', 'Col5', 
                        'Age', 'Col7_1925', 'Col8_4367']
    
    # Remove headers
    df_clean = df_clean[df_clean['State'].notna()].copy()
    df_clean = df_clean[~df_clean['State'].astype(str).str.contains('State|area|NaN', na=False)]
    
    # Convert Total to numeric
    df_clean['Total'] = pd.to_numeric(df_clean['Total'], errors='coerce')
    
    # Clean state names
    df_clean['State'] = df_clean['State'].str.strip()
    
    result = df_clean[['State', 'Total']].copy()
    result.columns = ['State', 'SSI_Persons']
    
    # Remove any remaining non-state rows
    result = result[result['SSI_Persons'].notna()].copy()
    
    print(f"\n✓ Extracted SSI data for {len(result)} states")
    print(f"\nSample:")
    print(result.head(10))
    
    if len(result[result['State']=='Massachusetts']) > 0:
        ma_ssi = result[result['State']=='Massachusetts']['SSI_Persons'].values[0]
        print(f"\nMassachusetts: {ma_ssi:,.0f} persons")
        print(f"  (Your number was 1,925 - that's column 7, subset)")
        print(f"  (Total SSI is: {ma_ssi:,.0f})")
    
    return result


def combine_all_programs(tanf_df, snap_df, ssi_df, acs_filepath):
    """
    Combine all program data with ACS for complete calibration targets.
    
    Returns:
        DataFrame: Complete state-level calibration data
    """
    print("\n" + "="*70)
    print("COMBINING ALL PROGRAMS WITH ACS")
    print("="*70)
    
    # Start with TANF (most complete state coverage)
    combined = tanf_df.copy()
    
    # Merge SNAP
    if snap_df is not None:
        combined = combined.merge(snap_df[['State', 'SNAP_Persons']], 
                                 on='State', how='left')
    
    # Merge SSI
    if ssi_df is not None:
        combined = combined.merge(ssi_df[['State', 'SSI_Persons']], 
                                 on='State', how='left')
    
    # Load ACS and aggregate to state
    acs = load_acs_county_data(acs_filepath)
    acs['state'] = acs['county_name'].str.split(', ').str[1]
    
    state_acs = acs.groupby('state').agg({
        'total_county_population': 'sum',
        'poverty_rate': lambda x: np.average(x, weights=acs.loc[x.index, 'total_county_population']),
        'black_pct': lambda x: np.average(x, weights=acs.loc[x.index, 'total_county_population']),
        'median_household_income': 'median'
    }).reset_index()
    
    # Merge with ACS
    combined = combined.merge(state_acs, left_on='State', right_on='state', how='left')
    
    # Calculate eligible populations (estimates)
    # TANF: ~10% of population, has children, low income
    combined['TANF_Eligible_Est'] = combined['total_county_population'] * 0.10
    
    # SNAP: ~20-25% of population (our CPS shows 41.7% of working-age)
    combined['SNAP_Eligible_Est'] = combined['total_county_population'] * 0.25
    
    # SSI: ~3-5% of population (disability-based)
    combined['SSI_Eligible_Est'] = combined['total_county_population'] * 0.04
    
    # Calculate participation rates
    combined['TANF_Participation_Rate'] = combined['TANF_Adults'] / combined['TANF_Eligible_Est']
    combined['SNAP_Participation_Rate'] = combined['SNAP_Persons'] / combined['SNAP_Eligible_Est']
    combined['SSI_Participation_Rate'] = combined['SSI_Persons'] / combined['SSI_Eligible_Est']
    
    # Calculate total seekers needed (working backwards from enrollment)
    # Assume: approval_rate = 0.70, applications_per_seeker = 2.0
    combined['Seekers_Needed_TANF'] = combined['TANF_Adults'] / 0.70 / 2.0
    combined['Seekers_Needed_SNAP'] = combined['SNAP_Persons'] / 0.70 / 2.0
    combined['Seekers_Needed_Total'] = combined[['Seekers_Needed_TANF', 'Seekers_Needed_SNAP']].max(axis=1)
    
    return combined


def create_calibration_summary(combined_df):
    """
    Create summary of calibration targets.
    """
    print("\n" + "="*70)
    print("STATE-LEVEL CALIBRATION TARGETS")
    print("="*70)
    
    print(f"\nExtracted data for {len(combined_df)} states")
    
    # Massachusetts detail
    ma = combined_df[combined_df['State'] == 'Massachusetts']
    
    if len(ma) > 0:
        print("\n" + "="*70)
        print("MASSACHUSETTS CALIBRATION TARGETS")
        print("="*70)
        
        ma = ma.iloc[0]
        
        print(f"\nReal Enrollment (FY2022):")
        print(f"  TANF adults: {ma['TANF_Adults']:,.0f}")
        print(f"  SNAP persons: {ma['SNAP_Persons']:,.0f}")
        print(f"  SSI persons: {ma['SSI_Persons']:,.0f}")
        
        print(f"\nEstimated Eligible:")
        print(f"  TANF: {ma['TANF_Eligible_Est']:,.0f}")
        print(f"  SNAP: {ma['SNAP_Eligible_Est']:,.0f}")
        print(f"  SSI: {ma['SSI_Eligible_Est']:,.0f}")
        
        print(f"\nParticipation Rates:")
        print(f"  TANF: {ma['TANF_Participation_Rate']:.1%}")
        print(f"  SNAP: {ma['SNAP_Participation_Rate']:.1%}")
        print(f"  SSI: {ma['SSI_Participation_Rate']:.1%}")
        
        print(f"\nSeekers Needed (Estimated):")
        print(f"  Based on TANF: {ma['Seekers_Needed_TANF']:,.0f}")
        print(f"  Based on SNAP: {ma['Seekers_Needed_SNAP']:,.0f}")
        print(f"  Recommended: {ma['Seekers_Needed_Total']:,.0f}")
        
        print(f"\n{'='*70}")
        print("CALIBRATION IMPLICATION")
        print(f"{'='*70}")
        
        print(f"\nCurrent MA Monte Carlo used: 1,000 seekers")
        print(f"Calibrated target should be: {ma['Seekers_Needed_Total']:,.0f} seekers")
        print(f"\nRatio: {ma['Seekers_Needed_Total'] / 1000:.1f}× more seekers needed!")
        
        print(f"\nThis explains:")
        print(f"  - Current -2.15pp effect may be")
        print(f"  - Artifact of unrealistic scale")
        print(f"  - OR real effect at current (low) volume")
        print(f"  - Need to test at calibrated scale!")
    
    # Show top 10 states by SNAP enrollment
    print("\n" + "="*70)
    print("TOP 10 STATES BY SNAP ENROLLMENT")
    print("="*70)
    
    top10 = combined_df.nlargest(10, 'SNAP_Persons')[['State', 'SNAP_Persons', 'TANF_Adults', 'SSI_Persons']]
    print(f"\n{top10.to_string()}")
    
    return combined_df


def main():
    """Extract all state-level calibration data."""
    print("\n" + "="*80)
    print("STATE-LEVEL MULTI-PROGRAM CALIBRATION EXTRACTION")
    print("="*80)
    
    print("\nExtracting real enrollment from:")
    print("  1. TANF: Adults from FYCY2022-Recipients")
    print("  2. SNAP: Persons from regional sheets (NERO, MARO, etc.)")
    print("  3. SSI: Persons from Table 31")
    
    # Extract each program
    tanf = extract_tanf_all_states('data/uploads/fy2022_tanf_caseload.xlsx')
    snap = extract_snap_all_states('data/uploads/FY22.xlsx')
    ssi = extract_ssi_all_states('data/uploads/ssi_asr23.xlsx')
    
    # Combine all
    calibration = combine_all_programs(
        tanf, snap, ssi,
        'src/data/us_census_acs_2022_county_data.csv'
    )
    
    # Summary
    summary = create_calibration_summary(calibration)
    
    # Save
    import os
    os.makedirs('data', exist_ok=True)
    
    calibration.to_csv('data/state_calibration_targets.csv', index=False)
    
    print(f"\n{'='*80}")
    print("COMPLETE")
    print(f"{'='*80}")
    
    print(f"\n✓ Saved: data/state_calibration_targets.csv")
    
    print(f"\nThis file contains for each state:")
    print(f"  - Real enrollment (TANF, SNAP, SSI)")
    print(f"  - Estimated eligible populations")
    print(f"  - Participation rates")
    print(f"  - Recommended seeker counts")
    
    print(f"\nUse this to:")
    print(f"  1. Calibrate seeker generation")
    print(f"  2. Calibrate capacity parameters")
    print(f"  3. Re-run Monte Carlo with realistic scale")
    print(f"  4. Validate -2.15pp MA effect is real!")


if __name__ == "__main__":
    main()