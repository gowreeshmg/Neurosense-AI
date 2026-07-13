import os
import random

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
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        
        self.client = None
        self.provider = None
        self.model_name = None

        if OPENAI_AVAILABLE and self.groq_key and len(self.groq_key.strip()) > 5:
            try:
                # Groq is 100% FREE and uses the exact same OpenAI SDK format
                self.client = OpenAI(api_key=self.groq_key.strip(), base_url="https://api.groq.com/openai/v1")
                self.provider = "Groq (Free Llama 3.3 70B)"
                self.model_name = "llama-3.3-70b-versatile"
                print(f"[CBT Assistant] Successfully connected to 100% FREE AI: {self.provider}.")
            except Exception as e:
                print(f"[CBT Assistant] Could not initialize Groq client: {e}")

        elif OPENAI_AVAILABLE and self.gemini_key and len(self.gemini_key.strip()) > 5:
            try:
                # Google Gemini Free API (OpenAI compatible endpoint)
                self.client = OpenAI(api_key=self.gemini_key.strip(), base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
                self.provider = "Google Gemini (Free Tier)"
                self.model_name = "gemini-1.5-flash"
                print(f"[CBT Assistant] Successfully connected to 100% FREE AI: {self.provider}.")
            except Exception as e:
                print(f"[CBT Assistant] Could not initialize Gemini client: {e}")

        elif OPENAI_AVAILABLE and self.openai_key and len(self.openai_key.strip()) > 5 and not self.openai_key.startswith("sk-proj-Z3AZwp"):
            try:
                self.client = OpenAI(api_key=self.openai_key.strip())
                self.provider = "OpenAI (GPT-4o-mini)"
                self.model_name = "gpt-4o-mini"
                print(f"[CBT Assistant] Successfully connected to OpenAI ChatGPT API.")
            except Exception as e:
                print(f"[CBT Assistant] Could not initialize OpenAI client: {e}")
        else:
            print("[CBT Assistant] No active live AI API key detected (or quota limited). Operating in offline rule-based CBT mode.")

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

    def chat_reply(self, user_message, current_stress_category="Academic Stress"):
        """
        Handles interactive conversational replies on the dashboard chat tab.
        Uses live OpenAI ChatGPT (GPT-4o-mini) if API key is present, otherwise falls back to local rule-based CBT logic.
        """
        if self.client and self.model_name:
            try:
                system_prompt = (
                    "You are 'NeuroSense Assistant', a compassionate and clinical Cognitive Behavioral Therapy (CBT) AI counselor designed to support individuals facing mental health challenges such as stress, anxiety, depression, and daily pressure. "
                    f"The user's recent multimodal check-in detected: {current_stress_category}. "
                    "Provide empathetic validation, practical cognitive reframing (e.g. Socratic questioning, catching cognitive distortions like catastrophizing or all-or-nothing thinking), and physiological grounding exercises when helpful. "
                    "Keep your reply conversational, structured, warm, and concise (under 140 words). Do not give generic advice; provide actionable CBT guidance tailored to any walk of life."
                )
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.7,
                    max_tokens=250
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"[CBT Assistant] {self.provider} API error during chat_reply ({e}). Using offline fallback.")

        # Offline Fallback (Rule-based CBT logic)
        msg_lower = user_message.lower()
        
        if any(w in msg_lower for w in ["hello", "hi", "hey", "start"]):
            return "Hello! I am your NeuroSense CBT Assistant. How are you feeling right now? You can share anything about your classes, deadlines, or personal life."
            
        elif any(w in msg_lower for w in ["exam", "deadline", "study", "assignment", "gpa", "coursework", "fail"]):
            return (
                "Academic pressure can feel intense. Let's practice a quick cognitive reframing shift:\n\n"
                "When you catch your mind thinking catastrophically (*'If I don't get an A, I will fail in life'*), remind yourself: *"
                "'An exam is just a measurement of my current understanding on this specific day, not my overall capability.'*\n\n"
                "Would you like to try our 25-minute study chunking routine?"
            )
            
        elif any(w in msg_lower for w in ["lonely", "alone", "friend", "breakup", "family", "depress", "sad"]):
            return (
                "Thank you for sharing that with me. Loneliness and relationship struggles in college can make everything feel much harder.\n\n"
                "Let's ground yourself for a moment: Place both feet flat on the floor and take a slow breath in. "
                "Remember that emotional pain comes in waves—this heavy feeling is temporary and will soften over time."
            )
            
        elif any(w in msg_lower for w in ["panic", "anxious", "anxiety", "breath", "heart", "scared"]):
            return (
                "Let's slow down your heart rate right now. We are going to do **Box Breathing** together:\n\n"
                "• Inhale slowly through your nose: **1... 2... 3... 4...**\n"
                "• Hold your breath gently: **1... 2... 3... 4...**\n"
                "• Exhale smoothly through your mouth: **1... 2... 3... 4...**\n\n"
                "Repeat this twice. How does your body feel right now?"
            )
            
        elif any(w in msg_lower for w in ["thank", "thanks", "better", "calm", "good"]):
            return "You are very welcome! I am so glad that helped. Remember, I am always here whenever you need a quick mental check-in or a grounding pause."
            
        else:
            return (
                f"I hear you. Whether you are dealing with academic pressure or personal challenges, taking a mindful pause is the best first step.\n\n"
                f"Based on your recent check-ins ({current_stress_category}), would you like me to guide you through a 2-minute relaxation exercise or help you prioritize your tasks today?"
            )

if __name__ == "__main__":
    bot = CBTEmpathyAssistant()
    print("CBT Chatbot initialized.")
