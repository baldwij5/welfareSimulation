"""
Matched County-Pair Experiment: AI Application Sorter

Runs matched-pairs design comparing control (FCFS) vs treatment (AI).

Design:
- Find matched pairs of similar counties
- Assign one to control (FCFS), one to treatment (AI)
- Compare within pairs
- Aggregate across pairs

Run with: python experiments/experiment_matched_pairs.py
"""

import sys
sys.path.insert(0, 'src')
import numpy as np
import pandas as pd

from simulation.runner import run_simulation_with_real_data
from ai.application_sorter import AI_ApplicationSorter


def load_matched_pairs(filepath='data/matched_county_pairs.csv'):
    """Load pre-computed matched county pairs."""
    try:
        pairs_df = pd.read_csv(filepath)
        pairs = []
        for _, row in pairs_df.iterrows():
            pairs.append((row['control_county'], row['treatment_county']))
        return pairs
    except FileNotFoundError:
        print(f"Error: {filepath} not found!")
        print(f"Run: python scripts/match_counties.py first")
        return None


def run_matched_pair(pair_id, county_control, county_treatment, n_seekers_per_county, n_months, random_seed):
    """
    Run one matched pair experiment.
    
    Args:
        pair_id: Pair number
        county_control: Control county (FCFS)
        county_treatment: Treatment county (AI)
        n_seekers_per_county: Seekers per county
        n_months: Months to simulate
        random_seed: Base random seed
        
    Returns:
        dict: Pair results
    """
    print(f"\n{'='*70}")
    print(f"PAIR {pair_id}: {county_control} vs {county_treatment}")
    print(f"{'='*70}")
    
    # Run control
    print(f"\nRunning CONTROL ({county_control}, FCFS)...")
    control = run_simulation_with_real_data(
        cps_file='src/data/cps_asec_2022_processed_full.csv',
        acs_file='src/data/us_census_acs_2022_county_data.csv',
        n_seekers=n_seekers_per_county,
        n_months=n_months,
        counties=[county_control],
        ai_sorter=None,  # FCFS
        random_seed=random_seed + pair_id
    )
    
    # Run treatment
    print(f"\nRunning TREATMENT ({county_treatment}, AI Simple-First)...")
    ai = AI_ApplicationSorter(strategy='simple_first')
    treatment = run_simulation_with_real_data(
        cps_file='src/data/cps_asec_2022_processed_full.csv',
        acs_file='src/data/us_census_acs_2022_county_data.csv',
        n_seekers=n_seekers_per_county,
        n_months=n_months,
        counties=[county_treatment],
        ai_sorter=ai,  # AI sorting
        random_seed=random_seed + pair_id  # Same seed for comparison
    )
    
    # Compare outcomes
    return compare_pair(pair_id, control, treatment, county_control, county_treatment)


