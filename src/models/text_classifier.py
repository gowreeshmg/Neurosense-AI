import os
import sys
import pickle
import numpy as np
from pathlib import Path
try:
    import pandas as pd
    from sklearn.model_selection import train_test_split
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import classification_report, accuracy_score
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    pd = None

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
        if HAS_SKLEARN:
            self.tfidf = TfidfVectorizer(max_features=self.max_features, ngram_range=(1, 2), stop_words='english')
            self.meta_scaler = StandardScaler()
            estimators = [
                ('lr', LogisticRegression(C=5.0, max_iter=1000, class_weight='balanced', random_state=42)),
                ('rf', RandomForestClassifier(n_estimators=150, max_depth=20, class_weight='balanced', random_state=42)),
                ('gb', GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=4, random_state=42))
            ]
            self.classifier = VotingClassifier(estimators=estimators, voting='soft')
        else:
            self.tfidf = None
            self.meta_scaler = None
            self.classifier = None
        self.classes_ = STRESS_CATEGORIES
        self.is_fitted = False

    def _extract_features(self, texts, meta_df=None, fit=False):
        if not HAS_SKLEARN or self.tfidf is None:
            return np.zeros((len(texts), 10))
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
        if not HAS_SKLEARN:
            print("[Text Pipeline] scikit-learn not available. Skipping training.")
            return 0.0
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Dataset not found at {data_path}. Run generate_text_data first.")
            
        df = pd.read_csv(data_path)
        print(f"[Text Pipeline] Loaded {len(df)} samples from {data_path}")
        
        X = self._extract_features(df["text"].values, meta_df=df, fit=True)
        y = df["label"].values
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        
        print("[Text Pipeline] Training Voting Ensemble (Logistic Regression + Random Forest + Gradient Boosting)...")
        self.classifier.fit(X_train, y_train)
        self.is_fitted = True
        
        y_pred = self.classifier.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        print(f"\n[Text Pipeline] Ensemble Test Accuracy: {acc * 100:.2f}%\n")
        
        y_test_names = [self.classes_[idx] for idx in y_test]
        y_pred_names = [self.classes_[idx] for idx in y_pred]
        print(classification_report(y_test_names, y_pred_names))
        
        self.save_model()
        return acc

    def _heuristic_predict(self, text):
        t_low = str(text).lower()
        words = t_low.split()
        word_count = len(words)
        fp_ratio = calculate_first_person_pronoun_ratio(text)
        neg_density = calculate_negative_word_density(text)
        
        acad_keywords = ["exam", "test", "deadline", "grade", "fail", "pass", "study", "studying", "class", "assignment", "project", "quiz", "school", "college", "university"]
        soc_keywords = ["lonely", "friend", "friends", "isolated", "alone", "social", "party", "people", "breakup", "relationship", "family", "parents"]
        gen_keywords = ["stress", "anxious", "anxiety", "depressed", "depression", "overwhelmed", "panic", "exhausted", "tired", "sleep", "insomnia", "worry", "worried", "scared", "fear", "hopeless"]
        
        acad_hits = sum(1 for w in words if any(k in w for k in acad_keywords))
        soc_hits = sum(1 for w in words if any(k in w for k in soc_keywords))
        gen_hits = sum(1 for w in words if any(k in w for k in gen_keywords))
        
        raw_score = (neg_density * 120.0) + (fp_ratio * 35.0) + (acad_hits * 14.0) + (soc_hits * 14.0) + (gen_hits * 18.0)
        stress_score = round(min(96.0, max(5.0, raw_score)), 2)
        
        if stress_score < 25.0 and acad_hits == 0 and soc_hits == 0 and gen_hits == 0:
            pred_cat = "Calm / Normal"
            prob_dict = {"Calm / Normal": 0.82, "Academic Burnout & Exam Anxiety": 0.08, "Social / Interpersonal Stress": 0.05, "General / Non-Academic Emotional Distress": 0.05}
        elif acad_hits >= soc_hits and acad_hits >= gen_hits and (acad_hits > 0 or stress_score > 35.0):
            pred_cat = "Academic Burnout & Exam Anxiety"
            prob_dict = {"Academic Burnout & Exam Anxiety": 0.74, "General / Non-Academic Emotional Distress": 0.14, "Social / Interpersonal Stress": 0.08, "Calm / Normal": 0.04}
        elif soc_hits > acad_hits and soc_hits >= gen_hits:
            pred_cat = "Social / Interpersonal Stress"
            prob_dict = {"Social / Interpersonal Stress": 0.72, "General / Non-Academic Emotional Distress": 0.16, "Academic Burnout & Exam Anxiety": 0.08, "Calm / Normal": 0.04}
        else:
            if stress_score > 40.0:
                pred_cat = "General / Non-Academic Emotional Distress"
                prob_dict = {"General / Non-Academic Emotional Distress": 0.70, "Academic Burnout & Exam Anxiety": 0.16, "Social / Interpersonal Stress": 0.10, "Calm / Normal": 0.04}
            else:
                pred_cat = "Calm / Normal"
                prob_dict = {"Calm / Normal": 0.75, "Academic Burnout & Exam Anxiety": 0.12, "General / Non-Academic Emotional Distress": 0.08, "Social / Interpersonal Stress": 0.05}
                
        return {
            "predicted_category": pred_cat,
            "probabilities": prob_dict,
            "linguistic_stress_score": stress_score,
            "confidence": round(float(prob_dict[pred_cat]), 4),
            "metadata": {
                "first_person_ratio": fp_ratio,
                "negative_word_density": neg_density,
                "word_count": word_count
            }
        }

    def predict(self, text):
        """
        Predicts stress category and severity from user text or transcribed speech.
        """
        if not self.is_fitted:
            try:
                self.load_model()
            except Exception:
                pass
                
        if not self.is_fitted or self.classifier is None or not HAS_SKLEARN:
            return self._heuristic_predict(text)
            
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
        if not HAS_SKLEARN:
            return
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
        if not HAS_SKLEARN:
            raise ImportError("scikit-learn not available")
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
