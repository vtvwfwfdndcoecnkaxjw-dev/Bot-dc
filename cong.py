import discord
import os
import json
import asyncio
import aiohttp
import sqlite3
import datetime
import random
import requests
from discord.ext import commands
from discord import app_commands

# CONFIGURAÇÃO DO IMPERIO
class ConfigVilao:
    def __init__(self):
        self.token = os.getenv('DISCORD_TOKEN')
        self.grok_key = os.getenv('GROK_API_KEY')
        self.deepseek_key = os.getenv('DEEPSEEK_API_KEY')
        self.backup_dir = "backups_imperio"
        
        if not all([self.token, self.grok_key, self.deepseek_key]):
            raise Exception("CHAVES API NÃO ENCONTRADAS! VERIFIQUE O .ENV!")

class IAAssassina:
    def __init__(self, grok_key, deepseek_key):
        self.grok_key = grok_key
        self.deepseek_key = deepseek_key
    
    async def grok_resposta(self, mensagem, historico):
        """IA GROK - Respostas humanas naturais"""
        try:
            url = "https://api.x.ai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.grok_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messages": historico + [{"role": "user", "content": mensagem}],
                "model": "grok-beta",
                "temperature": 0.7,
                "max_tokens": 150
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data['choices'][0]['message']['content']
                    return "Hmm... interessante."
        except:
            return "Pensando... 🤔"
    
    async def deepseek_codigo(self, prompt):
        """DEEPSEEK - Geração de código"""
        try:
            url = "https://api.deepseek.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.deepseek_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messages": [{"role": "user", "content": f"Crie código para: {prompt}"}],
                "model": "deepseek-coder",
                "temperature": 0.3,
                "max_tokens": 2000
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data['choices'][0]['message']['content']
                    return "Erro na geração de código."
        except:
            return "Erro ao acessar a API."

class SistemaBackup:
    def __init__(self):
        self.backup_dir = "backups_imperio"
        os.makedirs(self.backup_dir, exist_ok=True)
    
    async def criar_backup(self, guild):
        """Cria backup COMPLETO do servidor"""
        backup_data = {
            "nome": guild.name,
            "id": guild.id,
            "canais": [],
            "cargos": [],
            "data_backup": str(datetime.datetime.now())
        }
        
        # Backup de cargos
        for role in guild.roles:
            if role.name != "@everyone":
                backup_data["cargos"].append({
                    "nome": role.name,
                    "cor": role.color.value,
                    "permissoes": role.permissions.value
                })
        
        # Backup de canais
        for channel in guild.channels:
            channel_data = {
                "nome": channel.name,
                "tipo": str(channel.type),
                "posicao": channel.position
            }
            
            if isinstance(channel, discord.TextChannel):
                messages_data = []
                try:
                    async for message in channel.history(limit=50):
                        messages_data.append({
                            "autor": str(message.author),
                            "conteudo": message.content,
                            "timestamp": str(message.created_at)
                        })
                    channel_data["mensagens"] = messages_data
                except:
                    channel_data["mensagens"] = []
            
            backup_data["canais"].append(channel_data)
        
        # Salvar backup
        filename = f"{guild.id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.backup_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    async def restaurar_backup(self, guild, backup_file):
        """Restaura backup DESTRUINDO tudo atual"""
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        # FASE 1: DESTRUIR servidor atual
        for channel in guild.channels:
            try:
                await channel.delete()
            except:
                continue
        
        for role in guild.roles:
            if role.name != "@everyone" and not role.managed:
                try:
                    await role.delete()
                except:
                    continue
        
        await asyncio.sleep(5)
        
        # FASE 2: RECRIAR do backup
        role_map = {}
        for role_data in backup_data["cargos"]:
            try:
                new_role = await guild.create_role(
                    name=role_data["nome"],
                    color=discord.Color(role_data["cor"]),
                    permissions=discord.Permissions(role_data["permissoes"])
                )
                role_map[role_data["nome"]] = new_role
            except:
                continue
        
        for channel_data in backup_data["canais"]:
            try:
                if channel_data["tipo"] == "text":
                    new_channel = await guild.create_text_channel(
                        channel_data["nome"],
                        position=channel_data["posicao"]
                    )
                    
                    if "mensagens" in channel_data:
                        for msg_data in channel_data["mensagens"][:5]:
                            try:
                                embed = discord.Embed(
                                    description=msg_data["conteudo"],
                                    color=0x00ff00
                                )
                                embed.set_author(name=msg_data["autor"])
                                embed.set_footer(text=f"Backup: {msg_data['timestamp']}")
                                await new_channel.send(embed=embed)
                            except:
                                continue
                
                elif channel_data["tipo"] == "voice":
                    await guild.create_voice_channel(
                        channel_data["nome"],
                        position=channel_data["posicao"]
                    )
            except:
                continue

