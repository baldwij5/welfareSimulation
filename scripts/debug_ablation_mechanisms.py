"""
Debug Ablation: Verify Mechanisms Are Actually Being Applied

This script checks if mechanism configurations are actually affecting
seeker behavior and outcomes.

Usage:
    python scripts/debug_ablation_mechanisms.py

Tests:
    1. Do baseline seekers have None for disabled mechanisms?
    2. Do bureaucracy-only seekers have points but no fraud tracking?
    3. Are final outcomes actually different between configs?

Author: Jack Baldwin
Date: December 2024
"""

import sys
sys.path.insert(0, 'src')

import numpy as np
from core.mechanism_config import MechanismConfig
from core.seeker import Seeker
from data.data_loader import create_realistic_population

print("="*80)
print("DEBUGGING ABLATION MECHANISMS")
print("="*80)

# Test each configuration
configs = [
    ('Baseline', MechanismConfig.baseline()),
    ('Only Bureaucracy', MechanismConfig.only_bureaucracy()),
    ('Only Fraud', MechanismConfig.only_fraud()),
    ('Only Learning', MechanismConfig.only_learning()),
    ('Full Model', MechanismConfig.full_model())
]

counties = ['Suffolk County, Massachusetts']

for config_name, config in configs:
    print(f"\n{'='*80}")
    print(f"TESTING: {config_name}")
    print(f"{'='*80}")
    print(f"Active mechanisms: {config.get_active_mechanisms()}")
    
    # Create small population
    seekers = create_realistic_population(
        'src/data/cps_asec_2022_processed_full.csv',
        'src/data/us_census_acs_2022_county_data.csv',
        100,
        counties,
        proportional=True,
        random_seed=42,
        mechanism_config=config
    )
    
    # Check first 5 seekers
    print(f"\nChecking first 5 seekers:")
    
    for i, s in enumerate(seekers[:5]):
        print(f"\n  Seeker {s.id} (race={s.race}, education={s.cps_data.get('education', 'unknown')}):")
        
        # Check bureaucracy points
        if s.bureaucracy_navigation_points is None:
            print(f"    Bureaucracy points: None (unlimited)")
        else:
            print(f"    Bureaucracy points: {s.bureaucracy_navigation_points}")
        
        # Check fraud tracking
        if hasattr(s, 'fraud_detections'):
            if s.fraud_detections is None:
                print(f"    Fraud tracking: None (disabled)")
            else:
                print(f"    Fraud tracking: {len(s.fraud_detections)} detections")
        
        # Check learning
        print(f"    Initial SNAP belief: {s.perceived_approval_probability.get('SNAP', 'N/A'):.2f}")
        
        # Test learning by simulating denial
        initial_belief = s.perceived_approval_probability.get('SNAP', 0.70)
        s.update_beliefs('SNAP', 'DENIED')
        after_belief = s.perceived_approval_probability.get('SNAP', 0.70)
        
        if after_belief == initial_belief:
            print(f"    Learning: DISABLED (belief unchanged after denial)")
        else:
            print(f"    Learning: ENABLED (belief {initial_belief:.2f} → {after_belief:.2f})")
    
    # Summary statistics
    print(f"\n  POPULATION SUMMARY:")
    points_list = [s.bureaucracy_navigation_points for s in seekers 
                   if s.bureaucracy_navigation_points is not None]
    
    if points_list:
        print(f"    Bureaucracy points: mean={np.mean(points_list):.1f}, "
              f"min={np.min(points_list):.1f}, max={np.max(points_list):.1f}")
    else:
        print(f"    Bureaucracy points: ALL None (disabled)")
    
    # Check if fraud_detections exists and is used
    has_fraud_tracking = any(
        hasattr(s, 'fraud_detections') and s.fraud_detections is not None 
        for s in seekers
    )
    print(f"    Fraud tracking: {'ENABLED' if has_fraud_tracking else 'DISABLED'}")
    
    # Expected configuration
    print(f"\n  EXPECTED STATE:")
    print(f"    Bureaucracy: {'ENABLED' if config.bureaucracy_points_enabled else 'DISABLED'}")
    print(f"    Fraud: {'ENABLED' if config.fraud_history_enabled else 'DISABLED'}")
    print(f"    Learning: {'ENABLED' if config.learning_enabled else 'DISABLED'}")
    print(f"    Discrimination: {'ENABLED' if config.state_discrimination_enabled else 'DISABLED'}")


