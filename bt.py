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
import urllib.parse
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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS server_config (
            guild_id TEXT PRIMARY KEY,
            welcome_channel TEXT,
            mod_log_channel TEXT,
            auto_mod BOOLEAN DEFAULT 0
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

def deepseek_chat(messages, user_id):
    """Sistema de IA melhorado com fallback"""
    if not DEEPSEEK_API_KEY:
        return get_fallback_response(messages[-1]["content"])
    
    headers = {
        'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'model': 'deepseek-chat',
        'messages': messages,
        'stream': False,
        'temperature': 0.8,
        'max_tokens': 80
    }
    
    try:
        response = requests.post(
            'https://api.deepseek.com/v1/chat/completions', 
            json=payload, 
            headers=headers, 
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content'].strip()
        
        return get_fallback_response(messages[-1]["content"])
        
    except Exception as e:
        print(f"Erro DeepSeek: {e}")
        return get_fallback_response(messages[-1]["content"])

def get_fallback_response(user_message):
    """Respostas inteligentes quando a API falha"""
    user_message = user_message.lower()
    
    responses = {
        'oi': ['Eae!', 'Oi!', 'Fala!', 'Opa!'],
        'ola': ['Eae!', 'Oi!', 'Fala!', 'Opa!'],
        'tudo bem': ['Tudo sim!', 'De boa!', 'Tranquilo!', 'Suave!'],
        'como vai': ['De boa!', 'Tranquilo!', 'Suave!', 'Tudo certo!'],
        'obrigado': ['Por nada!', 'Disponha!', 'Tmj!', 'De boa!'],
        'valeu': ['Por nada!', 'Disponha!', 'Tmj!', 'De boa!'],
        'beleza': ['Beleza!', 'Show!', 'Tranquilo!', 'Top!'],
        'sim': ['Top!', 'Show!', 'Legal!', 'Daora!'],
        'nao': ['Poxa :(', 'Que pena', 'Entendi', 'Tudo bem'],
        'que': ['Não sei te dizer', 'Boa pergunta', 'Hmm...', 'Interessante'],
        'quem': ['Não conheço', 'Sei não', 'Hmm...', 'Boa pergunta']
    }
    
    for key, answers in responses.items():
        if key in user_message:
            return random.choice(answers)
    
    return random.choice(['Sim!', 'Entendi!', 'Legal!', 'Top!', 'Show!', 'Daora!'])

@bot.event
async def on_ready():
    print(f'🤖 AMIGÃO ATIVADO: {bot.user.name}')
    await bot.change_presence(activity=Game(name="!comandos | 30+ Recursos"))

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # SISTEMA DE IA MELHORADO
    if bot.user.mentioned_in(message) and not message.content.startswith('!'):
        user_id = str(message.author.id)
        
        if user_id not in conversation_history:
            conversation_history[user_id] = []
        
        # Limitar histórico
        user_history = conversation_history[user_id][-4:]
        
        messages = [
            {
                "role": "system", 
                "content": "Você é o Amigão, um usuário normal do Discord. Responda de forma CURTA, NATURAL e HUMANA. Use gírias brasileiras como 'mano', 'valeu', 'tmj'. Não use emojis demais. Seja direto."
            }
        ]
        
        for msg in user_history:
            role = "user" if msg['author'] == 'user' else "assistant"
            messages.append({"role": role, "content": msg['content']})
        
        # Corrigir a menção
        cleaned_content = message.content.replace(f'<@{bot.user.id}>', '').strip()
        messages.append({"role": "user", "content": cleaned_content})
        
        response = deepseek_chat(messages, user_id)
        
        # Salvar no histórico
        conversation_history[user_id].append({"author": "user", "content": cleaned_content})
        conversation_history[user_id].append({"author": "bot", "content": response})
        
        if len(conversation_history[user_id]) > 20:
            conversation_history[user_id] = conversation_history[user_id][-20:]
        
        await message.channel.send(response)
    
    await bot.process_commands(message)

# ========== 30+ COMANDOS PROFISSIONAIS ==========

# 🔧 MODERAÇÃO AVANÇADA
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Sem motivo"):
    """🔨 Banir usuário do servidor"""
    await member.ban(reason=reason)
    embed = Embed(title="🔨 USUÁRIO BANIDO", color=0xff0000)
    embed.add_field(name="Usuário", value=member.mention, inline=True)
    embed.add_field(name="Motivo", value=reason, inline=True)
    embed.add_field(name="Moderador", value=ctx.author.mention, inline=True)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="Sem motivo"):
    """👢 Expulsar usuário do servidor"""
    await member.kick(reason=reason)
    embed = Embed(title="👢 USUÁRIO EXPULSO", color=0xff9900)
    embed.add_field(name="Usuário", value=member.mention, inline=True)
    embed.add_field(name="Motivo", value=reason, inline=True)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 10):
    """🗑️ Limpar mensagens do canal"""
    if amount > 100:
        amount = 100
    deleted = await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"🗑️ {len(deleted) - 1} mensagens limpas!")
    await asyncio.sleep(3)
    await msg.delete()

