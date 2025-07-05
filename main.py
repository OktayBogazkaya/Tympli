import streamlit as st
from utils.supabase_auth import auth_screen, sign_out
from utils.database import init_supabase

# Initialize Supabase
supabase = init_supabase()

def main_home():
    """Main home page with basic info"""
    st.title("🛍️ Welcome to Tympli")
    st.subheader("Find Deals Simply")

# Initialize session state
if "user_email" not in st.session_state:
    st.session_state["user_email"] = None

if "last_search_result" not in st.session_state:
    st.session_state["last_search_result"] = None

if "last_search_query" not in st.session_state:
    st.session_state["last_search_query"] = None

# Main app logic
if st.session_state.get("user_email"):
    # User is authenticated - show sidebar and main content
    with st.sidebar:
        st.page_link("pages/1_🏠_Home.py", label="Home", icon="🏠")
        st.page_link("pages/2_🔎_Product_Search.py", label="Product Search", icon="🔍")
        st.page_link("pages/3_📋_Watchlist.py", label="Watchlist", icon="📋")
        st.markdown("---")
        if st.button("Logout"):
            sign_out()
            st.rerun()
    
    # Show main content
    st.switch_page("pages/1_🏠_Home.py")
else:
    # User not authenticated - show ONLY login screen (no sidebar)
    auth_screen()