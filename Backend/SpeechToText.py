import os
import wave
import pyaudio
import keyboard
import numpy as np
from faster_whisper import WhisperModel
from dotenv import dotenv_values
import mtranslate as mt
from rich import print

# Define paths
current_dir = os.getcwd()
TempDirPath = os.path.join(current_dir, "Frontend", "Files")
DataDirPath = os.path.join(current_dir, "Data")
os.makedirs(TempDirPath, exist_ok=True)
os.makedirs(DataDirPath, exist_ok=True)

# Load environment variables
env_vars = dotenv_values(".env")
InputLanguage = env_vars.get("INPUT_LANGUAGE", "en") # e.g., 'en', 'hi'

# Initialize Whisper Model (Fastest local model)
# Use 'base', 'small', or 'medium' depending on hardware. 'base' is fastest.
model_size = "base"
# Pre-downloading model if needed (automatically handles it)
model = WhisperModel(model_size, device="cpu", compute_type="int8")

def SetAssistantStatus(Status):
    """Updates the assistant's status in a file for the frontend to read."""
    with open(os.path.join(TempDirPath, 'Status.data'), "w", encoding='utf-8') as file:
        file.write(Status)

def QueryModifier(Query):
    """Adds appropriate punctuation and capitalization to the query."""
    if not Query: return ""
    new_query = Query.lower().strip()
    query_words = new_query.split()
    if not query_words: return ""
    
    question_words = ["how", "what", "who", "where", "when", "why", "which", "whose", "whom", "can you", "what's", "where's", "how's"]
    
    if any(word + " " in new_query for word in question_words):
        if new_query[-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "?"
        else:
            new_query += "?"
    else:
        if new_query[-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "."
        else:
            new_query += "."
    
    return new_query.capitalize()

def UniversalTranslator(Text):
    """Translates non-English text to English."""
    english_translation = mt.translate(Text, "en", "auto")
    return english_translation.capitalize()

def record_audio():
    """Records audio while Alt+J is held."""
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    WAVE_OUTPUT_FILENAME = os.path.join(DataDirPath, "input_audio.wav")

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    print("\n[bold yellow]Hold Alt + J to speak...[/bold yellow]")
    SetAssistantStatus("Ready")
    
    # Wait for Alt+J to be pressed
    keyboard.wait("alt+j")
    
    print("[bold green]Listening...[/bold green]")
    SetAssistantStatus("Listening...")
    
    frames = []
    
    # Record while Alt+J is held
    while keyboard.is_pressed("alt+j"):
        data = stream.read(CHUNK)
        frames.append(data)

    print("[bold cyan]Processing...[/bold cyan]")
    SetAssistantStatus("Processing...")

    stream.stop_stream()
    stream.close()
    p.terminate()

    # Save to a temporary wav file
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    return WAVE_OUTPUT_FILENAME

def SpeechRecognition():
    """Primary function for Main.py to call. Blocks until audio is captured and transcribed."""
    audio_file = record_audio()
    
    try:
        segments, info = model.transcribe(audio_file, beam_size=5, language=InputLanguage if InputLanguage else None)
        text = "".join([segment.text for segment in segments])
        
        if not text.strip():
            return ""

        if InputLanguage and (InputLanguage.lower() == "en" or "en" in InputLanguage.lower()):
            return QueryModifier(text)
        else:
            SetAssistantStatus("Translating...")
            return QueryModifier(UniversalTranslator(text))
    except Exception as e:
        print(f"[ERROR] STT Transcription failed: {e}")
        return ""

if __name__ == "__main__":
    while True:
        text = SpeechRecognition()
        if text:
            print(f"Recognized: {text}")