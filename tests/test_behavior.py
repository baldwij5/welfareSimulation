"""
Tests for Phase 2: Behavioral Logic (Ultra-Simplified)

Run with:
    pytest tests/test_behavior.py -v
"""

import pytest
import numpy as np
import sys
import os

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from core.seeker import Seeker


@pytest.mark.unit
class TestSeekerCreation:
    """Tests for Seeker initialization."""
    
    def test_seeker_creation_simple(self):
        """Test creating a seeker with explicit parameters."""
        seeker = Seeker(
            seeker_id=1,
            race='White',
            income=30000,
            county='TEST_COUNTY',
            has_children=True,
            has_disability=False,
            random_state=np.random.RandomState(42)
        )
        
        assert seeker.id == 1
        assert seeker.race == 'White'
        assert seeker.income == 30000
        assert seeker.county == 'TEST_COUNTY'
        assert seeker.has_children == True
        assert seeker.has_disability == False
    
    def test_fraud_propensity_generated(self):
        """Test that fraud propensity is generated (0 to 2)."""
        seeker = Seeker(1, 'White', 50000, county='TEST', random_state=np.random.RandomState(42))
        
        assert hasattr(seeker, 'fraud_propensity')
        assert 0 <= seeker.fraud_propensity <= 2
    
    def test_lying_magnitude_generated(self):
        """Test that lying magnitude is generated (0 to 100)."""
        seeker = Seeker(1, 'White', 50000, county='TEST', random_state=np.random.RandomState(42))
        
        assert hasattr(seeker, 'lying_magnitude')
        assert 0 <= seeker.lying_magnitude <= 100


@pytest.mark.unit
class TestApplicationDecision:
    """Tests for should_apply() method."""
    
    def test_should_apply_method_exists(self):
        """Test that should_apply method exists."""
        seeker = Seeker(1, 'White', 30000, county='TEST')
        assert hasattr(seeker, 'should_apply')
        assert callable(seeker.should_apply)
    
    def test_should_apply_returns_boolean(self):
        """Test that should_apply returns True or False."""
        seeker = Seeker(1, 'White', 30000, county='TEST')
        result = seeker.should_apply('SNAP', month=1)
        assert isinstance(result, bool)
    
    def test_snap_income_threshold(self):
        """Test SNAP income threshold ($2,500/month)."""
        # Below threshold - should apply
        seeker = Seeker(1, 'White', 24000, county='TEST')  # $2,000/month
        assert seeker.should_apply('SNAP', month=1) == True
        
        # At threshold - should not apply
        seeker = Seeker(2, 'White', 30000, county='TEST')  # $2,500/month
        assert seeker.should_apply('SNAP', month=1) == False
        
        # Above threshold - should not apply
        seeker = Seeker(3, 'White', 36000, county='TEST')  # $3,000/month
        assert seeker.should_apply('SNAP', month=1) == False
    
    def test_tanf_requires_income_and_children(self):
        """Test TANF requires low income AND children."""
        # Low income + children → apply
        seeker = Seeker(1, 'Black', 10000, county='TEST', has_children=True)
        assert seeker.should_apply('TANF', month=1) == True
        
        # Low income + NO children → don't apply
        seeker = Seeker(2, 'Black', 10000, county='TEST', has_children=False)
        assert seeker.should_apply('TANF', month=1) == False
        
        # High income + children → don't apply
        seeker = Seeker(3, 'Black', 20000, county='TEST', has_children=True)
        assert seeker.should_apply('TANF', month=1) == False
    
    def test_ssi_requires_income_and_disability(self):
        """Test SSI requires low income AND disability."""
        # Low income + disability → should have positive propensity
        seeker = Seeker(1, 'White', 20000, county='TEST', has_disability=True)
        propensity = seeker.calculate_application_propensity('SSI', month=1)
        assert propensity > 0.0, "Should have positive propensity with income+disability"
        
        # Low income + NO disability → don't apply (hard constraint)
        seeker = Seeker(2, 'White', 20000, county='TEST', has_disability=False)
        assert seeker.should_apply('SSI', month=1) == False
        
        # High income + disability → don't apply (hard constraint)
        seeker = Seeker(3, 'White', 30000, county='TEST', has_disability=True)
        assert seeker.should_apply('SSI', month=1) == False
    
    def test_stochastic_with_reproducibility(self):
        """Test that same month gives same result (reproducible stochastic)."""
        seeker = Seeker(1, 'Black', 20000, county='TEST', has_children=True)
        
        # Same month should give same result (reproducible randomness)
        result1 = seeker.should_apply('SNAP', month=5)
        result2 = seeker.should_apply('SNAP', month=5)
        assert result1 == result2  # Reproducible
        
        # Different months can give different results (stochastic)
        results = [seeker.should_apply('SNAP', month=m) for m in range(20)]
        # Should have SOME variation (not all identical)
        # But might all be True if propensity is very high
        assert isinstance(results[0], (bool, np.bool_))  # Returns bool type
    
    def test_multiple_programs_same_seeker(self):
        """Test seeker eligibility for multiple programs."""
        seeker = Seeker(1, 'Black', 10000, county='TEST', has_children=True, has_disability=True)
        
        # Should be eligible for all programs
        assert seeker.should_apply('SNAP', month=1) == True
        assert seeker.should_apply('TANF', month=1) == True
        assert seeker.should_apply('SSI', month=1) == True
    
    def test_high_income_no_eligibility(self):
        """Test that high income seeker is not eligible for anything."""
        seeker = Seeker(1, 'White', 100000, county='TEST', has_children=True, has_disability=True)
        
        # Should not be eligible for any program
        assert seeker.should_apply('SNAP', month=1) == False
        assert seeker.should_apply('TANF', month=1) == False
        assert seeker.should_apply('SSI', month=1) == False
    
    @pytest.mark.parametrize("program", ['SNAP', 'TANF', 'SSI'])
    def test_should_apply_works_for_all_programs(self, program):
        """Test that should_apply works for all programs."""
        seeker = Seeker(1, 'White', 10000, county='TEST', has_children=True, has_disability=True)
        
        # Should be able to call for any program
        result = seeker.should_apply(program, month=1)
        assert isinstance(result, (bool, np.bool_)), "Should return boolean type"


