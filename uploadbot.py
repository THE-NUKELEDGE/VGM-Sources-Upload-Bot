import discord
from discord.ext import commands
import re
import asyncio
import json
from datetime import datetime, timezone

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

url_pattern = re.compile(r'http[s]?://')

monitored_channels = {}
repost_channels = {}
debug_channel_id = None

# Load channel data from a JSON file if it exists
try:
    with open('channel_data.json', 'r') as f:
        data = json.load(f)
        monitored_channels = data.get('monitored_channels', {})
        repost_channels = data.get('repost_channels', {})
        debug_channel_id = data.get('debug_channel_id')
except FileNotFoundError:
    pass

# Function to check if the user has a role with the "kick members" permission
def can_kick_members(ctx):
    permissions = ctx.author.guild_permissions
    return permissions.kick_members

# Function to check if the message is created after a specific date
def is_after_date(message, date):
    return message.created_at.replace(tzinfo=timezone.utc) > date.replace(tzinfo=timezone.utc)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    global debug_channel_id
    if debug_channel_id:
        debug_channel = bot.get_channel(debug_channel_id)
        if debug_channel:
            # await debug_channel.send("Bot restarted. Current monitored and repost channels:")
            await print_channel_data()

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Check if the message is created after 5/25/2024
    if not is_after_date(message, datetime(2024, 5, 25)):
        return

    # Check if the message is in a monitored channel
    if message.channel.id in monitored_channels.values():
        # Check if the message has no attachments and no URLs
        if not message.attachments and not url_pattern.search(message.content):
            # Repost the message in the repost channel
            repost_channel_id = repost_channels.get(message.guild.id)
            if repost_channel_id:
                repost_channel = bot.get_channel(repost_channel_id)
                if repost_channel:
                    monitored_channel = discord.utils.get(message.guild.channels, id=message.channel.id)
                    repost_message = f"Message from {message.author.mention} in {monitored_channel.mention}: {message.content}"
                    await repost_channel.send(repost_message)
            # Delete the message from the monitored channel
            await message.delete()
            # Inform the user
            msg = await message.channel.send("Your message was deleted as you must be uploading either a link or an attachment to #uploads! Conversation or questions about something in the #uploads chat can take place in #general or #off-topic. This message will be deleted after 20 seconds.")
            await asyncio.sleep(20)
            await msg.delete()
            return

    await bot.process_commands(message)

@bot.command()
@commands.check(can_kick_members)
async def set_monitored_channel(ctx, channel: discord.TextChannel):
    monitored_channels[ctx.guild.id] = channel.id
    await ctx.send(f"Monitored channel set to {channel.mention}")
    # Save channel data
    save_channel_data()

@bot.command()
@commands.check(can_kick_members)
async def set_repost_channel(ctx, channel: discord.TextChannel):
    repost_channels[ctx.guild.id] = channel.id
    await ctx.send(f"Repost channel set to {channel.mention}")
    # Save channel data
    save_channel_data()

@bot.command()
@commands.check(can_kick_members)
async def set_debug_channel(ctx, channel: discord.TextChannel):
    global debug_channel_id
    debug_channel_id = channel.id
    await ctx.send(f"Debug channel set to {channel.mention}")
    # Save channel data
    save_channel_data()

@bot.command()
@commands.check(can_kick_members)
async def debug_channels(ctx):
    if debug_channel_id:
        debug_channel = bot.get_channel(debug_channel_id)
        if debug_channel:
            await debug_channel.send("Current monitored and repost channels:")
            await print_channel_data()
        else:
            await ctx.send("Debug channel not found. Please set it again using !set_debug_channel command.")
    else:
        await ctx.send("Debug channel not set. Please use !set_debug_channel command.")

@bot.command()
@commands.check(can_kick_members)
async def show_debug_info(ctx):
    global debug_channel_id
    if debug_channel_id:
        debug_channel = bot.get_channel(debug_channel_id)
        if debug_channel:
            await print_channel_data()
        else:
            await ctx.send("Debug channel not found. Please set it again using !set_debug_channel command.")
    else:
        await ctx.send("Debug channel not set. Please use !set_debug_channel command.")

@bot.command()
@commands.check(can_kick_members)
async def print_debug_info(ctx):
    global monitored_channels, repost_channels, debug_channel_id
    if debug_channel_id:
        output = f"Monitored Channels: {', '.join(str(channel_id) for channel_id in monitored_channels.values())}\n"
        output += f"Repost Channels: {', '.join(str(channel_id) for channel_id in repost_channels.values())}\n"
        output += f"Debug Channel ID: {debug_channel_id}\n"
        await ctx.send("```" + output + "```")
    else:
        await ctx.send("Debug channel not set. Please use !set_debug_channel command.")

# Function to save monitored and repost channels to the JSON file
def save_channel_data():
    data = {'monitored_channels': monitored_channels, 'repost_channels': repost_channels, 'debug_channel_id': debug_channel_id}
    with open('channel_data.json', 'w') as f:
        json.dump(data, f)

# Function to print monitored and repost channels to debug channel
async def print_channel_data():
    global debug_channel_id
    if debug_channel_id:
        debug_channel = bot.get_channel(debug_channel_id)
        if debug_channel:
            monitored_channel_mentions = [discord.utils.get(bot.get_all_channels(), id=channel_id).mention for channel_id in monitored_channels.values()]
            repost_channel_mentions = [discord.utils.get(bot.get_all_channels(), id=channel_id).mention for channel_id in repost_channels.values()]
            await debug_channel.send(f"Monitored channels: {', '.join(monitored_channel_mentions)}")
            await debug_channel.send(f"Repost channels: {', '.join(repost_channel_mentions)}")
        else:
            print("Debug channel not found.")

bot.run('TOKEN')
