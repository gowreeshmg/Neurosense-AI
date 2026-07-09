import sys
import numpy as np
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.config import DEFAULT_AUDIO_WEIGHT, DEFAULT_TEXT_WEIGHT, EMOTION_CATEGORIES, STRESS_CATEGORIES
from src.models.audio_classifier import AudioEnsemblePipeline
from src.models.text_classifier import LinguisticStressClassifier

class LateDecisionFusion:
    """
    Multimodal Late Decision Fusion & Risk Calibration Engine.
    Synthesizes predictions from the Speech/Acoustic pipeline (AudioEnsemblePipeline)
    and the Linguistic/Text pipeline (LinguisticStressClassifier) using dynamic confidence calibration.
    """
    def __init__(self, text_pipeline=None, audio_pipeline=None):
        self.text_pipeline = text_pipeline or LinguisticStressClassifier()
        self.audio_pipeline = audio_pipeline or AudioEnsemblePipeline()
        
    def analyze_multimodal(self, text_input=None, audio_features_195=None):
        """
        Performs dual-modality analysis. If one modality is missing, gracefully falls back to single-modality assessment.
        """
        text_result = None
        audio_result = None
        
        if text_input and str(text_input).strip():
            try:
                text_result = self.text_pipeline.predict(str(text_input))
            except Exception as e:
                print(f"[Fusion] Text prediction error: {e}")
                
        if audio_features_195 is not None and len(audio_features_195) > 0:
            try:
                audio_result = self.audio_pipeline.predict(audio_features_195)
            except Exception as e:
                print(f"[Fusion] Audio prediction error: {e}")
                
        # 1. Handle missing modalities
        if text_result is None and audio_result is None:
            return self._default_result()
        elif text_result is None:
            return self._single_modality_audio_result(audio_result)
        elif audio_result is None:
            return self._single_modality_text_result(text_result)
            
        # 2. Both modalities available -> Perform Late Decision Fusion
        t_conf = text_result.get("confidence", 0.8)
        a_conf = audio_result.get("confidence", 0.8)
        
        # Dynamic confidence weighting: give more weight to the more confident modality
        total_conf = t_conf + a_conf
        if total_conf > 0:
            w_text = (t_conf / total_conf) * 0.7 + (DEFAULT_TEXT_WEIGHT * 0.3)
            w_audio = 1.0 - w_text
        else:
            w_text = DEFAULT_TEXT_WEIGHT
            w_audio = DEFAULT_AUDIO_WEIGHT
            
        t_stress = text_result.get("linguistic_stress_score", 0.0)
        a_stress = audio_result.get("acoustic_stress_score", 0.0)
        
        combined_stress_score = round(float(w_text * t_stress + w_audio * a_stress), 2)
        
        # Determine primary stress origin
        t_cat = text_result.get("predicted_category", "Calm / Normal")
        if combined_stress_score < 30.0:
            final_category = "Calm / Normal"
        else:
            final_category = t_cat if t_cat != "Calm / Normal" else "Mixed Stress"
            
        # Determine clinical risk tier
        if combined_stress_score < 30.0:
            risk_tier = "Minimal / Normal"
            color_code = "green"
            action_summary = "No significant psychological stress detected. Emotional tone is balanced."
        elif combined_stress_score < 55.0:
            risk_tier = "Mild Stress"
            color_code = "blue"
            action_summary = f"Mild symptoms of {final_category.lower()} observed. Recommended: short breaks and time-management strategies."
        elif combined_stress_score < 80.0:
            risk_tier = "Moderate / High Stress"
            color_code = "orange"
            action_summary = f"Significant signs of {final_category.lower()} and vocal tension detected. Recommended: structured counseling or grounding CBT exercises."
        else:
            risk_tier = "Severe Emotional Distress / Risk"
            color_code = "red"
            action_summary = f"High emotional distress and acute {final_category.lower()} detected across both speech and text modalities. Immediate psychological check-in and support advised."
            
        return {
            "modality_status": "Dual-Modality (Text + Speech)",
            "combined_stress_score": combined_stress_score,
            "final_stress_category": final_category,
            "risk_tier": risk_tier,
            "color_code": color_code,
            "action_summary": action_summary,
            "fusion_weights": {
                "text_weight": round(float(w_text), 3),
                "audio_weight": round(float(w_audio), 3)
            },
            "text_analysis": text_result,
            "audio_analysis": audio_result
        }

    def _single_modality_text_result(self, text_result):
        score = text_result.get("linguistic_stress_score", 0.0)
        cat = text_result.get("predicted_category", "Calm / Normal")
        if score < 30.0:
            tier, color, summary = "Minimal / Normal", "green", "No significant text stress markers identified."
        elif score < 55.0:
            tier, color, summary = "Mild Stress", "blue", f"Mild linguistic markers of {cat.lower()} identified."
        elif score < 80.0:
            tier, color, summary = "Moderate / High Stress", "orange", f"High frequency of {cat.lower()} vocabulary identified."
        else:
            tier, color, summary = "Severe Emotional Distress / Risk", "red", f"Critical linguistic stress markers for {cat.lower()} detected."
            
        return {
            "modality_status": "Single-Modality (Text Only)",
            "combined_stress_score": score,
            "final_stress_category": cat,
            "risk_tier": tier,
            "color_code": color,
            "action_summary": summary,
            "fusion_weights": {"text_weight": 1.0, "audio_weight": 0.0},
            "text_analysis": text_result,
            "audio_analysis": None
        }

    def _single_modality_audio_result(self, audio_result):
        score = audio_result.get("acoustic_stress_score", 0.0)
        emotion = audio_result.get("predicted_emotion", "Neutral")
        cat = "Non-Academic / Vocal Stress" if emotion in ["Angry", "Fearful", "Sad", "Disgust"] else "Calm / Normal"
        if score < 30.0:
            tier, color, summary = "Minimal / Normal", "green", "Vocal tone is calm and stable."
        elif score < 55.0:
            tier, color, summary = "Mild Stress", "blue", f"Slight vocal tension ({emotion.lower()}) observed."
        elif score < 80.0:
            tier, color, summary = "Moderate / High Stress", "orange", f"High vocal agitation ({emotion.lower()}) and spectral energy detected."
        else:
            tier, color, summary = "Severe Emotional Distress / Risk", "red", f"Severe acoustic stress and emotional agitation ({emotion.lower()}) recorded."
            
        return {
            "modality_status": "Single-Modality (Speech Only)",
            "combined_stress_score": score,
            "final_stress_category": cat,
            "risk_tier": tier,
            "color_code": color,
            "action_summary": summary,
            "fusion_weights": {"text_weight": 0.0, "audio_weight": 1.0},
            "text_analysis": None,
            "audio_analysis": audio_result
        }

    def _default_result(self):
        return {
            "modality_status": "No Input Provided",
            "combined_stress_score": 0.0,
            "final_stress_category": "Calm / Normal",
            "risk_tier": "Minimal / Normal",
            "color_code": "green",
            "action_summary": "No data analyzed yet. Please provide text or audio recording.",
            "fusion_weights": {"text_weight": 0.5, "audio_weight": 0.5},
            "text_analysis": None,
            "audio_analysis": None
        }

if __name__ == "__main__":
    fusion = LateDecisionFusion()
    res = fusion.analyze_multimodal(
        text_input="I have three university exams next week and the assignment deadline is overwhelming me completely.",
        audio_features_195=np.random.normal(0.5, 0.2, size=195)
    )
    print("Test Multimodal Output:", res)
