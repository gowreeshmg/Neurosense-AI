import os
import sys
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.config import TEXT_DATASET_PATH, TEXT_MODEL_PATH, STRESS_CATEGORIES
from src.data_prep.generate_text_data import calculate_first_person_pronoun_ratio, calculate_negative_word_density

class LinguisticStressClassifier:
    """
    Linguistic & Text-Based Mental Health Classification Pipeline.
    Combines TF-IDF word embeddings (capturing academic vocabulary like 'exam', 'deadline' vs
    emotional vocabulary like 'lonely', 'depressed') with syntactic metadata (First-Person Pronoun Ratio & Negative Density).
    """
    def __init__(self, max_features=4000):
        self.max_features = max_features
        self.tfidf = TfidfVectorizer(max_features=self.max_features, ngram_range=(1, 2), stop_words='english')
        self.meta_scaler = StandardScaler()
        
        # Build ensemble of strong linear & tree models
        estimators = [
            ('lr', LogisticRegression(C=5.0, max_iter=1000, class_weight='balanced', random_state=42)),
            ('rf', RandomForestClassifier(n_estimators=150, max_depth=20, class_weight='balanced', random_state=42)),
            ('gb', GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=4, random_state=42))
        ]
        
        self.classifier = VotingClassifier(estimators=estimators, voting='soft')
        self.classes_ = STRESS_CATEGORIES
        self.is_fitted = False

    def _extract_features(self, texts, meta_df=None, fit=False):
        if fit:
            tfidf_mat = self.tfidf.fit_transform(texts).toarray()
        else:
            tfidf_mat = self.tfidf.transform(texts).toarray()
            
        if meta_df is not None:
            meta_cols = meta_df[["first_person_ratio", "negative_word_density", "word_count"]].values
        else:
            meta_cols = np.array([[
                calculate_first_person_pronoun_ratio(t),
                calculate_negative_word_density(t),
                len(t.split())
            ] for t in texts])
            
        if fit:
            meta_scaled = self.meta_scaler.fit_transform(meta_cols)
        else:
            meta_scaled = self.meta_scaler.transform(meta_cols)
            
        return np.hstack([tfidf_mat, meta_scaled])

    def train_and_evaluate(self, data_path=TEXT_DATASET_PATH):
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Text dataset not found at {data_path}. Run generate_text_data.py first.")
            
        print(f"[Text Pipeline] Loading dataset from {data_path}...")
        df = pd.read_csv(data_path)
        
        texts = df["text"].astype(str).values
        y = df["category"].values
        
        # Encode targets consistently
        label_map = {cat: i for i, cat in enumerate(self.classes_)}
        y_encoded = np.array([label_map[label] for label in y])
        
        X_train_texts, X_test_texts, y_train, y_test, df_train, df_test = train_test_split(
            texts, y_encoded, df, test_size=0.2, random_state=42, stratify=y_encoded
        )
        
        print("[Text Pipeline] Extracting TF-IDF and syntactic features...")
        X_train = self._extract_features(X_train_texts, meta_df=df_train, fit=True)
        X_test = self._extract_features(X_test_texts, meta_df=df_test, fit=False)
        
        print(f"[Text Pipeline] Feature matrix shape: {X_train.shape} (TF-IDF + 3 linguistic metadata features)")
        print("[Text Pipeline] Training Linguistic Stress Ensemble Classifier...")
        self.classifier.fit(X_train, y_train)
        self.is_fitted = True
        
        y_pred = self.classifier.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        
        print(f"\n[Text Pipeline] Test Accuracy: {acc*100:.2f}%")
        inv_map = {i: cat for cat, i in label_map.items()}
        y_test_names = [inv_map[i] for i in y_test]
        y_pred_names = [inv_map[i] for i in y_pred]
        print(classification_report(y_test_names, y_pred_names))
        
        self.save_model()
        return acc

    def predict(self, text):
        """
        Predicts stress category and severity from user text or transcribed speech.
        """
        if not self.is_fitted:
            self.load_model()
            
        x = self._extract_features([str(text)], fit=False)
        probs = self.classifier.predict_proba(x)[0]
        
        pred_idx = np.argmax(probs)
        pred_category = self.classes_[pred_idx]
        prob_dict = {self.classes_[i]: round(float(probs[i]), 4) for i in range(len(self.classes_))}
        
        # Calculate stress score
        calm_prob = prob_dict.get("Calm / Normal", 0.0)
        stress_prob = 1.0 - calm_prob
        neg_density = calculate_negative_word_density(text)
        
        stress_score = round(min(100.0, max(0.0, (stress_prob * 80.0) + (neg_density * 100.0))), 2)
        
        return {
            "predicted_category": pred_category,
            "probabilities": prob_dict,
            "linguistic_stress_score": stress_score,
            "confidence": round(float(np.max(probs)), 4),
            "metadata": {
                "first_person_ratio": calculate_first_person_pronoun_ratio(text),
                "negative_word_density": neg_density,
                "word_count": len(text.split())
            }
        }

    def save_model(self, path=TEXT_MODEL_PATH):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({
                "tfidf": self.tfidf,
                "meta_scaler": self.meta_scaler,
                "classifier": self.classifier,
                "classes_": self.classes_
            }, f)
        print(f"[Text Pipeline] Model saved successfully to {path}")

    def load_model(self, path=TEXT_MODEL_PATH):
        if not os.path.exists(path):
            for alt in [Path("/var/task/models_bin/text_classifier_pipeline.pkl"), Path("models_bin/text_classifier_pipeline.pkl"), Path(__file__).resolve().parent.parent.parent / "models_bin" / "text_classifier_pipeline.pkl"]:
                if alt.exists():
                    path = alt
                    break
        if not os.path.exists(path):
            raise FileNotFoundError(f"Trained text model not found at {path}. Run train_and_evaluate first.")
        with open(path, "rb") as f:
            checkpoint = pickle.load(f)
            self.tfidf = checkpoint["tfidf"]
            self.meta_scaler = checkpoint["meta_scaler"]
            self.classifier = checkpoint["classifier"]
            self.classes_ = checkpoint["classes_"]
            self.is_fitted = True
        print(f"[Text Pipeline] Model loaded successfully from {path}")

if __name__ == "__main__":
    classifier = LinguisticStressClassifier(max_features=4000)
    classifier.train_and_evaluate()
