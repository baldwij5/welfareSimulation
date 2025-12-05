"""
Monte Carlo Validation - California

Tests whether results are robust to sampling variation.

Design:
1. Select California counties
2. Run 100 Monte Carlo iterations:
   - Each iteration: Random sample from CPS (weighted by ACS)
   - Run parallel worlds
   - Calculate treatment effect
3. Compare to single-sample results
4. Show mean, CI, distribution

Run with: python experiments/monte_carlo_california.py
Time: ~2-3 hours (100 iterations × 2 conditions)
"""

import sys
sys.path.insert(0, 'src')
import numpy as np
import pandas as pd

from data.data_loader import create_realistic_population, load_acs_county_data
from simulation.runner import create_evaluators, create_reviewers, run_month
from ai.application_sorter import AI_ApplicationSorter


def run_one_monte_carlo_iteration(counties, n_seekers, n_months, cps_file, acs_file, 
                                   iteration_seed, base_seed=42):
    """
    Run one Monte Carlo iteration (one random sample).
    
    Returns treatment effect for this sample.
    """
    # Create random sample (different seed each iteration)
    seekers_master = create_realistic_population(
        cps_file=cps_file,
        acs_file=acs_file,
        n_seekers=n_seekers,
        counties=counties,
        proportional=True,
        random_seed=base_seed + iteration_seed  # Different sample each time
    )
    
    # Run parallel worlds on this sample
    control_result = run_simulation_one_world(
        seekers_master, counties, acs_file, n_months,
        ai_sorter=None, random_seed=base_seed + iteration_seed
    )
    
    treatment_result = run_simulation_one_world(
        seekers_master, counties, acs_file, n_months,
        ai_sorter=AI_ApplicationSorter('simple_first'),
        random_seed=base_seed + iteration_seed
    )
    
    # Calculate effect
    effect = calculate_treatment_effect(control_result, treatment_result)
    
    return effect


def run_simulation_one_world(seekers_master, counties, acs_file, n_months, ai_sorter, random_seed):
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
    
    # Create staff
    acs_data = load_acs_county_data(acs_file)
    evaluators = create_evaluators(counties, acs_data=acs_data, random_seed=random_seed)
    reviewers = create_reviewers(counties, acs_data=acs_data, random_seed=random_seed)
    
    # Run simulation
    for month in range(n_months):
        run_month(seekers, evaluators, reviewers, month, ai_sorter=ai_sorter)
    
    return {'seekers': seekers}


def calculate_treatment_effect(control, treatment):
    """Calculate treatment effect for one iteration."""
    c_white = [s for s in control['seekers'] if s.race == 'White']
    c_black = [s for s in control['seekers'] if s.race == 'Black']
    t_white = [s for s in treatment['seekers'] if s.race == 'White']
    t_black = [s for s in treatment['seekers'] if s.race == 'Black']
    
    if not c_white or not c_black:
        return None
    
    c_white_rate = sum(s.num_approvals for s in c_white) / sum(s.num_applications for s in c_white)
    c_black_rate = sum(s.num_approvals for s in c_black) / sum(s.num_applications for s in c_black)
    c_gap = c_white_rate - c_black_rate
    
    t_white_rate = sum(s.num_approvals for s in t_white) / sum(s.num_applications for s in t_white)
    t_black_rate = sum(s.num_approvals for s in t_black) / sum(s.num_applications for s in t_black)
    t_gap = t_white_rate - t_black_rate
    
    return {
        'control_gap': c_gap,
        'treatment_gap': t_gap,
        'treatment_effect': t_gap - c_gap,
        'n_white': len(c_white),
        'n_black': len(c_black)
    }


