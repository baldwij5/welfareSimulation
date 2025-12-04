"""
Parallel Worlds Experiment: Control vs Treatment on SAME Population

The cleanest experimental design:
- Create ONE population of seekers
- Run simulation TWICE:
  1. Control: FCFS (no AI)
  2. Treatment: AI sorting
- Compare outcomes on EXACT SAME people

This eliminates ALL confounding from population differences.

Run with: python experiments/experiment_parallel_worlds.py
"""

import sys
sys.path.insert(0, 'src')
import numpy as np
import pandas as pd
import copy

from data.data_loader import create_realistic_population
from simulation.runner import create_evaluators, create_reviewers, run_month
from ai.application_sorter import AI_ApplicationSorter


def run_parallel_worlds_experiment(cps_file, acs_file, n_seekers, n_months, counties, random_seed=42):
    """
    Run parallel worlds experiment.
    
    Create ONE population, run TWO simulations:
    1. Control (FCFS)
    2. Treatment (AI sorting)
    
    Perfect counterfactual comparison.
    
    Args:
        cps_file: CPS data path
        acs_file: ACS data path
        n_seekers: Total seekers
        n_months: Months to simulate
        counties: List of counties
        random_seed: Random seed
        
    Returns:
        dict: Both control and treatment results
    """
    print("=" * 70)
    print("PARALLEL WORLDS EXPERIMENT")
    print("=" * 70)
    print("\nDesign:")
    print("  1. Create ONE population of seekers")
    print("  2. Run simulation in Control World (FCFS)")
    print("  3. Run simulation in Treatment World (AI sorting)")
    print("  4. Compare SAME people in both worlds")
    print("\n  → Perfect counterfactual! No confounding!")
    
    # Step 1: Create ONE population (used in both worlds)
    print(f"\n{'='*70}")
    print("STEP 1: Creating Shared Population")
    print(f"{'='*70}")
    
    seekers_master = create_realistic_population(
        cps_file=cps_file,
        acs_file=acs_file,
        n_seekers=n_seekers,
        counties=counties,
        proportional=True,  # PROPORTIONAL allocation by eligible population
        random_seed=random_seed
    )
    
    print(f"\n✓ Created {len(seekers_master)} seekers across {len(counties)} counties")
    print(f"  This SAME population will be used in both worlds")
    
    # Show population characteristics
    white_seekers = [s for s in seekers_master if s.race == 'White']
    black_seekers = [s for s in seekers_master if s.race == 'Black']
    
    print(f"\n  Population demographics:")
    print(f"    White: {len(white_seekers)} ({len(white_seekers)/len(seekers_master)*100:.1f}%)")
    print(f"    Black: {len(black_seekers)} ({len(black_seekers)/len(seekers_master)*100:.1f}%)")
    
    # Step 2: Run Control World (FCFS)
    print(f"\n{'='*70}")
    print("STEP 2: Control World (FCFS, No AI)")
    print(f"{'='*70}")
    
    control_results = run_one_world(
        seekers_master=seekers_master,
        acs_file=acs_file,
        n_months=n_months,
        counties=counties,
        ai_sorter=None,  # No AI
        random_seed=random_seed,
        world_name="Control"
    )
    
    # Step 3: Run Treatment World (AI)
    print(f"\n{'='*70}")
    print("STEP 3: Treatment World (AI Simple-First)")
    print(f"{'='*70}")
    
    ai_tool = AI_ApplicationSorter(strategy='simple_first')
    
    treatment_results = run_one_world(
        seekers_master=seekers_master,
        acs_file=acs_file,
        n_months=n_months,
        counties=counties,
        ai_sorter=ai_tool,  # With AI
        random_seed=random_seed,
        world_name="Treatment"
    )
    
    # Step 4: Compare
    print(f"\n{'='*70}")
    print("STEP 4: Comparing Parallel Worlds")
    print(f"{'='*70}")
    
    comparison = compare_parallel_worlds(control_results, treatment_results, seekers_master)
    
    return {
        'control': control_results,
        'treatment': treatment_results,
        'comparison': comparison,
        'seekers': seekers_master
    }


