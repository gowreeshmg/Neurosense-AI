import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models_bin"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

# Dataset Paths
TEXT_DATASET_PATH = DATA_DIR / "student_stress_dataset.csv"
AUDIO_FEATURES_PATH = DATA_DIR / "audio_features_dataset.csv"

# Model Paths
TEXT_MODEL_PATH = MODELS_DIR / "text_classifier_pipeline.pkl"
AUDIO_MODEL_PATH = MODELS_DIR / "audio_ensemble_pipeline.pkl"
FUSION_MODEL_PATH = MODELS_DIR / "fusion_calibrator.pkl"

# Audio Settings
SAMPLE_RATE = 16000
DURATION_SECONDS = 3.0
N_MFCC = 40
N_MELS = 128
N_CHROMA = 12
N_CONTRAST = 7
N_TONNETZ = 6
TOTAL_AUDIO_FEATURES = 195  # 40*2 (mean+std) + 12*2 + 128 (pooled) + etc. -> EXACT 195 engineered features

# Categories
STRESS_CATEGORIES = [
    "Academic Stress",
    "Non-Academic Stress",
    "Mixed Stress",
    "Calm / Normal"
]

EMOTION_CATEGORIES = [
    "Neutral",
    "Calm",
    "Happy",
    "Sad",
    "Angry",
    "Fearful",
    "Disgust",
    "Surprised"
]

# Fusion Weights (Default priors before dynamic calibration)
DEFAULT_TEXT_WEIGHT = 0.65
DEFAULT_AUDIO_WEIGHT = 0.35

# Explainability Settings
LIME_NUM_SAMPLES = 500
SHAP_TOP_K_FEATURES = 10