def main():
    """Run California Monte Carlo validation."""
    print("\n" + "="*70)
    print("MONTE CARLO VALIDATION - CALIFORNIA")
    print("="*70)
    print("\nPurpose: Test if results are robust to sampling variation")
    print("\nDesign:")
    print("  State: California (largest, most diverse)")
    print("  Counties: Top 5 largest CA counties")
    print("  Iterations: 100 random samples")
    print("  For each: Run parallel worlds, calculate treatment effect")
    print("  Result: Mean effect ± CI (accounts for sampling uncertainty)")
    
    # Select California counties
    acs = load_acs_county_data('src/data/us_census_acs_2022_county_data.csv')
    
    ca_counties = acs[acs['county_name'].str.contains(', California')].copy()
    ca_counties = ca_counties.sort_values('total_county_population', ascending=False)
    
    # Top 5 largest
    counties = ca_counties.head(5)['county_name'].tolist()
    
    print(f"\nSelected California counties:")
    for i, county in enumerate(counties, 1):
        pop = ca_counties[ca_counties['county_name'] == county].iloc[0]['total_county_population']
        print(f"  {i}. {county}: {pop:,}")
    
    # Calculate seekers
    total_seekers = 2000  # Decent sample size
    
    print(f"\nTotal seekers: {total_seekers:,}")
    print(f"Iterations: 100")
    print(f"Total simulations: 200 (100 iterations × 2 conditions)")
    print(f"Estimated time: 2-3 hours")
    
    response = input(f"\nContinue? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return
    
    # Run Monte Carlo
    print(f"\n{'='*70}")
    print("RUNNING MONTE CARLO ITERATIONS")
    print(f"{'='*70}")
    
    results = []
    
    for i in range(100):
        if (i + 1) % 10 == 0:
            print(f"\nIteration {i+1}/100 ({(i+1)}% complete)")
        elif i == 0:
            print(f"\nIteration {i+1}/100...")
        
        try:
            effect = run_one_monte_carlo_iteration(
                counties=counties,
                n_seekers=total_seekers,
                n_months=12,
                cps_file='src/data/cps_asec_2022_processed_full.csv',
                acs_file='src/data/us_census_acs_2022_county_data.csv',
                iteration_seed=i
            )
            
            if effect:
                results.append(effect)
                
        except Exception as e:
            print(f"  Error in iteration {i+1}: {e}")
            continue
    
    # Analyze results
    print(f"\n{'='*70}")
    print("MONTE CARLO RESULTS")
    print(f"{'='*70}")
    
    results_df = pd.DataFrame(results)
    
    print(f"\nValid iterations: {len(results_df)}/100")
    
    # Treatment effect statistics
    effects = results_df['treatment_effect'].values
    
    mean_effect = np.mean(effects)
    se = np.std(effects) / np.sqrt(len(effects))
    ci_lower = mean_effect - 1.96 * se
    ci_upper = mean_effect + 1.96 * se
    
    print(f"\nTreatment Effect (Monte Carlo):")
    print(f"  Mean: {mean_effect*100:+.1f}pp")
    print(f"  SE: {se*100:.1f}pp")
    print(f"  95% CI: [{ci_lower*100:+.1f}pp, {ci_upper*100:+.1f}pp]")
    print(f"  Min: {np.min(effects)*100:+.1f}pp")
    print(f"  Max: {np.max(effects)*100:+.1f}pp")
    print(f"  SD: {np.std(effects)*100:.1f}pp")
    
    # Statistical test
    from scipy import stats
    t_stat, p_value = stats.ttest_1samp(effects, 0)
    
    print(f"\nOne-sample t-test (H0: effect = 0):")
    print(f"  t = {t_stat:.3f}")
    print(f"  p = {p_value:.4f}")
    
    if p_value < 0.05:
        print(f"  ✓ Significantly different from zero")
    
    # Save results
    import os
    os.makedirs('results', exist_ok=True)
    
    results_df.to_csv('results/monte_carlo_california.csv', index=False)
    
    print(f"\n✓ Detailed results saved: results/monte_carlo_california.csv")
    
    # Summary
    summary = {
        'state': 'California',
        'n_counties': len(counties),
        'n_iterations': len(results_df),
        'mean_effect': mean_effect,
        'se': se,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        't_stat': t_stat,
        'p_value': p_value
    }
    
    summary_df = pd.DataFrame([summary])
    summary_df.to_csv('results/monte_carlo_california_summary.csv', index=False)
    
    print(f"\n{'='*70}")
    print("MONTE CARLO COMPLETE")
    print(f"{'='*70}")
    
    if p_value < 0.05:
        if mean_effect > 0:
            print(f"\n✓ FINDING: AI increases disparity in California")
        else:
            print(f"\n✓ FINDING: AI decreases disparity in California")
        print(f"  Effect: {mean_effect*100:+.1f}pp (95% CI: [{ci_lower*100:+.1f}, {ci_upper*100:+.1f}])")
    else:
        print(f"\n⚠ FINDING: No significant effect")
        print(f"  Effect: {mean_effect*100:+.1f}pp (p = {p_value:.3f})")


if __name__ == "__main__":
    main()