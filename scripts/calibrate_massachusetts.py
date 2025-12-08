"""
Massachusetts Calibration System - FINAL VERSION

Keeps evaluators/reviewers as dicts (as run_month expects) but modifies the values.

Run with: python scripts/calibrate_massachusetts_v4.py
"""

import warnings
warnings.filterwarnings('ignore', message='X does not have valid feature names')

import sys
sys.path.insert(0, 'src')
import numpy as np
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

from data.data_loader import create_realistic_population, load_acs_county_data
from simulation.runner import create_evaluators, create_reviewers, run_month


@dataclass
class CalibrationTarget:
    """Real-world enrollment targets for Massachusetts."""
    tanf_adults: int = 22_098
    snap_persons: int = 255_236
    ssi_persons: int = 6_323
    
    approval_rate: float = 0.70
    applications_per_seeker: float = 2.0
    
    def calculate_seekers_from_snap(self) -> int:
        """Calculate seekers needed from SNAP enrollment."""
        total_applications = self.snap_persons / self.approval_rate
        seekers = total_applications / self.applications_per_seeker
        return int(seekers)


def count_program_enrollment(seekers, program):
    """Count seekers enrolled in a program."""
    return sum(1 for s in seekers if program in s.enrolled_programs)


def run_calibration_test(counties, n_seekers, capacity_mult_eval, capacity_mult_rev, seed):
    """
    Run a single simulation to test enrollment outcomes.
    
    Returns:
        Dict with enrollment counts or None if failed
    """
    try:
        # Create population
        seekers = create_realistic_population(
            cps_file='src/data/cps_asec_2022_processed_full.csv',
            acs_file='src/data/us_census_acs_2022_county_data.csv',
            n_seekers=n_seekers,
            counties=counties,
            proportional=True,
            random_seed=seed
        )
        
        if not seekers:
            print(f"    ✗ No seekers created")
            return None
        
        # Create staff (returns dicts)
        acs_data = load_acs_county_data('src/data/us_census_acs_2022_county_data.csv')
        
        evaluators = create_evaluators(counties, acs_data=acs_data, random_seed=seed)
        reviewers = create_reviewers(counties, acs_data=acs_data, load_state_models=True,
                                     random_seed=seed)
        
        # Verify they're dicts
        if not isinstance(evaluators, dict):
            print(f"    ✗ Expected evaluators to be dict, got {type(evaluators)}")
            return None
        
        if not isinstance(reviewers, dict):
            print(f"    ✗ Expected reviewers to be dict, got {type(reviewers)}")
            return None
        
        print(f"    → Evaluators: {len(evaluators)} staff (dict)")
        print(f"    → Reviewers: {len(reviewers)} staff (dict)")
        
        # Apply capacity multipliers to the VALUES (keep dict structure)
        applied_eval = 0
        for key, evaluator in evaluators.items():
            if hasattr(evaluator, 'monthly_capacity'):
                evaluator.monthly_capacity *= capacity_mult_eval
                applied_eval += 1
        
        applied_rev = 0
        for key, reviewer in reviewers.items():
            if hasattr(reviewer, 'monthly_capacity'):
                reviewer.monthly_capacity *= capacity_mult_rev
                applied_rev += 1
        
        print(f"    → Applied multipliers to {applied_eval}/{len(evaluators)} evaluators, {applied_rev}/{len(reviewers)} reviewers")
        
        # Run 12 months (evaluators and reviewers stay as dicts)
        for month in range(12):
            run_month(seekers, evaluators, reviewers, month, ai_sorter=None)
        
        # Count enrollment
        enrollment = {
            'TANF': count_program_enrollment(seekers, 'TANF'),
            'SNAP': count_program_enrollment(seekers, 'SNAP'),
            'SSI': count_program_enrollment(seekers, 'SSI')
        }
        
        print(f"    ✓ Enrollment: TANF={enrollment['TANF']:,}, SNAP={enrollment['SNAP']:,}, SSI={enrollment['SSI']:,}")
        
        return enrollment
        
    except Exception as e:
        import traceback
        print(f"    ✗ Test failed: {e}")
        traceback.print_exc()
        return None


def calculate_errors(simulated, targets):
    """Calculate percentage errors for each program."""
    target_vals = {
        'TANF': targets.tanf_adults,
        'SNAP': targets.snap_persons,
        'SSI': targets.ssi_persons
    }
    
    errors = {}
    for program in ['TANF', 'SNAP', 'SSI']:
        sim = simulated.get(program, 0)
        tgt = target_vals[program]
        pct_error = abs(sim - tgt) / tgt if tgt > 0 else float('inf')
        errors[f'{program.lower()}_pct_error'] = pct_error
    
    errors['mean_pct_error'] = np.mean([
        errors['tanf_pct_error'],
        errors['snap_pct_error'],
        errors['ssi_pct_error']
    ])
    
    return errors


