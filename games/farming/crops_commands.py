import discord
import sqlite3
import datetime
import asyncio
from discord.ext import commands
from .crops_defs import (
    get_crop_info, calculate_growth_time, get_user_crop_growth,
    update_user_crop_growth, get_user_crop_inventory,
    update_user_crop_inventory, calculate_time_remaining,
    minutes_to_time_format, get_user_farm_status, update_user_farm_name, plant_seed
)

from tools.utils import update_user_xp
database_name = 'your_database_name.db'
from .crops_utils import  initialize_crops_table
from .crops_dict import crops_data

# Create an instance of discord.Intents
intents = discord.Intents.all()
intents.voice_states = True
     
class CropsCommands(commands.Cog):
    def __init__(self, bot, cursor):
        self.bot = bot
        self.cursor = cursor

    # ... other functions ...

    def is_valid_crop(self, crop_name):
        return any(crop_name.title() == crop_data["name"] for crop_data in crops_data.values())

    @commands.command()
    async def plant(self, ctx, crop_name=None):
        if crop_name is None:
            await ctx.send("You must insert the plant in the command, try again. ( e.g: !plant [crop_name] )")
            return

        if not self.is_valid_crop(crop_name):
            await ctx.send(f"'{crop_name}' is not a valid crop. Please try again with a valid crop name. (e.g., !plant Carrot Seeds)")
            return

        # ... rest of the function ...
        crop_info = get_crop_info(self.cursor, crop_name)
        if not crop_info:
            await ctx.send(f"{ctx.author.mention}, {crop_name} is not a valid crop.")
            return

        crop_id, tier_id, growth_time, selling_price = crop_info

        # Check if the user has the seed in their inventory
        if not plant_seed(self.cursor, str(ctx.author.id), crop_id):
            await ctx.send(f"{ctx.author.mention}, you do not have {crop_name} seeds to plant.")
            return

        await ctx.send(
            f"{ctx.author.mention}, you planted {crop_name}! It will be ready for harvest in {minutes_to_time_format(growth_time)}. Selling price: {selling_price} coins."
        )

        # Log the event in the audit log channel
        audit_log_channel_id = 1234567890  # Replace with the ID of your audit log channel
        audit_log_channel = self.bot.get_channel(audit_log_channel_id)

        if audit_log_channel:
            await audit_log_channel.send(
                f"User {ctx.author.id} gained 1 of crop {crop_id}. Previous quantity: 0. Current quantity: None."
            )

    
    @commands.command()
    async def harvest(self, ctx):
        user_farm_status = get_user_farm_status(self.cursor, str(ctx.author.id))

        for crop_name, growth_stage, growth_time, start_time in user_farm_status:
            time_remaining = calculate_time_remaining(start_time, growth_time)

            if growth_stage == 1 and time_remaining <= 0:
                crop_id = crops_data[crop_name]["tier"]

                user_inventory = get_user_crop_inventory(self.cursor, str(ctx.author.id), crop_id)
                current_quantity = user_inventory[0] if user_inventory else 0

                # Update the user's crop inventory
                if user_inventory:
                    update_user_crop_inventory(self.cursor, str(ctx.author.id), crop_id, 1)
                else:
                    # If the user does not have any of this crop, insert a new row in the inventory table
                    query = "INSERT INTO user_crops (user_id, crop_id, quantity) VALUES (?, ?, ?)"
                    self.cursor.execute(query, (str(ctx.author.id), crop_id, 1))

                update_user_crop_growth(self.cursor, str(ctx.author.id), crop_id, 0, None)  # Reset growth_stage and start_time
                self.conn.commit()

                await ctx.send(
                    f"{ctx.author.mention}, you harvested {crop_name}! You now have {current_quantity + 1} of {crop_name}."
                )

                # Log the event in the audit log channel
                audit_log_channel_id = 1234567890  # Replace with the ID of your audit log channel
                audit_log_channel = self.bot.get_channel(audit_log_channel_id)

                if audit_log_channel:
                    await audit_log_channel.send(
                        f"User {ctx.author.id} gained 1 of crop {crop_id}. Previous quantity: {current_quantity}. Current quantity: {current_quantity + 1}."
                    )    

    @commands.command()
    async def update_crops_data(self, ctx):
        # Update the crops table
        for crop_name, crop_info in crops_data.items():
            query = "INSERT OR REPLACE INTO crops (name, tier_id, selling_price) VALUES (?, ?, ?)"
            self.cursor.execute(query, (crop_name, crop_info["tier"], crop_info["selling_price"]))

        # Update the crop_tiers table
        for tier_id in range(1, 11):  # Assuming there are 10 tiers
            tier_key = f"Tier {tier_id}"  # Construct the tier key using the tier_id
            if tier_key in crops_data:
                query = "INSERT OR REPLACE INTO crop_tiers (tier_id, growth_time) VALUES (?, ?)"
                self.cursor.execute(query, (tier_id, crops_data[tier_key]["growth_time"]))

        self.conn.commit()
        await ctx.send("Crops data updated in the database!")


    @commands.command(name="start_farm")
    async def start_farm(self, ctx):
        # Prompt the user to enter their farm name and initialize the farm
        await ctx.send(f"{ctx.author.mention}, let's start your farm! Please enter the name of your farm:")
        try:
            msg = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author, timeout=60)
            farm_name = msg.content.strip()
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. Please try again.")
            return

        # Update the user's farm name in the database
        update_user_farm_name(self.cursor, str(ctx.author.id), farm_name)
        self.conn.commit()

        # Add 10 potatoes and 10 xp/dollars to the user's inventory
        update_user_crop_inventory(self.cursor, str(ctx.author.id), 1, 10)  # Assuming crop_id 1 corresponds to potatoes
        await update_user_xp(str(ctx.author.id), 10, 'leveling', self.conn, self.bot)  # Use await here
        self.conn.commit()

        await ctx.send(f"{ctx.author.mention}, congratulations! Your farm '{farm_name}' has been created. You now have 10 potatoes and 10 xp/dollars to start with.")
        


def setup(bot, cursor):
    bot.add_cog(CropsCommands(bot, cursor))