# =============================================================================
# CRITICAL TEST: Are outcomes actually different?
# =============================================================================

print(f"\n{'='*80}")
print("CRITICAL TEST: Do Different Configs Produce Different Outcomes?")
print(f"{'='*80}")

# Create seekers with baseline vs full model
baseline_seekers = create_realistic_population(
    'src/data/cps_asec_2022_processed_full.csv',
    'src/data/us_census_acs_2022_county_data.csv',
    100,
    counties,
    proportional=True,
    random_seed=99,
    mechanism_config=MechanismConfig.baseline()
)

full_seekers = create_realistic_population(
    'src/data/cps_asec_2022_processed_full.csv',
    'src/data/us_census_acs_2022_county_data.csv',
    100,
    counties,
    proportional=True,
    random_seed=99,  # SAME seed!
    mechanism_config=MechanismConfig.full_model()
)

# Compare attributes
print(f"\nBaseline vs Full Model (same seed, different configs):")

# Bureaucracy points
baseline_points = [s.bureaucracy_navigation_points for s in baseline_seekers[:10] 
                   if s.bureaucracy_navigation_points is not None]
full_points = [s.bureaucracy_navigation_points for s in full_seekers[:10]
               if s.bureaucracy_navigation_points is not None]

print(f"\nBureaucracy points (first 10 seekers):")
print(f"  Baseline: {baseline_points if baseline_points else 'None (all unlimited)'}")
print(f"  Full:     {full_points if full_points else 'None (all unlimited)'}")

if not baseline_points and full_points:
    print(f"  ✓ CORRECT: Baseline has no points, Full has points")
elif baseline_points and not full_points:
    print(f"  ❌ WRONG: Baseline has points, Full doesn't!")
elif baseline_points == full_points:
    print(f"  ❌ BUG: Both configs have same points!")
else:
    print(f"  ⚠️  Both have no points (unexpected)")

# Learning
print(f"\nLearning (test belief updating):")
b_seeker = baseline_seekers[0]
f_seeker = full_seekers[0]

b_initial = b_seeker.perceived_approval_probability.get('SNAP', 0.70)
f_initial = f_seeker.perceived_approval_probability.get('SNAP', 0.70)

b_seeker.update_beliefs('SNAP', 'DENIED')
f_seeker.update_beliefs('SNAP', 'DENIED')

b_after = b_seeker.perceived_approval_probability.get('SNAP', 0.70)
f_after = f_seeker.perceived_approval_probability.get('SNAP', 0.70)

print(f"  Baseline: {b_initial:.3f} → {b_after:.3f} (change: {b_after - b_initial:.3f})")
print(f"  Full:     {f_initial:.3f} → {f_after:.3f} (change: {f_after - f_initial:.3f})")

if abs(b_after - b_initial) < 0.001 and abs(f_after - f_initial) > 0.01:
    print(f"  ✓ CORRECT: Baseline doesn't learn, Full does")
elif abs(b_after - b_initial) > 0.01 and abs(f_after - f_initial) < 0.001:
    print(f"  ❌ WRONG: Baseline learns, Full doesn't!")
elif abs(b_after - b_initial) < 0.001 and abs(f_after - f_initial) < 0.001:
    print(f"  ❌ BUG: Neither config learns!")
else:
    print(f"  ❌ BUG: Both configs learn the same!")

print(f"\n{'='*80}")
print("DIAGNOSIS COMPLETE")
print(f"{'='*80}")
print(f"\nIf you see '❌ BUG' or '❌ WRONG' above, mechanisms aren't being applied!")
print(f"If you see '✓ CORRECT', mechanisms work but don't affect final outcomes.")