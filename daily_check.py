import os
import requests
import notion_client # Importing the full library

# 1. Credentials
TOKEN = os.getenv("NOTION_TOKEN")
DB_ID = os.getenv("NOTION_DATABASE_ID")
PO_USER = os.getenv("PUSHOVER_USER_KEY")
PO_TOKEN = os.getenv("PUSHOVER_API_TOKEN")

# 2. Establish Connection (Using a unique variable name)
# We call 'notion_client.Client' to ensure no name clash
my_fridge_bot = notion_client.Client(auth=TOKEN)

def get_fridge_report():
    try:
        # Use our specific 'my_fridge_bot' variable
        response = my_fridge_bot.databases.query(
            database_id=DB_ID,
            filter={"property": "Archived", "checkbox": {"equals": False}}
        )
        results = response.get("results", [])

        if not results:
            return "Fridge is empty! No leftovers today."

        msg = "🍱 Fridge Update:\n"
        for page in results:
            props = page.get("properties", {})
            
            # Safe Title extraction (Titles are always a list)
            title_data = props.get("Food", {}).get("title", [])
            food = title_data[0]["text"]["content"] if title_data else "Unknown"
            
            # Safe Formula extraction
            days = props.get("Days Left", {}).get("formula", {}).get("string", "N/A")
            
            msg += f"- {food}: {days}\n"
        return msg
    except Exception as e:
        # This will send the exact error to Pushover so we can see it
        return f"Error: {str(e)}"

# 3. Execution
report_text = get_fridge_report()
print(f"DEBUG REPORT: {report_text}")

# 4. Send via Pushover
requests.post("https://api.pushover.net", data={
    "token": PO_TOKEN,
    "user": PO_USER,
    "message": report_text,
    "title": "Fridge Alert",
    "priority": 1
})
