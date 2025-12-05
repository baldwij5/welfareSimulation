"""
Find Small, Diverse States

Identifies states with:
- Few counties (manageable for analysis)
- High diversity (variation in poverty, race, income)

Run with: python scripts/find_small_diverse_state.py
"""

import sys
sys.path.insert(0, 'src')
import pandas as pd
import numpy as np

from data.data_loader import load_acs_county_data


def calculate_diversity_score(state_counties):
    """
    Calculate diversity score for a state.
    
    High diversity = variation across:
    - Poverty rate
    - Black %
    - Hispanic %
    - Median income
    
    Returns:
        float: Diversity score (higher = more diverse)
    """
    # Coefficient of variation for each characteristic
    poverty_cv = state_counties['poverty_rate'].std() / state_counties['poverty_rate'].mean()
    black_cv = (state_counties['black_pct'].std() + 0.1) / (state_counties['black_pct'].mean() + 0.1)  # Add 0.1 to avoid div by 0
    hispanic_cv = (state_counties['hispanic_pct'].std() + 0.1) / (state_counties['hispanic_pct'].mean() + 0.1)
    income_cv = state_counties['median_household_income'].std() / state_counties['median_household_income'].mean()
    
    # Average CV (higher = more diverse)
    diversity_score = (poverty_cv + black_cv + hispanic_cv + income_cv) / 4
    
    return diversity_score


def find_small_diverse_states(acs_data, max_counties=20):
    """
    Find states with few counties but high diversity.
    
    Args:
        acs_data: ACS DataFrame
        max_counties: Maximum number of counties (for "small" state)
        
    Returns:
        DataFrame: States ranked by diversity
    """
    # Add state column
    acs_data['state'] = acs_data['county_name'].str.split(', ').str[1]
    
    # Remove NaN states
    acs_data = acs_data[acs_data['state'].notna()].copy()
    
    # Analyze each state
    state_analysis = []
    
    for state in acs_data['state'].unique():
        state_counties = acs_data[acs_data['state'] == state].copy()
        
        n_counties = len(state_counties)
        
        # Only consider states with few counties
        if n_counties > max_counties or n_counties < 3:
            continue
        
        # Calculate diversity
        diversity = calculate_diversity_score(state_counties)
        
        # Get ranges
        poverty_range = state_counties['poverty_rate'].max() - state_counties['poverty_rate'].min()
        black_range = state_counties['black_pct'].max() - state_counties['black_pct'].min()
        hispanic_range = state_counties['hispanic_pct'].max() - state_counties['hispanic_pct'].min()
        income_range = (state_counties['median_household_income'].max() - 
                       state_counties['median_household_income'].min())
        
        state_analysis.append({
            'state': state,
            'n_counties': n_counties,
            'diversity_score': diversity,
            'poverty_range': poverty_range,
            'black_range': black_range,
            'hispanic_range': hispanic_range,
            'income_range': income_range,
            'total_population': state_counties['total_county_population'].sum(),
            'mean_poverty': state_counties['poverty_rate'].mean(),
            'mean_black': state_counties['black_pct'].mean()
        })
    
    results = pd.DataFrame(state_analysis)
    results = results.sort_values('diversity_score', ascending=False)
    
    return results


def main():
    """Find and display small diverse states."""
    print("\n" + "="*70)
    print("FINDING SMALL, DIVERSE STATES")
    print("="*70)
    print("\nCriteria:")
    print("  - Few counties (3-20)")
    print("  - High diversity (variation in poverty, race, income)")
    
    # Load ACS
    acs = load_acs_county_data('src/data/us_census_acs_2022_county_data.csv')
    
    # Find small diverse states
    results = find_small_diverse_states(acs, max_counties=20)
    
    print(f"\n{'='*70}")
    print("TOP 15 SMALL, DIVERSE STATES")
    print(f"{'='*70}")
    print(f"\n{'State':<20} {'Counties':<10} {'Diversity':<12} {'Pov Range':<12} {'Black Range':<12}")
    print("-" * 70)
    
    for i, row in results.head(15).iterrows():
        print(f"{row['state']:<20} {row['n_counties']:<10.0f} {row['diversity_score']:<12.2f} "
              f"{row['poverty_range']:<12.1f} {row['black_range']:<12.1f}")
    
    # Show details for top 5
    print(f"\n{'='*70}")
    print("DETAILED INFO - TOP 5")
    print(f"{'='*70}")
    
    for i, row in results.head(5).iterrows():
        print(f"\n{i+1}. {row['state']}")
        print(f"   Counties: {row['n_counties']:.0f}")
        print(f"   Diversity score: {row['diversity_score']:.2f}")
        print(f"   Poverty: {row['mean_poverty']:.1f}% (range: {row['poverty_range']:.1f}pp)")
        print(f"   Black: {row['mean_black']:.1f}% (range: {row['black_range']:.1f}pp)")
        print(f"   Income range: ${row['income_range']:,.0f}")
        print(f"   Total pop: {row['total_population']:,.0f}")
    
    # Recommend best for Monte Carlo
    print(f"\n{'='*70}")
    print("RECOMMENDATION FOR MONTE CARLO")
    print(f"{'='*70}")
    
    top_state = results.iloc[0]
    
    print(f"\nBest state: {top_state['state']}")
    print(f"  Counties: {top_state['n_counties']:.0f} (manageable!)")
    print(f"  Diversity: {top_state['diversity_score']:.2f} (high variation)")
    print(f"  Population: {top_state['total_population']:,.0f}")
    print(f"\nWhy this is ideal:")
    print(f"  ✓ Few counties → Fast Monte Carlo")
    print(f"  ✓ High diversity → Tests variation")
    print(f"  ✓ Represents range of US contexts")
    
    # Show the actual counties
    print(f"\nCounties in {top_state['state']}:")
    state_counties = acs[acs['county_name'].str.contains(f", {top_state['state']}")].copy()
    state_counties = state_counties.sort_values('total_county_population', ascending=False)
    
    print(f"\n{'County':<40} {'Pop':>12} {'Poverty':>10} {'Black%':>10}")
    print("-" * 75)
    for _, county in state_counties.head(20).iterrows():
        name = county['county_name'].split(', ')[0]
        print(f"{name:<40} {county['total_county_population']:>12,.0f} "
              f"{county['poverty_rate']:>9.1f}% {county['black_pct']:>9.1f}%")


if __name__ == "__main__":
    main()