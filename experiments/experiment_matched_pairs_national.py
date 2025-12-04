"""
National Matched County-Pair Experiment

Runs AI sorting experiment with matched pairs from across the US.

Advantages over state-only:
- Generalizable to national policy
- More variation (different state policies)
- Larger sample size (20 pairs)
- Better external validity

Run with: python experiments/experiment_matched_pairs_national.py
"""

import sys
sys.path.insert(0, 'src')
import numpy as np
import pandas as pd

from simulation.runner import run_simulation_with_real_data
from ai.application_sorter import AI_ApplicationSorter


def load_national_pairs(filepath='data/matched_county_pairs_national.csv'):
    """Load national matched county pairs."""
    try:
        pairs_df = pd.read_csv(filepath)
        pairs = []
        for _, row in pairs_df.iterrows():
            pairs.append((row['control_county'], row['treatment_county']))
        
        print(f"Loaded {len(pairs)} matched pairs from national sample")
        
        # Show geographic coverage
        cross_state = sum(pairs_df['cross_state'])
        print(f"  Cross-state pairs: {cross_state}/{len(pairs)} ({cross_state/len(pairs)*100:.0f}%)")
        
        states = set(pairs_df['control_state']) | set(pairs_df['treatment_state'])
        print(f"  States covered: {len(states)}")
        print(f"  States: {', '.join(sorted(states)[:10])}...")
        
        return pairs
    except FileNotFoundError:
        print(f"Error: {filepath} not found!")
        print(f"Run: python scripts/match_counties_national.py first")
        return None


def run_matched_pair(pair_id, county_control, county_treatment, n_seekers_per_county, n_months, random_seed):
    """
    Run one matched pair experiment.
    
    Same as state-level, but with national counties.
    """
    print(f"\n{'='*70}")
    print(f"Progress: Pair {pair_id} ({pair_id} complete)")
    print(f"{'='*70}")
    print(f"PAIR {pair_id}: {county_control} vs {county_treatment}")
    
    # Extract states for display
    state_control = county_control.split(', ')[1]
    state_treatment = county_treatment.split(', ')[1]
    
    if state_control != state_treatment:
        print(f"  [CROSS-STATE: {state_control} vs {state_treatment}]")
    
    # Run control
    print(f"\n  Running CONTROL ({county_control}, FCFS)...")
    control = run_simulation_with_real_data(
        cps_file='src/data/cps_asec_2022_processed_full.csv',
        acs_file='src/data/us_census_acs_2022_county_data.csv',
        n_seekers=n_seekers_per_county,
        n_months=n_months,
        counties=[county_control],
        ai_sorter=None,
        random_seed=random_seed + pair_id
    )
    
    # Run treatment
    print(f"\n  Running TREATMENT ({county_treatment}, AI Simple-First)...")
    ai = AI_ApplicationSorter(strategy='simple_first')
    treatment = run_simulation_with_real_data(
        cps_file='src/data/cps_asec_2022_processed_full.csv',
        acs_file='src/data/us_census_acs_2022_county_data.csv',
        n_seekers=n_seekers_per_county,
        n_months=n_months,
        counties=[county_treatment],
        ai_sorter=ai,
        random_seed=random_seed + pair_id
    )
    
    # Compare outcomes (use same compare_pair function)
    from experiments.experiment_matched_pairs import compare_pair
    return compare_pair(pair_id, control, treatment, county_control, county_treatment)


