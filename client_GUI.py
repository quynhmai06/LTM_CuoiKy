import socket
import tkinter as tk
from tkinter import font
from tkinter import ttk
from tkinter import filedialog
import time
import threading
import os
from datetime import datetime
from PIL import Image, ImageTk
import io
import base64

class RoundedText(tk.Canvas):
    def __init__(self, parent, **kwargs):
        tk.Canvas.__init__(self, parent, **kwargs)
        
class GUI:
    def __init__(self, ip_address, port):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.connect((ip_address, port))

        self.Window = tk.Tk()
        self.Window.withdraw()

        self.login = tk.Toplevel()
        self.login.title("UTH-CHAT")
        self.login.resizable(width=False, height=False)
        self.login.configure(width=480, height=650, bg="white")

        # Main container
        main_container = tk.Frame(self.login, bg="white")
        main_container.place(relx=0.5, rely=0.5, anchor="center", width=400, height=580)

        # Logo section với gradient green
        logo_section = tk.Frame(main_container, bg="white")
        logo_section.pack(pady=(20, 0))
        
        # Logo UTH - sử dụng text để tạo logo
        logo_frame = tk.Frame(logo_section, bg="white", width=280, height=100)
        logo_frame.pack()
        logo_frame.pack_propagate(False)
        
        # UTH text - màu xanh lá
        uth_label = tk.Label(logo_frame,
                            text="UTH",
                            font=("Arial", 50, "bold"),
                            bg="white",
                            fg="#145A49")
        uth_label.place(x=10, y=10)
        
        # UNIVERSITY text - màu đỏ
        uni_label = tk.Label(logo_frame,
                           text="UNIVERSITY",
                           font=("Arial", 11, "bold"),
                           bg="white",
                           fg="#E63946")
        uni_label.place(x=140, y=15)
        
        # OF TRANSPORT text - màu đỏ  
        of_label = tk.Label(logo_frame,
                          text="OF TRANSPORT",
                          font=("Arial", 11, "bold"),
                          bg="white",
                          fg="#E63946")
        of_label.place(x=140, y=35)
        
        # HOCHIMINH CITY text - màu đỏ
        hcm_label = tk.Label(logo_frame,
                           text="HOCHIMINH CITY",
                           font=("Arial", 11, "bold"),
                           bg="white",
                           fg="#E63946")
        hcm_label.place(x=140, y=55)

        # Brand name - UTH-CHAT
        brand_frame = tk.Frame(main_container, bg="white")
        brand_frame.pack(pady=(15, 5))
        
        brand_name = tk.Label(brand_frame,
                            text="UTH-CHAT",
                            font="Helvetica 28 bold",
                            bg="white",
                            fg="#0E6347")
        brand_name.pack()
        
        # Tagline
        tagline = tk.Label(main_container,
                         text="Kết nối - Chia sẻ - Trò chuyện",
                         font="Helvetica 11",
                         bg="white",
                         fg="#6B7280")
        tagline.pack(pady=(0, 35))

        # Form container với shadow effect (sử dụng frame lồng)
        shadow_frame = tk.Frame(main_container, bg="#E5E7EB")
        shadow_frame.pack(fill="x", padx=20)
        
        form_frame = tk.Frame(shadow_frame, bg="white")
        form_frame.pack(fill="x", padx=2, pady=2)

        # Username Input với icon
        user_container = tk.Frame(form_frame, bg="white")
        user_container.pack(fill="x", padx=20, pady=(25, 0))
        
        user_label = tk.Label(user_container,
                             text="👤  Tên người dùng",
                             font="Helvetica 10 bold",
                             bg="white",
                             fg="#0C5B41",
                             anchor="w")
        user_label.pack(fill="x", pady=(0, 8))
        
        user_input_frame = tk.Frame(user_container, bg="white", highlightbackground="#0C5B41", highlightthickness=2)
        user_input_frame.pack(fill="x")
        
        self.userEntryName = tk.Entry(user_input_frame,
                                      font="Helvetica 13",
                                      bg="white",
                                      fg="#1F2937",
                                      border=0,
                                      insertbackground="#0C5B41")
        self.userEntryName.pack(fill="x", padx=15, pady=12)
        self.userEntryName.insert(0, "Nhập tên của bạn...")
        self.userEntryName.config(fg="#9CA3AF")
        
        def on_user_focus_in(event):
            if self.userEntryName.get() == "Nhập tên của bạn...":
                self.userEntryName.delete(0, tk.END)
                self.userEntryName.config(fg="#1F2937")
            user_input_frame.config(highlightbackground="#0C5B41", highlightthickness=2)
        
        def on_user_focus_out(event):
            if not self.userEntryName.get():
                self.userEntryName.insert(0, "Nhập tên của bạn...")
                self.userEntryName.config(fg="#9CA3AF")
            user_input_frame.config(highlightbackground="#0C5B41", highlightthickness=2)
        
        self.userEntryName.bind("<FocusIn>", on_user_focus_in)
        self.userEntryName.bind("<FocusOut>", on_user_focus_out)
        self.userEntryName.focus()

        # Room ID Input với icon
        room_container = tk.Frame(form_frame, bg="white")
        room_container.pack(fill="x", padx=20, pady=(20, 25))
        
        room_label = tk.Label(room_container,
                            text="🚪  Room ID",
                            font="Helvetica 10 bold",
                            bg="white",
                            fg="#064934",
                            anchor="w")
        room_label.pack(fill="x", pady=(0, 8))

        room_input_frame = tk.Frame(room_container, bg="white", highlightbackground="#0C5B41", highlightthickness=2)
        room_input_frame.pack(fill="x")
        
        self.roomEntryName = tk.Entry(room_input_frame,
                                      font="Helvetica 13",
                                      bg="white",
                                      fg="#1F2937",
                                      border=0,
                                      insertbackground="#0C5B41")
        self.roomEntryName.pack(fill="x", padx=15, pady=12)
        self.roomEntryName.insert(0, "Nhập mã phòng...")
        self.roomEntryName.config(fg="#9CA3AF")
        
        def on_room_focus_in(event):
            if self.roomEntryName.get() == "Nhập mã phòng...":
                self.roomEntryName.delete(0, tk.END)
                self.roomEntryName.config(fg="#1F2937")
            room_input_frame.config(highlightbackground="#34D399", highlightthickness=2)
        
        def on_room_focus_out(event):
            if not self.roomEntryName.get():
                self.roomEntryName.insert(0, "Nhập mã phòng...")
                self.roomEntryName.config(fg="#9CA3AF")
            room_input_frame.config(highlightbackground="#0C5B41", highlightthickness=2)
        
        self.roomEntryName.bind("<FocusIn>", on_room_focus_in)
        self.roomEntryName.bind("<FocusOut>", on_room_focus_out)

        # Button container
        button_container = tk.Frame(main_container, bg="white")
        button_container.pack(fill="x", padx=20, pady=(20, 0))

        # Connect Button với gradient effect
        self.go = tk.Button(button_container,
                           text="KẾT NỐI NGAY ✨",
                           font="Helvetica 13 bold",
                           bg="#10B981",
                           fg="white",
                           border=0,
                           cursor="hand2",
                           activebackground="#059669",
                           activeforeground="white",
                           command=lambda: self.goAhead(
                               self.userEntryName.get() if self.userEntryName.get() != "Nhập tên của bạn..." else "",
                               self.roomEntryName.get() if self.roomEntryName.get() != "Nhập mã phòng..." else ""
                           ))
        self.go.pack(fill="x", ipady=14)
        
        def on_btn_enter(e):
            self.go.config(bg="#064934")
        
        def on_btn_leave(e):
            self.go.config(bg="#064934")
        
        self.go.bind("<Enter>", on_btn_enter)
        self.go.bind("<Leave>", on_btn_leave)
        
        # Bind Enter key
        self.roomEntryName.bind("<Return>", lambda e: self.go.invoke())

        # Info text
        info_frame = tk.Frame(main_container, bg="white")
        info_frame.pack(pady=(20, 10))
        
        info_text = tk.Label(info_frame,
                           text="💡 Tạo phòng mới hoặc tham gia phòng có sẵn",
                           font="Helvetica 9",
                           bg="white",
                           fg="#6B7280")
        info_text.pack()

        # Divider
        divider = tk.Frame(main_container, bg="#E5E7EB", height=1)
        divider.pack(fill="x", padx=40, pady=(15, 15))

        # Footer
        footer_text = tk.Label(main_container,
                             text="Powered by UTH Technology 🚀",
                             font="Helvetica 8",
                             bg="white",
                             fg="#9CA3AF")
        footer_text.pack()

        self.Window.mainloop()

    def goAhead(self, username, room_id=0):
        if not username or username == "Nhập tên của bạn...":
            return
            
        self.name = username
        self.server.send(str.encode(username))
        time.sleep(0.1)
        self.server.send(str.encode(room_id if room_id != "Nhập mã phòng..." else "0"))
        
        self.login.destroy()
        self.layout()

        rcv = threading.Thread(target=self.receive) 
        rcv.start()

    def layout(self):
        self.Window.deiconify()
        self.Window.title("💬 UTH-CHAT")
        self.Window.resizable(width=False, height=False)
        self.Window.configure(width=420, height=720, bg="#18191A")

        # Header bar
        header = tk.Frame(self.Window, bg="#242526", height=70)
        header.place(relwidth=1, relheight=0.09)

        # Avatar
        avatar = tk.Label(header,
                         text="👤",
                         bg="#242526",
                         fg="white",
                         font="Helvetica 18")
        avatar.place(relx=0.04, rely=0.5, anchor="w")

        # Name and status
        name_frame = tk.Frame(header, bg="#242526")
        name_frame.place(relx=0.15, rely=0.5, anchor="w")

        self.chatBoxHead = tk.Label(name_frame,
                                    bg="#242526",
                                    fg="white",
                                    text=self.name,
                                    font="Helvetica 12 bold",
                                    anchor="w")
        self.chatBoxHead.pack(anchor="w")

        # Status với dot xanh
        status_frame = tk.Frame(name_frame, bg="#242526")
        status_frame.pack(anchor="w")
        
        # Dot xanh online
        online_dot = tk.Label(status_frame,
                             text="●",
                             bg="#242526",
                             fg="#10B981",
                             font="Helvetica 6")
        online_dot.pack(side="left", padx=(0, 3))
        
        status_label = tk.Label(status_frame,
                               text="Đang online",
                               bg="#242526",
                               fg="#10B981",
                               font="Helvetica 8",
                               anchor="w")
        status_label.pack(side="left")

        # Header icons
        call_icon = tk.Label(header,
                            text="📞",
                            bg="#242526",
                            fg="#10B981",
                            font="Helvetica 16",
                            cursor="hand2")
        call_icon.place(relx=0.72, rely=0.5, anchor="center")

        video_icon = tk.Label(header,
                             text="🎥",
                             bg="#242526",
                             fg="#10B981",
                             font="Helvetica 16",
                             cursor="hand2")
        video_icon.place(relx=0.83, rely=0.5, anchor="center")

        minimize_icon = tk.Label(header,
                                text="─",
                                bg="#242526",
                                fg="#B0B3B8",
                                font="Helvetica 16 bold",
                                cursor="hand2")
        minimize_icon.place(relx=0.94, rely=0.5, anchor="center")

        # Chat area với Canvas để vẽ bubble
        chat_bg = tk.Frame(self.Window, bg="#18191A")
        chat_bg.place(relwidth=1, relheight=0.77, rely=0.09)

        # Canvas cho chat messages
        self.chat_canvas = tk.Canvas(chat_bg,
                                     bg="#18191A",
                                     highlightthickness=0)
        self.chat_canvas.place(relwidth=1, relheight=1)

        # Scrollbar
        scrollbar = tk.Scrollbar(chat_bg, 
                                command=self.chat_canvas.yview,
                                bg="#3A3B3C", 
                                troughcolor="#18191A")
        scrollbar.place(relheight=1, relx=0.97, relwidth=0.03)
        self.chat_canvas.config(yscrollcommand=scrollbar.set)

        # Frame bên trong canvas
        self.messages_frame = tk.Frame(self.chat_canvas, bg="#18191A")
        self.canvas_frame = self.chat_canvas.create_window((0, 0), 
                                                            window=self.messages_frame, 
                                                            anchor="nw",
                                                            width=400)

        # Update scrollregion khi frame thay đổi
        self.messages_frame.bind("<Configure>", 
                                lambda e: self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all")))

        # Bottom bar
        bottom_bar = tk.Frame(self.Window, bg="#242526")
        bottom_bar.place(relwidth=1, relheight=0.14, rely=0.86)

        # Action buttons row
        action_frame = tk.Frame(bottom_bar, bg="#242526")
        action_frame.place(relx=0, rely=0, relwidth=1, relheight=0.4)

        # Action buttons
        mic_btn = tk.Label(action_frame,
                          text="🎤",
                          bg="#242526",
                          fg="#10B981",
                          font="Helvetica 18",
                          cursor="hand2")
        mic_btn.place(relx=0.05, rely=0.5, anchor="w")

        self.browse = tk.Button(action_frame,
                               text="🖼️",
                               font="Helvetica 18",
                               bg="#242526",
                               fg="#10B981",
                               border=0,
                               cursor="hand2",
                               activebackground="#242526",
                               command=self.browseFile)
        self.browse.place(relx=0.18, rely=0.5, anchor="w")

        self.emoji_btn = tk.Button(action_frame,
                              text="😊",
                              bg="#242526",
                              fg="#10B981",
                              font="Helvetica 18",
                              border=0,
                              cursor="hand2",
                              activebackground="#242526",
                              command=self.show_emoji_picker)
        self.emoji_btn.place(relx=0.31, rely=0.5, anchor="w")

        gif_btn = tk.Label(action_frame,
                          text="GIF",
                          bg="#242526",
                          fg="#10B981",
                          font="Helvetica 10 bold",
                          cursor="hand2")
        gif_btn.place(relx=0.44, rely=0.5, anchor="w")

        # File status
        self.fileLocation = tk.Label(action_frame,
                                     text="",
                                     bg="#242526",
                                     fg="#8696A0",
                                     font="Helvetica 8",
                                     anchor="w")
        self.fileLocation.place(relx=0.58, rely=0.5, anchor="w")

        # Send file button
        self.sengFileBtn = tk.Button(action_frame,
                                     text="✓",
                                     font="Helvetica 14 bold",
                                     bg="#10B981",
                                     fg="white",
                                     border=0,
                                     cursor="hand2",
                                     activebackground="#059669",
                                     command=self.sendFile)

        # Message input
        input_frame = tk.Frame(bottom_bar, bg="#3A3B3C")
        input_frame.place(relx=0.03, rely=0.45, relwidth=0.78, relheight=0.5)

        self.entryMsg = tk.Entry(input_frame,
                                bg="#3A3B3C",
                                fg="#E4E6EB",
                                font="Helvetica 11",
                                border=0,
                                insertbackground="#10B981")
        self.entryMsg.place(relwidth=0.85, relheight=1, relx=0.04, rely=0)
        self.entryMsg.focus()
        self.entryMsg.bind("<Return>", lambda e: self.sendButton(self.entryMsg.get()))

        # Emoji in input - có thể click
        emoji_input_btn = tk.Button(input_frame,
                            text="😊",
                            bg="#3A3B3C",
                            fg="#10B981",
                            font="Helvetica 16",
                            border=0,
                            cursor="hand2",
                            activebackground="#3A3B3C",
                            command=self.show_emoji_picker)
        emoji_input_btn.place(relx=0.92, rely=0.5, anchor="center")

        # Send button (Like icon)
        self.buttonMsg = tk.Button(bottom_bar,
                                   text="👍",
                                   font="Helvetica 22",
                                   bg="#242526",
                                   fg="#10B981",
                                   border=0,
                                   cursor="hand2",
                                   activebackground="#242526",
                                   command=self.sendLike)
        self.buttonMsg.place(relx=0.85, rely=0.7, relheight=0.3, relwidth=0.13, anchor="w")

    def add_message(self, text, is_sent=True, sender_name=None, image_data=None):
        """Thêm tin nhắn vào chat với bubble tròn"""
        msg_container = tk.Frame(self.messages_frame, bg="#18191A")
        msg_container.pack(fill="x", pady=5, padx=10)
        
        # Lấy thời gian hiện tại
        current_time = datetime.now().strftime("%H:%M")
        
        if is_sent:
            # Tin nhắn gửi - bên phải, xanh lá
            bubble_frame = tk.Frame(msg_container, bg="#18191A")
            bubble_frame.pack(side="right")
            
            # Container cho bubble và thời gian
            content_frame = tk.Frame(bubble_frame, bg="#18191A")
            content_frame.pack(side="right")
            
            if image_data:
                # Hiển thị ảnh
                try:
                    img = Image.open(io.BytesIO(image_data))
                    # Resize ảnh nếu quá lớn
                    max_size = (250, 250)
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    
                    img_label = tk.Label(content_frame,
                                        image=photo,
                                        bg="#18191A",
                                        cursor="hand2")
                    img_label.image = photo  # Giữ reference
                    img_label.pack(side="top")
                except:
                    bubble = tk.Label(content_frame,
                                    text="📷 Ảnh",
                                    bg="#10B981",
                                    fg="white",
                                    font="Helvetica 10",
                                    padx=12,
                                    pady=8)
                    bubble.pack(side="top")
            else:
                # Hiển thị text
                bubble = tk.Label(content_frame,
                                text=text,
                                bg="#10B981",
                                fg="white",
                                font="Helvetica 10",
                                padx=12,
                                pady=8,
                                wraplength=250,
                                justify="left")
                bubble.pack(side="top")
            
            # Thời gian
            time_label = tk.Label(content_frame,
                                text=current_time,
                                bg="#18191A",
                                fg="#8696A0",
                                font="Helvetica 7")
            time_label.pack(side="top", anchor="e", pady=(2, 0))
            
        else:
            # Tin nhắn nhận - bên trái, xám, có avatar và tên
            left_container = tk.Frame(msg_container, bg="#18191A")
            left_container.pack(side="left", anchor="w")
            
            # Avatar
            avatar = tk.Label(left_container,
                            text="👤",
                            bg="#18191A",
                            fg="#E4E6EB",
                            font="Helvetica 16")
            avatar.pack(side="left", padx=(0, 8), anchor="n")
            
            # Container cho tên và bubble
            text_container = tk.Frame(left_container, bg="#18191A")
            text_container.pack(side="left", anchor="w")
            
            # Tên người gửi
            if sender_name:
                name_label = tk.Label(text_container,
                                    text=sender_name,
                                    bg="#18191A",
                                    fg="#B0B3B8",
                                    font="Helvetica 8",
                                    anchor="w")
                name_label.pack(anchor="w", padx=(0, 0))
            
            if image_data:
                # Hiển thị ảnh
                try:
                    img = Image.open(io.BytesIO(image_data))
                    max_size = (250, 250)
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    
                    img_label = tk.Label(text_container,
                                        image=photo,
                                        bg="#18191A",
                                        cursor="hand2")
                    img_label.image = photo
                    img_label.pack(anchor="w")
                except:
                    bubble = tk.Label(text_container,
                                    text="📷 Ảnh",
                                    bg="#3E4042",
                                    fg="#E4E6EB",
                                    font="Helvetica 10",
                                    padx=12,
                                    pady=8)
                    bubble.pack(anchor="w")
            else:
                # Bubble tin nhắn
                bubble = tk.Label(text_container,
                                text=text,
                                bg="#3E4042",
                                fg="#E4E6EB",
                                font="Helvetica 10",
                                padx=12,
                                pady=8,
                                wraplength=250,
                                justify="left")
                bubble.pack(anchor="w")
            
            # Thời gian
            time_label = tk.Label(text_container,
                                text=current_time,
                                bg="#18191A",
                                fg="#8696A0",
                                font="Helvetica 7")
            time_label.pack(anchor="w", pady=(2, 0))
        
        # Scroll xuống cuối
        self.messages_frame.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)

    def browseFile(self):
        self.filename = filedialog.askopenfilename(initialdir="/",
                                                   title="Chọn file",
                                                   filetypes=(("Image files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"),
                                                            ("Text files", "*.txt*"),
                                                            ("All files", "*.*")))
        if self.filename:
            file_ext = os.path.splitext(self.filename)[1].lower()
            if file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
                self.fileLocation.configure(text="🖼️ " + os.path.basename(self.filename))
            else:
                self.fileLocation.configure(text="📎 " + os.path.basename(self.filename))
            self.sengFileBtn.place(relx=0.92, rely=0.5, anchor="center")

    def sendFile(self):
        if not hasattr(self, 'filename') or not self.filename:
            return
        
        file_ext = os.path.splitext(self.filename)[1].lower()
        is_image = file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
        
        if is_image:
            # Gửi ảnh dưới dạng IMAGE
            self.server.send("IMAGE".encode())
            time.sleep(0.1)
            
            # Đọc và gửi ảnh
            with open(self.filename, "rb") as img_file:
                img_data = img_file.read()
                # Gửi kích thước ảnh
                self.server.send(str(len(img_data)).encode())
                time.sleep(0.1)
                # Gửi dữ liệu ảnh
                self.server.send(img_data)
            
            # Hiển thị ảnh đã gửi
            with open(self.filename, "rb") as img_file:
                self.add_message("", is_sent=True, image_data=img_file.read())
        else:
            # Gửi file thông thường
            self.server.send("FILE".encode())
            time.sleep(0.1)
            self.server.send(str("client_" + os.path.basename(self.filename)).encode())
            time.sleep(0.1)
            self.server.send(str(os.path.getsize(self.filename)).encode())
            time.sleep(0.1)

            file = open(self.filename, "rb")
            data = file.read(1024)
            while data:
                self.server.send(data)
                data = file.read(1024)
            
            # Hiển thị file đã gửi
            self.add_message("📄 " + os.path.basename(self.filename), is_sent=True)
        
        self.fileLocation.configure(text="")
        self.sengFileBtn.place_forget()

    def sendButton(self, msg):
        if msg.strip():
            self.msg = msg
            self.entryMsg.delete(0, tk.END)
            snd = threading.Thread(target=self.sendMessage)
            snd.start()

    def sendLike(self):
        """Send like emoji to chat"""
        self.msg = "👍"
        snd = threading.Thread(target=self.sendMessage)
        snd.start()

    def receive(self):
        while True:
            try:
                message = self.server.recv(1024).decode()

                if str(message) == "IMAGE":
                    # Nhận ảnh
                    img_size = int(self.server.recv(1024).decode())
                    
                    # Nhận dữ liệu ảnh
                    img_data = b""
                    while len(img_data) < img_size:
                        chunk = self.server.recv(min(1024, img_size - len(img_data)))
                        if not chunk:
                            break
                        img_data += chunk
                    
                    # Hiển thị ảnh nhận được
                    self.add_message("", is_sent=False, sender_name=self.name, image_data=img_data)

                elif str(message) == "FILE":
                    file_name = self.server.recv(1024).decode()
                    lenOfFile = self.server.recv(1024).decode()
                    send_user = self.server.recv(1024).decode()

                    if os.path.exists(file_name):
                        os.remove(file_name)

                    total = 0
                    with open(file_name, 'wb') as file:
                        while str(total) != lenOfFile:
                            data = self.server.recv(1024)
                            total = total + len(data)
                            file.write(data)

                    # Hiển thị file nhận được
                    self.add_message(f"📄 {file_name}", is_sent=False, sender_name=send_user)

                else:
                    # Kiểm tra nếu là tin nhắn từ bạn
                    if message.startswith("<Ban>"):
                        clean_msg = message.replace("<Ban>", "").strip()
                        self.add_message(clean_msg, is_sent=True)
                    else:
                        # Tin nhắn từ người khác - tách tên và nội dung
                        # Format: <tên> nội dung
                        if message.startswith("<") and ">" in message:
                            end_bracket = message.index(">")
                            sender = message[1:end_bracket]
                            content = message[end_bracket+1:].strip()
                            self.add_message(content, is_sent=False, sender_name=sender)
                        else:
                            self.add_message(message, is_sent=False, sender_name="User")

            except Exception as e:
                print(f"Có lỗi xảy ra: {e}")
                self.server.close()
                break

    def sendMessage(self):
        self.server.send(self.msg.encode())
        # Hiển thị tin nhắn đã gửi
        self.add_message(self.msg, is_sent=True)

    def show_emoji_picker(self):
        """Hiển thị bảng chọn emoji"""
        # Tạo cửa sổ emoji picker
        emoji_window = tk.Toplevel(self.Window)
        emoji_window.title("Chọn Emoji")
        emoji_window.geometry("380x320")
        emoji_window.configure(bg="#242526")
        emoji_window.resizable(False, False)
        
        # Header
        header = tk.Label(emoji_window,
                         text="😊 Chọn Emoji",
                         font="Helvetica 12 bold",
                         bg="#242526",
                         fg="white",
                         pady=10)
        header.pack(fill="x")
        
        # Danh sách emoji phổ biến
        emojis = [
            "😀", "😃", "😄", "😁", "😆", "😅", "🤣", "😂", "🙂", "🙃",
            "😉", "😊", "😇", "🥰", "😍", "🤩", "😘", "😗", "😚", "😙",
            "😋", "😛", "😜", "🤪", "😝", "🤑", "🤗", "🤭", "🤫", "🤔",
            "🤐", "🤨", "😐", "😑", "😶", "😏", "😒", "🙄", "😬", "🤥",
            "😌", "😔", "😪", "🤤", "😴", "😷", "🤒", "🤕", "🤢", "🤮",
            "🤧", "🥵", "🥶", "😶‍🌫️", "😵", "🤯", "🤠", "🥳", "😎", "🤓",
            "👍", "👎", "👌", "✌️", "🤞", "🤟", "🤘", "🤙", "👈", "👉",
            "👆", "👇", "☝️", "👏", "🙌", "👐", "🤲", "🤝", "🙏", "✍️",
            "💪", "🦾", "🦿", "🦵", "🦶", "👂", "👃", "🧠", "🫀", "🫁",
            "❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎", "💔",
            "❤️‍🔥", "❤️‍🩹", "💕", "💞", "💓", "💗", "💖", "💘", "💝", "💟",
            "☮️", "✝️", "☪️", "🕉️", "☸️", "✡️", "🔯", "🕎", "☯️", "☦️"
        ]
        
        # Frame chứa emoji grid
        emoji_frame = tk.Frame(emoji_window, bg="#242526")
        emoji_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Canvas với scrollbar
        canvas = tk.Canvas(emoji_frame, bg="#242526", highlightthickness=0)
        scrollbar = tk.Scrollbar(emoji_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#242526")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Tạo lưới emoji
        row = 0
        col = 0
        for emoji in emojis:
            btn = tk.Button(scrollable_frame,
                          text=emoji,
                          font="Helvetica 20",
                          bg="#3A3B3C",
                          fg="white",
                          border=0,
                          cursor="hand2",
                          width=2,
                          height=1,
                          activebackground="#4A4B4C",
                          command=lambda e=emoji: self.insert_emoji(e, emoji_window))
            btn.grid(row=row, column=col, padx=3, pady=3)
            
            col += 1
            if col > 9:  # 10 emoji mỗi hàng
                col = 0
                row += 1
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Đặt vị trí cửa sổ emoji gần input
        x = self.Window.winfo_x() + 50
        y = self.Window.winfo_y() + self.Window.winfo_height() - 400
        emoji_window.geometry(f"+{x}+{y}")
    
    def insert_emoji(self, emoji, window):
        """Chèn emoji vào ô nhập tin nhắn"""
        current_text = self.entryMsg.get()
        self.entryMsg.delete(0, tk.END)
        self.entryMsg.insert(0, current_text + emoji)
        self.entryMsg.focus()
        window.destroy()


if __name__ == "__main__":
    ip_address = "127.0.0.1"
    port = 12345
    g = GUI(ip_address, port)