import os
import requests
from notion_client import Client

# 1. Setup Credentials
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
PO_USER = os.getenv("PUSHOVER_USER_KEY")
PO_TOKEN = os.getenv("PUSHOVER_API_TOKEN")

# Initialize the client
# We use a unique variable name 'fridge_app' to avoid name clashes
fridge_app = Client(auth=NOTION_TOKEN)

def get_fridge_report():
    try:
        # RAW REQUEST METHOD: This bypasses the '.databases.query' shortcut 
        # that is causing the AttributeError.
        response = fridge_app.request(
            path=f"databases/{DATABASE_ID}/query",
            method="POST",
            body={
                "filter": {"property": "Archived", "checkbox": {"equals": False}}
            }
        )
        
        results = response.get("results", [])

        if not results:
            return "Fridge is empty! No leftovers today."

        msg = "🍱 Fridge Update:\n"
        for page in results:
            props = page.get("properties", {})
            
            # Safe Title extraction (Notion titles are lists)
            title_data = props.get("Food", {}).get("title", [])
            food = title_data[0]["text"]["content"] if title_data else "Unknown"
            
            # Safe Formula extraction
            days = props.get("Days Left", {}).get("formula", {}).get("string", "N/A")
            
            msg += f"- {food}: {days}\n"
        return msg
    except Exception as e:
        return f"Error: {str(e)}"

# 3. Execution
final_report = get_fridge_report()
print(f"DEBUG REPORT: {final_report}")

# 4. Send via Pushover
requests.post("https://api.pushover.net", data={
    "token": PO_TOKEN,
    "user": PO_USER,
    "message": final_report,
    "title": "Fridge Alert",
    "priority": 1
})
