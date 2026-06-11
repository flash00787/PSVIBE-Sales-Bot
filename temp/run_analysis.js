const { sshExec, mysqlQuery } = require('/home/node/.openclaw/workspace/lib/ssh_vps.js');
const fs = require('fs');

async function main() {
  const script = fs.readFileSync('/home/node/.openclaw/workspace/temp/analyze_multi_branch.sh', 'utf8');
  
  // First, SCP the script to VPS via inline base64
  const b64 = Buffer.from(script).toString('base64');
  await sshExec(`echo '${b64}' | base64 -d > /tmp/analyze_multi_branch.sh && chmod +x /tmp/analyze_multi_branch.sh`);
  
  console.log("Script uploaded. Running...");
  
  const result = await sshExec('/tmp/analyze_multi_branch.sh', 120000);
  console.log(result);
  
  // Save to file
  fs.writeFileSync('/home/node/.openclaw/workspace/temp/analyze_output.txt', result);
  console.log("\n=== Output saved to temp/analyze_output.txt ===");
  console.log("Length:", result.length, "chars");
}
main().catch(e => { console.error(e); process.exit(1); });
