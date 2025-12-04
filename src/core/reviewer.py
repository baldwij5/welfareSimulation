"""
Reviewer agent - supervisor/specialist who handles escalated cases.

Key differences from Evaluator:
- Higher accuracy in fraud detection
- More thorough investigation
- Limited capacity (can only handle X cases per month)
- Can override evaluator decisions
"""

import numpy as np


class Reviewer:
    """Supervisor who handles escalated benefit applications."""
    
    # Investigation action costs (bureaucracy points required)
    INVESTIGATION_ACTIONS = {
        'basic_income_check': {
            'cost': 2,
            'description': 'Verify reported income against records'
        },
        'request_pay_stubs': {
            'cost': 3,
            'description': 'Request 3 months of pay stubs'
        },
        'bank_statements': {
            'cost': 4,
            'description': 'Request bank account statements'
        },
        'employer_verification': {
            'cost': 3,
            'description': 'Contact employer directly'
        },
        'interview': {
            'cost': 4,
            'description': 'Conduct phone or in-person interview'
        },
        'medical_verification': {
            'cost': 6,
            'description': 'Verify disability documentation'
        },
        'household_verification': {
            'cost': 3,
            'description': 'Verify household composition'
        },
        'home_visit': {
            'cost': 5,
            'description': 'Physical home visit'
        }
    }
    
    # Fraud penalty multiplier
    FRAUD_COST_MULTIPLIER = 2.0  # Fraudsters pay double (maintaining lies is hard)
    
    def __init__(self, reviewer_id, capacity=50, accuracy=0.85, random_state=None):
        """
        Initialize a reviewer.
        
        Args:
            reviewer_id: Unique identifier
            capacity: Maximum applications that can be reviewed per month (legacy, unused)
            accuracy: Probability of detecting fraud (0.0-1.0)
            random_state: numpy RandomState for reproducibility
        """
        self.id = reviewer_id
        self.capacity = capacity  # Legacy - kept for compatibility
        self.accuracy = accuracy
        self.rng = random_state if random_state else np.random.RandomState()
        
        # Performance tracking
        self.applications_reviewed = 0
        self.applications_approved = 0
        self.applications_denied = 0
        self.fraud_detected = 0
        self.false_positives = 0  # Denied honest applications
        
        # Complexity-based capacity tracking
        self.monthly_capacity = 10.0  # Default complexity units, overridden by create_reviewers()
        self.capacity_used_this_month = 0.0
        self.current_month = 0
        self.reviewed_this_month = 0  # Legacy count
    
    def reset_monthly_capacity(self, month):
        """Reset capacity counter for new month."""
        self.current_month = month
        self.reviewed_this_month = 0
        self.capacity_used_this_month = 0.0  # Reset complexity units
    
    def can_review(self, application=None):
        """
        Check if reviewer has capacity to handle another case.
        
        Args:
            application: Optional Application with complexity score
            
        Returns:
            bool: True if has capacity
        """
        if application is None:
            # Legacy check - just count
            return self.reviewed_this_month < self.capacity
        
        # NEW: Complexity-based check
        if application.complexity is None:
            # No complexity score - use legacy count
            return self.reviewed_this_month < self.capacity
        
        # Check if enough complexity units remain
        remaining = self.monthly_capacity - self.capacity_used_this_month
        return application.complexity <= remaining
    
    def review_application(self, application, seeker=None):
        """
        Review an escalated application using bureaucracy navigation points system.
        
        Process:
        1. Select investigation actions based on suspicion/complexity
        2. Apply each action, deducting from seeker's bureaucracy points
        3. Fraudsters pay DOUBLE (maintaining lies is harder)
        4. If points drop below 0 → fraud detected
        5. If points remain positive after all checks → approved
        
        Args:
            application: Application object to review
            seeker: Seeker object (for bureaucracy points)
            
        Returns:
            str: Decision ('APPROVED', 'DENIED', or 'CAPACITY_EXCEEDED')
        """
        # Check capacity (complexity-aware)
        if not self.can_review(application):
            return "CAPACITY_EXCEEDED"
        
        # Use capacity (deduct complexity units)
        if application.complexity is not None:
            self.capacity_used_this_month += application.complexity
        
        # Track counts
        self.applications_reviewed += 1
        self.reviewed_this_month += 1
        
        # NEW: Bureaucracy points investigation (with history recording)
        if seeker is not None:
            # Record that investigation occurred
            seeker.record_investigation(self.current_month)
            
            # Conduct investigation
            fraud_detected = self._conduct_points_investigation(application, seeker)
        else:
            # Fallback to old probabilistic method if no seeker provided
            fraud_detected = self._probabilistic_detection(application)
        
        # Make decision based on detection
        if fraud_detected:
            application.approved = False
            application.denial_reason = "Failed investigation - unable to verify claims"
            application.investigated = True
            self.applications_denied += 1
            
            # Track false positives (denied honest error)
            if application.is_error and not application.is_fraud:
                self.false_positives += 1
            
            # Track fraud detection
            if application.is_fraud or application.is_error:
                self.fraud_detected += 1
            
            # NEW: Record fraud detection in seeker history
            if seeker and application.is_fraud:
                seeker.record_fraud_detection(self.current_month)
            
            # NEW: Record denial
            if seeker:
                reason = 'fraud' if application.is_fraud else 'verification_failed'
                seeker.record_denial(self.current_month, reason)
            
            return "DENIED"
        
        # Not detected - approve
        application.approved = True
        application.investigated = True
        self.applications_approved += 1
        
        return "APPROVED"
    
    def _conduct_points_investigation(self, application, seeker):
        """
        Conduct investigation using bureaucracy navigation points.
        
        Returns:
            bool: True if fraud detected (points exhausted)
        """
        # Start with seeker's capacity
        remaining_points = seeker.bureaucracy_navigation_points
        
        # Select investigation actions
        actions = self._select_investigation_actions(application)
        
        # Perform each action
        for action_name in actions:
            base_cost = self.INVESTIGATION_ACTIONS[action_name]['cost']
            
            # FRAUD PENALTY: Fraudsters pay double
            if application.is_fraud:
                actual_cost = base_cost * self.FRAUD_COST_MULTIPLIER
            else:
                actual_cost = base_cost
            
            # Deduct points
            remaining_points -= actual_cost
            
            # Check if fraud detected (points exhausted)
            if remaining_points < 0:
                # Seeker couldn't withstand scrutiny
                return True  # Fraud detected
        
        # Passed all checks
        return False  # Not detected
    
    def _select_investigation_actions(self, application):
        """
        Choose which investigation actions to perform.
        
        Based on:
        - Suspicion level (higher → more checks)
        - Application complexity (complex → more checks)
        - Program type (SSI → medical verification)
        
        Returns:
            list: Action names to perform (in order)
        """
        actions = []
        
        # Always start with basic income check
        actions.append('basic_income_check')
        
        # Suspicion-based escalation
        if application.suspicion_score > 0.5:
            actions.append('request_pay_stubs')
            actions.append('household_verification')
        
        if application.suspicion_score > 0.7:
            actions.append('bank_statements')
            actions.append('interview')
        
        if application.suspicion_score > 0.85:
            actions.append('employer_verification')
        
        # Program-specific actions
        if application.program == 'SSI' and application.reported_has_disability:
            actions.append('medical_verification')
        
        if application.program == 'TANF':
            actions.append('household_verification')  # Already added if suspicion > 0.5
        
        # Complexity-based
        if application.complexity and application.complexity > 0.8:
            # Very complex cases get home visit
            actions.append('home_visit')
        
        # Remove duplicates while preserving order
        seen = set()
        unique_actions = []
        for action in actions:
            if action not in seen:
                seen.add(action)
                unique_actions.append(action)
        
        return unique_actions
    
    def _probabilistic_detection(self, application):
        """
        Fallback probabilistic detection (old method).
        
        Used when seeker object not available.
        """
        if application.is_fraud or application.is_error:
            if self.rng.random() < self.accuracy:
                return True
        return False
    
    def get_approval_rate(self):
        """Calculate percentage of reviewed applications approved."""
        if self.applications_reviewed == 0:
            return 0.0
        return self.applications_approved / self.applications_reviewed
    
    def get_fraud_detection_rate(self):
        """Calculate percentage of fraud successfully detected."""
        if self.applications_reviewed == 0:
            return 0.0
        return self.fraud_detected / self.applications_reviewed
    
    def get_false_positive_rate(self):
        """Calculate percentage of honest applicants incorrectly denied."""
        if self.applications_reviewed == 0:
            return 0.0
        return self.false_positives / self.applications_reviewed
    
    def __repr__(self):
        return (f"Reviewer(id={self.id}, capacity={self.capacity}, "
                f"accuracy={self.accuracy:.1%}, "
                f"reviewed={self.applications_reviewed}, "
                f"approval_rate={self.get_approval_rate():.1%})")


