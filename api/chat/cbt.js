export default async function handler(req, res) {
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    try {
        const apiKey = process.env.GEMINI_API_KEY;
        
        if (!apiKey) {
            console.error("GEMINI_API_KEY is not configured.");
            return res.status(500).json({ error: "API key is missing in Vercel environment variables." });
        }

        const { message, current_stress_category, history } = req.body;

        if (!message) {
            return res.status(400).json({ error: 'Message is required' });
        }

        // Format history for Gemini API
        // Gemini expects: { "role": "user" | "model", "parts": [{ "text": "..." }] }
        let formattedHistory = [];
        if (history && Array.isArray(history)) {
            formattedHistory = history.map(msg => ({
                role: msg.role === 'assistant' ? 'model' : 'user',
                parts: [{ text: msg.content }]
            }));
        }

        // Add the current user message
        formattedHistory.push({
            role: 'user',
            parts: [{ text: message }]
        });

        // Add a system prompt block at the very beginning by inserting a user and model block 
        // to set the persona, since Gemini free API sometimes doesn't like systemInstructions easily via simple fetch.
        const systemPrompt = `You are NeuroSense GPT, an empathetic AI Cognitive Behavioral Therapy (CBT) assistant. The user's current detected stress state is: ${current_stress_category}. Your goal is to help them identify cognitive distortions (like catastrophizing, black-and-white thinking) and gently guide them through cognitive reframing. Keep responses concise, warm, empathetic, and actionable. Do not give medical advice. Keep responses under 3 sentences if possible.`;
        
        formattedHistory.unshift(
            { role: 'user', parts: [{ text: "System prompt: " + systemPrompt }] },
            { role: 'model', parts: [{ text: "Understood. I will act as NeuroSense GPT, an empathetic CBT assistant." }] }
        );

        const geminiRequestBody = {
            contents: formattedHistory,
            generationConfig: {
                temperature: 0.7,
                maxOutputTokens: 250,
            }
        };

        const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(geminiRequestBody)
        });

        if (!response.ok) {
            const errorData = await response.text();
            console.error("Gemini API Error:", response.status, errorData);
            return res.status(502).json({ error: "Failed to fetch response from Gemini AI." });
        }

        const data = await response.json();
        
        let reply = "I'm sorry, I couldn't generate a response at this time.";
        if (data.candidates && data.candidates[0] && data.candidates[0].content && data.candidates[0].content.parts) {
            reply = data.candidates[0].content.parts[0].text;
        }

        return res.status(200).json({ reply });

    } catch (error) {
        console.error("Serverless Function Error:", error);
        return res.status(500).json({ error: 'Internal Server Error' });
    }
}
