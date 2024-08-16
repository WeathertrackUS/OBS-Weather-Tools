import sqlite3
import pytz

ALLOWED_TABLES = {'sent_alerts'}
ALLOWED_COLUMNS = {'id', 'event', 'sent_datetime', 'expires_datetime', 'properties', 'description', 'instruction'}

def create_table(table_name, values):
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
    if table_name not in ALLOWED_TABLES:
        raise ValueError("Invalid table name")
    
    conn = sqlite3.connect('files/alerts.db')
    c = conn.cursor()
    c.execute(f"SELECT * FROM {table_name} WHERE id = ?", (identifier,))
    alert = c.fetchone()
    conn.close()
    return alert

def get_all_alerts(table_name):
    if table_name not in ALLOWED_TABLES:
        raise ValueError("Invalid table name")
    
    conn = sqlite3.connect('files/alerts.db')
    c = conn.cursor()
    c.execute(f"SELECT * FROM {table_name}")
    alerts = c.fetchall()
    conn.close()
    return alerts

def remove_alert(identifier, table_name):
    if table_name not in ALLOWED_TABLES:
        raise ValueError("Invalid table name")
    
    conn = sqlite3.connect('files/alerts.db')
    c = conn.cursor()
    c.execute(f"DELETE FROM {table_name} WHERE id = ?", (identifier,))
    conn.commit()
    conn.close()

def alert_exists(identifier, table_name):
    if table_name not in ALLOWED_TABLES:
        raise ValueError("Invalid table name")
    
    conn = sqlite3.connect('files/alerts.db')
    c = conn.cursor()
    c.execute(f"SELECT COUNT(*) FROM {table_name} WHERE id = ?", (identifier,))
    count = c.fetchone()[0]
    conn.close()
    return count > 0

def update(identifier, table_name, **kwargs):
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

    c.execute(query, tuple(values))
    conn.commit()
    conn.close()

def clear_database(table_name):
    if table_name not in ALLOWED_TABLES:
        raise ValueError("Invalid table name")
    
    conn = sqlite3.connect('files/alerts.db')
    c = conn.cursor()
    c.execute(f'DELETE FROM {table_name}')
    conn.commit()
    conn.close()
# database.py

import sqlite3
import pytz


def create_table(table_name, values):
    if table_name not in ['sent_alerts', 'other_allowed_table']:  # Whitelist of allowed table names
        raise ValueError("Invalid table name")
    
    conn = sqlite3.connect('files/alerts.db')
    c = conn.cursor()
    
    # Check if table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    if c.fetchone() is None:
        # Table doesn't exist, create it
        c.execute(f"CREATE TABLE {table_name} {values}")
    
    conn.commit()
    conn.close()


def insert(identifier, table_name, sent_datetime=None, expires_datetime=None,
           properties=None, description=None, instruction=None, event=None, **kwargs):
    """
    Inserts or replaces a record in the specified table in the SQLite database.

    Args:
        identifier (str): The unique identifier of the record.
        table_name (str): The name of the table to insert into.
        sent_datetime (datetime, optional): The datetime the alert was sent. Defaults to None.
        expires_datetime (datetime, optional): The datetime the alert expires. Defaults to None.
        properties (dict, optional): Additional properties of the alert. Defaults to None.
        description (str, optional): A description of the alert. Defaults to None.
        instruction (str, optional): An instruction related to the alert. Defaults to None.
        event (str, optional): The event associated with the alert. Defaults to None.
        **kwargs: Additional keyword arguments.

    Returns:
        None
    """
    conn = sqlite3.connect('files/alerts.db')
    c = conn.cursor()

    columns = ['id']
    values = [identifier]

    if event is not None:
        columns.append('event')
        values.append(event)

    if sent_datetime is not None:
        sent_datetime_utc = sent_datetime.astimezone(pytz.utc)
        sent_datetime_str = sent_datetime_utc.strftime('%Y-%m-%d %H:%M:%S')
        columns.append('sent_datetime')
        values.append(sent_datetime_str)

    if expires_datetime is not None:
        expires_datetime_utc = expires_datetime.astimezone(pytz.utc)
        expires_datetime_str = expires_datetime_utc.strftime('%Y-%m-%d %H:%M:%S')
        columns.append('expires_datetime')
        values.append(expires_datetime_str)

    if properties is not None:
        columns.append('properties')
        values.append(str(properties))

    if description is not None:
        columns.append('description')
        values.append(description)

    if instruction is not None:
        columns.append('instruction')
        values.append(instruction)

    placeholders = ', '.join(['?' for _ in values])
    colums_str = ', '.join(columns)

    query = f"INSERT OR REPLACE INTO {table_name} ({colums_str}) VALUES ({placeholders})"
    c.execute(query, values)
    conn.commit()
    conn.close()


