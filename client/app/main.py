import os
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

def get_chrome_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("enable-quic")
    chrome_options.add_argument("user-data-dir=/user-data")
    driver = webdriver.Remote(
        command_executor=os.environ["CHROME_DRIVER_ADDR"],
        options=chrome_options
    )
    return driver

def test_get_quic_cloudflare(driver, dir):
    Path(dir).mkdir(parents=True, exist_ok=True)

    driver.get("https://cloudflare-quic.com/")

    title = driver.title
    print("title: {}".format(title))

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
        print("indicator: {} ({})".format(indicator, indicator_strict))
        driver.refresh()

    print("cloudflare quic test done!")
    driver.save_screenshot("{}/finished.png".format(dir))

def test_google_signin(driver, dir):
    Path(dir).mkdir(parents=True, exist_ok=True)

    driver.get("https://accounts.google.com/")

    title = driver.title
    print("title: {}".format(title))
    driver.save_screenshot("{}/0-loaded.png".format(dir))

    if os.environ["CHROME_SETUP"] == "true":
        driver.implicitly_wait(10000) # give user enough time to sign in
    else:
        driver.implicitly_wait(2)

    try:
        indicator = driver.find_element(By.XPATH, "//h1[ contains (text(), 'Welcome' ) ]")
        print("Signed in: {}".format(indicator.text))
    except NoSuchElementException as e:
        print("element not found: {}".format(e))
        driver.save_screenshot("{}/x-element_not_found.png".format(dir))
        print(f"screenshot saved: {dir}/x-element_not_found.png")
        return False

    print("google signin done!")
    driver.save_screenshot("{}/finished.png".format(dir))

    return True

def test_google_hangouts_chat(driver, dir):
    Path(dir).mkdir(parents=True, exist_ok=True)

    driver.get("https://hangouts.google.com/")

    title = driver.title
    print("title: {}".format(title))
    driver.find_element(By.XPATH, "//span[contains(text(),'Chat') and @aria-level='2']")
    driver.save_screenshot("{}/0-loaded.png".format(dir))

    print("google hangouts chat done!")


driver = get_chrome_driver()
test_get_quic_cloudflare(driver, "{}/quic-cloudflare/chrome".format(os.environ["CAPTURES_DIR"]))
signed_in = test_google_signin(driver, "{}/google_signin".format(os.environ["CAPTURES_DIR"]))
if not signed_in:
    print("Google is not signed in.")
    print("Set environment variable CHROME_SETUP=true and attach to noVNC at port 7900 to set up Google account. Use defualt password \"secret\".")

test_google_hangouts_chat(driver, "{}/hangouts".format(os.environ["CAPTURES_DIR"]))
driver.quit()