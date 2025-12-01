"""
Demo: Simulation with Real CPS/ACS Data

Shows how to use real data to create realistic populations.
Run with: python demo_real_data.py
"""

import sys
import os

# Add src to path
sys.path.insert(0, 'src')

from simulation.runner import run_simulation_with_real_data
from data.data_loader import load_cps_data, load_acs_county_data, get_county_characteristics


def demo_data_exploration():
    """Explore the CPS and ACS data."""
    print("=" * 70)
    print("DATA EXPLORATION")
    print("=" * 70)
    
    # Load data
    cps = load_cps_data()
    acs = load_acs_county_data()
    
    print("\nCPS Data:")
    print(f"  Total observations: {len(cps):,}")
    print(f"  Key variables: INCTOT, race, has_children, has_disability")
    
    # Show income distribution
    working_age = cps[(cps['AGE'] >= 18) & (cps['AGE'] <= 64)]
    print(f"\nWorking-age adults (18-64): {len(working_age):,}")
    print(f"  Median income: ${working_age['INCTOT'].median():,.0f}")
    print(f"  Has children: {(working_age['has_children'] == 1).sum()} ({(working_age['has_children'] == 1).mean()*100:.1f}%)")
    print(f"  Has disability: {(working_age['has_disability'] == 1).sum()} ({(working_age['has_disability'] == 1).mean()*100:.1f}%)")
    
    print("\nACS Data:")
    print(f"  Total counties: {len(acs):,}")
    print(f"  Variables: demographics, poverty, program participation")
    
    # Show sample counties
    print(f"\nSample counties:")
    for i, county_name in enumerate(acs['county_name'].head(5)):
        county_data = get_county_characteristics(acs, county_name)
        print(f"  {county_name}:")
        print(f"    Population: {county_data['population']:,}")
        print(f"    Median income: ${county_data['median_income']:,.0f}")
        print(f"    Poverty rate: {county_data['poverty_rate']:.1f}%")


def demo_realistic_population():
    """Create and analyze a realistic population."""
    print("\n" + "=" * 70)
    print("REALISTIC POPULATION CREATION")
    print("=" * 70)
    
    counties = [
        'Autauga County, Alabama',
        'Baldwin County, Alabama',
        'Barbour County, Alabama'
    ]
    
    results = run_simulation_with_real_data(
        cps_file='src/data/cps_asec_2022_processed_full.csv',
        acs_file='src/data/us_census_acs_2022_county_data.csv',
        n_seekers=300,  # 100 per county
        n_months=12,
        counties=counties,
        random_seed=42
    )
    
    print("\n" + "=" * 70)
    print("SIMULATION RESULTS")
    print("=" * 70)
    
    print(f"\nOverall:")
    print(f"  Seekers: {results['summary']['total_seekers']}")
    print(f"  Applications: {results['summary']['total_applications']}")
    print(f"  Approved: {results['summary']['total_approvals']} ({results['summary']['approval_rate']:.1%})")
    
    # Analyze by county
    print(f"\nBy County:")
    for county in counties:
        county_seekers = [s for s in results['seekers'] if s.county == county]
        apps = sum(s.num_applications for s in county_seekers)
        approved = sum(s.num_approvals for s in county_seekers)
        
        print(f"\n  {county}:")
        print(f"    Seekers: {len(county_seekers)}")
        print(f"    Applications: {apps}")
        print(f"    Approved: {approved}")
        if apps > 0:
            print(f"    Approval rate: {approved/apps:.1%}")
    
    # Analyze by race
    print(f"\nBy Race:")
    for race in ['White', 'Black', 'Hispanic', 'Asian']:
        race_seekers = [s for s in results['seekers'] if s.race == race]
        if race_seekers:
            apps = sum(s.num_applications for s in race_seekers)
            approved = sum(s.num_approvals for s in race_seekers)
            investigated = sum(s.num_investigations for s in race_seekers)
            
            print(f"\n  {race}: {len(race_seekers)} seekers")
            print(f"    Applications: {apps}")
            if apps > 0:
                print(f"    Approval rate: {approved/apps:.1%}")
                print(f"    Investigation rate: {investigated/apps:.1%}")


def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("Simulation with Real CPS/ACS Data")
    print("="*70)
    print("\nUses real data to create realistic populations:")
    print("  • CPS: Individual characteristics (income, race, children, disability)")
    print("  • ACS: County demographics (poverty, program participation)")
    print("\nResult: Much more realistic than random generation!")
    
    demo_data_exploration()
    demo_realistic_population()
    
    print("\n" + "="*70)
    print("Demo Complete!")
    print("="*70)
    print("\nKey Benefits:")
    print("  • Realistic income distributions (from actual data)")
    print("  • Realistic demographic patterns")
    print("  • County-specific characteristics")
    print("  • Based on 152,733 real people!")
    print("\nYou can now run realistic simulations for dissertation research!")


if __name__ == "__main__":
    main()