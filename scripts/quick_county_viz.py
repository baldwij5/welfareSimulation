"""
Quick County Map Visualization

Creates US county-level choropleth from all_counties_results.csv
"""

import pandas as pd
import plotly.graph_objects as go

# Load results
results = pd.read_csv('results/all_counties_results.csv')
print(f"Loaded {len(results)} counties")

# Create simple summary map by state
results['state'] = results['county'].str.split(', ').str[1]

# Aggregate to state level
state_summary = results.groupby('state').agg({
    'treatment_effect': 'mean',
    'control_gap': 'mean',
    'n_white': 'sum'
}).reset_index()

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

# Create map
fig = go.Figure(data=go.Choropleth(
    locations=state_summary['abbr'],
    z=state_summary['effect_pp'],
    locationmode='USA-states',
    colorscale='RdYlGn_r',
    zmid=0,
    text=state_summary['state'],
    hovertemplate='<b>%{text}</b><br>Effect: %{z:.1f}pp<extra></extra>'
))

fig.update_layout(
    title='AI Treatment Effects by State (from 1,238 counties)',
    geo_scope='usa',
    width=1400,
    height=800
)

import os
os.makedirs('results/visualizations', exist_ok=True)
fig.write_html('results/visualizations/county_results_map.html')

print("\n✓ Map saved: results/visualizations/county_results_map.html")
print("\nOpen with: open results/visualizations/county_results_map.html")

# Also create distribution
import plotly.express as px

fig2 = px.histogram(results, x='treatment_effect', nbins=50,
                    title=f'Distribution of Treatment Effects ({len(results)} counties)')
fig2.add_vline(x=results['treatment_effect'].mean(), line_dash="dash", 
               annotation_text=f"Mean: {results['treatment_effect'].mean()*100:.1f}pp")
fig2.write_html('results/visualizations/county_distribution.html')

print("✓ Distribution saved: results/visualizations/county_distribution.html")