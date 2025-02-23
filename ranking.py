import shutil
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import os
import csv
from datetime import datetime
import time
import re
import pandas as pd
import subprocess


def setup_driver():
    options = uc.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    return uc.Chrome(options=options)


def is_properly_formatted_row(cells):
    """ Check if the row matches the expected format of the ranking data """
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
    """ Extracts player data from a row if properly formatted """
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
        print(f"Error extracting player data: {e}")
        return None


def save_to_csv(data, folder='atp_rankings_data'):
    """ Save data to CSV """
    if not os.path.exists(folder):
        os.makedirs(folder)

    filename = f"{folder}/atp_rankings_{datetime.now().strftime('%Y-%m-%d')}.csv"

    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Rank", "Player Name", "Age",
                        "Country", "Points", "Change"])
        writer.writerows(data)

    print(f"Data saved to {filename}")


def extract_rankings():
    """ Extract ATP rankings data from the website """
    url = 'https://live-tennis.eu/en/atp-live-ranking'
    driver = None

    try:
        driver = setup_driver()
        driver.get(url)
        time.sleep(15)

        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        data = []
        found_first_valid = False
        consecutive_invalid = 0
        max_consecutive_invalid = 10

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

        data.sort(key=lambda x: int(x[0]))
        return data

    except Exception as e:
        print(f"Error during scraping: {e}")
        return []

    finally:
        if driver:
            driver.quit()


def main():
    print("Starting ATP rankings extraction...")
    max_attempts = 3

    for attempt in range(max_attempts):
        print(f"\nAttempt {attempt + 1} of {max_attempts}")
        data = extract_rankings()

        if data:
            save_to_csv(data)
            print(f"Successfully extracted {len(data)} player rankings.")
            break
        else:
            print(f"No data extracted on attempt {attempt + 1}")
            if attempt < max_attempts - 1:
                wait_time = 10 * (attempt + 1)
                time.sleep(wait_time)
    else:
        print("Failed to extract data after all attempts.")


if __name__ == "__main__":
    main()

# Backup and Git commit
original_file = "atp_rankings.csv"
date_str = datetime.now().strftime("%Y-%m-%d")
backup_file = f"atp_rankings_{date_str}.csv"

# Copy the current file to the backup
shutil.copy(original_file, backup_file)

# Update original file with new data
df_new = pd.read_csv(f"atp_rankings_data/atp_rankings_{date_str}.csv")
df_new.to_csv(original_file, index=False)  # Overwrite original file

# Stage changes, commit, and push
repo_dir = '/Users/alexbieth/Documents/dev/atp'
os.chdir(repo_dir)

subprocess.run(['git', 'add', '.'])
commit_message = f"Add ATP rankings data for {date_str}"
subprocess.run(['git', 'commit', '-m', commit_message])
subprocess.run(['git', 'push', 'origin', 'main'])
