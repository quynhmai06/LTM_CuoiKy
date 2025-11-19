import socket
import sys
import time
import os
import threading
import uuid

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

IP_address = "127.0.0.1"
port = 12345

server.connect((IP_address, port))
print("Da ket noi toi server")

user_id = input("Nhap ten nguoi dung: ")
room_id = input("Nhap room id: ")

server.send(str.encode(user_id))
time.sleep(0.1)
server.send(str.encode(room_id))

welcome_msg = server.recv(1024).decode()
print(welcome_msg)

def receive():
    while True:
        try:
            message = server.recv(1024)
            if not message:
                break
            decoded = message.decode(errors="ignore")

            if decoded == "MSG":
                msg_id = server.recv(1024).decode(errors="ignore")
                ttl_ms = server.recv(1024).decode(errors="ignore")     
                sender = server.recv(1024).decode(errors="ignore")
                content_len = int(server.recv(1024).decode(errors="ignore"))

                buf = b""
                while len(buf) < content_len:
                    chunk = server.recv(min(4096, content_len - len(buf)))
                    if not chunk:
                        break
                    buf += chunk
                text = buf.decode(errors="ignore")
                print(f"<{sender}> {text}")

            elif decoded == "IMAGE":
                msg_id = server.recv(1024).decode()
                size_str = server.recv(1024).decode(errors="ignore")
                total_len = int(size_str)
                sender = server.recv(1024).decode(errors="ignore")

                img_data = b""
                while len(img_data) < total_len:
                    chunk = server.recv(min(4096, total_len - len(img_data)))
                    if not chunk:
                        break
                    img_data += chunk


                filename = f"image_from_{sender}_{msg_id}_{int(time.time())}.bin"
                with open(filename, "wb") as f:
                    f.write(img_data)
                print(f"<{sender}> da gui 1 anh (luu vao {filename})")

            elif decoded == "FILE":
                msg_id = server.recv(1024).decode()
                file_name = server.recv(1024).decode()
                print(f"DEBUG: Receiving FILE id={msg_id} name={file_name}")
                lenOfFile = int(server.recv(1024).decode())
                send_user = server.recv(1024).decode()

                if lenOfFile > 0 and os.path.exists(file_name):
                    os.remove(file_name)

                total = 0
                if lenOfFile > 0:
                    with open(file_name, 'wb') as f:
                        while total < lenOfFile:
                            data = server.recv(min(4096, lenOfFile - total))
                            if not data:
                                break
                            total += len(data)
                            f.write(data)
                print(f"<{send_user}> {file_name} da nhan")

            elif decoded == "VIDEO":
                msg_id = server.recv(1024).decode()
                file_name = server.recv(1024).decode()
                print(f"DEBUG: Receiving VIDEO id={msg_id} name={file_name}")
                lenOfFile = int(server.recv(1024).decode())
                send_user = server.recv(1024).decode()

                if lenOfFile > 0 and os.path.exists(file_name):
                    os.remove(file_name)

                total = 0
                if lenOfFile > 0:
                    with open(file_name, "wb") as f:
                        while total < lenOfFile:
                            data = server.recv(min(4096, lenOfFile - total))
                            if not data:
                                break
                            total += len(data)
                            f.write(data)

                print(f"<{send_user}> video {file_name} da nhan")

            elif decoded.startswith("USERLIST"):
                rest = decoded[len("USERLIST"):]
                if not rest:
                    rest = server.recv(4096).decode(errors="ignore")
                users = [u.strip() for u in rest.split(",") if u.strip()]
                print("Nguoi trong phong:", ", ".join(users))


            elif decoded == "READ":
                _msg_id = server.recv(1024).decode(errors="ignore")
                _reader = server.recv(1024).decode(errors="ignore")

            elif decoded == "RECALL":
                msg_id = server.recv(1024).decode(errors="ignore")
                who = server.recv(1024).decode(errors="ignore")
                print(f"[{who}] da go 1 tin nhan (id {msg_id})")

            elif decoded == "REPLY":
                reply_to = server.recv(1024).decode(errors="ignore")
                msg_id = server.recv(1024).decode(errors="ignore")
                sender = server.recv(1024).decode(errors="ignore")
                content_len = int(server.recv(1024).decode(errors="ignore"))
                buf = b""
                while len(buf) < content_len:
                    chunk = server.recv(min(4096, content_len - len(buf)))
                    if not chunk:
                        break
                    buf += chunk
                text = buf.decode(errors="ignore")
                print(f"<{sender}> (reply to {reply_to}) {text}")

            elif decoded == "REACT":
                msg_id = server.recv(1024).decode(errors="ignore")
                who = server.recv(1024).decode(errors="ignore")
                emoji = server.recv(1024).decode(errors="ignore")
                print(f"[{who}] reacted to {msg_id}: {emoji}")

            elif decoded == "TYPING":
                sender = server.recv(1024).decode(errors="ignore")
                status = server.recv(1024).decode(errors="ignore")

            else:
                print(decoded)

        except Exception as e:
            print("Loi khi nhan:", repr(e))
            break



