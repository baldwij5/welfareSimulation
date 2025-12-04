"""
County-Level Map - Alternative Approach

Uses Plotly Express built-in county support (simpler, more reliable)

Run with: python scripts/map_counties_simple.py
"""

import pandas as pd
import plotly.express as px

# Load results
print("Loading county results...")
results = pd.read_csv('results/all_counties_results.csv')
print(f"✓ Loaded {len(results)} counties")

# Parse state and county name
results['state'] = results['county'].str.split(', ').str[1]
results['county_only'] = results['county'].str.split(', ').str[0]

# Convert to percentage points
results['effect_pp'] = results['treatment_effect'] * 100

# Create summary stats
print(f"\nSummary Statistics:")
print(f"  Mean effect: {results['effect_pp'].mean():.1f}pp")
print(f"  Median effect: {results['effect_pp'].median():.1f}pp")
print(f"  Range: {results['effect_pp'].min():.1f}pp to {results['effect_pp'].max():.1f}pp")
print(f"  SD: {results['effect_pp'].std():.1f}pp")

# Count by effect direction
helped = (results['effect_pp'] < -2).sum()
hurt = (results['effect_pp'] > 2).sum()
neutral = len(results) - helped - hurt

print(f"\nEffect Categories:")
print(f"  AI helped (< -2pp): {helped} counties ({helped/len(results)*100:.1f}%)")
print(f"  No effect (-2 to +2pp): {neutral} counties ({neutral/len(results)*100:.1f}%)")
print(f"  AI hurt (> +2pp): {hurt} counties ({hurt/len(results)*100:.1f}%)")

# Create visualizations
import os
os.makedirs('results/visualizations', exist_ok=True)

# 1. Scatter plot by state (most reliable visualization)
print("\nCreating scatter plot...")
fig1 = px.scatter(
    results,
    x='control_gap',
    y='treatment_effect',
    color='effect_pp',
    color_continuous_scale='RdYlGn_r',
    color_continuous_midpoint=0,
    size=results['n_white'] + results['n_black'],
    hover_name='county',
    hover_data={
        'state': True,
        'control_gap': ':.1%',
        'treatment_gap': ':.1%',
        'effect_pp': ':.1f',
        'n_white': True,
        'n_black': True
    },
    labels={
        'control_gap': 'Baseline Disparity (Control World)',
        'treatment_effect': 'AI Treatment Effect',
        'effect_pp': 'Effect (pp)'
    },
    title=f'AI Treatment Effects: All {len(results)} US Counties'
)

fig1.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)
fig1.update_layout(width=1600, height=900)
fig1.write_html('results/visualizations/counties_scatter_detailed.html')
print("  ✓ Saved: counties_scatter_detailed.html")

# 2. Histogram with categories
print("Creating histogram...")
fig2 = px.histogram(
    results,
    x='effect_pp',
    nbins=60,
    title=f'Distribution of AI Treatment Effects: {len(results)} Counties',
    labels={'effect_pp': 'Treatment Effect (percentage points)'}
)

fig2.add_vline(x=0, line_color="black", line_dash="solid")
fig2.add_vline(x=results['effect_pp'].mean(), line_color="red", line_dash="dash",
              annotation_text=f"Mean: {results['effect_pp'].mean():.1f}pp")

fig2.update_layout(width=1200, height=600)
fig2.write_html('results/visualizations/distribution_detailed.html')
print("  ✓ Saved: distribution_detailed.html")

# 3. Box plot by state (top 20 states)
print("Creating state comparison...")
top_states = results.groupby('state').size().nlargest(20).index
results_top = results[results['state'].isin(top_states)]

fig3 = px.box(
    results_top,
    x='state',
    y='effect_pp',
    points='all',
    hover_name='county',
    title='AI Treatment Effects by State (Top 20 States by Number of Counties)',
    labels={'effect_pp': 'Treatment Effect (pp)', 'state': 'State'}
)

fig3.add_hline(y=0, line_dash="dash", line_color="gray")
fig3.update_layout(width=1600, height=700)
fig3.update_xaxes(tickangle=45)
fig3.write_html('results/visualizations/states_boxplot.html')
print("  ✓ Saved: states_boxplot.html")

# 4. Top/bottom counties table
print("Creating top/bottom counties...")
top_helped = results.nsmallest(20, 'effect_pp')[['county', 'effect_pp', 'control_gap', 'treatment_gap']]
top_hurt = results.nlargest(20, 'effect_pp')[['county', 'effect_pp', 'control_gap', 'treatment_gap']]

print("\n" + "="*70)
print("TOP 20 COUNTIES WHERE AI HELPED MOST (Largest Negative Effects)")
print("="*70)
for i, row in top_helped.iterrows():
    print(f"  {row['county']:<45} {row['effect_pp']:+7.1f}pp")

print("\n" + "="*70)
print("TOP 20 COUNTIES WHERE AI HURT MOST (Largest Positive Effects)")
print("="*70)
for i, row in top_hurt.iterrows():
    print(f"  {row['county']:<45} {row['effect_pp']:+7.1f}pp")

print("\n" + "="*70)
print("COMPLETE")
print("="*70)
print("\nOpen visualizations:")
print("  open results/visualizations/counties_scatter_detailed.html")
print("  open results/visualizations/distribution_detailed.html")
print("  open results/visualizations/states_boxplot.html")