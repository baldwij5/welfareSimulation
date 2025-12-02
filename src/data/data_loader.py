"""
Data loader for CPS and ACS datasets - WITH PROPER WEIGHTING

Strategy:
- CPS provides INDIVIDUAL characteristics (income, race, children, disability)
- ACS provides COUNTY targets (% Black, poverty rate, etc.)
- We WEIGHT CPS sampling to match ACS county demographics

This ensures each county's population matches its real demographic profile!
"""

import pandas as pd
import numpy as np


def load_cps_data(filepath='src/data/cps_asec_2022_processed_full.csv'):
    """
    Load CPS ASEC data (152,733 individuals).
    
    Returns:
        DataFrame: CPS data with individual-level characteristics
    """
    print(f"Loading CPS data from {filepath}...")
    df = pd.read_csv(filepath)
    print(f"  Loaded {len(df):,} observations")
    return df


def filter_to_eligible(cps_data):
    """
    Filter CPS to only people eligible for at least one program.
    
    Eligibility criteria (simplified):
    - SNAP: Income < $30,000/year (roughly $2,500/month)
    - TANF: Income < $12,000/year (roughly $1,000/month) + has children
    - SSI: Income < $23,000/year (roughly $1,913/month) + has disability
    
    We use the HIGHEST threshold ($30k for SNAP) to be inclusive.
    
    Args:
        cps_data: CPS DataFrame
        
    Returns:
        DataFrame: Only potentially eligible people
    """
    # Filter to working-age first
    working_age = cps_data[
        (cps_data['AGE'] >= 18) & 
        (cps_data['AGE'] <= 64)
    ].copy()
    
    print(f"Filtered to {len(working_age):,} working-age adults (18-64)")
    
    # Filter to income-eligible (use SNAP threshold as it's highest)
    # SNAP: $30,000/year = $2,500/month
    eligible = working_age[working_age['INCTOT'] < 30000].copy()
    
    print(f"Filtered to {len(eligible):,} income-eligible (<$30k/year)")
    print(f"  This is {len(eligible)/len(working_age)*100:.1f}% of working-age adults")
    
    return eligible


def load_acs_county_data(filepath='src/data/us_census_acs_2022_county_data.csv'):
    """
    Load ACS county-level data (3,203 counties).
    
    Returns:
        DataFrame: ACS data with county-level demographics
    """
    print(f"Loading ACS county data from {filepath}...")
    df = pd.read_csv(filepath)
    print(f"  Loaded {len(df):,} counties")
    return df


def get_county_characteristics(acs_data, county_name):
    """
    Get demographic targets for a specific county from ACS.
    
    Args:
        acs_data: ACS DataFrame
        county_name: County name (e.g., 'Kings County, New York')
        
    Returns:
        dict: County demographic targets for weighting
    """
    county = acs_data[acs_data['county_name'] == county_name]
    
    if len(county) == 0:
        print(f"Warning: County '{county_name}' not found in ACS data")
        return None
    
    county = county.iloc[0]
    
    return {
        'county_name': county['county_name'],
        'population': county['total_county_population'],
        'median_income': county['median_household_income'],
        'poverty_rate': county['poverty_rate'],
        'white_pct': county['white_pct'],
        'black_pct': county['black_pct'],
        'hispanic_pct': county['hispanic_pct'],
        'asian_pct': county['asian_pct'],
        'snap_rate': county['snap_participation_rate'],
        'ssi_rate': county['ssi_rate'],
        'disability_rate': county['disability_rate'],
    }


