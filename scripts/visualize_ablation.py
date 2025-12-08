"""
Visualization: Ablation Study Results

Creates publication-ready figures showing mechanism contributions
to AI effects on welfare administration disparities.

Usage:
    python scripts/visualize_ablation.py
    python scripts/visualize_ablation.py --results results/ablation_study_results.csv

Output:
    - results/visualizations/mechanism_decomposition.png
    - results/visualizations/mechanism_contributions.png
    - results/visualizations/additivity_check.png

Requirements:
    - matplotlib
    - seaborn
    - pandas

Author: Jack Baldwin
Date: December 2024
"""

import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import argparse
from pathlib import Path

# Set publication-quality style
plt.style.use('seaborn-v0_8-paper')
sns.set_palette("husl")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.size'] = 10


def load_and_prepare_data(results_file):
    """Load ablation results and calculate summary statistics."""
    df = pd.read_csv(results_file)
    
    # Calculate summary statistics by mechanism
    summary = df.groupby('mechanism')['race_effect'].agg([
        'mean', 'std', 'count', 'min', 'max'
    ]).reset_index()
    
    summary['se'] = summary['std'] / np.sqrt(summary['count'])
    summary['ci_lower'] = summary['mean'] - 1.96 * summary['se']
    summary['ci_upper'] = summary['mean'] + 1.96 * summary['se']
    summary['t_stat'] = summary['mean'] / summary['se']
    summary['p_value'] = 2 * (1 - stats.t.cdf(
        abs(summary['t_stat']), 
        summary['count'] - 1
    ))
    
    # Add significance stars
    summary['sig'] = summary['p_value'].apply(
        lambda p: '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else 'ns'
    )
    
    return df, summary


def create_mechanism_decomposition_plot(summary, output_file):
    """
    Create main figure: Mechanism decomposition with error bars.
    
    Shows effect size for each mechanism configuration with 95% CIs.
    """
    # Order mechanisms logically
    mechanism_order = [
        'Baseline (no mechanisms)',
        'Only Bureaucracy Points',
        'Only Fraud History',
        'Only Bayesian Learning',
        'Only State Discrimination',
        'Full Model (all mechanisms)'
    ]
    
    # Filter and sort
    plot_data = summary[summary['mechanism'].isin(mechanism_order)].copy()
    plot_data['mechanism'] = pd.Categorical(
        plot_data['mechanism'], 
        categories=mechanism_order, 
        ordered=True
    )
    plot_data = plot_data.sort_values('mechanism')
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Define colors
    colors = {
        'Baseline (no mechanisms)': '#95a5a6',      # Gray (neutral)
        'Only Bureaucracy Points': '#e74c3c',       # Red (structural)
        'Only Fraud History': '#3498db',            # Blue (institutional)
        'Only Bayesian Learning': '#2ecc71',        # Green (behavioral)
        'Only State Discrimination': '#f39c12',     # Orange (cognitive)
        'Full Model (all mechanisms)': '#2c3e50'    # Dark (complete)
    }
    
    # Plot each mechanism
    x_pos = np.arange(len(plot_data))
    
    for i, row in plot_data.iterrows():
        mech = row['mechanism']
        mean = row['mean'] * 100  # Convert to pp
        ci_low = row['ci_lower'] * 100
        ci_high = row['ci_upper'] * 100
        
        # Error bar
        yerr = [[mean - ci_low], [ci_high - mean]]
        
        # Plot point
        ax.errorbar(
            x_pos[i], mean, yerr=yerr,
            fmt='o', markersize=12, capsize=8, capthick=2,
            color=colors.get(mech, 'black'),
            linewidth=2.5,
            label=f"{mech.split('(')[0].strip()} ({row['sig']})",
            zorder=3
        )
        
        # Add value label
        ax.text(
            x_pos[i], mean + (ci_high - mean) + 0.5,
            f"{mean:+.1f}pp",
            ha='center', va='bottom',
            fontsize=9, fontweight='bold'
        )
    
    # Reference line at zero
    ax.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5, zorder=1)
    
    # Styling
    ax.set_ylabel('AI Effect on Racial Disparity (percentage points)', 
                  fontsize=12, fontweight='bold')
    ax.set_xlabel('Mechanism Configuration', fontsize=12, fontweight='bold')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(
        [m.replace(' (', '\n(') for m in plot_data['mechanism']], 
        rotation=0, ha='center', fontsize=9
    )
    
    ax.set_title(
        'Mechanism Ablation Study:\nAI Effects on White-Black Approval Gap in Welfare Administration',
        fontsize=14, fontweight='bold', pad=20
    )
    
    ax.grid(axis='y', alpha=0.3, linestyle=':', zorder=0)
    ax.legend(loc='upper right', fontsize=9, framealpha=0.95)
    
    # Add note
    n_iter = int(plot_data.iloc[0]['count'])
    ax.text(
        0.02, 0.02,
        f'Note: Error bars show 95% confidence intervals (N={n_iter} iterations per configuration)\n'
        f'Negative values = AI reduces disparity (beneficial)\n'
        f'*** p<0.001, ** p<0.01, * p<0.05, ns p≥0.05',
        transform=ax.transAxes,
        fontsize=8, style='italic',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3)
    )
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Created: {output_file}")
    
    return fig


