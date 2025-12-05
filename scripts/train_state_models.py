"""
Train State-Level Reviewer Models

Creates one statistical discrimination model per state.

Each state model:
- Trained on counties within that state
- Weighted by county population
- Captures state-specific welfare policies/contexts
- Used by ALL reviewers in that state

Run with: python scripts/train_state_models.py
Time: ~5-10 minutes
"""

import sys
sys.path.insert(0, 'src')
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import pickle
import os


def prepare_state_data(acs_data):
    """
    Prepare ACS data and extract state names.
    
    Returns:
        DataFrame: ACS with state column
    """
    print("Preparing state data...")
    
    # Extract state from county_name
    acs_data['state'] = acs_data['county_name'].str.split(', ').str[1]
    
    # Filter to counties with sufficient data
    acs_clean = acs_data[acs_data['total_county_population'] >= 5000].copy()
    
    print(f"  {len(acs_clean)} counties across {acs_clean['state'].nunique()} states")
    
    return acs_clean


def train_state_model(state_counties, state_name):
    """
    Train logistic regression for ONE state.
    
    Args:
        state_counties: DataFrame of counties in this state
        state_name: State name
        
    Returns:
        dict: Trained model package
    """
    # Features that predict program need
    feature_columns = [
        'poverty_rate',
        'median_household_income',
        'unemployment_rate',
        'black_pct',
        'hispanic_pct',
        'snap_participation_rate'
    ]
    
    # Check availability
    available = [f for f in feature_columns if f in state_counties.columns]
    
    # Create unemployment proxy if missing
    if 'unemployment_rate' not in state_counties.columns:
        state_counties['unemployment_rate'] = state_counties['poverty_rate'] * 0.5
        available.append('unemployment_rate')
    
    # Extract features
    X = state_counties[available].copy()
    X = X.fillna(X.median())
    
    # Outcome: High SNAP participation (proxy for need)
    if 'snap_participation_rate' in state_counties.columns:
        state_median = state_counties['snap_participation_rate'].median()
        y = (state_counties['snap_participation_rate'] > state_median).astype(int)
    else:
        # Fallback to poverty
        state_median = state_counties['poverty_rate'].median()
        y = (state_counties['poverty_rate'] > state_median).astype(int)
    
    # Population weights (larger counties = more influence)
    weights = state_counties['total_county_population'].values
    
    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Train logistic regression
    try:
        model = LogisticRegression(max_iter=1000, random_state=42)
        model.fit(X_scaled, y, sample_weight=weights)
        
        accuracy = model.score(X_scaled, y, sample_weight=weights)
        
        return {
            'model': model,
            'scaler': scaler,
            'features': available,
            'state': state_name,
            'n_counties': len(state_counties),
            'accuracy': accuracy,
            'total_population': weights.sum(),
            'median_outcome': state_median
        }
        
    except Exception as e:
        print(f"    ⚠️  Error training {state_name}: {e}")
        return None


def train_all_state_models(acs_data):
    """
    Train models for all 50 states.
    
    Returns:
        dict: {state: model_package}
    """
    print("\n" + "="*70)
    print("TRAINING STATE-SPECIFIC MODELS")
    print("="*70)
    
    state_models = {}
    
    # Remove NaN states
    acs_data = acs_data[acs_data['state'].notna()].copy()
    
    states = sorted(acs_data['state'].unique())
    
    print(f"\nTraining {len(states)} state models...")
    print(f"(Each weighted by county population)\n")
    
    for i, state in enumerate(states, 1):
        state_counties = acs_data[acs_data['state'] == state]
        
        # Skip states with too few counties
        if len(state_counties) < 3:
            print(f"{i:2d}. {state:<20} SKIPPED (only {len(state_counties)} counties)")
            continue
        
        print(f"{i:2d}. {state:<20} ", end='', flush=True)
        
        model = train_state_model(state_counties, state)
        
        if model:
            state_models[state] = model
            print(f"✓ {model['n_counties']:3d} counties, {model['accuracy']:.1%} accuracy")
        else:
            print(f"✗ Failed")
    
    return state_models


def save_state_models(state_models, directory='models/state_models'):
    """Save all state models."""
    os.makedirs(directory, exist_ok=True)
    
    # Save each state model separately
    for state, model in state_models.items():
        filename = f"{directory}/{state.replace(' ', '_')}.pkl"
        with open(filename, 'wb') as f:
            pickle.dump(model, f)
    
    # Also save index
    index = {
        'states': list(state_models.keys()),
        'n_states': len(state_models),
        'total_counties': sum(m['n_counties'] for m in state_models.values())
    }
    
    with open(f"{directory}/index.pkl", 'wb') as f:
        pickle.dump(index, f)
    
    print(f"\n✓ Saved {len(state_models)} state models to: {directory}/")


