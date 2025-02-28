import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.lines import Line2D
import matplotlib.dates as mdates
from datetime import datetime
import requests
from io import StringIO

# For interactive web apps
import streamlit as st


def load_player_ranking_data(player_name):
    """
    In a production environment, this would fetch data from a tennis API or database.
    For this example, we're using sample data.
    """
    # Sample data - in production would come from tennis-data.co.uk or ATP API
    if player_name.lower() == 'federer':
        data = {
            'date': ['2001-01-01', '2001-07-01', '2003-02-01', '2004-02-01',
                     '2008-08-01', '2009-07-01', '2010-06-01', '2012-07-01',
                     '2016-01-01', '2016-07-01', '2017-01-01', '2018-02-01',
                     '2019-07-01', '2021-03-01', '2022-07-01'],
            'ranking': [29, 15, 5, 1, 2, 1, 3, 1, 3, 16, 17, 1, 3, 6, 96],
            'event': [None, "First Wimbledon QF", None, "Reached #1 for first time",
                      "Lost #1 ranking", "Regained #1 after Wimbledon win", None,
                      "Returned to #1 after Wimbledon", None, "Knee injury", None,
                      "Oldest #1 in history", None, "Return from injury", "Final tournament"]
        }
    elif player_name.lower() == 'nadal':
        data = {
            'date': ['2003-01-01', '2005-06-01', '2008-08-01', '2009-07-01',
                     '2010-06-01', '2011-07-01', '2013-10-01', '2015-06-01',
                     '2017-10-01', '2018-05-01', '2021-03-01', '2022-06-01',
                     '2023-01-01'],
            'ranking': [200, 3, 1, 2, 1, 2, 1, 10, 1, 1, 3, 4, 6],
            'event': [None, "First French Open win", "Reached #1 for first time",
                      "Knee tendinitis", "Regained #1", None, "Return to #1",
                      "Injury struggles", "Return to #1", None, None,
                      "Won 22nd Grand Slam", "Hip injury"]
        }
    else:
        # Default empty data for other players
        data = {'date': [], 'ranking': [], 'event': []}

    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    return df


def get_career_events(player_name):
    """
    Fetch major career events for a player.
    In production, this would come from a database or API.
    """
    # Sample career milestones - in production would be more comprehensive
    events = {
        'federer': [
            {'date': '2003-07-06',
                'event': 'First Grand Slam title (Wimbledon)', 'importance': 'major'},
            {'date': '2004-02-02', 'event': 'First reached World No. 1',
                'importance': 'major'},
            {'date': '2009-06-07',
                'event': 'Completed Career Grand Slam (French Open)', 'importance': 'major'},
            {'date': '2016-07-26', 'event': 'Announced knee surgery, ended season',
                'importance': 'injury'},
            {'date': '2017-01-29', 'event': 'Comeback win at Australian Open',
                'importance': 'major'},
            {'date': '2018-02-19', 'event': 'Oldest World No. 1 in history',
                'importance': 'record'},
            {'date': '2022-09-23', 'event': 'Retirement at Laver Cup',
                'importance': 'major'}
        ],
        'nadal': [
            {'date': '2005-06-05',
                'event': 'First Grand Slam title (French Open)', 'importance': 'major'},
            {'date': '2008-08-18', 'event': 'First reached World No. 1',
                'importance': 'major'},
            {'date': '2009-05-31', 'event': 'First French Open loss',
                'importance': 'significant'},
            {'date': '2009-06-19',
                'event': 'Withdrew from Wimbledon (tendinitis)', 'importance': 'injury'},
            {'date': '2010-09-13',
                'event': 'Completed Career Grand Slam (US Open)', 'importance': 'major'},
            {'date': '2016-10-12',
                'event': 'Ended season early (wrist injury)', 'importance': 'injury'},
            {'date': '2022-01-30',
                'event': 'Record 21st Grand Slam (Australian Open)', 'importance': 'record'},
            {'date': '2022-06-05', 'event': 'Record 14th French Open title',
                'importance': 'record'}
        ]
    }

    return events.get(player_name.lower(), [])


