"""
Interactive US Map: AI Treatment Effects by State

Creates interactive choropleth map showing:
- How AI affects racial disparities in each state
- Changes over time (monthly evolution)
- Geographic patterns

Requires: plotly
Install: pip install plotly

Run with: python scripts/visualize_state_effects.py
"""

import sys
sys.path.insert(0, 'src')
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


def load_state_results(filepath='results/50_states_results.csv'):
    """Load 50-state experiment results."""
    try:
        results = pd.read_csv(filepath)
        print(f"✓ Loaded results for {len(results)} states")
        return results
    except FileNotFoundError:
        print(f"Error: {filepath} not found!")
        print(f"Run: python experiments/experiment_50_states.py first")
        return None


def create_treatment_effect_map(results_df):
    """
    Create static choropleth map of treatment effects.
    
    Args:
        results_df: DataFrame with state results
        
    Returns:
        plotly figure
    """
    # State name to abbreviation mapping
    state_abbrev = {
        'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
        'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
        'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID',
        'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS',
        'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
        'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS',
        'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV',
        'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY',
        'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK',
        'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
        'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT',
        'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV',
        'Wisconsin': 'WI', 'Wyoming': 'WY'
    }
    
    # Add state abbreviations
    results_df['state_abbr'] = results_df['state'].map(state_abbrev)
    
    # Convert to percentage points for display
    results_df['effect_pp'] = results_df['treatment_effect'] * 100
    
    # Create color scale (red = AI hurts, green = AI helps, white = neutral)
    fig = go.Figure(data=go.Choropleth(
        locations=results_df['state_abbr'],
        z=results_df['effect_pp'],
        locationmode='USA-states',
        colorscale=[
            [0.0, 'darkgreen'],   # Large negative (AI helps a lot)
            [0.4, 'lightgreen'],  # Small negative
            [0.5, 'white'],       # Zero effect
            [0.6, 'pink'],        # Small positive
            [1.0, 'darkred']      # Large positive (AI hurts a lot)
        ],
        zmid=0,  # Center at zero
        colorbar_title="Treatment Effect<br>(percentage points)",
        hovertemplate='<b>%{text}</b><br>' +
                     'Effect: %{z:.1f}pp<br>' +
                     '<extra></extra>',
        text=results_df['state']
    ))
    
    fig.update_layout(
        title_text='AI Application Sorting: Treatment Effects by State<br>' +
                   '<sub>Red = AI increases disparity, Green = AI decreases disparity</sub>',
        geo_scope='usa',
        width=1200,
        height=700,
        font=dict(size=14)
    )
    
    return fig


def create_heterogeneity_scatter(results_df):
    """
    Create scatter plot of treatment effects.
    
    Shows relationship between baseline disparity and treatment effect.
    """
    fig = px.scatter(
        results_df,
        x='control_gap',
        y='treatment_effect',
        hover_name='state',
        size='n_white',  # Bubble size = sample size
        color='treatment_effect',
        color_continuous_scale=['darkgreen', 'white', 'darkred'],
        color_continuous_midpoint=0,
        labels={
            'control_gap': 'Baseline Disparity (Control)',
            'treatment_effect': 'AI Treatment Effect',
            'n_white': 'Sample Size'
        },
        title='AI Treatment Effects vs Baseline Disparities by State'
    )
    
    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray", 
                  annotation_text="No effect line")
    
    fig.update_layout(width=1000, height=600)
    
    return fig


def create_distribution_histogram(results_df):
    """
    Create histogram of treatment effects across states.
    """
    fig = px.histogram(
        results_df,
        x='treatment_effect',
        nbins=20,
        labels={'treatment_effect': 'Treatment Effect (proportion)'},
        title='Distribution of AI Treatment Effects Across 50 States'
    )
    
    # Add mean line
    mean_effect = results_df['treatment_effect'].mean()
    fig.add_vline(x=mean_effect, line_dash="dash", line_color="red",
                  annotation_text=f"Mean: {mean_effect*100:.1f}pp")
    
    # Add zero line
    fig.add_vline(x=0, line_dash="solid", line_color="gray",
                  annotation_text="Zero effect")
    
    fig.update_layout(width=1000, height=500)
    
    return fig


