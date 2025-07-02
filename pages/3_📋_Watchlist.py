import streamlit as st
from utils.supabase_auth import sign_out
from utils.database import get_user_watchlist, remove_from_watchlist, get_or_create_user

# Set page config
st.set_page_config(
    page_title="Tympli - Watchlist",
    page_icon="📋",
    layout="wide"
)

# Initialize session state if needed
if "user_email" not in st.session_state:
    st.session_state["user_email"] = None

# Check if user is authenticated - redirect to main if not
if not st.session_state.user_email:
    st.error("Please log in to access this page.")
    st.info("Redirecting to login page...")
    st.switch_page("main.py")

# Sidebar - Only show if authenticated (this check already passed above)
with st.sidebar:
    st.write(f"Welcome, {st.session_state.user_email}!")
    st.page_link("pages/1_🏠_Home.py", label="Home", icon="🏠")
    st.page_link("pages/2_🔎_Product_Search.py", label="Product Search", icon="🔍")
    st.page_link("pages/3_📋_Watchlist.py", label="Watchlist", icon="📋")
    st.markdown("---")
    if st.button("Logout"):
        sign_out()
        st.rerun()

# Main page content
st.title("📋 Your Watchlist")
st.write("Keep track of products you're interested in!")

# Get user and their watchlist
user = get_or_create_user(st.session_state.user_email)
if user:
    watchlist_items = get_user_watchlist(user["id"])
    
    if watchlist_items:
        st.info(f"You have {len(watchlist_items)} items in your watchlist")
        
        for item in watchlist_items:
            with st.container():
                col1, col2, col3 = st.columns([1, 4, 1])
                
                with col1:
                    if item.get("image_url"):
                        st.image(item["image_url"], width=100)
                    else:
                        st.markdown("📦")
                
                with col2:
                    st.markdown(f"**[{item['title']}]({item['url']})**")
                    st.markdown(f"🏪 Platform: **{item['platform']}**")
                    if item.get("rating"):
                        st.markdown(f"⭐ {item['rating']}")
                    if item.get("search_query"):
                        st.markdown(f"🔍 Found via: *{item['search_query']}*")
                    st.markdown(f"📅 Added: {item['created_at'][:10]}")
                
                with col3:
                    if st.button("🗑️ Remove", key=f"remove_{item['id']}", help="Remove from watchlist"):
                        if remove_from_watchlist(item["id"]):
                            st.success("Removed from watchlist!")
                            st.rerun()
                        else:
                            st.error("Failed to remove item")
                
                st.markdown("---")
    
    else:
        st.info("Your watchlist is empty!")
        st.markdown("""
        ### Get Started
        
        1. Go to **Product Search**
        2. Search for products you're interested in
        3. Click **📌 Add to Watchlist** on any product
        4. Come back here to see your saved items!
        """)
        
        if st.button("🔍 Start Searching", type="primary"):
            st.switch_page("pages/2_🔎 _product_search.py")

else:
    st.error("Unable to load user data. Please try logging in again.")