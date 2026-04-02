import sys
import os
import asyncio
import warnings

# --- WARNING AND LOG SUPPRESSION ---
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow logs
warnings.filterwarnings("ignore", category=UserWarning, module='google.protobuf.symbol_database')
# -----------------------------------

from Backend.Model import FirstLayerDMM
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Automation import Automation
from Backend.SpeechToText import SpeechRecognition
from Backend.Chatbot import ChatBot
from Backend.TextToSpeech import TextToSpeech, wait_until_finished, shutdown_tts
from dotenv import dotenv_values
from rich import print
from Backend.Vision.VisualEngine import JarvisEyes
import threading
import datetime
import pygame
import time

pygame.mixer.init()

def play_thinking_sound():
    # Silent by user request
    pass

def stop_thinking_sound():
    # Silent by user request
    pass

def get_environmental_greeting():
    hour = datetime.datetime.now().hour
    if hour < 12:
        part_of_day = "morning"
    elif hour < 18:
        part_of_day = "afternoon"
    else:
        part_of_day = "evening"
    
    return f"Good {part_of_day}, {Username}. All core systems are online. How may I be of service?"

# Load environment variables
env_vars = dotenv_values(".env")
Username = env_vars.get("USERNAME", "Sir")
UserRealName = env_vars.get("USER_REAL_NAME", "Sir")
Assistantname = env_vars.get("ASSISTANT_NAME", "Jarvis")

from rich.live import Live
from rich.text import Text

