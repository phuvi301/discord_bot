import discord
import os
from dotenv import load_dotenv

load_dotenv()

class Client(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        # self.get_all_members() trả về danh sách discord.Member (có chứa thuộc tính status)
        members = list({m.id: m for m in self.get_all_members()}.values())
        print(f'Online users: {sum(1 for user in members if user.status == discord.Status.online)}')
        print(f'Idle users: {sum(1 for user in members if user.status == discord.Status.idle)}')
        print(f'Do not disturb users: {sum(1 for user in members if user.status == discord.Status.dnd)}')
        print(f'Offline users: {sum(1 for user in members if user.status == discord.Status.offline)}')
        print(f'Members: {sum(1 for user in members if not user.bot)}')
        print(f'Bots: {sum(1 for user in members if user.bot)}')


    async def on_message(self, message):
        print(f'Message from {message.author}: {message.content}')
        if message.content == "!hello":
            await message.channel.send("Hello!")


# Bot setup
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.presences = True

client = Client(intents=intents)
client.run(os.getenv('SECRET_ACCESS_TOKEN'))