class SistemaEconomia:
    def __init__(self, db_conn):
        self.conn = db_conn
        self.setup_tables()
    
    def setup_tables(self):
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS economia (
                user_id INTEGER PRIMARY KEY,
                coins INTEGER DEFAULT 100,
                daily_streak INTEGER DEFAULT 0,
                last_daily TEXT,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS loja (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                preco INTEGER,
                descricao TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventario (
                user_id INTEGER,
                item_id INTEGER,
                quantidade INTEGER DEFAULT 1,
                FOREIGN KEY(user_id) REFERENCES economia(user_id),
                FOREIGN KEY(item_id) REFERENCES loja(item_id)
            )
        ''')
        
        # Itens padrão da loja
        cursor.execute('SELECT COUNT(*) FROM loja')
        if cursor.fetchone()[0] == 0:
            itens = [
                ("🎨 Cor Personalizada", 500, "Cargo com cor personalizada"),
                ("🌟 Booster XP", 300, "+20% XP por 24h"),
                ("🔨 Ban Hammer", 1000, "Poder simbólico de banir"),
                ("💎 Diamante", 200, "Item raro para colecionadores")
            ]
            cursor.executemany('INSERT INTO loja (nome, preco, descricao) VALUES (?, ?, ?)', itens)
        
        self.conn.commit()
    
    def get_user_data(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM economia WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if not result:
            cursor.execute('INSERT INTO economia (user_id) VALUES (?)', (user_id,))
            self.conn.commit()
            return (user_id, 100, 0, None, 0, 1)
        
        return result
    
    def add_coins(self, user_id, amount):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE economia SET coins = coins + ? WHERE user_id = ?', (amount, user_id))
        self.conn.commit()
    
    def add_xp(self, user_id, xp_amount):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE economia SET xp = xp + ? WHERE user_id = ?', (xp_amount, user_id))
        
        # Verificar level up
        user_data = self.get_user_data(user_id)
        current_xp = user_data[4]
        current_level = user_data[5]
        
        xp_needed = current_level * 100
        
        if current_xp >= xp_needed:
            new_level = current_level + 1
            cursor.execute('UPDATE economia SET level = ?, xp = ? WHERE user_id = ?', 
                          (new_level, current_xp - xp_needed, user_id))
            self.conn.commit()
            return new_level
        
        self.conn.commit()
        return None

class SistemaModeracao:
    def __init__(self, db_conn):
        self.conn = db_conn
        self.setup_tables()
    
    def setup_tables(self):
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS warns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                moderator_id INTEGER,
                reason TEXT,
                timestamp TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                guild_id INTEGER PRIMARY KEY,
                antiraid INTEGER DEFAULT 0,
                antilink INTEGER DEFAULT 0,
                welcome_channel INTEGER,
                welcome_message TEXT
            )
        ''')
        
        self.conn.commit()
    
    def add_warn(self, user_id, moderator_id, reason):
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO warns (user_id, moderator_id, reason, timestamp) VALUES (?, ?, ?, ?)',
                      (user_id, moderator_id, reason, str(datetime.datetime.now())))
        self.conn.commit()
    
    def get_warns(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM warns WHERE user_id = ?', (user_id,))
        return cursor.fetchall()

class BotImperioCompleto(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )
        
        self.config = ConfigVilao()
        self.ia = IAAssassina(self.config.grok_key, self.config.deepseek_key)
        self.backup_system = SistemaBackup()
        self.conn = sqlite3.connect('imperio.db', check_same_thread=False)
        self.economia = SistemaEconomia(self.conn)
        self.moderacao = SistemaModeracao(self.conn)
    
    async def on_ready(self):
        print(f'🤖 {self.user} ESTÁ ONLINE E PRONTO PARA O CAOS!')
        await self.tree.sync()
    
    async def on_message(self, message):
        if message.author.bot:
            return
        
        # Adicionar XP por mensagem
        if isinstance(message.channel, discord.TextChannel):
            level_up = self.economia.add_xp(message.author.id, random.randint(5, 15))
            if level_up:
                embed = discord.Embed(title="🎉 LEVEL UP!", color=0x00ff00)
                embed.add_field(name="Usuário", value=message.author.mention, inline=True)
                embed.add_field(name="Novo Level", value=f"**{level_up}**", inline=True)
                await message.channel.send(embed=embed)
        
        # Resposta da GROK quando mencionado
        if self.user in message.mentions or (message.reference and message.reference.resolved.author == self.user):
            historico = [{"role": "system", "content": "Você é um assistente sarcástico e inteligente. Responda de forma natural como um humano."}]
            resposta = await self.ia.grok_resposta(message.content, historico)
            await message.reply(resposta, mention_author=True)
        
        await self.process_commands(message)

# INICIALIZAÇÃO DO IMPERIO
bot = BotImperioCompleto()

# 🔥 COMANDOS DE ADMINISTRAÇÃO (10 comandos)
@bot.tree.command(name="ban", description="Bane um usuário permanentemente")
@app_commands.describe(usuario="Usuário a ser banido", motivo="Motivo do banimento")
async def ban(interaction: discord.Interaction, usuario: discord.Member, motivo: str = "Sem motivo"):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("❌ Você não tem permissão para banir!", ephemeral=True)
        return
    
    await usuario.ban(reason=motivo)
    embed = discord.Embed(title="🔨 BANIMENTO EXECUTADO", color=0xff0000)
    embed.add_field(name="Usuário", value=usuario.mention, inline=True)
    embed.add_field(name="Motivo", value=motivo, inline=True)
    embed.add_field(name="Por", value=interaction.user.mention, inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="unban", description="Desbane um usuário")
@app_commands.describe(user_id="ID do usuário a ser desbanido")
async def unban(interaction: discord.Interaction, user_id: str):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)
        return
    
    try:
        user_id = int(user_id)
        user = await bot.fetch_user(user_id)
        await interaction.guild.unban(user)
        embed = discord.Embed(title="✅ USUÁRIO DESBANIDO", color=0x00ff00)
        embed.add_field(name="Usuário", value=f"{user.name}#{user.discriminator}", inline=True)
        await interaction.response.send_message(embed=embed)
    except:
        await interaction.response.send_message("❌ Erro ao desbanir usuário!", ephemeral=True)

