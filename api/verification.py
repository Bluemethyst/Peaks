from nextcord.ext import commands
from config import get_config
import nextcord
import sqlite3
import random

CONFIG = get_config()


class Verification(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.add_listener(self.on_member_join)
        self.bot.add_listener(self.on_member_remove)

    def generate_code(self):
        return random.randint(100000, 999999)

    def member_exists_in_db(self, user_id):
        conn = sqlite3.connect(CONFIG["settings"]["database_path"])
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM verification WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def insert_member_into_db(self, member):
        code = self.generate_code()
        conn = sqlite3.connect(CONFIG["settings"]["database_path"])
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO verification (user_id, verification_code, verified) VALUES (?, ?, ?)",
            (member.id, code, True),
        )
        conn.commit()
        conn.close()

    async def on_member_join(self, member: nextcord.Member):
        verify_channel = self.bot.get_channel(
            CONFIG["settings"]["verification_channel"]
        )
        verification_code_channel = self.bot.get_channel(
            CONFIG["settings"]["verification_code_channel"]
        )
        code = self.generate_code()
        await verification_code_channel.send(
            f"Welcome to the server, {member.mention}! Your verification code is: {code}. Use `/verify {code}` in {verify_channel.mention} to verify yourself."
        )
        conn = sqlite3.connect(CONFIG["settings"]["database_path"])
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO verification (user_id, verification_code, verified) VALUES (?, ?, ?)",
            (member.id, code, False),
        )
        conn.commit()
        conn.close()

    async def on_member_remove(self, member: nextcord.Member):
        conn = sqlite3.connect(CONFIG["settings"]["database_path"])
        cursor = conn.cursor()
        cursor.execute("DELETE FROM verification WHERE user_id = ?", (member.id,))
        conn.commit()
        conn.close()

    @nextcord.slash_command(description="Verify yourself to access the server")
    async def verify(self, interaction: nextcord.Interaction, code: int):
        await interaction.response.defer(ephemeral=True)
        conn = sqlite3.connect(CONFIG["settings"]["database_path"])
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM verification WHERE user_id = ?", (interaction.user.id,)
        )
        result = cursor.fetchone()
        conn.close()
        if code == result[1]:
            conn = sqlite3.connect(CONFIG["settings"]["database_path"])
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE verification SET verified = ? WHERE user_id = ?",
                (True, interaction.user.id),
            )
            conn.commit()
            conn.close()
            role = CONFIG["settings"]["verified_role"]
            guild = interaction.guild
            role = guild.get_role(role)
            await interaction.user.add_roles(role)
            await interaction.followup.send(
                "You have been verified! You can now access the server.", ephemeral=True
            )
        else:
            await interaction.followup.send(
                "Incorrect verification code, please try again.", ephemeral=True
            )

    @nextcord.slash_command(description="Admin command to grant all users verfied role")
    @commands.has_role(CONFIG["settings"]["admin_role"])
    @commands.has_role(1221934016878477393)
    async def grant_all(self, interaction: nextcord.Interaction):
        await interaction.response.defer()
        for guild in self.bot.guilds:
            for member in guild.members:
                if not self.member_exists_in_db(member.id):
                    self.insert_member_into_db(member)
        verified_role_id = CONFIG["settings"]["verified_role"]
        verified_role = member.guild.get_role(verified_role_id)
        if verified_role:
            try:
                await member.add_roles(verified_role)
                await interaction.followup.send(
                    "All users have been granted the verified role.",
                    ephemeral=True,
                )
            except nextcord.HTTPException as e:
                print(f"Failed to add verified role to {member.name}: {e}")