def create_contribution_breakdown(summary, output_file):
    """
    Create stacked/grouped bar showing contribution breakdown.
    
    Shows what % of total effect each mechanism contributes.
    """
    # Calculate contributions
    baseline_mean = summary[summary['mechanism'] == 'Baseline (no mechanisms)']['mean'].values[0]
    full_mean = summary[summary['mechanism'] == 'Full Model (all mechanisms)']['mean'].values[0]
    total_effect = full_mean - baseline_mean
    
    individual_mechs = [
        'Only Bureaucracy Points',
        'Only Fraud History',
        'Only Bayesian Learning',
        'Only State Discrimination'
    ]
    
    contributions = []
    for mech in individual_mechs:
        mech_data = summary[summary['mechanism'] == mech]
        if len(mech_data) > 0:
            mech_mean = mech_data['mean'].values[0]
            contribution = mech_mean - baseline_mean
            pct_of_total = (contribution / total_effect * 100) if abs(total_effect) > 0.01 else 0
            
            contributions.append({
                'mechanism': mech.replace('Only ', ''),
                'contribution_pp': contribution * 100,
                'pct_of_total': pct_of_total,
                'significant': mech_data['sig'].values[0] != 'ns'
            })
    
    contrib_df = pd.DataFrame(contributions)
    
    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # LEFT PANEL: Absolute contributions (pp)
    colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12']
    
    bars1 = ax1.barh(
        contrib_df['mechanism'],
        contrib_df['contribution_pp'],
        color=colors,
        alpha=0.8,
        edgecolor='black',
        linewidth=1.5
    )
    
    # Add significance markers
    for i, (idx, row) in enumerate(contrib_df.iterrows()):
        if row['significant']:
            ax1.text(
                row['contribution_pp'] + 0.2,
                i,
                '***' if row['contribution_pp'] < 0 else '***',
                va='center', fontsize=10, fontweight='bold'
            )
    
    ax1.axvline(x=0, color='black', linestyle='-', linewidth=1.5)
    ax1.set_xlabel('Contribution (percentage points)', fontsize=11, fontweight='bold')
    ax1.set_title('Absolute Contribution to AI Effect', fontsize=12, fontweight='bold')
    ax1.grid(axis='x', alpha=0.3, linestyle=':')
    
    # Add value labels
    for i, (idx, row) in enumerate(contrib_df.iterrows()):
        ax1.text(
            row['contribution_pp'] - 0.3 if row['contribution_pp'] < 0 else row['contribution_pp'] + 0.3,
            i,
            f"{row['contribution_pp']:+.2f}pp",
            va='center',
            ha='right' if row['contribution_pp'] < 0 else 'left',
            fontsize=9,
            fontweight='bold'
        )
    
    # RIGHT PANEL: Percentage of total effect
    bars2 = ax2.barh(
        contrib_df['mechanism'],
        contrib_df['pct_of_total'],
        color=colors,
        alpha=0.8,
        edgecolor='black',
        linewidth=1.5
    )
    
    ax2.axvline(x=0, color='black', linestyle='-', linewidth=1.5)
    ax2.set_xlabel('Percentage of Total Effect (%)', fontsize=11, fontweight='bold')
    ax2.set_title('Relative Contribution', fontsize=12, fontweight='bold')
    ax2.grid(axis='x', alpha=0.3, linestyle=':')
    
    # Add percentage labels
    for i, (idx, row) in enumerate(contrib_df.iterrows()):
        ax2.text(
            row['pct_of_total'] - 2 if row['pct_of_total'] < 0 else row['pct_of_total'] + 2,
            i,
            f"{row['pct_of_total']:.1f}%",
            va='center',
            ha='right' if row['pct_of_total'] < 0 else 'left',
            fontsize=9,
            fontweight='bold'
        )
    
    plt.suptitle(
        f'Mechanism Decomposition: Total Effect = {total_effect*100:+.2f}pp',
        fontsize=14, fontweight='bold', y=1.02
    )
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Created: {output_file}")
    
    return fig