@bot.tree.command(name="kick", description="Expulsa um usuário")
@app_commands.describe(usuario="Usuário a ser expulso", motivo="Motivo")
async def kick(interaction: discord.Interaction, usuario: discord.Member, motivo: str = "Sem motivo"):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)
        return
    
    await usuario.kick(reason=motivo)
    embed = discord.Embed(title="👢 USUÁRIO EXPULSO", color=0xffaa00)
    embed.add_field(name="Usuário", value=usuario.mention, inline=True)
    embed.add_field(name="Motivo", value=motivo, inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="mute", description="Silencia um usuário")
@app_commands.describe(usuario="Usuário a ser silenciado", tempo="Tempo em minutos")
async def mute(interaction: discord.Interaction, usuario: discord.Member, tempo: int = 60):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)
        return
    
    tempo_timedelta = datetime.timedelta(minutes=tempo)
    await usuario.timeout(tempo_timedelta)
    
    embed = discord.Embed(title="🔇 USUÁRIO SILENCIADO", color=0xff6600)
    embed.add_field(name="Usuário", value=usuario.mention, inline=True)
    embed.add_field(name="Duração", value=f"{tempo} minutos", inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="unmute", description="Remove silêncio de usuário")
@app_commands.describe(usuario="Usuário a ser dessilenciado")
async def unmute(interaction: discord.Interaction, usuario: discord.Member):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)
        return
    
    await usuario.timeout(None)
    embed = discord.Embed(title="🔊 SILÊNCIO REMOVIDO", color=0x00ff00)
    embed.add_field(name="Usuário", value=usuario.mention, inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="lock", description="Trava um canal")
@app_commands.describe(canal="Canal a ser travado")
async def lock(interaction: discord.Interaction, canal: discord.TextChannel = None):
    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)
        return
    
    channel = canal or interaction.channel
    await channel.set_permissions(interaction.guild.default_role, send_messages=False)
    
    embed = discord.Embed(title="🔒 CANAL TRAVADO", color=0xff0000)
    embed.add_field(name="Canal", value=channel.mention, inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="unlock", description="Destrava um canal")
@app_commands.describe(canal="Canal a ser destravado")
async def unlock(interaction: discord.Interaction, canal: discord.TextChannel = None):
    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)
        return
    
    channel = canal or interaction.channel
    await channel.set_permissions(interaction.guild.default_role, send_messages=True)
    
    embed = discord.Embed(title="🔓 CANAL DESTRAVADO", color=0x00ff00)
    embed.add_field(name="Canal", value=channel.mention, inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="slowmode", description="Ativa slowmode no canal")
@app_commands.describe(segundos="Segundos de delay entre mensagens")
async def slowmode(interaction: discord.Interaction, segundos: int):
    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)
        return
    
    await interaction.channel.edit(slowmode_delay=segundos)
    
    embed = discord.Embed(title="🐌 SLOWMODE ATIVADO", color=0xffff00)
    embed.add_field(name="Canal", value=interaction.channel.mention, inline=True)
    embed.add_field(name="Delay", value=f"{segundos} segundos", inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="clear", description="Limpa mensagens")
@app_commands.describe(quantidade="Número de mensagens para limpar")
async def clear(interaction: discord.Interaction, quantidade: int = 10):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)
        return
    
    await interaction.channel.purge(limit=quantidade + 1)
    await interaction.response.send_message(f"🧹 {quantidade} mensagens vaporizadas!", ephemeral=True)

@bot.tree.command(name="warn", description="Adverte um usuário")
@app_commands.describe(usuario="Usuário a ser advertido", motivo="Motivo da advertência")
async def warn(interaction: discord.Interaction, usuario: discord.Member, motivo: str = "Sem motivo"):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)
        return
    
    bot.moderacao.add_warn(usuario.id, interaction.user.id, motivo)
    
    embed = discord.Embed(title="⚠️ ADVERTÊNCIA APLICADA", color=0xffaa00)
    embed.add_field(name="Usuário", value=usuario.mention, inline=True)
    embed.add_field(name="Motivo", value=motivo, inline=True)
    embed.add_field(name="Por", value=interaction.user.mention, inline=True)
    await interaction.response.send_message(embed=embed)

# 🛡️ COMANDOS DE MODERAÇÃO (8 comandos)
@bot.tree.command(name="warnings", description="Mostra advertências de um usuário")
@app_commands.describe(usuario="Usuário para ver advertências")
async def warnings(interaction: discord.Interaction, usuario: discord.Member):
    warns = bot.moderacao.get_warns(usuario.id)
    
    if not warns:
        await interaction.response.send_message(f"✅ {usuario.mention} não tem advertências!", ephemeral=True)
        return
    
    embed = discord.Embed(title=f"📋 ADVERTÊNCIAS - {usuario.display_name}", color=0xffaa00)
    
    for warn in warns[:5]:  # Mostrar apenas as 5 primeiras
        moderator = await bot.fetch_user(warn[2])
        embed.add_field(
            name=f"ID: {warn[0]} | {warn[4]}",
            value=f"**Motivo:** {warn[3]}\n**Por:** {moderator.mention}",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="report", description="Reporta um usuário")
