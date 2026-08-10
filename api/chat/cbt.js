export default async function handler(req, res) {
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    try {
        const geminiKey = process.env.GEMINI_API_KEY;
        const groqKey = process.env.GROQ_API_KEY;
        
        if (!geminiKey && !groqKey) {
            console.error("No API keys configured.");
            return res.status(500).json({ error: "API key is missing. Please add GEMINI_API_KEY or GROQ_API_KEY in Vercel environment variables." });
        }

        const { message, current_stress_category, history } = req.body;

        if (!message) {
            return res.status(400).json({ error: 'Message is required' });
        }

        const systemPrompt = `You are NeuroSense GPT, an empathetic AI Cognitive Behavioral Therapy (CBT) assistant. The user's current detected stress state is: ${current_stress_category}. Your goal is to actively help them manage their stress. First, provide a warm, empathetic acknowledgment of their feelings. Then, ALWAYS provide specific, actionable ways to help solve or manage their stress (such as a CBT reframing exercise, a grounding technique, or a practical coping strategy). Keep your responses structured, highly actionable, and extremely helpful. Do not give medical advice. Provide a moderately detailed response (3 to 5 sentences).`;

        let reply = "I'm sorry, I couldn't generate a response at this time.";
        let geminiSuccess = false;

        // Try Gemini First if key is available
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
                    { role: 'user', parts: [{ text: "System prompt: " + systemPrompt }] },
                    { role: 'model', parts: [{ text: "Understood. I will act as NeuroSense GPT, an empathetic CBT assistant." }] }
                );

                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout

                const geminiRes = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${geminiKey}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        contents: formattedHistory,
                        generationConfig: { temperature: 0.7, maxOutputTokens: 250 }
                    }),
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);

                if (geminiRes.ok) {
                    const data = await geminiRes.json();
                    if (data.candidates && data.candidates[0] && data.candidates[0].content && data.candidates[0].content.parts) {
                        reply = data.candidates[0].content.parts[0].text;
                        geminiSuccess = true;
                    }
                } else {
                    console.warn("Gemini API Error or Rate Limit, falling back to Groq...");
                }
            } catch (err) {
                console.warn("Gemini request failed (timeout/network), falling back to Groq...", err.message);
            }
        }

        // Fallback to Groq if Gemini failed or isn't available
        if (!geminiSuccess && groqKey) {
            try {
                let groqHistory = [
                    { role: "system", content: systemPrompt }
                ];
                if (history && Array.isArray(history)) {
                    history.forEach(msg => {
                        groqHistory.push({ role: msg.role === 'assistant' ? 'assistant' : 'user', content: msg.content });
                    });
                }
                groqHistory.push({ role: "user", content: message });

                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout

                const groqRes = await fetch("https://api.groq.com/openai/v1/chat/completions", {
                    method: "POST",
                    headers: {
                        "Authorization": `Bearer ${groqKey}`,
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        model: "llama-3.3-70b-versatile", // Use active Llama 3.3 model
                        messages: groqHistory,
                        temperature: 0.7,
                        max_tokens: 250
                    }),
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);

                if (!groqRes.ok) {
                    const errData = await groqRes.text();
                    console.error("Groq API Error:", errData);
                    let parsedErr = "Failed to fetch response from Groq Llama AI.";
                    try {
                        const j = JSON.parse(errData);
                        if (j.error && j.error.message) parsedErr = "Groq: " + j.error.message;
                    } catch(e) { parsedErr = "Groq: " + errData; }
                    return res.status(502).json({ error: parsedErr });
                }

                const data = await groqRes.json();
                if (data.choices && data.choices[0]) {
                    reply = data.choices[0].message.content;
                }
            } catch (err) {
                console.error("Groq request failed:", err);
                return res.status(502).json({ error: "Failed to fetch response from Groq Llama AI." });
            }
        } else if (!geminiSuccess && !groqKey) {
            return res.status(502).json({ error: "Gemini API failed/timed out and no Groq API key is available for fallback." });
        }

        return res.status(200).json({ reply });

    } catch (error) {
        console.error("Serverless Function Error:", error);
        return res.status(500).json({ error: 'Internal Server Error' });
    }
}
