import discord
from discord.ext import commands
from aiohttp import web
import os
from dotenv import dotenv_values
import asyncio

config = dotenv_values(".env")

TOKEN = str(config["TOKEN"])

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# Initialize the bot
class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_app = web.Application()
        self.api_runner = None

        # Add API routes
        self.api_app.router.add_get("/guild_count", self.get_guild_count)
        self.api_app.router.add_get("/guild_ids", self.get_guild_ids)
        self.api_app.router.add_get("/get_guild", self.get_guild)

    async def setup_hook(self):
        """Setup the aiohttp server."""
        self.api_runner = web.AppRunner(self.api_app)
        await self.api_runner.setup()
        site = web.TCPSite(self.api_runner, host="127.0.0.1", port=8080)
        await site.start()
        print("API server running on http://127.0.0.1:8080")

    async def close(self):
        """Cleanup the aiohttp server."""
        if self.api_runner:
            await self.api_runner.cleanup()
        await super().close()

    async def get_guild_count(self, request):
        """API endpoint to return the guild count."""
        return web.json_response({"guild_count": len(self.guilds)})

    async def get_guild_ids(self, request):
        """API endpoint to return guild IDs."""
        guild_ids = [guild.id for guild in self.guilds]
        return web.json_response({"guild_ids": guild_ids})
    
    async def get_guild(self, request):
        params = request.query.get("id")
        guild = discord.utils.get(self.guilds, id=int(params))

        return web.json_response({"name" : guild.name})

    async def on_ready(self):
        print(f"Bot is ready. Logged in as {self.user}")

# Instantiate and run the bot
bot = MyBot(command_prefix="!", intents=discord.Intents.all())

async def load():
    for filename in os.listdir("cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")

async def main():
    async with bot:
        await bot.start(TOKEN)

asyncio.run(main())