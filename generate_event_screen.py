import streamlit as st
import json
import pandas as pd
from typing import Dict, List, Tuple
import re
from setup_database import DatabaseManager
import sqlite3
from datetime import datetime


def format_date(date_str):
    # From "2025-08-15" to "15 Aug 25"
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d %b %y")
    except ValueError:
        return date_str
    
def format_price(price):
    # Format price to include dollar sign and two decimal places
    display_price = price
    if display_price == 0:
        return "Free"
    return f"${price:.2f}" if isinstance(price, (int, float)) else price

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

def filter_events(events: List[Dict], filter_type: str, filter_value: str) -> List[Dict]:
    """Filter events based on selected filter type and value"""
    if filter_type == "All" or filter_value == "All":
        return events
    
    filtered_events = []
    for event in events:
        if filter_type == "Category":
            if event['category'].lower() == filter_value.lower():
                filtered_events.append(event)
        elif filter_type == "Location":
            if event['location'].lower() == filter_value.lower():
                filtered_events.append(event)
        elif filter_type == "Price Range":
            price = float(event['price'])
            if filter_value == "Free" and price == 0:
                filtered_events.append(event)
            elif filter_value == "$1 - $50" and 1 <= price <= 50:
                filtered_events.append(event)
            elif filter_value == "$51 - $100" and 51 <= price <= 100:
                filtered_events.append(event)
            elif filter_value == "$100+" and price > 100:
                filtered_events.append(event)
        elif filter_type == "Tags":
            event_tags_lower = [tag.lower() for tag in event['tags']]
            if filter_value.lower() in event_tags_lower:
                filtered_events.append(event)
        elif filter_type == "Date":
            try:
                event_date = datetime.strptime(event['date'], '%Y-%m-%d')
                today = datetime.now()
                
                if filter_value == "Today":
                    if event_date.date() == today.date():
                        filtered_events.append(event)
                elif filter_value == "This Week":
                    days_diff = (event_date - today).days
                    if 0 <= days_diff <= 7:
                        filtered_events.append(event)
                elif filter_value == "This Month":
                    if event_date.month == today.month and event_date.year == today.year:
                        filtered_events.append(event)
                elif filter_value == "Future":
                    if event_date > today:
                        filtered_events.append(event)
            except ValueError:
                # If date parsing fails, include the event
                filtered_events.append(event)
    
    return filtered_events

def get_filter_options(events: List[Dict], filter_type: str) -> List[str]:
    """Get available filter options based on filter type"""
    if filter_type == "All":
        return ["All"]
    elif filter_type == "Category":
        categories = list(set(event['category'] for event in events))
        return ["All"] + sorted(categories)
    elif filter_type == "Location":
        locations = list(set(event['location'] for event in events))
        return ["All"] + sorted(locations)
    elif filter_type == "Price Range":
        return ["All", "Free", "$1 - $50", "$51 - $100", "$100+"]
    elif filter_type == "Tags":
        all_tags = set()
        for event in events:
            all_tags.update(event['tags'])
        return ["All"] + sorted(list(all_tags))
    elif filter_type == "Date":
        return ["All", "Today", "This Week", "This Month", "Future"]
    
    return ["All"]

# Initialize the recommender
@st.cache_data
def load_recommender():
    db_manager = DatabaseManager()
    return EventRecommender(db_manager), db_manager

