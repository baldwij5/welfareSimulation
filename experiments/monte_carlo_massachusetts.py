"""
Massachusetts Monte Carlo - WITH DETAILED PROGRESS TRACKING

Adds progress monitoring for 182k seeker simulations:
- Shows progress for each month within each iteration
- Estimates time remaining
- Saves checkpoint files
- Can resume from interruption

Run: python experiments/monte_carlo_ma_progress.py --iterations 20 --calibrated
"""

import warnings
warnings.filterwarnings('ignore')

import sys
sys.path.insert(0, 'src')
import numpy as np
import pandas as pd
import argparse
import json
from pathlib import Path
from datetime import datetime
from scipy import stats
import os

from data.data_loader import create_realistic_population, load_acs_county_data
from simulation.runner import create_evaluators, create_reviewers, run_month
from ai.application_sorter import AI_ApplicationSorter
from core.seeker import Seeker


def load_calibrated_parameters(calibration_file='data/ma_calibrated_params.json'):
    """Load calibrated parameters if available."""
    default_params = {
        'seekers': 1000,
        'capacity_mult_snap': 1.0,
        'capacity_mult_tanf': 1.0,
        'capacity_mult_ssi': 1.0,
        'capacity_mult_reviewer': 1.0,
        'calibrated': False
    }
    
    calib_path = Path(calibration_file)
    if calib_path.exists():
        with open(calib_path, 'r') as f:
            params = json.load(f)
            params['calibrated'] = True
            if 'capacity_mult_snap' not in params:
                mult = params.get('capacity_mult_evaluator', 1.0)
                params['capacity_mult_snap'] = mult
                params['capacity_mult_tanf'] = mult
                params['capacity_mult_ssi'] = mult
            return params
    else:
        return default_params


def calculate_characteristic_disparity(seekers, characteristic, high_values, low_values):
    """Calculate approval rate disparity for a given characteristic."""
    high_group = [s for s in seekers if getattr(s, characteristic, None) in high_values]
    low_group = [s for s in seekers if getattr(s, characteristic, None) in low_values]
    
    high_apps = sum(s.num_applications for s in high_group) if high_group else 0
    high_approvals = sum(s.num_approvals for s in high_group) if high_group else 0
    high_rate = high_approvals / high_apps if high_apps > 0 else 0.0
    
    low_apps = sum(s.num_applications for s in low_group) if low_group else 0
    low_approvals = sum(s.num_approvals for s in low_group) if low_group else 0
    low_rate = low_approvals / low_apps if low_apps > 0 else 0.0
    
    return high_rate - low_rate