def analyze_career_trajectory(player_df, events):
    """
    Analyze a player's career trajectory to identify inflection points
    """
    # Convert events to DataFrame
    events_df = pd.DataFrame(events)
    if not events_df.empty:
        events_df['date'] = pd.to_datetime(events_df['date'])

    # Find significant ranking changes (inflection points)
    player_df['ranking_change'] = player_df['ranking'].diff()

    # Identify significant improvements or declines
    # Negative change means improvement in ranking (lower number is better)
    player_df['significance'] = 'stable'
    player_df.loc[player_df['ranking_change'] <= -
                  5, 'significance'] = 'major_improvement'
    player_df.loc[player_df['ranking_change']
                  >= 5, 'significance'] = 'major_decline'

    # Combine with career events for a complete picture
    analysis = {
        'ranking_data': player_df,
        'events': events_df if not events_df.empty else pd.DataFrame(),
        'inflection_points': player_df[player_df['significance'] != 'stable'].copy()
    }

    return analysis


def plot_career_trajectory(analysis_dict, player_name, save_path=None):
    """
    Create a visualization of a player's career trajectory with inflection points
    """
    player_df = analysis_dict['ranking_data']
    events_df = analysis_dict['events']

    # Set up the plot
    plt.figure(figsize=(12, 8))
    sns.set_style("whitegrid")

    # Plot the ranking trajectory (lower is better, so invert y-axis)
    plt.plot(player_df['date'], player_df['ranking'], 'b-', linewidth=2)
    plt.gca().invert_yaxis()

    # Mark inflection points
    for _, row in analysis_dict['inflection_points'].iterrows():
        if row['significance'] == 'major_improvement':
            plt.scatter(row['date'], row['ranking'],
                        color='green', s=100, zorder=5)
        elif row['significance'] == 'major_decline':
            plt.scatter(row['date'], row['ranking'],
                        color='red', s=100, zorder=5)

    # Add career events
    if not events_df.empty:
        event_dates = events_df['date'].tolist()
        # Find closest ranking date for each event
        for event_date, event_name, importance in zip(events_df['date'], events_df['event'], events_df['importance']):
            # Find closest date in player_df
            closest_idx = (player_df['date'] - event_date).abs().idxmin()
            closest_ranking = player_df.loc[closest_idx, 'ranking']

            marker_color = 'purple' if importance == 'major' else 'orange' if importance == 'injury' else 'blue'
            plt.scatter(event_date, closest_ranking,
                        color=marker_color, s=80, zorder=5, marker='*')

            # Add annotation for major events
            if importance in ['major', 'record']:
                plt.annotate(event_name,
                             xy=(event_date, closest_ranking),
                             xytext=(10, 0),
                             textcoords='offset points',
                             fontsize=8,
                             rotation=45,
                             ha='left')

    # Customize the plot
    plt.title(
        f"{player_name}'s Career Trajectory and Inflection Points", fontsize=16)
    plt.xlabel('Year', fontsize=12)
    plt.ylabel('ATP Ranking', fontsize=12)

    # Format x-axis to show years
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    plt.gca().xaxis.set_major_locator(mdates.YearLocator(2))  # Show every 2 years
    plt.xticks(rotation=45)

    # Add a legend
    legend_elements = [
        Line2D([0], [0], color='b', lw=2, label='Ranking Trajectory'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='green',
               markersize=10, label='Major Improvement'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='red',
               markersize=10, label='Major Decline'),
        Line2D([0], [0], marker='*', color='w', markerfacecolor='purple',
               markersize=10, label='Major Achievement'),
        Line2D([0], [0], marker='*', color='w', markerfacecolor='orange',
               markersize=10, label='Injury/Setback')
    ]
    plt.legend(handles=legend_elements, loc='best')

    plt.tight_layout()

    # Save if requested
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    return plt


