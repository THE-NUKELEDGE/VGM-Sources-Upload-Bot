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
show_debug_info = False

def load_channel_data():
    global monitored_channels, repost_channels, debug_channel_id, show_debug_info
    try:
        with open('channel_data.json', 'r') as f:
            data = json.load(f)
            monitored_channels = data.get('monitored_channels', {})
            repost_channels = data.get('repost_channels', {})
            debug_channel_id = data.get('debug_channel_id')
            show_debug_info = data.get('show_debug_info', False)
    except FileNotFoundError:
        pass

load_channel_data()

def can_kick_members(ctx):
    return ctx.author.guild_permissions.kick_members

def is_after_date(message, date):
    return message.created_at.replace(tzinfo=timezone.utc) > date.replace(tzinfo=timezone.utc)

async def notify_debug_channel(message):
    if debug_channel_id and show_debug_info:
        debug_channel = bot.get_channel(debug_channel_id)
        if debug_channel:
            await debug_channel.send(message)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if not is_after_date(message, datetime(2024, 5, 25)):
        return

    if message.channel.id in monitored_channels.values():
        if not message.attachments and not url_pattern.search(message.content):
            repost_channel_id = repost_channels.get(message.guild.id)
            if repost_channel_id:
                repost_channel = bot.get_channel(repost_channel_id)
                if repost_channel:
                    monitored_channel = discord.utils.get(message.guild.channels, id=message.channel.id)
                    repost_message = f"Message from {message.author.mention} in {monitored_channel.mention}: {message.content}"
                    await repost_channel.send(repost_message)
            await message.delete()
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
    save_channel_data()

@bot.command()
@commands.check(can_kick_members)
async def set_repost_channel(ctx, channel: discord.TextChannel):
    repost_channels[ctx.guild.id] = channel.id
    await ctx.send(f"Repost channel set to {channel.mention}")
    save_channel_data()

@bot.command()
@commands.check(can_kick_members)
async def set_debug_channel(ctx, channel: discord.TextChannel):
    global debug_channel_id
    debug_channel_id = channel.id
    await ctx.send(f"Debug channel set to {channel.mention}")
    save_channel_data()

@bot.command()
@commands.is_owner()
async def debug_channels(ctx):
    await notify_debug_channel("Current monitored and repost channels:")
    await print_channel_data()

@bot.command()
@commands.is_owner()
async def toggle_debug_info(ctx):
    global show_debug_info
    show_debug_info = not show_debug_info
    state = "enabled" if show_debug_info else "disabled"
    await ctx.send(f"Debug info is now {state}.")
    save_channel_data()

@bot.command()
@commands.is_owner()
async def show_debug_info(ctx):
    debug_status = "enabled" if show_debug_info else "disabled"
    monitored_channel_mentions = [discord.utils.get(bot.get_all_channels(), id=channel_id).mention for channel_id in monitored_channels.values()]
    repost_channel_mentions = [discord.utils.get(bot.get_all_channels(), id=channel_id).mention for channel_id in repost_channels.values()]
    debug_channel = bot.get_channel(debug_channel_id)
    debug_channel_mention = debug_channel.mention if debug_channel else "None"
    await ctx.send(f"Debug info is currently {debug_status}.")
    await ctx.send(f"Monitored channels: {', '.join(monitored_channel_mentions) if monitored_channel_mentions else 'None'}")
    await ctx.send(f"Repost channels: {', '.join(repost_channel_mentions) if repost_channel_mentions else 'None'}")
    await ctx.send(f"Debug channel: {debug_channel_mention}")

def save_channel_data():
    data = {
        'monitored_channels': monitored_channels,
        'repost_channels': repost_channels,
        'debug_channel_id': debug_channel_id,
        'show_debug_info': show_debug_info
    }
    with open('channel_data.json', 'w') as f:
        json.dump(data, f)

async def print_channel_data():
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
