import socket
import cv2
import pickle
import struct
import pyaudio
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import threading

# Fungsi untuk memutar audio
def play_audio(audio_data, mute=False):
    if mute:
        return  # Jangan memainkan audio jika mute
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=44100,
                    output=True,
                    frames_per_buffer=1024)
    stream.write(audio_data)
    stream.stop_stream()
    stream.close()
    p.terminate()

# Fungsi untuk membuat GUI
def create_gui():
    # Membuat root window
    root = tk.Tk()
    root.title("Client - Video Streaming")

    # Menampilkan label video
    video_label = tk.Label(root, text="Video Stream", font=("Arial", 16))
    video_label.pack(pady=10)

    # Frame untuk menampilkan video
    video_frame = tk.Label(root)
    video_frame.pack(padx=10, pady=10)

    # Tombol untuk menghentikan video streaming
    stop_button = tk.Button(root, text="Stop Streaming", command=root.quit)
    stop_button.pack(pady=20)

    # Tombol untuk mute/unmute audio
    mute_button = tk.Button(root, text="Mute Audio", command=lambda: toggle_mute(mute_button))
    mute_button.pack(pady=10)

    return root, video_frame, mute_button

# Fungsi untuk toggle mute/unmute
def toggle_mute(mute_button):
    global mute_status
    mute_status = not mute_status
    if mute_status:
        mute_button.config(text="Unmute Audio")
    else:
        mute_button.config(text="Mute Audio")

# Fungsi untuk menerima dan menampilkan video/audio
def receive_data(client_socket, video_frame):
    data = b""
    payload_size = struct.calcsize("Q")

    while True:
        while len(data) < payload_size:
            packet = client_socket.recv(4 * 1024)
            if not packet:
                break
            data += packet

        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack("Q", packed_msg_size)[0]

        while len(data) < msg_size:
            data += client_socket.recv(4 * 1024)

        frame_data = data[:msg_size]
        data = data[msg_size:]

        # Menampilkan frame video pada GUI
        frame = pickle.loads(frame_data)
        frame_resized = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_image = cv2.resize(frame_resized, (640, 480))  # Sesuaikan ukuran
        img = Image.fromarray(frame_image)
        img_tk = ImageTk.PhotoImage(image=img)
        video_frame.imgtk = img_tk
        video_frame.configure(image=img_tk)

        # Menambahkan audio (jika tersedia)
        audio_data = frame_data[-1024:]  # Ambil audio (pastikan ini sesuai dengan format pengiriman audio)
        play_audio(audio_data, mute=mute_status)

# Fungsi untuk menjalankan client socket dan menerima data
def start_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host_ip = '192.168.40.1'  # Alamat IP server
    port = 10050  # Port yang digunakan
    client_socket.connect((host_ip, port))

    # Setup GUI
    root, video_frame, mute_button = create_gui()

    # Status mute
    global mute_status
    mute_status = False

    # Menjalankan thread untuk menerima dan menampilkan data
    threading.Thread(target=receive_data, args=(client_socket, video_frame), daemon=True).start()

    # Menjalankan GUI
    root.mainloop()

# Jalankan client
start_client()
