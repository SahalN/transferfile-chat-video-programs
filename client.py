
import socket
import threading
import pickle
import struct
import tkinter as tk
from tkinter import filedialog, scrolledtext
from PIL import Image, ImageTk
import cv2
import time
import os

# Buat folder untuk file yang diterima
os.makedirs("downloads", exist_ok=True)

root = tk.Tk()
root.title("💬 Client Streaming")

# === UI SETUP ===
join_frame = tk.Frame(root, padx=10, pady=10)
join_frame.pack()

tk.Label(join_frame, text="Nama:").grid(row=0, column=0)
name_entry = tk.Entry(join_frame)
name_entry.grid(row=0, column=1)

tk.Label(join_frame, text="Host IP:").grid(row=1, column=0)
ip_entry = tk.Entry(join_frame)
ip_entry.grid(row=1, column=1)

connect_btn = tk.Button(join_frame, text="Gabung", width=20)
connect_btn.grid(row=2, column=0, columnspan=2, pady=10)

main_frame = tk.Frame(root)

# Chat (kiri)
left_frame = tk.Frame(main_frame)
left_frame.pack(side=tk.LEFT, fill=tk.Y)

viewer_label = tk.Label(left_frame, text="👁 0 penonton", font=("Arial", 10))
viewer_label.pack(anchor="w")

chat_box = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD, state=tk.DISABLED, width=40, height=20)
chat_box.pack(padx=5, pady=5)

msg_entry = tk.Entry(left_frame)
msg_entry.pack(padx=5, pady=(0, 5), fill=tk.X)

send_btn = tk.Button(left_frame, text="Kirim")
send_btn.pack(padx=5, pady=(0, 5), fill=tk.X)

file_btn = tk.Button(left_frame, text="📁 close stream")
file_btn.pack(padx=5, pady=(0, 10), fill=tk.X)

# Video (kanan)
canvas = tk.Canvas(main_frame, width=320, height=240)
canvas.pack(side=tk.RIGHT, padx=10, pady=10)

# === GLOBAL VARIABEL ===
client_socket = None
payload_size = struct.calcsize("Q")
data_buffer = b""
username = ""
canvas_image = None
last_time = time.time()

# === LOGIKA ===

def receive_data():
    global data_buffer
    while True:
        try:
            while len(data_buffer) < payload_size:
                packet = client_socket.recv(4096)
                if not packet:
                    return
                data_buffer += packet

            packed_size = data_buffer[:payload_size]
            data_buffer = data_buffer[payload_size:]
            msg_size = struct.unpack("Q", packed_size)[0]

            while len(data_buffer) < msg_size:
                data_buffer += client_socket.recv(4096)

            msg_data = data_buffer[:msg_size]
            data_buffer = data_buffer[msg_size:]

            message = pickle.loads(msg_data)

            if message["type"] == "frame":
                show_video(message["frame"])
            elif message["type"] == "chat" or message["type"] == "info":
                show_chat(message)
            elif message["type"] == "file":
                receive_file(message)

        except Exception as e:
            print("❌ Error receiving data:", e)
            break

def show_video(frame):
    global canvas_image, last_time
    now = time.time()
    fps = 1 / (now - last_time)
    last_time = now

    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(img).resize((320, 240))
    imgtk = ImageTk.PhotoImage(image=img)

    if canvas_image is None:
        canvas_image = canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
    else:
        canvas.itemconfig(canvas_image, image=imgtk)

    canvas.imgtk = imgtk

def show_chat(data):
    chat_box.config(state=tk.NORMAL)
    viewer_label.config(text=f"👁 {data.get('viewers', 0)} penonton")

    if data["type"] == "chat":
        chat_box.insert(tk.END, f"{data['from']}: {data['message']}\n")
    elif data["type"] == "info":
        if data.get("message", "").strip():
            chat_box.insert(tk.END, f"{data['message']}\n")

    chat_box.yview(tk.END)
    chat_box.config(state=tk.DISABLED)

def receive_file(data):
    filename = data.get("filename", "unknown_file")
    filedata = data.get("data")
    save_path = os.path.join("downloads", filename)

    with open(save_path, "wb") as f:
        f.write(filedata)

    show_chat({
        "type": "info",
        "message": f"📥 File diterima: {filename} disimpan ke downloads/",
        "viewers": 0
    })

def send_message():
    msg = msg_entry.get().strip()
    if msg:
        data = {"type": "chat", "message": msg}
        serialized = pickle.dumps(data)
        try:
            client_socket.sendall(struct.pack("Q", len(serialized)) + serialized)

            show_chat({
                "type": "chat",
                "from": username,
                "message": msg,
                "viewers": int(viewer_label.cget("text").split()[1])
            })
        except Exception as e:
            print("❌ Gagal mengirim pesan:", e)
        msg_entry.delete(0, tk.END)

def send_file():
    filepath = filedialog.askopenfilename()
    if filepath:
        filename = os.path.basename(filepath)
        with open(filepath, "rb") as f:
            filedata = f.read()
        data = {
            "type": "file",
            "filename": filename,
            "data": filedata
        }
        serialized = pickle.dumps(data)
        try:
            client_socket.sendall(struct.pack("Q", len(serialized)) + serialized)
            show_chat({
                "type": "info",
                "message": f"📤 Anda mengirim file: {filename}",
                "viewers": 0
            })
        except Exception as e:
            print("❌ Gagal mengirim file:", e)

def start_client():
    global client_socket, username
    username = name_entry.get().strip()
    ip = ip_entry.get().strip()
    if not username or not ip:
        return
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((ip, 9999))
        client_socket.send(f"{username}|sender".encode("utf-8"))
        threading.Thread(target=receive_data, daemon=True).start()
        join_frame.pack_forget()
        main_frame.pack(fill=tk.BOTH, expand=True)
    except Exception as e:
        print("❌ Gagal terhubung:", e)

# === EVENT HANDLER ===
connect_btn.config(command=start_client)
send_btn.config(command=send_message)
file_btn.config(command=send_file)
msg_entry.bind("<Return>", lambda e: send_message())

# === START APLIKASI ===
root.mainloop()
