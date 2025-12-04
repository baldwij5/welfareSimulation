"""
50-State Comprehensive Experiment

Runs parallel worlds experiment for EVERY state in the US.

Design:
- For each state: Select representative counties
- Create population proportional to state's eligible population
- Run Control (FCFS) and Treatment (AI) on SAME population
- Calculate treatment effect for each state
- Aggregate for national estimate with state-level heterogeneity

Run with: python experiments/experiment_50_states.py
Time: ~2-3 hours for all 50 states
"""

import sys
sys.path.insert(0, 'src')
import numpy as np
import pandas as pd
import copy

from data.data_loader import create_realistic_population, load_acs_county_data
from simulation.runner import create_evaluators, create_reviewers, run_month
from ai.application_sorter import AI_ApplicationSorter


def select_representative_counties_by_state(acs_data, min_population=50000, max_counties_per_state=5):
    """
    Select representative counties for each state.
    
    Strategy:
    - For each state, select 1-5 largest counties (above min population)
    - This ensures we capture most of the state's eligible population
    - While keeping simulation manageable
    
    Args:
        acs_data: ACS DataFrame
        min_population: Minimum county population to include
        max_counties_per_state: Maximum counties per state (default: 5)
        
    Returns:
        dict: {state: [county_names]}
    """
    # Parse state from county_name
    acs_data['state'] = acs_data['county_name'].str.split(', ').str[1]
    
    # Filter to minimum population
    acs_filtered = acs_data[acs_data['total_county_population'] >= min_population].copy()
    
    state_counties = {}
    
    for state in acs_filtered['state'].unique():
        state_data = acs_filtered[acs_filtered['state'] == state].copy()
        
        # Sort by population (largest first)
        state_data = state_data.sort_values('total_county_population', ascending=False)
        
        # Take top N counties
        top_counties = state_data.head(max_counties_per_state)['county_name'].tolist()
        
        state_counties[state] = top_counties
    
    return state_counties


def calculate_state_seekers(acs_data, state_counties, total_seekers=25000):
    """
    Allocate seekers to each state proportionally to eligible population.
    
    Args:
        acs_data: ACS DataFrame
        state_counties: Dict of {state: [counties]}
        total_seekers: Total seekers across all states
        
    Returns:
        dict: {state: n_seekers}
    """
    acs_data['state'] = acs_data['county_name'].str.split(', ').str[1]
    
    state_eligible_pops = {}
    
    for state, counties in state_counties.items():
        # Sum eligible population for selected counties
        total_eligible = 0
        for county in counties:
            county_data = acs_data[acs_data['county_name'] == county]
            if len(county_data) > 0:
                pop = county_data.iloc[0]['total_county_population']
                poverty = county_data.iloc[0]['poverty_rate']
                eligible = pop * (poverty / 100 * 2.5)
                total_eligible += eligible
        
        state_eligible_pops[state] = total_eligible
    
    # Total eligible
    grand_total = sum(state_eligible_pops.values())
    
    # Allocate proportionally
    state_allocations = {}
    for state, eligible in state_eligible_pops.items():
        proportion = eligible / grand_total
        n_seekers = max(100, int(total_seekers * proportion))  # Minimum 100 per state
        state_allocations[state] = n_seekers
    
    return state_allocations


