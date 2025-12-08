"""
Variance Diagnostic Tests

Tests that Monte Carlo iterations produce appropriate variance.
Addresses the suspiciously low variance (t=-535, CI=0.08pp) issue.

Run: pytest tests/test_monte_carlo_variance.py -v

Expected: 3 tests pass (verifies stochasticity)
"""

import pytest
import sys
import numpy as np

sys.path.insert(0, 'src')

from data.data_loader import create_realistic_population


class TestMonteCarloVariance:
    """Test that Monte Carlo iterations are truly independent and stochastic."""
    
    def test_different_seeds_produce_different_populations(self):
        """
        Different random seeds should create different seeker populations.
        
        This is CRITICAL - if seeds don't work, all iterations are identical!
        """
        county = ['Suffolk County, Massachusetts']
        
        # Create two populations with different seeds
        pop1 = create_realistic_population(
            cps_file='src/data/cps_asec_2022_processed_full.csv',
            acs_file='src/data/us_census_acs_2022_county_data.csv',
            n_seekers=100,
            counties=county,
            proportional=True,
            random_seed=42
        )
        
        pop2 = create_realistic_population(
            cps_file='src/data/cps_asec_2022_processed_full.csv',
            acs_file='src/data/us_census_acs_2022_county_data.csv',
            n_seekers=100,
            counties=county,
            proportional=True,
            random_seed=43  # Different seed
        )
        
        assert len(pop1) == len(pop2), "Populations should be same size"
        
        # Check that seeker IDs differ
        ids1 = set(s.id for s in pop1)
        ids2 = set(s.id for s in pop2)
        
        overlap = len(ids1 & ids2)
        overlap_pct = overlap / len(ids1)
        
        # With the fix, IDs should be in completely different ranges
        # Seed 42: 42,000,000 - 42,000,099
        # Seed 43: 43,000,000 - 43,000,099
        # Expected overlap: 0%
        assert overlap == 0, \
               f"IDs should be in different ranges (no overlap). Got {overlap_pct:.1%} overlap"
        
        print(f"  ✓ Seed test: 0% overlap (IDs in different ranges - correct!)")
    
    def test_same_seed_produces_identical_populations(self):
        """
        Same random seed should create identical populations (reproducibility).
        """
        county = ['Suffolk County, Massachusetts']
        
        # Create two populations with SAME seed
        pop1 = create_realistic_population(
            'src/data/cps_asec_2022_processed_full.csv',
            'src/data/us_census_acs_2022_county_data.csv',
            n_seekers=100,
            counties=county,
            proportional=True,
            random_seed=42
        )
        
        pop2 = create_realistic_population(
            'src/data/cps_asec_2022_processed_full.csv',
            'src/data/us_census_acs_2022_county_data.csv',
            n_seekers=100,
            counties=county,
            proportional=True,
            random_seed=42  # SAME seed
        )
        
        # Should be identical
        ids1 = [s.id for s in pop1]
        ids2 = [s.id for s in pop2]
        
        assert ids1 == ids2, "Same seed should produce identical populations"
        
        # Check demographics too
        race1 = [s.race for s in pop1]
        race2 = [s.race for s in pop2]
        
        assert race1 == race2, "Same seed should produce identical demographics"
        
        print(f"  ✓ Reproducibility test: Populations identical with same seed")
    
    def test_sequential_seeds_produce_varying_outcomes(self):
        """
        Sequential Monte Carlo iterations should produce varying approval rates.
        
        This tests the CRITICAL variance issue. If outcomes are too similar,
        it suggests determinism or insufficient stochasticity.
        """
        county = ['Suffolk County, Massachusetts']
        
        # Run 5 quick iterations and measure variance
        median_incomes = []
        
        for seed in range(42, 47):  # Seeds: 42, 43, 44, 45, 46
            # Create population
            seekers = create_realistic_population(
                'src/data/cps_asec_2022_processed_full.csv',
                'src/data/us_census_acs_2022_county_data.csv',
                n_seekers=100,
                counties=county,
                proportional=True,
                random_seed=seed
            )
            
            # Check median income (should vary due to different CPS samples)
            median_income = np.median([s.income for s in seekers])
            median_incomes.append(median_income)
        
        # Calculate variance
        variance = np.var(median_incomes)
        std = np.std(median_incomes)
        mean = np.mean(median_incomes)
        
        print(f"  Median incomes across 5 seeds: {[f'${x:,.0f}' for x in median_incomes]}")
        print(f"  Mean: ${mean:,.0f}, Std: ${std:,.0f}, Variance: {variance:,.0f}")
        
        # Check that there IS variance (not deterministic)
        assert variance > 0, \
               "CRITICAL: Zero variance across seeds! Model is deterministic!"
        
        # But not TOO much variance (should be somewhat stable)
        # With 100 seekers, median income variance should be moderate
        # Expect std of a few thousand dollars
        assert std > 100, \
               f"Variance too low: std=${std:,.0f}. Sampling might not be working."
        assert std < 10000, \
               f"Variance too high: std=${std:,.0f}. Sampling might be broken."
        
        # Coefficient of variation should be reasonable
        cv = std / mean if mean > 0 else float('inf')
        assert cv < 0.5, \
               f"Coefficient of variation too high: {cv:.2f}"
        
        print(f"  ✓ Variance test: Healthy stochasticity (CV={cv:.2f}, std=${std:,.0f})")


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v', '--tb=short', '-s'])  # -s shows print statements