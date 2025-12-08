"""
Massachusetts Calibration - PROGRAM-SPECIFIC CAPACITY

Each program gets its own capacity multiplier!
- SNAP should have high capacity (easy to get)
- TANF should have low capacity (restrictive)
- SSI should have very low capacity (disability verification)

Run: python scripts/calibrate_ma_by_program.py
"""

import warnings
warnings.filterwarnings('ignore')

import sys
sys.path.insert(0, 'src')
import numpy as np
import pandas as pd
import json
from datetime import datetime
from itertools import product

from data.data_loader import create_realistic_population, load_acs_county_data
from simulation.runner import create_evaluators, create_reviewers, run_month

# Targets (scaled for 10k seekers = 5.5% of 182k)
TANF_TARGET = 1_215  # 22,098 * 0.055
SNAP_TARGET = 14_013  # 255,236 * 0.055  
SSI_TARGET = 347     # 6,323 * 0.055

def run_test(counties, n_seekers, snap_mult, tanf_mult, ssi_mult, rev_mult, seed):
    """Run one simulation with program-specific capacities."""
    try:
        # Create seekers
        seekers = create_realistic_population(
            'src/data/cps_asec_2022_processed_full.csv',
            'src/data/us_census_acs_2022_county_data.csv',
            n_seekers, counties, True, seed
        )
        if not seekers:
            return None
        
        # Create staff
        acs = load_acs_county_data('src/data/us_census_acs_2022_county_data.csv')
        evals = create_evaluators(counties, acs_data=acs, random_seed=seed)
        revs = create_reviewers(counties, acs_data=acs, load_state_models=True, random_seed=seed)
        
        # Apply PROGRAM-SPECIFIC multipliers to evaluators
        for (county, program), evaluator in evals.items():
            if program == 'SNAP':
                evaluator.monthly_capacity *= snap_mult
            elif program == 'TANF':
                evaluator.monthly_capacity *= tanf_mult
            elif program == 'SSI':
                evaluator.monthly_capacity *= ssi_mult
        
        # Apply uniform multiplier to reviewers
        for reviewer in revs.values():
            reviewer.monthly_capacity *= rev_mult
        
        # Run 12 months
        for month in range(12):
            run_month(seekers, evals, revs, month, ai_sorter=None)
        
        # Count
        return {
            'TANF': sum(1 for s in seekers if 'TANF' in s.enrolled_programs),
            'SNAP': sum(1 for s in seekers if 'SNAP' in s.enrolled_programs),
            'SSI': sum(1 for s in seekers if 'SSI' in s.enrolled_programs)
        }
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    print("="*70)
    print("MA CALIBRATION - PROGRAM-SPECIFIC CAPACITY")
    print("="*70)
    print(f"\nTargets: TANF={TANF_TARGET}, SNAP={SNAP_TARGET}, SSI={SSI_TARGET}")
    
    # Get counties
    acs = load_acs_county_data('src/data/us_census_acs_2022_county_data.csv')
    acs['state'] = acs['county_name'].str.split(', ').str[1]
    counties = acs[acs['state'] == 'Massachusetts']['county_name'].tolist()
    
    # Fine-tuned ranges based on previous results
    snap_range = [2.0, 3.0, 4.0]         # Need MORE capacity (was too low at 2.0)
    tanf_range = [0.025]                  # Perfect! Keep it
    ssi_range = [0.005, 0.01, 0.015]     # Need LESS capacity (was too high at 0.01)
    rev_range = [0.025, 0.05]            # Keep tight range
    
    total_configs = len(snap_range) * len(tanf_range) * len(ssi_range) * len(rev_range)
    print(f"\nTesting {total_configs} configurations")
    print(f"SNAP range: {snap_range}")
    print(f"TANF range: {tanf_range}")
    print(f"SSI range: {ssi_range}")
    print(f"Reviewer range: {rev_range}")
    print(f"Estimated time: ~{total_configs * 2}min\n")
    
    best_error = float('inf')
    best_config = None
    results = []
    
    config = 0
    start = datetime.now()
    
    for snap_m, tanf_m, ssi_m, rev_m in product(snap_range, tanf_range, ssi_range, rev_range):
        config += 1
        elapsed = (datetime.now() - start).total_seconds() / 60
        avg = elapsed / config if config > 0 else 0
        remaining = avg * (total_configs - config)
        
        print(f"[{config}/{total_configs}] SNAP={snap_m:.3f}, TANF={tanf_m:.3f}, "
              f"SSI={ssi_m:.3f}, REV={rev_m:.3f} (~{remaining:.0f}min)")
        
        # Run 2 tests
        enrolls = []
        for i in range(2):
            e = run_test(counties, 10000, snap_m, tanf_m, ssi_m, rev_m, 
                        42000 + config*100 + i)
            if e:
                enrolls.append(e)
        
        if not enrolls:
            print("  Failed")
            continue
        
        # Average
        avg_e = {p: int(np.mean([e[p] for e in enrolls])) for p in ['TANF', 'SNAP', 'SSI']}
        
        # Calculate errors
        errors = [
            abs(avg_e['TANF'] - TANF_TARGET) / TANF_TARGET,
            abs(avg_e['SNAP'] - SNAP_TARGET) / SNAP_TARGET,
            abs(avg_e['SSI'] - SSI_TARGET) / SSI_TARGET
        ]
        mean_err = np.mean(errors)
        
        print(f"  Enrolled: T={avg_e['TANF']}, S={avg_e['SNAP']}, I={avg_e['SSI']}")
        print(f"  Errors: T={errors[0]:.1%}, S={errors[1]:.1%}, I={errors[2]:.1%} "
              f"(avg: {mean_err:.1%})")
        
        results.append({
            'snap_mult': snap_m,
            'tanf_mult': tanf_m,
            'ssi_mult': ssi_m,
            'rev_mult': rev_m,
            'tanf_enrolled': avg_e['TANF'],
            'snap_enrolled': avg_e['SNAP'],
            'ssi_enrolled': avg_e['SSI'],
            'tanf_error': errors[0],
            'snap_error': errors[1],
            'ssi_error': errors[2],
            'mean_error': mean_err
        })
        
        if mean_err < best_error:
            best_error = mean_err
            best_config = (snap_m, tanf_m, ssi_m, rev_m, avg_e)
            print(f"  ★ NEW BEST!")
    
    # Results
    print(f"\n{'='*70}")
    print("BEST CONFIGURATION")
    print("="*70)
    print(f"SNAP evaluator mult: {best_config[0]:.3f}")
    print(f"TANF evaluator mult: {best_config[1]:.3f}")
    print(f"SSI evaluator mult:  {best_config[2]:.3f}")
    print(f"Reviewer mult:       {best_config[3]:.3f}")
    print(f"\nEnrollment:")
    print(f"  TANF: {best_config[4]['TANF']:,} (target: {TANF_TARGET:,})")
    print(f"  SNAP: {best_config[4]['SNAP']:,} (target: {SNAP_TARGET:,})")
    print(f"  SSI:  {best_config[4]['SSI']:,} (target: {SSI_TARGET:,})")
    print(f"\nMean error: {best_error:.1%}")
    
    # Save
    params = {
        'state': 'Massachusetts',
        'calibration_date': datetime.now().strftime('%Y-%m-%d'),
        'seekers': 182_311,
        'capacity_mult_snap': best_config[0],
        'capacity_mult_tanf': best_config[1],
        'capacity_mult_ssi': best_config[2],
        'capacity_mult_reviewer': best_config[3],
        'calibration_method': 'program_specific_10k',
        'validation_tanf_target': TANF_TARGET,
        'validation_tanf_actual': best_config[4]['TANF'],
        'validation_snap_target': SNAP_TARGET,
        'validation_snap_actual': best_config[4]['SNAP'],
        'validation_ssi_target': SSI_TARGET,
        'validation_ssi_actual': best_config[4]['SSI'],
        'mean_error': best_error,
        'note': 'Program-specific capacity multipliers. Apply to evaluators by program.'
    }
    
    import os
    os.makedirs('data', exist_ok=True)
    
    with open('data/ma_calibrated_params.json', 'w') as f:
        json.dump(params, f, indent=2)
    
    pd.DataFrame(results).to_csv('data/ma_calibration_results_by_program.csv', index=False)
    
    print(f"\n✓ Saved to data/ma_calibrated_params.json")
    print(f"✓ Saved detailed results to data/ma_calibration_results_by_program.csv")
    print(f"\n✅ Ready for Monte Carlo!")

if __name__ == '__main__':
    main()