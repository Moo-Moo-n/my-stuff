import discord
from discord.ext import commands
from random import choice
from tools.utils import update_user_xp

class WesternDuel(commands.Cog):
    def __init__(self, bot, voice_time_cog, db_connection):
        self.bot = bot
        self.voice_time_cog = voice_time_cog
        self.db_connection = db_connection

    @commands.command()
    async def duel(self, ctx, opponent: discord.Member):
        if opponent.bot:
            await ctx.send("Bots cannot participate in duels.")
            return

        if opponent == ctx.author:
            await ctx.send("You cannot duel yourself.")
            return

        await ctx.send(f"{opponent.mention}, you've been challenged to a Western Duel by {ctx.author.mention}! Do you accept? (type 'yeehaw' or 'no')")

        def check(message):
            return message.author == opponent and message.content.lower() in ["yeehaw", "no"]

        try:
            message = await self.client.wait_for("message", check=check, timeout=60)
        except TimeoutError:
            await ctx.send(f"{opponent.mention} did not respond in time. Duel canceled.")
            return

        response = message.content.lower()
        if response == "no":
            await ctx.send(f"{opponent.mention} has declined the duel. Maybe next time!")
            return

        duelist = [ctx.author, opponent]
        winner = choice(duelist)

        if winner == ctx.author:
            xp_gain = 6
            xp_loss = -6
            await ctx.send(f"{winner.mention} has won the Western Duel against {opponent.mention}! {winner.mention} gains {xp_gain} minutes of XP.")
        else:
            xp_gain = -6
            xp_loss = 6
            await ctx.send(f"{winner.mention} has won the Western Duel against {ctx.author.mention}! {ctx.author.mention} loses {xp_loss} minutes of XP.")

        await update_user_xp(ctx.author.id, xp_gain, table_name="leveling", bot=self.client)
        await update_user_xp(opponent.id, xp_loss, table_name="leveling", bot=self.client)
        await update_user_xp(ctx.author.id, xp_gain, table_name="bpleveling", bot=self.client)
        await update_user_xp(opponent.id, xp_loss, table_name="bpleveling", bot=self.client)

def setup(client):
    client.add_cog(WesternDuel(client))
