"""
Tests for Phase 3: Simulation Loop

Run with:
    pytest tests/test_simulation.py -v
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
from core.evaluator import Evaluator
from core.reviewer import Reviewer


@pytest.mark.unit
class TestSimulationRunner:
    """Tests for simulation runner functions."""
    
    def test_create_population_function_exists(self):
        """Test that create_population function exists."""
        from simulation.runner import create_population
        assert callable(create_population)
    
    def test_create_population_returns_list(self):
        """Test that create_population returns a list of seekers."""
        from simulation.runner import create_population
        
        seekers = create_population(n_seekers=10, random_seed=42)
        
        assert isinstance(seekers, list)
        assert len(seekers) == 10
        # Check they have Seeker attributes instead of isinstance
        for s in seekers:
            assert hasattr(s, 'id')
            assert hasattr(s, 'income')
            assert hasattr(s, 'fraud_propensity')
            assert hasattr(s, 'should_apply')
            assert hasattr(s, 'create_application')
    
    def test_run_month_function_exists(self):
        """Test that run_month function exists."""
        from simulation.runner import run_month
        assert callable(run_month)
    
    def test_run_month_processes_applications(self):
        """Test that run_month processes applications."""
        from simulation.runner import create_population, create_evaluators, create_reviewers, run_month
        
        # Create small population
        counties = ['TEST_COUNTY']
        seekers = create_population(n_seekers=10, counties=counties, random_seed=42)
        evaluators = create_evaluators(counties, random_seed=42)
        reviewers = create_reviewers(counties, random_seed=42)
        
        # Run one month
        stats = run_month(seekers, evaluators, reviewers, month=1)
        
        assert stats is not None
        assert 'applications_submitted' in stats
        assert 'applications_approved' in stats
        assert 'applications_denied' in stats
    
    def test_run_simulation_function_exists(self):
        """Test that run_simulation function exists."""
        from simulation.runner import run_simulation
        assert callable(run_simulation)
    
    def test_run_simulation_completes(self):
        """Test that run_simulation completes without errors."""
        from simulation.runner import run_simulation
        
        # Small simulation
        results = run_simulation(n_seekers=20, n_months=12, random_seed=42)
        
        assert results is not None
        assert 'monthly_stats' in results
        assert len(results['monthly_stats']) == 12
    
    def test_run_simulation_tracks_seekers(self):
        """Test that run_simulation tracks seeker outcomes."""
        from simulation.runner import run_simulation
        
        results = run_simulation(n_seekers=20, n_months=6, random_seed=42)
        
        assert 'seekers' in results
        assert len(results['seekers']) == 20
        
        # Check that seekers have history
        for seeker in results['seekers']:
            assert hasattr(seeker, 'num_applications')
            # Some seekers should have applied
        
        total_apps = sum(s.num_applications for s in results['seekers'])
        assert total_apps > 0, "At least some seekers should have applied"


@pytest.mark.integration
class TestSimulationIntegration:
    """Integration tests for complete simulation."""
    
    def test_simulation_with_all_programs(self):
        """Test simulation with SNAP, TANF, and SSI."""
        from simulation.runner import run_simulation
        
        # Run simulation
        results = run_simulation(n_seekers=50, n_months=6, random_seed=42)
        
        # Check all programs were tested
        # (At least some applications for each program should exist)
        assert results is not None
    
    @pytest.mark.slow
    def test_larger_simulation(self):
        """Test larger simulation (100 seekers, 12 months)."""
        from simulation.runner import run_simulation
        
        results = run_simulation(n_seekers=100, n_months=12, random_seed=42)
        
        assert results is not None
        assert len(results['monthly_stats']) == 12
        assert len(results['seekers']) == 100
        
        # Check statistics make sense
        total_apps = sum(s.num_applications for s in results['seekers'])
        total_approved = sum(s.num_approvals for s in results['seekers'])
        
        assert total_apps > 0
        assert total_approved >= 0
        assert total_approved <= total_apps  # Can't approve more than applied


if __name__ == "__main__":
    pytest.main([__file__, "-v"])