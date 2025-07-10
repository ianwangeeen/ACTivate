import streamlit as st
import json
import pandas as pd
from typing import Dict, List, Tuple
import re
from setup_database import DatabaseManager
import sqlite3
from datetime import datetime
import folium
from streamlit_folium import folium_static
import requests
import time
from geopy.geocoders import Nominatim
import os

# Location coordinates for Singapore venues (you can add more as needed)
SINGAPORE_LOCATIONS = {
    'Marina Bay Convention Center': (1.2825, 103.8596),
    'Marina Bay Convention Centre': (1.2825, 103.8596),
    'Punggol Park': (1.3707, 103.9063),
    'Blu Jaz Clarke Quay': (1.2883, 103.8438),
    'Palate Sensations': (1.3082, 103.8238),
    'East Coast Park': (1.2966, 103.8672),
    'Tachyon@Tampines M-Works': (1.3457, 103.9421),
    'iLights@Marina Bay': (1.2823, 103.8579),
    'Singapore': (1.3521, 103.8198)  # Default fallback
}

def get_location_coordinates(location_name: str) -> Tuple[float, float]:
    """Get coordinates for a location, with fallback to Singapore center"""
    # Check if we have predefined coordinates
    if location_name in SINGAPORE_LOCATIONS:
        return SINGAPORE_LOCATIONS[location_name]
    
    # Try to geocode the location
    try:
        geolocator = Nominatim(user_agent="event_recommender")
        location = geolocator.geocode(f"{location_name}, Singapore")
        if location:
            return (location.latitude, location.longitude)
    except:
        pass
    
    # Fallback to Singapore center
    return SINGAPORE_LOCATIONS['Singapore']

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

def create_event_map(events: List[Dict], selected_user_id: int, db_manager: DatabaseManager) -> folium.Map:
    """Create a folium map with event markers"""
    # Center the map on Singapore
    singapore_center = [1.3521, 103.8198]
    m = folium.Map(location=singapore_center, zoom_start=11)
    
    # Get user for personalized recommendations
    user = db_manager.get_user_by_id(selected_user_id)
    recommender = EventRecommender(db_manager)
    
    # Get recommendations for color coding
    recommendations = recommender.recommend_events(selected_user_id, 0.1)  # Lower threshold for more variety
    recommended_event_ids = [event['id'] for event, similarity in recommendations]
    
    # Create a mapping of event IDs to similarity scores
    similarity_scores = {event['id']: similarity for event, similarity in recommendations}
    
    for event in events:
        lat, lon = get_location_coordinates(event['location'])
        
        # Determine marker color based on recommendation status
        if event['id'] in recommended_event_ids:
            similarity = similarity_scores[event['id']]
            if similarity > 0.7:
                color = 'red'  # High similarity
                icon_color = 'white'
            elif similarity > 0.5:
                color = 'orange'  # Medium similarity
                icon_color = 'white'
            else:
                color = 'yellow'  # Low similarity
                icon_color = 'black'
        else:
            color = 'blue'  # Not recommended
            icon_color = 'white'
        
        # Check if user is registered for this event
        is_registered = db_manager.is_user_registered(selected_user_id, event['id'])
        if is_registered:
            color = 'green'  # User is registered
            icon_color = 'white'
        
        # Create popup content
        popup_content = f"""
        <div style="width: 250px;">
            <h4>{event['title']}</h4>
            <p><strong>Category:</strong> {event['category']}</p>
            <p><strong>Date:</strong> {format_date(event['date'])}</p>
            <p><strong>Time:</strong> {event['time']}</p>
            <p><strong>Price:</strong> {format_price(event['price'])}</p>
            <p><strong>Location:</strong> {event['location']}</p>
            <p><strong>Tags:</strong> {', '.join(event['tags'])}</p>
            <p>{event['description'][:100]}...</p>
            {'✅ Registered' if is_registered else ''}
        </div>
        """
        
        # Add marker to map
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_content, max_width=300),
            tooltip=f"{event['title']} - {format_date(event['date'])}",
            icon=folium.Icon(color=color, icon='calendar', prefix='fa')
        ).add_to(m)
    
    return m

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

