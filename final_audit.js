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

  // ============================================================
  // 1. Sheet-level properties
  // ============================================================
  console.log('═'.repeat(70));
  console.log('🔍 SHEET-LEVEL PROPERTIES');
  console.log('═'.repeat(70));
  
  const ss = await sheets.spreadsheets.get({
    spreadsheetId: SHEET_ID,
    fields: 'properties,sheets(properties,protectedRanges,conditionalFormats,basicFilter)'
  });
  
  const props = ss.data.properties;
  console.log(`Title: ${props.title}`);
  console.log(`Locale: ${props.locale}`);
  console.log(`Time Zone: ${props.timeZone}`);
  console.log(`AutoRecalc: ${props.autoRecalc}`);

  // Check each tab for protected ranges and conditional formats
  console.log('\n🔍 PROTECTED RANGES & CONDITIONAL FORMATTING:');
  for (const s of ss.data.sheets || []) {
    const name = s.properties.title;
    const protectedCount = (s.protectedRanges || []).length;
    const condFmtCount = (s.conditionalFormats || []).length;
    if (protectedCount > 0 || condFmtCount > 0) {
      console.log(`  📑 "${name}": ${protectedCount} protected ranges, ${condFmtCount} conditional formats`);
    }
  }

  // ============================================================
  // 2. Check Receipts tab structure more carefully
  // ============================================================
  console.log('\n' + '═'.repeat(70));
  console.log('🔍 RECEIPTS TAB — STRUCTURAL ANALYSIS');
  console.log('═'.repeat(70));
  
  const recAll = await sheets.spreadsheets.values.get({
    spreadsheetId: SHEET_ID,
    range: `'Receipts'`
  });
  const recRows = recAll.data.values || [];
  console.log(`Total rows: ${recRows.length}`);
  console.log(`Structure: Each row has voucher ID in Col A, JSON receipt data in Col B`);
  console.log(`This is a LOG format, not a structured table`);
  console.log(`\nVoucher IDs found:`);
  for (let i = 0; i < recRows.length; i++) {
    const row = recRows[i];
    const vid = row[0] || '(empty)';
    let type = '?';
    if (row[1]) {
      try {
        const j = JSON.parse(row[1]);
        type = j.type || '?';
      } catch {}
    }
    console.log(`  Row ${i+1}: "${vid}" (type: ${type})`);
  }

  // ============================================================
  // 3. Check Console_Games tab
  // ============================================================
  console.log('\n' + '═'.repeat(70));
  console.log('🔍 CONSOLE_GAMES TAB');
  console.log('═'.repeat(70));
  
  try {
    const cg = await sheets.spreadsheets.values.get({
      spreadsheetId: SHEET_ID,
      range: `'Console_Games'!A1:Z3`
    });
    const cgRows = cg.data.values || [];
    if (cgRows.length > 0) {
      console.log(`Headers: ${JSON.stringify(cgRows[0])}`);
      if (cgRows.length > 1) console.log(`Row 2: ${JSON.stringify(cgRows[1])}`);
    }
  } catch (e) {
    console.log(`  Error: ${e.message}`);
  }

  // ============================================================
  // 4. Promotions_Log check
  // ============================================================
  console.log('\n' + '═'.repeat(70));
  console.log('🔍 PROMOTIONS_LOG TAB');
  console.log('═'.repeat(70));
  
  try {
    const pl = await sheets.spreadsheets.values.get({
      spreadsheetId: SHEET_ID,
      range: `'Promotions_Log'!A1:J3`
    });
    const plRows = pl.data.values || [];
    if (plRows.length > 0) {
      console.log(`Headers: ${JSON.stringify(plRows[0])}`);
      if (plRows.length > 1) console.log(`Row 2: ${JSON.stringify(plRows[1])}`);
    } else {
      console.log(`Empty`);
    }
  } catch (e) {
    console.log(`  Error: ${e.message}`);
  }

  // ============================================================
  // 5. Accounts & financial tabs structure check
  // ============================================================
  console.log('\n' + '═'.repeat(70));
  console.log('🔍 FINANCIAL TABS HEADERS CHECK');
  console.log('═'.repeat(70));
  
  const finTabs = ['Accounts', 'Account_Transfers', 'Payables', 'Receivables', 'Capital_Setup', 
                   'Assets_Register', 'Prepaid_Expenses', 'Advance_Staff', 'Advance_Payments'];
  
  for (const tab of finTabs) {
    try {
      const res = await sheets.spreadsheets.values.get({
        spreadsheetId: SHEET_ID,
        range: `'${tab}'!A1:Z1`
      });
      const rows = res.data.values || [];
      if (rows.length > 0) {
        console.log(`  📑 "${tab}": ${JSON.stringify(rows[0]).substring(0, 150)}`);
      } else {
        console.log(`  📑 "${tab}": EMPTY`);
      }
    } catch (e) {
      console.log(`  📑 "${tab}": ERROR - ${e.message}`);
    }
  }

  // ============================================================
  // 6. Check for hidden columns in Card_Wallet
  // ============================================================
  console.log('\n' + '═'.repeat(70));
  console.log('🔍 CARD_WALLET HIDDEN/MERGED CELLS CHECK');
  console.log('═'.repeat(70));
  
  const cwSheet = ss.data.sheets.find(s => s.properties.title === 'Card_Wallet');
  if (cwSheet) {
    // Check grid properties for hidden columns
    console.log(`Row count: ${cwSheet.properties.gridProperties?.rowCount}`);
    console.log(`Col count: ${cwSheet.properties.gridProperties?.columnCount}`);
    console.log(`Hidden: ${cwSheet.properties.hidden ? 'YES' : 'NO'}`);
  }

  // ============================================================
  // 7. All Promotions check — Active status
  // ============================================================
  console.log('\n' + '═'.repeat(70));
  console.log('🔍 PROMOTIONS — ACTIVE CHECK');
  console.log('═'.repeat(70));
  
  const promos = await sheets.spreadsheets.values.get({
    spreadsheetId: SHEET_ID,
    range: `'Promotions'`
  });
  const promosRows = promos.data.values || [];
  if (promosRows.length > 1) {
    const header = promosRows[0];
    const activeIdx = header.findIndex(h => h === 'Active');
    const titleIdx = header.findIndex(h => h === 'Title');
    console.log(`Active column index: ${activeIdx}, Title column index: ${titleIdx}`);
    for (let i = 1; i < promosRows.length; i++) {
      const active = activeIdx >= 0 ? promosRows[i][activeIdx] : '?';
      const title = titleIdx >= 0 ? promosRows[i][titleIdx] : promosRows[i][1];
      console.log(`  "${title}": Active = ${active}`);
    }
    const allFalse = promosRows.slice(1).every(r => r[activeIdx] === 'FALSE' || r[activeIdx] === false);
    if (allFalse && activeIdx >= 0) {
      console.log(`\n  ⚠️ ALL 5 promotions have Active=FALSE — none are currently active!`);
    }
  }

  // ============================================================
  // 8. Inventory tab check
  // ============================================================
  console.log('\n' + '═'.repeat(70));
  console.log('🔍 INVENTORY TAB');
  console.log('═'.repeat(70));
  
  try {
    const inv = await sheets.spreadsheets.values.get({
      spreadsheetId: SHEET_ID,
      range: `'Inventory'!A1:Z5`
    });
    const invRows = inv.data.values || [];
    if (invRows.length > 0) {
      console.log(`Headers: ${JSON.stringify(invRows[0]).substring(0, 200)}`);
      console.log(`Data rows: ${invRows.length - 1} (in first 5)`);
    }
  } catch (e) {
    console.log(`  Error: ${e.message}`);
  }

  console.log('\n' + '═'.repeat(70));
  console.log('✅ FINAL AUDIT CHECKS COMPLETE');
  console.log('═'.repeat(70));
}

main().catch(e => { console.error(e); process.exit(1); });
