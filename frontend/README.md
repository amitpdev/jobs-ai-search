# Jobs Frontend

> Interactive web interface for the Jobs AI Search platform with real-time NLU processing.

<!--toc:start-->
- [Jobs Frontend](#jobs-frontend)
  - [Overview](#overview)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Development](#development)
  - [Building for Production](#building-for-production)
  - [Available Commands](#available-commands)
<!--toc:end-->

## Overview

The Jobs Frontend provides a responsive user interface for the Jobs AI Search platform. It features real-time preference extraction from user queries, interactive search filters, and dynamic result presentation. The frontend communicates with both the NLU service for query understanding and the API for retrieving job listings.

## Prerequisites

Ensure you have the following installed on your system:

```bash
# Install Node.js and npm/yarn
brew install node
npm install -g yarn
```

## Installation

Clone the repository and set up the Frontend environment:

```sh
git clone https://github.com/amitpdev/jobs-ai-search.git
cd jobs-ai-search/frontend

# Install dependencies
yarn install
```

## Configuration

The frontend can be configured through environment variables. Create a `.env` file in the frontend directory:

```sh
cp .env.example .env
```

Important settings to configure:
- `VITE_API_URL` - URL for the Jobs API service (default: 'http://localhost:8000')
- `VITE_NLU_URL` - URL for the NLU service (default: 'http://localhost:5005')

## Development

Before starting the frontend development server, ensure the other required services are running:

1. The NLU service should be running (see [NLU documentation](../nlu/README.md))
2. The API service should be running (see [API documentation](../api/README.md))

Then start the development server:

```bash
yarn run dev

# Or to open the app automatically in your browser
yarn run dev -- --open
```

This will start a development server with hot module replacement for rapid development.

## Building for Production

To build the application for production deployment:

```bash
yarn run build
```

This generates optimized static files in the `dist` directory. You can preview the production build with:

```bash
yarn run preview
```

## Available Commands

The Frontend component uses yarn scripts for common tasks:

- `yarn run dev` - Start the development server
- `yarn run build` - Build for production
- `yarn run preview` - Preview production build locally
- `yarn run check` - Run svelte-check to verify the codebase
- `yarn run lint` - Run the linter to check code quality
- `yarn run format` - Format code using Prettier

## Key Features

- Real-time extraction of job preferences as users type
- Interactive preference bubbles that can be toggled/removed
- Semantic job search with hybrid relevance ranking
- Responsive design for mobile and desktop
- Light/dark mode support