def calculate_multi_characteristic_effects(control, treatment):
    """
    Calculate treatment effects across multiple characteristics WITH detailed tracking.
    
    Args:
        control: Dict with {seekers, evaluators, reviewers}
        treatment: Dict with {seekers, evaluators, reviewers}
    """
    # Extract seekers from dicts
    control_seekers = control['seekers'] if isinstance(control, dict) else control
    treatment_seekers = treatment['seekers'] if isinstance(treatment, dict) else treatment
    
    effects = {}
    
    # RACE
    c_race_gap = calculate_characteristic_disparity(control_seekers, 'race', ['White'], ['Black'])
    t_race_gap = calculate_characteristic_disparity(treatment_seekers, 'race', ['White'], ['Black'])
    effects['race_effect'] = t_race_gap - c_race_gap
    effects['control_race_gap'] = c_race_gap
    effects['treatment_race_gap'] = t_race_gap
    
    # EDUCATION
    c_edu_gap = calculate_characteristic_disparity(
        control_seekers, 'education', ['bachelors', 'graduate'], ['less_than_hs']
    )
    t_edu_gap = calculate_characteristic_disparity(
        treatment_seekers, 'education', ['bachelors', 'graduate'], ['less_than_hs']
    )
    effects['education_effect'] = t_edu_gap - c_edu_gap
    effects['control_education_gap'] = c_edu_gap
    effects['treatment_education_gap'] = t_edu_gap
    
    # EMPLOYMENT
    c_emp_gap = calculate_characteristic_disparity(
        control_seekers, 'employment_status',
        ['employed_full_time', 'employed_part_time'], ['unemployed']
    )
    t_emp_gap = calculate_characteristic_disparity(
        treatment_seekers, 'employment_status',
        ['employed_full_time', 'employed_part_time'], ['unemployed']
    )
    effects['employment_effect'] = t_emp_gap - c_emp_gap
    effects['control_employment_gap'] = c_emp_gap
    effects['treatment_employment_gap'] = t_emp_gap
    
    # DISABILITY
    c_dis_gap = calculate_characteristic_disparity(
        control_seekers, 'has_disability', [False], [True]
    )
    t_dis_gap = calculate_characteristic_disparity(
        treatment_seekers, 'has_disability', [False], [True]
    )
    effects['disability_effect'] = t_dis_gap - c_dis_gap
    effects['control_disability_gap'] = c_dis_gap
    effects['treatment_disability_gap'] = t_dis_gap
    
    # ===== NEW: DETAILED ADMINISTRATIVE TRACKING =====
    if isinstance(control, dict) and isinstance(treatment, dict):
        # Control world stats
        c_eval = control.get('evaluators', {})
        c_rev = control.get('reviewers', {})
        
        effects['control_eval_processed'] = sum(e.applications_processed for e in c_eval.values())
        effects['control_eval_approved'] = sum(e.applications_approved for e in c_eval.values())
        effects['control_eval_denied'] = sum(e.applications_denied for e in c_eval.values())
        effects['control_eval_escalated'] = sum(e.applications_escalated for e in c_eval.values())
        effects['control_eval_approval_rate'] = (
            effects['control_eval_approved'] / effects['control_eval_processed']
            if effects['control_eval_processed'] > 0 else 0
        )
        effects['control_escalation_rate'] = (
            effects['control_eval_escalated'] / effects['control_eval_processed']
            if effects['control_eval_processed'] > 0 else 0
        )
        
        effects['control_rev_reviewed'] = sum(r.applications_reviewed for r in c_rev.values())
        effects['control_rev_approved'] = sum(r.applications_approved for r in c_rev.values())
        effects['control_rev_denied'] = sum(r.applications_denied for r in c_rev.values())
        effects['control_fraud_detected'] = sum(r.fraud_detected for r in c_rev.values())
        effects['control_rev_approval_rate'] = (
            effects['control_rev_approved'] / effects['control_rev_reviewed']
            if effects['control_rev_reviewed'] > 0 else 0
        )
        
        # Treatment world stats
        t_eval = treatment.get('evaluators', {})
        t_rev = treatment.get('reviewers', {})
        
        effects['treatment_eval_processed'] = sum(e.applications_processed for e in t_eval.values())
        effects['treatment_eval_approved'] = sum(e.applications_approved for e in t_eval.values())
        effects['treatment_eval_denied'] = sum(e.applications_denied for e in t_eval.values())
        effects['treatment_eval_escalated'] = sum(e.applications_escalated for e in t_eval.values())
        effects['treatment_eval_approval_rate'] = (
            effects['treatment_eval_approved'] / effects['treatment_eval_processed']
            if effects['treatment_eval_processed'] > 0 else 0
        )
        effects['treatment_escalation_rate'] = (
            effects['treatment_eval_escalated'] / effects['treatment_eval_processed']
            if effects['treatment_eval_processed'] > 0 else 0
        )
        
        effects['treatment_rev_reviewed'] = sum(r.applications_reviewed for r in t_rev.values())
        effects['treatment_rev_approved'] = sum(r.applications_approved for r in t_rev.values())
        effects['treatment_rev_denied'] = sum(r.applications_denied for r in t_rev.values())
        effects['treatment_fraud_detected'] = sum(r.fraud_detected for r in t_rev.values())
        effects['treatment_rev_approval_rate'] = (
            effects['treatment_rev_approved'] / effects['treatment_rev_reviewed']
            if effects['treatment_rev_reviewed'] > 0 else 0
        )
    # ===== END DETAILED TRACKING =====
    
    return effects


