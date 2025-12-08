"""
Unit Tests for Seeker Mechanism Controls

Tests that Seeker class correctly respects MechanismConfig settings.
Each mechanism should be independently controllable.

Run: pytest tests/test_seeker_mechanisms.py -v

Expected: 8 tests pass (after modifying Seeker class)
"""

import pytest
import sys
sys.path.insert(0, 'src')

from core.seeker import Seeker
from core.mechanism_config import MechanismConfig


class TestSeekerMechanismControls:
    """Test that Seeker respects mechanism configuration."""
    
    def test_seeker_accepts_mechanism_config(self):
        """Seeker should accept and store mechanism config."""
        config = MechanismConfig.only_bureaucracy()
        
        seeker = Seeker(
            seeker_id=1,
            race='Black',
            income=15000,
            county='Test County, Massachusetts',
            has_children=True,
            has_disability=False,
            cps_data={'education': 'less_than_hs'},
            mechanism_config=config
        )
        
        assert hasattr(seeker, 'mechanism_config'), "Seeker should have mechanism_config attribute"
        assert seeker.mechanism_config == config, "Config should be stored correctly"
    
    def test_seeker_defaults_to_full_model_when_no_config(self):
        """When no config provided, should default to full model."""
        seeker = Seeker(
            seeker_id=1,
            race='Black',
            income=15000,
            county='Test County, Massachusetts',
            has_children=True,
            has_disability=False,
            cps_data={}
        )
        
        # Should default to full model
        assert seeker.mechanism_config.is_full_model(), "Should default to full model"
    
    def test_bureaucracy_points_disabled_gives_unlimited_points(self):
        """When bureaucracy disabled, seeker should have unlimited navigation capacity."""
        config = MechanismConfig.baseline()
        
        seeker = Seeker(
            seeker_id=1,
            race='Black',
            income=15000,
            county='Test County, Massachusetts',
            has_children=True,
            has_disability=False,
            cps_data={'education': 'less_than_hs'},  # Normally gives low points
            mechanism_config=config
        )
        
        # When disabled, points should be None (unlimited) or very high
        assert seeker.bureaucracy_navigation_points is None or \
               seeker.bureaucracy_navigation_points >= 100, \
               "Disabled bureaucracy should give unlimited points"
    
    def test_bureaucracy_points_enabled_varies_by_education(self):
        """When enabled, points should vary by education level."""
        config = MechanismConfig.only_bureaucracy()
        
        low_ed_seeker = Seeker(
            seeker_id=1,
            race='Black',
            income=15000,
            county='Test County, Massachusetts',
            has_children=True,
            has_disability=False,
            cps_data={'education': 'less_than_hs'},
            mechanism_config=config
        )
        
        high_ed_seeker = Seeker(
            seeker_id=2,
            race='White',
            income=15000,
            county='Test County, Massachusetts',
            has_children=True,
            has_disability=False,
            cps_data={'education': 'graduate'},
            mechanism_config=config
        )
        
        # Both should have points (not None)
        assert low_ed_seeker.bureaucracy_navigation_points is not None
        assert high_ed_seeker.bureaucracy_navigation_points is not None
        
        # High education should have MORE points
        assert high_ed_seeker.bureaucracy_navigation_points > \
               low_ed_seeker.bureaucracy_navigation_points, \
               "Graduate degree should have more points than less than HS"
    
    def test_fraud_history_disabled_never_bans(self):
        """When fraud disabled, seekers should never be banned regardless of detections."""
        config = MechanismConfig.baseline()
        
        seeker = Seeker(
            seeker_id=1,
            race='Black',
            income=15000,
            county='Test County, Massachusetts',
            has_children=True,
            has_disability=False,
            cps_data={},
            mechanism_config=config
        )
        
        # Record 3 fraud detections (normally triggers permanent ban)
        seeker.record_fraud_detection(month=1)
        seeker.record_fraud_detection(month=7)
        seeker.record_fraud_detection(month=13)
        
        # Should NOT be banned when mechanism disabled
        assert seeker.is_banned_for_fraud(month=14) == False, \
               "Should not be banned when fraud mechanism disabled"
        
        # Verify fraud_detections list is None or empty when disabled
        if hasattr(seeker, 'fraud_detections'):
            assert seeker.fraud_detections is None or len(seeker.fraud_detections) == 0
    
    def test_fraud_history_enabled_bans_after_three_strikes(self):
        """When enabled, fraud detections should create escalating bans."""
        config = MechanismConfig.only_fraud()
        
        seeker = Seeker(
            seeker_id=1,
            race='Black',
            income=15000,
            county='Test County, Massachusetts',
            has_children=True,
            has_disability=False,
            cps_data={},
            mechanism_config=config
        )
        
        # Should not be banned initially
        assert seeker.is_banned_for_fraud(month=0) == False
        
        # Record 1st fraud detection at month 1
        seeker.record_fraud_detection(month=1)
        # Should be banned for 6 months (months 1-7)
        assert seeker.is_banned_for_fraud(month=2) == True, "Should be banned during 6-month period"
        assert seeker.is_banned_for_fraud(month=6) == True, "Should still be banned at month 6"
        assert seeker.is_banned_for_fraud(month=8) == False, "Ban should expire after 6 months"
        
        # Record 2nd fraud detection at month 10
        seeker.record_fraud_detection(month=10)
        # Should be banned for 12 months (months 10-22)
        assert seeker.is_banned_for_fraud(month=11) == True, "Should be banned during 12-month period"
        assert seeker.is_banned_for_fraud(month=21) == True, "Should still be banned at month 21"
        assert seeker.is_banned_for_fraud(month=23) == False, "Ban should expire after 12 months"
        
        # Record 3rd fraud detection at month 24
        seeker.record_fraud_detection(month=24)
        # Should be PERMANENTLY banned
        assert seeker.is_banned_for_fraud(month=25) == True, "Should be permanently banned after 3 strikes"
        assert seeker.is_banned_for_fraud(month=100) == True, "Permanent ban never expires"
    
    def test_learning_disabled_beliefs_never_change(self):
        """When learning disabled, beliefs should remain constant."""
        config = MechanismConfig.baseline()
        
        seeker = Seeker(
            seeker_id=1,
            race='Black',
            income=15000,
            county='Test County, Massachusetts',
            has_children=True,
            has_disability=False,
            cps_data={},
            mechanism_config=config
        )
        
        # Record initial belief
        initial_snap_belief = seeker.perceived_approval_probability['SNAP']
        initial_tanf_belief = seeker.perceived_approval_probability['TANF']
        
        # Experience denials (normally would reduce beliefs)
        seeker.update_beliefs(program='SNAP', outcome='DENIED')
        seeker.update_beliefs(program='SNAP', outcome='DENIED')
        seeker.update_beliefs(program='TANF', outcome='DENIED')
        
        # Beliefs should NOT change when learning disabled
        assert seeker.perceived_approval_probability['SNAP'] == initial_snap_belief, \
               "SNAP belief should not change when learning disabled"
        assert seeker.perceived_approval_probability['TANF'] == initial_tanf_belief, \
               "TANF belief should not change when learning disabled"
    
    def test_learning_enabled_denials_reduce_beliefs(self):
        """When enabled, denials should reduce perceived approval probability."""
        config = MechanismConfig.only_learning()
        
        seeker = Seeker(
            seeker_id=1,
            race='Black',
            income=15000,
            county='Test County, Massachusetts',
            has_children=True,
            has_disability=False,
            cps_data={},
            mechanism_config=config
        )
        
        # Record initial belief
        initial_belief = seeker.perceived_approval_probability['SNAP']
        
        # Experience denial
        seeker.update_beliefs(program='SNAP', outcome='DENIED')
        
        # Belief should decrease (Bayesian updating with negative evidence)
        assert seeker.perceived_approval_probability['SNAP'] < initial_belief, \
               "Denial should reduce belief when learning enabled"
        
        # Verify it decreased by learning_rate amount
        # Expected: (1 - α) * old + α * 0.0 where α = learning_rate
        # If learning_rate = 0.3: (1-0.3) * 0.70 + 0.3 * 0.0 = 0.49
        expected_new = (1 - seeker.learning_rate) * initial_belief + seeker.learning_rate * 0.0
        assert abs(seeker.perceived_approval_probability['SNAP'] - expected_new) < 0.01, \
               "Belief should update according to Bayesian rule"
    
    def test_learning_enabled_approvals_increase_beliefs(self):
        """When enabled, approvals should increase perceived probability."""
        config = MechanismConfig.only_learning()
        
        seeker = Seeker(
            seeker_id=1,
            race='Black',
            income=15000,
            county='Test County, Massachusetts',
            has_children=True,
            has_disability=False,
            cps_data={},
            mechanism_config=config
        )
        
        initial_belief = seeker.perceived_approval_probability['TANF']
        
        # Experience approval
        seeker.update_beliefs(program='TANF', outcome='APPROVED')
        
        # Belief should increase
        assert seeker.perceived_approval_probability['TANF'] > initial_belief, \
               "Approval should increase belief when learning enabled"
    
    def test_custom_config_respects_all_flags(self):
        """Custom config should respect all flag combinations."""
        config = MechanismConfig(
            bureaucracy_points_enabled=True,
            fraud_history_enabled=False,
            learning_enabled=True,
            state_discrimination_enabled=False
        )
        
        seeker = Seeker(
            seeker_id=1,
            race='Black',
            income=15000,
            county='Test County, Massachusetts',
            has_children=True,
            has_disability=False,
            cps_data={'education': 'high_school'},
            mechanism_config=config
        )
        
        # Should have points (bureaucracy enabled)
        assert seeker.bureaucracy_navigation_points is not None
        
        # Should not track fraud (fraud disabled)
        if hasattr(seeker, 'fraud_detections'):
            assert seeker.fraud_detections is None or len(seeker.fraud_detections) == 0
        
        # Should learn (learning enabled)
        initial_belief = seeker.perceived_approval_probability['SNAP']
        seeker.update_beliefs('SNAP', 'DENIED')
        assert seeker.perceived_approval_probability['SNAP'] < initial_belief


if __name__ == '__main__':
    # Run tests
    import pytest
    pytest.main([__file__, '-v', '--tb=short'])