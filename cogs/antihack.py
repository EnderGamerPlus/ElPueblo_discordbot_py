import discord
from discord.ext import commands
import time

# { user_id: {"images": int, "messages": [timestamps]} }
user_activity = {}

IMAGE_THRESHOLD = 3       # Imágenes en un solo mensaje
MSG_THRESHOLD = 5         # Mensajes en poco tiempo
MSG_WINDOW_SECONDS = 5    # Ventana de tiempo para contar mensajes


class AntiHack(commands.Cog, name="antihack"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.honeypot_id = int(bot.config.get("HONEYPOT_CHANNEL_ID", 0))
        self.log_id = int(bot.config.get("LOG_CHANNEL_ID", 0))

    async def banear(self, member: discord.Member, message: discord.Message, razon: str):
        # 1. DM
        try:
            await member.send(
                f"⚠️ **Has sido baneado automáticamente de {message.guild.name}**\n\n"
                f"**Motivo:** Cuenta posiblemente vulnerada\n\n"
                f"**Detección:** {razon}\n\n"
                f"Si tu cuenta fue hackeada:\n"
                f"• Cambia tu contraseña de Discord\n"
                f"• Activa el 2FA en Ajustes → Mi cuenta\n"
                f"• Ve a Ajustes → Apps autorizadas y revoca todo lo sospechoso\n\n"
                f"Contacta a un administrador para apelar el ban."
            )
        except discord.Forbidden:
            pass

        # 2. Ban
        try:
            await member.ban(
                reason=razon,
                delete_message_seconds=86400
            )
        except discord.Forbidden:
            self.bot.logger.warning(f"Sin permisos para banear a {member}")
            return

        # 3. Log
        log_channel = message.guild.get_channel(self.log_id)
        if log_channel:
            embed = discord.Embed(
                title="🔨 Ban automático — Cuenta comprometida",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Usuario", value=f"{member.mention} (`{member.id}`)", inline=False)
            embed.add_field(name="Motivo", value=razon, inline=False)
            embed.add_field(
                name="Mensaje", value=message.content[:200] or "*(sin texto)*", inline=False)
            if message.attachments:
                embed.add_field(
                    name="Adjuntos",
                    value="\n".join(a.url for a in message.attachments[:5]),
                    inline=False
                )
            await log_channel.send(embed=embed)

        # Limpiar datos del usuario
        user_activity.pop(member.id, None)
        self.bot.logger.info(f"Baneado: {member} | Motivo: {razon}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignorar bots y DMs
        if message.author.bot or not message.guild:
            return

        # SOLO actuar en el canal honeypot
        if not self.honeypot_id or message.channel.id != self.honeypot_id:
            return

        member = message.guild.get_member(message.author.id)
        if not member:
            return

        # Ignorar admins y moderadores
        if member.guild_permissions.administrator or member.guild_permissions.ban_members:
            return

        uid = member.id
        if uid not in user_activity:
            user_activity[uid] = {"images": 0, "messages": []}

        now = time.time()

        # ── DETECCIÓN 1: @everyone o @here ──────────────────────────
        contenido = message.content.lower()
        if "@everyone" in contenido or "@here" in contenido:
            await self.banear(member, message, "Uso de @everyone/@here en canal protegido")
            return

        # ── DETECCIÓN 2: Más de 3 imágenes en un mensaje ────────────
        if len(message.attachments) > IMAGE_THRESHOLD:
            await self.banear(member, message, f"Más de {IMAGE_THRESHOLD} imágenes en un solo mensaje")
            return

        # ── DETECCIÓN 3: Muchos mensajes seguidos ───────────────────
        user_activity[uid]["messages"].append(now)
        # Limpiar mensajes fuera de la ventana de tiempo
        user_activity[uid]["messages"] = [
            t for t in user_activity[uid]["messages"]
            if now - t <= MSG_WINDOW_SECONDS
        ]
        if len(user_activity[uid]["messages"]) >= MSG_THRESHOLD:
            await self.banear(member, message, f"Spam: {MSG_THRESHOLD}+ mensajes en {MSG_WINDOW_SECONDS} segundos")
            return


async def setup(bot) -> None:
    await bot.add_cog(AntiHack(bot))
