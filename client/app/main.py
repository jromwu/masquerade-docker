import os
import string
import time
import random
import logging
import concurrent.futures
import sys

from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, TimeoutException

EMAIL_1 = "masque.traffic.test.0@gmail.com" # TODO: remove hardcoded email
EMAIL_2 = "masque.traffic.test@gmail.com"   # TODO: remove hardcoded email

GOOGLE_DRIVE_1GB_LINK = "https://drive.google.com/file/d/1jxqVPXaC3_ijbW10Q_iWmGVhW5L39bCk/view?usp=share_link"
GOOGLE_DRIVE_512MB_LINK = "https://drive.google.com/file/d/1CVl7jyCm_mfYX8qT81Wzlbln1h7ihiiG/view?usp=share_link"
GOOGLE_DRIVE_256MB_LINK = "https://drive.google.com/file/d/1Zxc9-SA3I9xbyflWe4dYl0eZhAR2zCKx/view?usp=share_link"
GOOGLE_DRIVE_64MB_LINK = "https://drive.google.com/file/d/1f42zBHJIHjnSWIOIQerGBlWlSIlujMRK/view?usp=share_link"
GOOGLE_DRIVE_16MB_LINK = "https://drive.google.com/file/d/1sWe3IUOr4Oykj3uqUtQ8k4obbLh7SQWM/view?usp=share_link"

google_chat_frame_selector = "*:not([style*='display: none']) > [aria-label='Chat content']"

# Borrowed from https://stackoverflow.com/questions/279561/what-is-the-python-equivalent-of-static-variables-inside-a-function
def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate

def get_chrome_driver(remote_addr):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("enable-quic")
    chrome_options.add_argument("user-data-dir=/user-data")
    chrome_options.add_argument("use-fake-device-for-media-stream")
    chrome_options.add_argument("use-fake-ui-for-media-stream")
    chrome_options.add_experimental_option("prefs", {
        "download.prompt_for_download": False,
        # "download.directory_upgrade": True,
        "safebrowsing_for_trusted_sources_enabled": False
        # "safebrowsing.enabled": True
    })
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

def test_google_hangouts_chat(driver1, driver2, dir, num_msgs=5, min_length=1, max_length=100, min_wait=0.01, max_wait=60):
    Path(dir).mkdir(parents=True, exist_ok=True)

    def send_chat_messages(driver, dir, num_msgs, min_length, max_length):
        Path(dir).mkdir(parents=True, exist_ok=True)
        try:
            driver.implicitly_wait(2)
            chat_frame = driver.find_element(By.CSS_SELECTOR, google_chat_frame_selector)
            driver.switch_to.frame(chat_frame)
            for i in range(0, num_msgs):
                time.sleep(random.uniform(min_wait, max_wait))
                logging.info(f"sending message {i}")
                chat_input = driver.find_element(By.CSS_SELECTOR, "[role=textbox]")
                random_string = ''.join(random.choice(string.digits + string.ascii_letters + string.punctuation + " ") for _ in range(random.randint(min_length, max_length)))
                chat_input.send_keys(f"Hello! This is test message {i} {random_string}")
                driver.save_screenshot(f"{dir}/2-entered_message_{i}.png")
                chat_input.send_keys(Keys.ENTER)
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
        chat_future_1 = executor.submit(send_chat_messages, driver1, f"{dir}/chat-1", num_msgs, min_length, max_length)
        chat_future_2 = executor.submit(send_chat_messages, driver2, f"{dir}/chat-2", num_msgs, min_length, max_length)
        chat_future_1.result()
        chat_future_2.result()
    
    logging.info("google hangouts chat done!")

def wait(driver, dir, length):
    # Selenium session will timeout and exit after ~5 minutes of inactivity,
    # so we save a screenshot every TIMEOUT_LENGTH to avoid this.
    TIMEOUT_LENGTH = 250 
    driver.save_screenshot(f"{dir}/y-keep_alive.png")
    while length > TIMEOUT_LENGTH:
        time.sleep(TIMEOUT_LENGTH)
        logging.info("waking up to keep Selenium session alive")
        length -= TIMEOUT_LENGTH
        driver.save_screenshot(f"{dir}/y-keep_alive.png")
    time.sleep(length)

