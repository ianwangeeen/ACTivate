import streamlit as st
import json
import pandas as pd
from typing import Dict, List, Tuple
import re
from setup_database import DatabaseManager
import sqlite3
from datetime import datetime

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
    
    st.markdown('<h1 class="main-header">ACTivate</h1>', unsafe_allow_html=True)
    
    # Initialize recommender
    recommender, db_manager = load_recommender()

    users = db_manager.get_all_users()
    user_options = {f"{user['name']}": user['id'] for user in users}
    selected_user_name = st.sidebar.selectbox("Choose a user:", list(user_options.keys()))
    selected_user_id = user_options[selected_user_name]
    

    tab1, tab2 = st.tabs(["Home", "📅 My Events"])

    with tab1:
        recommendations_tab(recommender, db_manager, selected_user_id)
    
    with tab2:
        my_events_tab(db_manager, selected_user_id)
    
    # Move sidebar content to a separate function
    sidebar_content(db_manager)

def recommendations_tab(recommender, db_manager, selected_user_id):
    """Content for the recommendations tab"""
    
    # Get user information from database
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
        
        st.markdown("## 🎪 Recommended For You")
        
        if recommendations:
            st.success(f"Found {len(recommendations)} event(s) that may interest you!")
            
            for i, (event, similarity) in enumerate(recommendations, 1):
                col1, col2 = st.columns([3, 1])
                
                with col1:
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
                
                
                with col2:
                    # Registration button
                    is_registered = db_manager.is_user_registered(selected_user_id, event['id'])
                    if is_registered:
                        if st.button(f"✅ Registered", key=f"unreg_{event['id']}", type="secondary"):
                            if db_manager.unregister_user_from_event(selected_user_id, event['id']):
                                st.success("Unregistered successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to unregister.")
                    else:
                        if st.button(f"📝 Register", key=f"reg_{event['id']}", type="primary"):
                            if db_manager.register_user_for_event(selected_user_id, event['id']):
                                st.success("Registered successfully!")
                                st.rerun()
                            else:
                                st.error("Registration failed.")
                
                st.markdown("---")
        else:
            st.warning("There are no recommendations available at the moment. Please check back later or explore the All Events below!")

        st.markdown("## 📋 All Available Events")
        events = db_manager.get_all_events()
        for event in events:
            event_col, register_col = st.columns([3, 1])

            with event_col:
                st.markdown(f"""
                <div class="event-card">
                    <h4>{event['title']}</h4>
                    <p><strong>Category:</strong> {event['category']}</p>
                    <p><strong>Price:</strong> ${event['price']}</p>
                    <p><strong>Date:</strong> {event['date']}</p>
                </div>
                """, unsafe_allow_html=True)

            with register_col:
                if st.button(f"📝 Register", key=f"reg_all_{event['id']}", type="primary"):
                    if db_manager.register_user_for_event(selected_user_id, event['id']):
                        st.success("Registered successfully!")
                        st.rerun()
                    else:
                        st.error("Registration failed.")

def my_events_tab(db_manager, selected_user_id):
    """Content for the My Events tab"""
    user = db_manager.get_user_by_id(selected_user_id)
    
    if user:
        st.markdown(f"## 📅 {user['name']}'s Registered Events")
        
        # Get user's registered events
        user_events = db_manager.get_user_events(selected_user_id)
        
        if user_events:
            st.success(f"You are registered for {len(user_events)} events!")
            
            # Sort events by date
            user_events.sort(key=lambda x: x['date'])
            
            for event in user_events:
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Parse registration date for display
                    try:
                        reg_date = datetime.fromisoformat(event['registration_date'])
                        reg_date_str = reg_date.strftime("%Y-%m-%d %H:%M")
                    except:
                        reg_date_str = event['registration_date']
                    
                    st.markdown(f"""
                    <div class="event-card">
                        <h4>🎫 {event['title']}</h4>
                        <p><strong>Category:</strong> {event['category']}</p>
                        <p><strong>Description:</strong> {event['description']}</p>
                        <p><strong>📍 Location:</strong> {event['location']}</p>
                        <p><strong>📅 Date:</strong> {event['date']}</p>
                        <p><strong>💰 Price:</strong> ${event['price']}</p>
                        <p><strong>🏷️ Tags:</strong> {', '.join(event['tags'])}</p>
                        <p><strong>✅ Registered:</strong> {reg_date_str}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    # Unregister button
                    if st.button(f"❌ Unregister", key=f"unreg_my_{event['id']}", type="secondary"):
                        if db_manager.unregister_user_from_event(selected_user_id, event['id']):
                            st.success("Unregistered successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to unregister.")
                
                st.markdown("---")

        else:
            st.info("You haven't registered for any events yet. Check out the Recommendations tab to find events you might like!")
            
            # Quick link to recommendations
            # if st.button("🔍 Find Events to Register For", type="primary"):
            #     st.switch_page("recommendations")

def sidebar_content(db_manager):
    """Sidebar content moved to separate function"""
    # Admin section for adding new data
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔧 Admin Panel")
    
    # Add new user
    # if st.sidebar.expander("Add New User"):
    #     new_user_name = st.text_input("User Name")
    #     new_user_interests = st.text_area("Interests (comma-separated)")
        
    #     if st.button("Add User"):
    #         if new_user_name and new_user_interests:
    #             interests_list = [interest.strip() for interest in new_user_interests.split(',')]
    #             if db_manager.add_user(new_user_name, interests_list):
    #                 st.success("User added successfully!")
    #                 st.rerun()
    #             else:
    #                 st.error("Failed to add user.")
    
    # Add new event
    # if st.sidebar.expander("Add New Event"):
    #     new_event_title = st.text_input("Event Title")
    #     new_event_desc = st.text_area("Event Description")
    #     new_event_category = st.text_input("Category")
    #     new_event_tags = st.text_area("Tags (comma-separated)")
    #     new_event_location = st.text_input("Location")
    #     new_event_date = st.date_input("Date")
    #     new_event_price = st.number_input("Price", min_value=0.0, value=0.0)
        
    #     if st.button("Add Event"):
    #         if all([new_event_title, new_event_desc, new_event_category, new_event_tags, new_event_location]):
    #             tags_list = [tag.strip() for tag in new_event_tags.split(',')]
    #             if db_manager.add_event(new_event_title, new_event_desc, new_event_category, 
    #                                   tags_list, new_event_location, str(new_event_date), new_event_price):
    #                 st.success("Event added successfully!")
    #                 st.rerun()
    #             else:
    #                 st.error("Failed to add event.")
    
    # Database status
    st.sidebar.markdown("### 📊 Database Status")
    total_users = len(db_manager.get_all_users())
    total_events = len(db_manager.get_all_events())
    st.sidebar.metric("Total Users", total_users)
    st.sidebar.metric("Total Events", total_events)

if __name__ == "__main__":
    main()