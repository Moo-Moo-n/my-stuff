import sqlite3

# Create an in-memory SQLite database for demonstration
conn = sqlite3.connect('your_database_name.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS user_inventory (
    user_id TEXT,
    crop_id INTEGER,
    quantity INTEGER,
    farm_name TEXT,  -- Add the new 'farm_name' column
    PRIMARY KEY (user_id, crop_id),
    FOREIGN KEY (crop_id) REFERENCES crops (crop_id)
);
''')
print("Temporary database with the specified schema has been created.")

# Commit changes and close the connection
conn.commit()
conn.close()

