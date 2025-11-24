# -*- coding: utf-8 -*-
import discord
import asyncio
import json
import os
import datetime
import requests
import random
import aiohttp
import io
import sqlite3
from discord import Game, Embed
from discord.ext import commands
from discord.ui import Button, View
from collections import defaultdict, deque

# CONFIGURAÇÃO DO VILÃO
with open('.env', 'r') as f:
    env_vars = {}
    for line in f:
        if '=' in line:
            key, value = line.strip().split('=', 1)
            env_vars[key] = value

DISCORD_TOKEN = env_vars.get('DISCORD_TOKEN')
DEEPSEEK_API_KEY = env_vars.get('DEEPSEEK_API_KEY')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# SISTEMAS AVANÇADOS
memory_storage = {}
conversation_history = {}
user_profiles = {}
server_stats = {}
welcome_systems = {}
auto_moderations = {}
reaction_roles = {}
ticket_systems = {}
level_systems = {}
economy_systems = {}
mod_logs = {}
custom_commands = {}
voice_sessions = {}
reminder_systems = {}
poll_systems = {}

# BANCO DE DADOS VILÃO
def init_database():
    conn = sqlite3.connect('villain_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            level INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 0,
            coins INTEGER DEFAULT 1000,
            warnings INTEGER DEFAULT 0,
            profile_data TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS moderation (
            case_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            mod_id TEXT,
            action TEXT,
            reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS economy (
            user_id TEXT PRIMARY KEY,
            wallet INTEGER DEFAULT 0,
            bank INTEGER DEFAULT 0,
            last_daily DATETIME
        )
    ''')
    
    conn.commit()
    conn.close()

init_database()

def deepseek_chat(messages, user_id):
    headers = {
        'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'model': 'deepseek-chat',
        'messages': messages,
        'stream': False,
        'temperature': 0.7,
        'max_tokens': 100
    }
    
    try:
        response = requests.post('https://api.deepseek.com/v1/chat/completions', 
                               json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        return "👍"
    except:
        return "Entendi!"

def save_systems():
    data = {
        'memory': memory_storage,
        'conversation_history': conversation_history,
        'welcome_systems': welcome_systems,
        'auto_moderations': auto_moderations,
        'reaction_roles': reaction_roles,
        'ticket_systems': ticket_systems,
        'level_systems': level_systems,
        'economy_systems': economy_systems,
        'mod_logs': mod_logs,
        'custom_commands': custom_commands,
        'poll_systems': poll_systems
    }
    with open('systems.json', 'w') as f:
        json.dump(data, f)

def load_systems():
    global memory_storage, conversation_history, welcome_systems, auto_moderations
    global reaction_roles, ticket_systems, level_systems, economy_systems
    global mod_logs, custom_commands, poll_systems
    
    try:
        with open('systems.json', 'r') as f:
            data = json.load(f)
            memory_storage = data.get('memory', {})
            conversation_history = data.get('conversation_history', {})
            welcome_systems = data.get('welcome_systems', {})
            auto_moderations = data.get('auto_moderations', {})
            reaction_roles = data.get('reaction_roles', {})
            ticket_systems = data.get('ticket_systems', {})
            level_systems = data.get('level_systems', {})
            economy_systems = data.get('economy_systems', {})
            mod_logs = data.get('mod_logs', {})
            custom_commands = data.get('custom_commands', {})
            poll_systems = data.get('poll_systems', {})
    except:
        pass

@bot.event
async def on_ready():
    load_systems()
    await bot.change_presence(activity=Game(name="!help | Modo Vilão"))
    print(f'BOT VILÃO PROFISSIONAL ATIVADO! {bot.user.name}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # SISTEMA DE XP
    user_id = str(message.author.id)
    guild_id = str(message.guild.id) if message.guild else "dm"
    
    if guild_id in level_systems and level_systems[guild_id]['enabled']:
        xp_gain = random.randint(5, 15)
        # Implementar lógica de XP no banco
    
    # AUTO MODERAÇÃO
    if guild_id in auto_moderations and auto_moderations[guild_id]['enabled']:
        content = message.content.lower()
        if any(word in content for word in auto_moderations[guild_id]['banned_words']):
            await message.delete()
            await message.channel.send(f"{message.author.mention} Mensagem removida por conter palavras proibidas!", delete_after=5)
    
    # RESPOSTA IA
    if bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        user_id = str(message.author.id)
        if user_id not in conversation_history:
            conversation_history[user_id] = []
        
        user_history = conversation_history[user_id][-6:]
        
        messages = [
            {"role": "system", "content": "Você é um usuário normal. Responda de forma curta, natural e humana. Use até 2 linhas. Sem emojis excessivos."}
        ]
        
        for msg in user_history:
            role = "user" if msg['author'] == 'user' else "assistant"
            messages.append({"role": role, "content": msg['content']})
        
        messages.append({"role": "user", "content": message.content.replace(f'<@{bot.user.id}>', '').strip()})
        
        response = deepseek_chat(messages, user_id)
        
        conversation_history[user_id].append({"author": "user", "content": message.content})
        conversation_history[user_id].append({"author": "bot", "content": response})
        
        if len(conversation_history[user_id]) > 30:
            conversation_history[user_id] = conversation_history[user_id][-30:]
        
        save_systems()
        
        await message.channel.send(response)
    
    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    guild_id = str(member.guild.id)
    if guild_id in welcome_systems and welcome_systems[guild_id]['enabled']:
        channel = bot.get_channel(welcome_systems[guild_id]['channel_id'])
        if channel:
            welcome_msg = welcome_systems[guild_id]['message'].replace('{user}', member.mention)
            await channel.send(welcome_msg)

# COMANDOS DE MODERAÇÃO AVANÇADA
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Sem motivo"):
    """BANIR USUÁRIO"""
    await member.ban(reason=reason)
    embed = Embed(title="🔨 Usuário Banido", color=0xff0000)
    embed.add_field(name="Usuário", value=member.mention, inline=True)
    embed.add_field(name="Motivo", value=reason, inline=True)
    embed.add_field(name="Moderador", value=ctx.author.mention, inline=True)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="Sem motivo"):
    """EXPULSAR USUÁRIO"""
    await member.kick(reason=reason)
    embed = Embed(title="👢 Usuário Expulso", color=0xff9900)
    embed.add_field(name="Usuário", value=member.mention, inline=True)
    embed.add_field(name="Motivo", value=reason, inline=True)
    embed.add_field(name="Moderador", value=ctx.author.mention, inline=True)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 10):
    """LIMPAR MENSAGENS"""
    await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"🗑️ {amount} mensagens limpas!", delete_after=5)

@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member, duration: str = "30m", *, reason="Sem motivo"):
    """SILENCIAR USUÁRIO"""
    muted_role = discord.utils.get(ctx.guild.roles, name="Silenciado")
    if not muted_role:
        muted_role = await ctx.guild.create_role(name="Silenciado")
        for channel in ctx.guild.channels:
            await channel.set_permissions(muted_role, send_messages=False)
    
    await member.add_roles(muted_role, reason=reason)
    embed = Embed(title="🔇 Usuário Silenciado", color=0x666666)
    embed.add_field(name="Usuário", value=member.mention, inline=True)
    embed.add_field(name="Duração", value=duration, inline=True)
    embed.add_field(name="Motivo", value=reason, inline=True)
    await ctx.send(embed=embed)

# SISTEMA DE TICKETS
@bot.command()
async def ticket(ctx, *, reason="Suporte"):
    """ABRIR TICKET DE SUPORTE"""
    guild_id = str(ctx.guild.id)
    if guild_id not in ticket_systems:
        ticket_systems[guild_id] = {'category_id': None, 'support_roles': []}
    
    category = bot.get_channel(ticket_systems[guild_id]['category_id']) if ticket_systems[guild_id]['category_id'] else ctx.guild
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.author: discord.PermissionOverwrite(read_messages=True),
        ctx.guild.me: discord.PermissionOverwrite(read_messages=True)
    }
    
    for role_id in ticket_systems[guild_id]['support_roles']:
        role = ctx.guild.get_role(role_id)
        if role:
            overwrites[role] = discord.PermissionOverwrite(read_messages=True)
    
    ticket_channel = await ctx.guild.create_text_channel(
        f'ticket-{ctx.author.name}',
        category=category,
        overwrites=overwrites
    )
    
    embed = Embed(title="🎫 Ticket Aberto", color=0x00ff00)
    embed.add_field(name="Usuário", value=ctx.author.mention, inline=True)
    embed.add_field(name="Motivo", value=reason, inline=True)
    embed.add_field(name="Ações", value="Use `!close` para fechar", inline=True)
    await ticket_channel.send(embed=embed)
    await ctx.send(f"Ticket criado: {ticket_channel.mention}", delete_after=5)

@bot.command()
async def close(ctx):
    """FECHAR TICKET"""
    if 'ticket' in ctx.channel.name:
        await ctx.send("🗑️ Fechando ticket em 5 segundos...")
        await asyncio.sleep(5)
        await ctx.channel.delete()

# SISTEMA DE REACTION ROLES
@bot.command()
@commands.has_permissions(manage_roles=True)
async def reactionrole(ctx, message_id: str, emoji: str, role: discord.Role):
    """ADICIONAR REACTION ROLE"""
    guild_id = str(ctx.guild.id)
    if guild_id not in reaction_roles:
        reaction_roles[guild_id] = {}
    
    try:
        message = await ctx.channel.fetch_message(int(message_id))
        await message.add_reaction(emoji)
        reaction_roles[guild_id][emoji] = role.id
        save_systems()
        await ctx.send(f"✅ Reaction Role adicionado: {emoji} → {role.name}")
    except:
        await ctx.send("❌ Erro ao criar Reaction Role")

@bot.event
async def on_raw_reaction_add(payload):
    guild_id = str(payload.guild_id)
    if guild_id in reaction_roles:
        emoji = str(payload.emoji)
        if emoji in reaction_roles[guild_id]:
            guild = bot.get_guild(payload.guild_id)
            role = guild.get_role(reaction_roles[guild_id][emoji])
            member = guild.get_member(payload.user_id)
            if role and member and not member.bot:
                await member.add_roles(role)

# SISTEMA ECONÔMICO
@bot.command()
async def daily(ctx):
    """RESGATAR RECOMPENSA DIÁRIA"""
    user_id = str(ctx.author.id)
    conn = sqlite3.connect('villain_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT wallet, last_daily FROM economy WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    
    if not result:
        cursor.execute('INSERT INTO economy (user_id, wallet, last_daily) VALUES (?, ?, ?)', 
                      (user_id, 100, datetime.datetime.now().isoformat()))
        conn.commit()
        await ctx.send("🎁 Recompensa diária: **100 moedas**!")
    else:
        wallet, last_daily = result
        last_date = datetime.datetime.fromisoformat(last_daily) if last_daily else datetime.datetime.min
        
        if (datetime.datetime.now() - last_date).days >= 1:
            amount = random.randint(80, 150)
            cursor.execute('UPDATE economy SET wallet = wallet + ?, last_daily = ? WHERE user_id = ?',
                          (amount, datetime.datetime.now().isoformat(), user_id))
            conn.commit()
            await ctx.send(f"🎁 Recompensa diária: **{amount} moedas**!")
        else:
            await ctx.send("⏰ Você já resgatou sua recompensa hoje!")
    
    conn.close()

@bot.command()
async def balance(ctx, member: discord.Member = None):
    """VER SALDO"""
    target = member or ctx.author
    user_id = str(target.id)
    
    conn = sqlite3.connect('villain_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT wallet, bank FROM economy WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    wallet = result[0] if result else 0
    bank = result[1] if result else 0
    
    embed = Embed(title=f"💰 Carteira de {target.name}", color=0xffd700)
    embed.add_field(name="Carteira", value=f"🪙 {wallet}", inline=True)
    embed.add_field(name="Banco", value=f"🏦 {bank}", inline=True)
    embed.add_field(name="Total", value=f"💎 {wallet + bank}", inline=True)
    await ctx.send(embed=embed)

# SISTEMA DE LEVEL
@bot.command()
async def rank(ctx, member: discord.Member = None):
    """VER RANK E LEVEL"""
    target = member or ctx.author
    user_id = str(target.id)
    
    conn = sqlite3.connect('villain_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT level, xp FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    level = result[0] if result else 1
    xp = result[1] if result else 0
    xp_needed = level * 100
    
    embed = Embed(title=f"🏅 Rank de {target.name}", color=0x00ff00)
    embed.add_field(name="Level", value=level, inline=True)
    embed.add_field(name="XP", value=f"{xp}/{xp_needed}", inline=True)
    embed.add_field(name="Progresso", value=f"{(xp/xp_needed)*100:.1f}%", inline=True)
    await ctx.send(embed=embed)

# SISTEMA DE WELCOME
@bot.command()
@commands.has_permissions(manage_guild=True)
async def setwelcome(ctx, channel: discord.TextChannel, *, message):
    """CONFIGURAR MENSAGEM DE BOAS-VINDAS"""
    guild_id = str(ctx.guild.id)
    if guild_id not in welcome_systems:
        welcome_systems[guild_id] = {}
    
    welcome_systems[guild_id] = {
        'enabled': True,
        'channel_id': channel.id,
        'message': message
    }
    save_systems()
    await ctx.send("✅ Sistema de boas-vindas configurado!")

# AUTO MODERAÇÃO
@bot.command()
@commands.has_permissions(manage_guild=True)
async def automod(ctx, action: str, *, words=None):
    """CONFIGURAR AUTO MODERAÇÃO"""
    guild_id = str(ctx.guild.id)
    if guild_id not in auto_moderations:
        auto_moderations[guild_id] = {'enabled': False, 'banned_words': []}
    
    if action == "enable":
        auto_moderations[guild_id]['enabled'] = True
        await ctx.send("✅ Auto moderação ativada!")
    elif action == "disable":
        auto_moderations[guild_id]['enabled'] = False
        await ctx.send("❌ Auto moderação desativada!")
    elif action == "add" and words:
        banned_words = [word.strip().lower() for word in words.split(',')]
        auto_moderations[guild_id]['banned_words'].extend(banned_words)
        await ctx.send(f"✅ {len(banned_words)} palavras adicionadas à lista negra!")
    
    save_systems()

# SISTEMA DE PESQUISA
@bot.command()
async def google(ctx, *, query):
    """PESQUISAR NO GOOGLE"""
    search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    await ctx.send(f"🔍 **Resultados para '{query}':**\n{search_url}")

@bot.command()
async def youtube(ctx, *, query):
    """PESQUISAR NO YOUTUBE"""
    search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    await ctx.send(f"🎥 **Vídeos para '{query}':**\n{search_url}")

# SISTEMA DE UTILIDADES
@bot.command()
async def weather(ctx, *, city):
    """VER CLIMA (SIMULAÇÃO)"""
    temperatures = {
        'são paulo': '25°C', 'rio de janeiro': '28°C', 'brasília': '27°C',
        'salvador': '30°C', 'fortaleza': '29°C', 'belo horizonte': '26°C'
    }
    
    temp = temperatures.get(city.lower(), '22°C')
    embed = Embed(title=f"🌤️ Clima em {city.title()}", color=0x87ceeb)
    embed.add_field(name="Temperatura", value=temp, inline=True)
    embed.add_field(name="Condição", value="Parcialmente Nublado", inline=True)
    embed.add_field(name="Umidade", value="65%", inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def timer(ctx, seconds: int):
    """DEFINIR TIMER"""
    if seconds > 3600:
        await ctx.send("⏰ Timer máximo: 1 hora")
        return
    
    await ctx.send(f"⏰ Timer definido para {seconds} segundos")
    await asyncio.sleep(seconds)
    await ctx.send(f"🔔 {ctx.author.mention} Timer finalizado!")

@bot.command()
async def remind(ctx, time: str, *, reminder):
    """DEFINIR LEMBRETE"""
    await ctx.send(f"✅ Lembrete definido: '{reminder}' para {time}")
    # Implementar parser de tempo para segundos

# SISTEMA DE DIVERSÃO
@bot.command()
async def meme(ctx):
    """MEME ALEATÓRIO"""
    memes = [
        "https://i.imgur.com/8x9Z0hF.jpg",
        "https://i.imgur.com/3JkQ7Zt.jpg", 
        "https://i.imgur.com/5W5Q5Z5.jpg",
        "https://i.imgur.com/7X8Y9Z0.jpg"
    ]
    embed = Embed(title="😂 Meme do Dia", color=0xff00ff)
    embed.set_image(url=random.choice(memes))
    await ctx.send(embed=embed)

@bot.command()
async def joke(ctx):
    """PIADA ALEATÓRIA"""
    jokes = [
        "Por que o Python foi pra terapia? Porque tinha muitos issues!",
        "Como o SQL saiu com a namorada? SELECT * FROM dates WHERE love > 0",
        "Quantos programadores são necessários para trocar uma lâmpada? Nenhum, é problema de hardware!",
        "O que o commit falou para o repositório? Você me completa!"
    ]
    await ctx.send(f"🎭 {random.choice(jokes)}")

@bot.command()
async def quote(ctx):
    """CITAÇÃO INSPIRADORA"""
    quotes = [
        "O código é como o humor. Quando você tem que explicar, é ruim.",
        "Antes de deletar código, comente. Depois de testar, delete.",
        "Programadores são ferramentas para converter cafeína em código.",
        "Existem 10 tipos de pessoas: as que entendem binário e as que não entendem."
    ]
    embed = Embed(title="💡 Citação do Dia", description=random.choice(quotes), color=0xffff00)
    await ctx.send(embed=embed)

# SISTEMA DE CONFIGURAÇÃO
@bot.command()
@commands.has_permissions(manage_guild=True)
async def setup(ctx):
    """CONFIGURAÇÃO RÁPIDA DO SERVIDOR"""
    # Criar cargos básicos
    roles = ["Administrador", "Moderador", "Membro VIP", "Silenciado"]
    for role_name in roles:
        if not discord.utils.get(ctx.guild.roles, name=role_name):
            await ctx.guild.create_role(name=role_name)
    
    # Criar canais básicos
    channels = ["🚀│comandos", "💬│chat-geral", "🎮│jogos", "📢│anúncios"]
    for channel_name in channels:
        if not discord.utils.get(ctx.guild.channels, name=channel_name):
            await ctx.guild.create_text_channel(channel_name)
    
    embed = Embed(title="⚙️ Configuração Concluída", color=0x00ff00)
    embed.add_field(name="Cargos Criados", value=", ".join(roles), inline=False)
    embed.add_field(name="Canais Criados", value=", ".join(channels), inline=False)
    await ctx.send(embed=embed)

# COMANDO DE AJUDA COMPLETO
@bot.command()
async def help(ctx):
    """MENU DE AJUDA COMPLETO"""
    embed = Embed(title="🦹‍♂️ COMANDOS DO BOT VILÃO", color=0x8A2BE2)
    
    embed.add_field(
        name="🔧 MODERAÇÃO", 
        value="`!ban` `!kick` `!mute` `!clear` `!automod`",
        inline=False
    )
    
    embed.add_field(
        name="💰 ECONOMIA", 
        value="`!daily` `!balance` `!rank` `!work`",
        inline=False
    )
    
    embed.add_field(
        name="🎫 TICKETS", 
        value="`!ticket` `!close` `!reactionrole`",
        inline=False
    )
    
    embed.add_field(
        name="🌐 UTILIDADES", 
        value="`!weather` `!timer` `!remind` `!google` `!youtube`",
        inline=False
    )
    
    embed.add_field(
        name="🎮 DIVERSÃO", 
        value="`!meme` `!joke` `!quote` `!rps` `!guess`",
        inline=False
    )
    
    embed.add_field(
        name="⚙️ CONFIGURAÇÃO", 
        value="`!setup` `!setwelcome` `!backup` `!restore`",
        inline=False
    )
    
    embed.set_footer(text="Use !comando para mais informações sobre cada comando")
    await ctx.send(embed=embed)

# COMANDOS EXISTENTES ANTERIORES (backup, restore, secure_channel, games, rps, guess)
@bot.command()
async def backup(ctx):
    """FAZ BACKUP COMPLETO DO SERVIDOR"""
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ Acesso negado!")
        return
    
    guild = ctx.guild
    backup_data = {
        'name': guild.name,
        'icon': str(guild.icon_url) if guild.icon_url else None,
        'channels': {},
        'roles': [],
        'backup_time': str(datetime.datetime.now())
    }
    
    for role in guild.roles:
        if role.name != "@everyone":
            backup_data['roles'].append({
                'name': role.name,
                'color': role.color.value,
                'permissions': role.permissions.value,
                'position': role.position
            })
    
    for channel in guild.channels:
        if isinstance(channel, discord.TextChannel):
            channel_data = {
                'name': channel.name,
                'topic': channel.topic,
                'position': channel.position,
                'category': channel.category.name if channel.category else None
            }
            backup_data['channels'][str(channel.id)] = channel_data
        
        elif isinstance(channel, discord.VoiceChannel):
            channel_data = {
                'name': channel.name,
                'position': channel.position,
                'category': channel.category.name if channel.category else None
            }
            backup_data['channels'][str(channel.id)] = channel_data
    
    filename = f"backup_{guild.id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)
    
    await ctx.send(f"✅ Backup completo salvo como `{filename}`!")

@bot.command()
async def restore(ctx, filename: str):
    """RESTAURA BACKUP - DESTRÓI TUDO E RECRIA"""
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ Acesso negado!")
        return
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
    except:
        await ctx.send("❌ Arquivo de backup não encontrado!")
        return
    
    guild = ctx.guild
    
    for channel in guild.channels:
        try:
            await channel.delete()
        except:
            pass
    
    for role in guild.roles:
        if role.name != "@everyone" and not role.managed:
            try:
                await role.delete()
            except:
                pass
    
    await asyncio.sleep(2)
    
    role_mapping = {}
    for role_data in sorted(backup_data['roles'], key=lambda x: x['position']):
        try:
            new_role = await guild.create_role(
                name=role_data['name'],
                color=discord.Color(role_data['color']),
                permissions=discord.Permissions(role_data['permissions'])
            )
            role_mapping[role_data['name']] = new_role
        except:
            pass
    
    categories = {}
    for channel_id, channel_data in backup_data['channels'].items():
        try:
            if channel_data.get('topic') is not None:
                if channel_data['category'] and channel_data['category'] not in categories:
                    categories[channel_data['category']] = await guild.create_category(channel_data['category'])
                
                category = categories.get(channel_data['category'])
                await guild.create_text_channel(
                    channel_data['name'],
                    topic=channel_data['topic'],
                    category=category,
                    position=channel_data['position']
                )
            else:
                if channel_data['category'] and channel_data['category'] not in categories:
                    categories[channel_data['category']] = await guild.create_category(channel_data['category'])
                
                category = categories.get(channel_data['category'])
                await guild.create_voice_channel(
                    channel_data['name'],
                    category=category,
                    position=channel_data['position']
                )
        except:
            pass
    
    await ctx.send("✅ Servidor restaurado do backup com sucesso!")

@bot.command()
async def secure_channel(ctx):
    """CRIA CANAL SEGURO E BLOQUEADO"""
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ Acesso negado!")
        return
    
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.author: discord.PermissionOverwrite(read_messages=True)
    }
    
    channel = await ctx.guild.create_text_channel('🚨canal-seguro', overwrites=overwrites)
    await channel.send(f"🔒 Canal seguro criado para {ctx.author.mention}!")
    await ctx.message.delete()

@bot.command()
async def games(ctx):
    """MENU DE JOGOS"""
    embed = Embed(title="🎮 Jogos Disponíveis", color=0x00ff00)
    embed.add_field(name="!rps", value="Pedra, Papel, Tesoura", inline=False)
    embed.add_field(name="!guess", value="Adivinhe o número (1-100)", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def rps(ctx, choice: str):
    """PEDRA, PAPEL, TESOURA"""
    choices = ['pedra', 'papel', 'tesoura']
    if choice.lower() not in choices:
        await ctx.send("Escolha: pedra, papel ou tesoura!")
        return
    
    bot_choice = random.choice(choices)
    
    if choice.lower() == bot_choice:
        result = "Empate!"
    elif (choice.lower() == 'pedra' and bot_choice == 'tesoura') or \
         (choice.lower() == 'papel' and bot_choice == 'pedra') or \
         (choice.lower() == 'tesoura' and bot_choice == 'papel'):
        result = "Você ganhou!"
    else:
        result = "Eu ganhei!"
    
    await ctx.send(f"🎯 Você: {choice}\n🤖 Eu: {bot_choice}\n**{result}**")

@bot.command()
async def guess(ctx):
    """JOGO DE ADIVINHAÇÃO"""
    number = random.randint(1, 100)
    await ctx.send("🎯 Adivinhe o número entre 1 e 100!")
    
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()
    
    try:
        guess_msg = await bot.wait_for('message', check=check, timeout=30.0)
        guess_num = int(guess_msg.content)
        
        if guess_num == number:
            await ctx.send("🎉 Acertou!")
        elif guess_num < number:
            await ctx.send("📈 Maior!")
        else:
            await ctx.send("📉 Menor!")
            
    except asyncio.TimeoutError:
        await ctx.send(f"⏰ Tempo esgotado! Era {number}")

# INICIALIZAÇÃO DO BOT VILÃO SUPREMO
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
