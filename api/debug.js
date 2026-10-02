export default async function handler(req, res) {
    const geminiKey = process.env.GEMINI_API_KEY;
    const groqKey = process.env.GROQ_API_KEY;
    
    const results = {
        gemini_key_exists: !!geminiKey,
        gemini_key_length: geminiKey ? geminiKey.length : 0,
        gemini_key_prefix: geminiKey ? geminiKey.substring(0, 6) + "..." : "MISSING",
        groq_key_exists: !!groqKey,
        groq_key_length: groqKey ? groqKey.length : 0,
        groq_key_prefix: groqKey ? groqKey.substring(0, 6) + "..." : "MISSING",
        tests: {}
    };

    // Test 1: List Groq models
    if (groqKey) {
        try {
            const modelsRes = await fetch("https://api.groq.com/openai/v1/models", {
                headers: { "Authorization": `Bearer ${groqKey}` }
            });
            if (modelsRes.ok) {
                const data = await modelsRes.json();
                results.tests.groq_models = data.data ? data.data.map(m => m.id).sort() : "No models found";
            } else {
                const err = await modelsRes.text();
                results.tests.groq_models_error = `${modelsRes.status}: ${err}`;
            }
        } catch (e) {
            results.tests.groq_models_error = e.message;
        }
    }

    // Test 2: Try Gemini with a simple prompt
    if (geminiKey) {
        try {
            const gemRes = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${geminiKey}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    contents: [{ role: 'user', parts: [{ text: 'Say hello in one word' }] }],
                    generationConfig: { maxOutputTokens: 10 }
                })
            });
            if (gemRes.ok) {
                const data = await gemRes.json();
                results.tests.gemini_test = data.candidates?.[0]?.content?.parts?.[0]?.text || "OK but no text";
            } else {
                const err = await gemRes.text();
                results.tests.gemini_error = `${gemRes.status}: ${err.substring(0, 500)}`;
            }
        } catch (e) {
            results.tests.gemini_error = e.message;
        }
    }

    return res.status(200).json(results);
}
