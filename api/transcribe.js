export default async function handler(req, res) {
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    try {
        const groqKey = process.env.GROQ_API_KEY;
        if (!groqKey) {
            return res.status(500).json({ error: "Groq API key is required for transcription." });
        }

        const { data } = req.body;
        if (!data) {
            return res.status(400).json({ error: 'No audio data provided' });
        }

        let base64String = data;
        if (base64String.includes('base64,')) {
            base64String = base64String.split('base64,')[1];
        }
        const buffer = Buffer.from(base64String, 'base64');

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
        return res.status(200).json({ text: groqData.text });

    } catch (err) {
        console.error("Transcription Error:", err);
        return res.status(500).json({ error: err.message });
    }
}
