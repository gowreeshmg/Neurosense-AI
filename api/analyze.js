export default async function handler(req, res) {
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    try {
        const geminiKey = process.env.GEMINI_API_KEY;
        const groqKey = process.env.GROQ_API_KEY;

        const { data } = req.body;
        if (!data || !data[0]) {
            return res.status(400).json({ error: 'No data provided' });
        }

        const input = data[0];
        let textToAnalyze = "";
        let hasAudio = false;

        // Check if audio (base64)
        if (typeof input === 'object' && input.data) {
            hasAudio = true;
            if (!groqKey) {
                return res.status(500).json({ error: "Groq API key is required for audio transcription." });
            }

            // Convert base64 audio data to Buffer
            let base64String = input.data;
            if (base64String.includes('base64,')) {
                base64String = base64String.split('base64,')[1];
            }
            const buffer = Buffer.from(base64String, 'base64');

            // Construct FormData for Groq Whisper
            const formData = new FormData();
            const blob = new Blob([buffer], { type: 'audio/webm' }); 
            formData.append('file', blob, 'audio.webm');
            formData.append('model', 'whisper-large-v3');

            const groqRes = await fetch('https://api.groq.com/openai/v1/audio/transcriptions', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${groqKey}`
                },
                body: formData
            });

            if (!groqRes.ok) {
                const errText = await groqRes.text();
                throw new Error("Groq Whisper error: " + errText);
            }

            const groqData = await groqRes.json();
            textToAnalyze = groqData.text;
        } else if (typeof input === 'string') {
            textToAnalyze = input;
        }

        if (!textToAnalyze) {
            return res.status(400).json({ error: 'Failed to extract text for analysis.' });
        }

        // Now we use Groq/Gemini to analyze the text and return the JSON
        const prompt = `You are a clinical AI. Analyze this patient narrative: "${textToAnalyze}".
Identify if there are signs of Stress, Anxiety, Depression, Emotional Distress, or if it is Normal/Calm.
Return ONLY a valid JSON object matching this schema exactly:
{
  "modality_status": "${hasAudio ? 'Dual-Modality (Text + Speech)' : 'Single-Modality (Text Only)'}",
  "combined_stress_score": <number 0-100 based on severity>,
  "final_stress_category": "<Anxiety|Depression|Stress|Emotional Distress|Normal>",
  "risk_tier": "<Anxiety|Depression|Stress|Emotional Distress|Normal>",
  "color_code": "<red|orange|blue|green>",
  "action_summary": "<1 sentence summary of detected symptoms and recommendations>",
  "fusion_weights": { "text_weight": 0.6, "audio_weight": 0.4 },
  "text_analysis": { "predicted_category": "<category>", "linguistic_stress_score": <score>, "metadata": { "word_count": ${textToAnalyze.split(' ').length}, "first_person_ratio": 0.1 } },
  "audio_analysis": ${hasAudio ? '{ "predicted_emotion": "<emotion>", "acoustic_stress_score": <score> }' : 'null'},
  "text_xai": { "predicted_category": "<category>", "html_highlighted": "<the narrative text, but wrap high stress words in <span class='xai-word xai-high-stress'>word</span>>" },
  "cbt_intervention": {
    "greeting": "NeuroSense CBT Empathy Assistant",
    "empathetic_validation": "<warm validation>",
    "recommended_exercise": "<name of grounding exercise>",
    "exercise_details": "<short description>",
    "coping_strategy": "<actionable step>"
  },
  "gemini_evaluation": {
    "clinical_tier": "<category>",
    "detected_symptoms": ["<symptom1>", "<symptom2>"]
  }
}`;

        let jsonResult = null;

        if (geminiKey) {
            const llmRes = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${geminiKey}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    contents: [{ parts: [{ text: prompt }] }],
                    generationConfig: { responseMimeType: "application/json" }
                })
            });
            const llmData = await llmRes.json();
            const textContent = llmData.candidates[0].content.parts[0].text;
            jsonResult = JSON.parse(textContent);
        } else if (groqKey) {
            const llmRes = await fetch('https://api.groq.com/openai/v1/chat/completions', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${groqKey}`, 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    model: 'llama-3.3-70b-versatile',
                    response_format: { type: "json_object" },
                    messages: [{ role: 'system', content: prompt }]
                })
            });
            const llmData = await llmRes.json();
            jsonResult = JSON.parse(llmData.choices[0].message.content);
        }

        if (!jsonResult) {
            throw new Error("Failed to generate analysis");
        }

        return res.status(200).json({
            data: [{
                fusion_result: jsonResult,
                transcription: { text: textToAnalyze }
            }]
        });

    } catch (err) {
        console.error("Analyze Error:", err);
        return res.status(500).json({ error: err.message });
    }
}
