import os
import sqlite3
import logging

# Initialize logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def initialize_database(db_path, data_key):
    """Initialize the database and set up the required tables."""
    try:
        # Check if the database file exists
        if not os.path.exists(db_path):
            logger.error(f"Database file {db_path} does not exist.")
            raise FileNotFoundError(f"Database file {db_path} not found.")

        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        logger.info(f"Connected to database at {db_path}.")

        # Check if data_key is valid (simple check)
        if not data_key or len(data_key) < 16:
            logger.error("Invalid data key. Ensure it is at least 16 characters long.")
            raise ValueError("Invalid data key.")

        # Check and create the necessary tables (example: users table)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        logger.info("Users table created or already exists.")

        # Commit the transaction and close the connection
        conn.commit()
        conn.close()

        logger.info("Database initialization successful.")
    except sqlite3.Error as e:
        logger.error(f"SQLite error: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        raise

if __name__ == "__main__":
    # Example usage (you can replace these with actual environment variables)
    db_path = os.getenv("DB_PATH", "D:/ppp/Devin/database/my_database.db")
    data_key = os.getenv("DATA_KEY", "")

    # Initialize database
    initialize_database(db_path, data_key)
