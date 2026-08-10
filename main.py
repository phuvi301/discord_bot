import os
import aiohttp
from dotenv import load_dotenv
import discord

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

class CustomClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        
        # Đặt trạng thái Đang xem youtube
        activity = discord.Activity(type=discord.ActivityType.watching, name="YouTube")
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

        # Xử lý Lệnh Activity (Prefix Check)
        if message.content.startswith(config["prefix"]):
            args = message.content[len(config["prefix"]):].strip().split()
            if not args:
                return

            cmd = args.pop(0).lower()

            # Bỏ qua nếu lệnh là !hello
            if cmd == "hello":
                await message.channel.send(f"Hello <@!{message.author.id}>!")
                return

            # Kiểm tra voice channel
            if not message.author.voice or not message.author.voice.channel:
                await message.reply("You need to join a Voice Channel")
                return

            voice_channel = message.author.voice.channel

            # Tạo Activity link
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
                                    f"Click on the Link to start the GAME:\n> https://discord.com/invite/{invite_code}"
                                )
                                return
                        
                        await message.reply(":x: Cannot start minigame")
            else:
                await message.reply("Available games: `wtt`, `betrayal`, `fishing`, `poker`")

# Khởi tạo và chạy client
client = CustomClient(intents=intents)
client.run(config["token"])