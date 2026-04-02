# JARVIS 2.0: Backend Intelligence

This directory contains the central intelligence engines that power JARVIS's ability to see, hear, and think. Each module is optimized for low-latency asynchronous execution to provide a seamless human-AI interaction loop.

---

## 👂 Ears (Speech Perception)
- **SpeechRecognition.py**: A high-performance STT (Speech-to-Text) module designed to capture and transcribe verbal queries with minimal processing delay.

## 🧠 Brain (Semantic Processing)
- **Model.py (DMM)**: The **Decision-Making Model**. This zero-shot classifier identifies the intent of every query (Automation, Vision, Search, or Chat) and resolves pronouns using the conversation history.
- **Chatbot.py**: The conversational engine powered by **Llama 3**. Features a custom tag-based output system (`[Speech]`, `[Details]`) for streaming audio and text separately.
- **RealtimeSearchEngine.py**: Connects JARVIS to the internet for queries that require up-to-date real-world information.

## 👄 Voice (Speech Synthesis)
- **TextToSpeech.py**: A professional-grade TTS engine using **Edge-TTS**. 
  - Supports non-blocking background synthesis.
  - Implements a parallel playback loop for zero-latency speech start.

## 👁️ Vision (Deep Intelligence)
- **VisualEngine.py**: Orchestrates the camera "Warm-up" and sensor activation.
- **FaceRecognition.py**: 
  - Performs facial measurement using **Mediapipe**.
  - Classifies identities using a **Random Forest** model (`face_model.pkl`).
  - Includes automated storage management for training data.
- **ObjectDetection.py**: Real-time object identification using the COCO-SSD MobileNet architecture.

---

## 🛠️ Data Management
JARVIS stores his long-term memory in the `Data/` directory. This includes:
- **FaceDB.json**: The identity registry mapping IDs to names.
- **ChatLog.json**: The conversation history buffer.
- **face_model.pkl**: The trained neural weights for his visual memory.
