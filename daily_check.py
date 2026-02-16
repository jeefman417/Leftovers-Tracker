import os
import requests
import notion_client

# 1. Credentials
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
PO_USER = os.getenv("PUSHOVER_USER_KEY")
PO_TOKEN = os.getenv("PUSHOVER_API_TOKEN")

# 2. Establish Connection (Unique variable name to avoid library clash)
fridge_conn = notion_client.Client(auth=NOTION_TOKEN)

def get_fridge_report():
    try:
        response = fridge_conn.databases.query(
            database_id=DATABASE_ID,
            filter={"property": "Archived", "checkbox": {"equals": False}}
        )
        results = response.get("results", [])

        if not results:
            return "Fridge is empty! No leftovers today."

        msg = "🍱 Fridge Update:\n"
        for page in results:
            props = page.get("properties", {})
            title_list = props.get("Food", {}).get("title", [])
            food = title_list[0]["text"]["content"] if title_list else "Unknown"
            days = props.get("Days Left", {}).get("formula", {}).get("string", "N/A")
            msg += f"- {food}: {days}\n"
        return msg
    except Exception as e:
        return f"Error: {str(e)}"

# 3. Execution
report = get_fridge_report()
print(f"REPORT: {report}")

# 4. Send via Pushover (No complex URL math required)
requests.post("https://api.pushover.net", data={
    "token": PO_TOKEN,
    "user": PO_USER,
    "message": report,
    "title": "Fridge Alert 🧊",
    "priority": 1 # High priority
})
