# ODD Protocol Documentation: Welfare Administration Simulation with AI Triage

**Model Name:** Welfare Administration Agent-Based Model (WAABM)  
**Version:** 1.0  
**Date:** December 2024  
**Author:** Jack Baldwin  
**Affiliation:** Maxwell School of Citizenship and Public Affairs, Syracuse University

**Citation format:** This model description follows the ODD (Overview, Design concepts, Details) protocol for describing agent-based models (Grimm et al. 2020).

---

## 1. PURPOSE AND PATTERNS

### 1.1 Purpose

The purpose of this model is to explore how AI-based application triage systems interact with heterogeneous applicant capabilities and constrained caseworker capacity to produce differential welfare access outcomes. The model tests theoretical predictions from the **AI-Administrative Navigation & Outcome Framework (AANOF)**, specifically examining:

1. How administrative burden (learning, psychological, and compliance costs) affects application completion rates
2. How AI triage strategies alter the distribution of welfare outcomes across demographic groups
3. The tradeoffs between system efficiency and equity under different policy configurations

The model is designed to inform policy decisions about AI adoption in welfare administration and to identify conditions under which automation increases or decreases disparities in program access.

### 1.2 Patterns

The model is evaluated against the following empirical patterns observed in real-world welfare systems:

**Pattern 1: Participation Gradient by Socioeconomic Status**
- Real-world observation: SNAP participation rates show strong income gradient, with lower-income quintiles having lower take-up rates despite eligibility
- Model expectation: Should reproduce declining participation rates for populations with lower Bureaucracy Navigation Points (BNP)

**Pattern 2: Caseworker Discretion Variance**
- Real-world observation: Approval rates vary significantly across individual caseworkers (15-30% coefficient of variation reported in literature)
- Model expectation: Model with discretion parameters should show similar variance

**Pattern 3: Processing Time Distribution**
- Real-world observation: Application processing times follow right-skewed distribution (median ~14 days, long tail to 60+ days)
- Model expectation: Queue dynamics should produce similar distribution

**Pattern 4: AI Prioritization Effects**
- Real-world observation: Automated triage systems improve mean processing times but can increase disparities (Eubanks 2018)
- Model expectation: AI strategies that prioritize "simple" cases should show efficiency gains with equity costs

---

## 2. ENTITIES, STATE VARIABLES, AND SCALES

### 2.1 Entities

The model includes four types of entities:

#### **2.1.1 Seekers (Applicants)**

Individual welfare applicants with heterogeneous characteristics

**Key State Variables:**
- `seeker_id`: Unique identifier
- `bureaucracy_navigation_points (BNP)`: Composite measure of navigation capacity (0-20 scale)
  - `learning_cost_capacity`: Ability to understand requirements (0-10)
  - `psychological_cost_capacity`: Stress/stigma tolerance (0-10)
  - `compliance_cost_capacity`: Time/documentation capability (0-10)
- `demographics`: 
  - `age`: Years (18-65)
  - `education`: Years of schooling (0-20)
  - `race`: Category (mapped from Census data)
  - `employment_status`: Binary
  - `income`: Continuous (from CPS data)
- `application_status`: {not_started, in_progress, submitted, approved, denied, abandoned}
- `steps_completed`: Count of completed administrative steps
- `time_in_system`: Simulation ticks since application start

#### **2.1.2 Caseworkers (Street-Level Bureaucrats)**

Government employees who process applications

**Key State Variables:**
- `caseworker_id`: Unique identifier
- `caseload`: Current number of applications assigned
- `capacity`: Maximum applications processable per time unit
- `discretion_level`: Degree of flexibility in rule interpretation (0.2-0.8)
- `experience_years`: Years in role (affects discretion)
- `processing_time_mean`: Average time per case
- `approval_rate`: Historical proportion of approvals

#### **2.1.3 Counties (Administrative Jurisdictions)**

Geographic units with varying characteristics

