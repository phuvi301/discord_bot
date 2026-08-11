import sys, os, asyncio, aiohttp
from aiohttp import web

print("=== main.py starting ===", flush=True)

# --- 1. KHỞI TẠO WEB SERVER SIÊU TỐC CHO REPLIT HEALTH CHECK ---
async def handle_health_check(request):
    return web.Response(text="Bot is alive!", status=200)

async def init_fast_web_server():
    app = web.Application()
    app.router.add_get('/', handle_health_check)
    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"[INFO] Fast Health Check Web Server running on port {port}", flush=True)

# Khởi tạo event loop và mở cổng HTTP ngay lập tức
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(init_fast_web_server())

# --- 2. IMPORT CÁC THƯ VIỆN BỔ SUNG ---
import urllib.request
from dotenv import load_dotenv
print("[OK] dotenv", flush=True)
import discord
print("[OK] discord", flush=True)
import yt_dlp
print("[OK] yt_dlp - all imports done", flush=True)

# --- 3. TỰ ĐỘNG TẢI LIBOPUS CHO DISCORD VOICE ---
import ctypes.util

def ensure_and_load_opus():
    if discord.opus.is_loaded():
        print("[INFO] discord.opus is already loaded", flush=True)
        return True

    project_root = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.environ.get("OPUS_LIBRARY"),
        os.path.join(project_root, "libopus.so.0"),
        os.path.join(project_root, "libopus.so"),
        ctypes.util.find_library("opus"),
        "libopus.so.0",
        "libopus.so",
        "opus",
        "libopus",
    ]

    attempted = set()
    errors = []
    for lib_path in candidates:
        if not lib_path or lib_path in attempted:
            continue
        attempted.add(lib_path)
        try:
            discord.opus.load_opus(lib_path)
            print(f"[SUCCESS] Loaded Opus from {lib_path}", flush=True)
            return True
        except Exception as exc:
            errors.append(f"{lib_path}: {exc}")

    print("[CRITICAL] Could not load libopus; voice playback is unavailable.", flush=True)
    if errors:
        print(f"[DEBUG] Opus loader attempts: {' | '.join(errors)}", flush=True)
    return False

print("[DEBUG] Calling ensure_and_load_opus...", flush=True)
ensure_and_load_opus()
print("[DEBUG] Done", flush=True)

# Load file .env
print("[DEBUG] Calling load_dotenv...", flush=True)
load_dotenv()
print("[DEBUG] load_dotenv done", flush=True)

# Cấu hình Bot
config = {
    "token": os.getenv("SECRET_ACCESS_TOKEN"),
    "prefix": "?"
}

# Khai báo Intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.presences = True

# Danh sách Application ID cho các game
GAMES = {
    "wtt": "880218394199220334",
    "watchtogether": "880218394199220334",
    "betrayal": "773336526917861400",
    "betrayal.io": "773336526917861400",
    "poker": "755827207812677713",
    "poker-night": "755827207812677713",
    "fishing": "814288819477020702",
    "fishington.io": "814288819477020702"
}

# Cấu hình yt-dlp tối ưu vượt rào cản bot YouTube
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0', # Ép dùng IPv4
    'extractor_args': {
        'youtube': {
            # Bỏ 'web' để tránh bị YouTube chặn IP của Replit
            'player_client': ['android_testsuite', 'tv', 'android', 'ios', 'mweb']
        }
    }
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -probesize 32k -analyzeduration 0 -user_agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"',
    'options': '-vn -filter:a "volume=0.5" -loglevel error',
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

class MusicPlayer:
    def __init__(self):
        self.queue = []      # [(song_info, requester)]
        self.current = None  # (song_info, requester)

    def next_song(self):
        if self.queue:
            self.current = self.queue.pop(0)
            return self.current
        self.current = None
        return None

    def clear(self):
        self.queue.clear()
        self.current = None

guild_players = {}

def get_player(guild_id):
    if guild_id not in guild_players:
        guild_players[guild_id] = MusicPlayer()
    return guild_players[guild_id]