recv_thread = threading.Thread(target=receive, daemon=True)
recv_thread.start()

try:
    while True:
        message = sys.stdin.readline()
        if not message:
            continue

        # CLI commands: /react <msg_id> <emoji>, /reply <msg_id> <text>, /recall <msg_id>
        if message.strip().startswith("/react "):
            parts = message.strip().split(" ", 2)
            if len(parts) < 3:
                print("Usage: /react <msg_id> <emoji>")
                continue
            msgid, emoji = parts[1], parts[2]
            server.send(b"REACT")
            time.sleep(0.02)
            server.send(msgid.encode())
            time.sleep(0.02)
            server.send(emoji.encode("utf-8"))
            continue
        if message.strip().startswith("/recall "):
            parts = message.strip().split(" ", 1)
            if len(parts) < 2:
                print("Usage: /recall <msg_id>")
                continue
            msgid = parts[1]
            server.send(b"RECALL")
            time.sleep(0.02)
            server.send(msgid.encode())
            continue
        if message.strip().startswith("/reply "):
            parts = message.strip().split(" ", 2)
            if len(parts) < 3:
                print("Usage: /reply <msg_id> <text>")
                continue
            reply_to = parts[1]
            reply_text = parts[2]
            new_msg_id = uuid.uuid4().hex
            server.send(b"REPLY")
            time.sleep(0.02)
            server.send(reply_to.encode())
            time.sleep(0.02)
            server.send(new_msg_id.encode())
            time.sleep(0.02)
            server.send(str(len(reply_text.encode())).encode())
            time.sleep(0.02)
            server.send(reply_text.encode())
            continue
        if message.strip() == "FILE":
            file_name = input("Nhap ten file: ")
            if not os.path.exists(file_name):
                print(f"File '{file_name}' khong ton tai hoac duong dan khong chinh xac.")
                continue
            ext = os.path.splitext(file_name)[1].lower()
            video_exts = [".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv"]

            tag = "VIDEO" if ext in video_exts else "FILE"

            # include msg_id for files and videos
            msg_id = uuid.uuid4().hex
            server.send(tag.encode())
            time.sleep(0.02)
            server.send(msg_id.encode())
            print(f"DEBUG: sending tag={tag}")
            time.sleep(0.1)

            dest_name = "client_" + file_name
            server.send(dest_name.encode())
            print(f"DEBUG: sending name={dest_name}")
            time.sleep(0.1)
            server.send(str(os.path.getsize(file_name)).encode())
            print(f"DEBUG: sending size={os.path.getsize(file_name)}")
            time.sleep(0.1)

            with open(file_name, "rb") as file:
                data = file.read(1024)
                while data:
                    server.send(data)
                    data = file.read(1024)
            sys.stdout.write("<Ban>")
            sys.stdout.write(f"{tag} da gui\n")
            sys.stdout.flush()
        else:
            server.send(message.encode())
            sys.stdout.write("<Ban>")
            sys.stdout.write(message)
            sys.stdout.flush()
except KeyboardInterrupt:
    pass
finally:
    try:
        server.close()
    except:
        pass

