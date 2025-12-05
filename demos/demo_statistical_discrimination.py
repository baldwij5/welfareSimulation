"""
Demo: Statistical Discrimination System

Shows how learned patterns from ACS data create emergent bias.

Run with: python demo_statistical_discrimination.py
"""

import sys
sys.path.insert(0, 'src')
import numpy as np

from core.seeker import Seeker
from core.application import Application
from core.reviewer import Reviewer


def demo_without_model():
    """Show investigation without statistical discrimination."""
    print("="*70)
    print("WITHOUT STATISTICAL DISCRIMINATION (Baseline)")
    print("="*70)
    
    # Create reviewer without model
    reviewer = Reviewer(
        reviewer_id=1,
        credibility_model=None,
        acs_data=None,
        random_state=np.random.RandomState(42)
    )
    
    # Two seekers with same characteristics
    seeker1 = Seeker(1, 'Black', 15000, 'Jefferson County, Alabama', False, False,
                    cps_data={}, random_state=np.random.RandomState(42))
    seeker1.bureaucracy_navigation_points = 12.0
    
    seeker2 = Seeker(2, 'White', 15000, 'Orange County, California', False, False,
                    cps_data={}, random_state=np.random.RandomState(43))
    seeker2.bureaucracy_navigation_points = 12.0
    
    print(f"\nSeeker 1 (Black, Jefferson County, AL):")
    print(f"  Bureaucracy points: {seeker1.bureaucracy_navigation_points}")
    mult1 = reviewer._calculate_credibility_from_patterns(seeker1)
    print(f"  Credibility multiplier: {mult1:.2f}")
    print(f"  Investigation difficulty: Normal (no model)")
    
    print(f"\nSeeker 2 (White, Orange County, CA):")
    print(f"  Bureaucracy points: {seeker2.bureaucracy_navigation_points}")
    mult2 = reviewer._calculate_credibility_from_patterns(seeker2)
    print(f"  Credibility multiplier: {mult2:.2f}")
    print(f"  Investigation difficulty: Normal (no model)")
    
    print(f"\n→ Both treated equally (no statistical discrimination)")


