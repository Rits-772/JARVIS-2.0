import json
from groq import Groq
from rich import print
from dotenv import dotenv_values

env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GROQ_API_KEY")

client = Groq(api_key=GroqAPIKey)

# List of valid intents for validation
VALID_INTENTS = [
    "exit", "general", "realtime", "open", "close", "play", 
    "generate image", "system", "google search",
    "youtube search", "reminder", "vision face", "vision object",
    "vision general", "vision learn"
]

ChatHistory = [
    {"role": "user", "content": "how are you?"},
    {"role": "assistant", "content": '[{"intent": "general", "query": "how are you?"}]'},
    {"role": "user", "content": "open chrome and tell me about mahatma gandhi."},
    {"role": "assistant", "content": '[{"intent": "open", "query": "chrome"}, {"intent": "general", "query": "tell me about mahatma gandhi."}]'},
    {"role": "user", "content": "what is today's date and by the way remind me that i have a dancing performance on 5th aug at 11pm"},
    {"role": "assistant", "content": '[{"intent": "general", "query": "what is today\'s date"}, {"intent": "reminder", "query": "11:00pm 5th aug dancing performance"}]'},
    {"role": "user", "content": "recognize and learn my face, I am Ritvik Sharma"},
    {"role": "assistant", "content": '[{"intent": "vision learn", "query": "Ritvik Sharma"}]'},
]

preamble = """
You are a highly accurate Decision-Making Model (DMM) that converts user queries into a structured JSON array of tasks.
Each task must be an object with an "intent" and a "query".

Available Intents:
- 'general': Conversational queries or simple questions (e.g., "who was akbar?", "what is the time?").
- 'realtime': Queries requiring up-to-date info or person lookups (e.g., "who is the current PM?", "today's news").
- 'open' / 'close': Managing applications (e.g., "open facebook", "close notepad").
- 'play': Playing music (e.g., "play afsanay by ys").
- 'generate image': Creating AI images (e.g., "generate image of a lion").
- 'reminder': Setting alerts (e.g., "remind me at 9pm for meeting").
- 'vision learn': Training a new face (e.g., "learn my face, I am Ritvik").
- 'vision face' / 'vision object' / 'vision general': Visual sensor requests.
- 'exit': Saying goodbye.

Instructions:
1. Always respond with a valid JSON array of objects: [{"intent": "...", "query": "..."}].
2. Do not include any text outside the JSON array.
3. If a query has multiple tasks, create an object for each.
4. If unsure, default to 'general'.
"""

def FirstLayerDMM(prompt: str = "test", chat_history: list = []):
    """
    Classifies the user prompt into structured JSON tasks.
    Uses chat_history to resolve references (pronouns).
    """
    system_msg = {
        "role": "system", 
        "content": preamble + "\n\nCRITICAL: Use conversation history to resolve pronouns (e.g., 'his songs' -> 'charlie puth's songs')."
    }
    
    context_msgs = []
    if chat_history:
        for entry in chat_history[-6:]:
             context_msgs.append({
                 "role": entry.get("role", "user"), 
                 "content": entry.get("content", "")
             })

    messages = [system_msg] + context_msgs + ChatHistory + [{"role": "user", "content": prompt}]
    
    try:
        completion = client.chat.completions.create(
            model='llama-3.1-8b-instant', 
            messages=messages,
            max_tokens=200,
            temperature=0.1, 
            response_format={"type": "json_object"} if "llama-3-70b" in "llama-3.1-8b-instant" else None # 8b doesn't always support json_object mode, but we'll prompt for it
        )
        
        raw_response = completion.choices[0].message.content.strip()
        tasks = json.loads(raw_response)
        
        # If it's a single dict instead of a list, wrap it
        if isinstance(tasks, dict):
            if "tasks" in tasks:
                tasks = tasks["tasks"]
            else:
                tasks = [tasks]
                
        # Simple validation
        final_tasks = []
        for task in tasks:
            if "intent" in task and task["intent"] in VALID_INTENTS:
                final_tasks.append(task)
        
        return final_tasks if final_tasks else [{"intent": "general", "query": prompt}]

    except Exception as e:
        print(f"[DMM Error] {e}")
        return [{"intent": "general", "query": prompt}]
    
if __name__ == "__main__":
    while True:
        print(FirstLayerDMM(input(">>> ")))