**Key State Variables:**
- `county_id`: FIPS code
- `population`: County population (from ACS data)
- `staff_capacity`: Total caseworker capacity (population-scaled)
- `ai_strategy`: {none, simple_first, random, risk_first, need_first}
- `policy_stance`: Political orientation affecting burden levels (-0.3 to +0.3)
- `application_queue`: Ordered list of pending applications

#### **2.1.4 AI System (Optional, when enabled)**

Automated triage algorithm

**Key State Variables:**
- `strategy`: Sorting algorithm type
- `prediction_model`: Scoring function for applications
- `confidence_threshold`: Minimum score for auto-processing
- `override_rate`: Proportion of AI decisions reviewed by humans

### 2.2 Scales

**Spatial Scale:**
- Geographic extent: County-level (US counties)
- Resolution: Individual agents within counties
- No explicit spatial movement (applicants assigned to counties)

**Temporal Scale:**
- Time step: 1 day (simulation tick)
- Typical simulation length: 365 ticks (1 year)
- Initialization period: 30 ticks (warm-up)

**Population Scale:**
- Number of seekers: Scaled from real county populations (typically 100-10,000 per county in simulation)
- Number of caseworkers: Determined by population-scaled capacity formula
- Number of counties: Typically 10-50 matched pairs for experiments

---

## 3. PROCESS OVERVIEW AND SCHEDULING

The model follows a discrete-time update schedule with the following sequence each time step:

### 3.1 Update Sequence (Daily Cycle)

```
1. SEEKER ACTIONS (in random order):
   a. New seekers enter system (based on arrival rate)
   b. Active seekers attempt to complete next administrative step
   c. BNP updated based on completed steps (learning effects)
   d. Applications abandoned if BNP exhausted
   e. Completed applications enter county queue

2. AI SYSTEM (if enabled):
   a. Score new applications in queue
   b. Reorder queue based on strategy
   c. Flag applications for auto-processing

3. CASEWORKER ACTIONS (in random order):
   a. Process applications from queue (up to capacity)
   b. Apply discretion to borderline cases
   c. Generate approval/denial decisions
   d. Update caseload and experience

4. COUNTY UPDATES:
   a. Update queue statistics
   b. Log outcomes and waiting times
   c. Adjust policy parameters (if dynamic)

5. SYSTEM MONITORING:
   a. Record aggregate statistics
   b. Check pattern validation metrics
   c. Export data for analysis
```

### 3.2 Initialization

**Step 1:** Generate synthetic population
- Draw demographics from stratified CPS/ACS samples
- Assign BNP components based on demographic characteristics
- Distribute seekers across counties proportional to population

**Step 2:** Initialize counties
- Set staff capacity based on population-scaled formula
- Assign policy stance (calibrated or experimental)
- Initialize AI system (if treatment condition)

**Step 3:** Warm-up period
- Run 30 ticks without data collection
- Allow queues to reach steady-state
- Stabilize caseworker experience levels

---

## 4. DESIGN CONCEPTS

### 4.1 Basic Principles

The model operationalizes two foundational theories:

**Administrative Burden Theory (Moynihan & Herd 2014)**
- Administrative processes impose learning, psychological, and compliance costs
- Costs vary by individual characteristics
- High costs lead to non-take-up among eligible populations

**Street-Level Bureaucracy Theory (Lipsky 2010)**
- Front-line workers exercise discretion under resource constraints
- Coping mechanisms (rationing, creaming) emerge from workload pressure
- Individual decisions aggregate to systematic policy outcomes

### 4.2 Emergence

Key emergent phenomena:

1. **Participation Gaps**: Disparities in approval rates across demographic groups emerge from interaction between:
   - Individual BNP heterogeneity
   - Queue prioritization rules
   - Caseworker capacity constraints

2. **Efficiency-Equity Tradeoff**: AI strategies improve mean processing times while potentially increasing outcome variance