def create_regional_comparison(results_df):
    """
    Compare treatment effects by US region.
    """
    # Define regions
    regions = {
        'Northeast': ['Connecticut', 'Maine', 'Massachusetts', 'New Hampshire', 
                     'Rhode Island', 'Vermont', 'New Jersey', 'New York', 'Pennsylvania'],
        'Midwest': ['Illinois', 'Indiana', 'Michigan', 'Ohio', 'Wisconsin',
                   'Iowa', 'Kansas', 'Minnesota', 'Missouri', 'Nebraska',
                   'North Dakota', 'South Dakota'],
        'South': ['Delaware', 'Florida', 'Georgia', 'Maryland', 'North Carolina',
                 'South Carolina', 'Virginia', 'West Virginia', 'Alabama',
                 'Kentucky', 'Mississippi', 'Tennessee', 'Arkansas', 'Louisiana',
                 'Oklahoma', 'Texas'],
        'West': ['Arizona', 'Colorado', 'Idaho', 'Montana', 'Nevada', 'New Mexico',
                'Utah', 'Wyoming', 'Alaska', 'California', 'Hawaii', 'Oregon', 'Washington']
    }
    
    # Assign regions
    def get_region(state):
        for region, states in regions.items():
            if state in states:
                return region
        return 'Other'
    
    results_df['region'] = results_df['state'].apply(get_region)
    
    # Box plot by region
    fig = px.box(
        results_df,
        x='region',
        y='treatment_effect',
        points='all',
        hover_name='state',
        labels={
            'region': 'US Region',
            'treatment_effect': 'Treatment Effect'
        },
        title='AI Treatment Effects by US Region'
    )
    
    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    
    fig.update_layout(width=1000, height=600)
    
    return fig


def create_top_bottom_states(results_df, n=10):
    """
    Show top states where AI helped/hurt most.
    """
    # Sort by effect
    sorted_df = results_df.sort_values('treatment_effect')
    
    # Top 10 where AI helped (most negative)
    helped = sorted_df.head(n)
    
    # Top 10 where AI hurt (most positive)
    hurt = sorted_df.tail(n)
    
    # Combine
    top_bottom = pd.concat([helped, hurt])
    
    fig = px.bar(
        top_bottom,
        x='treatment_effect',
        y='state',
        orientation='h',
        color='treatment_effect',
        color_continuous_scale=['darkgreen', 'white', 'darkred'],
        color_continuous_midpoint=0,
        labels={
            'treatment_effect': 'Treatment Effect',
            'state': 'State'
        },
        title=f'Top {n} States Where AI Helped/Hurt Most'
    )
    
    fig.update_layout(
        width=1000,
        height=800,
        yaxis={'categoryorder': 'total ascending'}
    )
    
    return fig


def save_all_visualizations(results_df):
    """Create and save all visualizations."""
    import os
    os.makedirs('results/visualizations', exist_ok=True)
    
    print("\nCreating visualizations...")
    
    # 1. US Map
    print("  1. US choropleth map...")
    fig_map = create_treatment_effect_map(results_df)
    fig_map.write_html('results/visualizations/us_map_treatment_effects.html')
    print("     ✓ Saved: results/visualizations/us_map_treatment_effects.html")
    
    # 2. Scatter plot
    print("  2. Scatter plot (baseline vs treatment)...")
    fig_scatter = create_heterogeneity_scatter(results_df)
    fig_scatter.write_html('results/visualizations/scatter_baseline_vs_treatment.html')
    print("     ✓ Saved: results/visualizations/scatter_baseline_vs_treatment.html")
    
    # 3. Histogram
    print("  3. Distribution histogram...")
    fig_hist = create_distribution_histogram(results_df)
    fig_hist.write_html('results/visualizations/histogram_treatment_effects.html')
    print("     ✓ Saved: results/visualizations/histogram_treatment_effects.html")
    
    # 4. Regional comparison
    print("  4. Regional comparison...")
    fig_region = create_regional_comparison(results_df)
    fig_region.write_html('results/visualizations/regional_comparison.html')
    print("     ✓ Saved: results/visualizations/regional_comparison.html")
    
    # 5. Top/bottom states
    print("  5. Top/bottom states...")
    fig_topbottom = create_top_bottom_states(results_df, n=10)
    fig_topbottom.write_html('results/visualizations/top_bottom_states.html')
    print("     ✓ Saved: results/visualizations/top_bottom_states.html")
    
    print("\n✓ All visualizations created!")
    print("\nOpen any HTML file in your browser to view interactive maps/plots")


def main():
    """Create all visualizations from 50-state results."""
    print("\n" + "="*70)
    print("50-State Results Visualization")
    print("="*70)
    print("\nCreates interactive visualizations:")
    print("  1. US choropleth map (treatment effects by state)")
    print("  2. Scatter plot (baseline vs treatment)")
    print("  3. Distribution histogram")
    print("  4. Regional comparison (Northeast, South, Midwest, West)")
    print("  5. Top/bottom states (who was helped/hurt most)")
    
    # Load results
    results = load_state_results()
    
    if results is None:
        return
    
    # Create visualizations
    save_all_visualizations(results)
    
    print("\n" + "="*70)
    print("VISUALIZATION COMPLETE")
    print("="*70)
    print("\nGenerated 5 interactive HTML visualizations")
    print("Open in browser for interactive exploration!")
    print("\nExample:")
    print("  open results/visualizations/us_map_treatment_effects.html")


if __name__ == "__main__":
    main()