import discord
from discord.ext import commands
import sqlite3
import os
from tools.utils import calculate_level, get_user_role_by_level,get_user_xp, get_user_role_by_xp, get_level_xp, get_user_level, get_next_level_xp_threshold
from leveling.roles_list import roles_list
from .bproles_list import bproles_list
database_name = os.getenv("database_name")
db_connection = sqlite3.connect(database_name, check_same_thread=False, timeout=10)


class BattlePassCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_connection = sqlite3.connect("your_database_name.db")
        self.db_cursor = self.db_connection.cursor()

    @commands.command()
    async def givebp(self, ctx, recipient: discord.Member, xp: int):
        sender_id = str(ctx.author.id)
        recipient_id = str(recipient.id)
        sender_xp = get_user_xp(sender_id, "bpleveling")
        recipient_xp = get_user_xp(recipient_id, "bpleveling")

        if sender_xp < xp:
            await ctx.send("You do not have enough battle pass XP to give.")
            return

        updated_sender_xp = sender_xp - xp
        updated_recipient_xp = recipient_xp + xp

        conn = sqlite3.connect("your_database_name.db")
        cur = conn.cursor()

        try:
            cur.execute("UPDATE bpleveling SET xp = ? WHERE user_id = ?", (updated_sender_xp, sender_id))
            cur.execute("UPDATE bpleveling SET xp = ? WHERE user_id = ?", (updated_recipient_xp, recipient_id))
            conn.commit()

            await ctx.send(f"{ctx.author.mention} has given {recipient.mention} {xp} battle pass XP.")

            sender_new_xp = get_user_xp(sender_id, "bpleveling")
            recipient_new_xp = get_user_xp(recipient_id, "bpleveling")

            await ctx.send(f"{ctx.author.mention}, your new battle pass XP: {sender_new_xp}")
            await ctx.send(f"{recipient.mention}, your new battle pass XP: {recipient_new_xp}")
        except Exception as e:
            print(f"An error occurred while giving battle pass XP: {e}")

        cur.close()
        conn.close()

    @commands.command()
    async def addbp(self, ctx, xp: int, member: discord.Member = None):
        if member is None:
            member = ctx.author

        if xp <= 0:
            await ctx.send("Battle pass XP amount must be positive.")
            return

        member_id = str(member.id)
        member_xp = get_user_xp(member_id, "bpleveling")

        new_member_xp = member_xp + xp

        self.db_cursor.execute("UPDATE bpleveling SET xp = ? WHERE user_id = ?", (new_member_xp, member_id))
        self.db_connection.commit()

        await ctx.send(f"{ctx.author.mention} added {xp} battle pass XP to {member.mention}.")

    @commands.command()
    async def leaderboardbp(self, ctx):
        if ctx.guild is None:
            await ctx.send("This command can only be used within a server.")
            return

        query = "SELECT user_id, xp, level FROM bpleveling ORDER BY xp DESC LIMIT 10"
        self.db_cursor.execute(query)
        results = self.db_cursor.fetchall()

        if not results:
            await ctx.send("No users found.")
            return

        embed = discord.Embed(title="Battle Pass Leaderboard", color=discord.Color.blue())

        for index, row in enumerate(results):
            user_id, xp, level = row
            user = ctx.guild.get_member(user_id)
            if user:
                role = get_user_role_by_level(level, 'bpleveling')
                embed.add_field(name=f"Rank #{index + 1}", value=f"User: {user.display_name}\nRole: {role}\nLevel: {level}\nXP: {xp}", inline=index % 2 == 0)

        await ctx.send(embed=embed)

    @commands.command()
    async def createroles(self, ctx):
        guild = ctx.guild

        await self.create_roles(guild, bproles_list.items())


    async def create_roles(self, guild, roles_list):
        speaker_role = discord.utils.get(guild.roles, name="Speaker of the House")
        if speaker_role is None:
            # Handle if "Speaker of the House" role doesn't exist
            return

        for level, role_data in roles_list:
            role_name = role_data["name"]
            role_position = speaker_role.position - 1  # Position the role one position above "Speaker of the House"
            role = discord.utils.get(guild.roles, name=role_name)
            if role is None:
                role = await guild.create_role(name=role_name)
            await role.edit(position=role_position)


    @commands.command()
    async def setroles(self, ctx):
        guild = ctx.guild

        colors = [
            "#00081F",  # Deep Indigo
            "#0C1653",  # Midnight Blue
            "#1F377B",  # Royal Blue
            "#345EBD",  # Cobalt Blue
            "#5985FF",  # Sky Blue
            "#7DA2FF",  # Baby Blue
            "#A9C6FF",  # Pale Blue
            "#D4E5FF",  # Light Blue
            "#F4F9FF",  # Ice Blue
            "#FFEEEB",  # Soft Pink
            "#FFB7B2",  # Coral
            "#FF6560"   # Bright Red
        ]

        speaker_role = discord.utils.get(guild.roles, name="Speaker of the House")
        if speaker_role is None:
            # Handle if "Speaker of the House" role doesn't exist
            return

        for index, role_data in bproles_list.items():
            role_name = role_data["name"]
            role_position = speaker_role.position - 1  # Position the role one position above "Speaker of the House"
            role = discord.utils.get(guild.roles, name=role_name)
            if role is None:
                role = await guild.create_role(name=role_name, position=role_position)
            await role.edit(position=role_position, color=discord.Color(int(colors[index][1:], 16)))

        await ctx.send("Battle pass roles have been set.")


    @commands.command(name="levelbp")
    async def levelbp(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author

        user_id = str(member.id)

        current_xp = get_user_xp(user_id, "bpleveling", self.db_connection)

        current_level = calculate_level(current_xp, "bpleveling")  # Call the calculate_level function

        if current_level >= 0:
            next_level = current_level + 1

            role_name_current = get_user_role_by_level(current_level, "bpleveling")  # Call the get_user_role_by_level function from utils.py
            role_name_next = get_user_role_by_level(next_level, "bpleveling")

            xp_required_current_level = get_level_xp(current_level, "bpleveling")  # Pass "bpleveling" as xp_type
            xp_required_next_level = get_level_xp(next_level, "bpleveling")  # Pass "bpleveling" as xp_type

            xp_remaining = xp_required_next_level - current_xp

            hours_remaining = xp_remaining // 60
            minutes_remaining = xp_remaining % 60

            total_xp_hours = current_xp // 60
            total_xp_minutes = current_xp % 60
            total_xp_formatted = f"{total_xp_hours} hours {total_xp_minutes} minutes"

            time_remaining_formatted = f"{hours_remaining} hours {minutes_remaining} minutes"

            embed = discord.Embed(title="Battle Pass Level Information", color=discord.Color.blue())
            embed.set_author(name=member.display_name, icon_url=member.avatar.url)
            embed.add_field(name="Current XP (Total)", value=total_xp_formatted, inline=False)
            embed.add_field(name="Current XP (Raw)", value=str(current_xp), inline=False)
            embed.add_field(name=f"Current Level: {role_name_current}", value=current_level, inline=False)
            embed.add_field(name=f"Next Level: {role_name_next}", value=next_level, inline=False)
            embed.add_field(name="Time Remaining", value=time_remaining_formatted, inline=False)

            await ctx.send(embed=embed)
        else:
            await ctx.send("No user found with the given ID.")




def setup(bot, db_connection):
    # Register the BattlePassCommands cog
    battle_pass_commands = BattlePassCommands(bot)
    bot.add_cog(battle_pass_commands)

    # Add the individual commands to the bot
    bot.add_command(battle_pass_commands.givebp)
    bot.add_command(battle_pass_commands.addbp)
    bot.add_command(battle_pass_commands.leaderboardbp)
    bot.add_command(battle_pass_commands.createroles)
    bot.add_command(battle_pass_commands.setroles)
    bot.add_command(battle_pass_commands.levelbp)

    # Add more commands and cogs as needed

    print("All BPLeveling commands and cogs have been registered.")