def create_additivity_diagnostic(summary, df, output_file):
    """
    Create diagnostic plot showing whether mechanisms are additive.
    
    Compares sum of individual effects to full model effect.
    """
    # Calculate additivity
    baseline_mean = summary[summary['mechanism'] == 'Baseline (no mechanisms)']['mean'].values[0]
    full_mean = summary[summary['mechanism'] == 'Full Model (all mechanisms)']['mean'].values[0]
    total_effect = full_mean - baseline_mean
    
    individual_mechs = [
        'Only Bureaucracy Points',
        'Only Fraud History',
        'Only Bayesian Learning',
        'Only State Discrimination'
    ]
    
    individual_effects = []
    for mech in individual_mechs:
        mech_data = summary[summary['mechanism'] == mech]
        if len(mech_data) > 0:
            mech_mean = mech_data['mean'].values[0]
            contribution = mech_mean - baseline_mean
            individual_effects.append(contribution)
    
    sum_individual = sum(individual_effects)
    interaction = total_effect - sum_individual
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot components
    x_positions = [0, 1, 2, 3, 4, 5.5, 7]
    labels = [
        'Baseline',
        'Bureaucracy',
        'Fraud',
        'Learning',
        'Discrimination',
        'Sum of\nIndividual',
        'Full Model\n(Observed)'
    ]
    
    values = [
        baseline_mean * 100,
        individual_effects[0] * 100 if len(individual_effects) > 0 else 0,
        individual_effects[1] * 100 if len(individual_effects) > 1 else 0,
        individual_effects[2] * 100 if len(individual_effects) > 2 else 0,
        individual_effects[3] * 100 if len(individual_effects) > 3 else 0,
        sum_individual * 100,
        full_mean * 100
    ]
    
    colors_list = ['#95a5a6', '#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#2c3e50']
    
    bars = ax.bar(x_positions, values, color=colors_list, alpha=0.8, 
                  edgecolor='black', linewidth=1.5, width=0.8)
    
    # Add value labels on bars
    for i, (x, v) in enumerate(zip(x_positions, values)):
        ax.text(x, v + 0.3 if v > 0 else v - 0.3, 
                f'{v:+.1f}pp',
                ha='center', va='bottom' if v > 0 else 'top',
                fontsize=9, fontweight='bold')
    
    # Add interaction arrow and label
    if abs(interaction) > 0.01:
        ax.annotate(
            '',
            xy=(7, sum_individual * 100),
            xytext=(7, full_mean * 100),
            arrowprops=dict(
                arrowstyle='<->',
                color='red',
                lw=2,
                linestyle='--'
            )
        )
        
        ax.text(
            7.5, (sum_individual + full_mean) * 50,
            f'Interaction:\n{interaction*100:+.2f}pp',
            fontsize=9,
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7)
        )
    
    # Styling
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1, zorder=0)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel('Effect on Racial Disparity (percentage points)', 
                  fontsize=12, fontweight='bold')
    ax.set_title('Additivity Check: Sum of Individual vs. Full Model',
                fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3, linestyle=':')
    
    # Add interpretation text
    if abs(interaction) < 0.01:
        interp = "Mechanisms are ADDITIVE (independent)"
    elif interaction < 0:
        interp = "Mechanisms SYNERGIZE (amplify each other)"
    else:
        interp = "Mechanisms INTERFERE (partially cancel)"
    
    ax.text(
        0.5, 0.98,
        f'Total Effect: {total_effect*100:+.2f}pp | '
        f'Sum of Parts: {sum_individual*100:+.2f}pp | '
        f'Interaction: {interaction*100:+.2f}pp\n{interp}',
        transform=ax.transAxes,
        ha='center', va='top',
        fontsize=10,
        bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8)
    )
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Created: {output_file}")
    
    return fig


