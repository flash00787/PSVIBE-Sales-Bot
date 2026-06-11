#!/usr/bin/env node
/**
 * Kora Dashboard Server — Serves static HTML dashboard
 * Port: 9091 (configurable via PORT env)
 * Run: node kora_dashboard/server.js
 */
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 9091;
const DASHBOARD_DIR = __dirname;

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css',
  '.js': 'application/javascript',
  '.json': 'application/json',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
};

const server = http.createServer((req, res) => {
  let filePath = path.join(DASHBOARD_DIR, req.url === '/' ? 'index.html' : req.url);
  
  // Security: prevent directory traversal
  if (!filePath.startsWith(DASHBOARD_DIR)) {
    res.writeHead(403);
    return res.end('Forbidden');
  }

  const ext = path.extname(filePath);
  const contentType = MIME[ext] || 'text/plain';

  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404);
      res.end('Not Found');
      return;
    }
    res.writeHead(200, { 'Content-Type': contentType });
    res.end(data);
  });
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`🎮 Kora Dashboard running at http://0.0.0.0:${PORT}/`);
  console.log(`   Access locally: http://localhost:${PORT}/`);
  console.log(`   Press Ctrl+C to stop`);
});
