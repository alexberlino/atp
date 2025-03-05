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
        # Give the page some time to fully load JavaScript content
        time.sleep(5)

        print("Waiting for page load...")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))

        print("Finding ranking rows...")
        # Try different selectors
        try:
            rows = driver.find_elements(
                By.CSS_SELECTOR, ".ranking-table tbody tr")
        except:
            try:
                rows = driver.find_elements(
                    By.XPATH, "//table[contains(@class, 'ranking')]//tbody/tr")
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
