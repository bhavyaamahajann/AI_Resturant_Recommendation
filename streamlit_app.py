import os
import streamlit as st
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
    initial_sidebar_state="expanded"
)

# Custom CSS injection for premium glassmorphism aesthetics
st.markdown("""
    <style>
    /* Gradient Background */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%) !important;
        color: #f8fafc !important;
    }
    
    /* Input Labels */
    label, p, span {
        color: #e2e8f0 !important;
    }
    
    /* Glassmorphism card for the results */
    .restaurant-card {
        background: rgba(30, 41, 59, 0.7) !important;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        position: relative;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        transition: border-color 0.3s ease;
    }
    
    .restaurant-card:hover {
        border-color: rgba(244, 63, 94, 0.4);
    }
    
    /* Rank circular badge */
    .rank-badge {
        position: absolute;
        top: 15px;
        right: 15px;
        background: linear-gradient(135deg, #f43f5e, #f97316);
        color: white !important;
        border-radius: 50%;
        width: 35px;
        height: 35px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        box-shadow: 0 0 10px rgba(244, 63, 94, 0.4);
    }
    
    /* Ambiance Badge */
    .ambiance-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 6px;
        background: rgba(244, 63, 94, 0.1);
        border: 1px solid rgba(244, 63, 94, 0.2);
        color: #f43f5e !important;
        font-size: 0.75rem;
        margin-right: 6px;
        margin-top: 4px;
    }
    
    /* Reasoning Quote Box */
    .reasoning-box {
        background: rgba(15, 23, 42, 0.5);
        border-left: 4px solid #f43f5e;
        padding: 12px 16px;
        border-radius: 8px;
        margin-top: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Cache Data Loading
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

# 3. Sidebar (Preferences Form)
with st.sidebar:
    st.markdown("""
        <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 8px;'>
            <div style='width: 40px; height: 40px; border-radius: 12px; background: linear-gradient(135deg, #f43f5e, #f97316); display: flex; align-items: center; justify-content: center;'>
                <span style='font-size: 1.4rem; color: white !important;'>✨</span>
            </div>
            <h1 style='margin: 0; font-size: 1.8rem; color: white !important; font-weight: 700;'>FlavorIQ</h1>
        </div>
        <p style='color: #94a3b8 !important; font-size: 0.85rem; margin-top: 0;'>AI-powered culinary intelligence for your dining experience</p>
        <hr style='border-color: rgba(255,255,255,0.1); margin-top: 0; margin-bottom: 20px;' />
    """, unsafe_allow_html=True)
    
    st.subheader("Your Preferences")
    
    # Location Selection
    locations = store.known_locations(limit=100)
    selected_location = st.selectbox("Location", options=locations)
    
    # Cuisine Input
    selected_cuisine = st.text_input("Cuisine", placeholder="e.g. Italian, North Indian")
    
    # Budget Tier Selector
    selected_budget = st.selectbox(
        "Budget Tier", 
        options=[BudgetTier.LOW, BudgetTier.MEDIUM, BudgetTier.HIGH],
        format_func=lambda x: x.value.capitalize(),
        index=1
    )
    
    # Rating Slider
    min_rating = st.slider("Minimum Rating", min_value=0.0, max_value=5.0, value=3.5, step=0.1)
    
    # Extras tag list
    extras_input = st.text_input("Extras (Optional, comma-separated)", placeholder="e.g. romantic, outdoor seating")
    
    st.markdown("<br>", unsafe_allow_html=True)
    submit_btn = st.button("Find Recommendations", use_container_width=True, type="primary")

# 4. Main Panel Layout
if submit_btn:
    if not selected_cuisine:
        st.warning("Please enter at least one cuisine.")
    else:
        with st.spinner("AI is analyzing local matches..."):
            cuisines_list = [c.strip() for c in selected_cuisine.split(",") if c.strip()]
            extras_list = [e.strip() for e in extras_input.split(",") if e.strip()] if extras_input else []
            
            prefs = UserPreferences(
                location=selected_location,
                budget=selected_budget,
                cuisines=cuisines_list,
                min_rating=min_rating,
                extras=extras_list,
                top_n=5
            )
            
            try:
                result = service.recommend(prefs)
                
                # Header Summary
                if result.summary:
                    st.success(f"✨ **AI Summary:** {result.summary}")
                
                # Warnings & Notice
                if result.metadata.warnings:
                    for warning in result.metadata.warnings:
                        st.info(f"⚠️ {warning}")
                
                # Recommendations Feed
                for rec in result.recommendations:
                    # Look up original restaurant to get raw attributes like address or type
                    orig_rest = store.get_by_id(rec.restaurant_id)
                    address = "Locality Road, India"
                    ambiance_badges = ""
                    
                    if orig_rest:
                        if orig_rest.raw_attributes:
                            address = orig_rest.raw_attributes.get("address", address)
                            rest_type = orig_rest.raw_attributes.get("rest_type")
                            if rest_type:
                                # Split by comma to render individual badges
                                types = [t.strip() for t in rest_type.split(",") if t.strip()]
                                for t in types:
                                    ambiance_badges += f'<span class="ambiance-badge">{t}</span>'
                                    
                    st.markdown(f"""
                        <div class="restaurant-card">
                            <div class="rank-badge">#{rec.rank}</div>
                            <h3 style="margin-top:0; color:white; font-size: 1.45rem; font-weight: 600;">{rec.name}</h3>
                            <p style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 8px;">
                                🍽️ {rec.cuisine} &nbsp;|&nbsp; ⭐ {rec.rating:.1f} &nbsp;|&nbsp; 💰 ₹{rec.estimated_cost or 500:.0f} for two
                            </p>
                            <p style="color: #64748b; font-size: 0.825rem; margin-bottom: 12px; font-style: italic;">
                                📍 {address}
                            </p>
                            <div>
                                {ambiance_badges}
                            </div>
                            <div class="reasoning-box">
                                <p style="margin: 0; font-style: italic; color: #e2e8f0; font-size: 0.95rem; line-height: 1.5;">
                                    "{rec.explanation}"
                                </p>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
            except OrchestrationError as e:
                st.error(f"Recommendation Failed: {e.message}")
            except Exception as e:
                st.error(f"Something went wrong: {e}")
else:
    # Default Welcome Screen
    st.markdown("""
        <div style='text-align: center; padding: 100px 20px;'>
            <h2 style='font-size: 2.2rem; color: white !important; font-weight: 600; margin-bottom: 15px;'>Ready to Discover?</h2>
            <p style='color: #94a3b8 !important; font-size: 1.1rem; max-width: 600px; margin: 0 auto;'>
                Configure your preferences in the sidebar on the left and submit to find the absolute best-suited restaurants powered by our recommendation engine.
            </p>
        </div>
    """, unsafe_allow_html=True)
