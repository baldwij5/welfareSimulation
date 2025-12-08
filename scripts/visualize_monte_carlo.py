"""
Enhanced Monte Carlo Visualization with Administrative Outcomes

Creates detailed breakdown of application processing outcomes:
- Honest vs fraud vs error applications
- Approval/denial/escalation rates
- Reviewer outcomes
- False positive/negative rates

Usage:
    python scripts/visualize_monte_carlo_enhanced.py

Output:
    - Administrative outcomes table (console + CSV)
    - Detailed processing breakdown figure
    - Fraud detection performance metrics

Author: Jack Baldwin
Date: December 2024
"""

import warnings
warnings.filterwarnings('ignore')

import sys
sys.path.insert(0, 'src')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
from pathlib import Path

# Set style
plt.style.use('seaborn-v0_8-paper')
plt.rcParams['figure.dpi'] = 300


def load_monte_carlo_results(results_file):
    """Load and validate Monte Carlo results."""
    if not Path(results_file).exists():
        print(f"❌ Results file not found: {results_file}")
        print(f"   Run Monte Carlo first")
        return None
    
    df = pd.read_csv(results_file)
    print(f"✓ Loaded {len(df)} iterations")
    
    return df


def extract_administrative_outcomes(results_file):
    """
    Extract detailed administrative outcomes from Monte Carlo results.
    
    NOTE: This requires running Monte Carlo with detailed tracking.
    If your current results don't have this data, we'll need to add
    tracking to monte_carlo_ma_progress.py and re-run.
    
    Returns:
        DataFrame with detailed outcomes or None if data not available
    """
    # Check if detailed results file exists
    detailed_file = results_file.replace('.csv', '_detailed.csv')
    
    if Path(detailed_file).exists():
        return pd.read_csv(detailed_file)
    else:
        print(f"⚠️  Detailed outcomes file not found: {detailed_file}")
        print(f"   Need to add detailed tracking to Monte Carlo script")
        return None


def create_administrative_outcomes_table(control_stats, treatment_stats, output_file=None):
    """
    Create detailed table showing application processing outcomes.
    
    Args:
        control_stats: Dict with control world statistics
        treatment_stats: Dict with treatment world statistics
        output_file: Optional path to save figure
        
    Returns:
        DataFrame with outcomes table
    """
    # Structure of outcomes table
    table_data = {
        'Application Type': [
            'Honest Applications',
            '  → Approved',
            '  → Denied',
            '  → Escalated',
            '',
            'Fraud Applications',
            '  → Approved (missed)',
            '  → Denied (caught)',
            '  → Escalated',
            '',
            'Error Applications',
            '  → Approved',
            '  → Denied',
            '  → Escalated',
            '',
            'TOTAL Applications',
        ],
        'Control (FCFS)': [],
        'Treatment (AI)': [],
        'Difference': []
    }
    
    # This will be populated from detailed results
    # For now, showing the structure
    
    df = pd.DataFrame(table_data)
    
    if output_file:
        # Create figure version
        fig, ax = plt.subplots(figsize=(12, 10))
        ax.axis('tight')
        ax.axis('off')
        
        # Create table
        table = ax.table(
            cellText=df.values,
            colLabels=df.columns,
            cellLoc='left',
            loc='center',
            colWidths=[0.4, 0.2, 0.2, 0.2]
        )
        
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2)
        
        # Style header
        for i in range(len(df.columns)):
            cell = table[(0, i)]
            cell.set_facecolor('#2c3e50')
            cell.set_text_props(weight='bold', color='white')
        
        plt.title('Administrative Outcomes: Control vs Treatment',
                 fontsize=14, fontweight='bold', pad=20)
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✓ Created: {output_file}")
    
    return df


def create_processing_flowchart(stats, output_file):
    """
    Create Sankey-style flowchart showing application processing.
    
    Shows:
      Applications → Evaluator → [Approved/Denied/Escalated]
                              ↓
      Escalated → Reviewer → [Approved/Denied]
    """
    # This would create a Sankey diagram
    # Showing flow from applications through system
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Left: Control world
    ax1.set_title('Control (FCFS)', fontsize=14, fontweight='bold')
    # ... create flowchart ...
    
    # Right: Treatment world  
    ax2.set_title('Treatment (AI Sorting)', fontsize=14, fontweight='bold')
    # ... create flowchart ...
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Created: {output_file}")


def calculate_fraud_detection_metrics(df):
    """
    Calculate fraud detection performance metrics.
    
    Metrics:
    - True Positive Rate (fraud caught / total fraud)
    - False Positive Rate (honest denied / total honest)
    - Precision (fraud caught / total denied)
    - F1 Score
    """
    # This requires detailed tracking in Monte Carlo
    pass


def main():
    parser = argparse.ArgumentParser(
        description='Enhanced Monte Carlo visualization with administrative outcomes'
    )
    parser.add_argument(
        '--results',
        default='results/monte_carlo_ma_results.csv',
        help='Path to Monte Carlo results'
    )
    args = parser.parse_args()
    
    print("="*70)
    print("ENHANCED MONTE CARLO VISUALIZATION")
    print("="*70)
    
    # Load results
    df = load_monte_carlo_results(args.results)
    if df is None:
        return
    
    # Create output directory
    output_dir = Path('results/visualizations')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Try to load detailed outcomes
    detailed = extract_administrative_outcomes(args.results)
    
    if detailed is None:
        print(f"\n{'='*70}")
        print("NOTE: Detailed Tracking Not Available")
        print("="*70)
        print(f"\nYour current Monte Carlo results don't include detailed")
        print(f"application-level tracking (honest/fraud/error breakdowns).")
        print(f"\nTo get this data, we need to:")
        print(f"  1. Add detailed tracking to monte_carlo_ma_progress.py")
        print(f"  2. Save application-level statistics per iteration")
        print(f"  3. Re-run Monte Carlo (or extract from next run)")
        print(f"\nFor now, creating visualizations from available data...")
    else:
        print(f"✓ Loaded detailed outcomes: {len(detailed)} records")
        
        # Create detailed tables and figures
        create_administrative_outcomes_table(
            detailed[detailed['world'] == 'control'].iloc[0],
            detailed[detailed['world'] == 'treatment'].iloc[0],
            output_dir / 'administrative_outcomes_table.png'
        )
    
    # Create standard visualizations (these work with current data)
    from visualize_monte_carlo import (
        plot_variance_diagnostic,
        plot_all_effects
    )
    
    plot_variance_diagnostic(df, output_dir / 'monte_carlo_variance.png')
    plot_all_effects(df, output_dir / 'monte_carlo_all_effects.png')
    
    print(f"\n{'='*70}")
    print("VISUALIZATION COMPLETE")
    print("="*70)
    print(f"\nFigures saved to: {output_dir}/")


if __name__ == '__main__':
    main()