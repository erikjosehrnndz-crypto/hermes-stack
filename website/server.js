// server.js
const express = require('express');
const path = require('path');
const fs = require('fs');
const app = express();
const PORT = process.env.PORT || 3000;

// Serve static assets built by Vite
app.use(express.static(path.join(__dirname, 'dist')));

// API: Return directory tree of /root (limited depth for security)
app.get('/api/tree', (req, res) => {
  const basePath = '/host-root';
  function walk(dir, depth) {
    if (depth > 3) return [];
    const entries = [];
    try {
      const items = fs.readdirSync(dir, { withFileTypes: true });
      for (const item of items) {
        // ignore hidden .git, .env, .gemini, etc.
        if (item.name.startsWith('.')) continue;
        const fullPath = path.join(dir, item.name);
        if (item.isDirectory()) {
          entries.push({
            name: item.name,
            type: 'directory',
            children: walk(fullPath, depth + 1),
          });
        } else {
          entries.push({ name: item.name, type: 'file' });
        }
      }
    } catch (e) {
      // ignore permission errors
    }
    return entries;
  }
  const tree = walk(basePath, 0);
  res.json(tree);
});

// Health endpoint for sub‑agent monitoring
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: Date.now() });
});

// Fallback to index.html for SPA routes
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Hermes website listening on port ${PORT}`);
});