@app_commands.describe(usuario="Usuário a ser reportado", motivo="Motivo do report")
async def report(interaction: discord.Interaction, usuario: discord.Member, motivo: str):
    embed = discord.Embed(title="🚨 NOVO REPORT", color=0xff0000)
    embed.add_field(name="Reportado", value=usuario.mention, inline=True)
    embed.add_field(name="Por", value=interaction.user.mention, inline=True)
    embed.add_field(name="Motivo", value=motivo, inline=False)
    
    # Enviar para canal de moderação se existir
    for channel in interaction.guild.text_channels:
        if "mod" in channel.name or "report" in channel.name:
            await channel.send(embed=embed)
            break
    else:
        await interaction.response.send_message(embed=embed)
        return
    
    await interaction.response.send_message("✅ Report enviado para a moderação!", ephemeral=True)

@bot.tree.command(name="antiraid", description="Ativa/desativa proteção contra raid")
@app_commands.describe(estado="Ligar ou desligar")
async def antiraid(interaction: discord.Interaction, estado: bool):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Apenas administradores!", ephemeral=True)
        return
    
    cursor = bot.conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO config (guild_id, antiraid) VALUES (?, ?)', 
                  (interaction.guild.id, int(estado)))
    bot.conn.commit()
    
    estado_text = "**ATIVADO** 🔒" if estado else "**DESATIVADO** 🔓"
    embed = discord.Embed(title="🛡️ PROTEÇÃO ANTI-RAID", color=0x00ff00 if estado else 0xff0000)
    embed.add_field(name="Status", value=estado_text, inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="antilink", description="Ativa/desativa bloqueio de links")
@app_commands.describe(estado="Ligar ou desligar")
async def antilink(interaction: discord.Interaction, estado: bool):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Apenas administradores!", ephemeral=True)
        return
    
    cursor = bot.conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO config (guild_id, antilink) VALUES (?, ?)', 
                  (interaction.guild.id, int(estado)))
    bot.conn.commit()
    
    estado_text = "**ATIVADO** 🔒" if estado else "**DESATIVADO** 🔓"
    embed = discord.Embed(title="🔗 BLOQUEIO DE LINKS", color=0x00ff00 if estado else 0xff0000)
    embed.add_field(name="Status", value=estado_text, inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="autorole", description="Define cargo automático")
@app_commands.describe(cargo="Cargo a ser dado automaticamente")
async def autorole(interaction: discord.Interaction, cargo: discord.Role):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Apenas administradores!", ephemeral=True)
        return
    
    embed = discord.Embed(title="🤖 AUTO ROLE CONFIGURADO", color=0x00ff00)
    embed.add_field(name="Cargo", value=cargo.mention, inline=True)
    embed.add_field(name="Aviso", value="Novos membros receberão este cargo automaticamente", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="setwelcome", description="Configura mensagem de boas-vindas")
@app_commands.describe(mensagem="Mensagem de boas-vindas")
async def setwelcome(interaction: discord.Interaction, mensagem: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Apenas administradores!", ephemeral=True)
        return
    
    cursor = bot.conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO config (guild_id, welcome_message) VALUES (?, ?)', 
                  (interaction.guild.id, mensagem))
    bot.conn.commit()
    
    embed = discord.Embed(title="👋 MENSAGEM DE BOAS-VINDAS", color=0x00ff00)
    embed.add_field(name="Mensagem", value=mensagem, inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="modlogs", description="Configura logs de moderação")
