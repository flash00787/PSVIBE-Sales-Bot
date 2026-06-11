#!/usr/bin/env node
/**
 * 🌐 Multi-Channel Support Framework — Kora Workspace
 *
 * Unified inbox concept — prepare framework for:
 *   - Telegram (existing)
 *   - Facebook Messenger (future)
 *   - Discord (future)
 *   - Website Chat / Web widget (future)
 *
 * Features:
 *   - Message queue with channel tags
 *   - Auto-reply routing system (rule-based)
 *   - Channel-agnostic message format
 *   - Priority queue
 *   - Reply templates
 *   - Rate limiting per channel
 *
 * Run: node multi_channel.js [--test] [--stats]
 */

const fs = require('fs');
const path = require('path');

const DATA_DIR = path.join(__dirname, 'memory', 'multi_channel');
const QUEUE_FILE = path.join(DATA_DIR, 'message_queue.json');
const ROUTES_FILE = path.join(DATA_DIR, 'routing_rules.json');
const TEMPLATES_FILE = path.join(__dirname, 'knowledge', 'reply_templates.json');
const STATS_FILE = path.join(DATA_DIR, 'channel_stats.json');

if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });

// ═══════════════════════════════════════════
// CHANNEL DEFINITIONS
// ═══════════════════════════════════════════
const CHANNELS = {
  telegram: {
    id: 'telegram',
    name: 'Telegram',
    icon: '📱',
    enabled: true,
    rateLimit: { maxPerMinute: 30, maxPerHour: 500 },
    priority: 1,
  },
  facebook: {
    id: 'facebook',
    name: 'Facebook Messenger',
    icon: '💬',
    enabled: false,
    rateLimit: { maxPerMinute: 20, maxPerHour: 300 },
    priority: 2,
  },
  discord: {
    id: 'discord',
    name: 'Discord',
    icon: '🎮',
    enabled: false,
    rateLimit: { maxPerMinute: 30, maxPerHour: 500 },
    priority: 2,
  },
  webchat: {
    id: 'webchat',
    name: 'Website Chat',
    icon: '🌍',
    enabled: false,
    rateLimit: { maxPerMinute: 10, maxPerHour: 200 },
    priority: 3,
  },
};

// ═══════════════════════════════════════════
// MESSAGE QUEUE
// ═══════════════════════════════════════════
class MessageQueue {
  constructor() {
    this.queue = this._load();
  }

  _load() {
    try { return JSON.parse(fs.readFileSync(QUEUE_FILE, 'utf8')); }
    catch { return []; }
  }

  _save() {
    // Keep max 1000 messages
    if (this.queue.length > 1000) {
      this.queue = this.queue.slice(-1000);
    }
    fs.writeFileSync(QUEUE_FILE, JSON.stringify(this.queue, null, 2));
  }

