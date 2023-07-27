import sqlite3
from datetime import datetime, timedelta
from . import crops_dict
from games.farming.crops_dict import crops_data
# Function to get crop information from the database

def get_crop_info(crop_name):
    # Check if the crop_name exists in crops_data
    if crop_name in crops_data:
        crop_info = crops_data[crop_name]
        crop_id = crop_info["crop_id"]
        tier_id = crop_info["tier"]
        growth_time = crop_info["growth_time"]
        selling_price = crop_info["selling_price"]
        return tier_id, growth_time, selling_price
    else:
        return None


# Function to calculate growth time for a crop based on its tier
def calculate_growth_time(cursor, tier_id):
    query = "SELECT growth_time FROM crop_tiers WHERE tier_id = ?"
    cursor.execute(query, (tier_id,))
    return cursor.fetchone()[0]

# Function to get a user's crop growth information
def get_user_crop_growth(cursor, user_id, crop_id):
    query = "SELECT growth_stage, start_time FROM crop_growth WHERE user_id = ? AND crop_id = ?"
    cursor.execute(query, (user_id, crop_id))
    return cursor.fetchone()

# Function to update a user's crop growth information
def update_user_crop_growth(cursor, user_id, crop_id, growth_stage, start_time):
    query = "INSERT OR REPLACE INTO crop_growth (user_id, crop_id, growth_stage, start_time) VALUES (?, ?, ?, ?)"
    cursor.execute(query, (user_id, crop_id, growth_stage, start_time))

def update_user_crop_inventory(cursor, user_id, crop_id, quantity):
    # Check if the user and crop combination exists in the database
    cursor.execute(
        "SELECT quantity FROM user_inventory WHERE user_id = ? AND crop_id = ?",
        (user_id, crop_id),
    )
    existing_quantity = cursor.fetchone()

    # If the user and crop combination exists, update the quantity
    if existing_quantity:
        current_quantity = existing_quantity[0]
        new_quantity = current_quantity + quantity
        cursor.execute(
            "UPDATE user_inventory SET quantity = ? WHERE user_id = ? AND crop_id = ?",
            (new_quantity, user_id, crop_id),
        )

    # Get the user's current crop quantity after the update
    cursor.execute(
        "SELECT quantity FROM user_inventory WHERE user_id = ? AND crop_id = ?",
        (user_id, crop_id),
    )

    current_quantity = cursor.fetchone()

    # Print checks to the audit log channel
    print(
        f"User {user_id} gained {quantity} of crop {crop_id}. Previous quantity: {existing_quantity[0] if existing_quantity else 0}. Current quantity: {current_quantity[0] if current_quantity else 0}."
    )
    
def plant_seed(cursor, user_id, crop_id):
    # Check if the user has the seed in their inventory
    cursor.execute(
        "SELECT quantity FROM user_inventory WHERE user_id = ? AND crop_id = ?",
        (user_id, crop_id),
    )
    existing_quantity = cursor.fetchone()

    if existing_quantity and existing_quantity[0] > 0:
        # Reduce the quantity of seeds by one
        cursor.execute(
            "UPDATE user_inventory SET quantity = quantity - 1 WHERE user_id = ? AND crop_id = ?",
            (user_id, crop_id),
        )
        return True
    else:
        return False

# Function to calculate the time remaining for a crop to be ready for harvest
def calculate_time_remaining(start_time, growth_time):
    time_diff = growth_time - (datetime.utcnow() - start_time).total_seconds() / 60
    return max(0, round(time_diff))

def update_user_farm_name(cursor, user_id, farm_name):
    query = "INSERT OR REPLACE INTO user_inventory (user_id, farm_name) VALUES (?, ?)"
    cursor.execute(query, (user_id, farm_name))

# Function to convert minutes to a human-readable time format (HH:MM:SS)
def minutes_to_time_format(minutes):
    return str(timedelta(minutes=minutes))

# Function to get the user's current farm status (list of crops and their growth status)
def get_user_farm_status(cursor, user_id):
    query = """
        SELECT c.name, cg.growth_stage, ct.growth_time, cg.start_time
        FROM crops c
        LEFT JOIN crop_growth cg ON c.crop_id = cg.crop_id AND cg.user_id = ?
        JOIN crop_tiers ct ON c.tier_id = ct.tier_id
    """
    cursor.execute(query, (user_id,))
    return cursor.fetchall()

# Function to initialize the crops table in the database with data from crops_dict

def get_user_crop_inventory(cursor, user_id, crop_id):
    query = "SELECT quantity FROM user_inventory WHERE user_id = ? AND crop_id = ?"
    cursor.execute(query, (user_id, crop_id))
    return cursor.fetchone()

def initialize_crops_table(database_name):
    conn = sqlite3.connect(database_name)
    cursor = conn.cursor()

    # Create the crops table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS crops (
            crop_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            tier_id INTEGER NOT NULL,
            selling_price INTEGER NOT NULL,
            growth_time INTEGER NOT NULL
        )
        """
    )

    # Insert data from crops_data dictionary into the crops table
    for crop_name, crop_info in crops_dict.crops_data.items():
        tier_id = crop_info["tier"]
        selling_price = crop_info["selling_price"]
        growth_time = crop_info["growth_time"]
        cursor.execute(
            "INSERT INTO crops (name, tier_id, selling_price, growth_time) VALUES (?, ?, ?, ?)",
            (crop_name, tier_id, selling_price, growth_time),
        )

    conn.commit()
    conn.close()