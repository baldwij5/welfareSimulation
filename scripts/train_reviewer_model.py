"""
Train Reviewer Credibility Model from ACS Patterns

Learns statistical patterns from county-level data that reviewers
unconsciously use to assess applicant credibility.

Model predicts: Likelihood of legitimate program need
Based on: County characteristics + applicant observables

This creates STATISTICAL DISCRIMINATION without explicit bias!

Run with: python scripts/train_reviewer_model.py
"""

import sys
sys.path.insert(0, 'src')
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import pickle
import os


def prepare_acs_data(acs_file):
    """
    Prepare ACS data for model training.
    
    Returns:
        DataFrame: Cleaned ACS with relevant features
    """
    print("Loading ACS data...")
    acs = pd.read_csv(acs_file)
    print(f"  Loaded {len(acs)} counties")
    
    # Filter to counties with sufficient data
    acs_clean = acs[acs['total_county_population'] >= 10000].copy()
    
    print(f"  Using {len(acs_clean)} counties (pop >= 10k)")
    
    return acs_clean


def train_credibility_model(acs_data):
    """
    Train model to predict program need from county/applicant characteristics.
    
    Model learns:
    - Which counties have high program participation (legitimate need)
    - Patterns in poverty, unemployment, demographics
    - Reviewer uses these patterns to assess individuals
    
    Returns:
        dict: Model, scaler, metadata
    """
    print("\n" + "="*70)
    print("TRAINING CREDIBILITY MODEL")
    print("="*70)
    
    # Features that reviewer can observe/infer
    feature_columns = [
        'poverty_rate',                    # County context
        'median_household_income',         # Economic conditions
        'unemployment_rate',               # Job market (if available)
        'black_pct',                       # Demographics (structural, not individual race)
        'hispanic_pct',
        'educational_attainment_bachelors_pct',  # Education level (if available)
        'snap_participation_rate'          # Program usage patterns
    ]
    
    # Check which features are available
    available_features = [f for f in feature_columns if f in acs_data.columns]
    
    print(f"\nAvailable features: {len(available_features)}")
    for f in available_features:
        print(f"  - {f}")
    
    # If key features missing, use core set
    if 'unemployment_rate' not in acs_data.columns:
        print("\n⚠️  Creating unemployment proxy from poverty rate")
        acs_data['unemployment_rate'] = acs_data['poverty_rate'] * 0.5
        available_features.append('unemployment_rate')
    
    if 'educational_attainment_bachelors_pct' not in acs_data.columns:
        print("⚠️  Creating education proxy")
        acs_data['educational_attainment_bachelors_pct'] = 100 - acs_data['poverty_rate'] * 2
        available_features.append('educational_attainment_bachelors_pct')
    
    # Extract features
    X = acs_data[available_features].copy()
    
    # Fill missing values with median
    X = X.fillna(X.median())
    
    print(f"\nFeature summary:")
    print(X.describe())
    
    # Outcome: High program participation (indicates legitimate need)
    # Use SNAP participation as proxy for need
    if 'snap_participation_rate' in acs_data.columns:
        snap_median = acs_data['snap_participation_rate'].median()
        y = (acs_data['snap_participation_rate'] > snap_median).astype(int)
        print(f"\nOutcome: SNAP participation > {snap_median:.1f}%")
    else:
        # Fallback: Use poverty rate
        poverty_median = acs_data['poverty_rate'].median()
        y = (acs_data['poverty_rate'] > poverty_median).astype(int)
        print(f"\nOutcome: Poverty rate > {poverty_median:.1f}%")
    
    print(f"  High need counties: {y.sum()} ({y.sum()/len(y)*100:.1f}%)")
    print(f"  Low need counties: {(1-y).sum()} ({(1-y).sum()/len(y)*100:.1f}%)")
    
    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Train logistic regression
    print(f"\nTraining logistic regression...")
    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(X_scaled, y)
    
    # Evaluate
    accuracy = model.score(X_scaled, y)
    print(f"  Training accuracy: {accuracy:.1%}")
    
    # Show coefficients (what patterns model learned)
    print(f"\nLearned patterns (coefficients):")
    for feature, coef in zip(available_features, model.coef_[0]):
        print(f"  {feature:<40} {coef:+.3f}")
    
    print(f"\nInterpretation:")
    print(f"  Positive coef: Higher value → higher predicted need")
    print(f"  Negative coef: Higher value → lower predicted need")
    
    # Package model
    model_package = {
        'model': model,
        'scaler': scaler,
        'features': available_features,
        'accuracy': accuracy,
        'n_counties': len(acs_data),
        'outcome': 'snap_participation_rate'
    }
    
    return model_package