def run_state_experiment(state, counties, n_seekers, n_months, cps_file, acs_file, random_seed):
    """
    Run parallel worlds experiment for one state.
    
    Args:
        state: State name
        counties: List of counties in this state
        n_seekers: Seekers for this state
        n_months: Months to simulate
        cps_file: CPS data path
        acs_file: ACS data path
        random_seed: Random seed
        
    Returns:
        dict: State-level results
    """
    print(f"\n{'='*70}")
    print(f"STATE: {state}")
    print(f"{'='*70}")
    print(f"  Counties: {len(counties)}")
    print(f"  Seekers: {n_seekers}")
    
    # Create shared population for this state
    seekers_master = create_realistic_population(
        cps_file=cps_file,
        acs_file=acs_file,
        n_seekers=n_seekers,
        counties=counties,
        proportional=True,
        random_seed=random_seed
    )
    
    # Run Control (FCFS)
    print(f"\n  Running Control (FCFS)...")
    control = run_state_simulation(seekers_master, counties, acs_file, n_months, 
                                   ai_sorter=None, random_seed=random_seed)
    
    # Run Treatment (AI)
    print(f"  Running Treatment (AI)...")
    ai_tool = AI_ApplicationSorter('simple_first')
    treatment = run_state_simulation(seekers_master, counties, acs_file, n_months,
                                     ai_sorter=ai_tool, random_seed=random_seed)
    
    # Calculate treatment effect
    result = calculate_state_effect(state, control, treatment)
    
    return result


def run_state_simulation(seekers_master, counties, acs_file, n_months, ai_sorter, random_seed):
    """Run one simulation (control or treatment) for a state."""
    from data.data_loader import load_acs_county_data
    
    # Create fresh copies of seekers
    seekers = []
    for original in seekers_master:
        from core.seeker import Seeker
        fresh = Seeker(
            seeker_id=original.id,
            race=original.race,
            income=original.income,
            county=original.county,
            has_children=original.has_children,
            has_disability=original.has_disability,
            cps_data=original.cps_data,
            random_state=np.random.RandomState(original.id)
        )
        seekers.append(fresh)
    
    # Create staff
    acs_data = load_acs_county_data(acs_file)
    evaluators = create_evaluators(counties, acs_data=acs_data, random_seed=random_seed)
    reviewers = create_reviewers(counties, acs_data=acs_data, random_seed=random_seed)
    
    # Run simulation
    for month in range(n_months):
        run_month(seekers, evaluators, reviewers, month, ai_sorter=ai_sorter)
    
    # Return results
    return {
        'seekers': seekers,
        'total_apps': sum(s.num_applications for s in seekers),
        'total_approved': sum(s.num_approvals for s in seekers)
    }


def calculate_state_effect(state, control, treatment):
    """Calculate treatment effect for one state."""
    # Get outcomes by race
    c_white = [s for s in control['seekers'] if s.race == 'White']
    c_black = [s for s in control['seekers'] if s.race == 'Black']
    t_white = [s for s in treatment['seekers'] if s.race == 'White']
    t_black = [s for s in treatment['seekers'] if s.race == 'Black']
    
    if not c_white or not c_black or not t_white or not t_black:
        return {
            'state': state,
            'control_gap': None,
            'treatment_gap': None,
            'treatment_effect': None,
            'n_white': len(c_white) if c_white else 0,
            'n_black': len(c_black) if c_black else 0,
            'skipped': True
        }
    
    # Calculate approval rates
    c_white_rate = sum(s.num_approvals for s in c_white) / sum(s.num_applications for s in c_white)
    c_black_rate = sum(s.num_approvals for s in c_black) / sum(s.num_applications for s in c_black)
    c_gap = c_white_rate - c_black_rate
    
    t_white_rate = sum(s.num_approvals for s in t_white) / sum(s.num_applications for s in t_white)
    t_black_rate = sum(s.num_approvals for s in t_black) / sum(s.num_applications for s in t_black)
    t_gap = t_white_rate - t_black_rate
    
    effect = t_gap - c_gap
    
    print(f"\n  Results:")
    print(f"    Control gap: {c_gap*100:+.1f}pp")
    print(f"    Treatment gap: {t_gap*100:+.1f}pp")
    print(f"    Effect: {effect*100:+.1f}pp")
    
    return {
        'state': state,
        'control_gap': c_gap,
        'treatment_gap': t_gap,
        'treatment_effect': effect,
        'control_white_rate': c_white_rate,
        'control_black_rate': c_black_rate,
        'treatment_white_rate': t_white_rate,
        'treatment_black_rate': t_black_rate,
        'n_white': len(c_white),
        'n_black': len(c_black),
        'control_total_apps': control['total_apps'],
        'treatment_total_apps': treatment['total_apps'],
        'skipped': False
    }


