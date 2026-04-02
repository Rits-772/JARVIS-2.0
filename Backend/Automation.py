from Backend.SystemTasks import handle_system_command
from AppOpener import close, open as appopen
from webbrowser import open as webopen
from pywhatkit import search, playonyt
from dotenv import dotenv_values
from bs4 import BeautifulSoup
from rich import print
from groq import Groq
import webbrowser
import subprocess
import requests
import keyboard
import asyncio
import os

env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GROQ_API_KEY")
Username = env_vars.get("USERNAME", "Sir")

# List of CSS classes for parsing specific elements in HTML content.
classes = ["ZCubwf", "hgKElc", "LTKOO sY7ric", "Z0LCw", "gsrt vk_bk FzvWbSb YwPhnf", "pclqee", "tw-Data-text tw-text-small tw-ta", 
           "IZ6rdc", "O5uR6d LTKOO", "vLz6yd", "webanswers-webanswers_table__webanswers-table", "dDoNo ikb4Bb gsrt", "sXLaOe", 
           "LWkfke", "VQF4g", "qv3Wpe", "kno-rdesc", "SPZz6b"]

useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36"

client = Groq(api_key=GroqAPIKey)

professional_responses = [
    "Your satisfaction is my top priority; feel free to reach out if there's anything else i cn help you with.",
    "I'm at your service for any additional questions or support you may need-don't hesitate to ask.",
]

messages = []

SystemChatBot = [{"role": "system", "content": f"Hello, I am {Username}, You're a content writer. You have to write letters, codes, aapplications, essays, notes, songs, poems etc."}]

def GoogleSearch(Topic):
    search(Topic)
    return True

def Content(Topic):
    
    def OpenNotepad(File):
        default_text_editor = 'notepad.exe'
        subprocess.Popen([default_text_editor, File])
        
    def ContentWriterAI(prompt):
        messages.append({"role": "user", "content": f"{prompt}"})
        
        completion = client.chat.completions.create(
            model = "llama-3.3-70b-versatile",
            messages=SystemChatBot + messages,
            max_tokens = 2048,
            temperature=0.7,
            top_p=1,
            stream=True,
            stop=None
        )
        
        Answer = ""
        
        for chunk in completion:
            if chunk.choices[0].delta.content:
                Answer += chunk.choices[0].delta.content
        
        Answer = Answer.strip().replace("</s>", "")
        messages.append({"role": "assistant", "content": Answer})
        
        return Answer
        
    Topic: str = Topic.replace("content ", "")
    ContentByAI = ContentWriterAI(Topic)
    
    with open(rf"Data\{Topic.lower().replace(' ', '')}.txt", "w", encoding="utf-8") as file:
        file.write( str(ContentByAI))
        file.close()
        
    OpenNotepad(rf"Data\{Topic.lower().replace(' ', '')}.txt")
    return True

def YouTubeSearch(Topic):
    Url4Search = f"https://www.youtube.com/results?search_query={Topic}"
    webbrowser.open(Url4Search)
    return True

def PlayYouTube(query):
    playonyt(query)
    return True

def OpenApp(app, sess=requests.session()):
    from urllib.parse import unquote

    known_apps = {
        "facebook": "https://www.facebook.com",
        "instagram": "https://www.instagram.com",
        "youtube": "https://www.youtube.com",
        "gmail": "https://mail.google.com",
        "whatsapp": "https://web.whatsapp.com",
        "linkedin": "https://www.linkedin.com",
        "twitter": "https://twitter.com",
        "reddit": "https://www.reddit.com"
    }

    try:
        # Try to open using AppOpener
        appopen(app, match_closest=True, output=True, throw_error=True)
        return True

    except Exception as e:
        print(f"[bold red]AppOpener failed: {e}[/bold red]")

        # Check if app is a known website
        app_lower = app.lower()
        if app_lower in known_apps:
            print(f"[green]Opening known app URL: {known_apps[app_lower]}[/green]")
            webopen(known_apps[app_lower])
            return True

        # Bing search fallback
        def search_bing(query):
            url = f"https://www.bing.com/search?q={query}"
            headers = {"User-Agent": useragent}
            try:
                response = sess.get(url, headers=headers)
                if response.status_code == 200:
                    return response.text
                else:
                    print(f"[red]Bing search failed with status: {response.status_code}[/red]")
            except Exception as e:
                print(f"[red]Bing request error: {e}[/red]")
            return None

        def extract_links(html):
            soup = BeautifulSoup(html, "html.parser")
            links = []

            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith("http") and "bing.com" not in href:
                    links.append(href)

            return links

        html = search_bing(app)
        links = extract_links(html)

        if links:
            print(f"[green]Opening extracted link: {links[0]}[/green]")
            webopen(links[0])
        else:
            print(f"[yellow]No link found. Opening Bing search page.[/yellow]")
            webopen(f"https://www.bing.com/search?q={app}")

        return True


def CloseApp(app):
    if "chrome" in app:
        pass
    else: 
        try:
            close(app, match_closest=True, output=True, throw_error=True)
            return True
        except:
            return False
        

def System(command):
    return handle_system_command(command)


async def TranslateAndExecute(commands: list[str]):
     
    funcs = []
    
    for command in commands:
        command_lower = command.lower()
        if command.startswith("open "):
            if "open it" in command:
                pass
            elif "open file" == command:
                pass
            else:
                fun = asyncio.to_thread(OpenApp, command.removeprefix("open "))
                funcs.append(fun)
            
        elif command.startswith("general "):
            pass
        
        elif command.startswith("realtime "):
            pass
        
        elif command.startswith("close "):
            fun = asyncio.to_thread(CloseApp, command.removeprefix("close "))
            funcs.append(fun)
            
        elif command.startswith("play "):
            fun = asyncio.to_thread(PlayYouTube, command.removeprefix("play "))
            funcs.append(fun)
            
        elif command.startswith("content "):
            fun = asyncio.to_thread(Content, command.removeprefix("content "))
            funcs.append(fun)
            
        elif command.startswith("google search "):
            fun = asyncio.to_thread(GoogleSearch, command.removeprefix("google search "))
            funcs.append(fun)
        
        elif command.startswith("youtube search "):
            fun = asyncio.to_thread(YouTubeSearch, command.removeprefix("youtube search "))
            funcs.append(fun)
        
        elif command.startswith("system "):
            fun = asyncio.to_thread(System, command.removeprefix("system "))
            funcs.append(fun)

        elif "vision" in command_lower:
            # Main.py handles vision, so we skip here but log it
            print(f"[Automation] Vision task detected: {command}. (Handled by Main architecture)")
            
        elif "generate image" in command_lower:
            # Main.py handles image generation, so we skip here
            print(f"[Automation] Image generation task detected: {command}. (Handled by Main architecture)")
            
        elif "reminder" in command_lower:
            # Placeholder for future reminder integration in Automation
            print(f"[Automation] Reminder task detected: {command}. (Integration pending)")
        
        else: 
            print(f"No Function Found. For {command}")
            
    if not funcs:
        return

    results = await asyncio.gather(*funcs)
    
    for result in results:
        yield result
            
async def Automation(commands: list[str]):
    
    async for result in TranslateAndExecute(commands):
        pass
    
    return True
    
if __name__ == "__main__":
    asyncio.run(Automation(["system system config", "system location"]))