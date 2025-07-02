import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()


NOTION_API_KEY = os.getenv("NOTION_API_KEY")
PARENT_PAGE_ID =  os.getenv("PARENT_PAGE_ID")



def create_notion_note(title: str, content: str):
    """
    Creates a new note as a sub-page within the specified PARENT_PAGE_ID.
    
    Args:
        title (str): The title of the new note.
        content (str): The main text content of the note.
    """
    
    # The Notion API endpoint for creating pages
    url = "https://api.notion.com/v1/pages"

    # Headers required by the Notion API
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",  # Required version header
    }

    # The data payload for the new page
    # This specifies the parent, the title, and the content blocks
    payload = {
        "parent": {"page_id": PARENT_PAGE_ID},
        "properties": {
            "title": [
                {
                    "text": {
                        "content": title
                    }
                }
            ]
        },
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": content
                            }
                        }
                    ]
                }
            }
        ]
    }

    # Make the API request
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        # Check if the request was successful
        if response.status_code == 200:
            new_page_url = response.json().get("url")
            print(f"✅ Note successfully created!")
            print(f"   URL: {new_page_url}")
        else:
            # Print the error details if something went wrong
            print(f"❌ Error creating note (Status Code: {response.status_code})")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ An error occurred with the network request: {e}")


# --- HOW TO USE IT ---
if __name__ == "__main__":
    # 1. Define the title and content for your new note
    note_title = "Meeting Idea"
    note_content = "We should discuss the new marketing strategy in the next team meeting. Key points: budget, timeline, and target audience."

    # 2. Call the function to create the note in Notion
    create_notion_note(note_title, note_content)

    print("\n--- Creating another note ---")

    create_notion_note(
        title="Grocery List",
        content="Milk, Bread, Eggs, and Python snacks."
    )