3. **Bureaucratic Drift**: Caseworker coping behaviors under high caseload systematically alter policy implementation

### 4.3 Adaptation

**Seeker Adaptation:**
- BNP can increase through learning (completing steps builds capacity)
- Information access improves with social network effects (not yet implemented)

**Caseworker Adaptation:**
- Discretion increases with experience (linear growth, bounded)
- Processing speed adjusts to caseload (fatigue effects)

**System Adaptation:**
- AI system can be recalibrated based on outcomes (future extension)

### 4.4 Objectives

**Seekers**: Maximize probability of approval while minimizing effort (implicit utility function)

**Caseworkers**: Balance competing goals:
- Meet agency processing targets
- Apply rules correctly
- Provide responsive service (constrained by capacity)

**Counties**: Implement policy goals (efficient and equitable service delivery)

### 4.5 Learning

**Current implementation:**
- Seekers exhibit simple learning: completing steps increases future BNP slightly

**Future extensions:**
- Social learning: seekers share information within networks
- Caseworker learning: improved discrimination between cases over time

### 4.6 Prediction

Agents have limited predictive capacity:
- Seekers do not accurately predict approval probability
- Caseworkers use heuristics rather than optimal prediction
- AI system makes probabilistic predictions (if enabled)

### 4.7 Sensing

**Seekers sense:**
- Their own BNP level
- Number of steps remaining
- Time elapsed

**Caseworkers sense:**
- Own caseload level
- Individual case characteristics
- Queue length (influences processing speed)

**Counties sense:**
- Aggregate queue statistics
- Overall approval rates

### 4.8 Interaction

**Direct interactions:**
- Seeker ↔ Caseworker: Application processing encounter
- Seeker ↔ AI: Automated scoring/prioritization

**Indirect interactions:**
- Seekers compete for limited caseworker attention via queue
- Caseworker workload affects processing quality for all cases

### 4.9 Stochasticity

Stochastic elements:

1. **Seeker generation**: Demographics drawn from stratified samples (empirical distributions)
2. **Step completion**: Probabilistic success based on BNP vs. step difficulty
3. **Caseworker assignment**: Random allocation to cases
4. **Discretion application**: Probabilistic application of flexible rules
5. **Abandonment**: Stochastic drop-out based on remaining BNP

### 4.10 Collectives

**Counties** aggregate:
- Multiple seekers
- Multiple caseworkers
- Shared policy parameters and queue

**Treatment groups** (for experiments):
- Matched county pairs
- One with AI, one without

### 4.11 Observation

**Data collected at each time step:**

Individual-level:
- Seeker outcomes (approved, denied, abandoned)
- Time-to-decision
- BNP at decision point
- Demographic characteristics

Aggregate-level:
- Approval rates by demographic group
- Queue lengths and wait times
- Caseworker utilization rates
- Efficiency metrics (throughput)

**Validation metrics:**
- Participation gradient by BNP quintile
- Approval rate variance across caseworkers
- Processing time distribution
- Equity indices (Gini coefficient of outcomes)

---

## 5. INITIALIZATION

### 5.1 Initial State

**Seeker Population:**
```python
# Pseudo-code for initialization
for each county in counties:
    population_size = county.population * sampling_rate
    for i in range(population_size):
        seeker = create_seeker()
        seeker.demographics = draw_from_CPS_stratified()
        seeker.BNP = calculate_BNP(seeker.demographics)
        seeker.application_status = "not_started"
```

**County Configuration:**
```python
county.staff_capacity = calculate_capacity(county.population)
county.policy_stance = calibrated_value  # From empirical data
county.ai_strategy = experimental_condition  # Treatment assignment
```

**Caseworkers:**
```python
num_caseworkers = county.staff_capacity / cases_per_worker
for j in range(num_caseworkers):
    worker = create_caseworker()
    worker.experience_years = random.uniform(0, 15)
    worker.discretion_level = 0.5 + 0.1 * worker.experience_years
```

