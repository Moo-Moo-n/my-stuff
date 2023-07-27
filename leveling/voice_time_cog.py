import os
import sqlite3
from datetime import datetime
import discord
from tools.utils import update_user_xp, is_member_in_table, get_user_xp
from discord.ext import commands
from dotenv import load_dotenv
import time
import aiosqlite
load_dotenv()
database_name = os.getenv("database_name")
audit_log_channel_id = os.getenv("AUDIT_LOG_CHANNEL_ID")

class VoiceTimeCog(commands.Cog):
    def __init__(self, bot, db_connection):
        self.bot = bot
        self.db_connection = db_connection
        self.db_cursor = db_connection.cursor()
        self.processed_users = set()  # Add this line to initialize the set

    # ... (Other functions and setup)

    async def initialize_db(self):
        self.db_connection = await aiosqlite.connect('your_database_name.db')
        print('Database connection established.')

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return

        if before.channel != after.channel:
            if after.channel is not None:  # Joined a voice channel
                await self.handle_voice_join(member, after)
            else:  # Left a voice channel
                await self.handle_voice_leave(member, before.channel)
                
    async def create_audit_log_embed(self, member, channel, action):
        embed = discord.Embed(title=f"Voice Channel {action}", color=discord.Color.blurple())
        embed.add_field(name="Member", value=member.mention, inline=False)
        embed.add_field(name="Channel", value=channel.name, inline=False)
        embed.timestamp = discord.utils.utcnow()
        return embed
    
    async def handle_voice_join(self, member, after):
        user_id = member.id
        start_time = datetime.now()

        print(f"User ID: {user_id}")
        print(f"Username: {member.display_name}")
        print(f"Start time: {start_time}")

        # Fetch the audit log channel
        audit_log_channel = await self.bot.fetch_channel(audit_log_channel_id)

        # Create an audit log embed for voice join
        embed = await self.create_audit_log_embed(member, after.channel, "Join")
        if isinstance(audit_log_channel, discord.TextChannel) and audit_log_channel.permissions_for(member.guild.me).send_messages:
            await audit_log_channel.send(embed=embed)
        else:
            print("Error: Audit log channel not found or is not a text channel.")

        print("attempting to create_voice_time")
        # Create or update voice_time table with start_time
        await self.create_voice_time(member, start_time, table_name='voice_time')

    async def create_voice_time(self, member, start_time, table_name='voice_time'):
        user_id = member.id

        async with aiosqlite.connect('your_database_name.db') as conn:
            cursor = await conn.cursor()

            # Check if member is already in the table
            if await is_member_in_table(user_id, table_name):
                # Convert start_time to a string if it's an integer
                if isinstance(start_time, int):
                    start_time = datetime.utcfromtimestamp(start_time).strftime("%Y-%m-%d %H:%M:%S.%f")

                query = f"UPDATE {table_name} SET start_time = ? WHERE user_id = ?"
                await cursor.execute(query, (start_time, user_id))
                await conn.commit()  # Commit the transaction after update
                print(f"Member {user_id}'s start_time has been updated in {table_name} to: {start_time}.")

        # Rest of your code for sending audit log and other checks
                
    async def get_voice_session_start_time(self, user_id):
        query = "SELECT start_time FROM voice_time WHERE user_id = ?"

        async with aiosqlite.connect('your_database_name.db') as conn:
            cursor = await conn.cursor()
            await cursor.execute(query, (user_id,))
            result = await cursor.fetchone()

            print(f"Database result for user ID {user_id}: {result}")

            if result is not None and result[0] is not None:
                start_time = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S.%f")
                print(f"Start time for user ID {user_id}: {start_time}")
                return start_time
            else:
                # If the start time is None or not found, check if the user is in the voice_time table without a specific start_time
                query = "SELECT start_time FROM voice_time WHERE user_id = ?"
                await cursor.execute(query, (user_id,))
                result = await cursor.fetchone()

                if result is not None and result[0] is not None:
                    start_time = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S.%f")
                    print(f"Start time (without specific start_time) for user ID {user_id}: {start_time}")
                    return start_time
                else:
                    print(f"Start time not found for user ID {user_id}.")
                    return None


    async def handle_voice_leave(self, member, channel):
        user_id = member.id
        start_time = await self.get_voice_session_start_time(user_id)

        if start_time is not None:
            end_time = datetime.now()
            duration = end_time - start_time

            # Convert the duration to minutes
            xp_gained = int(duration.total_seconds() // 60)  # Use regular division to get minutes

            old_user_xp = await get_user_xp(user_id, 'leveling', self.db_connection)
            old_user_bpxp = await get_user_xp(user_id, 'bpleveling', self.db_connection)

            formatted_start_time = start_time.strftime("%Y-%m-%d %H:%M:%S")
            formatted_end_time = end_time.strftime("%Y-%m-%d %H:%M:%S")

            try:
                await update_user_xp(user_id, xp_gained, 'leveling', self.db_connection, self.bot)
                await update_user_xp(user_id, xp_gained, 'bpleveling', self.db_connection, self.bot)
                await self.delete_voice_time(user_id)

            except Exception as e:
                print(f"Error updating XP for user ID {user_id}: {e}")

            # ... (Rest of the code for handling voice leave)

            # Create an audit log embed for voice leave
            leave_embed = await self.create_audit_log_embed(member, channel, "Left")
            leave_embed.add_field(name="Start Time", value=formatted_start_time, inline=False)
            leave_embed.add_field(name="End Time", value=formatted_end_time, inline=False)
            leave_embed.add_field(name="Duration", value=str(duration), inline=False)
            leave_embed.add_field(name="XP Gained", value=int(xp_gained))

            audit_log_channel = await self.bot.fetch_channel(audit_log_channel_id)

            if audit_log_channel is not None and isinstance(audit_log_channel, discord.TextChannel):
                await audit_log_channel.send(embed=leave_embed)
            else:
                print("Error: Audit log channel not found or is not a text channel.")

            print(f"User ID {user_id} gained {xp_gained} XP from voice activity.")
        else:
            print(f"Error: No start time found for user ID {user_id}.")

    async def delete_voice_time(self, user_id):
        query = "UPDATE voice_time SET start_time = NULL, end_time = NULL WHERE user_id = ?"
        
        async with aiosqlite.connect('your_database_name.db') as conn:
            cursor = await conn.cursor()
            await cursor.execute(query, (user_id,))
            await conn.commit()
        
        print(f"Deleted voice time record for member {user_id}.")


    def cog_unload(self):
        if self.db_connection:
            self.bot.loop.create_task(self.db_connection.close())
            print('Database connection closed.')
    
    def save_daily_logs(self):
        # Get the current date
        current_date = datetime.now().date()

        # Retrieve leveling and bpleveling XP and levels for all users
        leveling_data = self.retrieve_user_data("leveling")
        bpleveling_data = self.retrieve_user_data("bpleveling")

        # Save the leveling and bpleveling data to the daily log file
        with open(f"leveling_log_{current_date}.txt", "w") as file:
            file.write("Leveling Data:\n")
            for user_id, xp, level in leveling_data:
                file.write(f"User ID: {user_id}, XP: {xp}, Level: {level}\n")

            file.write("\nBpleveling Data:\n")
            for user_id, xp, level in bpleveling_data:
                file.write(f"User ID: {user_id}, XP: {xp}, Level: {level}\n")

    def retrieve_user_data(self, table_name):
        table_name = 'voice_time'
        conn = sqlite3.connect(database_name)
        cur = conn.cursor()
        query = f"SELECT user_id, xp, level FROM {table_name}"
        cur.execute(query)
        result = cur.fetchall()
        cur.close()
        conn.close()
        return result

def setup(bot, db_connection):
    voice_time_cog = VoiceTimeCog(bot, db_connection)
    bot.add_cog(voice_time_cog)
    print("VoiceTimeCog setup.")
