import re
import datetime
import os
from groq import Groq
from dotenv import dotenv_values
from Backend.Memory import memory
from googlesearch import search

# Use Tavily for higher quality LLM-optimized search if available
try:
    from tavily import TavilyClient
except ImportError:
    TavilyClient = None

env_vars = dotenv_values(".env")
Username = env_vars.get("USERNAME", "Sir")
Assistantname = env_vars.get("ASSISTANT_NAME", "Jarvis")
GroqAPIKey = env_vars.get("GROQ_API_KEY")
TavilyAPIKey = env_vars.get("TAVILY_API_KEY")

client = Groq(api_key=GroqAPIKey)
tavily = TavilyClient(api_key=TavilyAPIKey) if (TavilyClient and TavilyAPIKey) else None

System = f"""Hello, I am {Username}. You are JARVIS, a highly advanced AI assistant with real-time access to global data streams.
Your persona is inspired by the classic MCU J.A.R.V.I.S. You are incredibly polite, composed, and efficient, but you possess a subtle, dry British wit.

JARVIS-SPECIFIC OUTPUT FORMAT:
You MUST structure your responses into two distinct sections using these tags:
1. [Speech] Concise, insightful, and sophisticated spoken part. ONLY include the direct answer.
2. [Details] Comprehensive data, weather reports, or technical context for follow-up. 

IMPORTANT Persona Rule:
- Do NOT mention the current time, date, or day in your response unless specifically asked.
- Prioritize brevity. "Less is more."
- Address the user as 'Sir'.
"""

def GoogleSearch(query):
    """Fallback search using googlesearch-python."""
    try:
        results = list(search(query, advanced=True, num_results=5))
        Answer = f"The search results for '{query}' are:\n[start]\n"
        for i in results:
            Answer += f"Title: {i.title}\nDescription: {i.description}\n\n"
        Answer += "[end]"
        return Answer
    except Exception as e:
        return f"Google search failed: {e}"

def TavilySearch(query):
    """Optimized search for LLMs using Tavily."""
    if not tavily:
        return GoogleSearch(query)
    try:
        # Search for context optimized for LLMs
        results = tavily.search(query=query, search_depth="advanced", max_results=5)
        Answer = f"The search results for '{query}' are:\n[start]\n"
        for result in results.get("results", []):
            Answer += f"Title: {result.get('title')}\nContent: {result.get('content')}\nURL: {result.get('url')}\n\n"
        Answer += "[end]"
        return Answer
    except Exception as e:
        print(f"[DEBUG] Tavily search failed, falling back to Google: {e}")
        return GoogleSearch(query)

def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer

def Information():
    now = datetime.datetime.now()
    return f"Real-time Info:\nDay: {now.strftime('%A')}\nDate: {now.strftime('%d %B %Y')}\nTime: {now.strftime('%H:%M:%S')}\n"

def RealtimeSearchEngine(prompt):
    """
    Streams the LLM response with real-time search results.
    Matches the ChatBot generator interface.
    """
    # 1. Fetch real-time context
    search_context = TavilySearch(prompt)
    
    # 2. Get current memory context (Facts/Prefs)
    memory_context = memory.get_context_for_brain()
    
    # 3. Add prompt to memory and get clean history
    memory.add_chat_turn("user", prompt)
    llm_history = memory.get_llm_messages()
    
    # 4. Construct messages payload
    msgs = [
        {"role": "system", "content": System},
        {"role": "system", "content": f"Current Context:\n{memory_context}\n\nSearch Data:\n{search_context}\n\n{Information()}"}
    ] + llm_history

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=msgs,
        max_tokens=1024,
        temperature=0.7,
        top_p=1,
        stream=True
    )

    full_answer = ""
    sentence_buffer = ""
    sentence_end = re.compile(r'([.!?])(\s+|$)')

    for chunk in completion:
        token = chunk.choices[0].delta.content
        if not token:
            continue
        
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

    if sentence_buffer.strip():
        yield {"type": "sentence", "text": sentence_buffer.strip()}

    full_answer = full_answer.strip().replace("</s>", "")
    
    # 4. Save response to memory
    memory.add_chat_turn("assistant", full_answer)

    yield {"type": "full", "text": AnswerModifier(full_answer)}

if __name__ == "__main__":
    while True:
        prompt = input("Enter your Question: ")
        for item in RealtimeSearchEngine(prompt):
            if item["type"] == "full":
                print(f"\n[Response]: {item['text']}")
