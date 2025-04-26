# Jobs Worker

> Job scraper and data processing worker for the Jobs AI Search platform.

<!--toc:start-->
- [Jobs Worker](#jobs-worker)
  - [Overview](#overview)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Running the Worker](#running-the-worker)
  - [Available Commands](#available-commands)
<!--toc:end-->

## Overview

The Jobs Worker component is responsible for scraping job listings from LinkedIn, processing the data, and storing it in the database. It uses Celery for task management and Selenium for web scraping.

## Prerequisites

Ensure you have the following installed on your system:

```bash
# Install just for running command recipes
brew install just

# Install uv (optional, will be installed by justfile if needed)
pip install uv
```

You'll also need:
- Selenium WebDriver compatible with your browser
- Redis (for Celery task queue)

## Installation

Clone the repository and set up the Worker environment:

```sh
git clone https://github.com/amitpdev/jobs-ai-search.git
cd jobs-ai-search/worker

# Install development dependencies
just install-dev
```

The `install-dev` command will create a virtual environment, activate it, and install all required dependencies using uv.

## Configuration

Copy the sample environment file and configure as needed:

```sh
cp .env{_sample,}
```

Required settings in `.env`:
- `JOBS_API_ENDPOINT='http://127.0.0.1:8000/jobs'` - URL for the API service
- LinkedIn credentials:
  ```
  LINKEDIN_USERNAME='your-email@example.com'
  LINKEDIN_PASSWORD='your-password'
  ```
- LinkedIn search parameters:
  ```
  LINKEDIN_QUERY_KEYWORDS='software engineer'
  LINKEDIN_QUERY_LOCATION='San Francisco Bay Area'
  LINKEDIN_QUERY_JOB_TYPE='F'  # F=Full-time, P=Part-time, C=Contract, etc.
  ```

Additional configuration options are available in `worker/config.py`.

## Running the Worker

The worker consists of multiple components that need to be run separately:

1. **Celery Worker** - Processes tasks from the queue
2. **Beat Scheduler** - Schedules periodic tasks
3. **Scraper** - Manually trigger scraping job
4. **Parser** - Manually trigger parsing job

## Available Commands

The Worker component uses `just` as a command runner. Available commands include:

```bash
# Start the main Celery worker
just worker

# Start the Beat scheduler for periodic tasks
just beat

# Manually run a scraping job
just scrape

# Manually run a parsing job
just parse
```

For a typical setup, you'll want to run both the worker and beat processes:

```bash
# In one terminal
just worker

# In another terminal
just beat
```

For a full list of commands:

```bash
just
```

## How It Works

1. The Beat scheduler periodically triggers scraping tasks
2. The Worker scrapes job listings from LinkedIn using Selenium
3. Job descriptions are parsed and embedded using transformers
4. The processed data is sent to the API for storage in PostgreSQL
5. The data becomes available for searching via the API
