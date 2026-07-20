import discord
import asyncio
from discord.ext import commands

ROLES_PERMITIDOS = [
    1161138418860965949,
    # añade más IDs aquí
]

class Utility(commands.Cog, name="utility"):
    def __init__(self, bot) -> None:
        self.bot = bot

    def tiene_permiso(self, member: discord.Member) -> bool:
        roles_usuario = [role.id for role in member.roles]
        return any(rol in roles_usuario for rol in ROLES_PERMITIDOS)

    @commands.hybrid_command(
        name="1a",
        description="Envía 10 mensajes de $w con 10s de diferencia."
    )
    async def uno_a(self, context: commands.Context) -> None:
        if not self.tiene_permiso(context.author):
            await context.send("❌ No tienes permisos para usar este comando.", ephemeral=True)
            return

        await context.send("✅ Iniciando secuencia...", ephemeral=True)

        for i in range(10):
            await context.channel.send("$w")
            if i < 9:
                await asyncio.sleep(10)


async def setup(bot) -> None:
    await bot.add_cog(Utility(bot))