def aggregate_national_results(state_results):
    """Aggregate treatment effects across all states."""
    print(f"\n{'='*70}")
    print(f"NATIONAL AGGREGATE RESULTS (50 STATES)")
    print(f"{'='*70}\n")
    
    # Filter to valid states
    valid_states = [s for s in state_results if not s['skipped']]
    
    print(f"Valid states: {len(valid_states)} of {len(state_results)}")
    
    if not valid_states:
        print("No valid states!")
        return None
    
    # Calculate national ATE (unweighted)
    effects = [s['treatment_effect'] for s in valid_states]
    ate = np.mean(effects)
    se = np.std(effects) / np.sqrt(len(effects))
    
    print(f"\nAverage Treatment Effect (ATE) - Unweighted:")
    print(f"  Mean: {ate*100:+.1f}pp")
    print(f"  SE: {se*100:.1f}pp")
    print(f"  95% CI: [{(ate - 1.96*se)*100:+.1f}pp, {(ate + 1.96*se)*100:+.1f}pp]")
    
    # Statistical test
    from scipy import stats
    t_stat = ate / se
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), len(valid_states) - 1))
    
    print(f"\nOne-sample t-test (H0: effect = 0):")
    print(f"  t-statistic: {t_stat:.3f}")
    print(f"  p-value: {p_value:.4f}")
    
    if p_value < 0.05:
        print(f"  ✓ Statistically significant (p < 0.05)")
    else:
        print(f"  ⚠ Not significant (p >= 0.05)")
    
    # Heterogeneity
    print(f"\nHeterogeneity across states:")
    print(f"  Min effect: {min(effects)*100:+.1f}pp")
    print(f"  Max effect: {max(effects)*100:+.1f}pp")
    print(f"  Range: {(max(effects) - min(effects))*100:.1f}pp")
    print(f"  SD: {np.std(effects)*100:.1f}pp")
    
    # Regional patterns
    print(f"\n  States where AI INCREASED disparity (effect > +2pp): {sum(1 for e in effects if e > 0.02)}")
    print(f"  States where AI DECREASED disparity (effect < -2pp): {sum(1 for e in effects if e < -0.02)}")
    print(f"  States with no effect (-2pp to +2pp): {sum(1 for e in effects if -0.02 <= e <= 0.02)}")
    
    return {
        'ate': ate,
        'se': se,
        't_stat': t_stat,
        'p_value': p_value,
        'n_states': len(valid_states),
        'min_effect': min(effects),
        'max_effect': max(effects),
        'sd': np.std(effects)
    }


