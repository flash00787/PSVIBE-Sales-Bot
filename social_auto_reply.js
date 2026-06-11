#!/usr/bin/env node
/**
 * PS VIBE — Social Media Auto-Reply System
 * ==========================================
 * Webhook server for Facebook Messenger + Instagram messages.
 * Auto-replies using PS VIBE FAQ knowledge base with keyword matching.
 *
 * Deploy: /opt/social_auto_reply/social_auto_reply.js
 * Port:   3100
 * Service: social-auto-reply.service
 *
 * Endpoints:
 *   GET  /webhook/facebook  — Facebook webhook verification
 *   POST /webhook/facebook  — Receive messages
 *   GET  /webhook/instagram — Instagram webhook verification
 *   POST /webhook/instagram — Receive messages
 *   GET  /health            — Health check
 *   GET  /stats             — Message & response stats
 *
 * Facebook API requirements:
 *   1. Facebook Page
 *   2. Facebook Developer app (developers.facebook.com)
 *   3. App review for `pages_messaging` permission
 *   4. Page Access Token (set in .env or FB_PAGE_TOKEN env var)
 */

'use strict';

const express = require('express');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// ── Configuration ──────────────────────────────────────────────────────────
const CONFIG = {
  port: parseInt(process.env.PORT, 10) || 3100,
  host: process.env.HOST || '0.0.0.0',

  // Facebook
  fbVerifyToken: process.env.FB_VERIFY_TOKEN || 'psvibe_fb_webhook_2026',
  fbPageToken: process.env.FB_PAGE_TOKEN || '',
  fbGraphVersion: process.env.FB_GRAPH_VERSION || 'v18.0',

  // Instagram (stub — same verify token for now, extend later)
  igVerifyToken: process.env.IG_VERIFY_TOKEN || 'psvibe_ig_webhook_2026',

  // Paths
  faqPath: process.env.FAQ_PATH || path.join(__dirname, 'knowledge', 'psvibe_faq.json'),
  logDir: process.env.LOG_DIR || path.join(__dirname, 'logs'),

  // Matching
  minConfidence: 0.25,       // minimum keyword-match ratio to send a matched answer
  maxKeywordDistance: 2,     // Levenshtein distance threshold for typo tolerance
};

// ── State ──────────────────────────────────────────────────────────────────
const stats = {
  startedAt: new Date().toISOString(),
  totalMessages: 0,
  totalMatched: 0,
  totalFallback: 0,
  totalGreetings: 0,
  lastMessageAt: null,
  avgResponseMs: 0,
  _responseTimes: [],
};

let faq = null;
let faqLoadError = null;

// ── Load FAQ ───────────────────────────────────────────────────────────────
function loadFAQ() {
  try {
    if (!fs.existsSync(CONFIG.faqPath)) {
      faqLoadError = `FAQ file not found: ${CONFIG.faqPath}`;
      console.error(`[FAQ] ${faqLoadError}`);
      return false;
    }
    const raw = fs.readFileSync(CONFIG.faqPath, 'utf8');
    faq = JSON.parse(raw);
    faqLoadError = null;
    console.log(`[FAQ] Loaded "${faq.name}" — v${faq.version}, ${Object.keys(faq.categories).length} categories`);
    return true;
  } catch (e) {
    faqLoadError = `FAQ load error: ${e.message}`;
    console.error(`[FAQ] ${faqLoadError}`);
    return false;
  }
}

// ── Logging ────────────────────────────────────────────────────────────────
function ensureLogDir() {
  if (!fs.existsSync(CONFIG.logDir)) {
    fs.mkdirSync(CONFIG.logDir, { recursive: true });
  }
}

function logMessage(entry) {
  ensureLogDir();
  const dateStr = new Date().toISOString().slice(0, 10);
  const logFile = path.join(CONFIG.logDir, `messages_${dateStr}.ndjson`);

  const record = {
    timestamp: new Date().toISOString(),
    ...entry,
  };

  fs.appendFileSync(logFile, JSON.stringify(record) + '\n');
}

