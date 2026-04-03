import sys
import os
import asyncio
import warnings
from rich import print
import datetime
from dotenv import dotenv_values

# --- WARNING AND LOG SUPPRESSION ---
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
warnings.filterwarnings("ignore", category=UserWarning, module='google.protobuf.symbol_database')
warnings.filterwarnings("ignore", category=UserWarning, module='huggingface_hub')

from Backend.Model import FirstLayerDMM
from Backend.SpeechToText import SpeechRecognition
from Backend.TextToSpeech import TextToSpeech, shutdown_tts
from Backend.Vision.VisualEngine import JarvisEyes
from Backend.Router import JarvisRouter
from Backend.Memory import memory
from Backend.Logger import log_info, log_error

# Load environment variables
env_vars = dotenv_values(".env")
Username = env_vars.get("USERNAME", "Sir")
Assistantname = env_vars.get("ASSISTANT_NAME", "Jarvis")

def get_environmental_greeting():
    """Returns a time-aware greeting for JARVIS."""
    hour = datetime.datetime.now().hour
    if hour < 12:
        part_of_day = "morning"
    elif hour < 18:
        part_of_day = "afternoon"
    else:
        part_of_day = "evening"
    return f"Good {part_of_day}, {Username}. All core systems are online. I am listening, Sir."

async def MainExecution():
    """
    Main Orchestration Loop for JARVIS 3.0 (PC Optimized).
    - Offline Speech-to-Text (Faster-Whisper Continuous)
    - Local Vision Engine (Mediapipe + Random Forest)
    - Decision Making & Task Routing (Groq Llama 3.1)
    - 3-Layer Memory & Structured Logging
    """
    # UI Setup
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"\n[bold cyan]------------------------------------------------[/bold cyan]")
    print(f"[bold cyan]      {Assistantname.upper()} 3.0 - ADVANCED PC ASSISTANT[/bold cyan]")
    print(f"[bold cyan]------------------------------------------------[/bold cyan]\n")
    
    print(f"[bold yellow][System][/bold yellow] Initializing Visual Sensors...")
    JarvisEyes.warm_up_camera()
    log_info("Core systems initializing...")

    # Say the welcome message
    greeting = get_environmental_greeting()
    # We don't await this because the greeting should be spoken as the system comes ready
    TextToSpeech(greeting)
    
    router = JarvisRouter()

    while True:
        try:
            # Step 1: Listen using the Alt+J Hotkey (Blocking)
            query = SpeechRecognition()
            
            if not query or len(query.strip()) < 2:
                continue
                
            print(f"[bold white]\nUser:[/bold white] {query}")
            
            # Step 2: Intent Classification via Decision-Making Model (DMM)
            # Uses conversation history from the new memory system
            chat_context = memory.short_term 
            decision = FirstLayerDMM(query, chat_context)
            
            # Step 3: Route Tasks via the Async Router
            # Executes vision scans, image generation, and streaming chat in parallel/sequence as needed
            await router.route_tasks(decision, query)
            
        except KeyboardInterrupt:
            # Propagate to global handler
            raise
        except Exception as e:
            log_error(f"Global error in MainExecution: {e}")
            print(f"[bold red][System Error][/bold red]: {e}")
            continue

if __name__ == "__main__":
    try:
        asyncio.run(MainExecution())
    except KeyboardInterrupt:
        print(f"\n[bold red][System][/bold red] External override detected. JARVIS is shutting down.")
        shutdown_tts()
        sys.exit()
    except Exception as e:
        log_error(f"Startup crash: {e}")
        print(f"[bold red]CRITICAL SHUTDOWN:[/bold red] {e}")
        shutdown_tts()
        sys.exit(1)
