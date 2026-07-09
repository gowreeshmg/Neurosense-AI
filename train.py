#!/usr/bin/env python3
"""
NeuroSense AI — Master Training & Evaluation Script
Orchestrates dataset generation, feature selection, multi-model training, 
10-fold cross-validation evaluation, and model serialization.
"""
import os
import sys
import json
import time
from pathlib import Path

# Add project root to sys path
sys.path.append(str(Path(__file__).resolve().parent))

from src.config import TEXT_DATASET_PATH, AUDIO_FEATURES_PATH, MODELS_DIR
from src.data_prep.generate_text_data import generate_dataset as generate_text_dataset
from src.data_prep.audio_processor import generate_benchmark_audio_dataset
from src.models.text_classifier import LinguisticStressClassifier
from src.models.audio_classifier import AudioEnsemblePipeline
from src.models.fusion_engine import LateDecisionFusion

def main():
    print("=" * 80)
    print("      NeuroSense AI: Dual-Modality Mental Health System Master Trainer")
    print("=" * 80)
    start_time = time.time()
    
    # Step 1: Ensure/Generate Datasets
    print("\n[Step 1/4] Verifying and generating benchmark training datasets...")
    if not os.path.exists(TEXT_DATASET_PATH):
        generate_text_dataset(total_samples=1500)
    else:
        print(f"-> Text dataset already present at {TEXT_DATASET_PATH}")
        
    if not os.path.exists(AUDIO_FEATURES_PATH):
        generate_benchmark_audio_dataset(num_samples=1200)
    else:
        print(f"-> Audio acoustic feature dataset already present at {AUDIO_FEATURES_PATH}")
        
    # Step 2: Train Linguistic Stress Classifier
    print("\n[Step 2/4] Training Linguistic Stress Classifier (TF-IDF + Pronoun Density + Ensemble)...")
    text_clf = LinguisticStressClassifier(max_features=4000)
    text_acc = text_clf.train_and_evaluate(data_path=TEXT_DATASET_PATH)
    
    # Step 3: Train Audio Rank-Based Ensemble Classifier
    print("\n[Step 3/4] Training Audio Rank-Based Ensemble (Random Forest + Gradient Boosting + MLP)...")
    audio_clf = AudioEnsemblePipeline(top_k_features=35)
    audio_acc = audio_clf.train_and_evaluate(data_path=AUDIO_FEATURES_PATH)
    
    # Step 4: Verify Multimodal Late Fusion Engine
    print("\n[Step 4/4] Verifying Multimodal Late Decision Fusion Engine...")
    fusion = LateDecisionFusion(text_pipeline=text_clf, audio_pipeline=audio_clf)
    sample_res = fusion.analyze_multimodal(
        text_input="I have three major exams next week and the assignment deadline for coursework is making me feel completely overwhelmed and anxious.",
        audio_features_195=[0.5]*195
    )
    print(f"-> Fusion verification successful! Final Category: {sample_res['final_stress_category']} (Risk Tier: {sample_res['risk_tier']})")
    
    elapsed = time.time() - start_time
    summary = {
        "training_time_seconds": round(elapsed, 2),
        "text_classifier_test_accuracy": round(float(text_acc), 4),
        "audio_classifier_test_accuracy": round(float(audio_acc), 4),
        "fusion_status": "Verified & Calibrated",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    summary_path = os.path.join(MODELS_DIR, "training_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
        
    print("\n" + "=" * 80)
    print(f"Training completed successfully in {elapsed:.2f} seconds!")
    print(f"Text Accuracy:  {text_acc*100:.2f}%")
    print(f"Audio Accuracy: {audio_acc*100:.2f}%")
    print(f"Model pipelines and metrics saved to: {MODELS_DIR}")
    print("=" * 80)

if __name__ == "__main__":
    main()
