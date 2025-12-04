"""
ALL COUNTIES Experiment - Complete National Analysis

Runs parallel worlds experiment for EVERY county in the US.

Design:
- For each county with sufficient population:
  - Create population proportional to county's eligible population
  - Run Control (FCFS) and Treatment (AI) on SAME population
  - Calculate treatment effect
- Results: County-level treatment effects for entire nation
- Enables fine-grained geographic analysis

Run with: python experiments/experiment_all_counties.py
Time: 8-12 hours for ~500-1000 counties
"""

import sys
sys.path.insert(0, 'src')
import numpy as np
import pandas as pd

from data.data_loader import create_realistic_population, load_acs_county_data
from simulation.runner import create_evaluators, create_reviewers, run_month
from ai.application_sorter import AI_ApplicationSorter


def select_counties(acs_data, min_population=10000, min_black_count=10):
    """
    Select ALL counties with minimal criteria.
    
    Criteria:
    - Minimum population: 10k (very small threshold)
    - Minimum Black count: 10 people (for disparity calculation)
    
    This will include ~3,000+ counties (nearly all US counties)
    
    Args:
        acs_data: ACS DataFrame
        min_population: Minimum county population (default: 10k)
        min_black_count: Minimum Black residents (default: 10)
        
    Returns:
        list: ALL county names meeting minimal criteria
    """
    # Calculate Black population count
    acs_data['black_count'] = acs_data['total_county_population'] * (acs_data['black_pct'] / 100)
    
    # Very minimal filtering
    filtered = acs_data[
        (acs_data['total_county_population'] >= min_population) &
        (acs_data['black_count'] >= min_black_count)
    ].copy()
    
    print(f"\nUsing {len(filtered)} counties (ALL that meet minimal criteria):")
    print(f"  Min population: {min_population:,}")
    print(f"  Min Black residents: {min_black_count}")
    print(f"  Coverage: {len(filtered)}/3,202 US counties ({len(filtered)/3202*100:.1f}%)")
    print(f"  Population covered: {filtered['total_county_population'].sum() / acs_data['total_county_population'].sum() * 100:.1f}% of US")
    
    # Sort by population
    filtered = filtered.sort_values('total_county_population', ascending=False)
    
    return filtered['county_name'].tolist()


def calculate_county_seekers(acs_data, counties, total_seekers=50000):
    """
    Allocate seekers proportionally to county eligible populations.
    
    Args:
        acs_data: ACS DataFrame
        counties: List of county names
        total_seekers: Total seekers to allocate
        
    Returns:
        dict: {county: n_seekers}
    """
    allocations = {}
    eligible_pops = {}
    
    for county in counties:
        county_data = acs_data[acs_data['county_name'] == county]
        if len(county_data) > 0:
            pop = county_data.iloc[0]['total_county_population']
            poverty = county_data.iloc[0]['poverty_rate']
            eligible = pop * (poverty / 100 * 2.5)
            eligible_pops[county] = eligible
    
    total_eligible = sum(eligible_pops.values())
    
    for county, eligible in eligible_pops.items():
        proportion = eligible / total_eligible
        # Minimum 50 per county for statistical power
        n = max(50, int(total_seekers * proportion))
        allocations[county] = n
    
    # Adjust to match total
    allocated = sum(allocations.values())
    if allocated != total_seekers:
        largest = max(allocations, key=allocations.get)
        allocations[largest] += (total_seekers - allocated)
    
    return allocations


def run_county_experiment(county, n_seekers, n_months, cps_file, acs_file, random_seed):
    """
    Run parallel worlds for one county.
    
    Returns:
        dict: County results with treatment effect
    """
    # Create population
    seekers_master = create_realistic_population(
        cps_file=cps_file,
        acs_file=acs_file,
        n_seekers=n_seekers,
        counties=[county],
        proportional=False,  # Single county, doesn't matter
        random_seed=random_seed
    )
    
    # Run Control
    control = run_county_simulation(
        seekers_master, [county], acs_file, n_months,
        ai_sorter=None, random_seed=random_seed
    )
    
    # Run Treatment
    ai_tool = AI_ApplicationSorter('simple_first')
    treatment = run_county_simulation(
        seekers_master, [county], acs_file, n_months,
        ai_sorter=ai_tool, random_seed=random_seed
    )
    
    # Calculate effect
    return calculate_county_effect(county, control, treatment)


