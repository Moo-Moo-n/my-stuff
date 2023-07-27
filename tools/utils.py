import discord
import sqlite3
import traceback
from leveling.roles_list import roles_list
import os
import aiosqlite
import datetime
from games.battlepass.bproles_list import bproles_list
  # Get database name from .env file
audit_log_channel_id = 1114398557651353610  # Get audit log channel ID from .env file
intents = discord.Intents.all()
bot = discord.Client(intents=intents)
GUILD_ID = 938986918446788639

async def send_level_up_message(audit_log_channel_id, message, level, member):
    # Concatenate the level information with the message
    level_message = f"Level: {level}"
    message_with_level = f"{message} {level_message}"
    channel = discord.utils.get(member.guild.channels, name="audit_log")  # Replace "audit_log" with the desired channel name
    try:
        await channel.send(message_with_level)
    except Exception as e:
        traceback.print_exc()
        print(f"Failed to send a message to the channel '{channel.name}': {e}")

def get_user_role_by_level(level, table_name):
    level_list = bproles_list if table_name == "bpleveling" else roles_list

    if 0 <= level < len(level_list):
        return level_list[level]["name"]

    return None


async def is_member_in_table(user_id, table_name):
    async with aiosqlite.connect('your_database_name.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(f"SELECT * FROM {table_name} WHERE user_id=?", (user_id,))
            result = await cursor.fetchone()

            if result:
                # Member already exists in the table
                print(f'Member {user_id} already exists in {table_name}.')
                return True
            else:
                # Member not found in the table, insert them
                await cursor.execute(f"INSERT INTO {table_name} (user_id) VALUES (?)", (user_id,))
                await conn.commit()
                print(f'Member {user_id} has been successfully inserted into {table_name}.')
                return False

# The rest of the functions remain the same, but you should remove the "async" keyword since they are now synchronous functions.
    
async def get_user_level(user_id, table_name, db_connection):
    query = f"SELECT level FROM {table_name} WHERE user_id = ?"
    with db_connection:
        db_cursor = db_connection.cursor()
        db_cursor.execute(query, (user_id,))
        result = db_cursor.fetchone()

        if result:
            selected_level = result[0]
            print(f"Selected level for user ID {user_id}: {selected_level}")
            return selected_level
        else:
            print(f"No level found for user ID {user_id} in table '{table_name}'")
            await is_member_in_table(user_id, table_name)  # Insert the member into the table
            return 0  # Return 0 as the default level when not found




async def calculate_and_apply_level(user_id, table_name, db_connection, bot):
    # Get the XP for the user
    xp = await get_user_xp(user_id, table_name, db_connection)

    # Calculate the new level based on the XP and table_name
    new_level = await calculate_level(xp, table_name)

    # Update user level in the database
    query = f"UPDATE {table_name} SET level = ? WHERE user_id = ?"
    with db_connection:
        db_cursor = db_connection.cursor()
        db_cursor.execute(query, (new_level, user_id))

    print(f"Updated user {user_id} level to {new_level} in {table_name} table.")
    return new_level


async def get_user_role_by_xp(xp, table_name):
    level_list = bproles_list if table_name == "bpleveling" else roles_list

    current_level = await calculate_level(xp, table_name)
    role = level_list[current_level]["name"] if 0 <= current_level < len(level_list) else None

    print(f"Role returned for level {current_level}: {role}")
    return role

async def calculate_level(xp, table_name):
    level_list = bproles_list if table_name == "bpleveling" else roles_list

    print("Table Name:", table_name)  # Add this line to check the table_name
    print("XP:", xp)  # Add this line to check the xp value
    # Determine the level based on the XP
    level = 0
    while level + 1 < len(level_list):
        xp_required = level_list[level + 1]["xp_required"]
        if xp >= xp_required:
            level += 1
        else:
            break
    print("Level:", level)
    return level

def set_user_level(user_id, level, table_name, db_connection):
    query = f"UPDATE {table_name} SET level = ? WHERE user_id = ?"
    with db_connection:
        db_cursor = db_connection.cursor()
        db_cursor.execute(query, (level, user_id))

    print(f"Updated user {user_id} level to {level} in {table_name} table.")
    return level

def calculate_next_level(xp, table_name):
    if table_name == "bp" or table_name == "battlepass":
        xp_required_dict = bproles_list
    else:
        xp_required_dict = roles_list

    for level, xp_required in xp_required_dict.items():
        if xp < xp_required:
            return level - 1


def get_next_level_xp_threshold(level, xp_type):
    if xp_type == "bp" or xp_type == "battlepass":
        xp_required_dict = bproles_list
    else:
        xp_required_dict = roles_list

    if level + 1 in xp_required_dict:
        return xp_required_dict[level + 1]
    else:
        return float('inf')  # Return infinity if the next level is not defined


async def check_role_assignment(member, user_id, guild, db_connection):
    roles_to_assign = []  # List of roles to assign to the member

    # Check the user's level and assign roles accordingly
    leveling_roles = {
        role["level"]: guild.get_role(role["role_id"]) for role in roles_list
    }

    level = await get_user_level(user_id, "leveling", db_connection)  # Get the user's level
    if level is not None and level in leveling_roles:
        role = leveling_roles[level]
        roles_to_assign.append(role)

    # Check the user's battle pass level and assign roles accordingly
    bpleveling_roles = {
        role["level"]: guild.get_role(role["role_id"]) for role in bproles_list
    }

    bplevel = await get_user_level(user_id, "bpleveling", db_connection)  # Get the user's battle pass level
    if bplevel is not None and bplevel in bpleveling_roles:
        role = bpleveling_roles[bplevel]
        roles_to_assign.append(role)

    # Assign the roles to the member
    if roles_to_assign:
        await member.add_roles(*roles_to_assign)
        print(f"Assigned roles {roles_to_assign} to user {member.display_name} ({member.id}).")
    else:
        print(f"No roles to assign to user {member.display_name} ({member.id}).")


async def get_user_xp(user_id, table_name, db_connection):
    query = f"SELECT xp FROM {table_name} WHERE user_id = ?;"

    async with aiosqlite.connect('your_database_name.db') as conn:
        cursor = await conn.execute(query, (user_id,))
        result = await cursor.fetchone()

    if result is not None and result[0] is not None:
        xp = int(result[0])
        print(f"Retrieved {table_name} XP for user ID {user_id}: {xp}")
        return xp
    else:
        print(f"{table_name} XP not found for user ID {user_id}. Query: {query}")
        return 0


def get_level_xp(level, table_name):
    level_list = bproles_list if table_name == "bpleveling" else roles_list

    if 0 <= level < len(level_list):
        return level_list[level]["xp_required"]

    return 0


async def update_user_level(user_id, table_name, db_connection):
    # Fetch the user's old level from the database
    old_level = int(await get_user_level(user_id, table_name, db_connection))

    # Fetch the user's XP from the database
    xp = int(await get_user_xp(user_id, table_name, db_connection))

    # Calculate the new level based on the XP and table_name
    new_level = int(await calculate_level(xp, table_name))

    if new_level > old_level:
        # Update user level in the database
        query = f"UPDATE {table_name} SET level = ? WHERE user_id = ?"
        with db_connection:
            db_cursor = db_connection.cursor()
            db_cursor.execute(query, (new_level, user_id))

        print(f"Updated user {user_id} level from {old_level} to {new_level} in {table_name} table.")
    else:
        print(f"User {user_id} has not advanced to a new level in {table_name} table.")

    return new_level



import aiosqlite
from tools.utils import get_user_xp

async def update_user_xp(user_id, xp_earned, table_name, db_connection, bot):
    current_xp = await get_user_xp(user_id, table_name, db_connection)
    current_bp_xp = await get_user_xp(user_id, 'bpleveling', db_connection)

    # Ensure the XP values are integers
    current_xp = int(current_xp)
    current_bp_xp = int(current_bp_xp)
    xp_earned = int(xp_earned)

    new_xp = current_xp + xp_earned
    new_bp_xp = current_bp_xp + xp_earned

    async with aiosqlite.connect('your_database_name.db') as conn:
        # Update XP in the table
        await conn.execute(f"UPDATE {table_name} SET xp = ? WHERE user_id = ?", (str(new_xp), user_id))
        await conn.commit()

    try:
        # Get the username for the user_id
        user = bot.get_user(user_id)
        username = user.name if user else f"Unknown User (ID: {user_id})"

        # Call update_user_level to update the level in bproles_list and roles_list
        await update_user_level(user_id, 'leveling', db_connection)
        await update_user_level(user_id, 'bpleveling', db_connection)

        current_level = await calculate_level(new_xp, 'leveling')
        current_bp_level = await calculate_level(new_bp_xp, 'bpleveling')

        next_level_threshold = get_next_level_xp_threshold(current_level, 'leveling')
        next_bp_level_threshold = get_next_level_xp_threshold(current_bp_level, 'bpleveling')
        users_embed = discord.Embed(title=f"{table_name} XP Added to {username}", color=discord.Color.green())

        if table_name == 'bpleveling':
            users_embed.add_field(name="Old BP XP", value=int(current_bp_xp))
            users_embed.add_field(name="XP Earned", value=int(xp_earned))
            users_embed.add_field(name="New Total BP XP", value=int(new_bp_xp))
            users_embed.add_field(name="Next BP Level Threshold", value=next_bp_level_threshold["xp_required"])  # Access the XP amount
        else:  # Assume leveling table if not 'bpleveling'
            users_embed.add_field(name="Old XP", value=int(current_xp))
            users_embed.add_field(name="XP Earned", value=int(xp_earned))
            users_embed.add_field(name="New Total XP", value=int(new_xp))
            users_embed.add_field(name="Next Level Threshold", value=next_level_threshold["xp_required"])  # Access the XP amount

        # Get the audit log channel
        audit_log_channel = await bot.fetch_channel(audit_log_channel_id)
        if audit_log_channel:
            await audit_log_channel.send(embed=users_embed)

    except Exception as e:
        print(f"Error updating {table_name} XP for user ID {user_id}: {e}")






