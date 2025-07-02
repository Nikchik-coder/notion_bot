import os
import tempfile
import logging
import json
import datetime
import pyaudio
import wave
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Import existing modules
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import whisper_client, llm
from utils.utils import create_calendar_event_from_data, create_notion_note

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioRecordingBot:
    """
    A bot that records audio, transcribes it with Whisper, analyzes it with LLM,
    and creates events in both Notion and Google Calendar.
    """
    
    def __init__(self):
        # Audio recording parameters
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.recording = False
        
        # Initialize audio
        self.audio = pyaudio.PyAudio()
        
        # Validate clients
        if not whisper_client:
            logger.error("Whisper client not initialized. Please check your API keys.")
        if not llm:
            logger.error("LLM client not initialized. Please check your API keys.")
    
    def record_audio(self, duration: Optional[int] = None) -> str:
        """
        Record audio from microphone and save to temporary file.
        
        Args:
            duration: Recording duration in seconds. If None, record until user stops.
            
        Returns:
            Path to the recorded audio file
        """
        # Create temporary file for audio
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        temp_filename = temp_file.name
        temp_file.close()
        
        print("🎤 Starting audio recording...")
        if duration:
            print(f"   Recording for {duration} seconds...")
        else:
            print("   Press Enter to stop recording...")
        
        # Open stream
        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )
        
        frames = []
        self.recording = True
        
        try:
            if duration:
                # Fixed duration recording
                for _ in range(0, int(self.rate / self.chunk * duration)):
                    data = stream.read(self.chunk)
                    frames.append(data)
            else:
                # Manual stop recording
                import threading
                def stop_on_enter():
                    input()
                    self.recording = False
                
                thread = threading.Thread(target=stop_on_enter)
                thread.daemon = True
                thread.start()
                
                while self.recording:
                    data = stream.read(self.chunk)
                    frames.append(data)
                    
        except KeyboardInterrupt:
            print("\n🛑 Recording interrupted by user")
        finally:
            stream.stop_stream()
            stream.close()
            
        print("✅ Recording finished!")
        
        # Save audio file
        with wave.open(temp_filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(frames))
            
        logger.info(f"Audio saved to: {temp_filename}")
        return temp_filename
    
    def transcribe_audio(self, audio_file: str) -> str:
        """
        Transcribe audio file using Whisper.
        
        Args:
            audio_file: Path to audio file
            
        Returns:
            Transcribed text
        """
        if not whisper_client:
            raise Exception("Whisper client not available")
            
        logger.info("Starting audio transcription...")
        
        try:
            with open(audio_file, "rb") as file:
                transcription = whisper_client.audio.transcriptions.create(
                    model=os.getenv("WHISPER_MODEL", "whisper-1"),
                    file=file
                )
            
            transcribed_text = transcription.text
            logger.info(f"Audio transcription completed. Text length: {len(transcribed_text)} characters")
            
            return transcribed_text
            
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            raise
    
    def analyze_with_llm(self, text: str) -> Dict[str, Any]:
        """
        Analyze transcribed text with LLM to extract event information.
        
        Args:
            text: Transcribed text to analyze
            
        Returns:
            Dictionary containing event details
        """
        if not llm:
            raise Exception("LLM client not available")
            
        logger.info("Starting LLM analysis of transcribed text...")
        
        # Always use today's date
        today_date = datetime.date.today().isoformat()
        
        system_prompt = f"""
         You are an AI assistant that analyzes voice notes to extract calendar event information.
         
         From the provided text, extract the following information and return it as JSON:
         {{
             "title": "Brief, descriptive title for the event based on the content",
             "description": "Detailed description including all relevant information from the voice note",
             "date": "{today_date}",
             "start_time": "HH:MM format (extract time from voice note - this is REQUIRED)",
             "end_time": "HH:MM format (extract from voice note, if not mentioned add 1 hour to start_time)",
             "location": "Location if mentioned, otherwise empty string",
             "priority": "high/medium/low based on urgency indicators in the voice note",
             "category": "meeting/appointment/reminder/task/other",
             "attendees": ["list of email addresses if mentioned in the voice note"],
             "notes": "Any additional context or details from the voice note"
         }}
         
         CRITICAL TIME PARSING INSTRUCTIONS:
         - The DATE is ALWAYS today ({today_date}) - do not change this
         - Look for time mentions like: "at 2 PM", "3:30", "nine thirty", "half past two", "quarter to five", "7 AM", "7:00", "seven o'clock"
         - Convert ALL times to valid 24-hour format (e.g., "2 PM" = "14:00", "7 AM" = "07:00")
         - IGNORE any invalid times like "29:00", "25:00", "26:00", or any hour > 23
         - If you see malformed times like "22:00 PM" or "29:00 p.m.", interpret them logically:
           * "22:00 PM" should become "22:00" (22:00 is already evening in 24-hour format)
           * "29:00" is invalid - ignore it
         - Valid hours: 00-23, Valid minutes: 00-59
         - If NO valid time is found or all times are garbled/invalid, use these defaults:
           * start_time: "09:00" (9 AM)
           * end_time: "10:00" (10 AM)
         - Common speech patterns: "7 o'clock" = "07:00", "half past 7" = "07:30", "quarter to 8" = "07:45"
         - Create a meaningful TITLE based on what the user is talking about
         - Include all relevant details in the DESCRIPTION
         """
        
        user_prompt = f"Please analyze this voice note and extract event information:\n\n{text}"
        
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = llm.invoke(messages)
            result_text = response.content
            
            # Try to parse JSON from the response
            try:
                # Extract JSON from response (in case there's extra text)
                start_idx = result_text.find('{')
                end_idx = result_text.rfind('}') + 1
                json_str = result_text[start_idx:end_idx]
                event_data = json.loads(json_str)
            except (json.JSONDecodeError, ValueError):
                # Fallback if JSON parsing fails - always use today's date
                today_date = datetime.date.today().isoformat()
                event_data = {
                    "title": "Voice Note Event",
                    "description": text,
                    "date": today_date,
                    "start_time": "09:00",
                    "end_time": "10:00",
                    "location": "",
                    "priority": "medium",
                    "category": "other",
                    "attendees": [],
                    "notes": "Analyzed from voice note"
                }
            
            logger.info(f"LLM analysis completed for event: {event_data.get('title', 'Untitled')}")
            
            return event_data
            
        except Exception as e:
            logger.error(f"Error during LLM analysis: {e}")
            raise
    
    def create_notion_note_from_event(self, event_data: Dict[str, Any]) -> None:
        """
        Create a Notion note from event data.
        
        Args:
            event_data: Dictionary containing event information
        """
        logger.info("Creating Notion note...")
        
        title = event_data.get('title', 'Voice Note Event')
        
        # Format the content with all event details
        content_parts = [
            f"**Date:** {event_data.get('date', 'Not specified')}",
            f"**Time:** {event_data.get('start_time', 'TBD')} - {event_data.get('end_time', 'TBD')}",
            f"**Category:** {event_data.get('category', 'Other')}",
            f"**Priority:** {event_data.get('priority', 'Medium')}",
        ]
        
        if event_data.get('location'):
            content_parts.append(f"**Location:** {event_data['location']}")
            
        if event_data.get('attendees'):
            content_parts.append(f"**Attendees:** {', '.join(event_data['attendees'])}")
        
        content_parts.extend([
            "",
            "**Description:**",
            event_data.get('description', 'No description provided'),
            "",
            "**Additional Notes:**",
            event_data.get('notes', 'Created from voice note')
        ])
        
        content = "\n".join(content_parts)
        
        try:
            create_notion_note(title, content)
            logger.info("Notion note created successfully from event data")
        except Exception as e:
            logger.error(f"Error creating Notion note: {e}")
            raise
    
    def create_calendar_event_from_event(self, event_data: Dict[str, Any]) -> None:
        """
        Create a Google Calendar event from event data extracted from voice note.
        
        Args:
            event_data: Dictionary containing event information
        """
        logger.info("Creating Google Calendar event...")
        
        try:
            # Extract data from the event_data dictionary
            title = event_data.get('title', 'Voice Note Event')
            description = event_data.get('description', 'Created from voice note')
            date_str = event_data.get('date', datetime.date.today().isoformat())
            start_time = event_data.get('start_time', '09:00')
            end_time = event_data.get('end_time', '10:00')
            location = event_data.get('location', '')
            attendees = event_data.get('attendees', [])
            
            # Call the updated calendar creation function with real data
            create_calendar_event_from_data(
                title=title,
                description=description,
                date_str=date_str,
                start_time=start_time,
                end_time=end_time,
                location=location,
                attendees=attendees
            )
            logger.info("Google Calendar event created successfully from voice note data")
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}")
            raise
    
    def process_voice_note(self, duration: Optional[int] = None) -> Dict[str, Any]:
        """
        Complete workflow: record, transcribe, analyze, and create events.
        
        Args:
            duration: Recording duration in seconds. If None, manual stop.
            
        Returns:
            Dictionary containing all processed data
        """
        try:
            # Step 1: Record audio
            audio_file = self.record_audio(duration)
            
            # Step 2: Transcribe audio
            transcribed_text = self.transcribe_audio(audio_file)
            
            # Step 3: Analyze with LLM
            event_data = self.analyze_with_llm(transcribed_text)
            
            # Step 4: Create Notion note
            self.create_notion_note_from_event(event_data)
            
            # Step 5: Create Google Calendar event
            self.create_calendar_event_from_event(event_data)
            
            # Clean up temporary audio file
            try:
                os.unlink(audio_file)
                logger.info("Temporary audio file cleaned up")
            except Exception as e:
                logger.warning(f"Could not clean up audio file: {e}")
            
            logger.info("Voice note processing completed successfully")
            
            return {
                "transcription": transcribed_text,
                "event_data": event_data,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error in voice note processing: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def __del__(self):
        """Clean up audio resources."""
        if hasattr(self, 'audio'):
            self.audio.terminate()


def main():
    """Main function to run the bot."""
    print("🤖 Audio Recording Bot Started!")
    print("=" * 50)
    
    bot = AudioRecordingBot()
    
    while True:
        print("\nOptions:")
        print("1. Record voice note (press Enter to stop)")
        print("2. Record voice note (10 seconds)")
        print("3. Record voice note (30 seconds)")
        print("4. Quit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            result = bot.process_voice_note()
        elif choice == "2":
            result = bot.process_voice_note(duration=10)
        elif choice == "3":
            result = bot.process_voice_note(duration=30)
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")
            continue
        
        if result.get("status") == "success":
            print(f"\n📊 Processing Summary:")
            print(f"   Transcription: {result['transcription'][:100]}...")
            print(f"   Event Title: {result['event_data']['title']}")
        else:
            print(f"\n❌ Error: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
