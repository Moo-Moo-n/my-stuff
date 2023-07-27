import discord
from discord.ext import commands
from .fishingcog import FishingGame, fish_items
import datetime
from .fishing_config import tier_names, base_tier_probabilities, final_tier_probabilities, tier_intervals, max_cast_duration, xp_rewards
import random
from .catch_messages import catch_messages
import tools
import os
import sqlite3
audit_log_channel_id = 1114398557651353610
database_name = os.getenv("database_name")
db_connection = sqlite3.connect(database_name, check_same_thread=False, timeout=10)

class Fishing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.fishing_game = FishingGame()

    @commands.command(aliases=['fish'])
    async def fishing(self, ctx):
        explanation = """
        Welcome to the Fishing game! Here's how it works:

        1. Use `!cast` to cast your fishing line.
        2. Wait for a certain duration to increase your chances of catching rarer fish.
        3. Use `!checkline` to see if your fishing line is still intact or if it snapped.
        4. If you don't use checkline every 20 minutes, it will snap!
        5. If your line is intact, keep waiting or use `!reel` to catch a fish at the current probabilities.
        6. Reeling in a fish will earn you XP based on the fish's tier.
        
        Good luck and happy fishing!
        """

        embed = discord.Embed(title="Fishing Game", description=explanation, color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.command()
    async def cast(self, ctx):
        user_id = str(ctx.author.id)
        cast_start_time = self.fishing_game.get_cast_start_time(user_id)

        if cast_start_time is not None:
            current_time = datetime.datetime.now()
            cast_duration = current_time - cast_start_time
            formatted_duration = self.fishing_game.format_timedelta(cast_duration)
            await ctx.send(f"You have already cast your line {formatted_duration} ago.")
        else:
            current_time = datetime.datetime.now()
            self.fishing_game.update_cast_start_time(user_id, current_time)
            embed = discord.Embed(title="Fishing Game", color=discord.Color.blue())
            embed.add_field(name="Cast Confirmation", value="You cast your line.", inline=False)
            embed.add_field(name="Instructions", value="Now wait and use `!checkline` to see how long you've been casting and your probabilities!\n\nRemember, you need to `!checkline` every 20 minutes or your line will snap and you'll have to cast again!", inline=False)
            await ctx.send(embed=embed)
            
    @commands.command()
    async def checkline(self, ctx):
        user_id = str(ctx.author.id)
        cast_start_time = self.fishing_game.get_cast_start_time(user_id)

        if cast_start_time is None:
            await ctx.send("You haven't cast your line yet. Use `!cast` to start fishing.")
        else:
            current_time = datetime.datetime.now()
            cast_duration = (current_time - cast_start_time).total_seconds() / 60  # Duration in minutes

            # Check if the line has snapped
            if cast_duration >= 21:
                self.fishing_game.remove_cast_start_time(user_id)
                self.fishing_game.checkline_timers.pop(user_id, None)
                late_minutes = int(cast_duration - 21)
                await ctx.send(f"Your fishing line has snapped! You're {late_minutes} minutes late.")
            else:
                formatted_duration = self.fishing_game.format_timedelta(current_time - cast_start_time)
                tier_probabilities = self.fishing_game.calculate_tier_probabilities(cast_duration)

                tier_prob_output = "\n".join([f"{tier_names[i]}: {tier_probabilities[i] * 100:.2f}%" for i in range(len(tier_names))])

                embed = discord.Embed(title="Fishing Game", color=discord.Color.blue())
                embed.add_field(name="Casting Duration", value=f"You have been casting for {formatted_duration}.", inline=False)
                embed.add_field(name="Current Tier Probabilities", value=tier_prob_output, inline=False)
                self.fishing_game.checkline_timers[user_id] = current_time

                await ctx.send(embed=embed)

    @commands.command()
    async def resetfishing(self, ctx):
        user_id = str(ctx.author.id)

        # Remove cast start time and checkline timer
        self.fishing_game.remove_cast_start_time(user_id)
        self.fishing_game.checkline_timers.pop(user_id, None)

        await ctx.send("Your fishing status has been reset. You can start a new fishing session now.")

    @commands.command()
    async def reel(self, ctx):
        user_id = str(ctx.author.id)
        item_tier_index = self.fishing_game.calculate_item_tier(user_id)

        if item_tier_index is None:
            await ctx.send("You haven't cast your line yet. Use `!cast` to start fishing.")
        else:
            item_list = fish_items[item_tier_index]['fish']
            item = random.choice(item_list)
            xp_reward = xp_rewards[item_tier_index]
            old_xp = self.fishing_game.get_user_xp(user_id)
            new_xp = old_xp + xp_reward

            # Update XP in both regular leveling and battle pass
            await tools.update_user_xp(user_id, xp_reward, "leveling", self.dbconnection, self.bot)  # Regular leveling XP

            xp_message = f"XP Earned: {xp_reward}\nNew Total XP: {new_xp}"

            sale_value = xp_reward * 10  # Sale value in minutes (XP reward * 10)

            # Retrieve the current tier probabilities based on the casting duration
            cast_duration = self.fishing_game.get_cast_duration(user_id)
            tier_probabilities = self.fishing_game.calculate_tier_probabilities(cast_duration)

            # Update tier probabilities for reeling in the fish
            self.fishing_game.update_tier_probabilities(user_id, tier_probabilities)

            # Clear fishing status if user gets stuck in a loop
            if user_id in self.fishing_game.checkline_timers:
                self.fishing_game.checkline_timers.pop(user_id)

            # Remove cast start time and checkline timer
            self.fishing_game.remove_cast_start_time(user_id)

            catch_message = random.choice(catch_messages[item_tier_index + 1]).format(item=item)
            await ctx.send(f"{catch_message}\n\n{xp_message}\n\nSold for: {sale_value} minutes.")

            # Print the XP added to users table
            users_embed = discord.Embed(title="XP Added to Users", color=discord.Color.green())
            users_embed.add_field(name="XP Earned", value=xp_reward)
            users_embed.add_field(name="New Total XP", value=new_xp)

            # Print the XP added to bpleveling table
            bpleveling_embed = discord.Embed(title="XP Added to Battle Pass", color=discord.Color.blue())
            bpleveling_embed.add_field(name="XP Earned", value=xp_reward)
            bpleveling_embed.add_field(name="New Total XP", value=new_xp)

            # Get the audit log channel
            audit_log_channel = self.bot.get_channel(audit_log_channel_id)
            if audit_log_channel:
                await audit_log_channel.send(embed=users_embed)
                await audit_log_channel.send(embed=bpleveling_embed)



def setup(bot):
    bot.add_cog(Fishing(bot))


