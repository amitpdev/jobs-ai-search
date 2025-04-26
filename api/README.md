# Jobs API

> Backend REST API for the Jobs AI Search platform.

<!--toc:start-->
- [Jobs API](#jobs-api)
  - [Overview](#overview)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Running the API](#running-the-api)
  - [Available Commands](#available-commands)
<!--toc:end-->

## Overview

The Jobs API provides the backend REST interface for job searches, handling NLU processing and database queries for the Jobs AI Search platform.

## Prerequisites

Ensure you have the following installed on your system:

```bash
# Install just for running command recipes
brew install just

# Install uv (optional, will be installed by justfile if needed)
pip install uv
```

## Installation

Clone the repository and set up the API environment:

```sh
git clone https://github.com/amitpdev/jobs-ai-search.git
cd jobs-ai-search/api

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
- `ENDPOINT_NLU='http://localhost:5005/model/parse'` - URL for the NLU service
- Configure PostgreSQL connection settings:
  ```
  POSTGRES_HOST=localhost
  POSTGRES_PORT=5432
  POSTGRES_DB=jobs
  POSTGRES_USER=postgres
  POSTGRES_PASSWORD=postgres
  ```

Additional configuration options are available in `api/config.py`.

## Running the API

To start the API server with auto-reload for development:

```bash
just run
```

This will launch the FastAPI server using uvicorn with hot reload enabled.

## Available Commands

The API component uses `just` as a command runner. Available commands include:

- `just run` - Start the API server with auto-reload
- `just install` - Install the package in a virtual environment
- `just install-dev` - Install the package with development dependencies
- `just venv` - Create and set up a virtual environment using uv

For a full list of commands:

```bash
just
```
