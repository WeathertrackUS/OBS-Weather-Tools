import sqlite3
from datetime import datetime, timezone
import os
import logging
from dateutil import parser

ALLOWED_TABLES = {'sent_alerts', 'active_alerts'}
ALLOWED_COLUMNS = {'id', 'event', 'sent_datetime', 'expires_datetime', 'properties', 'description', 'instruction', 'details', 'expiration_time', 'locations'}  #skipq: FLK-E501

# Define the absolute path to the database file
db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../files/alerts.db'))

# Ensure the database file exists
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def create_table(table_name, values):
    """
    Creates a table in the SQLite database if it does not already exist.

    Args:
        table_name (str): The name of the table to be created.
        values (str): The column definitions for the table.

    Returns:
        None

    Raises:
        ValueError: If the table name is not in the ALLOWED_TABLES set.
    """
    if table_name not in ALLOWED_TABLES:
        raise ValueError("Invalid table name")

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    if c.fetchone() is None:
        c.execute(f"CREATE TABLE {table_name} {values}")

    conn.commit()
    conn.close()


def insert(identifier, table_name, **kwargs):
    """
    Inserts or replaces a record in the specified table.

    Args:
        identifier (str): The identifier for the record.
        table_name (str): The name of the table to insert into.
        **kwargs: Additional key-value pairs to insert into the record.

    Returns:
        None

    Raises:
        ValueError: If the table name is not in the ALLOWED_TABLES set.
    """
    if table_name not in ALLOWED_TABLES:
        raise ValueError("Invalid table name")

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    columns = ['id']
    values = [identifier]
    placeholders = ['?']

    for key, value in kwargs.items():
        if key not in ALLOWED_COLUMNS:
            continue
        columns.append(key)
        values.append(value)
        placeholders.append('?')

    columns_str = ', '.join(columns)
    placeholders_str = ', '.join(placeholders)

    query = f"INSERT OR REPLACE INTO {table_name} ({columns_str}) VALUES ({placeholders_str})"
    c.execute(query, values)
    conn.commit()
    conn.close()


def get_alert(identifier, table_name):
    """
    Retrieves an alert from the database based on the provided identifier and table name.

    Args:
        identifier (str): The unique identifier of the alert to retrieve.
        table_name (str): The name of the table in which the alert is stored.

    Returns:
        tuple: The retrieved alert, or None if no alert is found.

    Raises:
        ValueError: If the table name is not in the ALLOWED_TABLES set.
    """
    if table_name not in ALLOWED_TABLES:
        raise ValueError("Invalid table name")

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(f"SELECT * FROM {table_name} WHERE id = ?", (identifier,))  # skipcq: BAN-B608
    alert = c.fetchone()
    conn.close()
    return alert


def get_all_alerts(table_name):
    """
    Retrieves all alerts from the specified table in the database.

    Args:
        table_name (str): The name of the table from which to retrieve alerts.

    Returns:
        list: A list of all alerts in the specified table.

    Raises:
        ValueError: If the table name is not in the ALLOWED_TABLES set.
    """
    if table_name not in ALLOWED_TABLES:
        raise ValueError("Invalid table name")

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(f"SELECT * FROM {table_name}")  # skipcq: BAN-B608
    alerts = c.fetchall()
    conn.close()
    return alerts


def remove_alert(identifier, table_name):
    """
    Removes an alert from the database based on the provided identifier and table name.

    Args:
        identifier (str): The unique identifier of the alert to remove.
        table_name (str): The name of the table in which the alert is stored.

    Raises:
        ValueError: If the table name is not in the ALLOWED_TABLES set.

    Returns:
        None
    """
    if table_name not in ALLOWED_TABLES:
        raise ValueError("Invalid table name")

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(f"DELETE FROM {table_name} WHERE id = ?", (identifier,))  # skipcq: BAN-B608
    conn.commit()
    conn.close()


