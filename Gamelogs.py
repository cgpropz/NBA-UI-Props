from seleniumbase import Driver
import pandas as pd
import time  # For retries

# Retry decorator (magic: auto-retries functions 3x)
def retry_on_exception(max_attempts=3, backoff=2):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise e  # Final fail → raise
                    print(f"Attempt {attempt + 1} failed: {e}. Retrying in {backoff**attempt}s...")
                    time.sleep(backoff ** attempt)
            return None
        return wrapper
    return decorator

url = 'https://www.nba.com/stats/players/boxscores'

@retry_on_exception(max_attempts=3, backoff=2)  # ← Bulletproof retry
def scrape_gamelogs():
    driver = Driver(uc=True, headless=True, timeout=30)  # 30s timeout = safe
    try:
        driver.get(url)
        driver.sleep(10)  # Initial load buffer (JS heavy)

        # Wait for table with retry baked in
        table_xpath = '/html/body/div[1]/div[2]/div[2]/div[3]/section[2]/div/div[2]/div[3]/table'
        driver.wait_for_element('xpath', table_xpath)

        driver.sleep(6)
        driver.wait_for_element('xpath', '/html/body/div[2]/div[2]/div/div[1]/div/div[2]/div/button').click()
        driver.sleep(1)
        driver.wait_for_element('xpath', '/html/body/div[1]/div[2]/div[2]/div[3]/section[2]/div/div[2]/div[2]/div[1]/div[3]/div/label/div/select').click()
        driver.sleep(1)
        driver.wait_for_element('xpath', '/html/body/div[1]/div[2]/div[2]/div[3]/section[2]/div/div[2]/div[2]/div[1]/div[3]/div/label/div/select/option[1]').click()
        driver.sleep(2)

        # Scroll to trigger lazy-load (NBA tables paginate)
        driver.execute_script("window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });")
        driver.sleep(10)  # Let scroll + load settle

        # Grab table
        table = driver.find_element('xpath', table_xpath)
        df = pd.read_html(table.get_attribute('outerHTML'))[0]
        df.to_csv('Full_Gamelogs25.csv', index=False)
        print("FULL GAMELOGS Data Saved...")
        print(df.head())  # Quick preview
        return df
    finally:
        driver.quit()

# Run it
print("Running full Gamelogs scrape (undetected-chromedriver)...")
try:
    scrape_gamelogs()
except Exception as e:
    print(f"Gamelogs failed → backup needed: {e}")