def save_model(model_package, filepath='models/reviewer_credibility_model.pkl'):
    """Save trained model."""
    os.makedirs('models', exist_ok=True)
    
    with open(filepath, 'wb') as f:
        pickle.dump(model_package, f)
    
    print(f"\n✓ Model saved: {filepath}")


def test_model(model_package, acs_data):
    """
    Test model on example counties.
    
    Shows how different county profiles get different credibility scores.
    """
    print(f"\n{'='*70}")
    print("MODEL PREDICTIONS - EXAMPLE COUNTIES")
    print(f"{'='*70}")
    
    # Select diverse counties
    test_counties = [
        'Los Angeles County, California',
        'Orange County, California',
        'Jefferson County, Alabama',
        'Kings County, New York',
        'Barbour County, Alabama'
    ]
    
    print(f"\nPredicted 'high need' probability for each county:")
    print(f"  (Higher = more credible applicants from this county)")
    
    for county in test_counties:
        county_data = acs_data[acs_data['county_name'] == county]
        
        if len(county_data) == 0:
            continue
        
        county_data = county_data.iloc[0]
        
        # Extract features
        features = []
        for f in model_package['features']:
            features.append(county_data.get(f, acs_data[f].median()))
        
        # Predict
        features_scaled = model_package['scaler'].transform([features])
        prob_high_need = model_package['model'].predict_proba(features_scaled)[0][1]
        
        # Show
        poverty = county_data['poverty_rate']
        black_pct = county_data['black_pct']
        
        print(f"\n  {county}")
        print(f"    Poverty: {poverty:.1f}%, Black: {black_pct:.1f}%")
        print(f"    Predicted need: {prob_high_need:.1%}")
        
        if prob_high_need > 0.7:
            print(f"    → High credibility (lighter investigation)")
        elif prob_high_need < 0.3:
            print(f"    → Low credibility (intensive investigation)")
        else:
            print(f"    → Medium credibility (normal investigation)")


def main():
    """Train and save reviewer credibility model."""
    print("\n" + "="*70)
    print("TRAINING REVIEWER STATISTICAL DISCRIMINATION MODEL")
    print("="*70)
    print("\nPurpose:")
    print("  Learn patterns from ACS data that reviewers use to")
    print("  assess applicant credibility during interviews")
    print("\nApproach:")
    print("  - Train on 3,202 US counties")
    print("  - Features: Poverty, income, unemployment, demographics")
    print("  - Outcome: Program participation (proxy for need)")
    print("  - Model: Logistic regression")
    print("\nResult:")
    print("  Statistical patterns reviewers apply (unconsciously)")
    
    # Load data
    acs_data = prepare_acs_data('src/data/us_census_acs_2022_county_data.csv')
    
    # Train model
    model_package = train_credibility_model(acs_data)
    
    # Save
    save_model(model_package)
    
    # Test on examples
    test_model(model_package, acs_data)
    
    print(f"\n{'='*70}")
    print("TRAINING COMPLETE")
    print(f"{'='*70}")
    print("\nModel trained from real ACS patterns!")
    print("Reviewers will use this for statistical discrimination")
    print("\nNext steps:")
    print("  1. Update Reviewer to load model")
    print("  2. Apply credibility adjustments during investigation")
    print("  3. Run experiments to see emergent bias effects")


if __name__ == "__main__":
    main()