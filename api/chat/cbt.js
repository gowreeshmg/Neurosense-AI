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
            : `Act as a highly empathetic, natural human therapist having a live text conversation. 
Listen actively and explore the root causes of their emotions. 

If they give a short statement like "I am depressed", respond naturally and briefly: e.g., "I'm really sorry to hear that. What's been going on lately?"
DO NOT write a long essay. Keep responses concise (1-3 sentences) if their message is short. Only write longer responses if they give you a lot of detail.

DO NOT give pre-built or formulaic answers like "I hear that sadness is a dominant part of your experience." Read what they actually typed, and respond directly to that specific content just like a real human would.

The user's current detected emotional state is: ${current_stress_category}.

IMPORTANT RULES:
- Keep it casual, warm, and highly conversational.
- End with a simple question to keep them talking if you need more context.
- Never say "I'm just an AI".`;

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

                const geminiRes = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=${geminiKey}`, {
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
                        model: "llama3-8b-8192",
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
