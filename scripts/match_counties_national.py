"""
National Matched County-Pair Design

Finds matched pairs of counties across the entire United States.

Benefits over state-only:
- More variation in demographics
- Better generalizability
- National policy relevance
- More heterogeneity to study

Run with: python scripts/match_counties_national.py
"""

import sys
sys.path.insert(0, 'src')
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors

from data.data_loader import load_acs_county_data


def find_national_matched_pairs(acs_data, n_pairs=20, min_population=50000, max_population=500000):
    """
    Find matched pairs of similar counties across the United States.
    
    Strategy:
    - Focus on medium-sized counties (50k-500k) for comparability
    - Match on demographics, not geography
    - Ensures variation across regions
    
    Args:
        acs_data: ACS DataFrame
        n_pairs: Number of matched pairs (default: 20 for statistical power)
        min_population: Minimum county population
        max_population: Maximum county population
        
    Returns:
        list: [(county_A, county_B, similarity_score, distance), ...]
    """
    print("=" * 70)
    print("NATIONAL MATCHED COUNTY-PAIR DESIGN")
    print("=" * 70)
    
    # Filter to medium-sized counties (comparable capacity)
    counties = acs_data[
        (acs_data['total_county_population'] >= min_population) &
        (acs_data['total_county_population'] <= max_population)
    ].copy()
    
    print(f"\nFiltered to {len(counties)} medium-sized counties nationwide")
    print(f"  Population range: {min_population:,} - {max_population:,}")
    
    # Show regional distribution
    counties['state'] = counties['county_name'].str.split(', ').str[1]
    print(f"\n  States represented: {counties['state'].nunique()}")
    print(f"  Top states:")
    top_states = counties['state'].value_counts().head(10)
    for state, count in top_states.items():
        print(f"    {state}: {count} counties")
    
    # Create matching features
    counties['log_pop'] = np.log(counties['total_county_population'])
    
    matching_vars = [
        'log_pop',           # Population size
        'poverty_rate',      # Economic conditions
        'black_pct',         # Racial composition
        'hispanic_pct',      # Racial composition
        'median_household_income',  # Economic conditions
        'snap_participation_rate'   # Program usage
    ]
    
    # Check all vars exist
    available_vars = [v for v in matching_vars if v in counties.columns]
    X = counties[available_vars].fillna(0).values
    
    print(f"\nMatching on {len(available_vars)} variables:")
    for var in available_vars:
        print(f"  - {var}")
    
    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Find nearest neighbors
    nn = NearestNeighbors(n_neighbors=5)  # More neighbors for better matches
    nn.fit(X_scaled)
    
    # Find best pairs
    matched_pairs = []
    used_indices = set()
    
    # Sort by population (process mid-sized first for best matches)
    median_pop = counties['total_county_population'].median()
    counties['pop_diff_from_median'] = abs(counties['total_county_population'] - median_pop)
    sorted_indices = counties['pop_diff_from_median'].argsort()
    
    for i in sorted_indices:
        if i in used_indices:
            continue
        
        # Find nearest neighbors
        distances, indices = nn.kneighbors([X_scaled[i]])
        
        # Get closest unused county FROM DIFFERENT STATE
        county_i_state = counties.iloc[i]['state']
        
        for dist, idx in zip(distances[0][1:], indices[0][1:]):
            if idx not in used_indices:
                county_j_state = counties.iloc[idx]['state']
                
                # PREFER different states for national variation
                # But allow same state if good match
                if county_i_state != county_j_state or dist < 0.5:
                    county_a = counties.iloc[i]['county_name']
                    county_b = counties.iloc[idx]['county_name']
                    
                    similarity = 1 / (1 + dist)
                    
                    matched_pairs.append((county_a, county_b, similarity, dist))
                    used_indices.add(i)
                    used_indices.add(idx)
                    break
        
        if len(matched_pairs) >= n_pairs:
            break
    
    # Print matched pairs with geographic diversity info
    print(f"\n{'='*70}")
    print(f"MATCHED PAIRS (n={len(matched_pairs)})")
    print(f"{'='*70}\n")
    
    cross_state_pairs = 0
    
    for i, (county_a, county_b, similarity, dist) in enumerate(matched_pairs, 1):
        state_a = county_a.split(', ')[1]
        state_b = county_b.split(', ')[1]
        
        cross_state = state_a != state_b
        if cross_state:
            cross_state_pairs += 1
        
        print(f"Pair {i}: Similarity={similarity:.3f} {'[CROSS-STATE]' if cross_state else '[SAME STATE]'}")
        
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
        pop_diff_pct = abs(data_a['total_county_population'] - data_b['total_county_population']) / data_a['total_county_population'] * 100
        print(f"    Pop: {abs(data_a['total_county_population'] - data_b['total_county_population']):,} ({pop_diff_pct:.1f}%)")
        print(f"    Poverty: {abs(data_a['poverty_rate'] - data_b['poverty_rate']):.1f}pp")
        print(f"    Black %: {abs(data_a['black_pct'] - data_b['black_pct']):.1f}pp")
        print()
    
    print(f"Cross-state pairs: {cross_state_pairs}/{len(matched_pairs)} ({cross_state_pairs/len(matched_pairs)*100:.0f}%)")
    print(f"→ National variation: {'High' if cross_state_pairs > len(matched_pairs)/2 else 'Low'}")
    
    return matched_pairs


