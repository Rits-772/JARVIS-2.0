from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from bs4 import BeautifulSoup
from dotenv import dotenv_values
from rich import print
from urllib.request import urlopen
from groq import Groq
from Backend.TextToSpeech import TextToSpeech
from Backend.SpeechToText import SpeechRecognition
import cv2, smtplib, imaplib, email, time, webbrowser, instaloader, winshell, speedtest, os, platform, psutil, socket, keyboard, datetime, pyautogui, requests, shutil, ctypes, subprocess, pyperclip

env_vars = dotenv_values(".env")

EmailID = env_vars.get("EmailID")
EmailPassword = env_vars.get("EmailPassword")
GroqAPIKey = env_vars.get("GROQ_API_KEY")

client = Groq(api_key=GroqAPIKey)

# 1. System Prompt for Intent Recognition
system_prompt = {
    "role": "system",
    "content": (
        "You are an intent identifier for a voice assistant. "
        "Given a user's command, respond with one of the following intent names only:\n"
        "- send_email\n"
        "- read_email\n"
        "- mute\n"
        "- unmute\n"
        "- volume_up\n"
        "- volume_down\n"
        "- set_volume\n"
        "- take_screenshot\n"
        "- get_location\n"
        "- get_ip\n"
        "- get_public_ip\n"
        "- system_config\n"
        "- cpu_ram_usage\n"
        "- internet_speed\n"
        "- internet_status\n"
        "- battery_status\n"
        "- date\n"
        "- uptime\n"
        "- lock_pc\n"
        "- shutdown\n"
        "- restart\n"
        "- sleep\n"
        "- clear_clipboard\n"
        "- get_clipboard\n"
        "- uptime\n"
        "- open_notepad\n"
        "- open_calculator\n"
        "- open_cmd\n"
        "- open_explorer\n"
        "- open_task_manager\n"
        "- open_control_panel\n"
        "- open_settings\n"
        "- check_time\n"
        "- get_location\n"
        "- delete_temp_files\n"
        "- recycle_bin\n"
        "- open_instagram_profile\n"
        "- help\n"
        "- click_photo\n"
        "- open_website\n\n"
        "If the intent does not match any of the above, respond only with: unknown"
    )
}

def identify_intent_with_groq(user_command: str) -> str:
    chat = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[system_prompt, {"role": "user", "content": user_command}],
        temperature=0,
        top_p=1,
        stream=True,
        stop=None
    )
    Answer = ""
        
    for chunk in chat:
        if chunk.choices[0].delta.content:
            Answer += str(chunk.choices[0].delta.content)

    Answer = Answer.replace("</s>", "")
    return Answer.strip().lower()  # Normalize the response to lowercase and strip whitespace