def test_google_hangouts_call(driver1, driver2, dir, call_length=30):
    Path(dir).mkdir(parents=True, exist_ok=True)

    def call(driver, dir):
        Path(dir).mkdir(parents=True, exist_ok=True)
        try:
            driver.implicitly_wait(2)
            chat_frame = driver.find_element(By.CSS_SELECTOR, google_chat_frame_selector)
            driver.switch_to.frame(chat_frame)
            # for some reason, the call button is not present for some Google account
            driver.implicitly_wait(0)
            start_call_button = WebDriverWait(driver, timeout=10).until(expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, "div[role='button'][aria-label*='Start a video call']:not([aria-disabled='true'])")))
            start_call_button.click()
            
            driver.save_screenshot(f"{dir}/2-initiated_call.png")
            driver.switch_to.default_content()
        except Exception as e:
            logging.exception(e)
            driver.save_screenshot(f"{dir}/x-exception_thrown.png")
            logging.info(f"screenshot saved: {dir}/x-exception_thrown.png")
            raise e

    def accept_call(driver, dir):
        Path(dir).mkdir(parents=True, exist_ok=True)
        try:
            driver.implicitly_wait(2)
            call_frame = driver.find_element(By.NAME, "pip_frame")
            driver.switch_to.frame(call_frame)

            driver.implicitly_wait(0)
            join_button = WebDriverWait(driver, timeout=30).until(expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Answer call']")))
            join_button.click()
            # driver.execute_script("arguments[0].click();", join_button)
            
            driver.save_screenshot(f"{dir}/2-accepted_call.png")
            driver.implicitly_wait(2)
            driver.switch_to.default_content()
        except Exception as e:
            logging.exception(e)
            driver.save_screenshot(f"{dir}/x-exception_thrown.png")
            logging.info(f"screenshot saved: {dir}/x-exception_thrown.png")
            raise e
    
    def stop_call(driver, dir):
        Path(dir).mkdir(parents=True, exist_ok=True)
        try:
            driver.implicitly_wait(2)
            call_frame = driver.find_element(By.NAME, "pip_frame")
            driver.switch_to.frame(call_frame)

            hang_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Leave call']")
            ActionChains(driver)\
                .move_to_element(hang_button)\
                .click()\
                .pause(1)\
                .click()\
                .perform()
            # hang_button.click()
            
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
        logging.info(f"call will last {call_length} seconds")
        wait_future_1 = executor.submit(wait, driver1, f"{dir}/call-1/", call_length)
        wait_future_2 = executor.submit(wait, driver2, f"{dir}/call-2/", call_length)
        wait_future_1.result()
        wait_future_2.result()
        driver1.save_screenshot(f"{dir}/call-1/4-call_about_to_end.png")
        driver2.save_screenshot(f"{dir}/call-2/4-call_about_to_end.png")
        if bool(random.getrandbits(1)):
            stop_call(driver1, f"{dir}/call-1")
            logging.info("google hangouts call hanged by driver 1!")
        else:
            stop_call(driver2, f"{dir}/call-2")
            logging.info("google hangouts call hanged by driver 2!")
    
    logging.info("google hangouts call done!")

# It's worth noting that Google Hangouts calls are now also powered by Google Meet
def test_google_meet(driver1, driver2, dir, meet_length=30):
    Path(dir).mkdir(parents=True, exist_ok=True)
    leave_call_button_selector = "button[aria-label='Leave call']"

    def create_meeting(driver, dir):
        Path(dir).mkdir(parents=True, exist_ok=True)
        try:
            driver.get("https://meet.google.com/")
            driver.implicitly_wait(2)
            new_meeting_button = driver.find_element(By.XPATH, "//button[./span[normalize-space()='New meeting']]")
            new_meeting_button.click()
            instant_meeting_button = driver.find_element(By.CSS_SELECTOR, "li[aria-label='Start an instant meeting']")
            instant_meeting_button.click()
            driver.implicitly_wait(0)
            meeting_link_box = WebDriverWait(driver, timeout=15).until(lambda driver: driver.find_element(By.XPATH, "//div[starts-with(text(), 'meet.google.com/')]"))
            driver.save_screenshot(f"{dir}/1-started_meeting.png")
            meeting_link = meeting_link_box.text
        except Exception as e:
            logging.exception(e)
            driver.save_screenshot(f"{dir}/x-exception_thrown.png")
            logging.info(f"screenshot saved: {dir}/x-exception_thrown.png")
            raise e

        # if meeting_link is None:
        #     meeting_link = driver.current_url
        if not meeting_link.startswith('http'):
            meeting_link = 'https://' + meeting_link
        return meeting_link

    def accept_join(driver, dir):
        Path(dir).mkdir(parents=True, exist_ok=True)
        try:
            driver.implicitly_wait(0)
            try:
                # Maybe warnings and notifications will pop up, click the "Got it" buttons to dismiss them
                while True:
                    got_it_button = WebDriverWait(driver, timeout=3).until(expected_conditions.element_to_be_clickable((By.XPATH, "//button[./span[text()='Got it']]")))
                    got_it_button.click()
            except (NoSuchElementException, TimeoutException) as e:
                pass
            accept_button = WebDriverWait(driver, timeout=30).until(expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, "button[data-mdc-dialog-action='accept']")))
            accept_button.click()
            driver.save_screenshot(f"{dir}/2-accepted_participant.png")
        except Exception as e:
            logging.exception(e)
            driver.save_screenshot(f"{dir}/x-exception_thrown.png")
            logging.info(f"screenshot saved: {dir}/x-exception_thrown.png")
            raise e
    
    def join_meeting(driver, dir, link):
        Path(dir).mkdir(parents=True, exist_ok=True)
        try:
            driver.get(link)
            driver.implicitly_wait(2)
            # maybe a microphone popup will appear, use selector "div[aria-modal='true'] button" to click dismiss
            ask_to_join_button = driver.find_element(By.XPATH, "//button[./span[text()='Ask to join']]")
            ask_to_join_button.click()
            driver.save_screenshot(f"{dir}/1-waiting_to_join.png")
            driver.implicitly_wait(0)
            leave_call_button = WebDriverWait(driver, timeout=20).until(lambda driver: driver.find_element(By.CSS_SELECTOR, leave_call_button_selector))
            driver.save_screenshot(f"{dir}/2-joined_meeting.png")
        except Exception as e:
            logging.exception(e)
            driver.save_screenshot(f"{dir}/x-exception_thrown.png")
            logging.info(f"screenshot saved: {dir}/x-exception_thrown.png")
            raise e

    def exit_meeting(driver, dir):
        Path(dir).mkdir(parents=True, exist_ok=True)
        try:
            driver.implicitly_wait(2)
            exit_button = driver.find_element(By.CSS_SELECTOR, leave_call_button_selector)
            exit_button.click()
            driver.save_screenshot(f"{dir}/5-exited.png")
        except Exception as e:
            logging.exception(e)
            driver.save_screenshot(f"{dir}/x-exception_thrown.png")
            logging.info(f"screenshot saved: {dir}/x-exception_thrown.png")
            raise e
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        if bool(random.getrandbits(1)):
            logging.info(f"Meeting being created by driver 1")
            meeting_link = create_meeting(driver1, f"{dir}/create_meeting")
            logging.info(f"Meeting at {meeting_link} being joined by driver 2")
            join_future = executor.submit(join_meeting, driver2, f"{dir}/join_meeting", meeting_link)
            accept_future = executor.submit(accept_join, driver1, f"{dir}/create_meeting")
        else:
            logging.info(f"Meeting being created by driver 2")
            meeting_link = create_meeting(driver2, f"{dir}/create_meeting")
            logging.info(f"Meeting at {meeting_link} being joined by driver 1")
            join_future = executor.submit(join_meeting, driver1, f"{dir}/join_meeting", meeting_link)
            accept_future = executor.submit(accept_join, driver2, f"{dir}/create_meeting")
        join_future.result()
        accept_future.result()
        logging.info(f"Participants joined, meeting started")
        driver1.save_screenshot(f"{dir}/during_meeting_1/3-meeting_in_progress.png")
        driver2.save_screenshot(f"{dir}/during_meeting_2/3-meeting_in_progress.png")
        logging.info(f"The meeting will last {meet_length} seconds")
        wait_future_1 = executor.submit(wait, driver1, f"{dir}/during_meeting_1/", meet_length)
        wait_future_2 = executor.submit(wait, driver2, f"{dir}/during_meeting_2/", meet_length)
        wait_future_1.result()
        wait_future_2.result()
        driver1.save_screenshot(f"{dir}/during_meeting_1/4-meeting_about_to_end.png")
        driver2.save_screenshot(f"{dir}/during_meeting_2/4-meeting_about_to_end.png")
        exit_future_1 = executor.submit(exit_meeting, driver1, f"{dir}/during_meeting_1")
        exit_future_2 = executor.submit(exit_meeting, driver2, f"{dir}/during_meeting_2")
        exit_future_1.result()
        exit_future_2.result()
    
    logging.info("google meet done!")

