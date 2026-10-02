export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { text } = req.body;
  
  if (!text) {
    return res.status(400).json({ error: 'No text provided for analysis.' });
  }

  const geminiKey = process.env.GEMINI_API_KEY;
  const groqKey = process.env.GROQ_API_KEY;

  if (!geminiKey && !groqKey) {
      return res.status(500).json({ error: "API keys are missing." });
  }

  const systemPrompt = `You are a cognitive behavioral and linguistic stress analysis AI. Analyze the following text for signs of stress, anxiety, or cognitive load.
Return ONLY a valid JSON object with the following exact structure, no markdown formatting, no backticks, no other text:
{
  "combined_stress_score": <integer from 0 to 100>,
  "predicted_category": "<string: Normal, Stress, Anxiety, Depression, Emotional Distress>",
  "risk_tier": "<same as predicted_category>",
  "text_highlights": [
    {"word": "<stressed word>", "weight": <float from -1 to 1>},
    {"word": "<positive word>", "weight": <float from -1 to 1>}
  ]
}
The 'text_highlights' array should contain 3-8 key words from the text that indicate stress (positive weight) or calmness (negative weight).`;

  let resultJson = null;
  let geminiSuccess = false;

  // ===== TRY GEMINI FIRST =====
  if (geminiKey) {
      try {
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 8000); // 8s timeout

          // Use gemini-2.0-flash (gemini-1.5-flash is RETIRED as of 2026)
          const geminiRes = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${geminiKey}`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                  contents: [
                      { role: 'user', parts: [{ text: "System prompt: " + systemPrompt + "\n\nText to analyze: " + text }] }
                  ],
                  generationConfig: { temperature: 0.1, responseMimeType: "application/json" }
              }),
              signal: controller.signal
          });
          
          clearTimeout(timeoutId);

          if (geminiRes.ok) {
              const data = await geminiRes.json();
              if (data.candidates && data.candidates[0] && data.candidates[0].content && data.candidates[0].content.parts) {
                  let textResponse = data.candidates[0].content.parts[0].text;
                  try {
                      // Remove markdown code blocks if present
                      textResponse = textResponse.replace(/^```json/g, '').replace(/^```/g, '').replace(/```$/g, '').trim();
                      resultJson = JSON.parse(textResponse);
                      geminiSuccess = true;
                  } catch(e) {
                      console.warn("Failed to parse Gemini JSON:", e);
                  }
              }
          } else {
              const errText = await geminiRes.text();
              console.warn("Gemini API Error:", geminiRes.status, errText);
          }
      } catch (err) {
          console.warn("Gemini request failed (timeout/network), falling back to Groq...");
      }
  }

  // ===== FALLBACK TO GROQ =====
  if (!geminiSuccess && groqKey) {
      try {
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 15000); // 15s timeout

          const groqRes = await fetch("https://api.groq.com/openai/v1/chat/completions", {
              method: "POST",
              headers: {
                  "Authorization": `Bearer ${groqKey}`,
                  "Content-Type": "application/json"
              },
              body: JSON.stringify({
                  model: "llama-3.3-70b-versatile",
                  messages: [
                      { role: "system", content: systemPrompt },
                      { role: "user", content: "Text to analyze: " + text }
                  ],
                  temperature: 0.1,
                  response_format: { type: "json_object" }
              }),
              signal: controller.signal
          });
          
          clearTimeout(timeoutId);

          if (groqRes.ok) {
              const data = await groqRes.json();
              if (data.choices && data.choices[0]) {
                  try {
                      resultJson = JSON.parse(data.choices[0].message.content);
                  } catch(e) {
                      console.warn("Failed to parse Groq JSON:", e);
                  }
              }
          } else {
              const errText = await groqRes.text();
              console.error("Groq API Error on fallback:", errText);
          }
      } catch (err) {
          console.error("Groq request failed:", err);
      }
  }

  if (resultJson) {
      return res.status(200).json(resultJson);
  } else {
      return res.status(502).json({ error: "Failed to generate analysis from AI engines." });
  }
}
