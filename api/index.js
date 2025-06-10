const express = require('express');
const cors = require('cors');
const axios = require('axios');
const fs = require('fs');
const path = require('path');
const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// Load your AI Pipe key from Vercel environment variables
const AI_PIPE_KEY = process.env.AI_PIPE_KEY;

// Load your pre-generated context snippets
const contextSnippetsPath = path.join(__dirname, '..', 'data', 'context_snippets.json');
const contextSnippets = JSON.parse(fs.readFileSync(contextSnippetsPath, 'utf-8'));

// Find the best context for a given question
function findContext(question) {
  const matched = contextSnippets.find(q => 
    question.toLowerCase().includes(q.question.toLowerCase())
  );
  return matched ? matched.contexts.join('\n') : '';
}

// Call the AI Pipe API with the question and context
async function callAIPipe(question, context) {
  const response = await axios.post(
    "https://aipipe.org/openrouter/v1/chat/completions",
    {
      model: "gpt-3.5-turbo",
      messages: [
        { role: "system", content: "You are a helpful TDS course TA. Answer using the context." },
        { role: "user", content: `Question: ${question}\nContext: ${context}` }
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

// Handle POST requests to /api
app.post('/api', async (req, res) => {
  try {
    const { question } = req.body;
    
    // Step 1: Get relevant context for the question
    const context = findContext(question);
    
    // Step 2: Generate answer using AI Pipe
    const answer = await callAIPipe(question, context);
    
    // Step 3: Extract links from the context
    const links = [];
    const urlRegex = /https?:\/\/[^\s)]+/g;
    const urls = context.match(urlRegex) || [];
    urls.forEach(url => {
      links.push({ url, text: "Relevant discussion" });
    });

    res.json({ answer, links: links.slice(0, 3) }); // Return top 3 links
  } catch (error) {
  console.error("API Error:", error.response?.data || error.message);
  res.status(500).json({ 
    error: "Failed to generate answer",
    details: error.response?.data || error.message 
  });
}
});

// Export for Vercel
module.exports = app;
