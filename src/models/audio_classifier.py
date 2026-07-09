import os
import sys
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import classification_report, accuracy_score

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.config import AUDIO_FEATURES_PATH, AUDIO_MODEL_PATH, EMOTION_CATEGORIES, TOTAL_AUDIO_FEATURES

try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    from lightgbm import LGBMClassifier
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False


class AudioEnsemblePipeline:
    """
    Rank-Based Ensemble Classifier for Speech Emotion & Acoustic Stress Detection.
    Implements feature selection + multi-model voting as recommended in Papers #14 and #13.
    """
    def __init__(self, top_k_features=35):
        self.top_k_features = top_k_features
        self.scaler = StandardScaler()
        self.selector = SelectKBest(score_func=f_classif, k=self.top_k_features)
        
        # Build base estimators
        estimators = [
            ('rf', RandomForestClassifier(n_estimators=200, max_depth=15, class_weight='balanced', random_state=42)),
            ('gb', GradientBoostingClassifier(n_estimators=120, learning_rate=0.08, max_depth=5, random_state=42)),
            ('mlp', MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=400, alpha=0.01, random_state=42))
        ]
        
        if XGBOOST_AVAILABLE:
            estimators.append(('xgb', XGBClassifier(n_estimators=150, learning_rate=0.08, max_depth=6, eval_metric='mlogloss', random_state=42)))
            
        if LIGHTGBM_AVAILABLE:
            estimators.append(('lgb', LGBMClassifier(n_estimators=150, learning_rate=0.08, max_depth=6, verbose=-1, random_state=42)))
            
        self.ensemble = VotingClassifier(estimators=estimators, voting='soft')
        self.feature_names_in = [f"feature_{i+1}" for i in range(TOTAL_AUDIO_FEATURES)]
        self.selected_indices = None
        self.classes_ = EMOTION_CATEGORIES
        self.is_fitted = False

    def train_and_evaluate(self, data_path=AUDIO_FEATURES_PATH):
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Audio features dataset not found at {data_path}. Run audio_processor.py first.")
            
        print(f"[Audio Pipeline] Loading dataset from {data_path}...")
        df = pd.read_csv(data_path)
        
        X = df[self.feature_names_in].values
        y = df["emotion"].values
        stress_scores = df["stress_intensity"].values
        
        # Encode target if XGB/LGB present or just for clean handling
        label_map = {cat: i for i, cat in enumerate(self.classes_)}
        y_encoded = np.array([label_map[label] for label in y])
        
        X_train, X_test, y_train, y_test, s_train, s_test = train_test_split(
            X, y_encoded, stress_scores, test_size=0.2, random_state=42, stratify=y_encoded
        )
        
        print("[Audio Pipeline] Scaling and performing ANOVA F-test Feature Selection...")
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_train_selected = self.selector.fit_transform(X_train_scaled, y_train)
        self.selected_indices = self.selector.get_support(indices=True)
        
        print(f"[Audio Pipeline] Selected top {self.top_k_features} acoustic features out of {TOTAL_AUDIO_FEATURES}.")
        print("[Audio Pipeline] Training Rank-Based Ensemble model (Random Forest + Gradient Boosting + MLP/XGB)...")
        self.ensemble.fit(X_train_selected, y_train)
        self.is_fitted = True
        
        # Evaluate on test set
        X_test_scaled = self.scaler.transform(X_test)
        X_test_selected = self.selector.transform(X_test_scaled)
        y_pred = self.ensemble.predict(X_test_selected)
        acc = accuracy_score(y_test, y_pred)
        
        print(f"\n[Audio Pipeline] Test Accuracy: {acc*100:.2f}%")
        inv_map = {i: cat for cat, i in label_map.items()}
        y_test_names = [inv_map[i] for i in y_test]
        y_pred_names = [inv_map[i] for i in y_pred]
        print(classification_report(y_test_names, y_pred_names))
        
        self.save_model()
        return acc

    def predict(self, feature_vector_195):
        """
        Takes a 195-dim acoustic feature vector and returns:
          - predicted emotion (str)
          - class probabilities (dict)
          - estimated acoustic stress intensity (0.0 to 100.0)
        """
        if not self.is_fitted:
            self.load_model()
            
        x = np.array(feature_vector_195, dtype=np.float32).reshape(1, -1)
        if x.shape[1] != TOTAL_AUDIO_FEATURES:
            raise ValueError(f"Expected {TOTAL_AUDIO_FEATURES} features, got {x.shape[1]}")
            
        x_scaled = self.scaler.transform(x)
        x_selected = self.selector.transform(x_scaled)
        
        probs = self.ensemble.predict_proba(x_selected)[0]
        pred_idx = np.argmax(probs)
        pred_emotion = self.classes_[pred_idx]
        
        prob_dict = {self.classes_[i]: round(float(probs[i]), 4) for i in range(len(self.classes_))}
        
        # Calculate stress intensity score based on high-stress emotions and high spectral contrast/MFCC energy
        high_stress_emotions = ["Angry", "Fearful", "Sad", "Disgust"]
        stress_prob_sum = sum(probs[self.classes_.index(e)] for e in high_stress_emotions)
        
        # Incorporate spectral contrast / RMS energy from feature vector
        rms_val = float(feature_vector_195[-1])
        stress_intensity = round(min(100.0, max(5.0, stress_prob_sum * 85.0 + (rms_val * 60.0))), 2)
        
        return {
            "predicted_emotion": pred_emotion,
            "probabilities": prob_dict,
            "acoustic_stress_score": stress_intensity,
            "confidence": round(float(np.max(probs)), 4)
        }

    def save_model(self, path=AUDIO_MODEL_PATH):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({
                "scaler": self.scaler,
                "selector": self.selector,
                "ensemble": self.ensemble,
                "selected_indices": self.selected_indices,
                "classes_": self.classes_
            }, f)
        print(f"[Audio Pipeline] Model saved successfully to {path}")

    def load_model(self, path=AUDIO_MODEL_PATH):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Trained audio model not found at {path}. Run train_and_evaluate first.")
        with open(path, "rb") as f:
            checkpoint = pickle.load(f)
            self.scaler = checkpoint["scaler"]
            self.selector = checkpoint["selector"]
            self.ensemble = checkpoint["ensemble"]
            self.selected_indices = checkpoint["selected_indices"]
            self.classes_ = checkpoint["classes_"]
            self.is_fitted = True
        print(f"[Audio Pipeline] Model loaded successfully from {path}")

if __name__ == "__main__":
    pipeline = AudioEnsemblePipeline(top_k_features=35)
    pipeline.train_and_evaluate()