@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member, *, reason="Sem motivo"):
    """🔇 Silenciar usuário"""
    muted_role = discord.utils.get(ctx.guild.roles, name="Silenciado")
    if not muted_role:
        muted_role = await ctx.guild.create_role(name="Silenciado")
        for channel in ctx.guild.channels:
            await channel.set_permissions(muted_role, send_messages=False)
    
    await member.add_roles(muted_role, reason=reason)
    await ctx.send(f"🔇 {member.mention} foi silenciado. Motivo: {reason}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):
    """🔊 Remover silenciamento"""
    muted_role = discord.utils.get(ctx.guild.roles, name="Silenciado")
    if muted_role and muted_role in member.roles:
        await member.remove_roles(muted_role)
        await ctx.send(f"🔊 {member.mention} foi dessilenciado")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def cargo(ctx, member: discord.Member, role: discord.Role):
    """🎭 Adicionar cargo a usuário"""
    await member.add_roles(role)
    await ctx.send(f"🎭 Cargo {role.name} adicionado para {member.mention}")

# 🛡️ SEGURANÇA E BACKUP
@bot.command()
@commands.has_permissions(administrator=True)
async def backup(ctx):
    """💾 Fazer backup completo do servidor"""
    guild = ctx.guild
    
    backup_data = {
        'server_name': guild.name,
        'backup_date': datetime.datetime.now().isoformat(),
        'roles': [],
        'channels': [],
        'settings': {
            'verification_level': guild.verification_level.value,
            'default_notifications': guild.default_notifications.value
        }
    }
    
    # Backup de cargos
    for role in guild.roles:
        if role.name != "@everyone":
            backup_data['roles'].append({
                'name': role.name,
                'color': role.color.value,
                'permissions': role.permissions.value,
                'position': role.position
            })
    
    # Backup de canais
    for channel in guild.channels:
        channel_info = {
            'name': channel.name,
            'type': str(channel.type),
            'position': channel.position
        }
        
        if isinstance(channel, discord.TextChannel):
            channel_info['topic'] = channel.topic
            channel_info['nsfw'] = channel.nsfw
            channel_info['slowmode_delay'] = channel.slowmode_delay
        
        backup_data['channels'].append(channel_info)
    
    filename = f"backup_{guild.id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)
    
    await ctx.send(f"✅ Backup completo salvo como `{filename}`")

@bot.command()
@commands.has_permissions(administrator=True)
async def canalseguro(ctx):
    """🔒 Criar canal seguro privado"""
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.author: discord.PermissionOverwrite(read_messages=True),
        ctx.guild.me: discord.PermissionOverwrite(read_messages=True)
    }
    
    channel = await ctx.guild.create_text_channel('🔒canal-seguro', overwrites=overwrites)
    await channel.send(f"🔒 Canal seguro criado para {ctx.author.mention}!")
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def lockdown(ctx):
    """🚫 Bloquear todo o servidor"""
    for channel in ctx.guild.channels:
        try:
            await channel.set_permissions(ctx.guild.default_role, send_messages=False)
        except:
            pass
    
    embed = Embed(title="🚫 LOCKDOWN ATIVADO", color=0xff0000)
    embed.description = "Todos os canais foram bloqueados para membros comuns."
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def unlock(ctx):
    """🔓 Desbloquear servidor"""
    for channel in ctx.guild.channels:
        try:
            await channel.set_permissions(ctx.guild.default_role, send_messages=True)
        except:
            pass
    
    embed = Embed(title="🔓 SERVIDOR DESBLOQUEADO", color=0x00ff00)
    embed.description = "Todos os canais foram desbloqueados."
    await ctx.send(embed=embed)

