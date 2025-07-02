import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

def create_calendar_event_from_data(title, description, date_str, start_time, end_time, location="", attendees=None):
    """
    Creates a Google Calendar event with the provided data.
    
    Args:
        title: Event title
        description: Event description  
        date_str: Date in YYYY-MM-DD format
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
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_path):
                print(f"Error: credentials.json not found at {credentials_path}")
                print("Please download your OAuth2 credentials from Google Cloud Console")
                print("and save them as 'credentials.json' in the project root directory.")
                return
                
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)

        # Parse the date and times
        event_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
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
        print(f"✅ Calendar event created: {created_event.get('htmlLink')}")
        return created_event

    except HttpError as error:
        print(f"❌ An error occurred: {error}")
        raise


def main():
    """Shows basic usage of the Google Calendar API (legacy function for backward compatibility)."""
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
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_path):
                print(f"Error: credentials.json not found at {credentials_path}")
                print("Please download your OAuth2 credentials from Google Cloud Console")
                print("and save them as 'credentials.json' in the project root directory.")
                return
                
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)

        # --- CREATE THE EVENT ---
        
        # Get today's date and create start/end times
        today = datetime.date.today()
        start_time = datetime.datetime.combine(today, datetime.time(9, 0))  # 9:00 AM
        end_time = datetime.datetime.combine(today, datetime.time(10, 0))   # 10:00 AM
        
        # Format for Google Calendar API (ISO format)
        start_datetime = start_time.isoformat()
        end_datetime = end_time.isoformat()
        
        # Define the event details
        event = {
            'summary': 'My Python Coding Session',
            'location': 'My Desk',
            'description': 'A chance to write some awesome Python code!',
            'start': {
                'dateTime': start_datetime,
                'timeZone': 'America/Los_Angeles',
            },
            'end': {
                'dateTime': end_datetime,
                'timeZone': 'America/Los_Angeles',
            },
            'attendees': [
                {'email': 'nikita.dash.sh1rokov@gmail.com'},
                {'email': 'nikita.dash.sh1rokov@gmail.com'},
            ],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }

        # Call the Calendar API to insert the event
        event = service.events().insert(calendarId='primary', body=event).execute()
        print(f"Event created: {event.get('htmlLink')}")


    except HttpError as error:
        print(f"An error occurred: {error}")

if __name__ == "__main__":
    main()