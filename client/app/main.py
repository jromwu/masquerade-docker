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
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException

CHAT_MIN_WAIT_TIME = 0.01
CHAT_MAX_WAIT_TIME = 5

EMAIL_1 = "masque.traffic.test.0@gmail.com" # TODO: remove hardcoded email
EMAIL_2 = "masque.traffic.test@gmail.com"   # TODO: remove hardcoded email

google_chat_frame_selector = "*:not([style*='display: none']) > [aria-label='Chat content']"

def get_chrome_driver(remote_addr):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("enable-quic")
    chrome_options.add_argument("user-data-dir=/user-data")
    chrome_options.add_argument("use-fake-device-for-media-stream")
    chrome_options.add_argument("use-fake-ui-for-media-stream")
    driver = webdriver.Remote(
        command_executor=remote_addr,
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
        driver.switch_to.default_content()
    except NoSuchElementException as e:
        logging.warning("element not found")
        logging.exception(e)
        driver.save_screenshot("{}/x-element_not_found.png".format(dir))
        logging.info(f"screenshot saved: {dir}/x-element_not_found.png")

def test_google_hangouts_chat(driver1, driver2, dir):
    Path(dir).mkdir(parents=True, exist_ok=True)

    def send_chat_messages(driver, dir, num_msgs=5, min_length=1, max_length=100):
        Path(dir).mkdir(parents=True, exist_ok=True)
        try:
            chat_frame = driver.find_element(By.CSS_SELECTOR, google_chat_frame_selector)
            driver.switch_to.frame(chat_frame)
            for i in range(0, num_msgs):
                logging.info(f"sending message {i}")
                chat_input = driver.find_element(By.CSS_SELECTOR, "[role=textbox]")
                random_string = ''.join(random.choice(string.digits + string.ascii_letters + string.punctuation + " ") for _ in range(random.randint(min_length, max_length)))
                chat_input.send_keys(f"Hello! This is test message {i} {random_string}")
                driver.save_screenshot(f"{dir}/2-entered_message_{i}.png")
                chat_input.send_keys(Keys.ENTER)
                time.sleep(random.uniform(CHAT_MIN_WAIT_TIME, CHAT_MAX_WAIT_TIME))
            driver.save_screenshot(f"{dir}/3-sent_messages.png")
            driver.switch_to.default_content()
        except NoSuchElementException as e:
            logging.warning("element not found")
            logging.exception(e)
            driver.save_screenshot("{}/x-element_not_found.png".format(dir))
            logging.info(f"screenshot saved: {dir}/x-element_not_found.png")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        setup_future_1 = executor.submit(setup_google_hangouts_chat, driver1, f"{dir}/setup-1", EMAIL_2)
        setup_future_2 = executor.submit(setup_google_hangouts_chat, driver2, f"{dir}/setup-2", EMAIL_1)
        setup_future_1.result()
        setup_future_2.result()
        chat_future_1 = executor.submit(send_chat_messages, driver1, f"{dir}/chat-1")
        chat_future_2 = executor.submit(send_chat_messages, driver2, f"{dir}/chat-2")
        chat_future_1.result()
        chat_future_2.result()
    
    logging.info("google hangouts chat done!")

def test_google_hangouts_call(driver1, driver2, dir, call_length=30):
    Path(dir).mkdir(parents=True, exist_ok=True)

    def call(driver, dir):
        Path(dir).mkdir(parents=True, exist_ok=True)
        try:
            chat_frame = driver.find_element(By.CSS_SELECTOR, google_chat_frame_selector)
            driver.switch_to.frame(chat_frame)
            # for some reason, the call button is not present for some Google account
            start_call_button = driver.find_element(By.CSS_SELECTOR, "div[role='button'][aria-label*='Start a video call']:not([aria-disabled='true'])")
            start_call_button.click()
            
            driver.save_screenshot(f"{dir}/2-initiated_call.png")
            driver.switch_to.default_content()
        except NoSuchElementException as e:
            logging.warning("element not found")
            logging.exception(e)
            driver.save_screenshot("{}/x-element_not_found.png".format(dir))
            logging.info(f"screenshot saved: {dir}/x-element_not_found.png")

    def accept_call(driver, dir):
        Path(dir).mkdir(parents=True, exist_ok=True)
        try:
            call_frame = driver.find_element(By.NAME, "pip_frame")
            driver.switch_to.frame(call_frame)

            driver.implicitly_wait(0)
            join_button = WebDriverWait(driver, timeout=30).until(lambda driver: driver.find_element(By.CSS_SELECTOR, "button[aria-label='Answer call']"))
            join_button.click()
            
            driver.save_screenshot(f"{dir}/2-accepted_call.png")
            driver.implicitly_wait(2)
            driver.switch_to.default_content()
        except NoSuchElementException as e:
            logging.warning("element not found")
            logging.exception(e)
            driver.save_screenshot("{}/x-element_not_found.png".format(dir))
            logging.info(f"screenshot saved: {dir}/x-element_not_found.png")
    
    def stop_call(driver, dir):
        Path(dir).mkdir(parents=True, exist_ok=True)
        try:
            call_frame = driver.find_element(By.NAME, "pip_frame")
            driver.switch_to.frame(call_frame)

            hang_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Leave call']")
            ActionChains(driver)\
                .move_to_element(hang_button)\
                .click()\
                .pause(1)\
                .perform()
            hang_button.click()
            
            driver.save_screenshot(f"{dir}/5-hanged_call.png")
            driver.switch_to.default_content()
        except (NoSuchElementException, ElementNotInteractableException) as e:
            logging.exception(e)
            driver.save_screenshot("{}/x-element_not_found.png".format(dir))
            logging.info(f"screenshot saved: {dir}/x-element_not_found.png")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        setup_future_1 = executor.submit(setup_google_hangouts_chat, driver1, f"{dir}/setup-1", EMAIL_2)
        setup_future_2 = executor.submit(setup_google_hangouts_chat, driver2, f"{dir}/setup-2", EMAIL_1)
        setup_future_1.result()
        setup_future_2.result()
        if bool(random.getrandbits(1)):
            call_future_1 = executor.submit(call, driver1, f"{dir}/call-1")
            call_future_2 = executor.submit(accept_call, driver2, f"{dir}/call-2")
            logging.info("google hangouts call initiated by driver 1!")
        else:
            call_future_1 = executor.submit(call, driver2, f"{dir}/call-1")
            call_future_2 = executor.submit(accept_call, driver1, f"{dir}/call-2")
            logging.info("google hangouts call initiated by driver 2!")
        call_future_1.result()
        call_future_2.result()
        driver1.save_screenshot(f"{dir}/call-1/3-call_established.png")
        driver2.save_screenshot(f"{dir}/call-2/3-call_established.png")
        logging.info("google hangouts call established!")
        time.sleep(call_length)
        driver1.save_screenshot(f"{dir}/call-1/4-call_about_to_end.png")
        driver2.save_screenshot(f"{dir}/call-2/4-call_about_to_end.png")
        if bool(random.getrandbits(1)):
            stop_call(driver1, f"{dir}/call-1")
            logging.info("google hangouts call hanged by driver 1!")
        else:
            stop_call(driver2, f"{dir}/call-2")
            logging.info("google hangouts call hanged by driver 2!")
    
    logging.info("google hangouts chat done!")

def is_docker():
    path = '/proc/self/cgroup'
    return (
        os.path.exists('/.dockerenv') or
        os.path.isfile(path) and any('docker' in line for line in open(path))
    )

logging.basicConfig(format='%(asctime)s-%(process)d-%(levelname)s:  %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)
logging.info(f"In docker: {is_docker()}")

driver = get_chrome_driver(os.environ["CHROME_DRIVER_ADDR"])
uncaptured_driver = get_chrome_driver(os.environ["CHROME_UNCAPTURED_DRIVER_ADDR"])
try:
    # test_get_quic_cloudflare(driver, "{}/quic-cloudflare/chrome".format(os.environ["CAPTURES_DIR"]))
    signed_in = test_google_signin(driver, "{}/google_signin".format(os.environ["CAPTURES_DIR"]))
    uncaptured_signed_in = test_google_signin(uncaptured_driver, "{}/uncaptured/google_signin".format(os.environ["CAPTURES_DIR"]))
    if not signed_in or not uncaptured_signed_in:
        print("Google is not signed in.")
        print("Set environment variable CHROME_SETUP=true and attach to noVNC at port 7900 or 7901 to set up Google account. Use defualt password \"secret\".")
        driver.quit()
        uncaptured_driver.quit()
        exit(1)
    
    test_google_hangouts_chat(driver, uncaptured_driver, "{}/hangouts_chat".format(os.environ["CAPTURES_DIR"]))
    test_google_hangouts_call(driver, uncaptured_driver, f"{os.environ['CAPTURES_DIR']}/hangouts_call", call_length=20)
    
    if not is_docker():
        time.sleep(300) # for development
finally:
    driver.quit()
    uncaptured_driver.quit()