# 💰 SISTEMA ECONÔMICO
@bot.command()
async def daily(ctx):
    """🎁 Resgatar recompensa diária"""
    user_id = str(ctx.author.id)
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT wallet, last_daily FROM economy WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    
    now = datetime.datetime.now().isoformat()
    
    if not result:
        # Primeira vez
        coins = random.randint(150, 300)
        cursor.execute('INSERT INTO economy (user_id, wallet, last_daily) VALUES (?, ?, ?)', 
                      (user_id, coins, now))
        message = f"🎁 **Recompensa diária coletada!**\nVocê ganhou **{coins}** moedas!"
    else:
        wallet, last_daily = result
        if last_daily:
            last_date = datetime.datetime.fromisoformat(last_daily)
            if (datetime.datetime.now() - last_date).days >= 1:
                coins = random.randint(150, 300)
                cursor.execute('UPDATE economy SET wallet = wallet + ?, last_daily = ? WHERE user_id = ?',
                              (coins, now, user_id))
                message = f"🎁 **Recompensa diária coletada!**\nVocê ganhou **{coins}** moedas!"
            else:
                message = "⏰ **Você já coletou sua recompensa hoje!**\nVolte amanhã para mais moedas."
        else:
            coins = random.randint(150, 300)
            cursor.execute('UPDATE economy SET wallet = wallet + ?, last_daily = ? WHERE user_id = ?',
                          (coins, now, user_id))
            message = f"🎁 **Recompensa diária coletada!**\nVocê ganhou **{coins}** moedas!"
    
    conn.commit()
    conn.close()
    
    embed = Embed(title="💰 RECOMPENSA DIÁRIA", description=message, color=0xffd700)
    await ctx.send(embed=embed)

