import { client } from "@gradio/client";

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { text, audioUrl } = req.body;

  try {
    // Authenticate with the Hugging Face token from environment variables
    const hfToken = process.env.HF_TOKEN;
    if (!hfToken) {
      console.warn("HF_TOKEN environment variable is not set. Gradio client will run unauthenticated and may hit ZeroGPU limits.");
    }

    // Connect to the Hugging Face Space
    const app = await client("https://webapp1-neurosense-ai.hf.space/", { hf_token: hfToken });
    
    let result = null;

    // Handle text or multimodal analysis
    if (text && !audioUrl) {
      console.log("Running authenticated text analysis...");
      const response = await app.predict("/analyze_text", [ text ]);
      if (response && response.data && response.data[0]) {
        result = response.data[0];
      }
    } else if (audioUrl) {
      // For audio, the file might need to be fetched and sent, 
      // but Vercel limits Serverless Function payload sizes (4.5MB).
      // Since this fix is for text rate limits, we'll implement text first.
      return res.status(501).json({ error: "Audio upload via authenticated API not yet implemented." });
    }

    if (result) {
      return res.status(200).json(result);
    } else {
      return res.status(500).json({ error: "Invalid response from Gradio" });
    }

  } catch (error) {
    console.error("Authenticated Gradio API error:", error);
    
    // Check for specific ZeroGPU or quota errors
    if (error.message && (error.message.includes("quota") || error.message.includes("ZeroGPU"))) {
       return res.status(429).json({ error: "Hugging Face ZeroGPU quota exceeded. Ensure HF_TOKEN is valid." });
    }

    return res.status(500).json({ error: "Backend error", details: error.message });
  }
}
