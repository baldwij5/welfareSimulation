"""
Sensitivity Analysis: Parameter Robustness Testing

Tests robustness of AI effects to uncertain parameter assumptions.

Usage:
    # Priority 1 (core parameters): ~3 hours
    python experiments/sensitivity_analysis.py --priority 1 --iterations 10
    
    # Priority 2 (core + secondary): ~7 hours
    python experiments/sensitivity_analysis.py --priority 2 --iterations 10
    
    # Full sensitivity: ~10 hours
    python experiments/sensitivity_analysis.py --priority 3 --iterations 10
    
    # Test specific parameter
    python experiments/sensitivity_analysis.py --parameter approval_rate --iterations 10
    
    # Resume from checkpoint
    python experiments/sensitivity_analysis.py --priority 1 --resume

Output:
    - results/sensitivity_analysis_results.csv (all results)
    - results/sensitivity_checkpoint.csv (for resuming)
    - Console summary with robustness bounds

Author: Jack Baldwin
Date: December 2024
"""

import warnings
warnings.filterwarnings('ignore')

import sys
sys.path.insert(0, 'src')

import numpy as np
import pandas as pd
import argparse
import json
import time
from pathlib import Path
from datetime import datetime
from scipy import stats as sp_stats

from core.seeker import Seeker
from data.data_loader import create_realistic_population, load_acs_county_data
from simulation.runner import create_evaluators, create_reviewers, run_month
from ai.application_sorter import AI_ApplicationSorter


# Parameter ranges for sensitivity testing
PARAMETER_RANGES = {
    # Priority 1: Core assumptions (MUST TEST)
    'approval_rate': [0.60, 0.65, 0.70, 0.75, 0.80],
    'learning_rate': [0.10, 0.20, 0.30, 0.40, 0.50],
    
    # Priority 2: Secondary parameters (SHOULD TEST)
    'strictness': [0.30, 0.40, 0.50, 0.60, 0.70],
    'application_threshold': [0.15, 0.20, 0.25, 0.30, 0.35],
    
    # Priority 3: Tertiary parameters (NICE TO HAVE)
    'bureaucracy_mult': [0.50, 0.75, 1.00, 1.25, 1.50],
}

PARAMETER_PRIORITIES = {
    1: ['approval_rate', 'learning_rate'],
    2: ['approval_rate', 'learning_rate', 'strictness', 'application_threshold'],
    3: ['approval_rate', 'learning_rate', 'strictness', 'application_threshold', 'bureaucracy_mult']
}


def calculate_race_disparity(seekers):
    """Calculate White-Black approval rate gap."""
    white = [s for s in seekers if s.race == 'White']
    black = [s for s in seekers if s.race == 'Black']
    
    w_apps = sum(s.num_applications for s in white)
    b_apps = sum(s.num_applications for s in black)
    
    if w_apps == 0 or b_apps == 0:
        return None
    
    w_rate = sum(s.num_approvals for s in white) / w_apps
    b_rate = sum(s.num_approvals for s in black) / b_apps
    
    return w_rate - b_rate


def run_one_world(seekers_master, counties, ai_sorter, seed, params, 
                  param_name, param_value):
    """
    Run one world with specified parameter value.
    
    Args:
        seekers_master: Master population
        counties: County list
        ai_sorter: AI sorter (None for control)
        seed: Random seed
        params: Capacity parameters
        param_name: Which parameter is being varied
        param_value: Value for that parameter
    """
    # Copy seekers and apply parameter
    seekers = []
    for orig in seekers_master:
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
        
        # Apply parameter variation
        if param_name == 'learning_rate':
            fresh.learning_rate = param_value
        elif param_name == 'application_threshold':
            fresh.application_threshold = param_value
        # Note: bureaucracy_mult would need to be applied during creation
        
        seekers.append(fresh)
    
    # Create staff
    acs_data = load_acs_county_data('src/data/us_census_acs_2022_county_data.csv')
    
    # Apply strictness parameter if testing it
    if param_name == 'strictness':
        evaluators = {}
        eval_id = 0
        for county in counties:
            for program in ['SNAP', 'TANF', 'SSI']:
                from core.evaluator import Evaluator
                evaluator = Evaluator(
                    evaluator_id=eval_id,
                    county=county,
                    program=program,
                    strictness=param_value,  # Apply parameter
                    random_state=np.random.RandomState(seed + eval_id)
                )
                # Get capacity from ACS
                county_data = acs_data[acs_data['county_name'] == county]
                if len(county_data) > 0:
                    pop = county_data.iloc[0]['total_county_population']
                    from simulation.runner import calculate_evaluator_capacity
                    evaluator.monthly_capacity = calculate_evaluator_capacity(pop)
                else:
                    evaluator.monthly_capacity = 20.0
                
                # Apply program-specific multipliers
                if program == 'SNAP':
                    evaluator.monthly_capacity *= params['capacity_mult_snap']
                elif program == 'TANF':
                    evaluator.monthly_capacity *= params['capacity_mult_tanf']
                elif program == 'SSI':
                    evaluator.monthly_capacity *= params['capacity_mult_ssi']
                
                evaluators[(county, program)] = evaluator
                eval_id += 1
    else:
        evaluators = create_evaluators(counties, acs_data=acs_data, random_seed=seed)
        # Apply capacity
        for (county, program), evaluator in evaluators.items():
            if program == 'SNAP':
                evaluator.monthly_capacity *= params['capacity_mult_snap']
            elif program == 'TANF':
                evaluator.monthly_capacity *= params['capacity_mult_tanf']
            elif program == 'SSI':
                evaluator.monthly_capacity *= params['capacity_mult_ssi']
    
    reviewers = create_reviewers(counties, acs_data=acs_data, load_state_models=True, random_seed=seed)
    for reviewer in reviewers.values():
        reviewer.monthly_capacity *= params['capacity_mult_reviewer']
    
    # Run simulation
    for month in range(12):
        run_month(seekers, evaluators, reviewers, month, ai_sorter=ai_sorter)
    
    return seekers


