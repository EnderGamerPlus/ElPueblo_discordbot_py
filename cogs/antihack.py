import discord
from discord.ext import commands


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
                f"**Motivo:** {razon}\n\n"
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

        self.bot.logger.info(f"Baneado: {member} | Motivo: {razon}")

    @commands.hybrid_command(
        name="honeypotmsg",
        description="Envía el mensaje de advertencia del honeypot en el canal actual."
    )
    @commands.has_permissions(administrator=True)
    async def honeypotmsg(self, context: commands.Context) -> None:
        embed = discord.Embed(
            title="⚠️ CANAL DE SEGURIDAD — NO ESCRIBAS AQUÍ",
            description=(
                "Este canal está monitoreado por un sistema automático de detección de cuentas comprometidas.\n\n"
                "**Cualquier mensaje enviado aquí resultará en un ban automático e inmediato.**\n\n"
                "Este sistema existe para proteger el servidor de cuentas hackeadas que envían spam malicioso. "
                "Si ves este canal, simplemente ignóralo.\n\n"
                "Si fuiste baneado por error, contacta a un administrador."
            ),
            color=discord.Color.yellow()
        )
        await context.send(embed=embed)

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

        # ── DETECCIÓN: Cualquier mensaje en el canal honeypot ───────
        await self.banear(member, message, "Posible cuenta comprometida")


async def setup(bot) -> None:
    await bot.add_cog(AntiHack(bot))
