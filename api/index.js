const express = require('express');
const cors = require('cors');
const axios = require('axios');
const fs = require('fs');
const path = require('path');
const app = express();

app.use(cors());
app.use(express.json());

const AI_PIPE_KEY = process.env.AI_PIPE_KEY;
const contextSnippets = JSON.parse(
  fs.readFileSync(path.join(__dirname, '..', 'data', 'context_snippets.json'), 'utf-8')
);

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
        timeout: 10000 // 10-second timeout
      }
    );
    return response.data.choices[0].message.content;
  } catch (error) {
    console.error("AI Pipe Error:", error.response?.data || error.message);
    throw error;
  }
}

app.post('/api', async (req, res) => {
  try {
    const { question } = req.body;
    console.log("Received question:", question);

    // Find context
    const matchedQuestion = contextSnippets.find(q => 
      question.toLowerCase().includes(q.question.toLowerCase())
    );
    const context = matchedQuestion ? matchedQuestion.contexts.join('\n') : '';
    console.log("Matched context:", context);

    // Call AI Pipe
    const answer = await callAIPipe(question, context);
    console.log("Generated answer:", answer);

    // Extract links
    const urlRegex = /https?:\/\/[^\s)]+/g;
    const urls = context.match(urlRegex) || [];
    const links = urls.slice(0, 3).map(url => ({ url, text: "Relevant discussion" }));
    console.log("Links extracted:", links);

    res.json({ answer, links });
  } catch (error) {
    console.error("Full error:", error);
    res.status(500).json({ 
      error: "Failed to generate answer",
      details: error.message 
    });
  }
});


module.exports = app;
