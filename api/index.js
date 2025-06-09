const express = require('express');
const cors = require('cors');
const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// Handle POST requests to /api
app.post('/api', (req, res) => {
  try {
    const { question } = req.body;
    res.json({
      answer: "This is a working answer!",
      links: []
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Export for Vercel (DO NOT USE app.listen())
module.exports = app;
