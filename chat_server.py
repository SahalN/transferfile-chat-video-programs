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
        client.send(bytes("", "utf8"))
        addresses[client] = client_address
        Thread(target=handle_client, args=(client,)).start()


def handle_client(client):
    name = client.recv(BUFSIZ).decode("utf8")
    clients[client] = name
    broadcast(bytes(f"{name} telah bergabung!", "utf8"))

    while True:
        try:
            msg = client.recv(BUFSIZ)
            if msg == bytes("{quit}", "utf8"):
                client.send(bytes("{quit}", "utf8"))  # agar client tahu server sudah OK
                client.close()
                del clients[client]
                broadcast(bytes(f"{name} telah keluar dari chat.", "utf8"))
                break
            else:
                broadcast(msg, name + ": ")
        except ConnectionResetError:
            # Handle jika client keluar secara paksa
            if client in clients:
                del clients[client]
                broadcast(bytes(f"{name} keluar mendadak.", "utf8"))
            break


def broadcast(msg, prefix=""):
    for sock in clients:
        sock.send(bytes(prefix, "utf8") + msg)

    # Kirim daftar user online ke semua klien
    online_users = ", ".join([clients[sock] for sock in clients])
    for sock in clients:
        sock.send(bytes(f"[USER ONLINE]: {online_users}", "utf8"))


SERVER = socket(AF_INET, SOCK_STREAM)
SERVER.bind(ADDR)

if __name__ == "__main__":
    SERVER.listen(5)
    print("Menunggu koneksi...")
    ACCEPT_THREAD = Thread(target=accept_incoming_connections)
    ACCEPT_THREAD.start()
    ACCEPT_THREAD.join()
    SERVER.close()
