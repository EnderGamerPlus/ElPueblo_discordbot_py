import discord
from discord.ext import commands


class Ban(commands.Cog, name="ban"):
    def __init__(self, bot) -> None:
        self.bot = bot

    # ═══════════════════════════════════════════════════════════════
    # ⬇️ BLOQUE EXTRA: Ban por ID fija ⬇️
    # ═══════════════════════════════════════════════════════════════
    # Banea a un usuario específico por su ID, esté o no en el server.
    # NOTAS:
    # - El bot necesita el permiso "Banear miembros".
    # - El rol del bot debe estar por encima del rol más alto del
    #   usuario (si es que está en el server).
    # - CUALQUIER usuario puede ejecutar el comando, pero solo banea
    #   a la ID fija de abajo (no acepta otros objetivos).
    ID_A_BANEAR = 432610292342587392

    async def banear_por_id(self, guild: discord.Guild, user_id: int, razon: str) -> bool:
        try:
            await guild.ban(
                discord.Object(id=user_id),
                reason=razon,
                delete_message_seconds=86400  # borra sus mensajes de las últimas 24h
            )
            self.bot.logger.info(
                f"Baneado por ID: {user_id} | Motivo: {razon}")
            return True
        except discord.Forbidden:
            self.bot.logger.warning(f"Sin permisos para banear a {user_id}")
            return False
        except discord.HTTPException as e:
            self.bot.logger.warning(f"Error al banear a {user_id}: {e}")
            return False

    @commands.hybrid_command(
        name="banearid",
        description="Banea al usuario configurado por ID."
    )
    @commands.guild_only()  # solo en servidores (no en DMs); sin restricción de permisos
    async def banearid(self, context: commands.Context) -> None:
        ok = await self.banear_por_id(
            context.guild,
            self.ID_A_BANEAR,
            f"Ban manual por ID solicitado por {context.author} ({context.author.id})"
        )
        if ok:
            await context.send(f"🔨 Usuario `{self.ID_A_BANEAR}` baneado correctamente.")
        else:
            await context.send("❌ No pude banearlo. Revisa mis permisos y la jerarquía de roles.")
    # ═══════════════════════════════════════════════════════════════
    # ⬆️ FIN DEL BLOQUE EXTRA ⬆️
    # ═══════════════════════════════════════════════════════════════


async def setup(bot) -> None:
    await bot.add_cog(Ban(bot))
