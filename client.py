import socket
import sys
import time
import os
import threading

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
                size_str = server.recv(1024).decode(errors="ignore")
                total_len = int(size_str)
                sender = server.recv(1024).decode(errors="ignore")

                img_data = b""
                while len(img_data) < total_len:
                    chunk = server.recv(min(4096, total_len - len(img_data)))
                    if not chunk:
                        break
                    img_data += chunk


                filename = f"image_from_{sender}_{int(time.time())}.bin"
                with open(filename, "wb") as f:
                    f.write(img_data)
                print(f"<{sender}> da gui 1 anh (luu vao {filename})")

            elif decoded == "FILE":
                file_name = server.recv(1024).decode()
                lenOfFile = server.recv(1024).decode()
                send_user = server.recv(1024).decode()

                if os.path.exists(file_name):
                    os.remove(file_name)

                total = 0
                with open(file_name, 'wb') as f:
                    while str(total) != lenOfFile:
                        data = server.recv(1024)
                        total = total + len(data)
                        f.write(data)
                print(f"<{send_user}> {file_name} da nhan")

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

        if message.strip() == "FILE":
            file_name = input("Nhap ten file: ")
            server.send("FILE".encode())
            time.sleep(0.1)
            server.send(str("client_" + file_name).encode())
            time.sleep(0.1)
            server.send(str(os.path.getsize(file_name)).encode())
            time.sleep(0.1)

            with open(file_name, "rb") as file:
                data = file.read(1024)
                while data:
                    server.send(data)
                    data = file.read(1024)
            sys.stdout.write("<Ban>")
            sys.stdout.write("File da gui\n")
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

