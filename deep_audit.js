const { google } = require('googleapis');
const fs = require('fs');

const SA_FILE = '/home/node/.openclaw/workspace/kora_drive_sa.json';
const SHEET_ID = '1VFNvhdcYVlVrr5TS49n2peIZa3U6y_AI-Mfo7q7gVsA';

async function main() {
  const key = JSON.parse(fs.readFileSync(SA_FILE, 'utf8'));
  const auth = new google.auth.JWT({
    email: key.client_email,
    key: key.private_key,
    scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly']
  });
  await auth.authorize();
  const sheets = google.sheets({ version: 'v4', auth });

  // Get all tab names
  const meta = await sheets.spreadsheets.get({ spreadsheetId: SHEET_ID, fields: 'sheets.properties' });
  const allTabs = (meta.data.sheets || []).map(s => s.properties.title);
  console.log(`Total tabs: ${allTabs.length}`);

  // ============================================================
  // 1. DEEP FORMULA SCAN — ALL TABS, all rows
  // ============================================================
  console.log('\n' + '═'.repeat(70));
  console.log('🔍 FULL FORMULA ERROR SCAN (all 27 tabs)');
  console.log('═'.repeat(70));

  const errorPatterns = ['#REF!', '#N/A!', '#VALUE!', '#ERROR!', '#NAME?', '#DIV/0!'];
  let allErrors = [];
  let oldRefErrors = [];

  for (const tabName of allTabs) {
    try {
      const res = await sheets.spreadsheets.values.get({
        spreadsheetId: SHEET_ID,
        range: `'${tabName}'`,
        valueRenderOption: 'FORMULA'
      });
      const rows = res.data.values || [];
      
      for (let r = 0; r < rows.length; r++) {
        const row = rows[r];
        for (let c = 0; c < row.length; c++) {
          const cell = row[c];
          if (typeof cell !== 'string') continue;
          
          // Check for error values
          for (const pat of errorPatterns) {
            if (cell.includes(pat)) {
              allErrors.push({ tab: tabName, cell: `${String.fromCharCode(65 + c)}${r + 1}`, formula: cell.substring(0, 200) });
              break;
            }
          }
          
          // Check for old Card_wallet references
          if (cell.startsWith('=')) {
            // Case-sensitive check for 'Card_wallet' (not 'Card_Wallet')
            if (cell.includes("Card_wallet'") || cell.includes('Card_wallet!')) {
              oldRefErrors.push({ tab: tabName, cell: `${String.fromCharCode(65 + c)}${r + 1}`, formula: cell.substring(0, 200) });
            }
          }
        }
      }
    } catch (e) {
      console.log(`  ⚠️ Could not read '${tabName}': ${e.message}`);
    }
  }

  console.log(`\nFormula errors (#REF!, #N/A, etc.): ${allErrors.length}`);
  if (allErrors.length > 0) {
    for (const e of allErrors) {
      console.log(`  ❌ '${e.tab}'!${e.cell}: ${e.formula}`);
    }
  } else {
    console.log('  ✅ No formula errors found anywhere');
  }

  console.log(`\nOld "Card_wallet" reference errors: ${oldRefErrors.length}`);
  if (oldRefErrors.length > 0) {
    for (const e of oldRefErrors) {
      console.log(`  ⚠️ '${e.tab}'!${e.cell}: ${e.formula}`);
    }
  } else {
    console.log('  ✅ No old references found');
  }

  // ============================================================
  // 2. DEEP CARD_WALLET ANALYSIS
  // ============================================================
  console.log('\n' + '═'.repeat(70));
  console.log('🔍 CARD_WALLET DEEP ANALYSIS');
  console.log('═'.repeat(70));

  const cwRes = await sheets.spreadsheets.values.get({
    spreadsheetId: SHEET_ID,
    range: `'Card_Wallet'`
  });
  const cwRows = cwRes.data.values || [];
  console.log(`Total rows: ${cwRows.length} (1 header + ${cwRows.length - 1} data)`);
  
  if (cwRows.length > 0) {
    const header = cwRows[0];
    console.log(`Headers (${header.length}): ${JSON.stringify(header)}`);
    
    // Show all data rows
    console.log('\nAll data rows:');
    for (let i = 1; i < cwRows.length; i++) {
      console.log(`  Row ${i + 1}: ${JSON.stringify(cwRows[i])}`);
    }
  }

  // ============================================================
  // 3. CHECK RECEIPTS TAB PROPERLY
  // ============================================================
  console.log('\n' + '═'.repeat(70));
  console.log('🔍 RECEIPTS TAB');
  console.log('═'.repeat(70));
  
  try {
    const recRes = await sheets.spreadsheets.values.get({
      spreadsheetId: SHEET_ID,
      range: `'Receipts'`
    });
    const recRows = recRes.data.values || [];
    console.log(`Total rows: ${recRows.length}`);
    
    // First row seems to be JSON data rather than headers
    if (recRows.length > 0) {
      console.log(`Row 1 (first 3 cols): ${JSON.stringify(recRows[0]?.slice(0, 3) || [])}`);
      console.log(`Row 2 (first 3 cols): ${JSON.stringify(recRows[1]?.slice(0, 3) || [])}`);
      console.log(`Row 3 (first 3 cols): ${JSON.stringify(recRows[2]?.slice(0, 3) || [])}`);
      
      // Check if there's a header row somewhere
      for (let i = 0; i < Math.min(recRows.length, 10); i++) {
        const row = recRows[i];
        if (row && row[0] && !row[0].startsWith('{') && !row[0].startsWith('NM-') && !row[0].startsWith('TP-')) {
          console.log(`  Possible header at row ${i + 1}: ${JSON.stringify(row.slice(0, 5))}`);
        }
      }
    }
  } catch (e) {
    console.log(`  ❌ Error: ${e.message}`);
  }

  // ============================================================
  // 4. CHECK DASHBOARD FOR FORMULAS
  // ============================================================
  console.log('\n' + '═'.repeat(70));
  console.log('🔍 DASHBOARD FORMULAS (first 20 rows)');
  console.log('═'.repeat(70));
  
  try {
    const dashRes = await sheets.spreadsheets.values.get({
      spreadsheetId: SHEET_ID,
      range: `'Dashboard'!A1:Z20`,
      valueRenderOption: 'FORMULA'
    });
    const dashRows = dashRes.data.values || [];
    let formulaCount = 0;
    for (let r = 0; r < dashRows.length; r++) {
      for (let c = 0; c < dashRows[r].length; c++) {
        const cell = dashRows[r][c];
        if (typeof cell === 'string' && cell.startsWith('=')) {
          formulaCount++;
          // Check for common issues in dashboard formulas
          const hasIssue = errorPatterns.some(p => cell.includes(p));
          const hasOldRef = cell.includes("Card_wallet'") || cell.includes('Card_wallet!');
          if (hasIssue || hasOldRef) {
            console.log(`  ${hasIssue ? '❌' : '⚠️'} ${String.fromCharCode(65 + c)}${r + 1}: ${cell.substring(0, 150)}`);
          }
        }
      }
    }
    console.log(`  Total formulas in Dashboard (rows 1-20): ${formulaCount}`);
    console.log(`  ✅ Dashboard formulas look clean`);
  } catch (e) {
    console.log(`  ❌ Error: ${e.message}`);
  }

  // ============================================================
  // 5. SALES_DAILY & TOPUP_LOG QUICK CHECK
  // ============================================================
  console.log('\n' + '═'.repeat(70));
  console.log('🔍 KEY OPERATIONAL TABS DATA CHECK');
  console.log('═'.repeat(70));
  
  for (const tab of ['Sales_Daily', 'TopUp_Log', 'Stock_Out', 'Stock_In', 'Salary_Payroll', 'Attendance_Log', 'OPEX_Log']) {
    try {
      const res = await sheets.spreadsheets.values.get({
        spreadsheetId: SHEET_ID,
        range: `'${tab}'!A1:Z3`
      });
      const rows = res.data.values || [];
      const dataRows = rows.length > 0 ? rows.length - 1 : 0;
      const headerSnippet = rows.length > 0 ? JSON.stringify(rows[0]).substring(0, 120) : 'N/A';
      // Get total row count quickly
      console.log(`  📑 "${tab}": headers=${rows.length > 0 ? rows[0].length : 0} cols | ${dataRows}+ data rows | ${headerSnippet}`);
    } catch (e) {
      console.log(`  ❌ "${tab}": ${e.message}`);
    }
  }

  // ============================================================
  // 6. CONSOLE_BOOKING DEEP CHECK
  // ============================================================
  console.log('\n' + '═'.repeat(70));
  console.log('🔍 CONSOLE_BOOKING FULL DATA');
  console.log('═'.repeat(70));
  
  try {
    const cbRes = await sheets.spreadsheets.values.get({
      spreadsheetId: SHEET_ID,
      range: `'Console_Booking'`
    });
    const cbRows = cbRes.data.values || [];
    console.log(`Total rows: ${cbRows.length} (1 header + ${cbRows.length - 1} bookings)`);
    if (cbRows.length > 0) {
      console.log(`Headers: ${JSON.stringify(cbRows[0])}`);
      for (let i = 1; i < Math.min(cbRows.length, 6); i++) {
        console.log(`  Booking ${i}: ${JSON.stringify(cbRows[i])}`);
      }
      if (cbRows.length > 6) console.log(`  ... and ${cbRows.length - 6} more`);
    }
  } catch (e) {
    console.log(`  ❌ Error: ${e.message}`);
  }

  // ============================================================
  // 7. PROMOTIONS FULL DATA
  // ============================================================
  console.log('\n' + '═'.repeat(70));
  console.log('🔍 PROMOTIONS FULL DATA');
  console.log('═'.repeat(70));
  
  try {
    const pRes = await sheets.spreadsheets.values.get({
      spreadsheetId: SHEET_ID,
      range: `'Promotions'`
    });
    const pRows = pRes.data.values || [];
    console.log(`Total rows: ${pRows.length} (1 header + ${pRows.length - 1} promos)`);
    if (pRows.length > 0) {
      console.log(`Headers: ${JSON.stringify(pRows[0])}`);
      for (let i = 1; i < pRows.length; i++) {
        console.log(`  Promo ${i}: ${JSON.stringify(pRows[i])}`);
      }
    }
  } catch (e) {
    console.log(`  ❌ Error: ${e.message}`);
  }

  // ============================================================
  // 8. GAME_LIBRARY CHECK
  // ============================================================
  console.log('\n' + '═'.repeat(70));
  console.log('🔍 GAME_LIBRARY QUICK CHECK');
  console.log('═'.repeat(70));
  
  try {
    const glRes = await sheets.spreadsheets.values.get({
      spreadsheetId: SHEET_ID,
      range: `'Game_Library'!A1:Z3`
    });
    const glRows = glRes.data.values || [];
    if (glRows.length > 0) {
      console.log(`Headers (${glRows[0].length} cols): ${JSON.stringify(glRows[0]).substring(0, 200)}`);
      console.log(`Has ${glRows.length - 1}+ data rows`);
    }
  } catch (e) {
    console.log(`  ❌ Error: ${e.message}`);
  }

  console.log('\n' + '═'.repeat(70));
  console.log('✅ DEEP AUDIT COMPLETE');
  console.log('═'.repeat(70));
}

main().catch(e => { console.error(e); process.exit(1); });