def run_one_world(seekers_master, acs_file, n_months, counties, ai_sorter, random_seed, world_name):
    """
    Run simulation in one world (control or treatment).
    
    IMPORTANT: We create FRESH copies of seekers so their state doesn't carry over.
    Each world gets a pristine version of the population.
    """
    from data.data_loader import load_acs_county_data
    
    print(f"\nRunning {world_name} World...")
    
    # Create FRESH copies of seekers (so state doesn't carry over between worlds)
    seekers = []
    for original_seeker in seekers_master:
        # Create new seeker with same characteristics
        from core.seeker import Seeker
        
        fresh_seeker = Seeker(
            seeker_id=original_seeker.id,
            race=original_seeker.race,
            income=original_seeker.income,
            county=original_seeker.county,
            has_children=original_seeker.has_children,
            has_disability=original_seeker.has_disability,
            cps_data=original_seeker.cps_data,
            random_state=np.random.RandomState(original_seeker.id)  # Same seed = same behavior
        )
        seekers.append(fresh_seeker)
    
    # Create staff
    acs_data = load_acs_county_data(acs_file)
    evaluators = create_evaluators(counties, acs_data=acs_data, random_seed=random_seed)
    reviewers = create_reviewers(counties, acs_data=acs_data, random_seed=random_seed)
    
    # Run simulation month by month
    monthly_stats = []
    
    for month in range(n_months):
        stats = run_month(seekers, evaluators, reviewers, month, ai_sorter=ai_sorter)
        monthly_stats.append(stats)
        
        if (month + 1) % 6 == 0:
            print(f"  Completed month {month + 1}/{n_months}")
    
    # Calculate summary
    total_apps = sum(s['applications_submitted'] for s in monthly_stats)
    total_approved = sum(s['applications_approved'] for s in monthly_stats)
    
    summary = {
        'total_seekers': len(seekers),
        'total_applications': total_apps,
        'total_approvals': total_approved,
        'approval_rate': total_approved / total_apps if total_apps > 0 else 0,
        'world': world_name
    }
    
    return {
        'seekers': seekers,
        'evaluators': evaluators,
        'reviewers': reviewers,
        'monthly_stats': monthly_stats,
        'summary': summary
    }


