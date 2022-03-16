from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from heapq import merge
import logging
import datetime
import chromedriver_binary
import threading
import argparse
import subprocess
import os
import time
from enum import Enum


unifi_0_end_date = datetime.datetime(2018, 6, 17)
unifi_1_end_date = datetime.datetime(2019, 3, 3)
unifi_2_end_date = datetime.datetime(2019, 8, 1)
unifi_3_end_date = datetime.datetime(2019, 12, 3)
unifi_4_end_date = datetime.datetime(2020, 2, 13)
unifi_5_end_date = datetime.datetime(2020, 6, 24)
unifi_6_end_date = datetime.datetime(2020, 9, 30)
unifi_7_end_date = datetime.datetime(2021, 2, 3)
unifi_8_end_date = datetime.datetime(2021, 5, 3)
unifi_9_end_date = datetime.datetime.today()
# yyyy/mm/dd
unifi_site_end_dates = [
  # these dates represent the end date range of that site. Start from unifi 0 and see if the AP has a warranty date of less than or equal to that end date
  unifi_0_end_date, unifi_1_end_date, unifi_2_end_date, unifi_3_end_date, unifi_4_end_date, unifi_5_end_date, unifi_6_end_date, unifi_7_end_date, unifi_8_end_date, unifi_9_end_date,
]

# export PATH="/Applications/Google Chrome.app/Contents/MacOS:$PATH"

# 210119C540757: {'Warehouse_U': '1'}
# DVT: {'Warehouse_U': '2'}
# MP1: {'Warehouse_S': '15', 'Warehouse_U': '1'}
# mp1: {'Warehouse_S': '1'}
# MP2: {'Warehouse_R': '1', 'Warehouse_S': '17', 'Warehouse_U': '167'}
# MP3: {'Warehouse': '191', 'Warehouse_S': '36', 'Warehouse_U': '28'}
# mp3: {'Warehouse_S': '3', 'Warehouse_U': '1'}
# MPT2: {'Warehouse_S': '1'}
# PVT: {'Warehouse_S': '32', 'Warehouse_U': '25'}
# pvt-2: {'Warehouse_S': '3'}
# PVT2: {'Warehouse_S': '1'}
# R: {'Warehouse_S': '8', 'Warehouse_U': '8'}
# S: {'Warehouse_S': '34'}

class SalesOrderType(Enum):
   install = "Install Hardware"
   itTransfer = "IT Transfer"
   postInstall = "Post-Install Hardware"
   rma = "RMA"
   rmaExchange = "RMA Exchange"

class OrderType(Enum):
  POSTINSTALL = 0
  RMA = 1


logging.basicConfig(
   #level=logging.DEBUG,
   #format="{asctime} {levelname:<8} {message}",
   #style='{',
   #filename='%slog' % __file__[:-2],
   #filemode='w' #write
)

welcome = 'TOAST CONFIGURATION CENTER TOOLS\n' \
         '==============================================================================\n' \
         'Welcome to NetSuite Auto-fulfillment.\n' \
         'Enter a NetSuite Sales Order number to start.\n' \
         '=============================================================================='

# TODO: 1. change the args to reflect multiple use cases
#       2. add 'is_test' flag to CLI args
#       3. Add verbose flag
#       4. Add test flag
driver = None
actions = None
user_input = None
is_test = True
wait = None


def main():
   # os.system('Google\\ Chrome --remote-debugging-port=9222 --user-data-dir=remote-profile')
   # Adds debugging port in chrome browser, so that Selenium can open in the existing Chrome session/profile.
   global driver, wait, actions
   chrome_options = Options()
   chrome_options.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
   driver = webdriver.Chrome(options=chrome_options)
   wait = WebDriverWait(driver, 5)

   #prompt_input()
   driver.switch_to.window(driver.window_handles[0])
   find_ubiquiti_site()


