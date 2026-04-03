import asyncio
import sys
import re
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
        """
        log_query(original_query, "Multiple" if len(tasks) > 1 else tasks[0]["intent"], tasks)
        
        automation_queries = []
        vision_tasks = []
        image_tasks = []
        conversational_task = None
        
        for task in tasks:
            intent = task["intent"]
            query = task["query"]
            
            if intent in ["general", "realtime"]:
                conversational_task = task
            elif intent.startswith("vision"):
                vision_tasks.append(task)
            elif intent == "generate image":
                image_tasks.append(query)
            elif intent == "exit":
                await self.handle_exit()
            else:
                automation_queries.append(f"{intent} {query}")

        # Parallelize non-conversational tasks where possible
        if vision_tasks:
            for v_task in vision_tasks:
                await self.handle_vision(v_task)
            
        if image_tasks:
            for img_query in image_tasks:
                asyncio.create_task(self.handle_image_generation(img_query))

        if automation_queries:
            # Automation() is generally safe to run alongside other tasks
            asyncio.create_task(Automation(automation_queries))

        # Conversational Task (Streaming)
        if conversational_task:
            await self.handle_conversational(conversational_task)
        elif not (vision_tasks or image_tasks or automation_queries):
            await self.handle_conversational({"intent": "general", "query": original_query})

    async def handle_conversational(self, task):
        """Streaming chat logic with state-machine [Speech] filtering."""
        intent = task["intent"]
        query = task["query"]
        is_realtime = (intent == "realtime")
        engine = RealtimeSearchEngine if is_realtime else ChatBot
        
        display_text = Text()
        display_text.append(f"[{self.assistant_name}]: ", style="bold cyan")
        
        full_content = ""
        current_draft = ""
        inside_speech = False  # State-machine flag
        
        StopSpeech()
        
        try:
            with Live(display_text, refresh_per_second=15, transient=False) as live:
                for item in engine(query):
                    if item["type"] == "token":
                        token = item["text"]
                        full_content += token
                        current_draft += token
                        
                        temp_text = display_text.copy()
                        temp_text.append(current_draft, style="bright_black")
                        live.update(temp_text)
                    
                    elif item["type"] == "sentence":
                        sentence = item["text"]
                        
                        # --- STATE MACHINE for [Speech] / [Details] tags ---
                        # Tags span multiple sentences, so we track state.
                        
                        # Check if this sentence opens or closes a speech block
                        if "[Speech]" in sentence:
                            inside_speech = True
                        
                        if inside_speech:
                            # Strip the tags themselves, speak the raw text
                            speakable = sentence
                            speakable = speakable.replace("[Speech]", "").replace("[/Speech]", "")
                            speakable = speakable.replace("[Details]", "").replace("[/Details]", "")
                            speakable = speakable.strip()
                            if speakable:
                                TextToSpeech(speakable)
                        
                        # Check if speech block ended in this sentence
                        if "[/Speech]" in sentence or "[Details]" in sentence:
                            inside_speech = False
                        
                        display_text.append(current_draft, style="cyan")
                        current_draft = ""
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
        await asyncio.to_thread(GenerateImages, prompt)
        TextToSpeech(f"Sir, I have generated the images for {prompt}.")

    async def handle_exit(self):
        TextToSpeech("Shutting down. Goodbye, Sir.")
        wait_until_finished()
        shutdown_tts()
        sys.exit()