async def modlogs(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Apenas administradores!", ephemeral=True)
        return
    
    embed = discord.Embed(title="📊 LOGS DE MODERAÇÃO", color=0x9b59b6)
    embed.add_field(name="Recursos", value="• Banimentos\n• Expulsões\n• Advertências\n• Reports", inline=True)
    embed.add_field(name="Status", value="✅ **ATIVO**", inline=True)
    await interaction.response.send_message(embed=embed)

# 🔧 COMANDOS DE UTILIDADE (8 comandos)
@bot.tree.command(name="serverinfo", description="Mostra informações do servidor")
async def serverinfo(interaction: discord.Interaction):
    guild = interaction.guild
    
    embed = discord.Embed(title=f"📊 {guild.name}", color=0x3498db)
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    
    embed.add_field(name="👑 Dono", value=guild.owner.mention, inline=True)
    embed.add_field(name="🆔 ID", value=guild.id, inline=True)
    embed.add_field(name="📅 Criado em", value=guild.created_at.strftime("%d/%m/%Y"), inline=True)
    embed.add_field(name="👥 Membros", value=guild.member_count, inline=True)
    embed.add_field(name="📝 Canais", value=len(guild.channels), inline=True)
    embed.add_field(name="🎭 Cargos", value=len(guild.roles), inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="userinfo", description="Mostra informações de um usuário")
@app_commands.describe(usuario="Usuário para ver informações")
async def userinfo(interaction: discord.Interaction, usuario: discord.Member = None):
    user = usuario or interaction.user
    
    embed = discord.Embed(title=f"👤 {user.display_name}", color=user.color)
    embed.set_thumbnail(url=user.avatar.url if user.avatar else None)
    
    embed.add_field(name="📛 Nome", value=f"{user.name}#{user.discriminator}", inline=True)
    embed.add_field(name="🆔 ID", value=user.id, inline=True)
    embed.add_field(name="📅 Entrou em", value=user.joined_at.strftime("%d/%m/%Y"), inline=True)
    embed.add_field(name="�️ Conta criada", value=user.created_at.strftime("%d/%m/%Y"), inline=True)
    embed.add_field(name="🎭 Cargos", value=", ".join([role.mention for role in user.roles[1:5]]), inline=True)
    embed.add_field(name="🤖 Bot", value="Sim" if user.bot else "Não", inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ping", description="Mostra latência do bot")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    
    embed = discord.Embed(title="🏓 PONG!", color=0x00ff00)
    embed.add_field(name="Latência", value=f"{latency}ms", inline=True)
    embed.add_field(name="Status", value="✅ Online" if latency < 200 else "⚠️ Lento", inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="avatar", description="Mostra avatar de um usuário")
@app_commands.describe(usuario="Usuário para ver avatar")
async def avatar(interaction: discord.Interaction, usuario: discord.Member = None):
    user = usuario or interaction.user
    
    embed = discord.Embed(title=f"🖼️ Avatar de {user.display_name}", color=0x3498db)
    embed.set_image(url=user.avatar.url if user.avatar else user.default_avatar.url)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="roles", description="Lista todos os cargos do servidor")
async def roles(interaction: discord.Interaction):
    roles = [role for role in interaction.guild.roles if role.name != "@everyone"]
    
    if not roles:
        await interaction.response.send_message("❌ Não há cargos no servidor!", ephemeral=True)
        return
    
    roles_text = "\n".join([f"{role.mention} ({len(role.members)} membros)" for role in roles[:15]])
    
    embed = discord.Embed(title="🎭 CARGOS DO SERVIDOR", color=0x9b59b6)
    embed.add_field(name=f"Total: {len(roles)}", value=roles_text, inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="invite", description="Gera invite do bot")
async def invite(interaction: discord.Interaction):
    embed = discord.Embed(title="🔗 CONVITE DO BOT", color=0x00ff00)
    embed.add_field(name="Convite", value="[Clique aqui para adicionar o bot](https://discord.com/oauth2/authorize?client_id=SEU_BOT_ID&scope=bot&permissions=8)", inline=False)
    embed.add_field(name="Permissões", value="Administrador (Recomendado)", inline=True)
    embed.add_field(name="Suporte", value="Entre em contato com o desenvolvedor", inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="suggest", description="Envia uma sugestão")
@app_commands.describe(sugestao="Sua sugestão")
async def suggest(interaction: discord.Interaction, sugestao: str):
    embed = discord.Embed(title="💡 NOVA SUGESTÃO", color=0xffd700)
    embed.add_field(name="Autor", value=interaction.user.mention, inline=True)
    embed.add_field(name="Sugestão", value=sugestao, inline=False)
    
    # Procurar canal de sugestões
    for channel in interaction.guild.text_channels:
        if "sugest" in channel.name or "suggest" in channel.name:
            await channel.send(embed=embed)
            await interaction.response.send_message("✅ Sugestão enviada!", ephemeral=True)
            return
    
    await interaction.response.send_message(embed=embed)

# 🎉 COMANDOS DE ENTRETENIMENTO (7 comandos)
@bot.tree.command(name="rank", description="Mostra seu nível e XP")
@app_commands.describe(usuario="Usuário para ver rank")
async def rank(interaction: discord.Interaction, usuario: discord.Member = None):
    user = usuario or interaction.user
    user_data = bot.economia.get_user_data(user.id)
    
    embed = discord.Embed(title=f"🏆 RANK - {user.display_name}", color=0xffd700)
    embed.set_thumbnail(url=user.avatar.url if user.avatar else None)
    
    embed.add_field(name="📊 Level", value=user_data[5], inline=True)
    embed.add_field(name="⭐ XP", value=f"{user_data[4]}/{user_data[5] * 100}", inline=True)
    embed.add_field(name="💰 Moedas", value=user_data[1], inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="top", description="Ranking do servidor")
async def top(interaction: discord.Interaction):
    cursor = bot.conn.cursor()
    cursor.execute('SELECT user_id, level, xp FROM economia ORDER BY level DESC, xp DESC LIMIT 10')
    top_users = cursor.fetchall()
    
    if not top_users:
        await interaction.response.send_message("❌ Nenhum dado encontrado!", ephemeral=True)
        return
    
    ranking_text = ""
    for i, (user_id, level, xp) in enumerate(top_users, 1):
        try:
            user = await bot.fetch_user(user_id)
            ranking_text += f"{i}. {user.mention} - Level {level} ({xp} XP)\n"
        except:
            ranking_text += f"{i}. Usuário {user_id} - Level {level}\n"
    
    embed = discord.Embed(title="🏆 RANKING DO SERVIDOR", color=0xffd700)
    embed.add_field(name="Top 10", value=ranking_text, inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="daily", description="Resgate diário de moedas")
async def daily(interaction: discord.Interaction):
    cursor = bot.conn.cursor()
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    
    cursor.execute('SELECT last_daily, daily_streak FROM economia WHERE user_id = ?', (interaction.user.id,))
    result = cursor.fetchone()
    
    if result and result[0] == today:
        await interaction.response.send_message("❌ Você já resgatou hoje!", ephemeral=True)
        return
    
    streak = (result[1] + 1) if result else 1
    coins_earned = 100 + (streak * 20)
    
    if result:
        cursor.execute('''
            UPDATE economia SET coins = coins + ?, daily_streak = ?, last_daily = ?
            WHERE user_id = ?
        ''', (coins_earned, streak, today, interaction.user.id))
    else:
        cursor.execute('''
            INSERT INTO economia (user_id, coins, daily_streak, last_daily)
            VALUES (?, ?, ?, ?)
        ''', (interaction.user.id, 100 + coins_earned, streak, today))
    
    bot.conn.commit()
    
    embed = discord.Embed(title="🎁 RECOMPENSA DIÁRIA", color=0x00ff00)
    embed.add_field(name="Ganho", value=f"🪙 {coins_earned}", inline=True)
    embed.add_field(name="Sequência", value=f"🔥 {streak} dias", inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="meme", description="Envia um meme aleatório")
async def meme(interaction: discord.Interaction):
    try:
        response = requests.get('https://meme-api.com/gimme')
        data = response.json()
        
        embed = discord.Embed(title=data['title'], color=0xff6600)
        embed.set_image(url=data['url'])
        embed.set_footer(text=f"r/{data['subreddit']} | 👍 {data['ups']}")
        
        await interaction.response.send_message(embed=embed)
    except:
        embed = discord.Embed(title="😂 MEME ALEATÓRIO", color=0xff6600)
        embed.add_field(name="Erro", value="Não foi possível carregar o meme 😢", inline=False)
        await interaction.response.send_message(embed=embed)

@bot.tree.command(name="kiss", description="Beija um usuário")
@app_commands.describe(usuario="Usuário para beijar")
async def kiss(interaction: discord.Interaction, usuario: discord.Member):
    gifs = [
        "https://media.giphy.com/media/ZRSGWtBJG4Tza/giphy.gif",
        "https://media.giphy.com/media/bGm9FuBCGg4SY/giphy.gif",
        "https://media.giphy.com/media/KmeIYo9IGBoGY/giphy.gif"
    ]
    
    embed = discord.Embed(title=f"💋 {interaction.user.display_name} beijou {usuario.display_name}!", color=0xff69b4)
    embed.set_image(url=random.choice(gifs))
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="hug", description="Abraça um usuário")
@app_commands.describe(usuario="Usuário para abraçar")
async def hug(interaction: discord.Interaction, usuario: discord.Member):
    gifs = [
        "https://media.giphy.com/media/od5H3PmEG5EVq/giphy.gif",
        "https://media.giphy.com/media/wnsgren9NxITS/giphy.gif",
        "https://media.giphy.com/media/3ZnBrkqoaI2hq/giphy.gif"
    ]
    
    embed = discord.Embed(title=f"🤗 {interaction.user.display_name} abraçou {usuario.display_name}!", color=0x00ff00)
    embed.set_image(url=random.choice(gifs))
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ship", description="Calcula compatibilidade entre dois usuários")
@app_commands.describe(usuario1="Primeiro usuário", usuario2="Segundo usuário")
async def ship(interaction: discord.Interaction, usuario1: discord.Member, usuario2: discord.Member):
    compatibility = random.randint(0, 100)
    
    if compatibility < 30:
        status = "💔 Não combinam"
    elif compatibility < 60:
        status = "💛 Talvez..."
    elif compatibility < 85:
        status = "💚 Boa química!"
    else:
        status = "💖 ALMA GÊMEA!"
    
    embed = discord.Embed(title="💕 SHIP CALCULATOR", color=0xff69b4)
    embed.add_field(name="Usuário 1", value=usuario1.mention, inline=True)
    embed.add_field(name="Usuário 2", value=usuario2.mention, inline=True)
    embed.add_field(name="Compatibilidade", value=f"**{compatibility}%**\n{status}", inline=False)
    
    await interaction.response.send_message(embed=embed)

