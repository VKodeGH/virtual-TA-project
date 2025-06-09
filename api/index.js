const axios = require('axios');

// Load your AI Pipe key from environment variables
const AI_PIPE_KEY = process.env.AI_PIPE_KEY;

// Helper: Call the AI Pipe API
async function callAIPipe(question, context) {
  const prompt = `
You are a helpful teaching assistant for the TDS course.
Answer the following student question using the provided context from course content and Discourse posts.
If you cite any Discourse post, include the link.

Question: ${question}

Context:
${context}
  `.trim();

  const response = await axios.post(
    "https://aipipe.org/openrouter/v1/chat/completions",
    {
      model: "gpt-3.5-turbo", // or whatever model your AI Pipe supports
      messages: [
        { role: "system", content: "You are a helpful teaching assistant for the TDS course." },
        { role: "user", content: prompt }
      ],
      max_tokens: 512,
      temperature: 0.2
    },
    {
      headers: {
        "Authorization": `Bearer ${AI_PIPE_KEY}`,
        "Content-Type": "application/json"
      }
    }
  );
  return response.data.choices[0].message.content;
}

// Dummy: Load processed data (replace with real search logic if needed)
const fs = require('fs');
const path = require('path');
const processedDataPath = path.join(__dirname, '..', 'data', 'processed_data.pkl');

// For simplicity, let's load top 3 discourse links from your processed data
function getRelevantContext(question) {
  // In production, use a real search. For now, just load some context:
  // (You can improve this by porting your TF-IDF search to JS or by calling your Python logic via an HTTP API)
  return "Relevant course and discourse content here.";
}

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  if (req.method === 'POST') {
    try {
      const { question } = req.body;
      const context = getRelevantContext(question); // Replace with real context search
      const answer = await callAIPipe(question, context);

      // For now, return dummy links (replace with real relevant links)
      const links = [
        { url: "https://discourse.onlinedegree.iitm.ac.in/t/example1", text: "Example link 1" },
        { url: "https://discourse.onlinedegree.iitm.ac.in/t/example2", text: "Example link 2" }
      ];

      res.json({ answer, links });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  } else {
    res.status(405).send('Method Not Allowed');
  }
};
