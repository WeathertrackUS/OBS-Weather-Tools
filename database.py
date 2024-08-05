# database.py

import sqlite3
from dateutil import parser
import pytz

def create_table(table_name, values):
    conn = sqlite3.connect('alerts.db')
    c = conn.cursor()
    c.execute(f'''CREATE TABLE IF NOT EXISTS {table_name}
                 {values}''')
    conn.commit()
    conn.close()

def insert(identifier, table_name, sent_datetime=None, expires_datetime=None, properties=None, description=None, instruction=None, event=None, **kwargs):
    conn = sqlite3.connect('alerts.db')
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
    conn = sqlite3.connect('alerts.db')
    c = conn.cursor()
    c.execute(f"SELECT * FROM {table_name} WHERE id = ?", (identifier,))
    alert = c.fetchone()
    conn.close()
    return alert

def get_all_alerts(table_name):
    conn = sqlite3.connect('alerts.db')
    c = conn.cursor()
    c.execute(f"SELECT * FROM {table_name}")
    alerts = c.fetchall()
    conn.close()
    return alerts

def remove_alert(identifier, table_name):
    conn = sqlite3.connect('alerts.db')
    c = conn.cursor()
    c.execute(f"DELETE FROM {table_name} WHERE id = ?", (identifier,))
    conn.commit()
    conn.close()

def alert_exists(identifier, table_name):
    conn = sqlite3.connect('alerts.db')
    c = conn.cursor()
    c.execute(f"SELECT COUNT(*) FROM {table_name} WHERE id = ?", (identifier,))
    count = c.fetchone()[0]
    conn.close()
    return count > 0

def update(identifier, table_name, **kwargs):
    conn = sqlite3.connect('alerts.db')
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
    conn = sqlite3.connect('alerts.db')
    c = conn.cursor()
    c.execute(f'DELETE FROM {table_name}')
    conn.commit()
    conn.close()