def main():
    """Run 50-state experiment."""
    print("\n" + "="*70)
    print("50-STATE COMPREHENSIVE EXPERIMENT")
    print("="*70)
    print("\nResearch Question:")
    print("  Does AI sorting affect racial disparities in welfare?")
    print("  National evidence from all 50 states")
    print("\nDesign:")
    print("  - For EACH state: Select representative counties")
    print("  - Create population proportional to state size")
    print("  - Run parallel worlds (Control vs Treatment)")
    print("  - Calculate state-level treatment effects")
    print("  - Aggregate for national estimate")
    print("\nTotal simulations: 100 (50 states × 2 conditions)")
    print("Estimated time: 2-3 hours")
    
    # Load ACS data
    acs = load_acs_county_data('src/data/us_census_acs_2022_county_data.csv')
    
    # Select counties for each state
    print(f"\n{'='*70}")
    print("SELECTING REPRESENTATIVE COUNTIES BY STATE")
    print(f"{'='*70}")
    
    state_counties = select_representative_counties_by_state(
        acs_data=acs,
        min_population=50000,
        max_counties_per_state=3  # 1-3 largest counties per state
    )
    
    print(f"\nSelected counties for {len(state_counties)} states")
    
    # Calculate seeker allocation by state
    print(f"\nCalculating seeker allocation by state...")
    state_allocations = calculate_state_seekers(
        acs_data=acs,
        state_counties=state_counties,
        total_seekers=25000  # 25k total across all states
    )
    
    print(f"\nTop 10 states by seekers:")
    top_10 = sorted(state_allocations.items(), key=lambda x: x[1], reverse=True)[:10]
    for state, n in top_10:
        print(f"  {state}: {n} seekers")
    
    # Ask for confirmation
    print(f"\n{'='*70}")
    print(f"READY TO RUN EXPERIMENT")
    print(f"{'='*70}")
    print(f"\nWill run:")
    print(f"  - {len(state_counties)} states")
    print(f"  - {sum(state_allocations.values())} total seekers")
    print(f"  - 100 simulations (50 control + 50 treatment)")
    print(f"  - Estimated time: 2-3 hours")
    
    response = input(f"\nContinue? (y/n): ")
    if response.lower() != 'y':
        print("Experiment cancelled.")
        return
    
    # Run experiments for all states
    state_results = []
    
    for i, (state, counties) in enumerate(state_counties.items(), 1):
        n_seekers = state_allocations.get(state, 100)
        
        print(f"\n{'='*70}")
        print(f"Progress: State {i} of {len(state_counties)} ({i/len(state_counties)*100:.0f}% complete)")
        print(f"{'='*70}")
        
        try:
            result = run_state_experiment(
                state=state,
                counties=counties,
                n_seekers=n_seekers,
                n_months=12,
                cps_file='src/data/cps_asec_2022_processed_full.csv',
                acs_file='src/data/us_census_acs_2022_county_data.csv',
                random_seed=42 + i
            )
            state_results.append(result)
            
        except Exception as e:
            print(f"  ⚠️ Error in {state}: {e}")
            state_results.append({
                'state': state,
                'skipped': True,
                'error': str(e)
            })
            continue
        
        # Save intermediate results every 10 states
        if i % 10 == 0:
            import os
            os.makedirs('results', exist_ok=True)
            
            temp_df = pd.DataFrame([s for s in state_results if not s.get('skipped')])
            temp_df.to_csv(f'results/50_states_checkpoint_{i}.csv', index=False)
            print(f"\n  ✓ Checkpoint saved (after {i} states)")
    
    # Save final results
    import os
    os.makedirs('results', exist_ok=True)
    
    results_df = pd.DataFrame([s for s in state_results if not s.get('skipped')])
    results_df.to_csv('results/50_states_results.csv', index=False)
    
    print(f"\n✓ Complete results saved: results/50_states_results.csv")
    
    # Aggregate
    aggregate = aggregate_national_results(state_results)
    
    # Save aggregate
    if aggregate:
        summary = pd.DataFrame([aggregate])
        summary.to_csv('results/50_states_summary.csv', index=False)
    
    print(f"\n{'='*70}")
    print(f"50-STATE EXPERIMENT COMPLETE")
    print(f"{'='*70}")
    
    if aggregate:
        if aggregate['p_value'] < 0.05:
            if aggregate['ate'] > 0:
                print(f"\n✓ FINDING: AI sorting INCREASES racial disparity nationwide")
            else:
                print(f"\n✓ FINDING: AI sorting DECREASES racial disparity nationwide")
            print(f"  Average effect: {aggregate['ate']*100:+.1f}pp")
            print(f"  Statistically significant (p = {aggregate['p_value']:.4f})")
        else:
            print(f"\n⚠ FINDING: No significant national effect")
            print(f"  Average effect: {aggregate['ate']*100:+.1f}pp")
            print(f"  p-value: {aggregate['p_value']:.4f}")
        
        print(f"\n  Heterogeneity: SD = {aggregate['sd']*100:.1f}pp")
        print(f"  Range: {aggregate['min_effect']*100:+.1f}pp to {aggregate['max_effect']*100:+.1f}pp")
    
    print(f"\n✓ Results files:")
    print(f"  - results/50_states_results.csv (state-by-state)")
    print(f"  - results/50_states_summary.csv (national aggregate)")


if __name__ == "__main__":
    main()