def handle_system_command(command: str) -> bool:
    intent = identify_intent_with_groq(command)
    print(f"Intent identified: {intent}")

    # Volume control
    if intent == "mute" or intent == "unmute":
        keyboard.press_and_release("volume mute")
        return True
    elif intent == "volume_up":
        keyboard.press_and_release("volume up")
        return True
    elif intent == "volume_down":
        keyboard.press_and_release("volume down")
        return True
    elif intent == "set_volume":
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = interface.QueryInterface(IAudioEndpointVolume)

        # Get current volume
        current_volume = volume.GetMasterVolumeLevelScalar()
        print(f"Current volume: {current_volume*100:.0f}%")

        # Set volume (0.0 to 1.0)
        new_volume = command.split("set volume level to ")[-1].strip()
        if new_volume.endswith("%"):
            new_volume = float(new_volume[:-1]) / 100.0 
        else:
            try:
                new_volume = float(new_volume) / 100.0
            except ValueError:
                print("[red]Invalid volume level. Please specify a number or percentage.[/red]")
                return False
        volume.SetMasterVolumeLevelScalar(new_volume, None)
        print(f"Volume set to: {new_volume*100:.0f}%")
        return True

    # Screenshot
    elif intent == "take_screenshot":
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join("Data", f"screenshot_{timestamp}.png")
            pyautogui.screenshot(path)
            print(f"[green]Screenshot saved to {path}[/green]")
            TextToSpeech(f"The Screenshot has been saved, Sir.")
            return True
        except Exception as e:
            print(f"[red]Screenshot failed: {e}[/red]")
            return False

    # IP-based location
    elif intent == "get_location":
        try:
            res = requests.get("https://ipinfo.io").json()
            location = res.get("city", "") + ", " + res.get("region", "") + ", " + res.get("country", "")
            print(f"[cyan]Your approximate location is: {location}[/cyan]")
            TextToSpeech(f"Your approximate location is {location}, Sir.")
            return True
        except Exception as e:
            print(f"[red]Could not fetch location: {e}[/red]")
            return False

    # System configuration
    elif intent == "system_config":
        TextToSpeech("Here is the system configuration:")
        print(f"[bold magenta]System Configuration:[/bold magenta]")
        print(f"System: {platform.system()}")
        print(f"Node Name: {platform.node()}")
        print(f"Release: {platform.release()}")
        print(f"Version: {platform.version()}")
        print(f"Machine: {platform.machine()}")
        print(f"Processor: {platform.processor()}")
        return True

    # System usage
    elif intent == "cpu_ram_usage":
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        print(f"[bold cyan]CPU Usage:[/bold cyan] {cpu}%")
        print(f"[bold cyan]RAM Usage:[/bold cyan] {ram.percent}%")
        TextToSpeech(f"CPU usage is {cpu} percent and RAM usage is {ram.percent} percent, Sir.")
        if cpu > 80:
            print("[red]Warning: High CPU usage![/red]")
            TextToSpeech("Warning, Sir. High CPU usage detected.")
        return True

    elif intent == "ram_usage":
        ram = psutil.virtual_memory()
        print(f"[cyan]Total RAM: {ram.total / (1024 ** 3):.2f} GB")
        print(f"[cyan]Available: {ram.available / (1024 ** 3):.2f} GB")
        return True

    elif intent == "disk_usage":
        total, used, free = shutil.disk_usage("/")
        print(f"[cyan]Total: {total / (1024 ** 3):.2f} GB, Used: {used / (1024 ** 3):.2f} GB, Free: {free / (1024 ** 3):.2f} GB")
        TextToSpeech(f"Total disk space is {total / (1024 ** 3):.2f} GB, used space is {used / (1024 ** 3):.2f} GB, and free space is {free / (1024 ** 3):.2f} GB, Sir.")
        if used / total > 0.8:
            print("[red]Warning: High disk usage![/red]")
            TextToSpeech("Warning, Sir. High disk usage detected.")
        return True

    elif intent == "battery_status":
        battery = psutil.sensors_battery()
        if battery:
            plugged = "Plugged In" if battery.power_plugged else "Not Plugged In"
            print(f"[yellow]Battery: {battery.percent}% - {plugged}[/yellow]")
            TextToSpeech(f"Battery is at {battery.percent} percent and is {plugged.lower()}, Sir.")
            if battery.secsleft != psutil.POWER_TIME_UNLIMITED:
                time_left = f"{battery.secsleft // 3600}h {(battery.secsleft % 3600) // 60}m"
                print(f"[yellow]Time Left: {time_left}[/yellow]")
                TextToSpeech(f"Time left is {time_left}, Sir.")
            else:
                print("[yellow]Time Left: Unknown[/yellow]")
            return True
        else:
            print("[red]Battery information not available.[/red]")
            return False

    elif intent == "get_ip":
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            print(f"[blue]Your IP Address is: {ip}[/blue]")
            TextToSpeech(f"Your IP Address is {ip}, Sir.")
            return True
        except Exception as e:
            print(f"[red]Failed to fetch IP address: {e}[/red]")
            return False

    elif intent == "get_public_ip":
        try:
            ip = urlopen('https://api.ipify.org').read().decode('utf8')
            print(f"[blue]Your Public IP Address is: {ip}[/blue]")
            return True
        except Exception as e:
            print(f"[red]Failed to fetch public IP: {e}[/red]")
            return False

    elif intent == "internet_speed":
        try:
            st = speedtest.Speedtest()
            st.get_best_server()
            download_speed = st.download() / 1_000_000  # Convert to Mbps
            upload_speed = st.upload() / 1_000_000  # Convert to Mbps
            ping = st.results.ping
            print(f"[green]Download Speed: {download_speed:.2f} Mbps[/green]")
            print(f"[green]Upload Speed: {upload_speed:.2f} Mbps[/green]")
            print(f"[green]Ping: {ping} ms[/green]")
            return True
        except ImportError:
            print("[red]speedtest-cli module not found. Install it to check internet speed.[/red]")
            return False

    elif intent == "internet_status":
        try:
            requests.get("https://www.google.com", timeout=5)
            print("[green]Internet is connected.[/green]")
            return True
        except:
            print("[red]No internet connection.[/red]")
            return True

    elif intent == "date":
        now = datetime.datetime.now()
        print(f"[green]Current Date & Time: {now.strftime('%Y-%m-%d %H:%M:%S')}[/green]")
        return True

    elif intent == "uptime":
        uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time())
        print(f"[magenta]System Uptime: {uptime}[/magenta]")
        return True

    elif intent == "clear_clipboard" or intent == "get_clipboard":
        try:

            if intent == "clear_clipboard":
                pyperclip.copy("")
                print("[cyan]Clipboard cleared.[/cyan]")
            else:
                print(f"[cyan]Clipboard: {pyperclip.paste()}[/cyan]")
            return True
        except ImportError:
            print("[red]pyperclip module not found. Install it to access clipboard.[/red]")
            return False

    # System actions
    elif intent == "lock_pc":
        ctypes.windll.user32.LockWorkStation()
        return True
    elif intent == "shutdown":
        TextToSpeech("Are you sure you want to shutdown the system, Sir?")
        print("Speak 'yes' to confirm or 'no' to cancel: ")
        condition = SpeechRecognition().lower().strip()
        if "no" in condition or "cancel" in condition:
            print("[yellow]Shutdown cancelled.[/yellow]")
            return False
        os.system("shutdown /s /t 1")
        return True
    elif intent == "restart":
        TextToSpeech("Are you sure you want to restart the system, Sir?")
        print("Speak 'yes' to confirm or 'no' to cancel: ")
        condition = SpeechRecognition().lower().strip()
        if "no" in condition or "cancel" in condition:
            print("[yellow]Restart cancelled.[/yellow]")
            return False
        os.system("shutdown /r /t 1")
        return True
    elif intent == "sleep":
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        return True

    elif intent == "empty_recycle_bin":
        try:

            winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=True)
            print("[green]Recycle bin emptied.[/green]")
            return True
        except ImportError:
            print("[red]winshell not installed. Install to use recycle bin control.[/red]")
            return False

    elif intent == "delete_temp_files":
        temp_path = os.getenv('TEMP')
        try:
            for root, dirs, files in os.walk(temp_path):
                for file in files:
                    try:
                        os.remove(os.path.join(root, file))
                    except:
                        pass
            print("[green]Temporary files deleted.[/green]")
            return True
        except Exception as e:
            print(f"[red]Failed to delete temp files: {e}[/red]")
            return False

    elif intent == "open_notepad":
        subprocess.Popen("notepad.exe")
        return True
    elif intent == "open_calculator":
        subprocess.Popen("calc.exe")
        return True
    elif intent == "open_cmd":
        subprocess.Popen("cmd.exe")
        return True
    elif intent == "open_task_manager":
        subprocess.Popen("taskmgr")
        return True
    elif intent == "open_explorer":
        subprocess.Popen("explorer.exe")
        return True
    elif intent == "open_control_panel":
        subprocess.Popen("control.exe")
        return True
    elif intent == "open_settings":
        subprocess.Popen("ms-settings:")
        return True

    elif intent == "open_instagram_profile":
        if "my instagram profile" in command:
            username = env_vars.get("InstagramUsername", "")
            if not username:
                print("[red]Instagram username not set in .env file.[/red]")
                TextToSpeech("Sir, your Instagram username is not set.")
                return False
            url = f"https://www.instagram.com/{username}/"
            print(f"[green]Opening your Instagram profile: {url}[/green]")
            webbrowser.open(url)
            TextToSpeech(f"Opening your Instagram profile, Sir.")
            time.sleep(2)
            return True
        TextToSpeech("Please provide the username of the Instagram profile you want to open.")
        username = input("Enter Instagram username: ").strip()
        if username:
            url = f"https://www.instagram.com/{username}/"
            print(f"[green]Opening Instagram profile: {url}[/green]")
            webbrowser.open(url)
            TextToSpeech(f"Opening Instagram profile of {username}, Sir.")
            time.sleep(2)
            TextToSpeech("Sir, would you like to download the profile picture of this user?")
            condition = input("Enter 'yes' to download or 'no' to skip: ").strip().lower()
            if "yes" in condition or "sure" in condition:
                try:
                    mod = instaloader.Instaloader()
                    mod.download_profile(username, profile_pic_only=True)
                    print(f"[green]Profile picture of {username} downloaded successfully.[/green]")
                    TextToSpeech(f"Profile picture of {username} downloaded successfully, Sir.")
                except Exception as e:
                    print(f"[red]Failed to download profile picture: {e}[/red]")
                    TextToSpeech(f"Failed to download profile picture of {username}, Sir.")
            else:
                TextToSpeech("Okay, Sir.")
            return True
        else:
            print("[red]No username provided.[/red]")
            return False

    elif intent == "open_website":
        TextToSpeech("Please provide the URL of the website you want to open.")
        url = input("Enter website URL: ").strip()
        if url:
            print(f"[green]Opening website: {url}[/green]")
            webbrowser.open(url)
            TextToSpeech(f"Opening {url}, Sir.")
            return True
        else:
            print("[red]No URL provided.[/red]")
            return False
        
    elif intent == "send_email":
        TextToSpeech("Please provide the recipient's email address.")
        recipient = input("Enter recipient email: ").strip()
        if not recipient:
            print("[red]No recipient email provided.[/red]")
            return False
        TextToSpeech("Please provide the subject of the email.")
        subject = input("Enter email subject: ").strip()
        if not subject:
            print("[red]No subject provided.[/red]")
            return False
        TextToSpeech("Please provide the body of the email.")
        body = input("Enter email body: ").strip()
        if not body:
            print("[red]No body provided.[/red]")
            return False
        if not EmailID or not EmailPassword:
            print("[red]Email credentials not set in .env file.[/red]")
            TextToSpeech("Sir, email credentials are not set.")
            return False
        print(f"[green]Sending email to {recipient} with subject '{subject}'...[/green]")
        TextToSpeech(f"Sending email to {recipient} with subject {subject}, Sir.")
        try:
            server = smtplib.SMTP('smtp.office365.com', 587)
            server.starttls()
            server.login(EmailID, EmailPassword)
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(EmailID, recipient, message)
            server.quit()
            print("[green]Email sent successfully.[/green]")
            TextToSpeech("Email has been sent, Sir.")
            return True
        except Exception as e:
            print(f"[red]Failed to send email: {e}[/red]")
            return False
    
    elif intent == "read_email":
        if not EmailID or not EmailPassword:
            print("[red]Email credentials not set in .env file.[/red]")
            TextToSpeech("Sir, email credentials are not set.")
            return False
        try:
            mail = imaplib.IMAP4_SSL('outlook.office365.com')
            mail.login(EmailID, EmailPassword)
            mail.select('inbox')
            result, data = mail.search(None, 'ALL')
            email_ids = data[0].split()
            latest_email_id = email_ids[-1]
            result, data = mail.fetch(latest_email_id, '(RFC822)')
            msg = email.message_from_bytes(data[0][1])
            subject = msg['subject']
            from_ = msg['from']
            print(f"[green]Latest Email:\nFrom: {from_}\nSubject: {subject}[/green]")
            TextToSpeech(f"Latest email from {from_} with subject {subject}, Sir.")
            mail.logout()
            return True
        except Exception as e:
            print(f"[red]Failed to read email: {e}[/red]")
            return False
        
    elif intent == "help":
        help_text = (
            "Here are some things you can ask me to do:\n"
            "- Control volume: mute, unmute, volume up, volume down, set volume\n"
            "- Take screenshots\n"
            "- Check IP, internet status, speed, or location\n"
            "- Manage system: lock, shutdown, restart, sleep, uptime\n"
            "- Open apps like notepad, calculator, command prompt, settings, etc.\n"
            "- Manage clipboard or recycle bin\n"
            "- Check system stats like CPU, RAM, disk, battery\n"
            "- Send and read emails\n"
            "- Open Instagram profiles and websites\n"
        )
        print(f"[bold green]{help_text}[/bold green]")
        TextToSpeech("Here's a list of things I can help you with, Sir.")
        return True

    elif intent == "click_photo":
        from Backend.Vision.VisualEngine import JarvisEyes
        
        TextToSpeech("Please provide the name for the photo.")
        photo_name = input("Enter photo name: ").strip()
        photoPath = rf"Data/{photo_name}.jpg"
        if not photo_name:
            print("[red]No photo name provided.[/red]")
            return False

        # Prevent double-opening the camera if JarvisEyes is already using it
        if hasattr(JarvisEyes, 'cap') and JarvisEyes.cap and JarvisEyes.cap.isOpened():
             print("[System] Using existing visual stream to capture photo.")
             ret, frame = JarvisEyes.cap.read()
             if ret:
                 cv2.imwrite(photoPath, frame)
                 print(f"Photo captured via stream and saved as '{photo_name}.jpg'")
                 TextToSpeech(f"Photo captured via stream, Sir.")
                 return True
        
        print(f"[green]Clicking photo: {photo_name}[/green]")
        TextToSpeech(f"Clicking photo {photo_name}, Sir.")
        
        cam = cv2.VideoCapture(0)
        if not cam.isOpened():
            print("Error: Could not open camera.")
            return False
        
        ret, frame = cam.read()
        if ret:
            cv2.imwrite(photoPath, frame)
            print(f"Photo captured and saved as '{photo_name}.jpg'")
        else:
            print("Error: Could not capture frame.")

        cam.release()
        cv2.destroyAllWindows()
        return True

    print(f"[red]Unknown system command: {command}[/red]")
    return False

if __name__ == "__main__":
    while True:
        command = input("Enter a system command: ")
        if handle_system_command(command):
            print("[green]Command executed successfully.[/green]")
        else:
            print("[red]Command execution failed.[/red]")