### 5.2 Parameter Values

**Core Parameters (Calibrated):**

| Parameter | Value | Source | Notes |
|-----------|-------|--------|-------|
| BNP_education_weight | 0.6 | Literature review | College = +3, HS = +1 |
| BNP_employment_weight | 0.3 | Synthesis | Employed = +2 |
| capacity_per_1000_pop | 2.5 | Admin data | Caseworkers per 1000 residents |
| step_difficulty_range | [0.3, 1.0] | ABM design | Normalized complexity |
| learning_rate | 0.05 | Calibration | BNP increase per step |
| abandonment_threshold | 0.0 | Assumption | Abandon when BNP ≤ 0 |

**AI Strategy Parameters:**

| Strategy | Description | Implementation |
|----------|-------------|----------------|
| simple_first | Prioritize low complexity | Sort by difficulty ascending |
| need_first | Prioritize low income | Sort by income ascending |
| random | No prioritization | Shuffle queue |
| risk_first | Prioritize high approval prob | Sort by predicted approval desc |

---

## 6. INPUT DATA

### 6.1 Empirical Data Sources

**Demographics (CPS/ACS):**
- Obtained from: IPUMS CPS and American Community Survey
- Variables used: age, education, race, employment, income
- Sampling method: Stratified random sampling by county and demographics

**County Characteristics:**
- FIPS codes and population from US Census
- Staff capacity estimates from state administrative data (when available)
- Policy stance proxies from voting data

### 6.2 Data Processing

```
1. Load CPS microdata
2. Filter to welfare-eligible population (income < 200% poverty line)
3. Create stratified sampling weights
4. Generate synthetic agents matching empirical distributions
5. Validate: compare simulated vs. real demographic margins
```

### 6.3 Model Calibration

**Target statistics for calibration:**
- SNAP participation rate by income quintile (USDA FNS data)
- Mean processing time (state admin data, ~14 days)
- Approval rate variance across counties (~20%)

**Calibration method:**
- Manual parameter tuning to match patterns
- Future: Automated calibration using approximate Bayesian computation

---

## 7. SUBMODELS

### 7.1 BNP Calculation

**Purpose:** Compute Bureaucracy Navigation Points from demographics

**Formula:**
```
learning_capacity = base_learning + 
                   (education_effect * years_education) +
                   (experience_effect * prior_welfare_use)

psychological_capacity = base_psychological +
                        (employment_effect * employed) +
                        (age_effect * within_optimal_age_range)

compliance_capacity = base_compliance +
                     (employment_penalty * employed) +  # Less time if working
                     (transport_bonus * has_transport)

BNP_total = learning_capacity + psychological_capacity + compliance_capacity
```

**Parameters:**
- base_learning = 5.0
- education_effect = 0.3 per year
- employment_effect = 2.0
- etc. (see Parameter Table)

### 7.2 Step Completion Process

**Purpose:** Determine whether seeker successfully completes administrative step

**Process:**
```
1. Get step difficulty: d ∈ [0.3, 1.0]
2. Get current BNP: B
3. Calculate success probability: P = min(1, B / (d * 10))
4. Draw random number r ~ Uniform(0,1)
5. If r < P:
      - Mark step complete
      - Reduce BNP by cost: B = B - (d * 2)
      - Increase BNP by learning: B = B + learning_rate
   Else:
      - Step not complete
      - Reduce BNP by partial cost: B = B - (d * 0.5)
6. If B ≤ 0: mark application as abandoned
```

### 7.3 AI Triage Submodel

**Purpose:** Score and reorder application queue

**Strategies:**

**Simple-First:**
```python
def simple_first(queue):
    scored = [(app, calculate_complexity(app)) for app in queue]
    sorted_queue = sorted(scored, key=lambda x: x[1])  # Ascending
    return [app for app, score in sorted_queue]

def calculate_complexity(app):
    return sum(step.difficulty for step in app.remaining_steps)
```

