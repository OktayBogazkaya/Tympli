import streamlit as st
from utils.supabase_auth import sign_out
import streamlit.components.v1 as components

# Check if user is authenticated - redirect to main if not
if not st.session_state.get("user_email"):
    st.error("Please log in to access this page.")
    st.info("Redirecting to login page...")
    st.switch_page("main.py")

# Sidebar - Only show if authenticated (this check already passed above)
with st.sidebar:
    st.page_link("pages/1_🏠_Home.py", label="Home", icon="🏠")
    st.page_link("pages/2_🔎_Product_Search.py", label="Product Search", icon="🔍")
    st.page_link("pages/3_📋_Watchlist.py", label="Watchlist", icon="📋")
    st.markdown("---")
    if st.button("Logout"):
        sign_out()
        st.rerun()

def main_home():
    """Main home page with basic info"""
    st.title("🛍️ Welcome to Tympli - Find Deals Simply")

    st.markdown("""
    ## What is Tympli?
    
    Tympli is your ultimate deal-hunting companion that helps you find the best products and prices across multiple eCommerce platforms. 
    """)

    st.subheader("🎥 See Tympli in Action")

    components.iframe("https://screen.studio/share/udXpsOF2", height=400)


    st.write("---")
    st.subheader("⭐️ Features")
    
    st.markdown("""
        - **Multi-Platform Search**: Search across Amazon, Walmart, Best Buy, eBay, Target, Costco, Five Below, and Newegg
        - **Smart Comparison**: Get results from multiple platforms in one search
        - **Personal Watchlist**: Save interesting products to track later
        - **Real-time Data**: Get up-to-date product information and ratings
        """)
    st.write("---")
    st.subheader("⚙️ How it works")  

    st.markdown("""
        1. **Search**: Enter what you're looking for in the Product Search page
        2. **Compare**: View results from multiple platforms side by side
        3. **Save**: Add interesting products to your personal watchlist
        4. **Track**: Keep track of your saved items in the Watchlist page
        """)
    
    # --- Pricing Section ---

    st.write("---")
    st.subheader("💳 Pricing Plans (Comming Soon)")

    # Optional: Stripe links
    stripe_link_starter = st.secrets["stripe_link_starter"]
    stripe_link_basic = st.secrets["stripe_link_basic"]
    stripe_link_pro = st.secrets["stripe_link_pro"]

    # Three-column layout
    col1, col2, col3 = st.columns(3, border=True)

    with col1:
        st.markdown("### 🚀 Starter")
        st.markdown("**$0 / month**")
        st.link_button("Subscribe", url=stripe_link_starter, disabled=True)
        st.write("Ideal for beginners who want to try it out.")
        st.write("**Includes:**")
        st.markdown("""
        - ✅ Product Search  
        - ✅ Watchlist  
        """)

    with col2:
        st.markdown("### 🔔 Basic")
        st.markdown("**$19.99 / month**")
        st.link_button("Subscribe", url=stripe_link_basic, disabled=True)
        st.write("Great for users who want notifications.")
        st.write("**Includes:**")
        st.markdown("""
        - ✅ Everything in Starter  
        - ✅ Notifications  
        """)

    with col3:
        st.markdown("### 💼 Pro")
        st.markdown("**$49.99 / month**")
        st.link_button("Subscribe",url=stripe_link_pro, disabled=True)
        st.write("For power users who want all perks.")
        st.write("**Includes:**")
        st.markdown("""
        - ✅ Everything in Basic  
        - ✅ Telegram Group  
        - ✅ Daily Deals Newsletter  
        """)

    st.write("---")
    st.subheader("❓ FAQ")

    with st.expander("What platforms does Tympli search?"):
        st.write("""
        Tympli searches across popular e-commerce sites like **Amazon, Walmart, Best Buy, eBay, Target, Costco, Five Below**, and **Newegg** — all in one place.
        """)

    with st.expander("Do I need an account to use Tympli?"):
        st.write("""
        You can browse products without logging in. However, to **save items to your watchlist** or access personalized features, you'll need to create an account or log in.
        """)

    with st.expander("How often is product data updated?"):
        st.write("""
        Tympli fetches product data in **real time** from each platform when you search. This ensures you're seeing the **latest prices, ratings, and availability**.
        """)

    # Footer
    st.markdown("---")
    st.markdown("© 2025 Tympli. All rights reserved.")

# Show main content
main_home()