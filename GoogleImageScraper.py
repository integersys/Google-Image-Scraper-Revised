# -*- coding: utf-8 -*-
"""
Created on Sat Jul 18 13:01:02 2020

@author: OHyic
"""
#import selenium drivers
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

#import helper libraries
import time
import urllib.request
from urllib.parse import urlparse, quote_plus
import os
import requests
import io
from PIL import Image
import re

#custom patch libraries
import patch

class GoogleImageScraper():
    def __init__(self, webdriver_path, image_path, search_key="cat", number_of_images=1, headless=True, min_resolution=(0, 0), max_resolution=(1920, 1080), max_missed=10):
        #check parameter types
        image_path = os.path.join(image_path, search_key)
        if (type(number_of_images)!=int):
            print("[Error] Number of images must be integer value.")
            return
        if not os.path.exists(image_path):
            print("[INFO] Image path not found. Creating a new folder.")
            os.makedirs(image_path)
            
        #check if chromedriver is installed
        if (not os.path.isfile(webdriver_path)):
            is_patched = patch.download_lastest_chromedriver()
            if (not is_patched):
                exit("[ERR] Please update the chromedriver.exe in the webdriver folder according to your chrome version:https://chromedriver.chromium.org/downloads")

        for i in range(1):
            try:
                #try going to www.google.com
                options = Options()
                if(headless):
                    options.add_argument('--headless=new')
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
                options.add_experimental_option('useAutomationExtension', False)
                driver = webdriver.Chrome(webdriver_path, chrome_options=options)
                driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                    'source': "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                })
                driver.set_window_size(1400,1050)
                driver.get("https://www.google.com")
                try:
                    WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "W0wltc"))).click()
                except Exception as e:
                    continue
            except Exception as e:
                #update chromedriver
                pattern = r'(\d+\.\d+\.\d+\.\d+)'
                version = list(set(re.findall(pattern, str(e))))[0]
                is_patched = patch.download_lastest_chromedriver(version)
                if (not is_patched):
                    exit("[ERR] Please update the chromedriver.exe in the webdriver folder according to your chrome version:https://chromedriver.chromium.org/downloads")

        self.driver = driver
        self.search_key = search_key
        self.number_of_images = number_of_images
        self.webdriver_path = webdriver_path
        self.image_path = image_path
        self.url = f"https://www.google.com/search?q={quote_plus(search_key)}&udm=2&hl=en"
        self.headless=headless
        self.min_resolution = min_resolution
        self.max_resolution = max_resolution
        self.max_missed = max_missed

    def find_image_urls(self):
        """
            This function search and return a list of image urls based on the search key.
            Example:
                google_image_scraper = GoogleImageScraper("webdriver_path","image_path","search_key",number_of_photos)
                image_urls = google_image_scraper.find_image_urls()

        """
        print("[INFO] Gathering image links")
        self.driver.get(self.url)
        if "/sorry/" in self.driver.current_url:
            if self.headless:
                print("[ERROR] Google requested browser verification. Set headless to False and run again.")
                self.driver.quit()
                return []
            print("[INFO] Google requested verification. Complete the check in Chrome to continue.")
            try:
                WebDriverWait(self.driver, 180).until(lambda driver: "/sorry/" not in driver.current_url)
            except Exception:
                print("[ERROR] Google verification was not completed within three minutes.")
                self.driver.quit()
                return []
        for button_id in ("W0wltc", "L2AGLb"):
            buttons = self.driver.find_elements(By.ID, button_id)
            if buttons and buttons[0].is_displayed():
                buttons[0].click()
                time.sleep(2)
                break
        try:
            WebDriverWait(self.driver, 15).until(
                lambda driver: len(driver.find_elements(By.CSS_SELECTOR, "div[data-docid]")) > 0
            )
        except Exception:
            print("[ERROR] Google image results did not load.")
            self.driver.quit()
            return []
        image_urls = []
        seen_result_ids = set()
        missed_count = 0
        time.sleep(3)

        def find_preview_source(driver):
            for image in driver.find_elements(By.CSS_SELECTOR, "img.iPVvYb"):
                source = image.get_attribute("src") or ""
                if source.startswith("http") and "encrypted" not in source and source not in image_urls:
                    return source
            return False

        while len(image_urls) < self.number_of_images and missed_count < self.max_missed:
            results = self.driver.find_elements(By.CSS_SELECTOR, "div[data-docid]")
            result = None
            result_id = None

            for candidate in results:
                candidate_id = candidate.get_attribute("data-docid")
                if candidate_id and candidate_id not in seen_result_ids:
                    result = candidate
                    result_id = candidate_id
                    break

            if result is None:
                previous_result_count = len(results)
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                current_result_count = len(self.driver.find_elements(By.CSS_SELECTOR, "div[data-docid]"))
                if current_result_count <= previous_result_count:
                    missed_count += 1
                continue

            seen_result_ids.add(result_id)

            try:
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", result)
                try:
                    result.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", result)
                source = WebDriverWait(self.driver, 5).until(find_preview_source)
                image_urls.append(source)
                print(f"[INFO] {self.search_key} \t #{len(image_urls) - 1} \t {source}")
                missed_count = 0
                time.sleep(1)
            except Exception:
                print("[INFO] Unable to get link")
                missed_count += 1

        self.driver.quit()
        print("[INFO] Google search ended")
        return image_urls

    def save_images(self,image_urls, keep_filenames):
        print(keep_filenames)
        #save images into file directory
        """
            This function takes in an array of image urls and save it into the given image path/directory.
            Example:
                google_image_scraper = GoogleImageScraper("webdriver_path","image_path","search_key",number_of_photos)
                image_urls=["https://example_1.jpg","https://example_2.jpg"]
                google_image_scraper.save_images(image_urls)

        """
        print("[INFO] Saving image, please wait...")
        for indx,image_url in enumerate(image_urls):
            try:
                print("[INFO] Image url:%s"%(image_url))
                search_string = ''.join(e for e in self.search_key if e.isalnum())
                image = requests.get(image_url,timeout=5)
                if image.status_code == 200:
                    with Image.open(io.BytesIO(image.content)) as image_from_web:
                        try:
                            if (keep_filenames):
                                #extact filename without extension from URL
                                o = urlparse(image_url)
                                image_url = o.scheme + "://" + o.netloc + o.path
                                name = os.path.splitext(os.path.basename(image_url))[0]
                                #join filename and extension
                                filename = "%s.%s"%(name,image_from_web.format.lower())
                            else:
                                filename = "%s%s.%s"%(search_string,str(indx),image_from_web.format.lower())

                            image_path = os.path.join(self.image_path, filename)
                            print(
                                f"[INFO] {self.search_key} \t {indx} \t Image saved at: {image_path}")
                            image_from_web.save(image_path)
                        except OSError:
                            rgb_im = image_from_web.convert('RGB')
                            rgb_im.save(image_path)
                        image_resolution = image_from_web.size
                        if image_resolution != None:
                            if image_resolution[0]<self.min_resolution[0] or image_resolution[1]<self.min_resolution[1] or image_resolution[0]>self.max_resolution[0] or image_resolution[1]>self.max_resolution[1]:
                                image_from_web.close()
                                os.remove(image_path)

                        image_from_web.close()
            except Exception as e:
                print("[ERROR] Download failed: ",e)
                pass
        print("--------------------------------------------------")
        print("[INFO] Downloads completed. Please note that some photos were not downloaded as they were not in the correct format (e.g. jpg, jpeg, png)")