def main():
    st.set_page_config(
        page_title="ACTivate",
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
    .filter-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border: 1px solid #dee2e6;
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
        
        # Filter Section - Place this before recommendations
        st.markdown("## 🔍 Filter Events")
        
        # Get all events for filtering
        all_events = db_manager.get_all_events()
        
        # Filter controls in a styled container
        with st.container():
            # st.markdown('<div class="filter-section">', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                filter_type = st.selectbox(
                    "Filter by:",
                    ["All", "Category", "Location", "Price Range", "Tags", "Date"],
                    key="filter_type"
                )
            
            with col2:
                # Get filter options based on selected filter type
                filter_options = get_filter_options(all_events, filter_type)
                filter_value = st.selectbox(
                    "Select value:",
                    filter_options,
                    key="filter_value"
                )
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Get recommendations (only events with >50% similarity)
        recommendations = recommender.recommend_events(selected_user_id, similarity_threshold=0.5)
        
        # Apply filters to recommendations
        if recommendations:
            recommended_events = [event for event, similarity in recommendations]
            filtered_recommended_events = filter_events(recommended_events, filter_type, filter_value)
            
            # Rebuild recommendations list with filtered events and their similarities
            filtered_recommendations = []
            for event, similarity in recommendations:
                if event in filtered_recommended_events:
                    filtered_recommendations.append((event, similarity))
        else:
            filtered_recommendations = []
        
        # Display filtered recommendations
        if filter_type == "All" or filter_value == "All":
            st.markdown("## 🎪 Recommended For You")
        else:
            st.markdown(f"## 🎪 Recommended For You - {filter_type}: {filter_value}")
        
        if filtered_recommendations:
            if filter_type == "All":
                st.info(f"Showing {len(filtered_recommendations)} recommended event(s)!")
            else:
                st.success(f"Found {len(filtered_recommendations)} recommended event(s) that match your filter!")
            
            for i, (event, similarity) in enumerate(filtered_recommendations, 1):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"""
                    <div class="event-card">
                        <h4>🎫 {event['title']}</h4>
                        <p><strong>Category:</strong> {event['category']}</p>
                        <p><strong>Description:</strong> {event['description']}</p>
                        <p><strong>📍 Location:</strong> {event['location']}</p>
                        <p><strong>📅 Date:</strong> {format_date(event['date'])}</p>
                        <p><strong>🕐 Time:</strong> {event['time']}</p>
                        <p><strong>💰 Price:</strong> {format_price(event['price'])}</p>
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
            if recommendations:
                st.info(f"No recommended events match the current filter ({filter_type}: {filter_value}). Try adjusting your filter or check all events below.")
            else:
                st.warning("There are no recommendations available at the moment. Please check back later or explore the All Events below!")

        # Apply filters to all events
        filtered_events = filter_events(all_events, filter_type, filter_value)
        
        # Display filtered events
        if filter_type == "All" or filter_value == "All":
            st.markdown("## 📋 All Available Events")
        else:
            st.markdown(f"## 📋 Events - {filter_type}: {filter_value}")
        
        if filtered_events:
            st.info(f"Showing {len(filtered_events)} event(s)")
            
            for event in filtered_events:
                event_col, register_col = st.columns([3, 1])

                with event_col:
                    st.markdown(f"""
                    <div class="event-card">
                        <h4>{event['title']}</h4>
                        <p><strong>Category:</strong> {event['category']}</p>
                        <p><strong>Description:</strong> {event['description']}</p>
                        <p><strong>📍 Location:</strong> {event['location']}</p>
                        <p><strong>📅 Date:</strong> {format_date(event['date'])}</p>
                        <p><strong>🕐 Time:</strong> {event['time']}</p>
                        <p><strong>💰 Price:</strong> {format_price(event['price'])}</p>
                        <p><strong>🏷️ Tags:</strong> {', '.join(event['tags'])}</p>
                    </div>
                    """, unsafe_allow_html=True)

                with register_col:
                    is_registered = db_manager.is_user_registered(selected_user_id, event['id'])
                    if is_registered:
                        if st.button(f"✅ Registered", key=f"unreg_all_{event['id']}", type="secondary"):
                            if db_manager.unregister_user_from_event(selected_user_id, event['id']):
                                st.success("Unregistered successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to unregister.")
                    else:
                        if st.button(f"📝 Register", key=f"reg_all_{event['id']}", type="primary"):
                            if db_manager.register_user_for_event(selected_user_id, event['id']):
                                st.success("Registered successfully!")
                                st.rerun()
                            else:
                                st.error("Registration failed.")
        else:
            st.warning(f"No events found for {filter_type}: {filter_value}")

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
                        <p><strong>🕐 Time:</strong> {event['time']}</p>
                        <p><strong>💰 Price:</strong> {format_price(event['price'])}</p>
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

def sidebar_content(db_manager):
    """Sidebar content moved to separate function"""
    # Admin section for adding new data
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔧 Admin Panel")
    
    # Database status
    st.sidebar.markdown("### 📊 Database Status")
    total_users = len(db_manager.get_all_users())
    total_events = len(db_manager.get_all_events())
    st.sidebar.metric("Total Users", total_users)
    st.sidebar.metric("Total Events", total_events)

if __name__ == "__main__":
    main()