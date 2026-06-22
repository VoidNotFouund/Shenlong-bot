import json
import random
import time
import os
import discord
from discord.ext import commands
import asyncio
import re

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

IDS_CARGOS = [
    1477738723356442695,  # Cargo 1
    1477740135960412183,  # Cargo 2
    1477740937517072604,  # Cargo 3
    1510790994709450832   # Cargo 4
]

# IDs dos cargos que serão mencionados ao abrir um ticket
IDS_MENCAO = [
    1477738723356442695,
    1510790994709450832,
    1477740135960412183
]

CATEGORIA_TICKETS = 1477764400134885628
CANAL_LOGS = 1477757187869769840

# Anti-Link
LINKS_BLOQUEADOS = [
    "discord.gg/",
    "discord.com/invite/",
    "discordapp.com/invite/",
    "bit.ly/",
    "cutt.ly/",
    "tinyurl.com/"
]

# Configurações de Auto-Moderação
MAX_CAPS_PERCENT = 0.7
MAX_EMOJIS = 10
MAX_MENTIONS = 5
FLOOD_LIMIT = 5
FLOOD_WINDOW = 5
user_msg_history = {}

XP_FILE = "xp.json"
cooldown_xp = {}

def carregar_xp():
    try:
        with open(XP_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
            return dados if isinstance(dados, dict) else {}
    except:
        return {}

def salvar_xp(dados):
    temp_file = f"{XP_FILE}.tmp"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4)
    os.replace(temp_file, XP_FILE)

xp_data = carregar_xp()

def calcular_nivel(xp):
    return int((xp / 100) ** 0.5) + 1

def xp_proximo_nivel(nivel):
    return (nivel ** 2) * 100

# ==========================
# BOTÃO FECHAR TICKET
# ==========================

class CloseTicket(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🔒 Fechar Ticket",
        style=discord.ButtonStyle.red,
        custom_id="fechar_ticket"
    )
    async def fechar(self, interaction: discord.Interaction, button: discord.ui.Button):

        possui_cargo = any(
            cargo.id in IDS_CARGOS
            for cargo in interaction.user.roles
        )

        if not possui_cargo:
            await interaction.response.send_message(
                "❌ Apenas a equipe pode fechar tickets.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "🔒 Fechando ticket em 5 segundos...",
            ephemeral=True
        )

        logs = bot.get_channel(CANAL_LOGS)

        dono_id = None

        if interaction.channel.topic:
            try:
                dono_id = int(interaction.channel.topic)
            except:
                pass

        embed_log = discord.Embed(
            title="🔒 Ticket Fechado",
            color=0xFF0000
        )

        embed_log.add_field(
            name="Fechado por",
            value=f"{interaction.user.mention}\nID: {interaction.user.id}",
            inline=False
        )

        if dono_id:
            embed_log.add_field(
                name="Dono do Ticket",
                value=f"<@{dono_id}>\nID: {dono_id}",
                inline=False
            )

        embed_log.add_field(
            name="Canal",
            value=interaction.channel.name,
            inline=False
        )

        if logs:
            await logs.send(embed=embed_log)

        await asyncio.sleep(5)
        await interaction.channel.delete()

# ==========================
# BOTÃO ABRIR TICKET
# ==========================

class TicketButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🎫 Abrir Ticket",
        style=discord.ButtonStyle.green,
        custom_id="abrir_ticket"
    )
    async def ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.defer(ephemeral=True)

        categoria = interaction.guild.get_channel(CATEGORIA_TICKETS)

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(
                view_channel=False
            ),

            interaction.user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            ),
            interaction.guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_channels=True,
                read_message_history=True
            )
        }

        # Adiciona permissões para todos os cargos da lista
        for cargo_id in IDS_CARGOS:
            cargo = interaction.guild.get_role(cargo_id)
            if cargo:
                overwrites[cargo] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True
                )

        canal = await interaction.guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=categoria,
            overwrites=overwrites,
            topic=str(interaction.user.id)
        )

        logs = bot.get_channel(CANAL_LOGS)

        embed_log = discord.Embed(
            title="📂 Ticket Criado",
            color=0x00FF00
        )

        embed_log.add_field(
            name="Usuário",
            value=f"{interaction.user.mention}\nID: {interaction.user.id}",
            inline=False
        )

        embed_log.add_field(
            name="Canal",
            value=canal.name,
            inline=False
        )

        if logs:
            await logs.send(embed=embed_log)

        # Cria as menções para os cargos específicos
        mencoes_cargos = " ".join([f"<@&{cid}>" for cid in IDS_MENCAO])

        await canal.send(
            f"📢 Novo recrutamento aberto!\n"
            f"{interaction.user.mention} {mencoes_cargos}"
        )

        embed_ticket = discord.Embed(
            title="🐉 Formulário de Recrutamento",
            description=f"""
Olá {interaction.user.mention}!

Obrigado pelo interesse em fazer parte da equipe.

Responda às perguntas abaixo para avaliarmos seu recrutamento:

**1️⃣ Qual cargo você deseja ocupar?**
• Tradutor
• Revisor
• Cleaner
• Typesetter
• QC

**2️⃣ Possui alguma experiência?**

**3️⃣ Você trabalha por:**
• PC 💻
• Mobile 📱

**4️⃣ Já participou de alguma Scan?**
Se sim, informe o nome e a função que exercia.

**5️⃣ Quanto tempo livre você possui por semana?**

Após responder, aguarde um membro da equipe analisar sua inscrição.
""",
            color=0x00FF00
        )
        embed_ticket.set_image(url="https://cdn.discordapp.com/attachments/1492895451681259562/1518256287589077053/fd9ad3878785774402f260eb659a142b.gif?ex=6a3941da&is=6a37f05a&hm=b4e9bdf0c9454d7aed658b38cfbc3dc2c0f866b2dca31479e2410cdbbe389791&.")

        embed_ticket.set_footer(
            text="Shenlong • Sistema de Recrutamento"
        )

        await canal.send(
            embed=embed_ticket,
            view=CloseTicket()
        )

        await interaction.followup.send(
            f"✅ Ticket criado: {canal.mention}",
            ephemeral=True
        )

# ==========================
# EVENTOS
# ==========================

