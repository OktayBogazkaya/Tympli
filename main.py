import streamlit as st
import asyncio
import json
import base64
from typing import List
from pydantic import BaseModel, Field  
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client  # Official Smithery.ai client
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from supabase import create_client, Client
from supabase_auth import auth_screen, sign_out

# Constants
PLATFORMS = ["Amazon", "Walmart", "Best Buy", "Ebay", "Target", "Costco", "Five Below", "Newegg"]

# Smithery.ai configuration - Official BrightData MCP server
SMITHERY_API_KEY = st.secrets.get("SMITHERY_API_KEY", "")  # Your Smithery API key

# Initialize Supabase client
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_supabase()

# Pydantic models (unchanged)
class Hit(BaseModel):
    title: str
    url: str
    rating: str
    image_url: str

class PlatformBlock(BaseModel):
    platform: str
    hits: List[Hit]

class ProductSearchResponse(BaseModel):
    platforms: List[PlatformBlock]

# Model setup (unchanged)
model = ChatOpenAI(
    model="gpt-4o",
    api_key=st.secrets["OPENAI_API_KEY"]
)

def create_smithery_url():
    """Create Smithery.ai MCP server URL with configuration"""
    # BrightData MCP configuration (same as your original npx env vars)
    config = {
        "apiToken": st.secrets["API_TOKEN"],
        "browserAuth": st.secrets["BROWSER_AUTH"], 
        "webUnlockerZone": st.secrets["WEB_UNLOCKER_ZONE"]
    }
    
    # Encode config in base64 as required by Smithery.ai
    config_b64 = base64.b64encode(json.dumps(config).encode()).decode()
    
    # Create the official Smithery.ai BrightData MCP URL
    url = f"https://server.smithery.ai/@luminati-io/brightdata-mcp/mcp?config={config_b64}&api_key={SMITHERY_API_KEY}"
    
    return url

SYSTEM_PROMPT = (
    "To find products, first use the search_egine tool. When finding products, use the web_data tool for the platform. "
    "If none exists, scrape as markdown. "
    "Example: Don't use web_data_bestbuy_products for search. Use it only for getting data on specific products you already found in search."
)

# Database functions (unchanged - keeping all your existing database functions)
def get_or_create_user(email: str):
    """Get existing user or create new one"""
    try:
        result = supabase.table("users").select("*").eq("email", email).execute()
        
        if result.data:
            return result.data[0]
        else:
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

# MODIFIED: Async agent call for Smithery.ai using official method
async def run_agent(query, platforms):
    """Run agent using Smithery.ai hosted BrightData MCP server"""
    try:
        # Create Smithery.ai URL with configuration
        smithery_url = create_smithery_url()
        
        # Connect using official Smithery.ai streamable HTTP client
        async with streamablehttp_client(smithery_url) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                # Initialize the connection
                await session.initialize()
                
                # Load MCP tools from the session
                tools = await load_mcp_tools(session)
                
                # Create agent with tools and response format
                agent = create_react_agent(model, tools, response_format=ProductSearchResponse)

                prompt = f'{query}\n\nPlatforms: {",".join(platforms)}'
                result = await agent.ainvoke({
                    'messages': [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ]
                })

                print("Raw agent result:", result)
                structured = result["structured_response"]
                print(f"Structured response:", structured.model_dump(mode="json"))
                return structured.model_dump()
            
    except Exception as e:
        print(f"Error connecting to Smithery.ai MCP server: {str(e)}")
        st.error(f"Smithery.ai connection error: {str(e)}")
        return None

# Rest of your functions remain unchanged
def display_product_search():
    """Display product search interface"""
    
    query = st.text_input("Enter a product or search phrase:", placeholder="e.g. wireless headphones")
    selected_platforms = st.multiselect("Select platforms:", PLATFORMS, default=["Amazon"])

    if st.button("Search") and query and selected_platforms:
        with st.spinner("Running agent via Smithery.ai BrightData MCP... this may take a moment..."):
            result = asyncio.run(run_agent(query, selected_platforms))

        if result and "platforms" in result:
            st.session_state.last_search_result = result
            st.session_state.last_search_query = query
    
    if st.session_state.last_search_result:
        for platform in st.session_state.last_search_result["platforms"]:
            st.subheader(platform["platform"])
            
            for i, hit in enumerate(platform["hits"]):
                col1, col2, col3 = st.columns([1, 4, 1])
                
                with col1:
                    st.image(hit["image_url"], width=100)
                
                with col2:
                    st.markdown(f"**[{hit['title']}]({hit['url']})**")
                    st.markdown(f"⭐ {hit['rating']}")
                
                with col3:
                    button_key = f"add_{platform['platform']}_{i}_{hit['url'][:20]}"
                    if st.button("Add to Watchlist", key=button_key):
                        user = get_or_create_user(st.session_state.user_email)
                        if user:
                            success = add_to_watchlist(user["id"], hit, platform["platform"], st.session_state.last_search_query)
                            if success:
                                st.success("Added to watchlist!")
                
                st.markdown("---")

def display_watchlist():
    """Display user's watchlist"""
    st.header("📋 Your Watchlist")
    
    user = get_or_create_user(st.session_state.user_email)
    if not user:
        st.error("Error loading user data")
        return
        
    watchlist_items = get_user_watchlist(user["id"])
        
    if not watchlist_items:
        st.info("Your watchlist is empty. Search for products and add them to your watchlist!")
        return
    
    platforms_data = {}
    for item in watchlist_items:
        platform = item["platform"]
        if platform not in platforms_data:
            platforms_data[platform] = []
        platforms_data[platform].append(item)
    
    for platform, items in platforms_data.items():
        st.subheader(f"{platform} ({len(items)} items)")
        
        for item in items:
            col1, col2, col3 = st.columns([1, 4, 1])
            
            with col1:
                if item["image_url"]:
                    st.image(item["image_url"], width=100)
            
            with col2:
                st.markdown(f"**[{item['title']}]({item['url']})**")
                st.markdown(f"⭐ {item['rating']}")
                st.markdown(f"*Added from search: {item['search_query']}*")
                st.markdown(f"*Added on: {item['created_at'][:10]}*")
            
            with col3:
                if st.button("Remove", key=f"remove_{item['id']}"):
                    if remove_from_watchlist(item["id"]):
                        st.success("Removed from watchlist!")
                        st.rerun()
            
            st.markdown("---")

def main_app():
    """Main application interface"""
    
    st.set_page_config(
        page_title="Tympli",
        page_icon="🛍️",
        #layout="wide",
        initial_sidebar_state="auto"
    )

    st.header("🛍️ Tympli - Find Deals Simply. ")
    
    with st.sidebar:
        st.sidebar.write(f"Welcome, {st.session_state.user_email}!")

        if st.sidebar.button("Logout"):
            sign_out()
    
    tab1, tab2 = st.tabs(["🔎 Product Search", "📋 Watchlist"])
    
    with tab1:
        display_product_search()
    
    with tab2:
        display_watchlist()

# Initialize session state
if "user_email" not in st.session_state:
    st.session_state["user_email"] = None

if "last_search_result" not in st.session_state:
    st.session_state["last_search_result"] = None

if "last_search_query" not in st.session_state:
    st.session_state["last_search_query"] = None

# Main app logic
if st.session_state.user_email:
    main_app()
else:
    auth_screen()
