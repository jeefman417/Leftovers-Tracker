import os
import requests
from notion_client import Client

# 1. Setup
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# RENAME the variable to 'notion_app' to avoid name clashes
notion_app = Client(auth=NOTION_TOKEN)

def get_fridge_summary():
    try:
        # We use the renamed 'notion_app' variable here
        response = notion_app.databases.query(
            database_id=DATABASE_ID,
            filter={"property": "Archived", "checkbox": {"equals": False}}
        )
        results = response.get("results", [])
        
        if not results:
            return "🧊 Your fridge is empty! No leftovers to worry about today."
        
        msg = "🍱 Morning Fridge Update:\n"
        for page in results:
            p = page.get("properties", {})
            
            # Safe Food Name extraction
            title_list = p.get("Food", {}).get("title", [])
            food = title_list[0]["text"]["content"] if title_list else "Unknown"
            
            # Safe Days Left extraction
            days = p.get("Days Left", {}).get("formula", {}).get("string", "N/A")
            
            msg += f"- {food}: {days}\n"
        return msg
    except Exception as e:
        # This will send the exact error to your phone if it fails
        return f"❌ Error checking fridge: {str(e)}"

# 3. Send to Phone (Fixed URL with the Slash /)
topic = "my-fridge-alerts-2026" 
summary = get_fridge_summary()

requests.post(f"https://ntfy.sh/{topic}",
    data=summary.encode('utf-8'),
    headers={
        "Title": "Fridge Alert",
        "Priority": "high"
    }
)
