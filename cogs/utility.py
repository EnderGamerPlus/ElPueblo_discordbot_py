import discord
import asyncio
from discord.ext import commands
from discord.ext import tasks
from datetime import datetime, timezone, timedelta

ROLES_PERMITIDOS = [
    1161138418860965949,
]

CANAL_ID = 1526037172203814972
ROL_ID = 1467236589192347668
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

        # Solo actuar cuando el minuto sea :30
        if ahora.minute != 30:
            return

        canal = self.bot.get_channel(CANAL_ID)
        if not canal:
            return

        hora = ahora.hour

        # ── Reclamos cada 3h (horas: 0, 3, 6, 9, 12, 15, 18, 21) ──
        if hora % 3 == 0:
            # Evitar mandar dos veces en el mismo :30
            clave = f"{ahora.date()}-{hora}"
            if self.ultimo_reclamo != clave:
                self.ultimo_reclamo = clave
                await canal.send(
                    f"Reclamos reiniciados\na <@&{ROL_ID}>\n{GIF_URL}"
                )
                self.bot.logger.info(
                    f"Mensaje de reclamos enviado a las {ahora.strftime('%H:%M')} GMT-4")
            return

        # ── Rolls cada hora ─────────────────────────────────────────
        await canal.send(
            f"1a <@&{ROL_ID}>\n{GIF_URL}"
        )
        self.bot.logger.info(
            f"Mensaje de rolls enviado a las {ahora.strftime('%H:%M')} GMT-4")

    @scheduler.before_loop
    async def before_scheduler(self):
        await self.bot.wait_until_ready()

    def tiene_permiso(self, member: discord.Member) -> bool:
        roles_usuario = [role.id for role in member.roles]
        return any(rol in roles_usuario for rol in ROLES_PERMITIDOS)


async def setup(bot) -> None:
    await bot.add_cog(Utility(bot))
