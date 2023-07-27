import sqlite3
import discord
from . import crops_dict
intents = discord.Intents.all()
intents.voice_states = True
def initialize_crops_table(database_name):
    conn = sqlite3.connect(database_name)
    cursor = conn.cursor()

    # Create Crops Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS crops (
        crop_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        tier_id INTEGER,
        growth_time INTEGER,
        selling_price INTEGER,
        FOREIGN KEY (tier_id) REFERENCES crop_tiers (tier_id)
    );
    ''')

    # Insert data from crops_dict into Crops Table
    for crop_name, crop_data in crops_dict.items():
        tier = crop_data['tier']
        growth_time = crop_data['growth_time']
        selling_price = crop_data['selling_price']

        cursor.execute('INSERT INTO crops (name, tier_id, growth_time, selling_price) VALUES (?, ?, ?, ?);',
                       (crop_name, tier, growth_time, selling_price))

    # Commit changes and close the connection
    conn.commit()
    conn.close()
    


# Function to check if the crops table is initialized, and if not, initialize it
def ensure_crops_table_initialized():
    conn = sqlite3.connect('your_database_name.db')
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='crops';")
    table_exists = cursor.fetchone()

    if not table_exists:
        initialize_crops_table('your_database_name.db')

    conn.close()