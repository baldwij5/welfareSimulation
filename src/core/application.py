"""
Application - data structure representing a benefit application.

Contains both reported characteristics (what the seeker claims) and
true characteristics (ground truth, only visible to simulation).
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Application:
    """
    Represents a welfare benefit application.
    
    Attributes:
        application_id: Unique identifier
        seeker_id: ID of the person applying
        program: Which benefit program ('SNAP', 'TANF', 'SSI')
        month: Time period of application
        
        reported_income: What seeker reports
        reported_household_size: What seeker reports
        reported_has_disability: What seeker reports
        
        true_income: Actual income (ground truth)
        true_household_size: Actual household size
        true_has_disability: Actual disability status
        
        is_fraud: Whether this is intentional fraud
        is_error: Whether this contains honest errors
    """
    application_id: int
    seeker_id: int
    program: str
    month: int
    
    # Reported characteristics (what seeker claims)
    reported_income: float
    reported_household_size: int
    reported_has_disability: bool
    
    # True characteristics (ground truth)
    true_income: float
    true_household_size: int
    true_has_disability: bool
    
    # Flags
    is_fraud: bool = False
    is_error: bool = False
    
    # Processing results (filled in by evaluator/reviewer)
    suspicion_score: Optional[float] = None
    escalated_to_reviewer: bool = False
    investigated: bool = False
    approved: bool = False
    denial_reason: Optional[str] = None
    
    # Complexity score (0.0 = simple, 1.0 = very complex)
    # Calculated during application creation
    complexity: Optional[float] = None
    
    # NEW: Documentation quality (0.0 = poor, 1.0 = excellent)
    # Reflects how well-prepared the application is
    documentation_quality: Optional[float] = None
    
    def get_income_discrepancy(self):
        """Calculate how much reported income differs from truth."""
        return self.true_income - self.reported_income
    
    def get_income_discrepancy_pct(self):
        """Calculate percentage discrepancy in income."""
        if self.true_income == 0:
            return 0.0
        return (self.true_income - self.reported_income) / self.true_income
    
    def get_quality_category(self):
        """Return categorical quality label for documentation."""
        if self.documentation_quality is None:
            return 'Unknown'
        elif self.documentation_quality >= 0.80:
            return 'Excellent'
        elif self.documentation_quality >= 0.65:
            return 'Good'
        elif self.documentation_quality >= 0.50:
            return 'Fair'
        elif self.documentation_quality >= 0.35:
            return 'Poor'
        else:
            return 'Very Poor'
    
    @staticmethod
    def calculate_documentation_quality(seeker, is_fraud=False, is_error=False):
        """
        Calculate application documentation quality (0.0-1.0).
        
        Quality reflects how well-prepared and complete the application is.
        
        Factors:
        - Education (stronger effect - college grads better at forms)
        - Prior experience (learning by doing)
        - Employment (have documentation ready)
        - Age (bureaucratic experience)
        - Disability (potential barriers)
        - Household size (documentation complexity)
        - Fraud/error (inconsistencies reduce quality)
        - Random variation (individual differences)
        
        Args:
            seeker: Seeker object
            is_fraud: Whether application is fraudulent
            is_error: Whether application contains errors
            
        Returns:
            float: Quality score 0.0 (poor) to 1.0 (excellent)
        """
        import numpy as np
        
        quality = 0.50  # Baseline (average)
        
        # EDUCATION (strongest predictor)
        education = seeker.cps_data.get('education', 'unknown')
        if education == 'graduate':
            quality += 0.25
        elif education == 'bachelors':
            quality += 0.20
        elif education == 'some_college':
            quality += 0.10
        elif education == 'high_school':
            quality += 0.05
        elif education == 'less_than_hs':
            quality -= 0.10
        
        # EXPERIENCE (learning by doing)
        if seeker.num_applications > 0:
            experience_boost = min(0.15, 0.05 * seeker.num_applications)
            quality += experience_boost
        
        # EMPLOYMENT (documentation available)
        employment = seeker.cps_data.get('employment_status', 'unknown')
        if employment in ['employed_full_time', 'employed_part_time']:
            quality += 0.08
        elif employment == 'unemployed':
            quality -= 0.05
        
        # AGE (bureaucratic experience)
        age = seeker.cps_data.get('age', 40)
        if age >= 50:
            quality += 0.05
        elif age < 25:
            quality -= 0.05
        
        # DISABILITY (potential barriers)
        if seeker.has_disability:
            quality -= 0.05
        
        # HOUSEHOLD SIZE (documentation complexity)
        num_children = seeker.cps_data.get('num_children', 0)
        if num_children >= 3:
            quality -= 0.05
        
        # FRAUD PENALTY (inconsistencies)
        if is_fraud:
            quality -= 0.15
        
        # ERROR PENALTY (sloppiness)
        if is_error:
            quality -= 0.10
        
        # RANDOM VARIATION (individual differences)
        random_component = seeker.rng.normal(0, 0.12)
        quality += random_component
        
        # Clip to [0, 1]
        return np.clip(quality, 0.0, 1.0)
    
    def __repr__(self):
        status = "FRAUD" if self.is_fraud else "ERROR" if self.is_error else "HONEST"
        return (f"Application(id={self.application_id}, seeker={self.seeker_id}, "
                f"program={self.program}, status={status}, "
                f"reported_income=${self.reported_income:,.0f}, "
                f"true_income=${self.true_income:,.0f})")


if __name__ == "__main__":
    # Quick test
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
        reported_income=15000,  # Underreporting
        reported_household_size=3,
        reported_has_disability=False,
        true_income=50000,
        true_household_size=3,
        true_has_disability=False,
        is_fraud=True
    )
    
    print("Honest Application:")
    print(f"  {honest_app}")
    print(f"  Discrepancy: ${honest_app.get_income_discrepancy():,.0f}")
    
    print("\nFraud Application:")
    print(f"  {fraud_app}")
    print(f"  Discrepancy: ${fraud_app.get_income_discrepancy():,.0f} "
          f"({fraud_app.get_income_discrepancy_pct():.1%})")