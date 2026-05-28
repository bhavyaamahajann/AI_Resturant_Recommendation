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
    
    /* Style all text inputs */
    div[data-baseweb="input"] {
        background-color: #141a24 !important;
        border: 1px solid rgba(45, 55, 72, 0.8) !important;
        border-radius: 12px !important;
    }
    div[data-baseweb="input"] input {
        color: white !important;
        background-color: transparent !important;
        font-size: 0.9rem !important;
    }
    
    /* Style select boxes */
    div[data-baseweb="select"] {
        background-color: #141a24 !important;
        border: 1px solid rgba(45, 55, 72, 0.8) !important;
        border-radius: 12px !important;
    }
    div[data-baseweb="select"] div {
        color: white !important;
        background-color: transparent !important;
        font-size: 0.9rem !important;
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
        top: -6px !important;
    }
    div[data-testid="stSlider"] div[aria-valuemax] {
        background: linear-gradient(to right, #ff3b30, #ff9500) !important;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Helpers for Mock Enrichment
def get_cuisine_image(cuisine: str, index: int) -> str:
    c = (cuisine or '').lower()
    if any(x in c for x in ['italian', 'pizza', 'pasta']):
        return f"https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800&q=80&sig={index}"
    if any(x in c for x in ['indian', 'biryani', 'kebab', 'curry']):
        return f"https://images.unsplash.com/photo-1585938338392-50a599e0217b?w=800&q=80&sig={index}"
    if any(x in c for x in ['asian', 'chinese', 'thai', 'sushi']):
        return f"https://images.unsplash.com/photo-1563245372-f21724e3856d?w=800&q=80&sig={index}"
    if any(x in c for x in ['cafe', 'bakery', 'dessert', 'coffee']):
        return f"https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=800&q=80&sig={index}"
    if any(x in c for x in ['burger', 'fast food', 'american']):
        return f"https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=800&q=80&sig={index}"
    return f"https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800&q=80&sig={index}"

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

# 5. Render Views
# 5a. Search View
if st.session_state.view == "search":
    # Dynamic search-specific styles (restricts form wrapper width & styles budget columns)
    st.markdown("""
        <style>
        /* Card container styling (only on search screen) */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #1e2530 !important;
            border: 1px solid rgba(71, 85, 105, 0.4) !important;
            border-radius: 16px !important;
            padding: 32px !important;
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5) !important;
            max-width: 800px !important;
            margin: 0 auto !important;
        }
        /* Style buttons inside columns (budget buttons) */
        div[data-testid="column"] div.stButton > button {
            border-radius: 12px !important;
            padding: 12px 16px !important;
        }
        </style>
    """, unsafe_allow_html=True)

    col_left, col_mid, col_right = st.columns([1, 6, 1])
    
    with col_mid:
        st.markdown(textwrap.dedent("""
            <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 4px; justify-content: center; padding-top: 40px;'>
                <div style='width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(to right, #ff3b30, #ff9500); display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 15px rgba(255, 59, 48, 0.3);'>
                    <svg viewBox="0 0 24 24" style="width: 24px; height: 24px; fill: white; color: white;">
                        <path d="M12 2Q12 12 22 12Q12 12 12 22Q12 12 2 12Q12 12 12 2" />
                    </svg>
                </div>
                <h1 style='margin: 0; font-size: 2.2rem; color: white !important; font-weight: 700; tracking-wide: 0.05em;'>FlavorIQ</h1>
            </div>
            <p style='color: #94a3b8 !important; font-size: 0.95rem; margin-top: 0; text-align: center; margin-bottom: 32px;'>AI-powered culinary intelligence for your perfect dining experience</p>
        """), unsafe_allow_html=True)
        
        with st.container(border=True):
            st.markdown("<h2 style='margin-top:0; font-size: 1.5rem; font-weight: 700; color: white !important; margin-bottom: 24px;'>Preferences</h2>", unsafe_allow_html=True)
            
            # Location dropdown
            locations = store.known_locations(limit=100)
            if "Bangalore" in locations:
                locations.remove("Bangalore")
                locations = ["Bangalore"] + locations
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
            
            # Extras optional text input
            extras_input = st.text_input("Extras (Optional)", placeholder="e.g. outdoor seating, romantic")
            
            st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
            
            # Actions buttons
            find_btn = st.button("Find Recommendations", use_container_width=True, type="primary")
            ai_btn = st.button("✨ Get AI Recommendations", use_container_width=True)
            
            if find_btn or ai_btn:
                if not selected_cuisine:
                    st.error("Please enter at least one cuisine.")
                else:
                    with st.spinner("AI is analyzing local matches..."):
                        cuisines_list = [c.strip() for c in selected_cuisine.split(",") if c.strip()]
                        extras_list = [e.strip() for e in extras_input.split(",") if e.strip()] if extras_input else []
                        
                        prefs = UserPreferences(
                            location=selected_location,
                            budget=BudgetTier(st.session_state.budget),
                            cuisines=cuisines_list,
                            min_rating=min_rating,
                            extras=extras_list,
                            top_n=9
                        )
                        
                        try:
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
                            st.rerun()
                            
                        except OrchestrationError as e:
                            st.error(f"Recommendation Failed: {e.message}")
                        except Exception as e:
                            st.error(f"Something went wrong: {e}")

# 5b. Results View
elif st.session_state.view == "results":
    # Back button
    if st.button("← Back to Search", key="back_to_search"):
        st.session_state.view = "search"
        st.rerun()
        
    st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
    
    # AI Summary Banner
    if st.session_state.ai_summary:
        st.markdown(textwrap.dedent(f"""
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
                        # Card markup (dedented to avoid code blocks in markdown)
                        st.markdown(textwrap.dedent(f"""
                            <div style='border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; overflow: hidden; background: rgba(30, 41, 59, 0.7); position: relative; margin-bottom: 12px; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);'>
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
                        """), unsafe_allow_html=True)
                        if st.button("View Details", key=f"btn_details_{item['restaurant_id']}", use_container_width=True):
                            st.session_state.selected_item = item
                            st.session_state.view = "detail"
                            st.session_state.previous_view = "results"
                            st.rerun()

# 5c. Detail View
elif st.session_state.view == "detail" and st.session_state.selected_item:
    item = st.session_state.selected_item
    
    if st.button("← Back to Results", key="back_to_results"):
        st.session_state.view = st.session_state.previous_view
        st.rerun()
        
    st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
    
    st.markdown(textwrap.dedent(f"""
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
        st.markdown(textwrap.dedent(f"""
            <div style='background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 24px; margin-bottom: 24px; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);'>
                <h3 style='margin-top: 0; font-size: 1.2rem; font-weight: 600; color: white; margin-bottom: 16px;'>Ambiance & Features</h3>
                <div style='display: flex; flex-wrap: wrap; gap: 10px;'>
                    {" ".join([f'<span style="padding: 6px 14px; border-radius: 9999px; background: linear-gradient(to right, rgba(244,63,94,0.15), rgba(249,115,22,0.15)); border: 1px solid rgba(244,63,94,0.25); color: #fecdd3; font-weight: 500; font-size: 0.85rem;">{tag}</span>' for tag in item['ambiance']])}
                </div>
            </div>
        """), unsafe_allow_html=True)
        
        st.markdown(textwrap.dedent(f"""
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
        
        st.markdown(textwrap.dedent(f"""
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
        st.markdown(textwrap.dedent(f"""
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
