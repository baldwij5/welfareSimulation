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
    
    def __init__(self, reviewer_id, capacity=50, accuracy=0.85, random_state=None):
        """
        Initialize a reviewer.
        
        Args:
            reviewer_id: Unique identifier
            capacity: Maximum applications that can be reviewed per month
            accuracy: Probability of detecting fraud (0.0-1.0)
            random_state: numpy RandomState for reproducibility
        """
        self.id = reviewer_id
        self.capacity = capacity
        self.accuracy = accuracy
        self.rng = random_state if random_state else np.random.RandomState()
        
        # Performance tracking
        self.applications_reviewed = 0
        self.applications_approved = 0
        self.applications_denied = 0
        self.fraud_detected = 0
        self.false_positives = 0  # Denied honest applications
        
        # Monthly capacity tracking
        self.current_month = 0
        self.reviewed_this_month = 0
    
    def reset_monthly_capacity(self, month):
        """Reset capacity counter for new month."""
        self.current_month = month
        self.reviewed_this_month = 0
    
    def can_review(self):
        """Check if reviewer has capacity to handle another case."""
        return self.reviewed_this_month < self.capacity
    
    def review_application(self, application):
        """
        Review an escalated application with higher scrutiny.
        
        Args:
            application: Application object to review
            
        Returns:
            str: Decision ('APPROVED' or 'DENIED')
        """
        if not self.can_review():
            # If at capacity, return to evaluator (shouldn't happen with proper logic)
            return "CAPACITY_EXCEEDED"
        
        self.applications_reviewed += 1
        self.reviewed_this_month += 1
        
        # Step 1: Thorough investigation (reveals truth with probability = accuracy)
        fraud_detected = False
        
        if application.is_fraud or application.is_error:
            # There IS something wrong - can reviewer detect it?
            if self.rng.random() < self.accuracy:
                fraud_detected = True
                self.fraud_detected += 1
        
        # Step 2: Make decision
        if fraud_detected:
            application.approved = False
            application.denial_reason = "Detected fraud/error in review"
            application.investigated = True
            self.applications_denied += 1
            
            # Track false positives (denied an honest error, not intentional fraud)
            if application.is_error and not application.is_fraud:
                self.false_positives += 1
            
            return "DENIED"
        
        # Step 3: If no fraud detected, approve
        # (Could still be fraud that slipped through)
        application.approved = True
        application.investigated = True
        self.applications_approved += 1
        
        return "APPROVED"
    
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