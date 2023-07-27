from discord.ext import commands
import discord

bproles_list = {
    0: {"name": "Stargazer", "xp_required": 0, "level": 0, "role_id": 1130484362912223332},
    1: {"name": "Astronaut", "xp_required": 900, "level": 1, "role_id": 1130484359032479805},
    2: {"name": "Meteorite Hunter", "xp_required": 1200, "level": 2, "role_id": 1130484366578024508},
    3: {"name": "Galactic Explorer", "xp_required": 1600, "level": 3, "role_id": 1130484371422457956},
    4: {"name": "Nebula Navigator", "xp_required": 2133, "level": 4, "role_id": 1130484378359824395},
    5: {"name": "Celestial Voyager", "xp_required": 2844, "level": 5, "role_id": 1130484386027032587},
    6: {"name": "Cosmic Adventurer", "xp_required": 3793, "level": 6, "role_id": 1130484393727766588},
    7: {"name": "Astro Trailblazer", "xp_required": 5057, "level": 7, "role_id": 1130484399297790082},
    8: {"name": "Galaxy Guardian", "xp_required": 6742, "level": 8, "role_id": 1130484403882164355},
    9: {"name": "Universal Sentinel", "xp_required":8990, "level": 9, "role_id": 1130484410832146472},
    10: {"name": "Interstellar Legend", "xp_required": 11986, "level": 10, "role_id": 1130484414686699550},
    11: {"name": "Cosmic Overlord (Premium)", "xp_required": 16000, "level": 11, "role_id": 1130484418914566286}
    # Add more entries for other levels if necessary
}