def aggregate_results(pair_results):
    """Same aggregation as state-level, with additional regional analysis."""
    print(f"\n{'='*70}")
    print(f"NATIONAL AGGREGATE RESULTS")
    print(f"{'='*70}\n")
    
    valid_pairs = [p for p in pair_results if p['treatment_effect'] is not None]
    
    print(f"Valid pairs: {len(valid_pairs)} of {len(pair_results)}")
    
    if not valid_pairs:
        print("No valid pairs!")
        return None
    
    # Calculate ATE
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
    elif p_value < 0.10:
        print(f"  ⚠ Marginally significant (p < 0.10)")
    else:
        print(f"  ⚠ Not significant (p >= 0.10)")
    
    # Efficiency
    control_total_apps = sum(p['control_total_apps'] for p in valid_pairs)
    treatment_total_apps = sum(p['treatment_total_apps'] for p in valid_pairs)
    
    control_total_approved = sum(p['control_total_apps'] * p['control_approval_rate'] for p in valid_pairs)
    treatment_total_approved = sum(p['treatment_total_apps'] * p['treatment_approval_rate'] for p in valid_pairs)
    
    print(f"\nOverall Efficiency:")
    print(f"  Control: {control_total_approved:.0f} approved of {control_total_apps:.0f} ({control_total_approved/control_total_apps:.1%})")
    print(f"  Treatment: {treatment_total_approved:.0f} approved of {treatment_total_apps:.0f} ({treatment_total_approved/treatment_total_apps:.1%})")
    
    efficiency_gain = treatment_total_approved - control_total_approved
    print(f"  Efficiency gain: {efficiency_gain:+.0f} applications ({efficiency_gain/control_total_approved*100:+.1f}%)")
    
    return {
        'ate': ate,
        'se': se,
        't_stat': t_stat,
        'p_value': p_value,
        'n_pairs': len(valid_pairs),
        'efficiency_gain': efficiency_gain,
        'control_total_apps': control_total_apps,
        'treatment_total_apps': treatment_total_apps
    }


def main():
    """Run national matched pairs experiment."""
    print("\n" + "="*70)
    print("NATIONAL MATCHED COUNTY-PAIR EXPERIMENT")
    print("="*70)
    print("\nResearch Question:")
    print("  Does AI application sorting create racial disparities?")
    print("  (National sample for generalizability)")
    print("\nDesign:")
    print("  - 20 matched pairs from across the US")
    print("  - Medium-sized counties (50k-500k pop)")
    print("  - Random assignment to AI vs FCFS")
    print("  - Nationwide policy inference")
    
    # Load matched pairs
    matched_pairs = load_national_pairs()
    
    if not matched_pairs:
        print("\nRun matching first:")
        print("  python scripts/match_counties_national.py")
        return
    
    # Run experiments
    pair_results = []
    
    print(f"\nRunning {len(matched_pairs)} matched pairs...")
    print(f"Estimated time: {len(matched_pairs) * 2} minutes\n")
    
    for i, (county_control, county_treatment) in enumerate(matched_pairs, 1):
        result = run_matched_pair(
            pair_id=i,
            county_control=county_control,
            county_treatment=county_treatment,
            n_seekers_per_county=200,
            n_months=12,
            random_seed=42
        )
        pair_results.append(result)
    
    # Save results
    import os
    os.makedirs('results', exist_ok=True)
    
    results_data = []
    for p in pair_results:
        if p['treatment_effect'] is not None:
            results_data.append({
                'pair_id': p['pair_id'],
                'control_county': p['control_county'],
                'treatment_county': p['treatment_county'],
                'control_state': p['control_county'].split(', ')[1],
                'treatment_state': p['treatment_county'].split(', ')[1],
                'cross_state': p['control_county'].split(', ')[1] != p['treatment_county'].split(', ')[1],
                'control_gap': p['control_gap'],
                'treatment_gap': p['treatment_gap'],
                'treatment_effect': p['treatment_effect'],
                'control_approval_rate': p['control_approval_rate'],
                'treatment_approval_rate': p['treatment_approval_rate']
            })
    
    results_df = pd.DataFrame(results_data)
    results_df.to_csv('results/matched_pairs_national_results.csv', index=False)
    print(f"\n✓ Results saved to: results/matched_pairs_national_results.csv")
    
    # Aggregate
    aggregate = aggregate_results(pair_results)
    
    print("\n" + "="*70)
    print("NATIONAL EXPERIMENT COMPLETE")
    print("="*70)
    
    if aggregate:
        if aggregate['p_value'] < 0.05:
            if aggregate['ate'] > 0:
                print(f"\n✓ FINDING: AI sorting INCREASES racial disparity nationwide")
            else:
                print(f"\n✓ FINDING: AI sorting DECREASES racial disparity nationwide")
            print(f"  Average effect: {aggregate['ate']:+.1%}")
            print(f"  Statistically significant: Yes (p = {aggregate['p_value']:.4f})")
        else:
            print(f"\n⚠ FINDING: AI effect not statistically significant at national level")
            print(f"  Average effect: {aggregate['ate']:+.1%}")
            print(f"  p-value: {aggregate['p_value']:.4f}")
            print(f"  Interpretation: Effects are heterogeneous or underpowered")


if __name__ == "__main__":
    main()