def compare_parallel_worlds(control, treatment, seekers_master):
    """
    Compare outcomes between parallel worlds.
    
    Since we have the SAME people, we can do person-level comparisons!
    """
    print(f"\nComparing SAME population in parallel worlds...")
    
    # Match seekers by ID
    control_seekers = {s.id: s for s in control['seekers']}
    treatment_seekers = {s.id: s for s in treatment['seekers']}
    
    # Individual-level treatment effects
    individual_effects = []
    
    for seeker_id in control_seekers.keys():
        if seeker_id in treatment_seekers:
            c_seeker = control_seekers[seeker_id]
            t_seeker = treatment_seekers[seeker_id]
            
            # Calculate approval rates for this individual
            c_rate = c_seeker.num_approvals / c_seeker.num_applications if c_seeker.num_applications > 0 else 0
            t_rate = t_seeker.num_approvals / t_seeker.num_applications if t_seeker.num_applications > 0 else 0
            
            individual_effects.append({
                'seeker_id': seeker_id,
                'race': c_seeker.race,
                'education': c_seeker.education,
                'bureaucracy_points': c_seeker.bureaucracy_navigation_points,
                'control_approval_rate': c_rate,
                'treatment_approval_rate': t_rate,
                'treatment_effect': t_rate - c_rate
            })
    
    effects_df = pd.DataFrame(individual_effects)
    
    # Aggregate statistics
    print(f"\n{'='*70}")
    print("PARALLEL WORLDS COMPARISON")
    print(f"{'='*70}\n")
    
    print(f"1. OVERALL EFFICIENCY")
    print("-" * 70)
    
    print(f"\nControl World (FCFS):")
    print(f"  Applications: {control['summary']['total_applications']}")
    print(f"  Approved: {control['summary']['total_approvals']}")
    print(f"  Approval rate: {control['summary']['approval_rate']:.1%}")
    
    print(f"\nTreatment World (AI):")
    print(f"  Applications: {treatment['summary']['total_applications']}")
    print(f"  Approved: {treatment['summary']['total_approvals']}")
    print(f"  Approval rate: {treatment['summary']['approval_rate']:.1%}")
    
    efficiency_gain = treatment['summary']['total_approvals'] - control['summary']['total_approvals']
    print(f"\n  → Efficiency gain: {efficiency_gain:+.0f} applications ({efficiency_gain/control['summary']['total_approvals']*100:+.1f}%)")
    
    # Racial disparities
    print(f"\n2. RACIAL DISPARITIES")
    print("-" * 70)
    
    for world, results in [('Control', control), ('Treatment', treatment)]:
        white_outcomes = [s for s in results['seekers'] if s.race == 'White']
        black_outcomes = [s for s in results['seekers'] if s.race == 'Black']
        
        if white_outcomes and black_outcomes:
            white_apps = sum(s.num_applications for s in white_outcomes)
            white_approved = sum(s.num_approvals for s in white_outcomes)
            white_rate = white_approved / white_apps if white_apps > 0 else 0
            
            black_apps = sum(s.num_applications for s in black_outcomes)
            black_approved = sum(s.num_approvals for s in black_outcomes)
            black_rate = black_approved / black_apps if black_apps > 0 else 0
            
            gap = white_rate - black_rate
            
            print(f"\n{world} World:")
            print(f"  White: {white_rate:.1%} approval ({white_approved}/{white_apps})")
            print(f"  Black: {black_rate:.1%} approval ({black_approved}/{black_apps})")
            print(f"  Gap: {gap*100:.1f} percentage points")
    
    # Calculate treatment effect
    control_white = [s for s in control['seekers'] if s.race == 'White']
    control_black = [s for s in control['seekers'] if s.race == 'Black']
    treatment_white = [s for s in treatment['seekers'] if s.race == 'White']
    treatment_black = [s for s in treatment['seekers'] if s.race == 'Black']
    
    c_white_rate = sum(s.num_approvals for s in control_white) / sum(s.num_applications for s in control_white)
    c_black_rate = sum(s.num_approvals for s in control_black) / sum(s.num_applications for s in control_black)
    c_gap = c_white_rate - c_black_rate
    
    t_white_rate = sum(s.num_approvals for s in treatment_white) / sum(s.num_applications for s in treatment_white)
    t_black_rate = sum(s.num_approvals for s in treatment_black) / sum(s.num_applications for s in treatment_black)
    t_gap = t_white_rate - t_black_rate
    
    treatment_effect = t_gap - c_gap
    
    print(f"\n3. TREATMENT EFFECT (Difference-in-Differences)")
    print("-" * 70)
    print(f"\nControl gap: {c_gap*100:.1f}pp")
    print(f"Treatment gap: {t_gap*100:.1f}pp")
    print(f"\nTreatment Effect: {treatment_effect*100:+.1f}pp")
    
    if treatment_effect > 0.01:
        print(f"  → AI INCREASED racial disparity")
    elif treatment_effect < -0.01:
        print(f"  → AI DECREASED racial disparity")
    else:
        print(f"  → No significant effect")
    
    # Statistical test (paired by individual)
    print(f"\n4. INDIVIDUAL-LEVEL ANALYSIS")
    print("-" * 70)
    
    # For each person, compare their outcomes in both worlds
    white_effects = effects_df[effects_df['race'] == 'White']['treatment_effect']
    black_effects = effects_df[effects_df['race'] == 'Black']['treatment_effect']
    
    print(f"\nAverage individual treatment effect:")
    print(f"  White: {white_effects.mean():+.1%}")
    print(f"  Black: {black_effects.mean():+.1%}")
    print(f"  Difference: {(black_effects.mean() - white_effects.mean())*100:+.1f}pp")
    
    # T-test for differential effects
    from scipy import stats
    t_stat, p_value = stats.ttest_ind(white_effects.dropna(), black_effects.dropna())
    
    print(f"\nT-test for differential effects:")
    print(f"  t-statistic: {t_stat:.3f}")
    print(f"  p-value: {p_value:.4f}")
    
    if p_value < 0.05:
        print(f"  ✓ AI affects White and Black differently (p < 0.05)")
    
    # Save individual-level data
    import os
    os.makedirs('results', exist_ok=True)
    effects_df.to_csv('results/parallel_worlds_individual.csv', index=False)
    print(f"\n✓ Individual-level data saved: results/parallel_worlds_individual.csv")
    
    # HETEROGENEITY ANALYSIS BY STATE
    print(f"\n5. HETEROGENEOUS EFFECTS BY STATE/COUNTY")
    print("-" * 70)
    
    # Get state from seekers
    control_by_county = {}
    treatment_by_county = {}
    
    for s in control['seekers']:
        if s.county not in control_by_county:
            control_by_county[s.county] = []
        control_by_county[s.county].append(s)
    
    for s in treatment['seekers']:
        if s.county not in treatment_by_county:
            treatment_by_county[s.county] = []
        treatment_by_county[s.county].append(s)
    
    county_effects = []
    
    print(f"\nTreatment effects by county:")
    print(f"  {'County':<35} | {'Control Gap':>12} | {'Treatment Gap':>14} | {'Effect':>8}")
    print(f"  {'-'*35}-+-{'-'*12}-+-{'-'*14}-+-{'-'*8}")
    
    for county in sorted(control_by_county.keys()):
        c_seekers = control_by_county[county]
        t_seekers = treatment_by_county[county]
        
        # Calculate gaps for this county
        c_white = [s for s in c_seekers if s.race == 'White']
        c_black = [s for s in c_seekers if s.race == 'Black']
        t_white = [s for s in t_seekers if s.race == 'White']
        t_black = [s for s in t_seekers if s.race == 'Black']
        
        if c_white and c_black and t_white and t_black:
            c_white_apps = sum(s.num_applications for s in c_white)
            c_white_approved = sum(s.num_approvals for s in c_white)
            c_white_rate = c_white_approved / c_white_apps if c_white_apps > 0 else 0
            
            c_black_apps = sum(s.num_applications for s in c_black)
            c_black_approved = sum(s.num_approvals for s in c_black)
            c_black_rate = c_black_approved / c_black_apps if c_black_apps > 0 else 0
            
            t_white_apps = sum(s.num_applications for s in t_white)
            t_white_approved = sum(s.num_approvals for s in t_white)
            t_white_rate = t_white_approved / t_white_apps if t_white_apps > 0 else 0
            
            t_black_apps = sum(s.num_applications for s in t_black)
            t_black_approved = sum(s.num_approvals for s in t_black)
            t_black_rate = t_black_approved / t_black_apps if t_black_apps > 0 else 0
            
            c_county_gap = c_white_rate - c_black_rate
            t_county_gap = t_white_rate - t_black_rate
            county_effect = t_county_gap - c_county_gap
            
            # Shorten county name for display
            county_short = county.split(',')[0]
            state = county.split(', ')[1]
            
            print(f"  {county_short+', '+state:<35} | {c_county_gap:>11.1%} | {t_county_gap:>13.1%} | {county_effect:>+7.1%}")
            
            county_effects.append({
                'county': county,
                'state': state,
                'control_gap': c_county_gap,
                'treatment_gap': t_county_gap,
                'treatment_effect': county_effect,
                'n_white': len(c_white),
                'n_black': len(c_black)
            })
    
    # Test for heterogeneity
    if len(county_effects) > 1:
        effects_only = [c['treatment_effect'] for c in county_effects]
        print(f"\n  Heterogeneity across counties:")
        print(f"    Min effect: {min(effects_only)*100:+.1f}pp")
        print(f"    Max effect: {max(effects_only)*100:+.1f}pp")
        print(f"    Range: {(max(effects_only) - min(effects_only))*100:.1f}pp")
        print(f"    SD: {np.std(effects_only)*100:.1f}pp")
        
        if np.std(effects_only) > 0.05:
            print(f"    → HIGH heterogeneity (effects vary by location!)")
        else:
            print(f"    → Low heterogeneity (consistent effects)")
    
    # Save county-level effects
    county_effects_df = pd.DataFrame(county_effects)
    county_effects_df.to_csv('results/parallel_worlds_by_county.csv', index=False)
    print(f"\n✓ County-level effects saved: results/parallel_worlds_by_county.csv")
    
    return {
        'treatment_effect': treatment_effect,
        't_stat': t_stat,
        'p_value': p_value,
        'control_gap': c_gap,
        'treatment_gap': t_gap,
        'individual_effects': effects_df,
        'county_effects': county_effects
    }