def alert_exists(identifier, table_name):
    """
    Checks if an alert exists in the database based on the provided identifier and table name.

    Args:
        identifier (str): The unique identifier of the alert to check.
        table_name (str): The name of the table in which the alert is stored.

    Returns:
        bool: True if the alert exists, False otherwise.

    Raises:
        ValueError: If the table name is not in the ALLOWED_TABLES set.
    """
    if table_name not in ALLOWED_TABLES:
        raise ValueError("Invalid table name")

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(f"SELECT COUNT(*) FROM {table_name} WHERE id = ?", (identifier,))  # skipcq: BAN-B608
    count = c.fetchone()[0]
    conn.close()
    return count > 0


def update(identifier, table_name, **kwargs):
    """
    Updates a record in the specified table with the provided identifier.

    Args:
        identifier (str): The unique identifier of the record to update.
        table_name (str): The name of the table in which the record is stored.
        **kwargs: Key-value pairs of columns and values to update in the record.

    Raises:
        ValueError: If the table name is not in the ALLOWED_TABLES set.

    Returns:
        None
    """
    if table_name not in ALLOWED_TABLES:
        raise ValueError("Invalid table name")

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    set_clauses = []
    values = []
    for key, value in kwargs.items():
        if key not in ALLOWED_COLUMNS:
            continue
        set_clauses.append(f"{key} = ?")
        values.append(value)

    set_clause = ', '.join(set_clauses)
    query = f"UPDATE {table_name} SET {set_clause} WHERE id = ?"
    values.append(identifier)

    c.execute(query, tuple(values))  # skipcq: BAN-B608
    conn.commit()
    conn.close()


def clear_database(table_name):
    """
    Clears all records from the specified table in the database.

    Args:
        table_name (str): The name of the table to clear.

    Raises:
        ValueError: If the table name is not in the ALLOWED_TABLES set.

    Returns:
        None
    """
    if table_name not in ALLOWED_TABLES:
        raise ValueError("Invalid table name")

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(f'DELETE FROM {table_name}')  # skipcq: BAN-B608
    conn.commit()
    conn.close()


def insert_or_update_alert(alert_id, event, details, expiration_time, locations):
    """
    Inserts a new alert or updates an existing one in the database.

    Parameters:
        alert_id (str): The unique ID of the alert.
        event (str): The name of the alert event.
        details (str): Additional details about the alert.
        expiration_time (str): The expiration time of the alert (ISO format).
        locations (str): The locations affected by the alert.

    Returns:
        None
    """
    try:
        # Parse the expiration time and convert to UTC
        expiration_time_utc = parser.isoparse(expiration_time).astimezone(timezone.utc).isoformat()

        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO active_alerts (id, event, details, expiration_time, locations)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                event=excluded.event,
                details=excluded.details,
                expiration_time=excluded.expiration_time,
                locations=excluded.locations
            """,
            (alert_id, event, details, expiration_time_utc, locations)
        )
        conn.commit()
        logging.debug(f"Alert inserted/updated successfully: {alert_id}, {event}")
    except Exception as e:
        logging.error(f"Error inserting/updating alert: {e}")
    finally:
        conn.close()


def remove_expired_alerts():
    """
    Removes alerts from the database that have expired.

    Returns:
        None
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    current_time = datetime.now(timezone.utc).isoformat()  # Use timezone-aware current time
    logging.debug(f"Current time for expiration check: {current_time}")
    c.execute("SELECT * FROM active_alerts WHERE expiration_time <= ?", (current_time,))
    expired_alerts = c.fetchall()
    logging.debug(f"Expired alerts to be removed: {expired_alerts}")
    c.execute("DELETE FROM active_alerts WHERE expiration_time <= ?", (current_time,))
    conn.commit()
    conn.close()


def fetch_active_alerts():
    """
    Fetches all active alerts from the database.

    Returns:
        list: A list of active alerts.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT * FROM active_alerts")
    alerts = c.fetchall()
    conn.close()
    return alerts


# Create the table for active alerts
create_table('active_alerts', '''
    (
        id TEXT PRIMARY KEY,
        event TEXT,
        details TEXT,
        expiration_time TEXT,
        locations TEXT
    )
''')