@bot.event
async def on_ready():
    bot.add_view(TicketButton())
    bot.add_view(CloseTicket())
    print(f"Logado como {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    conteudo = message.content.lower()

    # Anti-Link
    if any(link in conteudo for link in LINKS_BLOQUEADOS):
        if not (message.author.guild_permissions.administrator or any(cargo.id in IDS_CARGOS for cargo in message.author.roles)):
            await message.delete()
            logs = bot.get_channel(CANAL_LOGS)
            
            try:
                await message.author.ban(reason=f"Divulgação de link: {message.content}")
                if logs:
                    await logs.send(f"🔨 Usuário banido automaticamente por enviar link: {message.author} ({message.author.id})\nConteúdo: {message.content}")
            except Exception as e:
                if logs:
                    await logs.send(f"❌ Erro ao banir {message.author}: {e}")
            return

    # Honeypot
    if message.channel.id == 1518251467427811420:
        if message.author.guild_permissions.administrator or any(cargo.id in IDS_CARGOS for cargo in message.author.roles):
            return

        logs = bot.get_channel(CANAL_LOGS)
        if logs:
            await logs.send(f"🚨 Honeypot ativado!\nUsuário: {message.author} ({message.author.id})")

        await message.delete()
        await message.author.ban(reason="Atividade detectada no canal Honeypot")
        return

    # Não ganha XP em tickets
    if hasattr(message.channel, "category_id") and message.channel.category_id == CATEGORIA_TICKETS:
        await bot.process_commands(message)
        return

    # Auto-moderação (Flood, Caps, Emojis, Menções)
    if not (message.author.guild_permissions.administrator or any(cargo.id in IDS_CARGOS for cargo in message.author.roles)):
        # Flood
        u_id = message.author.id
        agora_mod = time.time()
        if u_id not in user_msg_history:
            user_msg_history[u_id] = []
        user_msg_history[u_id].append(agora_mod)
        user_msg_history[u_id] = [t for t in user_msg_history[u_id] if agora_mod - t < FLOOD_WINDOW]
        
        if len(user_msg_history[u_id]) > FLOOD_LIMIT:
            await message.delete()
            await message.channel.send(f"⚠️ {message.author.mention}, evite o flood!", delete_after=3)
            return

        # CAPS LOCK
        if len(message.content) > 15:
            upper_case = sum(1 for c in message.content if c.isupper())
            if (upper_case / len(message.content)) > MAX_CAPS_PERCENT:
                await message.delete()
                await message.channel.send(f"⚠️ {message.author.mention}, não use CAPS LOCK excessivo!", delete_after=3)
                return

        # Spam de Emoji
        emojis_custom = re.findall(r'<a?:\w+:\d+>', message.content)
        emojis_unicode = re.findall(r'[\U00010000-\U0010ffff]', message.content)
        if (len(emojis_custom) + len(emojis_unicode)) > MAX_EMOJIS:
            await message.delete()
            await message.channel.send(f"⚠️ {message.author.mention}, muitos emojis!", delete_after=3)
            return

        # Spam de Menções
        if (len(message.mentions) + len(message.role_mentions)) > MAX_MENTIONS:
            await message.delete()
            await message.channel.send(f"⚠️ {message.author.mention}, evite spam de menções!", delete_after=3)
            return

    agora = time.time()
    user_id = str(message.author.id)

    if user_id not in xp_data:
        xp_data[user_id] = {"xp": 0, "messages": 0}
    if "messages" not in xp_data[user_id]:
        xp_data[user_id]["messages"] = 0
    xp_data[user_id]["messages"] += 1

    if user_id not in cooldown_xp:
        cooldown_xp[user_id] = 0

    if agora - cooldown_xp[user_id] >= 30:
        ganho = random.randint(5, 15)
        xp_antigo = xp_data[user_id]["xp"]
        nivel_antigo = calcular_nivel(xp_antigo)
        xp_data[user_id]["xp"] += ganho
        nivel_novo = calcular_nivel(xp_data[user_id]["xp"])
        salvar_xp(xp_data)
        cooldown_xp[user_id] = agora

        if nivel_novo > nivel_antigo:
            await message.channel.send(f"🎉 {message.author.mention} subiu para o nível **{nivel_novo}**!")
    else:
        salvar_xp(xp_data)

    await bot.process_commands(message)

# ==========================
# COMANDOS
# ==========================

@bot.command()
async def painel(ctx):
    possui_cargo = any(
        cargo.id in IDS_CARGOS
        for cargo in ctx.author.roles
    )

    if not possui_cargo and not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ Apenas a equipe pode usar este comando.", delete_after=5)
        return

    embed = discord.Embed(
        title="🔥 NOVOS GUERREIROS SÃO NECESSÁRIOS 🔥",
        description="""
O recrutamento está aberto e estamos em busca de novos membros para fortalecer nossa equipe!

⚡ Tradutor — Traduz os capítulos para o português.
⚡ Revisor — Corrige erros de português e melhora a leitura.
⚡ Cleaner — Remove textos e efeitos da página original.
⚡ Typesetter — Insere os textos traduzidos nos balões e páginas.
⚡ QC (Quality Check) — Faz a revisão final para garantir a qualidade do capítulo.

🌟 Não tem experiência?
Sem problemas! Estamos dispostos a ensinar quem tiver dedicação e vontade de aprender.

📩 Abra um ticket e venha lutar ao nosso lado! 🐉⚡
""",
        color=0x00FF00
    )
    embed.set_image(url="https://cdn.discordapp.com/attachments/1492895451681259562/1518256287589077053/fd9ad3878785774402f260eb659a142b.gif?ex=6a3941da&is=6a37f05a&hm=b4e9bdf0c9454d7aed658b38cfbc3dc2c0f866b2dca31479e2410cdbbe389791&.")
    embed.set_footer(text="Shenlong • Sistema de Recrutamento")
    await ctx.send(embed=embed, view=TicketButton())

@bot.command()
async def xp(ctx, member: discord.Member = None):
    member = member or ctx.author
    user_id = str(member.id)
    
    if user_id not in xp_data:
        xp_data[user_id] = {"xp": 0, "messages": 0}
    
    if "messages" not in xp_data[user_id]:
        xp_data[user_id]["messages"] = 0

    xp_total = xp_data[user_id]["xp"]
    mensagens = xp_data[user_id]["messages"]
    nivel = calcular_nivel(xp_total)
    
    xp_atual_nivel = ((nivel - 1) ** 2) * 100
    xp_proximo = xp_proximo_nivel(nivel)
    xp_no_nivel = xp_total - xp_atual_nivel
    xp_necessario = xp_proximo - xp_atual_nivel
    
    porcentagem = min(100, int((xp_no_nivel / xp_necessario) * 100))
    blocos_cheios = int(porcentagem / 5)
    barra = "▰" * blocos_cheios + "▱" * (20 - blocos_cheios)

    ranking = sorted(xp_data.items(), key=lambda x: x[1]["xp"], reverse=True)
    posicao = next((i + 1 for i, (uid, _) in enumerate(ranking) if uid == user_id), len(ranking))

    medalha = ""
    if posicao == 1: medalha = "🥇 "
    elif posicao == 2: medalha = "🥈 "
    elif posicao == 3: medalha = "🥉 "
    
    entrada = member.joined_at.strftime("%d/%m/%Y")
    cor = member.top_role.color if member.top_role.color.value != 0 else 0x00FF00

    embed = discord.Embed(title=f"🐉 Perfil de {member.display_name}", color=cor)
    embed.set_thumbnail(url=member.display_avatar.url)
    
    embed.add_field(name="🏆 Nível", value=f"**{nivel}**", inline=True)
    embed.add_field(name="🥇 Posição", value=f"{medalha}#{posicao}", inline=True)
    embed.add_field(name="💬 Mensagens", value=f"{mensagens}", inline=True)
    
    embed.add_field(name="⭐ XP Total", value=f"`{xp_total}`", inline=True)
    embed.add_field(name="🎯 Próximo Nível", value=f"`{xp_proximo - xp_total}` XP", inline=True)
    embed.add_field(name="🎖️ Cargo mais alto", value=member.top_role.mention, inline=True)
    
    embed.add_field(name="📅 Entrada no Servidor", value=entrada, inline=False)
    embed.add_field(name="📈 Progresso", value=f"`{barra}` {porcentagem}%", inline=False)
    
    await ctx.send(embed=embed)

@bot.command()
async def top(ctx):
    ranking = sorted(xp_data.items(), key=lambda x: x[1]["xp"], reverse=True)[:10]
    descricao = ""
    medalhas = ["🥇", "🥈", "🥉"]
    
    for pos, (user_id, dados) in enumerate(ranking, start=1):
        membro = ctx.guild.get_member(int(user_id))
        if not membro: continue
        
        xp_total = dados["xp"]
        nivel = calcular_nivel(dados["xp"])
        
        xp_base = ((nivel - 1) ** 2) * 100
        xp_prox = (nivel ** 2) * 100
        xp_necessario = xp_prox - xp_base
        xp_atual_no_nivel = xp_total - xp_base
        porcentagem = min(100, int((xp_atual_no_nivel / xp_necessario) * 100))
        blocos = int(porcentagem / 10)
        barra = "█" * blocos + "░" * (10 - blocos)
        
        medalha = medalhas[pos - 1] if pos <= 3 else "🏅"
        descricao += f"{medalha} #{pos} • {membro.mention}\n🏆 Nível {nivel} • ⭐ {xp_total} XP\n`{barra}` {porcentagem}%\n\n"

    embed = discord.Embed(title="👑 Ranking Shenlong", description=descricao or "Sem dados.", color=0xFFD700)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def enviar_regras(ctx):
    channel_id = 1477722117809115308
    channel = bot.get_channel(channel_id)
    
    if channel:
        embed = discord.Embed(
            title="📜 Regras — Z scans ⭐",
            description=(
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "⭐ 🤝 **1. RESPEITO**\n"
                "• Respeite todos os membros, sem exceções\n"
                "• Proibido qualquer tipo de preconceito ou ofensa\n"
                "• Evite discussões tóxicas ou provocações\n"
                "• Brincadeiras só são permitidas sem desrespeito\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "⭐ 📢 **2. USO DOS CANAIS**\n"
                "• Utilize os canais corretamente\n"
                "• Proibido spam, flood ou excesso de mensagens\n"
                "• Evite mensagens fora de contexto\n"
                "• Use os canais de suporte quando necessário\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "⭐ 🚫 **3. CONTEÚDO PROIBIDO**\n"
                "• Proibido conteúdo +18 (NSFW)\n"
                "• Proibido links maliciosos ou suspeitos\n"
                "• Proibido divulgar conteúdo ilegal\n"
                "• Não compartilhe dados pessoais\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "⭐ 📚 **4. PROJETOS DA SCAN**\n"
                "• Não cobre capítulos ou prazos\n"
                "• Evite spoilers sem aviso\n"
                "• Respeite o trabalho da equipe\n"
                "• Proibido repost sem autorização\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "⭐ 👥 **5. STAFF**\n"
                "• Respeite a equipe e seus cargos\n"
                "• Não finja ser staff\n"
                "• Problemas devem ser resolvidos no suporte\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "⭐ 🔊 **6. DIVULGAÇÃO**\n"
                "• Apenas com permissão da staff\n"
                "• Parcerias no canal correto\n"
                "• Proibido spam de servidores\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "⭐ ⚠️ **7. PUNIÇÕES**\n"
                "• Aviso\n"
                "• Mute\n"
                "• Kick\n"
                "• Ban\n\n"
                "*A punição varia conforme a gravidade*\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "⭐ 📝 **8. REGRAS GERAIS**\n"
                "• Proibido uso de contas fakes\n"
                "• Evite tumulto e desordem\n"
                "• Use o bom senso sempre\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "✨ **Ao permanecer, você concorda com todas as regras.**"
            ),
            color=0x00FF00
        )
        await channel.send(embed=embed)
        await ctx.send(f"✅ Regras enviadas para o canal {channel.mention}!")
    else:
        await ctx.send(f"❌ Não consegui encontrar o canal com ID `{channel_id}`.")

@enviar_regras.error
async def enviar_regras_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Você não tem permissão para usar este comando (Administrador necessário).")
    else:
        await ctx.send(f"❌ Ocorreu um erro: {error}")

# ==========================
# EVENTO: ON_MEMBER_JOIN
# ==========================
@bot.event
async def on_member_join(member):
    channel_id = 1477734931085004990
    channel = bot.get_channel(channel_id)
    if channel:
        gif_url = "https://cdn.discordapp.com/attachments/1492895451681259562/1518447106325483691/1c49b480bf1f412e339b3a5cd8c43dd6.gif?ex=6a39f391&is=6a38a211&hm=4f563104d73b497df0a8b7fc6d299f810834b6fefd8bc76d95f61af2201aa7e5&"
        message = (
            f"🐉 Seja bem-vindo(a), {member.mention}!\n"
          

bot.run(os.getenv("TOKEN"))
