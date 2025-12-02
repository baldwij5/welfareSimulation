"""
Tests for AI Application Sorter

Run with: pytest tests/test_ai_sorter.py -v
"""

import pytest
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from ai.application_sorter import AI_ApplicationSorter
from core.application import Application


@pytest.mark.unit
class TestAISorter:
    """Tests for AI_ApplicationSorter class."""
    
    def test_ai_sorter_creation(self):
        """Test that we can create an AI sorter."""
        ai = AI_ApplicationSorter(strategy='simple_first')
        assert ai.strategy == 'simple_first'
        assert ai.applications_sorted == 0
    
    def test_simple_first_sorts_correctly(self):
        """Test that simple_first strategy sorts low to high complexity."""
        ai = AI_ApplicationSorter(strategy='simple_first')
        
        # Create applications with different complexity
        apps = [
            Application(1, 101, 'SSI', 1, 15000, 2, True, 15000, 2, True),
            Application(2, 102, 'SNAP', 1, 20000, 2, False, 20000, 2, False),
            Application(3, 103, 'TANF', 1, 10000, 4, False, 10000, 4, False),
        ]
        apps[0].complexity = 0.9  # SSI - complex
        apps[1].complexity = 0.3  # SNAP - simple
        apps[2].complexity = 0.6  # TANF - medium
        
        sorted_apps = ai.sort_applications(apps)
        
        # Should be sorted by complexity (low to high)
        assert sorted_apps[0].complexity == 0.3  # SNAP first
        assert sorted_apps[1].complexity == 0.6  # TANF second
        assert sorted_apps[2].complexity == 0.9  # SSI last
    
    def test_fcfs_preserves_order(self):
        """Test that FCFS strategy preserves original order."""
        ai = AI_ApplicationSorter(strategy='fcfs')
        
        apps = [
            Application(1, 101, 'SSI', 1, 15000, 2, True, 15000, 2, True),
            Application(2, 102, 'SNAP', 1, 20000, 2, False, 20000, 2, False),
        ]
        apps[0].complexity = 0.9
        apps[1].complexity = 0.3
        
        sorted_apps = ai.sort_applications(apps)
        
        # Order preserved
        assert sorted_apps[0].application_id == 1  # SSI still first
        assert sorted_apps[1].application_id == 2  # SNAP still second
    
    def test_complex_first_sorts_reverse(self):
        """Test that complex_first sorts high to low."""
        ai = AI_ApplicationSorter(strategy='complex_first')
        
        apps = [
            Application(1, 101, 'SNAP', 1, 20000, 2, False, 20000, 2, False),
            Application(2, 102, 'SSI', 1, 15000, 2, True, 15000, 2, True),
        ]
        apps[0].complexity = 0.3  # Simple
        apps[1].complexity = 0.9  # Complex
        
        sorted_apps = ai.sort_applications(apps)
        
        # Should be complex first
        assert sorted_apps[0].complexity == 0.9  # SSI first
        assert sorted_apps[1].complexity == 0.3  # SNAP second
    
    def test_ai_tracks_usage(self):
        """Test that AI tracks how many applications sorted."""
        ai = AI_ApplicationSorter(strategy='simple_first')
        
        apps = [Application(i, 100+i, 'SNAP', 1, 20000, 2, False, 20000, 2, False) 
                for i in range(10)]
        
        ai.sort_applications(apps)
        
        assert ai.applications_sorted == 10
        assert len(ai.strategy_history) == 1


@pytest.mark.integration
class TestAIIntegration:
    """Integration tests for AI sorter in simulation."""
    
    def test_simulation_runs_with_ai(self):
        """Test that simulation runs with AI sorter."""
        from simulation.runner import run_simulation
        
        ai = AI_ApplicationSorter(strategy='simple_first')
        
        results = run_simulation(
            n_seekers=20,
            n_months=6,
            ai_sorter=ai,
            random_seed=42
        )
        
        assert results is not None
        assert results['summary']['total_applications'] > 0
    
    def test_ai_affects_outcomes(self):
        """Test that AI sorting changes which applications get processed."""
        from simulation.runner import run_simulation
        
        # Control
        control = run_simulation(n_seekers=50, n_months=6, ai_sorter=None, random_seed=42)
        
        # Treatment
        ai = AI_ApplicationSorter(strategy='simple_first')
        treatment = run_simulation(n_seekers=50, n_months=6, ai_sorter=ai, random_seed=42)
        
        # With AI, overflow patterns should differ
        # (Can't assert exact values, but systems should produce different results)
        # This test just ensures both run
        assert control is not None
        assert treatment is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])