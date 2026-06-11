#!/usr/bin/env node
/**
 * i18n.js — Multi-Language Support System
 * 
 * Provides bilingual (Myanmar + English) translations for PS VIBE.
 * Can detect language and auto-translate responses.
 * 
 * Usage:
 *   node i18n.js test <phrase>        → Detect language + translate
 *   node i18n.js bot                  → Generate bilingual bot strings
 *   node i18n.js export               → Export all translations
 *   node i18n.js stats                → Translation coverage stats
 */

const fs = require('fs');
const path = require('path');

const LOCALE_PATH = path.join(__dirname, 'locales');

// ── Translation Database ──
const TRANSLATIONS = {
  // 🎮 Console Types
  'ps5': { en: 'PS5', mm: 'PS5' },
  'ps4': { en: 'PS4', mm: 'PS4' },
  
  // 💰 Pricing
  'pricing': { en: 'Pricing', mm: 'စျေးနှုန်းများ' },
  'price_per_hour': { en: 'Price per hour', mm: 'တစ်နာရီစျေးနှုန်း' },
  'total_amount': { en: 'Total amount', mm: 'စုစုပေါင်းငွေပမာဏ' },
  'discount': { en: 'Discount', mm: 'လျှော့စျေး' },
  'balance': { en: 'Balance', mm: 'လက်ကျန်ငွေ' },
  'deposit': { en: 'Deposit', mm: 'ငွေသွင်း' },
  'payment': { en: 'Payment', mm: 'ငွေပေးချေမှု' },
  'cash': { en: 'Cash', mm: 'ငွေသား' },
  'wavepay': { en: 'WavePay', mm: 'WavePay' },
  'ayapay': { en: 'AYA Pay', mm: 'AYA Pay' },
  'cbpay': { en: 'CB Pay', mm: 'CB Pay' },
  'kpay': { en: 'KPay', mm: 'KPay' },

  // 🎮 Booking
  'booking': { en: 'Booking', mm: 'ကြိုတင်မှာယူမှု' },
  'console': { en: 'Console', mm: 'ကွန်ဆိုး' },
  'available': { en: 'Available', mm: 'ရနိုင်သည်' },
  'occupied': { en: 'Occupied', mm: 'သုံးစွဲနေသည်' },
  'reserved': { en: 'Reserved', mm: 'ကြိုမှာထားသည်' },
  'start_time': { en: 'Start time', mm: 'စတင်ချိန်' },
  'end_time': { en: 'End time', mm: 'ပြီးဆုံးချိန်' },
  'duration': { en: 'Duration', mm: 'ကြာချိန်' },
  'extend': { en: 'Extend', mm: 'အချိန်တိုး' },
  
  // 👥 Member
  'member': { en: 'Member', mm: 'အဖွဲ့ဝင်' },
  'member_id': { en: 'Member ID', mm: 'အဖွဲ့ဝင်နံပါတ်' },
  'member_name': { en: 'Member name', mm: 'အဖွဲ့ဝင်အမည်' },
  'renew': { en: 'Renew', mm: 'သက်တမ်းတိုး' },
  'topup': { en: 'Top Up', mm: 'ငွေဖြည့်' },
  'new_member': { en: 'New Member', mm: 'အဖွဲ့ဝင်အသစ်' },
  'register': { en: 'Register', mm: 'မှတ်ပုံတင်' },
  
  // 🍔 Food & Drink
  'food_menu': { en: 'Food Menu', mm: 'အစားအသောက်မီနူး' },
  'drinks': { en: 'Drinks', mm: 'အဖျော်ယမကာများ' },
  'food': { en: 'Food', mm: 'အစားအစာ' },
  'order': { en: 'Order', mm: 'မှာယူရန်' },
  'add_to_order': { en: 'Add to order', mm: 'ထည့်မယ်' },
  'confirm_order': { en: 'Confirm order', mm: 'အတည်ပြုမယ်' },
  
  // 🎮 Games
  'game_library': { en: 'Game Library', mm: 'ဂိမ်းစာရင်း' },
  'search_game': { en: 'Search game', mm: 'ဂိမ်းရှာရန်' },
  'popular_games': { en: 'Popular Games', mm: 'လူကြိုက်များသောဂိမ်းများ' },
  'all_games': { en: 'All Games', mm: 'ဂိမ်းအားလုံး' },
  'play': { en: 'Play', mm: 'ကစားမယ်' },
  'select_game': { en: 'Select game', mm: 'ဂိမ်းရွေးပါ' },
  
  // 🕐 Time
  'today': { en: 'Today', mm: 'ယနေ့' },
  'yesterday': { en: 'Yesterday', mm: 'မနေ့က' },
  'this_week': { en: 'This Week', mm: 'ဒီတစ်ပတ်' },
  'this_month': { en: 'This Month', mm: 'ဒီလ' },
  'minutes': { en: 'minutes', mm: 'မိနစ်' },
  'hours': { en: 'hours', mm: 'နာရီ' },
  
  // 🌐 Common
  'welcome': { en: 'Welcome to PS VIBE! Play The Game. Share The VIBE!', mm: 'PS VIBE မှ ကြိုဆိုပါတယ်! Play The Game. Share The VIBE!' },
  'thank_you': { en: 'Thank you!', mm: 'ကျေးဇူးတင်ပါတယ်!' },
  'please_wait': { en: 'Please wait...', mm: 'ခဏစောင့်ပါ...' },
  'confirmed': { en: 'Confirmed ✅', mm: 'အတည်ပြုပြီး ✅' },
  'cancelled': { en: 'Cancelled ❌', mm: 'ပယ်ဖျက်ပြီး ❌' },
  'success': { en: 'Success! 🎉', mm: 'အောင်မြင်ပါတယ်! 🎉' },
  'error': { en: 'Error! ❌', mm: 'အမှားရှိပါတယ်! ❌' },
  'back': { en: '← Back', mm: '← နောက်သို့' },
  'main_menu': { en: 'Main Menu 🏠', mm: 'ပင်မမီနူး 🏠' },
  'yes': { en: 'Yes', mm: 'ဟုတ်' },
  'no': { en: 'No', mm: 'မဟုတ်' },
  'confirm': { en: 'Confirm ✅', mm: 'အတည်ပြုမယ် ✅' },
  'cancel': { en: 'Cancel ❌', mm: 'ပယ်ဖျက်မယ် ❌' },
  'close': { en: 'Close', mm: 'ပိတ်မယ်' },
  'info': { en: 'ℹ️ Info', mm: 'ℹ️ အချက်အလက်' },
  'help': { en: 'Help 🆘', mm: 'အကူအညီ 🆘' },
  
  // ⏰ Session
  'session_active': { en: 'Session Active 🎮', mm: 'ဂိမ်းကစားနေသည် 🎮' },
  'session_ended': { en: 'Session Ended', mm: 'ဂိမ်းပြီးဆုံးသည်' },
  'time_remaining': { en: 'Time Remaining', mm: 'လက်ကျန်အချိန်' },
  'session_warning': { en: '⚠️ Your session ends in 5 minutes!', mm: '⚠️ သင့်အချိန် ၅ မိနစ်အလိုတွင်ကုန်ပါမည်!' },
  'extend_session': { en: 'Extend Session ⏱️', mm: 'အချိန်တိုးမယ် ⏱️' },
  
  // 📊 Report
  'daily_report': { en: 'Daily Report', mm: 'နေ့စဉ်အစီရင်ခံစာ' },
  'total_sales': { en: 'Total Sales', mm: 'စုစုပေါင်းရောင်းအား' },
  'console_sales': { en: 'Console Sales', mm: 'ကွန်ဆိုးရောင်းအား' },
  'food_sales': { en: 'Food Sales', mm: 'အစားအသောက်ရောင်းအား' },
  'top_games': { en: 'Top Games', mm: 'ထိပ်တန်းဂိမ်းများ' },
  'active_sessions': { en: 'Active Sessions', mm: 'လက်ရှိကစားနေသော' },
};