def run_county_simulation(seekers_master, counties, acs_file, n_months, ai_sorter, random_seed):
    """Run simulation for one county."""
    from data.data_loader import load_acs_county_data
    
    # Fresh copies
    seekers = []
    for orig in seekers_master:
        from core.seeker import Seeker
        fresh = Seeker(
            seeker_id=orig.id,
            race=orig.race,
            income=orig.income,
            county=orig.county,
            has_children=orig.has_children,
            has_disability=orig.has_disability,
            cps_data=orig.cps_data,
            random_state=np.random.RandomState(orig.id)
        )
        seekers.append(fresh)
    
    # Create staff
    acs_data = load_acs_county_data(acs_file)
    evaluators = create_evaluators(counties, acs_data=acs_data, random_seed=random_seed)
    reviewers = create_reviewers(counties, acs_data=acs_data, random_seed=random_seed)
    
    # Run
    for month in range(n_months):
        run_month(seekers, evaluators, reviewers, month, ai_sorter=ai_sorter)
    
    return {'seekers': seekers}


def calculate_county_effect(county, control, treatment):
    """Calculate treatment effect for one county."""
    c_white = [s for s in control['seekers'] if s.race == 'White']
    c_black = [s for s in control['seekers'] if s.race == 'Black']
    t_white = [s for s in treatment['seekers'] if s.race == 'White']
    t_black = [s for s in treatment['seekers'] if s.race == 'Black']
    
    if not c_white or not c_black:
        return {
            'county': county,
            'state': county.split(', ')[1] if ', ' in county else 'Unknown',
            'skipped': True,
            'reason': 'Insufficient sample'
        }
    
    c_white_apps = sum(s.num_applications for s in c_white)
    c_white_approved = sum(s.num_approvals for s in c_white)
    c_black_apps = sum(s.num_applications for s in c_black)
    c_black_approved = sum(s.num_approvals for s in c_black)
    
    if c_white_apps == 0 or c_black_apps == 0:
        return {
            'county': county,
            'state': county.split(', ')[1] if ', ' in county else 'Unknown',
            'skipped': True,
            'reason': 'No applications'
        }
    
    c_white_rate = c_white_approved / c_white_apps
    c_black_rate = c_black_approved / c_black_apps
    c_gap = c_white_rate - c_black_rate
    
    t_white_apps = sum(s.num_applications for s in t_white)
    t_white_approved = sum(s.num_approvals for s in t_white)
    t_black_apps = sum(s.num_applications for s in t_black)
    t_black_approved = sum(s.num_approvals for s in t_black)
    
    t_white_rate = t_white_approved / t_white_apps if t_white_apps > 0 else 0
    t_black_rate = t_black_approved / t_black_apps if t_black_apps > 0 else 0
    t_gap = t_white_rate - t_black_rate
    
    effect = t_gap - c_gap
    
    return {
        'county': county,
        'state': county.split(', ')[1] if ', ' in county else 'Unknown',
        'treatment_effect': effect,
        'control_gap': c_gap,
        'treatment_gap': t_gap,
        'n_white': len(c_white),
        'n_black': len(c_black),
        'skipped': False
    }


