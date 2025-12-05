"""
Diagnostic: Check Representativeness of Stratified Sampling

Tests whether our race-only stratification produces representative samples
on other important characteristics.

Run with: python scripts/diagnose_representativeness.py
"""

import sys
sys.path.insert(0, 'src')
import pandas as pd
import numpy as np

from data.data_loader import create_realistic_population, load_acs_county_data, load_cps_data, filter_to_eligible


def check_sample_representativeness():
    """
    Check if race-stratified sampling produces representative samples
    on other characteristics.
    """
    print("=" * 70)
    print("REPRESENTATIVENESS DIAGNOSTIC")
    print("=" * 70)
    print("\nQuestion: Does stratifying on race only produce")
    print("representative samples on other characteristics?")
    print("\nChecking: Education, Employment, Disability, Age, Hispanic")
    
    # Select test county
    test_county = 'Jefferson County, Alabama'
    
    print(f"\n{'='*70}")
    print(f"TEST COUNTY: {test_county}")
    print(f"{'='*70}")
    
    # Load CPS
    cps = load_cps_data('src/data/cps_asec_2022_processed_full.csv')
    cps_eligible = filter_to_eligible(cps)
    
    # Get ACS targets
    acs = load_acs_county_data('src/data/us_census_acs_2022_county_data.csv')
    acs_county = acs[acs['county_name'] == test_county].iloc[0]
    
    print(f"\nACS Targets (true county demographics):")
    print(f"  White: {acs_county['white_pct']:.1f}%")
    print(f"  Black: {acs_county['black_pct']:.1f}%")
    print(f"  Hispanic: {acs_county['hispanic_pct']:.1f}%")
    print(f"  Asian: {acs_county.get('asian_pct', 0):.1f}%")
    
    # Create our stratified sample
    print(f"\nCreating stratified sample (n=500)...")
    sample_seekers = create_realistic_population(
        cps_file='src/data/cps_asec_2022_processed_full.csv',
        acs_file='src/data/us_census_acs_2022_county_data.csv',
        n_seekers=500,
        counties=[test_county],
        proportional=False,
        random_seed=42
    )
    
    # Check race distribution (should match perfectly)
    print(f"\n{'='*70}")
    print(f"RACE DISTRIBUTION CHECK")
    print(f"{'='*70}")
    
    race_counts = {}
    for race in ['White', 'Black', 'Hispanic', 'Asian']:
        count = sum(1 for s in sample_seekers if s.race == race)
        pct = count / len(sample_seekers) * 100
        race_counts[race] = (count, pct)
        
        target = acs_county.get(f'{race.lower()}_pct', 0)
        diff = pct - target
        
        print(f"  {race:<10} Sample: {pct:5.1f}%  Target: {target:5.1f}%  Diff: {diff:+5.1f}pp")
    
    # Check OTHER characteristics that we DON'T stratify on
    print(f"\n{'='*70}")
    print(f"OTHER CHARACTERISTICS (Not Stratified)")
    print(f"{'='*70}")
    
    # Education
    print(f"\nEducation distribution:")
    for edu in ['bachelors', 'graduate', 'some_college', 'high_school', 'less_than_hs']:
        count = sum(1 for s in sample_seekers if s.education == edu)
        sample_pct = count / len(sample_seekers) * 100
        
        # What's the true rate in CPS eligible population?
        cps_eligible_count = sum(1 for _, row in cps_eligible.iterrows() if row.get('education') == edu)
        true_pct = cps_eligible_count / len(cps_eligible) * 100
        
        diff = sample_pct - true_pct
        
        print(f"  {edu:<15} Sample: {sample_pct:5.1f}%  CPS: {true_pct:5.1f}%  Diff: {diff:+5.1f}pp")
    
    # Employment
    print(f"\nEmployment:")
    employed_sample = sum(1 for s in sample_seekers if s.employed) / len(sample_seekers) * 100
    employed_cps = sum(1 for _, row in cps_eligible.iterrows() if row.get('employed')) / len(cps_eligible) * 100
    print(f"  Employed: Sample {employed_sample:.1f}%  vs CPS {employed_cps:.1f}%  (Diff: {employed_sample - employed_cps:+.1f}pp)")
    
    # Disability
    print(f"\nDisability:")
    disabled_sample = sum(1 for s in sample_seekers if s.has_disability) / len(sample_seekers) * 100
    disabled_cps = sum(1 for _, row in cps_eligible.iterrows() if row.get('has_disability')) / len(cps_eligible) * 100
    print(f"  Disabled: Sample {disabled_sample:.1f}%  vs CPS {disabled_cps:.1f}%  (Diff: {disabled_sample - disabled_cps:+.1f}pp)")
    
    # Check WITHIN-RACE characteristics
    print(f"\n{'='*70}")
    print(f"WITHIN-RACE CHARACTERISTICS (Sample Only)")
    print(f"{'='*70}")
    
    # Black population specifically
    black_seekers = [s for s in sample_seekers if s.race == 'Black']
    white_seekers = [s for s in sample_seekers if s.race == 'White']
    
    print(f"\nBlack population in sample (n={len(black_seekers)}):")
    
    # Education among Black
    black_college = sum(1 for s in black_seekers if s.education in ['bachelors', 'graduate']) / len(black_seekers) * 100
    black_hs = sum(1 for s in black_seekers if s.education == 'high_school') / len(black_seekers) * 100
    black_less = sum(1 for s in black_seekers if s.education == 'less_than_hs') / len(black_seekers) * 100
    
    print(f"  College educated: {black_college:.1f}%")
    print(f"  High school: {black_hs:.1f}%")
    print(f"  Less than HS: {black_less:.1f}%")
    
    # Employment among Black
    black_employed = sum(1 for s in black_seekers if s.employed) / len(black_seekers) * 100
    print(f"  Employed: {black_employed:.1f}%")
    
    # Disability among Black
    black_disabled = sum(1 for s in black_seekers if s.has_disability) / len(black_seekers) * 100
    print(f"  Disabled: {black_disabled:.1f}%")
    
    print(f"\nWhite population in sample (n={len(white_seekers)}):")
    
    # Same for White
    white_college = sum(1 for s in white_seekers if s.education in ['bachelors', 'graduate']) / len(white_seekers) * 100
    white_employed = sum(1 for s in white_seekers if s.employed) / len(white_seekers) * 100
    white_disabled = sum(1 for s in white_seekers if s.has_disability) / len(white_seekers) * 100
    
    print(f"  College educated: {white_college:.1f}%")
    print(f"  Employed: {white_employed:.1f}%")
    print(f"  Disabled: {white_disabled:.1f}%")
    
    # Compare Black vs White
    print(f"\nBlack-White differences in sample:")
    print(f"  College: {black_college - white_college:+.1f}pp")
    print(f"  Employment: {black_employed - white_employed:+.1f}pp")
    print(f"  Disability: {black_disabled - white_disabled:+.1f}pp")
    
    print(f"\n{'='*70}")
    print(f"CONCLUSION")
    print(f"{'='*70}")
    print(f"\nIf differences are:")
    print(f"  < 5pp  → Stratification is fine (representative)")
    print(f"  5-10pp → Some bias, but probably OK")
    print(f"  > 10pp → Significant bias, consider Monte Carlo")


def main():
    """Run representativeness check."""
    print("\n" + "="*70)
    print("Checking Sample Representativeness")
    print("="*70)
    print("\nThis tests whether our race-only stratification")
    print("produces representative samples on other dimensions.")
    
    check_sample_representativeness()
    
    print("\n" + "="*70)
    print("NEXT STEPS")
    print("="*70)
    print("\nIf samples are representative:")
    print("  → Current approach is fine")
    print("  → Can analyze multiple disparities without Monte Carlo")
    print("\nIf samples are NOT representative:")
    print("  → Consider Monte Carlo for robustness")
    print("  → Or multi-dimensional stratification")


if __name__ == "__main__":
    main()