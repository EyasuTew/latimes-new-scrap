import os
import re
from enum import unique, Enum
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
import calendar
from datetime import datetime
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class NewsExtractor:
    def __init__(self, search_phrase, category):
        self.search_phrase = search_phrase
        self.url = f"https://www.latimes.com/search?q={search_phrase}&f0={category}&s=1"
        self.driver = webdriver.Chrome()
        # self.driver.get(self.url)
        self.data = []

    def load_website(self):
        logging.info(f"Loading website... {self.url}")
        self.driver.get(self.url)
        logging.info("Website loaded")

    def calculate_news_months(self, number_of_months: int) -> float:
        current_month = datetime.now().month
        current_year = datetime.now().year
        month = current_month - number_of_months
        year = current_year
        if number_of_months <= 1:
            month = current_month
        elif month <= 0:
            year -= (1 + int(abs(month) / 12))
            if month < -11:
                month += (12 - int(abs(month) // 12) + 12)
            else:
                month += 12
        num_days = calendar.monthrange(year, month)[1]
        return float(datetime(year, month, num_days).timestamp())

    def extract_news(self, number_of_months: int):
        oldest_timestamp = self.calculate_news_months(number_of_months)
        check = True
        self.load_website()

        while check:
            news_list = self.driver.find_elements(By.XPATH, "//ul[@class='search-results-module-results-menu']//li")

            for i in range(len(news_list)):
                i_news_timestamp = news_list[i].find_element(By.CLASS_NAME, "promo-timestamp").get_attribute(
                    "data-timestamp")
                if (oldest_timestamp > (float(i_news_timestamp) / 1000)):
                    check = False
                    break
                i_news_title = news_list[i].find_element(By.CLASS_NAME, "promo-title").text
                i_news_image_url = news_list[i].find_element(By.CLASS_NAME, "image").get_attribute('src')
                i_news_description = news_list[i].find_element(By.CLASS_NAME, "promo-description").text
                i_news_date = news_list[i].find_element(By.CLASS_NAME, "promo-timestamp").text

                self.data.append({
                    "title": i_news_title,
                    "date": datetime.fromtimestamp(int(i_news_timestamp) / 1000).strftime("%Y-%m-%d"),
                    "description": i_news_description,
                    "picture_filename": self.download_image(i_news_image_url),
                    "count_of_search_phrases": self.count_search_phrases(self.search_phrase, i_news_title,
                                                                         i_news_description),
                    "contains_money": self.check_money(i_news_title, i_news_description),
                })
            if not check:
                break
            self.driver.find_element(By.CLASS_NAME, "search-results-module-next-page").click()

    def count_search_phrases(self, search_phrase, *texts) -> int:
        count = 0
        for text in texts:
            count += text.lower().count(search_phrase.lower())
        return count

    def check_money(self, *texts) -> bool:
        for text in texts:
            result = re.match("\$?(\d+\,*\.*){1,}(.dollars|.USD)?", text)
            if result:
                return True
        return False

    def download_image(self, url) -> str:
        directory = "images"
        # Send an HTTP GET request to the URL
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Create the directory if it doesn't exist
            if not os.path.exists(directory):
                os.makedirs(directory)

            # Generate a filename based on the current timestamp
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            extension = url.split('.')[-1]  # Get the extension from the URL
            filename = f"image_{timestamp}.{extension}"

            # Write the content of the response to a file
            with open(os.path.join(directory, filename), 'wb') as f:
                f.write(response.content)

            logging.info("Image downloaded successfully.")
            return filename
        else:
            logging.error("Failed to download image.")
            return "ERROR"

    def store_data(self):
        df = pd.DataFrame(self.data)
        df.to_excel("news_data.xlsx", index=False)
        logging.info("Stored data in Excel")


@unique
class CategoryEnum(Enum):
    ENTERTAINMENT = "00000163-01e3-d9e5-adef-33e330f30000"
    WORLD_AND_NATION = "00000168-8694-d5d8-a76d-efddaf000000"
    SPORTS = "00000163-01e3-d9e5-adef-33e30d170000"