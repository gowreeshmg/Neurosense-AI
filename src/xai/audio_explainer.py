import sys
import numpy as np
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.models.audio_classifier import AudioEnsemblePipeline
from src.config import TOTAL_AUDIO_FEATURES

class AudioExplainerSHAP:
    """
    Acoustic Feature Importance & Attribution Engine.
    Inspired by SHAP feature attribution in Paper #14 & #4.
    Translates raw 195-dimensional acoustic coefficients into human-readable clinical/prosodic explanations
    (e.g., 'Elevated MFCC-17 Throat Tension' vs 'Harmonic Chromagram Stability').
    """
    def __init__(self, audio_classifier=None):
        self.audio_classifier = audio_classifier or AudioEnsemblePipeline()
        if not self.audio_classifier.is_fitted:
            try:
                self.audio_classifier.load_model()
            except Exception:
                pass
            
    def _get_feature_name(self, index):
        """
        Maps 195 raw indices to descriptive acoustic categories.
        """
        if index < 40:
            return f"MFCC Mean Coeff #{index+1} (Vocal Tract Shape)"
        elif index < 80:
            return f"MFCC Variance Coeff #{index-39} (Vocal Tension Modulation)"
        elif index < 144:
            return f"Mel-Spectrogram Band #{index-79} (Acoustic Energy Distribution)"
        elif index < 156:
            pitch_classes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            return f"Chromagram Pitch Mean ({pitch_classes[index-144]})"
        elif index < 168:
            pitch_classes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            return f"Chromagram Pitch Variance ({pitch_classes[index-156]})"
        elif index < 175:
            return f"Spectral Contrast Brightness Band #{index-167} (Vocal Fry/Clear Tone)"
        elif index < 182:
            return f"Spectral Contrast Variance Band #{index-174}"
        elif index < 194:
            return f"Tonnetz Tonal Interval Feature #{index-181}"
        else:
            return "RMS Vocal Amplitude Energy / Micro-Tremor"

    def explain_instance(self, feature_vector_195, top_k=6):
        """
        Calculates top acoustic features driving the emotion & stress prediction.
        """
        pred = self.audio_classifier.predict(feature_vector_195)
        pred_emotion = pred["predicted_emotion"]
        stress_score = pred["acoustic_stress_score"]
        
        # Get selected indices from pipeline
        selected_indices = self.audio_classifier.selected_indices
        if selected_indices is None or len(selected_indices) == 0:
            selected_indices = np.arange(min(35, TOTAL_AUDIO_FEATURES))
            
        # Get ensemble Random Forest base feature importances as our Shapley proxy
        rf_model = self.audio_classifier.ensemble.named_estimators_['rf']
        importances = rf_model.feature_importances_
        
        # Calculate local weighted impact
        x_scaled = self.audio_classifier.scaler.transform(np.array(feature_vector_195, dtype=np.float32).reshape(1, -1))[0]
        x_selected = x_scaled[selected_indices]
        
        feature_attributions = []
        for idx_in_sel, orig_idx in enumerate(selected_indices):
            imp = importances[idx_in_sel]
            val = x_selected[idx_in_sel]
            
            # Signed attribution based on whether value is above/below mean and if predicted emotion is stress-heavy
            is_high_stress_pred = pred_emotion in ["Angry", "Fearful", "Sad", "Disgust"]
            if is_high_stress_pred:
                signed_score = imp * (val if val > 0 else -0.5 * val)
            else:
                signed_score = imp * (-val if val > 0 else 0.5 * val)
                
            name = self._get_feature_name(orig_idx)
            
            # Clinical interpretation
            if "MFCC" in name:
                interp = "Indicates physical vocal cord tension and rapid speech articulation shifts."
            elif "Spectral Contrast" in name:
                interp = "Reflects high vocal brightness or harsh vocal fry associated with emotional strain."
            elif "Chromagram" in name:
                interp = "Tracks pitch stability and emotional tone variations across octaves."
            elif "RMS" in name:
                interp = "Measures overall speaking volume intensity and micro-tremor amplitude."
            else:
                interp = "Represents harmonic frequency balance."
                
            feature_attributions.append({
                "feature_name": name,
                "raw_index": int(orig_idx),
                "impact_percentage": round(float(abs(signed_score) * 100 * 2.5), 1),
                "direction": "stress" if (is_high_stress_pred and val > 0) else "calm",
                "clinical_interpretation": interp
            })
            
        sorted_attribs = sorted(feature_attributions, key=lambda x: x["impact_percentage"], reverse=True)[:top_k]
        
        return {
            "predicted_emotion": pred_emotion,
            "acoustic_stress_score": stress_score,
            "top_acoustic_drivers": sorted_attribs,
            "summary": f"Prediction of '{pred_emotion}' (Stress: {stress_score}%) is predominantly driven by {sorted_attribs[0]['feature_name']} and {sorted_attribs[1]['feature_name']}."
        }

if __name__ == "__main__":
    explainer = AudioExplainerSHAP()
    res = explainer.explain_instance(np.random.normal(0.6, 0.3, size=195))
    print("Top Acoustic Features Explained:\n", res["summary"])