def main():
    """Run parallel worlds experiment."""
    print("\n" + "="*70)
    print("PARALLEL WORLDS EXPERIMENT")
    print("="*70)
    print("\nResearch Question:")
    print("  What is the causal effect of AI sorting on racial disparities?")
    print("\nDesign:")
    print("  - ONE population of seekers")
    print("  - TWO parallel simulations (Control vs Treatment)")
    print("  - SAME people, SAME applications")
    print("  - Only difference: Sorting algorithm")
    print("\nAdvantages:")
    print("  ✓ Perfect counterfactual comparison")
    print("  ✓ No confounding from population differences")
    print("  ✓ Individual-level treatment effects")
    print("  ✓ Maximum statistical power")
    
    # Select diverse counties nationwide
    counties = [
        'Jefferson County, Alabama',      # South, diverse
        'Kings County, New York',         # Urban, very diverse
        'Cook County, Illinois',          # Urban, diverse
        'Maricopa County, Arizona',       # Southwest, growing
        'Orange County, California',      # West, diverse
        'Harris County, Texas',           # South, diverse
        'King County, Washington',        # Northwest, tech hub
        'Fulton County, Georgia'          # South, majority Black
    ]
    
    print(f"\nSelected {len(counties)} diverse counties:")
    for county in counties:
        print(f"  - {county}")
    
    # Run experiment
    results = run_parallel_worlds_experiment(
        cps_file='src/data/cps_asec_2022_processed_full.csv',
        acs_file='src/data/us_census_acs_2022_county_data.csv',
        n_seekers=1600,  # 200 per county
        n_months=12,
        counties=counties,
        random_seed=42
    )
    
    # Save aggregate results
    comparison = results['comparison']
    
    summary_results = {
        'treatment_effect': comparison['treatment_effect'],
        'control_gap': comparison['control_gap'],
        'treatment_gap': comparison['treatment_gap'],
        't_statistic': comparison['t_stat'],
        'p_value': comparison['p_value'],
        'control_total_apps': results['control']['summary']['total_applications'],
        'treatment_total_apps': results['treatment']['summary']['total_applications'],
        'control_approval_rate': results['control']['summary']['approval_rate'],
        'treatment_approval_rate': results['treatment']['summary']['approval_rate']
    }
    
    summary_df = pd.DataFrame([summary_results])
    summary_df.to_csv('results/parallel_worlds_summary.csv', index=False)
    
    print("\n" + "="*70)
    print("EXPERIMENT COMPLETE")
    print("="*70)
    
    print(f"\nFINDING:")
    if comparison['p_value'] < 0.05:
        if comparison['treatment_effect'] > 0:
            print(f"  ✓ AI sorting INCREASES racial disparity")
            print(f"    Effect: {comparison['treatment_effect']*100:+.1f}pp")
            print(f"    Statistically significant (p = {comparison['p_value']:.4f})")
        else:
            print(f"  ✓ AI sorting DECREASES racial disparity")
            print(f"    Effect: {comparison['treatment_effect']*100:+.1f}pp")
            print(f"    Statistically significant (p = {comparison['p_value']:.4f})")
    else:
        print(f"  ⚠ No statistically significant effect")
        print(f"    Effect: {comparison['treatment_effect']*100:+.1f}pp")
        print(f"    p-value: {comparison['p_value']:.4f}")
    
    print(f"\n✓ Results saved:")
    print(f"  - results/parallel_worlds_summary.csv (aggregate)")
    print(f"  - results/parallel_worlds_individual.csv (person-level)")


if __name__ == "__main__":
    main()