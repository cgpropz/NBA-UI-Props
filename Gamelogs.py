from seleniumbase import Driver
import pandas as pd

url = 'https://www.nba.com/stats/players/boxscores'

driver = Driver(uc=True, headless=True)
driver.get(url)
driver.sleep(5)

driver.wait_for_element('xpath', '/html/body/div[1]/div[2]/div[2]/div[3]/section[2]/div/div[2]/div[3]/table')
driver.sleep(6)

driver.wait_for_element('xpath', '/html/body/div[2]/div[2]/div/div[1]/div/div[2]/div/button').click()
driver.sleep(1)

driver.wait_for_element('xpath', '/html/body/div[1]/div[2]/div[2]/div[3]/section[2]/div/div[2]/div[2]/div[1]/div[3]/div/label/div/select').click()
driver.sleep(1)

driver.wait_for_element('xpath', '/html/body/div[1]/div[2]/div[2]/div[3]/section[2]/div/div[2]/div[2]/div[1]/div[3]/div/label/div/select/option[1]').click()
driver.sleep(2)

driver.execute_script("window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });")
driver.sleep(5)

table = driver.find_element('xpath','/html/body/div[1]/div[2]/div[2]/div[3]/section[2]/div/div[2]/div[3]/table')

df = pd.read_html(table.get_attribute('outerHTML'))[0]
df.to_csv('/Users/kahlilhodge/NBA-UI-Props/Full_Gamelogs25.csv', index=False)
print("FULL GAMELOGS Data Saved...")   
print(df)