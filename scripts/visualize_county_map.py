"""
County-Level Choropleth Map - Treatment Effects

Creates detailed county-level map showing AI effects across the entire US.

Requires: plotly
Install: pip install plotly

Run with: python scripts/visualize_county_map.py
"""

import sys
sys.path.insert(0, 'src')
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from urllib.request import urlopen
import json


def load_county_results(filepath='results/all_counties_results.csv'):
    """Load all-counties experiment results."""
    try:
        results = pd.read_csv(filepath)
        print(f"✓ Loaded results for {len(results)} counties")
        return results
    except FileNotFoundError:
        print(f"⚠️  {filepath} not found")
        print(f"Run: python experiments/experiment_all_counties.py first")
        return None


def get_county_fips_mapping(acs_file='src/data/us_census_acs_2022_county_data.csv'):
    """
    Get FIPS codes for counties (needed for choropleth).
    
    Returns:
        dict: {county_name: fips_code}
    """
    acs = pd.read_csv(acs_file)
    
    # Create FIPS if not present (state FIPS + county FIPS)
    # For now, create mapping from county name
    fips_map = {}
    
    for _, row in acs.iterrows():
        county_name = row['county_name']
        # FIPS should be in ACS data, or we construct it
        # Format: state (2 digits) + county (3 digits)
        if 'fips' in row and pd.notna(row['fips']):
            fips_map[county_name] = str(int(row['fips'])).zfill(5)
    
    return fips_map


def create_county_choropleth(results_df):
    """
    Create detailed county-level choropleth map.
    
    Args:
        results_df: DataFrame with county results
        
    Returns:
        plotly figure
    """
    # Get FIPS codes
    from data.data_loader import load_acs_county_data
    acs = load_acs_county_data('src/data/us_census_acs_2022_county_data.csv')
    
    # Merge to get FIPS if available
    if 'fips' in acs.columns:
        acs_fips = acs[['county_name', 'fips']].copy()
        acs_fips['fips'] = acs_fips['fips'].astype(str).str.zfill(5)
        results_df = results_df.merge(acs_fips, left_on='county', right_on='county_name', how='left')
    
    # Load GeoJSON for US counties
    with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
        counties_geojson = json.load(response)
    
    # Convert effect to percentage points
    results_df['effect_pp'] = results_df['treatment_effect'] * 100
    
    # Create figure
    fig = go.Figure(go.Choroplethmapbox(
        geojson=counties_geojson,
        locations=results_df['fips'],
        z=results_df['effect_pp'],
        colorscale=[
            [0.0, 'darkgreen'],   # AI helps
            [0.4, 'lightgreen'],
            [0.5, 'white'],       # Neutral
            [0.6, 'pink'],
            [1.0, 'darkred']      # AI hurts
        ],
        zmid=0,
        marker_opacity=0.7,
        marker_line_width=0.5,
        colorbar_title="Treatment<br>Effect (pp)",
        hovertemplate='<b>%{customdata[0]}</b><br>' +
                     'Effect: %{z:.1f}pp<br>' +
                     'Control gap: %{customdata[1]:.1f}pp<br>' +
                     'Treatment gap: %{customdata[2]:.1f}pp<br>' +
                     '<extra></extra>',
        customdata=results_df[['county', 'control_gap', 'treatment_gap']].values * [1, 100, 100]
    ))
    
    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=3,
        mapbox_center={"lat": 37.0902, "lon": -95.7129},
        title_text='AI Treatment Effects: All US Counties<br>' +
                   '<sub>Green = AI reduces disparity, Red = AI increases disparity</sub>',
        width=1400,
        height=900,
        font=dict(size=14)
    )
    
    return fig


def create_county_scatter(results_df):
    """Scatter plot of all counties."""
    # Add state for coloring
    results_df['state'] = results_df['county'].str.split(', ').str[1]
    
    fig = px.scatter(
        results_df,
        x='control_gap',
        y='treatment_effect',
        color='state',
        hover_name='county',
        size='n_white',
        labels={
            'control_gap': 'Baseline Disparity (Control)',
            'treatment_effect': 'AI Treatment Effect'
        },
        title=f'AI Treatment Effects: All {len(results_df)} Counties'
    )
    
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.update_layout(width=1200, height=700)
    
    return fig


def create_state_aggregated_from_counties(results_df):
    """
    Aggregate county results to state level.
    
    Shows state-level patterns from county data.
    """
    results_df['state'] = results_df['county'].str.split(', ').str[1]
    
    # Aggregate by state (weighted by sample size)
    state_summary = results_df.groupby('state').agg({
        'treatment_effect': 'mean',
        'control_gap': 'mean',
        'treatment_gap': 'mean',
        'n_white': 'sum',
        'n_black': 'sum'
    }).reset_index()
    
    state_summary['n_counties'] = results_df.groupby('state').size().values
    
    # State map
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
    
    state_summary['state_abbr'] = state_summary['state'].map(state_abbrev)
    state_summary['effect_pp'] = state_summary['treatment_effect'] * 100
    
    fig = go.Figure(data=go.Choropleth(
        locations=state_summary['state_abbr'],
        z=state_summary['effect_pp'],
        locationmode='USA-states',
        colorscale='RdYlGn_r',  # Red-Yellow-Green reversed
        zmid=0,
        colorbar_title="Avg Effect (pp)",
        hovertemplate='<b>%{text}</b><br>' +
                     'Effect: %{z:.1f}pp<br>' +
                     'Counties: %{customdata}<br>' +
                     '<extra></extra>',
        text=state_summary['state'],
        customdata=state_summary['n_counties']
    ))
    
    fig.update_layout(
        title_text='State-Level AI Effects (Aggregated from County Data)',
        geo_scope='usa',
        width=1200,
        height=700
    )
    
    return fig


def main():
    """Create county-level visualizations."""
    print("\n" + "="*70)
    print("County-Level Visualization")
    print("="*70)
    
    # Load results
    results = load_county_results()
    
    if results is None:
        print("\nNo county results found.")
        print("\nOptions:")
        print("  1. Run: python experiments/experiment_all_counties.py")
        print("  2. Use existing 50-state results for demo")
        return
    
    import os
    os.makedirs('results/visualizations', exist_ok=True)
    
    print("\nCreating county-level visualizations...")
    
    # County-level map
    print("  1. County choropleth map...")
    try:
        fig_county = create_county_choropleth(results)
        fig_county.write_html('results/visualizations/county_map_treatment_effects.html')
        print("     ✓ Saved: county_map_treatment_effects.html")
    except Exception as e:
        print(f"     ⚠️  Error creating county map: {e}")
        print(f"     (FIPS codes may be needed)")
    
    # Scatter plot
    print("  2. County scatter plot...")
    fig_scatter = create_county_scatter(results)
    fig_scatter.write_html('results/visualizations/county_scatter.html')
    print("     ✓ Saved: county_scatter.html")
    
    # State aggregation
    print("  3. State-aggregated map...")
    fig_state = create_state_aggregated_from_counties(results)
    fig_state.write_html('results/visualizations/state_from_counties.html')
    print("     ✓ Saved: state_from_counties.html")
    
    print("\n" + "="*70)
    print("VISUALIZATION COMPLETE")
    print("="*70)
    print("\nOpen visualizations:")
    print("  open results/visualizations/county_map_treatment_effects.html")
    print("  open results/visualizations/county_scatter.html")


if __name__ == "__main__":
    main()