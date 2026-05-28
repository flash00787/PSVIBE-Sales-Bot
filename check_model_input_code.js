const fs = require('fs');
const file = 'model-input-ChW9XXsQ.js';
if (!fs.existsSync('/app/dist/' + file)) {
  console.log('No model-input file found');
} else {
  console.log('Found file:', file);
  const code = fs.readFileSync('/app/dist/' + file, 'utf8');
  console.log('File length:', code.length);
  // Search for default fallback values
  const regex = /fallbacks|default|openai/gi;
  let match;
  while ((match = regex.exec(code)) !== null) {
    console.log(`Found ${match[0]} at index ${match.index}`);
    const start = Math.max(0, match.index - 150);
    const end = Math.min(code.length, match.index + 150);
    console.log('--- CONTEXT ---');
    console.log(code.substring(start, end));
    console.log('===============\n');
  }
}
