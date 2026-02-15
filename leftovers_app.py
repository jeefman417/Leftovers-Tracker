import streamlit as st
from notion_client import Client
import cloudinary.uploader
import cloudinary
from datetime import datetime, timedelta

# --- 1. CONFIGURATION & SECRETS ---
st.set_page_config(page_title="Fridge Leftovers Tracker", page_icon="🧊", layout="wide")

try:
    # Notion Credentials
    notion = Client(auth=st.secrets["NOTION_TOKEN"])
    DATABASE_ID = st.secrets["NOTION_DATABASE_ID"]
    
    # Cloudinary Credentials
    cloudinary.config(
        cloud_name=st.secrets["CLOUDINARY_CLOUD_NAME"],
        api_key=st.secrets["CLOUDINARY_API_KEY"],
        api_secret=st.secrets["CLOUDINARY_API_SECRET"]
    )
except Exception as e:
    st.error("❌ Missing Secrets! Check your Streamlit Cloud Settings.")
    st.stop()

# --- 2. HELPER FUNCTIONS ---
def add_leftover(food_name, expiry_date, location, added_by, meal_cost, notes="", photo_file=None):
    """Sends new leftover data to Notion"""
    try:
        image_url = None
        if photo_file:
            upload_result = cloudinary.uploader.upload(photo_file)
            image_url = upload_result["secure_url"]

        new_page = {
            "parent": {"database_id": DATABASE_ID},
            "properties": {
                "Food": {"title": [{"text": {"content": food_name}}]},
                "Date Added": {"date": {"start": datetime.now().date().isoformat()}},
                "Expires": {"date": {"start": expiry_date.isoformat()}},
                "Meal Cost": {"number": meal_cost},
                "Location": {"select": {"name": location}},
                "Added By": {"select": {"name": added_by}},
                "Notes": {"rich_text": [{"text": {"content": notes}}]},
                "Archived": {"checkbox": False}
            }
        }

        if image_url:
            new_page["properties"]["Photo"] = {
                "files": [{"name": f"Photo_{food_name}", "type": "external", "external": {"url": image_url}}]
            }

        notion.pages.create(**new_page)
        return True, "Added to the fridge!"
    except Exception as e:
        return False, str(e)

# --- 3. UI - ADD NEW ITEM ---
st.title("🧊 Fridge Leftover Tracker")

with st.form("add_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        food_name = st.text_input("What food is it?")
        location = st.selectbox("Location", ["Top shelf", "Middle shelf", "Bottom shelf", "Crisper drawer", "Door"])
        photo_file = st.camera_input("Take a photo")
        
    with col2:
        added_by = st.selectbox("Who added it?", ["You", "Wife"])
        # Set min_value to today to prevent "wonky" dates
        expiry_date = st.date_input("Expiration Date", min_value=datetime.now().date(), value=datetime.now().date() + timedelta(days=3))
        meal_cost = st.number_input("Estimated Meal Cost ($)", min_value=0.0, value=5.0, step=0.50)
        notes = st.text_area("Notes")

    if st.form_submit_button("Add to Fridge"):
        if food_name:
            success, msg = add_leftover(food_name, expiry_date, location, added_by, meal_cost, notes, photo_file)
            if success: 
                st.success(msg)
                st.balloons()
            else: st.error(f"Error: {msg}")
        else:
            st.warning("Please enter a food name.")

# --- 4. UI - FRIDGE VIEW & VERDICT ---
st.divider()
st.header("🔍 Current Fridge Inventory")

# Query only non-archived items
results = notion.databases.query(
    database_id=DATABASE_ID,
    filter={"property": "Archived", "checkbox": {"equals": False}}
).get("results")

# Replace your current display loop with this "Safe" version:

if not results:
    st.info("The fridge is empty! Time to cook something new.")
else:
    for page in results:
        p = page.get("properties", {})  # Use .get to avoid None errors
        item_id = page["id"]

        # --- Safe Data Extraction ---
        # Food Title
        food_title = p.get("Food", {}).get("title", [])
        food = food_title[0]["text"]["content"] if food_title else "Unknown Food"

        # Meal Cost (Handles empty numbers)
        cost_prop = p.get("Meal Cost", {}).get("number")
        cost = cost_prop if cost_prop is not None else 0.0

        # Status & Days Left (Handles empty formulas)
        status = p.get("Status", {}).get("formula", {}).get("string", "No Status")
        days_left = p.get("Days Left", {}).get("formula", {}).get("string", "N/A")

        # Photo (Handles empty files)
        photo_files = p.get("Photo", {}).get("files", [])
        photo = photo_files[0].get("external", {}).get("url") if photo_files else None

        # Location & Added By
        loc_prop = p.get("Location", {}).get("select")
        loc = loc_prop["name"] if loc_prop else "Unknown"
        
        user_prop = p.get("Added By", {}).get("select")
        user = user_prop["name"] if user_prop else "Unknown"

        # --- UI Display ---
        with st.container():
            c1, c2, c3 = st.columns([1, 2, 1])
            with c1:
                if photo: st.image(photo, width=150)
                else: st.write("📷 No photo")
            with c2:
                st.subheader(food)
                st.write(f"📍 {loc} | 👤 {user}")
                st.write(f"**Status:** {status} ({days_left})")
                st.write(f"💰 **Value:** ${cost:.2f}")
            with c3:
                # Same buttons as before...
