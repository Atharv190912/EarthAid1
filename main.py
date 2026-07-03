import streamlit as st
import pandas as pd
import pydeck as pdk
import os
from datetime import datetime
import base64
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import io
import random
from streamlit_cookies_manager import EncryptedCookieManager

# --- Constants ---
REPORTS_FILE = "reports.csv"
INITIATIVES_FILE = "initiatives.csv"
POINTS_FILE = "points.csv"
RESPONSES_FILE = "initiative_responses.csv"
USERS_FILE = "users.csv"
IMAGE_DIR = "images"
os.makedirs(IMAGE_DIR, exist_ok=True)

CATEGORY_COLORS = {
    "Climate Change": [255, 0, 0],
    "Deforestation": [0, 128, 0],
    "Air Pollution": [128, 128, 128],
    "Water Scarcity": [0, 0, 255],
    "Biodiversity Loss": [255, 165, 0],
    "Ocean Acidification": [255, 255, 0],
    "Soil Degradation": [165, 42, 42],
    "Microplastic Pollution": [255, 192, 203],
    "Overfishing": [0, 128, 128],
    "Other": [128, 0, 128]
}

SOLUTIONS = {
    "Climate Change": "Switch to renewable energy sources, plant trees, reduce fossil fuel use.",
    "Deforestation": "Promote tree plantation, use recycled products, support forest-friendly policies.",
    "Air Pollution": "Use public transport, reduce industrial emissions, promote clean energy.",
    "Water Scarcity": "Fix leaks, use water-saving appliances, support rainwater harvesting.",
    "Biodiversity Loss": "Support wildlife conservation, avoid habitat destruction, go organic.",
    "Ocean Acidification": "Reduce carbon footprint, support marine conservation, reduce plastic use.",
    "Soil Degradation": "Compost, avoid overuse of chemicals, practice crop rotation.",
    "Microplastic Pollution": "Use fewer plastics, support plastic bans, use reusable alternatives.",
    "Overfishing": "Consume sustainable seafood, support marine protected areas.",
    "Other": "Be mindful of the environment, share eco-friendly practices."
}

# Sample cities - expanded list for better global representation
cities = [
    ("New York, USA", 40.7128, -74.0060),
    ("Mumbai, India", 19.0760, 72.8777),
    ("Dubai, UAE", 25.276987, 55.296249),
    ("London, UK", 51.5074, -0.1278),
    ("Tokyo, Japan", 35.6762, 139.6503),
    ("Sydney, Australia", -33.8688, 151.2093),
    ("Rio de Janeiro, Brazil", -22.9068, -43.1729),
    ("Cape Town, South Africa", -33.9249, 18.4241),
    ("Paris, France", 48.8566, 2.3522),
    ("Beijing, China", 39.9042, 116.4074)
]

# ---------------- SAFE CSV LOADER ----------------
def safe_read_csv(file, columns):
    """Robust CSV loader: creates file with headers if missing, and
    returns an empty (but correctly-columned) DataFrame if the file
    exists but is empty or corrupted, instead of crashing."""
    if os.path.exists(file):
        try:
            if os.path.getsize(file) == 0:
                return pd.DataFrame(columns=columns)
            return pd.read_csv(file)
        except Exception:
            return pd.DataFrame(columns=columns)
    else:
        df = pd.DataFrame(columns=columns)
        df.to_csv(file, index=False)
        return df

# --- Load Credentials ---
def load_credentials():
    users_df = safe_read_csv(USERS_FILE, ["username", "name", "password"])
    credentials = {
        "usernames": {
            row["username"]: {
                "name": row["name"],
                "password": row["password"]
            }
            for _, row in users_df.iterrows()
        }
    }
    return users_df, credentials

users_df, credentials = load_credentials()

# --- Save Credentials ---
def save_credentials(df):
    try:
        df.to_csv(USERS_FILE, index=False)
    except Exception as e:
        st.error(f"Error saving credentials: {e}")
        print(f"Error saving credentials: {e}")

# --- Helper Functions ---
def get_base64_encoded_image(image_path):
    """Get base64 encoded image"""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

