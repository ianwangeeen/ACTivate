import streamlit as st
import json
import pandas as pd
from typing import Dict, List, Tuple
import re
from setup_database import DatabaseManager
import sqlite3

# Sample data - Users and their interests
# USERS_DATA = {
#     "users": [
#         {
#             "id": 1,
#             "name": "Alice Johnson",
#             "interests": ["technology", "artificial intelligence", "startups", "networking", "innovation"]
#         },
#         {
#             "id": 2,
#             "name": "Bob Smith",
#             "interests": ["fitness", "running", "health", "outdoor activities", "sports"]
#         },
#         {
#             "id": 3,
#             "name": "Carol Davis",
#             "interests": ["art", "painting", "creativity", "museums", "culture"]
#         },
#         {
#             "id": 4,
#             "name": "David Wilson",
#             "interests": ["music", "concerts", "jazz", "live performance", "entertainment"]
#         },
#         {
#             "id": 5,
#             "name": "Eva Martinez",
#             "interests": ["cooking", "food", "recipes", "culinary arts", "restaurants"]
#         }
#     ]
# }

# # Sample events database
# EVENTS_DATA = {
#     "events": [
#         {
#             "id": 1,
#             "title": "Tech Innovation Summit 2025",
#             "description": "Join industry leaders discussing AI, startups, and cutting-edge technology",
#             "category": "Technology",
#             "tags": ["technology", "artificial intelligence", "startups", "innovation", "networking"],
#             "location": "Convention Center",
#             "date": "2025-08-15",
#             "price": 150
#         },
#         {
#             "id": 2,
#             "title": "Morning Fitness Bootcamp",
#             "description": "High-intensity outdoor workout session for all fitness levels",
#             "category": "Fitness",
#             "tags": ["fitness", "outdoor activities", "health", "sports", "exercise"],
#             "location": "City Park",
#             "date": "2025-07-20",
#             "price": 25
#         },
#         {
#             "id": 3,
#             "title": "Modern Art Gallery Opening",
#             "description": "Exclusive preview of contemporary paintings and sculptures",
#             "category": "Arts & Culture",
#             "tags": ["art", "painting", "culture", "museums", "creativity"],
#             "location": "Downtown Gallery",
#             "date": "2025-07-25",
#             "price": 0
#         },
#         {
#             "id": 4,
#             "title": "Jazz Under the Stars",
#             "description": "Live jazz performance in an intimate outdoor setting",
#             "category": "Music",
#             "tags": ["music", "jazz", "live performance", "entertainment", "concerts"],
#             "location": "Rooftop Venue",
#             "date": "2025-08-05",
#             "price": 40
#         },
#         {
#             "id": 5,
#             "title": "Culinary Masterclass",
#             "description": "Learn advanced cooking techniques from professional chefs",
#             "category": "Food & Drink",
#             "tags": ["cooking", "food", "culinary arts", "recipes", "learning"],
#             "location": "Culinary Institute",
#             "date": "2025-07-30",
#             "price": 80
#         },
#         {
#             "id": 6,
#             "title": "Marathon Training Group",
#             "description": "Weekly running group preparing for the city marathon",
#             "category": "Fitness",
#             "tags": ["running", "fitness", "sports", "health", "training"],
#             "location": "Various Routes",
#             "date": "2025-07-15",
#             "price": 15
#         },
#         {
#             "id": 7,
#             "title": "Startup Pitch Competition",
#             "description": "Watch entrepreneurs pitch their innovative business ideas",
#             "category": "Business",
#             "tags": ["startups", "innovation", "technology", "networking", "entrepreneurship"],
#             "location": "Business Hub",
#             "date": "2025-08-10",
#             "price": 30
#         },
#         {
#             "id": 8,
#             "title": "Food Festival Downtown",
#             "description": "Taste cuisines from around the world at local restaurants",
#             "category": "Food & Drink",
#             "tags": ["food", "restaurants", "culture", "festival", "dining"],
#             "location": "Downtown Square",
#             "date": "2025-08-01",
#             "price": 20
#         }
#     ]
# }

class EventRecommender:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def calculate_similarity(self, user_interests: List[str], event_tags: List[str]) -> float:
        """Calculate similarity between user interests and event tags"""
        if not user_interests or not event_tags:
            return 0.0
        
        # Convert to lowercase for case-insensitive matching
        user_interests_lower = [interest.lower() for interest in user_interests]
        event_tags_lower = [tag.lower() for tag in event_tags]
        
        # Calculate intersection
        common_interests = set(user_interests_lower) & set(event_tags_lower)
        
        # Calculate Jaccard similarity
        union_size = len(set(user_interests_lower) | set(event_tags_lower))
        if union_size == 0:
            return 0.0
        
        return len(common_interests) / union_size
    
    def recommend_events(self, user_id: int, similarity_threshold: float = 0.5) -> List[Tuple[Dict, float]]:
        """Recommend events for a specific user with similarity above threshold"""
        # user = next((u for u in self.users if u['id'] == user_id), None)
        user = self.db_manager.get_user_by_id(user_id)
        if not user:
            return []
        
        events = self.db_manager.get_all_events()
        recommendations = []
        for event in events:
            similarity = self.calculate_similarity(user['interests'], event['tags'])
            if similarity > similarity_threshold:  # Only include events above threshold
                recommendations.append((event, similarity))
        
        # Sort by similarity score (descending)
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        return recommendations
    
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