def create_distribution_plots(df, output_file):
    """
    Create violin/box plots showing distribution of effects across iterations.
    
    Shows variance and outliers for each mechanism.
    """
    mechanism_order = [
        'Baseline (no mechanisms)',
        'Only Bureaucracy Points',
        'Only Fraud History',
        'Only Bayesian Learning',
        'Only State Discrimination',
        'Full Model (all mechanisms)'
    ]
    
    # Filter data
    plot_data = df[df['mechanism'].isin(mechanism_order)].copy()
    plot_data['mechanism'] = pd.Categorical(
        plot_data['mechanism'],
        categories=mechanism_order,
        ordered=True
    )
    plot_data['race_effect_pp'] = plot_data['race_effect'] * 100
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # Violin plot
    parts = ax.violinplot(
        [plot_data[plot_data['mechanism'] == m]['race_effect_pp'].values 
         for m in mechanism_order],
        positions=range(len(mechanism_order)),
        widths=0.7,
        showmeans=True,
        showextrema=True
    )
    
    # Color the violins
    colors = ['#95a5a6', '#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#2c3e50']
    for i, pc in enumerate(parts['bodies']):
        pc.set_facecolor(colors[i])
        pc.set_alpha(0.7)
        pc.set_edgecolor('black')
        pc.set_linewidth(1.5)
    
    # Overlay box plot for quartiles
    bp = ax.boxplot(
        [plot_data[plot_data['mechanism'] == m]['race_effect_pp'].values 
         for m in mechanism_order],
        positions=range(len(mechanism_order)),
        widths=0.3,
        patch_artist=False,
        showfliers=True,
        boxprops=dict(linewidth=2),
        whiskerprops=dict(linewidth=1.5),
        capprops=dict(linewidth=1.5),
        medianprops=dict(linewidth=2.5, color='red')
    )
    
    # Styling
    ax.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    ax.set_xticks(range(len(mechanism_order)))
    ax.set_xticklabels(
        [m.replace(' (', '\n(') for m in mechanism_order],
        rotation=0, ha='center', fontsize=9
    )
    ax.set_ylabel('AI Effect on Racial Disparity (percentage points)',
                  fontsize=12, fontweight='bold')
    ax.set_title('Distribution of Effects Across Monte Carlo Iterations',
                fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3, linestyle=':')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Created: {output_file}")
    
    return fig


def create_summary_table_figure(summary, output_file):
    """
    Create a publication-ready table as a figure.
    """
    mechanism_order = [
        'Baseline (no mechanisms)',
        'Only Bureaucracy Points',
        'Only Fraud History',
        'Only Bayesian Learning',
        'Only State Discrimination',
        'Full Model (all mechanisms)'
    ]
    
    # Prepare table data
    table_data = []
    for mech in mechanism_order:
        row_data = summary[summary['mechanism'] == mech]
        if len(row_data) > 0:
            row = row_data.iloc[0]
            table_data.append([
                mech.replace('Only ', '').replace(' (no mechanisms)', ''),
                f"{row['mean']*100:+.2f}",
                f"[{row['ci_lower']*100:+.2f}, {row['ci_upper']*100:+.2f}]",
                f"{row['t_stat']:+.2f}",
                f"{row['p_value']:.4f}",
                row['sig'],
                int(row['count'])
            ])
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.axis('tight')
    ax.axis('off')
    
    # Create table
    table = ax.table(
        cellText=table_data,
        colLabels=['Mechanism', 'Effect (pp)', '95% CI', 't-stat', 'p-value', 'Sig', 'N'],
        cellLoc='center',
        loc='center',
        colWidths=[0.35, 0.12, 0.20, 0.10, 0.12, 0.06, 0.05]
    )
    
    # Style table
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    
    # Header styling
    for i in range(7):
        cell = table[(0, i)]
        cell.set_facecolor('#2c3e50')
        cell.set_text_props(weight='bold', color='white')
    
    # Row styling (alternate colors)
    for i in range(1, len(table_data) + 1):
        for j in range(7):
            cell = table[(i, j)]
            if i % 2 == 0:
                cell.set_facecolor('#ecf0f1')
            else:
                cell.set_facecolor('white')
            
            # Highlight significant results
            if j == 5:  # Significance column
                if table_data[i-1][5] in ['*', '**', '***']:
                    cell.set_text_props(weight='bold', color='red')
    
    plt.title('Ablation Study Results: Statistical Summary',
             fontsize=14, fontweight='bold', pad=20)
    
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Created: {output_file}")
    
    return fig


