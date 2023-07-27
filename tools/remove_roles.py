import discord
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))

roles_to_remove = [
    {"name": "The Grand Wizard", "xp_required": 259200, "level": 25},
    {"name": "Speaker of the House", "xp_required": 236900, "level": 24},
    {"name": "Party God", "xp_required": 214600, "level": 23},
    {"name": "Master of Ceremonies", "xp_required": 192300, "level": 22},
    {"name": "Life of the Party", "xp_required": 170000, "level": 21},
    {"name": "The Guitar Hero", "xp_required": 141750, "level": 20},
    {"name": "Mic Dropper", "xp_required": 135000, "level": 19},
    {"name": "Golden Voice", "xp_required": 117000, "level": 18},
    {"name": "Party Animal", "xp_required": 100000, "level": 17},
    {"name": "Silver Tongue", "xp_required": 85000, "level": 16},
    {"name": "Smooth Talker", "xp_required": 75000, "level": 15},
    {"name": "Party Starter", "xp_required": 65000, "level": 14},
    {"name": "Karaoke King", "xp_required": 50000, "level": 13},
    {"name": "Thrillseeker", "xp_required": 40000, "level": 12},
    {"name": "Disco Diva", "xp_required": 30000, "level": 11},
    {"name": "Partygoer", "xp_required": 21000, "level": 10},
    {"name": "Fun Lover", "xp_required": 16000, "level": 9},
    {"name": "Conversationalist", "xp_required": 12000, "level": 8},
    {"name": "Groovy Guest", "xp_required": 8500, "level": 7},
    {"name": "Chatterbox", "xp_required": 6000, "level": 6},
    {"name": "Storyteller", "xp_required": 4300, "level": 5},
    {"name": "Social Butterfly", "xp_required": 3000, "level": 4},
    {"name": "Lounge Lurker", "xp_required": 1850, "level": 3},
    {"name": "Couch Potato", "xp_required": 1150, "level": 3},
    {"name": "Party Crasher", "xp_required": 550, "level": 2},
    {"name": "Passerby", "xp_required": 100, "level": 1},
    {"name": "Stranger", "xp_required": 0, "level": 0},
]

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print("Logged in as", client.user)

    guild = client.get_guild(GUILD_ID)
    if guild is None:
        print("Error: Guild not found.")
        await client.close()
        return

    for role_data in roles_to_remove:
        role_name = role_data["name"]
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            members_with_role = role.members
            for member in members_with_role:
                await member.remove_roles(role)
                print(f"Removed role '{role_name}' from member '{member.name}' ({member.id})")

    await client.close()


client.run(TOKEN)
