import json
import dotenv
import sqlite3
import os
import nextcord
from api.verification import Verification
from api.packselector import Pack
from loggerthyst import info, error, warn, fatal
from nextcord.ext import commands


intents = nextcord.Intents.all()
bot = commands.Bot(intents=intents)
dotenv.load_dotenv()
bot.add_cog(Verification(bot))
bot.add_cog(Pack(bot))


@bot.event
async def on_ready():
    info(f"Logged in as {bot.user}")

    if os.path.isfile("config.json"):
        info("Config file found, loading config...")
        with open("config.json", "r") as config_file:
            CONFIG = json.load(config_file)

    else:
        warn("Config file not found, creating one with default config...")
        with open("config.json", "w") as config_file:
            CONFIG = {
                "settings": {
                    "suggestions_forum_id": 1221696367261646918,
                    "verification_code_channel": 1156493862236332086,
                    "verification_channel": 1156493862236332086,
                    "verified_role": 1224494944153243699,
                    "server_ip": "themtn.xyz",
                    "server_data_api": "https://api.mcsrvstat.us/3/",
                    "modpack_api": "https://curserinth-api.kuylar.dev/v2/project/modpack__",
                    "database_path": "data.sqlite",
                }
            }
            config_file.write(json.dumps(CONFIG, indent=4))
    conn = sqlite3.connect(CONFIG["settings"]["database_path"])
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS verification (
            user_id INTEGER PRIMARY KEY,
            verification_code INTEGER,
            verified BOOLEAN
        )
        """
    )
    conn.commit()
    conn.close()


bot.run(os.getenv("BOT_TOKEN"))
