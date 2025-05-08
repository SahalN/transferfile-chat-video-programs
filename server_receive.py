import socket
import tqdm
import os
from threading import Thread

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5001
BUFFER_SIZE = 4096
SEPARATOR = "<SEPARATOR>"

# Direktori khusus untuk menyimpan file
SAVE_DIR = "server_uploads"
os.makedirs(SAVE_DIR, exist_ok=True)

# Membuat TCP socket
server_socket = socket.socket()
server_socket.bind((SERVER_HOST, SERVER_PORT))
server_socket.listen(5)
print(f"[*] Listening as {SERVER_HOST}:{SERVER_PORT}")

def handle_client(client_socket, address):
    print(f"[+] {address} connected.")

    try:
        # Terima info file
        received = client_socket.recv(BUFFER_SIZE).decode()
        filename, filesize = received.split(SEPARATOR)
        filename = os.path.basename(filename)
        filesize = int(filesize)

        # Path lengkap ke direktori penyimpanan
        save_path = os.path.join(SAVE_DIR, f"received_{address[1]}_{filename}")

        # Simpan file ke folder
        progress = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True)
        with open(save_path, "wb") as f:
            while True:
                bytes_read = client_socket.recv(BUFFER_SIZE)
                if not bytes_read:
                    break
                f.write(bytes_read)
                progress.update(len(bytes_read))

        print(f"[✓] File dari {address} berhasil disimpan di: {save_path}")
    except Exception as e:
        print(f"[ERROR] Gagal menerima dari {address}: {e}")
    finally:
        client_socket.close()

# Terima koneksi terus-menerus
while True:
    client_socket, address = server_socket.accept()
    thread = Thread(target=handle_client, args=(client_socket, address))
    thread.start()
