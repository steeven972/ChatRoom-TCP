import mysql.connector
import queue
import threading
import time

db_queue = queue.Queue()

def db_worker():
    db = get_connection()
    cursor = db.cursor()

    print("[DB WORKER] Started")

    while True:
        task = db_queue.get()

        try:
            if task["type"] == "add_or_update_client":
                client_id = add_or_update_client(cursor=cursor, **task["data"])
                if "response" in task:
                    task["response"].put(client_id)

            elif task["type"] == "save_message":
                save_message(cursor=cursor, **task["data"])

            elif task["type"] == "get_client_id":
                client_id = get_client_id(cursor=cursor, **task["data"])
                task["response"].put(client_id)

            db.commit()

        except Exception as e:
            print(f"[DB ERROR] Task type: {task['type']}, Error: {e}")
            db.rollback()

        finally:
            db_queue.task_done()


def get_connection():
    while True:
        try:
            db = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="chat_app",
                autocommit=False
            )
            print("[DB] Connected")
            return db
        except Exception as e:
            print(f"[DB] Connection failed: {e}")
            time.sleep(2)

def add_or_update_client(username, connected=True, ip_addr=None, port=None, cursor=None):
    cursor.execute("SELECT id FROM clients WHERE username = %s", (username,))
    result = cursor.fetchone()

    if result:
        cursor.execute("""
            UPDATE clients
            SET connected=%s, last_seen=NOW(), ip=%s, port=%s
            WHERE id=%s
        """, (connected, ip_addr, port, result[0]))
        return result[0]
    else:
        cursor.execute("""
            INSERT INTO clients (username, connected, ip, port)
            VALUES (%s, %s, %s, %s)
        """, (username, connected, ip_addr, port))
        return cursor.lastrowid
    
def save_message(sender_id, receiver_id, message, cursor=None):
    cursor.execute("""
        INSERT INTO messages (sender_id, receiver_id, message)
        VALUES (%s, %s, %s)
    """, (sender_id, receiver_id, message))


def get_client_id(username, cursor=None):
    cursor.execute("SELECT id FROM clients WHERE username=%s", (username,))
    result = cursor.fetchone()
    return result[0] if result else None