// ── Levenshtein Distance (for typo tolerance) ──────────────────────────────
function levenshtein(a, b) {
  if (a === b) return 0;
  const m = a.length;
  const n = b.length;
  if (m === 0) return n;
  if (n === 0) return m;

  let prev = Array.from({ length: n + 1 }, (_, i) => i);
  let curr = new Array(n + 1);

  for (let i = 1; i <= m; i++) {
    curr[0] = i;
    for (let j = 1; j <= n; j++) {
      curr[j] = Math.min(
        prev[j] + 1,
        curr[j - 1] + 1,
        prev[j - 1] + (a[i - 1] !== b[j - 1] ? 1 : 0)
      );
    }
    [prev, curr] = [curr, prev];
  }
  return prev[n];
}

// ── Normalize message for matching ─────────────────────────────────────────
function normalize(text) {
  return text
    .toLowerCase()
    .replace(/[!?။၊\s]+/g, ' ')
    .trim();
}

// ── Keyword Matching Engine ────────────────────────────────────────────────
function matchFAQ(message) {
  if (!faq) return null;

  const normalized = normalize(message);
  const words = normalized.split(' ').filter(w => w.length > 0);

  // 1. Check greetings first
  if (faq.greeting_keywords) {
    const greetWords = faq.greeting_keywords.keywords || [];
    let greetMatch = false;
    for (const kw of greetWords) {
      if (normalized.includes(normalize(kw))) {
        greetMatch = true;
        break;
      }
      // typo-tolerant
      for (const w of words) {
        if (w.length >= 3 && levenshtein(w, normalize(kw)) <= CONFIG.maxKeywordDistance) {
          greetMatch = true;
          break;
        }
      }
      if (greetMatch) break;
    }
    if (greetMatch) {
      return {
        matched: true,
        id: 'greeting',
        label: '👋 Greeting',
        answer: faq.greeting_keywords.response,
        confidence: 1.0,
      };
    }
  }

  // 2. Scan all FAQ categories
  let bestMatch = null;
  let bestConfidence = 0;

  for (const [catKey, cat] of Object.entries(faq.categories)) {
    for (const item of cat.items) {
      let keywordHits = 0;
      const keywordSet = (item.keywords || []).map(k => normalize(k));
      const patternSet = (item.patterns || []).map(p => normalize(p));

      // Match against keywords
      for (const kw of keywordSet) {
        if (kw.length === 0) continue;
        // Direct substring match
        if (normalized.includes(kw)) {
          keywordHits++;
          continue;
        }
        // Token-level typo-tolerant match
        for (const w of words) {
          if (w.length >= 3 && levenshtein(w, kw) <= CONFIG.maxKeywordDistance) {
            keywordHits += 0.8; // slightly lower confidence for fuzzy match
            break;
          }
        }
      }

      // Match against patterns (phrases)
      let patternHits = 0;
      for (const p of patternSet) {
        if (p.length === 0) continue;
        if (normalized.includes(p)) {
          patternHits++;
          continue;
        }
        // Fuzzy phrase match — check if most tokens appear nearby
        const pWords = p.split(' ').filter(w => w.length > 0);
        if (pWords.length >= 2) {
          let phraseTokenMatch = 0;
          for (const pw of pWords) {
            if (pw.length < 3) continue;
            for (const w of words) {
              if (w.length >= 3 && levenshtein(w, pw) <= CONFIG.maxKeywordDistance) {
                phraseTokenMatch++;
                break;
              }
            }
          }
          if (phraseTokenMatch >= Math.ceil(pWords.length * 0.6)) {
            patternHits += 0.7;
          }
        }
      }

      // Use incremental scoring so large keyword sets don't dilute confidence.
      // Each direct keyword match adds 0.25, each fuzzy adds ~0.20, each pattern match adds 0.30.
      // Cap at 1.0 so 4 keyword hits or 3 pattern matches = full confidence.
      const rawScore = keywordHits * 0.25 + patternHits * 0.30;
      const confidence = Math.min(rawScore, 1.0);

      if (confidence > bestConfidence && confidence >= CONFIG.minConfidence) {
        bestConfidence = confidence;
        bestMatch = {
          matched: true,
          id: item.id,
          category: catKey,
          label: cat.label,
          answer: item.answer,
          confidence: Math.round(confidence * 100) / 100,
        };
      }
    }
  }

  return bestMatch;
}

