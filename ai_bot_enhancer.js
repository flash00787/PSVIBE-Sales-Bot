#!/usr/bin/env node
/**
 * ai_bot_enhancer.js — PS VIBE Sale Bot AI Enhancement Module
 * 
 * Adds AI-powered features to the Sale Bot:
 *   1. Smart Game Search — fuzzy search for games
 *   2. NLU Command Parser — understand "top up A001 50000", "check member PSV_A001"
 *   3. Intent Classification — detect what the staff/customer wants
 *   4. Context-aware suggestions — based on customer history
 * 
 * Usage:
 *   node ai_bot_enhancer.js search <query>          → Smart game search
 *   node ai_bot_enhancer.js parse "<text>"           → NLU command parsing
 *   node ai_bot_enhancer.js suggest <member_id>      → Smart suggestions
 *   node ai_bot_enhancer.js enhance <text>           → Full AI enhancement
 *   node ai_bot_enhancer.js train <logfile>          → Learn from conversation logs
 */

const fs = require('fs');
const path = require('path');
const https = require('https');

const DEEPSEEK_KEY = process.env.DEEPSEEK_API_KEY;
const LOG_PATH = path.join(__dirname, 'knowledge', 'bot_learning.json');

// ── Load learning data ──
function loadLearn() {
  try {
    return JSON.parse(fs.readFileSync(LOG_PATH, 'utf8'));
  } catch { return { commands: {}, games: {}, members: {}, patterns: [] }; }
}

// ── 1. Smart Game Search (fuzzy match + phonetic) ──
function smartGameSearch(query, gameList) {
  const q = query.toLowerCase().trim();
  
  // Direct match
  const exact = gameList.filter(g => g.title.toLowerCase() === q);
  if (exact.length > 0) return exact;
  
  // Contains match
  const contains = gameList.filter(g => 
    g.title.toLowerCase().includes(q) || q.includes(g.title.toLowerCase())
  );
  
  // Word-by-word match
  const words = q.split(/\s+/);
  const wordMatch = gameList.filter(g => {
    const gt = g.title.toLowerCase();
    return words.some(w => gt.includes(w) && w.length > 2);
  });
  
  // Burmese phonetic matching
  const burmeseNormalize = text => text
    .replace(/ခ/g, 'ခ့').replace(/ဂ/g, 'ဃ')
    .replace(/ဆ/g, 'ဆ').replace(/ဈ/g, 'ဈ');
  
  const phonetic = gameList.filter(g => 
    burmeseNormalize(g.title.toLowerCase()).includes(burmeseNormalize(q)) ||
    burmeseNormalize(q).includes(burmeseNormalize(g.title.toLowerCase()))
  );
  
  // Combine deduped
  const scored = new Map();
  const addScore = (games, score) => {
    games.forEach(g => {
      scored.set(g.title, { game: g, score: (scored.get(g.title)?.score || 0) + score });
    });
  };
  
  addScore(exact, 100);
  addScore(contains, 50);
  addScore(wordMatch, 30);
  addScore(phonetic, 20);
  
  return [...scored.values()]
    .sort((a, b) => b.score - a.score)
    .slice(0, 10)
    .map(s => ({ ...s.game, matchScore: s.score }));
}

// ── 2. NLU Command Parser ──
function parseCommand(text) {
  const lower = text.toLowerCase().trim();
  const result = { intent: null, member: null, amount: null, console: null, duration: null, confidence: 0 };

  // Pattern: "top up <id> <amount>" or "ငွေဖြည့် <id> <amount>"
  const topUpMatch = lower.match(/(top\s*up|ငွေဖြည့်|ဖြည့်)\s+(\S+)\s*(\d+[,.\s]*\d*)/i);
  if (topUpMatch) {
    result.intent = 'topup';
    result.member = topUpMatch[2].toUpperCase();
    result.amount = parseInt(topUpMatch[3].replace(/[,.\s]/g, ''));
    result.confidence = 90;
    return result;
  }

  // Pattern: "check <id>" or "စစ် <id>" or "ကြည့် <id>"
  const checkMatch = lower.match(/(check|စစ်|ကြည့်|ရှာ)\s+(psv[_\s]?[a-z0-9]+|\d{5,})/i);
  if (checkMatch) {
    result.intent = 'check_member';
    result.member = checkMatch[2].toUpperCase().replace(/[\s_]/g, '_');
    result.confidence = 85;
    return result;
  }

  // Pattern: "book <console> for <duration>" or "မှာ <စက်> <နာရီ>"
  const bookMatch = lower.match(/(book|မှာ|ယူ|ငှား)\s+([c][\s-]?\d{2,})\s*(?:for\s)?\s*(\d+)\s*(?:hour|hr|h|နာရီ|ကြာ)?/i);
  if (bookMatch) {
    result.intent = 'booking';
    result.console = bookMatch[2].toUpperCase().replace(/[\s-]/g, '-');
    result.duration = parseInt(bookMatch[3]);
    result.confidence = 80;
    return result;
  }

  // Pattern: "balance <id>" or "လက်ကျန် <id>"
  const balMatch = lower.match(/(balance|လက်ကျန်|balance\s+mins?)\s+(\S+)/i);
  if (balMatch) {
    result.intent = 'balance';
    result.member = balMatch[2].toUpperCase();
    result.confidence = 80;
    return result;
  }

  // Greeting / menu
  if (/^(hi|hello|မင်္ဂလာပါ|start|menu)$/i.test(lower)) {
    result.intent = 'menu';
    result.confidence = 95;
    return result;
  }

  // Daily sales
  if (/(daily|ဒီနေ့|နေ့စဉ်|sales)/i.test(lower) && !/(top|up)/i.test(lower)) {
    result.intent = 'daily_sales';
    result.confidence = 70;
    return result;
  }

  result.intent = 'unknown';
  result.confidence = 0;
  return result;
}

