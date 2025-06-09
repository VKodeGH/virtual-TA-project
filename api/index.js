const express = require('express');
const cors = require('cors');
const axios = require('axios');
const app = express();

app.use(cors());
app.use(express.json());

const AI_PIPE_KEY = process.env.AI_PIPE_KEY;

// Dummy context: a relevant excerpt from your course or Discourse data
const dummyContext = `
Course content: To calculate token costs for GPT-3.5-turbo, count the number of tokens in your text and multiply by the rate per 1,000 tokens.
Discourse post: "You just have to use a tokenizer, similar to what Prof. Anand used, to get the number of tokens and multiply that by the given rate." (https://discourse.onlinedegree.iitm.ac.in/t/ga5-question-8-clarification/155939/3)
`;

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
      model: "gpt-3.5-turbo",
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

app.post('/api', async (req, res) => {
  try {
    const { question } = req.body;
    const answer = await callAIPipe(question, dummyContext);

    const links = [
      {
        url: "https://discourse.onlinedegree.iitm.ac.in/t/ga5-question-8-clarification/155939/3",
        text: "Discourse discussion on token counting"
      }
    ];

    res.json({ answer, links });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = app;