  /**
   * Add a message to the unified inbox
   * @param {Object} msg - { channel, userId, userName, text, timestamp, metadata }
   */
  enqueue(msg) {
    const entry = {
      id: `msg_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      channel: msg.channel || 'unknown',
      userId: msg.userId || 'anonymous',
      userName: msg.userName || 'Guest',
      text: msg.text || '',
      priority: CHANNELS[msg.channel]?.priority || 99,
      timestamp: msg.timestamp || new Date().toISOString(),
      status: 'pending', // pending | processing | replied | archived
      replyTo: msg.replyTo || null,
      metadata: msg.metadata || {},
      tags: msg.tags || [],
    };
    this.queue.push(entry);
    this._save();
    return entry;
  }

  /** Get pending messages, ordered by priority then timestamp */
  getPending(limit = 20) {
    return this.queue
      .filter(m => m.status === 'pending')
      .sort((a, b) => a.priority - b.priority || new Date(a.timestamp) - new Date(b.timestamp))
      .slice(0, limit);
  }

  /** Mark a message as replied */
  markReplied(msgId, reply) {
    const msg = this.queue.find(m => m.id === msgId);
    if (msg) {
      msg.status = 'replied';
      msg.reply = reply;
      msg.repliedAt = new Date().toISOString();
      this._save();
    }
  }

  /** Archive old messages */
  archive(olderThanHours = 72) {
    const cutoff = Date.now() - olderThanHours * 3600000;
    const before = this.queue.length;
    this.queue = this.queue.filter(m =>
      m.status !== 'archived' || new Date(m.timestamp).getTime() > cutoff
    );
    return before - this.queue.length;
  }

  /** Get queue stats */
  stats() {
    const byChannel = {};
    const byStatus = { pending: 0, processing: 0, replied: 0, archived: 0 };
    for (const m of this.queue) {
      byChannel[m.channel] = (byChannel[m.channel] || 0) + 1;
      byStatus[m.status] = (byStatus[m.status] || 0) + 1;
    }
    return { total: this.queue.length, byChannel, byStatus };
  }
}

// ═══════════════════════════════════════════
// ROUTING RULES ENGINE
// ═══════════════════════════════════════════
class RoutingEngine {
  constructor() {
    this.rules = this._load();
  }

  _load() {
    try { return JSON.parse(fs.readFileSync(ROUTES_FILE, 'utf8')); }
    catch {
      return this._defaultRules();
    }
  }

  _defaultRules() {
    return {
      categories: {
        pricing: {
          keywords: ['price', 'cost', 'how much', 'rate', 'စျေး', 'ဘယ်လောက်', 'ဈေး'],
          reply: 'pricing_info',
          priority: 1,
        },
        booking: {
          keywords: ['book', 'reserve', 'slot', 'booking', 'ကြိုရင်', 'booking'],
          reply: 'booking_help',
          priority: 2,
        },
        hours: {
          keywords: ['hours', 'open', 'close', 'time', 'ဖွင့်', 'ပိတ်', 'အချိန်'],
          reply: 'hours_info',
          priority: 1,
        },
        location: {
          keywords: ['where', 'location', 'address', 'map', 'လိပ်စာ', 'မြေပုံ', 'နေရာ'],
          reply: 'location_info',
          priority: 1,
        },
        membership: {
          keywords: ['member', 'join', 'register', 'card', 'wallet', 'အဖွဲ့ဝင်', 'member'],
          reply: 'membership_info',
          priority: 2,
        },
        topup: {
          keywords: ['topup', 'top up', 'reload', 'add money', 'balance', 'ငွေဖြည့်', 'topup'],
          reply: 'topup_help',
          priority: 1,
        },
        games: {
          keywords: ['games', 'play', 'list', 'available', 'ဂိမ်း', 'game', 'PS5'],
          reply: 'games_list',
          priority: 2,
        },
        complaint: {
          keywords: ['complaint', 'problem', 'issue', 'bad', 'not working', 'ပြဿနာ', 'မရဘူး'],
          reply: 'complaint_escalate',
          priority: 0, // Highest
        },
        greeting: {
          keywords: ['hello', 'hi', 'hey', 'good morning', 'good evening', 'မင်္ဂလာပါ', 'ဟဲလို'],
          reply: 'greeting',
          priority: 3,
        },
        food: {
          keywords: ['food', 'drink', 'menu', 'snack', 'အစားအသောက်', 'စား'],
          reply: 'food_menu',
          priority: 3,
        },
      },
      defaultReply: 'fallback',
    };
  }

  /**
   * Route a message to the best matching category
   * @returns {{ category: string, reply: string, score: number }}
   */
  route(text) {
    const lower = text.toLowerCase();
    let bestMatch = null;
    let bestScore = 0;

    for (const [category, config] of Object.entries(this.rules.categories)) {
      let score = 0;
      for (const kw of config.keywords) {
        if (lower.includes(kw.toLowerCase())) {
          score += kw.length; // Longer keyword = stronger match
        }
      }
      // Adjust by priority (lower priority number = more important)
      const weightedScore = score * (10 - config.priority);

      if (weightedScore > bestScore) {
        bestScore = weightedScore;
        bestMatch = { category, reply: config.reply, score: weightedScore };
      }
    }

    if (!bestMatch || bestScore < 3) {
      return { category: 'fallback', reply: this.rules.defaultReply, score: 0 };
    }
    return bestMatch;
  }

  addRule(category, keywords, reply, priority = 2) {
    this.rules.categories[category] = { keywords, reply, priority };
    fs.writeFileSync(ROUTES_FILE, JSON.stringify(this.rules, null, 2));
  }
}

// ═══════════════════════════════════════════
// REPLY TEMPLATES
// ═══════════════════════════════════════════
const DEFAULT_TEMPLATES = {
  pricing_info: {
    en: `🎮 PS VIBE Gaming Lounge — Pricing:
• PS5 Console: 5,000 Ks / hour
• Multiplayer: +2,000 Ks for 2nd controller
• Member Discount: 10% off with member card
• Packages available — ask staff for details!`,
    mm: `🎮 PS VIBE — ဈေးနှုန်းများ:
• PS5 Console: ၅၀၀၀ ကျပ် / တစ်နာရီ
• Multiplayer: ဒုတိယ controller အတွက် ၂၀၀၀ ကျပ် ထပ်တိုး
• Member များ ၁၀% discount ရပါတယ်
• Package များလည်းရှိပါတယ် — ဝန်ထမ်းများကိုမေးမြန်းပါ`,
  },
  booking_help: {
    en: `📅 To book a console:
1. Tell us: console type (PS5), date, time, duration
2. We'll confirm availability
3. Your slot is reserved!

Call: [shop number] or message us here!`,
    mm: `📅 Console ကြိုရင်ဘွတ်ကင်လုပ်ရန်:
၁။ PS5 လား၊ ရက်စွဲ၊ အချိန်၊ ကြာချိန် ပြောပြပေးပါ
၂။ ရနိုင်မရနိုင် ပြန်အတည်ပြုပေးပါမယ်
၃။ သင့်အချိန်ကို သေချာရယူထားပါမယ်

ဆက်သွယ်ရန်: [ဆိုင်ဖုန်း]`,
  },
  hours_info: {
    en: `🕐 PS VIBE Operating Hours:
• Open daily: 10:00 AM — 10:00 PM
• Last session starts: 9:00 PM
• Closed on: [special holidays]

📍 Location: [address]`,
    mm: `🕐 PS VIBE ဖွင့်ချိန်:
• နေ့တိုင်း: မနက် ၁၀:၀၀ — ည ၁၀:၀၀
• နောက်ဆုံး session: ည ၉:၀၀
• ပိတ်ရက်: [အထူးရုံးပိတ်ရက်များ]

📍 နေရာ: [လိပ်စာ]`,
  },
  location_info: {
    en: `📍 PS VIBE Gaming Lounge
[Full Address]
Map: [Google Maps link]

Landmarks: [nearby landmarks]`,
    mm: `📍 PS VIBE Gaming Lounge
[လိပ်စာအပြည့်အစုံ]
မြေပုံ: [Google Maps link]`,
  },
  greeting: {
    en: `👋 Hello! Welcome to PS VIBE Gaming Lounge! 🎮
How can I help you today?
• 🎮 Book a console
• 💰 Check balance / Top up
• 📋 See our games
• ❓ Ask a question`,
    mm: `👋 မင်္ဂလာပါ! PS VIBE Gaming Lounge မှကြိုဆိုပါတယ်! 🎮
ဘာကူညီပေးရမလဲ?
• 🎮 Console ဘွတ်ကင်လုပ်မလား
• 💰 Balance စစ်မလား / Top up လုပ်မလား
• 📋 ဂိမ်းတွေကြည့်မလား
• ❓ မေးချင်တာရှိလား`,
  },
  fallback: {
    en: `🤔 I'm not sure I understand. Could you rephrase?
Our staff is available to help! You can:
• Ask about pricing, booking, or hours
• We'll get back to you shortly`,
    mm: `🤔 နားမလည်ပါဘူး။ ပြန်မေးပေးပါလား?
ကျွန်တော်တို့ဝန်ထမ်းတွေ ကူညီဖို့အဆင်သင့်ပါ:
• ဈေးနှုန်း၊ ဘွတ်ကင်၊ ဖွင့်ချိန်တွေ မေးနိုင်ပါတယ်`,
  },
};

class TemplateManager {
  constructor() {
    this.templates = this._load();
  }

