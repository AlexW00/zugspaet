# Zugspät

## TL;DR

A web application that tracks and analyzes Deutsche Bahn train delays using historical data from the DB API. View delay statistics and patterns for any major German train station.

## Description

Zugspät (a play on "Zug" [train] and "spät" [late]) is a data collection and visualization platform that helps understand Deutsche Bahn train delays. It:

- Fetches real-time train data from Deutsche Bahn's API every 3 hours
- Stores historical delay information in a PostgreSQL database
- Provides a modern web interface to explore delay statistics by station
- Visualizes delay patterns and trends over time
- Supports multiple languages through i18n

## Development

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 16
- Deutsche Bahn API credentials (API key and Client ID)

### Environment Setup

1. Clone the repository
2. Create a `.env` file with the following variables:

```
API_KEY=your_db_api_key
CLIENT_ID=your_db_client_id
PRIVATE_API_KEY=your_private_api_key
POSTGRES_PASSWORD=your_db_password
BASE_URL=http://localhost:5000
```

### Running with Docker

```bash
docker-compose up
```

### Running Locally

1. Set up the Python environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Set up the frontend:

```bash
cd frontend
npm install
npm run build
```

3. Start the server:

```bash
python server.py
```

## Credits

Forked from [deutsche-bahn-data](https://github.com/piebro/deutsche-bahn-data) by [piebro](https://github.com/piebro) - a collection of Python scripts to fetch and store Deutsche Bahn train data. Without this project, Zugspät would not be possible.