# Initialize the recommender
@st.cache_data
def load_recommender():
    db_manager = DatabaseManager()
    return EventRecommender(db_manager), db_manager

def main():
    st.set_page_config(
        page_title="Event Recommender",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for mobile-friendly design
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .user-info {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .event-card {
        background-color: white;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .similarity-score {
        background-color: #e8f4f8;
        padding: 0.5rem;
        border-radius: 5px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-header">🎯 Event Recommender</h1>', unsafe_allow_html=True)
    
    # Initialize recommender
    recommender, db_manager = load_recommender()

    users = db_manager.get_all_users()

    # Sidebar for user selection
    st.sidebar.title("👤 Select User")
    user_options = {f"{user['name']}": user['id'] for user in users}
    selected_user_name = st.sidebar.selectbox("Choose a user:", list(user_options.keys()))
    selected_user_id = user_options[selected_user_name]
    
    # Similarity threshold
    st.sidebar.markdown("### 🎯 Recommendation Criteria")
    st.sidebar.info("Only events with >50% similarity match will be shown")
    
    # Get user information
    user = db_manager.get_user_by_id(selected_user_id)
    
    if user:
        # Display user information
        st.markdown(f"""
        <div class="user-info">
            <h3>👤 {user['name']}</h3>
            <p><strong>Interests:</strong> {', '.join(user['interests'])}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Get recommendations (only events with >50% similarity)
        recommendations = recommender.recommend_events(selected_user_id, similarity_threshold=0.5)
        
        st.markdown("## Recommended")
        
        if recommendations:
            st.success(f"Found {len(recommendations)} event(s) recommended for you!")
            
            for i, (event, similarity) in enumerate(recommendations, 1):

                st.markdown(f"""
                    <div class="event-card">
                        <h4>🎫 {event['title']}</h4>
                        <p><strong>Category:</strong> {event['category']}</p>
                        <p><strong>Description:</strong> {event['description']}</p>
                        <p><strong>📍 Location:</strong> {event['location']}</p>
                        <p><strong>📅 Date:</strong> {event['date']}</p>
                        <p><strong>💰 Price:</strong> ${event['price']}</p>
                        <p><strong>🏷️ Tags:</strong> {', '.join(event['tags'])}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # col1, col2 = st.columns([3, 1])
                
                # with col1:
                #     st.markdown(f"""
                #     <div class="event-card">
                #         <h4>🎫 {event['title']}</h4>
                #         <p><strong>Category:</strong> {event['category']}</p>
                #         <p><strong>Description:</strong> {event['description']}</p>
                #         <p><strong>📍 Location:</strong> {event['location']}</p>
                #         <p><strong>📅 Date:</strong> {event['date']}</p>
                #         <p><strong>💰 Price:</strong> ${event['price']}</p>
                #         <p><strong>🏷️ Tags:</strong> {', '.join(event['tags'])}</p>
                #     </div>
                #     """, unsafe_allow_html=True)
                
                # with col2:
                #     st.markdown(f"""
                #     <div class="similarity-score">
                #         <strong>Match Score</strong><br>
                #         <span style="font-size: 1.5em; color: #1f77b4;">{similarity:.2%}</span>
                #     </div>
                #     """, unsafe_allow_html=True)
                
                st.markdown("---")
        else:
            st.warning("No events found with >50% similarity match. Try a different user or check back later for new events!")
    
    # Additional features in sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 App Features")
    st.sidebar.markdown("""
    - **Interest Matching**: Recommends events based on user interests
    - **Similarity Scoring**: Uses Jaccard similarity for matching
    - **Mobile Friendly**: Optimized for phone interfaces
    - **Real-time Updates**: Dynamic recommendations
    """)
    
    # Show all events option
    if st.sidebar.checkbox("Show All Events"):
        st.markdown("## 📋 All Available Events")
        for event in recommender.events:
            st.markdown(f"""
            <div class="event-card">
                <h4>{event['title']}</h4>
                <p><strong>Category:</strong> {event['category']}</p>
                <p><strong>Price:</strong> ${event['price']}</p>
                <p><strong>Date:</strong> {event['date']}</p>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()