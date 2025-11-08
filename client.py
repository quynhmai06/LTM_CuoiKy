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
    """Thread: nhan tat ca thong diep tu server va xu ly (tin nhan hoac FILE)."""
    while True:
        try:
            message = server.recv(1024)
            if not message:
                break
            decoded = message.decode()
            if decoded == "FILE":
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
                print("<" + str(send_user) + "> " + file_name + " da nhan")
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

