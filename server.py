import socket
import threading
import pickle
import struct
import cv2
import os
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, scrolledtext

# --- Server config ---
HOST = socket.gethostbyname(socket.gethostname())
PORT = 9999
clients = []
client_names = {}
lock = threading.Lock()

os.makedirs("upload", exist_ok=True)

# --- GUI setup ---
root = tk.Tk()
root.title(f"📡 Server GUI ({HOST}:{PORT})")

left_frame = tk.Frame(root)
left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

viewer_label = tk.Label(left_frame, text="👁 0 penonton", font=("Arial", 10))
viewer_label.pack(anchor="w")

chat_box = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD, state=tk.DISABLED, width=40, height=20)
chat_box.pack(pady=5)

msg_entry = tk.Entry(left_frame)
msg_entry.pack(padx=5, pady=(0, 5), fill=tk.X)

send_btn = tk.Button(left_frame, text="Kirim", command=lambda: send_message_from_server())
send_btn.pack(padx=5, pady=(0, 5), fill=tk.X)

upload_btn = tk.Button(left_frame, text="Upload File", command=lambda: send_file_from_server())
upload_btn.pack(padx=5, pady=(0, 10), fill=tk.X)

video_frame = tk.Label(root)
video_frame.pack(side=tk.RIGHT, padx=10, pady=10)

cap = cv2.VideoCapture(0)

def update_video():
    success, frame = cap.read()
    if success:
        frame_resized = cv2.resize(frame, (320, 240))
        send_to_clients({"type": "frame", "frame": frame_resized})

        img = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        imgtk = ImageTk.PhotoImage(image=img)
        video_frame.imgtk = imgtk
        video_frame.configure(image=imgtk)

    root.after(30, update_video)

def log_chat(msg):
    chat_box.config(state=tk.NORMAL)
    chat_box.insert(tk.END, msg + "\n")
    chat_box.yview(tk.END)
    chat_box.config(state=tk.DISABLED)

def send_message_from_server():
    msg = msg_entry.get().strip()
    if msg:
        msg_entry.delete(0, tk.END)
        data = {"type": "chat", "from": "SERVER", "message": msg, "viewers": len(clients)}
        log_chat(f"SERVER: {msg}")
        send_to_clients(data)

def send_file_from_server():
    filepath = filedialog.askopenfilename()
    if filepath:
        filename = os.path.basename(filepath)
        with open(filepath, "rb") as f:
            filedata = f.read()
        data = {"type": "file", "filename": filename, "data": filedata}
        log_chat(f"📁 SERVER mengirim file: {filename}")
        send_to_clients(data)

def send_to_clients(data, except_sock=None):
    with lock:
        for c in clients.copy():
            if c != except_sock:
                try:
                    pkt = pickle.dumps(data)
                    c.sendall(struct.pack("Q", len(pkt)) + pkt)
                except:
                    clients.remove(c)

def update_viewer_count():
    with lock:
        viewers = len(clients)
    viewer_label.config(text=f"👁 {viewers} penonton")
    info = {"type": "info", "message": "", "viewers": viewers}
    send_to_clients(info)

def handle_client(conn, addr):
    try:
        name = conn.recv(1024).decode("utf-8")
        with lock:
            client_names[conn] = name
            clients.append(conn)

        msg = f"🟢 {name} telah bergabung!"
        log_chat(msg)
        send_to_clients({"type": "info", "message": msg, "viewers": len(clients)})
        update_viewer_count()

        while True:
            header = conn.recv(8)
            if not header:
                break
            msg_size = struct.unpack("Q", header)[0]
            data = b""
            while len(data) < msg_size:
                data += conn.recv(4096)
            message = pickle.loads(data)

            if message["type"] == "chat":
                chat_data = {
                    "type": "chat",
                    "from": name,
                    "message": message["message"],
                    "viewers": len(clients)
                }
                log_chat(f"{name}: {message['message']}")
                send_to_clients(chat_data, except_sock=conn)

            elif message["type"] == "file":
                filename = message["filename"]
                filedata = message["data"]
                filepath = os.path.join("upload", filename)
                with open(filepath, "wb") as f:
                    f.write(filedata)
                log_chat(f"📁 File '{filename}' diterima dari {name}")
                send_to_clients({
                    "type": "info",
                    "message": f"📁 {name} mengirim file: {filename}",
                    "viewers": len(clients)
                }, except_sock=conn)
    finally:
        with lock:
            clients.remove(conn)
            left_name = client_names.pop(conn, "Unknown")
        log_chat(f"🔴 {left_name} keluar.")
        send_to_clients({"type": "info", "message": f"🔴 {left_name} keluar.", "viewers": len(clients)})
        update_viewer_count()
        conn.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    log_chat(f"✅ Server berjalan di {HOST}:{PORT}")

    def accept_loop():
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

    threading.Thread(target=accept_loop, daemon=True).start()

update_video()
start_server()
root.mainloop()
