import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone, timedelta

USUARIOS_DM = [
    473316504239210507,
    1006400692551958670,
    410909681608032266,
]

GIF_URL = "https://klipy.com/gifs/1a-lex-luthor"
GMT_MINUS_4 = timezone(timedelta(hours=-4))


class Utility(commands.Cog, name="utility"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.scheduler.start()

    def cog_unload(self):
        self.scheduler.cancel()

    @tasks.loop(minutes=1)
    async def scheduler(self):
        ahora = datetime.now(GMT_MINUS_4)

        if ahora.minute != 30:
            return

        for user_id in USUARIOS_DM:
            try:
                user = await self.bot.fetch_user(user_id)
                await user.send(f"1a\n{GIF_URL}")
                self.bot.logger.info(f"DM enviado a {user} a las {ahora.strftime('%H:%M')} GMT-4")
            except discord.Forbidden:
                self.bot.logger.warning(f"No se pudo enviar DM a {user_id} (DMs cerrados)")
            except Exception as e:
                self.bot.logger.error(f"Error enviando DM a {user_id}: {e}")

    @scheduler.before_loop
    async def before_scheduler(self):
        await self.bot.wait_until_ready()


async def setup(bot) -> None:
    await bot.add_cog(Utility(bot))