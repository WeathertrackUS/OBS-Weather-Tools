# database.py

import sqlite3
from dateutil import parser
import pytz

def create_table():
    conn = sqlite3.connect('alerts.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sent_alerts
                 (id TEXT PRIMARY KEY, sent_datetime TEXT, expires_datetime TEXT, properties TEXT)''')
    conn.commit()
    conn.close()

def insert_alert(identifier, sent_datetime, expires_datetime, properties):
    conn = sqlite3.connect('alerts.db')
    c = conn.cursor()
    sent_datetime_utc = sent_datetime.astimezone(pytz.utc)
    expires_datetime_utc = expires_datetime.astimezone(pytz.utc)
    sent_datetime_str = sent_datetime_utc.strftime('%Y-%m-%d %H:%M:%S')
    expires_datetime_str = expires_datetime_utc.strftime('%Y-%m-%d %H:%M:%S')
    c.execute("INSERT OR REPLACE INTO sent_alerts VALUES (?, ?, ?, ?)", (identifier, sent_datetime_str, expires_datetime_str, str(properties)))
    conn.commit()
    conn.close()

def get_alert(identifier):
    conn = sqlite3.connect('alerts.db')
    c = conn.cursor()
    c.execute("SELECT * FROM sent_alerts WHERE id = ?", (identifier,))
    alert = c.fetchone()
    conn.close()
    return alert

def get_all_alerts():
    conn = sqlite3.connect('alerts.db')
    c = conn.cursor()
    c.execute("SELECT * FROM sent_alerts")
    alerts = c.fetchall()
    conn.close()
    return alerts

def remove_alert(identifier):
    conn = sqlite3.connect('alerts.db')
    c = conn.cursor()
    c.execute("DELETE FROM sent_alerts WHERE id = ?", (identifier,))
    conn.commit()
    conn.close()

def alert_exists(identifier):
    conn = sqlite3.connect('alerts.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM sent_alerts WHERE id = ?", (identifier,))
    count = c.fetchone()[0]
    conn.close()
    return count > 0

def update_alert(identifier, sent_datetime, expires_datetime, properties):
    conn = sqlite3.connect('alerts.db')
    c = conn.cursor()
    sent_datetime_utc = sent_datetime.astimezone(pytz.utc)
    expires_datetime_utc = expires_datetime.astimezone(pytz.utc)
    sent_datetime_str = sent_datetime_utc.strftime('%Y-%m-%d %H:%M:%S')
    expires_datetime_str = expires_datetime_utc.strftime('%Y-%m-%d %H:%M:%S')
    c.execute("UPDATE sent_alerts SET sent_datetime = ?, expires_datetime = ?, properties = ? WHERE id = ?",
              (sent_datetime_str, expires_datetime_str, str(properties), identifier))
    conn.commit()
    conn.close()
