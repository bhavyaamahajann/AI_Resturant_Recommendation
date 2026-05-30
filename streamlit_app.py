import os
import streamlit as st
import textwrap
from pathlib import Path

# Copy Streamlit secrets to environment variables for pydantic-settings compatibility
for key in ["LLM_API_KEY", "LLM_MODEL"]:
    if key in st.secrets:
        os.environ[key] = st.secrets[key]

from src.data.store import RestaurantStore
from src.data.preferences import UserPreferences
from src.data.models import BudgetTier
from src.services.orchestrator import RecommendationService, OrchestrationError

# 1. Page Configuration & Custom CSS (Sleek Dark Theme)
st.set_page_config(
    page_title="FlavorIQ - AI Restaurant Recommender",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS injection for premium glassmorphism aesthetics
st.markdown("""
    <style>
    /* Gradient Background */
    .stApp {
        background: linear-gradient(135deg, #0d1117 0%, #171d26 50%, #0d1117 100%) !important;
        color: #f8fafc !important;
    }
    
    /* Input Labels and Text */
    label, p, span, h1, h2, h3, h4, h5, h6 {
        color: #cbd5e1 !important;
    }
    
    /* Hide Streamlit sidebar by default */
    section[data-testid="stSidebar"] {
        display: none !important;
    }
    
    /* Style all text inputs, select boxes, and their children */
    div[data-baseweb="input"],
    div[data-baseweb="select"],
    input,
    select {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1.5px solid #475569 !important;
        border-radius: 12px !important;
    }
    
    /* Target the text input element specifically */
    div[data-baseweb="input"] input,
    input {
        color: #ffffff !important;
        background-color: transparent !important;
        font-size: 0.95rem !important;
    }

    /* Style select boxes selection text */
    div[data-baseweb="select"] div {
        color: #ffffff !important;
        background-color: transparent !important;
        font-size: 0.95rem !important;
    }

    /* Target placeholders */
    ::placeholder {
        color: #94a3b8 !important;
        opacity: 1 !important;
    }
    
    :-ms-input-placeholder {
        color: #94a3b8 !important;
    }
    
    ::-ms-input-placeholder {
        color: #94a3b8 !important;
    }

    /* Input focus state */
    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="select"]:focus-within {
        border-color: #ff5b3f !important;
        box-shadow: 0 0 0 1px #ff5b3f !important;
    }

    /* Style select dropdown options list */
    ul[role="listbox"],
    ul[role="listbox"] li {
        background-color: #1e293b !important;
        color: #ffffff !important;
    }
    ul[role="listbox"] li:hover {
        background-color: #ff5b3f !important;
        color: #ffffff !important;
    }
    
    /* Primary Button (Find Recommendations) */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(to right, #ff3b30, #ff9500) !important;
        color: white !important;
        border: none !important;
        border-radius: 9999px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        box-shadow: 0 4px 20px rgba(255, 59, 48, 0.25) !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
    }
    div.stButton > button[kind="primary"]:hover {
        box-shadow: 0 4px 25px rgba(255, 59, 48, 0.4) !important;
        transform: translateY(-1px) !important;
    }
    
    /* Secondary Button (Get AI Recommendations / View Details) */
    div.stButton > button:not([kind="primary"]) {
        background-color: #1e2530 !important;
        color: white !important;
        border: 1px solid rgba(71, 85, 105, 0.6) !important;
        border-radius: 9999px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
    }
    div.stButton > button:not([kind="primary"]):hover {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border-color: #10b981 !important;
    }
    
    /* Rating Slider thumb and filled track styling */
    div[role="slider"] {
        background-color: #ff5b3f !important;
        border: none !important;
        box-shadow: 0 0 12px rgba(255, 91, 63, 0.8) !important;
        width: 16px !important;
        height: 16px !important;
    }
    div[data-testid="stSlider"] div[aria-valuemax] {
        background: linear-gradient(to right, #ff3b30, #ff9500) !important;
    }
    
    /* Clickable Restaurant Card container and hover effects */
    .restaurant-card {
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 16px !important;
        overflow: hidden !important;
        background: rgba(30, 41, 59, 0.7) !important;
        position: relative !important;
        margin-bottom: 12px !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        cursor: pointer !important;
    }
    .restaurant-card:hover {
        transform: translateY(-4px) scale(1.01) !important;
        border-color: rgba(255, 91, 63, 0.4) !important;
        box-shadow: 0 12px 40px rgba(255, 91, 63, 0.15) !important;
    }
    </style>
""", unsafe_allow_html=True)

# Unsplash Photo ID Collections for Dynamic Image Sourcing
ITALIAN_PHOTOS = [
    "photo-1546069901-ba9599a7e63c",  # salad/pasta
    "photo-1513104890138-7c749659a591",  # pizza
    "photo-1551183053-bf91a1d81141",  # pasta
    "photo-1595295333158-4742f28fbd85",  # pasta dish
    "photo-1555396273-367ea4eb4db5"   # wine/interior
]

INDIAN_PHOTOS = [
    "photo-1626132647523-66f5bf380027",  # thali
    "photo-1596797038530-2c107229654b",  # curry
    "photo-1565557623262-b51c2513a641",  # tandoori
    "photo-1626777552726-4a6b54c97e46",  # thali
    "photo-1589301760014-d929f3979dbc"   # curry
]

ASIAN_PHOTOS = [
    "photo-1563245372-f21724e3856d",  # sushi
    "photo-1540648639573-8c848de23f0a",  # noodles
    "photo-1552611052-33e04de081de",  # ramen
    "photo-1512058564366-18510be2db19"   # stir fry
]

CAFE_PHOTOS = [
    "photo-1554118811-1e0d58224f24",  # cafe
    "photo-1445116572660-236099ec97a0",  # coffee
    "photo-1498804103079-a6351b050096",  # brunch
    "photo-1501339847302-ac426a4a7cbb"   # dessert
]

GENERIC_PHOTOS = [
    "photo-1517248135467-4c7edcad34c4",  # table
    "photo-1552566626-52f8b828add9",  # romantic
    "photo-1414235077428-338989a2e8c0",  # fine dining
    "photo-1559339352-11d035aa65de"   # outdoor
]

# Helper to strip all leading/trailing whitespace of every HTML line, preventing markdown code blocks
def clean_html(html_str: str) -> str:
    return "\n".join(line.strip() for line in html_str.splitlines())

# 2. Helpers for Mock Enrichment
def get_cuisine_image(cuisine: str, index: int) -> str:
    c = (cuisine or '').lower()
    if any(x in c for x in ['italian', 'pizza', 'pasta']):
        photo = ITALIAN_PHOTOS[index % len(ITALIAN_PHOTOS)]
    elif any(x in c for x in ['indian', 'biryani', 'kebab', 'curry']):
        photo = INDIAN_PHOTOS[index % len(INDIAN_PHOTOS)]
    elif any(x in c for x in ['asian', 'chinese', 'thai', 'sushi']):
        photo = ASIAN_PHOTOS[index % len(ASIAN_PHOTOS)]
    elif any(x in c for x in ['cafe', 'bakery', 'dessert', 'coffee']):
        photo = CAFE_PHOTOS[index % len(CAFE_PHOTOS)]
    else:
        photo = GENERIC_PHOTOS[index % len(GENERIC_PHOTOS)]
    return f"https://images.unsplash.com/{photo}?w=800&q=80"

def get_popular_dishes(cuisine: str) -> list[str]:
    c = (cuisine or '').lower()
    if 'italian' in c:
        return ["Truffle Pasta", "Margherita Pizza", "Tiramisu"]
    if 'indian' in c:
        return ["Butter Chicken", "Garlic Naan", "Paneer Tikka"]
    if any(x in c for x in ['asian', 'chinese']):
        return ["Dim Sum", "Kung Pao Chicken", "Hakka Noodles"]
    if any(x in c for x in ['cafe', 'continental']):
        return ["Avocado Toast", "Club Sandwich", "Red Velvet Waffle"]
    return ["Chef's Special", "Signature Dish", "House Dessert"]

def get_ambiance_tags(rating: float, cost: float) -> list[str]:
    tags = []
    if rating and rating >= 4.3:
        tags.append("Fine Dining")
    else:
        tags.append("Casual Dining")
    
    if cost and cost >= 1200:
        tags.append("Romantic")
    elif cost and cost <= 500:
        tags.append("Pocket Friendly")
    else:
        tags.append("Cozy Vibe")
        
    tags.append("Great Service")
    return tags

# 3. Cache Data Loading
@st.cache_resource
def get_service():
    data_path = Path("data/restaurants.parquet")
    store = RestaurantStore.from_parquet(data_path)
    return RecommendationService(store)

try:
    service = get_service()
    store = service._store
except Exception as e:
    st.error(f"Failed to load data store: {e}")
    st.stop()

# 4. Initialize Session State
if "view" not in st.session_state:
    st.session_state.view = "search"
if "previous_view" not in st.session_state:
    st.session_state.previous_view = "search"
if "selected_item" not in st.session_state:
    st.session_state.selected_item = None
if "recommendations" not in st.session_state:
    st.session_state.recommendations = []
if "ai_summary" not in st.session_state:
    st.session_state.ai_summary = ""
if "warnings" not in st.session_state:
    st.session_state.warnings = []
if "budget" not in st.session_state:
    st.session_state.budget = "medium"

# Check query parameters for card selection (allows clicking the entire card)
if "select" in st.query_params:
    sel_id = st.query_params["select"]
    recs = st.session_state.recommendations
    selected_item = None
    for r in recs:
        if r["restaurant_id"] == sel_id:
            selected_item = r
            break
    if not selected_item:
        # Fallback: check database directly
        orig_rest = store.get_by_id(sel_id)
        if orig_rest:
            selected_item = {
                "rank": 1,
                "restaurant_id": orig_rest.id,
                "name": orig_rest.name,
                "cuisine": orig_rest.primary_cuisine,
                "rating": orig_rest.rating,
                "estimated_cost": orig_rest.cost_estimate or 500,
                "explanation": "Selected restaurant details",
                "image": get_cuisine_image(orig_rest.primary_cuisine, 0),
                "address": orig_rest.raw_attributes.get("address") if orig_rest.raw_attributes else f"{orig_rest.name}, Bangalore",
                "phone": "+91 80 40000000",
                "hours": "12:00 PM - 11:30 PM",
                "distance": "1.5 km",
                "reviewCount": 120,
                "popularDishes": get_popular_dishes(orig_rest.primary_cuisine),
                "ambiance": get_ambiance_tags(orig_rest.rating, orig_rest.cost_estimate or 500)
            }
    if selected_item:
        st.session_state.selected_item = selected_item
        st.session_state.view = "detail"
        st.session_state.previous_view = "results"
        # Clear the parameter so it doesn't get sticky on back button
        st.query_params.clear()
        st.rerun()

# 5. Render Views
# 5a. Search View
if st.session_state.view == "search":
    # Dynamic search-specific styles (restricts form wrapper width & styles budget columns)
    st.markdown("""
        <style>
        /* Restrict main container width & top padding only on search view */
        .block-container {
            max-width: 800px !important;
            padding-top: 3rem !important;
            padding-bottom: 3rem !important;
            margin: 0 auto !important;
        }
        /* Card container styling (only on search screen) */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #1e2530 !important;
            border: 1px solid rgba(71, 85, 105, 0.4) !important;
            border-radius: 16px !important;
            padding: 32px !important;
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5) !important;
            width: 100% !important;
        }
        /* Style buttons inside columns (budget buttons) */
        div[data-testid="column"] div.stButton > button {
            border-radius: 12px !important;
            padding: 12px 16px !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Render header directly (no columns, centered container with max-width 800px)
    st.markdown(clean_html("""
        <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 4px; justify-content: flex-start; padding-top: 0px;'>
            <div style='width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(to right, #ff3b30, #ff9500); display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 15px rgba(255, 59, 48, 0.3);'>
                <svg viewBox="0 0 24 24" style="width: 24px; height: 24px; fill: white; color: white;">
                    <path d="M12 2Q12 12 22 12Q12 12 12 22Q12 12 2 12Q12 12 12 2" />
                </svg>
            </div>
            <h1 style='margin: 0; font-size: 2.2rem; color: white !important; font-weight: 700; tracking-wide: 0.05em;'>FlavorIQ</h1>
        </div>
        <p style='color: #94a3b8 !important; font-size: 0.95rem; margin-top: 0; text-align: left; margin-bottom: 32px;'>AI-powered culinary intelligence for your perfect dining experience</p>
    """), unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("<h2 style='margin-top:0; font-size: 1.5rem; font-weight: 700; color: white !important; margin-bottom: 24px;'>Preferences</h2>", unsafe_allow_html=True)
        
        # Location dropdown
        locations = store.known_locations(limit=100)
        cleaned_locs = list(set(loc.strip() for loc in locations if loc.strip()))
        cleaned_locs = [loc for loc in cleaned_locs if loc.lower() != "bangalore"]
        locations = ["-select a location-"] + sorted(cleaned_locs)
        selected_location = st.selectbox("Location", options=locations)
        
        # Cuisine text input
        selected_cuisine = st.text_input("Cuisine", placeholder="e.g. Italian, North Indian")
        
        # Budget Native Button Selector in a 3-column row
        st.markdown("<label class='block text-xs font-semibold mb-3' style='color:#cbd5e1; font-size:0.875rem;'>Budget</label>", unsafe_allow_html=True)
        b_col1, b_col2, b_col3 = st.columns(3)
        with b_col1:
            if st.button("Low", key="btn_budget_low", type="primary" if st.session_state.budget == "low" else "secondary", use_container_width=True):
                st.session_state.budget = "low"
                st.rerun()
        with b_col2:
            if st.button("Medium", key="btn_budget_medium", type="primary" if st.session_state.budget == "medium" else "secondary", use_container_width=True):
                st.session_state.budget = "medium"
                st.rerun()
        with b_col3:
            if st.button("High", key="btn_budget_high", type="primary" if st.session_state.budget == "high" else "secondary", use_container_width=True):
                st.session_state.budget = "high"
                st.rerun()
        
        st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)

        # Minimum Rating slider
        min_rating = st.slider("Minimum Rating", min_value=0.0, max_value=5.0, value=3.5, step=0.1)
        
        # Number of Results slider
        top_n = st.slider("Number of Results", min_value=1, max_value=20, value=9, step=1)
        
        # Extras optional text input
        extras_input = st.text_input("Extras (Optional)", placeholder="e.g. outdoor seating, romantic")
        
        st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
        
        # Actions buttons
        find_btn = st.button("Find Recommendations", use_container_width=True, type="primary")
        ai_btn = st.button("✨ Get AI Recommendations", use_container_width=True)
        
        if find_btn or ai_btn:
            if selected_location == "-select a location-":
                st.error("Please select a location.")
            elif not selected_cuisine:
                st.error("Please enter at least one cuisine.")
            else:
                loader_placeholder = st.empty()
                loader_placeholder.markdown("""
                    <div class="overlay-loader">
                        <div class="spinner-container">
                            <div class="custom-spinner"></div>
                            <div class="loader-text">AI is analyzing local matches...</div>
                        </div>
                    </div>
                    <style>
                    .overlay-loader {
                        position: fixed;
                        top: 0;
                        left: 0;
                        width: 100vw;
                        height: 100vh;
                        background: rgba(13, 17, 23, 0.85) !important;
                        backdrop-filter: blur(8px);
                        display: flex !important;
                        justify-content: center !important;
                        align-items: center !important;
                        z-index: 999999 !important;
                    }
                    .spinner-container {
                        text-align: center;
                        background: rgba(30, 41, 59, 0.85) !important;
                        padding: 40px !important;
                        border-radius: 24px !important;
                        border: 1px solid rgba(255, 255, 255, 0.1) !important;
                        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5) !important;
                        display: flex !important;
                        flex-direction: column !important;
                        align-items: center !important;
                    }
                    .custom-spinner {
                        width: 60px !important;
                        height: 60px !important;
                        border: 4px solid rgba(255, 255, 255, 0.1) !important;
                        border-top-color: #ff5b3f !important;
                        border-radius: 50% !important;
                        animation: spin 1s linear infinite !important;
                        margin-bottom: 20px !important;
                    }
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                    .loader-text {
                        color: white !important;
                        font-size: 1.2rem !important;
                        font-weight: 600 !important;
                        margin: 0 !important;
                        font-family: sans-serif !important;
                    }
                    </style>
                """, unsafe_allow_html=True)
                
                success = False
                try:
                    cuisines_list = [c.strip() for c in selected_cuisine.split(",") if c.strip()]
                    extras_list = [e.strip() for e in extras_input.split(",") if e.strip()] if extras_input else []
                    
                    prefs = UserPreferences(
                        location=selected_location,
                        budget=BudgetTier(st.session_state.budget),
                        cuisines=cuisines_list,
                        min_rating=min_rating,
                        extras=extras_list,
                        top_n=top_n
                    )
                    
                    result = service.recommend(prefs)
                    
                    # Enrich results
                    enriched = []
                    for i, rec in enumerate(result.recommendations):
                        r_id = rec.restaurant_id
                        mock_distance = f"{((int(r_id[:4], 16) % 35 + 10) / 10):.1f} km"
                        mock_review_count = int(rec.rating * 74 + (int(r_id[4:6], 16) % 150))
                        mock_phone = f"+91 80 4{(int(r_id[:6], 16) % 9000000 + 1000000)}"
                        mock_address = f"{rec.name}, Locality Road, {selected_location}, India"
                        
                        orig_rest = store.get_by_id(r_id)
                        if orig_rest and orig_rest.raw_attributes:
                            mock_address = orig_rest.raw_attributes.get("address", mock_address)
                            
                        rec_item = {
                            "rank": rec.rank,
                            "restaurant_id": rec.restaurant_id,
                            "name": rec.name,
                            "cuisine": rec.cuisine,
                            "rating": rec.rating,
                            "estimated_cost": rec.estimated_cost or 500,
                            "explanation": rec.explanation,
                            "image": get_cuisine_image(rec.cuisine, i),
                            "address": mock_address,
                            "phone": mock_phone,
                            "hours": "12:00 PM - 11:30 PM",
                            "distance": mock_distance,
                            "reviewCount": mock_review_count,
                            "popularDishes": get_popular_dishes(rec.cuisine),
                            "ambiance": get_ambiance_tags(rec.rating, rec.estimated_cost or 500)
                        }
                        enriched.append(rec_item)
                        
                    st.session_state.recommendations = enriched
                    st.session_state.ai_summary = result.summary or ""
                    st.session_state.warnings = result.metadata.warnings or []
                    st.session_state.view = "results"
                    st.session_state.previous_view = "search"
                    success = True
                except OrchestrationError as e:
                    st.error(f"Recommendation Failed: {e.message}")
                except Exception as e:
                    st.error(f"Something went wrong: {e}")
                finally:
                    loader_placeholder.empty()
                
                if success:
                    st.rerun()

# 5b. Results View
elif st.session_state.view == "results":
    # Back button
    if st.button("← Back to Search", key="back_to_search"):
        st.session_state.view = "search"
        st.rerun()
        
    st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
    
    # AI Summary Banner
    if st.session_state.ai_summary:
        st.markdown(clean_html(f"""
            <div style='background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.05)); border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 16px; padding: 20px; margin-bottom: 24px; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);'>
                <div style='display: flex; gap: 12px; align-items: start;'>
                    <span style='font-size: 1.2rem; color: #10b981;'>✨</span>
                    <div>
                        <h3 style='margin: 0 0 4px 0; color: #10b981 !important; font-size: 1.1rem; font-weight: 600;'>AI Summary</h3>
                        <p style='margin: 0; color: #cbd5e1 !important; font-size: 0.9rem; line-height: 1.5;'>{st.session_state.ai_summary}</p>
                    </div>
                </div>
            </div>
        """), unsafe_allow_html=True)
        
    # Warnings Banner
    if st.session_state.warnings:
        for warn in st.session_state.warnings:
            st.info(f"⚠️ {warn}")
            
    # Results Grid (3 columns)
    recs = st.session_state.recommendations
    if not recs:
        st.info("No recommendations found matching your criteria.")
    else:
        for i in range(0, len(recs), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(recs):
                    item = recs[i+j]
                    with cols[j]:
                        # Card markup (wrapped in clickable link, using premium transitions)
                        st.markdown(clean_html(f"""
                            <a href='?select={item["restaurant_id"]}' target='_self' style='text-decoration: none !important; color: inherit !important; display: block;'>
                                <div class='restaurant-card'>
                                    <div style='position: absolute; top: 16px; right: 16px; width: 36px; height: 36px; border-radius: 50%; background: linear-gradient(135deg, #f43f5e, #f97316); display: flex; align-items: center; justify-content: center; font-weight: bold; color: white !important; z-index: 10;'>
                                        #{item['rank']}
                                    </div>
                                    <div style='height: 180px; width: 100%; overflow: hidden; position: relative;'>
                                        <img src='{item['image']}' style='width: 100%; height: 100%; object-fit: cover;' />
                                        <div style='position: absolute; inset: 0; background: linear-gradient(to top, rgba(15,23,42,0.85) 0%, transparent 100%);'></div>
                                    </div>
                                    <div style='padding: 20px;'>
                                        <h3 style='margin: 0 0 8px 0; font-size: 1.25rem; font-weight: 600; color: white;'>{item['name']}</h3>
                                        <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 12px;'>
                                            <span style='color: #fbbf24; font-size: 0.85rem; font-weight: 600; display: flex; align-items: center; gap: 4px;'>
                                                ⭐ {item['rating']:.1f} <span style='color: #64748b; font-size: 0.75rem; font-weight: 400;'>({item['reviewCount']})</span>
                                            </span>
                                            <span style='color: #94a3b8; font-size: 0.85rem; display: flex; align-items: center; gap: 4px;'>
                                                📍 {item['distance']}
                                            </span>
                                        </div>
                                        <div style='display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px;'>
                                            <span style='padding: 3px 8px; border-radius: 9999px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); font-size: 0.75rem; color: #e2e8f0;'>
                                                {item['cuisine']}
                                            </span>
                                            <span style='padding: 3px 8px; border-radius: 9999px; background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.25); font-size: 0.75rem; color: #34d399;'>
                                                ₹{item['estimated_cost']:.0f} for two
                                            </span>
                                        </div>
                                        <div style='margin-bottom: 12px;'>
                                            <span style='font-size: 0.75rem; color: #64748b; display: block; margin-bottom: 2px;'>Popular:</span>
                                            <p style='margin: 0; font-size: 0.85rem; color: #cbd5e1;'>{", ".join(item['popularDishes'])}</p>
                                        </div>
                                        <div style='display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px;'>
                                            {" ".join([f'<span style="padding: 2px 6px; border-radius: 4px; background: rgba(244, 63, 94, 0.1); border: 1px solid rgba(244, 63, 94, 0.15); font-size: 0.7rem; color: #f43f5e;">{tag}</span>' for tag in item['ambiance']])}
                                        </div>
                                    </div>
                                </div>
                            </a>
                        """), unsafe_allow_html=True)

# 5c. Detail View
elif st.session_state.view == "detail" and st.session_state.selected_item:
    item = st.session_state.selected_item
    
    if st.button("← Back to Results", key="back_to_results"):
        st.session_state.view = st.session_state.previous_view
        st.rerun()
        
    st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
    
    st.markdown(clean_html(f"""
        <div style='height: 320px; border-radius: 16px; overflow: hidden; position: relative; margin-bottom: 24px; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);'>
            <img src='{item['image']}' style='width: 100%; height: 100%; object-fit: cover;' />
            <div style='position: absolute; inset: 0; background: linear-gradient(to top, #0f172a 15%, rgba(15,23,42,0.3) 100%);'></div>
            <div style='position: absolute; bottom: 24px; left: 24px;'>
                <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 8px;'>
                    <h1 style='margin: 0; font-size: 2.2rem; color: white !important; font-weight: 700;'>{item['name']}</h1>
                    <div style='padding: 4px 12px; border-radius: 9999px; background: linear-gradient(135deg, #f43f5e, #f97316); color: white !important; font-weight: bold; font-size: 0.9rem;'>
                        #{item['rank']}
                    </div>
                </div>
                <div style='display: flex; align-items: center; gap: 16px; font-size: 0.95rem; color: #cbd5e1;'>
                    <span style='color: #fbbf24; font-weight: 600; display: flex; align-items: center; gap: 4px;'>
                        ⭐ {item['rating']:.1f} <span style='color: #94a3b8; font-weight: 400;'>({item['reviewCount']} reviews)</span>
                    </span>
                    <span>•</span>
                    <span>{item['cuisine']}</span>
                    <span>•</span>
                    <span style='color: #34d399; font-weight: 600;'>₹{item['estimated_cost']:.0f} for two</span>
                </div>
            </div>
        </div>
    """), unsafe_allow_html=True)
    
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.markdown(clean_html(f"""
            <div style='background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 24px; margin-bottom: 24px; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);'>
                <h3 style='margin-top: 0; font-size: 1.2rem; font-weight: 600; color: white; margin-bottom: 16px;'>Ambiance & Features</h3>
                <div style='display: flex; flex-wrap: wrap; gap: 10px;'>
                    {" ".join([f'<span style="padding: 6px 14px; border-radius: 9999px; background: linear-gradient(to right, rgba(244,63,94,0.15), rgba(249,115,22,0.15)); border: 1px solid rgba(244,63,94,0.25); color: #fecdd3; font-weight: 500; font-size: 0.85rem;">{tag}</span>' for tag in item['ambiance']])}
                </div>
            </div>
        """), unsafe_allow_html=True)
        
        st.markdown(clean_html(f"""
            <div style='background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.05)); border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 16px; padding: 24px; margin-bottom: 24px; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);'>
                <div style='display: flex; gap: 12px; align-items: start;'>
                    <span style='font-size: 1.3rem; color: #10b981; margin-top: 2px;'>✨</span>
                    <div>
                        <h3 style='margin: 0 0 8px 0; color: #10b981 !important; font-size: 1.2rem; font-weight: 600;'>Why AI Recommends This</h3>
                        <p style='margin: 0; color: #e2e8f0 !important; font-size: 0.95rem; line-height: 1.6; font-style: italic;'>"{item['explanation']}"</p>
                    </div>
                </div>
            </div>
        """), unsafe_allow_html=True)
        
        st.markdown(clean_html(f"""
            <div style='background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 24px; margin-bottom: 24px; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);'>
                <h3 style='margin-top: 0; font-size: 1.2rem; font-weight: 600; color: white; margin-bottom: 16px;'>Must-Try Dishes</h3>
                <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px;'>
                    {" ".join([f'''
                        <div style='padding: 16px; border-radius: 12px; background: rgba(51, 65, 85, 0.4); border: 1px solid rgba(255,255,255,0.06);'>
                            <span style='font-size: 1.1rem; display: block; margin-bottom: 6px;'>🍽️</span>
                            <span style='color: white; font-weight: 500; font-size: 0.9rem;'>{dish}</span>
                        </div>
                    ''' for dish in item['popularDishes']])}
                </div>
            </div>
        """), unsafe_allow_html=True)
        
    with col_right:
        st.markdown(clean_html(f"""
            <div style='background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 24px; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);'>
                <h3 style='margin-top: 0; font-size: 1.2rem; font-weight: 600; color: white; margin-bottom: 20px;'>Details</h3>
                
                <div style='display: flex; gap: 12px; align-items: start; margin-bottom: 20px;'>
                    <span style='color: #f43f5e; font-size: 1.1rem;'>📍</span>
                    <div>
                        <span style='color: #64748b; font-size: 0.75rem; display: block; margin-bottom: 2px;'>Address</span>
                        <span style='color: #cbd5e1; font-size: 0.85rem;'>{item['address']}</span>
                    </div>
                </div>
                
                <div style='display: flex; gap: 12px; align-items: start; margin-bottom: 20px;'>
                    <span style='color: #f97316; font-size: 1.1rem;'>🧭</span>
                    <div>
                        <span style='color: #64748b; font-size: 0.75rem; display: block; margin-bottom: 2px;'>Distance</span>
                        <span style='color: #cbd5e1; font-size: 0.85rem;'>{item['distance']} away</span>
                    </div>
                </div>
                
                <div style='display: flex; gap: 12px; align-items: start; margin-bottom: 20px;'>
                    <span style='color: #10b981; font-size: 1.1rem;'>📞</span>
                    <div>
                        <span style='color: #64748b; font-size: 0.75rem; display: block; margin-bottom: 2px;'>Phone</span>
                        <span style='color: #cbd5e1; font-size: 0.85rem;'>{item['phone']}</span>
                    </div>
                </div>
                
                <div style='display: flex; gap: 12px; align-items: start; margin-bottom: 24px;'>
                    <span style='color: #3b82f6; font-size: 1.1rem;'>🕒</span>
                    <div>
                        <span style='color: #64748b; font-size: 0.75rem; display: block; margin-bottom: 2px;'>Hours</span>
                        <span style='color: #cbd5e1; font-size: 0.85rem;'>{item['hours']}</span>
                    </div>
                </div>
            </div>
        """), unsafe_allow_html=True)
        
        st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
        reserve_btn = st.button("Reserve Table", use_container_width=True, type="primary")
        directions_btn = st.button("Get Directions", use_container_width=True)
