export default async function handler(req, res) {
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    try {
        const geminiKey = process.env.GEMINI_API_KEY;
        const groqKey = process.env.GROQ_API_KEY;
        
        if (!geminiKey && !groqKey) {
            return res.status(500).json({ error: "API key is missing. Please add GEMINI_API_KEY or GROQ_API_KEY in Vercel environment variables." });
        }

        const { message, current_stress_category, history, is_reframe } = req.body;

        if (!message) {
            return res.status(400).json({ error: 'Message is required' });
        }

        const systemPrompt = is_reframe 
            ? `You are a clinical psychologist AI. Reframe the following sentence into a healthier, grounded cognitive perspective, resolving any cognitive distortions. Return ONLY the reframed sentence. No conversational intro, no quotes, just the sentence.`
            : `You are Dr. Neuro, a warm, empathetic, and highly experienced clinical psychologist who specializes in Cognitive Behavioral Therapy (CBT). You have 20 years of experience helping students and young adults.

Your therapeutic approach:
1. ALWAYS acknowledge and validate the person's feelings first with genuine warmth
2. Ask thoughtful, open-ended exploratory questions to understand the ROOT CAUSE (e.g., "What do you think triggered this feeling?", "When did you first start feeling this way?", "Can you walk me through what happened?")
3. Do NOT give solutions immediately - first understand the full picture through 2-3 exchanges
4. After understanding the situation, suggest specific CBT techniques like:
   - Cognitive restructuring (identifying and challenging negative thoughts)
   - Grounding exercises (5-4-3-2-1 technique)
   - Behavioral activation (small, achievable activities)
   - Journaling prompts
   - Breathing techniques
5. Use a conversational, caring tone as if talking face-to-face
6. Remember context from previous messages in the conversation

The user's current detected emotional state is: ${current_stress_category}.

IMPORTANT RULES:
- Keep responses 3-5 sentences long, never shorter
- Always end with either a question or a gentle suggestion
- Never say "I'm just an AI" or similar disclaimers
- Never give medical or medication advice
- Be warm and human-like, not clinical or robotic`;

        let reply = null;

        // ===== TRY GEMINI FIRST =====
        if (geminiKey) {
            try {
                let formattedHistory = [];
                if (history && Array.isArray(history)) {
                    formattedHistory = history.map(msg => ({
                        role: msg.role === 'assistant' ? 'model' : 'user',
                        parts: [{ text: msg.content }]
                    }));
                }
                formattedHistory.push({ role: 'user', parts: [{ text: message }] });
                formattedHistory.unshift(
                    { role: 'user', parts: [{ text: systemPrompt }] },
                    { role: 'model', parts: [{ text: "I understand. I'm Dr. Neuro, ready to listen and support you through whatever you're going through. I'll take my time to really understand your situation before suggesting anything." }] }
                );

                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 12000);

                const geminiRes = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key=${geminiKey}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        contents: formattedHistory,
                        generationConfig: { temperature: 0.8, maxOutputTokens: 500 }
                    }),
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);

                if (geminiRes.ok) {
                    const data = await geminiRes.json();
                    if (data.candidates && data.candidates[0] && data.candidates[0].content && data.candidates[0].content.parts) {
                        reply = data.candidates[0].content.parts[0].text;
                    }
                } else {
                    const errText = await geminiRes.text();
                    console.warn("Gemini API Error:", geminiRes.status, errText);
                }
            } catch (err) {
                console.warn("Gemini failed, falling back to Groq:", err.message);
            }
        }

        // ===== FALLBACK TO GROQ =====
        if (!reply && groqKey) {
            try {
                let groqHistory = [{ role: "system", content: systemPrompt }];
                if (history && Array.isArray(history)) {
                    history.forEach(msg => {
                        groqHistory.push({ role: msg.role === 'assistant' ? 'assistant' : 'user', content: msg.content });
                    });
                }
                groqHistory.push({ role: "user", content: message });

                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 20000);

                const groqRes = await fetch("https://api.groq.com/openai/v1/chat/completions", {
                    method: "POST",
                    headers: {
                        "Authorization": `Bearer ${groqKey}`,
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        model: "qwen/qwen3.8-27b",
                        messages: groqHistory,
                        temperature: 0.8,
                        max_tokens: 500
                    }),
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);

                if (!groqRes.ok) {
                    const errData = await groqRes.text();
                    console.error("Groq API Error:", errData);
                    return res.status(502).json({ error: "Groq AI Error: " + errData });
                }

                const data = await groqRes.json();
                if (data.choices && data.choices[0]) {
                    reply = data.choices[0].message.content;
                }
            } catch (err) {
                console.error("Groq request failed:", err);
                return res.status(502).json({ error: "Groq AI connection timed out." });
            }
        }

        if (!reply) {
            return res.status(502).json({ error: "Both Gemini and Groq failed to generate a response." });
        }

        return res.status(200).json({ reply });

    } catch (error) {
        console.error("Serverless Function Error:", error);
        return res.status(500).json({ error: 'Internal Server Error' });
    }
}
