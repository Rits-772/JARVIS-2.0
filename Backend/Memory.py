import json
import os
from datetime import datetime
from dotenv import dotenv_values

# Define paths
current_dir = os.getcwd()
DataDirPath = os.path.join(current_dir, "Data")
MemoryFilePath = os.path.join(DataDirPath, "Memory.json")
ChatLogFilePath = os.path.join(DataDirPath, "ChatLog.json")
os.makedirs(DataDirPath, exist_ok=True)

class JarvisMemory:
    def __init__(self, max_short_term=10):
        self.max_short_term = max_short_term
        self.short_term = self._load_short_term()
        self.long_term = self._load_long_term()
        
    def _load_short_term(self):
        """Loads the last N messages from ChatLog.json."""
        if os.path.exists(ChatLogFilePath):
            try:
                with open(ChatLogFilePath, "r") as f:
                    log = json.load(f)
                    return log[-self.max_short_term:]
            except Exception:
                return []
        return []

    def _load_long_term(self):
        """Loads user preferences and persistent facts from Memory.json."""
        if os.path.exists(MemoryFilePath):
            try:
                with open(MemoryFilePath, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {
            "user_name": "Ritvik Sharma",
            "preferences": {},
            "key_facts": []
        }

    def save_long_term(self):
        """Saves persistent memory to disk."""
        with open(MemoryFilePath, "w") as f:
            json.dump(self.long_term, f, indent=4)

    def add_chat_turn(self, role, content):
        """Adds a message to the short-term memory (RAM) and syncs to ChatLog."""
        entry = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.short_term.append(entry)
        if len(self.short_term) > self.max_short_term:
            self.short_term.pop(0)
            
        # Append to full log file
        log = []
        if os.path.exists(ChatLogFilePath):
            try:
                with open(ChatLogFilePath, "r") as f:
                    log = json.load(f)
            except:
                pass
        
        log.append(entry)
        with open(ChatLogFilePath, "w") as f:
            json.dump(log, f, indent=4)

    def update_fact(self, key, value):
        """Updates a user preference or fact in long-term memory."""
        self.long_term["preferences"][key] = value
        self.save_long_term()

    def get_context_for_brain(self):
        """Returns a string representing the context (Memory + Recent Chat)."""
        context = f"User Name: {self.long_term.get('user_name', 'Sir')}\n"
        
        if self.long_term["preferences"]:
            context += "Preferences: " + str(self.long_term["preferences"]) + "\n"
            
        chat_context = ""
        for turn in self.short_term:
            role = "User" if turn["role"] == "user" else "Assistant"
            chat_context += f"{role}: {turn['content']}\n"
            
        return context + "\nRecent Conversation:\n" + chat_context

# Global instance for easy access
memory = JarvisMemory()

if __name__ == "__main__":
    # Test
    print(memory.get_context_for_brain())
