import discord
from discord.ext import commands

excluded_commands = ["add", "setxp", "print_members", "givebp", "addbp"]


import discord
from discord.ext import commands

class CommandsList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def commands(self, ctx, cog_name: str = None):
        if cog_name is None:
            # List all cogs and their commands
            cogs = self.bot.cogs
            embed = discord.Embed(title="Available Cogs and Commands", color=discord.Color.blue())
            for cog_name, cog_object in cogs.items():
                command_names = [command.name for command in cog_object.get_commands()]
                command_list = ", ".join(command_names)
                embed.add_field(name=cog_name, value=command_list, inline=False)
            await ctx.send(embed=embed)
        else:
            # List commands for a specific cog
            cog = self.bot.get_cog(cog_name)
            if cog is not None:
                commands_list = cog.get_commands()
                command_names = [command.name for command in commands_list]
                command_list = ", ".join(command_names)
                embed = discord.Embed(title=f"Commands for {cog_name}", description=command_list, color=discord.Color.green())
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"No cog found with the name {cog_name}.")


def has_required_role(user):
    # Replace "Your Role Name" with the actual name of the role required to see the excluded commands
    required_role = discord.utils.get(user.guild.roles, name="admin")

    return required_role is not None and required_role in user.roles


def setup(bot):
    bot.add_cog(CommandsList(bot))
