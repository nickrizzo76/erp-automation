from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from heapq import merge
import logging
import chromedriver_binary
import threading
import argparse
import subprocess
import os
import time
import enum

class SalesOrderType(enum.Enum):
    install = "Install Hardware"
    itTransfer = "IT Transfer"
    postInstall = "Post-Install Hardware"
    rma = "RMA"
    rmaExchange = "RMA Exchange"



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
user_input = None
is_test = True
wait = WebDriverWait(driver, 300)
netsuite_homepage_url = 'https://4478811.app.netsuite.com/app/center/card.nl?sc=-29&whence='
test_order_number = ('1100987')
test_order_link = 'https://4478811.app.netsuite.com/app/accounting/transactions/salesord.nl?id=24625748&whence='
test_order_link_2 = 'https://4478811.app.netsuite.com/app/accounting/transactions/salesord.nl?id=21811708&whence='


def main():
    # os.system('Google\\ Chrome --remote-debugging-port=9222 --user-data-dir=remote-profile')
    # Adds debugging port in chrome browser, so that Selenium can open in the existing Chrome session/profile.
    global driver, wait
    chrome_options = Options()
    chrome_options.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
    driver = webdriver.Chrome(options=chrome_options)
    wait.driver = driver
    #prompt_input()
    driver.switch_to.window(driver.window_handles[0])

    items = fulfill_sales_order(test_order_number, SalesOrderType.postInstall)
    #fulfill_sales_order(test_order_number)


def prompt_input():
    global user_input
    sign_in()
    if is_test:
        user_input = test_order_number   
    else:
        user_input = input("Search a NetSuite Sales Order\n")
    search_sales_order(user_input)
    get_line_items(user_input)
    #fulfill_sales_order(user_input)


def sign_in():
    logging.debug('sign_in()')

    # check if already logged into Okta
    driver.get("https://toasttab.okta.com/login/login.htm?fromURI=%2Fapp%2FUserHome#")

    if driver.current_url != 'https://toasttab.okta.com/app/UserHome#':
        if is_test:
            automatic_sign_in()
        else:
            manual_sign_in()


def automatic_sign_in():
    logging.debug('automatic_sign_in')

    time.sleep(2)

    driver.find_element_by_id('okta-signin-username')

    #try:
    #    wait.until(EC.presence_of_element_located((By.ID, "okta-signin-username")))
    #finally:
    #    logging.debug('found okta-signin-username')


    logging.debug('entering credentials')
    driver.find_element_by_id("okta-signin-username").clear() # username
    driver.find_element_by_id("okta-signin-password").clear() # password
    driver.find_element_by_id("okta-signin-username").send_keys("redacted") # add env to fill this in
    driver.find_element_by_id("okta-signin-password").send_keys("redacted") # add env to fill this in
    logging.debug('credentials entered')
    # Submit
    #submitButton = wait.until(EC.presence_of_element_located((By.ID, 'okta-signin-submit')))
    submitButton = driver.find_element_by_id('okta-signin-submit')
    submitButton.click()

    time.sleep(2)
    # Send push notification to Duo Mobile phone app
    print('waiting for iframe')
    #frame = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@title="Duo Security"]')))
    frame = driver.find_element_by_xpath('//*[@title="Duo Security"]')
    driver.switch_to.frame(frame)
    print('switched to duo security iframe')
    print('finding push button')

    time.sleep(2)
    #pushButton = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="auth_methods"]/fieldset/div[1]/button')))
    pushButton = driver.find_element_by_xpath('//*[@id="auth_methods"]/fieldset/div[1]/button')
    pushButton.click()
    print('button clicked')


def manual_sign_in():
    print('manual_sign_in')


def search_sales_order(sales_order_number):
    print('searching sales order')
    driver.get(netsuite_homepage_url)
    search_bar = driver.find_element_by_id('_searchstring')
    search_bar.send_keys(test_order_number) # DEBUG SALES ORDER <--------- CHANGE THIS LATER
    search_bar.send_keys(Keys.ENTER)