  _load() {
    try { return JSON.parse(fs.readFileSync(TEMPLATES_FILE, 'utf8')); }
    catch {
      fs.writeFileSync(TEMPLATES_FILE, JSON.stringify(DEFAULT_TEMPLATES, null, 2));
      return DEFAULT_TEMPLATES;
    }
  }

  get(category, lang = 'en') {
    const t = this.templates[category];
    if (!t) return this.templates.fallback?.[lang] || 'Sorry, no reply template available.';
    return t[lang] || t.en || Object.values(t)[0] || 'No template.';
  }

  set(category, lang, text) {
    if (!this.templates[category]) this.templates[category] = {};
    this.templates[category][lang] = text;
    fs.writeFileSync(TEMPLATES_FILE, JSON.stringify(this.templates, null, 2));
  }

  list() {
    return Object.keys(this.templates);
  }
}

// ═══════════════════════════════════════════
// CHANNEL STATS
// ═══════════════════════════════════════════
class ChannelStats {
  constructor() {
    this.stats = this._load();
  }

  _load() {
    try { return JSON.parse(fs.readFileSync(STATS_FILE, 'utf8')); }
    catch { return {}; }
  }

  _save() {
    fs.writeFileSync(STATS_FILE, JSON.stringify(this.stats, null, 2));
  }

