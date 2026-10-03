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

  const systemPrompt = `You are an expert clinical psychologist AI specializing in cognitive-behavioral text analysis. You must classify text into EXACTLY ONE of these 5 categories based on strict clinical criteria:

CLASSIFICATION RULES (follow these STRICTLY):

1. "Normal" (score 0-20): Calm, positive, or neutral everyday statements.
2. "Stress" (score 30-55): Frustration about external factors: work, exams, deadlines, being busy, overloaded.
3. "Anxiety" (score 40-65): Fear of the future, nervousness, "what if", panic, racing thoughts.
4. "Depression" (score 50-75): Total loss of interest in life, saying life is pointless, wanting to sleep forever, feeling completely empty and numb.
5. "Emotional Distress" (score 60-85): Intense immediate pain, feeling lonely, isolated, misunderstood, overwhelmed by feelings, crying, disconnected from family/friends.

CRITICAL INSTRUCTION FOR EMOTIONAL DISTRESS vs DEPRESSION:
If the text talks about feeling "disconnected", "lonely", "indifferent in a crowded room", "isolated", or "can't cope with these emotions" -> YOU MUST CLASSIFY AS "Emotional Distress". 
Only classify as "Depression" if they explicitly talk about life having no point, total numbness, or extreme lethargy.

Return ONLY a valid JSON object with this exact structure:
{
  "combined_stress_score": <integer 0-100>,
  "text_score": <integer 0-100, optional, provide if evaluating multiple modalities>,
  "audio_score": <integer 0-100, optional, provide if evaluating multiple modalities>,
  "predicted_category": "<exactly one of: Normal, Stress, Anxiety, Depression, Emotional Distress>",
  "risk_tier": "<same as predicted_category>",
  "final_stress_category": "<same as predicted_category>",
  "text_highlights": [
    {"word": "<key word from text>", "weight": <float -1 to 1, positive=negative emotion, negative=positive>}
  ],
  "cognitive_distortion": "<a short name of a cognitive distortion found in the text (e.g. Catastrophizing, Emotional Reasoning, Overgeneralization). If the category is anything other than Normal, you MUST provide a distortion name. Do NOT output Healthy unless category is Normal>",
  "reframed_sentence_text": "<a single sentence rewriting the NARRATIVE TEXT to be completely neutral, calm, and free of any anxiety. Strip away all descriptions of panic or physical stress symptoms. State only the objective facts in a normal, relaxed tone. DO NOT add advice. RETURN ONLY THE REWRITTEN SENTENCE.>",
  "reframed_sentence_audio": "<a single sentence rewriting the VOICE TRANSCRIPTION to be completely neutral, calm, and free of any anxiety. Strip away all descriptions of panic or physical stress symptoms. State only the objective facts in a normal, relaxed tone. DO NOT add advice. RETURN ONLY THE REWRITTEN SENTENCE. (only if voice transcription provided)>"
}
Include 4-8 key words in text_highlights. Ensure text_score and audio_score are populated if analyzing both. Always provide a reframed_sentence_text.`;

  let resultJson = null;
  let geminiErrString = "Key not provided";
  let groqErrString = "Key not provided";

  // ===== TRY GEMINI FIRST =====
  if (geminiKey) {
      try {
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 4500);

          const geminiRes = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key=${geminiKey}`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                  contents: [
                      { role: 'user', parts: [{ text: systemPrompt + "\n\nText to analyze:\n\"" + text + "\"" }] }
                  ],
                  generationConfig: { temperature: 0.05, responseMimeType: "application/json" }
              }),
              signal: controller.signal
          });
          
          clearTimeout(timeoutId);

          if (geminiRes.ok) {
              const data = await geminiRes.json();
              if (data.candidates && data.candidates[0] && data.candidates[0].content && data.candidates[0].content.parts) {
                  let textResponse = data.candidates[0].content.parts[0].text;
                  try {
                      textResponse = textResponse.replace(/^```json/g, '').replace(/^```/g, '').replace(/```$/g, '').trim();
                      resultJson = JSON.parse(textResponse);
                  } catch(e) {
                      console.warn("Failed to parse Gemini JSON:", e); geminiErrString = "JSON Parse Error: " + e.message;
                  }
              }
          } else {
              const errText = await geminiRes.text(); geminiErrString = errText;
              console.warn("Gemini API Error:", geminiRes.status, errText);
          }
      } catch (err) {
          geminiErrString = err.message; console.warn("Gemini failed, falling back to Groq:", err.message);
      }
  }

  // ===== FALLBACK TO GROQ =====
  if (!resultJson && groqKey) {
      try {
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 4500);

          const groqRes = await fetch("https://api.groq.com/openai/v1/chat/completions", {
              method: "POST",
              headers: {
                  "Authorization": `Bearer ${groqKey}`,
                  "Content-Type": "application/json"
              },
              body: JSON.stringify({
                  model: "qwen/qwen3.8-27b",
                  messages: [
                      { role: "system", content: systemPrompt },
                      { role: "user", content: "Text to analyze:\n\"" + text + "\"" }
                  ],
                  temperature: 0.05,
                  response_format: { type: "json_object" }
              }),
              signal: controller.signal
          });
          
          clearTimeout(timeoutId);

          if (groqRes.ok) {
              const data = await groqRes.json();
              if (data.choices && data.choices[0]) {
                  try {
                      let content = data.choices[0].message.content;
                      content = content.replace(/^```json/g, '').replace(/^```/g, '').replace(/```$/g, '').trim();
                      resultJson = JSON.parse(content);
                  } catch(e) {
                      console.warn("Failed to parse Groq JSON:", e); groqErrString = "JSON Parse Error: " + e.message;
                  }
              }
          } else {
              const errText = await groqRes.text(); groqErrString = errText;
              console.error("Groq API Error:", errText);
          }
      } catch (err) {
          groqErrString = err.message; console.error("Groq request failed:", err);
      }
  }

  if (resultJson) {
      if (!resultJson.final_stress_category) {
          resultJson.final_stress_category = resultJson.predicted_category || resultJson.risk_tier || "Normal";
      }
      return res.status(200).json(resultJson);
  } else {
      return res.status(502).json({ 
          error: "Failed to generate analysis from AI engines.", 
          geminiError: geminiErrString, 
          groqError: groqErrString 
      });
  }
}
