import tkinter as tk
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import os

def receive():
    while True:
        try:
            msg = client_socket.recv(BUFSIZ).decode("utf8")
            msg_list.insert(tk.END, msg)
        except OSError:
            break

def send(event=None):
    msg = my_msg.get()
    my_msg.set("")
    client_socket.send(bytes(msg, "utf8"))
    if msg == "{quit}":
        client_socket.close()
        top.quit()

def on_closing(event=None):
    my_msg.set("{quit}")
    send()

def login():
    global client_socket, BUFSIZ
    username = entry_username.get()
    password = entry_password.get()

    if not username or not password:
        return

    try:
        client_socket = socket(AF_INET, SOCK_STREAM)
        client_socket.connect((entry_host.get(), int(entry_port.get())))
        BUFSIZ = 1024
        client_socket.send(bytes(username, "utf8"))
        Thread(target=receive).start()
        login_frame.pack_forget()
        chat_frame.pack()
        top.title(f"Chat - {username}")
    except Exception as e:
        print("Gagal koneksi:", e)

def upload_file():
    from tkinter import filedialog
    import socket

    filepath = filedialog.askopenfilename()
    if filepath:
        SEPARATOR = "<SEPARATOR>"
        BUFFER_SIZE = 4096
        filesize = os.path.getsize(filepath)

        s = socket.socket()
        s.connect(("127.0.0.1", 5001))
        s.send(f"{filepath}{SEPARATOR}{filesize}".encode())

        with open(filepath, "rb") as f:
            while True:
                bytes_read = f.read(BUFFER_SIZE)
                if not bytes_read:
                    break
                s.sendall(bytes_read)
        s.close()

top = tk.Tk()
top.title("Login ke Chat")
top.geometry("500x400")
top.configure(bg="#f0f0f5")

# ======= LOGIN FRAME =======
login_frame = tk.Frame(top, bg="#f0f0f5")
tk.Label(login_frame, text="HOST:").pack()
entry_host = tk.Entry(login_frame)
entry_host.insert(0, "127.0.0.1")
entry_host.pack()

tk.Label(login_frame, text="PORT:").pack()
entry_port = tk.Entry(login_frame)
entry_port.insert(0, "33000")
entry_port.pack()

tk.Label(login_frame, text="Username:").pack()
entry_username = tk.Entry(login_frame)
entry_username.pack()

tk.Label(login_frame, text="Password:").pack()
entry_password = tk.Entry(login_frame, show="*")
entry_password.pack()

tk.Button(login_frame, text="Login", command=login, bg="#4CAF50", fg="white").pack(pady=10)
login_frame.pack(pady=40)

# ======= CHAT FRAME =======
chat_frame = tk.Frame(top, bg="#ffffff")
messages_frame = tk.Frame(chat_frame)
my_msg = tk.StringVar()
my_msg.set("")

scrollbar = tk.Scrollbar(messages_frame)
msg_list = tk.Listbox(messages_frame, height=15, width=70, yscrollcommand=scrollbar.set)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
msg_list.pack(side=tk.LEFT, fill=tk.BOTH)
msg_list.pack()
messages_frame.pack()

entry_field = tk.Entry(chat_frame, textvariable=my_msg, width=50)
entry_field.bind("<Return>", send)
entry_field.pack()

send_button = tk.Button(chat_frame, text="Kirim", command=send, bg="#2196F3", fg="white")
send_button.pack(pady=5)

upload_button = tk.Button(chat_frame, text="Upload File", command=upload_file, bg="#FF9800", fg="white")
upload_button.pack(pady=5)

top.protocol("WM_DELETE_WINDOW", on_closing)
top.mainloop()
