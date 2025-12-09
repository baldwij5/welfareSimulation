"""
Tests for Fraud History System

Run with: pytest tests/test_fraud_history.py -v
"""

import pytest
import sys
import os
import numpy as np

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from core.seeker import Seeker
from core.application import Application
from core.evaluator import Evaluator
from core.reviewer import Reviewer


@pytest.mark.unit
class TestFraudHistoryTracking:
    """Tests for fraud history tracking in Seeker."""
    
    def test_seeker_has_fraud_history_attributes(self):
        """Test that seeker has fraud history attributes."""
        seeker = Seeker(1, 'White', 15000, 'TEST', False, False, random_state=np.random.RandomState(42))
        
        assert hasattr(seeker, 'fraud_detected_count')
        assert hasattr(seeker, 'last_fraud_detection_month')
        assert hasattr(seeker, 'investigation_history')
        assert hasattr(seeker, 'denial_history')
        assert hasattr(seeker, 'fraud_flag')
    
    def test_initial_fraud_count_is_zero(self):
        """Test that new seekers have no fraud history."""
        seeker = Seeker(1, 'White', 15000, 'TEST', False, False, random_state=np.random.RandomState(42))
        
        assert seeker.fraud_detected_count == 0
        assert seeker.last_fraud_detection_month is None
        assert seeker.fraud_flag == False
    
    def test_record_fraud_detection_increments_count(self):
        """Test that recording fraud increases count."""
        seeker = Seeker(1, 'White', 15000, 'TEST', False, False, random_state=np.random.RandomState(42))
        
        seeker.record_fraud_detection(month=5)
        
        assert seeker.fraud_detected_count == 1
        assert seeker.last_fraud_detection_month == 5
    
    def test_fraud_flag_after_three_detections(self):
        """Test that permanent flag set after 3 detections."""
        seeker = Seeker(1, 'White', 15000, 'TEST', False, False, random_state=np.random.RandomState(42))
        
        seeker.record_fraud_detection(month=1)
        seeker.record_fraud_detection(month=8)
        assert seeker.fraud_flag == False  # Not yet
        
        seeker.record_fraud_detection(month=15)
        assert seeker.fraud_flag == True  # Now permanent!


@pytest.mark.unit
class TestFraudBans:
    """Tests for fraud ban system."""
    
    def test_no_ban_initially(self):
        """Test that seekers start unbanned."""
        seeker = Seeker(1, 'White', 15000, 'TEST', False, False, random_state=np.random.RandomState(42))
        
        assert seeker.is_banned_for_fraud(month=5) == False
    
    def test_six_month_ban_after_first_offense(self):
        """Test 6-month ban after first fraud detection."""
        seeker = Seeker(1, 'White', 15000, 'TEST', False, False, random_state=np.random.RandomState(42))
        
        # Caught at month 5
        seeker.record_fraud_detection(month=5)
        
        # Banned for months 6-10 (6 month ban)
        assert seeker.is_banned_for_fraud(month=6) == True
        assert seeker.is_banned_for_fraud(month=10) == True
        
        # Can apply again at month 11
        assert seeker.is_banned_for_fraud(month=11) == False
    
    def test_twelve_month_ban_after_second_offense(self):
        """Test 12-month ban after second fraud detection."""
        seeker = Seeker(1, 'White', 15000, 'TEST', False, False, random_state=np.random.RandomState(42))
        
        # First offense at month 5
        seeker.record_fraud_detection(month=5)
        
        # Second offense at month 12 (after first ban expired)
        seeker.record_fraud_detection(month=12)
        
        # Now banned for 12 months (until month 24)
        assert seeker.is_banned_for_fraud(month=13) == True
        assert seeker.is_banned_for_fraud(month=23) == True
        assert seeker.is_banned_for_fraud(month=24) == False
    
    def test_permanent_ban_after_third_offense(self):
        """Test permanent ban after 3rd detection."""
        seeker = Seeker(1, 'White', 15000, 'TEST', False, False, random_state=np.random.RandomState(42))
        
        seeker.record_fraud_detection(month=1)
        seeker.record_fraud_detection(month=8)
        seeker.record_fraud_detection(month=20)
        
        # Permanently banned
        assert seeker.fraud_flag == True
        assert seeker.is_banned_for_fraud(month=100) == True
        assert seeker.is_banned_for_fraud(month=1000) == True


