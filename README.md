# Notion Bot - Audio Recording & Event Creation

A comprehensive Python bot that records audio, transcribes it with Whisper, analyzes it with AI, and automatically creates events in both Notion and Google Calendar.

## Features

🎤 **Audio Recording** - Record voice notes directly from your microphone
🗣️ **Speech Transcription** - Convert audio to text using OpenAI Whisper
🤖 **AI Analysis** - Extract event details using LLM (Google Gemini or Together AI)
📝 **Notion Integration** - Automatically create structured notes in Notion
📅 **Calendar Integration** - Create Google Calendar events from voice notes

## Setup Instructions

### 1. Create a Notion Integration

1. Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click "New integration"
3. Give it a name (e.g., "Python Notes Bot")
4. Select the workspace where you want to create notes
5. Click "Submit"
6. Copy the "Internal Integration Token" (starts with `secret_`)

### 2. Set up Google Calendar API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google Calendar API
4. Create credentials (OAuth 2.0 Client ID)
5. Download the credentials file and save it as `credentials.json` in the project root

### 3. Set up AI API Keys

Choose one or more providers:

**For Whisper (Speech-to-Text):**
- OpenAI: Get API key from [OpenAI Platform](https://platform.openai.com/)
- DeepInfra: Get API key from [DeepInfra](https://deepinfra.com/)

**For LLM Analysis:**
- Google Gemini: Get API key from [Google AI Studio](https://makersuite.google.com/)
- Together AI: Get API key from [Together AI](https://together.ai/)

### 4. Set up Environment Variables

Create a `.env` file in the project root with your API keys:

```env
# Notion Configuration
NOTION_API_KEY=your_notion_api_key_here
PARENT_PAGE_ID=your_32_character_page_id_here

# Whisper Configuration (choose one)
WHISPER_API_KEY=your_whisper_api_key_here
WHISPER_BASE_URL=https://api.deepinfra.com/v1/openai
WHISPER_MODEL=openai/whisper-large-v3

# LLM Configuration (choose one)
# Option 1: Google Gemini
GOOGLE_API_KEY=your_google_api_key_here
LLM_MODEL=gemini-pro

# Option 2: Together AI
# TOGETHER_API_KEY=your_together_api_key_here
# LLM_MODEL=mistralai/Mixtral-8x7B-Instruct-v0.1
```

### 5. Get Your Parent Page ID

1. Go to your Notion workspace
2. Find or create the page where you want to store your notes
3. Copy the page URL (it looks like: `https://notion.so/workspace/page-title-32char-id`)
4. Extract the 32-character ID from the URL (the part after the last dash)
5. **Important**: Give your integration access to this page:
   - Click the "..." menu on the page
   - Select "Add connections"
   - Choose your integration

### 6. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note for Windows users:** If you encounter issues with `pyaudio`, you may need to install it using:
```bash
pip install pipwin
pipwin install pyaudio
```

### 7. Test the Setup

Run the script to validate your setup:

```bash
python src/note.py
```

The script will first validate your configuration and then create test notes if everything is set up correctly.

## Usage

### Basic Usage

```python
from src.note import create_notion_note

# Create a note
create_notion_note("My Note Title", "This is the content of my note.")
```

### Validation

```python
from src.note import validate_setup

# Check if everything is configured correctly
if validate_setup():
    print("Setup is valid!")
else:
    print("Please fix the configuration issues.")
```

## Troubleshooting

### Error: "Could not find page with ID"

This usually means:
1. The page ID is incorrect
2. Your integration doesn't have access to the page
3. The page was deleted or moved

**Solution**: Follow steps 3-4 in the setup instructions above.

### Error: "Unauthorized"

This usually means:
1. The API key is incorrect
2. The API key is not set in the .env file

**Solution**: Double-check your API key and .env file configuration.

## File Structure

```
notion_bot/
├── src/
│   ├── note.py          # Main script for creating notes
│   └── bot.py           # (Additional bot functionality)
├── utils/
│   └── utils.py         # Utility functions
├── .env                 # Your API key (create this file)
└── README.md           # This file
```
