const express = require('express');
const cors = require('cors');
const axios = require('axios');
const fs = require('fs');
const path = require('path');
const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// Load environment variables
const AI_PIPE_KEY = process.env.AI_PIPE_KEY;

// Load context snippets
const contextSnippetsPath = path.join(__dirname, '..', 'data', 'context_snippets.json');
const contextSnippets = JSON.parse(fs.readFileSync(contextSnippetsPath, 'utf-8'));

// Generate answer using AI Pipe
async function callAIPipe(question, context) {
  try {
    const response = await axios.post(
      "https://aipipe.org/openrouter/v1/chat/completions",
      {
        model: "gpt-3.5-turbo",
        messages: [
          { role: "system", content: "You are a helpful TDS course TA." },
          { role: "user", content: `Question: ${question}\nContext: ${context}` }
        ],
        max_tokens: 512,
        temperature: 0.2
      },
      {
        headers: {
          "Authorization": `Bearer ${AI_PIPE_KEY}`,
          "Content-Type": "application/json"
        },
        timeout: 10000
      }
    );
    return response.data.choices[0].message.content;
  } catch (error) {
    console.error("AI Pipe Error:", error.response?.data || error.message);
    throw error;
  }
}

// Handle POST requests
app.post('/api', async (req, res) => {
  try {
    const { question } = req.body;
    
    // Find matching context
    const matched = contextSnippets.find(q => 
      question.toLowerCase().includes(q.question.toLowerCase())
    );
    const context = matched ? matched.contexts.join('\n') : '';
    
    // Generate answer
    const answer = await callAIPipe(question, context);
    
    // Extract links
    const links = [];
    const urlRegex = /https?:\/\/[^\s)]+/g;
    const urls = context.match(urlRegex) || [];
    urls.forEach(url => links.push({ url, text: "Relevant discussion" }));
    
    res.json({ answer, links: links.slice(0, 3) });
  } catch (error) {
    res.status(500).json({ 
      error: "Failed to generate answer",
      details: error.message 
    });
  }
});

// Export for Vercel
module.exports = app;
