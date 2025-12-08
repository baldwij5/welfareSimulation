"""
Visualize Sensitivity Analysis Results

Creates publication-ready figures showing parameter robustness.

Usage:
    python scripts/visualize_sensitivity.py

Output:
    - results/visualizations/tornado_diagram.png (parameter importance)
    - results/visualizations/sensitivity_by_parameter.png (detailed plots)
    - results/visualizations/robustness_bounds.png (summary table)

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
from scipy import stats

# Set style
plt.style.use('seaborn-v0_8-paper')
plt.rcParams['figure.dpi'] = 300


def create_tornado_diagram(results_df, output_file):
    """
    Create tornado diagram showing which parameters matter most.
    
    Width of bar = range of effects across parameter values
    """
    # Calculate range for each parameter
    param_ranges = []
    
    for param in results_df['parameter'].unique():
        param_df = results_df[results_df['parameter'] == param]
        summary = param_df.groupby('value')['race_effect'].mean()
        
        min_effect = summary.min()
        max_effect = summary.max()
        range_width = max_effect - min_effect
        baseline = summary.median()  # Use median as baseline
        
        param_ranges.append({
            'parameter': param,
            'baseline': baseline,
            'min': min_effect,
            'max': max_effect,
            'range': range_width
        })
    
    # Sort by range (most important first)
    tornado_df = pd.DataFrame(param_ranges).sort_values('range', ascending=True)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))
    
    y_pos = np.arange(len(tornado_df))
    
    # For each parameter, draw bar from min to max
    for i, row in enumerate(tornado_df.itertuples()):
        param = row.parameter
        baseline = row.baseline * 100
        min_val = row.min * 100
        max_val = row.max * 100
        
        # Left side (negative)
        left_width = baseline - min_val
        ax.barh(i, left_width, left=min_val, height=0.6,
               color='#e74c3c', alpha=0.7, edgecolor='black', linewidth=1.5)
        
        # Right side (positive)
        right_width = max_val - baseline
        ax.barh(i, right_width, left=baseline, height=0.6,
               color='#3498db', alpha=0.7, edgecolor='black', linewidth=1.5)
        
        # Baseline marker
        ax.plot(baseline, i, 'D', markersize=10, color='black', zorder=5)
        
        # Range label
        ax.text(max_val + 0.3, i, f"[{min_val:+.1f}, {max_val:+.1f}]",
               va='center', fontsize=9)
    
    # Zero line
    ax.axvline(x=0, color='black', linestyle='-', linewidth=1.5, zorder=0)
    
    # Styling
    ax.set_yticks(y_pos)
    ax.set_yticklabels(tornado_df['parameter'], fontsize=11)
    ax.set_xlabel('AI Effect on Racial Disparity (percentage points)', 
                  fontsize=12, fontweight='bold')
    ax.set_title('Tornado Diagram: Parameter Sensitivity\n(Wider bars = more influential)',
                fontsize=14, fontweight='bold')
    ax.grid(axis='x', alpha=0.3, linestyle=':')
    
    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#e74c3c', alpha=0.7, label='Below baseline'),
        Patch(facecolor='#3498db', alpha=0.7, label='Above baseline'),
        plt.Line2D([0], [0], marker='D', color='w', markerfacecolor='black',
                  markersize=8, label='Baseline value')
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Created: {output_file}")


def create_parameter_plots(results_df, output_file):
    """Create detailed plots for each parameter."""
    params = results_df['parameter'].unique()
    n_params = len(params)
    
    fig, axes = plt.subplots(n_params, 1, figsize=(12, 4*n_params))
    
    if n_params == 1:
        axes = [axes]
    
    for ax, param in zip(axes, params):
        param_df = results_df[results_df['parameter'] == param]
        
        # Calculate mean and CI for each value
        summary = param_df.groupby('value')['race_effect'].agg(['mean', 'std', 'count'])
        summary['se'] = summary['std'] / np.sqrt(summary['count'])
        summary['ci_lower'] = summary['mean'] - 1.96 * summary['se']
        summary['ci_upper'] = summary['mean'] + 1.96 * summary['se']
        
        # Plot
        x = summary.index
        y = summary['mean'] * 100
        yerr = [
            (summary['mean'] - summary['ci_lower']) * 100,
            (summary['ci_upper'] - summary['mean']) * 100
        ]
        
        ax.errorbar(x, y, yerr=yerr, fmt='o-', linewidth=2.5, markersize=10,
                   capsize=8, capthick=2, color='#2c3e50')
        
        # Fill between CI
        ax.fill_between(x, summary['ci_lower']*100, summary['ci_upper']*100,
                       alpha=0.2, color='gray')
        
        # Zero line
        ax.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
        
        # Styling
        ax.set_xlabel(f'{param}', fontsize=11, fontweight='bold')
        ax.set_ylabel('AI Effect on Racial Disparity (pp)', fontsize=10, fontweight='bold')
        ax.set_title(f'Sensitivity to {param}', fontsize=12, fontweight='bold')
        ax.grid(alpha=0.3, linestyle=':')
        
        # Annotate range
        min_y = summary['mean'].min() * 100
        max_y = summary['mean'].max() * 100
        range_y = max_y - min_y
        ax.text(0.02, 0.98, f'Range: {range_y:.2f}pp',
               transform=ax.transAxes, va='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Created: {output_file}")


def create_robustness_table(results_df, output_file):
    """Create summary table showing robustness bounds."""
    # Calculate summary by parameter
    table_data = []
    
    for param in results_df['parameter'].unique():
        param_df = results_df[results_df['parameter'] == param]
        summary = param_df.groupby('value')['race_effect'].agg(['mean', 'std', 'count'])
        
        # Get baseline (middle value)
        values = sorted(param_df['value'].unique())
        baseline_val = values[len(values)//2]
        baseline_effect = summary.loc[baseline_val, 'mean']
        
        # Get range
        min_effect = summary['mean'].min()
        max_effect = summary['mean'].max()
        range_width = max_effect - min_effect
        
        # Check robustness
        all_same_sign = (summary['mean'].min() > 0) or (summary['mean'].max() < 0)
        narrow = range_width < 0.03  # Less than 3pp
        robust = all_same_sign and narrow
        
        table_data.append({
            'Parameter': param,
            'Baseline Effect': f"{baseline_effect*100:+.2f}pp",
            'Min Effect': f"{min_effect*100:+.2f}pp",
            'Max Effect': f"{max_effect*100:+.2f}pp",
            'Range': f"{range_width*100:.2f}pp",
            'Robust': '✓' if robust else '✗'
        })
    
    table_df = pd.DataFrame(table_data)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.axis('tight')
    ax.axis('off')
    
    mpl_table = ax.table(
        cellText=table_df.values,
        colLabels=table_df.columns,
        cellLoc='center',
        loc='center',
        colWidths=[0.25, 0.15, 0.15, 0.15, 0.12, 0.10]
    )
    
    mpl_table.auto_set_font_size(False)
    mpl_table.set_fontsize(10)
    mpl_table.scale(1, 2.5)
    
    # Style
    for i in range(len(table_df.columns)):
        mpl_table[(0, i)].set_facecolor('#2c3e50')
        mpl_table[(0, i)].set_text_props(weight='bold', color='white')
    
    for i in range(1, len(table_df) + 1):
        for j in range(len(table_df.columns)):
            if i % 2 == 0:
                mpl_table[(i, j)].set_facecolor('#ecf0f1')
    
    plt.title('Parameter Sensitivity: Robustness Bounds',
             fontsize=14, fontweight='bold', pad=20)
    
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Created: {output_file}")


def main():
    results_file = 'results/sensitivity_analysis_results.csv'
    
    if not Path(results_file).exists():
        print(f"❌ Results not found: {results_file}")
        print(f"   Run sensitivity analysis first:")
        print(f"   python experiments/sensitivity_analysis.py --priority 1")
        return
    
    print("="*70)
    print("VISUALIZING SENSITIVITY ANALYSIS")
    print("="*70)
    
    df = pd.read_csv(results_file)
    print(f"✓ Loaded {len(df)} experiments")
    print(f"  Parameters tested: {df['parameter'].nunique()}")
    print(f"  Values per parameter: ~{len(df) / df['parameter'].nunique() / 10:.0f}")
    
    # Create output directory
    output_dir = Path('results/visualizations')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create visualizations
    print(f"\nCreating visualizations...")
    
    create_tornado_diagram(df, output_dir / 'tornado_diagram.png')
    create_parameter_plots(df, output_dir / 'sensitivity_by_parameter.png')
    create_robustness_table(df, output_dir / 'robustness_bounds.png')
    
    print(f"\n{'='*70}")
    print("VISUALIZATION COMPLETE")
    print("="*70)
    print(f"\nFigures saved to: {output_dir}/")


if __name__ == '__main__':
    main()