def add_bg_from_local(image_path):
    """Add background image from local file"""
    try:
        base64_image = get_base64_encoded_image(image_path)
        return f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{base64_image}");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
        """
    except:
        return ""

# ---------------- APP CONFIG (must come before any other st.* call) ----------------
st.set_page_config(
    page_title="EarthAid | Youth-powered Environmental Platform",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- SECURE COOKIE MANAGER (persistent login) ----------------
# The encryption key must live in Streamlit Secrets (.streamlit/secrets.toml locally,
# or the "Secrets" panel on Streamlit Community Cloud) as:
#
#   COOKIES_PASSWORD = "XzfCuEhcuZ4xzH2gXjsKwr73HteQ3frq"
#
# No hardcoded fallback password is used — if the secret is missing, the app
# refuses to start rather than silently falling back to a known/insecure key.
if "COOKIES_PASSWORD" in st.secrets:
    cookies = EncryptedCookieManager(
        prefix="earthaid_",
        password=st.secrets["COOKIES_PASSWORD"]
    )
else:
    st.error("⚠️ Configuration Error: `COOKIES_PASSWORD` not found in Streamlit Secrets. "
             "Add a strong, random secret to `.streamlit/secrets.toml` (or your Cloud app's "
             "Secrets settings) before running EarthAid.")
    st.stop()

if not cookies.ready():
    st.stop()

# --- Session State Setup ---
if "authentication_status" not in st.session_state:
    st.session_state['authentication_status'] = None
if "username" not in st.session_state:
    st.session_state['username'] = None
if "name" not in st.session_state:
    st.session_state['name'] = None
if "show_signup" not in st.session_state:
    st.session_state['show_signup'] = False
if "selected_report_index" not in st.session_state:
    st.session_state['selected_report_index'] = None
if "active_tab" not in st.session_state:
    st.session_state['active_tab'] = 0
if "selected_initiative" not in st.session_state:
    st.session_state['selected_initiative'] = None

# --- Helper functions for reporting data (crash-safe on empty CSVs) ---
def load_reports_data():
    """Load and prepare reports data"""
    return safe_read_csv(REPORTS_FILE,
        ["description", "category", "latitude", "longitude", "username", "before", "after", "timestamp"]
    )

def load_initiatives_data():
    """Load and prepare initiatives data"""
    return safe_read_csv(INITIATIVES_FILE,
        ["name", "description", "contact", "publisher", "timestamp"]
    )

def load_points_data():
    """Load points data"""
    return safe_read_csv(POINTS_FILE, ["username", "lifepoints"])

def load_responses_data():
    """Load initiative responses data"""
    return safe_read_csv(RESPONSES_FILE, ["initiative", "participant", "contact", "timestamp"])

def award_points(username, points=1):
    """Award points to a user"""
    points_df = load_points_data()
    if username in points_df["username"].values:
        points_df.loc[points_df["username"] == username, "lifepoints"] += points
    else:
        points_df = pd.concat([points_df, pd.DataFrame([[username, points]], columns=["username", "lifepoints"])], ignore_index=True)
    points_df.to_csv(POINTS_FILE, index=False)
    return points_df

# Auto-login from cookie if a valid session cookie exists.
# Re-validate against users.csv so a stale/tampered cookie can't log someone in.
if not st.session_state['authentication_status'] and cookies.get("logged_in") == "true":
    saved_username = cookies.get("username")
    saved_name = cookies.get("name")
    if saved_username and saved_username in credentials["usernames"]:
        st.session_state['authentication_status'] = True
        st.session_state['username'] = saved_username
        st.session_state['name'] = saved_name or credentials["usernames"][saved_username]["name"]

# --- Custom CSS for Modern UI ---
st.markdown("""
<style>
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&Adisplay=swap');
    * {font-family: 'Poppins', sans-serif;}

    /* Main app styling */
    .stApp {
        background-color: #f8f9fa;
        color: #333;
    }

    /* Headers */
    h1, h2, h3, h4 {
        color: #2e7d32;
        font-weight: 600;
        letter-spacing: -0.5px;
    }
    h1 {
        font-size: 2.5rem;
        margin-bottom: 1.5rem;
        background: linear-gradient(90deg, #2e7d32, #388e3c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Cards & containers */
    .card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 4px solid #4CAF50;
    }

    /* Sidebar Styling */
    div[data-testid="stSidebar"] {
        background-color: #ffffff;
        padding: 2rem 1.5rem;
        border-radius: 0;
        box-shadow: 0 0 10px rgba(0,0,0,0.05);
    }
    div[data-testid="stSidebar"] h2 {
        color: #2e7d32;
        font-size: 1.8rem;
        margin-bottom: 2rem;
        border-bottom: 2px solid #e0e0e0;
        padding-bottom: 10px;
    }
    div[data-testid="stSidebar"] label {
        color: #555;
        font-weight: 500;
        margin-bottom: 5px;
        display: block;
    }

    /* Form Inputs */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea,
    .stSelectbox>div>div>div,
    .stDateInput>div>div>input,
    .stMultiselect>div>div>div {
        background-color: #f9f9f9;
        border: 1px solid #e0e0e0;
        padding: 0.6rem;
        border-radius: 8px;
        box-shadow: none;
        font-size: 16px;
        transition: all 0.3s ease;
    }
    .stTextInput>div>div>input:focus,
    .stTextArea>div>div>textarea:focus {
        border-color: #4CAF50;
        box-shadow: 0 0 0 1px rgba(76, 175, 80, 0.3);
    }

    /* Buttons */
    .stButton>button {
        background-color: #2e7d32;
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
        width: 100%;
        height: auto;
        margin-top: 1rem;
    }
    .stButton>button:hover {
        background-color: #388e3c;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stButton>button:active {
        transform: translateY(0);
    }

    /* Alerts & Messages */
    .element-container .stAlert {
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .element-container .stAlert p {
        font-size: 16px;
        line-height: 1.6;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f1f8e9;
        border-radius: 5px 5px 0 0;
        padding: 10px 20px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #c8e6c9;
        color: #2e7d32;
    }

    /* Custom Components */
    .eco-badge {
        background-color: #e8f5e9;
        color: #2e7d32;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 14px;
        display: inline-block;
        margin-right: 5px;
    }

    .initiative-card {
        border: 1px solid #e0e0e0;
        border-left: 4px solid #4CAF50;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        background-color: white;
        transition: all 0.3s ease;
    }
    .initiative-card:hover {
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        transform: translateY(-3px);
    }

    /* Profile Card */
    .profile-card {
        background: linear-gradient(135deg, #e8f5e9, #c8e6c9);
        border-radius: 12px;
        padding: 25px;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
    }
    .profile-points {
        font-size: 32px;
        font-weight: 700;
        color: #2e7d32;
        margin: 10px 0;
    }

    /* Leaderboard */
    .leaderboard-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 15px;
        background-color: white;
        border-radius: 8px;
        margin-bottom: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }
    .leaderboard-item:nth-child(1) {
        background: linear-gradient(135deg, #fff9c4, #ffecb3);
    }
    .leaderboard-item:nth-child(2) {
        background: linear-gradient(135deg, #f5f5f5, #e0e0e0);
    }
    .leaderboard-item:nth-child(3) {
        background: linear-gradient(135deg, #ffe0b2, #ffcc80);
    }

    /* Upload buttons */
    .uploadedFile {
        background-color: #f1f8e9;
        border-radius: 8px;
        padding: 5px 10px;
    }

    /* Map Container */
    .map-container {
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    /* Report images */
    .report-image-container {
        display: flex;
        gap: 15px;
        margin-top: 20px;
    }
    .report-image {
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    .report-image:hover {
        transform: scale(1.02);
    }

    /* Mobile Responsiveness */
    @media (max-width: 768px) {
        h1 {
            font-size: 1.8rem;
        }
        .card {
            padding: 1rem;
        }
        .profile-card {
            padding: 15px;
        }
    }
</style>
""", unsafe_allow_html=True)

# ---------------------- USER AUTH SECTION ------------------------
if not st.session_state['authentication_status']:
    with st.sidebar:
        st.image("https://imgur.com/uJlMRu9.png", width=200)
        st.title("🌱 EarthAid Login")

        mode = st.radio("Choose an option:", ["Login", "Create Account"], horizontal=True)

        if mode == "Create Account":
            with st.form("signup_form"):
                st.subheader("Join EarthAid Community")
                new_name = st.text_input("Full Name", placeholder="Enter your full name")
                new_username = st.text_input("Username", placeholder="Choose a username")
                new_password = st.text_input("Password", type="password", placeholder="Choose a secure password")

                submit_button = st.form_submit_button("Create Account")

                if submit_button:
                    if new_username in users_df["username"].values:
                        st.error("❌ Username already exists.")
                    elif new_name and new_username and new_password:
                        new_user = pd.DataFrame([[new_username, new_name, new_password]],
                                                columns=["username", "name", "password"])
                        users_df = pd.concat([users_df, new_user], ignore_index=True)
                        users_df.to_csv(USERS_FILE, index=False)
                        st.success("✅ Account created! You can now log in.")
                        st.session_state['show_signup'] = False
                    else:
                        st.warning("Please fill all fields.")

            st.markdown("""
            <div style="text-align: center; margin-top: 20px; color: #666;">
                Already have an account? Select "Login" above.
            </div>
            """, unsafe_allow_html=True)

        elif mode == "Login":
            with st.form("login_form"):
                st.subheader("Welcome Back!")
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")

                submit_button = st.form_submit_button("Login")

                if submit_button:
                    if username in credentials["usernames"]:
                        if credentials["usernames"][username]["password"] == password:
                            st.session_state['authentication_status'] = True
                            st.session_state['name'] = credentials["usernames"][username]["name"]
                            st.session_state['username'] = username

                            # Persist login across refreshes/sessions via encrypted cookie
                            cookies["logged_in"] = "true"
                            cookies["username"] = username
                            cookies["name"] = credentials["usernames"][username]["name"]
                            cookies.save()

                            st.rerun()
                        else:
                            st.error("❌ Incorrect password. Please try again.")
                    else:
                        st.error("❌ Username not found. Please check your credentials.")

            st.markdown("""
            <div style="text-align: center; margin-top: 20px; color: #666;">
                New to EarthAid? Select "Create Account" above.
            </div>
            """, unsafe_allow_html=True)

    # Show a welcome banner for non-logged in users
    st.markdown("""
    <div style="text-align:center; padding: 40px 20px; background: linear-gradient(135deg, #e8f5e9, #c8e6c9); border-radius: 15px; margin-bottom: 30px;">
        <h1 style="margin-bottom: 10px; color: #2e7d32;">🌱 Welcome to EarthAid</h1>
        <p style="font-size: 20px; color: #333; max-width: 800px; margin: 0 auto 20px auto;">
            A youth-powered platform to report, solve, and act on environmental issues.
        </p>
        <p style="font-size: 16px; color: #555;">Please login or create an account to access all features.</p>
    </div>
    """, unsafe_allow_html=True)

    # Show features preview
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="card">
            <h3 style="text-align: center;">📢 Report Issues</h3>
            <p style="text-align: center;">Document environmental problems in your area and earn LifePoints.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="card">
            <h3 style="text-align: center;">🗺️ Interactive Map</h3>
            <p style="text-align: center;">Explore environmental issues reported around the world.</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="card">
            <h3 style="text-align: center;">🤝 Join Initiatives</h3>
            <p style="text-align: center;">Participate in local and global environmental initiatives.</p>
        </div>
        """, unsafe_allow_html=True)

    # About section
    st.markdown("""
    <div style="margin-top: 50px; padding: 20px; background: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
        <h2>👨‍💻 Created by Atharv Johari</h2>
        <p>A 12-year-old innovator passionate about environmental change and technology.</p>
        <p>EarthAid is designed to connect young environmental advocates and empower them to make a difference.</p>
    </div>
    """, unsafe_allow_html=True)

else:
    # --- Sidebar for logged in users ---
    with st.sidebar:
        st.image("https://imgur.com/uJlMRu9.png", width=150)

        # User profile summary
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 20px;">
            <p style="font-size: 18px; font-weight: 600; margin-bottom: 5px;">Welcome, {st.session_state['name']} 👋</p>
            <span style="font-size: 14px; color: #666;">@{st.session_state['username']}</span>
        </div>
        """, unsafe_allow_html=True)

        # Points display
        points_df = load_points_data()
        user_points = 0
        if st.session_state['username'] in points_df["username"].values:
            user_points = int(points_df[points_df["username"] == st.session_state['username']]["lifepoints"])

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #e8f5e9, #c8e6c9); padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
            <p style="font-size: 14px; margin-bottom: 5px;">Your LifePoints</p>
            <p style="font-size: 24px; font-weight: 700; color: #2e7d32; margin: 0;">{user_points} 🍃</p>
        </div>
        """, unsafe_allow_html=True)

        # Navigation
        st.subheader("Navigation")

        # Logout button
        if st.button("Logout", key="logout_button"):
            # Clear cookie so the session doesn't auto-restore
            cookies["logged_in"] = "false"
            cookies["username"] = ""
            cookies["name"] = ""
            cookies.save()

            for k in ['authentication_status', 'name', 'username']:
                st.session_state[k] = None
            st.rerun()

    # --- Main content for logged in users ---
    tabs = st.tabs(["🏠 Home", "📢 Report Issue", "🗺️ Earth Map", "🤝 Initiatives", "👤 Profile", "🏆 Leaderboard"])

    with tabs[0]:
        st.header("🌱 Welcome to EarthAid")

        # Welcome banner
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #e8f5e9, #c8e6c9); padding: 25px; border-radius: 15px; margin-bottom: 30px;">
            <h2 style="margin-top: 0;">Hello, {st.session_state['name']}!</h2>
            <p style="font-size: 18px;">Welcome to EarthAid - a youth-powered platform to report, solve, and act on environmental issues.</p>
            <p style="font-size: 16px; color: #555;">Join the mission. Earn LifePoints. Create change. 🌿</p>
        </div>
        """, unsafe_allow_html=True)

        # Dashboard stats
        col1, col2, col3 = st.columns(3)

        # Load data for stats
        reports_df = load_reports_data()
        initiatives_df = load_initiatives_data()

        with col1:
            st.markdown(f"""
            <div class="card" style="text-align: center;">
                <h3>Total Reports</h3>
                <p style="font-size: 32px; font-weight: 700; color: #2e7d32;">{len(reports_df)}</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="card" style="text-align: center;">
                <h3>Active Initiatives</h3>
                <p style="font-size: 32px; font-weight: 700; color: #2e7d32;">{len(initiatives_df)}</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="card" style="text-align: center;">
                <h3>Your LifePoints</h3>
                <p style="font-size: 32px; font-weight: 700; color: #2e7d32;">{user_points} 🍃</p>
            </div>
            """, unsafe_allow_html=True)

        # Recent activity
        st.subheader("Recent Activity")

        col_reports, col_initiatives = st.columns(2)

        with col_reports:
            st.markdown("""
            <div class="card">
                <h3>Recent Reports</h3>
            """, unsafe_allow_html=True)

            if not reports_df.empty:
                if "timestamp" in reports_df.columns:
                    recent_reports = reports_df.sort_values("timestamp", ascending=False).head(3)
                else:
                    recent_reports = reports_df.tail(3)

                for _, report in recent_reports.iterrows():
                    category = report.get('category', 'Unknown')
                    description = report.get('description', 'No description')
                    username = report.get('username', 'Anonymous')
                    st.markdown(f"""
                    <div style="padding: 10px; margin-bottom: 10px; border-left: 3px solid #4CAF50; background-color: #f9f9f9; border-radius: 5px;">
                        <span class="eco-badge">{category}</span>
                        <p style="margin: 5px 0;">{description[:100]}{'...' if len(description) > 100 else ''}</p>
                        <small style="color: #777;">Reported by @{username}</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.write("No reports yet. Be the first to report an issue!")

            st.markdown("</div>", unsafe_allow_html=True)

        with col_initiatives:
            st.markdown("""
            <div class="card">
                <h3>Recent Initiatives</h3>
            """, unsafe_allow_html=True)

            if not initiatives_df.empty:
                if "timestamp" in initiatives_df.columns:
                    recent_initiatives = initiatives_df.sort_values("timestamp", ascending=False).head(3)
                else:
                    recent_initiatives = initiatives_df.tail(3)

                for _, initiative in recent_initiatives.iterrows():
                    name = initiative.get('name', 'Untitled Initiative')
                    description = initiative.get('description', 'No description')
                    publisher = initiative.get('publisher', 'Anonymous')
                    st.markdown(f"""
                    <div style="padding: 10px; margin-bottom: 10px; border-left: 3px solid #2196F3; background-color: #f9f9f9; border-radius: 5px;">
                        <h4 style="margin: 0; color: #2196F3;">{name}</h4>
                        <p style="margin: 5px 0;">{description[:100]}{'...' if len(description) > 100 else ''}</p>
                        <small style="color: #777;">Created by @{publisher}</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.write("No initiatives yet. Start one today!")

            st.markdown("</div>", unsafe_allow_html=True)

        # About the creator
        st.markdown("""
        <div class="card" style="margin-top: 30px;">
            <h3>👨‍💻 Created by Atharv Johari</h3>
            <p>A youth innovator passionate about environmental change and technology.</p>
            <p>EarthAid is designed to connect young environmental advocates and empower them to make a difference through technology and community action.</p>
        </div>
        """, unsafe_allow_html=True)

        # Quick links
        st.subheader("Quick Actions")
        quick_col1, quick_col2 = st.columns(2)

        with quick_col1:
            if st.button("📝 Report New Issue", use_container_width=True):
                st.session_state["active_tab"] = 1
                st.rerun()

        with quick_col2:
            if st.button("🔍 View Global Map", use_container_width=True):
                st.session_state["active_tab"] = 2
                st.rerun()

    with tabs[1]:
        st.header("📢 Report Environmental Issue")

        # Instructions card
        st.markdown("""
        <div class="card">
            <h3>How to Report an Issue</h3>
            <p>1. Fill in the details about the environmental issue you've noticed</p>
            <p>2. Upload a photo of the issue (required)</p>
            <p>3. If you've taken action, upload an "after" photo (optional)</p>
            <p>4. Submit your report to earn LifePoints!</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([2, 1])

        with col1:
            with st.form("report_form"):
                st.subheader("Issue Details")
                desc = st.text_area("Describe the issue", placeholder="What environmental issue did you notice? Be specific.")

                col_cat, col_city = st.columns(2)
                with col_cat:
                    category = st.selectbox("Issue Category", list(CATEGORY_COLORS.keys()))
                with col_city:
                    city = st.selectbox("City", [c[0] for c in cities])

                st.markdown("<p style='margin-top:20px;'>Upload Images:</p>", unsafe_allow_html=True)

                col_img1, col_img2 = st.columns(2)
                with col_img1:
                    st.markdown("<p><strong>Before Photo (Required)</strong></p>", unsafe_allow_html=True)
                    before_img = st.file_uploader("", type=["jpg", "png", "jpeg"], key="before_img")

                with col_img2:
                    st.markdown("<p><strong>After Photo (Optional)</strong></p>", unsafe_allow_html=True)
                    after_img = st.file_uploader("", type=["jpg", "png", "jpeg"], key="after_img")

                submit_button = st.form_submit_button("Submit Report")

                if submit_button:
                    lat, lon = next(((lat, lon) for c, lat, lon in cities if c == city), (None, None))

                    if desc and category and st.session_state['username'] and before_img:
                        before_path, after_path = "", ""
                        if before_img:
                            before_path = os.path.join(IMAGE_DIR, f"{st.session_state['username']}_before_{datetime.now().timestamp()}.jpg")
                            with open(before_path, "wb") as f:
                                f.write(before_img.getbuffer())
                        if after_img:
                            after_path = os.path.join(IMAGE_DIR, f"{st.session_state['username']}_after_{datetime.now().timestamp()}.jpg")
                            with open(after_path, "wb") as f:
                                f.write(after_img.getbuffer())

                        df = load_reports_data()
                        new_row = {
                            "description": desc, "category": category, "latitude": lat,
                            "longitude": lon, "username": st.session_state['username'],
                            "before": before_path, "after": after_path,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                        df.to_csv(REPORTS_FILE, index=False)

                        award_points(st.session_state['username'], 1)

                        st.success("✅ Report successfully submitted! You earned 1 LifePoint.")

                        st.markdown(f"""
                        <div style="background-color: #e3f2fd; padding: 20px; border-radius: 10px; margin-top: 20px;">
                            <h3 style="color: #1565c0;">💡 Solution for {category}</h3>
                            <p>{SOLUTIONS.get(category, "Stay eco-conscious and spread awareness.")}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        if not before_img:
                            st.warning("Please upload a 'Before' photo of the issue.")
                        else:
                            st.warning("Please fill all required fields.")

        with col2:
            st.markdown("""
            <div class="card">
                <h3>Why Report?</h3>
                <ul style="list-style: none; padding-left: 0;">
                    <li>🌍 Help track environmental issues</li>
                    <li>💪 Inspire others to take action</li>
                    <li>🏆 Earn LifePoints</li>
                    <li>📊 Contribute to global data</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

            reports_df = load_reports_data()
            if not reports_df.empty and "category" in reports_df.columns:
                st.markdown("""
                <div class="card">
                    <h3>Top Issues Reported</h3>
                </div>
                """, unsafe_allow_html=True)

                category_counts = reports_df["category"].value_counts().head(5)
                for cat, count in category_counts.items():
                    st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; padding: 5px 0;">
                        <span>{cat}</span>
                        <span style="font-weight: bold; color: #2e7d32;">{count}</span>
                    </div>
                    """, unsafe_allow_html=True)

    # ---- Map tab with no-token map style + safe lat/lon mean ----
    with tabs[2]:
        st.header("🗺️ Live Earth Map")
        df = load_reports_data()

        if not df.empty:
            # Add city names to dataframe by matching coordinates
            city_names = []
            for _, row in df.iterrows():
                lat, lon = row['latitude'], row['longitude']
                city_name = "Unknown Location"
                for city, city_lat, city_lon in cities:
                    if pd.notna(lat) and pd.notna(lon) and abs(lat - city_lat) < 0.01 and abs(lon - city_lon) < 0.01:
                        city_name = city
                        break
                city_names.append(city_name)

            df['city_name'] = city_names

            # Drop rows with no valid coordinates before mapping
            map_df = df.dropna(subset=["latitude", "longitude"])

            # Safe center calculation — fallback if lat/lon are all NaN
            center_lat = map_df["latitude"].mean() if not map_df.empty else 20.0
            center_lon = map_df["longitude"].mean() if not map_df.empty else 0.0

            # Color points by category
            def _get_color(cat):
                return CATEGORY_COLORS.get(cat, [200, 30, 0]) + [180]

            if not map_df.empty:
                map_df = map_df.copy()
                map_df["color"] = map_df["category"].apply(_get_color)

                # Use CartoDB Positron style — no Mapbox token required
                st.pydeck_chart(pdk.Deck(
                    map_style='https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
                    initial_view_state=pdk.ViewState(
                        latitude=center_lat,
                        longitude=center_lon,
                        zoom=2,
                        pitch=50
                    ),
                    layers=[
                        pdk.Layer(
                            'ScatterplotLayer',
                            data=map_df,
                            get_position='[longitude, latitude]',
                            get_fill_color='color',
                            get_radius=200000,
                            pickable=True,
                        )
                    ],
                    tooltip={"text": "{category}\n{description}"}
                ))
            else:
                st.info("No reports with valid coordinates yet.")

            # Show all reports with images
            st.markdown("---")
            st.subheader("📍 Reported Issues")

            for idx, row in df.iterrows():
                city_name = row['city_name']
                category = row.get('category', 'Unknown')
                description = row.get('description', 'No description')
                username = row.get('username', 'Anonymous')
                before_img = row.get('before', '')
                after_img = row.get('after', '')

                st.markdown(f"""
                <div class="card">
                    <h4 style="color: #2e7d32; margin-top: 0;">📍 {city_name}</h4>
                    <span class="eco-badge">{category}</span>
                    <p style="margin-top: 10px;"><strong>Description:</strong> {description}</p>
                    <p><strong>Reported by:</strong> @{username}</p>
                </div>
                """, unsafe_allow_html=True)

                if before_img or after_img:
                    if st.button(f"📸 Check Images - {city_name}", key=f"view_img_{idx}"):
                        st.markdown("---")
                        img_cols = st.columns(2)

                        with img_cols[0]:
                            if before_img and os.path.exists(before_img):
                                st.markdown("**Before Image:**")
                                st.image(before_img, use_container_width=True)
                            else:
                                st.info("No 'Before' image available")

                        with img_cols[1]:
                            if after_img and os.path.exists(after_img):
                                st.markdown("**After Image:**")
                                st.image(after_img, use_container_width=True)
                            else:
                                st.info("No 'After' image uploaded yet")

                        st.markdown("---")

                st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.info("No reports yet to display on the map.")

    with tabs[3]:
        st.header("🤝 Initiatives")

        tab1, tab2 = st.tabs(["📝 Submit Initiative", "🌍 View & Join Initiatives"])

        with tab1:
            st.markdown("""
            <div class="card">
                <h3>Start Your Own Initiative</h3>
                <p>Have an idea to make a difference? Share it with the community and inspire others to join you!</p>
            </div>
            """, unsafe_allow_html=True)

            with st.form("initiative_form"):
                name_ = st.text_input("Initiative Name", placeholder="e.g., Community Beach Cleanup")
                desc_ = st.text_area("Describe your initiative", placeholder="What is your initiative about? What are the goals?")
                contact_ = st.text_input("Your contact info", placeholder="email@example.com or phone number")

                submit_init = st.form_submit_button("Submit Initiative")

                if submit_init:
                    if name_ and desc_ and contact_ and st.session_state['username']:
                        df = load_initiatives_data()
                        new_row = {
                            "name": name_,
                            "description": desc_,
                            "contact": contact_,
                            "publisher": st.session_state['username'],
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                        df.to_csv(INITIATIVES_FILE, index=False)

                        award_points(st.session_state['username'], 1)

                        st.success("✅ Initiative submitted successfully! You earned 1 LifePoint.")
                        st.balloons()
                    else:
                        st.warning("Please complete all fields.")

        with tab2:
            st.markdown("""
            <div class="card">
                <h3>Join an Initiative</h3>
                <p>Browse active initiatives and join the ones that resonate with you. Make a difference together! 🌱</p>
            </div>
            """, unsafe_allow_html=True)

            df = load_initiatives_data()

            if df.empty:
                st.info("No initiatives submitted yet. Be the first to start one!")
            else:
                if "timestamp" in df.columns:
                    df = df.sort_values("timestamp", ascending=False)

                for idx, row in df.iterrows():
                    st.markdown(f"""
                    <div class="initiative-card">
                        <h3 style="color: #2e7d32; margin-top: 0;">🌿 {row['name']}</h3>
                        <p><strong>Description:</strong> {row['description']}</p>
                        <p><strong>Organizer:</strong> @{row.get('publisher', 'Unknown')}</p>
                        <p><strong>Contact:</strong> {row['contact']}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    col_join, col_space = st.columns([1, 3])

                    with col_join:
                        if st.button(f"Join '{row['name']}'", key=f"join_{idx}", use_container_width=True):
                            if st.session_state['username']:
                                responses = load_responses_data()

                                already_joined = False
                                if not responses.empty:
                                    already_joined = ((responses["initiative"] == row['name']) &
                                                    (responses["participant"] == st.session_state['username'])).any()

                                if already_joined:
                                    st.warning(f"You've already joined '{row['name']}'!")
                                else:
                                    responses = pd.concat([responses, pd.DataFrame([{
                                        "initiative": row['name'],
                                        "participant": st.session_state['username'],
                                        "contact": row['contact'],
                                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    }])], ignore_index=True)
                                    responses.to_csv(RESPONSES_FILE, index=False)

                                    award_points(st.session_state['username'], 1)

                                    st.success(f"✅ Joined '{row['name']}'! You earned 1 LifePoint. The organizer has been notified.")
                            else:
                                st.warning("Please log in to join initiatives.")

                    st.markdown("---")

    with tabs[4]:
        st.header("👤 Your Profile")

        if st.session_state['username']:
            points_df = load_points_data()
            reports_df = load_reports_data()
            initiatives_df = load_initiatives_data()
            responses_df = load_responses_data()

            user_points = 0
            if st.session_state['username'] in points_df["username"].values:
                user_points = int(points_df[points_df["username"] == st.session_state['username']]["lifepoints"].values[0])

            user_reports = 0
            if not reports_df.empty and "username" in reports_df.columns:
                user_reports = len(reports_df[reports_df["username"] == st.session_state['username']])

            user_initiatives = 0
            if not initiatives_df.empty and "publisher" in initiatives_df.columns:
                user_initiatives = len(initiatives_df[initiatives_df["publisher"] == st.session_state['username']])

            user_joined = 0
            if not responses_df.empty and "participant" in responses_df.columns:
                user_joined = len(responses_df[responses_df["participant"] == st.session_state['username']])

            col_profile1, col_profile2 = st.columns([1, 2])

            with col_profile1:
                st.markdown(f"""
                <div class="profile-card">
                    <div style="font-size: 64px; margin-bottom: 10px;">👤</div>
                    <h2 style="margin: 10px 0;">{st.session_state['name']}</h2>
                    <p style="color: #666; margin-bottom: 20px;">@{st.session_state['username']}</p>
                    <div class="profile-points">{user_points} 🍃</div>
                    <p style="color: #555;">LifePoints</p>
                </div>
                """, unsafe_allow_html=True)

            with col_profile2:
                st.markdown("""
                <div class="card">
                    <h3>Your Impact</h3>
                </div>
                """, unsafe_allow_html=True)

                impact_col1, impact_col2 = st.columns(2)

                with impact_col1:
                    st.metric("Reports Submitted", user_reports, help="Environmental issues you've reported")
                    st.metric("Initiatives Created", user_initiatives, help="Initiatives you've started")

                with impact_col2:
                    st.metric("Initiatives Joined", user_joined, help="Initiatives you've participated in")

                    if not points_df.empty:
                        rank = (points_df["lifepoints"] > user_points).sum() + 1
                        st.metric("Global Rank", f"#{rank}", help="Your position on the leaderboard")

            st.markdown("---")
            st.subheader("🏅 Your Achievements")

            achievements = []

            if user_points >= 1:
                achievements.append(("🌱", "First Steps", "Earned your first LifePoint"))
            if user_points >= 5:
                achievements.append(("🌿", "Eco Warrior", "Earned 5 LifePoints"))
            if user_points >= 10:
                achievements.append(("🌳", "Environmental Champion", "Earned 10 LifePoints"))
            if user_reports >= 1:
                achievements.append(("📢", "Reporter", "Submitted your first report"))
            if user_reports >= 5:
                achievements.append(("📊", "Data Contributor", "Submitted 5 reports"))
            if user_initiatives >= 1:
                achievements.append(("💡", "Innovator", "Created your first initiative"))
            if user_joined >= 1:
                achievements.append(("🤝", "Team Player", "Joined your first initiative"))

            if achievements:
                cols = st.columns(min(4, len(achievements)))
                for i, (emoji, title, desc) in enumerate(achievements):
                    with cols[i % 4]:
                        st.markdown(f"""
                        <div style="text-align: center; padding: 15px; background: white; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 10px;">
                            <div style="font-size: 48px;">{emoji}</div>
                            <h4 style="margin: 10px 0 5px 0;">{title}</h4>
                            <p style="font-size: 12px; color: #666; margin: 0;">{desc}</p>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("Start participating to earn achievements!")

            st.markdown("---")
            st.subheader("📜 Certificate of Impact")

            if user_points >= 5:
                st.success("🎉 Congratulations! You're eligible for a Certificate of Impact!")
                st.markdown("""
                <div class="card">
                    <p>You've demonstrated significant commitment to environmental action. Your certificate is on its way!</p>
                    <p><em>(Certificate feature coming soon)</em></p>
                </div>
                """, unsafe_allow_html=True)
            else:
                points_needed = 5 - user_points
                st.info(f"Earn {points_needed} more LifePoint{'s' if points_needed > 1 else ''} to unlock your Certificate of Impact!")
                progress = user_points / 5
                st.progress(progress)

            st.markdown("---")
            st.subheader("📅 Your Recent Activity")

            activity_tab1, activity_tab2, activity_tab3 = st.tabs(["Your Reports", "Your Initiatives", "Joined Initiatives"])

            with activity_tab1:
                if not reports_df.empty and "username" in reports_df.columns:
                    user_reports_df = reports_df[reports_df["username"] == st.session_state['username']]
                    if not user_reports_df.empty:
                        for _, report in user_reports_df.iterrows():
                            category = report.get('category', 'Unknown')
                            description = report.get('description', 'No description')
                            timestamp = report.get('timestamp', '')
                            st.markdown(f"""
                            <div class="card">
                                <span class="eco-badge">{category}</span>
                                <p style="margin-top: 10px;"><strong>Description:</strong> {description}</p>
                                {f"<p><small>Reported on: {timestamp}</small></p>" if timestamp and pd.notna(timestamp) else ""}
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.write("You haven't submitted any reports yet.")
                else:
                    st.write("You haven't submitted any reports yet.")

            with activity_tab2:
                if not initiatives_df.empty and "publisher" in initiatives_df.columns:
                    user_initiatives_df = initiatives_df[initiatives_df["publisher"] == st.session_state['username']]
                    if not user_initiatives_df.empty:
                        for _, init in user_initiatives_df.iterrows():
                            name = init.get('name', 'Untitled')
                            description = init.get('description', 'No description')
                            timestamp = init.get('timestamp', '')

                            participants = 0
                            if not responses_df.empty and "initiative" in responses_df.columns:
                                participants = len(responses_df[responses_df["initiative"] == name])

                            st.markdown(f"""
                            <div class="card">
                                <h4 style="color: #2e7d32; margin-top: 0;">{name}</h4>
                                <p><strong>Description:</strong> {description}</p>
                                <p><strong>Participants:</strong> {participants}</p>
                                {f"<p><small>Created on: {timestamp}</small></p>" if timestamp and pd.notna(timestamp) else ""}
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.write("You haven't created any initiatives yet.")
                else:
                    st.write("You haven't created any initiatives yet.")

            with activity_tab3:
                if not responses_df.empty and "participant" in responses_df.columns:
                    user_responses_df = responses_df[responses_df["participant"] == st.session_state['username']]
                    if not user_responses_df.empty:
                        for _, resp in user_responses_df.iterrows():
                            initiative = resp.get('initiative', 'Unknown Initiative')
                            contact = resp.get('contact', 'No contact')
                            timestamp = resp.get('timestamp', '')
                            st.markdown(f"""
                            <div class="card">
                                <h4 style="color: #2196F3; margin-top: 0;">{initiative}</h4>
                                <p><strong>Contact:</strong> {contact}</p>
                                {f"<p><small>Joined on: {timestamp}</small></p>" if timestamp and pd.notna(timestamp) else ""}
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.write("You haven't joined any initiatives yet.")
                else:
                    st.write("You haven't joined any initiatives yet.")
        else:
            st.warning("Please log in to view your profile.")

    with tabs[5]:
        st.header("🏆 Leaderboard")

        st.markdown("""
        <div class="card">
            <h3>Top Environmental Champions</h3>
            <p>See who's making the biggest impact in the EarthAid community!</p>
        </div>
        """, unsafe_allow_html=True)

        points_df = load_points_data()

        if not points_df.empty:
            leaderboard = points_df.sort_values("lifepoints", ascending=False).reset_index(drop=True)

            leaderboard["rank"] = range(1, len(leaderboard) + 1)
            leaderboard["medal"] = ""

            if len(leaderboard) > 0:
                leaderboard.at[0, "medal"] = "🥇"
            if len(leaderboard) > 1:
                leaderboard.at[1, "medal"] = "🥈"
            if len(leaderboard) > 2:
                leaderboard.at[2, "medal"] = "🥉"

            st.subheader("🌟 Top 3 Champions")

            top3_cols = st.columns(3)

            for i in range(min(3, len(leaderboard))):
                with top3_cols[i]:
                    user_data = leaderboard.iloc[i]
                    medal = user_data["medal"]
                    username = user_data["username"]
                    points = int(user_data["lifepoints"])

                    colors = ["#FFD700", "#C0C0C0", "#CD7F32"]

                    st.markdown(f"""
                    <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, {colors[i]}22, {colors[i]}44); border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                        <div style="font-size: 48px; margin-bottom: 10px;">{medal}</div>
                        <h3 style="margin: 10px 0;">@{username}</h3>
                        <p style="font-size: 24px; font-weight: 700; color: #2e7d32; margin: 10px 0;">{points} 🍃</p>
                        <p style="color: #666; font-size: 14px;">Rank #{i+1}</p>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("---")
            st.subheader("📊 Full Leaderboard")

            for idx, row in leaderboard.iterrows():
                is_current_user = row["username"] == st.session_state['username']

                medal_display = row["medal"] if row["medal"] else "  "

                if is_current_user:
                    st.markdown(f"""
                    <div class="leaderboard-item" style="background: linear-gradient(135deg, #c8e6c9, #a5d6a7); border: 2px solid #2e7d32;">
                        <span style="font-weight: 700;">#{row["rank"]} {medal_display} @{row["username"]} (You)</span>
                        <span style="font-size: 18px; font-weight: 700; color: #2e7d32;">{int(row["lifepoints"])} 🍃</span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="leaderboard-item">
                        <span>#{row["rank"]} {medal_display} @{row["username"]}</span>
                        <span style="font-weight: 600; color: #2e7d32;">{int(row["lifepoints"])} 🍃</span>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("---")
            st.subheader("📈 Leaderboard Stats")

            stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)

            with stat_col1:
                st.metric("Total Users", len(leaderboard))

            with stat_col2:
                st.metric("Total LifePoints", int(leaderboard["lifepoints"].sum()))

            with stat_col3:
                st.metric("Average Points", f"{leaderboard['lifepoints'].mean():.1f}")

            with stat_col4:
                st.metric("Top Score", int(leaderboard["lifepoints"].max()))
        else:
            st.info("No leaderboard data yet. Be the first to earn LifePoints!")

            st.markdown("""
            <div class="card">
                <h3>How to Earn LifePoints</h3>
                <ul>
                    <li>📢 Submit an environmental report: <strong>+1 point</strong></li>
                    <li>💡 Create an initiative: <strong>+1 point</strong></li>
                    <li>🤝 Join an initiative: <strong>+1 point</strong></li>
                </ul>
                <p style="margin-top: 15px;">Start making an impact today and climb the leaderboard!</p>
            </div>
            """, unsafe_allow_html=True)