# Types of inventory detail
# 1. Non-Serialized, not auto-fulfilled (167006): BIN | AVAILABLE | QUANTITY
# 2. Non-Serialized, not auto-fulfilled (TST606): SERIAL/LOT NUMBER | BIN | EXPIRATION DATE | LOT QTY AVAILABLE ACROSS BINS | UNPICKED BIN QTY | QUANTITY
# 3. Serialized (never fulfilled) ......(BBP409): SERIAL/LOT NUMBER | BIN | QUANTITY
# TODO: automatically fulfill non-serialized line-items/headers
def fulfill_sales_order(sales_order_number, sales_order_type) -> [(str,int)]:
    # fulfill_button = driver.find_element_by_id('process') #KEEP THIS!!! DON'T FULFILL FOR NOW
    #fulfill_button.click()
    print('get line items')
    driver.get('https://4478811.app.netsuite.com/app/accounting/transactions/itemship.nl?id=24715513&e=T&transform=salesord&memdoc=0&whence=') # replace with sales_order as argument
    time.sleep(2)

    items = driver.find_elements_by_xpath("//tr[starts-with(@id,'itemrow')]")

    column_data = [column.find_elements_by_xpath(".//*[starts-with(@class,'uir-list-row-cell listtext')]") for column in items]

    time.sleep(1)
    # chrome doesn't support xpath 2.0
    #inventory_detail_boxes = driver.find_elements_by_xpath("//a[regexp(@id,'inventorydetail_helper_popup_[2-9]{1}')]") <- regex not supported by chrome

    # --> Gather serialized line items
    # you can determine whether a line item is serialized by checking how many columns (headers) it has when you fulfill it
    # serialized have 3: SERIAL/LOT NUMBER, BIN, QUANTITY
    # non-serialized have 5: BIN, EXPIRATION DATE, LOT, QTY AVAILABLE ACROSS BINS, UNPICKED BIN QTY, QUANTITY
    header_line_item_indices = [] # used for displaying the top line of a Package/Assembly SKU to the user, so they know what Package the sub-items comprise
    serialized_line_item_indices = [] # used for displaying all serialized line items that the user must scan in
    inventory_detail_boxes = driver.find_elements_by_xpath("//a[starts-with(@id,'inventorydetail_helper_popup_')]")

    for i, detail in enumerate(inventory_detail_boxes):
        # check for visible detail box.  The top kit/SKU line item MAY not have a visible detail box and will throw an exception when Selenium attempts to click() on it
        if detail.get_attribute('class') == 'smalltextul i_inventorydetaildisabled':
            header_line_item_indices.append(i)
            continue
        # open inventory fulfillment pop up window
        detail.click()
        time.sleep(3) # wait for iframe to load
        # focus webdriver on inventory pop up
        iframe = driver.find_element_by_xpath("//iframe[@id='childdrecord_frame']")
        driver.switch_to.frame(iframe)
        # get number of columns/headers
        headers = driver.find_elements_by_class_name('listheader')
        # add to list if this line item is serialized
        if len(headers) == 3:
            serialized_line_item_indices.append(i)
        # non-serialized line item style #2
        if (headers[0].text == 'SERIAL/LOT NUMBER' and len(headers) == 6):
            # fulfill line item
            #first_input_box = driver.find_element_by_id('inpt_issueinventorynumber1_arrow')
            #first_input_box.click()
            ####driver.find_element_by_xpath(".//*[@class='uir-machine-row uir-machine-row-odd listtextnonedit uir-machine-row-focused']")
            # bin_drop_downs = driver.find_elements_by_class_name('dropdownNotSelected')
            # bin_drop_downs = driver.find_elements_by_xpath(".//*[@class='dropdownNotSelected']")
            # print(len(bin_drop_downs))
            # [print(i.text) for i in bin_drop_downs]
            lots = []
            flag = True
            while flag:
                input_box = driver.find_element_by_xpath(".//*[@class='dropdownInput textbox']")
                input_box.send_keys(Keys.ARROW_DOWN)
                #element = driver.find_element_by_xpath(".//*[@name='inpt_issueinventorynumber']")
                lot = input_box.get_attribute("title")
                if lot not in lots:
                    print(lot)
                    lots.append(lot)
                else:
                    flag = False

            #print(f'lots: {lots}')

        # close inventory pop up
        driver.find_element_by_xpath('//*[@id="secondaryclose"]').click()
        driver.switch_to.default_content

    #indices = (header_line_item_indices + serialized_line_item_indices).sort()
    indices = list(merge(header_line_item_indices, serialized_line_item_indices))
    for item in items:
        i = int(item.get_attribute("id")[-1])
        if i in indices:
            data = column_data[i]
            print(f'({data[1].text.strip()}) {data[2].text.strip()} \n\t Remaining: {data[5].text.strip()}\n\t Committed: {data[6].text.strip()}')


if __name__ == "__main__":
    main()