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


def calculate_evaluator_capacity(county_population, base_units_per_staff=25.0, staff_per_capita=1/50000):
    """
    Calculate evaluator capacity based on county population.
    
    Larger counties need more staff to handle more applications.
    
    CALIBRATED PARAMETERS:
    - Staff ratio: 1 per 50,000 people
    - Units per staff: 25.0 (calibrated to keep overflow <5%)
    
    Args:
        county_population: Total county population (from ACS)
        base_units_per_staff: Complexity units one staff can handle per month (default: 25)
        staff_per_capita: Staff ratio (default: 1 per 50,000 people)
        
    Returns:
        float: Monthly capacity in complexity units
    
    Examples:
        Small county (50,000 pop):  1 staff → 25 units/month
        Medium county (500,000 pop): 10 staff → 250 units/month
        Large county (2.5M pop): 50 staff → 1,250 units/month
    """
    # Calculate number of staff
    num_staff = county_population * staff_per_capita
    
    # Minimum 0.5 staff (part-time) for very small counties
    num_staff = max(0.5, num_staff)
    
    # Total capacity
    capacity = num_staff * base_units_per_staff
    
    return capacity


def calculate_reviewer_capacity(county_population, base_units_per_staff=15.0, staff_per_capita=1/50000):
    """
    Calculate reviewer capacity based on county population.
    
    Reviewers are specialists - same staff ratio as evaluators but handle fewer units.
    
    CALIBRATED PARAMETERS:
    - Staff ratio: 1 per 50,000 (same as evaluators)
    - Units per staff: 15.0 (fewer than evaluators' 20.0 - more specialized work)
    
    Args:
        county_population: Total county population (from ACS)
        base_units_per_staff: Complexity units one reviewer handles per month (default: 15)
        staff_per_capita: Staff ratio (default: 1 per 50,000 people)
        
    Returns:
        float: Monthly capacity in complexity units
    
    Examples:
        Small county (50,000 pop): 1 staff → 15 units/month
        Medium county (500,000 pop): 10 staff → 150 units/month
        Large county (2.5M pop): 50 staff → 750 units/month
    """
    # Calculate number of staff
    num_staff = county_population * staff_per_capita
    
    # Minimum 0.5 staff for very small counties
    num_staff = max(0.5, num_staff)
    
    # Total capacity
    capacity = num_staff * base_units_per_staff
    
    return capacity


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


def create_evaluators(counties, acs_data=None, random_seed=42):
    """
    Create evaluators for each county-program combination.
    
    Each county gets one evaluator per program.
    Capacity is scaled by county population (larger counties have more staff).
    
    Args:
        counties: List of county names
        acs_data: ACS DataFrame with county populations (optional)
        programs: List of programs (default: SNAP, TANF, SSI)
        random_seed: Random seed for reproducibility
        
    Returns:
        dict: {(county, program): Evaluator}
    """
    programs = ['SNAP', 'TANF', 'SSI']
    evaluators = {}
    evaluator_id = 0
    
    for county in counties:
        # Get county population if ACS data provided
        if acs_data is not None:
            county_data = acs_data[acs_data['county_name'] == county]
            if len(county_data) > 0:
                population = county_data.iloc[0]['total_county_population']
                capacity = calculate_evaluator_capacity(population)
            else:
                # County not found, use default
                capacity = 20.0
        else:
            # No ACS data, use default
            capacity = 20.0
        
        for program in programs:
            evaluator = Evaluator(
                evaluator_id=evaluator_id,
                county=county,
                program=program,
                strictness=0.5,  # Default strictness (can vary by county later)
                random_state=np.random.RandomState(random_seed + evaluator_id)
            )
            # Store capacity for later use (will add to Evaluator class in Step 3)
            evaluator.monthly_capacity = capacity
            
            evaluators[(county, program)] = evaluator
            evaluator_id += 1
    
    return evaluators


def create_reviewers(counties, acs_data=None, random_seed=42):
    """
    Create one reviewer per county-program combination (matches evaluators).
    
    Each evaluator has their own dedicated reviewer.
    Capacity is scaled by county population.
    
    Args:
        counties: List of county names
        acs_data: ACS DataFrame with county populations (optional)
        programs: List of programs (default: SNAP, TANF, SSI)
        random_seed: Random seed for reproducibility
        
    Returns:
        dict: {(county, program): Reviewer}
    """
    programs = ['SNAP', 'TANF', 'SSI']
    reviewers = {}
    reviewer_id = 0
    
    for county in counties:
        # Get county population if ACS data provided
        if acs_data is not None:
            county_data = acs_data[acs_data['county_name'] == county]
            if len(county_data) > 0:
                population = county_data.iloc[0]['total_county_population']
                capacity = calculate_reviewer_capacity(population)
            else:
                # County not found, use default
                capacity = 10.0
        else:
            # No ACS data, use default
            capacity = 10.0
        
        for program in programs:
            reviewer = Reviewer(
                reviewer_id=reviewer_id,
                capacity=50,  # Will be replaced with complexity units in Step 4
                accuracy=0.85,  # 85% fraud detection
                random_state=np.random.RandomState(random_seed + reviewer_id + 1000)
            )
            # Store capacity for later use (will update Reviewer class in Step 4)
            reviewer.monthly_capacity = capacity
            
            reviewers[(county, program)] = reviewer
            reviewer_id += 1
    
    return reviewers


