"""
Estimate Logit Models for Program Participation

Uses CPS data to estimate the probability of participating in:
- SNAP
- TANF (welfare)
- SSI

This gives us REALISTIC application probabilities based on actual behavior!
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score
import pickle


def load_and_prepare_cps(filepath='src/data/cps_asec_2022_processed_full.csv'):
    """
    Load CPS and prepare for logit regression.
    
    Returns:
        DataFrame: Ready for modeling
    """
    print("Loading CPS data...")
    cps = pd.read_csv(filepath)
    
    # Filter to working-age
    cps = cps[(cps['AGE'] >= 18) & (cps['AGE'] <= 64)].copy()
    print(f"  {len(cps):,} working-age adults")
    
    # Filter to eligible (income < $30k)
    cps = cps[cps['INCTOT'] < 30000].copy()
    print(f"  {len(cps):,} income-eligible (<$30k)")
    
    return cps


def estimate_snap_model(cps_data):
    """
    Estimate logit model for SNAP participation.
    
    Outcome: received_snap (1 = receiving SNAP, 0 = not)
    
    Predictors:
    - Income (INCTOT)
    - Race (black, hispanic, asian - white is reference)
    - Has children
    - Has disability
    - Age
    - Education (using dummies)
    - Employment status
    - Sex (female)
    
    Returns:
        LogisticRegression model
    """
    print("\n" + "="*70)
    print("SNAP PARTICIPATION MODEL")
    print("="*70)
    
    # Outcome
    y = cps_data['received_snap'].values
    
    print(f"\nOutcome: received_snap")
    print(f"  Participation rate: {y.mean():.1%}")
    print(f"  N receiving: {y.sum():,}")
    print(f"  N not receiving: {(1-y).sum():,}")
    
    # Predictors
    X = pd.DataFrame({
        'income': cps_data['INCTOT'] / 1000,  # In thousands for easier interpretation
        'black': cps_data['black'],
        'hispanic': cps_data['hispanic'],
        'asian': cps_data['asian'],
        'has_children': cps_data['has_children'],
        'has_disability': cps_data['has_disability'],
        'age': cps_data['AGE'],
        'female': cps_data['female'],
        'edu_hs': cps_data['edu_hs'],
        'edu_some_college': cps_data['edu_some_college'],
        'edu_ba': cps_data['edu_ba'],
        'edu_grad': cps_data['edu_grad'],
        # Reference: edu_less_than_hs
        'employed': cps_data['employed'],
        'not_in_labor_force': cps_data['not_in_labor_force'],
        # Reference: unemployed
    })
    
    print(f"\nPredictors ({X.shape[1]} variables):")
    for col in X.columns:
        print(f"  {col}")
    
    # Estimate logit
    print(f"\nEstimating logistic regression...")
    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(X, y)
    
    # Predictions
    y_pred = model.predict(X)
    y_prob = model.predict_proba(X)[:, 1]
    
    # Performance
    print(f"\nModel Performance:")
    print(f"  Accuracy: {(y_pred == y).mean():.1%}")
    print(f"  AUC-ROC: {roc_auc_score(y, y_prob):.3f}")
    
    # Coefficients
    print(f"\nKey Coefficients (Log-Odds):")
    coef_df = pd.DataFrame({
        'Variable': X.columns,
        'Coefficient': model.coef_[0],
        'Odds Ratio': np.exp(model.coef_[0])
    }).sort_values('Coefficient', ascending=False)
    
    print(coef_df.to_string(index=False))
    
    # Interpretation
    print(f"\nInterpretation (Odds Ratios):")
    print(f"  black: {np.exp(model.coef_[0][1]):.2f} → Black {np.exp(model.coef_[0][1]):.1f}x more likely to receive SNAP")
    print(f"  has_children: {np.exp(model.coef_[0][4]):.2f} → Having children {np.exp(model.coef_[0][4]):.1f}x more likely")
    print(f"  has_disability: {np.exp(model.coef_[0][5]):.2f} → Disability {np.exp(model.coef_[0][5]):.1f}x more likely")
    
    return model, X.columns.tolist()


def estimate_tanf_model(cps_data):
    """
    Estimate logit model for TANF (welfare) participation.
    
    Outcome: received_welfare
    """
    print("\n" + "="*70)
    print("TANF PARTICIPATION MODEL")
    print("="*70)
    
    y = cps_data['received_welfare'].values
    
    print(f"\nOutcome: received_welfare")
    print(f"  Participation rate: {y.mean():.1%}")
    print(f"  N receiving: {y.sum():,}")
    
    # Same predictors as SNAP
    X = pd.DataFrame({
        'income': cps_data['INCTOT'] / 1000,
        'black': cps_data['black'],
        'hispanic': cps_data['hispanic'],
        'asian': cps_data['asian'],
        'has_children': cps_data['has_children'],
        'has_disability': cps_data['has_disability'],
        'age': cps_data['AGE'],
        'female': cps_data['female'],
        'edu_hs': cps_data['edu_hs'],
        'edu_some_college': cps_data['edu_some_college'],
        'edu_ba': cps_data['edu_ba'],
        'edu_grad': cps_data['edu_grad'],
        'employed': cps_data['employed'],
        'not_in_labor_force': cps_data['not_in_labor_force'],
    })
    
    # Estimate
    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(X, y)
    
    y_pred = model.predict(X)
    y_prob = model.predict_proba(X)[:, 1]
    
    print(f"\nModel Performance:")
    print(f"  Accuracy: {(y_pred == y).mean():.1%}")
    if y.sum() > 0:
        print(f"  AUC-ROC: {roc_auc_score(y, y_prob):.3f}")
    
    # Top coefficients
    coef_df = pd.DataFrame({
        'Variable': X.columns,
        'Coefficient': model.coef_[0],
    }).sort_values('Coefficient', ascending=False)
    
    print(f"\nTop Positive Coefficients:")
    print(coef_df.head(5).to_string(index=False))
    
    return model, X.columns.tolist()


def estimate_ssi_model(cps_data):
    """
    Estimate logit model for SSI participation.
    
    Outcome: received_ssi
    """
    print("\n" + "="*70)
    print("SSI PARTICIPATION MODEL")
    print("="*70)
    
    y = cps_data['received_ssi'].values
    
    print(f"\nOutcome: received_ssi")
    print(f"  Participation rate: {y.mean():.1%}")
    print(f"  N receiving: {y.sum():,}")
    
    # Same predictors
    X = pd.DataFrame({
        'income': cps_data['INCTOT'] / 1000,
        'black': cps_data['black'],
        'hispanic': cps_data['hispanic'],
        'asian': cps_data['asian'],
        'has_children': cps_data['has_children'],
        'has_disability': cps_data['has_disability'],  # Should be VERY important for SSI
        'age': cps_data['AGE'],
        'female': cps_data['female'],
        'edu_hs': cps_data['edu_hs'],
        'edu_some_college': cps_data['edu_some_college'],
        'edu_ba': cps_data['edu_ba'],
        'edu_grad': cps_data['edu_grad'],
        'employed': cps_data['employed'],
        'not_in_labor_force': cps_data['not_in_labor_force'],
    })
    
    # Estimate
    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(X, y)
    
    y_pred = model.predict(X)
    y_prob = model.predict_proba(X)[:, 1]
    
    print(f"\nModel Performance:")
    print(f"  Accuracy: {(y_pred == y).mean():.1%}")
    if y.sum() > 0:
        print(f"  AUC-ROC: {roc_auc_score(y, y_prob):.3f}")
    
    # Top coefficients
    coef_df = pd.DataFrame({
        'Variable': X.columns,
        'Coefficient': model.coef_[0],
        'Odds Ratio': np.exp(model.coef_[0])
    }).sort_values('Coefficient', ascending=False)
    
    print(f"\nTop Coefficients:")
    print(coef_df.head(8).to_string(index=False))
    
    return model, X.columns.tolist()


def save_models(snap_model, tanf_model, ssi_model, feature_names):
    """
    Save estimated models for use in simulation.
    
    Args:
        snap_model: Fitted SNAP model
        tanf_model: Fitted TANF model
        ssi_model: Fitted SSI model
        feature_names: List of feature names
    """
    models = {
        'SNAP': {
            'model': snap_model,
            'features': feature_names
        },
        'TANF': {
            'model': tanf_model,
            'features': feature_names
        },
        'SSI': {
            'model': ssi_model,
            'features': feature_names
        }
    }
    
    with open('models/participation_models.pkl', 'wb') as f:
        pickle.dump(models, f)
    
    print("\n" + "="*70)
    print("Models saved to models/participation_models.pkl")
    print("="*70)


def main():
    """Estimate all models."""
    print("\n" + "="*70)
    print("CPS PROGRAM PARTICIPATION LOGIT MODELS")
    print("="*70)
    print("\nEstimating models to predict program participation based on:")
    print("  • Demographics (age, race, sex)")
    print("  • Economic (income, employment)")
    print("  • Family (children, marital status)")
    print("  • Human capital (education)")
    print("  • Health (disability)")
    
    # Load data
    cps = load_and_prepare_cps()
    
    # Estimate models
    snap_model, features = estimate_snap_model(cps)
    tanf_model, _ = estimate_tanf_model(cps)
    ssi_model, _ = estimate_ssi_model(cps)
    
    # Save models
    import os
    os.makedirs('models', exist_ok=True)
    save_models(snap_model, tanf_model, ssi_model, features)
    
    print("\n" + "="*70)
    print("COMPLETE!")
    print("="*70)
    print("\nYou now have logit models predicting program participation!")
    print("\nNext steps:")
    print("  1. Use these models in simulation (replace simple eligibility)")
    print("  2. Predict P(apply | characteristics) for each seeker")
    print("  3. Much more realistic application behavior!")


if __name__ == "__main__":
    main()