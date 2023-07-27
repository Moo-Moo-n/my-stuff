import sqlite3

# Create an in-memory SQLite database for demonstration
conn = sqlite3.connect('your_database_name')
cursor = conn.cursor()

# Create Crop Tiers Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS crop_tiers (
    tier_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    growth_time INTEGER,
    selling_price_multiplier REAL
);
''')

# Insert sample data into Crop Tiers Table
cursor.executemany('''
INSERT INTO crop_tiers (name, growth_time, selling_price_multiplier)
VALUES (?, ?, ?);
''', [
    ('Tier 1', 60, 1.0),
    ('Tier 2', 120, 1.5),
    # Add more tiers and their respective data
])

# Create Crops Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS crops (
    crop_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    tier_id INTEGER,
    selling_price INTEGER,
    FOREIGN KEY (tier_id) REFERENCES crop_tiers (tier_id)
);
''')

# Insert sample data into Crops Table
cursor.executemany('''
INSERT INTO crops (name, tier_id, selling_price)
VALUES (?, ?, ?);
''', [
    ('Carrot', 1, 10),
    ('Tomato', 1, 12),
    # Add more crops and their respective data
])

# Create User Inventory Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS user_inventory (
    user_id TEXT,
    crop_id INTEGER,
    quantity INTEGER,
    PRIMARY KEY (user_id, crop_id),
    FOREIGN KEY (crop_id) REFERENCES crops (crop_id)
);
''')

# Create Crop Growth Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS crop_growth (
    user_id TEXT,
    crop_id INTEGER,
    growth_stage INTEGER,
    start_time TIMESTAMP,
    PRIMARY KEY (user_id, crop_id),
    FOREIGN KEY (crop_id) REFERENCES crops (crop_id)
);
''')

# Commit changes and close the connection
conn.commit()
conn.close()

print("Temporary database with the specified schema has been created.")