// ── Fallback response ──────────────────────────────────────────────────────
function getFallbackAnswer() {
  if (faq && faq.fallback_answers && faq.fallback_answers.length > 0) {
    const idx = Math.floor(Math.random() * faq.fallback_answers.length);
    return faq.fallback_answers[idx];
  }
  return 'ကျေးဇူးပြုပြီး PS VIBE Customer Bot (@psvibe_customer_bot) ကို /start လုပ်ပြီး အသေးစိတ်မေးမြန်းနိုင်ပါတယ်။';
}

// ── Send Facebook message via Graph API ────────────────────────────────────
async function sendFacebookReply(recipientId, text) {
  if (!CONFIG.fbPageToken) {
    console.log('[FB] No page token configured — reply not sent (dev mode)');
    logMessage({
      platform: 'facebook',
      direction: 'OUTBOUND',
      recipientId,
      text,
      status: 'NOT_SENT_NO_TOKEN',
    });
    return { ok: false, reason: 'no_token' };
  }

  const url = `https://graph.facebook.com/${CONFIG.fbGraphVersion}/me/messages?access_token=${CONFIG.fbPageToken}`;
  const body = {
    recipient: { id: recipientId },
    message: { text },
  };

  try {
    const resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await resp.json();
    logMessage({
      platform: 'facebook',
      direction: 'OUTBOUND',
      recipientId,
      text,
      status: resp.ok ? 'SENT' : 'FAILED',
      apiResponse: data,
    });
    return { ok: resp.ok, data };
  } catch (e) {
    logMessage({
      platform: 'facebook',
      direction: 'OUTBOUND',
      recipientId,
      text,
      status: 'ERROR',
      error: e.message,
    });
    return { ok: false, error: e.message };
  }
}

// ── Process incoming message ───────────────────────────────────────────────
async function processMessage(platform, senderId, messageText) {
  const startTime = Date.now();

  if (!messageText || messageText.trim().length === 0) {
    return { handled: false, reason: 'empty_message' };
  }

  stats.totalMessages++;

  // Match against FAQ
  const match = matchFAQ(messageText);

  if (match) {
    if (match.id === 'greeting') {
      stats.totalGreetings++;
    } else {
      stats.totalMatched++;
    }

    const replyText = match.answer;

    // Send reply
    if (platform === 'facebook') {
      await sendFacebookReply(senderId, replyText);
    }

    const elapsed = Date.now() - startTime;
    stats._responseTimes.push(elapsed);
    if (stats._responseTimes.length > 100) stats._responseTimes.shift();
    stats.avgResponseMs = Math.round(
      stats._responseTimes.reduce((a, b) => a + b, 0) / stats._responseTimes.length
    );
    stats.lastMessageAt = new Date().toISOString();

    logMessage({
      platform,
      direction: 'INBOUND',
      senderId,
      messageText,
      matched: true,
      faqId: match.id,
      category: match.category || 'greeting',
      confidence: match.confidence,
      replyText,
      responseMs: elapsed,
    });

    return {
      handled: true,
      matched: true,
      faqId: match.id,
      confidence: match.confidence,
      reply: replyText,
      responseMs: elapsed,
    };
  }

  // Fallback
  stats.totalFallback++;
  const fallback = getFallbackAnswer();

  if (platform === 'facebook') {
    await sendFacebookReply(senderId, fallback);
  }

  const elapsed = Date.now() - startTime;
  stats._responseTimes.push(elapsed);
  if (stats._responseTimes.length > 100) stats._responseTimes.shift();
  stats.avgResponseMs = Math.round(
    stats._responseTimes.reduce((a, b) => a + b, 0) / stats._responseTimes.length
  );
  stats.lastMessageAt = new Date().toISOString();

  logMessage({
    platform,
    direction: 'INBOUND',
    senderId,
    messageText,
    matched: false,
    replyText: fallback,
    responseMs: elapsed,
  });

  return {
    handled: true,
    matched: false,
    reply: fallback,
    responseMs: elapsed,
  };
}

