import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import sqlite3
from leveling.voice_time_cog import VoiceTimeCog
from leveling.leveling_commands import LevelingCommands
from leveling.roles import Roles
from leveling.voice_time_cog import setup
from games.western_duel.WesternDuel import WesternDuel
from games.mugging_system.mugging_system import MuggingSystem
from games.fishing.fishingcmds import Fishing
from tools.commands_list import CommandsList
from games.battlepass.bpcmds import BattlePassCommands
from games.farming.crops_commands import CropsCommands
from games.farming.crops_utils import ensure_crops_table_initialized
# Load environment variables from .env file
load_dotenv()

intents = discord.Intents.all()
intents.voice_states = True
bot = commands.Bot(command_prefix='!', intents=intents)
db_connection = sqlite3.connect(os.getenv('database_name'))
from sqlite3 import Connection
database_name = os.getenv('database_name')
# Create a global variable to hold the database connection
db_connection: Connection = None

def create_connection_pool(database_name):
    global db_connection
    db_connection = sqlite3.connect(database_name)
    db_connection.row_factory = sqlite3.Row

# Call this function when the bot starts
create_connection_pool(os.getenv('database_name'))


# Event handler for when the bot is ready
@bot.event
async def on_ready():
    print('Connected to the following servers:')
    for guild in bot.guilds:
        print(f'- {guild.name} (ID: {guild.id})')
    total_members = sum(len(guild.members) for guild in bot.guilds)
    print(f'Total members: {total_members}')
    
    voice_time_cog = VoiceTimeCog(bot, db_connection)
    await bot.add_cog(voice_time_cog)
    print('VoiceTimeCog cog added.')    

    
    leveling_commands_cog = LevelingCommands(bot, db_connection)
    await bot.add_cog(leveling_commands_cog)
    print('LevelingCommands cog added.')

    roles_cog = Roles(bot)
    await bot.add_cog(roles_cog)
    print('Roles cog added.')

    western_duel_cog = WesternDuel(bot, voice_time_cog, db_connection)
    await bot.add_cog(western_duel_cog)
    print('WesternDuel cog added.')

    mugging_system_cog = MuggingSystem(bot, db_connection)
    await bot.add_cog(mugging_system_cog)
    print('MuggingSystem cog added.')

    fishing_cog = Fishing(bot)
    await bot.add_cog(fishing_cog)
    print('FishingCog cog added.')
    
    # Add the CropsCommands cog
    #cursor = db_connection.cursor()  # Replace this with your actual database connection
    #crops_commands_cog = CropsCommands(bot, cursor)  # Pass the bot instance to the cog
    #await bot.add_cog(crops_commands_cog)
    #print('Farming Commands cog added.')  
    
    create_connection_pool('your_database_name.db')   

    battle_pass_commands_cog = BattlePassCommands(bot)
    await bot.add_cog(battle_pass_commands_cog)
    print('BattlePassCommands cog added.')

    commands_list_cog = CommandsList(bot)
    await bot.add_cog(commands_list_cog)
    print('CommandsList cog added.')

    print('Bot is ready.')


# Run the bot
bot_token = os.getenv('BOT_TOKEN')
bot.run(bot_token)
