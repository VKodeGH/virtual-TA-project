const express = require('express');
const cors = require('cors');
const axios = require('axios');
const fs = require('fs');
const path = require('path');
const natural = require('natural');
const app = express();

app.use(cors());
app.use(express.json());

// 1. Load Data
const courseContent = JSON.parse(
  fs.readFileSync(path.join(__dirname, '..', 'data', 'course-content', 'course_content.json'), 'utf-8')
);
const discoursePosts = JSON.parse(
  fs.readFileSync(path.join(__dirname, '..', 'data', 'discourse-posts', 'discourse_posts.json'), 'utf-8')
);

// 2. Prepare combined documents for search
const allDocs = [
  ...courseContent.map(doc => ({
    content: doc.content,
    url: doc.url,
    source: 'course'
  })),
  ...discoursePosts.map(post => ({
    content: post.content,
    url: post.post_url,
    source: 'discourse'
  }))
];

// 3. Build TF-IDF vectorizer
const tfidf = new natural.TfIdf();
allDocs.forEach(doc => tfidf.addDocument(doc.content));

// 4. Helper: Find top N relevant docs for a question
function findRelevantDocs(question, topN = 3) {
  const scores = [];
  tfidf.tfidfs(question, (i, score) => scores.push({ i, score }));
  scores.sort((a, b) => b.score - a.score);
  return scores.slice(0, topN).map(s => allDocs[s.i]);
}

// 5. API endpoint
app.post('/api', async (req, res) => {
  try {
    const { question } = req.body;

    // Find relevant docs
    const relevantDocs = findRelevantDocs(question, 3);
    const context = relevantDocs.map(d => d.content).join('\n');

    // Extract links from relevant docs
    const links = relevantDocs
      .filter(d => d.url)
      .map(d => ({
        url: d.url,
        text: d.source === 'course' ? 'Course Material' : 'Discourse Discussion'
      }));

    // Add extra instruction for bonus questions
    const systemPrompt = question.toLowerCase().includes('bonus')
      ? 'Always return bonus scores as a numerical total (e.g., 110), not fractions. '
      : '';

    // Call AI Pipe for answer
    const response = await axios.post(
      "https://aipipe.org/openrouter/v1/chat/completions",
      {
        model: "gpt-3.5-turbo",
        messages: [
          { role: "system", content: systemPrompt + "Use the following context to answer student questions:\n" + context },
          { role: "user", content: question }
        ],
        max_tokens: 512,
        temperature: 0.1
      },
      {
        headers: {
          "Authorization": `Bearer ${process.env.AI_PIPE_KEY}`,
          "Content-Type": "application/json"
        }
      }
    );

    res.json({
      answer: response.data.choices[0].message.content,
      links: links.slice(0, 3)
    });
  } catch (error) {
    res.status(500).json({ error: "Failed to generate answer", details: error.message });
  }
});

module.exports = app;
