import os
import requests
from notion_client import Client

# 1. Setup
token = os.getenv("NOTION_TOKEN")
db_id = os.getenv("NOTION_DATABASE_ID")
po_user = os.getenv("PUSHOVER_USER_KEY")
po_token = os.getenv("PUSHOVER_API_TOKEN")

# Initialize specifically
client = Client(auth=token)

# 2. Query (Directly, no 'try' block so we can see the real error)
response = client.databases.query(
    database_id=db_id,
    filter={"property": "Archived", "checkbox": {"equals": False}}
)
results = response.get("results", [])

# 3. Build Message
if not results:
    msg = "Fridge is empty!"
else:
    msg = "🍱 Fridge Update:\n"
    for page in results:
        p = page["properties"]
        # Using a more robust way to get the text
        food = p["Food"]["title"][0]["text"]["content"] if p["Food"]["title"] else "Unknown"
        days = p["Days Left"]["formula"]["string"] if "formula" in p["Days Left"] else "N/A"
        msg += f"- {food}: {days}\n"

print(f"Final Message: {msg}")

# 4. Send to Pushover
requests.post("https://api.pushover.net", data={
    "token": po_token,
    "user": po_user,
    "message": msg,
    "title": "Fridge Alert",
    "priority": 1
})
