import socket
from _thread import *
from collections import defaultdict as df
import time
import os, json
from pathlib import Path
import base64
import uuid

# =============== LƯU LỊCH SỬ RA FILE JSONL ===============
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


def save_message(room_id, user, msg_type, content):
    """
    Lưu 1 bản ghi tin nhắn vào file JSONL: logs/room_<room_id>.jsonl
    msg_type: "text" | "file" | "image" | "react"
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
        except:
            pass
    return out


# ========================================================


class Server:
    def __init__(self):
        self.rooms = df(list)  # room_id -> list[connection]
        self.usernames = {}  # connection -> user_id
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
            "fuck", "bitch",
        ]
        self.violation_count = {}  # user_id -> số lần vi phạm
        self.muted_until = {}  # user_id -> timestamp bị mute đến khi nào

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
        # nhận tên & room_id từ client (hỗ trợ cả dạng cũ "User nam", "Join 1")
        user_id = connection.recv(1024).decode(errors="ignore").strip()
        user_id = user_id.replace("User ", "", 1).strip()
        room_id = connection.recv(1024).decode(errors="ignore").strip()
        room_id = room_id.replace("Join ", "", 1).strip()

        if not room_id:
            room_id = "0"

        self.rooms[room_id].append(connection)
        self.usernames[connection] = user_id

        # FIX: Thêm delay và gửi userlist trước, history sau
        time.sleep(0.1)  # Đảm bảo client đã sẵn sàng
        
        # Gửi danh sách user đang trong phòng
        self.broadcast_userlist(room_id)
        
        # Đợi một chút trước khi gửi history để tránh dính packet
        time.sleep(0.15)
        
        # Gửi lại lịch sử tin nhắn cho user mới vào phòng
        self._send_history_to_client(connection, room_id)

        while True:
            try:
                header = connection.recv(1024)
                if not header:
                    self.remove(connection, room_id)
                    break

                tag = header.decode(errors="ignore")
                try:
                    print(f"[Server] Received header from {user_id}: {tag}")
                except Exception:
                    print(f"[Server] Received header: {tag}")

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
                        self._store_history(room_id, user_id, msg.strip())
                        save_message(room_id, user_id, "text", {
                            "msg_id": uuid.uuid4().hex,
                            "text": msg.strip(),
                        })
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
        # New protocol: FILE frame includes msg_id first
        msg_id = connection.recv(1024).decode()
        file_name = connection.recv(1024).decode()
        lenOfFile = int(connection.recv(1024).decode())
        print(f"[Server] broadcastFile started from {user_id}: file_name={file_name} len={lenOfFile}")
        for client in self.rooms[room_id]:
            if client != connection:
                try:
                    client.send("FILE".encode())
                    time.sleep(0.05)
                    client.send(msg_id.encode())
                    time.sleep(0.1)
                    client.send(file_name.encode())
                    time.sleep(0.1)
                    client.send(str(lenOfFile).encode())
                    time.sleep(0.1)
                    client.send(user_id.encode())
                except:
                    client.close()
                    self.remove(client, room_id)

        total = 0
        print(file_name, lenOfFile)
        while total < lenOfFile:
            data = connection.recv(min(4096, lenOfFile - total))
            total = total + len(data)
            if total % (1024 * 50) == 0:
                print(f"[Server] broadcastFile receive progress for {file_name}: {total} bytes")
            for client in self.rooms[room_id]:
                if client != connection:
                    try:
                        client.send(data)
                    except:
                        client.close()
                        self.remove(client, room_id)
        print("Gui file xong")

        # LƯU LỊCH SỬ FILE (gồm msg_id và file_name)
        try:
            self._store_history(room_id, user_id, f"[FILE] {file_name}")
            save_message(room_id, user_id, "file", {"msg_id": msg_id, "file_name": file_name})
        except Exception as e:
            print("Loi luu history file:", e)

    def broadcastVideo(self, connection, room_id, user_id):
        """
        Gửi video cho tất cả client trong phòng.
        Cấu trúc frame giống FILE:
        VIDEO
        <file_name>
        <lenOfFile>
        <user_id>
        <bytes...>
        """
        try:
            # New protocol: VIDEO frame includes msg_id first
            msg_id = connection.recv(1024).decode()
            file_name = connection.recv(1024).decode()
            lenOfFile = connection.recv(1024).decode()
            print(f"[Server] broadcastVideo started from {user_id}: file_name={file_name} len={lenOfFile}")
            length = int(lenOfFile)

            # Gửi header VIDEO cho các client khác
            for client in list(self.rooms[room_id]):
                if client is connection:
                    continue
                try:
                    client.send(b"VIDEO")
                    time.sleep(0.05)
                    client.send(msg_id.encode())
                    time.sleep(0.1)
                    client.send(file_name.encode())
                    time.sleep(0.1)
                    client.send(lenOfFile.encode())
                    time.sleep(0.1)
                    client.send(user_id.encode())
                    time.sleep(0.1)
                except:
                    client.close()
                    self.remove(client, room_id)

            # Relay data video
            total = 0
            while total < length:
                data = connection.recv(min(4096, length - total))
                if not data:
                    break
                total += len(data)
                if total % (1024 * 50) == 0:
                    print(f"[Server] broadcastVideo receive progress for {file_name}: {total} bytes")
                for client in list(self.rooms[room_id]):
                    if client is connection:
                        continue
                    try:
                        client.send(data)
                    except:
                        client.close()
                        self.remove(client, room_id)

            print(f"Gui video xong: {file_name} ({total} bytes)")

            # Lưu history video
            try:
                self._store_history(room_id, user_id, f"[VIDEO] {file_name}")
                save_message(room_id, user_id, "video", {"msg_id": msg_id, "file_name": file_name})
            except Exception as e:
                print("Loi luu history video:", e)

        except Exception as e:
            print("Loi broadcastVideo:", e)

    def broadcastImage(self, connection, room_id, user_id):
        try:
            print(f"[Server] broadcastImage started from {user_id}")
            # New protocol: IMAGE frame includes msg_id first
            msg_id = connection.recv(1024).decode()
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
                    client.send(msg_id.encode())
                    time.sleep(0.05)
                    client.send(str(total_len).encode())
                    time.sleep(0.05)
                    client.send(user_id.encode())
                except:
                    client.close()
                    self.remove(client, room_id)

            # relay bytes ảnh + gom để lưu history
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
                        client.send(chunk)
                    except:
                        client.close()
                        self.remove(client, room_id)

            print(f"Gui image xong ({sent_total} bytes) tu {user_id}")

            # LƯU LỊCH SỬ ẢNH (gồm msg_id)
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

            # CHECK MUTE / FILTER BAD WORDS
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

            # LƯU LỊCH SỬ VĂN BẢN
            self._store_history(room_id, user_id, text)
            save_message(
                room_id,
                user_id,
                "text",
                {"msg_id": msg_id, "text": text},
            )

            clean_bytes = text.encode()
            clean_len = len(clean_bytes)

            for client in list(self.rooms[room_id]):
                if client is connection:
                    continue
                try:
                    client.send(b"MSG")
                    time.sleep(0.02)
                    client.send(msg_id.encode())
                    time.sleep(0.02)
                    client.send(ttl_ms.encode())
                    time.sleep(0.02)
                    client.send(user_id.encode())
                    time.sleep(0.02)
                    client.send(str(clean_len).encode())
                    time.sleep(0.02)
                    client.send(clean_bytes)
                except:
                    try:
                        client.close()
                    finally:
                        self.remove(client, room_id)

        except Exception as e:
            print("Loi broadcastMsg:", repr(e))

    def broadcastReply(self, connection, room_id, user_id):
        try:
            # REPLY
            reply_to = connection.recv(1024).decode(errors="ignore")  # msg_id được reply
            msg_id = connection.recv(1024).decode(errors="ignore")    # msg_id mới
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
            print(f"[Server] broadcastReply: {user_id} -> reply_to={reply_to} msg_id={msg_id} len={len(text)}")

            # CHECK MUTE + FILTER BAD WORDS
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

            # LƯU HISTORY CHO REPLY
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

            clean_bytes = text.encode()
            clean_len = len(clean_bytes)

            # broadcast cho các client khác
            for client in list(self.rooms[room_id]):
                if client is connection:
                    continue
                try:
                    client.send(b"REPLY")
                    time.sleep(0.02)
                    client.send(reply_to.encode())
                    time.sleep(0.02)
                    client.send(msg_id.encode())
                    time.sleep(0.02)
                    client.send(user_id.encode())
                    time.sleep(0.02)
                    client.send(str(clean_len).encode())
                    time.sleep(0.02)
                    client.send(clean_bytes)
                except:
                    try:
                        client.close()
                    finally:
                        self.remove(client, room_id)

        except Exception as e:
            print("Loi broadcastReply:", repr(e))

    def broadcastReact(self, connection, room_id, user_id):
        """
        Gói REACT client gửi:

        REACT
        <msg_id>
        <loai_react>   (emoji: 👍 ❤️ 😆 😢 😮 ...)
        """
        try:
            msg_id = connection.recv(1024).decode(errors="ignore").strip()
            reaction = connection.recv(1024).decode(errors="ignore").strip()

            allowed = {"👍", "❤️", "😆", "😢", "😮"}
            if reaction not in allowed:
                return

            print(f"[Server] broadcastReact: from {user_id} to {msg_id} reaction={reaction}")
            # Lưu history reaction
            try:
                save_message(
                    room_id,
                    user_id,
                    "react",
                    {"msg_id": msg_id, "reaction": reaction},
                )
            except Exception as e:
                print("Loi luu history react:", e)

            # Broadcast cho tất cả client khác trong room
            for client in list(self.rooms[room_id]):
                if client is connection:
                    continue
                try:
                    client.send(b"REACT")
                    time.sleep(0.02)
                    client.send(msg_id.encode())
                    time.sleep(0.02)
                    client.send(user_id.encode())
                    time.sleep(0.02)
                    client.send(reaction.encode("utf-8"))
                except:
                    try:
                        client.close()
                    finally:
                        self.remove(client, room_id)

        except Exception as e:
            print("Loi broadcastReact:", e)

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
            print(f"[Server] broadcastRecall: from {user_id} msg_id={msg_id}")
            for client in list(self.rooms[room_id]):
                try:
                    client.send(b"RECALL")
                    time.sleep(0.02)
                    client.send(msg_id.encode())
                    time.sleep(0.02)
                    client.send(user_id.encode())
                    time.sleep(0.02)
                except:
                    try:
                        client.close()
                    finally:
                        self.remove(client, room_id)
            print(f"{user_id} recall {msg_id}")
        except Exception as e:
            print("Loi broadcastRecall:", e)

    def handleAck(self, connection, room_id, user_id):
        try:
            msg_id = connection.recv(1024).decode(errors="ignore")
            for client in list(self.rooms[room_id]):
                try:
                    client.send(b"READ")
                    time.sleep(0.02)
                    client.send(msg_id.encode())
                    time.sleep(0.02)
                    client.send(user_id.encode())
                    time.sleep(0.02)
                except:
                    try:
                        client.close()
                    finally:
                        self.remove(client, room_id)
        except Exception as e:
            print("Loi handleAck:", e)

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
        """
        Gửi danh sách user trong phòng - VERSION CỐ ĐỊNH
        """
        try:
            users = []
            for conn in self.rooms[room_id]:
                uid = self.usernames.get(conn, "Unknown")
                users.append(uid)
            payload = ",".join(users)
            
            # FIX: Gửi 3 gói riêng biệt để tránh dính
            for client in list(self.rooms[room_id]):
                try:
                    # Gói 1: Header
                    client.send(b"USERLIST")
                    time.sleep(0.05)
                    
                    # Gói 2: Length
                    client.send(str(len(payload)).encode())
                    time.sleep(0.05)
                    
                    # Gói 3: Payload
                    client.send(payload.encode())
                    time.sleep(0.05)
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
            self.room_history[room_id] = self.room_history[room_id][-self.max_history :]

    def _send_history_to_client(self, connection, room_id):
        """
        Gửi lại lịch sử phòng cho 1 client mới vào - VERSION CỐ ĐỊNH
        """
        history = get_recent_messages(room_id, limit=50)
        if not history:
            return

        try:
            for r in history:
                typ = r.get("type")
                user = r.get("user", "???")
                content = r.get("content")

                # ===== TEXT =====
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

                    connection.send(b"MSG")
                    time.sleep(0.05)  # Tăng delay cho history
                    connection.send(msg_id.encode())
                    time.sleep(0.05)
                    connection.send(ttl_ms.encode())
                    time.sleep(0.05)
                    connection.send(user.encode())
                    time.sleep(0.05)
                    connection.send(str(len(data)).encode())
                    time.sleep(0.05)
                    connection.send(data)
                    time.sleep(0.05)  # Delay sau mỗi tin
                    continue

                # ===== IMAGE =====
                elif typ == "image" and isinstance(content, dict):
                    b64 = content.get("data", "")
                    try:
                        img_bytes = base64.b64decode(b64.encode("ascii"))
                    except Exception:
                        continue

                    size = len(img_bytes)
                    connection.send(b"IMAGE")
                    time.sleep(0.05)
                    connection.send(msg_id.encode())
                    time.sleep(0.05)
                    connection.send(str(size).encode())
                    time.sleep(0.05)
                    connection.send(user.encode())
                    time.sleep(0.05)
                    connection.send(img_bytes)
                    time.sleep(0.05)

                # ===== FILE =====
                elif typ == "file":
                    # content expected to be {"msg_id": ..., "file_name": ...}
                    if isinstance(content, dict):
                        msg_id = content.get("msg_id", uuid.uuid4().hex)
                        file_name = content.get("file_name", "file")
                    else:
                        msg_id = uuid.uuid4().hex
                        file_name = str(content)
                    # We don't have file content; send len=0 so client can show metadata
                    connection.send(b"FILE")
                    time.sleep(0.05)
                    connection.send(msg_id.encode())
                    time.sleep(0.05)
                    connection.send(file_name.encode())
                    time.sleep(0.05)
                    connection.send(str(0).encode())
                    time.sleep(0.05)
                    connection.send(user.encode())
                    time.sleep(0.05)

                # ===== VIDEO =====
                elif typ == "video":
                    if isinstance(content, dict):
                        msg_id = content.get("msg_id", uuid.uuid4().hex)
                        file_name = content.get("file_name", "video")
                    else:
                        msg_id = uuid.uuid4().hex
                        file_name = str(content)
                    connection.send(b"VIDEO")
                    time.sleep(0.05)
                    connection.send(msg_id.encode())
                    time.sleep(0.05)
                    connection.send(file_name.encode())
                    time.sleep(0.05)
                    connection.send(str(0).encode())
                    time.sleep(0.05)
                    connection.send(user.encode())
                    time.sleep(0.05)

                # ===== REACTION =====
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

                    connection.send(b"REACT")
                    time.sleep(0.05)
                    connection.send(msg_id.encode())
                    time.sleep(0.05)
                    connection.send(user.encode())
                    time.sleep(0.05)
                    connection.send(emoji.encode("utf-8"))
                    time.sleep(0.05)

        except Exception as e:
            print("Lỗi gửi history:", e)


if __name__ == "__main__":
    ip_address = "127.0.0.1"
    port = 12345

    s = Server()
    s.accept_connections(ip_address, port)