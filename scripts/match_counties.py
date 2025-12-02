"""
County Matching for Paired Experimental Design

Finds matched pairs of similar counties for causal inference.

Matching criteria:
- Population size (±50%)
- Poverty rate (±5pp)
- Racial composition (±10pp)
- Geographic proximity (same state)

Run with: python scripts/match_counties.py
"""

import sys
sys.path.insert(0, 'src')
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors

from data.data_loader import load_acs_county_data


def find_matched_pairs(acs_data, state='Alabama', n_pairs=10, min_population=20000):
    """
    Find matched pairs of similar counties for experimental design.
    
    Uses nearest neighbors matching on:
    - Log(population) - to avoid size dominating
    - Poverty rate
    - Black percentage
    - Hispanic percentage
    
    Args:
        acs_data: ACS DataFrame
        state: State to select counties from (default: Alabama)
        n_pairs: Number of matched pairs to find
        min_population: Minimum county population (exclude very small)
        
    Returns:
        list: [(county_A, county_B, similarity_score), ...]
    """
    print("=" * 70)
    print("FINDING MATCHED COUNTY PAIRS")
    print("=" * 70)
    
    # Filter to state and minimum population
    if state:
        # County names are formatted as "County Name, State"
        counties = acs_data[acs_data['county_name'].str.contains(f', {state}')].copy()
    else:
        counties = acs_data.copy()
    
    counties = counties[counties['total_county_population'] >= min_population].copy()
    
    print(f"\nFiltered to {len(counties)} counties in {state}")
    print(f"  (minimum population: {min_population:,})")
    
    # Create matching features
    counties['log_pop'] = np.log(counties['total_county_population'])
    
    matching_vars = ['log_pop', 'poverty_rate', 'black_pct', 'hispanic_pct']
    X = counties[matching_vars].values
    
    # Standardize features (so all have equal weight)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    print(f"\nMatching on:")
    for var in matching_vars:
        print(f"  - {var}")
    
    # Find nearest neighbors
    nn = NearestNeighbors(n_neighbors=3)  # Self + 2 neighbors
    nn.fit(X_scaled)
    
    # Find best pairs
    matched_pairs = []
    used_indices = set()
    
    # Sort by population (process largest first to get good matches)
    sorted_indices = counties['total_county_population'].argsort()[::-1]
    
    for i in sorted_indices:
        if i in used_indices:
            continue
        
        # Find nearest neighbors
        distances, indices = nn.kneighbors([X_scaled[i]])
        
        # Get closest unused county
        for dist, idx in zip(distances[0][1:], indices[0][1:]):  # Skip self
            if idx not in used_indices:
                county_a = counties.iloc[i]['county_name']
                county_b = counties.iloc[idx]['county_name']
                
                # Calculate similarity score (lower distance = more similar)
                similarity = 1 / (1 + dist)  # 0-1 scale, higher = more similar
                
                matched_pairs.append((county_a, county_b, similarity, dist))
                used_indices.add(i)
                used_indices.add(idx)
                break
        
        if len(matched_pairs) >= n_pairs:
            break
    
    # Print matched pairs
    print(f"\n{'='*70}")
    print(f"MATCHED PAIRS (n={len(matched_pairs)})")
    print(f"{'='*70}\n")
    
    for i, (county_a, county_b, similarity, dist) in enumerate(matched_pairs, 1):
        print(f"Pair {i}: Similarity={similarity:.3f}")
        
        # Get data for both counties
        data_a = counties[counties['county_name'] == county_a].iloc[0]
        data_b = counties[counties['county_name'] == county_b].iloc[0]
        
        print(f"  Control: {county_a}")
        print(f"    Pop: {data_a['total_county_population']:,}, "
              f"Poverty: {data_a['poverty_rate']:.1f}%, "
              f"Black: {data_a['black_pct']:.1f}%, "
              f"White: {data_a['white_pct']:.1f}%")
        
        print(f"  Treatment: {county_b}")
        print(f"    Pop: {data_b['total_county_population']:,}, "
              f"Poverty: {data_b['poverty_rate']:.1f}%, "
              f"Black: {data_b['black_pct']:.1f}%, "
              f"White: {data_b['white_pct']:.1f}%")
        
        print(f"  Differences:")
        print(f"    Pop: {abs(data_a['total_county_population'] - data_b['total_county_population']):,} "
              f"({abs(data_a['total_county_population'] - data_b['total_county_population'])/data_a['total_county_population']*100:.1f}%)")
        print(f"    Poverty: {abs(data_a['poverty_rate'] - data_b['poverty_rate']):.1f}pp")
        print(f"    Black %: {abs(data_a['black_pct'] - data_b['black_pct']):.1f}pp")
        print()
    
    return matched_pairs