def grid_search_capacity(counties, n_seekers, targets, 
                        eval_range=None, rev_range=None,
                        n_tests_per_config=3, verbose=True):
    """
    Grid search over capacity multipliers.
    
    Returns:
        (best_eval_mult, best_rev_mult, best_enrollment, results_df)
    """
    if eval_range is None:
        eval_range = [0.05, 0.1, 0.25, 0.5, 1.0, 2.0]
    
    if rev_range is None:
        rev_range = [0.05, 0.1, 0.25, 0.5, 1.0, 2.0]
    
    if verbose:
        print(f"\n{'=' * 70}")
        print("GRID SEARCH FOR OPTIMAL CAPACITY")
        print("=" * 70)
        print(f"Evaluator range: {eval_range}")
        print(f"Reviewer range: {rev_range}")
        print(f"Configurations: {len(eval_range) * len(rev_range)}")
        print(f"Tests per config: {n_tests_per_config}")
        print(f"Total simulations: {len(eval_range) * len(rev_range) * n_tests_per_config}")
    
    best_error = float('inf')
    best_config = None
    best_enrollment = None
    all_results = []
    
    config_num = 0
    total_configs = len(eval_range) * len(rev_range)
    
    for eval_mult in eval_range:
        for rev_mult in rev_range:
            config_num += 1
            
            if verbose:
                print(f"\n[{config_num}/{total_configs}] Testing eval={eval_mult:.3f}, rev={rev_mult:.3f}")
            
            # Run multiple tests
            enrollments = []
            for test_i in range(n_tests_per_config):
                seed = 42000 + config_num * 100 + test_i
                
                print(f"  Test {test_i+1}/{n_tests_per_config} (seed={seed})...")
                
                enrollment = run_calibration_test(
                    counties, n_seekers, eval_mult, rev_mult, seed
                )
                
                if enrollment:
                    enrollments.append(enrollment)
                else:
                    print(f"  ⚠️  Test {test_i+1} failed, skipping")
            
            if not enrollments:
                if verbose:
                    print(f"  ✗ All {n_tests_per_config} tests failed for this config")
                continue
            
            # Average across tests
            avg_enrollment = {
                program: int(np.mean([e[program] for e in enrollments]))
                for program in ['TANF', 'SNAP', 'SSI']
            }
            
            # Calculate error
            errors = calculate_errors(avg_enrollment, targets)
            
            if verbose:
                print(f"  Average enrollment: TANF={avg_enrollment['TANF']:,}, "
                      f"SNAP={avg_enrollment['SNAP']:,}, SSI={avg_enrollment['SSI']:,}")
                print(f"  Errors: TANF={errors['tanf_pct_error']:.1%}, "
                      f"SNAP={errors['snap_pct_error']:.1%}, "
                      f"SSI={errors['ssi_pct_error']:.1%}")
                print(f"  Mean error: {errors['mean_pct_error']:.1%}")
            
            # Track result
            result = {
                'eval_mult': eval_mult,
                'rev_mult': rev_mult,
                'tanf_enrolled': avg_enrollment['TANF'],
                'snap_enrolled': avg_enrollment['SNAP'],
                'ssi_enrolled': avg_enrollment['SSI'],
                **errors
            }
            all_results.append(result)
            
            # Update best
            if errors['mean_pct_error'] < best_error:
                best_error = errors['mean_pct_error']
                best_config = (eval_mult, rev_mult)
                best_enrollment = avg_enrollment
                
                if verbose:
                    print(f"  ★ NEW BEST! Mean error: {best_error:.1%}")
    
    # Check if we found ANY valid configuration
    if best_config is None:
        print(f"\n{'=' * 70}")
        print("ERROR: ALL CONFIGURATIONS FAILED")
        print("=" * 70)
        return None, None, None, pd.DataFrame(all_results)
    
    if verbose:
        print(f"\n{'=' * 70}")
        print("CALIBRATION COMPLETE")
        print("=" * 70)
        print(f"Best configuration:")
        print(f"  Evaluator multiplier: {best_config[0]:.3f}")
        print(f"  Reviewer multiplier: {best_config[1]:.3f}")
        print(f"\nEnrollment match:")
        print(f"  TANF: {best_enrollment['TANF']:,} (target: {targets.tanf_adults:,})")
        print(f"  SNAP: {best_enrollment['SNAP']:,} (target: {targets.snap_persons:,})")
        print(f"  SSI: {best_enrollment['SSI']:,} (target: {targets.ssi_persons:,})")
        print(f"\nMean error: {best_error:.1%}")
    
    results_df = pd.DataFrame(all_results)
    
    return best_config[0], best_config[1], best_enrollment, results_df


