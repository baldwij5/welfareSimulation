"""
Diagnostic: Why Did AI Reduce Disparity?

Investigates the surprising experimental finding.
Run with: python scripts/diagnose_ai_results.py
"""

import sys
sys.path.insert(0, 'src')
import numpy as np

from data.data_loader import create_realistic_population


def diagnose_population_differences():
    """Check if Black and White seekers differ systematically."""
    print("=" * 70)
    print("DIAGNOSTIC: Population Differences by Race")
    print("=" * 70)
    
    # Create population
    counties = [
        'Autauga County, Alabama',
        'Jefferson County, Alabama',
        'Barbour County, Alabama'
    ]
    
    print("\nCreating population...")
    seekers = create_realistic_population(
        cps_file='src/data/cps_asec_2022_processed_full.csv',
        acs_file='src/data/us_census_acs_2022_county_data.csv',
        n_seekers=600,
        counties=counties,
        random_seed=42
    )
    
    # Separate by race
    white = [s for s in seekers if s.race == 'White']
    black = [s for s in seekers if s.race == 'Black']
    
    print(f"\n{'='*70}")
    print(f"COMPARISON BY RACE")
    print(f"{'='*70}\n")
    
    print(f"Sample sizes:")
    print(f"  White: {len(white)}")
    print(f"  Black: {len(black)}")
    
    # Compare bureaucracy points
    white_points = [s.bureaucracy_navigation_points for s in white]
    black_points = [s.bureaucracy_navigation_points for s in black]
    
    print(f"\nBureaucracy Navigation Points:")
    print(f"  White: mean={np.mean(white_points):.2f}, median={np.median(white_points):.2f}")
    print(f"  Black: mean={np.mean(black_points):.2f}, median={np.median(black_points):.2f}")
    print(f"  Difference: {np.mean(white_points) - np.mean(black_points):.2f}")
    
    if np.mean(white_points) > np.mean(black_points) + 1:
        print(f"  → White has HIGHER bureaucracy points (structural advantage)")
    
    # Compare education
    white_edu = [s.education for s in white if s.education]
    black_edu = [s.education for s in black if s.education]
    
    print(f"\nEducation (% with each level):")
    for edu in ['bachelors', 'graduate', 'high_school', 'some_college', 'less_than_hs']:
        white_pct = sum(1 for e in white_edu if e == edu) / len(white_edu) * 100
        black_pct = sum(1 for e in black_edu if e == edu) / len(black_edu) * 100
        print(f"  {edu:<20} White: {white_pct:5.1f}%  Black: {black_pct:5.1f}%")
    
    # Compare employment
    white_employed = sum(1 for s in white if s.employed) / len(white) * 100
    black_employed = sum(1 for s in black if s.employed) / len(black) * 100
    
    print(f"\nEmployment:")
    print(f"  White: {white_employed:.1f}% employed")
    print(f"  Black: {black_employed:.1f}% employed")
    
    # Compare income
    white_income = [s.income for s in white]
    black_income = [s.income for s in black]
    
    print(f"\nIncome:")
    print(f"  White: mean=${np.mean(white_income):,.0f}, median=${np.median(white_income):,.0f}")
    print(f"  Black: mean=${np.mean(black_income):,.0f}, median=${np.median(black_income):,.0f}")
    
    # Compare disability
    white_disability = sum(1 for s in white if s.has_disability) / len(white) * 100
    black_disability = sum(1 for s in black if s.has_disability) / len(black) * 100
    
    print(f"\nDisability:")
    print(f"  White: {white_disability:.1f}% have disability")
    print(f"  Black: {black_disability:.1f}% have disability")
    
    # Sample applications to check complexity
    print(f"\n{'='*70}")
    print(f"APPLICATION COMPLEXITY BY RACE")
    print(f"{'='*70}\n")
    
    # Create test applications
    white_apps = []
    for s in white[:100]:
        for prog in ['SNAP', 'TANF', 'SSI']:
            app = s.create_application(prog, month=0, application_id=0)
            if app:
                white_apps.append(app)
    
    black_apps = []
    for s in black[:100]:
        for prog in ['SNAP', 'TANF', 'SSI']:
            app = s.create_application(prog, month=0, application_id=0)
            if app:
                black_apps.append(app)
    
    white_complexity = [a.complexity for a in white_apps if a.complexity]
    black_complexity = [a.complexity for a in black_apps if a.complexity]
    
    print(f"Application Complexity:")
    print(f"  White: mean={np.mean(white_complexity):.3f}, median={np.median(white_complexity):.3f}")
    print(f"  Black: mean={np.mean(black_complexity):.3f}, median={np.median(black_complexity):.3f}")
    print(f"  Difference: {np.mean(white_complexity) - np.mean(black_complexity):.3f}")
    
    if np.mean(black_complexity) > np.mean(white_complexity):
        print(f"  → Black applications MORE complex (disadvantaged by simple-first AI)")
    elif np.mean(white_complexity) > np.mean(black_complexity):
        print(f"  → White applications MORE complex (disadvantaged by simple-first AI)")
    
    # County distribution
    print(f"\n{'='*70}")
    print(f"COUNTY DISTRIBUTION")
    print(f"{'='*70}\n")
    
    for county in counties:
        white_county = sum(1 for s in white if s.county == county)
        black_county = sum(1 for s in black if s.county == county)
        print(f"  {county}:")
        print(f"    White: {white_county} ({white_county/len(white)*100:.1f}%)")
        print(f"    Black: {black_county} ({black_county/len(black)*100:.1f}%)")


def main():
    """Run diagnostics."""
    print("\n" + "="*70)
    print("DIAGNOSTIC: Understanding Experimental Results")
    print("="*70)
    print("\nQuestion: Why did AI REDUCE disparity instead of increase it?")
    print("\nPossible explanations:")
    print("  1. Black apps are SIMPLER (benefit from simple-first)")
    print("  2. White apps are MORE COMPLEX (hurt by simple-first)")
    print("  3. Different county distributions")
    print("  4. Bureaucracy points differ by race")
    
    diagnose_population_differences()
    
    print("\n" + "="*70)
    print("DIAGNOSTIC COMPLETE")
    print("="*70)
    print("\nKey insights will explain the surprising result!")


if __name__ == "__main__":
    main()