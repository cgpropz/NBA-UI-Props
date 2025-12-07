from seleniumbase import Driver
import pandas as pd
import time

url = 'https://www.nba.com/stats/players/boxscores'

# PRO TIP: Use undetectable Chrome + extra stealth flags
driver = Driver(
    uc=True,
    headless=True,
    undetectable=True,           # crucial in 2025
    incognito=True,
    disable_csp=True,
    disable_ws=True,
    enable_ws=False,
    no_sandbox=True,
    disable_gpu=True,
    user_data_dir=None,
)

try:
    print("Opening NBA stats page...")
    driver.get(url)
    
    # Wait for ANY table to appear (not hard-coded path)
    print("Waiting for player stats table to load...")
    driver.wait_for_element("div.table-container table", timeout=60)  # much more reliable
    
    # Click "All" seasons dropdown properly
    print("Selecting 'All' seasons...")
    driver.click("div.ReactTable div.rt-th.rt-resizable-header.-cursor-pointer", by="css selector", timeout=20)
    time.sleep(1)
    
    # Select "All" from the season dropdown
    driver.select_option_by_text("select", "All")  # simple & works
    time.sleep(8)  # give it time to load full data
    
    # Scroll slowly to trigger lazy loading
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(5)
    
    # Grab the actual table (dynamic class, but always one)
    table = driver.find_element("table")
    
    # Convert to pandas
    df = pd.read_html(table.get_attribute('outerHTML'))[0]
    
    # Save
    df.to_csv('Full_Gamelogs25.csv', index=False)
    print("FULL GAMELOGS Data Saved Successfully!")
    print(f"Shape: {df.shape}")
    print(df.head())

except Exception as e:
    driver.save_screenshot("error_debug.png")  # super helpful in CI logs
    raise e

finally:
    driver.quit()
