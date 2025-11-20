import socket
from _thread import start_new_thread
from collections import defaultdict as df
import time
import os
import json
from pathlib import Path
import base64
import uuid

# =============== LƯU LỊCH SỬ RA FILE JSONL ===============
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


def save_message(room_id, user, msg_type, content):
    """
    Lưu 1 bản ghi tin nhắn vào file JSONL: logs/room_<room_id>.jsonl
    msg_type: "text" | "file" | "image" | "react" | "video"
    """
    fp = LOG_DIR / f"room_{room_id}.jsonl"
    record = {
        "user": user,
        "type": msg_type,
        "content": content,
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
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
        except Exception:
            pass
    return out


class Server:
    def __init__(self):
        self.rooms = df(list)      # room_id -> list[connection]
        self.usernames = {}        # connection -> user_id
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Lưu history in-memory (nếu cần)
        self.room_history = df(list)   # room_id -> list[(timestamp, sender, text)]
        self.max_history = 100

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
            "fuck", "bitch",
        ]
        self.violation_count = {}  # user_id -> số lần vi phạm
        self.muted_until = {}      # user_id -> timestamp bị mute đến khi nào

    # --------- HÀM TIỆN ÍCH GỬI / NHẬN 1 DÒNG ---------
    def send_line(self, conn, text: str):
        """
        Gửi 1 dòng kết thúc bởi '\n'
        """
        conn.sendall((text + "\n").encode())

    def recv_line(self, conn) -> str:
        """
        Đọc 1 dòng kết thúc bởi '\n'
        """
        buf = b""
        while b"\n" not in buf:
            chunk = conn.recv(1)
            if not chunk:
                break
            buf += chunk
        return buf.decode(errors="ignore").strip()

    # ---------------------------------------------------

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
            except Exception:
                pass

    def clientThread(self, connection):
        # ======= HANDSHAKE: username + room_id theo dạng line =======
        try:
            user_id = self.recv_line(connection)
            room_id = self.recv_line(connection)
        except Exception:
            connection.close()
            return

        room_id = room_id.replace("Join ", "", 1).strip()
        if not room_id:
            room_id = "0"

        self.rooms[room_id].append(connection)
        self.usernames[connection] = user_id

        # Gửi userlist và history cho client mới
        time.sleep(0.1)
        self.broadcast_userlist(room_id)
        time.sleep(0.15)
        self._send_history_to_client(connection, room_id)

        # ================== VÒNG LẶP XỬ LÝ ==================
        while True:
            try:
                tag = self.recv_line(connection)
                if not tag:
                    self.remove(connection, room_id)
                    break

                print(f"[Server] Received tag from {user_id}: {tag}")

                if tag == "FILE":
                    self.broadcastFile(connection, room_id, user_id)

                elif tag == "VIDEO":
                    self.broadcastVideo(connection, room_id, user_id)

                elif tag == "IMAGE":
                    self.broadcastImage(connection, room_id, user_id)

                elif tag == "MSG":
                    self.broadcastMsg(connection, room_id, user_id)

                elif tag == "REPLY":
                    self.broadcastReply(connection, room_id, user_id)

                elif tag == "REACT":
                    self.broadcastReact(connection, room_id, user_id)

                elif tag == "RECALL":
                    self.broadcastRecall(connection, room_id, user_id)

                elif tag == "ACK":
                    self.handleAck(connection, room_id, user_id)

                elif tag == "TYPING":
                    status = self.recv_line(connection)
                    self.handleTyping(connection, room_id, user_id, status)

                else:
                    # fallback tin nhắn kiểu rất cũ (không dùng header)
                    msg = tag.strip()
                    if msg:
                        self._store_history(room_id, user_id, msg)
                        save_message(
                            room_id,
                            user_id,
                            "text",
                            {"msg_id": uuid.uuid4().hex, "text": msg},
                        )
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

    # ---------------------- FILE ------------------------
    def broadcastFile(self, connection, room_id, user_id):
        # New protocol: FILE frame includes msg_id, file_name, lenOfFile bằng line
        msg_id = self.recv_line(connection)
        file_name = self.recv_line(connection)
        lenOfFile_str = self.recv_line(connection)
        try:
            lenOfFile = int(lenOfFile_str)
        except Exception:
            lenOfFile = 0

        print(f"[Server] broadcastFile from {user_id}: {file_name} len={lenOfFile}")
        # Gửi header cho các client khác
        for client in list(self.rooms[room_id]):
            if client is connection:
                continue
            try:
                self.send_line(client, "FILE")
                self.send_line(client, msg_id)
                self.send_line(client, file_name)
                self.send_line(client, str(lenOfFile))
                self.send_line(client, user_id)
            except Exception:
                client.close()
                self.remove(client, room_id)

        # Relay dữ liệu file
        total = 0
        while total < lenOfFile:
            data = connection.recv(min(4096, lenOfFile - total))
            if not data:
                break
            total += len(data)
            for client in list(self.rooms[room_id]):
                if client is connection:
                    continue
                try:
                    client.sendall(data)
                except Exception:
                    client.close()
                    self.remove(client, room_id)
        print("Gui file xong")

        # Lưu history FILE
        try:
            self._store_history(room_id, user_id, f"[FILE] {file_name}")
            save_message(room_id, user_id, "file", {
                "msg_id": msg_id,
                "file_name": file_name,
            })
        except Exception as e:
            print("Loi luu history file:", e)

    # ---------------------- VIDEO ------------------------
    def broadcastVideo(self, connection, room_id, user_id):
        try:
            msg_id = self.recv_line(connection)
            file_name = self.recv_line(connection)
            lenOfFile_str = self.recv_line(connection)
            try:
                length = int(lenOfFile_str)
            except Exception:
                length = 0

            print(f"[Server] broadcastVideo from {user_id}: {file_name} len={length}")

            # header
            for client in list(self.rooms[room_id]):
                if client is connection:
                    continue
                try:
                    self.send_line(client, "VIDEO")
                    self.send_line(client, msg_id)
                    self.send_line(client, file_name)
                    self.send_line(client, str(length))
                    self.send_line(client, user_id)
                except Exception:
                    client.close()
                    self.remove(client, room_id)

            total = 0
            while total < length:
                data = connection.recv(min(4096, length - total))
                if not data:
                    break
                total += len(data)
                for client in list(self.rooms[room_id]):
                    if client is connection:
                        continue
                    try:
                        client.sendall(data)
                    except Exception:
                        client.close()
                        self.remove(client, room_id)
            print(f"Gui video xong: {file_name} ({total} bytes)")

            # history
            try:
                self._store_history(room_id, user_id, f"[VIDEO] {file_name}")
                save_message(room_id, user_id, "video", {
                    "msg_id": msg_id,
                    "file_name": file_name,
                })
            except Exception as e:
                print("Loi luu history video:", e)

        except Exception as e:
            print("Loi broadcastVideo:", e)

    # ---------------------- IMAGE ------------------------
    def broadcastImage(self, connection, room_id, user_id):
        try:
            msg_id = self.recv_line(connection)
            size_str = self.recv_line(connection)
            try:
                total_len = int(size_str)
            except Exception:
                total_len = 0

            print(f"[Server] broadcastImage from {user_id} size={total_len}")

            # header IMAGE cho các client khác
            for client in list(self.rooms[room_id]):
                if client is connection:
                    continue
                try:
                    self.send_line(client, "IMAGE")
                    self.send_line(client, msg_id)
                    self.send_line(client, str(total_len))
                    self.send_line(client, user_id)
                except Exception:
                    client.close()
                    self.remove(client, room_id)

            sent_total = 0
            image_data = b""
            while sent_total < total_len:
                chunk = connection.recv(min(4096, total_len - sent_total))
                if not chunk:
                    break
                sent_total += len(chunk)
                image_data += chunk
                for client in list(self.rooms[room_id]):
                    if client is connection:
                        continue
                    try:
                        client.sendall(chunk)
                    except Exception:
                        client.close()
                        self.remove(client, room_id)
            print(f"Gui image xong ({sent_total} bytes) tu {user_id}")

            # lưu history
            try:
                if image_data:
                    b64 = base64.b64encode(image_data).decode("ascii")
                    save_message(
                        room_id,
                        user_id,
                        "image",
                        {"msg_id": msg_id, "size": sent_total, "data": b64},
                    )
                    self._store_history(room_id, user_id, f"[IMAGE] {sent_total} bytes")
            except Exception as e:
                print("Loi luu history image:", e)

        except Exception as e:
            print("Loi broadcastImage:", repr(e))

    # ---------------------- MSG TEXT ------------------------
    def broadcastMsg(self, connection, room_id, user_id):
        try:
            msg_id = self.recv_line(connection)
            ttl_ms = self.recv_line(connection)
            content_len_str = self.recv_line(connection)
            try:
                content_len = int(content_len_str)
            except Exception:
                content_len = 0

            buf = b""
            while len(buf) < content_len:
                chunk = connection.recv(min(4096, content_len - len(buf)))
                if not chunk:
                    break
                buf += chunk
            text = buf.decode(errors="ignore")

            # CHECK MUTE / FILTER BAD WORDS
            now = time.time()
            mute_until = self.muted_until.get(user_id, 0)
            if mute_until > now:
                remaining = int(mute_until - now)
                if remaining < 0:
                    remaining = 0
                try:
                    self.send_line(
                        connection,
                        f"<Server> ⛔ Bạn đang bị chặn gửi tin trong {remaining}s do vi phạm ngôn từ."
                    )
                except Exception:
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
                    self.send_line(connection, warn)
                except Exception:
                    pass

            # Lưu lịch sử
            self._store_history(room_id, user_id, text)
            save_message(
                room_id,
                user_id,
                "text",
                {"msg_id": msg_id, "text": text},
            )

            clean_bytes = text.encode("utf-8")
            clean_len = len(clean_bytes)

            for client in list(self.rooms[room_id]):
                if client is connection:
                    continue
                try:
                    self.send_line(client, "MSG")
                    self.send_line(client, msg_id)
                    self.send_line(client, ttl_ms)
                    self.send_line(client, user_id)
                    self.send_line(client, str(clean_len))
                    client.sendall(clean_bytes)
                except Exception:
                    client.close()
                    self.remove(client, room_id)

        except Exception as e:
            print("Loi broadcastMsg:", repr(e))

    # ---------------------- REPLY ------------------------
    def broadcastReply(self, connection, room_id, user_id):
        try:
            reply_to = self.recv_line(connection)
            msg_id = self.recv_line(connection)
            content_len_str = self.recv_line(connection)
            try:
                content_len = int(content_len_str)
            except Exception:
                content_len = 0

            buf = b""
            while len(buf) < content_len:
                chunk = connection.recv(min(4096, content_len - len(buf)))
                if not chunk:
                    break
                buf += chunk
            text = buf.decode(errors="ignore")

            print(f"[Server] broadcastReply: {user_id} -> reply_to={reply_to} msg_id={msg_id} len={len(text)}")

            # MUTE + FILTER
            now = time.time()
            mute_until = self.muted_until.get(user_id, 0)
            if mute_until > now:
                remaining = int(mute_until - now)
                if remaining < 0:
                    remaining = 0
                try:
                    self.send_line(
                        connection,
                        f"<Server> ⛔ Bạn đang bị chặn gửi tin trong {remaining}s do vi phạm ngôn từ."
                    )
                except Exception:
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
                    self.send_line(connection, warn)
                except Exception:
                    pass

            # Lưu history
            try:
                self._store_history(room_id, user_id, text)
                save_message(
                    room_id,
                    user_id,
                    "text",
                    {"msg_id": msg_id, "text": text},
                )
            except Exception as e:
                print("Loi luu history reply:", e)

            clean_bytes = text.encode("utf-8")
            clean_len = len(clean_bytes)

            for client in list(self.rooms[room_id]):
                if client is connection:
                    continue
                try:
                    self.send_line(client, "REPLY")
                    self.send_line(client, reply_to)
                    self.send_line(client, msg_id)
                    self.send_line(client, user_id)
                    self.send_line(client, str(clean_len))
                    client.sendall(clean_bytes)
                except Exception:
                    client.close()
                    self.remove(client, room_id)

        except Exception as e:
            print("Loi broadcastReply:", repr(e))

    # ---------------------- REACT ------------------------
    def broadcastReact(self, connection, room_id, user_id):
        try:
            msg_id = self.recv_line(connection)
            reaction = self.recv_line(connection)

            allowed = {"👍", "❤️", "😆", "😢", "😮"}
            if reaction not in allowed:
                return

            print(f"[Server] broadcastReact: from {user_id} to {msg_id} reaction={reaction}")

            # Lưu history
            try:
                save_message(
                    room_id,
                    user_id,
                    "react",
                    {"msg_id": msg_id, "reaction": reaction},
                )
            except Exception as e:
                print("Loi luu history react:", e)

            for client in list(self.rooms[room_id]):
                if client is connection:
                    continue
                try:
                    self.send_line(client, "REACT")
                    self.send_line(client, msg_id)
                    self.send_line(client, user_id)
                    self.send_line(client, reaction)
                except Exception:
                    client.close()
                    self.remove(client, room_id)

        except Exception as e:
            print("Loi broadcastReact:", e)

    # ---------------------- FILTER BAD WORDS ------------------------
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

    # ---------------------- RECALL ------------------------
    def broadcastRecall(self, connection, room_id, user_id):
        try:
            msg_id = self.recv_line(connection)
            print(f"[Server] broadcastRecall: from {user_id} msg_id={msg_id}")
            for client in list(self.rooms[room_id]):
                try:
                    self.send_line(client, "RECALL")
                    self.send_line(client, msg_id)
                    self.send_line(client, user_id)
                except Exception:
                    client.close()
                    self.remove(client, room_id)
            print(f"{user_id} recall {msg_id}")
        except Exception as e:
            print("Loi broadcastRecall:", e)

    # ---------------------- ACK / READ ------------------------
    def handleAck(self, connection, room_id, user_id):
        try:
            msg_id = self.recv_line(connection)
            for client in list(self.rooms[room_id]):
                try:
                    # Gửi READ <msg_id> rồi dòng tiếp là user đọc
                    self.send_line(client, f"READ {msg_id}")
                    self.send_line(client, user_id)
                except Exception:
                    client.close()
                    self.remove(client, room_id)
        except Exception as e:
            print("Loi handleAck:", e)

    # ---------------------- TYPING ------------------------
    def handleTyping(self, connection, room_id, user_id, status):
        try:
            for client in list(self.rooms[room_id]):
                if client is connection:
                    continue
                self.send_line(client, "TYPING")
                self.send_line(client, user_id)
                self.send_line(client, status)
        except Exception as e:
            print("Loi handleTyping:", e)

    # ---------------------- USERLIST ------------------------
    def broadcast_userlist(self, room_id):
        """
        Gửi danh sách user trong phòng: 'USERLIST user1,user2,...'
        """
        try:
            users = []
            for conn in self.rooms[room_id]:
                uid = self.usernames.get(conn, "Unknown")
                users.append(uid)
            payload = ",".join(users)
            for client in list(self.rooms[room_id]):
                try:
                    self.send_line(client, f"USERLIST {payload}")
                except Exception:
                    client.close()
                    self.remove(client, room_id)
            print(f"USERLIST room {room_id}: {payload}")
        except Exception as e:
            print("Loi broadcast_userlist:", repr(e))

    # ---------------------- BROADCAST TEXT CŨ ------------------------
    def broadcast(self, message_to_send, connection, room_id):
        for client in list(self.rooms[room_id]):
            if client is connection:
                continue
            try:
                client.send(message_to_send.encode())
            except Exception:
                client.close()
                self.remove(client, room_id)

    # ---------------------- REMOVE CLIENT ------------------------
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
        Gửi lại lịch sử phòng cho 1 client mới vào
        """
        history = get_recent_messages(room_id, limit=50)
        if not history:
            return

        try:
            for r in history:
                typ = r.get("type")
                user = r.get("user", "???")
                content = r.get("content")

                # TEXT
                if typ == "text":
                    if isinstance(content, dict):
                        msg_id = content.get("msg_id") or uuid.uuid4().hex
                        text = content.get("text", "")
                    else:
                        msg_id = uuid.uuid4().hex
                        text = str(content) if content is not None else ""

                    if not text:
                        continue

                    data = text.encode("utf-8")
                    ttl_ms = "-1"  # history

                    self.send_line(connection, "MSG")
                    time.sleep(0.02)
                    self.send_line(connection, msg_id)
                    time.sleep(0.02)
                    self.send_line(connection, ttl_ms)
                    time.sleep(0.02)
                    self.send_line(connection, user)
                    time.sleep(0.02)
                    self.send_line(connection, str(len(data)))
                    time.sleep(0.02)
                    connection.sendall(data)
                    time.sleep(0.02)
                    continue

                # IMAGE
                elif typ == "image" and isinstance(content, dict):
                    msg_id = content.get("msg_id", uuid.uuid4().hex)
                    b64 = content.get("data", "")
                    try:
                        img_bytes = base64.b64decode(b64.encode("ascii"))
                    except Exception:
                        continue

                    size = len(img_bytes)
                    self.send_line(connection, "IMAGE")
                    time.sleep(0.02)
                    self.send_line(connection, msg_id)
                    time.sleep(0.02)
                    self.send_line(connection, str(size))
                    time.sleep(0.02)
                    self.send_line(connection, user)
                    time.sleep(0.02)
                    connection.sendall(img_bytes)
                    time.sleep(0.02)

                # FILE
                elif typ == "file":
                    if isinstance(content, dict):
                        msg_id = content.get("msg_id", uuid.uuid4().hex)
                        file_name = content.get("file_name", "file")
                    else:
                        msg_id = uuid.uuid4().hex
                        file_name = str(content)

                    self.send_line(connection, "FILE")
                    time.sleep(0.02)
                    self.send_line(connection, msg_id)
                    time.sleep(0.02)
                    self.send_line(connection, file_name)
                    time.sleep(0.02)
                    self.send_line(connection, "0")  # len = 0, chỉ show metadata
                    time.sleep(0.02)
                    self.send_line(connection, user)
                    time.sleep(0.02)

                # VIDEO
                elif typ == "video":
                    if isinstance(content, dict):
                        msg_id = content.get("msg_id", uuid.uuid4().hex)
                        file_name = content.get("file_name", "video")
                    else:
                        msg_id = uuid.uuid4().hex
                        file_name = str(content)

                    self.send_line(connection, "VIDEO")
                    time.sleep(0.02)
                    self.send_line(connection, msg_id)
                    time.sleep(0.02)
                    self.send_line(connection, file_name)
                    time.sleep(0.02)
                    self.send_line(connection, "0")
                    time.sleep(0.02)
                    self.send_line(connection, user)
                    time.sleep(0.02)

                # REACTION
                elif typ == "react":
                    msg_id = ""
                    emoji = ""
                    if isinstance(content, dict):
                        msg_id = content.get("msg_id", "")
                        emoji = content.get("reaction", "")
                    else:
                        try:
                            msg_id, emoji = str(content).split("||", 1)
                            msg_id = msg_id.strip()
                            emoji = emoji.strip()
                        except Exception:
                            continue

                    if not msg_id or not emoji:
                        continue

                    self.send_line(connection, "REACT")
                    time.sleep(0.02)
                    self.send_line(connection, msg_id)
                    time.sleep(0.02)
                    self.send_line(connection, user)
                    time.sleep(0.02)
                    self.send_line(connection, emoji)
                    time.sleep(0.02)

        except Exception as e:
            print("Lỗi gửi history:", e)


if __name__ == "__main__":
    ip_address = "127.0.0.1"
    port = 12345
    s = Server()
    s.accept_connections(ip_address, port)