// ── Language Detection ──
function detectLanguage(text) {
  // Check for Myanmar characters (Unicode range: က-၉, U+1000-U+102F)
  const mmPattern = /[\u1000-\u109F\u2000-\u206F]/;
  const hasMM = mmPattern.test(text);
  
  if (hasMM) return 'mm';
  
  // Check for English characters
  const enPattern = /[a-zA-Z]/;
  return enPattern.test(text) ? 'en' : 'en'; // default to English
}

// ── Translate a single key ──
function t(key, lang = 'mm') {
  if (!TRANSLATIONS[key]) return key;
  return TRANSLATIONS[key][lang] || TRANSLATIONS[key]['en'];
}

// ── Detect + translate a phrase ──
function autoTranslate(text, targetLang = 'mm') {
  const sourceLang = detectLanguage(text);
  if (sourceLang === targetLang) return text;
  
  // Try direct key match
  const normalized = text.toLowerCase().replace(/[?!.,:;]/g, '').trim();
  for (const [key, trans] of Object.entries(TRANSLATIONS)) {
    if (trans.en.toLowerCase() === normalized || trans.mm.toLowerCase() === normalized) {
      return trans[targetLang];
    }
  }
  
  return text; // Can't translate, return as-is
}

// ── Template string with variables ──
function tTemplate(template, vars = {}, lang = 'mm') {
  // Translate each key in {braces}
  let result = t(template, lang);
  
  // Replace {variable} placeholders
  for (const [key, val] of Object.entries(vars)) {
    const placeholder = `{${key}}`;
    if (result.includes(placeholder)) {
      result = result.replace(placeholder, val);
    }
  }
  
  return result;
}

