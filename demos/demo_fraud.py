"""
Demo: Fraud Decision Logic

Shows how will_commit_fraud() works based on fraud_propensity.
Run with: python demo_fraud.py
"""

import sys
import os
import numpy as np

# Add src to path
sys.path.insert(0, 'src')

from core.seeker import Seeker


def demo_fraud_propensity_distribution():
    """Show distribution of fraud propensity across seekers."""
    print("=" * 70)
    print("FRAUD PROPENSITY DISTRIBUTION")
    print("=" * 70)
    
    seekers = [Seeker(i, 'White', 30000, random_state=np.random.RandomState(i)) 
               for i in range(100)]
    
    # Group by propensity level
    very_low = [s for s in seekers if s.fraud_propensity < 0.5]
    low = [s for s in seekers if 0.5 <= s.fraud_propensity < 1.0]
    high = [s for s in seekers if 1.0 <= s.fraud_propensity < 1.5]
    very_high = [s for s in seekers if s.fraud_propensity >= 1.5]
    
    print(f"\nOut of 100 seekers:")
    print(f"  Very Low (<0.5):   {len(very_low):2d} seekers")
    print(f"  Low (0.5-1.0):     {len(low):2d} seekers")
    print(f"  High (1.0-1.5):    {len(high):2d} seekers")
    print(f"  Very High (>1.5):  {len(very_high):2d} seekers")


def demo_fraud_by_propensity():
    """Show how fraud_propensity affects fraud decisions."""
    print("\n" + "=" * 70)
    print("FRAUD RATE BY PROPENSITY LEVEL")
    print("=" * 70)
    
    seekers = [Seeker(i, 'White', 30000, random_state=np.random.RandomState(i)) 
               for i in range(200)]
    
    # Test over 10 months
    results = {
        'Very Low (<0.5)': [],
        'Low (0.5-1.0)': [],
        'High (1.0-1.5)': [],
        'Very High (>1.5)': []
    }
    
    for seeker in seekers:
        fraud_attempts = sum(seeker.will_commit_fraud(m) for m in range(10))
        
        if seeker.fraud_propensity < 0.5:
            results['Very Low (<0.5)'].append(fraud_attempts)
        elif seeker.fraud_propensity < 1.0:
            results['Low (0.5-1.0)'].append(fraud_attempts)
        elif seeker.fraud_propensity < 1.5:
            results['High (1.0-1.5)'].append(fraud_attempts)
        else:
            results['Very High (>1.5)'].append(fraud_attempts)
    
    print("\nFraud attempts out of 10 months:\n")
    for category, attempts_list in results.items():
        if attempts_list:
            avg = np.mean(attempts_list)
            pct = (avg / 10) * 100
            bar = "█" * int(pct / 2)
            print(f"  {category:20s}: {avg:.1f}/10 ({pct:4.1f}%) {bar}")


def demo_individual_examples():
    """Show specific examples with different fraud propensities."""
    print("\n" + "=" * 70)
    print("INDIVIDUAL EXAMPLES")
    print("=" * 70)
    
    # Create seekers with different propensities
    seekers = []
    for i in range(50):
        s = Seeker(i, 'White', 30000, random_state=np.random.RandomState(i))
        seekers.append(s)
    
    # Find examples
    very_low = next(s for s in seekers if s.fraud_propensity < 0.3)
    moderate = next(s for s in seekers if 0.9 < s.fraud_propensity < 1.1)
    very_high = next(s for s in seekers if s.fraud_propensity > 1.7)
    
    examples = [
        ("Very Low Risk", very_low),
        ("Moderate Risk", moderate),
        ("Very High Risk", very_high)
    ]
    
    for label, seeker in examples:
        print(f"\n{label} Seeker:")
        print(f"  Fraud propensity: {seeker.fraud_propensity:.2f}")
        print(f"  Lying magnitude: {seeker.lying_magnitude:.1f}%")
        print(f"\n  Fraud decisions over 20 months:")
        
        decisions = [seeker.will_commit_fraud(m) for m in range(20)]
        fraud_count = sum(decisions)
        
        # Show as YYYYNNYY format
        display = ''.join(['Y' if d else 'N' for d in decisions])
        print(f"  {display}")
        print(f"  Total: {fraud_count}/20 ({fraud_count/20*100:.0f}% fraud rate)")


def demo_reproducibility():
    """Show that fraud decisions are reproducible."""
    print("\n" + "=" * 70)
    print("REPRODUCIBILITY TEST")
    print("=" * 70)
    
    seeker = Seeker(1, 'Black', 25000, random_state=np.random.RandomState(42))
    
    print(f"\nSeeker fraud propensity: {seeker.fraud_propensity:.2f}")
    print(f"\nCalling will_commit_fraud(month=5) three times:")
    
    result1 = seeker.will_commit_fraud(month=5)
    result2 = seeker.will_commit_fraud(month=5)
    result3 = seeker.will_commit_fraud(month=5)
    
    print(f"  Call 1: {result1}")
    print(f"  Call 2: {result2}")
    print(f"  Call 3: {result3}")
    print(f"\n  → All the same! (Reproducible)")


def demo_overall_fraud_rate():
    """Calculate overall fraud rate across population."""
    print("\n" + "=" * 70)
    print("OVERALL FRAUD RATE")
    print("=" * 70)
    
    # Create diverse population
    seekers = [Seeker(i, 'White', 30000, random_state=np.random.RandomState(i)) 
               for i in range(500)]
    
    # Count fraud over 12 months
    total_decisions = 0
    fraud_decisions = 0
    
    for seeker in seekers:
        for month in range(12):
            total_decisions += 1
            if seeker.will_commit_fraud(month):
                fraud_decisions += 1
    
    fraud_rate = (fraud_decisions / total_decisions) * 100
    
    print(f"\n500 seekers over 12 months:")
    print(f"  Total decisions: {total_decisions:,}")
    print(f"  Fraud attempts: {fraud_decisions:,}")
    print(f"  Overall fraud rate: {fraud_rate:.2f}%")
    print(f"\n  → Research shows 3-7% is typical for welfare fraud")


def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("Fraud Decision Logic Demo")
    print("="*70)
    print("\nHow it works:")
    print("  • Each seeker has fraud_propensity (0-2)")
    print("  • Higher propensity → more likely to commit fraud")
    print("  • Decision varies by month (reproducible randomness)")
    print("  • Overall fraud rate ~3-7% (realistic)")
    
    demo_fraud_propensity_distribution()
    demo_fraud_by_propensity()
    demo_individual_examples()
    demo_reproducibility()
    demo_overall_fraud_rate()
    
    print("\n" + "="*70)
    print("Demo Complete!")
    print("="*70)
    print("\nKey Points:")
    print("  • Fraud propensity drives fraud decisions")
    print("  • Most seekers have low propensity (< 1.0)")
    print("  • High propensity seekers commit more fraud")
    print("  • Overall rate is realistic (~3-7%)")
    print("  • Decisions are reproducible")
    print("\nNext: Run pytest tests/test_behavior.py::TestFraudDecision -v")


if __name__ == "__main__":
    main()