import os
import asyncio
import aiohttp
from dotenv import load_dotenv
import discord
import yt_dlp

# Load file .env trước khi đọc token
load_dotenv()

# Cấu hình Bot
config = {
    "token": os.getenv("SECRET_ACCESS_TOKEN"),
    "prefix": "!"
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

# Cấu hình yt-dlp & ffmpeg
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'extractflat': False,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

class MusicPlayer:
    def __init__(self):
        self.queue = []      # Danh sách bài hát chờ: [(song_info, requester)]
        self.current = None  # Bài hát đang phát: (song_info, requester)

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
        info = ytdl.extract_info(query, download=False)
        if 'entries' in info and info['entries']:
            info = info['entries'][0]
        return {
            'title': info.get('title', 'Unknown Title'),
            'webpage_url': info.get('webpage_url', info.get('url', '')),
            'stream_url': info.get('url'),
            'duration': info.get('duration', 0),
            'thumbnail': info.get('thumbnail', '')
        }
    return await asyncio.to_thread(_extract)

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
        source = discord.PCMVolumeTransformer(source, volume=0.5)

        def after_playing(error):
            if error:
                print(f"Lỗi phát nhạc: {error}")
            asyncio.run_coroutine_threadsafe(play_next_song_async(guild, text_channel), client.loop)

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

        asyncio.run_coroutine_threadsafe(text_channel.send(embed=embed), client.loop)
    except Exception as e:
        print(f"Lỗi khi phát nhạc: {e}")
        asyncio.run_coroutine_threadsafe(text_channel.send(f"❌ Không thể phát bài hát: {e}"), client.loop)
        play_next_song(guild, text_channel)

async def play_next_song_async(guild, text_channel):
    play_next_song(guild, text_channel)

class CustomClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        
        # Đặt trạng thái Đang nghe nhạc YouTube
        activity = discord.Activity(type=discord.ActivityType.listening, name="YouTube Music 🎵 | !help")
        await self.change_presence(activity=activity)

        # Lấy danh sách thành viên không trùng lặp
        members = list({m.id: m for m in self.get_all_members()}.values())
        print(f'Online users: {sum(1 for user in members if user.status == discord.Status.online and not user.bot)}')
        print(f'Online bots: {sum(1 for user in members if user.status == discord.Status.online and user.bot)}')
        print(f'Idle users: {sum(1 for user in members if user.status == discord.Status.idle)}')
        print(f'Do not disturb users: {sum(1 for user in members if user.status == discord.Status.dnd)}')
        print(f'Offline users: {sum(1 for user in members if user.status == discord.Status.offline)}')
        print(f'Members: {sum(1 for user in members if not user.bot)}')
        print(f'Bots: {sum(1 for user in members if user.bot)}')

    async def on_message(self, message):
        # Bỏ qua tin nhắn từ chính bot
        if message.author.bot:
            return

        print(f'Message from {message.author}: {message.content}')

        if "daniel" in message.content.lower():
            await message.channel.send("120")

        # Xử lý Lệnh Prefix Check
        if message.content.startswith(config["prefix"]):
            content_without_prefix = message.content[len(config["prefix"]):].strip()
            if not content_without_prefix:
                return

            parts = content_without_prefix.split(maxsplit=1)
            cmd = parts[0].lower()
            query = parts[1] if len(parts) > 1 else ""

            # Lệnh Hello
            if cmd == "hello":
                await message.channel.send(f"Hello <@!{message.author.id}>!")
                return

            # Lệnh Trợ giúp
            if cmd == "help":
                embed = discord.Embed(
                    title="📜 Danh sách lệnh Bot",
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="🎵 Lệnh Nghe Nhạc YouTube",
                    value=(
                        "`!play <tên/url>` (`!p`): Phát hoặc thêm bài hát vào hàng đợi\n"
                        "`!pause`: Tạm dừng phát nhạc\n"
                        "`!resume`: Tiếp tục phát nhạc\n"
                        "`!skip` (`!s`): Bỏ qua bài hát hiện tại\n"
                        "`!stop`: Dừng phát nhạc & xóa hàng đợi\n"
                        "`!queue` (`!q`): Xem danh sách bài hát chờ\n"
                        "`!nowplaying` (`!np`): Xem bài hát đang phát\n"
                        "`!leave` (`!dc`): Rời khỏi kênh thoại"
                    ),
                    inline=False
                )
                embed.add_field(
                    name="🎮 Lệnh Minigames Discord",
                    value="`!wtt`, `!betrayal`, `!poker`, `!fishing`",
                    inline=False
                )
                await message.channel.send(embed=embed)
                return

            # Kiểm tra voice channel cho Minigames & Music commands
            if cmd in ("play", "p", "pause", "resume", "skip", "s", "stop", "queue", "q", "nowplaying", "np", "leave", "dc") or cmd in GAMES:
                if not message.author.voice or not message.author.voice.channel:
                    await message.reply("⚠️ Bạn cần tham gia một kênh thoại (Voice Channel) trước!")
                    return
                voice_channel = message.author.voice.channel

            # Tạo Activity link cho Minigames
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

            # Xử lý Lệnh Nghe Nhạc YouTube
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

# Khởi tạo và chạy client
client = CustomClient(intents=intents)
client.run(config["token"])