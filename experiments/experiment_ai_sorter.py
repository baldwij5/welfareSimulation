"""
Experiment 1: AI Application Sorter

Tests whether "efficiency AI" (simple-first sorting) creates racial disparities.

Hypothesis: Simple-first AI will:
- Increase overall efficiency (more apps processed)
- But create disparities (if Black apps more complex)
- Disadvantage disabled (SSI is complex)

Run with: python experiments/experiment_ai_sorter.py
"""

import sys
sys.path.insert(0, 'src')
import numpy as np

from simulation.runner import run_simulation_with_real_data
from ai.application_sorter import AI_ApplicationSorter


def run_control():
    """Run control condition (no AI, FCFS)."""
    print("=" * 70)
    print("CONTROL: First-Come, First-Served (No AI)")
    print("=" * 70)
    
    counties = [
        'Autauga County, Alabama',      # Small, majority White
        'Jefferson County, Alabama',    # Large, diverse
        'Barbour County, Alabama'       # Small, majority Black
    ]
    
    results = run_simulation_with_real_data(
        cps_file='src/data/cps_asec_2022_processed_full.csv',
        acs_file='src/data/us_census_acs_2022_county_data.csv',
        n_seekers=600,  # 200 per county
        n_months=12,
        counties=counties,
        ai_sorter=None,  # No AI
        random_seed=42
    )
    
    return results


def run_treatment():
    """Run treatment condition (AI sorting by complexity)."""
    print("\n" + "=" * 70)
    print("TREATMENT: AI Simple-First Sorting")
    print("=" * 70)
    
    # Create AI tool
    ai_tool = AI_ApplicationSorter(strategy='simple_first')
    
    counties = [
        'Autauga County, Alabama',
        'Jefferson County, Alabama',
        'Barbour County, Alabama'
    ]
    
    results = run_simulation_with_real_data(
        cps_file='src/data/cps_asec_2022_processed_full.csv',
        acs_file='src/data/us_census_acs_2022_county_data.csv',
        n_seekers=600,
        n_months=12,
        counties=counties,
        ai_sorter=ai_tool,  # With AI
        random_seed=42  # Same seed for comparison
    )
    
    return results


def compare_results(control, treatment):
    """Compare control vs treatment outcomes."""
    print("\n" + "=" * 70)
    print("EXPERIMENTAL RESULTS")
    print("=" * 70)
    
    print("\n1. OVERALL EFFICIENCY")
    print("-" * 70)
    
    print(f"\nControl (FCFS):")
    print(f"  Applications: {control['summary']['total_applications']}")
    print(f"  Approved: {control['summary']['total_approvals']}")
    print(f"  Approval rate: {control['summary']['approval_rate']:.1%}")
    
    exceeded_control = sum(s.get('applications_capacity_exceeded', 0) 
                          for s in control['monthly_stats'])
    print(f"  Capacity exceeded: {exceeded_control} ({exceeded_control/control['summary']['total_applications']*100:.1f}%)")
    
    print(f"\nTreatment (AI Simple-First):")
    print(f"  Applications: {treatment['summary']['total_applications']}")
    print(f"  Approved: {treatment['summary']['total_approvals']}")
    print(f"  Approval rate: {treatment['summary']['approval_rate']:.1%}")
    
    exceeded_treatment = sum(s.get('applications_capacity_exceeded', 0) 
                            for s in treatment['monthly_stats'])
    print(f"  Capacity exceeded: {exceeded_treatment} ({exceeded_treatment/treatment['summary']['total_applications']*100:.1f}%)")
    
    # Efficiency gain
    efficiency_gain = treatment['summary']['total_approvals'] - control['summary']['total_approvals']
    print(f"\n  → AI processed {efficiency_gain} more applications (+{efficiency_gain/control['summary']['total_approvals']*100:.1f}%)")
    
    print("\n2. RACIAL DISPARITIES")
    print("-" * 70)
    
    # Analyze by race
    for results, label in [(control, 'Control'), (treatment, 'Treatment')]:
        print(f"\n{label}:")
        
        for race in ['White', 'Black']:
            race_seekers = [s for s in results['seekers'] if s.race == race]
            if race_seekers:
                apps = sum(s.num_applications for s in race_seekers)
                approved = sum(s.num_approvals for s in race_seekers)
                investigated = sum(s.num_investigations for s in race_seekers)
                
                approval_rate = approved / apps if apps > 0 else 0
                investigation_rate = investigated / apps if apps > 0 else 0
                
                print(f"  {race}: {len(race_seekers)} seekers")
                print(f"    Approval rate: {approval_rate:.1%}")
                print(f"    Investigation rate: {investigation_rate:.1%}")
    
    print("\n3. BY APPLICATION COMPLEXITY")
    print("-" * 70)
    
    # This requires tracking individual applications (not currently stored)
    # For now, analyze by program as proxy
    
    print("\n4. DISPARATE IMPACT")
    print("-" * 70)
    
    # Calculate Black-White gaps
    for results, label in [(control, 'Control'), (treatment, 'Treatment')]:
        white_seekers = [s for s in results['seekers'] if s.race == 'White']
        black_seekers = [s for s in results['seekers'] if s.race == 'Black']
        
        if white_seekers and black_seekers:
            white_apps = sum(s.num_applications for s in white_seekers)
            white_approved = sum(s.num_approvals for s in white_seekers)
            white_rate = white_approved / white_apps if white_apps > 0 else 0
            
            black_apps = sum(s.num_applications for s in black_seekers)
            black_approved = sum(s.num_approvals for s in black_seekers)
            black_rate = black_approved / black_apps if black_apps > 0 else 0
            
            gap = white_rate - black_rate
            
            print(f"\n{label}:")
            print(f"  White approval: {white_rate:.1%}")
            print(f"  Black approval: {black_rate:.1%}")
            print(f"  Gap: {gap*100:.1f} percentage points")


def main():
    """Run complete experiment."""
    print("\n" + "="*70)
    print("EXPERIMENT 1: AI Application Sorter")
    print("="*70)
    print("\nResearch Question:")
    print("  Does 'efficiency AI' (simple-first sorting) create racial disparities?")
    print("\nHypothesis:")
    print("  - AI increases efficiency (more processed)")
    print("  - But creates disparities if Black apps more complex")
    print("  - Disadvantages disabled (SSI is complex)")
    print("\nDesign:")
    print("  Control: FCFS (random order)")
    print("  Treatment: AI sorts simple → complex")
    
    # Run experiments
    control = run_control()
    treatment = run_treatment()
    
    # Compare
    compare_results(control, treatment)
    
    print("\n" + "="*70)
    print("EXPERIMENT COMPLETE")
    print("="*70)
    print("\nKey Question: Did AI increase disparity?")
    print("  If Black approval rate drops more than White → AI amplified inequality")
    print("  Even though AI doesn't see race!")


if __name__ == "__main__":
    main()