import socket 
from _thread import *
import sys
from collections import defaultdict as df
import time

class Server:
    def __init__(self):
        self.rooms = df(list)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def accept_connections(self, ip_address, port):
        self.ip_address = ip_address
        self.port = port
        self.server.bind((self.ip_address, int(self.port)))
        self.server.listen(100)
        print(f"Server dang lang nghe {self.ip_address}:{self.port}")

        try:
            while True:
                connection, address = self.server.accept()
                print(str(address[0]) + ":" + str(address[1]) + " Da ket noi")

                start_new_thread(self.clientThread, (connection,))
        except KeyboardInterrupt:
            print("Server dang dung (KeyboardInterrupt)")
        except Exception as e:
            print("Loi tren server:", repr(e))
        finally:
            try:
                self.server.close()
            except:
                pass
    
    def clientThread(self, connection):
        user_id = connection.recv(1024).decode().replace("User ", "")
        room_id = connection.recv(1024).decode().replace("Join ", "")

        if room_id not in self.rooms:
            connection.send("Tao phong moi thanh cong".encode())
        else:
            connection.send("Chao mung den phong chat".encode())

        self.rooms[room_id].append(connection)

        while True:
            try:
                header = connection.recv(1024)
                if not header:
                    self.remove(connection, room_id)
                    break

                tag = header.decode(errors="ignore")

                if tag == "FILE":
                    self.broadcastFile(connection, room_id, user_id)

                elif tag == "IMAGE":
                    self.broadcastImage(connection, room_id, user_id)

                else:
                    msg = tag
                    if msg:
                        message_to_send = f"<{user_id}> {msg}"
                        self.broadcast(message_to_send, connection, room_id)
                    else:
                        self.remove(connection, room_id)
                        break

            except Exception as e:
                print("Client da ngat ket noi / loi:", repr(e))
                self.remove(connection, room_id)
                break
    
    def broadcastFile(self, connection, room_id, user_id):
        file_name = connection.recv(1024).decode()
        lenOfFile = connection.recv(1024).decode()
        for client in self.rooms[room_id]:
            if client != connection:
                try: 
                    client.send("FILE".encode())
                    time.sleep(0.1)
                    client.send(file_name.encode())
                    time.sleep(0.1)
                    client.send(lenOfFile.encode())
                    time.sleep(0.1)
                    client.send(user_id.encode())
                except:
                    client.close()
                    self.remove(client, room_id)

        total = 0
        print(file_name, lenOfFile)
        while str(total) != lenOfFile:
            data = connection.recv(1024)
            total = total + len(data)
            for client in self.rooms[room_id]:
                if client != connection:
                    try: 
                        client.send(data)
                        # time.sleep(0.1)
                    except:
                        client.close()
                        self.remove(client, room_id)
        print("Gui file xong")


    def broadcastImage(self, connection, room_id, user_id):
        try:
            size_str = connection.recv(1024).decode(errors="ignore")
            try:
                total_len = int(size_str)
            except:
                total_len = 0
            for client in list(self.rooms[room_id]):
                if client is connection:
                    continue
                try:
                    client.send("IMAGE".encode())
                    time.sleep(0.05)
                    client.send(str(total_len).encode())
                    time.sleep(0.05)
                    client.send(user_id.encode())
                except:
                    client.close()
                    self.remove(client, room_id)
            sent_total = 0
            while sent_total < total_len:
                chunk = connection.recv(min(4096, total_len - sent_total))
                if not chunk:
                    break
                sent_total += len(chunk)
                for client in list(self.rooms[room_id]):
                    if client is connection:
                        continue
                    try:
                        client.send(chunk)
                    except:
                        client.close()
                        self.remove(client, room_id)

            print(f"Gui image xong ({sent_total} bytes) tu {user_id}")
        except Exception as e:
            print("Loi broadcastImage:", repr(e))


    def broadcast(self, message_to_send, connection, room_id):
        for client in self.rooms[room_id]:
            if client != connection:
                try:
                    client.send(message_to_send.encode())
                except:
                    client.close()
                    self.remove(client, room_id)

    def remove(self, connection, room_id):
        if connection in self.rooms[room_id]:
            self.rooms[room_id].remove(connection)

if __name__ == "__main__":
    ip_address = "127.0.0.1"
    port = 12345

    s = Server()
    s.accept_connections(ip_address, port)