@bot.command()
async def saldo(ctx, member: discord.Member = None):
    """💰 Ver saldo de moedas"""
    target = member or ctx.author
    user_id = str(target.id)
    
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT wallet, bank FROM economy WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    wallet = result[0] if result else 0
    bank = result[1] if result else 0
    total = wallet + bank
    
    embed = Embed(title=f"💰 CARTEIRA DE {target.name.upper()}", color=0xffd700)
    embed.set_thumbnail(url=target.avatar_url)
    embed.add_field(name="💳 Carteira", value=f"**{wallet}** moedas", inline=True)
    embed.add_field(name="🏦 Banco", value=f"**{bank}** moedas", inline=True)
    embed.add_field(name="💎 Total", value=f"**{total}** moedas", inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def transferir(ctx, member: discord.Member, quantia: int):
    """💸 Transferir moedas para outro usuário"""
    if quantia <= 0:
        await ctx.send("❌ Quantia deve ser maior que 0")
        return
    
    if member == ctx.author:
        await ctx.send("❌ Você não pode transferir para si mesmo")
        return
    
    user_id = str(ctx.author.id)
    target_id = str(member.id)
    
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    # Verificar saldo
    cursor.execute('SELECT wallet FROM economy WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    
    if not result or result[0] < quantia:
        await ctx.send("❌ Saldo insuficiente!")
        conn.close()
        return
    
    # Transferir
    cursor.execute('UPDATE economy SET wallet = wallet - ? WHERE user_id = ?', (quantia, user_id))
    
    # Adicionar ao destinatário
    cursor.execute('SELECT wallet FROM economy WHERE user_id = ?', (target_id,))
    target_result = cursor.fetchone()
    
    if target_result:
        cursor.execute('UPDATE economy SET wallet = wallet + ? WHERE user_id = ?', (quantia, target_id))
    else:
        cursor.execute('INSERT INTO economy (user_id, wallet) VALUES (?, ?)', (target_id, quantia))
    
    conn.commit()
    conn.close()
    
    embed = Embed(title="💸 TRANSFERÊNCIA REALIZADA", color=0x00ff00)
    embed.description = f"**{quantia}** moedas transferidas para {member.mention}"
    await ctx.send(embed=embed)

# 🎮 SISTEMA DE JOGOS
@bot.command()
async def loteria(ctx, aposta: int = 100):
    """🎰 Jogar na loteria"""
    if aposta < 50:
        await ctx.send("❌ Aposta mínima: 50 moedas")
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
    numeros_sorteados = [random.randint(1, 60) for _ in range(6)]
    meus_numeros = [random.randint(1, 60) for _ in range(6)]
    
    acertos = len(set(numeros_sorteados) & set(meus_numeros))
    
    if acertos == 6:
        premio = aposta * 100
        mensagem = "🎉 **JACKPOT!** Você acertou todos os 6 números!"
    elif acertos == 5:
        premio = aposta * 20
        mensagem = "🔥 **Excelente!** 5 números corretos!"
    elif acertos == 4:
        premio = aposta * 5
        mensagem = "👍 **Boa!** 4 números corretos!"
    elif acertos == 3:
        premio = aposta
        mensagem = "😊 **Na média!** 3 números corretos!"
    else:
        premio = 0
        mensagem = "😢 **Que pena!** Tente novamente."
    
    # Atualizar saldo
    if premio > 0:
        cursor.execute('UPDATE economy SET wallet = wallet + ? WHERE user_id = ?', (premio - aposta, user_id))
    else:
        cursor.execute('UPDATE economy SET wallet = wallet - ? WHERE user_id = ?', (aposta, user_id))
    
    conn.commit()
    conn.close()
    
    embed = Embed(title="🎰 LOTERIA", color=0x9b59b6)
    embed.add_field(name="Seus números", value=", ".join(map(str, sorted(meus_numeros))), inline=False)
    embed.add_field(name="Números sorteados", value=", ".join(map(str, sorted(numeros_sorteados))), inline=False)
    embed.add_field(name="Resultado", value=f"{mensagem}\n**Prêmio: {premio} moedas**", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def ppt(ctx, escolha: str):
    """✂️ Pedra, Papel, Tesoura"""
    opcoes = ['pedra', 'papel', 'tesoura']
    escolha = escolha.lower()
    
    if escolha not in opcoes:
        await ctx.send("❌ Escolha: `pedra`, `papel` ou `tesoura`")
        return
    
    bot_escolha = random.choice(opcoes)
    
    if escolha == bot_escolha:
        resultado = "🤝 **Empate!**"
        cor = 0xffff00
    elif (escolha == 'pedra' and bot_escolha == 'tesoura') or \
         (escolha == 'papel' and bot_escolha == 'pedra') or \
         (escolha == 'tesoura' and bot_escolha == 'papel'):
        resultado = "🎉 **Você ganhou!**"
        cor = 0x00ff00
    else:
        resultado = "🤖 **Eu ganhei!**"
        cor = 0xff0000
    
    embed = Embed(title="✂️ PEDRA, PAPEL, TESOURA", color=cor)
    embed.add_field(name="Sua escolha", value=escolha.title(), inline=True)
    embed.add_field(name="Minha escolha", value=bot_escolha.title(), inline=True)
    embed.add_field(name="Resultado", value=resultado, inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def dado(ctx, lados: int = 6):
    """🎲 Rolar um dado"""
    if lados < 2:
        await ctx.send("❌ O dado precisa ter pelo menos 2 lados")
        return
    
    resultado = random.randint(1, lados)
    embed = Embed(title="🎲 RESULTADO DO DADO", color=0x3498db)
    embed.description = f"{ctx.author.mention} rolou um dado de **{lados}** lados: **{resultado}**"
    await ctx.send(embed=embed)

@bot.command()
async def caracoroa(ctx):
    """🪙 Cara ou coroa"""
    resultado = random.choice(['cara', 'coroa'])
    embed = Embed(title="🪙 CARA OU COROA", color=0xffd700)
    embed.description = f"{ctx.author.mention} deu: **{resultado.upper()}**"
    await ctx.send(embed=embed)

# 🎫 SISTEMA DE TICKETS
@bot.command()
async def ticket(ctx, *, motivo="Suporte"):
    """🎫 Abrir ticket de suporte"""
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.author: discord.PermissionOverwrite(read_messages=True),
        ctx.guild.me: discord.PermissionOverwrite(read_messages=True)
    }
    
    # Encontrar categoria de tickets ou criar
    category = discord.utils.get(ctx.guild.categories, name="Tickets")
    if not category:
        category = await ctx.guild.create_category("Tickets")
    
    ticket_channel = await ctx.guild.create_text_channel(
        f'ticket-{ctx.author.name}',
        category=category,
        overwrites=overwrites
    )
    
    embed = Embed(title="🎫 TICKET ABERTO", color=0x00ff00)
    embed.add_field(name="👤 Usuário", value=ctx.author.mention, inline=True)
    embed.add_field(name="📝 Motivo", value=motivo, inline=True)
    embed.add_field(name="🛠️ Ações", value="Use `!fecharticket` para encerrar", inline=False)
    await ticket_channel.send(embed=embed)
    await ctx.send(f"✅ Ticket criado: {ticket_channel.mention}", delete_after=10)

@bot.command()
async def fecharticket(ctx):
    """🔒 Fechar ticket atual"""
    if 'ticket' in ctx.channel.name:
        await ctx.send("🗑️ Fechando ticket em 5 segundos...")
        await asyncio.sleep(5)
        await ctx.channel.delete()

# 🔧 UTILIDADES
@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    """👤 Informações do usuário"""
    target = member or ctx.author
    
    embed = Embed(title=f"👤 {target.name}", color=target.color)
    embed.set_thumbnail(url=target.avatar_url)
    embed.add_field(name="🆔 ID", value=target.id, inline=True)
    embed.add_field(name="📅 Conta criada", value=target.created_at.strftime("%d/%m/%Y"), inline=True)
    embed.add_field(name="📥 Entrou em", value=target.joined_at.strftime("%d/%m/%Y"), inline=True)
    
    roles = [role.mention for role in target.roles[1:]]
    embed.add_field(name="🎭 Cargos", value=" ".join(roles) if roles else "Nenhum", inline=False)
    
    embed.add_field(name="📊 Status", value=str(target.status).title(), inline=True)
    embed.add_field(name="🤖 Bot", value="Sim" if target.bot else "Não", inline=True)
    
    await ctx.send(embed=embed)

@bot.command()
async def serverinfo(ctx):
    """🏠 Informações do servidor"""
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
    embed.add_field(name="✨ Boost Level", value=guild.premium_tier, inline=True)
    embed.add_field(name="🚀 Boosts", value=guild.premium_subscription_count, inline=True)
    
    await ctx.send(embed=embed)

@bot.command()
async def avatar(ctx, member: discord.Member = None):
    """🖼️ Mostrar avatar do usuário"""
    target = member or ctx.author
    
    embed = Embed(title=f"🖼️ Avatar de {target.name}", color=target.color)
    embed.set_image(url=target.avatar_url)
    await ctx.send(embed=embed)

@bot.command()
async def calc(ctx, *, expressao: str):
    """🧮 Calculadora simples"""
    try:
        # Remover caracteres perigosos
        caracteres_seguros = set('0123456789+-*/.() ')
        expressao_segura = ''.join(c for c in expressao if c in caracteres_seguros)
        
        if not expressao_segura:
            await ctx.send("❌ Expressão vazia ou inválida")
            return
        
        resultado = eval(expressao_segura)
        embed = Embed(title="🧮 CALCULADORA", color=0x3498db)
        embed.add_field(name="Expressão", value=expressao_segura, inline=False)
        embed.add_field(name="Resultado", value=f"**{resultado}**", inline=False)
        await ctx.send(embed=embed)
        
    except:
        await ctx.send("❌ Expressão inválida!")

@bot.command()
async def timer(ctx, segundos: int):
    """⏰ Definir timer"""
    if segundos > 3600:
        await ctx.send("❌ Máximo: 3600 segundos (1 hora)")
        return
    if segundos < 5:
        await ctx.send("❌ Mínimo: 5 segundos")
        return
    
    await ctx.send(f"⏰ Timer de {segundos} segundos iniciado para {ctx.author.mention}!")
    await asyncio.sleep(segundos)
    await ctx.send(f"🔔 {ctx.author.mention} Timer de {segundos} segundos finalizado!")

@bot.command()
async def clima(ctx, *, cidade: str):
    """🌤️ Previsão do tempo (simulada)"""
    # Simulação de dados de clima
    temperaturas = {
        'são paulo': {'temp': '25°C', 'cond': 'Parcialmente nublado'},
        'rio de janeiro': {'temp': '28°C', 'cond': 'Ensolarado'},
        'brasília': {'temp': '27°C', 'cond': 'Parcialmente nublado'},
        'salvador': {'temp': '30°C', 'cond': 'Ensolarado'},
        'fortaleza': {'temp': '29°C', 'cond': 'Ensolarado'},
        'belo horizonte': {'temp': '26°C', 'cond': 'Parcialmente nublado'}
    }
    
    cidade_lower = cidade.lower()
    dados = temperaturas.get(cidade_lower, {'temp': '23°C', 'cond': 'Parcialmente nublado'})
    
    embed = Embed(title=f"🌤️ Clima em {cidade.title()}", color=0x87ceeb)
    embed.add_field(name="🌡️ Temperatura", value=dados['temp'], inline=True)
    embed.add_field(name="☁️ Condição", value=dados['cond'], inline=True)
    embed.add_field(name="💧 Umidade", value="65%", inline=True)
    embed.add_field(name="💨 Vento", value="15 km/h", inline=True)
    embed.add_field(name="🌅 Pressão", value="1015 hPa", inline=True)
    
    await ctx.send(embed=embed)

@bot.command()
async def traduzir(ctx, idioma: str, *, texto: str):
    """🌐 Tradutor (simulado)"""
    embed = Embed(title="🌐 TRADUTOR", color=0x3498db)
    embed.add_field(name=f"Texto original", value=texto, inline=False)
    embed.add_field(name=f"Tradução para {idioma.upper()}", value=f"*{texto}*", inline=False)
    embed.set_footer(text="Funcionalidade simulada - use serviços online para traduções reais")
    await ctx.send(embed=embed)

@bot.command()
async def moeda(ctx, valor: float, de: str, para: str):
    """💱 Conversor de moeda (simulado)"""
    taxas = {
        'USD': 5.2,  # Dólar
        'EUR': 5.6,  # Euro
        'GBP': 6.1,  # Libra
        'JPY': 0.035, # Iene
        'BRL': 1.0   # Real
    }
    
    de = de.upper()
    para = para.upper()
    
    if de not in taxas or para not in taxas:
        await ctx.send("❌ Moeda não suportada. Use: USD, EUR, GBP, JPY, BRL")
        return
    
    resultado = valor * (taxas[para] / taxas[de])
    
    embed = Embed(title="💱 CONVERSOR DE MOEDA", color=0xffd700)
    embed.add_field(name="Valor", value=f"{valor:.2f} {de}", inline=True)
    embed.add_field(name="Convertido", value=f"{resultado:.2f} {para}", inline=True)
    embed.add_field(name="Taxa", value=f"1 {de} = {taxas[para]/taxas[de]:.4f} {para}", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def piada(ctx):
    """🎭 Contar uma piada"""
    piadas = [
        "Por que o Python foi pra terapia? Porque tinha muitos issues!",
        "Como o SQL saiu com a namorada? SELECT * FROM dates WHERE love > 0",
        "Quantos programadores são necessários para trocar uma lâmpada? Nenhum, é problema de hardware!",
        "O que o commit falou para o repositório? Você me completa!",
        "Por que o JavaScript foi parar no hospital? Porque ele tinha um callback hell!",
        "Qual é o café favorito do desenvolvedor? Java!"
    ]
    
    embed = Embed(title="🎭 PIADA DO DIA", description=random.choice(piadas), color=0xff69b4)
    await ctx.send(embed=embed)

@bot.command()
async def citacao(ctx):
    """💡 Citação inspiradora"""
    citacoes = [
        "O código é como o humor. Quando você tem que explicar, é ruim.",
        "Antes de deletar código, comente. Depois de testar, delete.",
        "Programadores são ferramentas para converter cafeína em código.",
        "Existem 10 tipos de pessoas: as que entendem binário e as que não entendem.",
        "Debugging é como ser detetive em um filme de crime onde você também é o assassino.",
        "O melhor momento para plantar uma árvore foi há 20 anos. O segundo melhor é agora."
    ]
    
    embed = Embed(title="💡 CITAÇÃO INSPIRADORA", description=random.choice(citacoes), color=0xffff00)
    await ctx.send(embed=embed)

@bot.command()
async def meme(ctx):
    """😂 Meme aleatório"""
    memes = [
        "https://i.imgur.com/8x9Z0hF.jpg",
        "https://i.imgur.com/3JkQ7Zt.jpg", 
        "https://i.imgur.com/5W5Q5Z5.jpg",
        "https://i.imgur.com/7X8Y9Z0.jpg"
    ]
    
    embed = Embed(title="😂 MEME DO DIA", color=0xff00ff)
    embed.set_image(url=random.choice(memes))
    await ctx.send(embed=embed)

# ℹ️ COMANDOS DE AJUDA
@bot.command()
async def comandos(ctx):
    """📚 Mostrar todos os comandos disponíveis"""
    embed = Embed(title="🤖 AMIGÃO - TODOS OS COMANDOS", color=0x8A2BE2)
    
    embed.add_field(
        name="🔧 MODERAÇÃO (6 comandos)", 
        value="`!ban` `!kick` `!clear` `!mute` `!unmute` `!cargo`",
        inline=False
    )
    
    embed.add_field(
        name="🛡️ SEGURANÇA (5 comandos)", 
        value="`!backup` `!canalseguro` `!lockdown` `!unlock` `!fecharticket`",
        inline=False
    )
    
    embed.add_field(
        name="💰 ECONOMIA (4 comandos)", 
        value="`!daily` `!saldo` `!transferir` `!loteria`",
        inline=False
    )
    
    embed.add_field(
        name="🎮 JOGOS (4 comandos)", 
        value="`!ppt` `!dado` `!caracoroa` `!ticket`",
        inline=False
    )
    
    embed.add_field(
        name="🔧 UTILIDADES (9 comandos)", 
        value="`!userinfo` `!serverinfo` `!avatar` `!calc` `!timer` `!clima` `!traduzir` `!moeda` `!ping`",
        inline=False
    )
    
    embed.add_field(
        name="😄 DIVERSÃO (3 comandos)", 
        value="`!piada` `!citacao` `!meme`",
        inline=False
    )
    
    embed.add_field(
        name="🤖 IA CONVERSACIONAL", 
        value="Apenas **mencione o bot** para conversar naturalmente",
        inline=False
    )
    
    embed.set_footer(text="Total: 31 comandos profissionais • Desenvolvido com ❤️")
    await ctx.send(embed=embed)

@bot.command()
async def ping(ctx):
    """🏓 Testar latência do bot"""
    latency = round(bot.latency * 1000)
    
    if latency < 100:
        cor = 0x00ff00
        status = "Ótimo"
    elif latency < 200:
        cor = 0xffff00
        status = "Bom"
    else:
        cor = 0xff0000
        status = "Lento"
    
    embed = Embed(title="🏓 PONG!", color=cor)
    embed.add_field(name="Latência", value=f"{latency}ms", inline=True)
    embed.add_field(name="Status", value=status, inline=True)
    await ctx.send(embed=embed)

# INICIAR BOT
if __name__ == "__main__":
    if DISCORD_TOKEN:
        print("🚀 Iniciando Amigão Bot...")
        bot.run(DISCORD_TOKEN)
    else:
        print("❌ Token do Discord não encontrado no arquivo .env")