def find_ubiquiti_site():
  driver.get('https://toast.my.salesforce.com/02i?rlid=RelatedAssetList&id=0013c00001okm5V')
  table_data = driver.find_elements_by_class_name('dataCell')
  row_count = len(table_data) / 10
  print(f'rows: {row_count}')
  i = 0
  j = 1 # name column
  k = 2 # serial number column
  l = 8 # warranty date column
  row_offset = 10
  while i < row_count:
    if 'Access Point' in table_data[j].text:
      print(f'{table_data[j].text} :: {table_data[k].text} :: {table_data[l].text}')
      if table_data[l].text.strip() == '':
        table_data[k].click() # this needs to be tested!
      else:
        raw_warranty_date = table_data[l].text.split('-')
        year = int(raw_warranty_date[0])
        month = int(raw_warranty_date[1])
        day = int(raw_warranty_date[2])
        warranty_date = datetime.datetime(year, month, day)
        print(warranty_date)

        # compare dates
        for i, date in enumerate(unifi_site_end_dates):
          if warranty_date <= date:
            print(f'you\'re looking for UniFi {i}')
            return
          else:
            continue
        return
        # STUB: convert warranty date to datetime
        # compare to unifi site end dates
    else:
      j += row_offset
      k += row_offset
      l += row_offset
      i += 1



  # driver.get('https://toast.my.salesforce.com/home/home.jsp')
  # #searchBox = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, 'searchBoxClearContainer')))
  # searchBox = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'searchBoxClearContainer')))
  # inputBox = searchBox.find_element_by_id('phSearchInput')
  # # salesOrder = '1175738' # RMA
  # salesOrder = '01012767' # Post-Install
  # inputBox.send_keys(salesOrder)
  # inputBox.send_keys(Keys.ENTER)

  # order_type = OrderType.RMA
  # # click Order link
  # try:
  #   #RMA link
  #   link = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="RMA_Request__c_body"]/table/tbody/tr[2]/th/a')))
  #   order_type = 1
  # except:
  #   try:
  #     #post-install link
  #     link = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="Order_body"]/table/tbody/tr[2]/th/a')))
  #     order_type = OrderType.POSTINSTALL
  #   except Exception as err:
  #     print(err)
  # link.click()

  # # click Account link
  # if order_type == OrderType.POSTINSTALL:
  #   try:
  #     wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[2]/table/tbody/tr/td[2]/div[4]/div[2]/div[2]/table/tbody/tr[4]/td[2]/a'))).click()
  #   except Exception as err:
  #     print(err)
  # elif order_type == OrderType.RMA:
  #   try:
  #     wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[2]/table/tbody/tr/td[2]/div[4]/div[2]/div[4]/table/tbody/tr[1]/td[2]/div/a'))).click()
  #   except Exception as err:
  #     print(err)

  # # click Assets link
  # try:
  #   wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[2]/table/tbody/tr/td[2]/div[19]/div[1]/div/div[2]/div/a[2]'))).click()
  # except Exception as err:
  #   print(err)

  # # ONLY DO THIS IF YOU DIDN'T FIND ACCESS POINTS ON THE FIRST PASS -> THE EARLIEST ARE AT THE TOP
  # # find fewerMore class
  # try:
  #   element = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'fewerMore')))
  #   more_assets_exist = True
  #   # keep clicking on 'more' assets until they're all shown
  #   while more_assets_exist:
  #     try:
  #       element.find_element_by_xpath('//*[@id="bodyCell"]/div[4]/div/div[2]/div/a[2]').click()
  #     except Exception as err:
  #       more_assets_exist = False
  #       print('assets are fully expanded')
  # except Exception as err:
  #   print(err)

  # find the first web element with text that contains 'Access Point' then click on it
  ###driver.find_element_by_partial_link_text('Access Point').click()

  # loop through assets to find access points
  ## table_data = driver.find_elements_by_class_name('dataCell')
  ## print(table_data[0].text)
  # for i in table_data:
  #   print(i.text)



if __name__ == "__main__":
   main()