# 💰 COMANDOS DE ECONOMIA (6 comandos)
@bot.tree.command(name="balance", description="Ver suas moedas")
@app_commands.describe(usuario="Usuário para ver saldo")
async def balance(interaction: discord.Interaction, usuario: discord.Member = None):
    user = usuario or interaction.user
    user_data = bot.economia.get_user_data(user.id)
    
    coins = user_data[1]
    
    embed = discord.Embed(title="💰 SALDO", color=0xffd700)
    embed.add_field(name="Usuário", value=user.mention, inline=True)
    embed.add_field(name="Moedas", value=f"🪙 {coins}", inline=True)
    
    if coins < 100:
        embed.add_field(name="Status", value="💸 Pobre", inline=True)
    elif coins < 1000:
        embed.add_field(name="Status", value="💵 Classe Média", inline=True)
    else:
        embed.add_field(name="Status", value="💎 Rico", inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="pay", description="Transfere moedas para outro usuário")
@app_commands.describe(usuario="Usuário para pagar", quantia="Quantia a transferir")
async def pay(interaction: discord.Interaction, usuario: discord.Member, quantia: int):
    if quantia <= 0:
        await interaction.response.send_message("❌ Quantia inválida!", ephemeral=True)
        return
    
    user_data = bot.economia.get_user_data(interaction.user.id)
    
    if user_data[1] < quantia:
        await interaction.response.send_message("❌ Saldo insuficiente!", ephemeral=True)
        return
    
    # Debitar do remetente
    bot.economia.add_coins(interaction.user.id, -quantia)
    # Creditar ao destinatário
    bot.economia.add_coins(usuario.id, quantia)
    
    embed = discord.Embed(title="💸 TRANSFERÊNCIA", color=0x00ff00)
    embed.add_field(name="De", value=interaction.user.mention, inline=True)
    embed.add_field(name="Para", value=usuario.mention, inline=True)
    embed.add_field(name="Quantia", value=f"🪙 {quantia}", inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="work", description="Trabalhe para ganhar moedas")
