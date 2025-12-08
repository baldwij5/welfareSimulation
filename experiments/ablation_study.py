"""
Ablation Study: Mechanism Isolation Experiments

Isolates the causal contribution of each theoretical mechanism to the
AI effect on racial disparity in welfare administration.

Tests 6 configurations:
  1. Baseline (no mechanisms)
  2. Only Bureaucracy Points
  3. Only Fraud History
  4. Only Bayesian Learning
  5. Only State Discrimination
  6. Full Model (all mechanisms)

Usage:
  python experiments/ablation_study.py --iterations 20 --seekers 10000
  python experiments/ablation_study.py --iterations 20 --seekers 10000 --resume

Output:
  - results/ablation_study_results.csv (all iterations, all configs)
  - results/ablation_checkpoint.csv (for resuming)
  - Console output with progress tracking

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
from scipy import stats

from core.mechanism_config import MechanismConfig
from core.seeker import Seeker
from data.data_loader import create_realistic_population, load_acs_county_data
from simulation.runner import create_evaluators, create_reviewers, run_month
from ai.application_sorter import AI_ApplicationSorter


def calculate_race_disparity(seekers):
    """
    Calculate White-Black approval rate gap.
    
    Returns:
        dict with control_white_rate, control_black_rate, control_gap
    """
    white = [s for s in seekers if s.race == 'White']
    black = [s for s in seekers if s.race == 'Black']
    
    w_apps = sum(s.num_applications for s in white)
    b_apps = sum(s.num_applications for s in black)
    
    if w_apps == 0 or b_apps == 0:
        return None
    
    w_rate = sum(s.num_approvals for s in white) / w_apps
    b_rate = sum(s.num_approvals for s in black) / b_apps
    
    return {
        'white_rate': w_rate,
        'black_rate': b_rate,
        'gap': w_rate - b_rate
    }


def run_one_world(seekers_master, counties, ai_sorter, seed, mechanism_config, 
                  capacity_params, verbose=False):
    """
    Run one world (control or treatment) for 12 months.
    
    Args:
        seekers_master: Master population to copy
        counties: List of county names
        ai_sorter: AI sorter object (None for control)
        seed: Random seed
        mechanism_config: MechanismConfig object
        capacity_params: Dict with capacity multipliers
        verbose: Print progress
        
    Returns:
        list: Seekers after 12 months of simulation
    """
    # Copy seekers (fresh start)
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
            random_state=np.random.RandomState(orig.id),
            mechanism_config=mechanism_config
        )
        seekers.append(fresh)
    
    # Create staff with mechanism config
    acs = load_acs_county_data('src/data/us_census_acs_2022_county_data.csv')
    
    evaluators = create_evaluators(
        counties, 
        acs_data=acs,
        mechanism_config=mechanism_config,
        random_seed=seed
    )
    
    reviewers = create_reviewers(
        counties,
        acs_data=acs,
        mechanism_config=mechanism_config,
        load_state_models=mechanism_config.state_discrimination_enabled,
        random_seed=seed
    )
    
    # Apply calibrated capacity
    for (county, program), evaluator in evaluators.items():
        if program == 'SNAP':
            evaluator.monthly_capacity *= capacity_params['capacity_mult_snap']
        elif program == 'TANF':
            evaluator.monthly_capacity *= capacity_params['capacity_mult_tanf']
        elif program == 'SSI':
            evaluator.monthly_capacity *= capacity_params['capacity_mult_ssi']
    
    for reviewer in reviewers.values():
        reviewer.monthly_capacity *= capacity_params['capacity_mult_reviewer']
    
    # Run 12 months
    for month in range(12):
        run_month(seekers, evaluators, reviewers, month, ai_sorter=ai_sorter)
    
    return seekers


def run_ablation_iteration(mechanism_name, mechanism_config, ma_counties, 
                           n_seekers, iteration_num, capacity_params, verbose=True):
    """
    Run one Monte Carlo iteration for a specific mechanism configuration.
    
    Returns:
        dict: Results for this iteration
    """
    seed = 42 + iteration_num
    
    if verbose:
        print(f"    Iteration {iteration_num + 1}: seed={seed}...", end='', flush=True)
    
    start_time = time.time()
    
    try:
        # Create master population
        seekers_master = create_realistic_population(
            cps_file='src/data/cps_asec_2022_processed_full.csv',
            acs_file='src/data/us_census_acs_2022_county_data.csv',
            n_seekers=n_seekers,
            counties=ma_counties,
            proportional=True,
            random_seed=seed,
            mechanism_config=mechanism_config
        )
        
        if not seekers_master or len(seekers_master) == 0:
            if verbose:
                print(" FAILED (no seekers created)")
            return None
        
        # Control world (FCFS)
        control_seekers = run_one_world(
            seekers_master, ma_counties, None, seed, 
            mechanism_config, capacity_params, verbose=False
        )
        
        # Treatment world (AI sorting)
        ai_sorter = AI_ApplicationSorter('simple_first')
        treatment_seekers = run_one_world(
            seekers_master, ma_counties, ai_sorter, seed,
            mechanism_config, capacity_params, verbose=False
        )
        
        # Calculate effects
        control_stats = calculate_race_disparity(control_seekers)
        treatment_stats = calculate_race_disparity(treatment_seekers)
        
        if control_stats is None or treatment_stats is None:
            if verbose:
                print(" FAILED (no applications)")
            return None
        
        elapsed = time.time() - start_time
        
        results = {
            'mechanism': mechanism_name,
            'iteration': iteration_num,
            'seed': seed,
            'n_seekers': len(seekers_master),
            'control_white_rate': control_stats['white_rate'],
            'control_black_rate': control_stats['black_rate'],
            'control_gap': control_stats['gap'],
            'treatment_white_rate': treatment_stats['white_rate'],
            'treatment_black_rate': treatment_stats['black_rate'],
            'treatment_gap': treatment_stats['gap'],
            'race_effect': treatment_stats['gap'] - control_stats['gap'],
            'elapsed_seconds': elapsed
        }
        
        if verbose:
            print(f" done ({elapsed:.0f}s, effect={results['race_effect']*100:+.2f}pp)")
        
        return results
        
    except Exception as e:
        if verbose:
            print(f" FAILED ({str(e)[:50]})")
        return None


def run_mechanism_experiment(mechanism_name, mechanism_config, ma_counties,
                             n_seekers, n_iterations, capacity_params, 
                             checkpoint_file, verbose=True):
    """
    Run all iterations for one mechanism configuration.
    
    Returns:
        DataFrame with results
    """
    if verbose:
        print(f"\n{'='*70}")
        print(f"MECHANISM: {mechanism_name}")
        print(f"{'='*70}")
        print(f"  Active mechanisms: {mechanism_config.get_active_mechanisms()}")
        print(f"  Iterations: {n_iterations}")
    
    # Check for existing results in checkpoint
    existing_results = []
    if Path(checkpoint_file).exists():
        checkpoint_df = pd.read_csv(checkpoint_file)
        existing_results = checkpoint_df[
            checkpoint_df['mechanism'] == mechanism_name
        ].to_dict('records')
        
        if len(existing_results) > 0:
            if verbose:
                print(f"  Found {len(existing_results)} existing iterations (resuming)")
    
    # Determine which iterations to run
    completed_iterations = set(r['iteration'] for r in existing_results)
    iterations_to_run = [i for i in range(n_iterations) if i not in completed_iterations]
    
    if len(iterations_to_run) == 0:
        if verbose:
            print(f"  ✓ All {n_iterations} iterations already complete!")
        return pd.DataFrame(existing_results)
    
    if verbose:
        print(f"  Running {len(iterations_to_run)} iterations...")
    
    # Run missing iterations
    all_results = existing_results.copy()
    
    for iter_num in iterations_to_run:
        result = run_ablation_iteration(
            mechanism_name, mechanism_config, ma_counties,
            n_seekers, iter_num, capacity_params, verbose=verbose
        )
        
        if result:
            all_results.append(result)
            
            # Save checkpoint after each iteration
            checkpoint_df = pd.DataFrame(all_results)
            checkpoint_df.to_csv(checkpoint_file, index=False)
    
    df = pd.DataFrame(all_results)
    
    # Summary statistics
    if verbose and len(df) > 0:
        mean_effect = df['race_effect'].mean()
        std_effect = df['race_effect'].std()
        se_effect = std_effect / np.sqrt(len(df))
        ci_lower = mean_effect - 1.96 * se_effect
        ci_upper = mean_effect + 1.96 * se_effect
        
        t_stat = mean_effect / se_effect if se_effect > 0 else 0
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), len(df) - 1))
        
        sig = '***' if p_value < 0.001 else '**' if p_value < 0.01 else '*' if p_value < 0.05 else 'ns'
        
        print(f"\n  Summary:")
        print(f"    Mean effect: {mean_effect*100:+.2f}pp")
        print(f"    95% CI: [{ci_lower*100:+.2f}pp, {ci_upper*100:+.2f}pp]")
        print(f"    t={t_stat:.2f}, p={p_value:.4f} {sig}")
        print(f"    Completed: {len(df)}/{n_iterations} iterations")
    
    return df


def main():
    """Run complete ablation study."""
    parser = argparse.ArgumentParser(
        description='Ablation study: Isolate mechanism contributions'
    )
    parser.add_argument('--iterations', type=int, default=20,
                       help='Monte Carlo iterations per configuration')
    parser.add_argument('--seekers', type=int, default=10000,
                       help='Seekers per iteration (10k recommended for speed)')
    parser.add_argument('--resume', action='store_true',
                       help='Resume from checkpoint if available')
    args = parser.parse_args()
    
    print("="*70)
    print("ABLATION STUDY: MECHANISM ISOLATION")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Iterations per configuration: {args.iterations}")
    print(f"Seekers per iteration: {args.seekers:,}")
    print(f"Total experiments: 6 configs × {args.iterations} = {6 * args.iterations} runs")
    
    # Load calibrated capacity parameters
    calib_file = 'data/ma_calibrated_params.json'
    if Path(calib_file).exists():
        with open(calib_file, 'r') as f:
            capacity_params = json.load(f)
        print(f"✓ Loaded calibrated capacity from {calib_file}")
    else:
        print(f"⚠️  No calibration file found, using defaults")
        capacity_params = {
            'capacity_mult_snap': 1.0,
            'capacity_mult_tanf': 1.0,
            'capacity_mult_ssi': 1.0,
            'capacity_mult_reviewer': 1.0
        }
    
    # Get MA counties
    acs = load_acs_county_data('src/data/us_census_acs_2022_county_data.csv')
    acs['state'] = acs['county_name'].str.split(', ').str[1]
    ma_counties = acs[acs['state'] == 'Massachusetts']['county_name'].tolist()
    print(f"✓ Using {len(ma_counties)} Massachusetts counties")
    
    # Define mechanism configurations
    experiments = [
        ('Baseline (no mechanisms)', MechanismConfig.baseline()),
        ('Only Bureaucracy Points', MechanismConfig.only_bureaucracy()),
        ('Only Fraud History', MechanismConfig.only_fraud()),
        ('Only Bayesian Learning', MechanismConfig.only_learning()),
        ('Only State Discrimination', MechanismConfig.only_state_discrimination()),
        ('Full Model (all mechanisms)', MechanismConfig.full_model())
    ]
    
    # Setup checkpoint
    checkpoint_file = 'results/ablation_checkpoint.csv'
    Path('results').mkdir(exist_ok=True)
    
    if not args.resume and Path(checkpoint_file).exists():
        # Backup old checkpoint
        backup = f'results/ablation_checkpoint_backup_{int(time.time())}.csv'
        Path(checkpoint_file).rename(backup)
        print(f"✓ Backed up old checkpoint to {backup}")
    
    # Run each experiment
    print(f"\n{'='*70}")
    print("RUNNING ABLATION EXPERIMENTS")
    print("="*70)
    
    all_results = []
    start_total = time.time()
    
    for config_idx, (name, config) in enumerate(experiments):
        config_start = time.time()
        
        df = run_mechanism_experiment(
            mechanism_name=name,
            mechanism_config=config,
            ma_counties=ma_counties,
            n_seekers=args.seekers,
            n_iterations=args.iterations,
            capacity_params=capacity_params,
            checkpoint_file=checkpoint_file,
            verbose=True
        )
        
        all_results.append(df)
        
        config_elapsed = time.time() - config_start
        configs_remaining = len(experiments) - (config_idx + 1)
        
        if configs_remaining > 0:
            eta_minutes = (config_elapsed / 60) * configs_remaining
            print(f"\n  ⏱️  ETA for remaining configs: {eta_minutes:.0f} minutes")
    
    # Combine all results
    combined = pd.concat(all_results, ignore_index=True)
    
    # Save final results
    results_file = 'results/ablation_study_results.csv'
    combined.to_csv(results_file, index=False)
    
    total_elapsed = time.time() - start_total
    
    # Print summary
    print(f"\n{'='*70}")
    print("ABLATION STUDY COMPLETE")
    print("="*70)
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total time: {total_elapsed/60:.1f} minutes")
    print(f"Results saved to: {results_file}")
    
    # Summary table
    print(f"\n{'='*70}")
    print("MECHANISM CONTRIBUTION SUMMARY")
    print("="*70)
    
    summary = combined.groupby('mechanism')['race_effect'].agg(['mean', 'std', 'count'])
    summary['se'] = summary['std'] / np.sqrt(summary['count'])
    summary['ci_lower'] = summary['mean'] - 1.96 * summary['se']
    summary['ci_upper'] = summary['mean'] + 1.96 * summary['se']
    summary['t_stat'] = summary['mean'] / summary['se']
    summary['p_value'] = 2 * (1 - stats.t.cdf(abs(summary['t_stat']), summary['count'] - 1))
    
    print("\nMechanism                      | Effect (pp) | 95% CI              | t-stat  | p-value | n")
    print("-" * 100)
    
    for mech in ['Baseline (no mechanisms)', 
                 'Only Bureaucracy Points',
                 'Only Fraud History',
                 'Only Bayesian Learning',
                 'Only State Discrimination',
                 'Full Model (all mechanisms)']:
        if mech in summary.index:
            row = summary.loc[mech]
            sig = '***' if row['p_value'] < 0.001 else '**' if row['p_value'] < 0.01 else '*' if row['p_value'] < 0.05 else 'ns'
            
            print(f"{mech:30s} | {row['mean']*100:+7.2f}pp   | "
                  f"[{row['ci_lower']*100:+6.2f}, {row['ci_upper']*100:+6.2f}] | "
                  f"{row['t_stat']:+7.2f} | {row['p_value']:.4f} {sig:3s} | {int(row['count'])}")
    
    # Contribution analysis
    print(f"\n{'='*70}")
    print("MECHANISM CONTRIBUTION ANALYSIS")
    print("="*70)
    
    baseline_mean = summary.loc['Baseline (no mechanisms)', 'mean']
    full_mean = summary.loc['Full Model (all mechanisms)', 'mean']
    total_effect = full_mean - baseline_mean
    
    print(f"\nTotal AI effect (Full - Baseline): {total_effect*100:+.2f}pp")
    print(f"\nIndividual mechanism contributions:")
    
    individual_mechs = [
        'Only Bureaucracy Points',
        'Only Fraud History',
        'Only Bayesian Learning',
        'Only State Discrimination'
    ]
    
    contributions = {}
    for mech in individual_mechs:
        if mech in summary.index:
            mech_mean = summary.loc[mech, 'mean']
            contribution = mech_mean - baseline_mean
            pct_of_total = (contribution / total_effect * 100) if abs(total_effect) > 0.001 else 0
            
            contributions[mech] = contribution
            
            print(f"  {mech:30s}: {contribution*100:+6.2f}pp ({pct_of_total:5.1f}% of total)")
    
    # Additivity check
    print(f"\n{'='*70}")
    print("ADDITIVITY CHECK")
    print("="*70)
    
    sum_contributions = sum(contributions.values())
    interaction = total_effect - sum_contributions
    
    print(f"Sum of individual effects:  {sum_contributions*100:+.2f}pp")
    print(f"Full model effect:         {total_effect*100:+.2f}pp")
    print(f"Interaction term:          {interaction*100:+.2f}pp")
    
    if abs(interaction) < 0.01:  # Within 1pp
        print(f"\n✓ Mechanisms are approximately ADDITIVE (independent)")
        print(f"  Interpretation: Mechanisms work independently")
    else:
        print(f"\n⚠️  Mechanisms show INTERACTION EFFECTS (non-additive)")
        if interaction < 0:
            print(f"  Interpretation: Mechanisms SYNERGIZE (amplify each other)")
        else:
            print(f"  Interpretation: Mechanisms INTERFERE (partially cancel)")
    
    # Comparison to invalid Monte Carlo
    print(f"\n{'='*70}")
    print("COMPARISON TO PREVIOUS (INVALID) RESULTS")
    print("="*70)
    print(f"\nPrevious result (with seed bug): -11.35pp (CI: 0.08pp, t=-535)")
    print(f"New valid result (full model):   {full_mean*100:+.2f}pp "
          f"(CI: {(summary.loc['Full Model (all mechanisms)', 'ci_upper'] - summary.loc['Full Model (all mechanisms)', 'ci_lower'])*100:.2f}pp, "
          f"t={summary.loc['Full Model (all mechanisms)', 't_stat']:+.1f})")
    
    if abs(full_mean + 0.1135) < 0.02:  # Within 2pp of old result
        print(f"\n✓ Results are similar (seed bug didn't affect effect estimate much)")
    else:
        print(f"\n⚠️  Results differ by {abs(full_mean + 0.1135)*100:.1f}pp from invalid result")
        print(f"   The new (valid) result is the correct one to use!")
    
    print(f"\n✓ Ablation study complete!")
    print(f"✓ Results: {results_file}")
    print(f"✓ Checkpoint: {checkpoint_file}")


if __name__ == '__main__':
    main()