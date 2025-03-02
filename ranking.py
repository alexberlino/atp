import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import csv
from datetime import datetime
import re
import subprocess


def fetch_rankings():
    """Fetch ATP rankings using requests and BeautifulSoup instead of Selenium"""
    print("Fetching ATP rankings...")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    url = 'https://live-tennis.eu/en/atp-live-ranking'

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()  # Raise an exception for bad status codes

        print(
            f"Successfully fetched page with status code: {response.status_code}")
        return response.text
    except Exception as e:
        print(f"Error fetching rankings: {e}")
        return None


def parse_rankings(html_content):
    """Parse the HTML content to extract ranking data"""
    if not html_content:
        return []

    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        table = soup.find('table', {'class': 'restable'})

        if not table:
            print("Could not find ranking table")
            return []

        rows = table.find_all('tr')
        print(f"Found {len(rows)} rows in the table")

        data = []
        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 7:
                continue

            try:
                # Extract rank (first column)
                rank = cells[0].text.strip()
                if not rank.isdigit():
                    continue

                # Extract name (fourth column)
                name = cells[3].text.strip()
                if len(name.split()) < 2:
                    continue

                # Extract age
                age = cells[4].text.strip()
                if not age.isdigit():
                    continue

                # Extract country
                country = cells[5].text.strip()
                if not (len(country) == 3 and country.isalpha() and country.isupper()):
                    continue

                # Extract points
                points = cells[6].text.strip()
                if not points.replace(",", "").replace(".", "").isdigit():
                    continue

                # Extract change if available
                change = ""
                if len(cells) > 7:
                    change_text = cells[7].text.strip()
                    change_match = re.search(r'[+-]\d+', change_text)
                    if change_match:
                        change = change_match.group(0)

                data.append([rank, name, age, country, points, change])
            except Exception as e:
                print(f"Error parsing row: {e}")
                continue

        # Sort by rank to ensure proper ordering
        if data:
            data.sort(key=lambda x: int(x[0]))

        return data

    except Exception as e:
        print(f"Error parsing HTML: {e}")
        return []


def save_to_csv(data, filename='atp_rankings.csv'):
    """Save ranking data directly to the main CSV file"""
    if not data:
        print("No data to save")
        return None

    try:
        # Create a backup of the existing file if it exists
        if os.path.exists(filename):
            backup_name = f"atp_rankings_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
            os.rename(filename, backup_name)
            print(f"Created backup: {backup_name}")

        # Save the new data
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Rank", "Player Name", "Age",
                            "Country", "Points", "Change"])
            writer.writerows(data)

        print(f"Data saved to {filename} with {len(data)} entries")

        # Also save a date-stamped version for record-keeping
        dated_filename = f"atp_rankings_data/atp_rankings_{datetime.now().strftime('%Y-%m-%d')}.csv"
        os.makedirs(os.path.dirname(dated_filename), exist_ok=True)

        with open(dated_filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Rank", "Player Name", "Age",
                            "Country", "Points", "Change"])
            writer.writerows(data)

        print(f"Data also saved to {dated_filename}")

        # Update the last updated timestamp
        with open("last_updated.txt", "w") as f:
            f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        return filename

    except Exception as e:
        print(f"Error saving data: {e}")
        return None


def commit_and_push():
    """Commit and push changes to GitHub"""
    try:
        # Check current status
        status_output = subprocess.check_output(
            ["git", "status", "--porcelain"], text=True)

        if not status_output.strip():
            print("No changes detected by git status")

            # Force an update to last_updated.txt to ensure we have something to commit
            with open("last_updated.txt", "w") as f:
                f.write(
                    f"Force update at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            print("Created forced update to last_updated.txt")

        # Stage all changes
        subprocess.run(["git", "add", "-A"], check=True)
        print("Git add completed")

        # Commit with timestamp
        commit_message = f"ATP rankings update {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        print(f"Committed with message: {commit_message}")

        # Push to remote
        subprocess.run(["git", "push"], check=True)
        print("Successfully pushed to repository")

        return True
    except Exception as e:
        print(f"Error in git operations: {e}")
        return False


def main():
    print(f"Starting ATP rankings update at {datetime.now()}")

    # Make sure the output directory exists
    os.makedirs("atp_rankings_data", exist_ok=True)

    # Fetch and parse rankings
    html_content = fetch_rankings()
    if not html_content:
        print("Failed to fetch rankings")
        return False

    ranking_data = parse_rankings(html_content)
    if not ranking_data:
        print("Failed to parse rankings")
        return False

    print(f"Successfully extracted {len(ranking_data)} player rankings")

    # Print sample data for verification
    print("\nSample ranking data:")
    for entry in ranking_data[:5]:
        print(entry)

    # Save the data
    saved_file = save_to_csv(ranking_data)
    if not saved_file:
        print("Failed to save rankings")
        return False

    # Commit and push changes
    if commit_and_push():
        print("Rankings successfully updated and pushed to repository")
        return True
    else:
        print("Failed to commit and push changes")
        return False


if __name__ == "__main__":
    success = main()
    print(f"Script completed with success={success}")

    # Exit with appropriate status code
    exit(0 if success else 1)
