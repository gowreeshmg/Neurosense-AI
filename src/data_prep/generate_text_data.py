import os
import random
import pandas as pd
from pathlib import Path
import sys

# Ensure config is importable
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.config import TEXT_DATASET_PATH, STRESS_CATEGORIES

# Vocabulary pools based on empirical findings in Paper #14 & #8
ACADEMIC_TEMPLATES = [
    "I have {num} major exams next week and my coursework deadlines are overwhelming me completely.",
    "The assignment deadline for {subject} is tomorrow and I am terrified about my grades and GPA.",
    "I can't focus on my lectures because the exam pressure and coursework difficulty are causing severe concentration difficulties.",
    "My thesis defense and final semester exams are approaching, and the workload anxiety is keeping me awake all night.",
    "The competition in university for top grades and placement is making my daily stress unbearable.",
    "I am falling behind on my {subject} assignments and the fear of failing my semester is paralyzing my productivity.",
    "Trying to balance {num} lectures, lab reports, and continuous assessments is causing immense academic fatigue.",
    "I feel constant pressure from my professors and exam deadlines, and my academic performance is dropping rapidly.",
    "Whenever I open my textbooks for {subject}, my heart races due to performance anxiety and fear of low marks.",
    "The grading criteria are so strict that no matter how hard I study, I worry about losing my scholarship."
]

NON_ACADEMIC_TEMPLATES = [
    "I feel lonely and depressed because of family issues and difficult personal relationship struggles at home.",
    "Financial problems and paying for living expenses are causing me severe anxiety and emotional distress.",
    "My personal relationships are falling apart and I feel isolated from my friends and social circle.",
    "Dealing with health issues and family expectations at the same time makes me feel hopeless every day.",
    "Moving to higher education away from my family has caused deep loneliness and social adjustment difficulties.",
    "I feel a constant sense of sadness and emptiness inside that has nothing to do with school or studies.",
    "My family relationships are very strained right now, and the emotional burden is weighing heavily on my mental health.",
    "Financial insecurity and debt are constantly on my mind, leading to sleepless nights and panic attacks.",
    "I recently went through a tough breakup and the emotional pain makes it impossible to enjoy anything in life.",
    "I feel disconnected from everyone around me and struggle with severe social isolation in my dormitory."
]

MIXED_TEMPLATES = [
    "Between my upcoming {subject} exams and severe financial problems at home, I am completely overwhelmed and stressed.",
    "I can't study for my {num} assignments because my family relationship breakdown and loneliness are destroying my focus.",
    "My grades are slipping due to exam pressure, and on top of that, my financial debt and personal health issues are worsening.",
    "I feel anxious all the time because my academic workload is huge and I also have no social support or friends here.",
    "The fear of failing my {subject} coursework combined with family expectations and financial stress is making me feel hopeless.",
    "I am dealing with both academic exhaustion from late-night studying and emotional distress from relationship conflicts.",
    "My daily life is a struggle right now because of university exam competition and personal family drama happening simultaneously.",
    "I feel paralyzed by academic pressure while simultaneously fighting depression and loneliness in my personal life.",
    "Balancing part-time job hours to solve financial problems while preparing for {num} university exams is burning me out completely.",
    "I experience constant physical symptoms of stress from coursework deadlines combined with emotional anxiety about my future and relationships."
]

CALM_TEMPLATES = [
    "I completed my {subject} assignment early today and enjoyed a nice relaxing dinner with my friends.",
    "My study schedule is well organized and I feel confident about my upcoming lectures and coursework progress.",
    "I had a great balance today between studying for my classes and spending quality time exercising and relaxing.",
    "I feel calm and motivated about my academic journey, and my personal relationships are very supportive.",
    "Everything is going smoothly with my semester projects and I slept a restful eight hours last night.",
    "I attended all my university lectures today and understood the concepts clearly without any anxiety.",
    "My friends and family have been very encouraging, which helps me stay positive and focused on my goals.",
    "I took a helpful walk after finishing my homework and feel refreshed and mentally balanced.",
    "I am enjoying the topics discussed in my {subject} class and feel prepared for upcoming assessments.",
    "My daily routine is healthy, allowing me to manage my workload effectively while keeping my mental peace."
]

SUBJECTS = ["Computer Science", "Data Structures", "Machine Learning", "Mathematics", "Software Engineering", "Physics", "Thermodynamics", "Digital Logic", "Operating Systems", "Algorithms"]

def calculate_first_person_pronoun_ratio(text):
    words = text.lower().split()
    if not words:
        return 0.0
    first_person_words = {"i", "me", "my", "mine", "myself", "we", "our", "us"}
    count = sum(1 for w in words if w in first_person_words)
    return round(count / len(words), 4)

def calculate_negative_word_density(text):
    words = text.lower().split()
    if not words:
        return 0.0
    neg_words = {"stress", "stressed", "overwhelmed", "anxiety", "anxious", "depressed", "depression", "fear", "terrified", "hopeless", "lonely", "isolation", "panic", "fatigue", "falling", "failing", "pain", "sadness", "emptiness", "burnout"}
    count = sum(1 for w in words if w in neg_words)
    return round(count / len(words), 4)

def generate_dataset(total_samples=1500):
    print(f"Generating synthetic/curated student mental health text dataset ({total_samples} samples)...")
    data = []
    
    samples_per_cat = total_samples // 4
    
    # Helper to randomize templates
    def build_samples(templates, label, count):
        cat_data = []
        for _ in range(count):
            tpl = random.choice(templates)
            subj = random.choice(SUBJECTS)
            num = random.randint(2, 5)
            text = tpl.format(subject=subj, num=num)
            
            # Add slight random variations/modifiers to ensure vocabulary richness
            modifiers = [
                "",
                " Honestly, it is very hard to cope right now.",
                " I don't know what to do next.",
                " It has been like this for several weeks.",
                " I really need some advice or support.",
                " My daily focus has dropped significantly.",
                " I hope things improve soon."
            ] if label != "Calm / Normal" else [
                "",
                " Looking forward to a productive week ahead.",
                " I am grateful for the balance.",
                " Feeling very peaceful right now.",
                " It feels good to stay organized."
            ]
            text += random.choice(modifiers)
            
            # Compute linguistic metadata
            fp_ratio = calculate_first_person_pronoun_ratio(text)
            neg_density = calculate_negative_word_density(text)
            word_count = len(text.split())
            
            cat_data.append({
                "text": text,
                "category": label,
                "first_person_ratio": fp_ratio,
                "negative_word_density": neg_density,
                "word_count": word_count
            })
        return cat_data

    data.extend(build_samples(ACADEMIC_TEMPLATES, "Academic Stress", samples_per_cat))
    data.extend(build_samples(NON_ACADEMIC_TEMPLATES, "Non-Academic Stress", samples_per_cat))
    data.extend(build_samples(MIXED_TEMPLATES, "Mixed Stress", samples_per_cat))
    data.extend(build_samples(CALM_TEMPLATES, "Calm / Normal", total_samples - len(data)))
    
    # Shuffle dataset
    random.seed(42)
    random.shuffle(data)
    
    df = pd.DataFrame(data)
    os.makedirs(os.path.dirname(TEXT_DATASET_PATH), exist_ok=True)
    df.to_csv(TEXT_DATASET_PATH, index=False)
    print(f"Successfully generated {len(df)} samples and saved to {TEXT_DATASET_PATH}")
    return df

if __name__ == "__main__":
    df = generate_dataset(1500)
    print(df["category"].value_counts())
