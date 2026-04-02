from groq import Groq
from rich import print
from dotenv import dotenv_values

env_vars = dotenv_values(".env")

GroqAPIKey = env_vars.get("GROQ_API_KEY")

client = Groq(api_key=GroqAPIKey)

funcs = [
    "exit", "general", "realtime", "open", "close", "play", 
    "generate image", "content", "system", "google search",
    "youtube search", "reminder", "vision face", "vision object",
    "vision general", "vision learn"
]

ChatHistory = [
    {"role": "user", "content": "how are you?"},
    {"role": "assistant", "content": "general how are you?"},
    {"role": "user", "content": "do you like pizza?"},
    {"role": "assistant", "content": "general do you like pizza?"},
    {"role": "user", "content": "open chrome and tell me about mahatma gandhi."},
    {"role": "assistant", "content": "open chrome, general tell me about mahatma gandhi."},
    {"role": "user", "content": "open chrome and firefox"},
    {"role": "assistant", "content": "open chrome, open firefox"},
    {"role": "user", "content": "what is today's date and by the way remind me that i have a dancing performance on 5th aug at 11pm"},
    {"role": "assistant", "content": "general what is today's date, reminder 11:00pm 5th aug dancing performance"},
    {"role": "user", "content": "chat with me"},
    {"role": "assistant", "content": "general chat with me"},
    {"role": "user", "content": "recognize and learn my face, I am Ritvik Sharma"},
    {"role": "assistant", "content": "vision learn Ritvik Sharma"},
]

preamble = """
You are a very accurate Decision-Making Model, which decides what kind of a query is given to you.
You will decide whether a query is a 'general' query, a 'realtime' query, or is asking to perform any task or automation like 'open facebook, instagram', 'can you write a application and open it in notepad'
*** Do not answer any query, just decide what kind of query is given to you. ***
-> Respond with 'general ( query )' if a query can be answered by a llm model (conversational ai chatbot) and doesn't require any up to date information like if the query is 'who was akbar?' respond with 'general who was akbar?', if the query is 'how can i study more effectively?' respond with 'general how can i study more effectively?', if the query is 'can you help me with this math problem?' respond with 'general can you help me with this math problem?', if the query is 'Thanks, i really liked it.' respond with 'general thanks, i really liked it.' , if the query is 'what is python programming language?' respond with 'general what is python programming language?', etc. Respond with 'general (query)' if a query doesn't have a proper noun or is incomplete like if the query is 'who is he?' respond with 'general who is he?', if the query is 'what's his networth?' respond with 'general what's his networth?', if the query is 'tell me more about him.' respond with 'general tell me more about him.', and so on even if it require up-to-date information to answer. Respond with 'general (query)' if the query is asking about time, day, date, month, year, etc like if the query is 'what's the time?' respond with 'general what's the time?'.
-> Respond with 'realtime ( query )' if a query can not be answered by a llm model (because they don't have realtime data) and requires up to date information like if the query is 'who is indian prime minister' respond with 'realtime who is indian prime minister', if the query is 'tell me about facebook's recent update.' respond with 'realtime tell me about facebook's recent update.', if the query is 'tell me news about coronavirus.' respond with 'realtime tell me news about coronavirus.', etc and if the query is asking about any individual or thing like if the query is 'who is akshay kumar' respond with 'realtime who is akshay kumar', if the query is 'what is today's news?' respond with 'realtime what is today's news?', if the query is 'what is today's headline?' respond with 'realtime what is today's headline?', etc.
-> Respond with 'open (application name or website name)' if a query is asking to open any application like 'open facebook', 'open telegram', etc. but if the query is asking to open multiple applications, respond with 'open 1st application name, open 2nd application name' and so on.
-> Respond with 'close (application name)' if a query is asking to close any application like 'close notepad', 'close facebook', etc. but if the query is asking to close multiple applications or websites, respond with 'close 1st application name, close 2nd application name' and so on.
-> Respond with 'play (song name)' if a query is asking to play any song like 'play afsanay by ys', 'play let her go', etc. but if the query is asking to play multiple songs, respond with 'play 1st song name, play 2nd song name' and so on.
-> Respond with 'generate image (image prompt)' if a query is requesting to generate a image with given prompt like 'generate image of a lion', 'generate image of a cat', etc. but if the query is asking to generate multiple images, respond with 'generate image 1st image prompt, generate image 2nd image prompt' and so on.
-> Respond with 'reminder (datetime with message)' if a query is requesting to set a reminder like 'set a reminder at 9:00pm on 25th june for my business meeting.' respond with 'reminder 9:00pm 25th june business meeting'.
-> Respond with 'vision learn (name)' if a query is asking to learn, remember, or recognize a new face. Include the person's name if provided (e.g., 'Learn my face, I am Ritvik Sharma' -> 'vision learn Ritvik Sharma', 'Recognize me' -> 'vision learn Unknown').
-> Respond with 'vision face' if a query is asking to identify or scan for people/faces (e.g., 'Who is in front of the camera?', 'Scan for faces', 'Who is this?').
-> Respond with 'vision object' if a query is asking to identify or scan for objects (e.g., 'What is in front of the camera?', 'Scan for objects', 'Identify this item').
-> Respond with 'vision general' if a query is a broad request to see or describe the surroundings (e.g., 'Jarvis, what do you see?', 'Look at the room', 'Current visual status').
*** If the query is asking to perform multiple tasks like 'open facebook, telegram and close whatsapp' respond with 'open facebook, open telegram, close whatsapp' ***
*** If the user is saying goodbye or wants to end the conversation like 'bye jarvis.' respond with 'exit'.***
*** Respond with 'general (query)' if you can't decide the kind of query or if a query is asking to perform a task which is not mentioned above. ***
"""

def FirstLayerDMM(prompt : str = "test", chat_history : list = []):
    """
    Classifies the user prompt into specific tasks.
    Now accepts chat_history to resolve pronouns (it, him, her) based on context.
    """
    # System message with revised preamble
    system_msg = {"role": "system", "content": preamble + "\n\nCRITICAL: Use the provided conversation history to resolve pronouns (e.g., 'his songs' -> 'charlie puth's songs' if the previous topic was Charlie Puth)."}
    
    # Build context from actual history (list of dicts with role/content)
    context_msgs = []
    if chat_history:
        # Take last 6 messages (approx 3 turns) to provide context for pronouns
        for entry in chat_history[-6:]:
             context_msgs.append({
                 "role": entry.get("role", "user"), 
                 "content": entry.get("content", "")
             })

    messages = [system_msg] + context_msgs + ChatHistory + [{"role": "user", "content": prompt}]
    
    try:
        completion = client.chat.completions.create(
            model = 'llama-3.1-8b-instant', 
            messages = messages,
            max_tokens = 50,
            temperature = 0.1, 
        )
        
        response = completion.choices[0].message.content
        response = response.replace("\n", "").split(",")
        response = [i.strip() for i in response]
        
        # Filter valid functions
        temp = []
        for task in response:
            for func in funcs:
                if task.startswith(func):
                    temp.append(task)
                    break
                    
        # Default to general if nothing was parsed correctly
        if not temp:
            return ["general " + prompt]
            
        return temp

    except Exception as e:
        # Fallback to general chat if API fails
        return ["general " + prompt]
    
if __name__ == "__main__":
    while True:
        print(FirstLayerDMM(input(">>> ")))