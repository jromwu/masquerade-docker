import os
import tempfile
import threading
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

import cv2


class Recording:
    enabled = False;
    def __init__(self, get_frame, output, fps=30, output_fps=10):
        self.dir_path = tempfile.TemporaryDirectory()
        self.finish = False
        self.fps = fps
        self.delay = 1 / fps
        self.get_frame = get_frame
        self.output = output
        self.output_fps = output_fps
        self.recording_thread = None

    def start(self):
        if Recording.enabled:
            self.recording_thread = threading.Thread(target=self.start_record, daemon=True)
            self.recording_thread.start()
        else:
            print("recording disabled")

    def start_record(self):
        i = 0
        while not self.finish:
            self.get_frame("{}/{:07d}.png".format(self.dir_path.name, i))
            time.sleep(self.delay)
            i += 1

        self.construct_video(ext="png")
        self.dir_path.cleanup()

    def stop(self):
        self.finish = True
        if self.recording_thread is not None:
            self.recording_thread.join()

    def construct_video(self, ext="png"):
        images = sorted([img for img in os.listdir(self.dir_path.name) if img.endswith(".png")])
        # Determine the width and height from the first image
        image_path = os.path.join(self.dir_path.name, images[0])
        frame = cv2.imread(image_path)
        height, width, channels = frame.shape

        # Define the codec and create VideoWriter object
        fourcc = cv2.VideoWriter_fourcc('m','p','4','v') # Be sure to use lower case
        out = cv2.VideoWriter(self.output, fourcc, self.output_fps, (width, height))

        for image in images:
            image_path = os.path.join(self.dir_path.name, image)
            frame = cv2.imread(image_path)
            out.write(frame) # Write out frame to video

        # Release everything if job is finished
        out.release()
        cv2.destroyAllWindows()

        print("The output video is {}".format(self.output))

def test_eight_components():
    chrome_options = webdriver.ChromeOptions()
    driver = webdriver.Remote(
        command_executor=os.environ["DRIVER_ADDR"],
        options=chrome_options
    )

    recording = Recording(get_frame=lambda x: driver.save_screenshot(x), output="{}/captured.mp4".format(os.environ["CAPTURES_DIR"]))
    recording.start()

    driver.get("https://www.selenium.dev/selenium/web/web-form.html")

    title = driver.title
    assert title == "Web form"

    driver.implicitly_wait(0.5)

    driver.save_screenshot("{}/loaded.png".format(os.environ["CAPTURES_DIR"]))

    text_box = driver.find_element(by=By.NAME, value="my-text")
    submit_button = driver.find_element(by=By.CSS_SELECTOR, value="button")

    text_box.send_keys("Selenium")
    driver.save_screenshot("{}/filled.png".format(os.environ["CAPTURES_DIR"]))

    submit_button.click()

    message = driver.find_element(by=By.ID, value="message")
    value = message.text
    assert value == "Received!"

    print("everything is perfect!")
    driver.save_screenshot("{}/finished.png".format(os.environ["CAPTURES_DIR"]))

    recording.stop()
    driver.quit()

def get_chrome_driver():
    chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument("enable-quic")
    # chrome_options.add_argument("quic-version=h3-27")
    chrome_options.add_argument("origin-to-force-quic-on=cloudflare-quic.com:443")
    driver = webdriver.Remote(
        command_executor=os.environ["CHROME_DRIVER_ADDR"],
        options=chrome_options
    )
    return driver

def get_firefox_driver():
    firefox_options = webdriver.FirefoxOptions()
    firefox_options.set_preference("network.dns.httpssvc.http3_fast_fallback_timeout", 0)
    # firefox_options.set_preference("network.http.http3.alt-svc-mapping-for-testing", r'cloudflare-quic.com;h3=":443"')
    driver = webdriver.Remote(
        command_executor=os.environ["FIREFOX_DRIVER_ADDR"],
        options=firefox_options
    )
    return driver

