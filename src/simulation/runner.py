"""
Simulation runner - orchestrates the monthly simulation loop.

Main functions:
- create_population(): Generate initial seekers
- run_month(): Process one month of applications
- run_simulation(): Run complete simulation over time
"""

import numpy as np
import sys
import os

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.dirname(os.path.dirname(current_dir))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from src.core.seeker import Seeker
from src.core.evaluator import Evaluator
from src.core.reviewer import Reviewer


def create_population(n_seekers, counties=None, random_seed=42):
    """
    Create a population of seekers with diverse characteristics.
    
    For now, creates a simple population:
    - Mix of races
    - Income range: $10,000 to $80,000
    - 40% have children
    - 15% have disability
    - Distributed across counties
    
    Args:
        n_seekers: Number of seekers to create
        counties: List of county names (default: ['County_A', 'County_B', 'County_C'])
        random_seed: Random seed for reproducibility
        
    Returns:
        list: List of Seeker objects
    """
    rng = np.random.RandomState(random_seed)
    seekers = []
    
    # Default counties if not provided
    if counties is None:
        counties = ['County_A', 'County_B', 'County_C']
    
    races = ['White', 'Black', 'Hispanic', 'Asian']
    
    for i in range(n_seekers):
        # Assign race (round-robin for now)
        race = races[i % len(races)]
        
        # Assign county (round-robin)
        county = counties[i % len(counties)]
        
        # Generate income (lognormal distribution)
        # Mean around $40k, ranging from ~$10k to ~$80k
        income = rng.lognormal(mean=np.log(40000), sigma=0.6)
        income = max(10000, min(80000, income))  # Clip to reasonable range
        
        # Assign demographics
        has_children = rng.random() < 0.40  # 40% have children
        has_disability = rng.random() < 0.15  # 15% have disability
        
        # Create seeker (fraud/error propensity generated automatically)
        seeker = Seeker(
            seeker_id=i,
            race=race,
            income=income,
            county=county,
            has_children=has_children,
            has_disability=has_disability,
            random_state=np.random.RandomState(random_seed + i)
        )
        
        seekers.append(seeker)
    
    return seekers


def create_evaluators(counties, programs=['SNAP', 'TANF', 'SSI'], random_seed=42):
    """
    Create evaluators for each county-program combination.
    
    Each county gets one evaluator per program.
    
    Args:
        counties: List of county names
        programs: List of programs (default: SNAP, TANF, SSI)
        random_seed: Random seed for reproducibility
        
    Returns:
        dict: {(county, program): Evaluator}
    """
    evaluators = {}
    evaluator_id = 0
    
    for county in counties:
        for program in programs:
            evaluator = Evaluator(
                evaluator_id=evaluator_id,
                county=county,
                program=program,
                strictness=0.5,  # Default strictness (can vary by county later)
                random_state=np.random.RandomState(random_seed + evaluator_id)
            )
            evaluators[(county, program)] = evaluator
            evaluator_id += 1
    
    return evaluators


def create_reviewers(counties, programs=['SNAP', 'TANF', 'SSI'], random_seed=42):
    """
    Create one reviewer per county-program combination (matches evaluators).
    
    Each evaluator has their own dedicated reviewer.
    
    Args:
        counties: List of county names
        programs: List of programs (default: SNAP, TANF, SSI)
        random_seed: Random seed for reproducibility
        
    Returns:
        dict: {(county, program): Reviewer}
    """
    reviewers = {}
    reviewer_id = 0
    
    for county in counties:
        for program in programs:
            reviewer = Reviewer(
                reviewer_id=reviewer_id,
                capacity=50,  # Can handle 50 cases per month
                accuracy=0.85,  # 85% fraud detection
                random_state=np.random.RandomState(random_seed + reviewer_id + 1000)
            )
            reviewers[(county, program)] = reviewer
            reviewer_id += 1
    
    return reviewers