def analyze_state_variation(state_models):
    """
    Analyze variation across state models.
    
    Shows which states are harsher/more lenient.
    """
    print("\n" + "="*70)
    print("STATE MODEL VARIATION")
    print("="*70)
    
    # Compare coefficients across states
    print("\nBlack% coefficient by state (shows statistical discrimination):")
    print("  (Positive = Black% counties judged as higher need)\n")
    
    black_coeffs = []
    
    for state, model in state_models.items():
        if 'black_pct' in model['features']:
            idx = model['features'].index('black_pct')
            coef = model['model'].coef_[0][idx]
            black_coeffs.append((state, coef))
    
    # Sort by coefficient
    black_coeffs.sort(key=lambda x: x[1], reverse=True)
    
    # Show top and bottom 10
    print("  Most positive (higher Black% → easier investigation):")
    for state, coef in black_coeffs[:10]:
        print(f"    {state:<20} {coef:+.3f}")
    
    print("\n  Most negative (higher Black% → harder investigation):")
    for state, coef in black_coeffs[-10:]:
        print(f"    {state:<20} {coef:+.3f}")
    
    print(f"\n  Mean: {np.mean([c for _, c in black_coeffs]):.3f}")
    print(f"  SD: {np.std([c for _, c in black_coeffs]):.3f}")
    print(f"  Range: {max([c for _, c in black_coeffs]) - min([c for _, c in black_coeffs]):.3f}")


def test_state_model(state_models):
    """Test models on example counties."""
    print("\n" + "="*70)
    print("EXAMPLE STATE MODEL PREDICTIONS")
    print("="*70)
    
    test_cases = [
        ('Alabama', 'Jefferson County, Alabama', 'high poverty, high Black%'),
        ('Alabama', 'Baldwin County, Alabama', 'low poverty, low Black%'),
        ('California', 'Los Angeles County, California', 'medium poverty, diverse'),
        ('California', 'Orange County, California', 'low poverty, affluent'),
        ('New York', 'Kings County, New York', 'high poverty, diverse')
    ]
    
    from data.data_loader import load_acs_county_data
    acs = load_acs_county_data('src/data/us_census_acs_2022_county_data.csv')
    acs['state'] = acs['county_name'].str.split(', ').str[1]
    
    print("\nPredictions for example counties:")
    print("  (Shows state-specific patterns)\n")
    
    for state, county, description in test_cases:
        if state not in state_models:
            continue
        
        model = state_models[state]
        county_data = acs[acs['county_name'] == county]
        
        if len(county_data) == 0:
            continue
        
        county_data = county_data.iloc[0]
        
        # Extract features
        features = []
        for feat in model['features']:
            features.append(county_data.get(feat, acs[feat].median()))
        
        # Predict
        features_scaled = model['scaler'].transform([features])
        prob = model['model'].predict_proba(features_scaled)[0][1]
        
        print(f"  {county}")
        print(f"    State model: {state}")
        print(f"    Description: {description}")
        print(f"    Predicted need: {prob:.1%}", end='')
        
        if prob > 0.7:
            print(f" → EASIER investigation (0.8×)")
        elif prob < 0.3:
            print(f" → HARDER investigation (1.3×)")
        else:
            print(f" → Normal investigation (1.0×)")
        print()


def main():
    """Train and save state-level models."""
    print("\n" + "="*70)
    print("STATE-LEVEL REVIEWER MODELS")
    print("="*70)
    print("\nApproach:")
    print("  - Train ONE model per state (50 models total)")
    print("  - Each uses counties within that state")
    print("  - Weighted by county population")
    print("  - ALL reviewers in a state share the same model")
    print("\nBenefits:")
    print("  ✓ Sufficient sample size (10-100 counties per state)")
    print("  ✓ Captures state policy contexts")
    print("  ✓ Realistic (reviewers trained by state)")
    print("  ✓ Geographic variation (50 different patterns)")
    
    # Load ACS
    from data.data_loader import load_acs_county_data
    acs = load_acs_county_data('src/data/us_census_acs_2022_county_data.csv')
    
    # Prepare
    acs = prepare_state_data(acs)
    
    # Train all state models
    state_models = train_all_state_models(acs)
    
    print(f"\n✓ Successfully trained {len(state_models)} state models")
    
    # Save
    save_state_models(state_models)
    
    # Analyze variation
    analyze_state_variation(state_models)
    
    # Test
    test_state_model(state_models)
    
    print("\n" + "="*70)
    print("TRAINING COMPLETE")
    print("="*70)
    print(f"\nTrained {len(state_models)} state-specific models")
    print(f"Saved to: models/state_models/")
    print("\nEach state's reviewers will use their state's patterns!")
    print("\nNext: Run experiments to see state-level variation in bias")


if __name__ == "__main__":
    main()