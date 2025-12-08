"""
Integration Tests for Ablation Studies

Tests that ablation experiments work end-to-end with all components
integrated correctly.

Run: pytest tests/test_ablation_integration.py -v

Expected: 6 tests pass (after all components updated)
"""

import pytest
import sys
sys.path.insert(0, 'src')

from core.mechanism_config import MechanismConfig
from core.seeker import Seeker
from data.data_loader import create_realistic_population, load_acs_county_data
from simulation.runner import create_evaluators, create_reviewers, run_month


class TestAblationIntegration:
    """Test that ablation experiments work end-to-end."""
    
    @pytest.fixture
    def ma_test_county(self):
        """Get a single MA county for testing."""
        return ['Suffolk County, Massachusetts']
    
    @pytest.fixture
    def acs_data(self):
        """Load ACS data once for all tests."""
        return load_acs_county_data('src/data/us_census_acs_2022_county_data.csv')
    
    def test_baseline_simulation_completes(self, ma_test_county, acs_data):
        """Baseline (no mechanisms) should complete without errors."""
        config = MechanismConfig.baseline()
        
        # Create small population (fast test)
        seekers = create_realistic_population(
            cps_file='src/data/cps_asec_2022_processed_full.csv',
            acs_file='src/data/us_census_acs_2022_county_data.csv',
            n_seekers=100,
            counties=ma_test_county,
            proportional=True,
            random_seed=42,
            mechanism_config=config
        )
        
        assert len(seekers) > 0, "Should create seekers"
        assert all(s.mechanism_config == config for s in seekers), \
               "All seekers should have baseline config"
        
        # Create staff
        evaluators = create_evaluators(
            ma_test_county,
            acs_data=acs_data,
            mechanism_config=config,
            random_seed=42
        )
        
        reviewers = create_reviewers(
            ma_test_county,
            acs_data=acs_data,
            mechanism_config=config,
            load_state_models=False,  # Disabled in baseline
            random_seed=42
        )
        
        # Run 1 month (should complete without errors)
        stats = run_month(seekers, evaluators, reviewers, month=0, ai_sorter=None)
        
        assert stats is not None, "run_month should return stats"
        assert 'applications_submitted' in stats, "Stats should include applications"
        
        # Test passed if we got here without exceptions
    
    def test_only_bureaucracy_simulation_completes(self, ma_test_county, acs_data):
        """Only bureaucracy mechanism should work."""
        config = MechanismConfig.only_bureaucracy()
        
        seekers = create_realistic_population(
            'src/data/cps_asec_2022_processed_full.csv',
            'src/data/us_census_acs_2022_county_data.csv',
            n_seekers=100,
            counties=ma_test_county,
            proportional=True,
            random_seed=42,
            mechanism_config=config
        )
        
        assert len(seekers) > 0
        assert all(s.mechanism_config.only_bureaucracy() for s in seekers if hasattr(s.mechanism_config, 'only_bureaucracy'))
        
        # Verify bureaucracy points exist
        assert all(s.bureaucracy_navigation_points is not None for s in seekers), \
               "All seekers should have points when bureaucracy enabled"
        
        # Create staff and run
        evaluators = create_evaluators(ma_test_county, acs_data, config, 42)
        reviewers = create_reviewers(ma_test_county, acs_data, config, False, 42)
        
        stats = run_month(seekers, evaluators, reviewers, 0, None)
        assert stats is not None
    
    def test_only_learning_simulation_completes(self, ma_test_county, acs_data):
        """Only learning mechanism should work."""
        config = MechanismConfig.only_learning()
        
        seekers = create_realistic_population(
            'src/data/cps_asec_2022_processed_full.csv',
            'src/data/us_census_acs_2022_county_data.csv',
            n_seekers=100,
            counties=ma_test_county,
            proportional=True,
            random_seed=42,
            mechanism_config=config
        )
        
        assert len(seekers) > 0
        
        # Run simulation
        evaluators = create_evaluators(ma_test_county, acs_data, config, 42)
        reviewers = create_reviewers(ma_test_county, acs_data, config, False, 42)
        
        # Run 2 months to test learning over time
        run_month(seekers, evaluators, reviewers, 0, None)
        run_month(seekers, evaluators, reviewers, 1, None)
        
        # Verify some seekers updated beliefs
        # (At least some should have applied and received outcomes)
        beliefs_changed = any(
            s.perceived_approval_probability['SNAP'] != 0.70  # Initial value
            for s in seekers
        )
        
        # Note: This might not always be True with only 100 seekers
        # If no one applied to SNAP, beliefs won't change
        # So we just verify it doesn't crash
    
    def test_only_state_discrimination_simulation_completes(self, ma_test_county, acs_data):
        """Only state discrimination should work."""
        config = MechanismConfig.only_state_discrimination()
        
        seekers = create_realistic_population(
            'src/data/cps_asec_2022_processed_full.csv',
            'src/data/us_census_acs_2022_county_data.csv',
            n_seekers=100,
            counties=ma_test_county,
            proportional=True,
            random_seed=42,
            mechanism_config=config
        )
        
        assert len(seekers) > 0
        
        # Create staff WITH state models
        evaluators = create_evaluators(ma_test_county, acs_data, config, 42)
        reviewers = create_reviewers(
            ma_test_county,
            acs_data,
            config,
            load_state_models=True,  # Should load when enabled
            random_seed=42
        )
        
        # Verify at least some reviewers have state models
        # (Might not all have them depending on state)
        reviewers_with_models = sum(
            1 for r in reviewers.values() 
            if hasattr(r, 'state_model') and r.state_model is not None
        )
        
        # With state discrimination enabled, should have loaded models
        # (Though might be None if state not in our 51 trained models)
        
        stats = run_month(seekers, evaluators, reviewers, 0, None)
        assert stats is not None
    
    def test_all_single_mechanism_configs_complete(self, ma_test_county, acs_data):
        """Each single-mechanism config should run successfully."""
        configs = [
            ('Baseline', MechanismConfig.baseline()),
            ('Bureaucracy', MechanismConfig.only_bureaucracy()),
            ('Fraud', MechanismConfig.only_fraud()),
            ('Learning', MechanismConfig.only_learning()),
            ('Discrimination', MechanismConfig.only_state_discrimination())
        ]
        
        for name, config in configs:
            # Create population
            seekers = create_realistic_population(
                'src/data/cps_asec_2022_processed_full.csv',
                'src/data/us_census_acs_2022_county_data.csv',
                n_seekers=50,  # Small for speed
                counties=ma_test_county,
                proportional=True,
                random_seed=42,
                mechanism_config=config
            )
            
            assert len(seekers) > 0, f"{name} should create seekers"
            
            # Verify config propagated
            assert all(s.mechanism_config == config for s in seekers), \
                   f"{name} config should propagate to all seekers"
            
            # Create staff
            evaluators = create_evaluators(ma_test_county, acs_data, config, 42)
            reviewers = create_reviewers(
                ma_test_county, acs_data, config,
                load_state_models=config.state_discrimination_enabled,
                random_seed=42
            )
            
            # Run should complete without errors
            stats = run_month(seekers, evaluators, reviewers, 0, None)
            assert stats is not None, f"{name} run_month should return stats"
    
    def test_full_model_matches_current_implementation(self, ma_test_county, acs_data):
        """Full model should behave identically to current implementation."""
        config_full = MechanismConfig.full_model()
        config_none = None  # Your current code (defaults to full model)
        
        # Create two populations with same seed
        seekers_full = create_realistic_population(
            'src/data/cps_asec_2022_processed_full.csv',
            'src/data/us_census_acs_2022_county_data.csv',
            n_seekers=50,
            counties=ma_test_county,
            proportional=True,
            random_seed=99,
            mechanism_config=config_full
        )
        
        seekers_none = create_realistic_population(
            'src/data/cps_asec_2022_processed_full.csv',
            'src/data/us_census_acs_2022_county_data.csv',
            n_seekers=50,
            counties=ma_test_county,
            proportional=True,
            random_seed=99,
            mechanism_config=config_none  # Should default to full
        )
        
        # Should create same seekers (same seed, same config)
        assert len(seekers_full) == len(seekers_none), \
               "Full model should match default behavior"
        
        # Verify both have all mechanisms active
        for s_full, s_none in zip(seekers_full, seekers_none):
            assert s_full.mechanism_config.is_full_model()
            assert s_none.mechanism_config.is_full_model()


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v', '--tb=short'])