import os
import time
import re
import random
from src.assistant.guardrails import is_unrelated_to_mental_health, UNRELATED_PROJECT_REPLY

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class CBTEmpathyAssistant:
    """
    Cognitive Behavioral Therapy (CBT) Empathy & Intervention Assistant.
    Provides targeted cognitive reframing, grounding exercises, and actionable coping mechanisms
    tailored specifically to the stress category detected by the multimodal fusion engine.
    Supports 100% FREE live AI via Groq (Llama 3.3 70B Free) or Google Gemini Free Tier, as well as OpenAI.
    """
    def __init__(self):
        try:
            from dotenv import load_dotenv
            load_dotenv(override=True)
        except Exception:
            pass
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        
        self.gemini_client = None
        self.gemini_models = ["gemini-flash-latest"]
        self.gemini_quota_exceeded = False
        
        self.groq_client = None
        self.groq_model = "llama-3.3-70b-versatile"
        
        self.openai_client = None
        self.openai_model = "gpt-4o-mini"

        # Initialize Main Assistant: Google Gemini
        if OPENAI_AVAILABLE and self.gemini_key and len(self.gemini_key.strip()) > 5:
            try:
                self.gemini_client = OpenAI(api_key=self.gemini_key.strip(), base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
                print(f"[CBT Assistant] Main Engine: Google Gemini initialized.")
            except Exception as e:
                print(f"[CBT Assistant] Could not initialize Gemini client: {e}")

        # Initialize Failover Assistant: Llama 3.3 70B (via Groq Free API)
        if OPENAI_AVAILABLE and self.groq_key and len(self.groq_key.strip()) > 5:
            try:
                self.groq_client = OpenAI(api_key=self.groq_key.strip(), base_url="https://api.groq.com/openai/v1")
                print(f"[CBT Assistant] Failover Engine: Llama 3.3 (Groq) initialized.")
            except Exception as e:
                print(f"[CBT Assistant] Could not initialize Groq Llama client: {e}")

        # Initialize Backup Assistant: OpenAI GPT-4o-mini
        if OPENAI_AVAILABLE and self.openai_key and len(self.openai_key.strip()) > 5 and not self.openai_key.startswith("sk-proj-Z3AZwp"):
            try:
                self.openai_client = OpenAI(api_key=self.openai_key.strip())
                print(f"[CBT Assistant] Backup Engine: OpenAI initialized.")
            except Exception as e:
                print(f"[CBT Assistant] Could not initialize OpenAI client: {e}")

        self.grounding_exercises = {
            "5-4-3-2-1 Grounding": (
                "Let's ground your nervous system right now using the 5-4-3-2-1 sensory technique:\n"
                "• Look around and name 5 things you can see around you.\n"
                "• Notice 4 things you can physically feel (e.g., your feet on the floor, the chair underneath you).\n"
                "• Listen for 3 sounds around you (even distant or quiet ones).\n"
                "• Identify 2 things you can smell or like to smell.\n"
                "• Name 1 good thing about yourself or 1 thing you can taste."
            ),
            "Box Breathing (4-4-4-4)": (
                "Let's perform a physiological reset with Box Breathing:\n"
                "1. Inhale slowly through your nose for 4 seconds.\n"
                "2. Hold your breath gently for 4 seconds.\n"
                "3. Exhale smoothly through your mouth for 4 seconds.\n"
                "4. Hold empty for 4 seconds before inhaling again.\n"
                "Repeat this cycle 3 times to lower your heart rate."
            ),
            "Progressive Muscle Relaxation (PMR)": (
                "Your voice analysis showed elevated physical throat and vocal tension. Let's release that:\n"
                "• Take a deep breath and gently squeeze the muscles in your shoulders up towards your ears for 5 seconds.\n"
                "• Exhale quickly and let your shoulders drop completely, feeling the heaviness and relaxation.\n"
                "• Next, gently unclench your jaw and let your tongue rest loosely at the bottom of your mouth."
            )
        }

    def generate_intervention(self, fusion_result):
        """
        Generates a comprehensive CBT support response based on the fusion risk assessment.
        """
        cat = fusion_result.get("final_stress_category", "Calm / Normal")
        score = fusion_result.get("combined_stress_score", 0.0)
        tier = fusion_result.get("risk_tier", "Minimal / Normal")
        
        if tier == "Minimal / Normal":
            return {
                "greeting": "Hello! I am NeuroSense Assistant, your mental health companion.",
                "empathetic_validation": "It looks like your current emotional state and vocal tone are balanced and peaceful.",
                "recommended_exercise": "Preventive Mindfulness",
                "exercise_details": "To maintain this positive balance, take a 5-minute mindful walk without any screens today or write down three things you feel grateful for.",
                "coping_strategy": "Continue keeping up your healthy daily routine and supportive social connections."
            }
            
        elif cat == "Academic Stress" or cat == "Work Performance Stress":
            return {
                "greeting": "I hear how much pressure you are under right now regarding your tasks and responsibilities.",
                "empathetic_validation": f"Feeling overwhelmed by upcoming deadlines, work/study expectations, or performance anxiety ({score}% stress intensity) is a very common human experience. Remember that one project, exam, or tough day does not define your overall capability or self-worth.",
                "recommended_exercise": "The Pomodoro Task Chunking Technique",
                "exercise_details": (
                    "When tasks or projects feel paralyzing, break them into micro-steps:\n"
                    "1. Pick just ONE specific task or assignment right now.\n"
                    "2. Set a timer for just 25 minutes of focused work.\n"
                    "3. When the timer goes off, take a mandatory 5-minute break to stretch and drink water.\n"
                    "Do not worry about finishing everything today—just focus on completing one 25-minute block."
                ),
                "coping_strategy": "Cognitive Reframing: Instead of saying 'I have to finish everything right now or I will fail,' reframe it to: 'I will take my workload one hour at a time and do my personal best.'"
            }
            
        elif cat == "Non-Academic Stress" or cat == "Personal & Relationship Stress":
            return {
                "greeting": "I am right here with you, and I am listening.",
                "empathetic_validation": f"Dealing with personal life challenges, relationship struggles, family issues, or loneliness ({score}% stress intensity) takes a heavy emotional toll. It is completely okay to feel anxious, sad, or overwhelmed right now—your feelings are valid.",
                "recommended_exercise": "5-4-3-2-1 Sensory Grounding",
                "exercise_details": self.grounding_exercises["5-4-3-2-1 Grounding"],
                "coping_strategy": "Interpersonal Connection: Reach out to a trusted friend, family member, or mental health professional today. You do not have to carry this emotional weight entirely by yourself."
            }
            
        else: # Mixed Stress or Severe Risk
            return {
                "greeting": "Take a slow, deep breath with me. You are not alone in this.",
                "empathetic_validation": f"You are carrying a lot on your shoulders right now—balancing daily work and responsibilities while simultaneously navigating personal, financial, or emotional stress ({score}% stress intensity) is deeply exhausting.",
                "recommended_exercise": "Box Breathing + Progressive Muscle Relaxation",
                "exercise_details": self.grounding_exercises["Box Breathing (4-4-4-4)"] + "\n\n" + self.grounding_exercises["Progressive Muscle Relaxation (PMR)"],
                "coping_strategy": "Socratic De-escalation: When everything hits at once, pause and ask yourself: 'What is the single most urgent step I can take right now in the next 10 minutes?' Let go of the rest until tomorrow."
            }

    def chat_reply(self, user_message, current_stress_category="Academic Stress", history=None):
        """
        Handles interactive conversational replies on the dashboard chat tab.
        Uses live Google Gemini as MAIN assistant, automatically switching to Llama 3.3 (Groq) if Gemini takes >12s or hits quota.
        ZERO pre-built answers are used. Enforces strict topic filtering.
        """
        # 1. Fast local topic verification check before calling any AI API
        if is_unrelated_to_mental_health(user_message):
            return UNRELATED_PROJECT_REPLY

        system_prompt = (
            "You are 'NeuroSense Assistant', a compassionate and clinical Cognitive Behavioral Therapy (CBT) AI counselor designed to support individuals facing mental health challenges such as stress, anxiety, depression, burnout, heartbreak, and daily pressure. "
            "CRITICAL GUARDRAIL: You are STRICTLY RESTRICTED to answering questions related to our mental health project, such as stress, anxiety, depression, burnout, emotional well-being, love/relationship issues, heartbreak, academic/work pressure, and coping strategies. "
            f"If the user asks ANY question or topic that is NOT related to mental health, stress, relationship issues, love failure, or emotional well-being (for example: coding/programming questions, general knowledge, math homework, recipes, sports, entertainment, politics, financial advice, etc.), you MUST decline to answer and reply EXACTLY with: '{UNRELATED_PROJECT_REPLY}' "
            f"The user's recent check-in detected: {current_stress_category}. "
            "Provide empathetic validation, practical cognitive reframing (e.g. Socratic questioning, catching cognitive distortions like catastrophizing or all-or-nothing thinking), and physiological grounding exercises when helpful. "
            "Keep your reply conversational, structured, warm, and concise (under 140 words). Do not give generic or pre-built advice; provide customized CBT guidance tailored directly to whatever specific stressor or topic the user asks about."
        )

        # Build full conversation history messages array
        messages = [{"role": "system", "content": system_prompt}]
        if history and isinstance(history, list):
            for turn in history[-10:]: # Keep last 10 turns for context without overflow
                role = turn.get("role", "user")
                content = turn.get("content", "").strip()
                if role in ["user", "assistant"] and content:
                    messages.append({"role": role, "content": content})
        
        if not messages or messages[-1].get("content") != user_message:
            messages.append({"role": "user", "content": user_message})

        # STEP 1: Try Main Assistant — Google Gemini (Timeout 3.5 seconds)
        # If Gemini already exceeded its daily free tier quota, skip directly to Llama 3.3 for zero latency!
        if self.gemini_client and not self.gemini_quota_exceeded:
            for model_id in self.gemini_models:
                try:
                    response = self.gemini_client.chat.completions.create(
                        model=model_id,
                        messages=messages,
                        temperature=0.7,
                        max_tokens=650,
                        timeout=3.5
                    )
                    reply = response.choices[0].message.content.strip()
                    reply = re.sub(r'<thought>.*?</thought>', '', reply, flags=re.DOTALL | re.IGNORECASE).strip()
                    reply = re.sub(r'<think>.*?</think>', '', reply, flags=re.DOTALL | re.IGNORECASE).strip()
                    if reply.startswith('<thought>'):
                        reply = re.sub(r'<thought>.*', '', reply, flags=re.DOTALL | re.IGNORECASE).strip()
                    if reply:
                        return reply
                except Exception as e:
                    print(f"[CBT Assistant] Gemini ({model_id}) timed out (>3.5s) or hit quota limit: {e}")
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "quota" in str(e).lower() or "404" in str(e):
                        self.gemini_quota_exceeded = True
                        print("[CBT Assistant] Gemini free tier quota exceeded. Switching permanently to Llama 3.3 (Groq) for instant 0-delay replies!")
                    break
            if not self.gemini_quota_exceeded:
                print("[CBT Assistant] Gemini main assistant slow (>3.5s). Switching instantly to Llama 3.3 (Groq)...")

        # STEP 2: Automatic Failover — Llama 3.3 70B via Groq Free API (Timeout 8.0 seconds)
        if self.groq_client:
            try:
                response = self.groq_client.chat.completions.create(
                    model=self.groq_model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=650,
                    timeout=8.0
                )
                reply = response.choices[0].message.content.strip()
                reply = re.sub(r'<thought>.*?</thought>', '', reply, flags=re.DOTALL | re.IGNORECASE).strip()
                reply = re.sub(r'<think>.*?</think>', '', reply, flags=re.DOTALL | re.IGNORECASE).strip()
                if reply:
                    return reply
            except Exception as e:
                print(f"[CBT Assistant] Llama 3.3 (Groq) failover attempted and failed: {e}")

        # STEP 3: Backup Assistant — OpenAI GPT-4o-mini (if configured)
        if self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model=self.openai_model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=650,
                    timeout=12.0
                )
                reply = response.choices[0].message.content.strip()
                if reply:
                    return reply
            except Exception as e:
                print(f"[CBT Assistant] OpenAI backup failed: {e}")

        # STEP 4: ZERO PRE-BUILT ANSWERS ALLOWED!
        # If all live AI APIs failed or quota hit and no Groq key is added yet:
        return (
            "[AI Engine Notice] Google Gemini reached its momentary rate limit (15 requests/min) or timed out (>12s), "
            "and no Llama fallback (`GROQ_API_KEY`) was connected to handle the failover instantly. "
            "Please wait 10 seconds and send your message again, or add a free Groq API key in your `.env` file (`GROQ_API_KEY=gsk_...`) "
            "from https://console.groq.com/keys to enable seamless Llama 3.3 failover without delays!"
        )

if __name__ == "__main__":
    bot = CBTEmpathyAssistant()
    print("CBT Chatbot initialized.")