def compare_pair(pair_id, control, treatment, county_control, county_treatment):
    """
    Compare outcomes between control and treatment counties.
    
    Returns:
        dict: Pair-level results
    """
    # Calculate outcomes by race for each condition
    def get_race_stats(results, race):
        race_seekers = [s for s in results['seekers'] if s.race == race]
        if not race_seekers:
            return None
        
        apps = sum(s.num_applications for s in race_seekers)
        approved = sum(s.num_approvals for s in race_seekers)
        investigated = sum(s.num_investigations for s in race_seekers)
        
        return {
            'n_seekers': len(race_seekers),
            'applications': apps,
            'approvals': approved,
            'approval_rate': approved / apps if apps > 0 else 0,
            'investigations': investigated,
            'investigation_rate': investigated / apps if apps > 0 else 0
        }
    
    # Control outcomes
    control_white = get_race_stats(control, 'White')
    control_black = get_race_stats(control, 'Black')
    
    # Treatment outcomes
    treatment_white = get_race_stats(treatment, 'White')
    treatment_black = get_race_stats(treatment, 'Black')
    
    # Calculate gaps
    control_gap = None
    treatment_gap = None
    treatment_effect = None
    
    if control_white and control_black:
        control_gap = control_white['approval_rate'] - control_black['approval_rate']
    
    if treatment_white and treatment_black:
        treatment_gap = treatment_white['approval_rate'] - treatment_black['approval_rate']
    
    if control_gap is not None and treatment_gap is not None:
        treatment_effect = treatment_gap - control_gap
    
    # Print pair results
    print(f"\n  PAIR {pair_id} RESULTS:")
    print(f"  {'':20} | {'Control':>12} | {'Treatment':>12}")
    print(f"  {'-'*20}-+-{'-'*12}-+-{'-'*12}")
    
    if control_white and treatment_white:
        print(f"  {'White approval':<20} | {control_white['approval_rate']:>11.1%} | {treatment_white['approval_rate']:>11.1%}")
    if control_black and treatment_black:
        print(f"  {'Black approval':<20} | {control_black['approval_rate']:>11.1%} | {treatment_black['approval_rate']:>11.1%}")
    
    if control_gap is not None and treatment_gap is not None:
        print(f"  {'Racial gap':<20} | {control_gap:>11.1%} | {treatment_gap:>11.1%}")
        print(f"\n  Treatment Effect: {treatment_effect:+.1%}")
        if treatment_effect > 0.01:
            print(f"  → AI INCREASED disparity")
        elif treatment_effect < -0.01:
            print(f"  → AI DECREASED disparity")
        else:
            print(f"  → No significant effect")
    
    return {
        'pair_id': pair_id,
        'control_county': county_control,
        'treatment_county': county_treatment,
        'control_white': control_white,
        'control_black': control_black,
        'treatment_white': treatment_white,
        'treatment_black': treatment_black,
        'control_gap': control_gap,
        'treatment_gap': treatment_gap,
        'treatment_effect': treatment_effect,
        'control_total_apps': control['summary']['total_applications'],
        'treatment_total_apps': treatment['summary']['total_applications'],
        'control_approval_rate': control['summary']['approval_rate'],
        'treatment_approval_rate': treatment['summary']['approval_rate']
    }


def aggregate_results(pair_results):
    """
    Aggregate treatment effects across all pairs.
    
    Args:
        pair_results: List of pair-level results
        
    Returns:
        dict: Aggregate statistics
    """
    print(f"\n{'='*70}")
    print(f"AGGREGATE RESULTS ACROSS PAIRS")
    print(f"{'='*70}\n")
    
    # Filter to pairs with valid treatment effects
    valid_pairs = [p for p in pair_results if p['treatment_effect'] is not None]
    
    print(f"Valid pairs: {len(valid_pairs)} of {len(pair_results)}")
    
    if not valid_pairs:
        print("No valid pairs with both races!")
        return None
    
    # Calculate average treatment effect
    treatment_effects = [p['treatment_effect'] for p in valid_pairs]
    ate = np.mean(treatment_effects)
    se = np.std(treatment_effects) / np.sqrt(len(treatment_effects))
    
    print(f"\nAverage Treatment Effect (ATE):")
    print(f"  Mean: {ate:+.1%}")
    print(f"  SE: {se:.1%}")
    print(f"  95% CI: [{ate - 1.96*se:+.1%}, {ate + 1.96*se:+.1%}]")
    
    # Paired t-test
    control_gaps = [p['control_gap'] for p in valid_pairs]
    treatment_gaps = [p['treatment_gap'] for p in valid_pairs]
    
    from scipy import stats
    t_stat, p_value = stats.ttest_rel(treatment_gaps, control_gaps)
    
    print(f"\nPaired t-test:")
    print(f"  t-statistic: {t_stat:.3f}")
    print(f"  p-value: {p_value:.4f}")
    
    if p_value < 0.05:
        print(f"  ✓ Statistically significant (p < 0.05)")
    else:
        print(f"  ⚠ Not significant (p >= 0.05)")
    
    # Efficiency analysis
    control_total = sum(p['control_total_apps'] for p in valid_pairs)
    treatment_total = sum(p['treatment_total_apps'] for p in valid_pairs)
    
    control_approved = sum(p['control_total_apps'] * p['control_approval_rate'] 
                          for p in valid_pairs)
    treatment_approved = sum(p['treatment_total_apps'] * p['treatment_approval_rate'] 
                            for p in valid_pairs)
    
    print(f"\nOverall Efficiency:")
    print(f"  Control: {control_approved:.0f} approved of {control_total:.0f} ({control_approved/control_total:.1%})")
    print(f"  Treatment: {treatment_approved:.0f} approved of {treatment_total:.0f} ({treatment_approved/treatment_total:.1%})")
    
    efficiency_gain = treatment_approved - control_approved
    print(f"  Efficiency gain: {efficiency_gain:+.0f} applications ({efficiency_gain/control_approved*100:+.1f}%)")
    
    return {
        'ate': ate,
        'se': se,
        't_stat': t_stat,
        'p_value': p_value,
        'n_pairs': len(valid_pairs),
        'efficiency_gain': efficiency_gain
    }