  track(channelId, event) {
    if (!this.stats[channelId]) {
      this.stats[channelId] = { messages: 0, replies: 0, errors: 0, lastActivity: null };
    }
    this.stats[channelId][event] = (this.stats[channelId][event] || 0) + 1;
    this.stats[channelId].lastActivity = new Date().toISOString();
    this._save();
  }

  get(channelId) {
    return this.stats[channelId] || { messages: 0, replies: 0, errors: 0 };
  }

  summary() {
    const summary = {};
    for (const [ch, s] of Object.entries(this.stats)) {
      summary[ch] = {
        name: CHANNELS[ch]?.name || ch,
        icon: CHANNELS[ch]?.icon || '❓',
        ...s,
      };
    }
    return summary;
  }
}

// ═══════════════════════════════════════════
// UNIFIED INBOX (Main Interface)
// ═══════════════════════════════════════════
class UnifiedInbox {
  constructor() {
    this.queue = new MessageQueue();
    this.router = new RoutingEngine();
    this.templates = new TemplateManager();
    this.stats = new ChannelStats();
  }

  /**
   * Process an incoming message from any channel
   * @returns {{ reply: string, category: string, channel: string }}
   */
  processMessage(channel, userId, userName, text) {
    // Track stats
    this.stats.track(channel, 'messages');

    // Check if channel is enabled
    if (!CHANNELS[channel]?.enabled && channel !== 'test') {
      return { reply: null, category: 'disabled', channel };
    }

    // Route the message
    const route = this.router.route(text);

    // Get reply template
    const reply = this.templates.get(route.reply, this._detectLanguage(text));

    // Enqueue
    const msg = this.queue.enqueue({
      channel, userId, userName, text,
      tags: [route.category],
    });
    this.queue.markReplied(msg.id, reply);

    // Track reply
    this.stats.track(channel, 'replies');

    return {
      msgId: msg.id,
      reply,
      category: route.category,
      score: route.score,
      channel,
    };
  }