def validate_matches(matched_pairs, acs_data):
    """
    Validate that matched pairs are actually similar.
    
    Check balance on key covariates.
    """
    print("=" * 70)
    print("BALANCE CHECK")
    print("=" * 70)
    
    control_counties = [pair[0] for pair in matched_pairs]
    treatment_counties = [pair[1] for pair in matched_pairs]
    
    control_data = acs_data[acs_data['county_name'].isin(control_counties)]
    treatment_data = acs_data[acs_data['county_name'].isin(treatment_counties)]
    
    print(f"\nComparing control vs treatment groups:")
    print(f"  (Should be similar if matching worked)\n")
    
    vars_to_check = [
        ('total_county_population', 'Population'),
        ('poverty_rate', 'Poverty Rate'),
        ('black_pct', 'Black %'),
        ('white_pct', 'White %'),
        ('hispanic_pct', 'Hispanic %'),
        ('median_household_income', 'Median Income')
    ]
    
    print(f"  {'Variable':<20} | {'Control':>12} | {'Treatment':>12} | {'Diff':>8}")
    print(f"  {'-'*20}-+-{'-'*12}-+-{'-'*12}-+-{'-'*8}")
    
    for var, label in vars_to_check:
        if var in control_data.columns:
            control_mean = control_data[var].mean()
            treatment_mean = treatment_data[var].mean()
            diff = treatment_mean - control_mean
            
            # Format based on variable type
            if var == 'total_county_population':
                print(f"  {label:<20} | {control_mean:>12,.0f} | {treatment_mean:>12,.0f} | {diff:>8,.0f}")
            elif var == 'median_household_income':
                print(f"  {label:<20} | {control_mean:>12,.0f} | {treatment_mean:>12,.0f} | {diff:>8,.0f}")
            else:
                print(f"  {label:<20} | {control_mean:>12.1f} | {treatment_mean:>12.1f} | {diff:>8.1f}")
    
    print(f"\n✓ If differences are small, matching is good!")


def main():
    """Find and validate matched county pairs."""
    print("\n" + "="*70)
    print("Matched County-Pair Design for AI Experiment")
    print("="*70)
    print("\nStrategy: Find pairs of similar counties")
    print("  → Randomly assign one to control, one to treatment")
    print("  → Compare within pairs (controls for county characteristics)")
    print("  → Aggregate across pairs (statistical power)")
    
    # Load ACS data
    acs = load_acs_county_data('src/data/us_census_acs_2022_county_data.csv')
    
    # Find matched pairs
    matched_pairs = find_matched_pairs(
        acs_data=acs,
        state='Alabama',
        n_pairs=8,
        min_population=20000
    )
    
    # Validate matching
    validate_matches(matched_pairs, acs)
    
    # Save pairs
    pairs_data = []
    for i, (county_a, county_b, similarity, dist) in enumerate(matched_pairs, 1):
        pairs_data.append({
            'pair_id': i,
            'control_county': county_a,
            'treatment_county': county_b,
            'similarity': similarity,
            'distance': dist
        })
    
    pairs_df = pd.DataFrame(pairs_data)
    
    # Create data folder if it doesn't exist
    import os
    os.makedirs('data', exist_ok=True)
    
    pairs_df.to_csv('data/matched_county_pairs.csv', index=False)
    
    print("\n" + "="*70)
    print("MATCHING COMPLETE")
    print("="*70)
    print(f"\nFound {len(matched_pairs)} matched pairs")
    print(f"Saved to: data/matched_county_pairs.csv")
    print(f"\nNext: Run matched experiment with these pairs!")


if __name__ == "__main__":
    main()