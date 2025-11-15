import socket
from _thread import *
from collections import defaultdict as df
import time
import os, json
from pathlib import Path

# =============== LƯU LỊCH SỬ RA FILE JSONL ===============
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

def save_message(room_id, user, msg_type, content):
    """
    Lưu 1 bản ghi tin nhắn vào file JSONL: logs/room_<room_id>.jsonl
    msg_type: "text" | "file" | "image"
    """
    fp = LOG_DIR / f"room_{room_id}.jsonl"
    record = {
        "user": user,
        "type": msg_type,
        "content": content,
        "ts": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(fp, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def get_recent_messages(room_id, limit=20):
    """
    Đọc N dòng cuối lịch sử phòng từ file JSONL.
    """
    fp = LOG_DIR / f"room_{room_id}.jsonl"
    if not fp.exists():
        return []
    with open(fp, "r", encoding="utf-8") as f:
        lines = f.readlines()[-limit:]
    out = []
    for line in lines:
        try:
            out.append(json.loads(line))
        except:
            pass
    return out
# ========================================================


class Server:
    def __init__(self):
        self.rooms = df(list)          # room_id -> list[connection]
        self.usernames = {}            # connection -> user_id
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # ========== LƯU LỊCH SỬ TRÊN SERVER (IN-MEMORY) ==========
        # room_id -> list[(timestamp, sender, text)]
        self.room_history = df(list)
        self.max_history = 100  # mỗi phòng giữ tối đa 100 tin nhắn gần nhất
        # ==========================================================

        # từ ngữ xấu
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
        self.violation_count = {}   # user_id -> số lần vi phạm
        self.muted_until = {}       # user_id -> timestamp bị mute đến khi nào

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
        # nhận tên & room_id từ client
        user_id = connection.recv(1024).decode().replace("User ", "").strip()
        room_id = connection.recv(1024).decode().replace("Join ", "").strip()

        # KHÔNG gửi text chào trực tiếp nữa để tránh dính với USERLIST/MSG
        # Chỉ quản lý phòng + userlist + history
        self.rooms[room_id].append(connection)
        self.usernames[connection] = user_id

        # Gửi danh sách user đang trong phòng
        self.broadcast_userlist(room_id)
        time.sleep(0.02)

        # Gửi lại lịch sử tin nhắn cho user mới vào phòng
        # (history gửi theo format "Lich su phong chat" để khớp client hiện tại)
        self._send_history_to_client(connection, room_id)

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
                    # fallback tin nhắn kiểu cũ (không dùng MSG header)
                    msg = tag
                    if msg:
                        # LƯU LỊCH SỬ text kiểu cũ luôn cho đồng bộ
                        self._store_history(room_id, user_id, msg.strip())
                        save_message(room_id, user_id, "text", msg.strip())
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
                    except:
                        client.close()
                        self.remove(client, room_id)
        print("Gui file xong")

        # LƯU LỊCH SỬ FILE
        try:
            self._store_history(room_id, user_id, f"[FILE] {file_name}")
            save_message(room_id, user_id, "file", file_name)
        except Exception as e:
            print("Loi luu history file:", e)

    def broadcastImage(self, connection, room_id, user_id):
        try:
            size_str = connection.recv(1024).decode(errors="ignore")
            try:
                total_len = int(size_str)
            except:
                total_len = 0

            # gửi header image cho mọi client trong phòng
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

            # relay bytes ảnh
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

            # LƯU LỊCH SỬ ẢNH
            try:
                self._store_history(room_id, user_id, f"[IMAGE] {sent_total} bytes")
                save_message(room_id, user_id, "image", f"{sent_total} bytes")
            except Exception as e:
                print("Loi luu history image:", e)

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

            # ====== CHECK MUTE / FILTER BAD WORDS ======
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
            # ===========================================

            # ====== LƯU LỊCH SỬ VĂN BẢN =========
            self._store_history(room_id, user_id, text)
            save_message(room_id, user_id, "text", text)
            # ====================================

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
                    try:
                        client.close()
                    finally:
                        self.remove(client, room_id)
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
                    try:
                        client.close()
                    finally:
                        self.remove(client, room_id)
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
            print("Loi handleTyping:", e)

    def broadcast_userlist(self, room_id):
        """USERLIST: gửi danh sách user trong phòng.
           Format: USERLIST, <len>, <payload>."""
        try:
            users = []
            for conn in self.rooms[room_id]:
                uid = self.usernames.get(conn, "Unknown")
                users.append(uid)
            payload = ",".join(users)
            payload_bytes = payload.encode()

            for client in list(self.rooms[room_id]):
                try:
                    client.send(b"USERLIST");                          time.sleep(0.01)
                    client.send(str(len(payload_bytes)).encode());     time.sleep(0.01)
                    client.send(payload_bytes);                        time.sleep(0.01)
                except:
                    try:
                        client.close()
                    finally:
                        self.remove(client, room_id)
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

    # ========= HÀM LƯU / GỬI LỊCH SỬ =========

    def _store_history(self, room_id, sender, text):
        ts = time.time()
        self.room_history[room_id].append((ts, sender, text))
        if len(self.room_history[room_id]) > self.max_history:
            self.room_history[room_id] = self.room_history[room_id][-self.max_history:]

    def _send_history_to_client(self, connection, room_id):
        """
        Gửi lịch sử phòng cho 1 client mới vào
        THEO ĐÚNG FORMAT: 
        'Lich su phong chat:\\n'
        '[ts] user (type): content'
        để khớp với code client hiện tại của m.
        """
        history = get_recent_messages(room_id, limit=20)
        if not history:
            return

        try:
            # header mà client đang bắt bằng "if 'Lich su phong chat' in tag:"
            connection.send("Lich su phong chat:\n".encode())

            for r in history:
                line = f"[{r['ts']}] {r['user']} ({r['type']}): {r['content']}\n"
                connection.send(line.encode())
                time.sleep(0.005)
        except Exception as e:
            print("Lỗi gửi history:", e)


if __name__ == "__main__":
    ip_address = "127.0.0.1"
    port = 12345

    s = Server()
    s.accept_connections(ip_address, port)
