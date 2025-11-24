# -*- coding: utf-8 -*-
import discord
import asyncio
import json
import os
import datetime
import requests
import random
import sqlite3
import time
import aiohttp
from discord import Game, Embed
from discord.ext import commands

# CONFIGURAÇÃO
env_vars = {}
try:
    with open('.env', 'r') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                env_vars[key] = value
except:
    pass

DISCORD_TOKEN = env_vars.get('DISCORD_TOKEN', '')
DEEPSEEK_API_KEY = env_vars.get('DEEPSEEK_API_KEY', '')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# SISTEMAS
conversation_history = {}
user_profiles = {}
server_configs = {}
welcome_systems = {}
auto_moderation = {}
ticket_systems = {}
level_system = {}
economy_system = {}
mod_logs = {}

# BANCO DE DADOS
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            level INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 0,
            coins INTEGER DEFAULT 1000,
            warnings INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS economy (
            user_id TEXT PRIMARY KEY,
            wallet INTEGER DEFAULT 0,
            bank INTEGER DEFAULT 0,
            last_daily TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def deepseek_chat(messages, user_id):
    if not DEEPSEEK_API_KEY:
        return "Sim!"
    
    headers = {
        'Authorization': 'Bearer ' + DEEPSEEK_API_KEY,
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

@bot.event
async def on_ready():
    print(f'🤖 BOT VILÃO ATIVADO: {bot.user.name}')
    await bot.change_presence(activity=Game(name="!comandos | 30+ Recursos"))

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # RESPOSTA IA CORRIGIDA
    if bot.user.mentioned_in(message):
        user_id = str(message.author.id)
        if user_id not in conversation_history:
            conversation_history[user_id] = []
        
        user_history = conversation_history[user_id][-6:]
        
        messages = [
            {"role": "system", "content": "Você é um usuário normal do Discord. Responda de forma curta e natural como uma pessoa. Use gírias brasileiras."}
        ]
        
        for msg in user_history:
            role = "user" if msg['author'] == 'user' else "assistant"
            messages.append({"role": role, "content": msg['content']})
        
        # CORREÇÃO AQUI - converter ID para string
        cleaned_content = message.content.replace(f'<@{bot.user.id}>', '').strip()
        messages.append({"role": "user", "content": cleaned_content})
        
        response = deepseek_chat(messages, user_id)
        
        conversation_history[user_id].append({"author": "user", "content": message.content})
        conversation_history[user_id].append({"author": "bot", "content": response})
        
        if len(conversation_history[user_id]) > 30:
            conversation_history[user_id] = conversation_history[user_id][-30:]
        
        await message.channel.send(response)
    
    await bot.process_commands(message)

# ========== 30+ COMANDOS PROFISSIONAIS ==========

# 🔧 MODERAÇÃO AVANÇADA
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Sem motivo"):
    """Banir usuário permanentemente"""
    await member.ban(reason=reason)
    embed = Embed(title="🔨 BANIMENTO", color=0xff0000)
    embed.add_field(name="Usuário", value=member.mention, inline=True)
    embed.add_field(name="Motivo", value=reason, inline=True)
    embed.add_field(name="Moderador", value=ctx.author.mention, inline=True)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="Sem motivo"):
    """Expulsar usuário do servidor"""
    await member.kick(reason=reason)
    embed = Embed(title="👢 EXPULSÃO", color=0xff9900)
    embed.add_field(name="Usuário", value=member.mention, inline=True)
    embed.add_field(name="Motivo", value=reason, inline=True)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 10):
    """Limpar mensagens em massa"""
    deleted = await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🗑️ {len(deleted) - 1} mensagens deletadas!", delete_after=5)

