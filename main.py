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

# Make sure data is sorted by rank
df = df.sort_values(by="Rank")

# Add buttons for selecting top N players (horizontal layout)
st.markdown("### Top ATP Stats country and age")
top_n = st.radio(
    "Select top N players",
    options=[10, 20, 50, 100, 200, 500, 1000],
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

# -------------------- ENHANCED AGE ANALYSIS --------------------
st.markdown("### Age Distribution Analysis")

# Create two columns for the age analysis
age_col1, age_col2 = st.columns([3, 2])

# Age Analysis
age_values = df_top_n["Age"].dropna()
q1, q3 = np.percentile(age_values, [25, 75])
mean_age = np.mean(age_values)

with age_col1:
    # Create histogram for detailed age distribution
    fig_age_hist = go.Figure()

    # Add histogram
    fig_age_hist.add_trace(go.Histogram(
        x=df_top_n["Age"].dropna(),
        nbinsx=20,
        marker_color='rgba(52, 152, 219, 0.7)',
        name="Age Distribution",
        hovertemplate="Age: %{x}<br>Count: %{y}"
    ))

    # Add line for mean age
    fig_age_hist.add_vline(x=mean_age, line_dash="dash", line_color="red",
                           annotation_text=f"Mean: {mean_age:.1f}",
                           annotation_position="top right")

    # Add rug plot at the bottom for individual player ages
    fig_age_hist.add_trace(go.Scatter(
        x=df_top_n["Age"].dropna(),
        y=[0] * len(df_top_n["Age"].dropna()),
        mode="markers",
        marker=dict(
            symbol="line-ns",
            color="rgba(0, 0, 0, 0.3)",
            line=dict(width=1),
            size=8
        ),
        hoverinfo="skip",
        showlegend=False
    ))

    fig_age_hist.update_layout(
        title=f"Age Distribution of Top {top_n} Players",
        xaxis=dict(title="Age", range=[15, 45]),
        yaxis=dict(title="Number of Players"),
        bargap=0.1,
        template="plotly_white",
        height=400,
    )

    st.plotly_chart(fig_age_hist)

with age_col2:
    # Display age summary statistics
    st.subheader("Age Statistics")

    min_age = df_top_n["Age"].min()
    max_age = df_top_n["Age"].max()
    median_age = df_top_n["Age"].median()
    std_age = df_top_n["Age"].std()

    age_stats_df = pd.DataFrame({
        "Metric": ["Minimum Age", "Maximum Age", "Mean Age", "Median Age", "Q1 (25%)", "Q3 (75%)", "Std Deviation"],
        "Value": [
            f"{min_age:.1f}",
            f"{max_age:.1f}",
            f"{mean_age:.1f}",
            f"{median_age:.1f}",
            f"{q1:.1f}",
            f"{q3:.1f}",
            f"{std_age:.1f}"
        ]
    })

    st.table(age_stats_df)

    # Age Distribution Grouped by 5-Year Intervals
    bins = list(range(15, 51, 5))  # 16-20, 21-25, ..., 46-50
    labels = [f"{b}-{b+4}" for b in bins[:-1]]
    df_top_n["Age Group"] = pd.cut(
        df_top_n["Age"], bins=bins, labels=labels, right=True)
    age_group_counts = df_top_n["Age Group"].value_counts().sort_index()

    # Add age group bar chart
    fig_age_groups = go.Figure()
    fig_age_groups.add_trace(go.Bar(
        x=age_group_counts.index,
        y=age_group_counts.values,
        marker_color='rgba(231, 76, 60, 0.7)',
        text=age_group_counts.values,
        textposition='outside',
    ))

    fig_age_groups.update_layout(
        title="Players by Age Group",
        xaxis=dict(title="Age Group"),
        yaxis=dict(title="Count"),
        showlegend=False,
        height=250,
        margin=dict(l=40, r=40, t=40, b=40),
    )

    st.plotly_chart(fig_age_groups)

# -------------------- PLAYERS PER POPULATION ANALYSIS --------------------
st.markdown("### Players per Million Population")

# Population data for top tennis countries (in millions, 2023 estimates)
population_data = {
    "USA": 331.9, "ESP": 47.4, "FRA": 67.8, "GBR": 67.3, "ITA": 60.3,
    "ARG": 45.8, "AUS": 25.7, "GER": 83.1, "SUI": 8.7, "CAN": 38.2,
    "JPN": 125.7, "CZE": 10.7, "SRB": 6.9, "AUT": 9.0, "NED": 17.4,
    "POL": 37.8, "CRO": 4.0, "BRA": 213.4, "RSA": 60.0, "BEL": 11.6,
    "POR": 10.3, "SWE": 10.4, "NOR": 5.4, "GRE": 10.6, "CHN": 1412.0,
    "CHI": 19.2  # Chile
}

# Calculate players per million for each country in the dataset
country_counts_all = df_top_n["Country"].value_counts().reset_index()
country_counts_all.columns = ["Country", "Number of Players"]

# Add population data and calculate players per million
country_counts_all["Population (M)"] = country_counts_all["Country"].map(
    population_data)
country_counts_all["Players per Million"] = country_counts_all.apply(
    lambda row: row["Number of Players"] /
    row["Population (M)"] if pd.notna(row["Population (M)"]) else None,
    axis=1
)

# Filter out countries with missing population data
country_counts_all = country_counts_all.dropna(subset=["Players per Million"])

# Sort by players per million and get top 15
top_per_capita = country_counts_all.sort_values(
    "Players per Million", ascending=False).head(15)

# Create visualization
fig_per_capita = go.Figure()

# Add bars
fig_per_capita.add_trace(go.Bar(
    x=top_per_capita["Country"],
    y=top_per_capita["Players per Million"],
    marker_color='rgba(46, 204, 113, 0.7)',
    text=[f"{x:.2f}" for x in top_per_capita["Players per Million"]],
    textposition='outside',
))

# Update layout
fig_per_capita.update_layout(
    title=f"Top 15 Countries by Top {top_n} Players per Million Population",
    xaxis=dict(title="Country", tickangle=-45),
    yaxis=dict(title="Players per Million Population"),
    height=500,
    margin=dict(l=40, r=40, b=80, t=80),
    template="plotly_white",
)

st.plotly_chart(fig_per_capita)

# Add a data table for reference
st.subheader("Country Breakdown by Population")
display_df = top_per_capita[["Country", "Number of Players", "Population (M)", "Players per Million"]].sort_values(
    "Players per Million", ascending=False
)
display_df = display_df.reset_index(drop=True)
display_df["Players per Million"] = display_df["Players per Million"].round(2)
st.dataframe(display_df)

# -------------------- CONTINENT ANALYSIS --------------------
st.markdown("### Player Distribution by Continent")

# Country to continent mapping
continent_mapping = {
    # Europe
    "ESP": "Europe", "FRA": "Europe", "GBR": "Europe", "ITA": "Europe",
    "GER": "Europe", "SUI": "Europe", "CZE": "Europe", "SRB": "Europe",
    "AUT": "Europe", "NED": "Europe", "POL": "Europe", "CRO": "Europe",
    "BEL": "Europe", "POR": "Europe", "SWE": "Europe", "NOR": "Europe",
    "GRE": "Europe", "BUL": "Europe", "ROU": "Europe", "HUN": "Europe",
    "SVK": "Europe", "FIN": "Europe", "DEN": "Europe", "UKR": "Europe",
    "LAT": "Europe", "EST": "Europe", "LTU": "Europe", "SLO": "Europe",
    "MDA": "Europe", "RUS": "Europe", "BLR": "Europe", "MNE": "Europe",
    "BIH": "Europe", "LUX": "Europe", "IRL": "Europe", "ISL": "Europe",

    # North America
    "USA": "North America", "CAN": "North America", "MEX": "North America",
    "DOM": "North America", "PUR": "North America",

    # South America
    "ARG": "South America", "BRA": "South America", "CHI": "South America",
    "COL": "South America", "URU": "South America", "ECU": "South America",
    "PER": "South America", "VEN": "South America", "BOL": "South America",
    "PAR": "South America",

    # Asia
    "JPN": "Asia", "CHN": "Asia", "KOR": "Asia", "IND": "Asia",
    "TPE": "Asia", "UZB": "Asia", "KAZ": "Asia", "THA": "Asia",
    "HKG": "Asia", "PAK": "Asia", "MAS": "Asia", "SIN": "Asia",

    # Oceania
    "AUS": "Oceania", "NZL": "Oceania",

    # Africa
    "RSA": "Africa", "TUN": "Africa", "MAR": "Africa", "EGY": "Africa",
    "ALG": "Africa", "ZIM": "Africa", "NGR": "Africa", "KEN": "Africa"
}

# Add continent to the dataframe
df_top_n["Continent"] = df_top_n["Country"].map(continent_mapping)

# Count players by continent
continent_counts = df_top_n["Continent"].value_counts().reset_index()
continent_counts.columns = ["Continent", "Number of Players"]

# Calculate percentage
total_players = continent_counts["Number of Players"].sum()
continent_counts["Percentage"] = (
    continent_counts["Number of Players"] / total_players * 100).round(1)

# Sort by number of players
continent_counts = continent_counts.sort_values(
    "Number of Players", ascending=False)

# Create two columns
cont_col1, cont_col2 = st.columns([2, 1])

with cont_col1:
    # Create pie chart
    fig_continent = go.Figure()
    fig_continent.add_trace(go.Pie(
        labels=continent_counts["Continent"],
        values=continent_counts["Number of Players"],
        hole=0.4,
        marker=dict(
            colors=[
                'rgba(52, 152, 219, 0.8)',  # Blue (Europe)
                'rgba(46, 204, 113, 0.8)',  # Green (North America)
                'rgba(155, 89, 182, 0.8)',  # Purple (South America)
                'rgba(241, 196, 15, 0.8)',  # Yellow (Asia)
                'rgba(230, 126, 34, 0.8)',  # Orange (Oceania)
                'rgba(231, 76, 60, 0.8)',   # Red (Africa)
            ]
        ),
        textinfo="label+percent",
        hoverinfo="label+value+percent",
        textfont=dict(size=14)
    ))

    fig_continent.update_layout(
        title=f"Distribution of Top {top_n} Players by Continent",
        height=500,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )

    st.plotly_chart(fig_continent)

with cont_col2:
    # Display table with absolute numbers
    st.subheader("Players by Continent")
    continent_table = continent_counts.copy()
    continent_table["Percentage"] = continent_table["Percentage"].apply(
        lambda x: f"{x}%")
    st.table(continent_table)

    # Show top countries per continent
    st.subheader("Top Country per Continent")
    top_country_per_continent = []

    for continent in continent_counts["Continent"]:
        # Filter countries in this continent
        continent_countries = df_top_n[df_top_n["Continent"]
                                       == continent]["Country"].value_counts()
        if not continent_countries.empty:
            top_country = continent_countries.index[0]
            count = continent_countries.iloc[0]
            top_country_per_continent.append({
                "Continent": continent,
                "Top Country": top_country,
                "Players": count
            })

    top_country_df = pd.DataFrame(top_country_per_continent)
    st.table(top_country_df)

# -------------------- AGE DISTRIBUTION BY TOP COUNTRIES --------------------
st.markdown("### Age Distribution by Top Countries")

# Get top 8 countries by player count
top_countries = df_top_n["Country"].value_counts().head(8).index.tolist()

# Filter data for these countries
top_countries_data = df_top_n[df_top_n["Country"].isin(top_countries)]

# Create box plot
fig_age_country = go.Figure()

for country in top_countries:
    country_data = top_countries_data[top_countries_data["Country"]
                                      == country]["Age"].dropna()

    # Skip if no data
    if len(country_data) == 0:
        continue

    # Add box plot for this country
    fig_age_country.add_trace(go.Box(
        y=country_data,
        name=country,
        boxpoints='all',  # Show all points
        jitter=0.3,
        pointpos=-1.8,
        marker=dict(size=4),
        boxmean=True  # Show mean
    ))

fig_age_country.update_layout(
    title="Age Distribution Across Top 8 Tennis Nations",
    yaxis=dict(title="Age"),
    xaxis=dict(title="Country"),
    height=500,
    template="plotly_white",
    showlegend=False
)

st.plotly_chart(fig_age_country)

# Add a table with age stats by country
age_stats_by_country = []

for country in top_countries:
    country_ages = top_countries_data[top_countries_data["Country"]
                                      == country]["Age"].dropna()

    if len(country_ages) > 0:
        age_stats_by_country.append({
            "Country": country,
            "Count": len(country_ages),
            "Min Age": round(country_ages.min(), 1),
            "Max Age": round(country_ages.max(), 1),
            "Mean Age": round(country_ages.mean(), 1),
            "Median Age": round(country_ages.median(), 1)
        })

age_stats_country_df = pd.DataFrame(age_stats_by_country)
st.table(age_stats_country_df)

# -------------------- ATP RANKING POINTS ANALYSIS --------------------
st.markdown("### ATP Ranking Points Distribution")

# Check if the Points column exists in the dataset
if "Points" in df.columns:
    # Create points distribution visualization
    points_col1, points_col2 = st.columns([3, 2])

    with points_col1:
        # Create log scale distribution of points
        fig_points = go.Figure()

        # Add scatter plot with points
        fig_points.add_trace(go.Scatter(
            x=list(range(1, len(df_top_n) + 1)),
            y=df_top_n["Points"],
            mode="markers",
            marker=dict(
                size=8,
                color=df_top_n["Points"],
                colorscale="Viridis",
                showscale=True,
                colorbar=dict(title="Points")
            ),
            hovertemplate="Rank: %{x}<br>Points: %{y}<br>Player: %{text}",
            text=df_top_n["Name"]
        ))

        # Add log scale option
        use_log_scale = st.checkbox(
            "Use logarithmic scale for points", value=True)

        # Update y-axis based on scale selection
        if use_log_scale:
            fig_points.update_layout(yaxis_type="log")

        fig_points.update_layout(
            title="ATP Ranking Points by Rank",
            xaxis=dict(title="Rank"),
            yaxis=dict(title="Points"),
            height=500,
            template="plotly_white",
        )

        st.plotly_chart(fig_points)

    with points_col2:
        # Calculate points distribution stats
        points_stats = {
            "Total Points (Top 10)": df_top_n.iloc[:10]["Points"].sum(),
            "Total Points (All)": df_top_n["Points"].sum(),
            "% Points in Top 10": round(df_top_n.iloc[:10]["Points"].sum() / df_top_n["Points"].sum() * 100, 1),
            "% Points in Top 20": round(df_top_n.iloc[:20]["Points"].sum() / df_top_n["Points"].sum() * 100, 1),
            "% Points in Top 50": round(df_top_n.iloc[:50]["Points"].sum() / df_top_n["Points"].sum() * 100, 1),
            "Highest Points": df_top_n["Points"].max(),
            "Median Points": df_top_n["Points"].median(),
            "Points Needed for Top 100": df_top_n.iloc[99]["Points"] if len(df_top_n) >= 100 else "N/A",
            "Points Needed for Top 200": df_top_n.iloc[199]["Points"] if len(df_top_n) >= 200 else "N/A"
        }

        points_stats_df = pd.DataFrame({
            "Metric": list(points_stats.keys()),
            "Value": list(points_stats.values())
        })

        st.subheader("Points Distribution Statistics")
        st.table(points_stats_df)

        # Add points concentration visualization
        point_thresholds = [
            df_top_n.iloc[9]["Points"] if len(df_top_n) > 9 else 0,  # Top 10
            df_top_n.iloc[19]["Points"] if len(df_top_n) > 19 else 0,  # Top 20
            df_top_n.iloc[49]["Points"] if len(df_top_n) > 49 else 0,  # Top 50
            df_top_n.iloc[99]["Points"] if len(
                df_top_n) > 99 else 0   # Top 100
        ]

        threshold_labels = ["Top 10", "Top 20", "Top 50", "Top 100"]

        # Create a horizontal bar chart for point thresholds
        fig_thresholds = go.Figure()
        fig_thresholds.add_trace(go.Bar(
            y=threshold_labels,
            x=point_thresholds,
            orientation='h',
            marker_color='rgba(155, 89, 182, 0.7)',
            text=point_thresholds,
            textposition='outside',
        ))

        fig_thresholds.update_layout(
            title="Points Threshold by Ranking Group",
            xaxis=dict(title="Minimum ATP Points Required"),
            height=300,
            margin=dict(l=40, r=40, t=40, b=40),
        )

        st.plotly_chart(fig_thresholds)
else:
    st.warning(
        "Points data not available in the dataset. This analysis requires ATP ranking points.")
