"""
Evaluator agent - front-line caseworker who processes applications.

Responsibilities:
- Check basic eligibility
- Calculate suspicion scores
- Make initial decisions (approve/deny/escalate)
- Escalate complex or suspicious cases to Reviewer
"""

import numpy as np
from typing import Tuple


class Evaluator:
    """Front-line caseworker who processes benefit applications."""
    
    def __init__(self, evaluator_id, county, program, strictness=0.5, random_state=None):
        """
        Initialize an evaluator.
        
        Args:
            evaluator_id: Unique identifier
            county: County this evaluator works in
            program: Which program this evaluator handles ('SNAP', 'TANF', 'SSI')
            strictness: How strict in fraud detection (0.0-1.0)
            random_state: numpy RandomState for reproducibility
        """
        self.id = evaluator_id
        self.county = county
        self.program = program
        self.strictness = strictness
        self.rng = random_state if random_state else np.random.RandomState()
        
        # Performance tracking
        self.applications_processed = 0
        self.applications_approved = 0
        self.applications_denied = 0
        self.applications_escalated = 0
        
    def process_application(self, application, reviewer=None):
        """
        Process an application and make a decision.
        
        Args:
            application: Application object to process
            reviewer: Optional Reviewer object for escalation
            
        Returns:
            str: Decision ('APPROVED', 'DENIED', or 'ESCALATED')
        """
        self.applications_processed += 1
        
        # Step 1: Check basic eligibility
        eligible = self._check_eligibility(application)
        
        if not eligible:
            application.approved = False
            application.denial_reason = "Income too high"
            self.applications_denied += 1
            return "DENIED"
        
        # Step 2: Calculate suspicion score
        suspicion = self._calculate_suspicion(application)
        application.suspicion_score = suspicion
        
        # Step 3: Decide whether to escalate
        should_escalate = self._should_escalate(application, suspicion)
        
        if should_escalate and reviewer:
            application.escalated_to_reviewer = True
            self.applications_escalated += 1
            return "ESCALATED"
        
        # Step 4: Make decision based on suspicion
        if suspicion > self.strictness:
            application.investigated = True
            # For now, assume investigation reveals truth
            if application.is_fraud or application.is_error:
                application.approved = False
                application.denial_reason = "Failed verification"
                self.applications_denied += 1
                return "DENIED"
        
        # Approve if no issues found
        application.approved = True
        self.applications_approved += 1
        return "APPROVED"
    
    def _check_eligibility(self, application):
        """
        Check if applicant meets basic income requirements.
        
        Simplified eligibility rules:
        - SNAP: Income < 130% of poverty line (~$2,500/month for family of 2)
        - TANF: Income < 50% of poverty line (~$1,000/month for family of 2)
        - SSI: Income < $1,913/month + must have disability
        """
        monthly_income = application.reported_income / 12
        
        if application.program == 'SNAP':
            # Rough threshold: $2,500/month for household of 2
            threshold = 1250 * application.reported_household_size
            return monthly_income < threshold
            
        elif application.program == 'TANF':
            # More restrictive
            threshold = 500 * application.reported_household_size
            return monthly_income < threshold
            
        elif application.program == 'SSI':
            # Must have disability + low income
            return (application.reported_has_disability and 
                    monthly_income < 1913)
        
        return False
    
    def _calculate_suspicion(self, application):
        """
        Calculate suspicion score based on red flags.
        
        Red flags:
        - Very low reported income
        - Large household size
        - Multiple benefit applications (tracked elsewhere)
        
        Returns:
            float: Suspicion score (0.0 = not suspicious, 1.0 = very suspicious)
        """
        score = 0.0
        
        monthly_income = application.reported_income / 12
        
        # Red flag 1: Very low income (possible underreporting)
        if monthly_income < 1000:
            score += 0.3
        elif monthly_income < 2000:
            score += 0.1
        
        # Red flag 2: Large household (harder to verify)
        if application.reported_household_size >= 5:
            score += 0.2
        
        # Red flag 3: SSI without clear disability documentation
        if application.program == 'SSI':
            score += 0.3  # Always somewhat suspicious
        
        # Add random noise (evaluator judgment varies)
        noise = self.rng.normal(0, 0.1)
        score = max(0.0, min(1.0, score + noise))
        
        return score
    
    def _should_escalate(self, application, suspicion):
        """
        Decide whether to escalate to Reviewer.
        
        Escalate if:
        - Suspicion > 0.8 (very suspicious)
        - SSI application (disability verification needed)
        - Very large income discrepancy (if we could detect it)
        """
        # High suspicion
        if suspicion > 0.8:
            return True
        
        # SSI always needs specialist review (disability verification)
        if application.program == 'SSI':
            return True
        
        return False
    
    def get_approval_rate(self):
        """Calculate percentage of applications approved."""
        if self.applications_processed == 0:
            return 0.0
        return self.applications_approved / self.applications_processed
    
    def __repr__(self):
        return (f"Evaluator(id={self.id}, strictness={self.strictness:.2f}, "
                f"processed={self.applications_processed}, "
                f"approval_rate={self.get_approval_rate():.1%})")


if __name__ == "__main__":
    from application import Application
    
    # Create test applications
    rng = np.random.RandomState(42)
    
    honest_app = Application(
        application_id=1,
        seeker_id=101,
        program='SNAP',
        month=1,
        reported_income=30000,
        reported_household_size=2,
        reported_has_disability=False,
        true_income=30000,
        true_household_size=2,
        true_has_disability=False,
        is_fraud=False
    )
    
    fraud_app = Application(
        application_id=2,
        seeker_id=102,
        program='SNAP',
        month=1,
        reported_income=10000,  # Underreporting
        reported_household_size=2,
        reported_has_disability=False,
        true_income=50000,
        true_household_size=2,
        true_has_disability=False,
        is_fraud=True
    )
    
    ssi_app = Application(
        application_id=3,
        seeker_id=103,
        program='SSI',
        month=1,
        reported_income=18000,
        reported_household_size=1,
        reported_has_disability=True,
        true_income=18000,
        true_household_size=1,
        true_has_disability=True,
        is_fraud=False
    )
    
    # Test evaluator
    evaluator = Evaluator(1, strictness=0.5, random_state=rng)
    
    print("Processing Applications:\n")
    
    decision1 = evaluator.process_application(honest_app)
    print(f"Honest SNAP application:")
    print(f"  Decision: {decision1}")
    if honest_app.suspicion_score is not None:
        print(f"  Suspicion: {honest_app.suspicion_score:.2f}\n")
    else:
        print(f"  Suspicion: N/A (denied before scoring)\n")
    
    decision2 = evaluator.process_application(fraud_app)
    print(f"Fraudulent SNAP application:")
    print(f"  Decision: {decision2}")
    if fraud_app.suspicion_score is not None:
        print(f"  Suspicion: {fraud_app.suspicion_score:.2f}\n")
    else:
        print(f"  Suspicion: N/A\n")
    
    decision3 = evaluator.process_application(ssi_app)
    print(f"SSI application:")
    print(f"  Decision: {decision3}")
    if ssi_app.suspicion_score is not None:
        print(f"  Suspicion: {ssi_app.suspicion_score:.2f}\n")
    else:
        print(f"  Suspicion: N/A\n")
    
    print(f"Evaluator performance: {evaluator}")