def calculate_sampling_weights(cps_data, county_chars):
    """
    Calculate sampling weights to match county demographics.
    
    Uses stronger weighting to ensure good demographic match.
    
    Args:
        cps_data: CPS DataFrame (filtered to working-age)
        county_chars: Dict from get_county_characteristics()
        
    Returns:
        np.array: Sampling weights (one per CPS row)
    """
    weights = np.ones(len(cps_data))
    
    # Reset index to avoid indexing issues
    cps_data = cps_data.reset_index(drop=True)
    
    # For each person in CPS
    for idx in range(len(cps_data)):
        row = cps_data.iloc[idx]
        
        # RACE WEIGHT (most important - use percentage directly)
        # If county is 46.9% Black, Black people get weight of 46.9
        # If county is 45.5% White, White people get weight of 45.5
        race_weight = 0.01  # Small base weight for non-matching races
        
        if row['white'] == 1:
            race_weight = max(0.01, county_chars['white_pct'])
        elif row['black'] == 1:
            race_weight = max(0.01, county_chars['black_pct'])
        elif row['hispanic'] == 1:
            race_weight = max(0.01, county_chars['hispanic_pct'])
        elif row['asian'] == 1:
            race_weight = max(0.01, county_chars['asian_pct'])
        
        # POVERTY WEIGHT (secondary)
        poverty_weight = 1.0
        if row.get('in_poverty', 0) == 1:
            # Person is poor - boost if high poverty county
            poverty_weight = 1.0 + (county_chars['poverty_rate'] / 20.0)
        
        # DISABILITY WEIGHT (tertiary)
        disability_weight = 1.0
        if row.get('has_disability', 0) == 1:
            disability_weight = 1.0 + (county_chars['disability_rate'] / 20.0)
        
        # COMBINE: Race weight is dominant
        weights[idx] = race_weight * poverty_weight * disability_weight
    
    # Normalize to sum to 1
    weights = weights / weights.sum()
    
    return weights


def sample_for_county(cps_data, n_seekers, county_chars, random_seed=42):
    """
    Sample seekers from CPS for a specific county using STRATIFIED sampling.
    
    Strategy:
    1. Determine how many of each race we need (from ACS percentages)
    2. Sample that many from each race group in CPS
    3. Results in perfect demographic match!
    
    Args:
        cps_data: CPS DataFrame
        n_seekers: Number of seekers to sample
        county_chars: County characteristics from ACS
        random_seed: Random seed
        
    Returns:
        list: Sampled CPS rows (as dicts)
    """
    rng = np.random.RandomState(random_seed)
    
    # Reset index
    cps_data = cps_data.reset_index(drop=True)
    
    # Calculate target counts for each race
    target_counts = {
        'white': int(n_seekers * county_chars['white_pct'] / 100),
        'black': int(n_seekers * county_chars['black_pct'] / 100),
        'hispanic': int(n_seekers * county_chars['hispanic_pct'] / 100),
        'asian': int(n_seekers * county_chars['asian_pct'] / 100),
    }
    
    # Adjust for rounding (make sure total = n_seekers)
    total = sum(target_counts.values())
    if total < n_seekers:
        # Add remainder to largest group
        largest = max(target_counts, key=target_counts.get)
        target_counts[largest] += (n_seekers - total)
    
    print(f"    Target counts:")
    print(f"      White: {target_counts['white']} ({target_counts['white']/n_seekers*100:.1f}%)")
    print(f"      Black: {target_counts['black']} ({target_counts['black']/n_seekers*100:.1f}%)")
    print(f"      Hispanic: {target_counts['hispanic']} ({target_counts['hispanic']/n_seekers*100:.1f}%)")
    print(f"      Asian: {target_counts['asian']} ({target_counts['asian']/n_seekers*100:.1f}%)")
    
    # Sample from each race group
    sampled_rows = []
    
    for race, count in target_counts.items():
        if count == 0:
            continue
        
        # Get CPS people of this race
        if race == 'white':
            race_subset = cps_data[cps_data['white'] == 1]
        elif race == 'black':
            race_subset = cps_data[cps_data['black'] == 1]
        elif race == 'hispanic':
            race_subset = cps_data[cps_data['hispanic'] == 1]
        elif race == 'asian':
            race_subset = cps_data[cps_data['asian'] == 1]
        
        if len(race_subset) == 0:
            print(f"      Warning: No {race} individuals in CPS!")
            continue
        
        # Within this race, weight by poverty and disability
        race_weights = np.ones(len(race_subset))
        
        for idx in range(len(race_subset)):
            row = race_subset.iloc[idx]
            weight = 1.0
            
            # Weight by poverty
            if row.get('in_poverty', 0) == 1:
                weight *= (1.0 + county_chars['poverty_rate'] / 20.0)
            
            # Weight by disability
            if row.get('has_disability', 0) == 1:
                weight *= (1.0 + county_chars['disability_rate'] / 20.0)
            
            race_weights[idx] = weight
        
        # Normalize
        race_weights = race_weights / race_weights.sum()
        
        # Sample from this race group
        sampled_indices = rng.choice(
            len(race_subset),
            size=count,
            replace=True,
            p=race_weights
        )
        
        sampled_race = race_subset.iloc[sampled_indices]
        sampled_rows.extend(sampled_race.to_dict('records'))
    
    # Verify
    sampled_white = sum(1 for r in sampled_rows if r['white'] == 1)
    sampled_black = sum(1 for r in sampled_rows if r['black'] == 1)
    
    print(f"    Actual sampled:")
    print(f"      White: {sampled_white} ({sampled_white/len(sampled_rows)*100:.1f}%)")
    print(f"      Black: {sampled_black} ({sampled_black/len(sampled_rows)*100:.1f}%)")
    
    return sampled_rows


