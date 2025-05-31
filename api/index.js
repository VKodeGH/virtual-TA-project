const express = require('express');
const cors = require('cors');
const app = express();

// Enable CORS for all routes
app.use(cors());

// Handle POST requests
app.post('/api', (req, res) => {
  res.json({
    answer: "This is a placeholder response. The actual project is under development.",
    links: []
  });
});

// Export for Vercel
module.exports = app;