// ── Express App ────────────────────────────────────────────────────────────
const app = express();

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Request logging middleware
app.use((req, _res, next) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.path}`);
  next();
});

// ── Health Check ───────────────────────────────────────────────────────────
app.get('/health', (_req, res) => {
  res.json({
    status: 'ok',
    service: 'PS VIBE Social Auto-Reply',
    version: '1.0.0',
    uptime: Math.floor((Date.now() - new Date(stats.startedAt).getTime()) / 1000),
    faqLoaded: faq !== null,
    faqError: faqLoadError,
    fbConfigured: CONFIG.fbPageToken.length > 0,
    timestamp: new Date().toISOString(),
  });
});

// ── Stats ──────────────────────────────────────────────────────────────────
app.get('/stats', (_req, res) => {
  res.json({
    service: 'PS VIBE Social Auto-Reply',
    startedAt: stats.startedAt,
    totalMessages: stats.totalMessages,
    totalMatched: stats.totalMatched,
    totalFallback: stats.totalFallback,
    totalGreetings: stats.totalGreetings,
    matchRate: stats.totalMessages > 0
      ? Math.round((stats.totalMatched / stats.totalMessages) * 100)
      : 0,
    avgResponseMs: stats.avgResponseMs,
    lastMessageAt: stats.lastMessageAt,
    faqVersion: faq ? faq.version : null,
    fbConfigured: CONFIG.fbPageToken.length > 0,
  });
});

// ── Facebook Webhook ───────────────────────────────────────────────────────
// Verification (GET)
app.get('/webhook/facebook', (req, res) => {
  const mode = req.query['hub.mode'];
  const token = req.query['hub.verify_token'];
  const challenge = req.query['hub.challenge'];

  console.log(`[FB Verify] mode=${mode} token=${token ? '***' : 'none'} challenge=${challenge}`);

  if (mode === 'subscribe' && token === CONFIG.fbVerifyToken) {
    console.log('[FB Verify] ✅ Webhook verified');
    res.status(200).send(challenge);
  } else {
    console.log('[FB Verify] ❌ Verification failed');
    res.status(403).send('Forbidden');
  }
});

// Receive messages (POST)
app.post('/webhook/facebook', async (req, res) => {
  const body = req.body;

  console.log(`[FB Inbound] ${JSON.stringify(body).slice(0, 500)}`);

  // Always respond 200 OK to acknowledge receipt
  res.status(200).send('EVENT_RECEIVED');

  // Process entries
  if (body.entry) {
    for (const entry of body.entry) {
      if (!entry.messaging) continue;
      for (const event of entry.messaging) {
        // Handle messages only (ignore read receipts, postbacks, etc.)
        if (event.message && event.message.text && event.sender && event.sender.id) {
          const senderId = event.sender.id;
          const messageText = event.message.text;

          console.log(`[FB Message] From: ${senderId} Text: "${messageText.slice(0, 100)}"`);

          // Process asynchronously (don't block the 200 response)
          processMessage('facebook', senderId, messageText).catch(err => {
            console.error('[FB Process Error]', err);
          });
        }
      }
    }
  }
});

// ── Instagram Webhook ──────────────────────────────────────────────────────
// Verification (GET)
app.get('/webhook/instagram', (req, res) => {
  const mode = req.query['hub.mode'];
  const token = req.query['hub.verify_token'];
  const challenge = req.query['hub.challenge'];

  console.log(`[IG Verify] mode=${mode} token=${token ? '***' : 'none'} challenge=${challenge}`);

  if (mode === 'subscribe' && token === CONFIG.igVerifyToken) {
    console.log('[IG Verify] ✅ Webhook verified');
    res.status(200).send(challenge);
  } else {
    console.log('[IG Verify] ❌ Verification failed');
    res.status(403).send('Forbidden');
  }
});

// Receive messages (POST)
app.post('/webhook/instagram', async (req, res) => {
  const body = req.body;
  console.log(`[IG Inbound] ${JSON.stringify(body).slice(0, 500)}`);
  res.status(200).send('EVENT_RECEIVED');

  // Instagram Messaging uses a similar format to Messenger
  if (body.entry) {
    for (const entry of body.entry) {
      if (!entry.messaging) continue;
      for (const event of entry.messaging) {
        if (event.message && event.message.text && event.sender && event.sender.id) {
          const senderId = event.sender.id;
          const messageText = event.message.text;
          console.log(`[IG Message] From: ${senderId} Text: "${messageText.slice(0, 100)}"`);

          processMessage('instagram', senderId, messageText).catch(err => {
            console.error('[IG Process Error]', err);
          });
        }
      }
    }
  }
});

// ── FAQ Info Endpoint ──────────────────────────────────────────────────────
app.get('/faq', (_req, res) => {
  if (!faq) {
    return res.status(500).json({ error: 'FAQ not loaded', detail: faqLoadError });
  }
  res.json({
    name: faq.name,
    tagline: faq.tagline,
    version: faq.version,
    lastUpdated: faq.last_updated,
    categories: Object.keys(faq.categories).map(k => ({
      key: k,
      label: faq.categories[k].label,
      itemCount: faq.categories[k].items.length,
    })),
    totalItems: Object.values(faq.categories).reduce((sum, c) => sum + c.items.length, 0),
    fallbackCount: faq.fallback_answers ? faq.fallback_answers.length : 0,
  });
});

// ── Test endpoint (for development) ────────────────────────────────────────
app.post('/test/match', (req, res) => {
  const { message } = req.body;
  if (!message) {
    return res.status(400).json({ error: 'Missing "message" in body' });
  }
  const startTime = Date.now();
  const result = matchFAQ(message);
  const elapsed = Date.now() - startTime;

  res.json({
    input: message,
    normalized: normalize(message),
    result: result
      ? {
          matched: true,
          id: result.id,
          category: result.category || 'greeting',
          label: result.label,
          confidence: result.confidence,
          answer: result.answer,
        }
      : { matched: false, fallback: getFallbackAnswer() },
    matchTimeMs: elapsed,
  });
});

// ── 404 ────────────────────────────────────────────────────────────────────
app.use((_req, res) => {
  res.status(404).json({ error: 'Not found', service: 'PS VIBE Social Auto-Reply' });
});

// ── Error handler ──────────────────────────────────────────────────────────
app.use((err, _req, res, _next) => {
  console.error('[Server Error]', err);
  res.status(500).json({ error: 'Internal server error' });
});

// ── Start ──────────────────────────────────────────────────────────────────
function start() {
  // Load FAQ
  const faqOk = loadFAQ();
  if (!faqOk) {
    console.warn('[Start] ⚠️  FAQ not loaded — keyword matching will not work');
  }

  // Ensure log dir
  ensureLogDir();

  // Start listening
  app.listen(CONFIG.port, CONFIG.host, () => {
    console.log('');
    console.log('═══════════════════════════════════════════════════════');
    console.log('  PS VIBE — Social Media Auto-Reply System');
    console.log('  📡 Listening on http://' + CONFIG.host + ':' + CONFIG.port);
    console.log('═══════════════════════════════════════════════════════');
    console.log('');
    console.log('  Endpoints:');
    console.log('    GET  /health              — Health check');
    console.log('    GET  /stats               — Message stats');
    console.log('    GET  /faq                 — FAQ info');
    console.log('    POST /test/match          — Test keyword matching');
    console.log('    GET  /webhook/facebook    — FB webhook verification');
    console.log('    POST /webhook/facebook    — FB message receiver');
    console.log('    GET  /webhook/instagram   — IG webhook verification');
    console.log('    POST /webhook/instagram   — IG message receiver');
    console.log('');
    console.log('  Config:');
    console.log('    FAQ:        ' + (faqOk ? '✅ Loaded' : '❌ ' + faqLoadError));
    console.log('    FB Token:   ' + (CONFIG.fbPageToken.length > 0 ? '✅ Set' : '⚠️  Not set'));
    console.log('    Log Dir:    ' + CONFIG.logDir);
    console.log('    Min Conf:   ' + CONFIG.minConfidence);
    console.log('');
    console.log('  Facebook API Requirements:');
    console.log('    1. Facebook Page');
    console.log('    2. Facebook Developer App');
    console.log('    3. pages_messaging permission (app review)');
    console.log('    4. Page Access Token → FB_PAGE_TOKEN env var');
    console.log('');
    console.log('═══════════════════════════════════════════════════════');
  });
}

// ── Entry ──────────────────────────────────────────────────────────────────
start();