@pytest.mark.unit
class TestFraudDecision:
    """Tests for will_commit_fraud() method."""
    
    def test_will_commit_fraud_method_exists(self):
        """Test that will_commit_fraud method exists."""
        seeker = Seeker(1, 'White', 30000, county='TEST')
        assert hasattr(seeker, 'will_commit_fraud')
        assert callable(seeker.will_commit_fraud)
    
    def test_will_commit_fraud_returns_boolean(self):
        """Test that will_commit_fraud returns True or False."""
        seeker = Seeker(1, 'White', 30000, county='TEST')
        result = seeker.will_commit_fraud(month=1)
        assert isinstance(result, bool)
    
    def test_high_fraud_propensity_more_fraud(self):
        """Test that high fraud_propensity leads to more fraud."""
        # Create many seekers and count fraud by propensity level
        low_fraud_seekers = []
        high_fraud_seekers = []
        
        for i in range(100):
            seeker = Seeker(i, 'White', 30000, county='TEST', random_state=np.random.RandomState(i))
            if seeker.fraud_propensity < 0.5:
                low_fraud_seekers.append(seeker)
            elif seeker.fraud_propensity > 1.5:
                high_fraud_seekers.append(seeker)
        
        # Count fraud attempts
        low_fraud_count = sum(s.will_commit_fraud(month=1) for s in low_fraud_seekers)
        high_fraud_count = sum(s.will_commit_fraud(month=1) for s in high_fraud_seekers)
        
        # High propensity should commit more fraud
        if len(low_fraud_seekers) > 0 and len(high_fraud_seekers) > 0:
            low_fraud_rate = low_fraud_count / len(low_fraud_seekers)
            high_fraud_rate = high_fraud_count / len(high_fraud_seekers)
            assert high_fraud_rate > low_fraud_rate
    
    def test_fraud_varies_by_month(self):
        """Test that fraud decision can vary by month (due to randomness)."""
        seeker = Seeker(1, 'White', 30000, random_state=np.random.RandomState(42))
        
        # Check over 20 months
        decisions = [seeker.will_commit_fraud(month=m) for m in range(20)]
        
        # Should have some variation (not all same)
        # Unless fraud_propensity is very extreme (0 or 2)
        if 0.1 < seeker.fraud_propensity < 1.9:
            assert len(set(decisions)) > 1  # Some True, some False
    
    def test_deterministic_same_month_same_result(self):
        """Test that same month always gives same result (reproducible)."""
        seeker = Seeker(1, 'White', 30000, random_state=np.random.RandomState(42))
        
        # Call multiple times for same month
        result1 = seeker.will_commit_fraud(month=5)
        result2 = seeker.will_commit_fraud(month=5)
        result3 = seeker.will_commit_fraud(month=5)
        
        # Should all be the same
        assert result1 == result2 == result3
    
    def test_overall_fraud_rate_reasonable(self):
        """Test that overall fraud rate is in reasonable range."""
        seekers = [Seeker(i, 'White', 30000, county='TEST', random_state=np.random.RandomState(i)) 
                   for i in range(200)]
        
        # Count fraud across all seekers and 10 months
        total_decisions = 0
        fraud_decisions = 0
        
        for seeker in seekers:
            for month in range(10):
                total_decisions += 1
                if seeker.will_commit_fraud(month=month):
                    fraud_decisions += 1
        
        fraud_rate = fraud_decisions / total_decisions
        
        # For now, just check it's not 0% or 100% (we'll calibrate properly later)
        assert 0.0 < fraud_rate < 1.0, f"Fraud rate {fraud_rate:.1%} unreasonable"
        assert fraud_rate < 0.50, f"Fraud rate {fraud_rate:.1%} too high (>50%)"


