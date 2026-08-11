# 🎵 VEAES Discord Bot

Bot Discord đa năng hỗ trợ **phát nhạc YouTube** và **minigames**, được viết bằng Python với `discord.py`.

---

## ✨ Tính năng

### 🎵 Phát nhạc YouTube
- Tìm kiếm và phát nhạc từ **YouTube** (theo tên hoặc URL)
- **Hàng đợi bài hát** với thứ tự rõ ràng
- Fallback tự động sang **SoundCloud** nếu YouTube bị chặn
- Hỗ trợ **cookies.txt** để phát video giới hạn độ tuổi
- Hiển thị **embed** đẹp với thumbnail, thời lượng, người yêu cầu

### 🎮 Minigames Discord
- **Watch Together** (`!wtt`) — Xem video cùng nhau
- **Betrayal.io** (`!betrayal`) — Game sinh tồn trong bản đồ
- **Poker Night** (`!poker`) — Poker Texas Hold'em
- **Fishington.io** (`!fishing`) — Game câu cá

---

## 📋 Danh sách lệnh

| Lệnh | Viết tắt | Mô tả |
|---|---|---|
| `!play <tên/url>` | `!p` | Phát hoặc thêm bài hát vào hàng đợi |
| `!pause` | — | Tạm dừng phát nhạc |
| `!resume` | — | Tiếp tục phát nhạc |
| `!skip` | `!s` | Bỏ qua bài hát hiện tại |
| `!stop` | — | Dừng phát nhạc & xóa toàn bộ hàng đợi |
| `!queue` | `!q` | Xem danh sách bài hát chờ (tối đa 10 bài) |
| `!nowplaying` | `!np` | Xem bài hát đang phát |
| `!leave` | `!dc` | Bot rời khỏi kênh thoại |
| `!wtt` | `!watchtogether` | Tạo phòng Watch Together |
| `!betrayal` | `!betrayal.io` | Tạo phòng Betrayal.io |
| `!poker` | `!poker-night` | Tạo phòng Poker Night |
| `!fishing` | `!fishington.io` | Tạo phòng Fishington.io |
| `!help` | — | Hiển thị danh sách lệnh |

---

## 🚀 Cài đặt

### Yêu cầu
- Python 3.12+
- `ffmpeg` (phải có trong PATH)
- `libopus`

### 1. Clone dự án
```bash
git clone <repo-url>
cd DiscordBot
```

### 2. Cài dependencies
```bash
pip install -r requirements.txt
```

### 3. Tạo file `.env`
```env
SECRET_ACCESS_TOKEN=your_discord_bot_token_here
```

### 4. Chạy bot
```bash
python main.py
```

---

## ☁️ Deploy lên Replit

### Cấu hình `.replit`
```toml
modules = ["python-3.12"]
run = "bash start.sh"

[nix]
channel = "stable-25_05"
deps = [
    "ffmpeg-full",
    "libopus"
]

[env]
PYTHONUNBUFFERED = "1"
```

### Secrets (Environment Variables)
Vào tab **Secrets** trên Replit, thêm:
| Key | Value |
|---|---|
| `SECRET_ACCESS_TOKEN` | Token bot Discord của bạn |

### Lưu ý Replit
- Bot tự động tìm `libopus.so` trong `/nix/store/` bằng `os.scandir()` (không gây hang)
- File `start.sh` thiết lập `PYTHONPATH` trỏ đến `.pythonlibs/` của Replit
- Opus được pre-load qua `ctypes.CDLL()` **trước** khi `import discord` để tránh lazy-import hang

---

## 📁 Cấu trúc dự án

```
DiscordBot/
├── main.py          # File chính của bot
├── start.sh         # Script khởi động cho Replit
├── .replit          # Cấu hình Replit
├── requirements.txt # Danh sách Python packages
├── .env             # Token & biến môi trường (không commit!)
├── cookies.txt      # Cookie YouTube (tuỳ chọn, không commit!)
└── .gitignore
```

---

## 🔧 Biến môi trường

| Biến | Bắt buộc | Mô tả |
|---|---|---|
| `SECRET_ACCESS_TOKEN` | ✅ | Token của Discord Bot |

---

## 🍪 Cookie YouTube (Tuỳ chọn)

Nếu gặp lỗi **"Sign in to confirm you're not a bot"** hoặc video bị giới hạn độ tuổi:

1. Dùng extension [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) để xuất cookie từ YouTube
2. Lưu file với tên `cookies.txt` vào thư mục gốc của dự án
3. Bot sẽ tự động dùng cookies khi YouTube chặn request thường

> ⚠️ **Không commit `cookies.txt` lên Git** (đã có trong `.gitignore`)

---

## 🛠 Tech Stack

| Thư viện | Mục đích |
|---|---|
| `discord.py 2.7.1` | Discord API wrapper |
| `yt-dlp` | Trích xuất stream URL từ YouTube/SoundCloud |
| `aiohttp` | HTTP client async |
| `python-dotenv` | Đọc file `.env` |
| `PyNaCl` | Mã hoá cho voice |
| `ffmpeg` | Encode/decode audio stream |

---

## 📄 License

MIT License