def skip_or_wait_for_youtube_ads(driver):
    for i in range(4): # Assume there will be no more than 4 ads
        try:
            # if found, there is an ad, if it is skippable, once the skip button appears, this text will be gone
            driver.implicitly_wait(1)
            ad_indicator = driver.find_element(By.CLASS_NAME, "ytp-ad-preview-text") 
            logging.info("ads playing")
            driver.implicitly_wait(0)
            WebDriverWait(driver, timeout=30).until(expected_conditions.invisibility_of_element_located((By.CLASS_NAME, "ytp-ad-preview-text")))
            logging.info("ads unskippable part finished")
        except NoSuchElementException:
            break
        except TimeoutException as e:
            logging.exception(e)
            break

        try:
            driver.implicitly_wait(1)
            skip_ad_button = driver.find_element(By.CLASS_NAME, "ytp-ad-skip-button") # if found, there is a skip button
            driver.implicitly_wait(0)
            skip_ad_button = WebDriverWait(driver, timeout=20).until(expected_conditions.element_to_be_clickable((By.CLASS_NAME, "ytp-ad-skip-button")))
            skip_ad_button.click()
            logging.info("ads skipped")
            break
        except NoSuchElementException:
            pass
        except TimeoutException as e:
            logging.exception(e)
            break

    logging.info("ads finished")