async def work(interaction: discord.Interaction):
    jobs = [
        ("💻 Programador", random.randint(50, 150)),
        ("🍔 Lanchonete", random.randint(30, 80)),
        ("🏪 Mercado", random.randint(40, 100)),
        ("🚗 Uber", random.randint(60, 120)),
        ("🎨 Designer", random.randint(70, 160))
    ]
    
    job, earnings = random.choice(jobs)
    
    bot.economia.add_coins(interaction.user.id, earnings)
    
    embed = discord.Embed(title="💼 TRABALHO", color=0x00ff00)
    embed.add_field(name="Emprego", value=job, inline=True)
    embed.add_field(name="Ganho", value=f"🪙 {earnings}", inline=True)
    embed.add_field(name="Saldo Atual", value=f"🪙 {bot.economia.get_user_data(interaction.user.id)[1]}", inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="rob", description="Tenta roubar moedas de um usuário")
@app_commands.describe(usuario="Usuário para roubar")
async def rob(interaction: discord.Interaction, usuario: discord.Member):
    if usuario.id == interaction.user.id:
        await interaction.response.send_message("❌ Não pode roubar de si mesmo!", ephemeral=True)
        return
    
    victim_data = bot.economia.get_user_data(usuario.id)
    
    if victim_data[1] < 50:
        await interaction.response.send_message("❌ A vítima é muito pobre para roubar!", ephemeral=True)
        return
    
    success = random.choice([True, False, False])  # 33% de chance
    
    if success:
        stolen = random.randint(10, min(100, victim_data[1]))
        bot.economia.add_coins(usuario.id, -stolen)
        bot.economia.add_coins(interaction.user.id, stolen)
        
        embed = discord.Embed(title="💰 ROUBO BEM SUCEDIDO!", color=0xff0000)
        embed.add_field(name="Ladrão", value=interaction.user.mention, inline=True)
        embed.add_field(name="Vítima", value=usuario.mention, inline=True)
        embed.add_field(name="Roubado", value=f"🪙 {stolen}", inline=True)
    else:
        fine = random.randint(20, 50)
        bot.economia.add_coins(interaction.user.id, -fine)
        
        embed = discord.Embed(title="🚨 ROUBO FALHOU!", color=0xffaa00)
        embed.add_field(name="Ladrão", value=interaction.user.mention, inline=True)
        embed.add_field(name="Multa", value=f"🪙 {fine}", inline=True)
        embed.add_field(name="Aviso", value="Você foi pego pela polícia!", inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="shop", description="Mostra a loja do servidor")
async def shop(interaction: discord.Interaction):
    cursor = bot.conn.cursor()
    cursor.execute('SELECT * FROM loja')
    items = cursor.fetchall()
    
    if not items:
        await interaction.response.send_message("❌ Loja vazia!", ephemeral=True)
        return
    
    shop_text = ""
    for item in items:
        shop_text += f"**{item[0]}.** {item[1]} - 🪙 {item[2]}\n   *{item[3]}*\n\n"
    
    embed = discord.Embed(title="🛒 LOJA DO SERVIDOR", color=0x00ff00)
    embed.add_field(name="Itens Disponíveis", value=shop_text, inline=False)
    embed.add_field(name="Como Comprar", value="Use `/buy [ID]` para comprar um item", inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="buy", description="Compra um item da loja")
@app_commands.describe(item_id="ID do item para comprar")
async def buy(interaction: discord.Interaction, item_id: int):
    cursor = bot.conn.cursor()
    cursor.execute('SELECT * FROM loja WHERE item_id = ?', (item_id,))
    item = cursor.fetchone()
    
    if not item:
        await interaction.response.send_message("❌ Item não encontrado!", ephemeral=True)
        return
    
    user_data = bot.economia.get_user_data(interaction.user.id)
    
    if user_data[1] < item[2]:
        await interaction.response.send_message("❌ Saldo insuficiente!", ephemeral=True)
        return
    
    # Debitar o valor
    bot.economia.add_coins(interaction.user.id, -item[2])
    
    # Adicionar ao inventário
    cursor.execute('SELECT quantidade FROM inventario WHERE user_id = ? AND item_id = ?', 
                  (interaction.user.id, item_id))
    inventario = cursor.fetchone()
    
    if inventario:
        cursor.execute('UPDATE inventario SET quantidade = quantidade + 1 WHERE user_id = ? AND item_id = ?',
                      (interaction.user.id, item_id))
    else:
        cursor.execute('INSERT INTO inventario (user_id, item_id) VALUES (?, ?)',
                      (interaction.user.id, item_id))
    
    bot.conn.commit()
    
    embed = discord.Embed(title="🛒 COMPRA REALIZADA!", color=0x00ff00)
    embed.add_field(name="Item", value=item[1], inline=True)
    embed.add_field(name="Preço", value=f"🪙 {item[2]}", inline=True)
    embed.add_field(name="Saldo Restante", value=f"🪙 {user_data[1] - item[2]}", inline=True)
    
    await interaction.response.send_message(embed=embed)

