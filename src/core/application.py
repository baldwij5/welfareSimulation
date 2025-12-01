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
    
    def get_income_discrepancy(self):
        """Calculate how much reported income differs from truth."""
        return self.true_income - self.reported_income
    
    def get_income_discrepancy_pct(self):
        """Calculate percentage discrepancy in income."""
        if self.true_income == 0:
            return 0.0
        return (self.true_income - self.reported_income) / self.true_income
    
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