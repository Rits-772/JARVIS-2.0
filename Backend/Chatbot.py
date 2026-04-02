from groq import Groq
from json import load, dump
import datetime
import re
from dotenv import dotenv_values

env_vars = dotenv_values(".env")

Username = env_vars.get("USERNAME")
Assistantname = env_vars.get("ASSISTANT_NAME")
GroqAPIKey = env_vars.get("GROQ_API_KEY")
UserRealName = env_vars.get("USER_REAL_NAME")

client = Groq(api_key=GroqAPIKey)

messages = []

System = f"""Hello, I am {Username}. You are JARVIS, a highly advanced AI assistant.
Your persona is inspired by the classic MCU J.A.R.V.I.S. You are incredibly polite, composed, and efficient, but you possess a subtle, dry British wit.

JARVIS-SPECIFIC OUTPUT FORMAT:
You MUST structure your responses into two distinct sections using these tags:
1. [Speech] Concise, insightful, and sophisticated spoken part. ONLY include the direct answer.
2. [Details] Comprehensive data or technical context for follow-up. 

IMPORTANT Persona Rules:
- The user's name is {UserRealName}. You MUST NOT use this name in your responses unless the user specifically asks "Who am I?", "What is my name?", or similar identity-related questions.
- For all other interactions, ALWAYS address the user as "{Username}".
- Do NOT mention the current time, date, or day in your response unless the user specifically asks for it.
- Prioritize brevity. "Less is more."
"""

SystemChatBot = [
    {"role": "system", "content": System}
]

try:
    with open(r"Data\ChatLog.json", "r") as f:
        messsages = load(f)
except FileNotFoundError:
    with open(r"Data\ChatLog.json", "w") as f:
        dump([], f)
        
def RealtimeInformation():
    current_date_time = datetime.datetime.now()
    day = current_date_time.strftime("%A")
    date = current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")
    second = current_date_time.strftime("%S")
    
    data = f"Please use this real-time information if need, \n"
    data += f"Day: {day}\nDate: {date}\nMonth: {month}\nYear: {year}\n"
    data += f"Time: {hour} hours :{minute} minutes :{second} seconds.\n"
    return data

def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer

def ChatBot(Query):
    """
    Streams the LLM response, yielding complete sentences one by one as they 
    arrive. This allows TTS to start speaking immediately.
    
    Yields: str (individual sentences)
    Returns: The full answer is also saved to ChatLog.json for display.
    """
    try:
        with open(r"Data\ChatLog.json", "r") as f:
            messages = load(f)
        
        messages.append({"role": "user", "content": f"{Query}"})
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=SystemChatBot + [{"role": "system", "content": RealtimeInformation()}] + messages,
            max_tokens=1024,
            temperature=0.7,
            top_p=1,
            stream=True,
            stop=None
        )
        
        full_answer = ""
        sentence_buffer = ""
        
        # Sentence-ending punctuation pattern: punctuation followed by space or end of string
        sentence_end = re.compile(r'([.!?])(\s+|$)')
        
        for chunk in completion:
            token = chunk.choices[0].delta.content
            if not token:
                continue
            
            # Yield every token as it arrives for real-time word-by-word display
            yield {"type": "token", "text": token}
            
            full_answer += token
            sentence_buffer += token
            
            # Check if we have a complete sentence to yield for TTS
            match = sentence_end.search(sentence_buffer)
            if match:
                end_pos = match.end()
                sentence = sentence_buffer[:end_pos].strip()
                sentence_buffer = sentence_buffer[end_pos:]
                
                if sentence:
                    yield {"type": "sentence", "text": sentence}
        
        # Yield any remaining text that doesn't end with punctuation
        if sentence_buffer.strip():
            yield {"type": "sentence", "text": sentence_buffer.strip()}
        
        # Clean and save the full response
        full_answer = full_answer.replace("</s>", "")
        full_answer = AnswerModifier(full_answer)
        messages.append({"role": "assistant", "content": full_answer})
        
        with open(r"Data\ChatLog.json", "w") as f:
            dump(messages, f, indent=4)
        
        # Yield the complete answer for display
        yield {"type": "full", "text": full_answer}
    
    except Exception as e:
        print(f"Error in ChatBot: {e}")
        with open(r"Data\ChatLog.json", "w") as f:
            dump([], f, indent=4)
        yield {"type": "sentence", "text": "I encountered a brief error, sir. Please try again."}

if __name__ == "__main__":
    while True:
        user_input = input("Enter your Question: ")
        for item in ChatBot(user_input):
            if item["type"] == "full":
                print(f"\n[Full]: {item['text']}")
            else:
                print(f"[Sentence]: {item['text']}")