def login_screen():
    """Displays the login screen."""
    st.title("Login to ACTivate")

    st.markdown("""
        <style>
        .login-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 70vh;
            background-color: #f0f2f6;
            border-radius: 10px;
            padding: 2rem;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            max-width: 500px;
            margin: auto;
        }
        .login-input {
            width: 100%;
            padding: 0.75rem;
            margin-bottom: 1rem;
            border: 1px solid #ccc;
            border-radius: 5px;
        }
        .login-button {
            width: 100%;
            padding: 0.75rem;
            background-color: #1f77b4;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1.1rem;
        }
        .login-button:hover {
            background-color: #1a5e8a;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.subheader("Please enter your credentials")

        username = st.text_input("Username", key="username_input")
        password = st.text_input("Password", type="password", key="password_input")

        if st.button("Login", key="login_button", help="Click to log in"):
            # Basic hardcoded authentication for demonstration
            if username == "admin" and password == "password":
                st.session_state.logged_in = True
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid username or password.")
        st.markdown('</div>', unsafe_allow_html=True)



def map_view_tab(db_manager: DatabaseManager, selected_user_id: int):
    """Content for the map view tab"""
    user = db_manager.get_user_by_id(selected_user_id)
    
    if user:
        st.markdown(f"## 🗺️ Map View - {user['name']}")
        
        # Get all events for filtering
        all_events = db_manager.get_all_events()
        
        # Filter controls
        col1, col2 = st.columns(2)
        
        with col1:
            filter_type = st.selectbox(
                "Filter by:",
                ["All", "Category", "Location", "Price Range", "Tags", "Date"],
                key="map_filter_type"
            )
        
        with col2:
            filter_options = get_filter_options(all_events, filter_type)
            filter_value = st.selectbox(
                "Select value:",
                filter_options,
                key="map_filter_value"
            )
        
        # Apply filters
        filtered_events = filter_events(all_events, filter_type, filter_value)
        
        # Map legend
        st.markdown("""
        <div class="map-legend">
            <h4>🎨 Map Legend:</h4>
            <p>🔴 Red: Highly recommended for you (>70% match)</p>
            <p>🟠 Orange: Recommended (50-70% match)</p>
            <p>🟡 Yellow: Somewhat related (10-50% match)</p>
            <p>🔵 Blue: Other events</p>
            <p>🟢 Green: Events you're registered for</p>
        </div>
        """, unsafe_allow_html=True)
        
        if filtered_events:
            # Create and display map
            event_map = create_event_map(filtered_events, selected_user_id, db_manager)
            folium_static(event_map, width=1200, height=600)
            
            # Display summary
            if filter_type == "All":
                st.info(f"Showing {len(filtered_events)} events on the map")
            else:
                st.info(f"Showing {len(filtered_events)} events matching '{filter_type}: {filter_value}'")
            
            # Optional: Show event list below map
            with st.expander("📋 Event List", expanded=False):
                for event in filtered_events:
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**{event['title']}**")
                        st.write(f"📍 {event['location']} | 📅 {format_date(event['date'])} | 💰 {format_price(event['price'])}")
                        st.write(f"Category: {event['category']}")
                    
                    with col2:
                        is_registered = db_manager.is_user_registered(selected_user_id, event['id'])
                        if is_registered:
                            st.write("✅ Registered")
                        else:
                            if st.button(f"Register", key=f"map_reg_{event['id']}", type="primary"):
                                if db_manager.register_user_for_event(selected_user_id, event['id']):
                                    st.success("Registered!")
                                    st.rerun()
                    
                    st.markdown("---")
        else:
            st.warning(f"No events found matching '{filter_type}: {filter_value}'")

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
                        <img src="{event['image_url']}" alt="{event['title']}" style="width:800px; height:400px; object-fit:cover; border-radius:8px; margin-bottom:1rem;" />
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
                        <h4>🎫 {event['title']}</h4>
                        <img src="{event['image_url']}" alt="{event['title']}" style="width:800px; height:400px; object-fit:cover; border-radius:8px; margin-bottom:1rem;" />
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
                        <img src="{event['image_url']}" alt="{event['title']}" style="width:800px; height:400px; object-fit:cover; border-radius:8px; margin-bottom:1rem;" />
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

def edit_event_tab(db_manager: DatabaseManager, event_id: int, current_user_id: int):
    """Content for the Edit Event tab"""
    st.markdown(f"## ✏️ Edit Event (ID: {event_id})")

    event = db_manager.get_event_by_id(event_id)
    event_organiser_id = db_manager.get_organiser_id_for_event(event_id) # Assuming this method exists

    
    if not event:
        st.error(f"Event with ID {event_id} not found.")
        st.session_state.event_to_edit_id = None
        st.session_state.active_tab = "Home"
        st.rerun()
        return
    
    if event_organiser_id != current_user_id:
        st.warning("You are not authorized to edit this event.")
        st.session_state.event_to_edit_id = None
        st.session_state.active_tab = "Home"
        st.rerun()
        return


    st.markdown("---")
    st.write("Edit the details of the event below:")

    with st.form(key=f"edit_event_form_{st.session_state.edit_tab_key}"):
        st.subheader("Event Details")
        
        # Get organiser_id (this should ideally be non-editable or derived)
        # For simplicity, I'm making it display-only here. If you need to change it,
        # you'd need more complex logic (e.g., selecting a different organizer user).
        st.write(f"**Organizer ID:** {event['organiser_id']}") 

        edited_title = st.text_input("Title", value=event['title'])
        edited_category = st.text_input("Category", value=event['category'])
        edited_description = st.text_area("Description", value=event['description'])
        edited_location = st.text_input("Location", value=event['location'])
        
        # Handle date and time
        try:
            default_date = datetime.strptime(event['date'], "%Y-%m-%d").date()
        except ValueError:
            default_date = datetime.now().date() # Fallback
        edited_date = st.date_input("Date", value=default_date)
        edited_time = st.text_input("Time (HH:MM)", value=event['time']) # Consider using st.time_input for better UI
        
        edited_price = st.number_input("Price", value=float(event['price']), min_value=0.0, format="%.2f")
        edited_image_url = st.text_input("Image URL", value=event['image_url'])
        
        # Tags input: convert list to comma-separated string for editing, then back to list
        edited_tags_str = st.text_input("Tags (comma-separated)", value=", ".join(event['tags']))
        edited_tags = [tag.strip() for tag in edited_tags_str.split(',') if tag.strip()]

        st.markdown("---")
        submit_button = st.form_submit_button("Save Changes", type="primary")

        if submit_button:
            # Validate inputs if necessary (e.g., date format, time format)
            # For simplicity, assuming valid inputs for now

            updated_event_data = {
                'title': edited_title,
                'category': edited_category,
                'description': edited_description,
                'location': edited_location,
                'date': edited_date.strftime("%Y-%m-%d"),
                'time': edited_time,
                'price': edited_price,
                'image_url': edited_image_url,
                'tags': edited_tags # This will be stored as JSON in DB
            }

            if db_manager.update_event(event_id, updated_event_data):
                st.success(f"Event '{edited_title}' (ID: {event_id}) updated successfully!")
                # After successful save, redirect to Home or My Events tab
                st.session_state.event_to_edit_id = None # Clear event to edit
                st.session_state.active_tab = "Home" # Go back to home
                st.rerun()
            else:
                st.error("Failed to update event. Please check the input and try again.")
    
    if st.button("Cancel Edit", type="secondary"):
        st.session_state.event_to_edit_id = None
        st.session_state.active_tab = "Home"
        st.rerun()
    
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
    .map-legend {
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
    
    # Initialize session state for active tab and event to edit
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "Home"
    if 'event_to_edit_id' not in st.session_state:
        st.session_state.event_to_edit_id = None
    if 'edit_tab_key' not in st.session_state:
        st.session_state.edit_tab_key = 0 # To force re-render edit tab if event_to_edit_id changes

    tab_titles = ["Home", "📅 My Events", "🗺️ Map View", "✏️ Edit Event"]
    
    # Determine the index of the active tab
    try:
        active_tab_index = tab_titles.index(st.session_state.active_tab)
    except ValueError:
        active_tab_index = 0 # Default to Home if not found

    tab1, tab2, tab3, tab4 = st.tabs(tab_titles)

    with tab1:
        recommendations_tab(recommender, db_manager, selected_user_id)
            
    with tab2:
        my_events_tab(db_manager, selected_user_id)
    
    with tab3:
        map_view_tab(db_manager, selected_user_id)

    with tab4:
        edit_event_tab(db_manager, 1, selected_user_id)
    
    sidebar_content(db_manager)

if __name__ == "__main__":
    main()