import os
import time
import re
import random
import httpx
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
        self.gemini_models = ["gemini-2.0-flash", "gemini-1.5-flash"]
        self.gemini_quota_exceeded = False
        
        self.groq_client = None
        self.groq_model = "llama-3.3-70b-versatile"
        
        self.openai_client = None
        self.openai_model = "gpt-4o-mini"

        # Initialize Main Assistant: Google Gemini with zero retries for instant failover
        if OPENAI_AVAILABLE and self.gemini_key and len(self.gemini_key.strip()) > 5:
            try:
                self.gemini_client = OpenAI(api_key=self.gemini_key.strip(), base_url="https://generativelanguage.googleapis.com/v1beta/openai/", max_retries=0, timeout=httpx.Timeout(12.0, connect=5.0))
                print(f"[CBT Assistant] Main Engine: Google Gemini initialized.")
            except Exception as e:
                print(f"[CBT Assistant] Could not initialize Gemini client: {e}")

        # Initialize Failover Assistant: Llama 3.3 70B (via Groq Free API) with zero retries
        if OPENAI_AVAILABLE and self.groq_key and len(self.groq_key.strip()) > 5:
            try:
                self.groq_client = OpenAI(api_key=self.groq_key.strip(), base_url="https://api.groq.com/openai/v1", max_retries=0, timeout=httpx.Timeout(12.0, connect=5.0))
                print(f"[CBT Assistant] Failover Engine: Llama 3.3 (Groq) initialized.")
            except Exception as e:
                print(f"[CBT Assistant] Could not initialize Groq Llama client: {e}")

        # Initialize Backup Assistant: OpenAI GPT-4o-mini with zero retries
        if OPENAI_AVAILABLE and self.openai_key and len(self.openai_key.strip()) > 5 and not self.openai_key.startswith("sk-proj-Z3AZwp"):
            try:
                self.openai_client = OpenAI(api_key=self.openai_key.strip(), max_retries=0, timeout=httpx.Timeout(12.0, connect=5.0))
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
        Speed-optimised: Groq (Llama 3.3) first as primary for <3s responses,
        Gemini as fast fallback. max_tokens reduced for instant generation.
        """
        # 1. Fast local topic check before any API call
        if is_unrelated_to_mental_health(user_message):
            return UNRELATED_PROJECT_REPLY

        # Check history and user message to see if user is correcting the topic or asking for exercises
        recent_text = user_message.lower() + " " + " ".join([t.get("content", "").lower() for t in (history[-8:] if history else [])])
        if any(kw in recent_text for kw in ["not academic", "isn't academic", "not school", "not studying", "it is not academic", "it's not academic"]):
            context_instruction = "IMPORTANT: The user explicitly stated their stress is NOT academic stress. Do NOT mention school, exams, or academic tasks. Ask directly about what general life situation or emotions are causing their stress, or answer their direct request with actionable stress relief."
        elif any(kw in user_message.lower() for kw in ["exercise", "exercises", "technique", "techniques", "practice", "breathing", "reduce my stress", "calm"]):
            context_instruction = "The user is specifically asking for actionable stress reduction exercises and coping techniques. Provide clear step-by-step CBT or grounding exercises directly answering their request right now."
        else:
            context_instruction = f"User's detected stress context: {current_stress_category}."

        # Short, punchy system prompt with full conversation awareness
        system_prompt = (
            "You are 'NeuroSense Assistant', a compassionate CBT AI counselor. "
            "STRICT RULE: Only answer topics related to mental health, stress, anxiety, depression, burnout, relationships, lifestyle habits, or emotional well-being. "
            f"For ANY explicitly unrelated topic (like coding syntax, math problems, recipe ingredients) reply EXACTLY: '{UNRELATED_PROJECT_REPLY}' "
            f"{context_instruction} "
            "Always remember and directly respond to the user's exact question and previous chat history. Be concise — under 85 words. Never repeat a previous question."
        )

        # Build conversation history — up to last 8 turns to retain full memory
        messages = [{"role": "system", "content": system_prompt}]
        if history and isinstance(history, list):
            for turn in history[-8:]:
                role = turn.get("role", "user")
                content = turn.get("content", "").strip()
                if role in ["user", "assistant"] and content:
                    messages.append({"role": role, "content": content})

        if not messages or messages[-1].get("content") != user_message:
            messages.append({"role": "user", "content": user_message})

        # Ensure clients are dynamically initialized if keys were added after startup
        if OPENAI_AVAILABLE and not self.gemini_client:
            gk = os.getenv("GEMINI_API_KEY", "").strip()
            if len(gk) > 5:
                try: self.gemini_client = OpenAI(api_key=gk, base_url="https://generativelanguage.googleapis.com/v1beta/openai/", max_retries=0, timeout=httpx.Timeout(12.0, connect=5.0))
                except Exception: pass
        if OPENAI_AVAILABLE and not self.groq_client:
            rk = os.getenv("GROQ_API_KEY", "").strip()
            if len(rk) > 5:
                try: self.groq_client = OpenAI(api_key=rk, base_url="https://api.groq.com/openai/v1", max_retries=0, timeout=httpx.Timeout(12.0, connect=5.0))
                except Exception: pass

        # STEP 1: Primary — Groq Llama Instant (Try 1 model with generous 12.0s timeout for Vercel cold-start resilience)
        if self.groq_client:
            try:
                response = self.groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=messages,
                    temperature=0.65,
                    max_tokens=180,
                    timeout=httpx.Timeout(12.0, connect=5.0)
                )
                reply = response.choices[0].message.content.strip()
                reply = re.sub(r'<thought>.*?</thought>', '', reply, flags=re.DOTALL | re.IGNORECASE).strip()
                reply = re.sub(r'<think>.*?</think>', '', reply, flags=re.DOTALL | re.IGNORECASE).strip()
                if reply:
                    return reply
            except Exception as e:
                print(f"[CBT Assistant] Groq attempt failed or timed out ({e}), switching to Gemini...")

        # STEP 2: Fast Failover — Google Gemini 2.0 Flash (Try 1 model with generous 12.0s timeout)
        if self.gemini_client and not self.gemini_quota_exceeded:
            try:
                response = self.gemini_client.chat.completions.create(
                    model="gemini-2.0-flash",
                    messages=messages,
                    temperature=0.65,
                    max_tokens=180,
                    timeout=httpx.Timeout(12.0, connect=5.0)
                )
                reply = response.choices[0].message.content.strip()
                reply = re.sub(r'<thought>.*?</thought>', '', reply, flags=re.DOTALL | re.IGNORECASE).strip()
                reply = re.sub(r'<think>.*?</think>', '', reply, flags=re.DOTALL | re.IGNORECASE).strip()
                if reply:
                    return reply
            except Exception as e:
                print(f"[CBT Assistant] Gemini attempt failed or timed out ({e})")
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "quota" in str(e).lower():
                    self.gemini_quota_exceeded = True

        # STEP 3: Backup — OpenAI GPT-4o-mini
        if self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model=self.openai_model,
                    messages=messages,
                    temperature=0.65,
                    max_tokens=180,
                    timeout=httpx.Timeout(12.0, connect=5.0)
                )
                reply = response.choices[0].message.content.strip()
                if reply:
                    return reply
            except Exception as e:
                print(f"[CBT Assistant] OpenAI backup failed: {e}")

        # STEP 4: Never use pre-built answers. If all AI models fail or time out, return exact error message.
        return "⚠️ AI Connection Error: Unable to reach Gemini or Llama API. Please ensure your Vercel Environment Variables (GROQ_API_KEY and GEMINI_API_KEY) are active and redeployed, or check your internet connection."

if __name__ == "__main__":
    bot = CBTEmpathyAssistant()
    print("CBT Chatbot initialized.")
