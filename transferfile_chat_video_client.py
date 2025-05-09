import socket, pickle, struct, threading, os, sys, subprocess, time
import tkinter as tk
from tkinter import scrolledtext, filedialog
from PIL import Image, ImageTk
import cv2
# Warna tema
BG_COLOR = "#1e1e2f"
TEXT_COLOR = "#ffffff"
ENTRY_BG = "#2e2e3e"
BUTTON_BG = "#44475a"
BUTTON_FG = "#ffffff"
CHAT_BG = "#282a36"
VIDEO_BG = "#383a4c"

# GUI
root = tk.Tk()
root.title("💬 Client Streaming")
root.configure(bg=BG_COLOR)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ========== UI ==========

# Frame join
join_frame = tk.Frame(root, bg=BG_COLOR)
join_frame.pack(pady=10)
tk.Label(join_frame, text="Nama:", bg=BG_COLOR, fg=TEXT_COLOR).grid(row=0, column=0)
name_entry = tk.Entry(join_frame, bg=ENTRY_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
name_entry.grid(row=0, column=1)
tk.Label(join_frame, text="IP Server:", bg=BG_COLOR, fg=TEXT_COLOR).grid(row=1, column=0)
ip_entry = tk.Entry(join_frame, bg=ENTRY_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
ip_entry.grid(row=1, column=1)
connect_btn = tk.Button(join_frame, text="Gabung", bg=BUTTON_BG, fg=BUTTON_FG)
connect_btn.grid(row=2, column=0, columnspan=2, pady=10)

# Main Frame
main_frame = tk.Frame(root, bg=BG_COLOR)


# Chat Area
left_frame = tk.Frame(main_frame, bg=BG_COLOR)
left_frame.pack(side=tk.LEFT, fill=tk.Y)
viewer_label = tk.Label(left_frame, text="👁 0 penonton", bg=BG_COLOR, fg="#00ff99")
viewer_label.pack(anchor="w")
chat_box = scrolledtext.ScrolledText(left_frame, bg=CHAT_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, width=40, height=20)
chat_box.pack(padx=5, pady=5)
msg_entry = tk.Entry(left_frame, bg=ENTRY_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
msg_entry.pack(padx=5, pady=(0, 5), fill=tk.X)
send_btn = tk.Button(left_frame, text="Kirim", bg=BUTTON_BG, fg=BUTTON_FG)
send_btn.pack(padx=5, pady=(0, 5), fill=tk.X)
file_btn = tk.Button(left_frame, text="Transfer File", bg=BUTTON_BG, fg=BUTTON_FG)
file_btn.pack(padx=5, pady=(0, 10), fill=tk.X)

# Video Canvas
canvas = tk.Canvas(main_frame, width=320, height=240, bg="#383a4c")
canvas.pack(side=tk.RIGHT, padx=10, pady=10)

# Right panel (video)
video_frame = tk.Label(root, bg=VIDEO_BG)  # Tambahkan warna latar belakang di sini
video_frame.pack(side=tk.RIGHT, padx=10, pady=10)


# ========== GLOBAL VARS ==========
client_socket = None
payload_size = struct.calcsize("Q")
data_buffer = b""
username = ""
canvas_image = None
last_time = time.time()

# ========== FUNCTIONALITAS ==========

def show_chat(data):
    chat_box.config(state=tk.NORMAL)
    if data["type"] == "chat":
        chat_box.insert(tk.END, f"{data['from']}: {data['message']}\n")
    elif data["type"] == "info":
        chat_box.insert(tk.END, f"[INFO] {data['message']}\n")
    elif data["type"] == "file":
        filename = data["filename"]
        path = os.path.join(DOWNLOAD_DIR, filename)
        with open(path, "wb") as f:
            f.write(data["content"])
        chat_box.insert(tk.END, f"{data.get('from', 'Anonim')} mengirim file: {filename}\n")
    chat_box.yview(tk.END)
    chat_box.config(state=tk.DISABLED)

def show_video(frame):
    global canvas_image, last_time
    img = ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).resize((320, 240)))
    if canvas_image is None:
        canvas_image = canvas.create_image(0, 0, anchor=tk.NW, image=img)
    else:
        canvas.itemconfig(canvas_image, image=img)
    canvas.imgtk = img

def receive_data():
    global data_buffer
    while True:
        try:
            while len(data_buffer) < payload_size:
                data_buffer += client_socket.recv(4096)
            packed_msg_size = data_buffer[:payload_size]
            data_buffer = data_buffer[payload_size:]
            msg_size = struct.unpack("Q", packed_msg_size)[0]
            while len(data_buffer) < msg_size:
                data_buffer += client_socket.recv(4096)
            msg_data = data_buffer[:msg_size]
            data_buffer = data_buffer[msg_size:]
            message = pickle.loads(msg_data)

            if message["type"] == "frame":
                show_video(message["frame"])
            else:
                show_chat(message)

        except Exception as e:
            print(f"[!] Error receiving: {e}")
            break

def send_message(event=None):
    msg = msg_entry.get().strip()
    if not msg: return
    data = {"type": "chat", "message": msg}
    client_socket.sendall(struct.pack("Q", len(pickle.dumps(data))) + pickle.dumps(data))
    show_chat({"type": "chat", "from": username, "message": msg})
    msg_entry.delete(0, tk.END)

def send_file():
    filepath = filedialog.askopenfilename()
    if filepath:
        with open(filepath, "rb") as f:
            file_data = f.read()
        filename = os.path.basename(filepath)
        data = {"type": "file", "filename": filename, "content": file_data}
        client_socket.sendall(struct.pack("Q", len(pickle.dumps(data))) + pickle.dumps(data))
        show_chat({"type": "chat", "from": username, "message": f"📎 Mengirim file: {filename}"})

def start_client():
    global client_socket, username
    username = name_entry.get().strip()
    ip = ip_entry.get().strip()
    if not username or not ip:
        print("[!] Nama/IP tidak boleh kosong.")
        return
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((ip, 9999))
        client_socket.send(username.encode("utf-8"))
        threading.Thread(target=receive_data, daemon=True).start()
        join_frame.pack_forget()
        main_frame.pack(fill=tk.BOTH, expand=True)
    except Exception as e:
        print(f"[!] Gagal konek: {e}")

# ========== BINDING ==========
connect_btn.config(command=start_client)
send_btn.config(command=send_message)
file_btn.config(command=send_file)
msg_entry.bind("<Return>", send_message)

# ========== START ==========
root.mainloop()