def main():
    parser = argparse.ArgumentParser(
        description='Create visualizations from ablation study results'
    )
    parser.add_argument(
        '--results',
        default='results/ablation_study_results.csv',
        help='Path to ablation results CSV'
    )
    args = parser.parse_args()
    
    # Check if results exist
    if not Path(args.results).exists():
        print(f"❌ Results file not found: {args.results}")
        print(f"   Run ablation study first:")
        print(f"   python experiments/ablation_study.py --iterations 20 --seekers 10000")
        return
    
    print("="*70)
    print("CREATING ABLATION VISUALIZATIONS")
    print("="*70)
    
    # Load data
    print(f"\nLoading results from: {args.results}")
    df, summary = load_and_prepare_data(args.results)
    print(f"✓ Loaded {len(df)} observations across {len(summary)} configurations")
    
    # Create output directory
    output_dir = Path('results/visualizations')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create visualizations
    print(f"\nCreating visualizations...")
    
    fig1 = create_mechanism_decomposition_plot(
        summary,
        output_dir / 'mechanism_decomposition.png'
    )
    
    fig2 = create_contribution_breakdown(
        summary,
        output_dir / 'mechanism_contributions.png'
    )
    
    fig3 = create_distribution_plots(
        df,
        output_dir / 'effect_distributions.png'
    )
    
    fig4 = create_summary_table_figure(
        summary,
        output_dir / 'results_table.png'
    )
    
    # Summary
    print(f"\n{'='*70}")
    print("VISUALIZATION COMPLETE")
    print("="*70)
    print(f"\nCreated 4 publication-ready figures:")
    print(f"  1. mechanism_decomposition.png - Main results figure")
    print(f"  2. mechanism_contributions.png - Contribution breakdown")
    print(f"  3. effect_distributions.png - Variance visualization")
    print(f"  4. results_table.png - Statistical summary table")
    print(f"\nAll saved to: {output_dir}/")
    
    # Quick stats
    print(f"\n{'='*70}")
    print("QUICK SUMMARY")
    print("="*70)
    
    baseline_mean = summary[summary['mechanism'] == 'Baseline (no mechanisms)']['mean'].values[0]
    full_mean = summary[summary['mechanism'] == 'Full Model (all mechanisms)']['mean'].values[0]
    
    print(f"\nBaseline (no AI): {baseline_mean*100:+.2f}pp gap")
    print(f"Full Model (with AI): {full_mean*100:+.2f}pp gap")
    print(f"AI Total Effect: {(full_mean - baseline_mean)*100:+.2f}pp")
    
    print(f"\nMechanism contributions:")
    for mech in ['Only Bureaucracy Points', 'Only Fraud History', 
                 'Only Bayesian Learning', 'Only State Discrimination']:
        mech_data = summary[summary['mechanism'] == mech]
        if len(mech_data) > 0:
            mech_mean = mech_data['mean'].values[0]
            contribution = mech_mean - baseline_mean
            sig = mech_data['sig'].values[0]
            print(f"  {mech.replace('Only ', ''):20s}: {contribution*100:+.2f}pp {sig}")
    
    plt.show()


if __name__ == '__main__':
    main()