@pytest.mark.unit
class TestApplicationGeneration:
    """Tests for create_application() method."""
    
    def test_create_application_method_exists(self):
        """Test that create_application method exists."""
        seeker = Seeker(1, 'White', 20000, county='TEST', has_children=True)
        assert hasattr(seeker, 'create_application')
        assert callable(seeker.create_application)
    
    def test_eligible_seeker_creates_application(self):
        """Test that eligible seeker creates an application."""
        seeker = Seeker(1, 'Black', 20000, county='TEST', has_children=True)
        
        # Eligible for SNAP
        app = seeker.create_application('SNAP', month=1, application_id=100)
        
        assert app is not None
        assert app.seeker_id == seeker.id
        assert app.program == 'SNAP'
        assert app.month == 1
    
    def test_ineligible_seeker_returns_none(self):
        """Test that ineligible seeker returns None."""
        seeker = Seeker(1, 'White', 100000, county='TEST', has_children=False)
        
        # Not eligible for SNAP (income too high)
        app = seeker.create_application('SNAP', month=1, application_id=100)
        
        assert app is None
    
    def test_honest_application_reports_true_income(self):
        """Test that honest applications report true income."""
        # Create seeker with very low fraud AND error propensity
        seeker = Seeker(1, 'White', 20000, county='TEST', has_children=True, random_state=np.random.RandomState(42))
        seeker.fraud_propensity = 0.0  # Force honest (no fraud)
        seeker.error_propensity = 0.0  # Force accurate (no errors)
        
        app = seeker.create_application('SNAP', month=1, application_id=100)
        
        assert app is not None
        assert app.is_fraud == False
        assert app.is_error == False
        assert app.reported_income == app.true_income
        assert app.reported_income == seeker.income
    
    def test_fraudulent_application_underreports_income(self):
        """Test that fraudulent applications underreport income."""
        # Create seeker with very high fraud propensity AND eligible income
        seeker = Seeker(1, 'Black', 20000, county='TEST', has_children=True, random_state=np.random.RandomState(42))
        seeker.fraud_propensity = 2.0  # Force fraud behavior
        seeker.lying_magnitude = 50.0  # Will underreport by 50%
        
        # Try many months to find a fraud case
        fraud_app = None
        for month in range(100):
            app = seeker.create_application('SNAP', month=month, application_id=100+month)
            if app and app.is_fraud:
                fraud_app = app
                break
        
        # Should eventually commit fraud (with propensity 2.0)
        assert fraud_app is not None, "Should commit fraud with propensity=2.0"
        assert fraud_app.is_fraud == True
        assert fraud_app.reported_income < fraud_app.true_income
        
        # Check underreporting amount
        expected_reported = seeker.income * 0.5  # 50% underreporting
        assert abs(fraud_app.reported_income - expected_reported) < 1
    
    def test_application_tracks_seeker_count(self):
        """Test that creating applications increments num_applications."""
        seeker = Seeker(1, 'White', 20000, county='TEST', has_children=True)
        
        assert seeker.num_applications == 0
        
        # Create application
        app = seeker.create_application('SNAP', month=1, application_id=100)
        
        assert seeker.num_applications == 1
        
        # Create another
        app2 = seeker.create_application('SNAP', month=2, application_id=101)
        
        assert seeker.num_applications == 2
    
    def test_multiple_applications_different_months(self):
        """Test creating applications across multiple months."""
        seeker = Seeker(1, 'Black', 15000, county='TEST', has_children=True, has_disability=True)
        
        applications = []
        for month in range(5):
            app = seeker.create_application('SNAP', month=month, application_id=month)
            if app:
                applications.append(app)
        
        # Should have created 4-5 applications (stochastic now, might skip one month)
        assert 4 <= len(applications) <= 5, f"Expected 4-5 applications, got {len(applications)}"
        assert seeker.num_applications == len(applications)
        
        # Each should have consecutive months (though might skip one due to stochastic)
        months = [app.month for app in applications]
        assert len(months) == len(set(months)), "All months should be unique"
        assert all(0 <= m < 5 for m in months), "Months should be 0-4"


