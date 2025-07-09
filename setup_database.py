import sqlite3
import json
from typing import List, Dict

class DatabaseManager:
    def __init__(self, db_name: str = "event_recommender.db"):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """Initialize the database with tables and sample data"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                interests TEXT NOT NULL
            )
        ''')
        
        # Create events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                tags TEXT NOT NULL,
                location TEXT NOT NULL,
                date TEXT NOT NULL,
                price REAL NOT NULL
            )
        ''')
        
        # Check if tables are empty and populate with sample data
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            self.populate_sample_data(cursor)
        
        conn.commit()
        conn.close()
    
    def populate_sample_data(self, cursor):
        """Populate the database with sample data"""
        # Sample users data
        users_data = [
            (1, "Samuel Lim", json.dumps(["technology", "artificial intelligence", "startups", "networking", "innovation"])),
            (2, "Tan Zeng Iain", json.dumps(["fitness", "running", "health", "outdoor activities", "sports"])),
            (3, "Qing Whey", json.dumps(["art", "painting", "creativity", "museums", "culture"])),
            (4, "Jefferson Low", json.dumps(["music", "concerts", "jazz", "live performance", "entertainment"])),
            (5, "Choo Lan Chan", json.dumps(["cooking", "food", "recipes", "culinary arts", "restaurants"]))
        ]
        
        cursor.executemany('''
            INSERT INTO users (id, name, interests) VALUES (?, ?, ?)
        ''', users_data)
        
        # Sample events data
        events_data = [
            (1, "Tech Innovation Summit 2025", "Join industry leaders discussing AI, startups, and cutting-edge technology", 
             "Technology", json.dumps(["technology", "artificial intelligence", "startups", "innovation", "networking"]), 
             "Convention Center", "2025-08-15", 150),
            (2, "Morning Fitness Bootcamp", "High-intensity outdoor workout session for all fitness levels", 
             "Fitness", json.dumps(["fitness", "outdoor activities", "health", "sports", "exercise"]), 
             "City Park", "2025-07-20", 25),
            (3, "Modern Art Gallery Opening", "Exclusive preview of contemporary paintings and sculptures", 
             "Arts & Culture", json.dumps(["art", "painting", "culture", "museums", "creativity"]), 
             "Downtown Gallery", "2025-07-25", 0),
            (4, "Jazz Under the Stars", "Live jazz performance in an intimate outdoor setting", 
             "Music", json.dumps(["music", "jazz", "live performance", "entertainment", "concerts"]), 
             "Rooftop Venue", "2025-08-05", 40),
            (5, "Culinary Masterclass", "Learn advanced cooking techniques from professional chefs", 
             "Food & Drink", json.dumps(["cooking", "food", "culinary arts", "recipes", "learning"]), 
             "Culinary Institute", "2025-07-30", 80),
            (6, "Marathon Training Group", "Weekly running group preparing for the city marathon", 
             "Fitness", json.dumps(["running", "fitness", "sports", "health", "training"]), 
             "Various Routes", "2025-07-15", 15),
            (7, "Startup Pitch Competition", "Watch entrepreneurs pitch their innovative business ideas", 
             "Business", json.dumps(["startups", "innovation", "technology", "networking", "entrepreneurship"]), 
             "Business Hub", "2025-08-10", 30),
            (8, "Food Festival Downtown", "Taste cuisines from around the world at local restaurants", 
             "Food & Drink", json.dumps(["food", "restaurants", "culture", "festival", "dining"]), 
             "Downtown Square", "2025-08-01", 20)
        ]
        
        cursor.executemany('''
            INSERT INTO events (id, title, description, category, tags, location, date, price) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', events_data)
    
    def get_all_users(self) -> List[Dict]:
        """Retrieve all users from the database"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, interests FROM users")
        users = []
        for row in cursor.fetchall():
            users.append({
                'id': row[0],
                'name': row[1],
                'interests': json.loads(row[2])
            })
        
        conn.close()
        return users
    
    def get_all_events(self) -> List[Dict]:
        """Retrieve all events from the database"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, title, description, category, tags, location, date, price FROM events")
        events = []
        for row in cursor.fetchall():
            events.append({
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'category': row[3],
                'tags': json.loads(row[4]),
                'location': row[5],
                'date': row[6],
                'price': row[7]
            })
        
        conn.close()
        return events
    
    def get_user_by_id(self, user_id: int) -> Dict:
        """Get a specific user by ID"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, interests FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        
        if row:
            user = {
                'id': row[0],
                'name': row[1],
                'interests': json.loads(row[2])
            }
        else:
            user = None
        
        conn.close()
        return user
    
    def add_user(self, name: str, interests: List[str]) -> bool:
        """Add a new user to the database"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (name, interests) VALUES (?, ?)
            ''', (name, json.dumps(interests)))
            conn.commit()
            success = True
        except sqlite3.Error:
            success = False
        
        conn.close()
        return success
    
    def add_event(self, title: str, description: str, category: str, tags: List[str], 
                  location: str, date: str, price: float) -> bool:
        """Add a new event to the database"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO events (title, description, category, tags, location, date, price) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, description, category, json.dumps(tags), location, date, price))
            conn.commit()
            success = True
        except sqlite3.Error:
            success = False
        
        conn.close()
        return success