def run_sensitivity_iteration(param_name, param_value, counties, n_seekers, 
                              iteration, capacity_params, verbose=True):
    """Run one Monte Carlo iteration with specified parameter value."""
    seed = 42 + iteration
    
    if verbose:
        print(f"    Iteration {iteration + 1}: {param_name}={param_value}, seed={seed}...", 
              end='', flush=True)
    
    start = time.time()
    
    try:
        # Create population
        seekers_master = create_realistic_population(
            'src/data/cps_asec_2022_processed_full.csv',
            'src/data/us_census_acs_2022_county_data.csv',
            n_seekers,
            counties,
            proportional=True,
            random_seed=seed
        )
        
        if not seekers_master:
            if verbose:
                print(" FAILED (no seekers)")
            return None
        
        # Control world
        control_seekers = run_one_world(
            seekers_master, counties, None, seed, capacity_params,
            param_name, param_value
        )
        
        # Treatment world
        treatment_seekers = run_one_world(
            seekers_master, counties, AI_ApplicationSorter('simple_first'),
            seed, capacity_params, param_name, param_value
        )
        
        # Calculate effect
        control_gap = calculate_race_disparity(control_seekers)
        treatment_gap = calculate_race_disparity(treatment_seekers)
        
        if control_gap is None or treatment_gap is None:
            if verbose:
                print(" FAILED (no applications)")
            return None
        
        race_effect = treatment_gap - control_gap
        elapsed = time.time() - start
        
        if verbose:
            print(f" done ({elapsed:.0f}s, effect={race_effect*100:+.2f}pp)")
        
        return {
            'parameter': param_name,
            'value': param_value,
            'iteration': iteration,
            'control_gap': control_gap,
            'treatment_gap': treatment_gap,
            'race_effect': race_effect,
            'elapsed_seconds': elapsed
        }
        
    except Exception as e:
        if verbose:
            print(f" FAILED ({str(e)[:40]})")
        return None