def get_alert(identifier, table_name):
    """
    Retrieves an alert from the database based on its identifier and table name.

    Args:
        identifier (str): The unique identifier of the alert.
        table_name (str): The name of the table in the database where the alert is stored.

    Returns:
        tuple: The alert data as a tuple, or None if no alert is found.
    """
    conn = sqlite3.connect('files/alerts.db')
    c = conn.cursor()
    c.execute(f"SELECT * FROM {table_name} WHERE id = ?", (identifier,))
    alert = c.fetchone()
    conn.close()
    return alert


def get_all_alerts(table_name):
    """
    Retrieves all alerts from the specified table in the SQLite database.

    Args:
        table_name (str): The name of the table to retrieve alerts from.

    Returns:
        list: A list of all alerts in the specified table.
    """
    conn = sqlite3.connect('files/alerts.db')
    c = conn.cursor()
    c.execute(f"SELECT * FROM {table_name}")
    alerts = c.fetchall()
    conn.close()
    return alerts


def remove_alert(identifier, table_name):
    """
    Removes an alert from the database.

    Args:
        identifier (int): The unique identifier of the alert to be removed.
        table_name (str): The name of the table in the database where the alert is stored.

    Returns:
        None
    """
    conn = sqlite3.connect('files/alerts.db')
    c = conn.cursor()
    c.execute(f"DELETE FROM {table_name} WHERE id = ?", (identifier,))
    conn.commit()
    conn.close()


def alert_exists(identifier, table_name):
    """
    Checks if an alert exists in the database based on its identifier and table name.

    Args:
        identifier (str): The unique identifier of the alert to check for.
        table_name (str): The name of the table in the database where the alert is stored.

    Returns:
        bool: True if the alert exists, False otherwise.
    """
    conn = sqlite3.connect('files/alerts.db')
    c = conn.cursor()
    c.execute(f"SELECT COUNT(*) FROM {table_name} WHERE id = ?", (identifier,))
    count = c.fetchone()[0]
    conn.close()
    return count > 0


def update(identifier, table_name, **kwargs):
    """
    Updates an existing alert in the database.

    Args:
        identifier (int): The unique identifier of the alert to be updated.
        table_name (str): The name of the table in the database where the alert is stored.
        **kwargs: Additional keyword arguments to be updated in the alert.

    Returns:
        None
    """
    conn = sqlite3.connect('files/alerts.db')
    c = conn.cursor()

    set_clauses = []
    values = []
    for key, value in kwargs.items():
        if key in ['sent_datetime', 'expires_datetime']:
            value = value.astimezone(pytz.utc).strftime('%Y-%m-%d %H:%M:%S')
        set_clauses.append(f"{key} = ?")
        values.append(value)

    set_clause = ', '.join(set_clauses)
    query = f"UPDATE {table_name} SET {set_clause} WHERE id = ?"
    values.append(identifier)

    c.execute(query, tuple(values))
    conn.commit()
    conn.close()


def clear_database(table_name):
    """
    Clears the specified table in the SQLite database.

    Args:
        table_name (str): The name of the table to be cleared.

    Returns:
        None
    """
    conn = sqlite3.connect('files/alerts.db')
    c = conn.cursor()
    c.execute(f'DELETE FROM {table_name}')
    conn.commit()
    conn.close()
