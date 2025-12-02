"""
Seeker agent - represents a citizen who may apply for welfare benefits.

Simplified version with fraud mechanics.
"""

import numpy as np


class Seeker:
    """A person who may seek welfare benefits."""
    
    def __init__(self, seeker_id, race, income, county='DEFAULT', has_children=False, has_disability=False, cps_data=None, random_state=None):
        """
        Initialize a seeker with basic characteristics.
        
        Args:
            seeker_id: Unique identifier
            race: 'White', 'Black', 'Hispanic', or 'Asian'
            income: Annual income in dollars
            county: County of residence (e.g., 'Kings County, NY')
            has_children: Whether seeker has children
            has_disability: Whether seeker has a disability
            cps_data: Optional dict with ALL CPS variables for this person
            random_state: numpy RandomState for reproducibility
        """
        self.id = seeker_id
        self.race = race
        self.county = county
        self.rng = random_state if random_state else np.random.RandomState()
        
        # Basic characteristics (provided)
        self.income = income
        self.has_children = has_children
        self.has_disability = has_disability
        
        # Store complete CPS data (if provided)
        self.cps_data = cps_data if cps_data is not None else {}
        
        # Extract common variables for easy access
        if self.cps_data:
            self.age = self.cps_data.get('AGE', None)
            self.sex = 'Female' if self.cps_data.get('female', 0) == 1 else 'Male'
            self.education = self.cps_data.get('education', None)
            self.married = self.cps_data.get('MARST', 0) in [1, 2]  # 1=married spouse present, 2=married spouse absent
            self.num_children = self.cps_data.get('num_children', 0)
            self.employed = self.cps_data.get('employed', 0) == 1
        else:
            # Defaults if no CPS data
            self.age = None
            self.sex = None
            self.education = None
            self.married = False
            self.num_children = 0
            self.employed = False
        
        # Fraud propensity: uniform 0 to 2
        # < 1.0 = low fraud risk
        # > 1.0 = high fraud risk
        self.fraud_propensity = self.rng.uniform(0, 2)
        
        # Lying magnitude: uniform 0 to 100 (percentage points)
        # If fraud, underreport income by this %
        self.lying_magnitude = self.rng.uniform(0, 100)
        
        # Error propensity: uniform 0 to 2
        # < 1.0 = low error risk (careful, educated)
        # > 1.0 = high error risk (confused, uneducated)
        self.error_propensity = self.rng.uniform(0, 2)
        
        # Error magnitude: uniform 0 to 20 (percentage points)
        # If error, income report is off by this % (could be higher or lower)
        self.error_magnitude = self.rng.uniform(0, 20)
        
        # History tracking (for learning effects)
        self.num_applications = 0
        self.num_investigations = 0
        self.num_approvals = 0
        self.num_denials = 0
        
        # Enrollment tracking: {program: month_approved}
        # Tracks when seeker was last approved for each program
        self.enrolled_programs = {}  # e.g., {'SNAP': 5, 'TANF': 3}
        
        # Recertification schedules (months between recertifications)
        self.recert_schedules = {
            'SNAP': 6,   # Every 6 months
            'TANF': 12,  # Every 12 months
            'SSI': 36    # Every 36 months
        }
        
        # Bureaucracy navigation capacity (ability to withstand investigation)
        # Higher = better able to navigate bureaucratic requirements
        # Based on education, employment, age, organization
        self.bureaucracy_navigation_points = self._generate_bureaucracy_capacity()
    
    def get_monthly_income(self):
        """Convert annual income to monthly for benefit calculations."""
        return self.income / 12
    
    def __repr__(self):
        return (f"Seeker(id={self.id}, race={self.race}, "
                f"income=${self.income:,.0f}, children={self.has_children})")
    
    def should_apply(self, program, month):
        """
        Decide whether to apply for a benefit program.
        
        Applies if:
        1. Not currently enrolled AND meets eligibility, OR
        2. Currently enrolled AND recertification is due
        
        Args:
            program: Which program ('SNAP', 'TANF', 'SSI')
            month: Current month
            
        Returns:
            bool: True if eligible and should apply
        """
        monthly_income = self.get_monthly_income()
        
        # Check if recertification is needed
        if program in self.enrolled_programs:
            months_since_approval = month - self.enrolled_programs[program]
            recert_period = self.recert_schedules[program]
            
            # If recertification is due, must reapply
            if months_since_approval >= recert_period:
                # Remove from enrollment (expired)
                del self.enrolled_programs[program]
                # Fall through to regular eligibility check below
            else:
                # Still enrolled, don't need to apply yet
                return False
        
        # Regular eligibility check (for new applications)
        if program == 'SNAP':
            # SNAP: Income < $2,500/month
            income_eligible = monthly_income < 2500
            return income_eligible
            
        elif program == 'TANF':
            # TANF: Income < $1,000/month AND has children
            income_eligible = monthly_income < 1000
            has_children = self.has_children
            return income_eligible and has_children
            
        elif program == 'SSI':
            # SSI: Income < $1,913/month AND has disability
            income_eligible = monthly_income < 1913
            has_disability = self.has_disability
            return income_eligible and has_disability
        
        return False
    
    def enroll_in_program(self, program, month):
        """
        Mark seeker as enrolled in a program.
        
        Called when application is approved.
        
        Args:
            program: Which program ('SNAP', 'TANF', 'SSI')
            month: Month of approval
        """
        self.enrolled_programs[program] = month
    
    def is_enrolled(self, program):
        """
        Check if currently enrolled in a program.
        
        Args:
            program: Which program to check
            
        Returns:
            bool: True if enrolled
        """
        return program in self.enrolled_programs
    
    def will_commit_fraud(self, month):
        """
        Decide whether to commit fraud on an application this month.
        
        Based on fraud_propensity:
        - < 1.0: Low fraud risk (less likely to commit fraud)
        - > 1.0: High fraud risk (more likely to commit fraud)
        
        Uses month for reproducible randomness (same month = same decision).
        
        Args:
            month: Current month (for reproducibility)
            
        Returns:
            bool: True if will commit fraud
        """
        # Use fraud_propensity as a probability threshold
        # Transform 0-2 scale to roughly 0-50% probability
        # fraud_propensity of 1.0 → 25% chance
        # fraud_propensity of 2.0 → 50% chance
        base_probability = self.fraud_propensity / 4.0  # Divide by 4 to get 0-0.5 range
        
        # Create reproducible random number based on seeker_id + month
        decision_seed = self.id + month + 999  # +999 to differentiate from should_apply
        decision_rng = np.random.RandomState(decision_seed)
        random_value = decision_rng.random()
        
        # Commit fraud if random value < probability
        return random_value < base_probability
    
    def will_make_error(self, month):
        """
        Decide whether to make an honest error on an application this month.
        
        Based on error_propensity:
        - < 1.0: Low error risk (careful, educated)
        - > 1.0: High error risk (confused, less educated)
        
        Errors are HONEST mistakes, not intentional fraud.
        Target: ~10-15% error rate overall.
        
        Uses month for reproducible randomness (same month = same decision).
        
        Args:
            month: Current month (for reproducibility)
            
        Returns:
            bool: True if will make an error
        """
        # Use error_propensity as a probability threshold
        # Scale to get realistic ~10-15% overall error rate
        # 
        # error_propensity of 0.0 → 0% chance
        # error_propensity of 1.0 → 7.5% chance
        # error_propensity of 2.0 → 15% chance
        base_probability = self.error_propensity * 0.075  # Same scaling as fraud
        
        # Create reproducible random number based on seeker_id + month
        decision_seed = self.id + month + 777  # +777 to differentiate from fraud
        decision_rng = np.random.RandomState(decision_seed)
        random_value = decision_rng.random()
        
        # Make error if random value < probability
        return random_value < base_probability
    
    def create_application(self, program, month, application_id):
        """
        Create an application for a benefit program.
        
        This combines:
        1. Eligibility check (should_apply)
        2. Fraud decision (will_commit_fraud)
        3. Error decision (will_make_error)
        4. Income reporting (based on fraud/error/honest)
        
        Args:
            program: Which program ('SNAP', 'TANF', 'SSI')
            month: Current month
            application_id: Unique ID for this application
            
        Returns:
            Application object, or None if seeker doesn't apply
        """
        # Import here to avoid circular dependency
        from .application import Application
        
        # Step 1: Check if seeker applies
        if not self.should_apply(program, month):
            return None  # Not eligible, won't apply
        
        # Step 2: Decide if committing fraud (intentional lie)
        committing_fraud = self.will_commit_fraud(month)
        
        # Step 3: Decide if making error (honest mistake)
        # Note: Can't have both fraud AND error - fraud takes precedence
        making_error = False if committing_fraud else self.will_make_error(month)
        
        # Step 4: Calculate reported income
        if committing_fraud:
            # Fraud: Underreport income by lying_magnitude percentage
            underreport_pct = self.lying_magnitude / 100.0
            reported_income = self.income * (1.0 - underreport_pct)
            
        elif making_error:
            # Error: Report income incorrectly by error_magnitude (could be higher OR lower)
            # 50% chance of overreporting, 50% chance of underreporting
            error_direction_seed = self.id + month + 555
            direction_rng = np.random.RandomState(error_direction_seed)
            
            if direction_rng.random() < 0.5:
                # Underreport by error_magnitude
                error_pct = self.error_magnitude / 100.0
                reported_income = self.income * (1.0 - error_pct)
            else:
                # Overreport by error_magnitude
                error_pct = self.error_magnitude / 100.0
                reported_income = self.income * (1.0 + error_pct)
        else:
            # Honest: Report truthfully
            reported_income = self.income
        
        # Step 5: Create application
        application = Application(
            application_id=application_id,
            seeker_id=self.id,
            program=program,
            month=month,
            reported_income=reported_income,
            reported_household_size=2,  # Simplified: always 2
            reported_has_disability=self.has_disability,
            true_income=self.income,
            true_household_size=2,
            true_has_disability=self.has_disability,
            is_fraud=committing_fraud,
            is_error=making_error
        )
        
        # Track that seeker applied
        self.num_applications += 1
        
        # Calculate complexity score
        application.complexity = self._calculate_complexity(application)
        
        return application
    
    def _calculate_complexity(self, application):
        """
        Calculate complexity score for an application (0.0 to 1.0).
        
        Factors:
        - Program type (SSI most complex, SNAP simplest)
        - Household size (more people = more verification)
        - Number of children (each child needs verification)
        - Disability status (medical documentation required)
        - New vs recertification (new = more paperwork)
        - Age (elderly have additional rules)
        
        Args:
            application: The application being scored
            
        Returns:
            float: Complexity score (0.0 = simple, 1.0 = very complex)
        """
        complexity = 0.0
        
        # Base complexity by program
        program_base = {
            'SNAP': 0.30,  # Simplest (just income and household)
            'TANF': 0.50,  # Medium (children, work requirements)
            'SSI': 0.70    # Most complex (disability verification)
        }
        complexity += program_base.get(application.program, 0.40)
        
        # Household size (more people = more verification)
        if self.cps_data:
            household_size = self.cps_data.get('household_size', 2)
            complexity += min(0.15, (household_size - 1) * 0.05)
        
        # Number of children (each needs verification)
        if self.num_children:
            complexity += min(0.10, self.num_children * 0.03)
        
        # Disability (requires medical documentation)
        if self.has_disability:
            complexity += 0.20
        
        # New application vs recertification
        if self.is_enrolled(application.program):
            # Recertification - already have records
            complexity += 0.0
        else:
            # New application - more paperwork
            complexity += 0.15
        
        # Age (elderly have additional considerations)
        if self.age and self.age >= 65:
            complexity += 0.10
        
        # Cap at 1.0
        return min(1.0, complexity)
    
    def _generate_bureaucracy_capacity(self):
        """
        Generate bureaucracy navigation capacity (0-20 points).
        
        Represents ability to withstand investigation scrutiny:
        - Provide required documentation
        - Navigate complex forms
        - Respond to verification requests
        - Handle interviews professionally
        
        Factors (HONEST capacity - fraud adds separate costs):
        - Education: College educated navigate better
        - Employment: Has documentation readily available
        - Age: Older people more experienced with bureaucracy
        - Disability: May struggle with complex processes
        
        This creates structural inequality:
        - Educated, employed people withstand more scrutiny
        - Less educated, unemployed struggle even if honest
        
        Returns:
            float: Points (roughly 0-20, can go negative)
        """
        points = 10.0  # Base capacity
        
        # EDUCATION (bureaucratic literacy)
        if self.education in ['bachelors', 'graduate']:
            points += 5.0  # Understand complex forms, know rights
        elif self.education in ['high_school', 'some_college']:
            points += 2.0  # Basic literacy
        elif self.education == 'less_than_hs':
            points -= 3.0  # Struggle with forms, documentation
        
        # EMPLOYMENT (has documentation)
        if self.employed:
            points += 3.0  # Has pay stubs, employer verification easy
        else:
            points -= 2.0  # Lacks standard employment docs
        
        # AGE (experience with bureaucracy)
        if self.age:
            if self.age >= 50:
                points += 2.0  # Decades of experience
            elif self.age >= 35:
                points += 1.0  # Some experience
            elif self.age < 25:
                points -= 1.0  # New to the system
        
        # DISABILITY (may face challenges)
        if self.has_disability:
            points -= 2.0  # Physical/cognitive challenges with process
        
        # RANDOM VARIATION (life circumstances)
        # Some people are just more organized, less stressed, etc.
        points += self.rng.uniform(-2, 2)
        
        # Ensure minimum 0
        return max(0, points)



if __name__ == "__main__":
    # Quick manual test
    rng = np.random.RandomState(42)
    
    seekers = [
        Seeker(1, 'White', rng),
        Seeker(2, 'Black', rng),
        Seeker(3, 'Hispanic', rng)
    ]
    
    print("Sample Seekers:")
    for s in seekers:
        print(f"  {s}")
    
    # Check income distributions
    print("\nIncome Distribution Check:")
    for race in ['White', 'Black']:
        incomes = [Seeker(i, race, np.random.RandomState(i)).income 
                   for i in range(1000)]
        median = np.median(incomes)
        print(f"  {race}: median=${median:,.0f}")