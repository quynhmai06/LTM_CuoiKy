import socket
import sys
import time
import os
import threading
import uuid

IP_address = "127.0.0.1"
port = 12345

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.connect((IP_address, port))
print("Da ket noi toi server")

# ============= HÀM HỖ TRỢ =============
recv_buf = b""

def recv_line(conn):
    global recv_buf
    while b"\n" not in recv_buf:
        chunk = conn.recv(1)
        if not chunk:
            return ""
        recv_buf += chunk
    line, recv_buf = recv_buf.split(b"\n", 1)
    return line.decode(errors="ignore").strip()

def send_line(conn, text):
    conn.sendall((text + "\n").encode())
# =======================================

user_id = input("Nhap ten nguoi dung: ")
room_id = input("Nhap room id: ")

send_line(server, user_id)
send_line(server, room_id)

welcome_msg = recv_line(server)
print(welcome_msg)

def receive():
    while True:
        try:
            tag = recv_line(server)
            if not tag:
                break

            # ======================== MSG ========================
            if tag == "MSG":
                msg_id = recv_line(server)
                ttl_ms = recv_line(server)
                sender = recv_line(server)
                content_len = int(recv_line(server))

                buf = b""
                while len(buf) < content_len:
                    buf += server.recv(content_len - len(buf))

                print(f"<{sender}> {buf.decode(errors='ignore')}")

            # ======================== REPLY ======================
            elif tag == "REPLY":
                reply_to = recv_line(server)
                msg_id = recv_line(server)
                sender = recv_line(server)
                content_len = int(recv_line(server))

                buf = b""
                while len(buf) < content_len:
                    buf += server.recv(content_len - len(buf))

                print(f"<{sender}> (reply to {reply_to}) {buf.decode(errors='ignore')}")

            # ======================== IMAGE ======================
            elif tag == "IMAGE":
                msg_id = recv_line(server)
                size = int(recv_line(server))
                sender = recv_line(server)

                data = b""
                while len(data) < size:
                    data += server.recv(size - len(data))

                filename = f"image_{sender}_{msg_id}.bin"
                with open(filename, "wb") as f:
                    f.write(data)

                print(f"<{sender}> da gui hinh ({filename})")

            # ======================== FILE =======================
            elif tag == "FILE":
                msg_id = recv_line(server)
                fname = recv_line(server)
                size = int(recv_line(server))
                sender = recv_line(server)

                if size > 0:
                    data = b""
                    while len(data) < size:
                        data += server.recv(size - len(data))
                    with open(fname, "wb") as f:
                        f.write(data)

                print(f"<{sender}> gui file: {fname}")

            # ======================== VIDEO ======================
            elif tag == "VIDEO":
                msg_id = recv_line(server)
                fname = recv_line(server)
                size = int(recv_line(server))
                sender = recv_line(server)

                data = b""
                while len(data) < size:
                    data += server.recv(size - len(data))

                with open(fname, "wb") as f:
                    f.write(data)

                print(f"<{sender}> gui VIDEO: {fname}")

            # ===================== USERLIST ======================
            elif tag == "USERLIST":
                payload = recv_line(server)
                users = payload.split(",") if payload else []
                print("Nguoi trong phong:", ", ".join(users))

            # ======================== REACT ======================
            elif tag == "REACT":
                msg_id = recv_line(server)
                sender = recv_line(server)
                emoji = recv_line(server)
                print(f"[{sender}] reacted {emoji} to {msg_id}")

            # ======================== RECALL =====================
            elif tag == "RECALL":
                msg_id = recv_line(server)
                sender = recv_line(server)
                print(f"[{sender}] da go tin nhan {msg_id}")

            # ======================== READ =======================
            elif tag == "READ":
                msg_id = recv_line(server)
                reader = recv_line(server)
                # (CLI không cần in)

            # ======================== TYPING =====================
            elif tag == "TYPING":
                who = recv_line(server)
                st = recv_line(server)
                # (CLI không cần in)

            else:
                print(tag)

        except Exception as e:
            print("Loi:", e)
            break


threading.Thread(target=receive, daemon=True).start()

# ======================= GỬI =======================
while True:
    try:
        raw = input()
        if not raw:
            continue

        if raw.startswith("/react "):
            _, msgid, emo = raw.split(" ", 2)
            send_line(server, "REACT")
            send_line(server, msgid)
            send_line(server, emo)
            continue

        if raw.startswith("/recall "):
            _, msgid = raw.split(" ", 1)
            send_line(server, "RECALL")
            send_line(server, msgid)
            continue

        if raw.startswith("/reply "):
            _, msgid, text = raw.split(" ", 2)
            mid = uuid.uuid4().hex
            send_line(server, "REPLY")
            send_line(server, msgid)
            send_line(server, mid)
            send_line(server, str(len(text.encode())))
            server.sendall(text.encode())
            continue

        send_line(server, "MSG")
        msg_id = uuid.uuid4().hex
        payload = raw.encode()
        send_line(server, msg_id)
        send_line(server, "0")
        send_line(server, str(len(payload)))
        server.sendall(payload)

    except KeyboardInterrupt:
        break
