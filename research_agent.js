#!/usr/bin/env node
/**
 * research_agent.js — Multi-Session AI Research Agent v2.0
 * ==========================================================
 * Kora's deep research tool: web search → content extraction → AI synthesis.
 *
 * Workflow:
 *   1. Web search for the query (using web_search tool via Kora)
 *   2. Extract content from top results (using web_fetch tool via Kora)
 *   3. Synthesize findings using DeepSeek API
 *   4. Save well-formatted Markdown report to memory/research/
 *
 * Usage:
 *   node research_agent.js "research query" [--timeout 300]
 *   node research_agent.js "Bitcoin price analysis" --depth 3 --format markdown
 *
 * When running as a Kora subagent:
 *   - Use web_search() to find sources
 *   - Use web_fetch() to extract content
 *   - Pipe results to callDeepSeek() for synthesis
 *
 * Environment:
 *   DEEPSEEK_API_KEY - Required for AI synthesis
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

// ─── Configuration ──────────────────────────────────────────
const DEEPSEEK_KEY = process.env.DEEPSEEK_API_KEY;
const RESEARCH_DIR = path.join(__dirname, 'memory', 'research');
const MAX_RETRIES = 2;
const RETRY_DELAY_MS = 3000;

// ─── CLI Argument Parsing ───────────────────────────────────
const args = process.argv.slice(2);
let query = '';
let timeout = 60;
let depth = 3;       // Number of sources to extract
let format = 'markdown';
let model = 'deepseek-v4-pro';
let verbose = false;

for (let i = 0; i < args.length; i++) {
  switch (args[i]) {
    case '--help': case '-h':
      showHelp();
      process.exit(0);
    case '--timeout':
      timeout = parseInt(args[++i]) || 60;
      break;
    case '--depth':
      depth = parseInt(args[++i]) || 3;
      break;
    case '--format':
      format = args[++i] || 'markdown';
      break;
    case '--model':
      model = args[++i] || 'deepseek-v4-pro';
      break;
    case '--verbose': case '-v':
      verbose = true;
      break;
    default:
      query = args[i];
  }
}

function showHelp() {
  console.log(`
🔬 Kora Research Agent v2.0
═══════════════════════════════════════════════════════

Deep research using web search + content extraction + AI synthesis.

USAGE:
  node research_agent.js "research query" [options]

OPTIONS:
  --timeout N     AI synthesis timeout in seconds (default: 60)
  --depth N       Number of web sources to extract (default: 3)
  --format FORMAT Output format: markdown, json, brief (default: markdown)
  --model MODEL   DeepSeek model: deepseek-v4-pro, deepseek-v4-flash
  --verbose, -v   Show detailed progress
  --help, -h      Show this help

EXAMPLES:
  node research_agent.js "Latest AI models benchmark 2026"
  node research_agent.js "Myanmar economy outlook Q3 2026" --depth 5
  node research_agent.js "Bitcoin price" --timeout 120 --verbose

ENVIRONMENT:
  DEEPSEEK_API_KEY  Required for AI synthesis (set in ~/.bashrc or env)
`);
}

if (!query) {
  console.error('❌ Missing research query.');
  console.error('Usage: node research_agent.js "research query" [options]');
  console.error('Try --help for details.');
  process.exit(1);
}

if (!DEEPSEEK_KEY) {
  console.error('❌ DEEPSEEK_API_KEY not set in environment');
  console.error('   export DEEPSEEK_API_KEY="sk-..."');
  process.exit(1);
}

// ─── Utility Functions ──────────────────────────────────────

/** Generate a safe filename from query string */
function safeFilename(str, maxLen = 60) {
  return str
    .replace(/[<>:"/\\|?*\x00-\x1f]/g, '')
    .replace(/\s+/g, '_')
    .substring(0, maxLen);
}

/** Simple sleep/delay */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/** Format timestamp for reports */
function timestamp() {
  return new Date().toISOString().replace('T', ' ').substring(0, 19);
}

/** Format duration human-readable */
function formatDuration(ms) {
  const sec = (ms / 1000).toFixed(1);
  if (sec < 60) return `${sec}s`;
  const min = Math.floor(sec / 60);
  return `${min}m ${(sec % 60).toFixed(0)}s`;
}

/** Log with timestamp */
function log(msg, level = 'info') {
  const icons = { info: '📌', step: '⏳', done: '✅', warn: '⚠️', error: '❌' };
  const icon = icons[level] || '  ';
  if (verbose || level !== 'info') {
    console.log(`   ${icon} ${msg}`);
  }
}

// ─── Web Search Module ──────────────────────────────────────
/**
 * Performs web search.
 * When running via Kora subagent, this uses the web_search tool.
 * For standalone CLI usage, this is a stub that explains how to pass results.
 *
 * In Kora subagent context, you should:
 *   const results = await web_search(query, { count: depth });
 * Then pass results directly to the synthesis step.
 */
function webSearch(query, count = 3) {
  log(`Searching web: "${query.substring(0, 60)}..."`, 'step');
  log(`Requesting ${count} results`, 'info');
  log(`When running as Kora subagent, use the web_search tool directly.`, 'info');
  log(`For standalone CLI, pass pre-fetched content with --sources.`, 'info');
  return [];
}

// ─── Content Extraction Module ──────────────────────────────
/**
 * Extracts readable content from a URL.
 * When running via Kora subagent, use web_fetch(url, { extractMode: 'markdown' }).
 */
function extractContent(url) {
  log(`Fetching: ${url.substring(0, 80)}`, 'step');
  log(`When running as Kora subagent, use the web_fetch tool directly.`, 'info');
  return '';
}

// ─── DeepSeek API Integration ───────────────────────────────

/**
 * Call DeepSeek API for AI synthesis.
 * Supports retry on transient errors.
 */
function callDeepSeek(systemPrompt, userMessage, timeoutSec, attempt = 0) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({
      model: model,
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userMessage }
      ],
      max_tokens: 8192,
      temperature: 0.3,
      top_p: 0.95,
      stream: false,
    });

    const req = https.request({
      hostname: 'api.deepseek.com',
      path: '/v1/chat/completions',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${DEEPSEEK_KEY}`,
      },
      timeout: timeoutSec * 1000,
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          if (parsed.error) {
            const errMsg = parsed.error.message || 'Unknown API error';
            // Retry on rate limit or server errors
            if ((res.statusCode === 429 || res.statusCode >= 500) && attempt < MAX_RETRIES) {
              log(`Retry ${attempt + 1}/${MAX_RETRIES} after: ${errMsg}`, 'warn');
              setTimeout(() => {
                resolve(callDeepSeek(systemPrompt, userMessage, timeoutSec, attempt + 1));
              }, RETRY_DELAY_MS * (attempt + 1));
            } else {
              reject(new Error(`DeepSeek API error: ${errMsg}`));
            }
            return;
          }
          const text = parsed.choices?.[0]?.message?.content || '';
          const usage = parsed.usage;
          if (verbose && usage) {
            log(`Tokens: ${usage.prompt_tokens} in + ${usage.completion_tokens} out`, 'info');
          }
          resolve(text);
        } catch (e) {
          reject(new Error(`Parse error: ${e.message}`));
        }
      });
    });

    req.on('error', (err) => {
      if (attempt < MAX_RETRIES) {
        log(`Retry ${attempt + 1}/${MAX_RETRIES}: ${err.message}`, 'warn');
        setTimeout(() => {
          resolve(callDeepSeek(systemPrompt, userMessage, timeoutSec, attempt + 1));
        }, RETRY_DELAY_MS * (attempt + 1));
      } else {
        reject(err);
      }
    });
    req.on('timeout', () => {
      req.destroy();
      reject(new Error(`Request timed out after ${timeoutSec}s`));
    });
    req.write(body);
    req.end();
  });
}

// ─── Research Synthesis ─────────────────────────────────────

/**
 * Build the system prompt for DeepSeek synthesis.
 */
function buildSystemPrompt(query) {
  return `You are Kora's Research Agent — a specialized deep-research AI.

TASK: Synthesize a comprehensive research report based on the provided web search results.

GUIDELINES:
- **Accuracy first**: Only use facts from the provided sources. If information is missing, note it.
- **Structure**: Use clear headings (##), bullet points, and numbered lists.
- **Tables**: Use Markdown tables for comparing data (prices, specs, timelines).
- **Citations**: Reference sources inline with [Source 1], [Source 2], etc.
- **Objectivity**: Present multiple viewpoints. Flag speculation vs. confirmed facts.
- **Practical**: Include actionable insights, code snippets, or implementation notes where relevant.
- **Limitations**: End with a "Caveats & Limitations" section noting what couldn't be confirmed.

FORMAT RULES:
- Start with "## Key Findings" (3-5 bullet-point summary)
- Follow with detailed sections as appropriate
- Use \`\`\` code blocks for technical content
- Use | tables | for | comparisons |
- End with "## Sources" list and "## Caveats & Limitations"

Research Query: ${query}`;
}

/**
 * Synthesize research from web sources.
 * When running as Kora subagent, pass the output of web_search + web_fetch here.
 */
async function synthesize(query, sources, timeoutSec) {
  log('Synthesizing research...', 'step');

  let sourcesText = '';
  if (sources && sources.length > 0) {
    sourcesText = '\n\n## SOURCE MATERIAL\n\n';
    sources.forEach((s, i) => {
      sourcesText += `### Source ${i + 1}: ${s.title || s.url || 'Unknown'}\n`;
      sourcesText += `URL: ${s.url}\n\n`;
      sourcesText += `${s.content || s.snippet || 'No content extracted'}\n\n`;
      sourcesText += `---\n\n`;
    });
  } else {
    sourcesText = `\n\n## NOTE: No web sources provided\n`;
    sourcesText += `This synthesis is based on the model's training knowledge only.\n`;
    sourcesText += `For better results, use web_search + web_fetch tools when running via Kora.\n`;
  }

  const systemPrompt = buildSystemPrompt(query);
  const userMessage = `Research Query: ${query}\nDate: ${new Date().toISOString()}\n${sourcesText}\n\nPlease synthesize a comprehensive research report.`;

  return await callDeepSeek(systemPrompt, userMessage, timeoutSec);
}

// ─── Report Generation ──────────────────────────────────────

/**
 * Generate a formatted Markdown report.
 */
function generateReport(query, synthesis, sources, elapsed, format) {
  const now = new Date();
  const lines = [];

  lines.push(`# 📚 Research Report`);
  lines.push(``);
  lines.push(`> **Query:** ${query}`);
  lines.push(`> **Generated:** ${timestamp()} UTC`);
  lines.push(`> **Duration:** ${formatDuration(elapsed)}`);
  lines.push(`> **Model:** ${model}`);
  lines.push(`> **Sources Extracted:** ${sources ? sources.length : 0}`);
  lines.push(``);
  lines.push(`---`);
  lines.push(``);
  lines.push(synthesis);
  lines.push(``);
  lines.push(`---`);
  lines.push(``);
  lines.push(`## 🔍 Search Metadata`);
  lines.push(``);
  lines.push(`| Field | Value |`);
  lines.push(`|-------|-------|`);
  lines.push(`| Query | ${query} |`);
  lines.push(`| Timestamp | ${now.toISOString()} |`);
  lines.push(`| Elapsed | ${formatDuration(elapsed)} |`);
  lines.push(`| Model | ${model} |`);
  lines.push(`| Sources | ${sources ? sources.length : 0} |`);
  lines.push(``);

  if (sources && sources.length > 0) {
    lines.push(`## 📎 Sources Referenced`);
    lines.push(``);
    sources.forEach((s, i) => {
      lines.push(`${i + 1}. **${s.title || 'Untitled'}** — ${s.url || 'N/A'}`);
    });
    lines.push(``);
  }

  lines.push(`---`);
  lines.push(`*Generated by Kora Research Agent v2.0 | ${now.toISOString().substring(0, 10)}*`);

  return lines.join('\n');
}

/**
 * Generate a JSON report.
 */
function generateJSONReport(query, synthesis, sources, elapsed) {
  return JSON.stringify({
    query,
    timestamp: new Date().toISOString(),
    duration_ms: elapsed,
    model,
    source_count: sources ? sources.length : 0,
    sources: (sources || []).map(s => ({
      title: s.title || 'Untitled',
      url: s.url || null
    })),
    report: synthesis
  }, null, 2);
}

/**
 * Generate a brief text summary.
 */
function generateBriefReport(query, synthesis, sources, elapsed) {
  // Extract first 2 paragraphs from synthesis for brief mode
  const paragraphs = synthesis.split('\n\n').filter(p => p.trim().length > 0);
  const summary = paragraphs.slice(0, 3).join('\n\n');
  return [
    `═══════════════════════════════════════════════════════`,
    `🔬 Kora Research: ${query.substring(0, 70)}`,
    `═══════════════════════════════════════════════════════`,
    ``,
    summary,
    ``,
    `───`,
    `Generated: ${timestamp()} | ${formatDuration(elapsed)} | ${sources ? sources.length : 0} sources`,
    `Full report saved to: memory/research/`,
  ].join('\n');
}

// ─── Main Research Pipeline ─────────────────────────────────

async function research() {
  console.log(`\n🔬 Kora Research Agent v2.0`);
  console.log(`   Query: "${query}"`);
  console.log(`   Model: ${model} | Depth: ${depth} | Timeout: ${timeout}s`);
  console.log(`   Started: ${timestamp()} UTC\n`);

  const startTime = Date.now();
  let sources = [];
  let synthesis = '';

  try {
    // Phase 1: Web Search
    log(`Phase 1/3: Web Search`, 'step');
    sources = webSearch(query, depth);
    // When running via Kora subagent, sources are passed from tool output.
    // For standalone mode, sources will be empty and the model uses training knowledge.

    // Phase 2: Content Extraction
    if (sources.length > 0) {
      log(`Phase 2/3: Content Extraction (${sources.length} sources)`, 'step');
      sources = sources.map((s, i) => {
        if (!s.content && s.url) {
          s.content = extractContent(s.url);
        }
        return s;
      });
    } else {
      log(`Phase 2/3: Skipped (no web sources available in standalone mode)`, 'warn');
      log(`  Tip: Run via Kora subagent for web search + content extraction`, 'info');
    }

    // Phase 3: AI Synthesis
    log(`Phase 3/3: AI Synthesis`, 'step');
    synthesis = await synthesize(query, sources, timeout);

    const elapsed = Date.now() - startTime;

    // Generate report
    let report;
    let ext;
    switch (format) {
      case 'json':
        report = generateJSONReport(query, synthesis, sources, elapsed);
        ext = '.json';
        break;
      case 'brief':
        report = generateBriefReport(query, synthesis, sources, elapsed);
        ext = '.md';
        break;
      default:
        report = generateReport(query, synthesis, sources, elapsed, format);
        ext = '.md';
    }

    // Display
    console.log(`\n${'═'.repeat(60)}`);
    console.log(report);
    console.log(`${'═'.repeat(60)}`);

    // Save to file
    fs.mkdirSync(RESEARCH_DIR, { recursive: true });
    const safeName = safeFilename(query);
    const outPath = path.join(RESEARCH_DIR, `${safeName}_${Date.now()}${ext}`);
    fs.writeFileSync(outPath, report, 'utf-8');

    console.log(`\n💾 Saved to: ${outPath}`);
    console.log(`📊 Complete in ${formatDuration(elapsed)}\n`);

  } catch (err) {
    console.error(`\n❌ Research failed: ${err.message}`);
    if (verbose) {
      console.error(err.stack);
    }
    process.exit(1);
  }
}

// ─── Run ─────────────────────────────────────────────────────
research();
