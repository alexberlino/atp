import shutil
import os
import sys
import csv
import re
import time
import subprocess
from datetime import datetime

import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Set Chrome and ChromeDriver paths for Railway
chrome_path = "/usr/bin/google-chrome-stable"
chromedriver_path = shutil.which(
    "chromedriver") or "/usr/local/bin/chromedriver"  # Ensure the correct path

os.environ["CHROME_EXECUTABLE_PATH"] = chrome_path
print(f"Using Chrome executable at: {chrome_path}")


def setup_driver():
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument('--headless=new')  # Use Headless Mode 2.0
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36")

    try:
        driver = uc.Chrome(
            options=chrome_options,
            driver_executable_path=chromedriver_path
        )
        return driver
    except Exception as e:
        print(f"Error initializing Chrome driver: {e}")
        sys.exit(1)


def extract_rankings():
    url = 'https://live-tennis.eu/en/atp-live-ranking'
    driver = None

    try:
        print("Initializing Chrome in Railway...")
        driver = setup_driver()

        print(f"Navigating to {url}...")
        driver.get(url)
        time.sleep(3)  # Prevent bot detection

        print("Waiting for page load...")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
        )

        print("Finding ranking rows...")
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

        print(f"Found {len(rows)} potential rows")

        data = []
        for row in rows:
            player_data = extract_player_data(row)
            if player_data:
                data.append(player_data)

        return data

    except Exception as e:
        print(f"Error during scraping: {e}")
        return []

    finally:
        if driver:
            driver.quit()


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


def update_main_rankings_file(new_data_file):
    original_file = "atp_rankings.csv"

    if os.path.exists(original_file):
        df_old = pd.read_csv(original_file)
    else:
        df_old = None

    df_new = pd.read_csv(new_data_file)

    if df_old is not None and df_old.equals(df_new):
        print("No changes in rankings, skipping update.")
        return original_file

    date_str = datetime.now().strftime("%Y-%m-%d")
    backup_file = f"atp_rankings_{date_str}.csv"

    if os.path.exists(original_file):
        shutil.copy(original_file, backup_file)
        print(f"Backup created as {backup_file}")

    df_new.to_csv(original_file, index=False)

    with open("last_updated.txt", "w") as f:
        f.write(datetime.now().strftime("%Y-%m-%d"))

    print(f"Rankings updated in {original_file}!")
    return original_file


def commit_to_git():
    repo_dir = '/Users/alexbieth/Documents/dev/atp'

    if not os.path.exists(repo_dir):
        print("Skipping Git commit: Directory does not exist on Railway.")
        return

    os.chdir(repo_dir)

    try:
        subprocess.run(["git", "status"], check=True)
        subprocess.run(["git", "diff", "--stat"], check=True)

        subprocess.run(["git", "add", "."], check=True)

        commit_message = f"Add ATP rankings data for {datetime.now().strftime('%Y-%m-%d')}"
        commit_result = subprocess.run(
            ["git", "commit", "-m", commit_message], capture_output=True, text=True
        )

        if "nothing to commit" in commit_result.stdout.lower():
            print("No changes detected. Skipping push.")
        else:
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("Changes pushed to GitHub.")

    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {e}")


def main():
    print("Starting ATP rankings extraction on Railway...")
    data = extract_rankings()

    if data:
        print(f"Successfully extracted {len(data)} player rankings.")
        new_data_file = save_to_csv(data)
        update_main_rankings_file(new_data_file)
        commit_to_git()
    else:
        print("No data extracted.")


if __name__ == "__main__":
    main()
