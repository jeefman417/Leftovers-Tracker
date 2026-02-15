import os
import requests
import notion_client

# 1. Setup Notion
# Using 'my_fridge_connection' so there is ZERO chance of a name clash
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# Initialize the client from the library
my_fridge_connection = notion_client.Client(auth=NOTION_TOKEN)

def get_fridge_summary():
    try:
        # Use our unique variable name here
        response = my_fridge_connection.databases.query(
            database_id=DATABASE_ID,
            filter={"property": "Archived", "checkbox": {"equals": False}}
        )
        results = response.get("results", [])
        
        if not results:
            return "Your fridge is currently empty! No leftovers to track."
        
        msg = "🍱 Morning Fridge Update:\n"
        for page in results:
            p = page.get("properties", {})
            
            # Extract Food Name (Handling the Notion list structure)
            title_list = p.get("Food", {}).get("title", [])
            food = title_list[0].get("text", {}).get("content", "Unknown") if title_list else "Unknown Food"
            
            # Extract Days Left (From your Notion formula)
            days = p.get("Days Left", {}).get("formula", {}).get("string", "N/A")
            
            msg += f"- {food}: {days}\n"
        return msg
    except Exception as e:
        # If it fails, this will send the exact error text to your phone
        return f"Error checking Notion: {str(e)}"

# 2. Generate the message
summary = get_fridge_summary()

# 3. Print to GitHub Logs (for debugging)
print("--- ROBOT OUTPUT ---")
print(summary)

# 4. Send to Phone via ntfy.sh
# SLASH IS DEFINITELY INCLUDED HERE /
topic = "my-fridge-alerts-2026" 
final_url = "https://ntfy.sh" + topic

try:
    requests.post(
        final_url,
        data=summary.encode('utf-8'),
        headers={
            "Title": "Fridge Alert",
            "Priority": "high"
        }
    )
    print("--- NOTIFICATION SENT ---")
except Exception as e:
    print(f"--- FAILED TO SEND NOTIFICATION: {e} ---")
