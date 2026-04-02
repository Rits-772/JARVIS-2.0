import asyncio
from random import randint
from PIL import Image
import requests
from dotenv import get_key
import os
from time import sleep

# Ensure required directories exist
os.makedirs("Data", exist_ok=True)
os.makedirs("Frontend/Files", exist_ok=True)

# HuggingFace API setup (Updated to newest router endpoint)
API_URL = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"
API_KEY = get_key('.env', 'HUGGING_FACE_API_KEY')

if not API_KEY:
    raise EnvironmentError("❌ HuggingFaceAPIKey not found in .env file.")

headers = {"Authorization": f"Bearer {API_KEY}"}

# Display images
def open_images(prompt):
    folder_path = "Data"
    prompt = prompt.replace(" ", "_")
    files = [f"{prompt}{i}.jpg" for i in range(1, 5)]

    for jpg_file in files:
        image_path = os.path.join(folder_path, jpg_file)

        if os.path.exists(image_path):
            try:
                img = Image.open(image_path)
                print(f"✅ Opening Image: {image_path}")
                img.show()
                sleep(1)
            except IOError:
                print(f"⚠️ Unable to open {image_path}")
        else:
            # Silently skip missing files
            pass

# Make API request
async def query(payload):
    response = await asyncio.to_thread(requests.post, API_URL, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.content
    else:
        print(f"❌ API call failed [{response.status_code}]")
        print(f"Response: {response.text}")
        return None

# Generate images
async def generate_images(prompt: str):
    tasks = []
    for _ in range(4):
        payload = {
            "inputs": f"{prompt}, quality=4K, sharpness=maximum, Ultra High details, high resolution, ultra sharp focus, masterpiece, seed={randint(0, 1000000)}"

        }
        tasks.append(asyncio.create_task(query(payload)))

    image_bytes_list = await asyncio.gather(*tasks)

    for i, image_bytes in enumerate(image_bytes_list):
        if image_bytes:
            image_path = f"Data/{prompt.replace(' ', '_')}{i+1}.jpg"
            with open(image_path, "wb") as f:
                f.write(image_bytes)
            print(f"✅ Saved image {i+1} -> {image_path}")
        else:
            print(f"⚠️ Skipping image {i+1} due to failed response")

# Entrypoint wrapper
def GenerateImages(prompt: str):
    asyncio.run(generate_images(prompt))
    open_images(prompt)

if __name__ == "__main__":
    # Standalone mode: monitoring file for legacy integrations
    while True:
        try:
            with open("Frontend/Files/ImageGeneration.data", "r") as f:
                data = f.read().strip()

            if not data or "," not in data:
                sleep(1)
                continue

            prompt, status = data.split(",")

            if status.strip().lower() == "true":
                print(f"🖼 Generating Images for Prompt: '{prompt}'...")
                GenerateImages(prompt=prompt)

                with open("Frontend/Files/ImageGeneration.data", "w") as f:
                    f.write("False,False")
                break
            else:
                sleep(1)

        except Exception as e:
            # Only print if the file exists but has an error.
            # Avoid printing if the file is missing in standalone mode.
            if os.path.exists("Frontend/Files/ImageGeneration.data"):
                print(f"❗ Error in standalone monitor: {e}")
            sleep(1)
