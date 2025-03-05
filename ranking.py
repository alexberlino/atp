import shutil
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import csv
from datetime import datetime
import time
import re
import pandas as pd
import subprocess
import matplotlib.pyplot as plt
import numpy as np
import json


def setup_driver():
    options = uc.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920x1080")
    options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Use undetected_chromedriver instead of regular Chrome
    return uc.Chrome(options=options)


def is_properly_formatted_row(cells):
    """
    Check if the row matches the expected format of the ranking data
    """
    if len(cells) < 7:
        return False

    try:
        # Check rank format (should be just a number)
        rank = cells[0].text.strip()
        if not rank.isdigit():
            return False

        # Check name format (should be two or more words)
        name = cells[3].text.strip()
        if len(name.split()) < 2:
            return False

        # Check age (should be just a number)
        age = cells[4].text.strip()
        if not age.isdigit():
            return False

        # Check country code (should be 3 uppercase letters)
        country = cells[5].text.strip()
        if not (len(country) == 3 and country.isalpha() and country.isupper()):
            return False

        # Check points (should be a number without text)
        points = cells[6].text.strip()
        if not re.match(r'^[\d,]+$', points):
            return False

        return True

    except Exception:
        return False


def extract_player_data(row):
    try:
        cells = row.find_elements(By.TAG_NAME, "td")

        if not is_properly_formatted_row(cells):
            return None

        # Extract data from properly formatted row
        rank = cells[0].text.strip()
        name = cells[3].text.strip()
        age = cells[4].text.strip()
        country = cells[5].text.strip()
        points = cells[6].text.strip()
        change = ""

        # Try to get ranking change if it exists
        if len(cells) > 7:
            change_text = cells[7].text.strip()
            change_match = re.search(r'[+-]\d+', change_text)
            if change_match:
                change = change_match.group(0)

        return [rank, name, age, country, points, change]

    except Exception as e:
        print(f"Error extracting player data: {e}")
        return None


def save_to_csv(data, folder='atp_rankings_data'):
    if not os.path.exists(folder):
        os.makedirs(folder)

    filename = f"{folder}/atp_rankings_{datetime.now().strftime('%Y-%m-%d')}.csv"

    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Rank", "Player Name", "Age",
                        "Country", "Points", "Change"])
        writer.writerows(data)

    print(f"Data saved to {filename}")
    return filename


def extract_rankings():
    url = 'https://live-tennis.eu/en/atp-live-ranking'
    driver = None

    try:
        print("Initializing Chrome...")
        driver = setup_driver()

        print(f"Navigating to {url}...")
        driver.get(url)
        
        print("Waiting for page to stabilize...")
        time.sleep(5)  # Give the page some time to fully load JavaScript content

        print("Waiting for page load...")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))

        print("Finding ranking rows...")
        # Try different selectors
        try:
            rows = driver.find_elements(By.CSS_SELECTOR, ".ranking-table tbody tr")
        except:
            try:
                rows = driver.find_elements(By.XPATH, "//table[contains(@class, 'ranking')]//tbody/tr")
            except:
                rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

        print(f"Found {len(rows)} potential rows")
        
        # Debug: Print the first row HTML
        if rows:
            print("First row HTML structure:")
            print(rows[0].get_attribute('outerHTML'))

        data = []
        found_first_valid = False
        consecutive_invalid = 0
        max_consecutive_invalid = 10  # Stop if we find too many invalid rows after valid ones

        for row in rows:
            player_data = extract_player_data(row)

            if player_data:
                found_first_valid = True
                consecutive_invalid = 0
                data.append(player_data)
            elif found_first_valid:
                consecutive_invalid += 1
                if consecutive_invalid > max_consecutive_invalid:
                    break

        # Sort by rank to ensure proper ordering
        data.sort(key=lambda x: int(x[0]))

        return data

    except Exception as e:
        print(f"Error during scraping: {e}")
        if driver:
            print("Current URL:", driver.current_url)
            print("Page source (first 500 chars):", driver.page_source[:500])
        return []

    finally:
        if driver:
            driver.quit()


def update_main_rankings_file(new_data_file):
    original_file = "atp_rankings.csv"

    # Read old data if it exists
    if os.path.exists(original_file):
        df_old = pd.read_csv(original_file)
    else:
        df_old = None

    # Read new data
    df_new = pd.read_csv(new_data_file)

    # Compare old and new data
    if df_old is not None and df_old.equals(df_new):
        print("No changes in rankings, skipping update.")
        return original_file  # Exit without updating

    # Backup old data before overwriting
    date_str = datetime.now().strftime("%Y-%m-%d")
    backup_file = f"atp_rankings_{date_str}.csv"

    if os.path.exists(original_file):
        shutil.copy(original_file, backup_file)
        print(f"Backup created as {backup_file}")

    # Overwrite with new data
    df_new.to_csv(original_file, index=False)

    # Record update time
    with open("last_updated.txt", "w") as f:
        f.write(datetime.now().strftime("%Y-%m-%d"))

    print(f"Rankings updated in {original_file}!")
    return original_file


