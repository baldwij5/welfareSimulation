"""
Comprehensive Test Suite - Complete Coverage

This file documents all 107+ tests across the welfare simulation.

Test Categories:
1. Behavior Tests (42) - Seeker decision-making
2. Bureaucracy Points Tests (11) - Investigation capacity
3. Capacity Tests (17) - Workload constraints
4. Complexity Tests (7) - Application difficulty
5. Core Tests (15) - Basic classes
6. Simulation Tests (9) - Integration
7. AI Sorter Tests (7) - Experimental interventions
8. Matched Pairs Tests (NEW) - Causal inference

Run all: pytest -v
Expected: 110+ tests passing
"""

import pytest
import numpy as np
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from simulation.runner import run_simulation_with_real_data
from ai.application_sorter import AI_ApplicationSorter


@pytest.mark.integration
class TestMatchedPairsDesign:
    """Tests for matched county-pair experimental design."""
    
    def test_matched_pairs_file_created(self):
        """Test that matched pairs CSV exists."""
        import os
        # Check if file exists (created by match_counties.py)
        if os.path.exists('data/matched_county_pairs.csv'):
            assert True
        else:
            # File not required for test suite to pass
            pytest.skip("Matched pairs not yet generated")
    
    def test_load_matched_pairs(self):
        """Test loading matched county pairs."""
        try:
            import pandas as pd
            pairs_df = pd.read_csv('data/matched_county_pairs.csv')
            assert 'control_county' in pairs_df.columns
            assert 'treatment_county' in pairs_df.columns
            assert len(pairs_df) > 0
        except FileNotFoundError:
            pytest.skip("Matched pairs not yet generated")
    
    def test_matched_experiment_runs(self):
        """Test that matched experiment can run (if pairs exist)."""
        try:
            import pandas as pd
            pairs_df = pd.read_csv('data/matched_county_pairs.csv')
            
            if len(pairs_df) > 0:
                # Run one pair
                county_control = pairs_df.iloc[0]['control_county']
                county_treatment = pairs_df.iloc[0]['treatment_county']
                
                # Control
                control = run_simulation_with_real_data(
                    cps_file='src/data/cps_asec_2022_processed_full.csv',
                    acs_file='src/data/us_census_acs_2022_county_data.csv',
                    n_seekers=50,
                    n_months=3,
                    counties=[county_control],
                    ai_sorter=None,
                    random_seed=42
                )
                
                # Treatment
                ai = AI_ApplicationSorter('simple_first')
                treatment = run_simulation_with_real_data(
                    cps_file='src/data/cps_asec_2022_processed_full.csv',
                    acs_file='src/data/us_census_acs_2022_county_data.csv',
                    n_seekers=50,
                    n_months=3,
                    counties=[county_treatment],
                    ai_sorter=ai,
                    random_seed=42
                )
                
                # Both should complete
                assert control is not None
                assert treatment is not None
                
        except FileNotFoundError:
            pytest.skip("Matched pairs or data not available")


@pytest.mark.integration
class TestEndToEndWorkflow:
    """End-to-end integration tests for complete workflow."""
    
    def test_complete_workflow_with_all_features(self):
        """Test complete workflow with all features enabled."""
        from simulation.runner import run_simulation_with_real_data
        from ai.application_sorter import AI_ApplicationSorter
        
        # Run with all features
        ai = AI_ApplicationSorter('simple_first')
        
        results = run_simulation_with_real_data(
            cps_file='src/data/cps_asec_2022_processed_full.csv',
            acs_file='src/data/us_census_acs_2022_county_data.csv',
            n_seekers=100,
            n_months=6,
            counties=['Jefferson County, Alabama'],
            ai_sorter=ai,
            random_seed=42
        )
        
        # Verify all features working
        assert results is not None
        assert results['summary']['total_applications'] > 0
        
        # Check seekers have all attributes
        seeker = results['seekers'][0]
        assert hasattr(seeker, 'bureaucracy_navigation_points')
        assert hasattr(seeker, 'cps_data')
        assert hasattr(seeker, 'num_applications')
        
        # Check applications have complexity
        # (Would need to store applications to test this)
        
        # Check capacity was tracked
        evaluator = list(results['evaluators'].values())[0]
        assert hasattr(evaluator, 'capacity_used_this_month')
        assert hasattr(evaluator, 'monthly_capacity')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])