// ── Format amounts with currency ──
function fmtCurrency(amount, lang = 'mm') {
  const formatted = Number(amount).toLocaleString('en-US');
  if (lang === 'mm') return `${formatted} ကျပ်`;
  return `${formatted} Ks`;
}

// ── Format time remaining ──
function fmtTimeRemaining(minutes, lang = 'mm') {
  if (lang === 'mm') {
    const hrs = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hrs > 0) return `${hrs}နာရီ ${mins}မိနစ်`;
    return `${mins}မိနစ်`;
  }
  const hrs = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (hrs > 0) return `${hrs}h ${mins}m`;
  return `${mins} minutes`;
}

// ── Test translation ──
function testTranslate(phrase) {
  const lang = detectLanguage(phrase);
  const translated = autoTranslate(phrase);
  
  console.log(`🔍 Input: "${phrase}"`);
  console.log(`🌐 Detected: ${lang === 'mm' ? '🇲🇲 Myanmar' : '🇬🇧 English'}`);
  console.log(`🔄 Auto-translate: "${translated}"`);
  
  // Show matching key if found
  const normalized = phrase.replace(/[?!.,:;]/g, '').trim().toLowerCase();
  for (const [key, trans] of Object.entries(TRANSLATIONS)) {
    if (trans[lang]?.toLowerCase() === normalized) {
      console.log(`   Matched key: "${key}"`);
      console.log(`   Other language: "${trans[lang === 'mm' ? 'en' : 'mm']}"`);
      break;
    }
  }
}

// ── Export all translations ──
function exportTranslations() {
  fs.mkdirSync(LOCALE_PATH, { recursive: true });
  
  const en = {};
  const mm = {};
  
  for (const [key, trans] of Object.entries(TRANSLATIONS)) {
    en[key] = trans.en;
    mm[key] = trans.mm;
  }
  
  fs.writeFileSync(path.join(LOCALE_PATH, 'en.json'), JSON.stringify(en, null, 2));
  fs.writeFileSync(path.join(LOCALE_PATH, 'mm.json'), JSON.stringify(mm, null, 2));
  
  console.log('✅ Exported:');
  console.log(`   en.json — ${Object.keys(en).length} keys`);
  console.log(`   mm.json — ${Object.keys(mm).length} keys`);
  console.log(`   📁 ${LOCALE_PATH}/`);
}

// ── Stats ──
function stats() {
  const total = Object.keys(TRANSLATIONS).length;
  const categories = {};
  
  // Group by category prefix
  for (const key of Object.keys(TRANSLATIONS)) {
    // Use first letter as rough category or extract prefix
    const prefix = key.split('_')[0];
    if (!categories[prefix]) categories[prefix] = 0;
    categories[prefix]++;
  }
  
  console.log('🌐 Translation Statistics');
  console.log('━━━━━━━━━━━━━━━━━━━━━');
  console.log(`📝 Total keys: ${total}`);
  console.log(`🌍 Languages: 2 (🇬🇧 English, 🇲🇲 Myanmar)`);
  console.log();
  
  for (const [cat, count] of Object.entries(categories).sort((a, b) => b[1] - a[1])) {
    console.log(`  ${cat.padEnd(15)} ${count} keys`);
  }
  
  console.log();
  console.log('Coverage: 100% (auto-fallback to English for missing keys)');
}

// ── CLI ──
function main() {
  const args = process.argv.slice(2);
  const cmd = args[0] || 'stats';

  switch (cmd) {
    case 'test':
      testTranslate(args.slice(1).join(' '));
      break;

    case 'bot':
      // Generate bot-ready string map
      const strings = {};
      for (const [key, trans] of Object.entries(TRANSLATIONS)) {
        strings[key] = { en: trans.en, mm: trans.mm };
      }
      const outputPath = path.join(__dirname, 'locales', 'bot_strings.json');
      fs.mkdirSync(path.join(__dirname, 'locales'), { recursive: true });
      fs.writeFileSync(outputPath, JSON.stringify(strings, null, 2));
      console.log(`✅ Bot strings exported to ${outputPath}`);
      console.log(`   ${Object.keys(strings).length} translated strings`);
      break;

    case 'export':
      exportTranslations();
      break;

    case 'stats':
      stats();
      break;

    default:
      console.log(`
🌐 Multi-Language Support
  test <phrase> → Detect language + translate
  bot          → Generate bot string map
  export       → Export locale files
  stats        → Translation coverage

Examples:
  node i18n.js test 'စျေးနှုန်းတွေဘယ်လောက်လဲ'
  node i18n.js test 'How much is PS5?'
  node i18n.js export
`);
  }
}

main();
