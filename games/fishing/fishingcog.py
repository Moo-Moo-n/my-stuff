import sqlite3
import datetime
import random
from .fish_items import fish_items
from .fishing_config import tier_names, base_tier_probabilities, final_tier_probabilities, tier_intervals, max_cast_duration, xp_rewards
from tools.utils import update_user_xp

database_name = 'your_database_name.db'

class FishingGame:
    def __init__(self):
        self.checkline_timers = {}
        self.cast_start_times = {}
        self.checkline_timers = {}
        self.user_xp = {}
        self.tier_probabilities = {}
        
    def get_cast_duration(self, user_id):
        if user_id in self.cast_start_times:
            cast_start_time = self.cast_start_times[user_id]
            current_time = datetime.datetime.now()
            duration = (current_time - cast_start_time).total_seconds() / 60  # Duration in minutes
            return duration
        return None    

    def get_cast_start_time(self, user_id):
        conn = sqlite3.connect(database_name)
        cur = conn.cursor()
        query = "SELECT cast_start_time FROM fishing WHERE user_id = ?"
        cur.execute(query, (user_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()

        if result is not None:
            return datetime.datetime.fromisoformat(result[0])
        else:
            return None

    def update_cast_start_time(self, user_id, cast_start_time):
        conn = sqlite3.connect(database_name)
        cur = conn.cursor()
        query = "INSERT OR REPLACE INTO fishing (user_id, cast_start_time) VALUES (?, ?)"
        cur.execute(query, (user_id, cast_start_time))
        conn.commit()
        cur.close()
        conn.close()

    def remove_cast_start_time(self, user_id):
        conn = sqlite3.connect(database_name)
        cur = conn.cursor()
        query = "DELETE FROM fishing WHERE user_id = ?"
        cur.execute(query, (user_id,))
        conn.commit()
        cur.close()
        conn.close()

    def calculate_tier_probabilities(self, cast_duration):
        if cast_duration is None:
            return final_tier_probabilities

        if cast_duration >= max_cast_duration:
            return final_tier_probabilities

        tier_probabilities = []
        for i in range(len(base_tier_probabilities)):
            base_prob = base_tier_probabilities[i]
            final_prob = final_tier_probabilities[i]
            interval = tier_intervals[i]

            if cast_duration <= interval:
                tier_prob = base_prob
            else:
                progress = (cast_duration - interval) / (max_cast_duration - interval)
                tier_prob = base_prob + (final_prob - base_prob) * progress

            tier_probabilities.append(tier_prob)

        # Normalize probabilities
        sum_probs = sum(tier_probabilities)
        tier_probabilities = [prob / sum_probs for prob in tier_probabilities]

        return tier_probabilities

    def calculate_item_tier(self, user_id, cast_duration=None):
        cast_start_time = self.get_cast_start_time(user_id)

        if cast_start_time is None:
            return None

        current_time = datetime.datetime.now()
        if cast_duration is None:
            cast_duration = (current_time - cast_start_time).total_seconds() / 60  # Duration in minutes

        tier_probabilities = self.calculate_tier_probabilities(cast_duration)

        random_value = random.random()

        for index, probability in enumerate(tier_probabilities):
            if random_value <= probability:
                return index

        return None

    def update_tier_probabilities(self, user_id, tier_probabilities):
        self.tier_probabilities[user_id] = tier_probabilities

    def format_timedelta(self, td):
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours} hours, {minutes} minutes, {seconds} seconds"
