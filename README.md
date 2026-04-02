# JARVIS 2.0: High-End Neural Assistant

JARVIS 2.0 is a state-of-the-art AI orchestration platform designed for real-time interaction, visual intelligence, and autonomous task execution. Built with a focus on zero-latency responses and professional-grade aesthetics, this version represents a complete overhaul of the terminal intelligence experience.

---

## 🚀 Key Features

### 1. **Neural Decision Intelligence (Brain)**
- **Real-time Streaming**: Utilizes Llama 3 tokens via Groq for instantaneous conversational responses.
- **Context Awareness**: Remembers the last several turns of conversation to resolve complex pronouns (it, him, her) seamlessly.
- **DMM (Decision Making Model)**: A zero-shot classification layer that routes queries between general chat, real-time search, system automation, and visual tasks.

### 2. **Advanced Visual Sensors (Eyes)**
- **Stabilized Face Recognition**: Migrated from legacy Haar Cascades to a robust **Mediapipe + Random Forest** pipeline for superior accuracy.
- **Face Enrollment Protocol**: Easily teach JARVIS new identities via voice command ("Learn my face, I am [Name]").
- **Object Detection**: Integrated COCO-SSD for real-time item identification in his surroundings.

### 3. **Cinematic Speech System (Voice)**
- **Edge-TTS Integration**: Leverages Microsoft's high-fidelity Ryan/Emma voices for natural, human-like cadence.
- **Parallel Synthesis**: Synthesizes and plays audio in separate background threads, allowing speech to begin while the AI is still "thinking."

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.10+
- A valid Groq API Key (for the Brain)
- A HuggingFace Token (for Image Generation)

### 1. Clone & Install
```bash
git clone https://github.com/Rits-772/JARVIS-2.0.git
cd JARVIS-2.0
pip install -r Requirements.txt
```

### 2. Configuration
Create a `.env` file in the root directory and populate it with your credentials:
```env
USERNAME=Sir
USER_REAL_NAME=[Your Name]
ASSISTANT_NAME=Jarvis
GROQ_API_KEY=[Your_Key]
HUGGING_FACE_API_KEY=[Your_Key]
```

### 3. Run
```bash
python Main.py
```

---

## 📁 Directory Architecture

- `/Backend`: The core intelligence engines (STT, TTS, DMM, Vision).
- `/Data`: Stores trained facial models (`.pkl`) and identity registries (`.json`).
- `/Frontend`: File-based communication layers and UI assets.
- `Main.py`: The central orchestration loop and system state manager.

---

## 👔 Identity & Address
JARVIS is configured to address the user as **"Sir"** by default to maintain a professional, assistant-like persona. However, he maintains internal knowledge of your real identity and will only reveal it when specifically requested or during a secure visual search.