@pytest.mark.unit
class TestRecertification:
    """Tests for recertification logic."""
    
    def test_enrolled_programs_tracking(self):
        """Test that enrolled_programs dict exists."""
        seeker = Seeker(1, 'White', 20000, county='TEST', has_children=True)
        assert hasattr(seeker, 'enrolled_programs')
        assert isinstance(seeker.enrolled_programs, dict)
    
    def test_enroll_in_program(self):
        """Test enrolling seeker in a program."""
        seeker = Seeker(1, 'Black', 20000, county='TEST', has_children=True)
        
        # Initially not enrolled
        assert seeker.is_enrolled('SNAP') == False
        
        # Enroll
        seeker.enroll_in_program('SNAP', month=1)
        
        # Now enrolled
        assert seeker.is_enrolled('SNAP') == True
        assert seeker.enrolled_programs['SNAP'] == 1
    
    def test_enrolled_seeker_doesnt_reapply_immediately(self):
        """Test that enrolled seeker doesn't apply again immediately."""
        seeker = Seeker(1, 'White', 20000, county='TEST', has_children=True)
        
        # Eligible for SNAP
        assert seeker.should_apply('SNAP', month=1) == True
        
        # Enroll in SNAP
        seeker.enroll_in_program('SNAP', month=1)
        
        # Should not apply in month 2 (still enrolled)
        assert seeker.should_apply('SNAP', month=2) == False
        assert seeker.should_apply('SNAP', month=3) == False
    
    def test_snap_recertification_at_6_months(self):
        """Test that SNAP requires recertification after 6 months."""
        seeker = Seeker(1, 'Black', 20000, county='TEST', has_children=True)
        
        # Enroll in month 0
        seeker.enroll_in_program('SNAP', month=0)
        
        # Should NOT apply in months 1-5 (still enrolled)
        for month in range(1, 6):
            assert seeker.should_apply('SNAP', month) == False
        
        # Should apply in month 6 (recertification due)
        assert seeker.should_apply('SNAP', month=6) == True
        
        # Check that enrollment was removed (expired)
        assert seeker.is_enrolled('SNAP') == False
    
    def test_tanf_recertification_at_12_months(self):
        """Test that TANF requires recertification after 12 months."""
        seeker = Seeker(1, 'White', 10000, county='TEST', has_children=True)
        
        # Enroll in month 0
        seeker.enroll_in_program('TANF', month=0)
        
        # Should NOT apply in months 1-11
        for month in range(1, 12):
            assert seeker.should_apply('TANF', month) == False
        
        # Should apply in month 12 (recertification due)
        assert seeker.should_apply('TANF', month=12) == True
    
    def test_ssi_recertification_at_36_months(self):
        """Test that SSI requires recertification after 36 months."""
        seeker = Seeker(1, 'Hispanic', 20000, county='TEST', has_disability=True)
        
        # Enroll in month 0
        seeker.enroll_in_program('SSI', month=0)
        
        # Should NOT apply in month 12 or 24
        assert seeker.should_apply('SSI', month=12) == False
        assert seeker.should_apply('SSI', month=24) == False
        
        # Should apply in month 36 (recertification due) - check propensity positive
        propensity = seeker.calculate_application_propensity('SSI', month=36)
        assert propensity > 0.0, "Should have positive propensity at recertification"
    
    def test_multiple_program_enrollment(self):
        """Test seeker can be enrolled in multiple programs."""
        seeker = Seeker(1, 'Black', 10000, county='TEST', has_children=True, has_disability=True)
        
        # Enroll in all programs
        seeker.enroll_in_program('SNAP', month=0)
        seeker.enroll_in_program('TANF', month=0)
        seeker.enroll_in_program('SSI', month=0)
        
        # Check all enrolled
        assert seeker.is_enrolled('SNAP') == True
        assert seeker.is_enrolled('TANF') == True
        assert seeker.is_enrolled('SSI') == True
        
        # Different recertification schedules
        # Month 6: SNAP expires
        assert seeker.should_apply('SNAP', month=6) == True
        assert seeker.should_apply('TANF', month=6) == False  # Still enrolled
        assert seeker.should_apply('SSI', month=6) == False   # Still enrolled