def test_get_quic_cloudflare(driver, dir):
    Path(dir).mkdir(parents=True, exist_ok=True)

    recording = Recording(get_frame=lambda x: driver.save_screenshot(x), output="{}/captured-quic.mp4".format(dir), fps=60)
    recording.start()

    driver.get("https://cloudflare-quic.com/")

    title = driver.title
    print("title: {}".format(title))

    driver.implicitly_wait(0.5)

    for i in range(1, 4):
        driver.save_screenshot("{}/loaded-{}.png".format(dir, i))
        indicator = "not found"
        indicator_strict = "not found"
        try:
            indicator = driver.find_element(By.CSS_SELECTOR,"p strong").text
            indicator_strict = driver.find_element(By.CSS_SELECTOR,"div[class='grid__item grid__item--two-fifths--40pct-tablet grid__item--no-bottom-margin'] p strong").text
        except NoSuchElementException:
            pass
        print("indicator: {} ({})".format(indicator, indicator_strict))
        driver.refresh()

    print("everything is done!")
    driver.save_screenshot("{}/finished.png".format(dir))

    recording.stop()
    driver.quit()

def test_get_quic_nginx(driver, dir):
    Path(dir).mkdir(parents=True, exist_ok=True)

    recording = Recording(get_frame=lambda x: driver.save_screenshot(x), output="{}/captured-quic.mp4".format(dir), fps=60)
    recording.start()

    driver.get("https://quic.nginx.org/")

    title = driver.title
    print("title: {}".format(title))
    driver.save_screenshot("{}/loaded.png".format(dir))

    driver.implicitly_wait(40)

    for i in range(1, 3):
        driver.save_screenshot("{}/loaded-{}.png".format(dir, i))
        indicator = "not found"
        try:
            indicator = driver.find_element(By.CSS_SELECTOR,".quic-support__text.quic-support__text_success :not(hidden)")
            indicator = "found"
        except NoSuchElementException:
            pass
        print("indicator: {}".format(indicator))
        driver.refresh()

    print("everything is done!")
    driver.save_screenshot("{}/finished.png".format(dir))

    recording.stop()
    driver.quit()

def test_get_quic_fastly(driver, dir):
    Path(dir).mkdir(parents=True, exist_ok=True)

    recording = Recording(get_frame=lambda x: driver.save_screenshot(x), output="{}/captured-quic.mp4".format(dir), fps=60)
    recording.start()

    driver.get("https://http3.is/")

    title = driver.title
    print("title: {}".format(title))
    driver.save_screenshot("{}/loaded.png".format(dir))

    driver.implicitly_wait(40)

    for i in range(1, 3):
        driver.save_screenshot("{}/loaded-{}.png".format(dir, i))
        try:
            indicator = driver.find_element(By.CSS_SELECTOR,"video[width='500']")
            indicator = "found"
        except NoSuchElementException:
            indicator = "not found"
        print("indicator: {}".format(indicator))
        driver.refresh()

    print("everything is done!")
    driver.save_screenshot("{}/finished.png".format(dir))

    recording.stop()
    driver.quit()

print("hello world")
print("CHROME_DRIVER_ADDR={}".format(os.environ["CHROME_DRIVER_ADDR"]))
print("FIREFOX_DRIVER_ADDR={}".format(os.environ["FIREFOX_DRIVER_ADDR"]))
print("CAPTURES_DIR={}".format(os.environ["CAPTURES_DIR"]))
# test_eight_components()
test_get_quic_cloudflare(get_chrome_driver(), "{}/quic-cloudflare/chrome".format(os.environ["CAPTURES_DIR"]))
test_get_quic_cloudflare(get_firefox_driver(), "{}/quic-cloudflare/firefox".format(os.environ["CAPTURES_DIR"]))
test_get_quic_nginx(get_firefox_driver(), "{}/quic-nginx/firefox".format(os.environ["CAPTURES_DIR"]))
test_get_quic_nginx(get_chrome_driver(), "{}/quic-nginx/chrome".format(os.environ["CAPTURES_DIR"]))
test_get_quic_fastly(get_firefox_driver(), "{}/quic-fastly/firefox".format(os.environ["CAPTURES_DIR"]))
test_get_quic_fastly(get_chrome_driver(), "{}/quic-fastly/chrome".format(os.environ["CAPTURES_DIR"]))
