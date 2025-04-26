import os
import sys
import logging
import pickle
import random
import re
import urllib.parse
from time import sleep, time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    InvalidCookieDomainException,
    NoSuchElementException,
    WebDriverException
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from celery.states import FAILURE

from src import config
from src.celery import celeryapp
from src.tasks.parse import start as parse_start
from src.utils.logger import Logger

logger = Logger(__name__).logger

def setup_session() -> WebDriver:
    opts = Options()

    if config.SELENIUM_HEADLESS:
        logger.debug("Setting headless flag on")
        opts.add_argument("--headless=new")
    else:
        logger.debug("Setting headless flag off")

    if config.SELENIUM_LOCAL_CHROME:
        logger.debug("Setting up a local chrome driver...")
    else:
        logger.debug("Setting up a remote browser...")


    # opts.add_argument("--incognito")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--lang=en-US")
    opts.add_argument("--disable-notifications")
    opts.add_argument("--enable-automation")
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-setuid-sandbox")
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
        " Chrome/114.0.0.0 Safari/537.36"
    )

    opts.set_capability("acceptInsecureCerts", True)
    # 10 seconds implicit timeout
    opts.set_capability("timeouts", {"implicit": 10000})

    # Reduce selenium logging level (debug by default)
    urllib3_logger = logging.getLogger('urllib3.connectionpool')
    urllib3_logger.setLevel(logging.INFO)
    selenium_logger = logging.getLogger('selenium.webdriver.remote.remote_connection')
    selenium_logger.setLevel(logging.INFO)
    selenium_logger = logging.getLogger('selenium.webdriver.common.service')
    selenium_logger.setLevel(logging.INFO)


    if config.SELENIUM_LOCAL_CHROME:
        return webdriver.Chrome(
            options=opts)

    return webdriver.Remote(
        command_executor=config.SELENIUM_REMOTE_ENDPOINT,
        options=opts)


def browser_get(browser: webdriver.Chrome, url: str):

    logger.debug('Browsing target URL: %s', url)
    try:
        browser.get(url)
    except WebDriverException as ex:
        logger.exception(ex)
        logger.error("Cannot load %s - Terminating webdriver session", url)
        browser.quit()
        return

def load_cookies(browser: webdriver.Chrome) -> bool:
    """ Loads cookiejar into browser session, returns True if loaded """
    if os.path.isfile(config.COOKIEJAR_FILENAME):
        try:
            # throws EOFError if file size is zero
            with open(config.COOKIEJAR_FILENAME, 'rb') as file:
                cookiejar = pickle.load(file)
                for cookie in cookiejar:
                    browser.add_cookie(cookie)
                return True
        except (EOFError, InvalidCookieDomainException, AttributeError) as ex:
            logger.exception(ex)
            remove_cookiejar()
        except WebDriverException as ex:
            logger.exception(ex)
            browser.quit()
    return False


def save_cookies(browser: WebDriver):
    with open(config.COOKIEJAR_FILENAME, "wb") as cookiefile:
        pickle.dump(browser.get_cookies(), cookiefile)


def remove_cookiejar():
    if os.path.isfile(config.COOKIEJAR_FILENAME):
        os.remove(config.COOKIEJAR_FILENAME)


def create_results_dir(from_linkedin_query) -> str:
    # Create results dir by timestamp and query, return dir name
    timestamp_str = str(int(time()))
    if not os.path.exists(config.RESULTS_DIR):
        os.makedirs(config.RESULTS_DIR)
    _linkedin_query = re.sub(r"\s", "_", from_linkedin_query)
    results_dir = f"{config.RESULTS_DIR}/{timestamp_str}_{_linkedin_query}"

    os.makedirs(results_dir)
    return results_dir


