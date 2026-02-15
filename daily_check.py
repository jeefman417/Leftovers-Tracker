import os
import requests
from notion_client import Client

# 1. Setup Notion
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
notion_c = Client(auth=NOTION_TOKEN)

# 2. Query the Fridge
def get_fridge_summary():
    try:
        response = notion_c.databases.query(
            database_id=DATABASE_ID,
            filter={"property": "Archived", "checkbox": {"equals": False}}
        )
        results = response.get("results", [])
        
        if not results:
            return "🧊 Your fridge is empty! No leftovers to worry about today."
        
        msg = "🍱 Morning Fridge Update:\n"
        for page in results:
            p = page.get("properties", {})
            
            # --- FIX: Match these property names EXACTLY to Notion ---
            # Food Name
            title_list = p.get("Food", {}).get("title", [])
            food = title_list[0]["text"]["content"] if title_list else "Unknown"
            
            # Days Left
            days = p.get("Days Left", {}).get("formula", {}).get("string", "N/A")
            
            msg += f"- {food}: {days}\n"
        return msg
    except Exception as e:
        return f"❌ Error checking fridge: {str(e)}"

# 3. Send to Phone
topic = "my-fridge-alerts-2026" 
summary = get_fridge_summary()

requests.post(f"https://ntfy.sh/{topic}",
    data=summary.encode('utf-8'),
    headers={
        "Title": "Fridge Alert",
        "Priority": "high"
    }
)
