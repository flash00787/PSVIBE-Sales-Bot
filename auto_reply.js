#!/usr/bin/env node
/**
 * auto_reply.js — Smart Auto-Reply & Learning System
 * 
 * Matches incoming messages to FAQ knowledge base and auto-suggests replies.
 * Learns from new questions over time.
 * 
 * Usage:
 *   node auto_reply.js match "user message text"   → Find best FAQ match
 *   node auto_reply.js train                       → Show learned patterns
 *   node auto_reply.js stats                       → Show match statistics
 */

const fs = require('fs');
const path = require('path');

const FAQ_PATH = path.join(__dirname, 'knowledge', 'psvibe_faq.json');
const LEARN_PATH = path.join(__dirname, 'knowledge', 'learned_patterns.json');

function loadJson(filePath, fallback = {}) {
  try {
    if (!fs.existsSync(filePath)) return fallback;
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch { return fallback; }
}

function saveJson(filePath, data) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
}

// ── Text normalization ──
function normalize(text) {
  return text.toLowerCase()
    .replace(/[.!?,;:]/g, ' ')
    .replace(/\s+/g, ' ')
    .replace(/[၀-၉]/g, d => '၀၁၂၃၄၅၆၇၈၉'['၀၁၂၃၄၅၆၇၈၉'.indexOf(d)])  // Normalize Myanmar digits
    .trim();
}

function tokenize(text) {
  return normalize(text).split(/\s+/).filter(Boolean);
}

// ── Scoring ──
function wordOverlap(msgTokens, keywords) {
  const kws = keywords.map(k => normalize(k));
  let matches = 0;
  for (const token of msgTokens) {
    if (kws.some(k => token.includes(k) || k.includes(token))) {
      matches++;
    }
  }
  return msgTokens.length > 0 ? matches / Math.max(msgTokens.length, 1) : 0;
}

function patternMatch(msgTokens, patterns) {
  const msg = msgTokens.join(' ');
  for (const p of patterns) {
    const normalizedPattern = normalize(p);
    const ptokens = normalizedPattern.split(/\s+/);
    const overlap = ptokens.filter(t => msg.includes(t)).length;
    if (overlap >= Math.min(2, ptokens.length)) return true;
  }
  return false;
}

// ── Find best match ──
function findMatch(message, faq) {
  const msgTokens = tokenize(message);
  if (msgTokens.length === 0) return null;

  // Check greeting first
  const greeting = faq.greeting_keywords;
  const greetKws = greeting.keywords.map(k => normalize(k));
  if (msgTokens.some(t => greetKws.includes(t))) {
    return {
      type: 'greeting',
      match: 1.0,
      answer: greeting.response,
    };
  }

  let best = null;
  let bestScore = 0;

  for (const catKey in faq.categories) {
    const cat = faq.categories[catKey];
    for (const item of cat.items) {
      const kwScore = wordOverlap(msgTokens, item.keywords);
      const patMatch = patternMatch(msgTokens, item.patterns);

      let score = kwScore * 0.6;
      if (patMatch) score += 0.4;
      if (kwScore > 0.2) score += 0.1;

      if (score > bestScore) {
        bestScore = score;
        best = {
          type: 'faq',
          match: Math.round(score * 100),
          category: cat.label,
          id: item.id,
          answer: item.answer,
          faqOnly: !patMatch,
        };
      }
    }
  }

  // Threshold — don't match below 30%
  if (best && bestScore >= 0.3) return best;

  // Fallback
  const fallbacks = faq.fallback_answers;
  return {
    type: 'fallback',
    match: 0,
    answer: fallbacks[Math.floor(Math.random() * fallbacks.length)],
  };
}

// ── Learning system ──
function learn(message, actualAnswer) {
  const learned = loadJson(LEARN_PATH);
  if (!learned.patterns) learned.patterns = [];
  if (!learned.stats) learned.stats = { matched: 0, fallback: 0, learned: 0 };

  learned.stats.learned++;
  learned.patterns.push({
    message: message.substring(0, 200),
    answer: actualAnswer.substring(0, 200),
    timestamp: new Date().toISOString(),
  });

  // Keep last 500 patterns
  if (learned.patterns.length > 500) {
    learned.patterns = learned.patterns.slice(-500);
  }

  saveJson(LEARN_PATH, learned);
}

// ── Main CLI ──
const args = process.argv.slice(2);
if (args.length < 1) {
  console.log("Usage:");
  console.log("  node auto_reply.js match <message>  → Find best FAQ match");
  console.log("  node auto_reply.js train            → Show learned patterns");
  console.log("  node auto_reply.js stats            → Show match statistics");
  process.exit(0);
}

const cmd = args[0];

if (cmd === 'match') {
  const message = args.slice(1).join(' ');
  if (!message) { console.log("Usage: node auto_reply.js match <message>"); process.exit(1); }

  const faq = loadJson(FAQ_PATH);
  const result = findMatch(message, faq);

  console.log(`🔍 Input: "${message.substring(0, 100)}"`);
  console.log(`🏷️  Type: ${result.type} | Score: ${result.match}%`);
  if (result.category) console.log(`📂 Category: ${result.category}`);
  console.log(`\n💬 Reply:\n${result.answer}`);

  // Output JSON for programmatic use
  if (process.env.JSON_OUTPUT) {
    console.log(`\n---JSON---\n${JSON.stringify(result)}`);
  }

} else if (cmd === 'train') {
  const learned = loadJson(LEARN_PATH);
  const patterns = learned.patterns || [];
  console.log(`📚 Learned Patterns: ${patterns.length}`);
  patterns.slice(-10).forEach((p, i) => {
    console.log(`\n${i+1}. "${p.message.substring(0, 60)}..."`);
    console.log(`   → "${p.answer.substring(0, 60)}..."`);
    console.log(`   🕐 ${p.timestamp}`);
  });

} else if (cmd === 'stats') {
  const learned = loadJson(LEARN_PATH);
  const faq = loadJson(FAQ_PATH);
  const totalItems = Object.values(faq.categories || {}).reduce((s, c) => s + (c.items || []).length, 0);
  const stats = learned.stats || { matched: 0, fallback: 0, learned: 0 };

  console.log("📊 Auto-Reply Statistics");
  console.log(`📚 FAQ Categories: ${Object.keys(faq.categories || {}).length}`);
  console.log(`📝 FAQ Items: ${totalItems}`);
  console.log(`✅ Matched: ${stats.matched}`);
  console.log(`❓ Fallback: ${stats.fallback}`);
  console.log(`🧠 Learned Patterns: ${stats.learned}`);

} else {
  console.log(`Unknown command: ${cmd}`);
  process.exit(1);
}