def run_one_world_with_progress(seekers_master, counties, ai_sorter, seed, params, 
                                world_name, iteration_num, total_iterations):
    """Run simulation with month-by-month progress tracking."""
    print(f"\n    {world_name} world (iteration {iteration_num}/{total_iterations}):")
    
    # Fresh copies
    world_start = datetime.now()
    print(f"      Creating {len(seekers_master):,} seeker copies...", end='', flush=True)
    
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
        seekers.append(fresh)
    
    copy_time = (datetime.now() - world_start).total_seconds()
    print(f" done ({copy_time:.1f}s)")
    
    # Create staff
    print(f"      Creating staff...", end='', flush=True)
    staff_start = datetime.now()
    
    acs_data = load_acs_county_data('src/data/us_census_acs_2022_county_data.csv')
    evaluators = create_evaluators(counties, acs_data=acs_data, random_seed=seed)
    reviewers = create_reviewers(counties, acs_data=acs_data, load_state_models=True, random_seed=seed)
    
    # Apply program-specific capacity
    for (county, program), evaluator in evaluators.items():
        if program == 'SNAP':
            evaluator.monthly_capacity *= params['capacity_mult_snap']
        elif program == 'TANF':
            evaluator.monthly_capacity *= params['capacity_mult_tanf']
        elif program == 'SSI':
            evaluator.monthly_capacity *= params['capacity_mult_ssi']
    
    for reviewer in reviewers.values():
        reviewer.monthly_capacity *= params['capacity_mult_reviewer']
    
    staff_time = (datetime.now() - staff_start).total_seconds()
    print(f" done ({staff_time:.1f}s)")
    
    # Run simulation with month-by-month tracking
    print(f"      Running 12 months: ", end='', flush=True)
    month_times = []
    
    for month in range(12):
        month_start = datetime.now()
        run_month(seekers, evaluators, reviewers, month, ai_sorter=ai_sorter)
        month_time = (datetime.now() - month_start).total_seconds()
        month_times.append(month_time)
        
        # Show progress every 3 months
        if (month + 1) % 3 == 0:
            avg_month_time = np.mean(month_times)
            remaining_months = 12 - (month + 1)
            est_remaining = avg_month_time * remaining_months
            print(f"M{month+1}({month_time:.0f}s, ~{est_remaining:.0f}s left) ", end='', flush=True)
        else:
            print(f"M{month+1} ", end='', flush=True)
    
    total_world_time = (datetime.now() - world_start).total_seconds()
    print(f"\n      ✓ {world_name} complete: {total_world_time:.1f}s total, {np.mean(month_times):.1f}s/month avg")
    
    # Return seekers AND staff for detailed tracking
    return {
        'seekers': seekers,
        'evaluators': evaluators,
        'reviewers': reviewers
    }


def run_parallel_worlds_one_iteration(counties, n_seekers, params, iteration_seed, 
                                     iteration_num, total_iterations):
    """Run one Monte Carlo iteration with detailed progress."""
    iter_overall_start = datetime.now()
    
    print(f"\n  {'─'*66}")
    print(f"  Creating master population ({n_seekers:,} seekers)...", end='', flush=True)
    
    pop_start = datetime.now()
    seekers_master = create_realistic_population(
        cps_file='src/data/cps_asec_2022_processed_full.csv',
        acs_file='src/data/us_census_acs_2022_county_data.csv',
        n_seekers=n_seekers,
        counties=counties,
        proportional=True,
        random_seed=42 + iteration_seed
    )
    pop_time = (datetime.now() - pop_start).total_seconds()
    print(f" done ({pop_time:.1f}s)")
    
    if not seekers_master:
        return None
    
    # Run control world
    control_seekers = run_one_world_with_progress(
        seekers_master, counties, None, iteration_seed, params,
        "Control", iteration_num, total_iterations
    )
    
    # Run treatment world
    treatment_seekers = run_one_world_with_progress(
        seekers_master, counties, AI_ApplicationSorter('simple_first'), 
        iteration_seed, params,
        "Treatment", iteration_num, total_iterations
    )
    
    # Calculate effects
    effects = calculate_multi_characteristic_effects(control_seekers, treatment_seekers)
    effects['iteration'] = iteration_seed
    effects['n_seekers'] = len(seekers_master)
    
    iter_total_time = (datetime.now() - iter_overall_start).total_seconds()
    print(f"  ✓ Iteration {iteration_num} total: {iter_total_time:.1f}s ({iter_total_time/60:.1f}min)")
    
    return effects


