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
        self.usernames = {}
        self.bad_words = [
            "dm", "đm", "dmm", "dcm",
            "vl", "vcl", "ml", "cc",

            "ngu", "đồ ngu",
            "khùng", "khung",
            "điên", "thần kinh",

            "mất dạy", "vô học", "láo", "hỗn",

            "do ngu", "mat day", "vo hoc",
            "dien", "khung", "lao",

            "n gu", "n- gu", "nguuu",
            "fuck", "bitch"
]       
        self.violation_count = {}  
        self.muted_until = {}    

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
        user_id = connection.recv(1024).decode().replace("User ", "").strip()
        room_id = connection.recv(1024).decode().replace("Join ", "").strip()

        if room_id not in self.rooms:
            connection.send("Tao phong moi thanh cong".encode())
        else:
            connection.send("Chao mung den phong chat".encode())

        self.rooms[room_id].append(connection)
        self.usernames[connection] = user_id         
        self.broadcast_userlist(room_id)

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
                elif tag == "MSG":
                    self.broadcastMsg(connection, room_id, user_id)
                elif tag == "RECALL":
                    self.broadcastRecall(connection, room_id, user_id)
                elif tag == "ACK":
                    self.handleAck(connection, room_id, user_id)
                elif tag.startswith("TYPING"):
                    raw = tag[len("TYPING"):].strip()

                    if raw == "":
                        raw = connection.recv(1024).decode(errors="ignore").strip()

                    status = raw
                    self.handleTyping(connection, room_id, user_id, status)

                else:
                    msg = tag
                    if msg:
                        message_to_send = f"<{user_id}> {msg}"
                        self.broadcast(message_to_send, connection, room_id)
                    else:
                        self.remove(connection, room_id)
                        break

            except ConnectionResetError:
                print(f"{user_id} đã ngắt kết nối (đóng ứng dụng).")
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

    def broadcastMsg(self, connection, room_id, user_id):
        try:
            msg_id = connection.recv(1024).decode(errors="ignore")
            ttl_ms = connection.recv(1024).decode(errors="ignore")
            content_len = int(connection.recv(1024).decode(errors="ignore"))

            full_data = b""
            total = 0
            while total < content_len:
                chunk = connection.recv(min(4096, content_len - total))
                if not chunk:
                    break
                total += len(chunk)
                full_data += chunk

            text = full_data.decode(errors="ignore")

            now = time.time()
            mute_until = self.muted_until.get(user_id, 0)
            if mute_until > now:
                remaining = int(mute_until - now)
                if remaining < 0:
                    remaining = 0
                try:
                    connection.send(
                        f"<Server> ⛔ Bạn đang bị chặn gửi tin trong {remaining}s do vi phạm ngôn từ.".encode()
                    )
                except:
                    pass
                return

            text, violated = self.filter_and_check(text)

            if violated:
                cnt = self.violation_count.get(user_id, 0) + 1
                self.violation_count[user_id] = cnt

                if cnt >= 3:
                    self.muted_until[user_id] = time.time() + 30
                    self.violation_count[user_id] = 0
                    warn = "<Server> ⛔ Bạn đã bị tạm khóa gửi tin 30 giây do gửi nhiều tin nhắn không phù hợp."
                else:
                    warn = "<Server> ⚠️ Tin nhắn của bạn chứa ngôn từ không phù hợp!"

                try:
                    connection.send(warn.encode())
                except:
                    pass

            clean_bytes = text.encode()
            clean_len = len(clean_bytes)

            for client in list(self.rooms[room_id]):
                if client is connection:
                    continue
                try:
                    client.send(b"MSG");                  time.sleep(0.02)
                    client.send(msg_id.encode());         time.sleep(0.02)
                    client.send(ttl_ms.encode());         time.sleep(0.02)
                    client.send(user_id.encode());        time.sleep(0.02)
                    client.send(str(clean_len).encode()); time.sleep(0.02)
                    client.send(clean_bytes)
                except:
                    try:
                        client.close()
                    finally:
                        self.remove(client, room_id)

        except Exception as e:
            print("Loi broadcastMsg:", repr(e))



    def filter_and_check(self, text):
        original_lower = text.lower()
        violated = False

        for w in self.bad_words:
            if w in original_lower:
                violated = True
                text = text.replace(w, "***")
                text = text.replace(w.upper(), "***")
                text = text.replace(w.capitalize(), "***")

        return text, violated


    def broadcastRecall(self, connection, room_id, user_id):
        try:
            msg_id = connection.recv(1024).decode(errors="ignore")
            for client in list(self.rooms[room_id]):
                try:
                    client.send(b"RECALL");        time.sleep(0.02)
                    client.send(msg_id.encode());  time.sleep(0.02)
                    client.send(user_id.encode()); time.sleep(0.02)
                except:
                    try: client.close()
                    finally: self.remove(client, room_id)
            print(f"{user_id} recall {msg_id}")
        except Exception as e:
            print("Loi broadcastRecall:", repr(e))

    def handleAck(self, connection, room_id, user_id):
        try:
            msg_id = connection.recv(1024).decode(errors="ignore")
            for client in list(self.rooms[room_id]):
                try:
                    client.send(b"READ");          time.sleep(0.02)
                    client.send(msg_id.encode());  time.sleep(0.02)
                    client.send(user_id.encode()); time.sleep(0.02)
                except:
                    try: client.close()
                    finally: self.remove(client, room_id)
        except Exception as e:
            print("Loi handleAck:", repr(e))

    def handleTyping(self, connection, room_id, user_id, status):
        try:
            for client in list(self.rooms[room_id]):
                if client is connection:
                    continue
                client.send(b"TYPING")
                time.sleep(0.02)
                client.send(user_id.encode())
                time.sleep(0.02)
                client.send(status.encode())
        except Exception as e:
            print("Loi handleTyping:", repr(e))


    def broadcast_userlist(self, room_id):
        """Gửi danh sách user trong phòng cho tất cả client trong phòng."""
        try:
            users = []
            for conn in self.rooms[room_id]:
                uid = self.usernames.get(conn, "Unknown")
                users.append(uid)
            payload = ",".join(users)
            for client in list(self.rooms[room_id]):
                try:
                    client.send(b"USERLIST");      time.sleep(0.02)
                    client.send(payload.encode()); time.sleep(0.02)
                except:
                    try: client.close()
                    finally: self.remove(client, room_id)
            print(f"USERLIST room {room_id}: {payload}")
        except Exception as e:
            print("Loi broadcast_userlist:", repr(e))




    def broadcast(self, message_to_send, connection, room_id):
        for client in self.rooms[room_id]:
            if client != connection:
                try:
                    client.send(message_to_send.encode())
                except:
                    client.close()
                    self.remove(client, room_id)

    def remove(self, connection, room_id):
        try:
            uid = self.usernames.pop(connection, None)
        except Exception:
            uid = None

        if room_id in self.rooms and connection in self.rooms[room_id]:
            self.rooms[room_id].remove(connection)

        if room_id in self.rooms:
            self.broadcast_userlist(room_id)

        if uid:
            print(f"{uid} đã rời phòng {room_id}")
        else:
            print(f"Một client đã rời phòng {room_id}")




if __name__ == "__main__":
    ip_address = "127.0.0.1"
    port = 12345

    s = Server()
    s.accept_connections(ip_address, port)