def validate_national_matches(matched_pairs, acs_data):
    """
    Validate national matched pairs.
    
    Checks:
    - Balance on covariates
    - Geographic diversity
    - Regional representation
    """
    print("=" * 70)
    print("NATIONAL BALANCE CHECK")
    print("=" * 70)
    
    control_counties = [pair[0] for pair in matched_pairs]
    treatment_counties = [pair[1] for pair in matched_pairs]
    
    control_data = acs_data[acs_data['county_name'].isin(control_counties)]
    treatment_data = acs_data[acs_data['county_name'].isin(treatment_counties)]
    
    # Extract states
    control_data['state'] = control_data['county_name'].str.split(', ').str[1]
    treatment_data['state'] = treatment_data['county_name'].str.split(', ').str[1]
    
    print(f"\nGeographic Coverage:")
    print(f"  Control states: {control_data['state'].nunique()} states")
    print(f"  Treatment states: {treatment_data['state'].nunique()} states")
    
    all_states = set(control_data['state'].unique()) | set(treatment_data['state'].unique())
    print(f"  Total states: {len(all_states)}")
    
    # Regional balance
    print(f"\n  Top states in control group:")
    for state, count in control_data['state'].value_counts().head(5).items():
        print(f"    {state}: {count}")
    
    print(f"\n  Top states in treatment group:")
    for state, count in treatment_data['state'].value_counts().head(5).items():
        print(f"    {state}: {count}")
    
    # Covariate balance
    print(f"\nCovariate Balance:")
    print(f"  {'Variable':<25} | {'Control':>12} | {'Treatment':>12} | {'Diff':>10}")
    print(f"  {'-'*25}-+-{'-'*12}-+-{'-'*12}-+-{'-'*10}")
    
    vars_to_check = [
        ('total_county_population', 'Population'),
        ('poverty_rate', 'Poverty Rate'),
        ('black_pct', 'Black %'),
        ('white_pct', 'White %'),
        ('hispanic_pct', 'Hispanic %'),
        ('median_household_income', 'Median Income')
    ]
    
    for var, label in vars_to_check:
        if var in control_data.columns:
            control_mean = control_data[var].mean()
            treatment_mean = treatment_data[var].mean()
            diff = treatment_mean - control_mean
            
            if var == 'total_county_population':
                print(f"  {label:<25} | {control_mean:>12,.0f} | {treatment_mean:>12,.0f} | {diff:>10,.0f}")
            elif var == 'median_household_income':
                print(f"  {label:<25} | ${control_mean:>11,.0f} | ${treatment_mean:>11,.0f} | ${diff:>9,.0f}")
            else:
                print(f"  {label:<25} | {control_mean:>12.1f} | {treatment_mean:>12.1f} | {diff:>10.1f}")
    
    print(f"\n✓ Good balance if differences are small")


def main():
    """Find national matched county pairs."""
    print("\n" + "="*70)
    print("National Matched County-Pair Design")
    print("="*70)
    print("\nStrategy:")
    print("  - Match counties NATIONWIDE (not just one state)")
    print("  - Focus on medium-sized counties (50k-500k)")
    print("  - Match on demographics, economics, program usage")
    print("  - Prefer cross-state pairs for variation")
    print("\nBenefits:")
    print("  ✓ National generalizability")
    print("  ✓ More variation in policies/practices")
    print("  ✓ Regional heterogeneity")
    print("  ✓ Stronger external validity")
    
    # Load ACS data
    acs = load_acs_county_data('src/data/us_census_acs_2022_county_data.csv')
    
    # Find matched pairs
    matched_pairs = find_national_matched_pairs(
        acs_data=acs,
        n_pairs=20,  # More pairs for national study
        min_population=50000,
        max_population=500000
    )
    
    # Validate matching
    validate_national_matches(matched_pairs, acs)
    
    # Save pairs
    pairs_data = []
    for i, (county_a, county_b, similarity, dist) in enumerate(matched_pairs, 1):
        state_a = county_a.split(', ')[1]
        state_b = county_b.split(', ')[1]
        
        pairs_data.append({
            'pair_id': i,
            'control_county': county_a,
            'treatment_county': county_b,
            'control_state': state_a,
            'treatment_state': state_b,
            'cross_state': state_a != state_b,
            'similarity': similarity,
            'distance': dist
        })
    
    pairs_df = pd.DataFrame(pairs_data)
    
    import os
    os.makedirs('data', exist_ok=True)
    pairs_df.to_csv('data/matched_county_pairs_national.csv', index=False)
    
    print("\n" + "="*70)
    print("NATIONAL MATCHING COMPLETE")
    print("="*70)
    print(f"\nFound {len(matched_pairs)} matched pairs")
    
    cross_state = sum(pairs_df['cross_state'])
    print(f"  Cross-state pairs: {cross_state}/{len(matched_pairs)} ({cross_state/len(matched_pairs)*100:.0f}%)")
    
    states_covered = set(pairs_df['control_state']) | set(pairs_df['treatment_state'])
    print(f"  States covered: {len(states_covered)}")
    
    print(f"\nSaved to: data/matched_county_pairs_national.csv")
    print(f"\nNext: Run national experiment!")
    print(f"  python experiments/experiment_matched_pairs_national.py")


if __name__ == "__main__":
    main()