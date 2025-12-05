"""
Massachusetts Monte Carlo Parallel Worlds

Tests AI effect with Monte Carlo sampling for Massachusetts.

Design:
- Select all MA counties (14 counties)
- Run 100 Monte Carlo iterations
- Each iteration: Random CPS sample → Parallel worlds
- With state models and all mechanisms enabled

Run with: python experiments/monte_carlo_massachusetts.py
Time: ~1-2 hours
"""

import sys
sys.path.insert(0, 'src')
import numpy as np
import pandas as pd

from data.data_loader import create_realistic_population, load_acs_county_data
from simulation.runner import create_evaluators, create_reviewers, run_month
from ai.application_sorter import AI_ApplicationSorter


def run_parallel_worlds_one_iteration(counties, n_seekers, n_months, iteration_seed):
    """
    Run one Monte Carlo iteration of parallel worlds.
    
    Returns:
        dict: Treatment effect for this iteration
    """
    # Create random sample
    seekers_master = create_realistic_population(
        cps_file='src/data/cps_asec_2022_processed_full.csv',
        acs_file='src/data/us_census_acs_2022_county_data.csv',
        n_seekers=n_seekers,
        counties=counties,
        proportional=True,
        random_seed=42 + iteration_seed  # Different each time
    )
    
    # Run control world
    control = run_one_world(seekers_master, counties, n_months, None, iteration_seed)
    
    # Run treatment world
    treatment = run_one_world(seekers_master, counties, n_months, 
                             AI_ApplicationSorter('simple_first'), iteration_seed)
    
    # Calculate effect
    return calculate_effect(control, treatment, iteration_seed)


def run_one_world(seekers_master, counties, n_months, ai_sorter, seed):
    """Run simulation in one world."""
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
    
    # Create staff (with state models)
    acs_data = load_acs_county_data('src/data/us_census_acs_2022_county_data.csv')
    evaluators = create_evaluators(counties, acs_data=acs_data, random_seed=seed)
    reviewers = create_reviewers(counties, acs_data=acs_data, load_state_models=True, 
                                 random_seed=seed)
    
    # Run simulation
    for month in range(n_months):
        run_month(seekers, evaluators, reviewers, month, ai_sorter=ai_sorter)
    
    return {'seekers': seekers}


def calculate_effect(control, treatment, iteration):
    """Calculate treatment effect for one iteration."""
    c_white = [s for s in control['seekers'] if s.race == 'White']
    c_black = [s for s in control['seekers'] if s.race == 'Black']
    t_white = [s for s in treatment['seekers'] if s.race == 'White']
    t_black = [s for s in treatment['seekers'] if s.race == 'Black']
    
    if not c_white or not c_black:
        return None
    
    # Calculate approval rates
    c_w_apps = sum(s.num_applications for s in c_white)
    c_b_apps = sum(s.num_applications for s in c_black)
    
    if c_w_apps == 0 or c_b_apps == 0:
        return None
    
    c_w_rate = sum(s.num_approvals for s in c_white) / c_w_apps
    c_b_rate = sum(s.num_approvals for s in c_black) / c_b_apps
    c_gap = c_w_rate - c_b_rate
    
    t_w_apps = sum(s.num_applications for s in t_white)
    t_b_apps = sum(s.num_applications for s in t_black)
    
    if t_w_apps == 0 or t_b_apps == 0:
        return None
    
    t_w_rate = sum(s.num_approvals for s in t_white) / t_w_apps
    t_b_rate = sum(s.num_approvals for s in t_black) / t_b_apps
    t_gap = t_w_rate - t_b_rate
    
    return {
        'iteration': iteration,
        'control_gap': c_gap,
        'treatment_gap': t_gap,
        'treatment_effect': t_gap - c_gap,
        'n_white': len(c_white),
        'n_black': len(c_black),
        'c_applications': c_w_apps + c_b_apps,
        't_applications': t_w_apps + t_b_apps
    }


def main():
    """Run Massachusetts Monte Carlo."""
    print("\n" + "="*70)
    print("MASSACHUSETTS MONTE CARLO PARALLEL WORLDS")
    print("="*70)
    print("\nDesign:")
    print("  State: Massachusetts")
    print("  Counties: All 14 MA counties")
    print("  Iterations: 100 random samples")
    print("  Each: Parallel worlds (Control vs Treatment)")
    print("  With: State models + Learning + Fraud history")
    
    # Get MA counties
    acs = load_acs_county_data('src/data/us_census_acs_2022_county_data.csv')
    acs['state'] = acs['county_name'].str.split(', ').str[1]
    
    ma_counties = acs[acs['state'] == 'Massachusetts']['county_name'].tolist()
    
    print(f"\nMassachusetts counties: {len(ma_counties)}")
    for i, county in enumerate(ma_counties, 1):
        print(f"  {i:2d}. {county}")
    
    print(f"\nSimulation parameters:")
    print(f"  Total seekers: 1,000 (proportional allocation)")
    print(f"  Months: 12")
    print(f"  Iterations: 100")
    print(f"  Total simulations: 200 (100 × 2 worlds)")
    print(f"  Estimated time: 1-2 hours")
    
    response = input("\nContinue? (y/n): ")
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
            print(f"Iteration {i+1}/100 ({(i+1)}%)", flush=True)
        elif i == 0:
            print(f"Iteration {i+1}/100", flush=True)
        
        try:
            effect = run_parallel_worlds_one_iteration(
                counties=ma_counties,
                n_seekers=1000,
                n_months=12,
                iteration_seed=i
            )
            
            if effect:
                results.append(effect)
                
        except Exception as e:
            print(f"  Error iteration {i+1}: {e}")
            continue
    
    # Analyze results
    print(f"\n{'='*70}")
    print("MASSACHUSETTS MONTE CARLO RESULTS")
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
    print(f"  Mean: {mean_effect*100:+.2f}pp")
    print(f"  SE: {se*100:.2f}pp")
    print(f"  95% CI: [{ci_lower*100:+.2f}pp, {ci_upper*100:+.2f}pp]")
    print(f"  Range: [{np.min(effects)*100:+.2f}pp, {np.max(effects)*100:+.2f}pp]")
    print(f"  SD: {np.std(effects)*100:.2f}pp")
    
    # Statistical test
    from scipy import stats
    t_stat, p_value = stats.ttest_1samp(effects, 0)
    
    print(f"\nStatistical test (H0: effect = 0):")
    print(f"  t = {t_stat:.3f}")
    print(f"  p = {p_value:.4f}")
    
    if p_value < 0.05:
        print(f"  ✓ Significantly different from zero!")
    else:
        print(f"  ⚠ Not significant (null effect)")
    
    # Save
    import os
    os.makedirs('results', exist_ok=True)
    
    results_df.to_csv('results/monte_carlo_massachusetts.csv', index=False)
    
    summary = {
        'state': 'Massachusetts',
        'n_counties': len(ma_counties),
        'n_iterations': len(results_df),
        'mean_effect': mean_effect,
        'se': se,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        't_stat': t_stat,
        'p_value': p_value
    }
    
    pd.DataFrame([summary]).to_csv('results/monte_carlo_massachusetts_summary.csv', index=False)
    
    print(f"\n✓ Results saved:")
    print(f"  - results/monte_carlo_massachusetts.csv")
    print(f"  - results/monte_carlo_massachusetts_summary.csv")
    
    print(f"\n{'='*70}")
    print("COMPLETE")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()