def cps_row_to_seeker(row, seeker_id, county='DEFAULT', random_state=None):
    """
    Convert a CPS row to a Seeker object.
    
    Extracts REAL characteristics from CPS data, including current program enrollment!
    Now stores ALL CPS variables for later analysis!
    
    Args:
        row: Dict from CPS data (one person) - contains ALL CPS variables
        seeker_id: Unique ID
        county: County to assign
        random_state: Random state for fraud/error propensity
        
    Returns:
        Seeker object (with complete CPS data stored)
    """
    from core.seeker import Seeker
    
    # Extract key characteristics
    income = row['INCTOT']
    
    # Extract race
    if row['white'] == 1:
        race = 'White'
    elif row['black'] == 1:
        race = 'Black'
    elif row['hispanic'] == 1:
        race = 'Hispanic'
    elif row['asian'] == 1:
        race = 'Asian'
    else:
        race = 'Other'
    
    # Extract demographics
    has_children = row['has_children'] == 1 or row['num_children'] > 0
    has_disability = row['has_disability'] == 1
    
    # Create Seeker with COMPLETE CPS data
    seeker = Seeker(
        seeker_id=seeker_id,
        race=race,
        income=max(0, income),
        county=county,
        has_children=has_children,
        has_disability=has_disability,
        cps_data=row,  # ← Pass entire CPS row!
        random_state=random_state
    )
    
    # INITIALIZE ENROLLMENT based on CPS data!
    if row.get('received_snap', 0) == 1:
        seeker.enroll_in_program('SNAP', month=0)
    
    if row.get('received_welfare', 0) == 1:
        seeker.enroll_in_program('TANF', month=0)
    
    if row.get('received_ssi', 0) == 1:
        seeker.enroll_in_program('SSI', month=0)
    
    return seeker


