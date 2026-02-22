import socket
import threading
import time
from utils import recv_exact
import queue

from db import db_worker, db_queue

HEADER = 64
FORMAT = 'utf-8'
HOST = "0.0.0.0"
PORT = 5050
ADDR = (HOST, PORT)
DISCONNECT_MESSAGE = "!DISCONNECT"
CONNECTION_LIMIT = 5

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

clients = {}
clients_lock = threading.Lock()
threading.Thread(target=db_worker, daemon=True).start()
username_to_id_cache = {}

def send(conn, msg):
    try:
        message = msg.encode(FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        conn.sendall(send_length)
        conn.sendall(message)
    except Exception as e:
        print(f"Error sending message: {e}")
        remove_client(conn)
        

def receive(conn):
    while True:
        try:
            header = recv_exact(conn, HEADER)
            if not header:
                print("\nDisconnected from server.")
                break

            msg_length = int(header.decode(FORMAT).strip())

            data = recv_exact(conn, msg_length)
            if not data:
                break

            msg = data.decode(FORMAT)
            print(f"Message from client: {msg}")
        except Exception as e:
            print(f"Error receiving message: {e}")
            break


def show_clients():
    with clients_lock:
        print("Connected clients:")
        for conn, info in clients.items():
            print(f"{info['username']} at {info['ip_addr']}:{info['port']}")

def show_userConnected():
    with clients_lock:
        print("Connected clients:")
        for conn, info in clients.items():
            print(f"{info['username']} at {info['ip_addr']}:{info['port']}")

def broadcast(conn, msg):

    dead_clients = []

    with clients_lock:
        for client in list(clients):
            if client != conn:
                try:
                    send(client, f"@{clients[conn]['username']}: {msg}")
                except Exception as e:
                    dead_clients.append(client)
    for dead in dead_clients:
        remove_client(dead)
    
    response_queue = queue.Queue()
    db_queue.put({
        "type": "get_client_id",
        "data": {"username": clients[conn]["username"]},
        "response": response_queue
    })

    client_id = response_queue.get() 
    if clients[conn]["username"] not in username_to_id_cache:
        username_to_id_cache[clients[conn]["username"]] = client_id

    db_queue.put({
        "type": "save_message",
        "data": {
            "sender_id": client_id,
            "receiver_id": None,
            "message": msg
        }
    })
    

def remove_client(conn):
    with clients_lock:
        if conn in clients:
            print(f"[REMOVE] Client {clients[conn]['username']} at ({clients[conn]['ip_addr']}) removed")
            db_queue.put({
                "type": "add_or_update_client",
                "data": {
                    "username": clients[conn]['username'],
                    "connected": False,
                    "ip_addr": clients[conn]['ip_addr'],
                    "port": clients[conn]['port']
                }
            })
            
           
            del clients[conn]
    conn.close()

def get_client_id(username):
    if username not in username_to_id_cache:
        response_queue = queue.Queue()
        db_queue.put({
            "type": "get_client_id",
            "data": {"username": username},
            "response": response_queue
        })

        receiver_client_id = response_queue.get()
        username_to_id_cache[username] = receiver_client_id
    else:
        receiver_client_id = username_to_id_cache[username]
    
    return receiver_client_id

def handler_client(conn, addr):
    print(f"[NEW CONNECTION] {addr}")

    if conn not in clients:
        with clients_lock:  
            clients[conn] = {'ip_addr': addr[0],
                            'port': addr[1],
                            'username': None,
                            'connected': True,
                            'messages': []}
        
    else:
        with clients_lock:
            clients[conn]['connected'] = True
            
    while True:
        try:
            header = recv_exact(conn, HEADER)
            if not header:
                break

            msg_length = int(header.decode(FORMAT).strip())

            data = recv_exact(conn, msg_length)
            if not data:
                break

            msg = data.decode(FORMAT)
            
            if msg == DISCONNECT_MESSAGE:
                print(f"[DISCONNECT] {addr} requested disconnection.")
                db_queue.put({
                "type": "add_or_update_client",
                "data": {
                    "username": clients[conn]['username'],
                    "connected": False,
                    "ip_addr": addr[0],
                    "port": addr[1]
                }
            })
                
                break
                
            elif msg.startswith("USERNAME:"):
                username = msg.split(":", 1)[1]
                with clients_lock:
                    clients[conn]['username'] = username
                print(f"[USERNAME] {addr} set username to {username}")
                db_queue.put({
                    "type": "add_or_update_client",
                    "data": {
                        "username": clients[conn]['username'],
                        "connected": True,
                        "ip_addr": addr[0],
                        "port": addr[1]
                    }
                })

                
                continue
            elif msg.startswith("@"):

                # Séparer "@username: message"
                try:
                    header, message = msg.split(":", 1)
                except ValueError:

                    send(conn, "Format: @username: message")
                    continue

                target_username = header[1:].strip()  # enlève @
                message = message.strip()

                target_conn = None

                with clients_lock:
                    for client_conn, client_info in clients.items():
                        if client_info['username'] == target_username:
                            target_conn = client_conn
                            break

                if target_conn:

                    sender_client_id = get_client_id(clients[conn]["username"])
                    receiver_client_id = get_client_id(target_username)
                    print(f"Sender ID: {sender_client_id}, Receiver ID: {receiver_client_id}")
                    send(target_conn, f"[PRIVATE] @{clients[conn]['username']}: {message}")
                    db_queue.put({
                        "type": "save_message",
                        "data": {
                            "sender_id": sender_client_id,
                            "receiver_id": receiver_client_id,
                            "message": message
                        }
                    })
                    
                else:
                    send(conn, f"User '{target_username}' not found.")

            elif msg.startswith("/list"):
                show_clients()
                send(conn, "User list")
            else:
                 broadcast(conn, msg)
                 

            print(f"[{addr[0]}:{clients[conn]['username']}] {msg}")
            
           

        except:
            break

    remove_client(conn)



def start():
    server.listen(CONNECTION_LIMIT)
    print(f"[LISTENING] on {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handler_client, args=(conn, addr))
        thread.start()


print("[STARTING] Server starting...")
start()