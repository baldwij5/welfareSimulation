"""
Post-Process Monte Carlo: Administrative Outcomes Table

Creates detailed administrative outcomes table from completed Monte Carlo.

Usage:
    python scripts/post_process_monte_carlo.py

Output:
    - Console table
    - results/administrative_outcomes_table.csv
    - results/visualizations/administrative_outcomes_table.png

Author: Jack Baldwin
Date: December 2024
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy import stats


def create_administrative_outcomes_table(results_csv='results/monte_carlo_ma_results.csv'):
    """Create detailed administrative outcomes table."""
    if not Path(results_csv).exists():
        print(f"❌ Results not found: {results_csv}")
        return None
    
    df = pd.read_csv(results_csv)
    
    # Calculate means across iterations
    stats_dict = {
        # Race gaps (these are the main outcomes)
        'control_race_gap': df['control_race_gap'].mean(),
        'treatment_race_gap': df['treatment_race_gap'].mean(),
        'race_effect': df['race_effect'].mean(),
        
        # Evaluator stage
        'control_eval_processed': df['control_eval_processed'].mean(),
        'control_eval_approved': df['control_eval_approved'].mean(),
        'control_eval_denied': df['control_eval_denied'].mean(),
        'control_eval_escalated': df['control_eval_escalated'].mean(),
        'control_eval_approval_rate': df['control_eval_approval_rate'].mean(),
        'control_escalation_rate': df['control_escalation_rate'].mean(),
        
        'treatment_eval_processed': df['treatment_eval_processed'].mean(),
        'treatment_eval_approved': df['treatment_eval_approved'].mean(),
        'treatment_eval_denied': df['treatment_eval_denied'].mean(),
        'treatment_eval_escalated': df['treatment_eval_escalated'].mean(),
        'treatment_eval_approval_rate': df['treatment_eval_approval_rate'].mean(),
        'treatment_escalation_rate': df['treatment_escalation_rate'].mean(),
        
        # Reviewer stage
        'control_rev_reviewed': df['control_rev_reviewed'].mean(),
        'control_rev_approved': df['control_rev_approved'].mean(),
        'control_rev_denied': df['control_rev_denied'].mean(),
        'control_fraud_detected': df['control_fraud_detected'].mean(),
        'control_rev_approval_rate': df['control_rev_approval_rate'].mean(),
        
        'treatment_rev_reviewed': df['treatment_rev_reviewed'].mean(),
        'treatment_rev_approved': df['treatment_rev_approved'].mean(),
        'treatment_rev_denied': df['treatment_rev_denied'].mean(),
        'treatment_fraud_detected': df['treatment_fraud_detected'].mean(),
        'treatment_rev_approval_rate': df['treatment_rev_approval_rate'].mean(),
    }
    
    # Build table
    table_data = []
    
    # RACIAL DISPARITY SECTION
    table_data.append({
        'Metric': 'RACIAL DISPARITY (White - Black Gap)',
        'Control (FCFS)': '',
        'Treatment (AI)': '',
        'AI Effect': ''
    })
    table_data.append({
        'Metric': '  Approval Gap',
        'Control (FCFS)': f"{stats_dict['control_race_gap']*100:+.2f}pp",
        'Treatment (AI)': f"{stats_dict['treatment_race_gap']*100:+.2f}pp",
        'AI Effect': f"{stats_dict['race_effect']*100:+.2f}pp"
    })
    
    # Calculate % reduction
    pct_reduction = abs(stats_dict['race_effect'] / stats_dict['control_race_gap'] * 100) if stats_dict['control_race_gap'] != 0 else 0
    table_data.append({
        'Metric': '  % Reduction in Disparity',
        'Control (FCFS)': '-',
        'Treatment (AI)': '-',
        'AI Effect': f"{pct_reduction:.1f}%"
    })
    
    # Blank row
    table_data.append({
        'Metric': '',
        'Control (FCFS)': '',
        'Treatment (AI)': '',
        'AI Effect': ''
    })
    
    # EVALUATOR STAGE
    table_data.append({
        'Metric': 'EVALUATOR STAGE',
        'Control (FCFS)': '',
        'Treatment (AI)': '',
        'AI Effect': ''
    })
    table_data.append({
        'Metric': '  Applications Processed',
        'Control (FCFS)': f"{stats_dict['control_eval_processed']:,.0f}",
        'Treatment (AI)': f"{stats_dict['treatment_eval_processed']:,.0f}",
        'AI Effect': f"{stats_dict['treatment_eval_processed'] - stats_dict['control_eval_processed']:+,.0f}"
    })
    table_data.append({
        'Metric': '  Approved',
        'Control (FCFS)': f"{stats_dict['control_eval_approved']:,.0f}",
        'Treatment (AI)': f"{stats_dict['treatment_eval_approved']:,.0f}",
        'AI Effect': f"{stats_dict['treatment_eval_approved'] - stats_dict['control_eval_approved']:+,.0f}"
    })
    table_data.append({
        'Metric': '  Denied',
        'Control (FCFS)': f"{stats_dict['control_eval_denied']:,.0f}",
        'Treatment (AI)': f"{stats_dict['treatment_eval_denied']:,.0f}",
        'AI Effect': f"{stats_dict['treatment_eval_denied'] - stats_dict['control_eval_denied']:+,.0f}"
    })
    table_data.append({
        'Metric': '  Escalated to Reviewer',
        'Control (FCFS)': f"{stats_dict['control_eval_escalated']:,.0f}",
        'Treatment (AI)': f"{stats_dict['treatment_eval_escalated']:,.0f}",
        'AI Effect': f"{stats_dict['treatment_eval_escalated'] - stats_dict['control_eval_escalated']:+,.0f}"
    })
    table_data.append({
        'Metric': '  Approval Rate',
        'Control (FCFS)': f"{stats_dict['control_eval_approval_rate']:.1%}",
        'Treatment (AI)': f"{stats_dict['treatment_eval_approval_rate']:.1%}",
        'AI Effect': f"{(stats_dict['treatment_eval_approval_rate'] - stats_dict['control_eval_approval_rate'])*100:+.2f}pp"
    })
    table_data.append({
        'Metric': '  Escalation Rate',
        'Control (FCFS)': f"{stats_dict['control_escalation_rate']:.1%}",
        'Treatment (AI)': f"{stats_dict['treatment_escalation_rate']:.1%}",
        'AI Effect': f"{(stats_dict['treatment_escalation_rate'] - stats_dict['control_escalation_rate'])*100:+.2f}pp"
    })
    
    # Blank row
    table_data.append({
        'Metric': '',
        'Control (FCFS)': '',
        'Treatment (AI)': '',
        'AI Effect': ''
    })
    
    # REVIEWER STAGE
    table_data.append({
        'Metric': 'REVIEWER STAGE',
        'Control (FCFS)': '',
        'Treatment (AI)': '',
        'AI Effect': ''
    })
    table_data.append({
        'Metric': '  Cases Reviewed',
        'Control (FCFS)': f"{stats_dict['control_rev_reviewed']:,.0f}",
        'Treatment (AI)': f"{stats_dict['treatment_rev_reviewed']:,.0f}",
        'AI Effect': f"{stats_dict['treatment_rev_reviewed'] - stats_dict['control_rev_reviewed']:+,.0f}"
    })
    table_data.append({
        'Metric': '  Approved',
        'Control (FCFS)': f"{stats_dict['control_rev_approved']:,.0f}",
        'Treatment (AI)': f"{stats_dict['treatment_rev_approved']:,.0f}",
        'AI Effect': f"{stats_dict['treatment_rev_approved'] - stats_dict['control_rev_approved']:+,.0f}"
    })
    table_data.append({
        'Metric': '  Denied',
        'Control (FCFS)': f"{stats_dict['control_rev_denied']:,.0f}",
        'Treatment (AI)': f"{stats_dict['treatment_rev_denied']:,.0f}",
        'AI Effect': f"{stats_dict['treatment_rev_denied'] - stats_dict['control_rev_denied']:+,.0f}"
    })
    table_data.append({
        'Metric': '  Fraud Detected',
        'Control (FCFS)': f"{stats_dict['control_fraud_detected']:,.0f}",
        'Treatment (AI)': f"{stats_dict['treatment_fraud_detected']:,.0f}",
        'AI Effect': f"{stats_dict['treatment_fraud_detected'] - stats_dict['control_fraud_detected']:+,.0f}"
    })
    table_data.append({
        'Metric': '  Approval Rate',
        'Control (FCFS)': f"{stats_dict['control_rev_approval_rate']:.1%}",
        'Treatment (AI)': f"{stats_dict['treatment_rev_approval_rate']:.1%}",
        'AI Effect': f"{(stats_dict['treatment_rev_approval_rate'] - stats_dict['control_rev_approval_rate'])*100:+.2f}pp"
    })
    
    # Blank row
    table_data.append({
        'Metric': '',
        'Control (FCFS)': '',
        'Treatment (AI)': '',
        'AI Effect': ''
    })
    
    # STATISTICAL TESTS
    table_data.append({
        'Metric': 'STATISTICAL SIGNIFICANCE',
        'Control (FCFS)': '',
        'Treatment (AI)': '',
        'AI Effect': ''
    })
    
    se = df['race_effect'].std() / np.sqrt(len(df))
    t_stat = stats_dict['race_effect'] / se if se > 0 else 0
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), len(df) - 1))
    sig = '***' if p_value < 0.001 else '**' if p_value < 0.01 else '*' if p_value < 0.05 else 'ns'
    
    table_data.append({
        'Metric': '  Mean Effect',
        'Control (FCFS)': '-',
        'Treatment (AI)': '-',
        'AI Effect': f"{stats_dict['race_effect']*100:+.2f}pp"
    })
    table_data.append({
        'Metric': '  95% CI',
        'Control (FCFS)': '-',
        'Treatment (AI)': '-',
        'AI Effect': f"[{(stats_dict['race_effect'] - 1.96*se)*100:+.2f}, {(stats_dict['race_effect'] + 1.96*se)*100:+.2f}]"
    })
    table_data.append({
        'Metric': '  t-statistic',
        'Control (FCFS)': '-',
        'Treatment (AI)': '-',
        'AI Effect': f"{t_stat:+.2f}"
    })
    table_data.append({
        'Metric': '  p-value',
        'Control (FCFS)': '-',
        'Treatment (AI)': '-',
        'AI Effect': f"{p_value:.4f} {sig}"
    })
    table_data.append({
        'Metric': '  N iterations',
        'Control (FCFS)': f"{len(df)}",
        'Treatment (AI)': f"{len(df)}",
        'AI Effect': f"{len(df)}"
    })
    
    return pd.DataFrame(table_data)


def print_table(table):
    """Print formatted table to console."""
    print(f"\n{'='*100}")
    print("ADMINISTRATIVE OUTCOMES: Control vs Treatment")
    print(f"{'='*100}\n")
    
    for _, row in table.iterrows():
        metric = row['Metric']
        ctrl = row['Control (FCFS)']
        treat = row['Treatment (AI)']
        effect = row['AI Effect']
        
        print(f"{metric:45s} {ctrl:20s} {treat:20s} {effect:18s}")
    
    print(f"\n{'='*100}")


def create_table_figure(table, output_file):
    """Create figure version of table."""
    fig, ax = plt.subplots(figsize=(14, 12))
    ax.axis('tight')
    ax.axis('off')
    
    mpl_table = ax.table(
        cellText=table.values,
        colLabels=table.columns,
        cellLoc='left',
        loc='center',
        colWidths=[0.45, 0.20, 0.20, 0.15]
    )
    
    mpl_table.auto_set_font_size(False)
    mpl_table.set_fontsize(9)
    mpl_table.scale(1, 1.6)
    
    # Style header
    for i in range(len(table.columns)):
        mpl_table[(0, i)].set_facecolor('#2c3e50')
        mpl_table[(0, i)].set_text_props(weight='bold', color='white')
    
    # Style rows
    for i in range(1, len(table) + 1):
        for j in range(len(table.columns)):
            if i % 2 == 0:
                mpl_table[(i, j)].set_facecolor('#ecf0f1')
            
            # Bold section headers
            if table.iloc[i-1]['Metric'].isupper():
                mpl_table[(i, j)].set_text_props(weight='bold')
            
            # Highlight significant effects
            if j == 3 and '***' in str(table.iloc[i-1]['AI Effect']):
                mpl_table[(i, j)].set_text_props(color='red', weight='bold')
    
    plt.title('Administrative Outcomes: Impact of AI on Welfare Processing',
             fontsize=14, fontweight='bold', pad=20)
    
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Figure saved: {output_file}")


def main():
    print("="*100)
    print("POST-PROCESSING MONTE CARLO RESULTS")
    print("="*100)
    
    # Create table
    table = create_administrative_outcomes_table()
    
    if table is None:
        return
    
    # Print to console
    print_table(table)
    
    # Save CSV
    output_csv = 'results/administrative_outcomes_table.csv'
    table.to_csv(output_csv, index=False)
    print(f"\n✓ Table saved: {output_csv}")
    
    # Create figure
    Path('results/visualizations').mkdir(parents=True, exist_ok=True)
    output_fig = 'results/visualizations/administrative_outcomes_table.png'
    create_table_figure(table, output_fig)
    
    print(f"\n{'='*100}")
    print("POST-PROCESSING COMPLETE")
    print(f"{'='*100}")
    print(f"\nFiles created:")
    print(f"  - {output_csv}")
    print(f"  - {output_fig}")


if __name__ == '__main__':
    main()