def run_month(seekers, evaluators, reviewers, month):
    """
    Run one month of the simulation.
    
    Steps:
    1. Seekers create applications
    2. Route to correct county-program evaluator
    3. Reviewer handles escalations (same county-program)
    4. Update seeker histories
    5. Return monthly statistics
    
    Args:
        seekers: List of Seeker objects
        evaluators: Dict of {(county, program): Evaluator}
        reviewers: Dict of {(county, program): Reviewer}
        month: Current month number
        
    Returns:
        dict: Monthly statistics
    """
    # Reset reviewer capacity for new month
    for reviewer in reviewers.values():
        reviewer.reset_monthly_capacity(month)
    
    # Statistics tracking
    stats = {
        'month': month,
        'applications_submitted': 0,
        'applications_approved': 0,
        'applications_denied': 0,
        'applications_escalated': 0,
        'fraud_attempted': 0,
        'errors_made': 0,
        'honest_applications': 0,
    }
    
    # Application ID counter
    app_id = month * 10000  # Unique IDs per month
    
    # Step 1: Collect applications from all seekers
    applications = []
    for seeker in seekers:
        # Try each program (seeker decides whether to apply)
        for program in ['SNAP', 'TANF', 'SSI']:
            app = seeker.create_application(program, month, app_id)
            if app:
                applications.append(app)
                app_id += 1
                
                # Track application types
                if app.is_fraud:
                    stats['fraud_attempted'] += 1
                elif app.is_error:
                    stats['errors_made'] += 1
                else:
                    stats['honest_applications'] += 1
    
    stats['applications_submitted'] = len(applications)
    
    # Step 2: Process applications with correct evaluator for each county-program
    for app in applications:
        # Get the seeker
        seeker = next(s for s in seekers if s.id == app.seeker_id)
        
        # Get the correct evaluator and reviewer for this county-program
        key = (seeker.county, app.program)
        
        if key not in evaluators:
            # Shouldn't happen, but handle gracefully
            print(f"Warning: No evaluator for {key}")
            continue
        
        evaluator = evaluators[key]
        reviewer = reviewers[key]  # Same key for reviewer
        
        # Process application
        decision = evaluator.process_application(app, reviewer=reviewer)
        
        if decision == 'APPROVED':
            stats['applications_approved'] += 1
            seeker.num_approvals += 1
            # Enroll seeker in program
            seeker.enroll_in_program(app.program, month)
            
        elif decision == 'DENIED':
            stats['applications_denied'] += 1
            seeker.num_denials += 1
            
        elif decision == 'ESCALATED':
            stats['applications_escalated'] += 1
            
            # Reviewer processes escalated case
            if reviewer.can_review():
                final_decision = reviewer.review_application(app)
                
                if final_decision == 'APPROVED':
                    stats['applications_approved'] += 1
                    seeker.num_approvals += 1
                    # Enroll seeker in program
                    seeker.enroll_in_program(app.program, month)
                elif final_decision == 'DENIED':
                    stats['applications_denied'] += 1
                    seeker.num_denials += 1
                    
                # Track if investigated
                if app.investigated:
                    seeker.num_investigations += 1
    
    return stats


def run_simulation(n_seekers, n_months, counties=None, random_seed=42):
    """
    Run complete simulation.
    
    Args:
        n_seekers: Number of seekers to simulate
        n_months: Number of months to simulate
        counties: List of county names (default: 3 counties)
        random_seed: Random seed for reproducibility
        
    Returns:
        dict: Simulation results containing:
            - seekers: List of Seeker objects (final state)
            - monthly_stats: List of monthly statistics
            - summary: Overall summary statistics
            - evaluators: Dict of evaluators by (county, program)
            - reviewers: Dict of reviewers by county
    """
    # Default counties
    if counties is None:
        counties = ['County_A', 'County_B', 'County_C']
    
    # Step 1: Create population
    seekers = create_population(n_seekers, counties=counties, random_seed=random_seed)
    
    # Step 2: Create evaluators for each county-program combination
    evaluators = create_evaluators(counties, random_seed=random_seed)
    
    # Step 3: Create reviewers for each county
    reviewers = create_reviewers(counties, random_seed=random_seed)
    
    # Step 4: Run simulation month by month
    monthly_stats = []
    
    for month in range(n_months):
        stats = run_month(seekers, evaluators, reviewers, month)
        monthly_stats.append(stats)
    
    # Step 5: Calculate summary statistics
    summary = {
        'total_seekers': n_seekers,
        'total_months': n_months,
        'total_counties': len(counties),
        'total_applications': sum(s.num_applications for s in seekers),
        'total_approvals': sum(s.num_approvals for s in seekers),
        'total_denials': sum(s.num_denials for s in seekers),
        'total_investigations': sum(s.num_investigations for s in seekers),
        'approval_rate': 0.0,
        'investigation_rate': 0.0,
    }
    
    if summary['total_applications'] > 0:
        summary['approval_rate'] = summary['total_approvals'] / summary['total_applications']
        summary['investigation_rate'] = summary['total_investigations'] / summary['total_applications']
    
    # Step 6: Return results
    return {
        'seekers': seekers,
        'monthly_stats': monthly_stats,
        'summary': summary,
        'evaluators': evaluators,
        'reviewers': reviewers,
        'counties': counties
    }


