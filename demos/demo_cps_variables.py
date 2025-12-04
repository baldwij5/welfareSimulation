"""
Demo: Accessing CPS Variables from Seekers

Shows how seekers now contain ALL CPS data for analysis.
Run with: python demo_cps_variables.py
"""

import sys
sys.path.insert(0, 'src')

from simulation.runner import run_simulation_with_real_data


def demo_seeker_cps_data():
    """Show what CPS data is stored on seekers."""
    print("=" * 70)
    print("SEEKER CPS DATA ACCESS")
    print("=" * 70)
    
    # Run small simulation
    results = run_simulation_with_real_data(
        cps_file='src/data/cps_asec_2022_processed_full.csv',
        acs_file='src/data/us_census_acs_2022_county_data.csv',
        n_seekers=100,
        n_months=6,
        counties=['Autauga County, Alabama'],
        random_seed=42
    )
    
    # Get first seeker
    seeker = results['seekers'][0]
    
    print(f"\nSeeker #{seeker.id} - Basic Info:")
    print(f"  Income: ${seeker.income:,.0f}")
    print(f"  Race: {seeker.race}")
    print(f"  County: {seeker.county}")
    print(f"  Has children: {seeker.has_children}")
    print(f"  Has disability: {seeker.has_disability}")
    
    print(f"\nSeeker #{seeker.id} - Easy-Access CPS Variables:")
    print(f"  Age: {seeker.age}")
    print(f"  Sex: {seeker.sex}")
    print(f"  Education: {seeker.education}")
    print(f"  Married: {seeker.married}")
    print(f"  Num children: {seeker.num_children}")
    print(f"  Employed: {seeker.employed}")
    
    print(f"\nSeeker #{seeker.id} - All CPS Variables Available:")
    print(f"  seeker.cps_data contains {len(seeker.cps_data)} variables!")
    print(f"\nSample of available variables:")
    for i, key in enumerate(list(seeker.cps_data.keys())[:10]):
        print(f"    {key}: {seeker.cps_data[key]}")
    
    print(f"\n  ... and {len(seeker.cps_data) - 10} more variables!")


def demo_education_analysis():
    """Show analysis by education level."""
    print("\n" + "=" * 70)
    print("ANALYSIS BY EDUCATION")
    print("=" * 70)
    
    results = run_simulation_with_real_data(
        cps_file='src/data/cps_asec_2022_processed_full.csv',
        acs_file='src/data/us_census_acs_2022_county_data.csv',
        n_seekers=200,
        n_months=12,
        counties=['Baldwin County, Alabama', 'Barbour County, Alabama'],
        random_seed=42
    )
    
    # Group by education
    by_education = {}
    for seeker in results['seekers']:
        edu = seeker.education if seeker.education else 'Unknown'
        if edu not in by_education:
            by_education[edu] = []
        by_education[edu].append(seeker)
    
    print("\nSeeker counts by education:")
    for edu, seekers in sorted(by_education.items()):
        print(f"  {edu}: {len(seekers)} seekers")
    
    print("\nApplication rates by education:")
    for edu, seekers in sorted(by_education.items()):
        total_apps = sum(s.num_applications for s in seekers)
        avg_apps = total_apps / len(seekers)
        print(f"  {edu}: {avg_apps:.1f} applications per seeker")


def demo_age_analysis():
    """Show analysis by age group."""
    print("\n" + "=" * 70)
    print("ANALYSIS BY AGE")
    print("=" * 70)
    
    results = run_simulation_with_real_data(
        cps_file='src/data/cps_asec_2022_processed_full.csv',
        acs_file='src/data/us_census_acs_2022_county_data.csv',
        n_seekers=200,
        n_months=12,
        counties=['Autauga County, Alabama'],
        random_seed=42
    )
    
    # Group by age
    age_groups = {
        '18-24': [],
        '25-34': [],
        '35-49': [],
        '50-64': []
    }
    
    for seeker in results['seekers']:
        if seeker.age:
            if 18 <= seeker.age <= 24:
                age_groups['18-24'].append(seeker)
            elif 25 <= seeker.age <= 34:
                age_groups['25-34'].append(seeker)
            elif 35 <= seeker.age <= 49:
                age_groups['35-49'].append(seeker)
            elif 50 <= seeker.age <= 64:
                age_groups['50-64'].append(seeker)
    
    print("\nSeeker counts by age group:")
    for age_group, seekers in sorted(age_groups.items()):
        if seekers:
            print(f"  {age_group}: {len(seekers)} seekers")
    
    print("\nMedian income by age group:")
    for age_group, seekers in sorted(age_groups.items()):
        if seekers:
            median_income = np.median([s.income for s in seekers])
            print(f"  {age_group}: ${median_income:,.0f}")


def demo_all_available_variables():
    """Show ALL variables available from CPS."""
    print("\n" + "=" * 70)
    print("ALL AVAILABLE CPS VARIABLES")
    print("=" * 70)
    
    results = run_simulation_with_real_data(
        cps_file='src/data/cps_asec_2022_processed_full.csv',
        acs_file='src/data/us_census_acs_2022_county_data.csv',
        n_seekers=10,
        n_months=1,
        counties=['Autauga County, Alabama'],
        random_seed=42
    )
    
    seeker = results['seekers'][0]
    
    print(f"\nSeeker #{seeker.id} has access to {len(seeker.cps_data)} CPS variables:")
    print("\nComplete list:")
    
    for i, (key, value) in enumerate(sorted(seeker.cps_data.items())):
        print(f"  {i+1:2d}. {key:30s} = {value}")


def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("CPS Variables Access Demo")
    print("="*70)
    print("\nSeekers now store ALL CPS data!")
    print("  • Easy access: seeker.age, seeker.education, seeker.sex")
    print("  • Complete data: seeker.cps_data['VARIABLE_NAME']")
    print("\nYou can now analyze by:")
    print("  • Education level")
    print("  • Age groups")
    print("  • Employment status")
    print("  • Marital status")
    print("  • ANY CPS variable!")
    
    demo_seeker_cps_data()
    demo_education_analysis()
    demo_age_analysis()
    demo_all_available_variables()
    
    print("\n" + "="*70)
    print("Demo Complete!")
    print("="*70)
    print("\nKey Points:")
    print("  • All CPS variables stored in seeker.cps_data")
    print("  • Common variables easily accessible (age, education, sex)")
    print("  • Can analyze outcomes by ANY demographic")
    print("  • Much richer analysis possibilities!")


if __name__ == "__main__":
    import numpy as np
    main()