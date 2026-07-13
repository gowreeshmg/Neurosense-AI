# NeuroSense AI — Strict Topic Guardrails & Relevance Filtering
# Enforces that the assistant only answers questions related to mental health, stress, anxiety, depression, relationship issues, and emotional well-being.

import re

UNRELATED_PROJECT_REPLY = (
    "This question is not related to our project. As the NeuroSense AI assistant, "
    "I can only answer questions and provide support regarding mental health issues, "
    "stress, anxiety, depression, relationship challenges, and emotional well-being. "
    "Please ask a question related to mental health or stress support."
)

def is_unrelated_to_mental_health(text: str) -> bool:
    """
    Determines if a user query is clearly unrelated to mental health, stress, anxiety,
    depression, relationships, emotional well-being, or the NeuroSense project.
    Returns True if the query is unrelated, False if it is related or a valid greeting.
    """
    if not text or len(text.strip()) == 0:
        return False
        
    t_lower = text.lower().strip()
    
    # 1. Check for explicitly unrelated domain keywords FIRST
    unrelated_domains = [
        # Programming / Tech / Coding
        "python", "javascript", "java ", "c++", "c#", "html", "css", "sql", "write code", "coding",
        "algorithm", "function", "array", "for loop", "while loop", "variable", "syntax", "compile", "error",
        "bug", "debug", "git ", "github", "linux", "windows os", "ubuntu", "bash", "powershell",
        "react", "angular", "django", "flask", "api endpoint", "database", "query",
        
        # Cooking / Recipes
        "recipe", "cook", "cooking", "bake", "baking", "cake", "pizza", "pasta", "chicken",
        "ingredients", "oven", "boil", "fry", "kitchen", "restaurant",
        
        # Math / Physics / Hard Sciences
        "calculus", "algebra", "integral", "derivative", "equation", "solve math", "multiplication",
        "division", "geometry", "trigonometry", "physics formula", "quantum", "thermodynamics",
        "what is ", "calculate ", "solve ", "*", "+", "/"
        
        # General Trivia / Sports / Politics / Finance
        "who won", "world cup", "super bowl", "champion", "president", "election", "capital of",
        "stock market", "crypto", "bitcoin", "ethereum", "investing", "mutual fund", "weather forecast",
        "movie", "actor", "actress", "song lyrics", "celebrity", "joke", "funny story", "trivia"
    ]
    
    for domain_kw in unrelated_domains:
        if domain_kw in t_lower:
            # Unless they are specifically expressing stress *about* that topic
            if not any(sk in t_lower for sk in ["stress", "anxi", "depress", "panic", "overwhelm", "deadlin", "exam", "worry", "worried", "burnout", "feel", "sad"]):
                return True

    # 2. Allow general conversational greetings, check-ins, corrections, and help requests
    greetings = [
        "hello", "hi", "hey", "start", "good morning", "good afternoon", 
        "good evening", "how are you", "who are you", "what can you do", 
        "help", "test", "check-in", "checkin", "thank you", "thanks", "chat", "talk",
        "yes", "no", "ok", "okay", "please", "not academic", "it is not"
    ]
    if any(t_lower.startswith(g) or t_lower.endswith(g) or g == t_lower for g in greetings):
        return False

    # 3. Check for mental health, emotional, relationship, CBT, stress, exercise, and lifestyle keywords
    mental_health_keywords = [
        "stress", "anxi", "depress", "burnout", "lonel", "alone", "sad", "unhappy", "overwhelm",
        "mental", "health", "feel", "feeling", "mood", "emot", "calm", "relax", "breath",
        "ground", "cbt", "therap", "counsel", "counselor", "help", "fear", "worry", "worried",
        "cry", "crying", "sleep", "insomnia", "tired", "exhaust", "relationship", "friend",
        "family", "breakup", "partner", "boyfriend", "girlfriend", "marriage", "deadlin",
        "exam", "assignment", "pressure", "work", "workload", "job", "life", "school",
        "college", "university", "study", "studying", "gpa", "coursework", "fail",
        "panic", "heart", "scared", "mindful", "mindfulness", "self-care", "selfcare",
        "suicid", "die", "hopeless", "unbearable", "coping", "cope", "meditat", "peace",
        "psycholog", "psychiat", "doctor", "trauma", "ptsd", "adhd", "focus", "concentration",
        "overthinking", "catastroph", "distortion", "reframe", "reframing", "pomodoro",
        "talk", "chat", "listen", "advice", "support", "struggl", "problem", "issue", "hard",
        "tough", "bad", "good", "better", "worse", "pain", "hurting", "neurosense", "mind",
        "exercise", "exercises", "technique", "techniques", "strategy", "strategies",
        "practice", "reduce", "solution", "what should i do", "how to", "can you",
        "guide", "tips", "remedy", "relief", "calm down", "not academic", "not about",
        "it is not", "academic"
    ]
    
    for kw in mental_health_keywords:
        if kw in t_lower:
            return False
            
    # 4. If it contains zero mental health or greeting keywords, classify as unrelated
    words = re.findall(r'\w+', t_lower)
    if len(words) >= 4:
        return True
        
    return False