if __name__ == "__main__":
    # Quick test
    print("Running small simulation: 20 seekers, 6 months\n")
    
    results = run_simulation(n_seekers=20, n_months=6, random_seed=42)
    
    print("Summary:")
    print(f"  Total applications: {results['summary']['total_applications']}")
    print(f"  Approved: {results['summary']['total_approvals']}")
    print(f"  Denied: {results['summary']['total_denials']}")
    print(f"  Approval rate: {results['summary']['approval_rate']:.1%}")
    
    print("\nMonthly breakdown:")
    for stats in results['monthly_stats']:
        print(f"  Month {stats['month']}: {stats['applications_submitted']} apps, "
              f"{stats['applications_approved']} approved, "
              f"{stats['fraud_attempted']} fraud, "
              f"{stats['errors_made']} errors")


def run_simulation_with_real_data(cps_file, acs_file, n_seekers, n_months, counties, random_seed=42):
    """
    Run simulation using real CPS/ACS data for population characteristics.
    
    This creates a realistic population based on actual data distributions.
    
    Args:
        cps_file: Path to CPS data file
        acs_file: Path to ACS county data file
        n_seekers: Number of seekers to create
        n_months: Number of months to simulate
        counties: List of county names (must match ACS county_name exactly)
        random_seed: Random seed for reproducibility
        
    Returns:
        dict: Simulation results (same structure as run_simulation)
    """
    from data.data_loader import create_realistic_population
    
    # Step 1: Create realistic population from data
    print("Creating realistic population from CPS/ACS data...")
    seekers = create_realistic_population(
        cps_file=cps_file,
        acs_file=acs_file,
        n_seekers=n_seekers,
        counties=counties,
        random_seed=random_seed
    )
    
    # Step 2: Create evaluators and reviewers
    evaluators = create_evaluators(counties, random_seed=random_seed)
    reviewers = create_reviewers(counties, random_seed=random_seed)
    
    # Step 3: Run simulation month by month
    print(f"\nRunning simulation: {n_seekers} seekers, {n_months} months, {len(counties)} counties")
    monthly_stats = []
    
    for month in range(n_months):
        stats = run_month(seekers, evaluators, reviewers, month)
        monthly_stats.append(stats)
        
        if (month + 1) % 12 == 0:
            print(f"  Completed month {month + 1}/{n_months}")
    
    # Step 4: Calculate summary statistics
    summary = {
        'total_seekers': n_seekers,
        'total_months': n_months,
        'total_counties': len(counties),
        'total_applications': sum(s.num_applications for s in seekers),
        'total_approvals': sum(s.num_approvals for s in seekers),
        'total_denials': sum(s.num_denials for s in seekers),
        'total_investigations': sum(s.num_investigations for s in seekers),
        'approval_rate': 0.0,
        'investigation_rate': 0.0,
    }
    
    if summary['total_applications'] > 0:
        summary['approval_rate'] = summary['total_approvals'] / summary['total_applications']
        summary['investigation_rate'] = summary['total_investigations'] / summary['total_applications']
    
    # Step 5: Return results
    return {
        'seekers': seekers,
        'monthly_stats': monthly_stats,
        'summary': summary,
        'evaluators': evaluators,
        'reviewers': reviewers,
        'counties': counties,
        'data_source': 'CPS/ACS'
    }