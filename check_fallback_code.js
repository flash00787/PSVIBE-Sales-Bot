const fs = require('fs');
const code = fs.readFileSync('/app/dist/model-fallback-Bt3fFWwV.js', 'utf8');

const regex = /resolveAgentModelFallbackValues|defaultFallbacks|OPENAI_DEFAULT_MODEL/g;
let match;
while ((match = regex.exec(code)) !== null) {
  console.log(`Found ${match[0]} at index ${match.index}`);
  const start = Math.max(0, match.index - 200);
  const end = Math.min(code.length, match.index + 200);
  console.log('--- CONTEXT ---');
  console.log(code.substring(start, end));
  console.log('===============\n');
}
