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
            'description': 'Verify reported income against records',
            'has_contact': False  # Database check, no seeker interaction
        },
        'request_pay_stubs': {
            'cost': 3,
            'description': 'Request 3 months of pay stubs',
            'has_contact': False  # Paperwork request, minimal contact
        },
        'bank_statements': {
            'cost': 4,
            'description': 'Request bank account statements',
            'has_contact': False  # Document request
        },
        'employer_verification': {
            'cost': 3,
            'description': 'Contact employer directly',
            'has_contact': False  # Contact employer, not seeker
        },
        'interview': {
            'cost': 4,
            'description': 'Conduct phone or in-person interview',
            'has_contact': True  # DIRECT CONTACT - reviewer "hears" seeker
        },
        'medical_verification': {
            'cost': 6,
            'description': 'Verify disability documentation',
            'has_contact': False  # Medical records review
        },
        'household_verification': {
            'cost': 3,
            'description': 'Verify household composition',
            'has_contact': True  # Often involves phone call/interview
        },
        'home_visit': {
            'cost': 5,
            'description': 'Physical home visit',
            'has_contact': True  # IN-PERSON - reviewer "sees" seeker
        }
    }
    
    # Fraud penalty multiplier
    FRAUD_COST_MULTIPLIER = 2.0  # Fraudsters pay double (maintaining lies is hard)
    
    def __init__(self, reviewer_id, county=None, state=None, capacity=50, accuracy=0.85, 
                 mechanism_config=None, state_model=None, acs_data=None, random_state=None):
        """
        Initialize a reviewer.
        
        Args:
            reviewer_id: Unique identifier
            county: County this reviewer works in
            state: State this reviewer works in (for state-specific model)
            capacity: Maximum applications that can be reviewed per month (legacy)
            accuracy: Probability of detecting fraud (0.0-1.0)
            state_model: State-specific trained model (not national!)
            acs_data: ACS data for county lookups
            random_state: numpy RandomState for reproducibility
        """
        self.id = reviewer_id
        self.county = county
        self.state = state
        self.capacity = capacity  # Legacy - kept for compatibility
        self.accuracy = accuracy
        self.rng = random_state if random_state else np.random.RandomState()
        
        # === MECHANISM CONTROLS ===
        from core.mechanism_config import MechanismConfig
        
        # Default to full model if not specified
        if mechanism_config is None:
            mechanism_config = MechanismConfig.full_model()
        self.mechanism_config = mechanism_config
        
        # State model: Only store and use if discrimination mechanism enabled
        if self.mechanism_config.state_discrimination_enabled:
            self.state_model = state_model
        else:
            self.state_model = None  # Don't use even if provided
        # === END MECHANISM CONTROLS ===
        
        self.acs_data = acs_data
        
        # COUNTY-SPECIFIC PATTERN LEARNING (removed - too granular)
        # Now using state-level patterns instead
        
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
        
        NOW with CONTACT-BASED statistical discrimination:
        - Database checks: No bias (reviewer doesn't "see" seeker)
        - Interview/home visit: Statistical discrimination applied
        - Once assessed during contact, affects rest of investigation
        
        Returns:
            bool: True if fraud detected (points exhausted)
        """
        # Start with seeker's capacity
        remaining_points = seeker.bureaucracy_navigation_points
        
        # If bureaucracy mechanism disabled, points are None (unlimited)
        if remaining_points is None:
            # Always pass investigation when mechanism disabled
            return False
        
        # Track whether credibility has been assessed (during contact)
        credibility_assessed = False
        credibility_multiplier = 1.0
        
        # Select investigation actions
        actions = self._select_investigation_actions(application)
        
        # Perform each action
        for action_name in actions:
            action_info = self.INVESTIGATION_ACTIONS[action_name]
            base_cost = action_info['cost']
            has_contact = action_info['has_contact']
            
            # FRAUD PENALTY: Fraudsters pay double
            if application.is_fraud:
                actual_cost = base_cost * self.FRAUD_COST_MULTIPLIER
            else:
                actual_cost = base_cost
            
            # STATISTICAL DISCRIMINATION: Only during direct contact!
            if has_contact and not credibility_assessed:
                # First time reviewer "meets" seeker (phone call, home visit)
                # Forms impression based on STATE patterns
                credibility_multiplier = self._calculate_credibility_from_state_patterns(seeker)
                credibility_assessed = True
            
            # Once credibility assessed, affects THIS and SUBSEQUENT actions
            # (Reviewer's first impression colors rest of investigation)
            if credibility_assessed:
                actual_cost *= credibility_multiplier
            
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
    
    def _calculate_credibility_from_state_patterns(self, seeker):
        """
        Calculate credibility using STATE-specific patterns.
        
        All reviewers in Alabama: Use Alabama model
        All reviewers in California: Use California model
        
        Each state model captures:
        - State welfare policies (generous vs restrictive)
        - State demographic patterns
        - State economic conditions
        
        Returns:
            float: Investigation multiplier (0.8-1.3)
        """
        # If state discrimination mechanism disabled, always return neutral
        if not self.mechanism_config.state_discrimination_enabled:
            return 1.0
        
        if self.state_model is None or self.acs_data is None:
            return 1.0  # No model, neutral
        
        # Get county data
        county_data = self.acs_data[self.acs_data['county_name'] == seeker.county]
        if len(county_data) == 0:
            return 1.0
        
        county_data = county_data.iloc[0]
        
        # Extract features for state model
        features = []
        for feat in self.state_model['features']:
            if feat in county_data:
                features.append(county_data[feat])
            elif feat in self.acs_data.columns:
                features.append(self.acs_data[feat].median())
            else:
                features.append(0.0)
        
        # Predict using STATE model
        try:
            features_scaled = self.state_model['scaler'].transform([features])
            prob_high_need = self.state_model['model'].predict_proba(features_scaled)[0][1]
        except Exception:
            return 1.0
        
        # Convert to credibility multiplier
        if prob_high_need > 0.7:
            # County patterns (in this STATE) suggest high need
            return 0.8  # Easier investigation
        elif prob_high_need < 0.3:
            # County patterns (in this STATE) suggest low need
            return 1.3  # Harder investigation
        else:
            return 1.0  # Medium
    
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