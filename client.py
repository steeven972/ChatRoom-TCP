import socket
import threading 
import sys

from utils import recv_exact

HEADER = 64
HOSTNAME = socket.gethostbyname(socket.gethostname())
PORT = 5050
ADDR = (HOSTNAME, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
print_lock = threading.Lock()
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

running = True



def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.sendall(send_length)
    client.sendall(message)

def receive():
    global running
    while running:
        try:
            header = recv_exact(client, HEADER)
            print(header)
            if not header:
                print("\nDisconnected from server. client side")
                break

            msg_length = int(header.decode(FORMAT).strip())

            data = recv_exact(client, msg_length)
            if not data:
                break

            msg = data.decode(FORMAT)

            with print_lock:
                # Efface la ligne utilisateur en cours
                sys.stdout.write("\r" + " " * 80 + "\r")

                print(msg)

                # Réaffiche le prompt proprement
                sys.stdout.write("> ")
                sys.stdout.flush()

        except Exception as e:
            print(f"\nConnection error: {e}")
            break
    running = False
        

def disconnect():
    try:
        # prévenir proprement le serveur
        message = DISCONNECT_MESSAGE.encode(FORMAT)
        msg_length = len(message)

        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))

        client.sendall(send_length)
        client.sendall(message)

    except:
        pass  # si déjà mort, on ignore

    finally:
        client.close()   # ← LA vraie fermeture TCP
        print("Connection closed.")

def start():
    client.connect(ADDR)
    print(f"Connected to server at {ADDR}")

    USERNAME = input("Enter your username:").strip()
    send(f"USERNAME:{USERNAME}")

    thread = threading.Thread(target=receive, daemon=True)
    thread.start()
    while running:
        msg = input("> ")
        if msg.lower() == 'exit':
            disconnect()
            break
        send(msg)


start()