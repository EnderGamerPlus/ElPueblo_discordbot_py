import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone


class AntiHack(commands.Cog, name="antihack"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.honeypot_id = int(bot.config.get("HONEYPOT_CHANNEL_ID", 0))
        self.log_id = int(bot.config.get("LOG_CHANNEL_ID", 0))

    # ═══════════════════════════════════════════════════════════════
    # ⬇️ BLOQUE EXTRA: Borrado de mensajes recientes (últimas 24h) ⬇️
    # ═══════════════════════════════════════════════════════════════
    # Esto es independiente del kick. Recorre TODOS los canales de
    # texto del servidor y borra los mensajes del usuario enviados
    # en las últimas 24 horas.
    #
    # NOTAS IMPORTANTES:
    # - El bot necesita el permiso "Gestionar mensajes" en cada canal.
    # - Discord solo permite bulk-delete (borrado masivo) de mensajes
    #   con menos de 14 días de antigüedad, así que 24h no da problema.
    # - Esto puede tardar unos segundos si el server tiene muchos
    #   canales, porque hay que revisar canal por canal.
    # - Si quieres desactivar esta parte, simplemente no la llames
    #   desde expulsar() más abajo.
    async def borrar_mensajes_recientes(self, member: discord.Member, guild: discord.Guild, horas: int = 24):
        limite = datetime.now(timezone.utc) - timedelta(hours=horas)
        total_borrados = 0

        for canal in guild.text_channels:
            # Verificar que el bot tenga permiso de borrar en ese canal
            permisos = canal.permissions_for(guild.me)
            if not permisos.manage_messages or not permisos.read_message_history:
                continue

            try:
                borrados = await canal.purge(
                    after=limite,
                    check=lambda m: m.author.id == member.id,
                    bulk=True,
                    reason=f"Limpieza automática - cuenta comprometida ({member.id})"
                )
                total_borrados += len(borrados)
            except discord.Forbidden:
                continue
            except discord.HTTPException:
                continue

        self.bot.logger.info(
            f"Limpieza: {total_borrados} mensajes borrados de {member} en {guild.name}"
        )
        return total_borrados
    # ═══════════════════════════════════════════════════════════════
    # ⬆️ FIN DEL BLOQUE EXTRA ⬆️
    # ═══════════════════════════════════════════════════════════════

    async def expulsar(self, member: discord.Member, message: discord.Message, razon: str):
        # 1. DM
        try:
            await member.send(
                f"⚠️ **Has sido expulsado automáticamente de {message.guild.name}**\n\n"
                f"**Motivo:** {razon}\n\n"
                f"Si tu cuenta fue hackeada:\n"
                f"• Cambia tu contraseña de Discord\n"
                f"• Activa el 2FA en Ajustes → Mi cuenta\n"
                f"• Ve a Ajustes → Apps autorizadas y revoca todo lo sospechoso\n\n"
                f"Puedes volver a unirte al servidor cuando quieras. Contacta a un administrador si crees que fue un error."
            )
        except discord.Forbidden:
            pass

        # 1.5 Borrar mensajes recientes (llamada al bloque de arriba)
        await self.borrar_mensajes_recientes(member, message.guild, horas=24)

        # 2. Kick
        try:
            await member.kick(reason=razon)
        except discord.Forbidden:
            self.bot.logger.warning(f"Sin permisos para expulsar a {member}")
            return

        # 3. Log
        log_channel = message.guild.get_channel(self.log_id)
        if log_channel:
            embed = discord.Embed(
                title="👢 Expulsión automática — Cuenta comprometida",
                color=discord.Color.orange()
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

        self.bot.logger.info(f"Expulsado: {member} | Motivo: {razon}")

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
                "**Cualquier mensaje enviado aquí resultará en una expulsión automática e inmediata.**\n\n"
                "Este sistema existe para proteger el servidor de cuentas hackeadas que envían spam malicioso. "
                "Si ves este canal, simplemente ignóralo.\n\n"
                "Si fuiste expulsado por error, contacta a un administrador."
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
        await self.expulsar(member, message, "Posible cuenta comprometida")


async def setup(bot) -> None:
    await bot.add_cog(AntiHack(bot))
