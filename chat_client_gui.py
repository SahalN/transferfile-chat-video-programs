import tkinter as tk
from tkinter import filedialog, messagebox
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import os

BUFSIZ = 1024
FILE_SERVER_HOST = '127.0.0.1'
FILE_SERVER_PORT = 5001
SEPARATOR = "<SEPARATOR>"

class ChatClientApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Login Chat Client")
        self.master.geometry("800x600")
        self.master.configure(bg="#f0f4f7")

        self.username = tk.StringVar()
        self.password = tk.StringVar()

        # Frame Login
        self.login_frame = tk.Frame(master, bg="#f0f4f7")
        self.login_frame.pack(pady=50)

        tk.Label(self.login_frame, text="Username:", bg="#f0f4f7").grid(row=0, column=0, sticky="e")
        tk.Entry(self.login_frame, textvariable=self.username).grid(row=0, column=1)

        tk.Label(self.login_frame, text="Password:", bg="#f0f4f7").grid(row=1, column=0, sticky="e")
        tk.Entry(self.login_frame, textvariable=self.password, show="*").grid(row=1, column=1)

        tk.Button(self.login_frame, text="Login", bg="#0066cc", fg="white", command=self.connect_to_chat).grid(row=2, columnspan=2, pady=20)

    def connect_to_chat(self):
        if self.username.get() and self.password.get():
            try:
                self.client_socket = socket(AF_INET, SOCK_STREAM)
                self.client_socket.connect(('127.0.0.1', 33000))
                self.client_socket.send(self.username.get().encode("utf8"))

                self.open_chat_window()
                receive_thread = Thread(target=self.receive)
                receive_thread.start()
            except Exception as e:
                messagebox.showerror("Error", f"Gagal terhubung ke server: {e}")
        else:
            messagebox.showwarning("Login Gagal", "Username dan password wajib diisi.")

    def open_chat_window(self):
        self.login_frame.destroy()
        self.master.geometry("800x600")
        self.master.title(f"Chat Room - {self.username.get()}")

        # Frame Kiri untuk daftar User Online
        self.user_frame = tk.Frame(self.master, width=200, bg="#d9e5f5")
        self.user_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 5))

        self.user_list_label = tk.Label(self.user_frame, text="User Online", font=("Arial", 14), bg="#d9e5f5")
        self.user_list_label.pack(pady=10)

        self.user_listbox = tk.Listbox(self.user_frame, height=20, width=25)
        self.user_listbox.pack(fill=tk.Y)

        # Frame untuk Chat
        self.chat_frame = tk.Frame(self.master, bg="#e6f2ff")
        self.chat_frame.pack(expand=True, fill=tk.BOTH, side=tk.LEFT)

        self.text_frame = tk.Frame(self.chat_frame)
        self.scrollbar = tk.Scrollbar(self.text_frame)
        self.msg_list = tk.Listbox(self.text_frame, height=25, width=100, yscrollcommand=self.scrollbar.set, bg="white")
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.msg_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.text_frame.pack(pady=10)

        self.my_msg = tk.StringVar()
        self.entry_field = tk.Entry(self.chat_frame, textvariable=self.my_msg, width=70)
        self.entry_field.bind("<Return>", self.send)
        self.entry_field.pack(side=tk.LEFT, padx=(10, 0), pady=(0, 10))

        self.send_button = tk.Button(self.chat_frame, text="Kirim", command=self.send, bg="#4CAF50", fg="white")
        self.send_button.pack(side=tk.LEFT, padx=5, pady=(0, 10))

        self.upload_button = tk.Button(self.chat_frame, text="Upload File", command=self.upload_file, bg="#2196F3", fg="white")
        self.upload_button.pack(side=tk.LEFT, padx=5, pady=(0, 10))

        self.quit_button = tk.Button(self.chat_frame, text="Keluar", command=self.quit_chat, bg="#f44336", fg="white")
        self.quit_button.pack(side=tk.LEFT, padx=5, pady=(0, 10))


        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def receive(self):
        while True:
            try:
                msg = self.client_socket.recv(BUFSIZ).decode("utf8")
                if msg == "{quit}":
                    self.client_socket.close()
                    break
                elif msg.startswith("[USER ONLINE]:"):
                    self.update_user_list(msg)
                else:
                    self.msg_list.insert(tk.END, msg)
            except OSError:
                break

    def update_user_list(self, msg):
        # Ambil daftar user online dan tampilkan di Listbox
        user_list = msg.replace("[USER ONLINE]:", "").strip().split(", ")
        self.user_listbox.delete(0, tk.END)
        for user in user_list:
            self.user_listbox.insert(tk.END, user)

    def send(self, event=None):
        msg = self.my_msg.get()
        self.my_msg.set("")
        self.client_socket.send(bytes(msg, "utf8"))
        if msg == "{quit}":
            self.client_socket.close()
            self.master.quit()

    def upload_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            try:
                filename = os.path.basename(file_path)
                filesize = os.path.getsize(file_path)
                s = socket(AF_INET, SOCK_STREAM)
                s.connect((FILE_SERVER_HOST, FILE_SERVER_PORT))
                s.send(f"{filename}{SEPARATOR}{filesize}".encode())

                with open(file_path, "rb") as f:
                    while True:
                        bytes_read = f.read(BUFSIZ)
                        if not bytes_read:
                            break
                        s.sendall(bytes_read)
                s.close()

                # Broadcast ke semua client bahwa ada file
                self.client_socket.send(f"[FILE]:{filename}".encode("utf8"))
            except Exception as e:
                messagebox.showerror("Upload Gagal", f"Gagal mengirim file: {e}")

    def on_closing(self, event=None):
        self.quit_chat()

    def quit_chat(self):
        """Dipanggil saat tombol 'Keluar' ditekan."""
        self.my_msg.set("{quit}")
        self.send()
        self.master.quit()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClientApp(root)
    root.mainloop()