def format_duration(seconds):
    if not seconds:
        return "N/A"
    seconds = int(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"

async def search_yt(query):
    def _extract():
        search_query = query if query.startswith(('http://', 'https://')) else f"ytsearch:{query}"
        song_title = None

        # 1. Thử trích xuất từ YouTube không dùng cookie
        try:
            info = ytdl.extract_info(search_query, download=False)
            if 'entries' in info and info['entries']:
                info = info['entries'][0]

            song_title = info.get('title')
            stream_url = info.get('url')

            if not stream_url and 'formats' in info:
                formats = [f for f in info['formats'] if f.get('acodec') != 'none']
                if formats:
                    stream_url = formats[-1].get('url')

            if stream_url:
                return {
                    'title': song_title or 'Unknown Title',
                    'webpage_url': info.get('webpage_url', info.get('url', '')),
                    'stream_url': stream_url,
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail', '')
                }
        except Exception as e:
            print(f"⚠️ Thử YouTube mặc định thất bại: {e}")

        # 2. Nếu có cookies.txt, thử sử dụng cookie
        if os.path.exists('cookies.txt'):
            try:
                cookie_opts = {**YTDL_OPTIONS, 'cookiefile': 'cookies.txt'}
                with yt_dlp.YoutubeDL(cookie_opts) as ytdl_cookie:
                    info = ytdl_cookie.extract_info(search_query, download=False)
                    if 'entries' in info and info['entries']:
                        info = info['entries'][0]

                    song_title = info.get('title')
                    stream_url = info.get('url')

                    if not stream_url and 'formats' in info:
                        formats = [f for f in info['formats'] if f.get('acodec') != 'none']
                        if formats:
                            stream_url = formats[-1].get('url')

                    if stream_url:
                        return {
                            'title': song_title or 'Unknown Title',
                            'webpage_url': info.get('webpage_url', info.get('url', '')),
                            'stream_url': stream_url,
                            'duration': info.get('duration', 0),
                            'thumbnail': info.get('thumbnail', '')
                        }
            except Exception as e:
                print(f"⚠️ Thử YouTube với cookies.txt thất bại: {e}")

        # 3. Phương án dự phòng (Fallback): SoundCloud
        if not song_title:
            song_title = query.split('?')[0].split('/')[-1]

        sc_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'default_search': 'scsearch'
        }

        with yt_dlp.YoutubeDL(sc_opts) as sc_ytdl:
            sc_info = sc_ytdl.extract_info(f"scsearch:{song_title}", download=False)
            if 'entries' in sc_info and sc_info['entries']:
                sc_info = sc_info['entries'][0]
                return {
                    'title': f"{sc_info.get('title', 'Unknown Title')} (SoundCloud)",
                    'webpage_url': sc_info.get('webpage_url', ''),
                    'stream_url': sc_info.get('url'),
                    'duration': sc_info.get('duration', 0),
                    'thumbnail': sc_info.get('thumbnail', '')
                }

        raise Exception("Không thể trích xuất luồng âm thanh từ bài hát này.")

    return await asyncio.to_thread(_extract)

bot_client = None

def play_next_song(guild, text_channel):
    player = get_player(guild.id)
    song_item = player.next_song()

    if song_item is None:
        return

    song_info, requester = song_item
    voice_client = guild.voice_client

    if not voice_client or not voice_client.is_connected():
        return

    try:
        source = discord.FFmpegPCMAudio(song_info['stream_url'], **FFMPEG_OPTIONS)

        def after_playing(error):
            if error:
                print(f"Lỗi sau khi phát nhạc: {repr(error)}")
            if bot_client and bot_client.loop:
                asyncio.run_coroutine_threadsafe(play_next_song_async(guild, text_channel), bot_client.loop)

        voice_client.play(source, after=after_playing)

        embed = discord.Embed(
            title="🎶 Đang phát nhạc",
            description=f"[{song_info['title']}]({song_info['webpage_url']})",
            color=discord.Color.green()
        )
        if song_info.get('thumbnail'):
            embed.set_thumbnail(url=song_info['thumbnail'])
        embed.add_field(name="Thời lượng", value=format_duration(song_info.get('duration')), inline=True)
        embed.add_field(name="Người yêu cầu", value=requester.mention, inline=True)

        if bot_client and bot_client.loop:
            asyncio.run_coroutine_threadsafe(text_channel.send(embed=embed), bot_client.loop)
    except Exception as e:
        import traceback
        print(f"Lỗi khi phát nhạc: {repr(e)}")
        traceback.print_exc()
        if bot_client and bot_client.loop:
            asyncio.run_coroutine_threadsafe(text_channel.send(f"❌ Không thể phát bài hát: {e}"), bot_client.loop)
        play_next_song(guild, text_channel)

async def play_next_song_async(guild, text_channel):
    play_next_song(guild, text_channel)

class CustomClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

        activity = discord.Activity(type=discord.ActivityType.listening, name="YouTube Music 🎵 | !help")
        await self.change_presence(activity=activity)

        members = list({m.id: m for m in self.get_all_members()}.values())
        print(f'Online users: {sum(1 for user in members if user.status == discord.Status.online and not user.bot)}')
        print(f'Online bots: {sum(1 for user in members if user.status == discord.Status.online and user.bot)}')
        print(f'Idle users: {sum(1 for user in members if user.status == discord.Status.idle)}')
        print(f'Do not disturb users: {sum(1 for user in members if user.status == discord.Status.dnd)}')
        print(f'Offline users: {sum(1 for user in members if user.status == discord.Status.offline)}')
        print(f'Members: {sum(1 for user in members if not user.bot)}')
        print(f'Bots: {sum(1 for user in members if user.bot)}')

    async def on_message(self, message):
        if message.author.bot:
            return

        print(f'Message from {message.author}: {message.content}')

        if "daniel" in message.content.lower():
            await message.channel.send("120")

        if message.content.startswith(config["prefix"]):
            content_without_prefix = message.content[len(config["prefix"]):].strip()
            if not content_without_prefix:
                return

            parts = content_without_prefix.split(maxsplit=1)
            cmd = parts[0].lower()
            query = parts[1] if len(parts) > 1 else ""

            if cmd == "hello":
                await message.channel.send(f"Hello <@!{message.author.id}>!")
                return

            if cmd == "help":
                embed = discord.Embed(
                    title="📜 Danh sách lệnh Bot",
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="🎵 Lệnh Nghe Nhạc YouTube",
                    value=(
                        "`?play <tên/url>` (`?p`): Phát hoặc thêm bài hát vào hàng đợi\n"
                        "`?pause`: Tạm dừng phát nhạc\n"
                        "`?resume`: Tiếp tục phát nhạc\n"
                        "`?skip` (`?s`): Bỏ qua bài hát hiện tại\n"
                        "`?stop`: Dừng phát nhạc & xóa hàng đợi\n"
                        "`?queue` (`?q`): Xem danh sách bài hát chờ\n"
                        "`?nowplaying` (`?np`): Xem bài hát đang phát\n"
                        "`?leave` (`?dc`): Rời khỏi kênh thoại"
                    ),
                    inline=False
                )
                embed.add_field(
                    name="🎮 Lệnh Minigames Discord",
                    value="`?wtt`, `?betrayal`, `?poker`, `?fishing`",
                    inline=False
                )
                await message.channel.send(embed=embed)
                return

            if cmd in ("play", "p", "pause", "resume", "skip", "s", "stop", "queue", "q", "nowplaying", "np", "leave", "dc") or cmd in GAMES:
                if not message.author.voice or not message.author.voice.channel:
                    await message.reply("⚠️ Bạn cần tham gia một kênh thoại (Voice Channel) trước!")
                    return
                voice_channel = message.author.voice.channel

            if cmd in GAMES:
                app_id = GAMES[cmd]
                url = f"https://discord.com/api/v8/channels/{voice_channel.id}/invites"

                headers = {
                    "Authorization": f"Bot {config['token']}",
                    "Content-Type": "application/json"
                }

                payload = {
                    "max_age": 86400,
                    "max_uses": 0,
                    "target_application_id": app_id,
                    "target_type": 2,
                    "temporary": False,
                    "validate": None
                }

                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload, headers=headers) as response:
                        if response.status in (200, 201):
                            data = await response.json()
                            invite_code = data.get("code")
                            if invite_code:
                                await message.channel.send(
                                    f"Click vào đường dẫn để tham gia GAME:\n> https://discord.com/invite/{invite_code}"
                                )
                                return

                        await message.reply(":x: Không thể tạo link minigame.")
                return

            voice_client = message.guild.voice_client if message.guild else None
            player = get_player(message.guild.id) if message.guild else None

            if not message.guild:
                return

            if cmd in ("play", "p"):
                if not query:
                    await message.reply("⚠️ Vui lòng nhập tên bài hát hoặc đường dẫn YouTube! Ví dụ: `!play Despacito`")
                    return

                if voice_client is None:
                    voice_client = await voice_channel.connect()
                elif voice_client.channel != voice_channel:
                    await voice_client.move_to(voice_channel)

                status_msg = await message.channel.send("🔎 **Đang tìm kiếm bài hát trên YouTube...**")

                try:
                    song_info = await search_yt(query)
                except Exception as e:
                    await status_msg.edit(content=f"❌ Không tìm thấy bài hát hoặc có lỗi xảy ra: {e}")
                    return

                player.queue.append((song_info, message.author))

                if voice_client.is_playing() or voice_client.is_paused():
                    embed = discord.Embed(
                        title="📝 Đã thêm vào hàng đợi",
                        description=f"[{song_info['title']}]({song_info['webpage_url']})",
                        color=discord.Color.blue()
                    )
                    if song_info.get('thumbnail'):
                        embed.set_thumbnail(url=song_info['thumbnail'])
                    embed.add_field(name="Vị trí trong hàng đợi", value=f"#{len(player.queue)}", inline=True)
                    embed.add_field(name="Thời lượng", value=format_duration(song_info.get('duration')), inline=True)
                    embed.add_field(name="Người yêu cầu", value=message.author.mention, inline=True)
                    await status_msg.delete()
                    await message.channel.send(embed=embed)
                else:
                    await status_msg.delete()
                    play_next_song(message.guild, message.channel)
                return

            if cmd == "pause":
                if voice_client and voice_client.is_playing():
                    voice_client.pause()
                    await message.reply("⏸️ **Đã tạm dừng phát nhạc.**")
                else:
                    await message.reply("⚠️ Hiện không có bài hát nào đang phát.")
                return

            if cmd == "resume":
                if voice_client and voice_client.is_paused():
                    voice_client.resume()
                    await message.reply("▶️ **Đã tiếp tục phát nhạc.**")
                else:
                    await message.reply("⚠️ Nhạc không ở trạng thái tạm dừng.")
                return

            if cmd in ("skip", "s"):
                if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
                    voice_client.stop()
                    await message.reply("⏭️ **Đã bỏ qua bài hát hiện tại.**")
                else:
                    await message.reply("⚠️ Không có bài hát nào đang phát để bỏ qua.")
                return

            if cmd == "stop":
                player.clear()
                if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
                    voice_client.stop()
                await message.reply("⏹️ **Đã dừng phát nhạc và xóa sạch hàng đợi.**")
                return

            if cmd in ("queue", "q"):
                if not player.current and not player.queue:
                    await message.reply("📭 Hàng đợi phát nhạc hiện đang trống.")
                    return

                embed = discord.Embed(title="📜 Hàng đợi phát nhạc", color=discord.Color.gold())
                if player.current:
                    curr_info, curr_req = player.current
                    embed.add_field(
                        name="🎶 Đang phát",
                        value=f"[{curr_info['title']}]({curr_info['webpage_url']}) | Yêu cầu bởi: {curr_req.mention}",
                        inline=False
                    )

                if player.queue:
                    queue_list = []
                    for idx, (s_info, req) in enumerate(player.queue[:10], 1):
                        queue_list.append(f"`{idx}.` [{s_info['title']}]({s_info['webpage_url']}) | Yêu cầu bởi: {req.mention}")

                    if len(player.queue) > 10:
                        queue_list.append(f"*... và {len(player.queue) - 10} bài hát khác*")

                    embed.add_field(name="▶️ Tiếp theo", value="\n".join(queue_list), inline=False)

                await message.channel.send(embed=embed)
                return

            if cmd in ("nowplaying", "np"):
                if player.current:
                    song_info, requester = player.current
                    embed = discord.Embed(
                        title="🎶 Bài hát đang phát",
                        description=f"[{song_info['title']}]({song_info['webpage_url']})",
                        color=discord.Color.purple()
                    )
                    if song_info.get('thumbnail'):
                        embed.set_thumbnail(url=song_info['thumbnail'])
                    embed.add_field(name="Thời lượng", value=format_duration(song_info.get('duration')), inline=True)
                    embed.add_field(name="Người yêu cầu", value=requester.mention, inline=True)
                    await message.channel.send(embed=embed)
                else:
                    await message.reply("⚠️ Hiện không có bài hát nào đang phát.")
                return

            if cmd in ("leave", "dc"):
                player.clear()
                if voice_client:
                    await voice_client.disconnect()
                    await message.reply("👋 **Đã rời khỏi kênh thoại.**")
                else:
                    await message.reply("⚠️ Bot hiện không ở trong kênh thoại nào.")
                return

# --- 4. KHỞI CHẠY DISCORD BOT ---
async def main():
    global bot_client
    bot_client = CustomClient(intents=intents)
    await bot_client.start(config["token"])

if __name__ == "__main__":
    print("[INFO] Dang ket noi toi Discord Gateway...", flush=True)
    loop.run_until_complete(main())