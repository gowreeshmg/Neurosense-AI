# NeuroSense AI 🧠🎙️

**NeuroSense AI** is an advanced, dual-modality mental health system designed to detect and analyze psychological stress through both voice (acoustic features) and text (linguistic features). 

This project utilizes a **Serverless Split Architecture**, where the beautiful glassmorphism frontend is hosted on **Vercel** for lightning-fast global access, while the heavy PyTorch AI models are securely hosted on a **HuggingFace ZeroGPU** backend.

## 🌟 Key Features
- **Multimodal Fusion:** Analyzes both the words you speak and the *way* you speak them to calculate a highly accurate combined stress score.
- **Explainable AI (XAI):** Provides complete transparency into *why* the AI made its decision, highlighting specific words or acoustic patterns (like pitch and tone) that contributed to the stress score.
- **CBT Assistant:** A built-in Cognitive Behavioral Therapy chatbot that provides empathetic validation, personalized coping strategies, and interactive exercises based on your specific stress category.

## 📊 Stress Categories Detected
NeuroSense AI is trained to accurately categorize user distress into one of the following primary categories:
1. **Academic Stress:** Pressure from school, exams, grades, or academic performance.
2. **Career/Work Stress:** Burnout, workplace conflict, job insecurity, or overwhelming workloads.
3. **Relationship Stress:** Difficulties with romantic partners, family tension, or interpersonal conflicts.
4. **Social Anxiety:** Fear of social situations, extreme self-consciousness, or feelings of isolation.
5. **Financial Stress:** Anxiety regarding debt, bills, lack of income, or economic instability.

## 🛠️ Architecture
- **Frontend (Vercel):** Vanilla HTML, CSS (Glassmorphism UI), and JavaScript. Uses an invisible "Wake-Up Ping" to ensure the HuggingFace backend is awake.
- **Backend (HuggingFace):** Pure Gradio API running on ZeroGPU. Powered by a PyTorch Ensembled CNN(for audio) and a RoBERTa Transformer(for text).

## 🚀 How to Use
1. Allow microphone permissions when prompted.
2. Click **Start Recording** and speak for up to 10 seconds about what is currently on your mind.
3. The system will automatically transcribe your speech, extract 195 acoustic features, and send the data to the HuggingFace GPU for analysis.
4. Review your personalized clinical dashboard and chat with the CBT assistant if needed!
