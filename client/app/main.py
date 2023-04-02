import os
import string
import time
import random
import logging
import concurrent.futures

from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import NoSuchElementException

CHAT_MIN_WAIT_TIME = 0.01
CHAT_MAX_WAIT_TIME = 5

def get_chrome_driver():
    chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument("headless")
    chrome_options.add_argument("enable-quic")
    chrome_options.add_argument("user-data-dir=/user-data")
    driver = webdriver.Remote(
        command_executor=os.environ["CHROME_DRIVER_ADDR"],
        options=chrome_options
    )
    return driver

def get_chrome_uncaptured_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("enable-quic")
    chrome_options.add_argument("user-data-dir=/user-data")
    driver = webdriver.Remote(
        command_executor=os.environ["CHROME_UNCAPTURED_DRIVER_ADDR"],
        options=chrome_options
    )
    return driver

def test_get_quic_cloudflare(driver, dir):
    Path(dir).mkdir(parents=True, exist_ok=True)

    driver.get("https://cloudflare-quic.com/")

    title = driver.title
    logging.info("title: {}".format(title))

    driver.implicitly_wait(0.5)

    for i in range(0, 4):
        driver.save_screenshot("{}/{}-loaded.png".format(dir, i))
        indicator = "not found"
        indicator_strict = "not found"
        try:
            indicator = driver.find_element(By.CSS_SELECTOR,"p strong").text
            indicator_strict = driver.find_element(By.CSS_SELECTOR,"div[class='grid__item grid__item--two-fifths--40pct-tablet grid__item--no-bottom-margin'] p strong").text
        except NoSuchElementException:
            pass
        logging.info("indicator: {} ({})".format(indicator, indicator_strict))
        driver.refresh()

    logging.info("cloudflare quic test done!")
    driver.save_screenshot("{}/finished.png".format(dir))

def test_google_signin(driver, dir):
    Path(dir).mkdir(parents=True, exist_ok=True)

    driver.get("https://accounts.google.com/")

    title = driver.title
    logging.info("title: {}".format(title))
    driver.save_screenshot("{}/0-loaded.png".format(dir))

    if os.environ["CHROME_SETUP"] == "true":
        driver.implicitly_wait(10000) # give user enough time to sign in
    else:
        driver.implicitly_wait(2)

    try:
        indicator = driver.find_element(By.XPATH, "//h1[ contains (text(), 'Welcome' ) ]")
        logging.info("Signed in: {}".format(indicator.text))
    except NoSuchElementException as e:
        logging.warning("element not found".format(e))
        logging.exception(e)
        driver.save_screenshot("{}/x-element_not_found.png".format(dir))
        logging.info(f"screenshot saved: {dir}/x-element_not_found.png")
        return False

    logging.info("google signin done!")
    driver.save_screenshot("{}/finished.png".format(dir))

    return True

