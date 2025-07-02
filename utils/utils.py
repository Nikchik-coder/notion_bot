# Import configuration from config module
from config.config import (
    whisper_client, llm, generate_text,
    NOTION_API_KEY, PARENT_PAGE_ID, CALENDAR_SCOPES
)
import datetime
import os.path
import requests
import json
import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging
logger = logging.getLogger(__name__)

# Re-export for backward compatibility
__all__ = ['whisper_client', 'llm', 'generate_text', 'create_calendar_event_from_data', 'create_notion_note']


def create_calendar_event_from_data(title, description, date_str, start_time, end_time, location="", attendees=None):
    """
    Creates a Google Calendar event with the provided data.
    
    Args:
        title: Event title
        description: Event description  
        date_str: Date in YYYY-MM-DD format (IGNORED - always uses today's date)
        start_time: Start time in HH:MM format
        end_time: End time in HH:MM format
        location: Event location (optional)
        attendees: List of email addresses (optional)
    """
    if attendees is None:
        attendees = []
        
    creds = None
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level to the project root
    project_root = os.path.dirname(script_dir)
    
    # Paths for credentials and token files
    credentials_path = os.path.join(project_root, "credentials.json")
    token_path = os.path.join(project_root, "token.json")
    
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, CALENDAR_SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_path):
                logger.error(f"credentials.json not found at {credentials_path}. Please download your OAuth2 credentials from Google Cloud Console and save them as 'credentials.json' in the project root directory.")
                return
                
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, CALENDAR_SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)

        # ALWAYS use today's date regardless of what was passed in
        event_date = datetime.date.today()
        start_hour, start_min = map(int, start_time.split(':'))
        end_hour, end_min = map(int, end_time.split(':'))
        
        # Create datetime objects
        start_datetime = datetime.datetime.combine(event_date, datetime.time(start_hour, start_min))
        end_datetime = datetime.datetime.combine(event_date, datetime.time(end_hour, end_min))
        
        # Format for Google Calendar API (ISO format)
        start_iso = start_datetime.isoformat()
        end_iso = end_datetime.isoformat()
        
        # Prepare attendees list
        attendee_list = [{'email': email} for email in attendees]
        
        # Define the event details
        event = {
            'summary': title,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start_iso,
                'timeZone': 'America/Los_Angeles',  # You may want to make this configurable
            },
            'end': {
                'dateTime': end_iso,
                'timeZone': 'America/Los_Angeles',
            },
            'attendees': attendee_list,
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }

        # Call the Calendar API to insert the event
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        logger.info(f"Calendar event created successfully: {created_event.get('htmlLink')}")
        return created_event

    except HttpError as error:
        logger.error(f"Google Calendar API error: {error}")
        raise


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
            logger.info(f"Notion note created successfully: {new_page_url}")
        else:
            # Log error details if something went wrong
            logger.error(f"Error creating Notion note (Status Code: {response.status_code}): {response.text}")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Network request error while creating Notion note: {e}")