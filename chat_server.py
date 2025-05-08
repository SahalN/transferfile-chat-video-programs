from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread

clients = {}
addresses = {}

HOST = '127.0.0.1'
PORT = 33000
BUFSIZ = 1024
ADDR = (HOST, PORT)

def accept_incoming_connections():
    while True:
        client, client_address = SERVER.accept()
        print(f"{client_address} terhubung.")
        client.send(bytes("Ketik username Anda:", "utf8"))
        addresses[client] = client_address
        Thread(target=handle_client, args=(client,)).start()

def handle_client(client):
    name = client.recv(BUFSIZ).decode("utf8")
    clients[client] = name
    broadcast(bytes(f"{name} telah bergabung!", "utf8"))
    while True:
        msg = client.recv(BUFSIZ)
        if msg == bytes("{quit}", "utf8"):
            client.close()
            del clients[client]
            broadcast(bytes(f"{name} telah keluar dari chat.", "utf8"))
            break
        else:
            broadcast(msg, name + ": ")

def broadcast(msg, prefix=""):
    for sock in clients:
        sock.send(bytes(prefix, "utf8") + msg)

SERVER = socket(AF_INET, SOCK_STREAM)
SERVER.bind(ADDR)

if __name__ == "__main__":
    SERVER.listen(5)
    print("Menunggu koneksi...")
    ACCEPT_THREAD = Thread(target=accept_incoming_connections)
    ACCEPT_THREAD.start()
    ACCEPT_THREAD.join()
    SERVER.close()