def run_month(seekers, evaluators, reviewers, month, ai_sorter=None):
    """
    Run one month of the simulation.
    
    Steps:
    1. Reset staff capacity for new month
    2. Seekers create applications
    3. OPTIONAL: AI tool sorts applications
    4. Route to correct county-program evaluator
    5. Reviewer handles escalations (same county-program)
    6. Handle capacity-exceeded cases
    7. Update seeker histories
    8. Return monthly statistics
    
    Args:
        seekers: List of Seeker objects
        evaluators: Dict of {(county, program): Evaluator}
        reviewers: Dict of {(county, program): Reviewer}
        month: Current month number
        ai_sorter: Optional AI_ApplicationSorter for ordering applications
        
    Returns:
        dict: Monthly statistics
    """
    # Reset staff capacity for new month
    for evaluator in evaluators.values():
        evaluator.reset_monthly_capacity(month)
    
    for reviewer in reviewers.values():
        reviewer.reset_monthly_capacity(month)
    
    # Statistics tracking
    stats = {
        'month': month,
        'applications_submitted': 0,
        'applications_approved': 0,
        'applications_denied': 0,
        'applications_escalated': 0,
        'applications_capacity_exceeded': 0,  # NEW: Overflow tracking
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
    
    # NEW: AI sorting (if enabled)
    if ai_sorter:
        # Create seekers dict for need-based sorting
        seekers_dict = {s.id: s for s in seekers}
        applications = ai_sorter.sort_applications(applications, seekers_dict)
    
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
        
        # Process application (pass seeker for history tracking)
        decision = evaluator.process_application(app, reviewer=reviewer, seeker=seeker)
        
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
            if reviewer.can_review(app):  # Pass application for complexity check
                final_decision = reviewer.review_application(app, seeker=seeker)  # Pass seeker for points
                
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
        
        elif decision == 'CAPACITY_EXCEEDED':
            # NEW: Evaluator at capacity - queue for next month
            stats['applications_capacity_exceeded'] += 1
            # For now, just count it (could implement queue in future)
            # Application remains pending
    
    return stats


def run_simulation(n_seekers, n_months, counties=None, ai_sorter=None, random_seed=42):
    """
    Run complete simulation.
    
    Args:
        n_seekers: Number of seekers to simulate
        n_months: Number of months to simulate
        counties: List of county names (default: 3 counties)
        ai_sorter: Optional AI_ApplicationSorter for ordering applications
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
        stats = run_month(seekers, evaluators, reviewers, month, ai_sorter=ai_sorter)
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


def run_simulation_with_real_data(cps_file, acs_file, n_seekers, n_months, counties, ai_sorter=None, random_seed=42):
    """
    Run simulation using real CPS/ACS data for population characteristics.
    
    This creates a realistic population based on actual data distributions.
    
    Args:
        cps_file: Path to CPS data file
        acs_file: Path to ACS county data file
        n_seekers: Number of seekers to create
        n_months: Number of months to simulate
        counties: List of county names (must match ACS county_name exactly)
        ai_sorter: Optional AI_ApplicationSorter for ordering applications
        random_seed: Random seed for reproducibility
        
    Returns:
        dict: Simulation results (same structure as run_simulation)
    """
    from data.data_loader import create_realistic_population, load_acs_county_data
    
    # Step 1: Create realistic population from data
    print("Creating realistic population from CPS/ACS data...")
    seekers = create_realistic_population(
        cps_file=cps_file,
        acs_file=acs_file,
        n_seekers=n_seekers,
        counties=counties,
        random_seed=random_seed
    )
    
    # Step 2: Load ACS for population data
    acs_data = load_acs_county_data(acs_file)
    
    # Step 3: Create evaluators and reviewers with population-based capacity
    print(f"\nCreating staff with population-based capacity...")
    evaluators = create_evaluators(counties, acs_data=acs_data, random_seed=random_seed)
    reviewers = create_reviewers(counties, acs_data=acs_data, random_seed=random_seed)
    
    # Print capacity info
    print(f"\nStaff capacity by county:")
    for county in counties:
        county_data = acs_data[acs_data['county_name'] == county]
        if len(county_data) > 0:
            pop = county_data.iloc[0]['total_county_population']
            eval_cap = evaluators[(county, 'SNAP')].monthly_capacity
            rev_cap = reviewers[(county, 'SNAP')].monthly_capacity
            print(f"  {county}: Pop {pop:,}")
            print(f"    Evaluator capacity: {eval_cap:.1f} units/month")
            print(f"    Reviewer capacity: {rev_cap:.1f} units/month")
    
    # Step 4: Run simulation month by month
    if ai_sorter:
        print(f"\nRunning simulation with AI: {ai_sorter.name}")
    print(f"Running simulation: {n_seekers} seekers, {n_months} months, {len(counties)} counties")
    monthly_stats = []
    
    for month in range(n_months):
        stats = run_month(seekers, evaluators, reviewers, month, ai_sorter=ai_sorter)
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