import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} olarak giriş yapıldı.')

@bot.event
async def on_member_join(member):
    channel = member.guild.system_channel
    if channel is None:
        channel = discord.utils.get(member.guild.text_channels, name="genel")
    
    if channel:
        member_count = member.guild.member_count
        await channel.send(f"# HOŞGELDİN BÜCÜR OROSPU ÇOCUĞU {member.mention} {member_count} KİŞİ OLDUK.")

@bot.event
async def on_member_remove(member):
    channel = member.guild.system_channel
    if channel is None:
        channel = discord.utils.get(member.guild.text_channels, name="genel")
    
    if channel:
        member_count = member.guild.member_count
        await channel.send(f"# SİKTİR GİT OROSPU ÇOCUĞU {member.mention} {member_count} KİŞİ KALDIK.")

# Token'ı environment variable'dan al
bot.run(os.getenv("BOT_TOKEN"))
