import discord
from discord.ext import commands
import requests

# REPLACE THESE BELOW
bot_token = 'YOUR_BOT_TOKEN_HERE'
channel_id = 1219248017421504553
api_token = 'YOUR_PICARTA_TOKEN'

url = "https://picarta.ai/classify"
headers = {"Content-Type": "application/json"}
intents = discord.Intents.all()
intents.messages = True 
bot = commands.Bot(command_prefix='!', intents=intents)
bot.activity = discord.Game(name="Upload to #image-osint-bot channel")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.event
async def on_message(message):
    # Check if message has attachments and is in the specified channel
    if message.channel.id == channel_id and message.attachments:
        # Iterate through each attachment
        for attachment in message.attachments:
            img_url = attachment.url
            result = await classify_image(img_url)  # Await here
            await message.channel.send(embed=embed_result(result))

async def classify_image(img_url):
    payload = {"TOKEN": api_token, "IMAGE": img_url}
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def embed_result(result):
    if result:
        embed = discord.Embed(title=":mag: Image OSINT Results :mag_right:", color=0x00ff00)
        embed.add_field(name="Country", value=result.get('ai_country', 'Unknown'))
        embed.add_field(name="City", value=result.get('city', 'Unknown'))
        embed.add_field(name="Province", value=result.get('province', 'Unknown'))
        embed.add_field(name="Latitude", value=result.get('ai_lat', 'Unknown'))
        embed.add_field(name="Longitude", value=result.get('ai_lon', 'Unknown'))
    else:
        embed = discord.Embed(title="Image Classification Result", description="Failed to classify the image", color=0xff0000)
    return embed
bot.run(bot_token)