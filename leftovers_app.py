import streamlit as st
import notion_client
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="Leftovers Tracker", page_icon="🍱", layout="wide")

# Notion API Setup
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID", "your-database-id-here")

# Initialize Notion client
try:
    if not NOTION_TOKEN:
        st.error("❌ NOTION_TOKEN not set in environment variables")
        st.stop()
    elif not (NOTION_TOKEN.startswith("secret_") or NOTION_TOKEN.startswith("ntn_")):
        st.error("❌ NOTION_TOKEN should start with 'secret_' or 'ntn_'")
        st.stop()
    else:
        notion = notion_client.Client(auth=NOTION_TOKEN)
        st.success("✅ Notion connected successfully!")
except Exception as e:
    st.error(f"❌ Notion connection failed: {str(e)}")
    st.stop()

def add_leftover(food_name, expires_days, location, added_by, notes="", photo_file=None):
    """Add new leftover to Notion database"""
    try:
        expires_date = (datetime.now() + timedelta(days=expires_days)).isoformat()
        
        # Build properties dictionary
        properties = {
            "Food": {"title": [{"text": {"content": food_name}}]},
            "Date Added": {"date": {"start": datetime.now().isoformat()}},
            "Expires": {"date": {"start": expires_date}},
            "Days Left": {"number": expires_days},
            "Status": {"select": {"name": "Fresh"}},
            "Location": {"rich_text": [{"text": {"content": location}}]},
            "Added By": {"select": {"name": added_by}},
            "Notes": {"rich_text": [{"text": {"content": notes}}]}
        }
        
        # Add photo if provided
        if photo_file is not None:
            # Upload photo to Notion
            with photo_file as file:
                file_content = file.read()
            
            # Create file in Notion
            notion_file = notion.files.upload({
                "purpose": "inline",
                "file": file_content
            })
            
            # Add photo to properties
            properties["Photo"] = {"files": [{"name": photo_file.name, "type": "file", "file": {"url": notion_file["url"]}}]}
        
        notion.pages.create(
            parent={"database_id": DATABASE_ID},
            properties=properties
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
            
            # Get photo URL if available
            photo_url = None
            if 'Photo' in props and props['Photo']['files']:
                photo_url = props['Photo']['files'][0]['file']['url']
            
            if expires:
                leftovers.append({
                    'food': food,
                    'expires': expires,
                    'days_left': days_left,
                    'location': location,
                    'added_by': added_by,
                    'notes': notes,
                    'photo_url': photo_url
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
        photo_file = st.file_uploader("Upload Photo (optional)", type=["jpg", "jpeg", "png", "gif"])
    
    with col2:
        expires_days = st.number_input("Expires in", min_value=1, max_value=7, value=3)
    
    location = st.selectbox("Location", [
        "Top shelf", "Middle shelf", "Bottom shelf", "Crisper drawer", "Door"
    ])
    
    added_by = st.selectbox("Added by", ["You", "Wife"])
    notes = st.text_area("Notes (optional)", placeholder="e.g., Half eaten, needs reheating")
    
    submitted = st.form_submit_button("Add Leftover")
    
    if submitted:
        success, message = add_leftover(food_name, expires_days, location, added_by, notes, photo_file)
        if success:
            st.success(f"✅ {message}")
            st.balloons()
        else:
            st.error(f"❌ {message}")

# Current Leftovers Display
st.header("Current Leftovers")
leftovers = get_leftovers()

if leftovers:
    for item in leftovers:
        days_left = item['days_left']
        if days_left <= 1:
            status_text = f"⚠️ Expires in {days_left} day!"
            color = "red"
        elif days_left <= 3:
            status_text = f"⚠️ Expires in {days_left} days!"
            color = "orange"
        else:
            status_text = f"✅ Expires in {days_left} days"
            color = "green"
        
        # Display photo if available
        if item['photo_url']:
            st.image(item['photo_url'], width=150, caption=item['food'])
        
        st.markdown(f"""
        <div style="color: {color}; font-weight: bold; padding: 10px; border-radius: 5px; margin: 10px 0;">
        🍕 **{item['food']}** | 📍 {item['location']} | 👤 {item['added_by']}  
        {status_text} | 📅 {item['expires'][:10]} | 📝 {item['notes']}
        </div>
        """, unsafe_allow_html=True)
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
