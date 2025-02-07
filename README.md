# Open Maps Geospatial Repository

This repository contains the source code and configuration files for a geospatial application that serves vector tiles from PMTiles archives. The application uses FastAPI for the backend, Vue.js for the frontend, and MinIO as an object storage service. It does data processing to generate PMTiles with [DuckDB](https://duckdb.org/) and [Tippecanoe](https://github.com/felt/tippecanoe).

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
  - [Build PMTiles](#build-pmtiles)
  - [MinIO Setup](#minio-setup)
- [Usage](#usage)
- [File Structure](#file-structure)

## Features

- Downloads PMTiles files from S3 if they don't exist locally.
- Serves TileJSON metadata for the PMTiles archive.
- Provides vector tiles from the PMTiles archive.
- Uses MinIO as an object storage service.
- Frontend built with Vue.js and MapLibre GL.

## Prerequisites

- Python 3.13 or higher
- Node.js and npm
- Docker and Docker Compose

## Installation

### Backend Setup

Make sure you have UV installed on your system. https://docs.astral.sh/uv/getting-started/installation/

1. Clone the repository:

```sh
git clone git@github.com:jtbaker/open-maps.git
cd open-maps
uv sync
# activate the virtual environment
source ./.venv/bin/activate

export PYTHONPATH=./app

uvicorn main:app --reload
```

### Frontend Setup

1. Navigate to the frontend directory: `cd open-maps-frontend`
2. Install dependencies:

```sh
npm ci

npm run dev
```

### Build PMTiles

1. Run the following command to build PMTiles:

```sh
. ./scripts/build-pmtiles.sh
```

### MinIO Setup

1. Create a new MinIO instance by running this from the root:

```sh
docker compose up
```

Now you should be good to take a look at your application! Open your browser and go to `http://localhost:5173`. You should see the map displayed. Enjoy exploring!
