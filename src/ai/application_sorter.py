"""
AI Application Sorter - Automated triage tool

Sorts applications by complexity to "maximize efficiency."

Marketed as: "Process more applications by handling simple cases first"
Actual effect: Systematically delays complex cases, creating disparate impact
when capacity constraints exist.
"""

import random as random_module


class AI_ApplicationSorter:
    """
    AI tool that automatically sorts/prioritizes applications.
    
    This represents common "efficiency AI" tools being deployed in
    public administration to improve throughput.
    
    Key insight: Even facially-neutral AI can amplify inequality through
    interaction with capacity constraints and structural factors.
    """
    
    def __init__(self, strategy='simple_first', random_seed=None):
        """
        Initialize AI sorting tool.
        
        Args:
            strategy: Sorting strategy
                - 'simple_first': Low to high complexity (efficiency-focused)
                - 'complex_first': High to low complexity (equity-focused?)
                - 'random': Random shuffle (fairness)
                - 'need_based': Lowest income first (equity)
                - 'fcfs': No sorting, preserve order (baseline)
            random_seed: For reproducible random sorting
        """
        self.strategy = strategy
        self.name = f"ApplicationSorter AI v1.0 (strategy: {strategy})"
        self.random_seed = random_seed
        
        # Track what AI has done
        self.applications_sorted = 0
        self.strategy_history = []
    
    def sort_applications(self, applications, seekers_dict=None):
        """
        Sort applications according to AI strategy.
        
        Args:
            applications: List of Application objects
            seekers_dict: Optional dict {seeker_id: Seeker} for need-based sorting
            
        Returns:
            list: Sorted applications
        """
        if len(applications) == 0:
            return applications
        
        self.applications_sorted += len(applications)
        self.strategy_history.append({
            'count': len(applications),
            'strategy': self.strategy
        })
        
        if self.strategy == 'simple_first':
            # Sort by complexity (low to high)
            # "Process simple cases first for efficiency"
            return sorted(applications, 
                         key=lambda app: app.complexity if app.complexity else 0.5)
        
        elif self.strategy == 'complex_first':
            # Sort by complexity (high to low)
            # "Handle difficult cases when staff is fresh"
            return sorted(applications,
                         key=lambda app: app.complexity if app.complexity else 0.5,
                         reverse=True)
        
        elif self.strategy == 'random':
            # Random shuffle (fairness through lottery)
            shuffled = applications.copy()
            if self.random_seed is not None:
                random_module.Random(self.random_seed).shuffle(shuffled)
            else:
                random_module.shuffle(shuffled)
            return shuffled
        
        elif self.strategy == 'need_based' and seekers_dict:
            # Sort by income (lowest first)
            # "Serve the neediest first"
            def get_income(app):
                seeker = seekers_dict.get(app.seeker_id)
                if seeker:
                    return seeker.income
                return 999999  # Unknown, put at end
            
            return sorted(applications, key=get_income)
        
        elif self.strategy == 'fcfs':
            # First-come, first-served (no sorting)
            return applications
        
        else:
            # Default: preserve order
            return applications
    
    def get_stats(self):
        """Get AI tool usage statistics."""
        return {
            'name': self.name,
            'strategy': self.strategy,
            'applications_sorted': self.applications_sorted,
            'batches_processed': len(self.strategy_history)
        }
    
    def __repr__(self):
        return f"AI_ApplicationSorter(strategy='{self.strategy}', sorted={self.applications_sorted})"


if __name__ == "__main__":
    # Test the AI sorter
    from core.application import Application
    
    # Create sample applications with different complexity
    apps = [
        Application(1, 101, 'SSI', 1, 15000, 2, True, 15000, 2, True),
        Application(2, 102, 'SNAP', 1, 20000, 2, False, 20000, 2, False),
        Application(3, 103, 'TANF', 1, 10000, 4, False, 10000, 4, False),
    ]
    
    # Set complexity scores
    apps[0].complexity = 0.9  # SSI - complex
    apps[1].complexity = 0.3  # SNAP - simple
    apps[2].complexity = 0.6  # TANF - medium
    
    print("Original order:")
    for app in apps:
        print(f"  {app.program}: {app.complexity}")
    
    # Sort with AI
    ai = AI_ApplicationSorter(strategy='simple_first')
    sorted_apps = ai.sort_applications(apps)
    
    print("\nAI sorted order (simple first):")
    for app in sorted_apps:
        print(f"  {app.program}: {app.complexity}")
    
    print(f"\n{ai}")