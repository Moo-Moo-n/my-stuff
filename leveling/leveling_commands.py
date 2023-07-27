import sqlite3
import datetime
import traceback
import discord
from discord.ext import commands
from .voice_time_cog import VoiceTimeCog
from tools.utils import get_user_role_by_level,calculate_level,update_user_level, get_level_xp, get_user_level, get_user_xp, get_user_role_by_xp, set_user_level, update_user_xp
from leveling.roles_list import roles_list
import csv
from games.battlepass.bproles_list import bproles_list
from typing import Optional


database_name = 'your_database_name.db'
audit_log_channel_id = 1114398557651353610

class LevelingCommands(commands.Cog):
    def __init__(self, bot, db_connection):
        self.bot = bot
        self.db_connection = db_connection
        self.db_cursor = self.db_connection.cursor()
        self.guild = None

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def role_check_all(self, ctx):
        guild = ctx.guild

        for member in guild.members:
            user_id = str(member.id)

            # Get the level of the user
            level = await get_user_level(user_id, 'leveling', self.db_connection)

            # Get the role for the user's level
            role_data = get_user_role_by_level(level, 'leveling')

            if role_data is not None:
                role_id = role_data["role_id"]
                role = discord.utils.get(guild.roles, id=role_id)

                if role is not None:
                    # Add the role to the member
                    await member.add_roles(role)

        await ctx.send("Role check completed. Roles have been assigned.")

    
    @commands.command()
    async def checklevel(self, ctx, member: Optional[discord.Member] = None):
        if member is None:
            member = ctx.author

        user_id = str(member.id)
        xp_bpleveling = await get_user_xp(user_id, "bpleveling", self.db_connection)
        xp_leveling = await get_user_xp(user_id, "leveling", self.db_connection)
        current_bplevel = await get_user_level(user_id, "bpleveling", self.db_connection)
        current_level = await get_user_level(user_id, "leveling", self.db_connection)

        # Batch update for bpleveling
        for level, xp_required in reversed(bproles_list.items()):
            if xp_bpleveling >= xp_required['xp_required']:  # Access the XP value using 'xp_required' key
                if level > await get_user_level(user_id, "bpleveling", self.db_connection):
                    await update_user_level(user_id, "bpleveling", self.db_connection)

        # Batch update for leveling
        for level, xp_required in reversed(roles_list.items()):
            if xp_leveling >= xp_required['xp_required']:  # Access the XP value using 'xp_required' key
                if level > await get_user_level(user_id, "leveling", self.db_connection):
                    await update_user_level(user_id, "leveling", self.db_connection)

        await ctx.send(f"Level check complete for {member.name}. Levels updated if necessary.")

    
    @commands.command()
    async def give(self, ctx, recipient: discord.Member, xp: int):
        sender_id = str(ctx.author.id)
        recipient_id = str(recipient.id)
        sender_xp = get_user_xp(sender_id)
        recipient_xp = get_user_xp(recipient_id)

        if sender_xp < xp:
            await ctx.send("You do not have enough XP to give.")
            return

        updated_sender_xp = sender_xp - xp
        updated_recipient_xp = recipient_xp + xp

        conn = sqlite3.connect(database_name)
        cur = conn.cursor()

        try:
            cur.execute("UPDATE leveling SET xp = ? WHERE user_id = ?", (updated_sender_xp, sender_id))
            cur.execute("UPDATE leveling SET xp = ? WHERE user_id = ?", (updated_recipient_xp, recipient_id))
            conn.commit()

            await ctx.send(f"{ctx.author.mention} has given {recipient.mention} {xp} XP.")

            sender_new_xp = get_user_xp(sender_id)
            recipient_new_xp = get_user_xp(recipient_id)

            await ctx.send(f"{ctx.author.mention}, your new XP: {sender_new_xp}")
            await ctx.send(f"{recipient.mention}, your new XP: {recipient_new_xp}")
        except Exception as e:
            print(f"An error occurred while giving XP: {e}")

        cur.close()
        conn.close()


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def add(self, ctx, xp: int, member: discord.Member = None):
        if member is None:
            member = ctx.author

        if xp <= 0:
            await ctx.send("XP amount must be positive.")
            return

        member_id = str(member.id)
        member_xp = await get_user_xp(member_id, 'leveling',self.db_connection)

        new_member_xp = member_xp + xp

        self.db_cursor.execute("UPDATE leveling SET xp = ? WHERE user_id = ?", (new_member_xp, member_id))
        self.db_connection.commit()

        await ctx.send(f"{ctx.author.mention} added {xp} XP to {member.mention}.")

    async def update_all_user_levels(self, table_name):
        conn = sqlite3.connect(database_name)
        cur = conn.cursor()

        # Fetch all user IDs and XP from the specified table
        query = f"SELECT user_id, xp FROM {table_name}"
        cur.execute(query)
        rows = cur.fetchall()

        # Update the level for each user
        for user_id, xp in rows:
            current_level = await calculate_level(xp, table_name)

            # Check if the level is None in the row and update it to 0
            if current_level is None:
                set_user_level(user_id, 0, table_name, conn)
            else:
                set_user_level(user_id, current_level, table_name, conn)

        cur.close()
        conn.close()
        print(f"All user levels have been updated for {table_name}.")

    # Rest of your code ...

    @commands.command()
    @commands.is_owner()  # Only the bot owner can use this command
    async def update_levels(self, ctx):
        await ctx.send("Updating user levels for all users (leveling)...")
        await self.update_all_user_levels("leveling")
        await ctx.send("All user levels have been updated for leveling.")

        await ctx.send("Updating user levels for all users (bpleveling)...")
        await self.update_all_user_levels("bpleveling")
        await ctx.send("All user levels have been updated for bpleveling.")
        
    @commands.command()
    async def leaderboard(self, ctx):
        if ctx.guild is None:
            await ctx.send("This command can only be used within a server.")
            return

        query = "SELECT user_id, xp, level FROM leveling ORDER BY xp DESC LIMIT 10"
        self.db_cursor.execute(query)
        results = self.db_cursor.fetchall()

        if not results:
            await ctx.send("No leveling found.")
            return

        embed = discord.Embed(title="Leaderboard", color=discord.Color.blue())

        for index, row in enumerate(results):
            user_id, xp, level = row
            user = ctx.guild.get_member(user_id)
            level = get_user_level(user_id,'leveling',self.db_connection)
            if user:
                role = get_user_role_by_level(level, 'leveling')
                embed.add_field(name=f"Rank #{index + 1}", value=f"User: {user.display_name}\nRole: {role}\nLevel: {level}\nXP: {xp}", inline=index % 2 == 0)

        await ctx.send(embed=embed)


    @commands.command()
    async def level(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author

        user_id = str(member.id)

        current_xp = await get_user_xp(user_id, "leveling", self.db_connection)

        current_level = await calculate_level(current_xp, "leveling")  # Call the calculate_level function

        if current_level > 0:
            next_level = current_level + 1

            role_name_current = await get_user_role_by_xp(current_xp, "leveling")  # Call the get_user_role_by_xp function from utils.py
            role_name_next = await get_user_role_by_xp(get_level_xp(next_level, "leveling"), "leveling")

            xp_required_current_level = get_level_xp(current_level, "leveling")  # Pass "leveling" as xp_type
            xp_required_next_level = get_level_xp(next_level, "leveling")  # Pass "leveling" as xp_type

            xp_remaining = xp_required_next_level - current_xp

            hours_remaining = xp_remaining // 60
            minutes_remaining = xp_remaining % 60

            total_xp_hours = current_xp // 60
            total_xp_minutes = current_xp % 60
            total_xp_formatted = f"{total_xp_hours} hours {total_xp_minutes} minutes"

            time_remaining_formatted = f"{hours_remaining} hours {minutes_remaining} minutes"

            # Your existing embed code
            embed = discord.Embed(title="Level Information", color=discord.Color.blue())
            embed.set_author(name=member.display_name, icon_url=member.avatar.url)
            embed.add_field(name="Current XP (Total)", value=total_xp_formatted, inline=False)
            embed.add_field(name="Current XP (Raw)", value=str(current_xp), inline=False)
            embed.add_field(name=f"Current Level: {role_name_current}", value=current_level, inline=False)
            embed.add_field(name=f"Next Level: {role_name_next}", value=next_level, inline=False)
            embed.add_field(name="Time Remaining", value=time_remaining_formatted, inline=False)

            await ctx.send(embed=embed)
        else:
            await ctx.send("No user found with the given ID.")



          
    @commands.command()
    @commands.has_permissions(administrator=True)    
    async def setxp(self, ctx, member: discord.Member, xp: int):
        conn = sqlite3.connect(database_name)
        cur = conn.cursor()

        try:
            cur.execute("SELECT level FROM leveling WHERE user_id = ?", (member.id,))
            result = cur.fetchone()
            if result:
                current_level = await update_user_level(member.id, 'leveling', self.db_connection)  # Call the update_user_level function from utils.py
                cur.execute("UPDATE leveling SET xp = ?, level = ? WHERE user_id = ?", (xp, current_level, member.id))
                conn.commit()
                await ctx.send(f"Successfully set XP for {member.display_name}. New XP: {xp}, Level: {current_level}")
            else:
                await ctx.send(f"No user found with the given ID: {member.id}")
        except Exception as e:
            traceback.print_exc()
            await ctx.send(f"An error occurred while setting XP: {e}")
        cur.close()


    @commands.command()
    async def print_members(self, ctx):
        guild = ctx.guild
        members = guild.members

        member_list = []
        for member in members:
            member_list.append({"ID": member.id, "Name": member.name})

        if member_list:
            file_path = "member_list.csv"

            with open(file_path, "w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=["ID", "Name"])
                writer.writeheader()
                writer.writerows(member_list)

            await ctx.send(file=discord.File(file_path))
        else:
            await ctx.send("No members found in the guild.")

    
    @commands.command()
    async def voicetime(self, ctx):
        member = ctx.author
        user_id = member.id

        conn = sqlite3.connect(database_name)
        cur = conn.cursor()

        try:
            cur.execute("SELECT start_time FROM voice_time WHERE user_id = ? ORDER BY start_time DESC LIMIT 1",
                        (user_id,))
            result = cur.fetchone()

            if result:
                start_time = datetime.datetime.fromisoformat(result[0])
                current_time = datetime.datetime.now()
                duration = current_time - start_time

                if duration.total_seconds() < 60:
                    seconds = int(duration.total_seconds())
                    response = f"Your current voice time: {seconds} seconds\n"
                    response += "XP gained if you left now: 0 XP"  # No XP gained in seconds
                else:
                    minutes = int(duration.total_seconds() // 60)
                    xp_per_minute = 1  # Replace with your desired XP rate per minute
                    xp_gained = minutes * xp_per_minute

                    response = f"Your current voice time: {minutes} minutes\n"
                    response += f"XP gained if you left now: {xp_gained} XP"
            else:
                response = "No voice time recorded for you."

            await ctx.send(response)
        except Exception as e:
            traceback.print_exc()
            await ctx.send(f"An error occurred while fetching voice time: {e}")

        cur.close()
        conn.close()

def setup(bot, db_connection):
    leveling_commands = LevelingCommands(bot, db_connection)
    bot.add_cog(leveling_commands)

    # Registering multiple commands
    bot.add_command(leveling_commands.level)
    bot.add_command(leveling_commands.rank)
    bot.add_command(leveling_commands.leaderboard)
    # Add more commands here

    # Register other cogs and commands as needed
    voice_time_cog = VoiceTimeCog(bot, db_connection)
    bot.add_cog(voice_time_cog)
    bot.add_command(voice_time_cog.voice_time)

    # Add more cogs and commands here

    print("All Leveling commands and cogs have been registered.")