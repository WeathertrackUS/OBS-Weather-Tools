import sqlite3

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
