import sqlite3

ALLOWED_TABLES = {'sent_alerts'}
ALLOWED_COLUMNS = {'id', 'event', 'sent_datetime', 'expires_datetime', 'properties', 'description', 'instruction'}


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

    conn = sqlite3.connect('files/alerts.db')
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

    conn = sqlite3.connect('files/alerts.db')
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

    conn = sqlite3.connect('files/alerts.db')
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

    conn = sqlite3.connect('files/alerts.db')
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

    conn = sqlite3.connect('files/alerts.db')
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

    conn = sqlite3.connect('files/alerts.db')
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

    conn = sqlite3.connect('files/alerts.db')
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

    conn = sqlite3.connect('files/alerts.db')
    c = conn.cursor()
    c.execute(f'DELETE FROM {table_name}')  # skipcq: BAN-B608
    conn.commit()
    conn.close()
