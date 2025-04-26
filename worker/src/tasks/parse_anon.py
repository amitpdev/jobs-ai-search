import os
import re
from typing import Any

import httpx
import pandas as pd
from bs4 import BeautifulSoup
from celery.states import FAILURE

from src import config
from src.celery import celeryapp
from src.utils.date import convert_to_unix_timestamp

def debug_parse_print(text):
    if config.DEBUG:
        print(text)


def extract_job_post(page: BeautifulSoup) -> dict[str, Any]:
    job_post = {}

    # Job post ID
    a_tag = page.find("a", class_="topcard__link", href=True)
    if not a_tag.get("href"):
        debug_parse_print("Skipping: Post ID not found")
        return {}
    # extracting from "https://linkedin.com/jobs/view/devops-engineer-at-lab42-3623800907?..."
    pattern = r"jobs\/view\/.*-(\d+)\?"
    matches = re.findall(pattern, a_tag.get("href"))
    if matches:
        job_post_id = matches[0]
        job_post["job_post_id"] = job_post_id
        debug_parse_print(f"Post ID: {job_post_id}")
    else:
        debug_parse_print("Skipping: Post ID not found")
        return {}

    # Job Title
    job_title = clean_spaces(a_tag.text)
    job_post["job_title"] = job_title
    debug_parse_print(f"Job Title: {job_title}\n")

    # Company Name
    a_tag = page.find("a", class_="topcard__org-name-link", href=True)
    if not a_tag.get("text"):
        debug_parse_print("Skipping: Company Name not found")
        return {}

    company_name = clean_spaces(a_tag.text)
    job_post["company_name"] = company_name
    debug_parse_print(f"Company Name: {company_name}\n")

    # Location
    # 2nd span in div: "topcard__flavor-row"
    el = page.find(class_="topcard__flavor-row")
    location_span = el.find_all('span')[1]
    job_location = clean_spaces(location_span.text)
    job_post["job_location"] = job_location
    debug_parse_print(f"Job Location: {job_location}\n")

    # Workplace type
    el = page.find(class_="jobs-unified-top-card__workplace-type")
    if el:
        workplace_type = clean_spaces(el.text)
        job_post["workplace_type"] = workplace_type
        debug_parse_print(f"Workplace Type: {workplace_type}\n")

    # Posted date
    el = page.find(class_="jobs-unified-top-card__primary-description")
    posted_span = el.find_all('span')[3]
    posted_date = clean_spaces(posted_span.text)
    job_post["posted_date"] = posted_date
    job_post['posted_timestamp'] = convert_to_unix_timestamp(posted_date)
    debug_parse_print(f"Posted date: {posted_date}\n")

    # Job description
    el = page.find(class_="jobs-description__container")
    job_description = clean_spaces(el.text)
    job_post["job_description"] = job_description
    debug_parse_print(f"Job Description: {job_description}\n")

    # Company description (Optional)
    el = page.find(class_="jobs-company__box")
    if el:
        company_description = clean_spaces(el.text)
        job_post["company_description"] = company_description
        debug_parse_print(f"Company Description: {company_description}\n")

    # Contact
    job_post["contact"] = f"https://linkedin.com/jobs/view/{job_post_id}"

    return job_post


def clean_spaces(text: str) -> str:
    """Remove empty lines, leading spaces and trailing spaces"""
    return "\n".join(
        [line.strip() for line in text.split("\n") if line.strip()]
    )


@celeryapp.task
def start(results_dir: str):
    if len(results_dir) == 0:
        results_dir = config.RESULTS_DIR

    print(f"Parsing html files from {results_dir} ...")

    job_posts = [
        extract_job_post(
            BeautifulSoup(open(os.path.join(root, filename)).read(), "lxml")
        )
        for root, _, files in os.walk(results_dir)
        for filename in files
        if filename.endswith(".html")
    ]

    if not job_posts:
        print(f"Could not parse any job posts from htmls, check directory")
        return

    if config.OUTPUT_CSV:
        print(f"Writing {len(job_posts)} job posts to CSV: {config.OUTPUT_CSV}")
        jobs_dataframe = pd.DataFrame(job_posts)
        jobs_dataframe.to_csv(config.OUTPUT_CSV, index=False)

    if config.OUTPUT_API:
        print(f"Uploading {len(job_posts)} job posts with POST request: {config.OUTPUT_API}")
        try:
            resp = httpx.post(config.OUTPUT_API, json=job_posts)
            if resp.status_code != httpx.codes.OK:
                resp.raise_for_status()
        except httpx.ConnectError as e:
            print(e)
            return
        print(f"Response status_code: {resp.status_code} text: {resp.text}")


    print("Completed parsing.")

def main():
    # results_dir = input(
    #     "Enter directory to parse (e.g. results/1685662214_role)[Enter for default]: "
    # )
    results_dir = 'results/1688298723_Developer'
    result = start.apply(args=(results_dir,))
    if result.state == FAILURE:
        raise result.info

if __name__ == "__main__":
    main()
