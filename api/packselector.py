from io import BytesIO
import nextcord
import re
import httpx
from PIL import Image
from collections import Counter
from loggerthyst import info
from datetime import datetime
from config import get_config
from nextcord.ext import commands
from nextcord.ui import Modal, TextInput

CONFIG = get_config()


class Suggest(Modal):
    def __init__(self, bot):
        super().__init__(
            "Suggest a Modpack",
            timeout=5 * 60,
        )
        self.bot = bot

        self.link = TextInput(
            label="Your Modpack's Link",
            min_length=2,
            max_length=100,
        )
        self.add_item(self.link)

        self.description = TextInput(
            label="Why this pack?",
            style=nextcord.TextInputStyle.paragraph,
            placeholder="Just a quick explanation of why you think this pack suits this server.",
            max_length=500,
        )
        self.add_item(self.description)

    async def callback(self, interaction: nextcord.Interaction) -> None:
        await interaction.response.defer()
        API = CONFIG["settings"]["modpack_api"]
        pattern = r"(https?://(?:www\.)?(?:curseforge\.com|modrinth\.com)/minecraft/modpacks/|https?://modrinth\.com/modpack/)([\w-]+)"
        match = re.search(pattern, self.link.value)
        if match:
            modpack_name = match.group(2)
        else:
            await interaction.followup.send(
                "The provided link does not match the expected format. Please ensure it's a valid CurseForge or Modrinth modpack link.",
                ephemeral=True,
            )
            return
        r = httpx.get(API + modpack_name)
        data = r.json()
        title = data["title"]
        description = data["description"]
        icon = data["icon_url"]
        downloads = data["downloads"]
        created = data["published"]
        last_updated = data["updated"]
        gallery = data["gallery"]

        image_data = httpx.get(icon)
        image = Image.open(BytesIO(image_data.content))
        image = image.resize((100, 100))
        pixels = image.convert("RGB").getdata()
        color_counts = Counter(pixels)
        most_common_color = color_counts.most_common(1)[0][0]

        created_datetime = datetime.fromisoformat(created.replace("Z", "+00:00"))
        last_updated_datetime = datetime.fromisoformat(
            last_updated.replace("Z", "+00:00")
        )
        created_epoch = int(created_datetime.timestamp())
        last_updated_epoch = int(last_updated_datetime.timestamp())

        embed = nextcord.Embed(
            title=title,
            description=description,
            url=self.link.value,
            color=nextcord.Colour.from_rgb(*most_common_color),
        )
        embed.set_thumbnail(url=icon)
        if gallery and gallery[0]:
            embed.set_image(url=gallery[0]["url"])
        embed.add_field(name="Downloads", value=downloads, inline=True)
        embed.add_field(name="Created", value=f"<t:{created_epoch}>", inline=True)
        embed.add_field(
            name="Last Updated", value=f"<t:{last_updated_epoch}>", inline=True
        )
        channel_id = int(CONFIG["settings"]["suggestions_forum_id"])
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            await interaction.followup.send(
                "Suggestions channel not found. Please amend config.json",
                ephemeral=True,
            )
            return
        await channel.create_thread(
            name=title,
            reason="New modpack suggestion",
            content=f"**Submitted by {interaction.user.mention}**\n**Why would this pack suit The Mountain?** {self.description.value}",
            embed=embed,
        )
        modal_response = f"You submitted the following modpack: {title}\nShort description: {self.description.value}\nSuggestion link: {channel.mention}"
        await interaction.followup.send(modal_response, ephemeral=True)


class Pack(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command()
    async def pack(self, interaction: nextcord.Interaction):
        pass

    @pack.subcommand(description="Suggest a modpack")
    async def suggest(self, interaction: nextcord.Interaction):
        await interaction.response.send_modal(modal=Suggest(self.bot))
        info(command="pack suggest", interaction=interaction)
