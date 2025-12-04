"""
County-Level Choropleth Map - ALL 1,532 Counties

Creates true county-level visualization (not aggregated to states).

Requires: plotly, geopandas (optional)
Install: pip install plotly geopandas

Run with: python scripts/county_level_map.py
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import ssl
import certifi


def load_county_geojson():
    """
    Load US counties GeoJSON with SSL fix.
    """
    import urllib.request
    import json
    
    # Create SSL context that doesn't verify certificates
    # (Alternative: use certifi for proper SSL)
    context = ssl._create_unverified_context()
    
    url = 'https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json'
    
    try:
        with urllib.request.urlopen(url, context=context) as response:
            counties_geojson = json.load(response)
        print("✓ Loaded county GeoJSON")
        return counties_geojson
    except Exception as e:
        print(f"⚠️  Error loading GeoJSON: {e}")
        return None


def create_fips_mapping(results_df, acs_file='src/data/us_census_acs_2022_county_data.csv'):
    """
    Create FIPS codes for counties.
    
    FIPS format: 5 digits (2-digit state + 3-digit county)
    Example: 01001 = Autauga County, Alabama
    """
    # Load ACS to get FIPS if available
    acs = pd.read_csv(acs_file)
    
    # Check if FIPS exists in ACS
    if 'fips' in acs.columns or 'FIPS' in acs.columns:
        fips_col = 'fips' if 'fips' in acs.columns else 'FIPS'
        acs_fips = acs[['county_name', fips_col]].copy()
        acs_fips.columns = ['county', 'fips']
        acs_fips['fips'] = acs_fips['fips'].astype(str).str.zfill(5)
        
        # Merge with results
        results_with_fips = results_df.merge(acs_fips, on='county', how='left')
        
        print(f"✓ Matched {results_with_fips['fips'].notna().sum()} counties to FIPS codes")
        return results_with_fips
    
    else:
        print("⚠️  No FIPS codes in ACS data")
        print("  Will create state-level map instead")
        return results_df


def create_county_choropleth_map(results_df):
    """
    Create TRUE county-level choropleth map.
    
    Shows all 1,532 counties individually colored by treatment effect.
    """
    print("\nCreating county-level choropleth...")
    
    # Load GeoJSON
    geojson = load_county_geojson()
    
    if geojson is None:
        print("  Falling back to state-level aggregation")
        return create_state_aggregated_map(results_df)
    
    # Add FIPS codes
    results_with_fips = create_fips_mapping(results_df)
    
    # Filter to counties with FIPS
    results_with_fips = results_with_fips[results_with_fips['fips'].notna()].copy()
    
    print(f"  Plotting {len(results_with_fips)} counties with FIPS codes")
    
    # Convert to percentage points
    results_with_fips['effect_pp'] = results_with_fips['treatment_effect'] * 100
    results_with_fips['control_gap_pp'] = results_with_fips['control_gap'] * 100
    results_with_fips['treatment_gap_pp'] = results_with_fips['treatment_gap'] * 100
    
    # Create choropleth
    fig = go.Figure(go.Choroplethmapbox(
        geojson=geojson,
        locations=results_with_fips['fips'],
        z=results_with_fips['effect_pp'],
        colorscale=[
            [0.0, 'darkgreen'],    # Large negative (AI helps a lot)
            [0.3, 'lightgreen'],   # Small negative
            [0.5, 'white'],        # Zero
            [0.7, 'lightcoral'],   # Small positive
            [1.0, 'darkred']       # Large positive (AI hurts)
        ],
        zmin=-20,  # Set range for better color distribution
        zmax=20,
        zmid=0,
        marker_opacity=0.8,
        marker_line_width=0.5,
        marker_line_color='white',
        colorbar=dict(
            title="AI Effect<br>(pp)",
            thickness=20,
            len=0.7
        ),
        hovertemplate='<b>%{customdata[0]}</b><br>' +
                     'AI Effect: %{z:.1f}pp<br>' +
                     'Control gap: %{customdata[1]:.1f}pp<br>' +
                     'Treatment gap: %{customdata[2]:.1f}pp<br>' +
                     'Sample: %{customdata[3]} White, %{customdata[4]} Black<br>' +
                     '<extra></extra>',
        customdata=results_with_fips[[
            'county', 'control_gap_pp', 'treatment_gap_pp', 'n_white', 'n_black'
        ]].values
    ))
    
    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=3.5,
        mapbox_center={"lat": 37.0902, "lon": -95.7129},
        title={
            'text': f'AI Treatment Effects: {len(results_with_fips)} US Counties<br>' +
                   '<sub>Green = AI reduces disparity | Red = AI increases disparity | White = No effect</sub>',
            'x': 0.5,
            'xanchor': 'center'
        },
        width=1600,
        height=1000,
        font=dict(size=14),
        margin=dict(l=0, r=0, t=80, b=0)
    )
    
    return fig


def create_state_aggregated_map(results_df):
    """
    Fallback: Create state-level map from county data.
    """
    results_df['state'] = results_df['county'].str.split(', ').str[1]
    
    state_summary = results_df.groupby('state').agg({
        'treatment_effect': 'mean',
        'control_gap': 'mean',
        'treatment_gap': 'mean',
        'n_white': 'sum',
        'n_black': 'sum'
    }).reset_index()
    
    state_summary['n_counties'] = results_df.groupby('state').size().values
    
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
    
    state_summary['abbr'] = state_summary['state'].map(state_abbrev)
    state_summary['effect_pp'] = state_summary['treatment_effect'] * 100
    
    fig = go.Figure(data=go.Choropleth(
        locations=state_summary['abbr'],
        z=state_summary['effect_pp'],
        locationmode='USA-states',
        colorscale='RdYlGn_r',
        zmid=0,
        text=state_summary['state'],
        hovertemplate='<b>%{text}</b><br>' +
                     'Avg Effect: %{z:.1f}pp<br>' +
                     'Counties: %{customdata}<br>' +
                     '<extra></extra>',
        customdata=state_summary['n_counties']
    ))
    
    fig.update_layout(
        title=f'AI Effects Aggregated to State Level ({len(state_summary)} states from {len(results_df)} counties)',
        geo_scope='usa',
        width=1400,
        height=800
    )
    
    return fig


def create_top_counties_map(results_df, n=100):
    """
    Create map of top N counties by effect size.
    
    Shows counties where AI had largest positive/negative effects.
    """
    # Get top and bottom counties
    results_sorted = results_df.sort_values('treatment_effect')
    top_helped = results_sorted.head(n//2)  # AI helped most
    top_hurt = results_sorted.tail(n//2)    # AI hurt most
    
    top_counties = pd.concat([top_helped, top_hurt])
    
    # Create scatter geo
    top_counties['state'] = top_counties['county'].str.split(', ').str[1]
    top_counties['effect_pp'] = top_counties['treatment_effect'] * 100
    
    # Use Plotly scatter_geo for point map
    fig = px.scatter_geo(
        top_counties,
        locations='state',
        locationmode='USA-states',
        color='effect_pp',
        size=abs(top_counties['effect_pp']),
        hover_name='county',
        hover_data={
            'effect_pp': ':.1f',
            'control_gap': ':.1%',
            'n_white': True,
            'n_black': True
        },
        color_continuous_scale='RdYlGn_r',
        color_continuous_midpoint=0,
        title=f'Top {n} Counties by AI Effect Magnitude'
    )
    
    fig.update_geos(scope='usa')
    fig.update_layout(width=1400, height=800)
    
    return fig


def main():
    """Create all county-level visualizations."""
    print("\n" + "="*70)
    print("COUNTY-LEVEL VISUALIZATION - TRUE COUNTY MAP")
    print("="*70)
    
    # Load results
    results = pd.read_csv('results/all_counties_results.csv')
    print(f"✓ Loaded {len(results)} counties")
    
    import os
    os.makedirs('results/visualizations', exist_ok=True)
    
    print("\nCreating visualizations...")
    
    # 1. Try county-level choropleth
    print("\n1. County-level choropleth (1,532 individual counties)...")
    try:
        fig_county = create_county_choropleth_map(results)
        fig_county.write_html('results/visualizations/true_county_map.html')
        print("   ✓ Saved: true_county_map.html")
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
    
    # 2. State aggregation (fallback)
    print("\n2. State-level aggregation...")
    fig_state = create_state_aggregated_map(results)
    fig_state.write_html('results/visualizations/state_aggregated.html')
    print("   ✓ Saved: state_aggregated.html")
    
    # 3. Top counties point map
    print("\n3. Top 100 counties point map...")
    fig_top = create_top_counties_map(results, n=100)
    fig_top.write_html('results/visualizations/top_100_counties.html')
    print("   ✓ Saved: top_100_counties.html")
    
    # 4. Distribution
    print("\n4. Distribution histogram...")
    fig_hist = px.histogram(
        results, 
        x='treatment_effect',
        nbins=50,
        title=f'Treatment Effect Distribution: {len(results)} Counties',
        labels={'treatment_effect': 'Treatment Effect'}
    )
    fig_hist.add_vline(
        x=results['treatment_effect'].mean(),
        line_dash="dash",
        annotation_text=f"Mean: {results['treatment_effect'].mean()*100:.1f}pp"
    )
    fig_hist.write_html('results/visualizations/effect_distribution.html')
    print("   ✓ Saved: effect_distribution.html")
    
    # 5. Scatter of all counties
    print("\n5. Scatter plot (all counties)...")
    results['state'] = results['county'].str.split(', ').str[1]
    results['effect_pp'] = results['treatment_effect'] * 100
    
    fig_scatter = px.scatter(
        results,
        x='control_gap',
        y='treatment_effect',
        color='effect_pp',
        color_continuous_scale='RdYlGn_r',
        color_continuous_midpoint=0,
        hover_name='county',
        hover_data={
            'state': True,
            'n_white': True,
            'n_black': True,
            'control_gap': ':.1%',
            'treatment_effect': ':.1%'
        },
        labels={
            'control_gap': 'Baseline Disparity (Control)',
            'treatment_effect': 'AI Treatment Effect',
            'effect_pp': 'Effect (pp)'
        },
        title=f'AI Treatment Effects: All {len(results)} Counties'
    )
    fig_scatter.add_hline(y=0, line_dash="dash", line_color="gray")
    fig_scatter.update_layout(width=1400, height=800)
    fig_scatter.write_html('results/visualizations/all_counties_scatter.html')
    print("   ✓ Saved: all_counties_scatter.html")
    
    print("\n" + "="*70)
    print("VISUALIZATION COMPLETE")
    print("="*70)
    print("\nCreated:")
    print("  1. true_county_map.html - County-level choropleth (if FIPS available)")
    print("  2. state_aggregated.html - State-level aggregation")
    print("  3. top_100_counties.html - Point map of extreme counties")
    print("  4. effect_distribution.html - Histogram")
    print("  5. all_counties_scatter.html - Scatter plot")
    print("\nOpen:")
    print("  open results/visualizations/true_county_map.html")
    print("  open results/visualizations/all_counties_scatter.html")


if __name__ == "__main__":
    main()