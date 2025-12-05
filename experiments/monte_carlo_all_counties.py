"""
Complete Monte Carlo Experiment - All Counties

Runs Monte Carlo validation for all counties in the US.

Design:
- For each county: Run N Monte Carlo iterations
- Each iteration: Random sample from CPS
- Calculate treatment effect distribution
- Test capacity-constraint hypothesis

Configuration:
- Large counties (>200k): 100 iterations
- Medium counties (50-200k): 50 iterations  
- Small counties (<50k): 25 iterations
(Fewer iterations for small = faster while maintaining power)

Run with: python experiments/monte_carlo_all_counties.py
Time: 24-48 hours (run overnight for multiple nights)
"""

import sys
sys.path.insert(0, 'src')
import numpy as np
import pandas as pd

from data.data_loader import create_realistic_population, load_acs_county_data
from simulation.runner import create_evaluators, create_reviewers, run_month
from ai.application_sorter import AI_ApplicationSorter


def determine_iterations(population):
    """
    Determine number of Monte Carlo iterations based on county size.
    
    Larger counties: More iterations (more stable)
    Smaller counties: Fewer iterations (faster)
    
    Args:
        population: County population
        
    Returns:
        int: Number of iterations
    """
    if population >= 200000:
        return 100  # Large counties
    elif population >= 50000:
        return 50   # Medium counties
    else:
        return 25   # Small counties


def run_monte_carlo_for_county(county, county_pop, poverty_rate, n_iterations, n_months, 
                                cps_file, acs_file, base_seed):
    """
    Run Monte Carlo for one county.
    
    Args:
        county: County name
        county_pop: County total population
        poverty_rate: County poverty rate (for calculating eligible pop)
        n_iterations: Number of Monte Carlo iterations
        
    Returns:
        dict: County results with mean effect and CI
    """
    # Calculate seekers proportional to eligible population
    eligible_pop = county_pop * (poverty_rate / 100 * 2.5)
    n_seekers = max(50, int(eligible_pop * 0.0005))  # 0.05% of eligible (1 per 2,000)
    # This gives: LA ~1,700, rural ~50
    
    print(f" (n={n_seekers})", end='', flush=True)
    
    results = []
    
    for i in range(n_iterations):
        try:
            # Create random sample (different seed each iteration)
            seekers_master = create_realistic_population(
                cps_file=cps_file,
                acs_file=acs_file,
                n_seekers=n_seekers,
                counties=[county],
                proportional=False,  # Single county
                random_seed=base_seed + i
            )
            
            # Run parallel worlds
            control = run_one_world(seekers_master, [county], acs_file, n_months, 
                                   None, base_seed + i)
            treatment = run_one_world(seekers_master, [county], acs_file, n_months,
                                     AI_ApplicationSorter('simple_first'), base_seed + i)
            
            # Calculate effect
            effect = calculate_effect(control, treatment)
            
            if effect is not None:
                results.append(effect)
                
        except Exception as e:
            continue
    
    if len(results) == 0:
        return {
            'county': county,
            'state': county.split(', ')[1] if ', ' in county else 'Unknown',
            'skipped': True,
            'reason': 'No valid iterations'
        }
    
    # Aggregate across iterations
    effects = [r['treatment_effect'] for r in results]
    
    mean_effect = np.mean(effects)
    se = np.std(effects) / np.sqrt(len(effects))
    ci_lower = mean_effect - 1.96 * se
    ci_upper = mean_effect + 1.96 * se
    
    return {
        'county': county,
        'state': county.split(', ')[1] if ', ' in county else 'Unknown',
        'population': county_pop,
        'n_iterations': len(results),
        'n_seekers': n_seekers,
        'mean_effect': mean_effect,
        'se': se,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'min_effect': np.min(effects),
        'max_effect': np.max(effects),
        'sd_effect': np.std(effects),
        'skipped': False
    }


def run_one_world(seekers_master, counties, acs_file, n_months, ai_sorter, random_seed):
    """Run simulation in one world."""
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
    
    # Staff
    acs_data = load_acs_county_data(acs_file)
    evaluators = create_evaluators(counties, acs_data=acs_data, random_seed=random_seed)
    reviewers = create_reviewers(counties, acs_data=acs_data, random_seed=random_seed)
    
    # Run
    for month in range(n_months):
        run_month(seekers, evaluators, reviewers, month, ai_sorter=ai_sorter)
    
    return {'seekers': seekers}


