# NeuroSense AI — Deep Clinical Evaluation & Multimodal Stress Assessment via Google Gemini
import os
import json
import re
from pathlib import Path
from src.assistant.guardrails import is_unrelated_to_mental_health, UNRELATED_PROJECT_REPLY

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class GeminiClinicalEvaluator:
    """
    Multimodal Clinical Stress Evaluator powered by Google Gemini (Free Tier) / Groq / OpenAI.
    Provides deep psychological assessment, biomarker interpretation, and CBT risk evaluation
    for both Voice/Speech transcripts and Narrative text inputs.
    """
    def __init__(self):
        self.provider = "Offline Rule-based Evaluator"
        self.model_name = "local-clinical-engine"
        self.client = None
        
        # Check environment variables
        self.gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.groq_key = os.getenv("GROQ_API_KEY", "").strip()
        self.openai_key = os.getenv("OPENAI_API_KEY", "").strip()
        
        if OPENAI_AVAILABLE and self.groq_key and len(self.groq_key) > 5:
            try:
                self.client = OpenAI(api_key=self.groq_key, base_url="https://api.groq.com/openai/v1")
                self.provider = "Groq (Llama 3.3 70B)"
                self.model_name = "llama-3.3-70b-versatile"
                print(f"[Gemini Evaluator] Connected to {self.provider}.")
            except Exception as e:
                print(f"[Gemini Evaluator] Could not initialize Groq client: {e}")
        elif OPENAI_AVAILABLE and self.gemini_key and len(self.gemini_key) > 5:
            try:
                self.client = OpenAI(api_key=self.gemini_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
                self.provider = "Google Gemini (Free Tier)"
                self.model_name = "gemini-flash-latest"
                print(f"[Gemini Evaluator] Connected to 100% FREE AI: {self.provider}.")
            except Exception as e:
                print(f"[Gemini Evaluator] Could not initialize Gemini client: {e}")
        elif OPENAI_AVAILABLE and self.openai_key and len(self.openai_key) > 5:
            try:
                self.client = OpenAI(api_key=self.openai_key)
                self.provider = "OpenAI ChatGPT"
                self.model_name = "gpt-4o-mini"
                print(f"[Gemini Evaluator] Connected to {self.provider}.")
            except Exception as e:
                print(f"[Gemini Evaluator] Could not initialize OpenAI client: {e}")

    def evaluate_clinical_stress(self, text: str, modality: str = "Text Narrative", acoustic_features: dict = None) -> dict:
        """
        Analyzes a person's stress, depression, anxiety, and coping risk using Google Gemini AI.
        Works for both transcribed voice recordings and written text narratives.
        Enforces strict guardrails to only evaluate inputs related to mental health and emotional well-being.
        """
        if not text or len(text.strip()) < 3:
            return self._get_fallback_evaluation("Patient provided minimal or silent input.", modality, 20, "Low / Baseline Calm")

        # 1. Check if the query is clearly unrelated to mental health / stress / daily life
        if is_unrelated_to_mental_health(text):
            return {
                "ai_provider": f"{self.provider} (Guardrail Filter)",
                "stress_level_index": 0,
                "clinical_risk_tier": "Not Related to Project",
                "detected_symptoms": ["Unrelated Query / Topic"],
                "empathetic_clinical_summary": UNRELATED_PROJECT_REPLY,
                "recommended_intervention": "Please submit a text check-in or question directly related to your mental health, emotional state, or daily stress."
            }

        if self.client and self.model_name:
            models_to_try = [self.model_name]
            if "gemini" in self.model_name.lower():
                models_to_try = ["gemini-flash-latest", "gemini-1.5-flash-latest", "gemma-4-31b-it"]

            prompt = (
                f"You are an expert dual-modality clinical psychologist and Cognitive Behavioral Therapy (CBT) diagnostician. "
                f"Analyze the following patient input from a {modality} check-in:\n\n"
                f"PATIENT INPUT: \"{text}\"\n\n"
                f"CRITICAL GUARDRAIL: If the patient input is completely unrelated to mental health, stress, anxiety, depression, relationships, daily pressure, or emotional well-being (e.g. coding questions, general trivia, math homework, recipes, etc.), return exactly:\n"
                f"{{\n"
                f"  \"stress_level_index\": 0,\n"
                f"  \"clinical_risk_tier\": \"Not Related to Project\",\n"
                f"  \"detected_symptoms\": [\"Unrelated Query / Topic\"],\n"
                f"  \"empathetic_clinical_summary\": \"{UNRELATED_PROJECT_REPLY}\",\n"
                f"  \"recommended_intervention\": \"Please submit a text check-in or question directly related to your mental health, emotional state, or daily stress.\"\n"
                f"}}\n\n"
                f"Otherwise, evaluate the emotional state, stress severity (0-100), presence of anxiety/depression or burnout indicators, and provide actionable psychological recommendations.\n"
                f"Respond ONLY with a valid JSON object containing exactly these keys:\n"
                f"- \"stress_level_index\": (integer between 0 and 100 representing psychological strain)\n"
                f"- \"clinical_risk_tier\": (string, one of: \"Low / Baseline Calm\", \"Mild Stress & Fatigue\", \"Moderate Anxiety & Burnout Risk\", \"Severe Emotional Distress / High Risk\")\n"
                f"- \"detected_symptoms\": (array of 3 to 5 specific psychological/symptomatic strings detected or inferred, e.g. [\"Sleep Deprivation\", \"Catastrophizing\", \"Workload Overwhelm\"])\n"
                f"- \"empathetic_clinical_summary\": (string under 80 words explaining the clinical diagnosis and underlying stressors with professional empathy)\n"
                f"- \"recommended_intervention\": (string under 60 words recommending exact CBT or grounding exercises tailored to this subject)"
            )

            for model_id in models_to_try:
                try:
                    response = self.client.chat.completions.create(
                        model=model_id,
                        messages=[
                            {"role": "system", "content": "You are a clinical AI stress evaluation assistant. Output only JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.4,
                        max_tokens=400,
                        timeout=5.5
                    )
                    raw_content = response.choices[0].message.content.strip()
                    # Clean markdown code block if present
                    if raw_content.startswith("```json"):
                        raw_content = raw_content[7:]
                    if raw_content.startswith("```"):
                        raw_content = raw_content[3:]
                    if raw_content.endswith("```"):
                        raw_content = raw_content[:-3]
                    
                    parsed = json.loads(raw_content.strip())
                    parsed["ai_provider"] = f"{self.provider} ({model_id})"
                    return parsed
                except Exception as e:
                    continue # Try next model if busy or JSON parse error

        # Offline / Fallback Clinical Evaluation
        return self._get_fallback_evaluation(text, modality)

    def _get_fallback_evaluation(self, text: str, modality: str, custom_score: int = None, custom_tier: str = None) -> dict:
        if is_unrelated_to_mental_health(text):
            return {
                "ai_provider": f"{self.provider} (Guardrail Filter)",
                "stress_level_index": 0,
                "clinical_risk_tier": "Not Related to Project",
                "detected_symptoms": ["Unrelated Query / Topic"],
                "empathetic_clinical_summary": UNRELATED_PROJECT_REPLY,
                "recommended_intervention": "Please submit a text check-in or question directly related to your mental health, emotional state, or daily stress."
            }

        score = custom_score if custom_score is not None else 45
        tier = custom_tier if custom_tier is not None else "Mild Stress & Fatigue"

        t_lower = text.lower()
        if any(w in t_lower for w in ["overwhelm", "burnout", "can't cope", "exhaust", "crisis"]):
            score = max(score, 76)
            tier = "Severe Emotional Distress / High Risk"
        elif any(w in t_lower for w in ["deadline", "exam", "worry", "anxious", "stress", "pressure"]):
            score = max(score, 58)
            tier = "Moderate Anxiety & Burnout Risk"
        elif any(w in t_lower for w in ["calm", "good", "relax", "happy", "fine"]):
            score = min(score, 24)
            tier = "Low / Baseline Calm"

        symptoms = []
        if any(w in t_lower for w in ["sleep", "insomnia", "tired", "exhausted"]):
            symptoms.append("Sleep Disturbance & Fatigue")
        if any(w in t_lower for w in ["deadline", "exam", "job", "work", "class", "study", "project"]):
            symptoms.append("Occupational / Academic Pressure")
        if any(w in t_lower for w in ["anxious", "worry", "panic", "fear", "scared"]):
            symptoms.append("Acute Anxiety Symptoms")
        if any(w in t_lower for w in ["depress", "lonely", "hopeless", "sad", "cry"]):
            symptoms.append("Depressive Affect & Low Mood")
        if not symptoms:
            symptoms = ["Cognitive Load", "Daily Routine Adaptation"]

        summary = (
            f"Analysis of this {modality} check-in indicates {tier.lower()} (Index: {score}/100). "
            f"The subject exhibits signs of {' and '.join([s.lower() for s in symptoms[:2]]) if len(symptoms)>=2 else symptoms[0].lower()}. "
            "Empathetic grounding and cognitive reappraisal are advised to mitigate stress accumulation."
        )

        intervention = "Practice structured cognitive reframing, challenge negative assumptions using Socratic questioning, and break pending commitments into manageable 15-minute intervals."

        return {
            "ai_provider": "Offline Clinical Evaluator (Rule-Based Fallback)",
            "stress_level_index": score,
            "clinical_risk_tier": tier,
            "detected_symptoms": symptoms,
            "empathetic_clinical_summary": summary,
            "recommended_intervention": intervention
        }

if __name__ == "__main__":
    evaluator = GeminiClinicalEvaluator()
    print("Testing Voice Transcript Evaluation:")
    print(json.dumps(evaluator.evaluate_clinical_stress("I feel anxious about my job deadlines and relationship worries.", "Voice Recording"), indent=2))
