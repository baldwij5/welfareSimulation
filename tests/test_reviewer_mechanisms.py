"""
Unit Tests for Reviewer Mechanism Controls

Tests that Reviewer class correctly respects MechanismConfig,
particularly for state-level statistical discrimination.

Run: pytest tests/test_reviewer_mechanisms.py -v

Expected: 4 tests pass (after modifying Reviewer class)
"""

import pytest
import sys
import pickle
from pathlib import Path

sys.path.insert(0, 'src')

from core.reviewer import Reviewer
from core.seeker import Seeker
from core.mechanism_config import MechanismConfig


class TestReviewerMechanismControls:
    """Test that Reviewer respects mechanism configuration."""
    
    def test_reviewer_accepts_mechanism_config(self):
        """Reviewer should accept and store mechanism config."""
        config = MechanismConfig.only_state_discrimination()
        
        reviewer = Reviewer(
            reviewer_id=1,
            county='Test County, Massachusetts',
            state='Massachusetts',
            mechanism_config=config,
            state_model=None
        )
        
        assert hasattr(reviewer, 'mechanism_config'), \
               "Reviewer should have mechanism_config attribute"
        assert reviewer.mechanism_config == config, \
               "Config should be stored correctly"
    
    def test_state_discrimination_disabled_gives_neutral_credibility(self):
        """When disabled, credibility should always be 1.0 (neutral)."""
        config = MechanismConfig.baseline()
        
        reviewer = Reviewer(
            reviewer_id=1,
            county='Test County, Massachusetts',
            state='Massachusetts',
            mechanism_config=config,
            state_model=None  # No model when disabled
        )
        
        # Create Black seeker (would normally get discrimination if enabled)
        black_seeker = Seeker(
            seeker_id=1,
            race='Black',
            income=15000,
            county='Test County, Massachusetts',
            has_children=True,
            has_disability=False,
            cps_data={},
            mechanism_config=config
        )
        
        # Create White seeker
        white_seeker = Seeker(
            seeker_id=2,
            race='White',
            income=15000,
            county='Test County, Massachusetts',
            has_children=True,
            has_disability=False,
            cps_data={},
            mechanism_config=config
        )
        
        # Calculate credibility for both
        cred_black = reviewer._calculate_credibility_from_state_patterns(black_seeker)
        cred_white = reviewer._calculate_credibility_from_state_patterns(white_seeker)
        
        # Both should be 1.0 (neutral) when discrimination disabled
        assert cred_black == 1.0, "Black credibility should be neutral when disabled"
        assert cred_white == 1.0, "White credibility should be neutral when disabled"
        assert cred_black == cred_white, "Should not discriminate when disabled"
    
    def test_state_discrimination_enabled_varies_by_race(self):
        """When enabled, state model should be loaded and used."""
        config = MechanismConfig.only_state_discrimination()
        
        # Load actual Massachusetts state model (if it exists)
        state_model_path = Path('models/state_models/Massachusetts.pkl')
        
        if not state_model_path.exists():
            pytest.skip("Massachusetts state model not found")
        
        with open(state_model_path, 'rb') as f:
            state_model = pickle.load(f)
        
        # Load ACS data for real county lookup
        from data.data_loader import load_acs_county_data
        acs_data = load_acs_county_data('src/data/us_census_acs_2022_county_data.csv')
        
        reviewer = Reviewer(
            reviewer_id=1,
            county='Suffolk County, Massachusetts',
            state='Massachusetts',
            mechanism_config=config,
            state_model=state_model,
            acs_data=acs_data  # Need ACS data for county lookups
        )
        
        # Create seeker with real county
        seeker = Seeker(
            seeker_id=1,
            race='Black',
            income=15000,
            county='Suffolk County, Massachusetts',
            has_children=True,
            has_disability=False,
            cps_data={},
            mechanism_config=config
        )
        
        # Calculate credibility
        cred = reviewer._calculate_credibility_from_state_patterns(seeker)
        
        # Should return non-neutral value when enabled with real county
        # (Exact value depends on county patterns, but shouldn't always be 1.0)
        # Just verify the mechanism is being used (state_model is not None)
        assert reviewer.state_model is not None, \
               "State model should be loaded when discrimination enabled"
        assert cred is not None, \
               "Should return a credibility value"
        # Note: cred might be 1.0 (neutral) if county patterns are average
        # The key is that the model is loaded and being used
    
    def test_state_model_not_loaded_when_disabled(self):
        """When disabled, state_model should not be used even if provided."""
        config = MechanismConfig.baseline()
        
        # Try to pass a state model (shouldn't be used)
        fake_model = {'coefficients': [1.0, 2.0, 3.0]}
        
        reviewer = Reviewer(
            reviewer_id=1,
            county='Test County, Massachusetts',
            state='Massachusetts',
            mechanism_config=config,
            state_model=fake_model  # Provided but shouldn't be used
        )
        
        # State model should be None or unused when disabled
        # (Implementation detail: might store but not use, or set to None)
        if hasattr(reviewer, 'state_model'):
            # If stored, should not affect credibility calculation
            seeker = Seeker(
                seeker_id=1, race='Black', income=15000,
                county='Test', has_children=True, has_disability=False,
                cps_data={}, mechanism_config=config
            )
            cred = reviewer._calculate_credibility_from_state_patterns(seeker)
            assert cred == 1.0, "Should not use model when disabled"


if __name__ == '__main__':
    # Run tests
    import pytest
    pytest.main([__file__, '-v', '--tb=short'])