// ── 3. Smart Suggestions (member context) ──
function suggestForMember(memberId, memberData) {
  const suggestions = [];
  
  if (!memberData) {
    suggestions.push({ type: 'check', text: `🔍 Check member: ${memberId}` });
    return suggestions;
  }
  
  const balance = memberData.balance || 0;
  const lastGame = memberData.lastGame;
  const totalSpent = memberData.totalSpent || 0;
  
  if (balance > 0) {
    suggestions.push({ type: 'quick_sale', text: `💵 Quick sale (balance: ${balance.toLocaleString()} Ks)` });
  } else {
    suggestions.push({ type: 'topup', text: `💰 Suggest top-up for ${memberId}` });
  }
  
  if (lastGame) {
    suggestions.push({ type: 'rebook', text: `🔄 Re-book: ${lastGame} (previous session)` });
  }
  
  if (totalSpent > 500000) {
    suggestions.push({ type: 'vip', text: `👑 VIP customer — offer premium console` });
  }
  
  return suggestions;
}

// ── 4. Full AI Enhancement (via DeepSeek) ──
function aiEnhance(text) {
  return new Promise((resolve, reject) => {
    if (!DEEPSEEK_KEY) {
      resolve({ enhanced: text, note: 'No API key available' });
      return;
    }

    const body = JSON.stringify({
      model: 'deepseek-v4-flash',
      messages: [
        { role: 'system', content: 'You are a PS5 gaming lounge assistant bot. Given a staff message, enhance it with:\n- Correct formatting\n- Auto-detect missing info\n- Suggest 1-2 follow-up actions\n- Keep it concise (2-3 lines max)\n\nOutput JSON: {"enhanced": "...", "action": "...", "suggestion": "..."}' },
        { role: 'user', content: `Enhance this staff message:\n\n${text}` }
      ],
      max_tokens: 256,
      temperature: 0.2,
    });

    const req = https.request({
      hostname: 'api.deepseek.com',
      path: '/v1/chat/completions',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${DEEPSEEK_KEY}`,
      },
      timeout: 8000,
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          const content = parsed.choices?.[0]?.message?.content || '{}';
          const result = JSON.parse(content.replace(/```json|```/g, ''));
          resolve(result);
        } catch {
          resolve({ enhanced: text, action: 'manual', suggestion: null });
        }
      });
    });
    req.on('error', () => resolve({ enhanced: text, action: 'manual', suggestion: null }));
    req.write(body);
    req.end();
  });
}

// ── Train from conversation logs ──
function trainFromLogs(logText) {
  const learn = loadLearn();
  const lines = logText.split('\n');
  let trained = 0;

  for (const line of lines) {
    // Extract command patterns
    const cmdMatch = line.match(/(top.?up|check|book|balance)/i);
    if (cmdMatch) {
      const cmd = cmdMatch[1].toLowerCase();
      learn.commands[cmd] = (learn.commands[cmd] || 0) + 1;
      trained++;
    }

    // Extract member IDs
    const memberMatch = line.match(/(PSV[_\s]?[A-Z0-9]+)/i);
    if (memberMatch) {
      const mid = memberMatch[1].toUpperCase().replace(/\s/g, '');
      learn.members[mid] = (learn.members[mid] || 0) + 1;
    }

    // Save raw pattern
    if (line.trim().length > 10) {
      learn.patterns.push({ text: line.trim().substring(0, 200), timestamp: new Date().toISOString() });
    }
  }

  // Keep last 500 patterns
  if (learn.patterns.length > 500) {
    learn.patterns = learn.patterns.slice(-500);
  }

  fs.mkdirSync(path.dirname(LOG_PATH), { recursive: true });
  fs.writeFileSync(LOG_PATH, JSON.stringify(learn, null, 2));
  return { trained, totalCmds: Object.keys(learn.commands).length, totalMembers: Object.keys(learn.members).length };
}

// ── CLI ──
async function main() {
  const args = process.argv.slice(2);
  const cmd = args[0];

  if (!cmd) {
    console.log(`
🤖 PS VIBE Sale Bot — AI Enhancement Module

Commands:
  search <query>     → Smart game search (fuzzy match)
  parse "<text>"     → Parse natural language command
  suggest <member>   → Get smart suggestions
  enhance "<text>"   → Full AI enhancement
  train <file>       → Train from conversation log
  stats              → Show learning stats
`);
    return;
  }

  switch (cmd) {
    case 'search': {
      const query = args.slice(1).join(' ');
      // Simulate with sample games
      const games = [
        { title: 'Spider-Man 2', platform: 'PS5' },
        { title: 'Spider-Man: Miles Morales', platform: 'PS5' },
        { title: 'God of War Ragnarok', platform: 'PS5' },
        { title: 'Split Fiction', platform: 'PS5' },
        { title: 'It Takes Two', platform: 'PS5' },
        { title: 'Call of Duty: Black Ops 6', platform: 'PS5' },
        { title: 'EA FC 25', platform: 'PS5' },
        { title: 'Grand Theft Auto V', platform: 'PS5' },
        { title: 'The Last of Us Part I', platform: 'PS5' },
        { title: 'Horizon Forbidden West', platform: 'PS5' },
        { title: 'NBA 2K25', platform: 'PS5' },
        { title: 'Mortal Kombat 1', platform: 'PS5' },
        { title: 'Tekken 8', platform: 'PS5' },
        { title: 'Resident Evil 4 Remake', platform: 'PS5' },
        { title: 'Astro Bot', platform: 'PS5' },
      ];
      const results = smartGameSearch(query, games);
      console.log(`🔍 Smart Search: "${query}" → ${results.length} result(s)\n`);
      results.forEach((r, i) => {
        console.log(`  ${i+1}. ${r.title} (${r.platform}) — ${r.matchScore}% match`);
      });
      if (results.length === 0) console.log('  ❌ No matches found');
      break;
    }

    case 'parse': {
      const text = args.slice(1).join(' ');
      const result = parseCommand(text);
      console.log(`📝 Parse: "${text}"\n`);
      console.log(`  Intent:     ${result.intent}`);
      console.log(`  Member:     ${result.member || '—'}`);
      console.log(`  Amount:     ${result.amount ? result.amount.toLocaleString() + ' Ks' : '—'}`);
      console.log(`  Console:    ${result.console || '—'}`);
      console.log(`  Duration:   ${result.duration || '—'}`);
      console.log(`  Confidence: ${result.confidence}%`);
      break;
    }

    case 'suggest': {
      const memberId = args[1];
      const suggestions = suggestForMember(memberId, {
        balance: 75000,
        lastGame: 'Split Fiction',
        totalSpent: 350000,
      });
      console.log(`💡 Suggestions for ${memberId}:\n`);
      suggestions.forEach(s => console.log(`  ${s.text}`));
      break;
    }

    case 'enhance': {
      const text = args.slice(1).join(' ');
      const result = await aiEnhance(text);
      console.log(`✨ AI Enhancement: "${text}"\n`);
      console.log(`  Enhanced: ${result.enhanced}`);
      console.log(`  Action:   ${result.action}`);
      if (result.suggestion) console.log(`  Suggest:  ${result.suggestion}`);
      break;
    }

    case 'train': {
      const filePath = args[1];
      if (!fs.existsSync(filePath)) {
        console.log(`❌ File not found: ${filePath}`);
        process.exit(1);
      }
      const logText = fs.readFileSync(filePath, 'utf8');
      const result = trainFromLogs(logText);
      console.log(`🧠 Training complete:`);
      console.log(`  Lines processed: ${result.trained}`);
      console.log(`  Commands learned: ${result.totalCmds}`);
      console.log(`  Members recognized: ${result.totalMembers}`);
      break;
    }

    case 'stats': {
      const learn = loadLearn();
      console.log('📊 Bot Learning Statistics');
      console.log(`  Commands known: ${Object.keys(learn.commands).length}`);
      console.log(`  Members known: ${Object.keys(learn.members).length}`);
      console.log(`  Patterns: ${learn.patterns.length}`);
      console.log(`\n  Top commands:`);
      Object.entries(learn.commands)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .forEach(([cmd, count]) => console.log(`    ${cmd}: ${count}x`));
      break;
    }

    default:
      console.log(`Unknown command: ${cmd}`);
  }
}

main().catch(console.error);
