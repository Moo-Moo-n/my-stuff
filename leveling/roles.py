from discord.ext import commands
import discord
from .roles_list import roles_list
from games.battlepass.bproles_list import bproles_list

class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="roles")
    async def display_roles(self, ctx, role_type="regular"):
        if role_type == "bp":
            roles = bproles_list  # Battle Pass roles
        else:
            roles = roles_list  # Regular leveling roles

        guild = ctx.guild

        # Generate the table content
        table_content = ""
        for role_data in roles:
            level = role_data["level"]
            xp_required = role_data["xp_required"]
            name = role_data["name"]
            table_content += f"{level:2}  |  {xp_required:6}  |  {name}\n"

        # Create an embedded message with the table content
        if role_type == "bp":
            embed = discord.Embed(title="Battle Pass Role List", description=f"```\nLevel | XP Requirement | Name\n{table_content}```", color=discord.Color.blue())
        else:
            embed = discord.Embed(title="Regular Leveling Role List", description=f"```\nLevel | XP Requirement | Name\n{table_content}```", color=discord.Color.blue())

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Roles(bot))