def run_monte_carlo(n_iterations=20, use_calibrated=False, verbose=True):
    """Run Massachusetts Monte Carlo with progress tracking."""
    start_time = datetime.now()
    
    if verbose:
        print("=" * 70)
        print("MASSACHUSETTS MONTE CARLO - WITH PROGRESS TRACKING")
        print("=" * 70)
        print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Iterations: {n_iterations}")
    
    # Load parameters
    if use_calibrated:
        params = load_calibrated_parameters()
        if verbose:
            if params['calibrated']:
                print(f"\n✓ Using CALIBRATED parameters:")
                print(f"  - Seekers: {params['seekers']:,}")
                print(f"  - SNAP capacity: {params.get('capacity_mult_snap', 1.0):.3f}")
                print(f"  - TANF capacity: {params.get('capacity_mult_tanf', 1.0):.3f}")
                print(f"  - SSI capacity: {params.get('capacity_mult_ssi', 1.0):.3f}")
                print(f"  - Reviewer capacity: {params.get('capacity_mult_reviewer', 1.0):.3f}")
            else:
                print(f"\n⚠️  Calibration file not found, using defaults")
    else:
        params = load_calibrated_parameters()
        if verbose:
            print(f"\n⚠️  Using UNCALIBRATED parameters:")
            print(f"  - Seekers: {params['seekers']:,}")
    
    n_seekers = params['seekers']
    
    # Get MA counties
    acs = load_acs_county_data('src/data/us_census_acs_2022_county_data.csv')
    acs['state'] = acs['county_name'].str.split(', ').str[1]
    ma_counties = acs[acs['state'] == 'Massachusetts']['county_name'].tolist()
    
    if verbose:
        print(f"\nMassachusetts counties: {len(ma_counties)}")
        print(f"\n{'=' * 70}")
        print("RUNNING ITERATIONS")
        print("=" * 70)
    
    # Check for existing checkpoint
    checkpoint_file = 'results/monte_carlo_checkpoint.csv'
    if os.path.exists(checkpoint_file):
        print(f"\n⚠️  Found checkpoint file: {checkpoint_file}")
        response = input("Resume from checkpoint? (y/n): ")
        if response.lower() == 'y':
            checkpoint_df = pd.read_csv(checkpoint_file)
            results = checkpoint_df.to_dict('records')
            completed_iterations = set(checkpoint_df['iteration'].values)
            print(f"✓ Loaded {len(results)} completed iterations")
        else:
            results = []
            completed_iterations = set()
    else:
        results = []
        completed_iterations = set()
    
    failed = 0
    iteration_times = []
    
    for i in range(n_iterations):
        if i in completed_iterations:
            print(f"\n[{i+1}/{n_iterations}] Skipping (already completed)")
            continue
        
        iter_start = datetime.now()
        
        # Calculate ETA
        if iteration_times:
            avg_time = np.mean(iteration_times)
            remaining_iters = n_iterations - (i + 1 - failed)
            eta_seconds = avg_time * remaining_iters
            eta_minutes = eta_seconds / 60
            eta_str = f"ETA: {eta_minutes:.0f}min" if eta_minutes < 120 else f"ETA: {eta_minutes/60:.1f}hr"
        else:
            eta_str = "ETA: calculating..."
        
        if verbose:
            print(f"\n{'='*70}")
            print(f"ITERATION {i+1}/{n_iterations} - {eta_str}")
            print(f"{'='*70}")
        
        try:
            effect = run_parallel_worlds_one_iteration(
                counties=ma_counties,
                n_seekers=n_seekers,
                params=params,
                iteration_seed=i,
                iteration_num=i+1,
                total_iterations=n_iterations
            )
            
            if effect:
                results.append(effect)
                
                iter_time = (datetime.now() - iter_start).total_seconds()
                iteration_times.append(iter_time)
                
                if verbose:
                    print(f"\n  📊 Effects this iteration:")
                    print(f"    Race:       {effect['race_effect']:+.4f} ({effect['race_effect']*100:+.2f}pp)")
                    print(f"    Education:  {effect['education_effect']:+.4f} ({effect['education_effect']*100:+.2f}pp)")
                    print(f"    Employment: {effect['employment_effect']:+.4f} ({effect['employment_effect']*100:+.2f}pp)")
                    print(f"    Disability: {effect['disability_effect']:+.4f} ({effect['disability_effect']*100:+.2f}pp)")
                    
                    # Running average
                    if len(results) > 1:
                        df_so_far = pd.DataFrame(results)
                        print(f"\n  📈 Running average (n={len(results)}):")
                        print(f"    Race:       {df_so_far['race_effect'].mean():+.4f} ({df_so_far['race_effect'].mean()*100:+.2f}pp)")
                
                # Save checkpoint after each successful iteration
                checkpoint_df = pd.DataFrame(results)
                checkpoint_df.to_csv(checkpoint_file, index=False)
                
            else:
                failed += 1
                if verbose:
                    print(f"  ✗ Failed (no seekers generated)")
                
        except KeyboardInterrupt:
            print(f"\n\n⚠️  Interrupted by user!")
            print(f"Completed {len(results)} iterations before interruption")
            print(f"Checkpoint saved to: {checkpoint_file}")
            print(f"Resume by running same command again")
            break
            
        except Exception as e:
            failed += 1
            if verbose:
                print(f"  ✗ Failed: {e}")
            continue
    
    # Convert to DataFrame
    df = pd.DataFrame(results)
    
    # Summary statistics
    total_time = (datetime.now() - start_time).total_seconds()
    
    if verbose:
        print(f"\n{'=' * 70}")
        print("RESULTS SUMMARY")
        print("=" * 70)
        print(f"Total time: {total_time/60:.1f} minutes ({total_time/3600:.1f} hours)")
        print(f"Successful: {len(results)}/{n_iterations}")
        print(f"Failed: {failed}")
        
        if len(iteration_times) > 0:
            print(f"Average time per iteration: {np.mean(iteration_times)/60:.1f} minutes")
        
        if len(results) > 0:
            print(f"\n{'─'*70}")
            print("FINAL RESULTS")
            print(f"{'─'*70}")
            
            print(f"\nMEAN EFFECTS (negative = AI reduces disparity):")
            for char in ['race', 'education', 'employment', 'disability']:
                effect_col = f'{char}_effect'
                mean = df[effect_col].mean()
                print(f"  {char.title():12s}: {mean:+.4f} ({mean*100:+.2f}pp)")
            
            print(f"\n95% CONFIDENCE INTERVALS:")
            for char in ['race', 'education', 'employment', 'disability']:
                effect_col = f'{char}_effect'
                mean = df[effect_col].mean()
                std = df[effect_col].std()
                ci_lower = mean - 1.96 * std / np.sqrt(len(df))
                ci_upper = mean + 1.96 * std / np.sqrt(len(df))
                print(f"  {char.title():12s}: [{ci_lower*100:+.2f}pp, {ci_upper*100:+.2f}pp]")
            
            print(f"\nSTATISTICAL SIGNIFICANCE (H0: effect = 0):")
            for char in ['race', 'education', 'employment', 'disability']:
                effect_col = f'{char}_effect'
                mean = df[effect_col].mean()
                std = df[effect_col].std()
                t_stat = mean / (std / np.sqrt(len(df))) if std > 0 else 0
                p_value = 2 * (1 - stats.t.cdf(abs(t_stat), len(df) - 1))
                sig = '***' if p_value < 0.001 else '**' if p_value < 0.01 else '*' if p_value < 0.05 else 'ns'
                print(f"  {char.title():12s}: t={t_stat:+.3f}, p={p_value:.4f} {sig}")
            
            print(f"\n{'─'*70}")
            print("INTERPRETATION")
            print(f"{'─'*70}")
            
            # Race interpretation
            race_mean = df['race_effect'].mean()
            race_p = 2 * (1 - stats.t.cdf(abs(race_mean / (df['race_effect'].std() / np.sqrt(len(df)))), len(df) - 1))
            
            if race_p < 0.05:
                if race_mean < 0:
                    print(f"✓ AI significantly REDUCES racial disparity by {abs(race_mean)*100:.2f}pp")
                else:
                    print(f"⚠️  AI significantly INCREASES racial disparity by {race_mean*100:.2f}pp")
            else:
                print(f"○ AI has no significant effect on racial disparity")
            
            print(f"\nOriginal uncalibrated finding: -2.15pp (p<0.0001)")
            print(f"Calibrated finding: {race_mean*100:+.2f}pp (p={race_p:.4f})")
            
            if abs(race_mean * 100 - (-2.15)) < 0.5:
                print(f"→ Effect PERSISTS at calibrated scale! ✓")
            elif abs(race_mean * 100) < 0.5:
                print(f"→ Effect DISAPPEARED at calibrated scale (was artifact)")
            else:
                print(f"→ Effect CHANGED at calibrated scale (scale-dependent)")
    
    return df


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Massachusetts Monte Carlo with Progress Tracking'
    )
    parser.add_argument(
        '--iterations',
        type=int,
        default=20,
        help='Number of Monte Carlo iterations'
    )
    parser.add_argument(
        '--calibrated',
        action='store_true',
        help='Use calibrated parameters'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='results/monte_carlo_ma_results.csv',
        help='Output file path'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress progress output'
    )
    
    args = parser.parse_args()
    
    # Run simulation
    results_df = run_monte_carlo(
        n_iterations=args.iterations,
        use_calibrated=args.calibrated,
        verbose=not args.quiet
    )
    
    # Save final results
    os.makedirs('results', exist_ok=True)
    results_df.to_csv(args.output, index=False)
    
    # Remove checkpoint file on successful completion
    checkpoint_file = 'results/monte_carlo_checkpoint.csv'
    if os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)
    
    if not args.quiet:
        print(f"\n✓ Final results saved to: {args.output}")
        print(f"  {len(results_df)} iterations × {len(results_df.columns)} metrics")
        print(f"✓ Checkpoint file removed")
    
    print(f"\n{'=' * 70}")
    print("MONTE CARLO COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()