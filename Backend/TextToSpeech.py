import pygame
import asyncio
import edge_tts
import os
import re
import threading
import queue
import time
import glob
from dotenv import dotenv_values

env_vars = dotenv_values(".env")
AssistantVoice = env_vars.get("ASSISTANT_VOICE")

pygame.mixer.init()

def _cleanup_old_files():
    """Wipes all temporary speech chunks from the Data directory on startup."""
    files = glob.glob(r"Data\speech_*.mp3")
    for f in files:
        try:
            os.remove(f)
        except:
            pass

_cleanup_old_files()

def _preprocess(text: str) -> str:
    """Convert ellipses to natural spoken pauses."""
    return text.replace("...", " . . . ")

def _split_sentences(text: str) -> list[str]:
    """
    Split text into coherent sentence groups.
    Uses punctuation as primary split and groups short sentences together
    to avoid overly choppy speech.
    """
    # Split on sentence-ending punctuation, keeping the delimiter
    raw = re.split(r'(?<=[.!?])\s+', text.strip())
    
    groups = []
    buffer = ""
    for sentence in raw:
        buffer = (buffer + " " + sentence).strip()
        # Only hand off to TTS when we have a meaningful chunk (>20 chars)
        # This avoids 50ms clips for things like "Hi." or "Okay."
        if len(buffer) >= 40:
            groups.append(buffer)
            buffer = ""
    if buffer:
        groups.append(buffer)
        
    return groups

async def _synthesize(text: str, path: str) -> None:
    """Async helper to synthesize one sentence chunk to a file."""
    text = _preprocess(text)
    communicate = edge_tts.Communicate(text, AssistantVoice, pitch='-1Hz', rate='+5%')
    await communicate.save(path)

def _play_file(path: str, stop_func) -> bool:
    """Plays a single audio file. Returns False if stop_func signals to stop."""
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            if stop_func() == False:
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
                return False
            pygame.time.Clock().tick(10)
        
        # Explicitly unload to release file handle
        pygame.mixer.music.unload()
        return True
    except Exception as e:
        print(f"[TTS Error] Playback failed: {e}")
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        except:
            pass
        return False

class TTS_Engine:
    """
    A non-blocking background TTS worker.
    Handles synthesis and playback in a separate thread.
    """
    def __init__(self):
        self.text_queue = queue.Queue()
        self.audio_queue = queue.Queue()
        self.is_running = True
        self.DONE_SENTINEL = None
        self._stop_playback = False

        # Start background threads
        self.synth_thread = threading.Thread(target=self._synthesizer_loop, daemon=True)
        self.play_thread = threading.Thread(target=self._playback_loop, daemon=True)
        
        self.synth_thread.start()
        self.play_thread.start()

    def _synthesizer_loop(self):
        """Worker thread: consumes text, synthesizes, and queues file paths."""
        while self.is_running:
            try:
                text = self.text_queue.get(timeout=1)
                if text is self.DONE_SENTINEL:
                    continue

                # Group text into sentences if it's a long string
                sentences = _split_sentences(text) if isinstance(text, str) else [text]
                session_id = int(time.time() * 1000)

                for i, sentence_text in enumerate(sentences):
                    if not self.is_running: break
                    if not sentence_text or not sentence_text.strip():
                        continue
                    
                    path = rf"Data\speech_{session_id}_{i}.mp3"
                    try:
                        # Use a local loop check to avoid scheduling on a dead event loop during exit
                        if self.is_running:
                            asyncio.run(_synthesize(sentence_text, path))
                            self.audio_queue.put(path)
                    except Exception:
                        # Silently fail during shutdown/errors
                        pass
            except queue.Empty:
                continue
            except Exception:
                pass

    def _playback_loop(self):
        """Main thread alternative: play each chunk as it becomes available."""
        while self.is_running:
            try:
                path = self.audio_queue.get(timeout=1)
                if path is self.DONE_SENTINEL:
                    continue

                if os.path.exists(path):
                    success = _play_file(path, lambda: not self._stop_playback)
                    # Safe deletion
                    try:
                        os.remove(path)
                    except:
                        pass
                    if not success:
                        self._stop_playback = False # Reset stop flag
                else:
                    pass
            except queue.Empty:
                continue
            except Exception:
                pass

    def wait(self):
        """Blocks until all queued text has been synthesized and spoken."""
        while self.is_running and (not self.text_queue.empty() or not self.audio_queue.empty() or pygame.mixer.music.get_busy()):
            time.sleep(0.1)

    def speak(self, text):
        """Non-blocking call to queue text for speech."""
        if not text or not self.is_running: return
        self._stop_playback = False
        self.text_queue.put(text)

    def stop(self):
        """Instantly stops current playback and clears the queue."""
        self._stop_playback = True
        # Clear queues
        while not self.text_queue.empty():
            try: self.text_queue.get_nowait()
            except: break
        while not self.audio_queue.empty():
            try: self.audio_queue.get_nowait()
            except: break

    def shutdown(self):
        """Clean shutdown of the engine."""
        self.is_running = False
        self.stop()

# Singleton Instance
_engine = TTS_Engine()

def TextToSpeech(Text):
    """
    Original interface maintained for compatibility.
    Now redirects to the non-blocking background engine.
    """
    _engine.speak(Text)

def StopSpeech():
    """Immediately halts any ongoing speech activity."""
    _engine.stop()

def wait_until_finished():
    """Synchronous wait for the voice engine to finish speaking."""
    _engine.wait()

def shutdown_tts():
    """Final cleanup."""
    _engine.shutdown()

if __name__ == "__main__":
    while True:
        TextToSpeech(input("Enter the Text: "))