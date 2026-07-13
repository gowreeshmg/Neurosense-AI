from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class TextAnalyzeRequest(BaseModel):
    text: str = Field(..., description="User narrative, journal entry, or transcribed speech text")
    include_xai: bool = Field(True, description="Whether to include LIME token-level explainability")
    include_cbt: bool = Field(True, description="Whether to include CBT assistant intervention")

class WordContribution(BaseModel):
    word: str
    impact_score: float
    direction: str

class TextXAIOutput(BaseModel):
    predicted_category: str
    top_words: List[WordContribution]
    html_highlighted: str

class CBTInterventionOutput(BaseModel):
    greeting: str
    empathetic_validation: str
    recommended_exercise: str
    exercise_details: str
    coping_strategy: str

class GeminiClinicalReport(BaseModel):
    ai_provider: str
    stress_level_index: int
    clinical_risk_tier: str
    detected_symptoms: List[str]
    empathetic_clinical_summary: str
    recommended_intervention: str

class TextAnalyzeResponse(BaseModel):
    predicted_category: str
    probabilities: Dict[str, float]
    linguistic_stress_score: float
    confidence: float
    metadata: Dict[str, Any]
    xai_explanation: Optional[TextXAIOutput] = None
    cbt_intervention: Optional[CBTInterventionOutput] = None
    gemini_evaluation: Optional[GeminiClinicalReport] = None

class MultimodalAnalyzeRequest(BaseModel):
    text: Optional[str] = None
    audio_features_195: Optional[List[float]] = None
    include_xai: bool = True
    include_cbt: bool = True

class AudioDriver(BaseModel):
    feature_name: str
    raw_index: int
    impact_percentage: float
    direction: str
    clinical_interpretation: str

class AudioXAIOutput(BaseModel):
    predicted_emotion: str
    acoustic_stress_score: float
    top_acoustic_drivers: List[AudioDriver]
    summary: str

class MultimodalAnalyzeResponse(BaseModel):
    modality_status: str
    combined_stress_score: float
    final_stress_category: str
    risk_tier: str
    color_code: str
    action_summary: str
    fusion_weights: Dict[str, float]
    text_analysis: Optional[Dict[str, Any]] = None
    audio_analysis: Optional[Dict[str, Any]] = None
    text_xai: Optional[TextXAIOutput] = None
    audio_xai: Optional[AudioXAIOutput] = None
    cbt_intervention: Optional[CBTInterventionOutput] = None
    gemini_evaluation: Optional[GeminiClinicalReport] = None

class CBTChatRequest(BaseModel):
    message: str
    current_stress_category: str = "Academic Stress"

class CBTChatResponse(BaseModel):
    reply: str
    timestamp: str

class MetricsResponse(BaseModel):
    training_time_seconds: float
    text_classifier_test_accuracy: float
    audio_classifier_test_accuracy: float
    fusion_status: str
    timestamp: str
