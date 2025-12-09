"""
Visualize Monte Carlo Results

Creates diagnostic plots for Monte Carlo validation.

Usage:
    python scripts/visualize_monte_carlo.py

Output:
    - results/visualizations/monte_carlo_variance.png
    - results/visualizations/monte_carlo_all_effects.png

Author: Jack Baldwin
Date: December 2024
"""

import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set style
plt.style.use('seaborn-v0_8-paper')
plt.rcParams['figure.dpi'] = 300


def plot_variance_diagnostic(df, output_file):
    """Plot showing variance across iterations."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Top-left: Race effect over iterations
    ax = axes[0, 0]
    ax.plot(df['iteration'], df['race_effect'] * 100, 
            'o-', linewidth=2, markersize=8, color='#e74c3c', alpha=0.7)
    ax.axhline(y=df['race_effect'].mean() * 100, 
               color='black', linestyle='--', linewidth=2, label='Mean')
    ax.fill_between(
        df['iteration'],
        (df['race_effect'].mean() - df['race_effect'].std()) * 100,
        (df['race_effect'].mean() + df['race_effect'].std()) * 100,
        alpha=0.2, color='gray', label='±1 SD'
    )
    ax.set_xlabel('Iteration', fontweight='bold')
    ax.set_ylabel('Race Effect (pp)', fontweight='bold')
    ax.set_title('Effect Across Iterations', fontweight='bold')
    ax.grid(alpha=0.3)
    ax.legend()
    
    # Top-right: Distribution histogram
    ax = axes[0, 1]
    ax.hist(df['race_effect'] * 100, bins=15, 
            color='#3498db', alpha=0.7, edgecolor='black')
    ax.axvline(df['race_effect'].mean() * 100, 
               color='red', linestyle='--', linewidth=2, label='Mean')
    ax.set_xlabel('Race Effect (pp)', fontweight='bold')
    ax.set_ylabel('Frequency', fontweight='bold')
    ax.set_title('Distribution of Effects', fontweight='bold')
    ax.legend()
    ax.grid(alpha=0.3)
    
    # Bottom-left: Control vs Treatment gaps
    ax = axes[1, 0]
    ax.scatter(df['control_race_gap'] * 100, df['treatment_race_gap'] * 100,
              s=100, alpha=0.6, color='#2ecc71', edgecolor='black')
    
    # Add diagonal line (no effect)
    lims = [
        min(ax.get_xlim()[0], ax.get_ylim()[0]),
        max(ax.get_xlim()[1], ax.get_ylim()[1])
    ]
    ax.plot(lims, lims, 'k--', alpha=0.5, linewidth=1, label='No AI effect')
    
    ax.set_xlabel('Control Gap (pp)', fontweight='bold')
    ax.set_ylabel('Treatment Gap (pp)', fontweight='bold')
    ax.set_title('Treatment vs Control Disparity', fontweight='bold')
    ax.legend()
    ax.grid(alpha=0.3)
    
    # Bottom-right: Variance metrics
    ax = axes[1, 1]
    ax.axis('off')
    
    # Calculate variance metrics
    mean_effect = df['race_effect'].mean()
    std_effect = df['race_effect'].std()
    cv = std_effect / abs(mean_effect) if mean_effect != 0 else float('inf')
    min_effect = df['race_effect'].min()
    max_effect = df['race_effect'].max()
    range_effect = max_effect - min_effect
    
    stats_text = f"""
    VARIANCE DIAGNOSTICS
    {'─'*40}
    
    Mean Effect:     {mean_effect*100:+.2f}pp
    Std Dev:         {std_effect*100:.4f}pp
    CV:              {cv:.3f}
    Range:           {range_effect*100:.4f}pp
    Min:             {min_effect*100:+.2f}pp
    Max:             {max_effect*100:+.2f}pp
    
    N iterations:    {len(df)}
    
    {'─'*40}
    ASSESSMENT:
    """
    
    # Diagnostic assessment
    if std_effect < 0.0001:
        assessment = "❌ ZERO variance - BUG!"
    elif std_effect < 0.001:
        assessment = "⚠️  Very low variance"
    elif std_effect > 0.05:
        assessment = "⚠️  High variance (noisy)"
    else:
        assessment = "✓ Healthy variance"
    
    stats_text += assessment
    
    ax.text(0.1, 0.5, stats_text, 
            fontsize=11, family='monospace',
            verticalalignment='center',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.suptitle('Monte Carlo Variance Diagnostic', 
                fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Created: {output_file}")
    
    return fig


def plot_all_effects(df, output_file):
    """Plot all 4 effects."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    effects = [
        ('race_effect', 'Race (White-Black)', axes[0, 0], '#e74c3c'),
        ('education_effect', 'Education (College-<HS)', axes[0, 1], '#3498db'),
        ('employment_effect', 'Employment (Employed-Unemployed)', axes[1, 0], '#2ecc71'),
        ('disability_effect', 'Disability (No Disability-Has Disability)', axes[1, 1], '#f39c12')
    ]
    
    for effect_col, title, ax, color in effects:
        if effect_col in df.columns:
            values = df[effect_col] * 100
            mean_val = values.mean()
            std_val = values.std()
            
            ax.plot(df['iteration'], values, 
                   'o-', linewidth=2, markersize=6, color=color, alpha=0.7)
            ax.axhline(y=mean_val, color='black', linestyle='--', linewidth=2)
            ax.fill_between(
                df['iteration'],
                mean_val - std_val,
                mean_val + std_val,
                alpha=0.2, color='gray'
            )
            
            ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5, alpha=0.5)
            ax.set_xlabel('Iteration', fontweight='bold')
            ax.set_ylabel('Effect (pp)', fontweight='bold')
            ax.set_title(f'{title}\nMean: {mean_val:+.2f}pp ± {std_val:.2f}pp', 
                        fontweight='bold')
            ax.grid(alpha=0.3)
    
    plt.suptitle('AI Effects on Multiple Disparities', 
                fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Created: {output_file}")
    
    return fig


def main():
    results_file = 'results/monte_carlo_ma_results.csv'
    
    if not Path(results_file).exists():
        print(f"❌ Results not found: {results_file}")
        return
    
    print("="*70)
    print("VISUALIZING MONTE CARLO RESULTS")
    print("="*70)
    
    df = pd.read_csv(results_file)
    print(f"✓ Loaded {len(df)} iterations")
    
    # Create output directory
    output_dir = Path('results/visualizations')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nCreating visualizations...")
    
    plot_variance_diagnostic(df, output_dir / 'monte_carlo_variance.png')
    plot_all_effects(df, output_dir / 'monte_carlo_all_effects.png')
    
    # Variance check
    std_race = df['race_effect'].std()
    print(f"\n{'='*70}")
    print("VARIANCE CHECK")
    print("="*70)
    print(f"Race effect std dev: {std_race*100:.4f}pp")
    
    if std_race < 0.0001:
        print(f"❌ ZERO variance - seed bug still present!")
    elif std_race < 0.001:
        print(f"⚠️  Very low variance ({std_race*100:.4f}pp)")
    elif std_race > 0.05:
        print(f"⚠️  High variance ({std_race*100:.2f}pp)")
    else:
        print(f"✓ Healthy variance ({std_race*100:.4f}pp)")
    
    print(f"\n{'='*70}")
    print("COMPLETE")
    print("="*70)
    print(f"\nFigures saved to: {output_dir}/")


if __name__ == '__main__':
    main()