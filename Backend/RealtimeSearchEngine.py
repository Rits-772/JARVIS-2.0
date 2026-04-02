from googlesearch import search
from groq import Groq
from json import load, dump
import datetime
import re
from dotenv import dotenv_values


env_vars = dotenv_values(".env")

Username = env_vars.get("USERNAME")
Assistantname = env_vars.get("ASSISTANT_NAME")
GroqAPIKey = env_vars.get("GROQ_API_KEY")

client = Groq(api_key=GroqAPIKey)

System = f"""Hello, I am {Username}. You are JARVIS, a highly advanced AI assistant with real-time access to global data streams.
Your persona is inspired by the classic MCU J.A.R.V.I.S. You are incredibly polite, composed, and efficient, but you possess a subtle, dry British wit.

JARVIS-SPECIFIC OUTPUT FORMAT:
You MUST structure your responses into two distinct sections using these tags:
1. [Speech] Concise, insightful, and sophisticated spoken part. ONLY include the direct answer.
2. [Details] Comprehensive data, weather reports, or technical context for follow-up. 

IMPORTANT Persona Rule:
- Do NOT mention the current time, date, or day in your response unless the user specifically asks for it. Example: Do not say "The time is 10 PM" unless asked "What time is it?".
- Prioritize brevity. "Less is more."
- Address the user as 'Sir'.
"""

try:
    with open(r"Data\ChatLog.json", "r") as f:
        messages = load(f)
except:
    with open(r"Data\ChatLog.json", "w") as f:
        dump([], f)
        
def GoogleSearch(query):
    results = list(search(query, advanced = True, num_results=5))
    Answer = f"The search results for '{query}' are:\n[start]\n"
    
    for i in results:
        Answer += f"Title: {i.title}\nDescription: {i.description}\n\n"
        
    Answer += "[end]"
    return Answer

def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer

SystemChatBot = [
    {"role": "system", "content": System},
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello, how can i help you?"}   
]

def Information():
    data = ""
    current_date_time = datetime.datetime.now()
    day = current_date_time.strftime("%A")
    date = current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")
    second = current_date_time.strftime("%S")
    
    data = f"Use this real-time information if need, \n"
    data += f"Day: {day}\nDate: {date}\nMonth: {month}\nYear: {year}\n"
    data += f"Time: {hour} hours :{minute} minutes :{second} seconds.\n"
    return data

def RealtimeSearchEngine(prompt):
    """
    Streams the LLM response with real-time search results, yielding complete
    sentences one by one. Matches the ChatBot generator interface.

    Yields: dict with "type": "sentence" or "type": "full"
    """
    global SystemChatBot, messages

    with open(r"Data\ChatLog.json", "r") as f:
        messages = load(f)
    messages.append({"role": "user", "content": f"{prompt}"})

    SystemChatBot.append({"role": "system", "content": GoogleSearch(prompt)})

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=SystemChatBot + [{"role": "system", "content": Information()}] + messages,
        max_tokens=1024,
        temperature=0.7,
        top_p=1,
        stream=True,
        stop=None
    )

    full_answer = ""
    sentence_buffer = ""
    sentence_end = re.compile(r'([.!?])(\s+|$)')

    for chunk in completion:
        token = chunk.choices[0].delta.content
        if not token:
            continue
        
        # Yield every token as it arrives for real-time word-by-word display
        yield {"type": "token", "text": token}
        
        full_answer += token
        sentence_buffer += token

        match = sentence_end.search(sentence_buffer)
        if match:
            end_pos = match.end()
            sentence = sentence_buffer[:end_pos].strip()
            sentence_buffer = sentence_buffer[end_pos:]

            if sentence:
                yield {"type": "sentence", "text": sentence}

    # Yield remaining text
    if sentence_buffer.strip():
        yield {"type": "sentence", "text": sentence_buffer.strip()}

    full_answer = full_answer.strip().replace("</s>", "")
    messages.append({"role": "assistant", "content": full_answer})

    with open(r"Data\ChatLog.json", "w") as f:
        dump(messages, f, indent=4)

    SystemChatBot.pop()
    full_answer = AnswerModifier(full_answer)
    yield {"type": "full", "text": full_answer}


if __name__ == "__main__":
    while True:
        prompt = input("Enter your Question: ")
        for item in RealtimeSearchEngine(prompt):
            if item["type"] == "full":
                print(f"\n[Full]: {item['text']}")
            else:
                print(f"[Sentence]: {item['text']}")
