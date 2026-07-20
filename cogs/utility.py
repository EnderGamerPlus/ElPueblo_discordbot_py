import discord
import asyncio
from discord.ext import commands, tasks
from datetime import datetime, timezone, timedelta

ROLES_PERMITIDOS = [
    1161138418860965949,
]

CANAL_ID = 1526037172203814972
ROL_ID = 1489322921452114122
GIF_URL = "https://klipy.com/gifs/1a-lex-luthor"
GMT_MINUS_4 = timezone(timedelta(hours=-4))


class Utility(commands.Cog, name="utility"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.ultimo_reclamo = None
        self.scheduler.start()

    def cog_unload(self):
        self.scheduler.cancel()

    def tiene_permiso(self, member: discord.Member) -> bool:
        roles_usuario = [role.id for role in member.roles]
        return any(rol in roles_usuario for rol in ROLES_PERMITIDOS)

    @tasks.loop(minutes=1)
    async def scheduler(self):
        ahora = datetime.now(GMT_MINUS_4)

        if ahora.minute != 30:
            return

        canal = self.bot.get_channel(CANAL_ID)
        if not canal:
            self.bot.logger.warning("No se encontró el canal de anuncios")
            return

        hora = ahora.hour

        # ── Reclamos cada 3h ────────────────────────────────────────
        if hora % 3 == 0:
            clave = f"{ahora.date()}-{hora}"
            if self.ultimo_reclamo != clave:
                self.ultimo_reclamo = clave
                await canal.send(
                    f"Reclamos reiniciados\n<@&{ROL_ID}>\n{GIF_URL}",
                    allowed_mentions=discord.AllowedMentions(roles=True)
                )
                self.bot.logger.info(
                    f"Reclamos enviado a las {ahora.strftime('%H:%M')} GMT-4")
            return

        # ── Rolls cada hora ─────────────────────────────────────────
        await canal.send(
            f"<@&{ROL_ID}>\n{GIF_URL}",
            allowed_mentions=discord.AllowedMentions(roles=True)
        )
        self.bot.logger.info(
            f"Rolls enviado a las {ahora.strftime('%H:%M')} GMT-4")

    @scheduler.before_loop
    async def before_scheduler(self):
        await self.bot.wait_until_ready()


async def setup(bot) -> None:
    await bot.add_cog(Utility(bot))
