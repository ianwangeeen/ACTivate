import sqlite3
import json
from typing import List, Dict
from collections import Counter
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
                category TEXT NOT NULL,
                interests TEXT NOT NULL,
                preferred_day TEXT DEFAULT NULL,
                office_location TEXT DEFAULT NULL
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
                time TEXT NOT NULL,
                price REAL NOT NULL,
                organiser_id INTEGER DEFAULT NULL,
                image_url TEXT DEFAULT NULL
            )
        ''')

        # Create user_events table for tracking registrations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                event_id INTEGER NOT NULL,
                registration_date TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (event_id) REFERENCES events (id),
                UNIQUE(user_id, event_id)
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
            (51, "Samuel Lim", json.dumps(["Technology & Digital", "Learning & Personal Growth"]), json.dumps(["artificial intelligence", "data science", "software development", "career & networking", "investing & financial literacy"]), json.dumps(["Wednesday", "Friday"]), "DTTB"),
            (52, "Tan Zeng Iain", json.dumps(["Health & Wellness"]), json.dumps(["badminton", "meditation & mindfulness", "mental health", "running & marathons"]), json.dumps(["Monday", "Friday"]), "Connection 1"),
            (53, "Qing Whey", json.dumps(["Arts & Creativity"]), json.dumps(["calligraphy & typography", "graphic design", "painting & drawing"]), json.dumps(["Friday", "Saturday", "Sunday"]), "Nee Soon Camp"),
            (54, "Jefferson Low", json.dumps(["Music & Performance", "Arts & Creativity"]), json.dumps(["band", "karaoke", "photography", "video production", "journaling & scrapbooking"]), json.dumps(["Friday", "Saturday"]), "Nee Soon Camp"),
            (55, "Choo Lan Chan", json.dumps(["Food & Drink", "Music & Performance"]), json.dumps(["stand-up comedy", "foodie trails", "wine appreciation", "coffee appreciation"]), json.dumps(["Wednesday", "Saturday", "Sunday"]), "BMC"),
            (1, 'Alice Zhang', '["Tech & Digital"]', '["ux/ui design", "stand up comedy", "painting & drawing", "web3 & blockchain"]', '["Sunday", "Monday", "Friday"]', 'Nee Soon Camp'),
            (2, 'Bob Tan', '["Travel & Culture"]', '["mahjong meetups", "nutrition"]', '["Monday"]', 'Connection 1'),
            (3, 'Charlie Lee', '["Outdoors & Nature"]', '["cycling (road, mtb, leisure)", "photography (street, portrait, nature)"]', '["Sunday", "Monday", "Friday"]', 'BMC'),
            (4, 'Diana Lim', '["Arts & Creativity"]', '["yoga & pilates", "urban sketching"]', '["Thursday"]', 'Connection 1'),
            (5, 'Ethan Ng', '["Games & Hobbies"]', '["badminton", "climbing", "chess club"]', '["Wednesday"]', 'DTTB'),
            (6, 'Fiona Koh', '["Food & Drink"]', '["coffee appreciation", "foodie trails", "nutrition"]', '["Monday", "Saturday", "Friday"]', 'Nee Soon Camp'),
            (7, 'George Wong', '["Learning & Personal Growth"]', '["journaling & scrapbooking", "book clubs"]', '["Tuesday"]', 'BMC'),
            (8, 'Hannah Goh', '["Pets & Animals"]', '["animal volunteer work", "cat lovers circle"]', '["Friday", "Wednesday", "Monday"]', 'Connection 1'),
            (9, 'Ian Chong', '["Health & Wellness"]', '["meditation & mindfulness"]', '["Monday", "Wednesday"]', 'DTTB'),
            (10, 'Jenny Teo', '["Travel & Culture"]', '["weekend explorers", "local heritage & hidden gems"]', '["Wednesday"]', 'BMC'),
            (11, 'Kyle Ong', '["Tech & Digital"]', '["cybersecurity", "software development"]', '["Monday", "Thursday"]', 'DTTB'),
            (12, 'Laura Sim', '["Learning & Personal Growth"]', '["investing & financial literacy", "data science", "artificial intelligence"]', '["Monday", "Wednesday", "Saturday"]', 'Connection 1'),
            (13, 'Mike Yeo', '["Games & Hobbies"]', '["board games", "trading card games (mtg, pokémon)"]', '["Monday", "Sunday"]', 'Nee Soon Camp'),
            (14, 'Nina Chua', '["Arts & Creativity"]', '["painting & drawing", "calligraphy & typography"]', '["Monday", "Tuesday", "Wednesday"]', 'BMC'),
            (15, 'Owen Tan', '["Outdoors & Nature"]', '["stargazing & astronomy", "nature walks & forest bathing"]', '["Wednesday"]', 'Connection 1'),
            (16, 'Paula Phua', '["Health & Wellness"]', '["yoga & pilates", "spin"]', '["Friday"]', 'DTTB'),
            (17, 'Quinn Lee', '["Travel & Culture"]', '["travel hacks & points"]', '["Friday", "Tuesday"]', 'BMC'),
            (18, 'Rachel Lam', '["Food & Drink"]', '["tea appreciation", "wine appreciation"]', '["Saturday", "Wednesday"]', 'Connection 1'),
            (19, 'Sam Koh', '["Tech & Digital"]', '["ux/ui design", "web3 & blockchain"]', '["Tuesday", "Monday", "Sunday"]', 'DTTB'),
            (20, 'Tina Ng', '["Games & Hobbies"]', '["mahjong meetups", "chess club"]', '["Thursday"]', 'Nee Soon Camp'),
            (21, 'Uma Wong', '["Health & Wellness"]', '["mental health", "meditation & mindfulness"]', '["Wednesday", "Thursday"]', 'BMC'),
            (22, 'Victor Lim', '["Learning & Personal Growth"]', '["languages (e.g. japanese, arabic)"]', '["Friday"]', 'Connection 1'),
            (23, 'Wendy Goh', '["Pets & Animals"]', '["dog walking groups", "cat lovers circle"]', '["Tuesday"]', 'DTTB'),
            (24, 'Xavier Tan', '["Food & Drink"]', '["vegan / vegetarian", "nutrition"]', '["Sunday", "Wednesday"]', 'BMC'),
            (25, 'Yvonne Chia', '["Arts & Creativity"]', '["graphic design", "diy crafts & upcycling"]', '["Friday", "Sunday", "Wednesday"]', 'Connection 1'),
            (26, 'Zack Neo', '["Outdoors & Nature"]', '["bouldering", "kayaking / watersports"]', '["Friday", "Monday", "Wednesday"]', 'DTTB'),
            (27, 'Aaron Ho', '["Learning & Personal Growth"]', '["career & networking", "investing & financial literacy"]', '["Saturday", "Sunday", "Wednesday"]', 'BMC'),
            (28, 'Bella Sim', '["Tech & Digital"]', '["artificial intelligence", "data science"]', '["Thursday", "Tuesday"]', 'Connection 1'),
            (29, 'Chris Ong', '["Arts & Creativity"]', '["urban sketching", "journaling & scrapbooking"]', '["Sunday"]', 'DTTB'),
            (30, 'Delia Lee', '["Games & Hobbies"]', '["board games", "stand up comedy"]', '["Tuesday"]', 'BMC'),
            (31, 'Eric Tan', '["Music & Performance"]', '["band", "karaoke"]', '["Thursday", "Friday", "Tuesday"]', 'Connection 1'),
            (32, 'Grace Ng', '["Health & Wellness"]', '["nutrition", "yoga & pilates"]', '["Saturday", "Monday"]', 'DTTB'),
            (33, 'Henry Teo', '["Travel & Culture"]', '["local heritage & hidden gems", "weekend explorers"]', '["Sunday", "Monday", "Saturday"]', 'BMC'),
            (34, 'Ivy Goh', '["Food & Drink"]', '["tea appreciation", "coffee appreciation"]', '["Wednesday"]', 'Connection 1'),
            (35, 'Jack Lim', '["Outdoors & Nature"]', '["nature walks & forest bathing", "stargazing & astronomy"]', '["Tuesday", "Sunday"]', 'DTTB'),
            (36, 'Karen Yeo', '["Tech & Digital"]', '["software development", "cybersecurity"]', '["Wednesday", "Thursday", "Sunday"]', 'BMC'),
            (37, 'Leo Chua', '["Games & Hobbies"]', '["chess club", "mahjong meetups"]', '["Saturday", "Monday", "Thursday"]', 'Connection 1'),
            (38, 'Mia Koh', '["Arts & Creativity"]', '["painting & drawing", "pottery / ceramics"]', '["Wednesday", "Tuesday"]', 'Nee Soon Camp'),
            (39, 'Nathan Wong', '["Learning & Personal Growth"]', '["book clubs", "languages (e.g. japanese, arabic)"]', '["Friday", "Monday"]', 'BMC'),
            (40, 'Olivia Phua', '["Pets & Animals"]', '["animal volunteer work", "dog walking groups"]', '["Tuesday", "Wednesday"]', 'Connection 1'),
            (41, 'Peter Tan', '["Food & Drink"]', '["foodie trails", "vegan / vegetarian"]', '["Sunday", "Monday", "Saturday"]', 'DTTB'),
            (42, 'Quincy Lee', '["Tech & Digital"]', '["ux/ui design", "web3 & blockchain"]', '["Saturday", "Tuesday", "Sunday"]', 'Connection 1'),
            (43, 'Rachel Ong', '["Music & Performance"]', '["video production", "graphic design"]', '["Saturday", "Monday"]', 'BMC'),
            (44, 'Simon Ng', '["Health & Wellness"]', '["spin", "nutrition"]', '["Tuesday", "Sunday", "Wednesday"]', 'Connection 1'),
            (45, 'Tara Lim', '["Arts & Creativity"]', '["calligraphy & typography", "diy crafts & upcycling"]', '["Sunday", "Wednesday", "Thursday"]', 'DTTB'),
            (46, 'Umar Goh', '["Travel & Culture"]', '["travel hacks & points", "weekend explorers"]', '["Friday"]', 'BMC'),
            (47, 'Vera Teo', '["Games & Hobbies"]', '["board games", "stand up comedy"]', '["Saturday"]', 'Connection 1'),
            (48, 'Will Chong', '["Learning & Personal Growth"]', '["book clubs", "career & networking"]', '["Monday"]', 'Nee Soon Camp'),
            (49, 'Xena Ho', '["Outdoors & Nature"]', '["climbing", "bouldering"]', '["Tuesday", "Monday", "Wednesday"]', 'DTTB'),
            (50, 'Yuri Sim', '["Music & Performance"]', '["video production"]', '["Sunday"]', 'Connection 1')
        ]
        
        cursor.executemany('''
            INSERT INTO users (id, name, category, interests, preferred_day, office_location) VALUES (?, ?, ?, ?, ?, ?)
        ''', users_data)
        
        # Sample events data (date format is saved as YYYY-MM-DD)
        events_data = [
            (1, "Tech Innovation Summit 2025", "Join industry leaders discussing AI, startups, and cutting-edge technology", 
             "Technology", json.dumps(["technology", "artificial intelligence", "data science", "web3 & blockchain", "career & networking"]), 
             "Marina Bay Convention Center", "2025-08-15", "0900H - 1700H", 150, 1, "https://cdn.prod.website-files.com/67ccce3ca9de94dc1fafaee6/6852eb78fd649405d57a7864_BG%20Tech%20Innovation.png"),
            (2, "Morning Fitness Bootcamp", "High-intensity outdoor workout session for all fitness levels", 
             "Fitness", json.dumps(["mental health", "nutrition", "running & marathons"]), 
             "Punggol Park", "2025-07-20", "1900H - 2100H", 25, 2, "https://static1.squarespace.com/static/5691e3f8a2bab8b5b8e2cc2e/t/57d751e36b8f5b4daf5cefb4/1473729002130/?format=1500w"),
            (3, "Modern Art Gallery Opening", "Exclusive preview of contemporary paintings and sculptures", 
             "Arts & Culture", json.dumps(["calligraphy & typography", "diy crafts & upcycling", "painting & drawing", "photography", "urban sketching", "video production"]), 
             "Marina Bay Convention Centre", "2025-07-25", "2000H - 2230H", 0, 3, "https://sgmagazine.com/wp-content/uploads/2023/12/ArtScience-Museum-at-Marina-Bay-Sands.jpg"),
            (4, "Jazz Under the Stars", "Live jazz performance in an intimate outdoor setting", 
             "Music", json.dumps(["foodie trails", "wine appreciation", "band", "karaoke"]), 
             "Blu Jaz Clarke Quay", "2025-08-05", "2000H - 2100H", 40, 4, "https://www.blujazcafe.net/products/5a67480.jpg"),
            (5, "Culinary Masterclass", "Learn advanced cooking techniques from professional chefs", 
             "Food & Drink", json.dumps(["coffee appreciation", "foodie trails", "wine appreciation"]), 
             "Palate Sensations", "2025-07-30", "1900H-2030H", 80, 5, "https://media.nedigital.sg/fairprice/images/9120d59a-b799-4ee1-ab1c-5afb878af8a9/Lifestyle%20Image.jpg"),
            (6, "Marathon Training Group", "Weekly running group preparing for the city marathon", 
             "Fitness", json.dumps(["running & marathons", "mental health"]), 
             "East Coast Park", "2025-07-15", "1900H - 2100H", 15, 4, "https://images.squarespace-cdn.com/content/v1/55b7f4ffe4b0a286c4c3499e/84d6fbf5-4a9f-4af6-bd3d-b526c4a3229d/training-for-a-marathon"),
            (7, "Startup Pitch Competition", "Watch entrepreneurs pitch their innovative business ideas", 
             "Business", json.dumps(["career & networking", "investing & financial literacy", "artificial intelligence", "data science", "software development", "web3 & blockchain"]), 
             "Tachyon@Tampines M-Works", "2025-08-10", "1000H - 1500H", 30, 3, "https://www.webintravel.com/wp-content/uploads/2025/05/featured-GSP-2025-Winners-1066x440.png"),
            (8, "Food Festival Downtown", "Taste cuisines from around the world at local restaurants", 
             "Food & Drink", json.dumps(["foodie trails", "local heritage & hidden gems", "weekend explorers"]), 
             "iLights@Marina Bay", "2025-08-01", "1900H - 2100H", 20, 2, "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ2HM7hGKBe7T4auSW1MXMGGmMoTpwC-WbOFw&s")
        ]
        
        cursor.executemany('''
            INSERT INTO events (id, title, description, category, tags, location, date, time, price, organiser_id, image_url) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', events_data)
    
    def get_all_users(self) -> List[Dict]:
        """Retrieve all users from the database"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, category, interests, preferred_day, office_location FROM users")
        users = []
        for row in cursor.fetchall():
            users.append({
                'id': row[0],
                'name': row[1],
                'category': row[2],
                'interests': json.loads(row[3]),
                'preferred_day': json.loads(row[4]) if row[4] else None,
                'office_location': row[5]
            })
        
        conn.close()
        return users
    
    def get_all_events(self) -> List[Dict]:
        """Retrieve all events from the database"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, title, description, category, tags, location, date, time, price, organiser_id, image_url FROM events")
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
                'time': row[7],
                'price': row[8],
                'organiser_id': row[9],
                'image_url': row[10]
            })
        
        conn.close()
        return events
    
    def get_user_by_id(self, user_id: int) -> Dict:
        """Get a specific user by ID"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, category, interests, preferred_day, office_location FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        
        if row:
            user = {
                'id': row[0],
                'name': row[1],
                'category': row[2],
                'interests': json.loads(row[3]),
                'preferred_day': json.loads(row[4]) if row[4] else None,
                'office_location': row[5]
            }
        else:
            user = None
        
        conn.close()
        return user
    
    def add_user(self, name: str, category: str, interests: List[str], preferred_day: List[str], office_location: str) -> bool:
        """Add a new user to the database"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (name, category, interests, preferred_day, office_location) VALUES (?, ?, ?, ?, ?)
            ''', (name, json.dumps(category), json.dumps(interests), json.dumps(preferred_day), office_location))
            conn.commit()
            success = True
        except sqlite3.Error:
            success = False
        
        conn.close()
        return success
    
    def add_event(self, title: str, description: str, category: str, tags: List[str], 
                  location: str, date: str, time: str, price: float, organiser_id: int, image_url: str) -> bool:
        """Add a new event to the database"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO events (title, description, category, tags, location, date, time, price, organiser_id, image_url) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (title, description, category, json.dumps(tags), location, date, time, price, organiser_id, image_url))
            conn.commit()
            success = True
        except sqlite3.Error:
            success = False
        
        conn.close()
        return success
    
    def register_user_for_event(self, user_id: int, event_id: int) -> bool:
        """Register a user for an event"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            from datetime import datetime
            cursor.execute('''
                INSERT INTO user_events (user_id, event_id, registration_date) 
                VALUES (?, ?, ?)
            ''', (user_id, event_id, datetime.now().isoformat()))
            conn.commit()
            success = True
        except sqlite3.Error:
            success = False
        
        conn.close()
        return success
    
    def unregister_user_from_event(self, user_id: int, event_id: int) -> bool:
        """Unregister a user from an event"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                DELETE FROM user_events WHERE user_id = ? AND event_id = ?
            ''', (user_id, event_id))
            conn.commit()
            success = True
        except sqlite3.Error:
            success = False
        
        conn.close()
        return success
    
    def get_user_events(self, user_id: int) -> List[Dict]:
        """Get all events a user is registered for"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT e.id, e.title, e.description, e.category, e.tags, e.location, e.date, e.time, e.price, e.organiser_id, e.image_url, ue.registration_date
            FROM events e
            JOIN user_events ue ON e.id = ue.event_id
            WHERE ue.user_id = ?
            ORDER BY e.date
        ''', (user_id,))
        
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
                'time': row[7],
                'price': row[8],
                'organiser_id': row[9],
                'image_url': row[10],
                'registration_date': row[11]
            })
        
        conn.close()
        return events
    
    def is_user_registered(self, user_id: int, event_id: int) -> bool:
        """Check if a user is registered for an event"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM user_events WHERE user_id = ? AND event_id = ?
        ''', (user_id, event_id))
        
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    
    def get_event_by_id(self, event_id: int) -> Dict | None:
        """Get a specific event by ID"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, title, description, category, tags, location, date, time, price, organiser_id, image_url FROM events WHERE id = ?", (event_id,))
        row = cursor.fetchone()
        
        conn.close()
        if row:
            return {
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'category': row[3],
                'tags': json.loads(row[4]),
                'location': row[5],
                'date': row[6],
                'time': row[7],
                'price': row[8],
                'organiser_id': row[9],
                'image_url': row[10]
            }
        return None

    def get_organiser_id_for_event(self, event_id: int) -> int | None:
        """Get the organiser_id for a given event_id"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT organiser_id FROM events WHERE id = ?", (event_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def is_organiser_of_event(self, user_id: int, event_id: int) -> bool:
        """Check if a user is the organizer of a specific event"""
        organiser_id = self.get_organiser_id_for_event(event_id)
        return organiser_id == user_id

    def update_event(self, event_id: int, event_data: Dict) -> bool:
        """Update an existing event in the database"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE events
                SET title = ?, description = ?, category = ?, tags = ?, location = ?, date = ?, time = ?, price = ?, image_url = ?
                WHERE id = ?
            ''', (
                event_data['title'],
                event_data['description'],
                event_data['category'],
                json.dumps(event_data['tags']), # Store tags as JSON string
                event_data['location'],
                event_data['date'],
                event_data['time'],
                event_data['price'],
                event_data['image_url'],
                event_id
            ))
            conn.commit()
            success = True
        except sqlite3.Error as e:
            print(f"Error updating event {event_id}: {e}") # Use print for backend errors
            success = False
        
        conn.close()
        return success
    
    def get_preferences_by_interests(self,interest_list: List[str]) -> Dict[str, Dict[str, int]]:
        """
        For each interest in interest_list, compute frequency distributions
        of preferred_day and office_location among users whose interests include it.

        Returns:
            {
                interest: {
                    'preferred_day': {day: count, ...},
                    'office_location': {loc: count, ...}
                },
                ...
            }
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT interests, preferred_day, office_location FROM users")
        rows = cursor.fetchall()
        conn.close()

        result: Dict[str, Dict[str, Counter]] = {}
        for interest in interest_list:
            day_ctr = Counter()
            office_ctr = Counter()
            for interests_json, days_json, office in rows:
                try:
                    user_interests = json.loads(interests_json)
                except json.JSONDecodeError:
                    continue
                if interest not in user_interests:
                    continue
                # Count preferred days (list)
                try:
                    days = json.loads(days_json) if days_json else []
                except json.JSONDecodeError:
                    days = []
                for d in days:
                    day_ctr[d] += 1
                # Count office_location (scalar)
                office_ctr[office] += 1
            result[interest] = {
                'preferred_day': dict(day_ctr),
                'office_location': dict(office_ctr)
            }
        return result
    
