# Jobs NLU

> Natural Language Understanding service for job search query processing.

<!--toc:start-->
- [Jobs NLU](#jobs-nlu)
  - [Overview](#overview)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Training the Model](#training-the-model)
  - [Testing](#testing)
  - [Running the NLU Service](#running-the-nlu-service)
  - [Available Commands](#available-commands)
<!--toc:end-->

## Overview

The Jobs NLU component provides domain-specific entity extraction for job search queries. It uses a RASA-based model trained on thousands of annotated job listings to extract structured information from natural language queries, including job titles, skills, locations, and preferences.

## Prerequisites

Ensure you have the following installed on your system:

```bash
# Install just for running command recipes
brew install just

# Install uv (optional, will be installed by justfile if needed)
pip install uv

# Python 3.10.x is required for RASA
brew install python@3.10
```

## Installation

Clone the repository and set up the NLU environment:

```sh
git clone https://github.com/amitpdev/jobs-ai-search.git
cd jobs-ai-search/nlu

# Create a virtual environment and install dependencies
just venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

## Configuration

The NLU component is configured through files in the project directory:

- `config.yml` - Model configuration and pipeline
- `domain.yml` - Entities and intents
- `data/nlu.yml` - Training examples for intents and entities

Review and modify these files as needed to adjust the model's behavior.

## Training the Model

To train the standalone NLU model:

```bash
just train-nlu
```

For a complete model including dialogue management (not typically needed for this project):

```bash
just train-core
```

## Testing

To evaluate the NLU model performance:

```bash
just test
# or directly
rasa test
```

This will run evaluation on the test data and generate performance reports.

## Running the NLU Service

To start the NLU API service:

```bash
just run
```

This will launch the RASA server with the API enabled, listening on `http://localhost:5005`.

The API can then be used by the main Jobs API service to parse search queries:
```
POST http://localhost:5005/model/parse
Content-Type: application/json

{
  "text": "remote senior python developer with AWS experience"
}
```

## Available Commands

The NLU component uses `just` as a command runner. Available commands include:

- `just run` - Start the RASA API server
- `just train-nlu` - Train the NLU model only
- `just train-core` - Train the complete model
- `just train-run` - Train the NLU model and start the server
- `just venv` - Create and set up the virtual environment using uv

For a full list of commands:

```bash
just
```
