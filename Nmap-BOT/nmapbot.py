import discord
from discord.ext import commands
import subprocess

# Define intents
intents = discord.Intents.all()
intents.guilds = True
intents.messages = True

# Bot setup
bot = commands.Bot(command_prefix='/', intents=intents)
bot.activity = discord.Game(name="/nmap -A [IP]")

# Discord Bot Token
TOKEN = 'YOUR_DISCORD_BOT_TOKEN'
# Your channel ID to restrict the command
allowed_channel_id = 1217613955304785767

# Function to split the output into chunks of 10 lines
def split_output(output):
    chunks = []
    lines = output.split('\n')
    for i in range(0, len(lines), 10):
        chunk = '\n'.join(lines[i:i+10])
        chunks.append(chunk)
    return chunks

# Command to trigger Nmap scan
@bot.command()
async def nmap(ctx, *args):
    if ctx.channel.id != allowed_channel_id:
        await ctx.send("This command can only be executed in a specific channel.")
        return

    if len(args) < 2:
        await ctx.send("Please provide both the scan options and the IP address.")
        return

    options = args[0]
    ip = args[1]

    # Run Nmap scan
    try:
        await ctx.send(f"> *Scan Started*")
        result = subprocess.run(['nmap', options, ip], capture_output=True, text=True)
        output_chunks = split_output(result.stdout)
        await ctx.send(f"Nmap scan result for {ip}")
        for chunk in output_chunks:
            await ctx.send(f"```{chunk}```")
    except Exception as e:
        await ctx.send(f"Error occurred: {str(e)}")

# Run the bot
bot.run(TOKEN)
