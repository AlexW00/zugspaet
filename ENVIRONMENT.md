# Environment Variables

This document describes the environment variables used in the Zugspät application.

## Database Configuration
- `POSTGRES_PASSWORD`: Password for the PostgreSQL database

## API Configuration
- `API_KEY`: Your API key
- `CLIENT_ID`: Your client ID
- `PRIVATE_API_KEY`: Your private API key

## Application Configuration
- `BASE_URL`: The base URL of your application (e.g., https://your-domain.com)
- `DELETE_XML_AFTER_IMPORT`: Whether to delete XML files after import (true/false)
- `PRODUCTION`: Whether running in production mode (true/false)

## Ackee Analytics (Optional)
If both `ACKEE_SERVER_URL` and `ACKEE_DOMAIN_ID` are provided, Ackee tracking will be automatically enabled in the frontend.

- `ACKEE_SERVER_URL`: The URL of your Ackee server
- `ACKEE_DOMAIN_ID`: Your Ackee domain ID

## Example Configuration

```bash
# Required variables
POSTGRES_PASSWORD=your_postgres_password
API_KEY=your_api_key
CLIENT_ID=your_client_id
PRIVATE_API_KEY=your_private_api_key
BASE_URL=https://your-domain.com
DELETE_XML_AFTER_IMPORT=true
PRODUCTION=true

# Optional Ackee tracking
ACKEE_SERVER_URL=https://ackee.example.com
ACKEE_DOMAIN_ID=foobarid
```

## Docker Deployment

When deploying with Docker Compose, set these environment variables in your deployment environment (e.g., in Dockploy or your CI/CD system).