@pytest.mark.unit
class TestInvestigationHistory:
    """Tests for investigation history affecting suspicion."""
    
    def test_record_investigation_adds_to_history(self):
        """Test that investigations are recorded."""
        seeker = Seeker(1, 'White', 15000, 'TEST', False, False, random_state=np.random.RandomState(42))
        
        seeker.record_investigation(month=3)
        
        assert 3 in seeker.investigation_history
        assert seeker.has_investigation_history() == True
    
    def test_investigation_history_increases_suspicion(self):
        """Test that past investigations increase suspicion."""
        evaluator = Evaluator(1, county='TEST', program='SNAP', random_state=np.random.RandomState(42))
        
        # Seeker with no history
        seeker_clean = Seeker(1, 'White', 15000, 'TEST', False, False, random_state=np.random.RandomState(42))
        
        # Seeker with investigation history
        seeker_history = Seeker(2, 'White', 15000, 'TEST', False, False, random_state=np.random.RandomState(42))
        seeker_history.record_investigation(month=1)
        seeker_history.record_investigation(month=3)
        
        # Same application
        app = Application(1, 1, 'SNAP', 0, 15000, 2, False, 15000, 2, False)
        
        # Calculate suspicion
        suspicion_clean = evaluator._calculate_suspicion(app, seeker_clean)
        suspicion_history = evaluator._calculate_suspicion(app, seeker_history)
        
        # History should increase suspicion
        assert suspicion_history > suspicion_clean


@pytest.mark.integration  
class TestFraudHistoryIntegration:
    """Integration tests for complete fraud history system."""
    
    def test_fraudster_banned_after_detection(self):
        """Test that fraudster can't immediately reapply after being caught."""
        seeker = Seeker(1, 'White', 15000, 'TEST', True, False, random_state=np.random.RandomState(42))
        
        # Caught for fraud at month 5
        seeker.record_fraud_detection(month=5)
        
        # Should not be able to apply during ban
        can_apply_month_6 = seeker.should_apply('SNAP', month=6)
        can_apply_month_10 = seeker.should_apply('SNAP', month=10)
        
        assert can_apply_month_6 == False  # Banned
        assert can_apply_month_10 == False  # Still banned
        
        # Can apply after ban expires
        can_apply_month_11 = seeker.should_apply('SNAP', month=11)
        assert can_apply_month_11 == True  # Ban expired
    
    def test_repeat_offender_gets_longer_ban(self):
        """Test that repeat offenders get escalating bans."""
        seeker = Seeker(1, 'White', 15000, 'TEST', True, False, random_state=np.random.RandomState(42))
        
        # First offense: 6-month ban
        seeker.record_fraud_detection(month=0)
        assert seeker.is_banned_for_fraud(month=5) == True   # Still banned
        assert seeker.is_banned_for_fraud(month=6) == False  # Ban expired
        
        # Second offense: 12-month ban
        seeker.record_fraud_detection(month=7)
        assert seeker.is_banned_for_fraud(month=10) == True  # Banned
        assert seeker.is_banned_for_fraud(month=18) == True  # Still banned
        assert seeker.is_banned_for_fraud(month=19) == False # Expired
    
    def test_third_strike_permanent_ban(self):
        """Test three strikes and you're out."""
        seeker = Seeker(1, 'White', 15000, 'TEST', True, False, random_state=np.random.RandomState(42))
        
        # Three strikes
        seeker.record_fraud_detection(month=0)
        seeker.record_fraud_detection(month=7)
        seeker.record_fraud_detection(month=20)
        
        # Permanent ban
        assert seeker.fraud_flag == True
        assert seeker.is_banned_for_fraud(month=50) == True
        assert seeker.is_banned_for_fraud(month=100) == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])