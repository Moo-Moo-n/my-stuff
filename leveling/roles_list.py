from discord.ext import commands
import discord

roles_list = {
    0: {"name": "Stranger", "xp_required": 0, "level": 0, "role_id": 1129510284583784448},
    1: {"name": "Passerby", "xp_required": 120, "level": 1, "role_id": 1116884145885433906},
    2: {"name": "Party Crasher", "xp_required": 300, "level": 2, "role_id": 1116624694431465564},
    3: {"name": "Couch Potato", "xp_required": 600, "level": 3, "role_id": 1116885598863638538},
    4: {"name": "Lounge Lurker", "xp_required": 1150, "level": 4, "role_id": 1116888810572222514},
    5: {"name": "Social Butterfly", "xp_required": 2500, "level": 5, "role_id": 1116624701159116831},
    6: {"name": "Storyteller", "xp_required": 4000, "level": 6, "role_id": 1116624704229347328},
    7: {"name": "Chatterbox", "xp_required": 6000, "level": 7, "role_id": 1116624707085672512},
    8: {"name": "Groovy Guest", "xp_required": 8500, "level": 8, "role_id": 1116886920161665024},
    9: {"name": "Conversationalist", "xp_required": 11500, "level": 9, "role_id": 1116624709572898888},
    10: {"name": "Fun Lover", "xp_required": 15000, "level": 10, "role_id": 1116624712307580968},
    11: {"name": "Vibrant Personality", "xp_required": 19000, "level": 11, "role_id": 1129901549875888170},
    12: {"name": "Night Life Dweller", "xp_required": 23500, "level": 12, "role_id": 1129902197157675098},
    13: {"name": "Partygoer", "xp_required": 28500, "level": 13, "role_id": 1116624714589282355},
    14: {"name": "Disco Diva", "xp_required": 34000, "level": 14, "role_id": 1116888151990992976},
    15: {"name": "Epic Raver", "xp_required": 40000, "level": 15, "role_id": 1129902757843841044},
    16: {"name": "Thrillseeker", "xp_required": 46500, "level": 16, "role_id": 1116624716749344818},
    17: {"name": "Entertainer", "xp_required": 53500, "level": 17, "role_id": 1129902982004232303},
    18: {"name": "Karaoke King", "xp_required": 61000, "level": 18, "role_id": 1116624719056211968},
    19: {"name": "Big Vibin'", "xp_required": 69000, "level": 19, "role_id": 1129903491612151858},
    20: {"name": "Party Starter", "xp_required": 77500, "level": 20, "role_id": 1116624721971257355},
    21: {"name": "Smooth Talker", "xp_required": 86500, "level": 21, "role_id": 1116624731949506580},
    22: {"name": "Silver Tongue", "xp_required": 96000, "level": 22, "role_id": 1116624734092804106},
    23: {"name": "Liquor Lord", "xp_required": 96000, "level": 23, "role_id": 1129904655313404014},
    24: {"name": "Party Animal", "xp_required": 106000, "level": 24, "role_id": 1116886077299503154},
    25: {"name": "Golden Voice", "xp_required": 116500, "level": 25, "role_id": 1116624736726818846},
    26: {"name": "Mic Dropper", "xp_required": 127500, "level": 26, "role_id": 1116888490282602546},
    27: {"name": "The Guitar Hero", "xp_required": 139000, "level": 27, "role_id": 1116887572103303228},
    28: {"name": "Life of the Party", "xp_required": 151000, "level": 28, "role_id": 1116884883025973388},
    29: {"name": "Master of Ceremonies", "xp_required": 163500, "level": 29, "role_id": 1116624739264380988},
    30: {"name": "Party God", "xp_required": 176500, "level": 30, "role_id": 1116887939721482370},
    31: {"name": "Speaker of the House", "xp_required": 200000, "level": 31, "role_id": 1116884305373839400},
    32: {"name": "The Grand Wizard", "xp_required": 259200, "level": 32, "role_id": 1116624741474779237}
    # Add more entries for other levels if necessary
}




