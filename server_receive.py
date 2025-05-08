import socket
import tqdm
import os
from threading import Thread

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5001
BUFFER_SIZE = 4096
SEPARATOR = "<SEPARATOR>"
RECEIVED_DIR = "received_files"

# Membuat folder jika belum ada
os.makedirs(RECEIVED_DIR, exist_ok=True)

# Membuat TCP socket
server_socket = socket.socket()
server_socket.bind((SERVER_HOST, SERVER_PORT))
server_socket.listen(5)
print(f"[*] Listening as {SERVER_HOST}:{SERVER_PORT}")

def handle_client(client_socket, address):
    print(f"[+] {address} connected.")

    try:
        # terima info file: nama dan ukuran
        received = client_socket.recv(BUFFER_SIZE).decode()
        filename, filesize = received.split(SEPARATOR)
        filename = os.path.basename(filename)
        filesize = int(filesize)

        # Path penyimpanan file di dalam folder 'received_files'
        filepath = os.path.join(RECEIVED_DIR, f"received_{address[1]}_{filename}")

        # Simpan file
        progress = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True)
        with open(filepath, "wb") as f:
            while True:
                bytes_read = client_socket.recv(BUFFER_SIZE)
                if not bytes_read:
                    break
                f.write(bytes_read)
                progress.update(len(bytes_read))

        print(f"[✓] File dari {address} berhasil diterima dan disimpan di {filepath}")
    except Exception as e:
        print(f"[ERROR] Gagal menerima dari {address}: {e}")
    finally:
        client_socket.close()

# Terima koneksi terus-menerus
while True:
    client_socket, address = server_socket.accept()
    thread = Thread(target=handle_client, args=(client_socket, address))
    thread.start()
