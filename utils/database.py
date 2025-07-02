import streamlit as st
from supabase import create_client, Client

# Initialize Supabase client
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_supabase()

def get_or_create_user(email: str):
    """Get existing user or create new one"""
    try:
        result = supabase.table("users").select("*").eq("email", email).execute()
        
        if result.data:
            return result.data[0]
        else:
            # Create new user
            new_user = {"email": email}
            result = supabase.table("users").insert(new_user).execute()
            if result.data:
                return result.data[0]
            else:
                st.error("Failed to create user account")
                return None
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return None

def add_to_watchlist(user_id: str, product: dict, platform: str, search_query: str):
    """Add product to user's watchlist"""
    try:
        # Check if item already exists
        existing = supabase.table("watchlist").select("id").eq("user_id", user_id).eq("url", product["url"]).execute()
        
        if existing.data:
            st.warning("This product is already in your watchlist!")
            return False
        
        watchlist_item = {
            "user_id": user_id,
            "title": product["title"],
            "url": product["url"],
            "rating": product["rating"],
            "image_url": product["image_url"],
            "platform": platform,
            "search_query": search_query
        }
        
        result = supabase.table("watchlist").insert(watchlist_item).execute()
        if result.data:
            return True
        else:
            st.error("Failed to add item to watchlist")
            return False
    except Exception as e:
        st.error(f"Error adding to watchlist: {str(e)}")
        return False
    
def get_user_watchlist(user_id: str):
    """Get user's watchlist items"""
    try:
        result = supabase.table("watchlist").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return result.data
    except Exception as e:
        st.error(f"Error fetching watchlist: {str(e)}")
        return []

def remove_from_watchlist(watchlist_id: str):
    """Remove item from watchlist"""
    try:
        result = supabase.table("watchlist").delete().eq("id", watchlist_id).execute()
        return True
    except Exception as e:
        st.error(f"Error removing from watchlist: {str(e)}")
        return False
