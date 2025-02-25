import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
import shutil
from datetime import datetime

st.set_page_config(
    page_title="ATP Stats",  # Title of your app
    page_icon="🎾",  # Icon for the page
    layout="wide",  # Wide layout for better use in iframe
    initial_sidebar_state="collapsed"  # Sidebar collapsed by default
)

# Load Data
df = pd.read_csv("atp_rankings.csv")


# Read the last real update date
if os.path.exists("last_updated.txt"):
    with open("last_updated.txt", "r") as f:
        last_modified_date = f.read().strip()
else:
    last_modified_date = "Unknown"

# Format for display
st.markdown(f"**Last Update:** {last_modified_date}")







# Display last update date
st.markdown(f"**Last Update:** {last_modified_date}")

# Make a copy of the file with the current date
original_file = "rank_atp.csv"
date_str = datetime.now().strftime("%Y-%m-%d")
backup_file = f"rank_atp_{date_str}.csv"

# Make a copy of the file with the current date
shutil.copy(original_file, backup_file)

# Overwrite the original file with the new rankings data
df_new = pd.read_csv(f"atp_rankings_data/atp_rankings_2025-02-23.csv")
df_new.to_csv(original_file, index=False)  # Overwrite original file


# Make sure data is sorted by rank
df = df.sort_values(by="Rank")

# Add buttons for selecting top N players (horizontal layout)
st.markdown("### Top ATP Stats country and age")
top_n = st.radio(
    "Select top N players",
    options=[10,20, 50, 100, 200, 500, 1000],
    index=2,  # Default to top 1000
    horizontal=True
)

# Filter the data to show the top N players BY RANK
df_top_n = df.head(top_n)

# Generate the count of players by country
country_counts = df_top_n["Country"].value_counts().reset_index()
country_counts.columns = ["Country", "Number of Players"]

# Get top 10 countries
country_counts_top = country_counts.head(10)

# Country to flag code mapping - add more as needed
flag_codes = {
    "USA": "us", "ESP": "es", "FRA": "fr", "GBR": "gb", "ITA": "it",
    "ARG": "ar", "AUS": "au", "GER": "de", "SUI": "ch", "CAN": "ca", "JPN": "jp", "CZE": "cz", "SRB": "rs", "AUT": "at",
    "NED": "nl", "POL": "pl", "CRO": "hr", "BRA": "br", "RSA": "za",
    "BEL": "be", "POR": "pt", "SWE": "se", "NOR": "no", "GRE": "gr", "CHN": "cn", "CHI": "cn"
}

# Create the figure
fig = go.Figure()

# Add bars
fig.add_trace(go.Bar(
    x=country_counts_top["Country"],
    y=country_counts_top["Number of Players"],
    hovertext=[f"{row['Country']}: {row['Number of Players']} players" for _,
               row in country_counts_top.iterrows()],
    marker=dict(color='rgb(52, 152, 219)', line=dict(
        color='rgb(8, 48, 107)', width=1)),
    text=country_counts_top["Number of Players"],
    textposition='inside',
    # Change text color to white and bold
    textfont=dict(color="white", size=14, family="Arial Black")
))

# Update layout
fig.update_layout(
    title=f"Top 10 Countries by Player Count (from Top {top_n} Players by Rank)",
    yaxis=dict(
        title="Number of Players",
        range=[0, max(country_counts_top["Number of Players"]) * 1.1]
    ),
    xaxis=dict(
        tickangle=-45,
    ),
    bargap=0.2,
    margin=dict(l=40, r=40, b=50, t=80),
    showlegend=False,
    template="plotly_white",
    height=400,
)

# Fix the gap between y-axis and first bar
fig.update_xaxes(
    range=[-0.5, len(country_counts_top)-0.5],
    constrain="domain"
)

# Display the chart
st.plotly_chart(fig)

# Create fixed-width container for proper alignment
st.markdown(
    """
    <style>
    .flag-container {
        display: flex;
        justify-content: space-around; /* Space evenly */
        margin-top: -30px; /* Adjust this value to fine-tune vertical alignment */
        width: 100%;
        padding: 0 40px; /* Adjust padding to match chart margins */
    }
    .flag-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 60px; /* Fixed width for each flag item */
        margin: 0; /* Remove any additional margin */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Generate correctly positioned flags with custom HTML
flag_html = "<div class='flag-container'>"
for country in country_counts_top["Country"]:
    # Default to 'un' if not found
    flag_code = flag_codes.get(country.upper(), 'un')
    flag_html += f"<div class='flag-item'><img src='https://flagcdn.com/32x24/{flag_code.lower()}.png' width='32'></div>"
flag_html += "</div>"

# Display flags
st.markdown(flag_html, unsafe_allow_html=True)



# --- Age Analysis (Curve with Mean & Quartiles) ---
# Age Analysis
age_values = df_top_n["Age"].dropna()
q1, q3 = np.percentile(age_values, [25, 75])
mean_age = np.mean(age_values)

# Display Age Summary Table
st.markdown("### Age Summary")
age_summary_df = pd.DataFrame({
    "Metric": ["Average Age", "Q1 (25th Percentile)", "Q3 (75th Percentile)"],
    "Value": [round(mean_age, 2), round(q1, 2), round(q3, 2)]
})
st.table(age_summary_df)

# --- Age Distribution as Line Chart ---
# --- Age Distribution Grouped by 5-Year Intervals ---
bins = list(range(15, 51, 5))  # 16-20, 21-25, ..., 46-50
labels = [f"{b}-{b+4}" for b in bins[:-1]]
df_top_n["Age Group"] = pd.cut(
    df_top_n["Age"], bins=bins, labels=labels, right=True)
age_group_counts = df_top_n["Age Group"].value_counts().sort_index()

fig_age = go.Figure()
fig_age.add_trace(go.Scatter(
    x=age_group_counts.index,
    y=age_group_counts.values,
    mode='lines+markers',
    marker=dict(size=8, color='rgb(231, 76, 60)'),
    line=dict(width=2, color='rgb(100, 30, 22)')
))

fig_age.update_layout(
    title=f"Age Group Distribution of Top {top_n} Players",
    xaxis=dict(title="Age Group"),
    yaxis=dict(title="Number of Players"),
    showlegend=False,
    template="plotly_white",
    height=400,
)
st.plotly_chart(fig_age)
