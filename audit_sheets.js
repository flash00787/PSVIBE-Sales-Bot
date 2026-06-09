const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');

const SA_FILE = '/home/node/.openclaw/workspace/kora_drive_sa.json';
const DRIVE_ROOT = '1V6ctTJpXaoRIDnrfxwhVO72I7jfD5GsS';

async function main() {
  // Load SA key
  const key = JSON.parse(fs.readFileSync(SA_FILE, 'utf8'));
  
  // Create JWT auth (google-auth-library v10 uses options object)
  const auth = new google.auth.JWT({
    email: key.client_email,
    key: key.private_key,
    scopes: ['https://www.googleapis.com/auth/drive.readonly', 'https://www.googleapis.com/auth/spreadsheets.readonly']
  });
  
  await auth.authorize();
  console.log('✅ Authenticated as:', key.client_email);

  const drive = google.drive({ version: 'v3', auth });
  const sheets = google.sheets({ version: 'v4', auth });

  // Step 1: List items in Drive root folder
  console.log('\n📁 DRIVE ROOT FOLDER:', DRIVE_ROOT);
  console.log('─'.repeat(70));
  
  const rootRes = await drive.files.list({
    q: `'${DRIVE_ROOT}' in parents and trashed=false`,
    fields: 'files(id, name, mimeType)',
    pageSize: 50
  });
  
  const rootFiles = rootRes.data.files || [];
  console.log(`Found ${rootFiles.length} items:`);
  let finStmtsFolder = null;
  
  for (const f of rootFiles) {
    const type = f.mimeType === 'application/vnd.google-apps.folder' ? '📁' : '📄';
    console.log(`  ${type} ${f.name} (${f.id})`);
    if (f.name.toLowerCase().includes('financial') || f.name.toLowerCase().includes('statement')) {
      finStmtsFolder = f;
    }
  }

  if (!finStmtsFolder) {
    // If no obvious match, look for any folder
    finStmtsFolder = rootFiles.find(f => f.mimeType === 'application/vnd.google-apps.folder');
    if (finStmtsFolder) {
      console.log(`\n  ⚠️ No 'Financial Statements' folder found. Using first folder: "${finStmtsFolder.name}"`);
    } else {
      console.log('\n  ❌ No folders found in root!');
      return;
    }
  } else {
    console.log(`\n  ✅ Found Financial Statements folder: "${finStmtsFolder.name}"`);
  }

  // Step 2: List files inside Financial Statements folder
  console.log(`\n📁 Inside: "${finStmtsFolder.name}" (${finStmtsFolder.id})`);
  console.log('─'.repeat(70));
  
  const finRes = await drive.files.list({
    q: `'${finStmtsFolder.id}' in parents and trashed=false`,
    fields: 'files(id, name, mimeType, modifiedTime)',
    pageSize: 50
  });
  
  const finFiles = finRes.data.files || [];
  console.log(`Found ${finFiles.length} items:`);
  
  let mainSheet = null;
  for (const f of finFiles) {
    const type = f.mimeType === 'application/vnd.google-apps.folder' ? '📁' : 
                 f.mimeType === 'application/vnd.google-apps.spreadsheet' ? '📊' : '📄';
    console.log(`  ${type} ${f.name} (${f.id}) - Modified: ${f.modifiedTime || 'N/A'}`);
    if (f.mimeType === 'application/vnd.google-apps.spreadsheet') {
      if (!mainSheet) mainSheet = f; // Pick the first sheet found
    }
  }

  if (!mainSheet) {
    console.log('\n  ❌ No Google Sheets found in Financial Statements folder!');
    return;
  }

  console.log(`\n  ✅ Main sheet identified: "${mainSheet.name}" (${mainSheet.id})`);

  // Step 3: Get sheet metadata (all tabs)
  console.log(`\n📊 SHEET AUDIT: "${mainSheet.name}"`);
  console.log('═'.repeat(70));
  
  const metaRes = await sheets.spreadsheets.get({
    spreadsheetId: mainSheet.id,
    fields: 'sheets.properties'
  });
  
  const tabs = metaRes.data.sheets || [];
  console.log(`\n📋 TABS (${tabs.length} total):`);
  for (const tab of tabs) {
    const p = tab.properties;
    const hidden = p.hidden ? ' [HIDDEN]' : '';
    console.log(`  📑 "${p.title}" (sheetId=${p.sheetId}, rows=${p.gridProperties?.rowCount || '?'}, cols=${p.gridProperties?.columnCount || '?'})${hidden}`);
  }

  // Check for key tabs
  const tabNames = tabs.map(t => t.properties.title);
  const requiredTabs = ['Card_Wallet', 'Console_Booking', 'Promotions'];
  console.log('\n🔍 KEY TAB CHECK:');
  for (const name of requiredTabs) {
    const found = tabNames.includes(name);
    console.log(`  ${found ? '✅' : '❌'} "${name}"`);
  }

  // Check for old name 'Card_wallet'
  if (tabNames.includes('Card_wallet')) {
    console.log('  ⚠️  OLD tab name "Card_wallet" still exists! (should be "Card_Wallet")');
  }
  
  // Check for Members/Data_Entry variants
  const memberVariants = tabNames.filter(n => 
    n.toLowerCase().includes('member') || n.toLowerCase().includes('data_entry') || n.toLowerCase().includes('data'));
  if (memberVariants.length > 0) {
    console.log(`  📋 Member/data tabs found: ${memberVariants.join(', ')}`);
  }

  // Step 4: Deep-dive into Card_Wallet tab
  const cardWalletTab = tabs.find(t => t.properties.title === 'Card_Wallet' || t.properties.title === 'Card_wallet');
  if (cardWalletTab) {
    const tabName = cardWalletTab.properties.title;
    console.log(`\n🔍 DEEP DIVE: "${tabName}" tab`);
    console.log('─'.repeat(70));
    
    try {
      const cwData = await sheets.spreadsheets.values.get({
        spreadsheetId: mainSheet.id,
        range: `'${tabName}'!A1:Z200`
      });
      
      const cwRows = cwData.data.values || [];
      console.log(`  Rows with data: ${cwRows.length}`);
      
      if (cwRows.length > 0) {
        // Print header
        const header = cwRows[0];
        console.log(`  Headers (${header.length} cols): ${JSON.stringify(header)}`);
        
        // Find Column H (index 7, 0-based)
        const hIdx = header.findIndex(h => h && h.toLowerCase().includes('balance'));
        const effectiveHIdx = hIdx >= 0 ? hIdx : 7;
        const hLabel = hIdx >= 0 ? header[hIdx] : 'H (col 8)';
        
        console.log(`\n  Column "${hLabel}" (index=${effectiveHIdx}) analysis:`);
        
        // Sample first 20 data rows
        let numIssues = 0;
        let dataRowsChecked = 0;
        for (let i = 1; i < Math.min(cwRows.length, 21); i++) {
          const row = cwRows[i];
          if (row.length > effectiveHIdx) {
            const val = row[effectiveHIdx];
            dataRowsChecked++;
            if (val !== undefined && val !== null && val !== '') {
              const isNum = !isNaN(parseFloat(val)) && isFinite(val);
              if (!isNum) {
                numIssues++;
                console.log(`    ⚠️ Row ${i+1}: "${val}" — NOT a number`);
              }
            }
          }
        }
        
        if (numIssues === 0) {
          console.log(`    ✅ All ${dataRowsChecked} non-empty cells are numeric`);
        } else {
          console.log(`    ❌ ${numIssues} non-numeric values found (out of ${dataRowsChecked} checked)`);
        }
        
        // Print first few data rows for verification
        console.log(`\n  Sample data (first 5 rows):`);
        for (let i = 1; i < Math.min(cwRows.length, 6); i++) {
          console.log(`    Row ${i+1}: ${JSON.stringify(cwRows[i])}`);
        }
      }
    } catch (e) {
      console.log(`  ❌ Error reading tab: ${e.message}`);
    }
  }

  // Step 5: Check Console_Booking tab
  const consoleTab = tabs.find(t => t.properties.title === 'Console_Booking');
  if (consoleTab) {
    console.log(`\n🔍 "Console_Booking" tab`);
    console.log('─'.repeat(70));
    try {
      const cbData = await sheets.spreadsheets.values.get({
        spreadsheetId: mainSheet.id,
        range: `'Console_Booking'!A1:Z5`
      });
      const cbRows = cbData.data.values || [];
      if (cbRows.length > 0) {
        console.log(`  Headers: ${JSON.stringify(cbRows[0])}`);
        console.log(`  Data rows: ${cbRows.length - 1} (in first 5)`);
      } else {
        console.log(`  ⚠️ Empty or no headers`);
      }
    } catch (e) {
      console.log(`  ❌ Error: ${e.message}`);
    }
  }

  // Step 6: Check Promotions tab
  const promoTab = tabs.find(t => t.properties.title === 'Promotions');
  if (promoTab) {
    console.log(`\n🔍 "Promotions" tab`);
    console.log('─'.repeat(70));
    try {
      const pData = await sheets.spreadsheets.values.get({
        spreadsheetId: mainSheet.id,
        range: `'Promotions'!A1:Z5`
      });
      const pRows = pData.data.values || [];
      if (pRows.length > 0) {
        console.log(`  Headers: ${JSON.stringify(pRows[0])}`);
        console.log(`  Data rows: ${pRows.length - 1} (in first 5)`);
      } else {
        console.log(`  ⚠️ Empty or no headers`);
      }
    } catch (e) {
      console.log(`  ❌ Error: ${e.message}`);
    }
  }

  // Step 7: FORMULA AUDIT — Search for #REF!, #N/A!, #VALUE! errors across key tabs
  console.log(`\n🔍 FORMULA ERROR SCAN`);
  console.log('═'.repeat(70));
  
  const auditTabs = tabNames.filter(n => 
    ['Card_Wallet', 'Card_wallet', 'Console_Booking', 'Promotions', 'Members', 'Data_Entry', 'Receipt', 'Dashboard'].includes(n) ||
    n.toLowerCase().includes('member') || n.toLowerCase().includes('data')
  );
  
  if (auditTabs.length === 0) {
    // Audit all tabs
    auditTabs.push(...tabNames.slice(0, 10));
  }
  
  console.log(`  Scanning tabs: ${auditTabs.join(', ')}`);
  
  const errorPatterns = ['#REF!', '#N/A!', '#VALUE!', '#ERROR!', '#NAME?', '#DIV/0!'];
  let totalErrors = 0;
  
  for (const tabName of auditTabs) {
    try {
      const tabData = await sheets.spreadsheets.values.get({
        spreadsheetId: mainSheet.id,
        range: `'${tabName}'!A1:Z200`,
        valueRenderOption: 'FORMULA'
      });
      
      const rows = tabData.data.values || [];
      let tabErrors = 0;
      
      for (let r = 0; r < rows.length; r++) {
        const row = rows[r];
        for (let c = 0; c < row.length; c++) {
          const cell = row[c];
          if (typeof cell === 'string') {
            for (const pat of errorPatterns) {
              if (cell.includes(pat)) {
                const colLetter = String.fromCharCode(65 + c);
                console.log(`    ❌ '${tabName}'!${colLetter}${r+1}: "${cell}"`);
                tabErrors++;
                break;
              }
            }
            // Also check for old tab name references in formulas
            if (cell.startsWith('=') && cell.includes('Card_wallet') && !cell.includes('Card_Wallet')) {
              console.log(`    ⚠️ '${tabName}'!${String.fromCharCode(65 + c)}${r+1}: References old "Card_wallet" — "${cell.substring(0, 120)}${cell.length > 120 ? '...' : ''}"`);
              tabErrors++;
            }
          }
        }
      }
      
      totalErrors += tabErrors;
      if (tabErrors === 0) {
        console.log(`    ✅ '${tabName}' — no errors found`);
      }
    } catch (e) {
      console.log(`    ⚠️ Could not read '${tabName}': ${e.message}`);
    }
  }

  // Step 8: Check all remaining tabs for formula issues
  console.log(`\n🔍 COMPREHENSIVE FORMULA SCAN (all tabs, looking for old references)`);
  console.log('─'.repeat(70));
  
  let oldRefCount = 0;
  for (const tabName of tabNames) {
    try {
      const tabData = await sheets.spreadsheets.values.get({
        spreadsheetId: mainSheet.id,
        range: `'${tabName}'!A1:Z100`,
        valueRenderOption: 'FORMULA'
      });
      
      const rows = tabData.data.values || [];
      for (let r = 0; r < rows.length; r++) {
        const row = rows[r];
        for (let c = 0; c < row.length; c++) {
          const cell = row[c];
          if (typeof cell === 'string' && cell.startsWith('=') && cell.includes('Card_wallet') && !cell.includes('Card_Wallet')) {
            console.log(`    ⚠️ '${tabName}'!${String.fromCharCode(65 + c)}${r+1}: "${cell.substring(0, 150)}${cell.length > 150 ? '...' : ''}"`);
            oldRefCount++;
            if (oldRefCount >= 50) break;
          }
        }
        if (oldRefCount >= 50) break;
      }
    } catch (e) {
      // skip tabs that can't be read
    }
    if (oldRefCount >= 50) break;
  }
  
  if (oldRefCount === 0) {
    console.log('    ✅ No old "Card_wallet" references found in formulas');
  } else {
    console.log(`    ❌ ${oldRefCount}+ formulas reference old "Card_wallet" name`);
  }

  // Step 9: Check Receipt/Receipt_Data related tabs
  const receiptTabs = tabNames.filter(n => n.toLowerCase().includes('receipt'));
  if (receiptTabs.length > 0) {
    console.log(`\n🔍 RECEIPT TABS: ${receiptTabs.join(', ')}`);
    for (const rtab of receiptTabs) {
      try {
        const rData = await sheets.spreadsheets.values.get({
          spreadsheetId: mainSheet.id,
          range: `'${rtab}'!A1:H5`
        });
        const rRows = rData.data.values || [];
        if (rRows.length > 0) {
          console.log(`  "${rtab}" headers: ${JSON.stringify(rRows[0])}`);
        }
      } catch (e) {
        console.log(`  ❌ "${rtab}": ${e.message}`);
      }
    }
  } else {
    console.log(`\n🔍 RECEIPT TABS: None found with "receipt" in name`);
  }

  // Summary
  console.log('\n' + '═'.repeat(70));
  console.log('📋 AUDIT SUMMARY');
  console.log('═'.repeat(70));
  console.log(`  Sheet Name: "${mainSheet.name}"`);
  console.log(`  Sheet ID:   ${mainSheet.id}`);
  console.log(`  Total Tabs: ${tabs.length}`);
  console.log(`  Card_Wallet exists: ${cardWalletTab ? '✅ YES' : '❌ NO'}`);
  console.log(`  Formula errors found: ${totalErrors}`);
  console.log(`  Old name references: ${oldRefCount}`);

  return {
    sheetName: mainSheet.name,
    sheetId: mainSheet.id,
    tabs: tabNames,
    cardWalletExists: !!cardWalletTab,
    formulaErrors: totalErrors,
    oldRefs: oldRefCount
  };
}

main()
  .then(summary => {
    console.log('\n✅ Audit complete.');
  })
  .catch(err => {
    console.error('❌ Audit failed:', err.message);
    console.error(err.stack);
    process.exit(1);
  });
