import streamlit as st
import notion_client
from datetime import datetime, timedelta
import os

# Page configuration
st.set_page_config(
    page_title="Leftovers Tracker",
    page_icon="🍱",
    layout="wide"
)

# Custom CSS for mobile optimization
st.markdown("""
<style>
    .main { padding: 1rem; }
    .stButton { width: 100%; }
    .stTextInput { width: 100%; }
    .stNumberInput { width: 100%; }
    .stSelectbox { width: 100%; }
    .stTextArea { width: 100%; }
    .expiring-soon { color: #ff6b6b; font-weight: bold; }
    .fresh { color: #51cf66; }
</style>
""", unsafe_allow_html=True)

# Notion API Setup
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID", "your-database-id-here")

# Initialize Notion client
try:
    if not NOTION_TOKEN:
        st.sidebar.error("❌ NOTION_TOKEN not set in environment variables")
        notion_available = False
    elif not (NOTION_TOKEN.startswith("secret_") or NOTION_TOKEN.startswith("ntn_")):
        st.sidebar.error("❌ NOTION_TOKEN should start with 'secret_' or 'ntn_'")
        notion_available = False
    else:
        notion = notion_client.Client(auth=NOTION_TOKEN)
        notion_available = True
        st.sidebar.success("✅ Notion connected successfully!")
except Exception as e:
    notion_available = False
    st.sidebar.error(f"❌ Notion connection failed: {str(e)}")

def add_leftover(food_name, expires_days, location, added_by, notes=""):
    """Add new leftover to Notion database"""
    if not notion_available:
        return False, "Notion API not available"
    
    try:
        expires_date = (datetime.now() + timedelta(days=expires_days)).isoformat()
        
        notion.pages.create(
            parent={"database_id": DATABASE_ID},
            properties={
                "Food": {"title": [{"text": {"content": food_name}}]},
                "Date Added": {"date": {"start": datetime.now().isoformat()}},
                "Expires": {"date": {"start": expires_date}},
                "Days Left": {"number": expires_days},
                "Status": {"select": {"name": "Fresh"}},
                "Location": {"rich_text": [{"text": {"content": location}}]},
                "Added By": {"select": {"name": added_by}},
                "Notes": {"rich_text": [{"text": {"content": notes}}]}
            }
        )
        return True, "Leftover added successfully!"
    except Exception as e:
        return False, f"Error: {str(e)}"

def get_leftovers():
    """Get all leftovers from Notion"""
    try:
        # Simple approach - get all pages from database
        response = notion.databases.query(database_id=DATABASE_ID)
        
        leftovers = []
        for item in response['results']:
            props = item['properties']
            food = props['Food']['title'][0]['text']['content'] if props['Food']['title'] else 'Unknown'
            expires = props['Expires']['date']['start'] if props['Expires']['date'] else None
            days_left = props['Days Left']['number'] if props['Days Left']['number'] else 0
            location = props['Location']['rich_text'][0]['text']['content'] if props['Location']['rich_text'] else 'Unknown'
            added_by = props['Added By']['select']['name'] if props['Added By']['select'] else 'Unknown'
            notes = props['Notes']['rich_text'][0]['text']['content'] if props['Notes']['rich_text'] else ''
            
            if expires:
                leftovers.append({
                    'food': food,
                    'expires': expires,
                    'days_left': days_left,
                    'location': location,
                    'added_by': added_by,
                    'notes': notes
                })
        
        return leftovers
        
    except Exception as e:
        st.error(f"Error fetching leftovers: {str(e)}")
        return []

# Main App UI
st.title("🍱 Leftovers Tracker")
st.write("Track your leftovers and reduce food waste!")

# Add New Leftover Form
st.header("Add New Leftover")
with st.form("add_leftover"):
    col1, col2 = st.columns([2, 1])
    
    with col1:
        food_name = st.text_input("Food Name", placeholder="e.g., Pizza, Chicken pasta")
    
    with col2:
        expires_days = st.number_input("Expires in", min_value=1, max_value=7, value=3)
    
    location = st.selectbox("Location", [
        "Top shelf", 
        "Middle shelf", 
        "Bottom shelf", 
        "Crisper drawer",
        "Door"
    ])
    
    added_by = st.selectbox("Added by", ["You", "Wife"])
    notes = st.text_area("Notes (optional)", placeholder="e.g., Half eaten, needs reheating")
    
    submitted = st.form_submit_button("Add Leftover")
    
    if submitted:
        success, message = add_leftover(food_name, expires_days, location, added_by, notes)
        if success:
            st.success(f"✅ {message}")
            st.balloons()
        else:
            st.error(f"❌ {message}")

# Current Leftovers Display
st.header("Current Leftovers")
leftovers = get_leftovers()

if leftovers:
    tab1, tab2, tab3 = st.tabs(["All Leftovers", "Expiring Soon", "This Week"])
    
    with tab1:
        st.subheader("All Leftovers")
        for item in leftovers:
            days_left = item['days_left']
            if days_left <= 1:
                status_class = "expiring-soon"
                status_text = f"⚠️ Expires in {days_left} day!"
            elif days_left <= 3:
                status_class = "expiring-soon"
                status_text = f"⚠️ Expires in {days_left} days!"
            else:
                status_class = "fresh"
                status_text = f"✅ Expires in {days_left} days"
            
            st.markdown(f"""
            <div class="{status_class}">
            🍕 **{item['food']}**  
            📍 {item['location']} | 👤 {item['added_by']}  
            {status_text} | 📅 {item['expires'][:10]}  
            📝 {item['notes']}
            </div>
            """, unsafe_allow_html=True)
    
    with tab2:
        st.subheader("Expiring Soon (≤ 2 days)")
        expiring_soon = [item for item in leftovers if item['days_left'] <= 2]
        if expiring_soon:
            for item in expiring_soon:
                st.warning(f"🍕 **{item['food']}** - Expires in {item['days_left']} day(s) - {item['location']}")
        else:
            st.info("🎉 Nothing expiring soon! Great job!")
    
    with tab3:
        st.subheader("This Week (≤ 7 days)")
        this_week = [item for item in leftovers if item['days_left'] <= 7]
        for item in this_week:
            st.info(f"🍕 **{item['food']}** - {item['days_left']} days left - {item['location']}")

else:
    st.info("🎯 Add your first leftover above to get started!")

# Statistics
st.header("📊 Waste Reduction Stats")
col1, col2, col3 = st.columns(3)

with col1:
    total_items = len(leftovers)
    st.metric("Total Items", total_items)

with col2:
    expiring_count = len([item for item in leftovers if item['days_left'] <= 2])
    st.metric("Expiring Soon", expiring_count)

with col3:
    estimated_savings = total_items * 5
    st.metric("Est. Savings", f"${estimated_savings}")

# Footer
st.markdown("---")
st.markdown("💡 **Tip:** Check this app daily to stay on top of your leftovers!")