def main():
    """Run all-counties experiment."""
    print("\n" + "="*70)
    print("ALL COUNTIES EXPERIMENT - COMPLETE NATIONAL ANALYSIS")
    print("="*70)
    print("\nResearch Question:")
    print("  County-level variation in AI effects across entire US")
    print("\nDesign:")
    print("  - Select ~500-1000 counties (min 50k pop, min 5% Black)")
    print("  - Allocate seekers proportionally")
    print("  - Run parallel worlds for EACH county")
    print("  - Create county-level treatment effect map")
    
    # Load ACS
    acs = load_acs_county_data('src/data/us_census_acs_2022_county_data.csv')
    
    # Select counties
    print(f"\n{'='*70}")
    print("SELECTING COUNTIES")
    print(f"{'='*70}")
    
    counties = select_counties(
        acs_data=acs,
        min_population=10000,   # Very low threshold (include small counties)
        min_black_count=10      # At least 10 Black residents (for disparity)
    )
    
    print(f"\nUsing {len(counties)} counties - COMPLETE NATIONAL COVERAGE!")
    
    # Calculate allocations
    allocations = calculate_county_seekers(acs, counties, total_seekers=150000)  # 150k for full coverage
    
    print(f"\nTotal seekers allocated: {sum(allocations.values()):,}")
    
    print(f"\nTop 10 counties by seekers:")
    top_10 = sorted(allocations.items(), key=lambda x: x[1], reverse=True)[:10]
    for county, n in top_10:
        print(f"  {county}: {n} seekers")
    
    # Confirmation
    print(f"\n{'='*70}")
    print(f"READY TO RUN")
    print(f"{'='*70}")
    print(f"\nWill run:")
    print(f"  - {len(counties)} counties (COMPLETE US COVERAGE)")
    print(f"  - {sum(allocations.values()):,} total seekers")
    print(f"  - {len(counties) * 2:,} simulations")
    print(f"  - Estimated time: 24-48 hours (run overnight!)")
    print(f"\nCheckpoints saved every 50 counties")
    print(f"Can resume if interrupted")
    
    response = input(f"\nContinue? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return
    
    # Run experiments
    county_results = []
    
    for i, county in enumerate(counties, 1):
        n_seekers = allocations.get(county, 50)
        
        if i % 50 == 0:
            print(f"\nProgress: {i}/{len(counties)} counties ({i/len(counties)*100:.0f}%)")
        
        try:
            result = run_county_experiment(
                county=county,
                n_seekers=n_seekers,
                n_months=12,
                cps_file='src/data/cps_asec_2022_processed_full.csv',
                acs_file='src/data/us_census_acs_2022_county_data.csv',
                random_seed=42 + i
            )
            county_results.append(result)
            
        except Exception as e:
            print(f"  Error in {county}: {e}")
            county_results.append({
                'county': county,
                'state': county.split(', ')[1] if ', ' in county else 'Unknown',
                'skipped': True,
                'error': str(e)
            })
        
        # Checkpoint every 50
        if i % 50 == 0:
            import os
            os.makedirs('results', exist_ok=True)
            temp_df = pd.DataFrame([r for r in county_results if not r.get('skipped')])
            temp_df.to_csv(f'results/all_counties_checkpoint_{i}.csv', index=False)
            print(f"  ✓ Checkpoint saved")
    
    # Save final
    import os
    os.makedirs('results', exist_ok=True)
    
    results_df = pd.DataFrame([r for r in county_results if not r.get('skipped')])
    results_df.to_csv('results/all_counties_results.csv', index=False)
    
    print(f"\n✓ Results saved: results/all_counties_results.csv")
    print(f"  Valid counties: {len(results_df)}")
    
    # Summary stats
    print(f"\n{'='*70}")
    print("NATIONAL SUMMARY")
    print(f"{'='*70}")
    
    ate = results_df['treatment_effect'].mean()
    se = results_df['treatment_effect'].std() / np.sqrt(len(results_df))
    
    print(f"\nAverage Treatment Effect: {ate*100:+.1f}pp")
    print(f"SE: {se*100:.1f}pp")
    print(f"95% CI: [{(ate-1.96*se)*100:+.1f}pp, {(ate+1.96*se)*100:+.1f}pp]")
    
    print(f"\nHeterogeneity:")
    print(f"  Min: {results_df['treatment_effect'].min()*100:+.1f}pp")
    print(f"  Max: {results_df['treatment_effect'].max()*100:+.1f}pp")
    print(f"  SD: {results_df['treatment_effect'].std()*100:.1f}pp")
    
    print(f"\n✓ Run visualization:")
    print(f"  python scripts/visualize_county_map.py")


if __name__ == "__main__":
    main()