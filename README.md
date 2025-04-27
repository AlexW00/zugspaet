# 🚂 Zugspaet

[![Better Stack Badge](https://uptime.betterstack.com/status-badges/v1/monitor/1t537.svg)](https://uptime.betterstack.com/?utm_source=status_badge)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Have you ever wondered if the Deutsche Bahn (DB) train you're about to book is usually late or on time? Unfortunately, Deutsche Bahn does not offer any way to check the historical delay statistics for a specific train. This is where [Zugspaet](https://zugspaet.de/) comes in.

Zugspät tracks and analyzes Deutsche Bahn train delays using live data from the DB API. On a webapp, you can then enter your train and see how often it was late or on time in the past!

Check it out: https://zugspaet.de/

https://github.com/user-attachments/assets/9c3b25fc-0315-4f0e-a164-3d6ce205bda5

## Features

- 📊 Historical delay statistics and visualizations
- 🗺️ Support for all major German train stations
- 📱 Responsive web interface
- 🔄 Daily data updates
- 🚂 Toot toot!

## How It Works

Zu\[g\]spät (a play on "Zug" [train] and "spät" [late]) is a data collection and visualization tool that helps understand Deutsche Bahn train delays:

1. **Data Collection**: Uses the Deutsche Bahn API to periodically fetch real-time train data
2. **Storage**: Stores raw data as XML files and processed data in PostgreSQL
3. **Processing**: Runs nightly jobs to analyze and aggregate delay statistics
4. **Visualization**: Presents the data through an interactive web interface

## Tech Stack

- **Frontend**: TypeScript, React, Tailwind CSS
- **Backend**: Python, Flask
- **Database**: PostgreSQL
- **Infrastructure**: Deployed via Dokploy on a Hetzner VM
- **Data Processing**: Custom Python scripts (forked from [deutsche-bahn-data](https://github.com/piebro/deutsche-bahn-data))

## Development

### Prerequisites

- Python 3.11 or higher
- Node.js 20 or higher
- PostgreSQL 16
- Docker and Docker Compose (optional)
- Deutsche Bahn API credentials (API key and Client ID)

### Environment Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/AlexW00/zugspaet.git
   cd zugspaet
   ```

2. Create a `.env` file with the following variables:
   ```env
   API_KEY=your_db_api_key # Deutsche Bahn API key; requires Timetables & StaDa access
   CLIENT_ID=your_db_client_id # Deutsche Bahn Client ID
   PRIVATE_API_KEY=your_private_api_key # Secret used by the backend
   POSTGRES_PASSWORD=your_db_password
   BASE_URL=http://localhost:5000
   ```

### Running with Docker (Recommended)

The easiest way to get started is using Docker Compose:

```bash
docker-compose up
```

This will start all necessary services.

### Running Locally

1. Set up the Python environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Set up and build the frontend:

   ```bash
   cd frontend
   npm install
   npm run build
   ```

3. Start the development server:

   ```bash
   python server.py
   ```

4. Initialize the database:

   ```bash
   curl -X POST http://localhost:5000/private/import \
      -H "X-Private-Api-Key: $PRIVATE_API_KEY"
   ```

The application will be available at `http://localhost:5000`.

### Project Structure

```
├── frontend/            # frontend application
├── data/               # Raw XML data storage
├── migrations/         # Database migration scripts
├── server.py          # Main server
├── fetch_data.py      # Data collection script
├── db_utils.py        # Database utilities
└── docker-compose.yaml # Docker configuration
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

Forked from [deutsche-bahn-data](https://github.com/piebro/deutsche-bahn-data) by [piebro](https://github.com/piebro) - a collection of Python scripts to fetch and store Deutsche Bahn train data. Without this project, Zugspät would not be possible!