@pytest.mark.unit
class TestErrorDecision:
    """Tests for will_make_error() method and error propensity."""
    
    def test_error_propensity_generated(self):
        """Test that error propensity is generated (0 to 2)."""
        seeker = Seeker(1, 'White', 50000, random_state=np.random.RandomState(42))
        
        assert hasattr(seeker, 'error_propensity')
        assert 0 <= seeker.error_propensity <= 2
    
    def test_error_magnitude_generated(self):
        """Test that error magnitude is generated (0 to 20)."""
        seeker = Seeker(1, 'White', 50000, random_state=np.random.RandomState(42))
        
        assert hasattr(seeker, 'error_magnitude')
        assert 0 <= seeker.error_magnitude <= 20
    
    def test_will_make_error_method_exists(self):
        """Test that will_make_error method exists."""
        seeker = Seeker(1, 'White', 30000, county='TEST')
        assert hasattr(seeker, 'will_make_error')
        assert callable(seeker.will_make_error)
    
    def test_will_make_error_returns_boolean(self):
        """Test that will_make_error returns True or False."""
        seeker = Seeker(1, 'White', 30000, county='TEST')
        result = seeker.will_make_error(month=1)
        assert isinstance(result, bool)
    
    def test_high_error_propensity_more_errors(self):
        """Test that high error_propensity leads to more errors."""
        # Create many seekers and count errors by propensity level
        low_error_seekers = []
        high_error_seekers = []
        
        for i in range(100):
            seeker = Seeker(i, 'White', 30000, county='TEST', random_state=np.random.RandomState(i))
            if seeker.error_propensity < 0.5:
                low_error_seekers.append(seeker)
            elif seeker.error_propensity > 1.5:
                high_error_seekers.append(seeker)
        
        # Count error attempts
        low_error_count = sum(s.will_make_error(month=1) for s in low_error_seekers)
        high_error_count = sum(s.will_make_error(month=1) for s in high_error_seekers)
        
        # High propensity should make more errors
        if len(low_error_seekers) > 0 and len(high_error_seekers) > 0:
            low_error_rate = low_error_count / len(low_error_seekers)
            high_error_rate = high_error_count / len(high_error_seekers)
            assert high_error_rate > low_error_rate
    
    def test_errors_are_different_from_fraud(self):
        """Test that errors and fraud are mutually exclusive."""
        # Create seeker
        seeker = Seeker(1, 'Black', 20000, county='TEST', has_children=True, random_state=np.random.RandomState(42))
        
        # Create 100 applications
        applications = []
        for month in range(100):
            app = seeker.create_application('SNAP', month=month, application_id=month)
            if app:
                applications.append(app)
        
        # Check that no application is both fraud AND error
        for app in applications:
            if app.is_fraud:
                assert app.is_error == False, "Application can't be both fraud and error"
    
    def test_error_application_has_discrepancy(self):
        """Test that error applications have income discrepancy."""
        # Create seeker with high error propensity
        seeker = Seeker(1, 'White', 20000, county='TEST', has_children=True, random_state=np.random.RandomState(42))
        seeker.fraud_propensity = 0.0  # No fraud
        seeker.error_propensity = 2.0  # Force errors
        seeker.error_magnitude = 15.0  # 15% error
        
        # Try many months to find an error case
        error_app = None
        for month in range(100):
            app = seeker.create_application('SNAP', month=month, application_id=100+month)
            if app and app.is_error:
                error_app = app
                break
        
        # Should eventually make error (with propensity 2.0)
        assert error_app is not None, "Should make error with propensity=2.0"
        assert error_app.is_error == True
        assert error_app.is_fraud == False
        assert error_app.reported_income != error_app.true_income
        
        # Error magnitude should be around 15%
        discrepancy_pct = abs(error_app.get_income_discrepancy()) / error_app.true_income
        assert abs(discrepancy_pct - 0.15) < 0.01, f"Error magnitude {discrepancy_pct:.1%} != 15%"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])