from quart import Quart, render_template, request, session, redirect, url_for
from quart_discord import DiscordOAuth2Session
import aiohttp
from dotenv import dotenv_values

config = dotenv_values(".env")

app = Quart(__name__)
app.config["SECRET_KEY"] = str(config["SECRET_KEY"])
app.config["DISCORD_CLIENT_ID"] = int(config["DISCORD_CLIENT_ID"])
app.config["DISCORD_CLIENT_SECRET"] = str(config["DISCORD_CLIENT_SECRET"])
app.config["DISCORD_REDIRECT_URI"] = str(config["DISCORD_REDIRECT_URL"])

discord = DiscordOAuth2Session(app)

@app.route("/")
async def home():
    return await render_template("index.html", authorized = await discord.authorized)

@app.route("/login")
async def login():
    return await discord.create_session()

@app.route("/callback")
async def callback():
    try:
        await discord.callback()
    except:
        return redirect(url_for("login"))
    
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
async def dashboard():
    if not await discord.authorized:
        return redirect(url_for("login")) 
    
    async with aiohttp.ClientSession() as session:
        async with session.get("http://127.0.0.1:8080/guild_count") as resp:
            guild_count_data = await resp.json()

        async with session.get("http://127.0.0.1:8080/guild_ids") as resp:
            guild_ids_data = await resp.json()

    try:
        user_guilds = await discord.fetch_guilds()
    except:
        return redirect(url_for("login"))
    
    guilds = []

    for guild in user_guilds:
        if guild.id in guild_ids_data["guild_ids"]:
            if guild.permissions.administrator:			
                    guild.class_color = "green-border" if guild.id in guild_ids_data["guild_ids"] else "red-border"
                    guilds.append(guild)

    guilds.sort(key = lambda x: x.class_color == "red-border")
    name = (await discord.fetch_user()).name
    return await render_template("dashboard.html", guild_count = guild_count_data["guild_count"], guilds = guilds, username=name)

@app.route("/dashboard/<int:guild_id>")
async def dashboard_server(guild_id):
    if not await discord.authorized:
        return redirect(url_for("login")) 
        
    async with aiohttp.ClientSession() as session:
        async with session.get(url="http://127.0.0.1:8080/get_guild", params={"id": guild_id}) as resp:
            if resp.status == 200:
                guild = await resp.json()
                return guild["name"]
            else:
                print(f"Request failed with status code: {resp.status}")


if __name__ == "__main__":
    app.run(debug=True)