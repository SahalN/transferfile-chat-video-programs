import socket
import threading

import cv2
import pickle
import struct
import pyaudio

# Server socket setup
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_ip = socket.gethostbyname(socket.gethostname())  # Dapatkan IP host
port = 10050
server_socket.bind((host_ip, port))
server_socket.listen(5)

print(f'Server listening on {host_ip}:{port}...')

# Audio setup
p = pyaudio.PyAudio()
audio_stream = p.open(format=pyaudio.paInt16,
                     channels=1,
                     rate=44100,
                     input=True,
                     frames_per_buffer=1024)

clients = []  # Daftar untuk menyimpan client yang terhubung

# Fungsi untuk mengirim video + audio ke semua client
def send_to_clients(frame_data, audio_data):
    for client_socket in clients:
        try:
            # Gabungkan data video dan audio
            combined_data = frame_data + audio_data
            client_socket.sendall(combined_data)
        except:
            pass  # Jika client terputus, lanjutkan ke client berikutnya

# Fungsi untuk menangani client
def handle_client(client_socket):
    while True:
        try:
            # Ambil video frame dari webcam
            vid = cv2.VideoCapture(0)
            while vid.isOpened():
                img, frame = vid.read()
                if not img:
                    break

                # Serialize frame video
                frame_data = pickle.dumps(frame)
                message = struct.pack("Q", len(frame_data)) + frame_data

                # Ambil audio data
                audio_data = audio_stream.read(1024)

                # Kirimkan video + audio ke client
                send_to_clients(message, audio_data)

                cv2.imshow('Sending Video...', frame)

                if cv2.waitKey(1) == 13:  # Tekan Enter untuk berhenti
                    break

            vid.release()
            cv2.destroyAllWindows()
        except Exception as e:
            print(f"Error: {e}")
            break
    client_socket.close()

# Main server loop
while True:
    client_socket, addr = server_socket.accept()
    print(f"Client {addr} connected")
    clients.append(client_socket)
    # Jalankan thread untuk setiap client
    threading.Thread(target=handle_client, args=(client_socket,), daemon=True).start()
