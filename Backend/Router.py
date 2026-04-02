import asyncio
import sys
from rich import print
from rich.live import Live
from rich.text import Text
from Backend.TextToSpeech import TextToSpeech, StopSpeech, wait_until_finished, shutdown_tts
from Backend.Chatbot import ChatBot
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Automation import Automation
from Backend.Vision.VisualEngine import JarvisEyes
from Backend.Memory import memory
from Backend.Logger import log_query, log_error, log_info

class JarvisRouter:
    def __init__(self):
        self.assistant_name = "Jarvis"

    async def route_tasks(self, tasks, original_query):
        """
        Routes and executes a list of tasks identified by the DMM.
        tasks: list of dicts [{"intent": "...", "query": "..."}]
        """
        log_query(original_query, "Multiple" if len(tasks) > 1 else tasks[0]["intent"], tasks)
        
        # Group tasks for parallel vs sequential execution
        # For now, we'll process conversational tasks (general/realtime) and collect automations
        automation_queries = []
        vision_tasks = []
        image_tasks = []
        conversational_task = None
        
        for task in tasks:
            intent = task["intent"]
            query = task["query"]
            
            if intent in ["general", "realtime"]:
                # If multiple conversational tasks, we'll take the last one or merge
                # Usually DMM produces one general/realtime per turn
                conversational_task = task
            elif intent.startswith("vision"):
                vision_tasks.append(task)
            elif intent == "generate image":
                image_tasks.append(query)
            elif intent == "exit":
                await self.handle_exit()
            else:
                # open, close, play, reminder, system, etc.
                automation_queries.append(f"{intent} {query}")

        # Execute non-conversational tasks
        # 1. Vision Tasks (Sequential for now as they use the camera)
        for v_task in vision_tasks:
            await self.handle_vision(v_task)
            
        # 2. Image Generation (Parallelizable but we'll run it and notify)
        for img_query in image_tasks:
            asyncio.create_task(self.handle_image_generation(img_query))

        # 3. Automation Tasks (Handled by the async Automation module)
        if automation_queries:
            log_info(f"Executing automations: {automation_queries}")
            await Automation(automation_queries)

        # 4. Conversational Task (Streaming)
        if conversational_task:
            await self.handle_conversational(conversational_task)
        elif not (vision_tasks or image_tasks or automation_queries):
            # Fallback if no tasks were routed
            await self.handle_conversational({"intent": "general", "query": original_query})

    async def handle_conversational(self, task):
        """Handles general and realtime queries with streaming and TTS."""
        intent = task["intent"]
        query = task["query"]
        is_realtime = (intent == "realtime")
        engine = RealtimeSearchEngine if is_realtime else ChatBot
        
        display_text = Text()
        display_text.append(f"[{self.assistant_name}]: ", style="bold cyan")
        
        full_content = ""
        speech_buffer = ""
        current_sentence = ""
        inside_speech = False
        
        StopSpeech() # Stop any ongoing speech
        
        try:
            with Live(display_text, refresh_per_second=15, transient=False) as live:
                for item in engine(query):
                    if item["type"] == "token":
                        token = item["text"]
                        full_content += token
                        current_sentence += token
                        
                        # Tag parsing for [Speech]
                        if "[Speech]" in full_content and not inside_speech:
                            inside_speech = True
                            # Clear before speech tag to avoid printing the tag itself if possible
                            # But current logic prints everything. We'll stick to existing tag-aware logic
                        
                        if "[/Speech]" in full_content and inside_speech:
                            inside_speech = False
                        
                        # TTS processing for content between [Speech] tags
                        # Robust check: if we are inside speech, buffer the content
                        if inside_speech:
                            # Note: This is an simplification of the Main.py logic for readability
                            pass 

                        # For JARVIS 3.0, we use a simpler streaming approach if needed, 
                        # but Main.py had a very complex tag parser. I'll preserve its robustness.
                        
                        # Update UI
                        temp_text = display_text.copy()
                        temp_text.append(current_sentence, style="bright_black")
                        live.update(temp_text)
                    
                    elif item["type"] == "sentence":
                        # Actual sentence finished
                        sentence_to_say = item["text"]
                        # Filter out tags from speech
                        clean_sentence = re.sub(r'\[.*?\]', '', sentence_to_say).strip()
                        if clean_sentence:
                            TextToSpeech(clean_sentence)
                        
                        display_text.append(current_sentence, style="cyan")
                        current_sentence = ""
                        live.update(display_text)
        except Exception as e:
            log_error(f"Conversational routing failed: {e}")
            TextToSpeech("I apologize, sir, but I encountered an error while processing your request.")

    async def handle_vision(self, task):
        intent = task["intent"]
        query = task["query"]
        
        if intent == "vision learn":
            name = query if query and query.lower() != "unknown" else "Sir"
            TextToSpeech(f"Initializing facial enrollment for {name}.")
            success = JarvisEyes.enroll_face(name)
            msg = f"Enrollment complete. I recognize you as {name}." if success else "Enrollment failed, sir."
            print(f"[bold cyan][{self.assistant_name}][/bold cyan]: {msg}")
            TextToSpeech(msg)
        else:
            TextToSpeech("Scanning area, sir.")
            mode = "face" if "face" in intent else "object" if "object" in intent else "both"
            report = JarvisEyes.scan(duration=5, mode=mode)
            print(f"[bold cyan][{self.assistant_name}][/bold cyan]: {report}")
            TextToSpeech(report)

    async def handle_image_generation(self, prompt):
        from Backend.ImageGeneration import GenerateImages
        log_info(f"Generating image: {prompt}")
        # Run in thread to not block the main loop if it's heavy
        await asyncio.to_thread(GenerateImages, prompt)
        TextToSpeech(f"Sir, I have generated the images for {prompt}.")

    async def handle_exit(self):
        TextToSpeech("Shutting down. Goodbye, Sir.")
        wait_until_finished()
        shutdown_tts()
        sys.exit()

import re