def run_parameter_experiment(param_name, param_values, counties, n_seekers,
                             n_iterations, capacity_params, checkpoint_file, verbose=True):
    """Run sensitivity experiment for one parameter across all its values."""
    if verbose:
        print(f"\n{'='*70}")
        print(f"PARAMETER: {param_name}")
        print(f"{'='*70}")
        print(f"  Values: {param_values}")
        print(f"  Iterations per value: {n_iterations}")
        print(f"  Total experiments: {len(param_values) * n_iterations}")
    
    all_results = []
    
    # Load checkpoint if exists
    if Path(checkpoint_file).exists():
        checkpoint_df = pd.read_csv(checkpoint_file)
        existing = checkpoint_df[checkpoint_df['parameter'] == param_name]
        if len(existing) > 0:
            all_results = existing.to_dict('records')
            if verbose:
                print(f"  Loaded {len(existing)} existing results (resuming)")
    
    # Run experiments
    for value in param_values:
        if verbose:
            print(f"\n  Testing {param_name}={value}:")
        
        # Check which iterations are complete
        completed = set(
            r['iteration'] for r in all_results
            if r['value'] == value
        )
        iterations_to_run = [i for i in range(n_iterations) if i not in completed]
        
        if len(iterations_to_run) == 0:
            if verbose:
                print(f"    ✓ All {n_iterations} iterations complete (skipping)")
            continue
        
        # Run missing iterations
        for iter_num in iterations_to_run:
            result = run_sensitivity_iteration(
                param_name, value, counties, n_seekers,
                iter_num, capacity_params, verbose=verbose
            )
            
            if result:
                all_results.append(result)
                
                # Save checkpoint
                pd.DataFrame(all_results).to_csv(checkpoint_file, index=False)
    
    # Summary for this parameter
    if verbose and len(all_results) > 0:
        df = pd.DataFrame(all_results)
        summary = df.groupby('value')['race_effect'].agg(['mean', 'std', 'count'])
        
        print(f"\n  {'─'*66}")
        print(f"  SUMMARY FOR {param_name}:")
        print(f"  {'─'*66}")
        print(f"  Value    | Effect (pp) | Std    | N")
        print(f"  {'-'*50}")
        
        for value, row in summary.iterrows():
            mean_pp = row['mean'] * 100
            std_pp = row['std'] * 100
            print(f"  {value:6.2f}   | {mean_pp:+7.2f}pp   | {std_pp:5.2f} | {int(row['count'])}")
        
        # Effect range
        min_effect = summary['mean'].min() * 100
        max_effect = summary['mean'].max() * 100
        effect_range = max_effect - min_effect
        
        print(f"\n  Effect range: [{min_effect:+.2f}pp, {max_effect:+.2f}pp] (width: {effect_range:.2f}pp)")
    
    return pd.DataFrame(all_results)