if __name__ == "__main__":
    from application import Application
    
    # Create test applications
    rng = np.random.RandomState(42)
    
    # Create 100 applications (mix of honest and fraud)
    applications = []
    
    for i in range(100):
        is_fraud = i < 10  # 10% fraud rate
        true_income = rng.lognormal(np.log(50000), 0.8)
        
        if is_fraud:
            reported_income = true_income * 0.5  # Underreport by 50%
        else:
            reported_income = true_income
        
        app = Application(
            application_id=i,
            seeker_id=1000 + i,
            program='SNAP',
            month=1,
            reported_income=reported_income,
            reported_household_size=2,
            reported_has_disability=False,
            true_income=true_income,
            true_household_size=2,
            true_has_disability=False,
            is_fraud=is_fraud
        )
        applications.append(app)
    
    # Test reviewer
    reviewer = Reviewer(1, capacity=100, accuracy=0.85, random_state=rng)
    reviewer.reset_monthly_capacity(1)
    
    print("Reviewing 100 applications (10 fraud, 90 honest):\n")
    
    for app in applications:
        decision = reviewer.review_application(app)
    
    print(f"Reviewer Performance: {reviewer}")
    print(f"  Fraud detection rate: {reviewer.get_fraud_detection_rate():.1%}")
    print(f"  False positive rate: {reviewer.get_false_positive_rate():.1%}")
    print(f"  Capacity used: {reviewer.reviewed_this_month}/{reviewer.capacity}")