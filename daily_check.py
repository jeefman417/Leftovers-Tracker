import os
import requests

# 1. Setup
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
PO_USER = os.getenv("PUSHOVER_USER_KEY")
PO_TOKEN = os.getenv("PUSHOVER_API_TOKEN")

def get_fridge_report():
    # Headers for Notion API
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # The Query Body
    data = {
        "filter": {"property": "Archived", "checkbox": {"equals": False}}
    }

    try:
        # Direct API Call
        url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        results = response.json().get("results", [])

        if not results:
            return "Fridge is empty! No leftovers today."

        msg = "🍱 Fridge Update:\n"
        for page in results:
            props = page.get("properties", {})
            
            # Extract Food Name
            title_list = props.get("Food", {}).get("title", [])
            food = title_list[0]["text"]["content"] if title_list else "Unknown"
            
            # Extract Days Left Formula
            days = props.get("Days Left", {}).get("formula", {}).get("string", "N/A")
            
            msg += f"- {food}: {days}\n"
        return msg
    except Exception as e:
        return f"Error: {str(e)}"

# 3. Execution
report_text = get_fridge_report()
print(f"DEBUG REPORT: {report_text}")

# 4. Send via Pushover
requests.post("https://api.pushover.net/1/messages.json", data={
    "token": PO_TOKEN,
    "user": PO_USER,
    "message": report_text,
    "title": "Fridge Alert",
    "priority": 1
})
