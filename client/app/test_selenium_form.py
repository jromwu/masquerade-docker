import os
import tempfile
import threading
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
import cv2


class Recording:
    def __init__(self, get_frame, output, fps=30):
        self.dir_path = tempfile.TemporaryDirectory()
        self.finish = False
        self.fps = fps
        self.delay = 1 / fps
        self.get_frame = get_frame
        self.output = output
    
    def start(self):
        i = 0
        while not self.finish:
            self.get_frame("{}/{:07d}.png".format(self.dir_path.name, i))
            time.sleep(self.delay)
            i += 1

        self.construct_video(ext="png")
        self.dir_path.cleanup()
        
    def stop(self):
        self.finish = True

 
    def construct_video(self, ext="png"):
        images = sorted([img for img in os.listdir(self.dir_path.name) if img.endswith(".png")])

        # Determine the width and height from the first image
        image_path = os.path.join(self.dir_path.name, images[0])
        frame = cv2.imread(image_path)
        height, width, channels = frame.shape

        # Define the codec and create VideoWriter object
        fourcc = cv2.VideoWriter_fourcc('m','p','4','v') # Be sure to use lower case
        out = cv2.VideoWriter(self.output, fourcc, self.fps, (width, height))

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
    recording_thread = threading.Thread(target=recording.start, daemon=True)
    recording_thread.start()

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
    recording_thread.join()
    driver.quit()

print("hello world")
# print("DRIVER_ADDR={}".format(os.environ["DRIVER_ADDR"]))
# print("CAPTURES_DIR={}".format(os.environ["CAPTURES_DIR"]))
test_eight_components()