def demo_with_model():
    """Show investigation WITH statistical discrimination."""
    print(f"\n{'='*70}")
    print("WITH STATISTICAL DISCRIMINATION (Pattern-Based)")
    print("="*70)
    
    print(f"\nFirst, let's train a model...")
    print(f"(Run: python scripts/train_reviewer_model.py)")
    print(f"\nFor this demo, I'll create a simple mock model...")
    
    # Create simple mock model
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    import pandas as pd
    
    # Mock training data
    # High poverty + high Black % → High need (1)
    # Low poverty + low Black % → Low need (0)
    X_train = np.array([
        [25, 35000, 40],  # High poverty, low income, high Black% → High need
        [10, 60000, 10],  # Low poverty, high income, low Black% → Low need
        [20, 40000, 30],
        [12, 55000, 15],
        [22, 38000, 35]
    ])
    y_train = np.array([1, 0, 1, 0, 1])
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_train)
    
    model = LogisticRegression()
    model.fit(X_scaled, y_train)
    
    print(f"\nModel trained! Learned patterns:")
    print(f"  High poverty + High Black % → High need (easier investigation)")
    print(f"  Low poverty + Low Black % → Low need (harder investigation)")
    
    model_package = {
        'model': model,
        'scaler': scaler,
        'features': ['poverty_rate', 'median_household_income', 'black_pct']
    }
    
    # ACS data for two counties
    acs_data = pd.DataFrame({
        'county_name': ['Jefferson County, Alabama', 'Orange County, California'],
        'poverty_rate': [15.9, 9.7],
        'median_household_income': [52000, 90000],
        'black_pct': [42.7, 1.7]
    })
    
    # Create reviewer with model
    reviewer = Reviewer(
        reviewer_id=1,
        credibility_model=model_package,
        acs_data=acs_data,
        random_state=np.random.RandomState(42)
    )
    
    # Two seekers (SAME individual characteristics, DIFFERENT counties)
    seeker1 = Seeker(1, 'Black', 15000, 'Jefferson County, Alabama', False, False,
                    cps_data={}, random_state=np.random.RandomState(42))
    seeker1.bureaucracy_navigation_points = 12.0
    
    seeker2 = Seeker(2, 'White', 15000, 'Orange County, California', False, False,
                    cps_data={}, random_state=np.random.RandomState(43))
    seeker2.bureaucracy_navigation_points = 12.0
    
    print(f"\nSeeker 1 (Black, Jefferson County, AL):")
    print(f"  County: 16% poverty, 43% Black")
    print(f"  Bureaucracy points: {seeker1.bureaucracy_navigation_points}")
    
    mult1 = reviewer._calculate_credibility_from_patterns(seeker1)
    print(f"  Credibility multiplier: {mult1:.2f}")
    
    if mult1 < 1.0:
        print(f"  → EASIER investigation ({(1-mult1)*100:.0f}% reduction)")
        print(f"  → County patterns suggest high legitimate need")
    
    print(f"\nSeeker 2 (White, Orange County, CA):")
    print(f"  County: 10% poverty, 2% Black")
    print(f"  Bureaucracy points: {seeker2.bureaucracy_navigation_points}")
    
    mult2 = reviewer._calculate_credibility_from_patterns(seeker2)
    print(f"  Credibility multiplier: {mult2:.2f}")
    
    if mult2 > 1.0:
        print(f"  → HARDER investigation (+{(mult2-1)*100:.0f}% increase)")
        print(f"  → County patterns suggest low need (suspicious)")
    
    print(f"\n{'='*70}")
    print("STATISTICAL DISCRIMINATION IN ACTION")
    print("="*70)
    print(f"\nSame bureaucracy points (12.0)")
    print(f"Same individual characteristics")
    print(f"DIFFERENT counties")
    print(f"\n→ Investigation difficulty differs by county!")
    print(f"→ Seeker 1: {mult1:.2f}× costs")
    print(f"→ Seeker 2: {mult2:.2f}× costs")
    print(f"→ Difference: {mult2/mult1:.2f}× harder for Seeker 2")
    print(f"\nThis creates disparate impact WITHOUT seeing race!")
    print(f"Model only sees: poverty rate, income, Black% of COUNTY")
    print(f"Not individual race!")


def main():
    """Run demo."""
    print("\n" + "="*70)
    print("STATISTICAL DISCRIMINATION DEMO")
    print("="*70)
    print("\nShows how reviewers use learned patterns from ACS data")
    print("to assess applicant credibility, creating emergent bias.")
    
    # Demo without model
    demo_without_model()
    
    # Demo with model
    demo_with_model()
    
    print(f"\n{'='*70}")
    print("KEY INSIGHTS")
    print("="*70)
    print("\n1. No explicit racism:")
    print("   Reviewer never sees individual race")
    
    print("\n2. Uses aggregate statistics:")
    print("   County-level patterns (poverty, demographics)")
    
    print("\n3. Creates individual disparities:")
    print("   Applicants from 'high-need' counties → easier")
    print("   Applicants from 'low-need' counties → harder")
    
    print("\n4. Statistical discrimination:")
    print("   Using group averages to judge individuals")
    print("   Rational but creates bias!")
    
    print("\n5. Emergent, not designed:")
    print("   No one programmed racism")
    print("   Emerges from pattern recognition")
    
    print(f"\n{'='*70}")
    print("To use in simulations:")
    print(f"{'='*70}")
    print("\n1. Train model:")
    print("   python scripts/train_reviewer_model.py")
    print("\n2. Run experiments:")
    print("   python experiments/experiment_parallel_worlds.py")
    print("\n3. Compare:")
    print("   With vs without statistical discrimination")


if __name__ == "__main__":
    main()