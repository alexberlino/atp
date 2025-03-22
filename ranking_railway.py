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

print("Script has started...", flush=True)

# Set Chrome and ChromeDriver paths for Railway
chrome_path = "/usr/local/bin/chrome"
chromedriver_path = "/usr/local/bin/chromedriver"

os.environ["CHROME_EXECUTABLE_PATH"] = chrome_path
print(f"Using Chrome executable at: {chrome_path}", flush=True)

print("Starting ATP rankings extraction on Railway...", flush=True)


def setup_driver():
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument('--headless=new')  # Use Headless Mode 2.0
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36")
    # Explicitly set the binary location
    chrome_options.binary_location = chrome_path

    try:
        driver = uc.Chrome(
            options=chrome_options,
            driver_executable_path=chromedriver_path,
            version_main=134  # Explicitly set the Chrome major version
        )
        return driver
    except Exception as e:
        print(f"Error initializing Chrome driver: {e}", flush=True)
        sys.exit(1)


def is_properly_formatted_row(cells):
    if len(cells) < 7:
        return False
    try:
        rank = cells[0].text.strip()
        if not rank.isdigit():
            return False
        name = cells[3].text.strip()
        if len(name.split()) < 2:
            return False
        age = cells[4].text.strip()
        if not age.isdigit():
            return False
        country = cells[5].text.strip()
        if not (len(country) == 3 and country.isalpha() and country.isupper()):
            return False
        points = cells[6].text.strip()
        if not points.replace(",", "").isdigit():
            return False
        return True
    except Exception:
        return False


def extract_player_data(row):
    try:
        cells = row.find_elements(By.TAG_NAME, "td")
        if not is_properly_formatted_row(cells):
            return None
        rank = cells[0].text.strip()
        name = cells[3].text.strip()
        age = cells[4].text.strip()
        country = cells[5].text.strip()
        points = cells[6].text.strip()
        change = ""
        if len(cells) > 7:
            change_text = cells[7].text.strip()
            change_match = re.search(r'[+-]\d+', change_text)
            if change_match:
                change = change_match.group(0)
        return [rank, name, age, country, points, change]
    except Exception as e:
        print(f"Error extracting player data: {e}", flush=True)
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
    print(f"Data saved to {filename}", flush=True)
    return filename


def extract_rankings():
    url = 'https://live-tennis.eu/en/atp-live-ranking'
    driver = None
    try:
        print("Initializing Chrome in Railway...", flush=True)
        driver = setup_driver()
        print(f"Navigating to {url}...", flush=True)
        driver.get(url)
        time.sleep(3)  # Added delay to help with page load/bot detection
        print("Waiting for page load...", flush=True)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
        )
        print("Finding ranking rows...", flush=True)
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        print(f"Found {len(rows)} potential rows", flush=True)
        data = []
        for row in rows:
            player_data = extract_player_data(row)
            if player_data:
                data.append(player_data)
        return data
    except Exception as e:
        print(f"Error during scraping: {e}", flush=True)
        return []
    finally:
        if driver:
            driver.quit()


def update_main_rankings_file(new_data_file):
    original_file = "atp_rankings.csv"
    if os.path.exists(original_file):
        df_old = pd.read_csv(original_file)
    else:
        df_old = None
    df_new = pd.read_csv(new_data_file)
    if df_old is not None and df_old.equals(df_new):
        print("No changes in rankings, skipping update.", flush=True)
        return original_file
    date_str = datetime.now().strftime("%Y-%m-%d")
    backup_file = f"atp_rankings_{date_str}.csv"
    if os.path.exists(original_file):
        shutil.copy(original_file, backup_file)
        print(f"Backup created as {backup_file}", flush=True)
    df_new.to_csv(original_file, index=False)
    with open("last_updated.txt", "w") as f:
        f.write(datetime.now().strftime("%Y-%m-%d"))
    print(f"Rankings updated in {original_file}!", flush=True)
    return original_file


def commit_to_git():
    repo_dir = '/Users/alexbieth/Documents/dev/atp'
    if not os.path.exists(repo_dir):
        print("Skipping Git commit: Directory does not exist on Railway.", flush=True)
        return
    os.chdir(repo_dir)
    try:
        subprocess.run(["git", "status"], check=True)
        subprocess.run(["git", "diff", "--stat"], check=True)
        subprocess.run(["git", "add", "."], check=True)
        commit_message = f"Add ATP rankings data for {datetime.now().strftime('%Y-%m-%d')}"
        commit_result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            capture_output=True,
            text=True
        )
        if "nothing to commit" in commit_result.stdout.lower():
            print("No changes detected. Skipping push.", flush=True)
        else:
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("Changes pushed to GitHub.", flush=True)
    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {e}", flush=True)


def main():
    try:
        print("Starting ATP rankings extraction on Railway...", flush=True)
        data = extract_rankings()
        if data:
            print(
                f"Successfully extracted {len(data)} player rankings.", flush=True)
            new_data_file = save_to_csv(data)
            update_main_rankings_file(new_data_file)
            commit_to_git()
        else:
            print("No data extracted.", flush=True)
    except Exception as e:
        print(f"Unhandled error: {e}", flush=True)
    finally:
        # Keep container alive for debugging to review logs
        print("Exiting script, sleeping for 300 seconds for debugging...", flush=True)
        time.sleep(300)


if __name__ == "__main__":
    main()
