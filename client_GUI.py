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
import uuid


class RoundedText(tk.Canvas):
    def __init__(self, parent, **kwargs):
        tk.Canvas.__init__(self, parent, **kwargs)


class GUI:
    def __init__(self, ip_address, port):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.connect((ip_address, port))
        self.default_ttl_ms = 0

        self.msg_widgets = {}         # msg_id -> widget container
        self.msg_meta = {}            # msg_id -> {"text": ..., "sender": ...}
        self.reactions = {}           # msg_id -> {username: emoji}

        # state reply
        self.reply_to_msg_id = None
        self.reply_to_sender = None
        self.reply_to_preview = None

        self._typing = False
        self._typing_after_id = None
        self.running = True

        self.Window = tk.Tk()
        self.Window.withdraw()

        self.Window.protocol("WM_DELETE_WINDOW", self.on_close)
        self.login = tk.Toplevel()
        self.login.title("UTH-CHAT")
        self.login.resizable(width=False, height=False)
        self.login.configure(width=480, height=650, bg="white")

        # Main container
        main_container = tk.Frame(self.login, bg="white")
        main_container.place(relx=0.5, rely=0.5, anchor="center", width=400, height=580)

        # Logo section
        logo_section = tk.Frame(main_container, bg="white")
        logo_section.pack(pady=(20, 0))

        # Logo UTH
        logo_frame = tk.Frame(logo_section, bg="white", width=280, height=100)
        logo_frame.pack()
        logo_frame.pack_propagate(False)

        uth_label = tk.Label(
            logo_frame,
            text="UTH",
            font=("Arial", 50, "bold"),
            bg="white",
            fg="#145A49",
        )
        uth_label.place(x=10, y=10)

        uni_label = tk.Label(
            logo_frame,
            text="UNIVERSITY",
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#E63946",
        )
        uni_label.place(x=140, y=15)

        of_label = tk.Label(
            logo_frame,
            text="OF TRANSPORT",
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#E63946",
        )
        of_label.place(x=140, y=35)

        hcm_label = tk.Label(
            logo_frame,
            text="HOCHIMINH CITY",
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#E63946",
        )
        hcm_label.place(x=140, y=55)

        # Brand name
        brand_frame = tk.Frame(main_container, bg="white")
        brand_frame.pack(pady=(15, 5))

        brand_name = tk.Label(
            brand_frame,
            text="UTH-CHAT",
            font="Helvetica 28 bold",
            bg="white",
            fg="#0E6347",
        )
        brand_name.pack()

        tagline = tk.Label(
            main_container,
            text="Kết nối - Chia sẻ - Trò chuyện",
            font="Helvetica 11",
            bg="white",
            fg="#6B7280",
        )
        tagline.pack(pady=(0, 35))

        # Form container
        shadow_frame = tk.Frame(main_container, bg="#E5E7EB")
        shadow_frame.pack(fill="x", padx=20)

        form_frame = tk.Frame(shadow_frame, bg="white")
        form_frame.pack(fill="x", padx=2, pady=2)

        # Username
        user_container = tk.Frame(form_frame, bg="white")
        user_container.pack(fill="x", padx=20, pady=(25, 0))

        user_label = tk.Label(
            user_container,
            text="👤  Tên người dùng",
            font="Helvetica 10 bold",
            bg="white",
            fg="#0C5B41",
            anchor="w",
        )
        user_label.pack(fill="x", pady=(0, 8))

        user_input_frame = tk.Frame(
            user_container, bg="white",
            highlightbackground="#0C5B41", highlightthickness=2
        )
        user_input_frame.pack(fill="x")

        self.userEntryName = tk.Entry(
            user_input_frame,
            font="Helvetica 13",
            bg="white",
            fg="#1F2937",
            border=0,
            insertbackground="#0C5B41",
        )
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

        # Room ID
        room_container = tk.Frame(form_frame, bg="white")
        room_container.pack(fill="x", padx=20, pady=(20, 25))

        room_label = tk.Label(
            room_container,
            text="🚪  Room ID",
            font="Helvetica 10 bold",
            bg="white",
            fg="#064934",
            anchor="w",
        )
        room_label.pack(fill="x", pady=(0, 8))

        room_input_frame = tk.Frame(
            room_container, bg="white",
            highlightbackground="#0C5B41", highlightthickness=2
        )
        room_input_frame.pack(fill="x")

        self.roomEntryName = tk.Entry(
            room_input_frame,
            font="Helvetica 13",
            bg="white",
            fg="#1F2937",
            border=0,
            insertbackground="#0C5B41",
        )
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

        # Button
        button_container = tk.Frame(main_container, bg="white")
        button_container.pack(fill="x", padx=20, pady=(20, 0))

        self.go = tk.Button(
            button_container,
            text="KẾT NỐI NGAY ✨",
            font="Helvetica 13 bold",
            bg="#10B981",
            fg="white",
            border=0,
            cursor="hand2",
            activebackground="#059669",
            activeforeground="white",
            command=lambda: self.goAhead(
                self.userEntryName.get()
                if self.userEntryName.get() != "Nhập tên của bạn..." else "",
                self.roomEntryName.get()
                if self.roomEntryName.get() != "Nhập mã phòng..." else "",
            ),
        )
        self.go.pack(fill="x", ipady=14)

        def on_btn_enter(e):
            self.go.config(bg="#064934")

        def on_btn_leave(e):
            self.go.config(bg="#064934")

        self.go.bind("<Enter>", on_btn_enter)
        self.go.bind("<Leave>", on_btn_leave)

        self.roomEntryName.bind("<Return>", lambda e: self.go.invoke())

        info_frame = tk.Frame(main_container, bg="white")
        info_frame.pack(pady=(20, 10))

        info_text = tk.Label(
            info_frame,
            text="💡 Tạo phòng mới hoặc tham gia phòng có sẵn",
            font="Helvetica 9",
            bg="white",
            fg="#6B7280",
        )
        info_text.pack()

        divider = tk.Frame(main_container, bg="#E5E7EB", height=1)
        divider.pack(fill="x", padx=40, pady=(15, 15))

        footer_text = tk.Label(
            main_container,
            text="Powered by UTH Technology 🚀",
            font="Helvetica 8",
            bg="white",
            fg="#9CA3AF",
        )
        footer_text.pack()

        self.Window.mainloop()

    def goAhead(self, username, room_id=0):
        if not username or username == "Nhập tên của bạn...":
            return

        self.name = username.strip()
        self.room_id = room_id if room_id else "0"
        # handshake
        self.server.send(self.name.encode())
        time.sleep(0.1)
        self.server.send(
            (room_id if room_id != "Nhập mã phòng..." else "0").encode()
        )

        self.login.destroy()
        self.layout()

        rcv = threading.Thread(target=self.receive, daemon=True)
        rcv.start()

    def layout(self):
        self.Window.deiconify()
        self.Window.title("💬 UTH-CHAT")
        self.Window.resizable(width=False, height=False)
        self.Window.configure(width=420, height=720, bg="#18191A")

        # Header
        header = tk.Frame(self.Window, bg="#242526", height=68)
        header.place(relwidth=1, relheight=0.09)

        avatar = tk.Label(
            header,
            text="👤",
            bg="#242526",
            fg="white",
            font=("Helvetica", 18),
        )
        avatar.place(relx=0.05, rely=0.5, anchor="w")

        name_frame = tk.Frame(header, bg="#242526")
        name_frame.place(relx=0.16, rely=0.5, anchor="w")

        self.chatBoxHead = tk.Label(
            name_frame,
            bg="#242526",
            fg="white",
            text=self.name,
            font="Helvetica 12 bold",
            anchor="w",
        )
        self.chatBoxHead.pack(anchor="w")

        status_frame = tk.Frame(name_frame, bg="#242526")
        status_frame.pack(anchor="w")

        online_dot = tk.Label(
            status_frame,
            text="●",
            bg="#242526",
            fg="#10B981",
            font="Helvetica 6",
        )
        online_dot.pack(side="left", padx=(0, 3))

        status_label = tk.Label(
            status_frame,
            text="Đang online",
            bg="#242526",
            fg="#10B981",
            font="Helvetica 8",
            anchor="w",
        )
        status_label.pack(side="left")

        self.typing_label = tk.Label(
            status_frame,
            text="",
            bg="#242526",
            fg="#B0B3B8",
            font="Helvetica 8 italic",
            anchor="w",
        )
        self.typing_label.pack(side="left", padx=(10, 0))

        self.userlist_label = tk.Label(
            name_frame,
            text="",
            bg="#242526",
            fg="#B0B3B8",
            font="Helvetica 8",
            anchor="w",
            wraplength=220,
            justify="left",
        )
        self.userlist_label.pack(anchor="w")

        minimize_icon = tk.Label(
            header,
            text="─",
            bg="#242526",
            fg="#B0B3B8",
            font="Helvetica 14 bold",
            cursor="hand2",
        )
        minimize_icon.place(relx=0.96, rely=0.5, anchor="center")

        # Chat area
        chat_bg = tk.Frame(self.Window, bg="#18191A")
        chat_bg.place(relwidth=1, relheight=0.77, rely=0.09)

        self.chat_canvas = tk.Canvas(
            chat_bg, bg="#18191A", highlightthickness=0
        )
        self.chat_canvas.place(relwidth=1, relheight=1)

        scrollbar = tk.Scrollbar(
            chat_bg,
            command=self.chat_canvas.yview,
            bg="#3A3B3C",
            troughcolor="#18191A",
        )
        scrollbar.place(relheight=1, relx=0.97, relwidth=0.03)
        self.chat_canvas.config(yscrollcommand=scrollbar.set)

        self.messages_frame = tk.Frame(self.chat_canvas, bg="#18191A")
        self.canvas_frame = self.chat_canvas.create_window(
            (0, 0), window=self.messages_frame, anchor="nw", width=400
        )

        self.messages_frame.bind(
            "<Configure>",
            lambda e: self.chat_canvas.configure(
                scrollregion=self.chat_canvas.bbox("all")
            ),
        )

        # Bottom bar
        bottom_bar = tk.Frame(self.Window, bg="#242526")
        bottom_bar.place(relwidth=1, relheight=0.14, rely=0.86)

        action_frame = tk.Frame(bottom_bar, bg="#242526")
        action_frame.place(relx=0, rely=0, relwidth=1, relheight=0.4)

        mic_btn = tk.Label(
            action_frame,
            text="🎤",
            bg="#242526",
            fg="#10B981",
            font="Helvetica 18",
            cursor="hand2",
        )
        mic_btn.place(relx=0.05, rely=0.5, anchor="w")

        self.browse = tk.Button(
            action_frame,
            text="🖼️",
            font="Helvetica 18",
            bg="#242526",
            fg="#10B981",
            border=0,
            cursor="hand2",
            activebackground="#242526",
            command=self.browseFile,
        )
        self.browse.place(relx=0.18, rely=0.5, anchor="w")

        self.emoji_btn = tk.Button(
            action_frame,
            text="😊",
            bg="#242526",
            fg="#10B981",
            font="Helvetica 18",
            border=0,
            cursor="hand2",
            activebackground="#242526",
            command=self.show_emoji_picker,
        )
        self.emoji_btn.place(relx=0.31, rely=0.5, anchor="w")

        gif_btn = tk.Label(
            action_frame,
            text="GIF",
            bg="#242526",
            fg="#10B981",
            font="Helvetica 10 bold",
            cursor="hand2",
        )
        gif_btn.place(relx=0.44, rely=0.5, anchor="w")

        self.fileLocation = tk.Label(
            action_frame,
            text="",
            bg="#242526",
            fg="#8696A0",
            font="Helvetica 8",
            anchor="w",
        )
        self.fileLocation.place(relx=0.58, rely=0.5, anchor="w")

        self.sengFileBtn = tk.Button(
            action_frame,
            text="✓",
            font="Helvetica 14 bold",
            bg="#10B981",
            fg="white",
            border=0,
            cursor="hand2",
            activebackground="#059669",
            command=self.sendFile,
        )

        # LABEL hiển thị đang reply
        self.reply_label = tk.Label(
            action_frame,
            text="",
            bg="#242526",
            fg="#10B981",
            font="Helvetica 8 italic",
            anchor="w",
        )
        self.reply_label.place(relx=0.58, rely=0.15, anchor="w")

        input_frame = tk.Frame(bottom_bar, bg="#3A3B3C")
        input_frame.place(relx=0.03, relwidth=0.78, rely=0.45, relheight=0.5)

        self.entryMsg = tk.Entry(
            input_frame,
            bg="#3A3B3C",
            fg="#E4E6EB",
            font="Helvetica 11",
            border=0,
            insertbackground="#10B981",
        )
        self.entryMsg.place(relwidth=0.85, relheight=1, relx=0.04, rely=0)
        self.entryMsg.focus()
        self.entryMsg.bind("<Return>", lambda e: self.sendButton(self.entryMsg.get()))
        self.entryMsg.bind("<KeyPress>", self.on_typing)

        emoji_input_btn = tk.Button(
            input_frame,
            text="😊",
            bg="#3A3B3C",
            fg="#10B981",
            font="Helvetica 16",
            border=0,
            cursor="hand2",
            activebackground="#3A3B3C",
            command=self.show_emoji_picker,
        )
        emoji_input_btn.place(relx=0.92, rely=0.5, anchor="center")

        self.buttonMsg = tk.Button(
            bottom_bar,
            text="👍",
            font="Helvetica 22",
            bg="#242526",
            fg="#10B981",
            border=0,
            cursor="hand2",
            activebackground="#242526",
            command=self.sendLike,
        )
        self.buttonMsg.place(
            relx=0.85, rely=0.7, relheight=0.3, relwidth=0.13, anchor="w"
        )

    def add_system_message(self, text):
        msg_container = tk.Frame(self.messages_frame, bg="#18191A")
        msg_container.pack(fill="x", pady=6)

        box = tk.Frame(msg_container, bg="#18191A")
        box.pack(anchor="center")

        bubble = tk.Label(
            box,
            text=text,
            bg="#3A3B3C",
            fg="#E4E6EB",
            font="Helvetica 10 bold",
            padx=14,
            pady=10,
            wraplength=260,
            justify="center",
        )
        bubble.pack()

        time_label = tk.Label(
            box,
            text=datetime.now().strftime("%H:%M"),
            bg="#18191A",
            fg="#8696A0",
            font="Helvetica 7",
        )
        time_label.pack(anchor="center", pady=(2, 0))

        self.messages_frame.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)

    def add_message(self, text, is_sent=True, sender_name=None,
                    image_data=None, time_override=None,
                    reply_preview=None, reply_sender=None):
        msg_container = tk.Frame(self.messages_frame, bg="#18191A")
        msg_container.pack(fill="x", pady=5, padx=10)

        current_time = time_override or datetime.now().strftime("%H:%M")

        if is_sent:
            bubble_frame = tk.Frame(msg_container, bg="#18191A")
            bubble_frame.pack(side="right")

            content_frame = tk.Frame(bubble_frame, bg="#18191A")
            content_frame.pack(side="right")

            # quote khi reply (tin mình)
            if reply_preview:
                reply_box = tk.Frame(content_frame, bg="#18191A")
                reply_box.pack(side="top", anchor="e", pady=(0, 2))

                inner = tk.Frame(reply_box, bg="#1f2122")
                inner.pack(side="right", anchor="e")

                if reply_sender:
                    sender_lbl = tk.Label(
                        inner,
                        text=reply_sender,
                        bg="#1f2122",
                        fg="#10B981",
                        font="Helvetica 8 bold",
                        anchor="w",
                    )
                    sender_lbl.pack(fill="x", padx=6, pady=(4, 0))

                preview_lbl = tk.Label(
                    inner,
                    text=reply_preview,
                    bg="#1f2122",
                    fg="#E4E6EB",
                    font="Helvetica 8",
                    anchor="w",
                    wraplength=220,
                    justify="left",
                )
                preview_lbl.pack(fill="x", padx=6, pady=(0, 4))

            if image_data:
                try:
                    img = Image.open(io.BytesIO(image_data))
                    max_size = (250, 250)
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)

                    img_label = tk.Label(
                        content_frame,
                        image=photo,
                        bg="#18191A",
                        cursor="hand2",
                    )
                    img_label.image = photo
                    img_label.pack(side="top")
                except:
                    bubble = tk.Label(
                        content_frame,
                        text="📷 Ảnh",
                        bg="#10B981",
                        fg="white",
                        font="Helvetica 10",
                        padx=12,
                        pady=8,
                    )
                    bubble.pack(side="top")
            else:
                bubble = tk.Label(
                    content_frame,
                    text=text,
                    bg="#10B981",
                    fg="white",
                    font="Helvetica 10",
                    padx=12,
                    pady=8,
                    wraplength=250,
                    justify="left",
                )
                bubble.pack(side="top")

            time_label = tk.Label(
                content_frame,
                text=current_time,
                bg="#18191A",
                fg="#8696A0",
                font="Helvetica 7",
            )
            time_label.pack(side="top", anchor="e", pady=(2, 0))

            status_label = tk.Label(
                content_frame,
                text="",
                bg="#18191A",
                fg="#8696A0",
                font="Helvetica 7",
            )
            status_label.pack(side="top", anchor="e", pady=(0, 0))
            msg_container._status_label = status_label

        else:
            left_container = tk.Frame(msg_container, bg="#18191A")
            left_container.pack(side="left", anchor="w")

            avatar = tk.Label(
                left_container,
                text="👤",
                bg="#18191A",
                fg="#E4E6EB",
                font="Helvetica 16",
            )
            avatar.pack(side="left", padx=(0, 8), anchor="n")

            text_container = tk.Frame(left_container, bg="#18191A")
            text_container.pack(side="left", anchor="w")

            if sender_name:
                name_label = tk.Label(
                    text_container,
                    text=sender_name,
                    bg="#18191A",
                    fg="#B0B3B8",
                    font="Helvetica 8",
                    anchor="w",
                )
                name_label.pack(anchor="w", padx=(0, 0))

            # quote khi reply (người khác)
            if reply_preview:
                reply_box = tk.Frame(text_container, bg="#18191A")
                reply_box.pack(anchor="w", pady=(0, 2))

                inner = tk.Frame(reply_box, bg="#2a2c2f")
                inner.pack(anchor="w")

                if reply_sender:
                    sender_lbl = tk.Label(
                        inner,
                        text=reply_sender,
                        bg="#2a2c2f",
                        fg="#10B981",
                        font="Helvetica 8 bold",
                        anchor="w",
                    )
                    sender_lbl.pack(fill="x", padx=6, pady=(4, 0))

                preview_lbl = tk.Label(
                    inner,
                    text=reply_preview,
                    bg="#2a2c2f",
                    fg="#E4E6EB",
                    font="Helvetica 8",
                    anchor="w",
                    wraplength=220,
                    justify="left",
                )
                preview_lbl.pack(fill="x", padx=6, pady=(0, 4))

            if image_data:
                try:
                    img = Image.open(io.BytesIO(image_data))
                    max_size = (250, 250)
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)

                    img_label = tk.Label(
                        text_container,
                        image=photo,
                        bg="#18191A",
                        cursor="hand2",
                    )
                    img_label.image = photo
                    img_label.pack(anchor="w")
                except:
                    bubble = tk.Label(
                        text_container,
                        text="📷 Ảnh",
                        bg="#3E4042",
                        fg="#E4E6EB",
                        font="Helvetica 10",
                        padx=12,
                        pady=8,
                    )
                    bubble.pack(anchor="w")
            else:
                bubble = tk.Label(
                    text_container,
                    text=text,
                    bg="#3E4042",
                    fg="#E4E6EB",
                    font="Helvetica 10",
                    padx=12,
                    pady=8,
                    wraplength=250,
                    justify="left",
                )
                bubble.pack(anchor="w")

            time_label = tk.Label(
                text_container,
                text=current_time,
                bg="#18191A",
                fg="#8696A0",
                font="Helvetica 7",
            )
            time_label.pack(anchor="w", pady=(2, 0))

        self.messages_frame.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)
        return msg_container

    def _new_msg_id(self):
        return uuid.uuid4().hex

    def _attach_msg_id(self, container, msg_id):
        container._msg_id = msg_id
        self.msg_widgets[msg_id] = container
        # gắn luôn menu chuột phải cho mọi tin nhắn
        self._bind_right_click(container, msg_id)

    def _remove_msg_widget(self, msg_id):
        w = self.msg_widgets.pop(msg_id, None)
        if w:
            try:
                w.destroy()
            except:
                pass

    def _recall_msg(self, msg_id):
        if not msg_id:
            return
        try:
            self._safe_send(b"RECALL")
            time.sleep(0.02)
            self._safe_send(msg_id.encode())
        except:
            pass
        self._remove_msg_widget(msg_id)

    def _apply_reaction(self, msg_id, reaction, sender):
        """
        Cập nhật reaction cho 1 msg_id, kèm theo tên người react.
        self.reactions[msg_id] = { username: emoji }
        """
        if not sender:
            return

        msg_map = self.reactions.setdefault(msg_id, {})

        if not reaction:   # nếu sau này muốn support bỏ reaction thì dùng
            msg_map.pop(sender, None)
        else:
            msg_map[sender] = reaction

        cont = self.msg_widgets.get(msg_id)
        if not cont:
            return

        if not msg_map:
            if hasattr(cont, "_reaction_label"):
                try:
                    cont._reaction_label.destroy()
                except:
                    pass
                del cont._reaction_label
            return

        counts = {}
        for emo in msg_map.values():
            counts[emo] = counts.get(emo, 0) + 1

        best_emoji = None
        best_cnt = 0
        for emo, c in counts.items():
            if c > best_cnt:
                best_emoji, best_cnt = emo, c

        if not best_emoji:
            return

        label_text = best_emoji if best_cnt == 1 else f"{best_emoji} x{best_cnt}"

        if not hasattr(cont, "_reaction_label"):
            side = "right"
            anchor = "e"
            if hasattr(cont, "_is_sent") and not cont._is_sent:
                side = "left"
                anchor = "w"

            lbl = tk.Label(
                cont,
                text=label_text,
                bg="#18191A",
                fg="#FBBF24",
                font="Helvetica 10 bold",
                cursor="hand2",
            )
            lbl.pack(side=side, anchor=anchor, padx=6, pady=(0, 2))
            cont._reaction_label = lbl

            # Bấm vào emoji để xem ai đã react
            lbl.bind(
                "<Button-1>",
                lambda e, mid=msg_id: self._show_reaction_view(mid),
            )
        else:
            cont._reaction_label.config(text=label_text)

    def _show_reaction_view(self, msg_id):
        """
        Hiển thị popup nhỏ liệt kê ai đã react gì cho msg_id.
        """
        msg_map = self.reactions.get(msg_id)
        if not msg_map:
            return

        lines = [f"{user}: {emo}" for user, emo in msg_map.items()]
        text = "\n".join(lines)

        popup = tk.Toplevel(self.Window)
        popup.title("Reaction")
        popup.configure(bg="#242526")
        popup.resizable(False, False)

        label = tk.Label(
            popup,
            text=text,
            bg="#242526",
            fg="white",
            font="Helvetica 9",
            justify="left",
            padx=10,
            pady=8,
        )
        label.pack()

        # đặt vị trí gần con trỏ chuột
        x = self.Window.winfo_pointerx() + 10
        y = self.Window.winfo_pointery() + 10
        popup.geometry(f"+{x}+{y}")

        # tự đóng sau 3 giây
        popup.after(3000, popup.destroy)

    def _show_msg_menu(self, widget, msg_id):
        menu = tk.Menu(self.Window, tearoff=0)
        menu.configure(
            bg="#2f3136",
            fg="white",
            activebackground="#10B981",
            activeforeground="white",
        )

        menu.add_command(
            label="↩  Trả lời tin nhắn",
            command=lambda mid=msg_id: self._start_reply(mid),
        )

        # ====== SUBMENU REACTION ======
        react_menu = tk.Menu(
            menu,
            tearoff=0,
            bg="#2f3136",
            fg="white",
            activebackground="#10B981",
            activeforeground="white",
        )
        for emo in ["👍", "❤️", "😆", "😢", "😮"]:
            react_menu.add_command(
                label=emo,
                command=lambda e=emo, mid=msg_id: self._send_react(mid, e),
            )
        menu.add_cascade(label="✨ Reaction", menu=react_menu)
        # ==============================

        menu.add_command(
            label="🗑️  Gỡ tin nhắn",
            command=lambda: self._recall_msg(msg_id),
        )

        submenu = tk.Menu(
            menu,
            tearoff=0,
            bg="#2f3136",
            fg="white",
            activebackground="#10B981",
            activeforeground="white",
        )
        for sec in (5, 10, 30, 60):
            submenu.add_command(
                label=f"⏱️ {sec} giây",
                command=lambda s=sec, mid=msg_id: self.Window.after(
                    s * 1000, lambda: self._recall_msg(mid)
                ),
            )
        menu.add_cascade(label="⏰  Tự hủy sau...", menu=submenu)

        try:
            menu.tk_popup(self.Window.winfo_pointerx(), self.Window.winfo_pointery())
        finally:
            menu.grab_release()

    def _bind_right_click(self, widget, msg_id):
        widget.bind(
            "<Button-3>",
            lambda e, mid=msg_id: self._show_msg_menu(widget, mid),
        )
        for ch in widget.winfo_children():
            self._bind_right_click(ch, msg_id)

    # ====== HÀM BẮT ĐẦU / HỦY REPLY ======
    def _start_reply(self, msg_id):
        meta = self.msg_meta.get(msg_id)
        if not meta:
            return
        self.reply_to_msg_id = msg_id
        self.reply_to_sender = meta.get("sender", "")
        full_text = meta.get("text", "")
        preview = full_text if len(full_text) <= 40 else full_text[:37] + "..."
        self.reply_to_preview = preview

        self.reply_label.config(
            text=f"↩ Đang trả lời {self.reply_to_sender}: {preview}   (bấm để hủy)"
        )
        self.reply_label.bind("<Button-1>", lambda e: self._cancel_reply())

    def _cancel_reply(self):
        self.reply_to_msg_id = None
        self.reply_to_sender = None
        self.reply_to_preview = None
        self.reply_label.config(text="")
    # ==========================================

    def browseFile(self):
        self.filename = filedialog.askopenfilename(
            initialdir="/",
            title="Chọn file",
            filetypes=(
                ("Image files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"),
                ("Text files", "*.txt*"),
                ("All files", "*.*"),
            ),
        )
        if self.filename:
            file_ext = os.path.splitext(self.filename)[1].lower()
            if file_ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp"]:
                self.fileLocation.configure(
                    text="🖼️ " + os.path.basename(self.filename)
                )
            else:
                self.fileLocation.configure(
                    text="📎 " + os.path.basename(self.filename)
                )
            self.sengFileBtn.place(relx=0.92, rely=0.5, anchor="center")

    def sendFile(self):
        if not hasattr(self, "filename") or not self.filename:
            return

        file_ext = os.path.splitext(self.filename)[1].lower()
        is_image = file_ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp"]

        if is_image:
            self._safe_send(b"IMAGE")
            time.sleep(0.05)

            with open(self.filename, "rb") as img_file:
                img_data = img_file.read()
                self._safe_send(str(len(img_data)).encode())
                time.sleep(0.05)
                self._safe_send(img_data)

            with open(self.filename, "rb") as img_file:
                self.add_message("", is_sent=True, image_data=img_file.read())
        else:
            self._safe_send(b"FILE")
            time.sleep(0.05)
            basename = os.path.basename(self.filename)
            self._safe_send(("client_" + basename).encode())
            time.sleep(0.05)
            self._safe_send(str(os.path.getsize(self.filename)).encode())
            time.sleep(0.05)

            with open(self.filename, "rb") as f:
                while True:
                    data = f.read(4096)
                    if not data:
                        break
                    self._safe_send(data)
            self.add_message("📄 " + basename, is_sent=True)

        self.fileLocation.configure(text="")
        self.sengFileBtn.place_forget()

    def sendButton(self, msg):
        if msg.strip():
            if msg.startswith("/ttl "):
                parts = msg.split(" ", 2)
                if len(parts) >= 3 and len(parts[1]) and parts[1].isdigit():
                    self.default_ttl_ms = int(parts[1]) * 1000
                    self.msg = parts[2]
                else:
                    return
            else:
                self.default_ttl_ms = 0
                self.msg = msg

            self.entryMsg.delete(0, tk.END)
            snd = threading.Thread(target=self.sendMessage, daemon=True)
            snd.start()

    def sendLike(self):
        self.msg = "👍"
        snd = threading.Thread(target=self.sendMessage, daemon=True)
        snd.start()

    def _safe_send(self, data: bytes):
        if not self.running:
            return
        try:
            self.server.send(data)
        except:
            pass

    def _send_react(self, msg_id, emoji):
        """
        Gửi gói REACT lên server:
        REACT
        <msg_id>
        <emoji>
        """
        try:
            self._safe_send(b"REACT")
            time.sleep(0.02)
            self._safe_send(msg_id.encode())
            time.sleep(0.02)
            self._safe_send(emoji.encode("utf-8"))
        except Exception as e:
            print("Send REACT error:", e)

        # Cập nhật ngay trên UI của chính mình cho mượt
        self._apply_reaction(msg_id, emoji, self.name)

    def sendMessage(self):
        if not self.running:
            return

        content = getattr(self, "msg", "").strip()
        if not content:
            return

        msg_id = self._new_msg_id()
        content_bytes = content.encode("utf-8")
        reply_to = self.reply_to_msg_id

        try:
            if reply_to:
                # ===== REPLY =====
                self._safe_send(b"REPLY")
                time.sleep(0.02)
                self._safe_send(reply_to.encode())
                time.sleep(0.02)
                self._safe_send(msg_id.encode())
                time.sleep(0.02)
                self._safe_send(str(len(content_bytes)).encode())
                time.sleep(0.02)
                self._safe_send(content_bytes)
            else:
                # ===== MSG THƯỜNG =====
                ttl_ms = str(self.default_ttl_ms)

                self._safe_send(b"MSG")
                time.sleep(0.02)
                self._safe_send(msg_id.encode())
                time.sleep(0.02)
                self._safe_send(ttl_ms.encode())
                time.sleep(0.02)
                self._safe_send(str(len(content_bytes)).encode())
                time.sleep(0.02)
                self._safe_send(content_bytes)

        except Exception as e:
            print("Lỗi gửi tin:", e)
            return

        # ===== HIỂN THỊ LOCAL UI =====
        if reply_to:
            preview = self.reply_to_preview or ""
            sender = self.reply_to_sender or ""
            container = self.add_message(
                content,
                is_sent=True,
                reply_preview=preview,
                reply_sender=sender,
            )
            self._cancel_reply()
        else:
            container = self.add_message(content, is_sent=True)

        container._is_sent = True

        self._attach_msg_id(container, msg_id)
        self.msg_meta[msg_id] = {"text": content, "sender": self.name}

        if (not reply_to) and self.default_ttl_ms and int(self.default_ttl_ms) > 0:
            self.Window.after(
                int(self.default_ttl_ms),
                lambda mid=msg_id: self._recall_msg(mid)
            )

    def receive(self):
        while self.running:
            try:
                header = self.server.recv(1024)
                if not header:
                    break
                tag = header.decode(errors="ignore").strip()

                # ẢNH
                if tag == "IMAGE":
                    size_str = self.server.recv(1024).decode()
                    total_len = int(size_str)
                    sender = self.server.recv(1024).decode()

                    img_data = b""
                    while len(img_data) < total_len:
                        chunk = self.server.recv(min(4096, total_len - len(img_data)))
                        if not chunk:
                            break
                        img_data += chunk

                    self.add_message(
                        "",
                        is_sent=(sender == self.name),
                        sender_name=(None if sender == self.name else sender),
                        image_data=img_data,
                    )

                # FILE
                elif tag == "FILE":
                    file_name = self.server.recv(1024).decode()
                    lenOfFile = int(self.server.recv(1024).decode())
                    send_user = self.server.recv(1024).decode()

                    total = 0
                    with open(file_name, "wb") as file:
                        while total < lenOfFile:
                            data = self.server.recv(min(4096, lenOfFile - total))
                            if not data:
                                break
                            total += len(data)
                            file.write(data)

                    self.add_message(
                        f"📄 {file_name}",
                        is_sent=(send_user == self.name),
                        sender_name=(None if send_user == self.name else send_user),
                    )

                # MSG
                elif tag == "MSG":
                    msg_id = self.server.recv(1024).decode()
                    ttl_ms = int(self.server.recv(1024).decode())
                    sender = self.server.recv(1024).decode()
                    content_len = int(self.server.recv(1024).decode())

                    buf = b""
                    while len(buf) < content_len:
                        chunk = self.server.recv(min(4096, content_len - len(buf)))
                        if not chunk:
                            break
                        buf += chunk
                    text = buf.decode(errors="ignore")

                    is_me = (sender == self.name)
                    is_history = (ttl_ms < 0)   # TTL = -1 => history

                    container = self.add_message(
                        text,
                        is_sent=is_me,
                        sender_name=(None if is_me else sender),
                    )

                    container._is_sent = is_me
                    self._attach_msg_id(container, msg_id)
                    self.msg_meta[msg_id] = {"text": text, "sender": sender}

                    # Chỉ gửi ACK / TTL cho tin realtime
                    if (not is_history) and (not is_me):
                        try:
                            self._safe_send(b"ACK")
                            time.sleep(0.02)
                            self._safe_send(msg_id.encode())
                        except:
                            pass

                    if (not is_history) and ttl_ms and ttl_ms > 0 and is_me:
                        self.Window.after(
                            ttl_ms, lambda mid=msg_id: self._recall_msg(mid)
                        )

                # REPLY
                elif tag == "REPLY":
                    reply_to_id = self.server.recv(1024).decode(errors="ignore").strip()
                    msg_id = self.server.recv(1024).decode(errors="ignore").strip()
                    sender = self.server.recv(1024).decode(errors="ignore").strip()
                    content_len = int(self.server.recv(1024).decode(errors="ignore").strip())

                    buf = b""
                    while len(buf) < content_len:
                        chunk = self.server.recv(min(4096, content_len - len(buf)))
                        if not chunk:
                            break
                        buf += chunk
                    text = buf.decode(errors="ignore")

                    is_me = (sender == self.name)

                    meta = self.msg_meta.get(reply_to_id)
                    if meta:
                        preview_text = meta.get("text", "")
                        preview_sender = meta.get("sender", "")
                        if len(preview_text) > 40:
                            preview_text = preview_text[:37] + "..."
                    else:
                        preview_text = "(Tin nhắn không còn hoặc ở phiên khác)"
                        preview_sender = ""

                    container = self.add_message(
                        text,
                        is_sent=is_me,
                        sender_name=(None if is_me else sender),
                        reply_preview=preview_text,
                        reply_sender=preview_sender,
                    )
                    container._is_sent = is_me
                    self._attach_msg_id(container, msg_id)
                    self.msg_meta[msg_id] = {"text": text, "sender": sender}

                # REACT
                elif tag == "REACT":
                    msg_id = self.server.recv(1024).decode(errors="ignore").strip()
                    sender = self.server.recv(1024).decode(errors="ignore").strip()
                    reaction = self.server.recv(1024).decode(errors="ignore")
                    self._apply_reaction(msg_id, reaction, sender)

                # RECALL
                elif tag == "RECALL":
                    msg_id = self.server.recv(1024).decode()
                    _sender = self.server.recv(1024).decode()
                    self._remove_msg_widget(msg_id)

                # READ (có thể dính msg_id)
                elif tag.startswith("READ"):
                    rest = tag[len("READ"):].strip()
                    if rest:
                        msg_id = rest
                    else:
                        msg_id = self.server.recv(1024).decode(errors="ignore").strip()
                    reader = self.server.recv(1024).decode(errors="ignore").strip()

                    cont = self.msg_widgets.get(msg_id)
                    if cont and hasattr(cont, "_status_label"):
                        cont._status_label.config(text="Đã xem")
                    continue

                # USERLIST
                elif tag.startswith("USERLIST"):
                    after = tag[len("USERLIST"):].strip()

                    # 1) Trường hợp server gửi "USERLISTthanhdat,quan,nam"
                    if after:
                        users_str = after
                    else:
                        # 2) Trường hợp server gửi: "USERLIST" + \n + length + \n + payload
                        length_str = self.server.recv(1024).decode(errors="ignore")
                        try:
                            payload_len = int(length_str)
                            buf = b""
                            while len(buf) < payload_len:
                                chunk = self.server.recv(
                                    min(4096, payload_len - len(buf))
                                )
                                if not chunk:
                                    break
                                buf += chunk
                            users_str = buf.decode(errors="ignore")
                        except ValueError:
                            # Bị dính luôn payload vào length_str, hoặc server cũ
                            users_str = length_str.strip()

                    # --- Làm sạch: cắt bỏ phần dính thêm header khác (MSG, REPLY, ...) ---
                    for marker in ["MSG", "REPLY", "IMAGE", "FILE",
                                   "USERLIST", "READ", "REACT",
                                   "TYPING", "ACK", "RECALL"]:
                        idx = users_str.find(marker)
                        if idx > 0:
                            users_str = users_str[:idx]
                            break

                    users_str = users_str.strip()
                    if users_str:
                        users = [u for u in users_str.split(",") if u]
                    else:
                        users = []

                    self.update_userlist(users)

                # TYPING
                elif tag.startswith("TYPING"):
                    # xử lý cả "TYPING" và "TYPINGquan" / "TYPING quan START"
                    stripped = tag.strip()
                    rest = stripped[len("TYPING"):].strip()

                    if rest:
                        # có sẵn 1 phần/ cả sender trong gói đầu
                        parts = rest.split()
                        sender = parts[0]
                        if len(parts) > 1:
                            # hiếm khi status cũng dính chung luôn, vẫn xử lý được
                            status = parts[1]
                        else:
                            # chỉ có sender, đọc tiếp status từ server
                            status = self.server.recv(1024).decode(errors="ignore")
                    else:
                        # gói đẹp, "TYPING" riêng → đọc 2 gói tiếp theo
                        sender = self.server.recv(1024).decode(errors="ignore")
                        status = self.server.recv(1024).decode(errors="ignore")

                    self.show_typing(sender, status)

                # MỌI THỨ CÒN LẠI (fallback, chặn rác)
                else:
                    stripped = tag.strip()
                    if not stripped:
                        continue

                    # bỏ rác TYPING lẻ
                    if stripped.startswith("TYPING"):
                        continue

                    # xử lý case "3saoMSG<hex-id>"
                    if "MSG" in stripped:
                        idx = stripped.find("MSG")
                        before = stripped[:idx]
                        after = stripped[idx+3:]  # sau chữ MSG
                        hex_candidate = after.replace("-", "")
                        if hex_candidate and len(hex_candidate) in (32, 36) and all(
                            c in "0123456789abcdefABCDEF" for c in hex_candidate
                        ):
                            before = before.lstrip("0123456789").strip()
                            if not before:  # chỉ toàn length, không có text
                                continue
                            stripped = before

                    # Fix rác kiểu "-1thanhdat"
                    if stripped.startswith("-1") and " " not in stripped and len(stripped) < 40:
                        continue

                    # 1) Nếu lỡ dính USERLIST dạng text -> xử lý & bỏ
                    if stripped.startswith("USERLIST"):
                        users_str = stripped[len("USERLIST"):].strip()
                        if users_str:
                            users = [u for u in users_str.split(",") if u]
                            self.update_userlist(users)
                        continue

                    # 2) Bỏ READ control
                    if stripped.startswith("READ"):
                        continue

                    # 3) Bỏ các số thuần (TTL, length, -1, 0, 1,...)
                    if stripped.lstrip("-").isdigit():
                        continue

                    # 4) Bỏ log REACT cũ
                    if "REACT" in stripped or stripped.startswith("@REACT"):
                        continue

                    # 5) Bỏ log cũ dạng "<msgid>||<emoji>"
                    if "||" in stripped:
                        try:
                            mid, emo = stripped.split("||", 1)
                            mid = mid.strip()
                            emo = emo.strip()
                            hex_candidate2 = mid.replace("-", "")
                            if (
                                hex_candidate2
                                and len(hex_candidate2) in (32, 36)
                                and all(c in "0123456789abcdefABCDEF" for c in hex_candidate2)
                                and emo in ["👍", "❤️", "😆", "😢", "😮"]
                            ):
                                continue
                        except ValueError:
                            pass

                    # 6) Rác lịch sử kiểu "MSG91de9033..." không có khoảng trắng
                    if stripped.startswith("MSG") and (" " not in stripped) and len(stripped) > 10:
                        continue

                    # 7) Chuỗi kiểu "<32 hex><tên>" liền nhau
                    s_no_space = stripped.replace(" ", "")
                    if len(s_no_space) > 32:
                        prefix = s_no_space[:32]
                        if all(c in "0123456789abcdefABCDEF" for c in prefix):
                            continue

                    # 8) Chuỗi toàn hex id -> bỏ
                    hex_candidate = stripped.replace("-", "")
                    if hex_candidate and len(hex_candidate) in (32, 36) and all(
                        c in "0123456789abcdefABCDEF" for c in hex_candidate
                    ):
                        continue

                    # 9) Không phải rác -> hiển thị như message text
                    message = stripped

                    if message.startswith("<Server>"):
                        clean_msg = message.replace("<Server>", "").strip()
                        self.add_system_message(clean_msg)
                    elif message.startswith("<Ban>"):
                        clean_msg = message.replace("<Ban>", "").strip()
                        self.add_message(clean_msg, is_sent=True)
                    else:
                        if message.startswith("<") and ">" in message:
                            end_bracket = message.index(">")
                            sender = message[1:end_bracket]
                            content = message[end_bracket + 1 :].strip()
                            if sender == "Server":
                                self.add_system_message(content)
                            else:
                                self.add_message(
                                    content, is_sent=False, sender_name=sender
                                )
                        else:
                            self.add_message(message, is_sent=False)

            except:
                try:
                    self.server.close()
                except:
                    pass
                break

    def update_userlist(self, users):
        if not hasattr(self, "Window") or not self.Window.winfo_exists():
            return

        def _do_update():
            if not users:
                text = f"Phòng {getattr(self, 'room_id', '?')} · 0 online"
            else:
                text = (
                    f"Phòng {getattr(self, 'room_id', '?')} · {len(users)} online: "
                    + ", ".join(users)
                )
            self.userlist_label.config(text=text)

        self.Window.after(0, _do_update)

    def show_typing(self, sender, status):
        try:
            if sender == self.name:
                return

            if status == "START":
                self.typing_label.config(text=f"{sender} đang nhập...")
            else:
                if self.typing_label.cget("text").startswith(sender):
                    self.typing_label.config(text="")
        except Exception as e:
            print("show_typing error:", e)

    def on_typing(self, event=None):
        try:
            if not self._typing:
                self._typing = True
                threading.Thread(
                    target=self._send_typing_start, daemon=True
                ).start()

            if self._typing_after_id:
                self.Window.after_cancel(self._typing_after_id)
            self._typing_after_id = self.Window.after(
                1500, self._send_typing_stop
            )
        except:
            pass

    def _send_typing_start(self):
        try:
            self._safe_send(b"TYPING")
            time.sleep(0.02)
            self._safe_send(b"START")
        except Exception as e:
            print("Typing START error:", e)

    def _send_typing_stop(self):
        self._typing = False
        self._typing_after_id = None
        try:
            self._safe_send(b"TYPING")
            time.sleep(0.02)
            self._safe_send(b"STOP")
        except Exception as e:
            print("Typing STOP error:", e)

    def show_emoji_picker(self):
        emoji_window = tk.Toplevel(self.Window)
        emoji_window.title("Chọn Emoji")
        emoji_window.geometry("380x320")
        emoji_window.configure(bg="#242526")
        emoji_window.resizable(False, False)

        header = tk.Label(
            emoji_window,
            text="😊 Chọn Emoji",
            font="Helvetica 12 bold",
            bg="#242526",
            fg="white",
            pady=10,
        )
        header.pack(fill="x")

        emojis = [
            "😀","😃","😄","😁","😆","😅","🤣","😂","🙂","🙃","😉","😊","😇","🥰","😍","🤩","😘",
            "😗","😚","😙","😋","😛","😜","🤪","😝","🤑","🤗","🤭","🤫","🤔","🤐","🤨","😐","😑",
            "😶","😏","😒","🙄","😬","🤥","😌","😔","😪","🤤","😴","😷","🤒","🤕","🤢","🤮","🤧",
            "🥵","🥶","😶‍🌫️","😵","🤯","🤠","🥳","😎","🤓","👍","👎","👌","✌️","🤞","🤟","🤘","🤙",
            "👈","👉","👆","👇","☝️","👏","🙌","👐","🤲","🤝","🙏","✍️","💪","🦾","🦿","🦵","🦶",
            "👂","👃","🧠","🫀","🫁","❤️","🧡","💛","💚","💙","💜","🖤","🤍","🤎","💔","❤️‍🔥",
            "❤️‍🩹","💕","💞","💓","💗","💖","💘","💝","💟",
        ]

        emoji_frame = tk.Frame(emoji_window, bg="#242526")
        emoji_frame.pack(fill="both", expand=True, padx=10, pady=10)

        canvas = tk.Canvas(
            emoji_frame, bg="#242526", highlightthickness=0
        )
        scrollbar = tk.Scrollbar(
            emoji_frame, orient="vertical", command=canvas.yview
        )
        scrollable_frame = tk.Frame(canvas, bg="#242526")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            ),
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        row = 0
        col = 0
        for emoji in emojis:
            btn = tk.Button(
                scrollable_frame,
                text=emoji,
                font="Helvetica 20",
                bg="#3A3B3C",
                fg="white",
                border=0,
                cursor="hand2",
                width=2,
                height=1,
                activebackground="#4A4B4C",
                command=lambda e=emoji: self.insert_emoji(e, emoji_window),
            )
            btn.grid(row=row, column=col, padx=3, pady=3)

            col += 1
            if col > 9:
                col = 0
                row += 1

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        x = self.Window.winfo_x() + 50
        y = self.Window.winfo_y() + self.Window.winfo_height() - 400
        emoji_window.geometry(f"+{x}+{y}")

    def insert_emoji(self, emoji, window):
        current_text = self.entryMsg.get()
        self.entryMsg.delete(0, tk.END)
        self.entryMsg.insert(0, current_text + emoji)
        self.entryMsg.focus()
        window.destroy()

    def on_close(self):
        self.running = False
        try:
            self.server.close()
        except:
            pass
        try:
            self.Window.destroy()
        except:
            pass


if __name__ == "__main__":
    ip_address = "127.0.0.1"
    port = 12345
    g = GUI(ip_address, port)