def test_google_hangouts_chat(driver1, driver2, dir):
    Path(dir).mkdir(parents=True, exist_ok=True)

    def setup_google_hangouts_chat(driver, dir, target_email):
        Path(dir).mkdir(parents=True, exist_ok=True)
        driver.get("https://hangouts.google.com/")

        driver.implicitly_wait(2)
        title = driver.title
        logging.info("title: {}".format(title))
        try:
            driver.find_element(By.XPATH, "//span[contains(text(),'Chat') and @aria-level='2']")
            try:
                driver.implicitly_wait(2)
                get_started_button = driver.find_element(By.CSS_SELECTOR, "button[name=initial_dialog_get_started]")
                driver.save_screenshot("{}/0-get_started.png".format(dir))
                get_started_button.click()
                close_button = driver.find_element(By.CSS_SELECTOR, "[role=alertdialog] > [aria-label=Close]")
                close_button.click()
            except NoSuchElementException as e:
                logging.debug("element not found: {}".format(e))
            driver.implicitly_wait(2)            
                
            plus_button = driver.find_element(By.XPATH, "//div[@aria-label='Start a chat']")
            driver.save_screenshot("{}/0-loaded.png".format(dir))
            plus_button.click()
            addr_frame = driver.find_element(By.ID, "talk_flyout")
            driver.switch_to.frame(addr_frame)
            addr_input = driver.find_element(By.CSS_SELECTOR, "input[role=combobox]")
            addr_input.send_keys(target_email) 
            addr_input.send_keys(Keys.ENTER)
            driver.save_screenshot("{}/1-entered_addr.png".format(dir))
            start_chat_button = driver.find_element(By.CSS_SELECTOR, "[role=button]")
            start_chat_button.click()
            # addr_input.send_keys("masque.traffic.test@gmail.com")
            driver.switch_to.default_content()
        except NoSuchElementException as e:
            logging.warning("element not found")
            logging.exception(e)
            driver.save_screenshot("{}/x-element_not_found.png".format(dir))
            logging.info(f"screenshot saved: {dir}/x-element_not_found.png")
    
    def send_chat_messages(driver, chat_input, dir, num_msgs=5, min_length=1, max_length=100):
        Path(dir).mkdir(parents=True, exist_ok=True)
        try:
            chat_frame = driver.find_element(By.CSS_SELECTOR, "*:not([style*='display: none']) > [aria-label='Chat content']")
            driver.switch_to.frame(chat_frame)
            for i in range(0, num_msgs):
                chat_input = driver.find_element(By.CSS_SELECTOR, "[role=textbox]")
                random_string = ''.join(random.choice(string.ascii_letters + string.whitespace) for _ in range(random.randint(min_length, max_length)))
                chat_input.send_keys(f"Hello! This is test message {i}: {random_string}")
                driver.save_screenshot(f"{dir}/2-entered_message_{i}.png")
                chat_input.send_keys(Keys.ENTER)
                time.sleep(random.uniform(CHAT_MIN_WAIT_TIME, CHAT_MAX_WAIT_TIME))
            driver.save_screenshot(f"{dir}/3-sent_messages.png")
        except NoSuchElementException as e:
            logging.warning("element not found")
            logging.exception(e)
            driver.save_screenshot("{}/x-element_not_found.png".format(dir))
            logging.info(f"screenshot saved: {dir}/x-element_not_found.png")

    email_1 = "masque.traffic.test.0@gmail.com" # TODO: remove hardcoded email
    email_2 = "masque.traffic.test@gmail.com"   # TODO: remove hardcoded email

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_1 = executor.submit(setup_google_hangouts_chat, driver1, f"{dir}/setup-1", email_2)
        future_2 = executor.submit(setup_google_hangouts_chat, driver2, f"{dir}/setup-2", email_1)
        chat_input_1 = future_1.result()
        chat_input_2 = future_2.result()
        chat_future_1 = executor.submit(send_chat_messages, driver1, chat_input_1, f"{dir}/chat-1")
        chat_future_2 = executor.submit(send_chat_messages, driver2, chat_input_2, f"{dir}/chat-2")
        chat_future_1.result()
        chat_future_2.result()
    
    logging.info("google hangouts chat done!")

def is_docker():
    path = '/proc/self/cgroup'
    return (
        os.path.exists('/.dockerenv') or
        os.path.isfile(path) and any('docker' in line for line in open(path))
    )

logging.basicConfig(format='%(asctime)s-%(process)d-%(levelname)s:  %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)
logging.info(f"In docker: {is_docker()}")

driver = get_chrome_driver()
uncaptured_driver = get_chrome_uncaptured_driver()
try:
    test_get_quic_cloudflare(driver, "{}/quic-cloudflare/chrome".format(os.environ["CAPTURES_DIR"]))
    signed_in = test_google_signin(driver, "{}/google_signin".format(os.environ["CAPTURES_DIR"]))
    uncaptured_signed_in = test_google_signin(uncaptured_driver, "{}/uncaptured/google_signin".format(os.environ["CAPTURES_DIR"]))
    if not signed_in or not uncaptured_signed_in:
        print("Google is not signed in.")
        print("Set environment variable CHROME_SETUP=true and attach to noVNC at port 7900 or 7901 to set up Google account. Use defualt password \"secret\".")
        driver.quit()
        uncaptured_driver.quit()
        exit(1)
    
    test_google_hangouts_chat(driver, uncaptured_driver, "{}/hangouts".format(os.environ["CAPTURES_DIR"]))
    
    # time.sleep(300) # for development
finally:
    driver.quit()
    uncaptured_driver.quit()