def test_youtube_video(driver, dir, num_video=3, min_watch_length=30, max_watch_length=60):
    Path(dir).mkdir(parents=True, exist_ok=True)
    try:
        driver.get("https://www.youtube.com/")
        driver.implicitly_wait(2)
        try:
            cookies_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label*='cookies']")
            cookies_button.click()
        except NoSuchElementException:
            pass
        thumbnails = driver.find_elements(By.CLASS_NAME, "yt-core-image--loaded")
        driver.save_screenshot(f"{dir}/0-loaded_youtube_homepage.png")
        thumbnails[1].click() # we can change this to a random video, but it may get short videos
        driver.save_screenshot(f"{dir}/1-loaded_video.png")

        for i in range(num_video):
            driver.save_screenshot(f"{dir}/2-started_video-{i}.png")
            skip_or_wait_for_youtube_ads(driver)
            driver.implicitly_wait(2)
            metadata = driver.find_element(By.CSS_SELECTOR, "#title.ytd-watch-metadata h1 yt-formatted-string").text
            logging.info(f"Started watching video {i}: {metadata}")
            watch_time = random.uniform(min_watch_length, max_watch_length)
            logging.info(f"Watch for {watch_time} seconds")
            try:
                current_url = driver.current_url
                driver.implicitly_wait(0)
                WebDriverWait(driver, timeout=watch_time).until(lambda driver: driver.current_url != current_url) # wait for next song to autoplay
                logging.info(f"Video {i} finished before timeout.")
            except TimeoutException:
                logging.info(f"Getting the next video")
                driver.implicitly_wait(2)
                next_button = driver.find_element(By.CLASS_NAME, "ytp-next-button")
                next_button.click()
            
    except Exception as e:
        logging.exception(e)
        driver.save_screenshot(f"{dir}/x-exception_thrown.png")
        logging.info(f"screenshot saved: {dir}/x-exception_thrown.png")
        raise e
    
    logging.info("youtube video done!")

