import os
import pickle
import random
import re
import urllib.parse
from time import sleep, time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from celery.states import FAILURE

from src import config
from src.celery import celeryapp
from src.tasks.parse import start as parse_start


def setup_session() -> WebDriver:
    opts = Options()

    if config.SELENIUM_HEADLESS:
        print("Setting up a local headless browser...")
        opts.add_argument("--headless=new")
    else:
        print("Setting up a local browser...")

    opts.add_argument("--incognito")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--lang=en-US")
    opts.add_argument("--disable-notifications")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--enable-automation")
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-setuid-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-accelerated-2d-canvas")
    opts.add_argument("--allow-running-insecure-content")
    opts.add_argument("--disable-web-security")
    opts.add_argument("--disable-client-side-phishing-detection")
    opts.add_argument("--mute-audio")
    opts.add_argument("--ignore-certificate-errors")
    opts.add_argument("--remote-allow-origins=*")

    # Disable downloads
    opts.add_experimental_option(
        "prefs",
        {
            "safebrowsing.enabled": "false",
            "download.prompt_for_download": False,
            "download.default_directory": "/dev/null",
            "download_restrictions": 3,
            "profile.default_content_setting_values.notifications": 2,
        },
    )
    # User agent
    opts.add_argument(
        "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        " AppleWebKit/537.36 (KHTML, like Gecko)"
        " Chrome/112.0.0.0 Safari/537.36"
    )

    opts.set_capability("acceptSslCerts", True)
    opts.set_capability("acceptInsecureCerts", True)
    # 10 seconds implicit timeout
    opts.set_capability("timeouts", {"implicit": 10000})

    return webdriver.Chrome(options=opts)


def save_cookies(browser: WebDriver):
    with open(config.COOKIEJAR_FILENAME, "wb") as cookiefile:
        pickle.dump(browser.get_cookies(), cookiefile)


def remove_cookiejar():
    if os.path.isfile(config.COOKIEJAR_FILENAME):
        os.remove(config.COOKIEJAR_FILENAME)


# Load cookiejar into a browser object
def browser_get(browser: WebDriver, url: str, sleep_seconds: int):
    if os.path.isfile(config.COOKIEJAR_FILENAME):
        try:
            # throws EOFError if file size is zero
            cookiejar = pickle.load(open(config.COOKIEJAR_FILENAME, "rb"))
            for cookie in cookiejar:
                browser.add_cookie(cookie)
        except EOFError:
            remove_cookiejar()

    print(f"Browsing target URL: {url}")
    browser.get(url)
    save_cookies(browser)
    sleep(sleep_seconds)


def create_results_dir(query) -> str:
    # Create results dir by timestamp and query, return dir name
    timestamp_str = str(int(time()))
    if not os.path.exists(config.RESULTS_DIR):
        os.makedirs(config.RESULTS_DIR)
    _linkedin_query = re.sub(r"\s", "_", query)
    results_dir = f"results/{timestamp_str}_{_linkedin_query}"
    os.makedirs(results_dir)
    return results_dir


def scrape_loop(browser: WebDriver, results_dir: str, query: str, location: str) -> bool:

    # Compile url with search query and browse to it
    encoded_query = urllib.parse.quote(query)
    encoded_location = urllib.parse.quote(location)
    url = f"https://www.linkedin.com/jobs/search/?keywords={encoded_query}&location={encoded_location}&refresh=true"
    browser_get(browser, url, 4)

    # Iterate pages (~25 job posts on each page)
    current_page = 1
    print(f"Scraping page number {current_page}")

    # Find job post items on the left panel
    try:
        list_container = browser.find_element(
            By.CLASS_NAME, "two-pane-serp-page__results-list"
        )
        list_items = list_container.find_elements(
            By.CLASS_NAME, "job-search-card"
        )
    except NoSuchElementException:
        browser.save_screenshot("screenshot01.png")
        browser.quit()
        print("ERROR: Cannot find any job posts")
        return False

    print(f"Found {len(list_items)} job posts on this page")

    # Iterate job posts
    for i, item in enumerate(list_items):
        print(f"Clicking on job item number {i+1}")

        # Scroll to the item
        browser.execute_script("arguments[0].scrollIntoView();", item)
        sleep(1)
        # Click the item and wait
        item.click()
        random_wait = random.uniform(6, 11)  # avoid being detected?
        sleep(random_wait)

        # Click Show more undrer Job Description
        try:
            details_pane = browser.find_element(
                By.CLASS_NAME, "two-pane-serp-page__detail-view"
            )

            company_desc = details_pane.find_element(
                By.CLASS_NAME, "description__text"
            )

            button = company_desc.find_element(
                By.CLASS_NAME, "show-more-less-button"
            )
            browser.execute_script("arguments[0].scrollIntoView();", button)
            sleep(1)
            button.click()
            sleep(1)
        except (NoSuchElementException, ElementClickInterceptedException):
            browser.quit()
            return False

        # Grab only the right side panel (full job details)
        page = BeautifulSoup(browser.page_source, "lxml")
        details_pane = page.find("section", class_="two-pane-serp-page__detail-view")

        # Save results
        with open(
            f"{results_dir}/page_{current_page}_job_{i+1}.html",
            "w",
            encoding="utf-8",
        ) as file:
            file.write(str(details_pane.prettify()))

    return True



@celeryapp.task
def start():
    remove_cookiejar()
    browser = setup_session()

    results_dir = create_results_dir(config.LINKEDIN_QUERY_STRING)
    success = scrape_loop(
        browser,
        results_dir,
        config.LINKEDIN_QUERY_STRING,
        config.LINKEDIN_QUERY_LOCATION
    )

    if success:
        # Launch celery task with arguments.
        parse_start.s(results_dir)

    browser.quit()

def main():
    result = start.apply()
    if result.state == FAILURE:
        raise result.info

if __name__ == "__main__":
    main()
