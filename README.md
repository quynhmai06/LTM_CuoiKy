# UTH-CHAT — Simple Python Chat Room

UTH-CHAT is a minimal classroom/chatroom project implemented in Python with a server and both GUI and CLI clients. This README explains the core features, installation steps, and basic usage.

## ⭐ Tính năng chính

- Kết nối TCP: client kết nối bằng `username` + `room_id`.
- Hỗ trợ nhiều phòng (room) và danh sách người online (USERLIST).
- Tin nhắn văn bản (MSG): gửi/nhận và reply/quoted replies (REPLY).
- Reaction (REACT): thả emoji (👍, ❤️, 😆, 😢, 😮) để tương tác với tin nhắn.
- Recall (RECALL): gửi command để thu hồi (xóa) 1 tin nhắn global cho tất cả.
- Tự hủy tại máy người dùng (local-only): menu "Tự hủy sau..." sẽ xóa tin nhắn chỉ trên máy người thực hiện (không broadcast RECALL).
- Gửi/nhận hình ảnh (IMAGE) và hiển thị inline trong GUI. Server lưu ảnh vào lịch sử (base64) để replay.
- Gửi/nhận file (FILE): server relay bytes, lưu metadata; client lưu file vào ổ cứng khi nhận.
- Gửi/nhận video (VIDEO): server relay bytes; GUI hỗ trợ inline playback nếu `python-vlc` và VLC runtime có sẵn; ngược lại sẽ mở bằng app mặc định.
- Lưu lịch sử (JSONL) theo phòng (`logs/room_<id>.jsonl`).
- Filter ngôn từ xấu + tạm khóa (mute) người dùng khi lặp vi phạm nhiều lần.
- CLI client (`client.py`) với lệnh hỗ trợ: `/react`, `/reply`, `/recall`, `FILE` (gửi file/video).
- Search (Ctrl+F) trong GUI để tìm tin nhắn trong metadata local.
- Typing indicator: `TYPING START/STOP` events.

## ⚙️ Cài đặt / Yêu cầu

- Python 3.10+ (hoặc tương thích 3.11/3.13 theo môi trường bạn đang dùng).
- Thư viện Python: Pillow (PIL) — xử lý ảnh.
- (Tuỳ chọn) `python-vlc` + VLC runtime: cho inline video playback.

Ví dụ cài các package cần thiết:

```powershell
py -m pip install pillow python-vlc
```

Chú ý: Để dùng inline video, bạn cần cài VLC (https://www.videolan.org/vlc/).

## ▶️ Chạy server & client

1. Mở terminal (PowerShell) và chạy server:

```powershell
py server.py
```

2. Khởi chạy client GUI:

```powershell
py client_GUI.py
```

3. Hoặc dùng client console (text):

```powershell
py client.py
```

## 💡 Cách sử dụng (GUI)

- Login: nhập `Tên người dùng` và `Room ID` để vào phòng.
- Viết tin nhắn và nhấn Enter để gửi.
- Reply: click phải lên tin nhắn → `Trả lời tin nhắn` → gõ tin nhắn; server sẽ gửi REPLY.
- Reaction: menu `✨ Reaction` chọn emoji; server sẽ broadcast REACT.
- Recall (xóa toàn cục): `🗑️ Gỡ tin nhắn` (gửi RECALL global).
- Tự hủy (local-only): `⏰ Tự hủy sau...` — chỉ xóa tin nhắn trên máy bạn chứ không thông báo RECALL cho người khác.
- Gửi file/hình ảnh/video: `🖼️` browse → chọn file → nút `✓` send. GUI hiển thị preview filename; nhấn vào bubble để mở file/video.
- Inline video: nếu có `python-vlc` và VLC runtime, bấm để xem inline; có controls `⏯️` và `⏹️`.

## 🧭 Cách sử dụng (Console / CLI)

- `/react <msg_id> <emoji>`: gửi reaction.
- `/reply <msg_id> <text>`: reply 1 tin nhắn.
- `/recall <msg_id>`: bảo server broadcast RECALL (global remove).
- `FILE` (nhập lệnh FILE, sau đó follow prompts): gửi file hoặc video (console auto-detect video ext).

## 📁 Lưu trữ lịch sử và replay

- Server lưu lịch sử mỗi phòng trong `logs/room_<room_id>.jsonl` theo định dạng JSONL.
- Ảnh được lưu base64 trong lịch sử (cho phép replay); Files/Video chỉ lưu metadata (msg_id, file_name) để tránh lưu dữ liệu lớn.

## 🛡️ Moderation & Limitations

- Filter từ ngữ xấu: server sẽ thay \*\*\* cho từ không phù hợp.
- Sau nhiều lần vi phạm, user sẽ bị tạm mute (30s).
- Không có authentication (username có thể đơn giản gõ và đổi).
- Short-id (message short index) chưa có; hiện tại `msg_id` dùng UUID hex.
- Server không lưu file/video bytes trong history (chỉ metadata).

## 🔁 Gợi ý phát triển & tính năng mở rộng

- Cung cấp short ID (m1, m2, ...) để dễ thao tác via CLI.
- Lưu file/video (server-side) để cho phép tải lại qua history.
- Hiển thị countdown/undo cho `Tự hủy` local-only.
- Thêm authentication & persistent accounts.

---

Nếu bạn muốn tôi cập nhật README thêm screenshots, hướng dẫn chi tiết cài VLC, hoặc tự động hoá vài bước (ví dụ: `requirements.txt`, setup script), nói cho tôi biết — tôi sẽ bổ sung tiếp.

© UTH-CHAT — project sample (local testing / demo)