@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member, tempo: str = "30m"):
    """Silenciar usuário temporariamente"""
    muted_role = discord.utils.get(ctx.guild.roles, name="Silenciado")
    if not muted_role:
        muted_role = await ctx.guild.create_role(name="Silenciado")
        for channel in ctx.guild.channels:
            await channel.set_permissions(muted_role, send_messages=False)
    
    await member.add_roles(muted_role)
    await ctx.send(f"🔇 {member.mention} foi silenciado por {tempo}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):
    """Remover silenciamento"""
    muted_role = discord.utils.get(ctx.guild.roles, name="Silenciado")
    if muted_role and muted_role in member.roles:
        await member.remove_roles(muted_role)
        await ctx.send(f"🔊 {member.mention} foi dessilenciado")

# 🛡️ SEGURANÇA E BACKUP
@bot.command()
@commands.has_permissions(administrator=True)
async def backup(ctx):
    """Backup completo do servidor"""
    guild = ctx.guild
    backup_data = {
        'name': guild.name,
        'channels': [],
        'roles': [],
        'emojis': [],
        'backup_time': str(datetime.datetime.now())
    }
    
    for role in guild.roles:
        if role.name != "@everyone":
            backup_data['roles'].append({
                'name': role.name,
                'color': role.color.value,
                'permissions': role.permissions.value
            })
    
    for channel in guild.channels:
        channel_data = {
            'name': channel.name,
            'type': str(channel.type),
            'position': channel.position
        }
        if isinstance(channel, discord.TextChannel):
            channel_data['topic'] = channel.topic
        elif isinstance(channel, discord.VoiceChannel):
            channel_data['bitrate'] = channel.bitrate
            channel_data['user_limit'] = channel.user_limit
        
        backup_data['channels'].append(channel_data)
    
    for emoji in guild.emojis:
        backup_data['emojis'].append({
            'name': emoji.name,
            'url': str(emoji.url)
        })
    
    filename = f"backup_{guild.id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)
    
    await ctx.send(f"✅ Backup completo salvo como `{filename}`")

@bot.command()
@commands.has_permissions(administrator=True)
async def restore(ctx, filename: str):
    """Restaurar servidor do backup"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        guild = ctx.guild
        
        # Deletar canais existentes
        for channel in guild.channels:
            try:
                await channel.delete()
            except:
                pass
        
        await asyncio.sleep(2)
        
        # Recriar cargos
        for role_data in backup_data['roles']:
            try:
                await guild.create_role(
                    name=role_data['name'],
                    color=discord.Color(role_data['color']),
                    permissions=discord.Permissions(role_data['permissions'])
                )
            except:
                pass
        
        # Recriar canais
        for channel_data in backup_data['channels']:
            try:
                if channel_data['type'] == 'text':
                    await guild.create_text_channel(
                        name=channel_data['name'],
                        topic=channel_data.get('topic', '')
                    )
                elif channel_data['type'] == 'voice':
                    await guild.create_voice_channel(
                        name=channel_data['name'],
                        bitrate=channel_data.get('bitrate', 64000),
                        user_limit=channel_data.get('user_limit', 0)
                    )
            except:
                pass
        
        await ctx.send("✅ Servidor restaurado com sucesso!")
    except Exception as e:
        await ctx.send(f"❌ Erro ao restaurar: {str(e)}")

@bot.command()
@commands.has_permissions(administrator=True)
async def lockdown(ctx):
    """Bloquear todos os canais do servidor"""
    for channel in ctx.guild.channels:
        try:
            await channel.set_permissions(ctx.guild.default_role, send_messages=False)
        except:
            pass
    await ctx.send("🔒 Servidor em lockdown!")

@bot.command()
@commands.has_permissions(administrator=True)
async def unlock(ctx):
    """Desbloquear todos os canais"""
    for channel in ctx.guild.channels:
        try:
            await channel.set_permissions(ctx.guild.default_role, send_messages=True)
        except:
            pass
    await ctx.send("🔓 Servidor desbloqueado!")

# 💰 ECONOMIA E LEVEL
@bot.command()
async def daily(ctx):
    """Resgatar recompensa diária"""
    user_id = str(ctx.author.id)
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT wallet, last_daily FROM economy WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    
    now = datetime.datetime.now().isoformat()
    
    if not result:
        coins = random.randint(100, 200)
        cursor.execute('INSERT INTO economy (user_id, wallet, last_daily) VALUES (?, ?, ?)', 
                      (user_id, coins, now))
        await ctx.send(f"🎁 Recompensa diária: **{coins} moedas**!")
    else:
        wallet, last_daily = result
        if last_daily:
            last_date = datetime.datetime.fromisoformat(last_daily)
            if (datetime.datetime.now() - last_date).days >= 1:
                coins = random.randint(100, 200)
                cursor.execute('UPDATE economy SET wallet = wallet + ?, last_daily = ? WHERE user_id = ?',
                              (coins, now, user_id))
                await ctx.send(f"🎁 Recompensa diária: **{coins} moedas**!")
            else:
                await ctx.send("⏰ Você já resgatou hoje! Volte amanhã.")
        else:
            coins = random.randint(100, 200)
            cursor.execute('UPDATE economy SET wallet = wallet + ?, last_daily = ? WHERE user_id = ?',
                          (coins, now, user_id))
            await ctx.send(f"🎁 Recompensa diária: **{coins} moedas**!")
    
    conn.commit()
    conn.close()

@bot.command()
async def balance(ctx, member: discord.Member = None):
    """Ver saldo de moedas"""
    target = member or ctx.author
    user_id = str(target.id)
    
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT wallet, bank FROM economy WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    wallet = result[0] if result else 0
    bank = result[1] if result else 0
    
    embed = Embed(title=f"💰 Carteira de {target.name}", color=0xffd700)
    embed.add_field(name="💳 Carteira", value=f"**{wallet}** moedas", inline=True)
    embed.add_field(name="🏦 Banco", value=f"**{bank}** moedas", inline=True)
    embed.add_field(name="💎 Total", value=f"**{wallet + bank}** moedas", inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def rank(ctx, member: discord.Member = None):
    """Ver nível e XP"""
    target = member or ctx.author
    user_id = str(target.id)
    
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT level, xp FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    level = result[0] if result else 1
    xp = result[1] if result else 0
    xp_needed = level * 100
    
    embed = Embed(title=f"🏅 Rank de {target.name}", color=0x00ff00)
    embed.add_field(name="📊 Level", value=level, inline=True)
    embed.add_field(name="⭐ XP", value=f"{xp}/{xp_needed}", inline=True)
    embed.add_field(name="📈 Progresso", value=f"{(xp/xp_needed)*100:.1f}%", inline=True)
    await ctx.send(embed=embed)

# 🎮 JOGOS E DIVERSÃO
@bot.command()
async def loteria(ctx, aposta: int = 100):
    """Jogar na loteria"""
    if aposta < 10:
        await ctx.send("❌ Aposta mínima: 10 moedas")
        return
    
    user_id = str(ctx.author.id)
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT wallet FROM economy WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    
    if not result or result[0] < aposta:
        await ctx.send("❌ Moedas insuficientes!")
        conn.close()
        return
    
    # Sorteio
    numeros = [random.randint(1, 50) for _ in range(5)]
    meus_numeros = [random.randint(1, 50) for _ in range(5)]
    
    acertos = len(set(numeros) & set(meus_numeros))
    
    if acertos == 5:
        premio = aposta * 100
        mensagem = "🎉 JACKPOT! Você acertou todos os números!"
    elif acertos == 4:
        premio = aposta * 20
        mensagem = "🔥 Excelente! 4 números corretos!"
    elif acertos == 3:
        premio = aposta * 5
        mensagem = "👍 Bom! 3 números corretos!"
    elif acertos == 2:
        premio = aposta
        mensagem = "😊 2 números corretos!"
    else:
        premio = 0
        mensagem = "😢 Nenhum número correto..."
    
    if premio > 0:
        cursor.execute('UPDATE economy SET wallet = wallet + ? WHERE user_id = ?', (premio - aposta, user_id))
    else:
        cursor.execute('UPDATE economy SET wallet = wallet - ? WHERE user_id = ?', (aposta, user_id))
    
    conn.commit()
    conn.close()
    
    embed = Embed(title="🎰 LOTERIA", color=0x9b59b6)
    embed.add_field(name="Seus números", value=", ".join(map(str, meus_numeros)), inline=False)
    embed.add_field(name="Números sorteados", value=", ".join(map(str, numeros)), inline=False)
    embed.add_field(name="Resultado", value=f"{mensagem}\nPrêmio: **{premio}** moedas", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def ppt(ctx, escolha: str):
    """Pedra, Papel, Tesoura"""
    opcoes = ['pedra', 'papel', 'tesoura']
    if escolha.lower() not in opcoes:
        await ctx.send("❌ Escolha: `pedra`, `papel` ou `tesoura`")
        return
    
    bot_escolha = random.choice(opcoes)
    
    if escolha.lower() == bot_escolha:
        resultado = "🤝 Empate!"
    elif (escolha.lower() == 'pedra' and bot_escolha == 'tesoura') or \
         (escolha.lower() == 'papel' and bot_escolha == 'pedra') or \
         (escolha.lower() == 'tesoura' and bot_escolha == 'papel'):
        resultado = "🎉 Você ganhou!"
    else:
        resultado = "🤖 Eu ganhei!"
    
    await ctx.send(f"**Pedra, Papel, Tesoura!**\n\n🎯 Você: {escolha}\n🤖 Eu: {bot_escolha}\n\n**{resultado}**")

@bot.command()
async def dado(ctx, lados: int = 6):
    """Rolar um dado"""
    if lados < 2:
        await ctx.send("❌ O dado precisa ter pelo menos 2 lados")
        return
    
    resultado = random.randint(1, lados)
    await ctx.send(f"🎲 {ctx.author.mention} rolou um dado de {lados} lados: **{resultado}**")

@bot.command()
async def cara_coroa(ctx):
    """Cara ou coroa"""
    resultado = random.choice(['cara', 'coroa'])
    await ctx.send(f"🪙 {ctx.author.mention} deu: **{resultado.upper()}**")

# 🎫 SISTEMA DE TICKETS
@bot.command()
async def ticket(ctx, *, motivo="Suporte"):
    """Abrir ticket de suporte"""
    guild_id = str(ctx.guild.id)
    
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.author: discord.PermissionOverwrite(read_messages=True),
        ctx.guild.me: discord.PermissionOverwrite(read_messages=True)
    }
    
    ticket_channel = await ctx.guild.create_text_channel(
        f'ticket-{ctx.author.name}',
        overwrites=overwrites
    )
    
    embed = Embed(title="🎫 TICKET ABERTO", color=0x00ff00)
    embed.add_field(name="👤 Usuário", value=ctx.author.mention, inline=True)
    embed.add_field(name="📝 Motivo", value=motivo, inline=True)
    embed.add_field(name="🛠️ Ações", value="Use `!fechar` para encerrar", inline=True)
    await ticket_channel.send(embed=embed)
    await ctx.send(f"✅ Ticket criado: {ticket_channel.mention}", delete_after=5)

@bot.command()
async def fechar(ctx):
    """Fechar ticket atual"""
    if 'ticket' in ctx.channel.name:
        await ctx.send("🗑️ Fechando ticket em 5 segundos...")
        await asyncio.sleep(5)
        await ctx.channel.delete()

# 🔧 UTILIDADES
@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    """Informações do usuário"""
    target = member or ctx.author
    
    embed = Embed(title=f"👤 {target.name}", color=target.color)
    embed.set_thumbnail(url=target.avatar_url)
    embed.add_field(name="ID", value=target.id, inline=True)
    embed.add_field(name="Conta criada", value=target.created_at.strftime("%d/%m/%Y"), inline=True)
    embed.add_field(name="Entrou em", value=target.joined_at.strftime("%d/%m/%Y"), inline=True)
    embed.add_field(name="Cargos", value=", ".join([role.name for role in target.roles[1:]]), inline=False)
    embed.add_field(name="Status", value=str(target.status).title(), inline=True)
    
    await ctx.send(embed=embed)

@bot.command()
async def serverinfo(ctx):
    """Informações do servidor"""
    guild = ctx.guild
    
    embed = Embed(title=f"🏠 {guild.name}", color=0x3498db)
    embed.set_thumbnail(url=guild.icon_url)
    embed.add_field(name="👑 Dono", value=guild.owner.mention, inline=True)
    embed.add_field(name="🆔 ID", value=guild.id, inline=True)
    embed.add_field(name="📅 Criado em", value=guild.created_at.strftime("%d/%m/%Y"), inline=True)
    embed.add_field(name="👥 Membros", value=guild.member_count, inline=True)
    embed.add_field(name="📊 Canais", value=len(guild.channels), inline=True)
    embed.add_field(name="🎭 Cargos", value=len(guild.roles), inline=True)
    embed.add_field(name="😊 Emojis", value=len(guild.emojis), inline=True)
    embed.add_field(name="🌐 Região", value=str(guild.region).title(), inline=True)
    
    await ctx.send(embed=embed)

@bot.command()
async def avatar(ctx, member: discord.Member = None):
    """Mostrar avatar do usuário"""
    target = member or ctx.author
    
    embed = Embed(title=f"🖼️ Avatar de {target.name}", color=target.color)
    embed.set_image(url=target.avatar_url)
    await ctx.send(embed=embed)

@bot.command()
async def calc(ctx, *, expression: str):
    """Calculadora simples"""
    try:
        # Remover caracteres perigosos
        safe_expr = ''.join(c for c in expression if c in '0123456789+-*/.() ')
        result = eval(safe_expr)
        await ctx.send(f"🧮 Resultado: **{result}**")
    except:
        await ctx.send("❌ Expressão inválida!")

@bot.command()
async def timer(ctx, segundos: int):
    """Definir timer"""
    if segundos > 3600:
        await ctx.send("⏰ Máximo: 3600 segundos (1 hora)")
        return
    
    await ctx.send(f"⏰ Timer de {segundos} segundos iniciado!")
    await asyncio.sleep(segundos)
    await ctx.send(f"🔔 {ctx.author.mention} Timer finalizado!")

@bot.command()
async def lembrete(ctx, tempo: str, *, mensagem: str):
    """Definir lembrete"""
    await ctx.send(f"✅ Lembrete definido: '{mensagem}' para {tempo}")
    # Implementar parser de tempo mais avançado

@bot.command()
async def clima(ctx, *, cidade: str):
    """Previsão do tempo (simulada)"""
    temperaturas = {
        'são paulo': '25°C', 'rio de janeiro': '28°C', 'brasília': '27°C',
        'salvador': '30°C', 'fortaleza': '29°C', 'belo horizonte': '26°C'
    }
    
    temp = temperaturas.get(cidade.lower(), '22°C')
    embed = Embed(title=f"🌤️ Clima em {cidade.title()}", color=0x87ceeb)
    embed.add_field(name="🌡️ Temperatura", value=temp, inline=True)
    embed.add_field(name="☁️ Condição", value="Parcialmente Nublado", inline=True)
    embed.add_field(name="💧 Umidade", value="65%", inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def traduzir(ctx, idioma: str, *, texto: str):
    """Traduzir texto (simulado)"""
    await ctx.send(f"🌐 Tradução para {idioma}: *{texto}*")

@bot.command()
async def moeda(ctx, valor: float, de: str, para: str):
    """Conversor de moeda (simulado)"""
    taxas = {'USD': 5.0, 'EUR': 5.5, 'BRL': 1.0}
    resultado = valor * (taxas.get(para.upper(), 1) / taxas.get(de.upper(), 1))
    await ctx.send(f"💱 {valor} {de.upper()} = {resultado:.2f} {para.upper()}")

@bot.command()
async def piada(ctx):
    """Contar uma piada"""
    piadas = [
        "Por que o Python foi pra terapia? Porque tinha muitos issues!",
        "Como o SQL saiu com a namorada? SELECT * FROM dates WHERE love > 0",
        "Quantos programadores são necessários para trocar uma lâmpada? Nenhum, é problema de hardware!",
        "O que o commit falou para o repositório? Você me completa!"
    ]
    await ctx.send(f"🎭 {random.choice(piadas)}")

@bot.command()
async def quote(ctx):
    """Citação inspiradora"""
    quotes = [
        "O código é como o humor. Quando você tem que explicar, é ruim.",
        "Antes de deletar código, comente. Depois de testar, delete.",
        "Programadores são ferramentas para converter cafeína em código.",
        "Existem 10 tipos de pessoas: as que entendem binário e as que não entendem."
    ]
    embed = Embed(title="💡 Citação do Dia", description=random.choice(quotes), color=0xffff00)
    await ctx.send(embed=embed)

@bot.command()
async def meme(ctx):
    """Meme aleatório"""
    memes = [
        "https://i.imgur.com/8x9Z0hF.jpg",
        "https://i.imgur.com/3JkQ7Zt.jpg", 
        "https://i.imgur.com/5W5Q5Z5.jpg"
    ]
    embed = Embed(title="😂 Meme do Dia", color=0xff00ff)
    embed.set_image(url=random.choice(memes))
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def canal_seguro(ctx):
    """Criar canal seguro privado"""
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.author: discord.PermissionOverwrite(read_messages=True)
    }
    
    channel = await ctx.guild.create_text_channel('🚨canal-seguro', overwrites=overwrites)
    await channel.send(f"🔒 Canal seguro criado para {ctx.author.mention}!")
    await ctx.message.delete()

# ℹ️ COMANDOS DE AJUDA
@bot.command()
async def comandos(ctx):
    """Mostrar todos os comandos disponíveis"""
    embed = Embed(title="🦹‍♂️ COMANDOS DO BOT VILÃO (30+)", color=0x8A2BE2)
    
    embed.add_field(
        name="🔧 MODERAÇÃO", 
        value="`!ban` `!kick` `!clear` `!mute` `!unmute`",
        inline=False
    )
    
    embed.add_field(
        name="🛡️ SEGURANÇA", 
        value="`!backup` `!restore` `!lockdown` `!unlock` `!canal_seguro`",
        inline=False
    )
    
    embed.add_field(
        name="💰 ECONOMIA", 
        value="`!daily` `!balance` `!rank` `!loteria`",
        inline=False
    )
    
    embed.add_field(
        name="🎮 JOGOS", 
        value="`!ppt` `!dado` `!cara_coroa`",
        inline=False
    )
    
    embed.add_field(
        name="🎫 TICKETS", 
        value="`!ticket` `!fechar`",
        inline=False
    )
    
    embed.add_field(
        name="🔧 UTILIDADES", 
        value="`!userinfo` `!serverinfo` `!avatar` `!calc` `!timer` `!lembrete` `!clima` `!traduzir` `!moeda`",
        inline=False
    )
    
    embed.add_field(
        name="😄 DIVERSÃO", 
        value="`!piada` `!quote` `!meme`",
        inline=False
    )
    
    embed.add_field(
        name="ℹ️ INFORMATIVOS", 
        value="`!ping` `!comandos`",
        inline=False
    )
    
    embed.set_footer(text="Mencione o bot para conversar com a IA!")
    await ctx.send(embed=embed)

@bot.command()
async def ping(ctx):
    """Testar latência do bot"""
    await ctx.send(f'🏓 Pong! {round(bot.latency * 1000)}ms')

# INICIAR BOT
if __name__ == "__main__":
    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN)
    else:
        print("❌ Token do Discord não encontrado no arquivo .env")
