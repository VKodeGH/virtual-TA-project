const express = require('express');
const cors = require('cors');
const app = express();

app.use(cors());
app.use(express.json());

app.post('/api', (req, res) => {
  res.json({
    answer: "This is a working answer!",
    links: []
  });
});

module.exports = app;