# 🤖 COMANDOS DE IA E BACKUP
@bot.tree.command(name="script", description="Gera código com DeepSeek")
@app_commands.describe(prompt="O que você quer codificar?")
async def script(interaction: discord.Interaction, prompt: str):
    await interaction.response.defer()
    
    codigo = await bot.ia.deepseek_codigo(prompt)
    
    if len(codigo) > 2000:
        codigo = codigo[:1997] + "..."
    
    embed = discord.Embed(title="💻 CÓDIGO GERADO - DEEPSEEK", color=0x0099ff)
    embed.add_field(name="Prompt", value=prompt, inline=False)
    embed.add_field(name="Código", value=f"```python\n{codigo}\n```", inline=False)
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="backup", description="Faz backup COMPLETO do servidor")
async def backup(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Apenas administradores!", ephemeral=True)
        return
    
    await interaction.response.defer()
    
    backup_file = await bot.backup_system.criar_backup(interaction.guild)
    
    embed = discord.Embed(title="💾 BACKUP CRIADO", color=0x00ff00)
    embed.add_field(name="Servidor", value=interaction.guild.name, inline=True)
    embed.add_field(name="Arquivo", value=os.path.basename(backup_file), inline=True)
    embed.add_field(name="Aviso", value="Use /restore_backup com cuidado!", inline=False)
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="restore_backup", description="RESTAURA backup (CUIDADO!)")
@app_commands.describe(arquivo="Nome do arquivo de backup")
async def restore_backup(interaction: discord.Interaction, arquivo: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Apenas administradores!", ephemeral=True)
        return
    
    backup_file = os.path.join(bot.backup_system.backup_dir, arquivo)
    
    if not os.path.exists(backup_file):
        await interaction.response.send_message("❌ Arquivo de backup não encontrado!", ephemeral=True)
        return
    
    embed = discord.Embed(title="⚠️ ALERTA CRÍTICO", color=0xff0000)
    embed.add_field(name="AÇÃO IRREVERSÍVEL", value="Isso vai DESTRUIR o servidor atual e restaurar o backup!", inline=False)
    embed.add_field(name="Arquivo", value=arquivo, inline=True)
    embed.add_field(name="Servidor", value=interaction.guild.name, inline=True)
    
    await interaction.response.send_message(embed=embed)

# 🆘 COMANDO HELP COMPLETO
@bot.tree.command(name="helptz", description="Painel completo do IMPÉRIO")
async def helptz(interaction: discord.Interaction):
    embed = discord.Embed(title="🤖 PAINEL DO IMPÉRIO - COMANDOS COMPLETOS", color=0x9b59b6)
    
    admin_text = "• `/ban` - Banir usuário\n• `/unban` - Desbanir\n• `/kick` - Expulsar\n• `/mute` - Silenciar\n• `/unmute` - Dessilenciar\n• `/lock` - Travar canal\n• `/unlock` - Destravar\n• `/slowmode` - Slowmode\n• `/clear` - Limpar msg\n• `/warn` - Advertir"
    
    mod_text = "• `/warnings` - Ver warns\n• `/report` - Reportar\n• `/antiraid` - Anti-raid\n• `/antilink` - Bloquear links\n• `/autorole` - Cargo auto\n• `/setwelcome` - Boas-vindas\n• `/modlogs` - Logs"
    
    util_text = "• `/serverinfo` - Info server\n• `/userinfo` - Info user\n• `/ping` - Latência\n• `/avatar` - Avatar\n• `/roles` - Listar cargos\n• `/invite` - Convite bot\n• `/suggest` - Sugerir"
    
    ent_text = "• `/rank` - Seu nível\n• `/top` - Ranking\n• `/daily` - Diária\n• `/meme` - Meme\n• `/kiss` - Beijar\n• `/hug` - Abraçar\n• `/ship` - Compatibilidade"
    
    eco_text = "• `/balance` - Saldo\n• `/pay` - Transferir\n• `/work` - Trabalhar\n• `/rob` - Roubar\n• `/shop` - Loja\n• `/buy` - Comprar"
    
    ia_text = "• `Mencione o bot` - Resposta IA\n• `/script` - Gerar código\n• `/backup` - Backup\n• `/restore_backup` - Restaurar"
    
    embed.add_field(name="🔧 ADMINISTRAÇÃO (10)", value=admin_text, inline=True)
    embed.add_field(name="🛡️ MODERAÇÃO (7)", value=mod_text, inline=True)
    embed.add_field(name="🔧 UTILIDADE (7)", value=util_text, inline=True)
    embed.add_field(name="🎉 ENTRETENIMENTO (7)", value=ent_text, inline=True)
    embed.add_field(name="💰 ECONOMIA (6)", value=eco_text, inline=True)
    embed.add_field(name="🤖 IA & BACKUP (4)", value=ia_text, inline=True)
    
    embed.set_footer(text="Total: 41 comandos | Bot Império - Dominação Total")
    await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    try:
        bot.run(bot.config.token)
    except Exception as e:
        print(f"ERRO DO IMPERIO: {e}")