def test_youtube_music(driver, dir, num_song=3, min_song_listen_time=0, max_song_listen_time=60, chance_to_next_song=0.7):
    Path(dir).mkdir(parents=True, exist_ok=True)
    try:
        driver.get("https://music.youtube.com/channel/UCI6B8NkZKqlFWoiC_xE-hzA") # we can use this YOASOBI channel because their songs are all without music videos
        # driver.get("https://music.youtube.com/playlist?list=PLTKjnpVikK4zU42ASxX3_1Nb4Z9CttFyz") # or we can get a large playlist and let it shuffle play
        driver.implicitly_wait(0)
        
        try:
            cookies_button = WebDriverWait(driver, timeout=2).until(expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, "form button[aria-label*='Reject all']")))
            cookies_button.click()
        except (NoSuchElementException, TimeoutException):
            pass
        # Shuffle play to get randomness
        shuffle_button = WebDriverWait(driver, timeout=20).until(expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Shuffle']")))
        shuffle_button.click()
        driver.save_screenshot(f"{dir}/1-loaded.png")
        for i in range(num_song):
            driver.save_screenshot(f"{dir}/2-song-{i}.png")
            skip_or_wait_for_youtube_ads(driver)
            title = driver.find_element(By.CSS_SELECTOR, ".title.style-scope.ytmusic-player-bar").text
            logging.info(f"Started listening song {i}: {title}")

            if bool(random.random() < chance_to_next_song):
                driver.implicitly_wait(2)
                listen_time = random.uniform(min_song_listen_time, max_song_listen_time)
                logging.info(f"Getting next song after {listen_time}")
                time.sleep(listen_time)
                logging.info(f"clicking next")
                driver.find_element(By.CLASS_NAME, "next-button").click()
            else:
                logging.info(f"waiting for this song to finish")
                current_url = driver.current_url
                driver.implicitly_wait(0)
                WebDriverWait(driver, timeout=500).until(lambda driver: driver.current_url != current_url) # wait for next song to autoplay

    except Exception as e:
        logging.exception(e)
        driver.save_screenshot(f"{dir}/x-exception_thrown.png")
        logging.info(f"screenshot saved: {dir}/x-exception_thrown.png")
        raise e
    
    logging.info("youtube music done!")

"""
Check if a file with certain prefix is being downloaded in the "chrome://downloads" page.

Returns:
    False if file is still downloading or have not yet started, and file name downloaded if finished
    
    If check_downloading is True, return True if file has started downloading and False otherwise 

Raises:
  Exception: if downloading is errored or cancelled
"""
@static_vars(last_downloaded="")
def is_file_downloaded(driver, file_prefix, check_downloading=False):
        result = driver.execute_script( \
            "let lastDownload = document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList').items[0];"
            r"if (!lastDownload) { return false; }"
            "return [lastDownload.fileName, lastDownload.state, lastDownload.started];")
        
        if result == False: # no file downloaded/downloading
            return False
        file_name = result[0]
        state = result[1]
        if not file_name.startswith(file_prefix) or is_file_downloaded.last_downloaded == file_name:
            return False
        if check_downloading:
            return time.time() - result[2] < 60 # only count downloads started within 60 seconds
        if state == "COMPLETE":
            is_file_downloaded.last_downloaded = file_name
            return file_name
        if state == "IN_PROGRESS":
            return False
        raise Exception(f"File download failed with state: {state}") 

def test_google_file_download(driver, dir, file_link, timeout=60):
    Path(dir).mkdir(parents=True, exist_ok=True)

    try:
        driver.get(file_link) # we use this YOASOBI channel because their songs are all without music videos
        driver.implicitly_wait(2)
        # Shuffle play to get randomness
        download_button = driver.find_element(By.CSS_SELECTOR, "div[aria-label='Download'][role='button']")
        download_button.click()
        file_name = driver.title.removesuffix("- Google Drive").strip()
        logging.info(f"Start downloading {file_name}")
        driver.save_screenshot(f"{dir}/0-started_download.png")

        driver.execute_script("window.open('', 'download_tab');")
        driver.switch_to.window('download_tab')
        driver.get("chrome://downloads/")
        driver.find_element(By.TAG_NAME, "downloads-manager")

        driver.implicitly_wait(0)
        file_name_without_extension = os.path.splitext(file_name)[0]
        try:
            WebDriverWait(driver, 2).until(lambda driver: is_file_downloaded(driver, file_name_without_extension, check_downloading=True))
        except TimeoutException:
            # File not yet started download, maybe because virus scan check
            for handle in driver.window_handles:
                driver.switch_to.window(handle)
                if "virus scan" in driver.title.lower():
                    driver.implicitly_wait(2)
                    download_anyway_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
                    download_anyway_button.click()
                    driver.implicitly_wait(0)
                    driver.switch_to.window('download_tab')
                    WebDriverWait(driver, 2).until(lambda driver: is_file_downloaded(driver, file_name_without_extension, check_downloading=True))
                    driver.switch_to.window(handle)
                    driver.close()
                    driver.switch_to.window('download_tab')
                    break
        file_name_downloaded = WebDriverWait(driver, timeout).until(lambda driver: is_file_downloaded(driver, file_name_without_extension))
        logging.info(f"Finished downloading {file_name} to {file_name_downloaded}")
        driver.save_screenshot(f"{dir}/1-download_finished.png")
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        
    except Exception as e:
        logging.exception(e)
        driver.save_screenshot(f"{dir}/x-exception_thrown.png")
        logging.info(f"screenshot saved: {dir}/x-exception_thrown.png")
        raise e
    
    logging.info("google drive download done!")

def is_docker():
    path = '/proc/self/cgroup'
    return (
        os.path.exists('/.dockerenv') or
        os.path.isfile(path) and any('docker' in line for line in open(path))
    )

logging.basicConfig(format='%(asctime)s-%(process)d-%(levelname)s:  %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)
logging.info(f"In docker: {is_docker()}")

target = os.environ["TARGET"]
logging.info(f"Target: {target}")

driver = None
uncaptured_driver = None

try:
    match target:
        case "setup":
            driver = get_chrome_driver(os.environ["CHROME_DRIVER_ADDR"])
            uncaptured_driver = get_chrome_driver(os.environ["CHROME_UNCAPTURED_DRIVER_ADDR"])
            signed_in = test_google_signin(driver, "{}/google_signin".format(os.environ["CAPTURES_DIR"]))
            uncaptured_signed_in = test_google_signin(uncaptured_driver, "{}/uncaptured/google_signin".format(os.environ["CAPTURES_DIR"]))
            if not signed_in or not uncaptured_signed_in:
                print("Google is not signed in.")
                print("Set environment variable CHROME_SETUP=true and attach to noVNC at port 7900 or 7901 to set up Google account. Use defualt password \"secret\".")
                driver.quit()
                uncaptured_driver.quit()
                exit(1)
        case "test":
            driver = get_chrome_driver(os.environ["CHROME_DRIVER_ADDR"])
            test_get_quic_cloudflare(driver, "{}/quic-cloudflare/chrome".format(os.environ["CAPTURES_DIR"]))
            test_youtube_video(driver, f"{os.environ['CAPTURES_DIR']}/youtube_video", num_video=2, min_watch_length=5, max_watch_length=10)
            test_youtube_music(driver, f"{os.environ['CAPTURES_DIR']}/youtube_music", num_song=3, min_song_listen_time=5, max_song_listen_time=10, chance_to_next_song=1)
            test_google_file_download(driver, f"{os.environ['CAPTURES_DIR']}/drive_download", GOOGLE_DRIVE_16MB_LINK, timeout=60)
        case "test_google":
            driver = get_chrome_driver(os.environ["CHROME_DRIVER_ADDR"])
            uncaptured_driver = get_chrome_driver(os.environ["CHROME_UNCAPTURED_DRIVER_ADDR"])
            signed_in = test_google_signin(driver, "{}/google_signin".format(os.environ["CAPTURES_DIR"]))
            uncaptured_signed_in = test_google_signin(uncaptured_driver, "{}/uncaptured/google_signin".format(os.environ["CAPTURES_DIR"]))
            if not signed_in or not uncaptured_signed_in:
                print("Google is not signed in.")
                print("Set environment variable CHROME_SETUP=true and attach to noVNC at port 7900 or 7901 to set up Google account. Use defualt password \"secret\".")
                driver.quit()
                uncaptured_driver.quit()
                exit(1)
            else:
                test_google_hangouts_chat(driver, uncaptured_driver, f"{os.environ['CAPTURES_DIR']}/hangouts_chat", num_msgs=2, min_wait=0.01, max_wait=3)
                test_google_hangouts_call(driver, uncaptured_driver, f"{os.environ['CAPTURES_DIR']}/hangouts_call", call_length=10)
                test_google_meet(driver, uncaptured_driver, f"{os.environ['CAPTURES_DIR']}/google_meet", meet_length=10)
        case "chat":
            driver = get_chrome_driver(os.environ["CHROME_DRIVER_ADDR"])
            uncaptured_driver = get_chrome_driver(os.environ["CHROME_UNCAPTURED_DRIVER_ADDR"])
            test_google_hangouts_chat(driver, uncaptured_driver, f"{os.environ['CAPTURES_DIR']}/hangouts_chat", num_msgs=100, min_wait=0.01, max_wait=30)
        case "call":
            driver = get_chrome_driver(os.environ["CHROME_DRIVER_ADDR"])
            uncaptured_driver = get_chrome_driver(os.environ["CHROME_UNCAPTURED_DRIVER_ADDR"])
            test_google_hangouts_call(driver, uncaptured_driver, f"{os.environ['CAPTURES_DIR']}/hangouts_call", call_length=1200)
        case "meet":
            driver = get_chrome_driver(os.environ["CHROME_DRIVER_ADDR"])
            uncaptured_driver = get_chrome_driver(os.environ["CHROME_UNCAPTURED_DRIVER_ADDR"])
            test_google_meet(driver, uncaptured_driver, f"{os.environ['CAPTURES_DIR']}/google_meet", meet_length=2400)
        case "video":
            driver = get_chrome_driver(os.environ["CHROME_DRIVER_ADDR"])
            test_youtube_video(driver, f"{os.environ['CAPTURES_DIR']}/youtube_video", num_video=10, min_watch_length=120, max_watch_length=240)
        case "music":
            driver = get_chrome_driver(os.environ["CHROME_DRIVER_ADDR"])
            test_youtube_music(driver, f"{os.environ['CAPTURES_DIR']}/youtube_music", num_song=40, min_song_listen_time=5, max_song_listen_time=20, chance_to_next_song=0.3)
        case _:
            logging.warning("TARGET not set.")

    if not is_docker():
        time.sleep(300) # for development
finally:
    if driver is not None:
        driver.quit()
    if uncaptured_driver is not None:
        uncaptured_driver.quit()
