
import os
import discord
from discord.ext import commands
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

CARGO_1 = 1516608454964547797
CARGO_2 = 1494463012214669502

CATEGORIA_TICKETS = 1516946164149129328
CANAL_LOGS = 1516946200920854558

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
            cargo.id in [CARGO_1, CARGO_2]
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

        cargo1 = interaction.guild.get_role(CARGO_1)
        cargo2 = interaction.guild.get_role(CARGO_2)

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

            cargo1: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            ),

            cargo2: discord.PermissionOverwrite(
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

        await canal.send(
            f"📢 Novo recrutamento aberto!\n"
            f"{interaction.user.mention} <@&{CARGO_1}> <@&{CARGO_2}>"
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

        embed_ticket.set_image(
            url="https://cdn.discordapp.com/attachments/1516595138602733669/1516598738846613524/fd9ad3878785774402f260eb659a142b.gif"
        )

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

# ==========================
# COMANDO PAINEL
# ==========================

@bot.command()
async def painel(ctx):

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

    embed.set_image(
        url="https://cdn.discordapp.com/attachments/1516595138602733669/1516598738846613524/fd9ad3878785774402f260eb659a142b.gif"
    )

    embed.set_footer(
        text="Shenlong • Sistema de Recrutamento"
    )

    await ctx.send(
        embed=embed,
        view=TicketButton()
    )

# ==========================
# TOKEN
# ==========================

bot.run(os.getenv("TOKEN"))
