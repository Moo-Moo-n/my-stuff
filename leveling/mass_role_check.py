import discord
from discord.ext import commands
import sqlite3
from roles_list import roles_list
from games.battlepass.bproles_list import bproles_list
from dotenv import load_dotenv
import os
import sys

sys.path.append("c:/Users/izzyf/OneDrive/Desktop/DiscordVCBot")
# Load the environment variables from .env file
load_dotenv()

# Retrieve the bot token from the environment variables
TOKEN = os.getenv("BOT_TOKEN")

# Initialize your bot and connect to the database

# Create a new intents object
intents = discord.Intents.all()

# Initialize your bot with the intents
bot = commands.Bot(command_prefix="!", intents=intents)
database_name = "your_database_name.db"
db_connection = sqlite3.connect(database_name)
db_cursor = db_connection.cursor()

# Command to perform the role check and assign roles
@bot.command()
@commands.has_permissions(administrator=True)
async def mass_role_check(ctx):
    guild = ctx.guild
    roles_to_assign = []

    for member in guild.members:
        user_id = str(member.id)
        for table_name in ["leveling", "bpleveling"]:
            query = f"SELECT xp FROM {table_name} WHERE user_id = ?"
            db_cursor.execute(query, (user_id,))
            result = db_cursor.fetchone()

            if result is not None:
                xp = result[0]
                xp_roles_list = roles_list if table_name == "leveling" else 'bproles_list'
                for role_data in xp_roles_list:
                    if xp >= role_data["xp_required"]:
                        role_name = role_data["name"]
                        role = discord.utils.get(guild.roles, name=role_name)
                        if role is not None:
                            roles_to_assign.append((member, role))
                        break

    for member, role in roles_to_assign:
        await member.add_roles(role)

    await ctx.send("Role check completed. Roles have been assigned.")

# Run the bot
@bot.event
async def on_ready():
    print(f"Bot is ready. Connected to {bot.user.name}")
    print("------")

bot.run(TOKEN)