def create_realistic_population(cps_file, acs_file, n_seekers, counties, random_seed=42):
    """
    Create realistic population using CPS individuals weighted by ACS county demographics.
    
    THIS IS THE MAIN FUNCTION!
    
    Process:
    1. Load CPS (152,733 real people)
    2. Load ACS (3,203 counties)
    3. For each county:
       a. Get county demographics from ACS (% Black, poverty rate, etc.)
       b. Weight CPS individuals to match those demographics
       c. Sample from CPS using weights
       d. Create Seekers with those real characteristics
    
    Result: Population where each county matches its real demographic profile!
    
    Args:
        cps_file: Path to CPS data
        acs_file: Path to ACS county data
        n_seekers: Total seekers to create
        counties: List of county names (must match ACS exactly)
        random_seed: Random seed
        
    Returns:
        list: Seeker objects with realistic characteristics
    """
    rng = np.random.RandomState(random_seed)
    
    # Load data
    cps_data = load_cps_data(cps_file)
    acs_data = load_acs_county_data(acs_file)
    
    # Filter CPS to ELIGIBLE people only (income < $30k)
    cps_eligible = filter_to_eligible(cps_data)
    
    # Distribute seekers across counties
    seekers_per_county = n_seekers // len(counties)
    remainder = n_seekers % len(counties)
    
    all_seekers = []
    seeker_id = 0
    
    # For each county, sample with ACS-based weights
    for county_idx, county_name in enumerate(counties):
        # Get county demographics from ACS
        county_chars = get_county_characteristics(acs_data, county_name)
        
        if county_chars is None:
            print(f"Skipping {county_name}")
            continue
        
        # Number for this county
        n_county = seekers_per_county + (1 if county_idx < remainder else 0)
        
        print(f"\n{'='*70}")
        print(f"County: {county_name}")
        print(f"{'='*70}")
        print(f"  Creating {n_county} seekers")
        print(f"  Target demographics (from ACS):")
        print(f"    Poverty rate: {county_chars['poverty_rate']:.1f}%")
        print(f"    White: {county_chars['white_pct']:.1f}%")
        print(f"    Black: {county_chars['black_pct']:.1f}%")
        print(f"    Hispanic: {county_chars['hispanic_pct']:.1f}%")
        
        # Sample from ELIGIBLE CPS using ACS demographics
        county_sample = sample_for_county(
            cps_eligible,  # Only eligible people (<$30k income)
            n_county,
            county_chars,
            random_seed=random_seed + county_idx
        )
        
        # Convert to Seekers
        for person in county_sample:
            seeker = cps_row_to_seeker(
                person,
                seeker_id=seeker_id,
                county=county_name,
                random_state=np.random.RandomState(random_seed + seeker_id)
            )
            all_seekers.append(seeker)
            seeker_id += 1
    
    print(f"\n{'='*70}")
    print(f"COMPLETE POPULATION (ALL ELIGIBLE FOR AT LEAST ONE PROGRAM)")
    print(f"{'='*70}")
    print(f"Created {len(all_seekers)} seekers across {len(counties)} counties")
    print(f"All seekers have income < $30,000 (SNAP eligible)")
    print_population_summary(all_seekers)
    
    return all_seekers


def print_population_summary(seekers):
    """Print summary statistics."""
    
    print("\nPopulation Summary:")
    
    # Income
    incomes = [s.income for s in seekers]
    print(f"  Income:")
    print(f"    Median: ${np.median(incomes):,.0f}")
    print(f"    Mean: ${np.mean(incomes):,.0f}")
    
    # Race
    print(f"  Race:")
    for race in ['White', 'Black', 'Hispanic', 'Asian', 'Other']:
        count = sum(1 for s in seekers if s.race == race)
        if count > 0:
            print(f"    {race}: {count} ({count/len(seekers)*100:.1f}%)")
    
    # Demographics
    has_children = sum(1 for s in seekers if s.has_children)
    has_disability = sum(1 for s in seekers if s.has_disability)
    print(f"  Has children: {has_children} ({has_children/len(seekers)*100:.1f}%)")
    print(f"  Has disability: {has_disability} ({has_disability/len(seekers)*100:.1f}%)")
    
    # INITIAL ENROLLMENT (from CPS)
    snap_enrolled = sum(1 for s in seekers if s.is_enrolled('SNAP'))
    tanf_enrolled = sum(1 for s in seekers if s.is_enrolled('TANF'))
    ssi_enrolled = sum(1 for s in seekers if s.is_enrolled('SSI'))
    
    print(f"  Initial Enrollment (from CPS data):")
    print(f"    SNAP: {snap_enrolled} ({snap_enrolled/len(seekers)*100:.1f}%)")
    print(f"    TANF: {tanf_enrolled} ({tanf_enrolled/len(seekers)*100:.1f}%)")
    print(f"    SSI: {ssi_enrolled} ({ssi_enrolled/len(seekers)*100:.1f}%)")
    
    any_enrolled = sum(1 for s in seekers if len(s.enrolled_programs) > 0)
    print(f"    Any program: {any_enrolled} ({any_enrolled/len(seekers)*100:.1f}%)")


if __name__ == "__main__":
    # Test
    print("Testing data loader with weighted sampling...\n")
    
    counties = ['Autauga County, Alabama', 'Baldwin County, Alabama']
    
    seekers = create_realistic_population(
        'src/data/cps_asec_2022_processed_full.csv',
        'src/data/us_census_acs_2022_county_data.csv',
        n_seekers=200,  # 100 per county
        counties=counties,
        random_seed=42
    )
    
    print(f"\nSuccess! Created {len(seekers)} realistic seekers!")