def main():
    """Run matched pairs experiment."""
    print("\n" + "="*70)
    print("MATCHED COUNTY-PAIR EXPERIMENT")
    print("="*70)
    print("\nResearch Question:")
    print("  Does AI application sorting create racial disparities?")
    print("\nDesign:")
    print("  - Match similar counties on demographics")
    print("  - Randomly assign to control (FCFS) vs treatment (AI)")
    print("  - Compare within pairs")
    print("  - Aggregate treatment effect")
    
    # Load matched pairs
    matched_pairs = load_matched_pairs()
    
    if not matched_pairs:
        print("\nNo matched pairs found. Run matching first:")
        print("  python scripts/match_counties.py")
        return
    
    print(f"\nLoaded {len(matched_pairs)} matched pairs")
    
    # Run each pair
    pair_results = []
    
    print(f"\nRunning {len(matched_pairs)} matched pairs...")
    print(f"This will take approximately {len(matched_pairs) * 2} minutes.\n")
    
    for i, (county_control, county_treatment) in enumerate(matched_pairs, 1):
        print(f"\n{'='*70}")
        print(f"Progress: Pair {i} of {len(matched_pairs)} ({i/len(matched_pairs)*100:.0f}% complete)")
        print(f"{'='*70}")
        
        result = run_matched_pair(
            pair_id=i,
            county_control=county_control,
            county_treatment=county_treatment,
            n_seekers_per_county=200,
            n_months=12,
            random_seed=42
        )
        pair_results.append(result)
    
    # Save individual pair results
    import os
    os.makedirs('results', exist_ok=True)
    
    results_data = []
    for p in pair_results:
        if p['treatment_effect'] is not None:
            results_data.append({
                'pair_id': p['pair_id'],
                'control_county': p['control_county'],
                'treatment_county': p['treatment_county'],
                'control_gap': p['control_gap'],
                'treatment_gap': p['treatment_gap'],
                'treatment_effect': p['treatment_effect'],
                'control_approval_rate': p['control_approval_rate'],
                'treatment_approval_rate': p['treatment_approval_rate']
            })
    
    import pandas as pd
    results_df = pd.DataFrame(results_data)
    results_df.to_csv('results/matched_pairs_results.csv', index=False)
    print(f"\n✓ Detailed results saved to: results/matched_pairs_results.csv")
    
    # Aggregate
    aggregate = aggregate_results(pair_results)
    
    print("\n" + "="*70)
    print("EXPERIMENT COMPLETE")
    print("="*70)
    
    if aggregate and aggregate['ate'] > 0.01:
        print(f"\n✓ Finding: AI sorting INCREASES racial disparity")
        print(f"  Average effect: {aggregate['ate']:+.1%}")
        print(f"  Statistically significant: {'Yes' if aggregate['p_value'] < 0.05 else 'No'}")
    elif aggregate and aggregate['ate'] < -0.01:
        print(f"\n✓ Finding: AI sorting DECREASES racial disparity")
        print(f"  Average effect: {aggregate['ate']:+.1%}")
        print(f"  Statistically significant: {'Yes' if aggregate['p_value'] < 0.05 else 'No'}")
    else:
        print(f"\n⚠ Finding: AI has no significant effect on disparity")


if __name__ == "__main__":
    main()