def calculate_effect(control, treatment):
    """Calculate treatment effect."""
    c_white = [s for s in control['seekers'] if s.race == 'White']
    c_black = [s for s in control['seekers'] if s.race == 'Black']
    t_white = [s for s in treatment['seekers'] if s.race == 'White']
    t_black = [s for s in treatment['seekers'] if s.race == 'Black']
    
    if not c_white or not c_black or not t_white or not t_black:
        return None
    
    c_w_apps = sum(s.num_applications for s in c_white)
    c_w_approved = sum(s.num_approvals for s in c_white)
    c_b_apps = sum(s.num_applications for s in c_black)
    c_b_approved = sum(s.num_approvals for s in c_black)
    
    if c_w_apps == 0 or c_b_apps == 0:
        return None
    
    c_gap = (c_w_approved / c_w_apps) - (c_b_approved / c_b_apps)
    
    t_w_apps = sum(s.num_applications for s in t_white)
    t_w_approved = sum(s.num_approvals for s in t_white)
    t_b_apps = sum(s.num_applications for s in t_black)
    t_b_approved = sum(s.num_approvals for s in t_black)
    
    if t_w_apps == 0 or t_b_apps == 0:
        return None
    
    t_gap = (t_w_approved / t_w_apps) - (t_b_approved / t_b_apps)
    
    return {'treatment_effect': t_gap - c_gap}


def main():
    """Run Monte Carlo for all counties."""
    print("\n" + "="*70)
    print("MONTE CARLO - ALL COUNTIES")
    print("="*70)
    print("\nPurpose: Account for sampling variation in ALL counties")
    print("\nApproach:")
    print("  - Large counties (>200k): 100 iterations")
    print("  - Medium counties (50-200k): 50 iterations")
    print("  - Small counties (<50k): 25 iterations")
    
    # Load ACS
    acs = load_acs_county_data('src/data/us_census_acs_2022_county_data.csv')
    
    # Select counties (same as before)
    acs['black_count'] = acs['total_county_population'] * (acs['black_pct'] / 100)
    
    counties_df = acs[
        (acs['total_county_population'] >= 10000) &
        (acs['black_count'] >= 10)
    ].copy()
    
    counties_df = counties_df.sort_values('total_county_population', ascending=False)
    counties = counties_df['county_name'].tolist()
    
    # Calculate total iterations
    total_iters = sum(determine_iterations(p) for p in counties_df['total_county_population'])
    
    print(f"\nCounties: {len(counties)}")
    print(f"Total iterations: {total_iters:,}")
    print(f"Total simulations: {total_iters * 2:,} (control + treatment)")
    print(f"Estimated time: 48-72 hours")
    
    response = input(f"\nContinue? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return
    
    # Run Monte Carlo for each county
    county_results = []
    
    for i, row in enumerate(counties_df.itertuples(), 1):
        county = row.county_name
        pop = row.total_county_population
        poverty = row.poverty_rate
        
        n_iters = determine_iterations(pop)
        
        if i % 50 == 0:
            print(f"\nProgress: {i}/{len(counties)} counties ({i/len(counties)*100:.0f}%)")
        
        print(f"\n{i}. {county[:40]}: {n_iters} iters", end='', flush=True)
        
        result = run_monte_carlo_for_county(
            county=county,
            county_pop=pop,
            poverty_rate=poverty,
            n_iterations=n_iters,
            n_months=12,
            cps_file='src/data/cps_asec_2022_processed_full.csv',
            acs_file='src/data/us_census_acs_2022_county_data.csv',
            base_seed=42 + i * 1000
        )
        
        county_results.append(result)
        
        # Checkpoint every 100
        if i % 100 == 0:
            import os
            os.makedirs('results', exist_ok=True)
            temp_df = pd.DataFrame([r for r in county_results if not r.get('skipped')])
            temp_df.to_csv(f'results/monte_carlo_all_checkpoint_{i}.csv', index=False)
            print(f"\n  ✓ Checkpoint {i}")
    
    # Save final
    import os
    os.makedirs('results', exist_ok=True)
    
    results_df = pd.DataFrame([r for r in county_results if not r.get('skipped')])
    results_df.to_csv('results/monte_carlo_all_counties.csv', index=False)
    
    print(f"\n✓ Results saved: results/monte_carlo_all_counties.csv")
    
    # Aggregate
    print(f"\n{'='*70}")
    print("NATIONAL RESULTS")
    print(f"{'='*70}")
    
    mean_national = results_df['mean_effect'].mean()
    se_national = results_df['mean_effect'].std() / np.sqrt(len(results_df))
    
    print(f"\nNational average (across {len(results_df)} counties):")
    print(f"  Mean: {mean_national*100:+.1f}pp")
    print(f"  SE: {se_national*100:.1f}pp")
    print(f"  95% CI: [{(mean_national - 1.96*se_national)*100:+.1f}pp, {(mean_national + 1.96*se_national)*100:+.1f}pp]")
    
    print(f"\n✓ Test capacity hypothesis:")
    print(f"  python scripts/analyze_capacity_hypothesis.py")


if __name__ == "__main__":
    main()