def calibrate_massachusetts(save_results=True, verbose=True):
    """
    Main calibration function for Massachusetts.
    """
    start_time = datetime.now()
    
    if verbose:
        print("=" * 70)
        print("MASSACHUSETTS CALIBRATION - V4 (FINAL)")
        print("=" * 70)
        print(f"Start: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Define targets
    targets = CalibrationTarget()
    
    if verbose:
        print("Real enrollment targets:")
        print(f"  TANF adults: {targets.tanf_adults:,}")
        print(f"  SNAP persons: {targets.snap_persons:,}")
        print(f"  SSI persons: {targets.ssi_persons:,}")
    
    # Calculate seekers
    n_seekers = targets.calculate_seekers_from_snap()
    
    if verbose:
        print(f"\nCalculated seekers: {n_seekers:,}")
        print(f"  (From SNAP: {targets.snap_persons:,} / {targets.approval_rate} / {targets.applications_per_seeker})")
    
    # Get MA counties
    acs = load_acs_county_data('src/data/us_census_acs_2022_county_data.csv')
    acs['state'] = acs['county_name'].str.split(', ').str[1]
    ma_counties = acs[acs['state'] == 'Massachusetts']['county_name'].tolist()
    
    if verbose:
        print(f"\nMA counties: {len(ma_counties)}")
    
    # Grid search
    print(f"\n⚠️  QUICK TEST MODE: 2×2 grid (change line 282 after success)")
    
    best_eval, best_rev, best_enroll, results_df = grid_search_capacity(
        counties=ma_counties,
        n_seekers=n_seekers,
        targets=targets,
        eval_range=[1.0, 2.0],  # Quick test
        rev_range=[1.0, 2.0],   # Quick test
        n_tests_per_config=1,   # Quick test
        verbose=verbose
    )
    
    # Check if calibration succeeded
    if best_eval is None:
        print(f"\n{'=' * 70}")
        print("CALIBRATION FAILED")
        print("=" * 70)
        return None
    
    # Package results
    calibrated_params = {
        'state': 'Massachusetts',
        'calibration_date': datetime.now().strftime('%Y-%m-%d'),
        'seekers': n_seekers,
        'capacity_mult_evaluator': best_eval,
        'capacity_mult_reviewer': best_rev,
        'validation_tanf_actual': targets.tanf_adults,
        'validation_tanf_simulated': best_enroll['TANF'],
        'validation_snap_actual': targets.snap_persons,
        'validation_snap_simulated': best_enroll['SNAP'],
        'validation_ssi_actual': targets.ssi_persons,
        'validation_ssi_simulated': best_enroll['SSI'],
        'assumptions': {
            'approval_rate': targets.approval_rate,
            'applications_per_seeker': targets.applications_per_seeker
        }
    }
    
    # Save
    if save_results:
        import os
        os.makedirs('data', exist_ok=True)
        
        params_file = 'data/ma_calibrated_params.json'
        with open(params_file, 'w') as f:
            json.dump(calibrated_params, f, indent=2)
        
        if verbose:
            print(f"\n✓ Saved: {params_file}")
        
        results_file = 'data/ma_calibration_grid_search.csv'
        results_df.to_csv(results_file, index=False)
        
        if verbose:
            print(f"✓ Saved: {results_file}")
    
    # Summary
    total_time = (datetime.now() - start_time).total_seconds()
    
    if verbose:
        print(f"\n{'=' * 70}")
        print("CALIBRATION SUCCESSFUL!")
        print(f"Time: {total_time/60:.1f} minutes")
        print("=" * 70)
        
        print(f"\nCalibrated parameters:")
        print(f"  seekers: {n_seekers:,}")
        print(f"  capacity_mult_evaluator: {best_eval:.3f}")
        print(f"  capacity_mult_reviewer: {best_rev:.3f}")
        
        print(f"\n⚠️  This was a QUICK TEST (2×2 grid)")
        print(f"   For FULL calibration, edit line 282:")
        print(f"     eval_range=[0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 4.0]")
        print(f"     rev_range=[0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 4.0]")
        print(f"     n_tests_per_config=3")
        
        print(f"\nNext: Run Monte Carlo")
        print(f"  python experiments/monte_carlo_massachusetts_v2.py --iterations 20 --calibrated")
    
    return calibrated_params


def main():
    """Entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Calibrate MA simulation to real enrollment'
    )
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Do not save results'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress output'
    )
    
    args = parser.parse_args()
    
    result = calibrate_massachusetts(
        save_results=not args.no_save,
        verbose=not args.quiet
    )
    
    if result is None:
        print("\n❌ Calibration failed.")
        sys.exit(1)
    else:
        print("\n✅ Calibration succeeded!")
        sys.exit(0)


if __name__ == '__main__':
    main()