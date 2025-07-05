import streamlit as st
import asyncio
import json
import base64
from typing import List
from pydantic import BaseModel, Field  
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from utils.supabase_auth import sign_out
from utils.database import get_or_create_user, add_to_watchlist

# Set page config
st.set_page_config(
    page_title="Tympli - Product Search",
    page_icon="🔍",
    layout="wide"
)

# Initialize session state if needed
if "user_email" not in st.session_state:
    st.session_state["user_email"] = None

if "last_search_result" not in st.session_state:
    st.session_state["last_search_result"] = None

if "last_search_query" not in st.session_state:
    st.session_state["last_search_query"] = None

# Check if user is authenticated - redirect to main if not
if not st.session_state.get("user_email"):
    st.error("Please log in to access this page.")
    st.info("Redirecting to login page...")
    st.switch_page("main.py")

# Constants
PLATFORMS = ["Amazon", "Walmart", "Ebay", "Target"]

# Smithery.ai configuration
SMITHERY_API_KEY = st.secrets.get("SMITHERY_API_KEY", "")

# Pydantic models
class Hit(BaseModel):
    title: str
    url: str
    price: str
    rating: str
    image_url: str

class PlatformBlock(BaseModel):
    platform: str
    hits: List[Hit]

class ProductSearchResponse(BaseModel):
    platforms: List[PlatformBlock]

# Model setup
model = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=st.secrets["OPENAI_API_KEY"]
)

def create_smithery_url():
    """Create Smithery.ai MCP server URL with configuration"""
    config = {
        "apiToken": st.secrets["API_TOKEN"],
        "browserAuth": st.secrets["BROWSER_AUTH"], 
        "webUnlockerZone": st.secrets["WEB_UNLOCKER_ZONE"]
    }
    
    config_b64 = base64.b64encode(json.dumps(config).encode()).decode()
    url = f"https://server.smithery.ai/@luminati-io/brightdata-mcp/mcp?config={config_b64}&api_key={SMITHERY_API_KEY}"
    
    return url

SYSTEM_PROMPT = (
    "To find products, first use the search_engine tool. When finding products, use the web_data tool for the platform. "
    "If none exists, scrape as markdown. "
    "Search all requested platforms in sequence, not in parallel. "
    "Example: Don't use web_data_bestbuy_products for search. Use it only for getting data on specific products you already found in search."
)

async def run_agent_single_platform(query, platform):
    """Run agent for a single platform"""
    try:
        smithery_url = create_smithery_url()
        
        async with streamablehttp_client(smithery_url) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools = await load_mcp_tools(session)
                agent = create_react_agent(model, tools, response_format=ProductSearchResponse)

                prompt = f'{query}\n\nPlatforms: {platform}'
                result = await agent.ainvoke({
                    'messages': [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ]
                })

                print(f"Raw agent result for {platform}:", result)
                structured = result["structured_response"]
                print(f"Structured response for {platform}:", structured.model_dump(mode="json"))
                return structured.model_dump()
            
    except Exception as e:
        print(f"Error connecting to Smithery.ai MCP server for {platform}: {str(e)}")
        return None

async def run_agent_sequential(query, platforms):
    """Run agent sequentially for multiple platforms to avoid conflicts"""
    all_results = {"platforms": []}
    
    for platform in platforms:
        print(f"Searching {platform}...")
        result = await run_agent_single_platform(query, platform)
        if result and "platforms" in result:
            all_results["platforms"].extend(result["platforms"])
        
        await asyncio.sleep(1)
    
    return all_results if all_results["platforms"] else None



# Sidebar - Only show if authenticated
with st.sidebar:
    st.page_link("pages/1_🏠_Home.py", label="Home", icon="🏠")
    st.page_link("pages/2_🔎_Product_Search.py", label="Product Search", icon="🔍")
    st.page_link("pages/3_📋_Watchlist.py", label="Watchlist", icon="📋")
    st.markdown("---")
    if st.button("Logout"):
        sign_out()
        st.rerun()

# Main page content
st.title("🔎 Product Search")
st.write("Search for products across multiple eCommerce platforms and find the best deals!")

# Search interface
query = st.text_input(
    "Enter a product or search query:", 
    placeholder="e.g. find wireless headphones between $50 and $100",
    help="Be specific! Include price ranges, brands, or features you're looking for."
)

selected_platforms = st.multiselect(
    "Select platforms to search:", 
    PLATFORMS, 
    help="Choose which platforms you want to search. More platforms = more results but slower search."
)

# Add warning for multiple platforms
if len(selected_platforms) > 3:
    st.warning("⚠️ Searching many platforms may take longer as each platform is searched individually for better reliability.")

if st.button("🔍 Search Products", type="primary", disabled=not (query and selected_platforms)):
    if query and selected_platforms:
        with st.spinner("🔍 Searching across platforms... This may take a moment..."):
            try:
                result = asyncio.run(run_agent_sequential(query, selected_platforms))
                
                if result and "platforms" in result and result["platforms"]:
                    st.session_state.last_search_result = result
                    st.session_state.last_search_query = query
                else:
                    st.error("No results found. Try adjusting your search query or selecting different platforms.")
            except Exception as e:
                st.error(f"Search failed: {str(e)}")
                st.info("Try selecting fewer platforms or adjust your search query.")

# Display results
if st.session_state.get('last_search_result'):
    st.markdown("---")
    st.subheader("🎯 Search Results")

    total_products = sum(len(platform["hits"]) for platform in st.session_state.last_search_result["platforms"])
    
    for platform in st.session_state.last_search_result["platforms"]:
        with st.expander(f"🏪 {platform['platform']} ({len(platform['hits'])} results)", expanded=True):
            
            for i, hit in enumerate(platform["hits"]):
                col1, col2, col3 = st.columns([1, 4, 1])
                
                with col1:
                    if hit["image_url"] and hit["image_url"] != "No Image URL Available" and hit["image_url"].startswith(('http://', 'https://')):
                        try:
                            st.image(hit["image_url"], width=100)
                        except:
                            st.markdown("📦")
                    else:
                        st.markdown("📦")
                
                with col2:
                    st.markdown(f"**[{hit['title']}]({hit['url']})**")
                    if hit["price"]:
                        st.markdown(f"💰 {hit['price']}")
                    else:
                        st.markdown("💰 Price not available")                                 
                    if hit["rating"]:
                        st.markdown(f"⭐ {hit['rating']}")
                    else:
                        st.markdown("⭐ No rating available")
                
                with col3:
                    button_key = f"add_{platform['platform']}_{i}_{hit['url'][:20]}"
                    if st.button("📌 Add to Watchlist", key=button_key, help="Save this product to your watchlist"):
                        user = get_or_create_user(st.session_state.user_email)
                        if user:
                            success = add_to_watchlist(
                                user["id"], 
                                hit, 
                                platform["platform"], 
                                st.session_state.last_search_query
                            )
                            if success:
                                st.success("✅ Added to watchlist!")
                                st.balloons()
                
                st.markdown("---")

# Show search tips if no results   
if not st.session_state.get('last_search_result'):
    st.markdown("---")
    st.markdown("### 💡 Search Tips")
    
    st.write("""
    **Good search examples:**
    - "Find wireless bluetooth headphones with 4 star rating or above under $100"
    - "Find mouses from Logitech between \\$50 and \\$100"
    - "Find running shoes size 10 Nike"
    
    **For multiple platforms:**
    - Each platform is searched individually for better reliability
    - More platforms = longer search time but more comprehensive results
    - Consider starting with 2-3 platforms for faster results
    """)