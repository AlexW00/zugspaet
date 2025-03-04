import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask, send_from_directory
from flask_cors import CORS

from server.api.routes import api
from server.config.settings import (
    BASE_URL,
    LOG_LEVEL,
    LOGS_DIR,
    create_directories,
    validate_settings,
)
from server.db.database import init_database
from server.scheduler.tasks import init_scheduler

# Validate environment settings
validate_settings()

# Create necessary directories
create_directories()

# Configure logging
logging.basicConfig(level=LOG_LEVEL)
werkzeug_logger = logging.getLogger("werkzeug")
werkzeug_logger.setLevel(LOG_LEVEL)

# Create file handler
file_handler = RotatingFileHandler(LOGS_DIR / "app.log", maxBytes=10240, backupCount=10)
file_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
    )
)
file_handler.setLevel(LOG_LEVEL)

# Initialize database schema
print("Initializing database schema...")
init_database()


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, static_folder="../frontend/dist", static_url_path="")

    # Configure CORS
    CORS(app, resources={r"/api/*": {"origins": [BASE_URL]}})

    # Add file handler to Flask logger
    app.logger.addHandler(file_handler)
    app.logger.setLevel(LOG_LEVEL)

    # Register blueprints
    app.register_blueprint(api, url_prefix="/api")

    # Frontend routes
    @app.route("/")
    def serve_frontend():
        """Serve the frontend application."""
        return send_from_directory(app.static_folder, "index.html")

    @app.route("/<path:path>")
    def catch_all(path):
        """Catch-all route for frontend routing."""
        return send_from_directory(app.static_folder, "index.html")

    return app


def main():
    """Main application entry point."""
    # Create the Flask application
    app = create_app()

    # Initialize the scheduler
    scheduler = init_scheduler()

    try:
        # Run the application
        app.run(host="0.0.0.0", port=5000)
    finally:
        # Shut down the scheduler when the app stops
        scheduler.shutdown()


if __name__ == "__main__":
    main()