**Need-First:**
```python
def need_first(queue):
    scored = [(app, app.seeker.income) for app in queue]
    sorted_queue = sorted(scored, key=lambda x: x[1])  # Ascending
    return [app for app, score in sorted_queue]
```

**Risk-First:**
```python
def risk_first(queue):
    scored = [(app, predict_approval(app)) for app in queue]
    sorted_queue = sorted(scored, key=lambda x: x[1], reverse=True)
    return [app for app, score in sorted_queue]

def predict_approval(app):
    # Simple logistic model based on seeker characteristics
    score = logistic(β0 + β1*BNP + β2*income + β3*employment)
    return score
```

### 7.4 Caseworker Decision Submodel

**Purpose:** Determine approval/denial with discretion

**Process:**
```
1. Retrieve eligibility criteria (income threshold, household size)
2. Check strict eligibility: eligible = meets_all_criteria(application)
3. If clearly eligible or clearly ineligible:
      return deterministic decision
4. Else (borderline case):
      apply_discretion = random() < caseworker.discretion_level
      if apply_discretion:
         decision = apply_flexible_interpretation(application, caseworker)
      else:
         decision = apply_strict_interpretation(application)
5. Record decision and update caseworker statistics
```

### 7.5 Queue Management Submodel

**Purpose:** Maintain ordered queue and assign to caseworkers

**Process:**
```
Each time step:
1. Add newly submitted applications to queue
2. If AI enabled: apply triage strategy to reorder
3. For each caseworker with available capacity:
      - Retrieve next application from queue
      - Process application (see Decision Submodel)
      - Remove from queue
      - Record processing time
4. Update queue statistics (length, wait times)
```

---

## 8. REFERENCES

**Theoretical Foundation:**
- Moynihan, D., & Herd, P. (2014). Administrative burden: Learning, psychological, and compliance costs in citizen-state interactions. *Journal of Public Administration Research and Theory*, 25(1), 43-69.
- Lipsky, M. (2010). *Street-level bureaucracy: Dilemmas of the individual in public service* (30th Anniversary ed.). Russell Sage Foundation.
- Hupe, P., & Hill, M. (2007). Street-level bureaucracy and public accountability. *Public Administration*, 85(2), 279-299.

**Methodological:**
- Grimm, V., et al. (2020). The ODD protocol for describing agent-based and other simulation models: A second update to improve clarity, replication, and structural realism. *Journal of Artificial Societies and Social Simulation*, 23(2), 7.

**Empirical Data:**
- US Census Bureau. American Community Survey (ACS) Public Use Microdata
- IPUMS CPS: Current Population Survey
- USDA Food and Nutrition Service: SNAP Participation Data

---

## APPENDIX A: Model Validation Plan

### Validation Tests

**Face Validation:**
- Expert review by public administration scholars
- Feedback from welfare administrators

**Pattern Validation:**
- Compare simulated participation gradient to USDA data
- Match approval rate variance to empirical estimates
- Reproduce processing time distribution

**Sensitivity Analysis:**
- Vary key parameters (±20%) and assess output stability
- Identify most influential parameters

**Cross-Validation:**
- Train on subset of counties, test on hold-out set
- Compare predictions to actual outcomes

---

## APPENDIX B: Code and Data Availability

**Model Code:**
- Repository: https://github.com/baldwij5/welfareSimulation
- Language: Python 3.x
- Dependencies: Listed in requirements.txt

**Data:**
- Synthetic population generator: Available in repository
- Empirical calibration data: Aggregated data provided; microdata requires IPUMS registration

**Reproducibility:**
- Random seed control for all stochastic processes
- Complete parameter specifications in config files
- Analysis scripts included

---

**Document Version:** 1.0  
**Last Updated:** December 2024  
**Contact:** jackbaldwin@syr.edu
