import base64
import bcrypt 

def recv_exact(conn, length):
    data = b''
    while len(data) < length:
        packet = conn.recv(length - len(data))
        if not packet:
            return None
        data += packet
    return data


def cryptage_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return base64.b64encode(salt + hashed).decode("utf-8")

def verify_password(stored_password, provided_password):
    decoded = base64.base64decode(stored_password.encode("utf-8"))
    salt = decoded[:29]
    hashed = decoded[29:]
    return bcrypt.checkpw(provided_password.encode("utf-8"), salt + hashed)

'''if clients[conn]["username"] not in username_to_id_cache:
                        response_queue_sender = queue.Queue()
                        db_queue.put({
                            "type": "get_client_id",
                            "data": {"username": clients[conn]["username"]},
                            "response": response_queue_sender
                        })
                        sender_client_id = response_queue_sender.get()
                        username_to_id_cache[clients[conn]["username"]] = sender_client_id
                    else:
                        sender_client_id = username_to_id_cache[clients[conn]["username"]]
                    
                    
                    
                    db_queue.put({
                        "type": "get_client_id",
                        "data": {"username": clients[conn]["username"]},
                        "response": response_queue_sender
                    })

                    sender_client_id = response_queue_sender.get()

                    if target_username not in username_to_id_cache:

                        response_queue_receiver = queue.Queue()
                        db_queue.put({
                            "type": "get_client_id",
                            "data": {"username": target_username},
                            "response": response_queue_receiver
                        })

                        receiver_client_id = response_queue_receiver.get()
                        username_to_id_cache[target_username] = receiver_client_id
                    else:
                        receiver_client_id = username_to_id_cache[target_username]'''