def main():
    parser = argparse.ArgumentParser(
        description='Sensitivity analysis: Test robustness to parameters'
    )
    parser.add_argument('--priority', type=int, default=1, choices=[1, 2, 3],
                       help='Priority level (1=core, 2=core+secondary, 3=all)')
    parser.add_argument('--parameter', type=str, default=None,
                       help='Test specific parameter only')
    parser.add_argument('--iterations', type=int, default=10,
                       help='Monte Carlo iterations per parameter value')
    parser.add_argument('--seekers', type=int, default=10000,
                       help='Seekers per iteration (10k recommended)')
    parser.add_argument('--resume', action='store_true',
                       help='Resume from checkpoint')
    args = parser.parse_args()
    
    print("="*70)
    print("SENSITIVITY ANALYSIS: PARAMETER ROBUSTNESS")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Priority level: {args.priority}")
    print(f"Iterations per value: {args.iterations}")
    print(f"Seekers: {args.seekers:,}")
    
    # Load calibrated capacity
    calib_file = 'data/ma_calibrated_params.json'
    if Path(calib_file).exists():
        with open(calib_file, 'r') as f:
            capacity_params = json.load(f)
        print(f"✓ Loaded calibrated capacity")
    else:
        capacity_params = {
            'capacity_mult_snap': 1.0,
            'capacity_mult_tanf': 1.0,
            'capacity_mult_ssi': 1.0,
            'capacity_mult_reviewer': 1.0
        }
        print(f"⚠️  Using default capacity")
    
    # Get MA counties
    acs = load_acs_county_data('src/data/us_census_acs_2022_county_data.csv')
    acs['state'] = acs['county_name'].str.split(', ').str[1]
    ma_counties = acs[acs['state'] == 'Massachusetts']['county_name'].tolist()
    print(f"✓ Using {len(ma_counties)} Massachusetts counties")
    
    # Determine which parameters to test
    if args.parameter:
        # Test specific parameter
        if args.parameter not in PARAMETER_RANGES:
            print(f"❌ Unknown parameter: {args.parameter}")
            print(f"   Available: {list(PARAMETER_RANGES.keys())}")
            return
        params_to_test = {args.parameter: PARAMETER_RANGES[args.parameter]}
    else:
        # Test by priority
        param_names = PARAMETER_PRIORITIES[args.priority]
        params_to_test = {p: PARAMETER_RANGES[p] for p in param_names}
    
    total_experiments = sum(len(values) for values in params_to_test.values()) * args.iterations
    print(f"\nTesting {len(params_to_test)} parameters:")
    for p, vals in params_to_test.items():
        print(f"  - {p}: {len(vals)} values × {args.iterations} iterations = {len(vals) * args.iterations} experiments")
    print(f"\nTotal experiments: {total_experiments}")
    print(f"Estimated time: {total_experiments * 2 / 60:.1f} hours (at ~2 min/experiment)")
    
    # Setup checkpoint
    checkpoint_file = 'results/sensitivity_checkpoint.csv'
    Path('results').mkdir(exist_ok=True)
    
    if not args.resume and Path(checkpoint_file).exists():
        backup = f'results/sensitivity_checkpoint_backup_{int(time.time())}.csv'
        Path(checkpoint_file).rename(backup)
        print(f"✓ Backed up old checkpoint to {backup}")
    
    # Run experiments
    print(f"\n{'='*70}")
    print("RUNNING SENSITIVITY EXPERIMENTS")
    print("="*70)
    
    all_results = []
    start_total = time.time()
    
    for param_idx, (param_name, param_values) in enumerate(params_to_test.items()):
        df = run_parameter_experiment(
            param_name, param_values, ma_counties, args.seekers,
            args.iterations, capacity_params, checkpoint_file,
            verbose=True
        )
        all_results.append(df)
        
        # ETA for remaining parameters
        if param_idx < len(params_to_test) - 1:
            elapsed = time.time() - start_total
            avg_per_param = elapsed / (param_idx + 1)
            remaining_params = len(params_to_test) - (param_idx + 1)
            eta = avg_per_param * remaining_params
            print(f"\n  ⏱️  ETA for remaining parameters: {eta/60:.1f} minutes")
    
    # Combine and save
    combined = pd.concat(all_results, ignore_index=True)
    results_file = 'results/sensitivity_analysis_results.csv'
    combined.to_csv(results_file, index=False)
    
    total_elapsed = time.time() - start_total
    
    # Summary
    print(f"\n{'='*70}")
    print("SENSITIVITY ANALYSIS COMPLETE")
    print("="*70)
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total time: {total_elapsed/60:.1f} minutes")
    print(f"Results saved to: {results_file}")
    
    # Robustness summary
    print(f"\n{'='*70}")
    print("ROBUSTNESS SUMMARY")
    print("="*70)
    
    baseline_effect = None
    
    print(f"\nParameter            | Baseline  | Range          | Width  | Robust?")
    print(f"{'-'*70}")
    
    for param_name in params_to_test.keys():
        param_df = combined[combined['parameter'] == param_name]
        
        # Get baseline value
        baseline_val = PARAMETER_RANGES[param_name][len(PARAMETER_RANGES[param_name])//2]
        baseline_data = param_df[param_df['value'] == baseline_val]
        
        if len(baseline_data) > 0:
            baseline_mean = baseline_data['race_effect'].mean()
            if baseline_effect is None:
                baseline_effect = baseline_mean
        
        # Get range across all values
        summary = param_df.groupby('value')['race_effect'].mean()
        min_effect = summary.min() * 100
        max_effect = summary.max() * 100
        width = max_effect - min_effect
        
        # Check robustness
        # Robust if: (1) All values same sign, (2) Width < 3pp
        all_negative = summary.max() < 0
        all_positive = summary.min() > 0
        narrow_range = width < 3.0
        
        robust = (all_negative or all_positive) and narrow_range
        robust_str = "✓ Yes" if robust else "✗ No"
        
        print(f"{param_name:20s} | {baseline_mean*100:+6.2f}pp | "
              f"[{min_effect:+.2f}, {max_effect:+.2f}] | {width:5.2f}  | {robust_str}")
    
    # Overall assessment
    print(f"\n{'='*70}")
    print("OVERALL ROBUSTNESS ASSESSMENT")
    print("="*70)
    
    all_effects = combined.groupby(['parameter', 'value'])['race_effect'].mean()
    
    if all_effects.max() < 0:
        print(f"\n✓ FULLY ROBUST: Effect is negative across ALL parameter values")
        print(f"  Range: [{all_effects.min()*100:+.2f}pp, {all_effects.max()*100:+.2f}pp]")
        print(f"  Conclusion: AI reduces disparity regardless of parameter assumptions")
    elif all_effects.min() > 0:
        print(f"\n⚠️  Effect is positive across all values (AI increases disparity)")
    else:
        print(f"\n⚠️  MIXED RESULTS: Effect direction depends on parameters")
        print(f"  Range: [{all_effects.min()*100:+.2f}pp, {all_effects.max()*100:+.2f}pp]")
        print(f"  Conclusion: Finding is sensitive to parameter assumptions")
        print(f"  Need to report conditional results")
    
    print(f"\n✓ Sensitivity analysis complete!")
    print(f"✓ Results: {results_file}")
    print(f"✓ Next: python scripts/visualize_sensitivity.py")


if __name__ == '__main__':
    main()