export default async function handler(req, res) {
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    try {
        const groqKey = process.env.GROQ_API_KEY;
        if (!groqKey) {
            return res.status(500).json({ error: 'GROQ_API_KEY not configured' });
        }

        const { audio, mimeType } = req.body;
        if (!audio) {
            return res.status(400).json({ error: 'No audio data provided' });
        }

        // Convert base64 to binary buffer
        const audioBuffer = Buffer.from(audio.replace(/^data:[^;]+;base64,/, ''), 'base64');

        // Determine file extension from mime type
        const ext = (mimeType || 'audio/webm').includes('mp3') ? 'mp3'
                  : (mimeType || '').includes('mp4') ? 'mp4'
                  : (mimeType || '').includes('wav') ? 'wav'
                  : (mimeType || '').includes('ogg') ? 'ogg'
                  : 'webm';

        // Build multipart form for Groq Whisper API
        const formData = new FormData();
        const audioBlob = new Blob([audioBuffer], { type: mimeType || 'audio/webm' });
        formData.append('file', audioBlob, `audio.${ext}`);
        formData.append('model', 'whisper-large-v3');
        formData.append('response_format', 'json');
        formData.append('language', 'en');

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 25000); // 25s timeout

        const groqRes = await fetch('https://api.groq.com/openai/v1/audio/transcriptions', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${groqKey}`
                // Do NOT set Content-Type — let fetch set it with the boundary for multipart
            },
            body: formData,
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!groqRes.ok) {
            const errText = await groqRes.text();
            console.error('Groq Whisper error:', errText);
            return res.status(502).json({ error: 'Groq Whisper transcription failed', details: errText });
        }

        const data = await groqRes.json();
        const transcribedText = data.text || '';

        return res.status(200).json({ text: transcribedText, transcription: transcribedText });

    } catch (error) {
        if (error.name === 'AbortError') {
            return res.status(504).json({ error: 'Transcription timed out' });
        }
        console.error('Transcribe API error:', error);
        return res.status(500).json({ error: 'Internal server error', details: error.message });
    }
}
