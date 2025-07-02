import asyncio
from openai import OpenAI
from dotenv import load_dotenv
import os
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_together import ChatTogether
from typing import Optional

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Environment variable configurations
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WHISPER_API_KEY = os.getenv("WHISPER_API_KEY")
WHISPER_BASE_URL = os.getenv("WHISPER_BASE_URL")
WHISPER_MODEL = os.getenv("WHISPER_MODEL")  
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL") 

# Notion Configuration
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
PARENT_PAGE_ID = os.getenv("PARENT_PAGE_ID")

# Google Calendar Configuration
CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar"]

# --- Initialize Whisper Client (e.g., DeepInfra) ---
try:
    if WHISPER_API_KEY and WHISPER_BASE_URL:
        whisper_client = OpenAI(
            api_key=WHISPER_API_KEY,
            base_url=WHISPER_BASE_URL,
        )
        logger.info(f"Whisper client initialized (Base URL: {WHISPER_BASE_URL})")
    else:
        logger.warning("Whisper API key or base URL not set")
        whisper_client = None
except Exception as e:
    logger.critical(f"Failed to initialize Whisper client: {e}")
    whisper_client = None 


# --- Initialize LLM client (Google Gemini or Together) ---
try:
    # Check which API key is available and initialize appropriate client
    if GOOGLE_API_KEY:
        llm = ChatGoogleGenerativeAI(
            google_api_key=GOOGLE_API_KEY, #type:ignore
            model=LLM_MODEL
        )
        logger.info(f"LangChain Google Generative AI client initialized (Model: {LLM_MODEL})")
    elif TOGETHER_API_KEY:
        llm = ChatTogether(
            together_api_key=TOGETHER_API_KEY,#type:ignore
            model=LLM_MODEL
        )
        logger.info(f"LangChain Together client initialized (Model: {LLM_MODEL})")
    else:
        logger.warning("Neither GOOGLE_API_KEY nor TOGETHER_API_KEY is set. Cannot initialize LLM.")
        llm = None
except Exception as e:
     logger.critical(f"Failed to initialize LLM client: {e}")
     llm = None 

async def generate_text():
    return