  _detectLanguage(text) {
    // Check for Myanmar Unicode range
    const mmRegex = /[\u1000-\u109F\uAA60-\uAA7F]/;
    return mmRegex.test(text) ? 'mm' : 'en';
  }

  /** Get all channel definitions */
  getChannels() {
    return Object.values(CHANNELS).map(c => ({
      ...c,
      stats: this.stats.get(c.id),
    }));
  }

  /** Enable/disable a channel */
  setChannelEnabled(channelId, enabled) {
    if (CHANNELS[channelId]) {
      CHANNELS[channelId].enabled = enabled;
    }
  }
}

// ═══════════════════════════════════════════
// CLI / TEST
// ═══════════════════════════════════════════
function main() {
  const args = process.argv.slice(2);

  if (args.includes('--test')) {
    console.log('🧪 Multi-Channel Framework — Test Mode\n');

    const inbox = new UnifiedInbox();

    const testMessages = [
      { ch: 'telegram', user: 'U001', name: 'Aung', text: 'Hi, how much is PS5?' },
      { ch: 'telegram', user: 'U001', name: 'Aung', text: 'I want to book for tomorrow 3pm' },
      { ch: 'telegram', user: 'U002', name: 'Mya', text: 'မင်္ဂလာပါ PS5 ဘယ်လောက်လဲ' },
      { ch: 'webchat', user: 'W001', name: 'Kyaw', text: 'Where are you located?' },
      { ch: 'discord', user: 'D001', name: 'Zaw', text: 'What games you have?' },
      { ch: 'telegram', user: 'U003', name: 'Hla', text: 'The controller is broken' },
    ];

    console.log('📨 Processing test messages:\n');
    for (const msg of testMessages) {
      const result = inbox.processMessage(msg.ch, msg.user, msg.name, msg.text);
      console.log(`  [${result.channel}] ${msg.name}: "${msg.text}"`);
      console.log(`  → ${result.category} (score: ${result.score})`);
      console.log(`  → Reply: ${result.reply?.substring(0, 80)}...\n`);
    }

    console.log('═'.repeat(50));
    console.log('📊 Queue Stats:', inbox.queue.stats());
    console.log('📊 Channel Summary:', inbox.stats.summary());
    console.log('📋 Available templates:', inbox.templates.list().join(', '));

    return;
  }

  if (args.includes('--stats')) {
    const inbox = new UnifiedInbox();
    console.log('📊 Multi-Channel Stats:');
    console.log(JSON.stringify(inbox.queue.stats(), null, 2));
    console.log('\n📊 Channel Summary:');
    console.log(JSON.stringify(inbox.stats.summary(), null, 2));
    console.log('\n🌐 Channels:');
    inbox.getChannels().forEach(c => {
      console.log(`  ${c.icon} ${c.name}: ${c.enabled ? '✅ enabled' : '⏸️  disabled'} (priority ${c.priority})`);
    });
    return;
  }

  // Default: show info
  console.log('🌐 Multi-Channel Support Framework — Kora Workspace');
  console.log('═'.repeat(50));
  console.log('\n📡 Channels:');
  Object.values(CHANNELS).forEach(c => {
    console.log(`  ${c.icon} ${c.name}: ${c.enabled ? '✅ enabled' : '⏸️  disabled'}`);
  });
  console.log('\n⚙️  Components:');
  console.log('  📨 MessageQueue   — Unified inbox with channel tags');
  console.log('  🧭 RoutingEngine  — Keyword-based auto-routing (10 categories)');
  console.log('  📝 TemplateManager — Bilingual reply templates (EN/MM)');
  console.log('  📊 ChannelStats   — Per-channel tracking');
  console.log('\n🔧 Usage:');
  console.log('  node multi_channel.js --test   — Run test messages');
  console.log('  node multi_channel.js --stats  — Show stats');
  console.log('\n📁 Data stored in: memory/multi_channel/');
  console.log('📁 Templates: knowledge/reply_templates.json');
}

main();
