import os
import requests
from notion_client import Client

# 1. Setup Notion
# We use 'notion_c' as the variable name to avoid any name conflicts
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
notion_c = Client(auth=NOTION_TOKEN)

# 2. Query the Fridge
def get_fridge_summary():
    try:
        # We explicitly use 'database_id=' as a keyword argument
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
            
            # Safe Food Name extraction
            food_title = p.get("Food", {}).get("title", [])
            food = food_title[0]["text"]["content"] if food_title else "Unknown"
            
            # Safe Days Left extraction
            days = p.get("Days Left", {}).get("formula", {}).get("string", "N/A")
            
            msg += f"- {food}: {days}\n"
        return msg
    except Exception as e:
        return f"❌ Error checking fridge: {str(e)}"

# 3. Send to Phone (Using ntfy.sh)
topic = "my-fridge-alerts-2026" 
summary = get_fridge_summary()

requests.post(f"https://ntfy.sh{topic}",
    data=summary.encode('utf-8'),
    headers={
        "Title": "Fridge Alert",
        "Priority": "high"
    }
)