def scrape_loop(browser: WebDriver, results_dir: str, query: str, location: str) -> bool:

    # Compile url with search query and browse to it
    encoded_query = urllib.parse.quote(query)
    encoded_location = urllib.parse.quote(location)
    url = f"https://www.linkedin.com/jobs/search/?keywords={encoded_query}&location={encoded_location}&refresh=true"
    browser_get(browser, url)
    sleep(4)

    # Iterate pages (~25 job posts on each page)
    next_page_available = True
    current_page = 1
    while next_page_available:
        logger.debug(f"Scraping page number {current_page}")

        # Find job post items on the left panel
        try:
            list_container = browser.find_element(
                By.CLASS_NAME, "scaffold-layout__list-container"
            )
            list_items = list_container.find_elements(
                By.CLASS_NAME, "jobs-search-results__list-item"
            )
        except NoSuchElementException:
            browser.save_screenshot("screenshot01.png")
            browser.quit()
            logger.error("ERROR: Cannot find any job posts")
            return False

        logger.debug(f"Found {len(list_items)} job posts on this page")

        # Iterate job posts
        for i, item in enumerate(list_items):
            logger.debug(f"Clicking on job item number {i+1}")

            # Scroll to the item
            browser.execute_script("arguments[0].scrollIntoView();", item)
            sleep(1)
            # Click the item and wait
            item.click()
            random_wait = random.uniform(6, 20)  # avoid being detected?
            sleep(random_wait)

            # Click Show more undrer Company Description
            try:
                company_desc = browser.find_element(
                    By.CLASS_NAME, "jobs-company__company-description"
                )
                button = company_desc.find_element(
                    By.CLASS_NAME, "inline-show-more-text__button"
                )
                browser.execute_script("arguments[0].scrollIntoView();", button)
                sleep(1)
                button.click()
                sleep(1)
            except (NoSuchElementException, ElementClickInterceptedException):
                pass

            # Grab only the right side panel (full job details)
            page = BeautifulSoup(browser.page_source, "lxml")
            details_pane = page.find("div", class_="scaffold-layout__detail")

            # Save results
            with open(
                f"{results_dir}/page_{current_page}_job_{i+1}.html",
                "w",
                encoding="utf-8",
            ) as file:
                file.write(str(details_pane.prettify()))
        logger.debug(f"Saved {len(list_items)} html files into {results_dir}")

        # Next page logic
        if current_page >= config.LINKEDIN_SCRAPE_MAX_PAGES:
            next_page_available = False
            logger.debug(f"Reached maximum pages to scrape ({config.LINKEDIN_SCRAPE_MAX_PAGES}). exiting..")
            break

        # Locate page control container
        try:
            page_buttons_container = browser.find_element(
                By.CLASS_NAME, "artdeco-pagination__pages"
            )
            button_element = page_buttons_container.find_element(
                By.XPATH, f'//button[@aria-label="Page {current_page+1}"]'
            )
        except NoSuchElementException:
            next_page_available = False
            logger.debug(f"Next page control was not found. exiting..")
            break

        # Click next page button
        button_element.click()
        sleep(4)
        current_page += 1

    return True


def linkedin_login(browser: WebDriver, username: str, password: str) -> bool:
    assert username, "ERROR: you must provide a linkedin username"
    assert password, "ERROR: you must provide a linkedin password"

    browser_get(browser, "https://www.linkedin.com/home")
    sleep(3)

    # If cookie found and loaded, lets try silent login
    if load_cookies(browser):

        # Refresh page, should let us in if cookie is valid
        browser_get(browser, 'https://www.linkedin.com/home')
        sleep(3)

        if is_user_logged_in(browser):
            logger.debug("Successfuly logged in using cookie")
            # Save a more recent cookie and skip email/pass login
            save_cookies(browser)
            return True

    # Email/Pass login:
    logger.debug("Attempting email/pass sign in")

    # support two possible linkedin login page styles
    input_mappings = [
        ("session_key", "session_password"),
        ("email-or-phone", "password")
    ]
    found = False
    for email_id, password_id in input_mappings:
        try:
            email_input = browser.find_element(By.ID, email_id)
            password_input = browser.find_element(By.ID, password_id)
            found = True
            break
        except NoSuchElementException:
            pass

    if not found:
        logger.exception("Failed to find email and password inputs")
        browser.save_screenshot("screenshot01.png")
        browser.quit()
        return False

    email_input.send_keys(username)
    password_input.send_keys(password)
    password_input.submit()
    sleep(3)

    if is_user_logged_in(browser):
        logger.debug("Successfuly logged in using email/pass")
        # Save a more recent cookie and skip email/pass login
        save_cookies(browser)
        return True
    else:
        browser.quit()

    return False


def is_user_logged_in(browser: webdriver.Chrome) -> bool:
    """ Try to locate the profile image-button on the top bar (on the right) """
    me_photo_button = browser.find_elements(By.CLASS_NAME, "global-nav__me-photo")
    return len(me_photo_button) > 0

@celeryapp.task
def start():

    browser = setup_session()

    # First try to login
    if not linkedin_login(
        browser,
        config.LINKEDIN_USERNAME,
        config.LINKEDIN_PASSWORD):
        logger.error("ERROR: Unable to sign into Linkedin")
        return

    results_dir = create_results_dir(from_linkedin_query=config.LINKEDIN_QUERY_STRING)
    success = scrape_loop(
        browser,
        results_dir,
        config.LINKEDIN_QUERY_STRING,
        config.LINKEDIN_QUERY_LOCATION
    )

    if success:
        # Launch celery task with arguments.
        parse_start.s(results_dir)

def main():
    logger.debug("Welcome")
    result = start.apply()
    if result.state == FAILURE:
        raise result.info

if __name__ == "__main__":
    main()