def create_streamlit_app():
    """
    Create a Streamlit web app for interactive career analysis
    """
    st.title("Tennis Career Inflection Points Analyzer")

    # Player selection
    player_options = ["Federer", "Nadal"]
    selected_players = st.multiselect(
        "Select players to analyze:",
        options=player_options,
        default=["Federer"]
    )

    if not selected_players:
        st.warning("Please select at least one player.")
        return

    # Create tabs for each player and comparison
    tabs = ["Individual Analysis"] + \
        (["Comparison"] if len(selected_players) > 1 else [])
    selected_tab = st.radio("Analysis Type:", tabs)

    if selected_tab == "Individual Analysis":
        for player in selected_players:
            st.header(f"{player}'s Career Analysis")

            # Load and analyze data
            player_data = load_player_ranking_data(player)
            player_events = get_career_events(player)
            analysis = analyze_career_trajectory(player_data, player_events)

            # Plot
            fig = plt.figure(figsize=(12, 8))
            plot_fig = plot_career_trajectory(analysis, player)
            st.pyplot(plot_fig.figure)
            plt.close()

            # Show key inflection points
            st.subheader("Key Career Moments:")

            # Combine ranking events and career events
            key_moments = []
            for _, row in analysis['ranking_data'][analysis['ranking_data']['event'].notna()].iterrows():
                key_moments.append({
                    'date': row['date'],
                    'event': row['event'],
                    'ranking': row['ranking'],
                    'type': 'Ranking Change'
                })

            if not analysis['events'].empty:
                for _, row in analysis['events'].iterrows():
                    key_moments.append({
                        'date': row['date'],
                        'event': row['event'],
                        'ranking': 'N/A',  # Could look up nearest ranking if needed
                        'type': row['importance'].title()
                    })

            # Sort by date
            key_moments = sorted(key_moments, key=lambda x: x['date'])

            # Display as a table
            if key_moments:
                moments_df = pd.DataFrame(key_moments)
                moments_df['date'] = moments_df['date'].dt.strftime('%Y-%m-%d')
                moments_df.columns = ['Date', 'Event', 'Ranking', 'Type']
                st.table(moments_df)
            else:
                st.write("No key moments found.")

    elif selected_tab == "Comparison":
        st.header("Player Comparison")

        # Create comparison plot
        fig, ax = plt.subplots(figsize=(12, 8))

        # Plot each player with different colors
        colors = ['blue', 'red', 'green', 'orange']

        for i, player in enumerate(selected_players):
            player_data = load_player_ranking_data(player)
            player_events = get_career_events(player)
            analysis = analyze_career_trajectory(player_data, player_events)

            # Plot ranking trajectory
            ax.plot(player_data['date'], player_data['ranking'],
                    color=colors[i % len(colors)],
                    linewidth=2,
                    label=player)

            # Mark major achievements
            if not analysis['events'].empty:
                major_events = analysis['events'][analysis['events']
                                                  ['importance'] == 'major']
                for _, event in major_events.iterrows():
                    # Find closest ranking
                    closest_idx = (
                        player_data['date'] - event['date']).abs().idxmin()
                    closest_ranking = player_data.loc[closest_idx, 'ranking']

                    ax.scatter(event['date'], closest_ranking,
                               color=colors[i % len(colors)],
                               marker='*', s=100)

        # Customize plot
        ax.invert_yaxis()  # Lower ranking is better
        ax.set_title("Career Trajectory Comparison", fontsize=16)
        ax.set_xlabel("Year", fontsize=12)
        ax.set_ylabel("ATP Ranking", fontsize=12)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.xaxis.set_major_locator(mdates.YearLocator(2))
        plt.xticks(rotation=45)
        plt.legend()
        plt.grid(True, alpha=0.3)

        st.pyplot(fig)

        # Career longevity and achievements comparison
        st.subheader("Career Comparison")

        comparison_data = []
        for player in selected_players:
            player_data = load_player_ranking_data(player)
            player_events = get_career_events(player)

            # Calculate career stats
            career_length = (player_data['date'].max(
            ) - player_data['date'].min()).days / 365.25
            weeks_at_no1 = len(player_data[player_data['ranking'] == 1])
            best_ranking = player_data['ranking'].min()

            # Count major achievements
            major_wins = sum(1 for event in player_events if 'Grand Slam' in event.get(
                'event', '') and event.get('importance') == 'major')

            comparison_data.append({
                'Player': player,
                'Career Length (years)': round(career_length, 1),
                'Weeks at #1': weeks_at_no1,
                'Best Ranking': best_ranking,
                'Major Titles': major_wins
            })

        comparison_df = pd.DataFrame(comparison_data)
        st.table(comparison_df)


# For direct script execution
if __name__ == "__main__":
    # Example of direct use without Streamlit
    player_name = "Federer"
    player_data = load_player_ranking_data(player_name)
    player_events = get_career_events(player_name)
    analysis = analyze_career_trajectory(player_data, player_events)

    # Create and show plot
    plt.figure(figsize=(12, 8))
    plot = plot_career_trajectory(analysis, player_name)
    plt.show()

    # Or use Streamlit
    # Uncomment to run as a Streamlit app:
    # create_streamlit_app()
