import discord
from discord.ext import commands
import sqlite3
from leveling.roles_list import roles_list
import random
from tools.utils import get_user_level, get_user_xp, get_user_role_by_level, update_user_xp
from games.mugging_system.failure_quips import generate_failure_messages
from datetime import datetime, timedelta

database_name = "your_database_name.db"

class MuggingSystem(commands.Cog):
    def __init__(self, bot, dbconnection):
        self.bot = bot
        self.dbconnection = dbconnection
        self.mugging_cooldown = commands.CooldownMapping.from_cooldown(1, 5, commands.BucketType.user)
        self.victim_cooldown = commands.CooldownMapping.from_cooldown(1, 5, commands.BucketType.user)

    @commands.command()
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def mug(self, ctx, victim: discord.Member = None):
        if not victim:
            await ctx.send("Please mention a valid user to mug.")
            return

        if victim.bot:
            await ctx.send("Bots cannot be mugged.")
            return

        if victim == ctx.author:
            await ctx.send("You cannot mug yourself.")
            return

        mugger_xp = await get_user_xp(ctx.author.id, 'leveling', self.dbconnection)
        victim_xp = await get_user_xp(victim.id, 'leveling', self.dbconnection)


        if victim_xp <= 0:
            await ctx.send(f"{victim.mention} doesn't have any XP to mug.")
            return

        # Check mugging cooldown for the mugger
        mugger_bucket = self.mugging_cooldown.get_bucket(ctx.message)
        retry_after = mugger_bucket.update_rate_limit()
        if retry_after:
            cooldown_time = str(timedelta(seconds=retry_after))
            await ctx.send(f"You can mug again in {cooldown_time}.")
            return

        # Check mugging cooldown for the victim
        victim_bucket = self.victim_cooldown.get_bucket(ctx.message)
        retry_after = victim_bucket.update_rate_limit()
        if retry_after:
            await ctx.send(f"You can only be mugged again in {retry_after:.0f} seconds.")
            return

        # Calculate mugging chance based on failed attempts
        mugger_failed_attempts = get_failed_attempts(ctx.author.id)
        mugging_chance_failed = calculate_mugging_chance_failed(mugger_failed_attempts)
        table_name = 'leveling'
        # Calculate mugging chance based on level
        mugger_level = await get_user_level(ctx.author.id, table_name, self.dbconnection)
        mugging_chance_level = await calculate_mugging_chance_level(self, ctx.author.id)

        # Calculate total mugging chance
        total_mugging_chance = mugging_chance_failed + mugging_chance_level

        # Roll for success
        is_successful = random.random() < total_mugging_chance

        if is_successful:
            # Calculate the percentage of XP to be stolen based on the victim's role
            victim_role = await get_user_role_by_level(await get_user_level(victim.id, 'leveling', self.dbconnection), "leveling")
            xp_percentage = calculate_xp_percentage(victim_role)

            stolen_xp = int(victim_xp * xp_percentage)
            remaining_xp = victim_xp - stolen_xp

            # Update mugging statistics and XP
            reset_failed_attempts(ctx.author.id)
            update_user_xp(ctx.author.id, stolen_xp, 'leveling', self.dbconnection, self.bot)
            update_user_xp(victim.id, -stolen_xp, 'leveling', self.dbconnection, self.bot)

            await ctx.send(f"{ctx.author.mention} successfully mugged {victim.mention} and stole {stolen_xp} XP. {victim.name} now has {remaining_xp} XP.")
        else:
            # Failed attempt
            increment_failed_attempts(ctx.author.id)
            await update_user_xp(ctx.author.id, -10, 'leveling', self.dbconnection, self.bot)  # Deduct 10 XP from the mugger
            await update_user_xp(victim.id, 10, 'leveling', self.dbconnection, self.bot)
            failure_messages = generate_failure_messages(ctx, victim)
            failure_message = random.choice(failure_messages)
            await ctx.send(failure_message)


def calculate_mugging_chance_failed(failed_attempts):
    max_failed_attempts = 10
    pity_chance_increase = [0, 1, 3, 6, 8, 10, 11, 12, 13, 15]  # Percentage increase based on failed attempts

    if failed_attempts < max_failed_attempts:
        return pity_chance_increase[failed_attempts] / 100
    else:
        return 0.2  # Maximum mugging chance of 20% for more than 10 failed attempts

async def calculate_mugging_chance_level(self,user_id):
    mugger_level = await get_user_level(user_id, 'leveling', self.dbconnection)
    if mugger_level <= 10:
        return 0.1
    elif mugger_level <= 20:
        return 0.05
    else:
        return 0.03

def calculate_xp_percentage(role):
    if role is None:
        return 0.1  # Default percentage if role is not found

    for role_data in roles_list:
        if role_data["name"] == role:
            role_level = role_data["level"]
            total_roles = len(roles_list)

            if role_level < 5:  # Lowest roles bracket
                return 0.01
            elif role_level < total_roles - 5:  # Middle roles bracket
                return 0.003
            else:  # Highest roles bracket
                return 0.001

    return 0.1  # Role not found, return default percentage


def get_failed_attempts(user_id):
    conn = sqlite3.connect(database_name)
    cur = conn.cursor()
    query = "SELECT failed_attempts FROM mugging WHERE user_id = ?"
    cur.execute(query, (user_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()

    if result is not None:
        failed_attempts = int(result[0])
        return failed_attempts
    else:
        return 0

def increment_failed_attempts(user_id):
    conn = sqlite3.connect(database_name)
    cur = conn.cursor()
    query = "UPDATE mugging SET failed_attempts = failed_attempts + 1 WHERE user_id = ?"
    cur.execute(query, (user_id,))
    conn.commit()
    cur.close()
    conn.close()

def reset_failed_attempts(user_id):
    conn = sqlite3.connect(database_name)
    cur = conn.cursor()
    query = "UPDATE mugging SET failed_attempts = 0 WHERE user_id = ?"
    cur.execute(query, (user_id,))
    conn.commit()
    cur.close()
    conn.close()

def setup(bot):
    bot.add_cog(MuggingSystem(bot, sqlite3.connect(database_name)))