def MainExecution():
    """
    Main orchestration loop for the Jarvis program.
    Connects Ears (STT), Brain (DMM/Chatbot/Search), and Hands (Automation/System).
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"[bold cyan][System][/bold cyan] {Assistantname} is coming online...")
    
    # Warm up Vision System (Zero-Latency mode)
    print(f"[bold yellow][System][/bold yellow] Initializing Visual Sensors...")
    JarvisEyes.warm_up_camera()
    print(f"[bold yellow][System][/bold yellow] Visual Sensors Online.")

    # Welcome message (Environmentally aware)
    greeting = get_environmental_greeting()
    TextToSpeech(greeting)

    while True:
        try:
            # Step 1: Listen for user input
            print(f"\n[bold green][Listening...][/bold green]")
            query = SpeechRecognition()
            
            if not query or len(query.strip()) < 2:
                continue
                
            print(f"[bold white]User:[/bold white] {query}")
            
            # Step 2: Classify tasks via the Decision-Making Model (DMM) with context support
            try:
                import json
                with open(r"Data\ChatLog.json", "r") as f:
                    chat_history = json.load(f)
            except Exception:
                chat_history = []

            decision = FirstLayerDMM(query, chat_history)
            print(f"[bold blue][{Assistantname} Brain][/bold blue] Tasks identified: {decision}")
            
            # Variables to track if we need to provide a conversational response
            automation_tasks = []
            
            for task in decision:
                task = task.strip()
                
                if task.startswith("general") or task.startswith("realtime"):
                    # Route to conversational or realtime engine — full streaming mode
                    is_realtime = task.startswith("realtime")
                    prompt = task.replace("realtime " if is_realtime else "general ", "")
                    play_thinking_sound()

                    try:
                        from Backend.TextToSpeech import StopSpeech
                        StopSpeech()
                        
                        engine = RealtimeSearchEngine if is_realtime else ChatBot
                        
                        # High-end Streaming UI components
                        display_text = Text()
                        display_text.append(f"[{Assistantname}]: ", style="bold cyan")
                        
                        # Buffers and state for the robust tag parser
                        full_content = ""
                        last_processed_idx = 0
                        inside_speech = False
                        inside_details = False  # To handle technical details vs speech
                        speech_buffer = ""
                        current_drafting_sentence = ""
                        
                        # ---------------------------------------------------------
                        # ROBUST TAG-AWARE STREAMING LOOP
                        # ---------------------------------------------------------
                        with Live(display_text, refresh_per_second=15, transient=False) as live:
                            for item in engine(prompt):
                                if item["type"] == "token":
                                    token = item["text"]
                                    full_content += token
                                    
                                    # Identify all tag boundaries in the accumulated text
                                    # We look for [Speech], [/Speech], [Details], [/Details]
                                    while True:
                                        # Find the next tag start '['
                                        next_tag_start = full_content.find("[", last_processed_idx)
                                        
                                        # If no '[' found, all text from last_processed_idx to end is content
                                        if next_tag_start == -1:
                                            new_content = full_content[last_processed_idx:]
                                            if new_content:
                                                # Process this content based on current state
                                                current_drafting_sentence += new_content
                                                if inside_speech and not inside_details:
                                                    speech_buffer += new_content
                                                    # Feed to TTS at sentence boundaries
                                                    if any(p in new_content for p in ".!?"):
                                                        if speech_buffer.strip():
                                                            print(f"[Speech Debug] Feeding to TTS: {speech_buffer.strip()}")
                                                            TextToSpeech(speech_buffer.strip())
                                                        speech_buffer = ""
                                                
                                                # Update UI
                                                temp_text = display_text.copy()
                                                temp_text.append(current_drafting_sentence, style="bright_black")
                                                live.update(temp_text)
                                                last_processed_idx = len(full_content)
                                            break
                                        
                                        # We found a '['. Is it a full tag yet?
                                        next_tag_end = full_content.find("]", next_tag_start)
                                        if next_tag_end == -1:
                                            # Tag is incomplete (e.g., "[Spee"). 
                                            # Process any content BEFORE the '[' then wait for more tokens.
                                            pre_tag_content = full_content[last_processed_idx:next_tag_start]
                                            if pre_tag_content:
                                                current_drafting_sentence += pre_tag_content
                                                if inside_speech and not inside_details:
                                                    speech_buffer += pre_tag_content
                                                    if any(p in pre_tag_content for p in ".!?"):
                                                        if speech_buffer.strip():
                                                            print(f"[Speech Debug] Feeding to TTS: {speech_buffer.strip()}")
                                                            TextToSpeech(speech_buffer.strip())
                                                        speech_buffer = ""
                                                
                                                temp_text = display_text.copy()
                                                temp_text.append(current_drafting_sentence, style="bright_black")
                                                live.update(temp_text)
                                            
                                            last_processed_idx = next_tag_start
                                            break
                                        
                                        # We have a full tag like [Speech]
                                        tag = full_content[next_tag_start : next_tag_end + 1]
                                        
                                        # 1. Process content before the tag
                                        pre_tag_content = full_content[last_processed_idx:next_tag_start]
                                        if pre_tag_content:
                                            current_drafting_sentence += pre_tag_content
                                            if inside_speech and not inside_details:
                                                speech_buffer += pre_tag_content
                                                if any(p in pre_tag_content for p in ".!?"):
                                                    if speech_buffer.strip():
                                                        TextToSpeech(speech_buffer.strip())
                                                    speech_buffer = ""

                                        # 2. Update state based on the tag
                                        if tag == "[Speech]":
                                            inside_speech = True
                                        elif tag == "[/Speech]":
                                            if speech_buffer.strip() and inside_speech and not inside_details:
                                                print(f"[Speech Debug] Final Speech Chunk: {speech_buffer.strip()}")
                                                TextToSpeech(speech_buffer.strip())
                                            speech_buffer = ""
                                            inside_speech = False
                                        elif tag == "[Details]":
                                            inside_details = True
                                        elif tag == "[/Details]":
                                            inside_details = False
                                        
                                        # 3. Advance pointer past the tag
                                        last_processed_idx = next_tag_end + 1
                                        
                                        # Refresh UI after tag processing
                                        temp_text = display_text.copy()
                                        temp_text.append(current_drafting_sentence, style="bright_black")
                                        live.update(temp_text)

                                    time.sleep(0.04) # Natural typing delay

                                elif item["type"] == "sentence":
                                    # Generator reached sentence-ending punctuation
                                    display_text.append(current_drafting_sentence, style="cyan")
                                    current_drafting_sentence = ""
                                    stop_thinking_sound()
                    
                    except Exception as e:
                        print(f"[bold red][System Error][/bold red] Streaming failed: {e}")
                        TextToSpeech("I apologize, sir, but I encountered an error while processing your request.")
                    
                    finally:
                        stop_thinking_sound() # Ensure safety
                        # The Live display takes care of the final print.
                        # We just need a final newline for safety.
                        print("")

                elif task.startswith("vision"):
                    # Step 4: Handle Visual Intelligence Tasks
                    if task.startswith("vision learn"):
                        name = task.replace("vision learn", "").strip()
                        if not name or name.lower() == "unknown":
                            name = UserRealName
                        TextToSpeech(f"Initializing facial enrollment protocol for {name}.")
                        print(f"[bold cyan][{Assistantname}][/bold cyan]: Initializing facial enrollment protocol for {name}.")
                        
                        success = JarvisEyes.enroll_face(name)
                        if success:
                            msg = f"Enrollment complete. I will now be able to recognize you as {name}."
                        else:
                            msg = "I apologize, sir, but the face enrollment process failed. Did not capture sufficient data."
                        
                        print(f"[bold cyan][{Assistantname}][/bold cyan]: {msg}")
                        TextToSpeech(msg)
                    else:
                        TextToSpeech("Processing visual data. Scanning the area, sir.")
                        
                        if "face" in task:
                            report = JarvisEyes.scan(duration=10, mode="face")
                        elif "object" in task:
                            report = JarvisEyes.scan(duration=10, mode="object")
                        else:
                            report = JarvisEyes.scan(duration=10, mode="both")
                        
                        print(f"[bold cyan][{Assistantname}][/bold cyan]: {report}")
                        TextToSpeech(report)
                    
                elif "exit" in task.lower():
                    TextToSpeech("Shutting down core systems. Goodbye, Sir.")
                    print(f"[bold red][System] Exiting...[/bold red]")
                    wait_until_finished() # Ensure he finishes speaking before exit
                    shutdown_tts()
                    sys.exit()
                    
                elif task.startswith("generate image"):
                    # Dynamically import to avoid overhead if not used
                    from Backend.ImageGeneration import GenerateImages
                    prompt = task.replace("generate image ", "")
                    print(f"[bold yellow][System][/bold yellow] Generating image for: {prompt}")
                    GenerateImages(prompt)
                    TextToSpeech(f"Sir, I have generated the images based on your prompt: {prompt}.")
                    
                else:
                    # Collect automation/system tasks to run concurrently
                    automation_tasks.append(task)

            # Step 3: Execute all automation and system tasks in parallel
            if automation_tasks:
                print(f"[bold magenta][System][/bold magenta] Executing automations: {automation_tasks}")
                # Note: Automation() is an async function
                asyncio.run(Automation(automation_tasks))
                
        except Exception as e:
            print(f"[bold red][Error][/bold red] An unexpected error occurred: {e}")
            # Try to recover or notify the user
            continue

if __name__ == "__main__":
    try:
        MainExecution()
    except KeyboardInterrupt:
        print(f"\n[bold red][System][/bold red] Manual override detected. Powering down.")
        shutdown_tts()
        sys.exit()