def commit_to_git():
    repo_dir = '/Users/alexbieth/Documents/dev/atp'
    os.chdir(repo_dir)

    try:
        # Check if there are changes
        subprocess.run(["git", "status"], check=True)
        subprocess.run(["git", "diff", "--stat"],
                       check=True)  # Debug differences

        # Add changes
        subprocess.run(["git", "add", "."], check=True)

        # Commit only if there are changes
        commit_message = f"Add ATP rankings data for {datetime.now().strftime('%Y-%m-%d')}"
        commit_result = subprocess.run(
            ["git", "commit", "-m", commit_message], capture_output=True, text=True
        )

        if "nothing to commit" in commit_result.stdout.lower():
            print("No changes detected. Skipping push.")
        else:
            # Push only if commit was successful
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("Changes pushed to GitHub.")

    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {e}")


def analyze_age_distribution(data_file):
    """
    Analyze and visualize the age distribution of ATP players
    """
    # Read the data
    df = pd.read_csv(data_file)
    
    # Convert age to numeric
    df['Age'] = pd.to_numeric(df['Age'])
    
    # Create histogram
    plt.figure(figsize=(12, 6))
    
    # Create histogram with KDE
    counts, bins, patches = plt.hist(df['Age'], bins=range(16, 46), alpha=0.7, 
                                    color='skyblue', edgecolor='black')
    
    # Add mean and median lines
    plt.axvline(df['Age'].mean(), color='red', linestyle='dashed', linewidth=1, 
                label=f'Mean: {df["Age"].mean():.1f}')
    plt.axvline(df['Age'].median(), color='green', linestyle='dashed', linewidth=1, 
                label=f'Median: {df["Age"].median():.1f}')
    
    # Add annotations for number of players in each bin
    for count, x in zip(counts, bins):
        if count > 0:
            plt.text(x + 0.5, count + 1, str(int(count)), ha='center')
    
    # Add title and labels
    plt.title('Age Distribution of ATP Top Players', fontsize=16)
    plt.xlabel('Age', fontsize=12)
    plt.ylabel('Number of Players', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Set axis limits
    plt.xlim(16, 45)
    
    # Save the figure
    plt.tight_layout()
    plt.savefig('atp_age_distribution.png')
    plt.close()
    
    # Return some statistics
    stats = {
        'youngest': df['Age'].min(),
        'oldest': df['Age'].max(),
        'mean_age': df['Age'].mean(),
        'median_age': df['Age'].median(),
        'players_under_21': (df['Age'] < 21).sum(),
        'players_over_30': (df['Age'] > 30).sum(),
        'most_common_age': df['Age'].mode()[0]
    }
    
    return stats


def enhance_atp_analysis(data_file):
    """
    Perform enhanced analysis on ATP rankings data
    """
    # Read the data
    df = pd.read_csv(data_file)
    
    # Clean and convert data types
    df['Points'] = df['Points'].str.replace(',', '').astype(int)
    df['Age'] = pd.to_numeric(df['Age'])
    if 'Change' in df.columns and not df['Change'].empty and df['Change'].notna().any():
        df['Change'] = df['Change'].str.replace('+', '').astype(float)
    
    # 1. Country Analysis
    country_stats = df['Country'].value_counts().reset_index()
    country_stats.columns = ['Country', 'Count']
    country_stats = country_stats.sort_values('Count', ascending=False)
    
    # Visualization: Top 10 countries
    plt.figure(figsize=(12, 6))
    top_countries = country_stats.head(10)
    plt.bar(top_countries['Country'], top_countries['Count'], color='royalblue')
    plt.title('Top 10 Countries by Number of Players in Rankings', fontsize=16)
    plt.xlabel('Country', fontsize=12)
    plt.ylabel('Number of Players', fontsize=12)
    plt.xticks(rotation=45)
    
    for i, v in enumerate(top_countries['Count']):
        plt.text(i, v + 0.5, str(v), ha='center')
    
    plt.tight_layout()
    plt.savefig('atp_top_countries.png')
    plt.close()
    
    # 2. Age vs Ranking Analysis
    plt.figure(figsize=(10, 6))
    plt.scatter(df['Age'], df['Rank'].astype(int), alpha=0.5, color='teal')
    
    # Add trendline
    z = np.polyfit(df['Age'], df['Rank'].astype(int), 1)
    p = np.poly1d(z)
    plt.plot(df['Age'].sort_values(), p(df['Age'].sort_values()), "r--", alpha=0.8)
    
    plt.title('Player Age vs. Ranking', fontsize=16)
    plt.xlabel('Age', fontsize=12)
    plt.ylabel('Ranking', fontsize=12)
    plt.gca().invert_yaxis()  # Higher ranks (lower numbers) at top
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('atp_age_vs_ranking.png')
    plt.close()
    
    # 3. Points Distribution Analysis
    plt.figure(figsize=(12, 6))
    top_df = df.head(50)  # Top 50 players
    plt.bar(top_df['Rank'].astype(str), top_df['Points'], color='green', alpha=0.7)
    plt.title('ATP Points Distribution (Top 50 Players)', fontsize=16)
    plt.xlabel('Rank', fontsize=12)
    plt.ylabel('Points', fontsize=12)
    plt.xticks(rotation=90)
    plt.grid(True, axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig('atp_points_distribution.png')
    plt.close()
    
    # 4. Age Groups Performance
    df['Age_Group'] = pd.cut(df['Age'], bins=[15, 20, 25, 30, 35, 40, 45], 
                            labels=['Under 20', '21-25', '26-30', '31-35', '36-40', 'Over 40'])
    
    age_group_stats = df.groupby('Age_Group').agg({
        'Rank': 'count',
        'Points': 'mean',
        'Age': 'mean'
    }).reset_index()
    
    age_group_stats.columns = ['Age_Group', 'Player_Count', 'Avg_Points', 'Avg_Age']
    age_group_stats['Avg_Points'] = age_group_stats['Avg_Points'].round(0)
    
    # Visualization: Performance by age group
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    ax1.bar(age_group_stats['Age_Group'], age_group_stats['Player_Count'], color='skyblue', alpha=0.7)
    ax1.set_xlabel('Age Group', fontsize=12)
    ax1.set_ylabel('Number of Players', fontsize=12, color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    
    ax2 = ax1.twinx()
    ax2.plot(age_group_stats['Age_Group'], age_group_stats['Avg_Points'], 'ro-', linewidth=2)
    ax2.set_ylabel('Average Points', fontsize=12, color='red')
    ax2.tick_params(axis='y', labelcolor='red')
    
    plt.title('Number of Players and Average Points by Age Group', fontsize=16)
    plt.tight_layout()
    plt.savefig('atp_age_group_analysis.png')
    plt.close()
    
    return {
        'country_stats': country_stats.head(10).to_dict('records'),
        'age_group_stats': age_group_stats.to_dict('records'),
        'top_player': df.iloc[0]['Player Name'],
        'top_player_points': int(df.iloc[0]['Points']),
        'avg_points_top100': int(df.head(100)['Points'].mean()),
        'avg_age_top10': df.head(10)['Age'].mean(),
        'avg_age_top100': df.head(100)['Age'].mean(),
        'points_gap_1_10': int(df.iloc[0]['Points'] - df.iloc[9]['Points']),
        'points_gap_1_100': int(df.iloc[0]['Points'] - df.iloc[99]['Points']) if len(df) >= 100 else None
    }


def run_analysis(rankings_file="atp_rankings.csv"):
    """
    Run all analysis functions on the ATP rankings data
    """
    # Create analysis directory if it doesn't exist
    analysis_dir = "atp_analysis"
    if not os.path.exists(analysis_dir):
        os.makedirs(analysis_dir)
    
    # Run age distribution analysis
    print("Analyzing age distribution...")
    age_stats = analyze_age_distribution(rankings_file)
    
    # Run enhanced analysis
    print("Running enhanced rankings analysis...")
    enhanced_stats = enhance_atp_analysis(rankings_file)
    
    # Combine all stats into a single report
    all_stats = {
        "date": datetime.now().strftime('%Y-%m-%d'),
        "age_stats": age_stats,
        "rankings_stats": enhanced_stats
    }
    
    # Save stats as JSON
    stats_file = f"{analysis_dir}/atp_stats_{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(stats_file, 'w') as f:
        json.dump(all_stats, f, indent=4)
    
    print(f"Analysis completed. Results saved to {stats_file}")
    print(f"Visualizations saved to the current directory.")
    
    # Generate HTML report
    generate_html_report(all_stats, analysis_dir)
    
    return all_stats


def generate_html_report(stats, output_dir):
    """
    Generate an HTML report from the stats data
    """
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>ATP Rankings Analysis - {stats['date']}</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; color: #333; }}
            h1, h2, h3 {{ color: #2c3e50; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .stats-card {{ background: #f9f9f9; border-radius: 5px; padding: 15px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            .stats-row {{ display: flex; flex-wrap: wrap; margin: 0 -10px; }}
            .stats-col {{ flex: 1; padding: 10px; min-width: 200px; }}
            .stat-value {{ font-size: 24px; font-weight: bold; color: #3498db; }}
            .stat-label {{ font-size: 14px; color: #7f8c8d; }}
            .img-container {{ margin: 20px 0; }}
            img {{ max-width: 100%; height: auto; border-radius: 5px; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #3498db; color: white; }}
            tr:hover {{ background-color: #f5f5f5; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>ATP Rankings Analysis Report</h1>
            <p>Analysis date: {stats['date']}</p>
            
            <div class="stats-card">
                <h2>Age Distribution</h2>
                <div class="stats-row">
                    <div class="stats-col">
                        <div class="stat-label">Youngest Player</div>
                        <div class="stat-value">{stats['age_stats']['youngest']} years</div>
                    </div>
                    <div class="stats-col">
                        <div class="stat-label">Oldest Player</div>
                        <div class="stat-value">{stats['age_stats']['oldest']} years</div>
                    </div>
                    <div class="stats-col">
                        <div class="stat-label">Average Age</div>
                        <div class="stat-value">{stats['age_stats']['mean_age']:.1f} years</div>
                    </div>
                    <div class="stats-col">
                        <div class="stat-label">Most Common Age</div>
                        <div class="stat-value">{stats['age_stats']['most_common_age']} years</div>
                    </div>
                </div>
                <div class="img-container">
                    <img src="../atp_age_distribution.png" alt="Age Distribution">
                </div>
            </div>
            
            <div class="stats-card">
                <h2>Top Player Analysis</h2>
                <div class="stats-row">
                    <div class="stats-col">
                        <div class="stat-label">Top Ranked Player</div>
                        <div class="stat-value">{stats['rankings_stats']['top_player']}</div>
                    </div>
                    <div class="stats-col">
                        <div class="stat-label">Top Player Points</div>
                        <div class="stat-value">{stats['rankings_stats']['top_player_points']:,}</div>
                    </div>
                    <div class="stats-col">
                        <div class="stat-label">Points Gap (1-10)</div>
                        <div class="stat-value">{stats['rankings_stats']['points_gap_1_10']:,}</div>
                    </div>
                    <div class="stats-col">
                        <div class="stat-label">Points Gap (1-100)</div>
                        <div class="stat-value">{stats['rankings_stats']['points_gap_1_100']:,}</div>
                    </div>
                </div>
            </div>
            
            <div class="stats-card">
                <h2>Age Group Analysis</h2>
                <table>
                    <tr>
                        <th>Age Group</th>
                        <th>Players</th>
                        <th>Avg Points</th>
                        <th>Avg Age</th>
                    </tr>
                    {"".join([f"<tr><td>{g['Age_Group']}</td><td>{g['Player_Count']}</td><td>{g['Avg_Points']:,.0f}</td><td>{g['Avg_Age']:.1f}</td></tr>" for g in stats['rankings_stats']['age_group_stats']])}
                </table>
                <div class="img-container">
                    <img src="../atp_age_group_analysis.png" alt="Age Group Analysis">
                </div>
            </div>
            
            <div class="stats-card">
                <h2>Country Analysis</h2>
                <div class="img-container">
                    <img src="../atp_top_countries.png" alt="Top Countries">
                </div>
                <table>
                    <tr>
                        <th>Country</th>
                        <th>Number of Players</th>
                    </tr>
                    {"".join([f"<tr><td>{c['Country']}</td><td>{c['Count']}</td></tr>" for c in stats['rankings_stats']['country_stats']])}
                </table>
            </div>
            
            <div class="stats-card">
                <h2>Additional Visualizations</h2>
                <div class="img-container">
                    <img src="../atp_age_vs_ranking.png" alt="Age vs Ranking">
                </div>
                <div class="img-container">
                    <img src="../atp_points_distribution.png" alt="Points Distribution">
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Write HTML report
    with open(f"{output_dir}/atp_report_{stats['date']}.html", 'w') as f:
        f.write(html_content)
    
    print(f"HTML report generated: {output_dir}/atp_report_{stats['date']}.html")


def main():
    print("Starting ATP rankings extraction...")
    max_attempts = 3

    for attempt in range(max_attempts):
        print(f"\nAttempt {attempt + 1} of {max_attempts}")
        data = extract_rankings()

        if data:
            # Save the data to a date-specific file and get the filename
            new_data_file = save_to_csv(data)

            # Update the main rankings file
            update_main_rankings_file(new_data_file)

            print(f"Successfully extracted {len(data)} player rankings.")
            # Print first few entries to verify format
            print("\nFirst few entries:")
            for entry in data[:5]:
                print(entry)

            # Commit changes to Git
            commit_to_git()
            
            # Run analysis on the data
            print("\nStarting data analysis...")
            run_analysis("atp_rankings.csv")
            
            break
        else:
            print(f"No data extracted on attempt {attempt + 1}")
            if attempt < max_attempts - 1:
                wait_time = 10 * (attempt + 1)
                print(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
    else:
        print("Failed to extract data after all attempts.")


if __name__ == "__main__":
    main()